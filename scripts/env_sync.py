#!/usr/bin/env python3
"""Validate and synchronize managed deployment environment variables.

The module deliberately uses only the Python standard library so the reusable
workflow does not install dependencies or expose a secret bundle to package
manager hooks. Public errors identify configuration names and operation stages,
never secret values or provider response bodies.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable, Iterable


RENDER_API_BASE = "https://api.render.com/v1"
VERCEL_API_BASE = "https://api.vercel.com"
NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
VARIABLE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
CONFIDENTIAL_PUBLIC_MARKERS = (
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "PRIVATE_KEY",
    "DATABASE_URL",
    "CREDENTIAL",
)


class ValidationError(ValueError):
    """A value-free manifest or bundle validation failure."""


class SyncError(RuntimeError):
    """A value-free provider synchronization failure."""


@dataclass(frozen=True)
class Target:
    name: str
    provider: str
    provider_environment: str
    bundle_key: str
    secret_names: tuple[str, ...]
    destination_variable: str
    team_variable: str | None = None


@dataclass(frozen=True)
class Manifest:
    version: int
    strict: bool
    targets: tuple[Target, ...]


@dataclass(frozen=True)
class PlannedTarget:
    name: str
    provider: str
    provider_environment: str
    destination_id: str
    values: tuple[tuple[str, str], ...]
    team_id: str | None = None


@dataclass(frozen=True)
class SyncPlan:
    cicg_environment: str
    targets: tuple[PlannedTarget, ...]


class HttpTransport:
    """Small injectable JSON transport with deliberately generic failures."""

    def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: object | None = None,
    ) -> tuple[int, object]:
        data = None
        request_headers = dict(headers)
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            request_headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            url=url,
            data=data,
            headers=request_headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                response_data = response.read()
                if not response_data:
                    payload: object = None
                else:
                    try:
                        payload = json.loads(response_data.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        payload = None
                return response.status, payload
        except urllib.error.HTTPError as error:
            # Do not read or propagate provider response bodies.
            return error.code, None
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise SyncError("provider request failed") from None


def _load_json_object(text: str, label: str) -> dict[str, object]:
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        raise ValidationError(f"{label} must be valid JSON") from None
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be a JSON object")
    return value


def _require_string(value: object, label: str, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{label} must be a non-empty string")
    if pattern is not None and pattern.fullmatch(value) is None:
        raise ValidationError(f"{label} has an invalid name")
    return value


def _parse_secret_names(value: object, target_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValidationError(f"target {target_name} secret_names must be a non-empty array")
    names: list[str] = []
    for item in value:
        name = _require_string(item, f"target {target_name} secret name", VARIABLE_RE)
        if name in names:
            raise ValidationError(f"target {target_name} contains duplicate secret name: {name}")
        if name.startswith("NEXT_PUBLIC_") and any(
            marker in name for marker in CONFIDENTIAL_PUBLIC_MARKERS
        ):
            raise ValidationError(
                f"target {target_name} uses browser-visible key {name} for confidential data"
            )
        names.append(name)
    return tuple(names)


def parse_manifest(text: str) -> Manifest:
    raw = _load_json_object(text, "manifest")
    if raw.get("version") != 1:
        raise ValidationError("manifest version must be 1")

    strict_value = raw.get("strict", True)
    if not isinstance(strict_value, bool):
        raise ValidationError("manifest strict must be a boolean")

    raw_targets = raw.get("targets")
    if not isinstance(raw_targets, list) or not raw_targets:
        raise ValidationError("manifest targets must be a non-empty array")

    targets: list[Target] = []
    seen_names: set[str] = set()
    for index, item in enumerate(raw_targets):
        if not isinstance(item, dict):
            raise ValidationError(f"manifest target {index + 1} must be an object")
        name = _require_string(item.get("name"), f"target {index + 1} name", NAME_RE)
        if name in seen_names:
            raise ValidationError(f"duplicate target name: {name}")
        seen_names.add(name)

        provider = _require_string(item.get("provider"), f"target {name} provider")
        provider_environment = _require_string(
            item.get("environment"), f"target {name} environment"
        )
        if provider == "render":
            if provider_environment not in {"staging", "production"}:
                raise ValidationError(
                    f"target {name} Render environment must be staging or production"
                )
            destination_variable = _require_string(
                item.get("service_id_var"),
                f"target {name} service_id_var",
                VARIABLE_RE,
            )
            team_variable = None
        elif provider == "vercel":
            if provider_environment not in {"preview", "production"}:
                raise ValidationError(
                    f"target {name} Vercel environment must be preview or production"
                )
            destination_variable = _require_string(
                item.get("project_id_var"),
                f"target {name} project_id_var",
                VARIABLE_RE,
            )
            team_variable = _require_string(
                item.get("team_id_var", "VERCEL_ORG_ID"),
                f"target {name} team_id_var",
                VARIABLE_RE,
            )
        else:
            raise ValidationError(f"target {name} provider must be render or vercel")

        bundle_key = _require_string(
            item.get("bundle_key"), f"target {name} bundle_key", NAME_RE
        )
        targets.append(
            Target(
                name=name,
                provider=provider,
                provider_environment=provider_environment,
                bundle_key=bundle_key,
                secret_names=_parse_secret_names(item.get("secret_names"), name),
                destination_variable=destination_variable,
                team_variable=team_variable,
            )
        )

    return Manifest(version=1, strict=strict_value, targets=tuple(targets))


def _targets_for_environment(manifest: Manifest, cicg_environment: str) -> list[Target]:
    if cicg_environment not in {"staging", "production"}:
        raise ValidationError("environment must be staging or production")
    vercel_environment = "preview" if cicg_environment == "staging" else "production"
    return [
        target
        for target in manifest.targets
        if (
            target.provider == "render"
            and target.provider_environment == cicg_environment
        )
        or (
            target.provider == "vercel"
            and target.provider_environment == vercel_environment
        )
    ]


def _parse_bundle(text: str) -> dict[str, dict[str, str]]:
    raw = _load_json_object(text, "environment bundle")
    bundle: dict[str, dict[str, str]] = {}
    for bundle_key, raw_values in raw.items():
        if not isinstance(bundle_key, str) or NAME_RE.fullmatch(bundle_key) is None:
            raise ValidationError("environment bundle contains an invalid bundle key")
        if not isinstance(raw_values, dict):
            raise ValidationError(f"bundle key {bundle_key} must contain an object")
        values: dict[str, str] = {}
        for key, value in raw_values.items():
            if not isinstance(key, str) or VARIABLE_RE.fullmatch(key) is None:
                raise ValidationError(f"bundle key {bundle_key} contains an invalid managed key")
            if not isinstance(value, str):
                raise ValidationError(
                    f"bundle key {bundle_key} managed value for {key} must be a string"
                )
            values[key] = value
        bundle[bundle_key] = values
    return bundle


def _parse_variables(text: str) -> dict[str, str]:
    raw = _load_json_object(text, "repository variables")
    variables: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, str):
            variables[key] = value
    return variables


def build_sync_plan(
    manifest: Manifest,
    bundle_text: str,
    variables_text: str,
    cicg_environment: str,
    target_name: str | None = None,
) -> SyncPlan:
    selected_targets = _targets_for_environment(manifest, cicg_environment)
    if not selected_targets:
        raise ValidationError(f"manifest has no targets for {cicg_environment}")

    bundle = _parse_bundle(bundle_text)
    variables = _parse_variables(variables_text)
    expected_bundle_keys = {target.bundle_key for target in selected_targets}
    missing_bundle_keys = sorted(expected_bundle_keys - bundle.keys())
    if missing_bundle_keys:
        raise ValidationError(f"missing bundle key: {missing_bundle_keys[0]}")
    unexpected_bundle_keys = sorted(bundle.keys() - expected_bundle_keys)
    if manifest.strict and unexpected_bundle_keys:
        raise ValidationError(
            "unexpected bundle keys: " + ", ".join(unexpected_bundle_keys)
        )

    allowed_by_bundle: dict[str, set[str]] = {}
    for target in selected_targets:
        allowed_by_bundle.setdefault(target.bundle_key, set()).update(target.secret_names)
    for bundle_key, allowed_names in allowed_by_bundle.items():
        actual_names = set(bundle[bundle_key])
        missing_names = sorted(allowed_names - actual_names)
        if missing_names:
            raise ValidationError(
                f"bundle key {bundle_key} missing managed keys: {', '.join(missing_names)}"
            )
        unexpected_names = sorted(actual_names - allowed_names)
        if manifest.strict and unexpected_names:
            raise ValidationError(
                f"bundle key {bundle_key} has unexpected managed keys: "
                + ", ".join(unexpected_names)
            )

    planned_targets: list[PlannedTarget] = []
    for target in selected_targets:
        destination_id = variables.get(target.destination_variable, "")
        if not destination_id:
            raise ValidationError(
                f"target {target.name} missing repository variable: "
                f"{target.destination_variable}"
            )
        team_id = None
        if target.team_variable is not None:
            team_id = variables.get(target.team_variable, "")
            if not team_id:
                raise ValidationError(
                    f"target {target.name} missing repository variable: {target.team_variable}"
                )
        values = tuple(
            (name, bundle[target.bundle_key][name]) for name in target.secret_names
        )
        planned_targets.append(
            PlannedTarget(
                name=target.name,
                provider=target.provider,
                provider_environment=target.provider_environment,
                destination_id=destination_id,
                team_id=team_id,
                values=values,
            )
        )

    normalized_target_name = target_name or None
    if normalized_target_name is not None:
        filtered = [target for target in planned_targets if target.name == normalized_target_name]
        if not filtered:
            raise ValidationError(
                f"unknown target for {cicg_environment}: {normalized_target_name}"
            )
        planned_targets = filtered

    return SyncPlan(cicg_environment=cicg_environment, targets=tuple(planned_targets))


def merge_render_environment(
    current: list[dict[str, str]], managed: dict[str, str]
) -> list[dict[str, str]]:
    merged: dict[str, str] = {}
    for item in current:
        key = item.get("key")
        value = item.get("value")
        if isinstance(key, str) and isinstance(value, str):
            merged[key] = value
    merged.update(managed)
    return [{"key": key, "value": merged[key]} for key in sorted(merged)]


def _request_or_fail(
    transport: HttpTransport,
    method: str,
    url: str,
    headers: dict[str, str],
    body: object | None,
    expected_statuses: set[int],
    target: PlannedTarget,
    stage: str,
) -> object:
    try:
        status, payload = transport.request(method, url, headers, body)
    except SyncError:
        raise SyncError(
            f"{target.provider} target {target.name} failed during {stage}"
        ) from None
    if status not in expected_statuses:
        raise SyncError(
            f"{target.provider} target {target.name} failed during {stage}"
        )
    return payload


def _read_render_environment(
    target: PlannedTarget,
    token: str,
    transport: HttpTransport,
) -> list[dict[str, str]]:
    service_id = urllib.parse.quote(target.destination_id, safe="")
    url = f"{RENDER_API_BASE}/services/{service_id}/env-vars?limit=100"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    result: list[dict[str, str]] = []
    while True:
        payload = _request_or_fail(
            transport,
            "GET",
            url,
            headers,
            None,
            {200},
            target,
            "read-current-environment",
        )
        if not isinstance(payload, list):
            raise SyncError(
                f"render target {target.name} failed during read-current-environment"
            )
        for item in payload:
            if not isinstance(item, dict):
                raise SyncError(
                    f"render target {target.name} failed during read-current-environment"
                )
            env_var = item.get("envVar")
            if not isinstance(env_var, dict):
                raise SyncError(
                    f"render target {target.name} failed during read-current-environment"
                )
            key = env_var.get("key")
            value = env_var.get("value")
            if not isinstance(key, str) or not isinstance(value, str):
                raise SyncError(
                    f"render target {target.name} failed during read-current-environment"
                )
            result.append({"key": key, "value": value})

        if len(payload) < 100:
            break
        cursor = payload[-1].get("cursor") if payload else None
        if not isinstance(cursor, str) or not cursor:
            raise SyncError(f"render target {target.name} failed during pagination")
        url = (
            f"{RENDER_API_BASE}/services/{service_id}/env-vars?limit=100&cursor="
            f"{urllib.parse.quote(cursor, safe='')}"
        )
    return result


def _sync_render(
    target: PlannedTarget,
    token: str,
    transport: HttpTransport,
    logger: Callable[[str], None],
) -> None:
    current = _read_render_environment(target, token, transport)
    managed = dict(target.values)
    merged = merge_render_environment(current, managed)
    normalized_current = merge_render_environment(current, {})
    if merged == normalized_current:
        logger(f"render target={target.name} stage=unchanged")
        return
    service_id = urllib.parse.quote(target.destination_id, safe="")
    url = f"{RENDER_API_BASE}/services/{service_id}/env-vars"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    _request_or_fail(
        transport,
        "PUT",
        url,
        headers,
        merged,
        {200, 201, 202},
        target,
        "replace-complete-environment",
    )
    logger(f"render target={target.name} stage=updated")


def _sync_vercel(
    target: PlannedTarget,
    token: str,
    transport: HttpTransport,
    logger: Callable[[str], None],
) -> None:
    if target.team_id is None:
        raise SyncError(f"vercel target {target.name} missing team configuration")
    project_id = urllib.parse.quote(target.destination_id, safe="")
    query = urllib.parse.urlencode({"teamId": target.team_id, "upsert": "true"})
    url = f"{VERCEL_API_BASE}/v10/projects/{project_id}/env?{query}"
    body = [
        {
            "key": key,
            "value": value,
            "target": [target.provider_environment],
            "type": "sensitive",
        }
        for key, value in target.values
    ]
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    _request_or_fail(
        transport,
        "POST",
        url,
        headers,
        body,
        {200, 201},
        target,
        "upsert-environment",
    )
    logger(f"vercel target={target.name} stage=updated")


def synchronize(
    plan: SyncPlan,
    dry_run: bool,
    render_api_key: str,
    vercel_token: str,
    transport: HttpTransport,
    *,
    logger: Callable[[str], None] = print,
) -> None:
    providers = {target.provider for target in plan.targets}
    if not dry_run:
        if "render" in providers and not render_api_key:
            raise SyncError("RENDER_API_KEY is required for selected targets")
        if "vercel" in providers and not vercel_token:
            raise SyncError("VERCEL_TOKEN is required for selected targets")

    for target in plan.targets:
        key_names = ",".join(key for key, _ in target.values)
        logger(
            f"{target.provider} target={target.name} "
            f"environment={target.provider_environment} keys={key_names} "
            f"stage={'dry-run' if dry_run else 'planned'}"
        )
        if dry_run:
            continue
        if target.provider == "render":
            _sync_render(target, render_api_key, transport, logger)
        elif target.provider == "vercel":
            _sync_vercel(target, vercel_token, transport, logger)
        else:
            raise SyncError(f"unsupported provider for target {target.name}")


def _mask_values(value: object) -> Iterable[str]:
    if isinstance(value, dict):
        for child in value.values():
            yield from _mask_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _mask_values(child)
    elif isinstance(value, str) and value:
        yield value


def _workflow_command_escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _mask_bundle_leaf_values(bundle_text: str) -> None:
    try:
        bundle = json.loads(bundle_text)
    except (json.JSONDecodeError, TypeError):
        return
    for value in _mask_values(bundle):
        print(f"::add-mask::{_workflow_command_escape(value)}")


def _parse_boolean(value: str, label: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValidationError(f"{label} must be true or false")


def main() -> int:
    bundle_text = os.environ.get("ENV_SYNC_BUNDLE_JSON", "")
    _mask_bundle_leaf_values(bundle_text)
    try:
        manifest = parse_manifest(os.environ.get("ENV_SYNC_MANIFEST_JSON", ""))
        plan = build_sync_plan(
            manifest,
            bundle_text,
            os.environ.get("ENV_SYNC_REPOSITORY_VARIABLES_JSON", ""),
            os.environ.get("ENV_SYNC_ENVIRONMENT", ""),
            os.environ.get("ENV_SYNC_TARGET", "") or None,
        )
        synchronize(
            plan,
            _parse_boolean(os.environ.get("ENV_SYNC_DRY_RUN", "true"), "dry_run"),
            os.environ.get("RENDER_API_KEY", ""),
            os.environ.get("VERCEL_TOKEN", ""),
            HttpTransport(),
        )
    except (ValidationError, SyncError) as error:
        print(f"environment synchronization failed: {error}", file=sys.stderr)
        return 1
    except Exception:
        print("environment synchronization failed unexpectedly", file=sys.stderr)
        return 1
    print("environment synchronization completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import contextlib
import io
import json
import os
import unittest
from pathlib import Path
from unittest import mock

from scripts.env_sync import (
    HttpTransport,
    SyncError,
    ValidationError,
    build_sync_plan,
    main,
    merge_render_environment,
    parse_manifest,
    synchronize,
)


ROOT = Path(__file__).resolve().parents[1]


def manifest_payload(*, strict: bool = True) -> dict[str, object]:
    return {
        "version": 1,
        "strict": strict,
        "targets": [
            {
                "name": "render-api-staging",
                "provider": "render",
                "environment": "staging",
                "service_id_var": "APP_RENDER_API_STAGING_SERVICE_ID",
                "bundle_key": "render-api",
                "secret_names": ["DATABASE_URL", "JWT_SECRET"],
            },
            {
                "name": "render-api-production",
                "provider": "render",
                "environment": "production",
                "service_id_var": "APP_RENDER_API_PRODUCTION_SERVICE_ID",
                "bundle_key": "render-api",
                "secret_names": ["DATABASE_URL", "JWT_SECRET"],
            },
            {
                "name": "vercel-frontend-staging",
                "provider": "vercel",
                "environment": "preview",
                "project_id_var": "APP_VERCEL_PROJECT_ID",
                "team_id_var": "VERCEL_ORG_ID",
                "bundle_key": "vercel-frontend",
                "secret_names": ["NEXT_PUBLIC_API_BASE_URL", "NEXT_PUBLIC_APP_NAME"],
            },
            {
                "name": "vercel-frontend-production",
                "provider": "vercel",
                "environment": "production",
                "project_id_var": "APP_VERCEL_PROJECT_ID",
                "team_id_var": "VERCEL_ORG_ID",
                "bundle_key": "vercel-frontend",
                "secret_names": ["NEXT_PUBLIC_API_BASE_URL", "NEXT_PUBLIC_APP_NAME"],
            },
        ],
    }


def bundle_payload(*, extra_key: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "render-api": {
            "DATABASE_URL": "postgres://example/db",
            "JWT_SECRET": "quote'\" newline\nUnicode-Ã± shell-$() ; & |",
        },
        "vercel-frontend": {
            "NEXT_PUBLIC_API_BASE_URL": "https://api.example.test",
            "NEXT_PUBLIC_APP_NAME": "Example",
        },
    }
    if extra_key:
        payload["unexpected-target"] = {"EXTRA": "private"}
    return payload


def variables_payload() -> dict[str, str]:
    return {
        "APP_RENDER_API_STAGING_SERVICE_ID": "srv-staging",
        "APP_RENDER_API_PRODUCTION_SERVICE_ID": "srv-production",
        "APP_VERCEL_PROJECT_ID": "prj_frontend",
        "VERCEL_ORG_ID": "team_example",
    }


class FakeTransport(HttpTransport):
    def __init__(self, responses: list[tuple[int, object]]) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, object]] = []

    def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: object | None = None,
    ) -> tuple[int, object]:
        self.requests.append(
            {"method": method, "url": url, "headers": headers, "body": body}
        )
        if not self.responses:
            raise AssertionError(f"Unexpected request: {method} {url}")
        return self.responses.pop(0)


class ManifestValidationTests(unittest.TestCase):
    def test_rejects_malformed_manifest_json_without_echoing_input(self) -> None:
        secret_shaped = '{"version":1,"private":"do-not-print"'
        with self.assertRaisesRegex(ValidationError, "valid JSON") as raised:
            parse_manifest(secret_shaped)
        self.assertNotIn("do-not-print", str(raised.exception))

    def test_rejects_unsupported_version(self) -> None:
        payload = manifest_payload()
        payload["version"] = 2
        with self.assertRaisesRegex(ValidationError, "version must be 1"):
            parse_manifest(json.dumps(payload))

    def test_rejects_duplicate_target_names(self) -> None:
        payload = manifest_payload()
        targets = payload["targets"]
        assert isinstance(targets, list)
        targets.append(dict(targets[0]))
        with self.assertRaisesRegex(ValidationError, "duplicate target name"):
            parse_manifest(json.dumps(payload))

    def test_rejects_provider_environment_mismatch(self) -> None:
        payload = manifest_payload()
        targets = payload["targets"]
        assert isinstance(targets, list)
        targets[0]["environment"] = "preview"
        with self.assertRaisesRegex(ValidationError, "Render environment"):
            parse_manifest(json.dumps(payload))

    def test_rejects_confidential_next_public_name(self) -> None:
        payload = manifest_payload()
        targets = payload["targets"]
        assert isinstance(targets, list)
        targets[2]["secret_names"] = ["NEXT_PUBLIC_PRIVATE_TOKEN"]
        with self.assertRaisesRegex(ValidationError, "browser-visible"):
            parse_manifest(json.dumps(payload))

    def test_maps_staging_to_render_staging_and_vercel_preview(self) -> None:
        manifest = parse_manifest(json.dumps(manifest_payload()))
        plan = build_sync_plan(
            manifest,
            json.dumps(bundle_payload()),
            json.dumps(variables_payload()),
            "staging",
        )
        self.assertEqual(
            [(target.provider, target.provider_environment) for target in plan.targets],
            [("render", "staging"), ("vercel", "preview")],
        )

    def test_maps_production_to_provider_production(self) -> None:
        manifest = parse_manifest(json.dumps(manifest_payload()))
        plan = build_sync_plan(
            manifest,
            json.dumps(bundle_payload()),
            json.dumps(variables_payload()),
            "production",
        )
        self.assertEqual(
            [target.provider_environment for target in plan.targets],
            ["production", "production"],
        )

    def test_detects_missing_bundle_key_before_mutation(self) -> None:
        bundle = bundle_payload()
        del bundle["render-api"]
        with self.assertRaisesRegex(ValidationError, "missing bundle key: render-api"):
            build_sync_plan(
                parse_manifest(json.dumps(manifest_payload())),
                json.dumps(bundle),
                json.dumps(variables_payload()),
                "staging",
            )

    def test_detects_missing_allowlisted_name(self) -> None:
        bundle = bundle_payload()
        render_bundle = bundle["render-api"]
        assert isinstance(render_bundle, dict)
        del render_bundle["JWT_SECRET"]
        with self.assertRaisesRegex(ValidationError, "missing managed keys.*JWT_SECRET"):
            build_sync_plan(
                parse_manifest(json.dumps(manifest_payload())),
                json.dumps(bundle),
                json.dumps(variables_payload()),
                "staging",
            )

    def test_strict_mode_rejects_unexpected_bundle_keys(self) -> None:
        with self.assertRaisesRegex(ValidationError, "unexpected bundle keys"):
            build_sync_plan(
                parse_manifest(json.dumps(manifest_payload(strict=True))),
                json.dumps(bundle_payload(extra_key=True)),
                json.dumps(variables_payload()),
                "staging",
            )

    def test_non_strict_mode_ignores_unexpected_bundle_keys(self) -> None:
        plan = build_sync_plan(
            parse_manifest(json.dumps(manifest_payload(strict=False))),
            json.dumps(bundle_payload(extra_key=True)),
            json.dumps(variables_payload()),
            "staging",
        )
        self.assertEqual(len(plan.targets), 2)

    def test_rejects_missing_destination_variable(self) -> None:
        variables = variables_payload()
        del variables["APP_VERCEL_PROJECT_ID"]
        with self.assertRaisesRegex(ValidationError, "missing repository variable.*APP_VERCEL"):
            build_sync_plan(
                parse_manifest(json.dumps(manifest_payload())),
                json.dumps(bundle_payload()),
                json.dumps(variables),
                "staging",
            )

    def test_target_filter_does_not_bypass_complete_bundle_validation(self) -> None:
        bundle = bundle_payload()
        render_bundle = bundle["render-api"]
        assert isinstance(render_bundle, dict)
        del render_bundle["JWT_SECRET"]
        with self.assertRaisesRegex(ValidationError, "JWT_SECRET"):
            build_sync_plan(
                parse_manifest(json.dumps(manifest_payload())),
                json.dumps(bundle),
                json.dumps(variables_payload()),
                "staging",
                "vercel-frontend-staging",
            )

    def test_rejects_unknown_target_filter(self) -> None:
        with self.assertRaisesRegex(ValidationError, "unknown target"):
            build_sync_plan(
                parse_manifest(json.dumps(manifest_payload())),
                json.dumps(bundle_payload()),
                json.dumps(variables_payload()),
                "staging",
                "missing-target",
            )


class RenderAdapterTests(unittest.TestCase):
    def test_merge_preserves_unmanaged_and_replaces_only_managed_keys(self) -> None:
        merged = merge_render_environment(
            [
                {"key": "UNMANAGED", "value": "keep"},
                {"key": "DATABASE_URL", "value": "old"},
            ],
            {"DATABASE_URL": "new", "JWT_SECRET": "new-secret"},
        )
        self.assertEqual(
            merged,
            [
                {"key": "DATABASE_URL", "value": "new"},
                {"key": "JWT_SECRET", "value": "new-secret"},
                {"key": "UNMANAGED", "value": "keep"},
            ],
        )

    def test_render_sends_complete_merged_list(self) -> None:
        plan = build_sync_plan(
            parse_manifest(json.dumps(manifest_payload())),
            json.dumps(bundle_payload()),
            json.dumps(variables_payload()),
            "staging",
            "render-api-staging",
        )
        transport = FakeTransport(
            [
                (
                    200,
                    [
                        {"cursor": "one", "envVar": {"key": "UNMANAGED", "value": "keep"}},
                        {"cursor": "two", "envVar": {"key": "DATABASE_URL", "value": "old"}},
                    ],
                ),
                (200, []),
            ]
        )
        synchronize(plan, False, "render-token", "", transport, logger=lambda _: None)
        self.assertEqual([request["method"] for request in transport.requests], ["GET", "PUT"])
        self.assertEqual(
            transport.requests[1]["body"],
            [
                {"key": "DATABASE_URL", "value": "postgres://example/db"},
                {"key": "JWT_SECRET", "value": "quote'\" newline\nUnicode-Ã± shell-$() ; & |"},
                {"key": "UNMANAGED", "value": "keep"},
            ],
        )

    def test_render_skips_put_when_managed_values_already_match(self) -> None:
        plan = build_sync_plan(
            parse_manifest(json.dumps(manifest_payload())),
            json.dumps(bundle_payload()),
            json.dumps(variables_payload()),
            "staging",
            "render-api-staging",
        )
        current = [
            {"cursor": "one", "envVar": {"key": key, "value": value}}
            for key, value in bundle_payload()["render-api"].items()
        ]
        transport = FakeTransport([(200, current)])
        synchronize(plan, False, "render-token", "", transport, logger=lambda _: None)
        self.assertEqual([request["method"] for request in transport.requests], ["GET"])

    def test_dry_run_never_calls_render(self) -> None:
        plan = build_sync_plan(
            parse_manifest(json.dumps(manifest_payload())),
            json.dumps(bundle_payload()),
            json.dumps(variables_payload()),
            "staging",
            "render-api-staging",
        )
        transport = FakeTransport([])
        synchronize(plan, True, "", "", transport, logger=lambda _: None)
        self.assertEqual(transport.requests, [])


class VercelAndRedactionTests(unittest.TestCase):
    def test_vercel_uses_sensitive_preview_upsert_without_get(self) -> None:
        plan = build_sync_plan(
            parse_manifest(json.dumps(manifest_payload())),
            json.dumps(bundle_payload()),
            json.dumps(variables_payload()),
            "staging",
            "vercel-frontend-staging",
        )
        transport = FakeTransport([(200, {"created": 2})])
        synchronize(plan, False, "", "vercel-token", transport, logger=lambda _: None)
        self.assertEqual(len(transport.requests), 1)
        request = transport.requests[0]
        self.assertEqual(request["method"], "POST")
        self.assertIn("upsert=true", request["url"])
        self.assertNotIn("vercel-token", request["url"])
        body = request["body"]
        assert isinstance(body, list)
        self.assertEqual({entry["type"] for entry in body}, {"sensitive"})
        self.assertEqual({tuple(entry["target"]) for entry in body}, {("preview",)})

    def test_vercel_production_uses_production_target(self) -> None:
        plan = build_sync_plan(
            parse_manifest(json.dumps(manifest_payload())),
            json.dumps(bundle_payload()),
            json.dumps(variables_payload()),
            "production",
            "vercel-frontend-production",
        )
        transport = FakeTransport([(200, {})])
        synchronize(plan, False, "", "vercel-token", transport, logger=lambda _: None)
        body = transport.requests[0]["body"]
        assert isinstance(body, list)
        self.assertEqual({tuple(entry["target"]) for entry in body}, {("production",)})

    def test_non_dry_run_requires_only_selected_provider_token(self) -> None:
        plan = build_sync_plan(
            parse_manifest(json.dumps(manifest_payload())),
            json.dumps(bundle_payload()),
            json.dumps(variables_payload()),
            "staging",
            "vercel-frontend-staging",
        )
        with self.assertRaisesRegex(SyncError, "VERCEL_TOKEN"):
            synchronize(plan, False, "", "", FakeTransport([]), logger=lambda _: None)

    def test_logs_contain_names_but_no_secret_values_or_provider_bodies(self) -> None:
        plan = build_sync_plan(
            parse_manifest(json.dumps(manifest_payload())),
            json.dumps(bundle_payload()),
            json.dumps(variables_payload()),
            "staging",
            "vercel-frontend-staging",
        )
        logs: list[str] = []
        transport = FakeTransport([(500, {"message": "leaked provider body"})])
        with self.assertRaises(SyncError):
            synchronize(plan, False, "", "vercel-token", transport, logger=logs.append)
        combined = "\n".join(logs)
        self.assertIn("vercel-frontend-staging", combined)
        for value in bundle_payload()["vercel-frontend"].values():
            self.assertNotIn(value, combined)
        self.assertNotIn("vercel-token", combined)
        self.assertNotIn("leaked provider body", combined)

    def test_cli_masks_bundle_values_and_returns_generic_validation_failure(self) -> None:
        env = {
            "ENV_SYNC_MANIFEST_JSON": json.dumps(manifest_payload()),
            "ENV_SYNC_BUNDLE_JSON": "not-json-private-do-not-print",
            "ENV_SYNC_REPOSITORY_VARIABLES_JSON": json.dumps(variables_payload()),
            "ENV_SYNC_ENVIRONMENT": "staging",
            "ENV_SYNC_DRY_RUN": "true",
            "ENV_SYNC_TARGET": "",
        }
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=True):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main()
        self.assertEqual(exit_code, 1)
        combined = stdout.getvalue() + stderr.getvalue()
        self.assertNotIn("not-json-private-do-not-print", combined)
        self.assertNotIn("Traceback", combined)


class WorkflowSecurityTests(unittest.TestCase):
    def test_reusable_workflow_has_trusted_contract_and_forbidden_patterns_absent(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "sync-environment.yml").read_text(
            encoding="utf-8"
        )
        for required in (
            "workflow_call:",
            "ENV_SYNC_BUNDLE:",
            "RENDER_API_KEY:",
            "VERCEL_TOKEN:",
            "repository_variables_json:",
            "dry_run:",
            "validate-prod-promotion@v2.1",
            "contents: read",
            "pull-requests: read",
        ):
            self.assertIn(required, workflow)
        for forbidden in (
            "toJSON(secrets)",
            "upload-artifact",
            "GITHUB_STEP_SUMMARY",
            "GITHUB_OUTPUT",
            "set -x",
        ):
            self.assertNotIn(forbidden, workflow)

    def test_reusable_workflow_checks_out_pinned_central_implementation(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "sync-environment.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "ref: 508c9e39b9fe822cef4bdca588a9ff7ac7133cea",
            workflow,
        )
        self.assertNotIn("ref: ${{ github.workflow_sha }}", workflow)

    def test_render_deploy_declares_its_hook_secret_contract(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "deploy-render.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("    secrets:\n      RENDER_DEPLOY_HOOK_URL:", workflow)
        self.assertIn("        required: true", workflow)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Validate product-repo callers against the CICG CI/CD conventions."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from env_sync import ValidationError, parse_manifest

USES_RE = re.compile(
    r"uses:\s*The-Team-CG/\.github/\.github/workflows/"
    r"(ci-node|ci-python|deploy-vercel|deploy-render|security-gitleaks|"
    r"security-gitleaks-history|security-codeql|notify|release-tag|"
    r"promote-to-prod|rollback-vercel|rollback-render)\.yml@v2(?:\.1)?\b"
)
BRANCHES_RE = re.compile(r"branches:\s*\[staging,\s*prod\]")
WORKFLOW_RUN_BRANCHES_RE = re.compile(
    r"workflow_run[\s\S]*head_branch == ['\"](staging|prod)['\"]"
)
SONAR_RE = re.compile(r"sonar|SONAR_TOKEN|sonar-project", re.IGNORECASE)
SYNC_REF_RE = re.compile(
    r"uses:\s*The-Team-CG/\.github/\.github/workflows/"
    r"sync-environment\.yml@([0-9a-f]{40})\b"
)

EXPECTED_ENV_SYNC = {
    "capstone-system": {
        "destinations": {"CAPSTONE_VERCEL_PROJECT_ID", "VERCEL_ORG_ID"},
        "bundle_keys": {"vercel-frontend"},
        "render_deploy_names": set(),
    },
    "Front-and-back": {
        "destinations": {
            "FRONT_AND_BACK_RENDER_API_STAGING_SERVICE_ID",
            "FRONT_AND_BACK_RENDER_API_PRODUCTION_SERVICE_ID",
            "FRONT_AND_BACK_VERCEL_PROJECT_ID",
            "VERCEL_ORG_ID",
        },
        "bundle_keys": {"render-api", "vercel-frontend"},
        "render_deploy_names": {
            "RENDER_FRONT_AND_BACK_API_STAGING_DEPLOY_HOOK_URL",
            "RENDER_FRONT_AND_BACK_API_PRODUCTION_DEPLOY_HOOK_URL",
        },
    },
    "PAULUS": {
        "destinations": {
            "PAULUS_RENDER_API_STAGING_SERVICE_ID",
            "PAULUS_RENDER_API_PRODUCTION_SERVICE_ID",
            "PAULUS_RENDER_ANALYTICS_STAGING_SERVICE_ID",
            "PAULUS_RENDER_ANALYTICS_PRODUCTION_SERVICE_ID",
            "PAULUS_VERCEL_PROJECT_ID",
            "VERCEL_ORG_ID",
        },
        "bundle_keys": {"render-api", "render-analytics", "vercel-frontend"},
        "render_deploy_names": {
            "RENDER_PAULUS_API_STAGING_DEPLOY_HOOK_URL",
            "RENDER_PAULUS_API_PRODUCTION_DEPLOY_HOOK_URL",
            "RENDER_PAULUS_ANALYTICS_STAGING_DEPLOY_HOOK_URL",
            "RENDER_PAULUS_ANALYTICS_PRODUCTION_DEPLOY_HOOK_URL",
        },
    },
    "prism-cicg-workflow": {
        "destinations": {
            "PRISM_RENDER_API_STAGING_SERVICE_ID",
            "PRISM_RENDER_API_PRODUCTION_SERVICE_ID",
            "PRISM_VERCEL_PROJECT_ID_CLIENT",
            "PRISM_VERCEL_PROJECT_ID_EVENT",
            "PRISM_VERCEL_PROJECT_ID_GUEST",
            "PRISM_VERCEL_PROJECT_ID_SUPPLIER",
            "VERCEL_ORG_ID",
        },
        "bundle_keys": {
            "render-api",
            "vercel-client",
            "vercel-event",
            "vercel-guest",
            "vercel-supplier",
        },
        "render_deploy_names": {
            "RENDER_PRISM_API_STAGING_DEPLOY_HOOK_URL",
            "RENDER_PRISM_API_PRODUCTION_DEPLOY_HOOK_URL",
        },
    },
    "prism": {
        "destinations": {
            "PRISM_RENDER_API_STAGING_SERVICE_ID",
            "PRISM_RENDER_API_PRODUCTION_SERVICE_ID",
            "PRISM_VERCEL_PROJECT_ID_CLIENT",
            "PRISM_VERCEL_PROJECT_ID_EVENT",
            "PRISM_VERCEL_PROJECT_ID_GUEST",
            "PRISM_VERCEL_PROJECT_ID_SUPPLIER",
            "VERCEL_ORG_ID",
        },
        "bundle_keys": {
            "render-api",
            "vercel-client",
            "vercel-event",
            "vercel-guest",
            "vercel-supplier",
        },
        "render_deploy_names": {
            "RENDER_PRISM_API_STAGING_DEPLOY_HOOK_URL",
            "RENDER_PRISM_API_PRODUCTION_DEPLOY_HOOK_URL",
        },
    },
    "WOOF_V1": {
        "destinations": {
            "WOOF_RENDER_API_STAGING_SERVICE_ID",
            "WOOF_RENDER_API_PRODUCTION_SERVICE_ID",
            "WOOF_VERCEL_PROJECT_ID",
            "VERCEL_ORG_ID",
        },
        "bundle_keys": {"render-api", "vercel-frontend"},
        "render_deploy_names": {
            "RENDER_WOOF_API_STAGING_DEPLOY_HOOK_URL",
            "RENDER_WOOF_API_PRODUCTION_DEPLOY_HOOK_URL",
        },
    },
}


def validate_env_sync(root: Path, ci_text: str, deploy_text: str) -> list[str]:
    errors: list[str] = []
    name = root.name
    expected = EXPECTED_ENV_SYNC.get(name)
    if expected is None:
        return [f"{name}: no environment-sync validation contract is registered"]

    manifest_path = root / ".github" / "env-sync-manifest.json"
    manual_path = root / ".github" / "workflows" / "sync-environment.yml"
    if not manifest_path.is_file():
        errors.append(f"{name}: missing .github/env-sync-manifest.json")
        return errors
    if not manual_path.is_file():
        errors.append(f"{name}: missing .github/workflows/sync-environment.yml")
        return errors

    try:
        manifest = parse_manifest(manifest_path.read_text(encoding="utf-8"))
    except ValidationError as error:
        errors.append(f"{name}: invalid environment-sync manifest: {error}")
        return errors

    destinations = {
        target.destination_variable for target in manifest.targets
    } | {
        target.team_variable for target in manifest.targets if target.team_variable
    }
    if destinations != expected["destinations"]:
        errors.append(f"{name}: manifest destination variables do not match product contract")
    bundle_keys = {target.bundle_key for target in manifest.targets}
    if bundle_keys != expected["bundle_keys"]:
        errors.append(f"{name}: manifest bundle keys do not match product contract")

    target_pairs: dict[tuple[str, str], set[str]] = {}
    for target in manifest.targets:
        target_pairs.setdefault(
            (target.provider, target.bundle_key), set()
        ).add(target.provider_environment)
        if target.provider == "vercel" and target.destination_variable not in deploy_text:
            errors.append(
                f"{name}: Vercel destination {target.destination_variable} is absent from deploy.yml"
            )
    for (provider, bundle_key), environments in target_pairs.items():
        required = {"staging", "production"} if provider == "render" else {"preview", "production"}
        if environments != required:
            errors.append(
                f"{name}: {provider} bundle {bundle_key} must define both provider environments"
            )
    for deploy_name in expected["render_deploy_names"]:
        if deploy_name not in deploy_text:
            errors.append(f"{name}: Render manifest does not agree with deploy secret {deploy_name}")

    manual_text = manual_path.read_text(encoding="utf-8")
    combined_sync_text = manual_text + "\n" + deploy_text
    refs = SYNC_REF_RE.findall(combined_sync_text)
    if not refs or len(set(refs)) != 1:
        errors.append(f"{name}: sync callers must use one immutable central commit SHA")
    for required in (
        "vars.ENV_SYNC_MANIFEST_JSON",
        "toJSON(vars)",
        "secrets.ENV_SYNC_STAGING",
        "secrets.ENV_SYNC_PRODUCTION",
        "secrets.VERCEL_TOKEN",
    ):
        if required not in combined_sync_text:
            errors.append(f"{name}: environment-sync callers missing {required}")
    if any(target.provider == "render" for target in manifest.targets):
        if "secrets.RENDER_API_KEY" not in combined_sync_text:
            errors.append(f"{name}: Render targets require RENDER_API_KEY mapping")
    if "toJSON(secrets)" in combined_sync_text:
        errors.append(f"{name}: environment-sync callers must not serialize all secrets")
    if (
        "default: true" not in manual_text
        or 'expected_ref="refs/heads/$DISPATCH_ENVIRONMENT"' not in manual_text
        or "options: [staging, production]" not in manual_text
    ):
        errors.append(
            f"{name}: manual sync must default dry-run and guard staging/prod dispatches"
        )
    if "dry_run: false" not in deploy_text:
        errors.append(f"{name}: trusted deployment sync must apply changes before deploy")
    for dependency in ("sync-staging", "sync-production"):
        if dependency + ":" not in deploy_text:
            errors.append(f"{name}: deploy.yml missing {dependency} job")
        if not re.search(rf"needs:\s*(?:{dependency}|\[[^\]]*{dependency})", deploy_text):
            errors.append(f"{name}: deployment jobs do not depend on {dependency}")
    if "ENV_SYNC_" in ci_text:
        errors.append(f"{name}: pull-request CI must not receive environment-sync secrets")
    return errors


def validate_repo(root: Path) -> list[str]:
    errors: list[str] = []
    name = root.name
    workflow_dir = root / ".github" / "workflows"
    ci = workflow_dir / "ci.yml"
    deploy = workflow_dir / "deploy.yml"
    promote = workflow_dir / "promote.yml"
    release = workflow_dir / "release.yml"
    history = workflow_dir / "security-gitleaks-history.yml"
    rollback = workflow_dir / "rollback.yml"

    if not ci.is_file():
        errors.append(f"{name}: missing .github/workflows/ci.yml")
        ci_text = ""
    else:
        ci_text = ci.read_text(encoding="utf-8")
        if not USES_RE.search(ci_text):
            errors.append(f"{name}: ci.yml must use central @v2 reusable workflows")
        if not BRANCHES_RE.search(ci_text):
            errors.append(f"{name}: ci.yml must trigger on branches [staging, prod]")
        if SONAR_RE.search(ci_text):
            errors.append(f"{name}: ci.yml contains an active Sonar reference")

    if not deploy.is_file():
        errors.append(f"{name}: missing .github/workflows/deploy.yml")
        deploy_text = ""
    else:
        deploy_text = deploy.read_text(encoding="utf-8")
        if not re.search(r"deploy-(?:vercel|render)\.yml@v2\.1\b", deploy_text):
            errors.append(f"{name}: deploy.yml must call guarded deploy workflow@v2.1")
        if "pull-requests: read" not in deploy_text:
            errors.append(f"{name}: deploy.yml must grant pull-requests: read for the production guard")
        if "environment: staging" not in deploy_text or "environment: production" not in deploy_text:
            errors.append(f"{name}: deploy.yml must set staging and production environments")
        if not WORKFLOW_RUN_BRANCHES_RE.search(deploy_text):
            errors.append(f"{name}: deploy.yml must filter workflow_run to staging/prod")
        if "workflow_run.head_sha" not in deploy_text:
            errors.append(f"{name}: deploy.yml must deploy workflow_run.head_sha")
        if SONAR_RE.search(deploy_text):
            errors.append(f"{name}: deploy.yml contains an active Sonar reference")

    if ci_text and deploy_text:
        errors.extend(validate_env_sync(root, ci_text, deploy_text))

    if not promote.is_file():
        errors.append(f"{name}: missing .github/workflows/promote.yml")
    else:
        text = promote.read_text(encoding="utf-8")
        if "promote-to-prod.yml@v2" not in text:
            errors.append(f"{name}: promote.yml must call promote-to-prod@v2")
        if "source_branch: staging" not in text or "target_branch: prod" not in text:
            errors.append(f"{name}: promote.yml must target staging to prod")
        if "workflow_run.head_sha" not in text:
            errors.append(f"{name}: promote.yml must pass workflow_run.head_sha")

    if not release.is_file():
        errors.append(f"{name}: missing .github/workflows/release.yml")
    else:
        text = release.read_text(encoding="utf-8")
        if "release-tag.yml@v2" not in text or "target_ref: prod" not in text:
            errors.append(f"{name}: release.yml must tag prod through release-tag@v2")

    if not history.is_file():
        errors.append(f"{name}: missing .github/workflows/security-gitleaks-history.yml")
    elif "security-gitleaks-history.yml@v2" not in history.read_text(encoding="utf-8"):
        errors.append(f"{name}: history workflow must call security-gitleaks-history@v2")

    if not rollback.is_file():
        errors.append(f"{name}: missing .github/workflows/rollback.yml")
    else:
        text = rollback.read_text(encoding="utf-8")
        if not re.search(r"rollback-(?:vercel|render)\.yml@v2\.1\b", text):
            errors.append(f"{name}: rollback.yml must call guarded rollback workflow@v2.1")
        if "pull-requests: read" not in text:
            errors.append(f"{name}: rollback.yml must grant pull-requests: read for the production guard")

    for active_file in workflow_dir.glob("*.yml"):
        if active_file.name in {"security-gitleaks-history.yml"}:
            continue
        if SONAR_RE.search(active_file.read_text(encoding="utf-8")):
            errors.append(f"{name}: {active_file.name} contains an active Sonar reference")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        roots = [Path(value).resolve() for value in argv[1:]]
    else:
        workspace = Path(__file__).resolve().parents[2]
        roots = [
            workspace / "capstone-system",
            workspace / "Front-and-back",
            workspace / "PAULUS",
            workspace / "prism",
            workspace / "WOOF_V1",
        ]

    errors: list[str] = []
    for root in roots:
        if not root.is_dir():
            errors.append(f"missing repo dir: {root}")
            continue
        errors.extend(validate_repo(root))

    if errors:
        print("FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("PASS: product thin callers valid")
    for root in roots:
        print(f"  ok {root.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

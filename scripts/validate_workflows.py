#!/usr/bin/env python3
"""Structural validation of The-Team-CG reusable workflows."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
PROD_GUARD_ACTION = ROOT / ".github" / "actions" / "validate-prod-promotion" / "action.yml"

REQUIRED_FILES = {
    "ci-node.yml": [
        r"on:\s*\n\s*workflow_call:",
        r"name:\s*Reusable Node CI",
        r"audit_command",
        r"Dependency audit",
    ],
    "ci-python.yml": [
        r"on:\s*\n\s*workflow_call:",
        r"audit_command",
        r"pip-audit",
    ],
    "deploy-vercel.yml": [
        r"on:\s*\n\s*workflow_call:",
        r"environment:\s*\$\{\{\s*inputs\.environment\s*\}\}",
        r"staging\|production",
        r"VERCEL_TOKEN is required for deployment",
        r"validate-prod-promotion@v2\.1",
    ],
    "deploy-render.yml": [
        r"on:\s*\n\s*workflow_call:",
        r"secrets:\s*\n\s*RENDER_DEPLOY_HOOK_URL:\s*\n\s*description:.*\n\s*required:\s*true",
        r"environment:\s*\$\{\{\s*inputs\.environment\s*\}\}",
        r"Render deploy hook",
        r"trivy-action",
        r"validate-prod-promotion@v2\.1",
    ],
    "sync-environment.yml": [
        r"on:\s*\n\s*workflow_call:",
        r"ENV_SYNC_BUNDLE:",
        r"repository_variables_json:",
        r"ref:\s*508c9e39b9fe822cef4bdca588a9ff7ac7133cea",
        r"validate-prod-promotion@v2\.1",
        r"scripts/env_sync\.py",
    ],
    "notify.yml": [r"on:\s*\n\s*workflow_call:", r"NOTIFY_WEBHOOK_URL"],
    "release-tag.yml": [r"on:\s*\n\s*workflow_call:", r"version"],
    "security-gitleaks.yml": [r"on:\s*\n\s*workflow_call:", r"gitleaks"],
    "security-codeql.yml": [r"on:\s*\n\s*workflow_call:", r"codeql"],
    "security-gitleaks-history.yml": [
        r"on:\s*\n\s*workflow_call:",
        r"schedule:",
        r"gitleaks git",
        r"redact",
    ],
    "security-trivy.yml": [
        r"on:\s*\n\s*workflow_call:",
        r"trivy-action",
        r"HIGH,CRITICAL",
    ],
    "promote-to-prod.yml": [
        r"on:\s*\n\s*workflow_call:",
        r"staging-promotion",
        r"pulls\.create",
    ],
    "rollback-vercel.yml": [r"on:\s*\n\s*workflow_call:", r"deploy-vercel\.yml"],
    "rollback-render.yml": [r"on:\s*\n\s*workflow_call:", r"deploy-render\.yml"],
}


def main() -> int:
    errors: list[str] = []
    if not WORKFLOWS.is_dir():
        print(f"FAIL: missing {WORKFLOWS}", file=sys.stderr)
        return 1

    if not PROD_GUARD_ACTION.is_file():
        errors.append("missing production promotion guard action")
    else:
        guard_text = PROD_GUARD_ACTION.read_text(encoding="utf-8")
        for pattern in (
            r"listPullRequestsAssociatedWithCommit",
            r"base\.ref === 'prod'",
            r"merge_commit_sha === headSha",
            r"staging",
            r"hotfix/",
        ):
            if not re.search(pattern, guard_text):
                errors.append(f"validate-prod-promotion/action.yml: pattern not found: {pattern}")

    for filename, patterns in REQUIRED_FILES.items():
        path = WORKFLOWS / filename
        if not path.is_file():
            errors.append(f"missing workflow file: {filename}")
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if not re.search(pattern, text, re.MULTILINE):
                errors.append(f"{filename}: pattern not found: {pattern}")

    if (WORKFLOWS / "sonar.yml").exists():
        errors.append("sonar.yml must be removed from the active central workflow catalog")

    deploy = (WORKFLOWS / "deploy-vercel.yml").read_text(encoding="utf-8")
    render = (WORKFLOWS / "deploy-render.yml").read_text(encoding="utf-8")
    sync = (WORKFLOWS / "sync-environment.yml").read_text(encoding="utf-8")
    if "environment: ${{ inputs.environment }}" not in deploy:
        errors.append("deploy-vercel.yml must set job environment from inputs.environment")
    if "staging" not in deploy or "production" not in deploy:
        errors.append("deploy-vercel.yml must reference staging and production")
    if "context: ${{ inputs.docker_context }}" not in render:
        errors.append("deploy-render.yml must use the docker_context input without escaping")
    if "file: ${{ inputs.dockerfile }}" not in render:
        errors.append("deploy-render.yml must use the dockerfile input without escaping")
    if "tags: ${{ steps.image.outputs.image }}" not in render:
        errors.append("deploy-render.yml must use the resolved image tag without escaping")
    for forbidden in (
        "toJSON(secrets)",
        "upload-artifact",
        "GITHUB_STEP_SUMMARY",
        "GITHUB_OUTPUT",
        "set -x",
    ):
        if forbidden in sync:
            errors.append(f"sync-environment.yml contains forbidden secret-handling pattern: {forbidden}")
    if "contents: read" not in sync or "pull-requests: read" not in sync:
        errors.append("sync-environment.yml must use read-only contents and pull-request permissions")
    if "ref: ${{ github.workflow_sha }}" in sync:
        errors.append("sync-environment.yml must not use caller-scoped github.workflow_sha for central checkout")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("PASS: reusable workflows structurally valid")
    print(f"  root={ROOT}")
    for filename in sorted(REQUIRED_FILES):
        print(f"  ok {filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

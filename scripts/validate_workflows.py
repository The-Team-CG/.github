#!/usr/bin/env python3
"""Structural validation of The-Team-CG reusable workflows.

Validates the shipped YAML in this repo (not a reimplementation of CI logic):
- workflow_call entrypoints exist
- deploy workflow pins GitHub Environments staging and production
- required reusable workflow files are present
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

REQUIRED_FILES = {
    "ci-node.yml": [
        r"on:\s*\n\s*workflow_call:",
        r"name:\s*Reusable Node CI",
        r"audit_command",
        r"Dependency audit",
    ],
    "sonar.yml": [r"on:\s*\n\s*workflow_call:", r"project_key", r"SONAR_TOKEN"],
    "deploy-vercel.yml": [
        r"on:\s*\n\s*workflow_call:",
        r"environment:\s*\$\{\{\s*inputs\.environment\s*\}\}",
        r"staging\|production",
        r"environment must be staging or production",
    ],
    "ci-python.yml": [r"on:\s*\n\s*workflow_call:"],
    "notify.yml": [r"on:\s*\n\s*workflow_call:", r"NOTIFY_WEBHOOK_URL"],
    "release-tag.yml": [r"on:\s*\n\s*workflow_call:", r"version"],
}


def main() -> int:
    errors: list[str] = []
    if not WORKFLOWS.is_dir():
        print(f"FAIL: missing {WORKFLOWS}", file=sys.stderr)
        return 1

    for filename, patterns in REQUIRED_FILES.items():
        path = WORKFLOWS / filename
        if not path.is_file():
            errors.append(f"missing workflow file: {filename}")
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if not re.search(pattern, text, re.MULTILINE):
                errors.append(f"{filename}: pattern not found: {pattern}")

    deploy = (WORKFLOWS / "deploy-vercel.yml").read_text(encoding="utf-8")
    # Production path must use environment input (so environment: production can require reviewers)
    if "environment: ${{ inputs.environment }}" not in deploy.replace(" ", ""):
        # allow spacing variants already checked by regex; double-check intent:
        if "inputs.environment" not in deploy or "environment:" not in deploy:
            errors.append("deploy-vercel.yml must set job environment from inputs.environment")

    if "staging" not in deploy or "production" not in deploy:
        errors.append("deploy-vercel.yml must reference staging and production")

    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS: reusable workflows structurally valid")
    print(f"  root={ROOT}")
    for f in sorted(REQUIRED_FILES):
        print(f"  ok {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

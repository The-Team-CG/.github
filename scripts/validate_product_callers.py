#!/usr/bin/env python3
"""Validate product-repo callers against the CICG CI/CD conventions."""

from __future__ import annotations

import re
import sys
from pathlib import Path

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
    else:
        text = ci.read_text(encoding="utf-8")
        if not USES_RE.search(text):
            errors.append(f"{name}: ci.yml must use central @v2 reusable workflows")
        if not BRANCHES_RE.search(text):
            errors.append(f"{name}: ci.yml must trigger on branches [staging, prod]")
        if SONAR_RE.search(text):
            errors.append(f"{name}: ci.yml contains an active Sonar reference")

    if not deploy.is_file():
        errors.append(f"{name}: missing .github/workflows/deploy.yml")
    else:
        text = deploy.read_text(encoding="utf-8")
        if not re.search(r"deploy-(?:vercel|render)\.yml@v2\.1\b", text):
            errors.append(f"{name}: deploy.yml must call guarded deploy workflow@v2.1")
        if "pull-requests: read" not in text:
            errors.append(f"{name}: deploy.yml must grant pull-requests: read for the production guard")
        if "environment: staging" not in text or "environment: production" not in text:
            errors.append(f"{name}: deploy.yml must set staging and production environments")
        if not WORKFLOW_RUN_BRANCHES_RE.search(text):
            errors.append(f"{name}: deploy.yml must filter workflow_run to staging/prod")
        if "workflow_run.head_sha" not in text:
            errors.append(f"{name}: deploy.yml must deploy workflow_run.head_sha")
        if SONAR_RE.search(text):
            errors.append(f"{name}: deploy.yml contains an active Sonar reference")

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

#!/usr/bin/env python3
"""Validate product-repo thin callers against locked CI/CD conventions.

Reads real workflow and sonar files under product repo roots (passed as args
or discovered next to this monorepo-style workspace).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

USES_RE = re.compile(
    r"uses:\s*The-Team-CG/\.github/\.github/workflows/(ci-node|sonar|deploy-vercel|ci-python)\.yml@main"
)
BRANCHES_RE = re.compile(r"branches:\s*\[staging,\s*main\]")
ENV_STAGING = re.compile(r"environment:\s*staging")
ENV_PROD = re.compile(r"environment:\s*production")
OLD_SONAR = re.compile(r"caisteven17-code_PAULUS")
NEW_SONAR_PREFIX = re.compile(r"sonar\.projectKey=The-Team-CG_")


def validate_repo(root: Path) -> list[str]:
    errors: list[str] = []
    name = root.name
    ci = root / ".github" / "workflows" / "ci.yml"
    deploy = root / ".github" / "workflows" / "deploy.yml"
    sonar = root / "sonar-project.properties"

    if not ci.is_file():
        errors.append(f"{name}: missing .github/workflows/ci.yml")
    else:
        text = ci.read_text(encoding="utf-8")
        if not USES_RE.search(text):
            errors.append(f"{name}: ci.yml must uses: The-Team-CG/.github/... workflows")
        if not BRANCHES_RE.search(text):
            errors.append(f"{name}: ci.yml must trigger on branches [staging, main]")

    if not deploy.is_file():
        errors.append(f"{name}: missing .github/workflows/deploy.yml")
    else:
        text = deploy.read_text(encoding="utf-8")
        if "deploy-vercel.yml@main" not in text:
            errors.append(f"{name}: deploy.yml must call deploy-vercel reusable workflow")
        if not ENV_STAGING.search(text):
            errors.append(f"{name}: deploy.yml must set environment: staging")
        if not ENV_PROD.search(text):
            errors.append(f"{name}: deploy.yml must set environment: production")
        if not BRANCHES_RE.search(text):
            errors.append(f"{name}: deploy.yml must trigger on branches [staging, main]")

    if not sonar.is_file():
        errors.append(f"{name}: missing sonar-project.properties")
    else:
        text = sonar.read_text(encoding="utf-8")
        if OLD_SONAR.search(text):
            errors.append(f"{name}: still uses old personal Sonar key caisteven17-code_PAULUS")
        if not NEW_SONAR_PREFIX.search(text):
            errors.append(f"{name}: sonar.projectKey must start with The-Team-CG_")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        roots = [Path(p).resolve() for p in argv[1:]]
    else:
        # Default: sibling product repos next to workspace containing .github-org
        workspace = Path(__file__).resolve().parents[2]
        names = ["capstone-system", "Front-and-back", "PAULUS", "prism", "WOOF_V1"]
        roots = [workspace / n for n in names]

    all_errors: list[str] = []
    for root in roots:
        if not root.is_dir():
            all_errors.append(f"missing repo dir: {root}")
            continue
        all_errors.extend(validate_repo(root))

    if all_errors:
        print("FAIL")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    print("PASS: product thin callers valid")
    for root in roots:
        print(f"  ok {root.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

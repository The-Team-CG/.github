
# CICG Branch Promotion Workflows Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Move all CICG product repositories to protected staging and prod branches with full CI, automatic healthy staging promotion, manual staging-to-prod approval, exact-commit production deployment, and no SonarCloud dependency.

**Architecture:** Product repositories keep thin caller workflows. C:\Codes\cicg\.github-org owns reusable CI, security, deployment, promotion, release, and rollback workflows. Product callers use an immutable central release such as @v2. The central workflow repository remains on main. A successful staging deployment creates or updates one promotion PR, and the merge commit into prod deploys only after its own CI succeeds.

**Tech Stack:** GitHub Actions, Node.js 24, Python 3.13, npm, Node built-in test coverage, Vitest, Jest, pip-audit, Gitleaks, advisory CodeQL, Trivy, Vercel, Render, GHCR, GitHub Environments, GitHub pull requests, Prisma migrations, Supabase/Mongo provider environments.

## Global Constraints

- Product branches are staging and prod; the central reusable-workflow repository remains on main.
- Both product branches reject direct pushes and require pull requests and required checks.
- Full CI runs on pull requests and pushes targeting staging or prod.
- Staging deployment runs after successful staging push CI; production deployment runs after successful prod push CI.
- One staging-to-prod pull request is created or updated only after the exact staging commit passes deployment and smoke checks.
- The promotion pull request has a required staging-promotion readiness check tied to the exact staging SHA.
- A manual merge into prod is the production approval gate; deployment is automatic after successful prod CI.
- Node.js is version 24 with check-latest enabled; Python is version 3.13.
- Required gates are dependency audit, configured lint, configured typecheck, configured tests, coverage, build, and current-tree Gitleaks.
- Node dependency audit uses npm audit --audit-level=high; Python dependency audit uses pip-audit.
- CodeQL remains advisory when private-repository Advanced Security is unavailable.
- SonarCloud, sonar.yml, SONAR_TOKEN, sonar-project.properties, and required Sonar status checks are removed from active configuration.
- Coverage floors remain 50% lines, 50% statements, 50% functions, and 40% branches where the repository enforces coverage.
- Backend deployment precedes dependent frontend deployment and must pass health checks before frontend deployment begins.
- Database deployments use explicit forward-only migrations; production deployment never runs reset, seed, or development migration commands.
- Missing required deployment credentials, project identifiers, hooks, or health URLs fail deployment rather than producing a successful skip.
- Product callers reference an immutable central workflow release tag such as @v2, not mutable @main.
- Secrets are never committed, printed, echoed, uploaded, passed as ordinary inputs, or included in notification payloads.
- Production rollback is manual and targets a previously verified commit or image digest.
- Release tagging is manual from prod; notifications are optional and never gate delivery.

---

## File map

Central repository:

- Modify C:\Codes\cicg\.github-org\.github\workflows\ci-python.yml
- Modify C:\Codes\cicg\.github-org\.github\workflows\deploy-vercel.yml
- Modify C:\Codes\cicg\.github-org\.github\workflows\deploy-render.yml
- Modify C:\Codes\cicg\.github-org\.github\workflows\security-gitleaks-history.yml
- Modify C:\Codes\cicg\.github-org\.github\workflows\security-codeql.yml
- Modify C:\Codes\cicg\.github-org\.github\workflows\release-tag.yml
- Modify C:\Codes\cicg\.github-org\README.md
- Modify C:\Codes\cicg\.github-org\docs\CICD-SECRET-MODEL.md
- Modify C:\Codes\cicg\.github-org\docs\COVERAGE.md
- Modify C:\Codes\cicg\.github-org\docs\ENVIRONMENTS.md
- Modify C:\Codes\cicg\.github-org\docs\RENDER-SETUP.md
- Modify C:\Codes\cicg\.github-org\docs\WHAT-WE-NEED.md
- Modify C:\Codes\cicg\.github-org\docs\YOU-MUST-SET.md
- Modify both validator scripts
- Create promote-to-prod.yml, rollback-vercel.yml, and rollback-render.yml
- Delete .github/workflows/sonar.yml

Each product repository:

- Modify .github/workflows/ci.yml, deploy.yml, and release.yml.
- Create .github/workflows/promote.yml, security-gitleaks-history.yml, and rollback.yml.
- Delete sonar-project.properties.
- Rename Prism protect-main.yml to protect-prod.yml.
- Modify PAULUS/docs/CI_PIPELINE.md.

The approved design spec is C:\Codes\cicg\.github-org\docs\superpowers\specs\2026-08-10-cicg-branch-promotion-design.md. The older completed plan under docs\superpowers\plans\2026-07-25-centralized-cicd-portfolio.md remains historical context.

---

### Task 1: Harden central CI and security contracts

**Files:** central ci-python.yml, security-gitleaks-history.yml, security-codeql.yml, sonar.yml, and validate_workflows.py.

**Interfaces:** Python callers provide working_directory, python_version, install_command, audit_command, and test_command. Product history callers use workflow_call. CodeQL remains advisory. Central validation contains no Sonar requirement.

- [ ] Add audit_command with default python -m pip_audit.

~~~yaml
audit_command:
  description: Python dependency audit command; empty skips
  type: string
  required: false
  default: "python -m pip_audit"
~~~

- [ ] Install pip-audit after requirements and run the configured audit before tests.

~~~yaml
- name: Install dependency audit tool
  if: inputs.audit_command != ''
  run: python -m pip install pip-audit

- name: Dependency audit
  if: inputs.audit_command != ''
  run: eval "\${{ inputs.audit_command }}"
~~~

- [ ] Add workflow_call to the history scan while retaining workflow_dispatch, the Monday schedule, fetch-depth 0, redacted SARIF, and exit code 1.
- [ ] Preserve CodeQL continue-on-error and its explicit unavailable-plan warning.
- [ ] Delete sonar.yml and remove its required-file and Sonar pattern checks.
- [ ] Validate pip-audit, reusable history scanning, promotion, and rollback files.
- [ ] Run and commit:

~~~powershell
cd C:\Codes\cicg\.github-org
python scripts\validate_workflows.py
git diff --check
git add .github/workflows/ci-python.yml .github/workflows/security-gitleaks-history.yml .github/workflows/security-codeql.yml .github/workflows/sonar.yml scripts/validate_workflows.py
git commit -m "refactor: remove sonar and harden central security workflows"
~~~

Expected output includes PASS: reusable workflows structurally valid.

### Task 2: Correct central deployment, promotion, release, and rollback primitives

**Files:** central deploy-vercel.yml, deploy-render.yml, release-tag.yml, new promote-to-prod.yml, new rollback-vercel.yml, and new rollback-render.yml.

**Interfaces:** Vercel and Render use exact refs and fail on missing required configuration. Promotion accepts source_branch, target_branch, head_sha, and deployment_summary. Rollback accepts an explicit environment and exact target.

- [ ] Replace Vercel's successful credential-skip path with failures naming missing keys without values. Keep exact-ref checkout, vercel pull, vercel build, vercel deploy --prebuilt, and smoke testing.

~~~bash
if [ -z "$VERCEL_TOKEN" ]; then
  echo "::error::VERCEL_TOKEN is required for deployment"
  exit 1
fi
if [ -z "$ORG_ID" ]; then
  echo "::error::VERCEL_ORG_ID is required for deployment"
  exit 1
fi
if [ -z "$PROJECT_ID" ]; then
  echo "::error::VERCEL_PROJECT_ID is required for deployment"
  exit 1
fi
~~~

- [ ] Replace escaped default Render expressions with valid expressions and remove duplicate labels.

~~~yaml
- name: Build and push default image
  if: inputs.docker_target == ''
  uses: docker/build-push-action@v6
  with:
    context: \${{ inputs.docker_context }}
    file: \${{ inputs.dockerfile }}
    platforms: linux/amd64
    push: true
    tags: \${{ steps.image.outputs.image }}
    labels: |
      org.opencontainers.image.revision=\${{ inputs.ref }}
      org.opencontainers.image.source=\${{ github.server_url }}/\${{ github.repository }}
~~~

The implemented YAML must use actual GitHub expressions for those fields and must not contain a backslash before the expression opener.

- [ ] Change release-tag.yml default target_ref from main to prod.
- [ ] Create promote-to-prod.yml with workflow_call inputs source_branch default staging, target_branch default prod, head_sha required, and deployment_summary optional. Use actions/github-script@v7 with contents: write, pull-requests: write, and checks: write. Find the open PR with the source head and target base; fail if more than one exists; create one if none exists; update the existing one otherwise. Create a completed staging-promotion check for head_sha only after staging deployment and smoke succeed.
- [ ] Create rollback-vercel.yml and rollback-render.yml with workflow_dispatch inputs for environment and exact ref. Rollback preserves the healthy revision until the target passes health checks and does not run migrations, reset, or seed commands.
- [ ] Verify notify.yml skips only when NOTIFY_WEBHOOK_URL is absent, never prints webhook values, and never changes the success/failure result of CI or deployment.
- [ ] Run validation and commit:

~~~powershell
cd C:\Codes\cicg\.github-org
python scripts\validate_workflows.py
git diff --check
git add .github/workflows/deploy-vercel.yml .github/workflows/deploy-render.yml .github/workflows/release-tag.yml .github/workflows/promote-to-prod.yml .github/workflows/rollback-vercel.yml .github/workflows/rollback-render.yml
git commit -m "feat: add branch promotion and rollback workflows"
~~~

### Task 3: Update central operational docs and caller validation

**Files:** central README.md, active docs, validate_workflows.py, and validate_product_callers.py.

**Interfaces:** Docs distinguish product staging/prod from central main. No active docs contain Sonar or SONAR_TOKEN. Caller validation requires staging/prod, @v2, promotion callers, exact-SHA deployment, and no active Sonar.

- [ ] Rewrite branch and deployment tables to show PR CI, staging push CI, staging deployment, health/smoke, one promotion PR, promotion PR CI, manual prod merge, prod push CI, and production deployment.
- [ ] Remove Sonar setup, token, project, quality gate, and status references from active docs. Preserve the approved design spec and historical completed plan as records.
- [ ] Document environment-specific variables, secrets, separate runtime credentials, and visible failure for missing deployment configuration.
- [ ] Document the 50/50/50/40 coverage floor and exact product commands.
- [ ] Replace caller contracts with staging/prod and @v2.

~~~python
BRANCHES_RE = re.compile(r"branches:\s*\[staging,\s*prod\]")
WORKFLOW_RUN_BRANCHES_RE = re.compile(
    r"workflow_run[\s\S]*head_branch == ['\"](staging|prod)['\"]"
)
USES_RE = re.compile(
    r"uses:\s*The-Team-CG/\.github/\.github/workflows/"
    r"(ci-node|ci-python|deploy-vercel|deploy-render|security-gitleaks|"
    r"security-gitleaks-history|security-codeql|notify|release-tag|"
    r"promote-to-prod|rollback-vercel|rollback-render)\.yml@v2"
)
~~~

Remove required sonar-project.properties checks and reject active Sonar or central @main refs.
- [ ] Run and commit:

~~~powershell
cd C:\Codes\cicg\.github-org
python scripts\validate_workflows.py
python scripts\validate_product_callers.py C:\Codes\cicg\capstone-system C:\Codes\cicg\Front-and-back C:\Codes\cicg\PAULUS C:\Codes\cicg\prism C:\Codes\cicg\WOOF_V1
git add README.md docs scripts/validate_product_callers.py
git commit -m "docs: document staging to prod delivery policy"
~~~

### Task 4: Migrate product CI callers and remove active Sonar configuration

**Files:** each product .github/workflows/ci.yml, each sonar-project.properties, and PAULUS/docs/CI_PIPELINE.md.

**Interfaces:** CI triggers on pull requests and pushes to staging/prod, central refs use @v2, configured product commands remain required, and no Sonar job remains.

- [ ] Replace both branch trigger lists in all five CI files.

~~~yaml
on:
  pull_request:
    branches: [staging, prod]
  push:
    branches: [staging, prod]
~~~

- [ ] Change Node, Python, CodeQL, and Gitleaks refs from @main to @v2.
- [ ] Delete every Sonar job and remove Sonar from needs lists.
- [ ] Preserve current commands: capstone Node coverage; Front-and-back frontend/backend coverage; PAULUS Node workspace tests and Python audit; Prism API plus four frontend coverage commands; WOOF frontend plus backend Jest coverage.
- [ ] Delete active Sonar project files and remove Sonar from PAULUS active pipeline docs.
- [ ] Run repository-specific validation and commit in each product repository:

~~~powershell
npm run typecheck
npm run build
git add .github/workflows/ci.yml sonar-project.properties docs/CI_PIPELINE.md
git commit -m "ci: remove sonar and target staging and prod"
~~~

For repositories without root scripts, run the exact commands from their caller working directories.

### Task 5: Migrate product deployment callers

**Files:** each product .github/workflows/deploy.yml.

**Interfaces:** Deploy callers listen to successful CI workflow_run events, accept only staging/prod, pass the workflow head SHA, keep GitHub Environment names staging/production, and sequence backend before frontend.

- [ ] Replace every production branch condition with prod while preserving environment: production.

~~~yaml
if: >-
  github.event.workflow_run.conclusion == 'success' &&
  github.event.workflow_run.head_branch == 'prod'
~~~

- [ ] Keep the exact workflow-run SHA:

~~~yaml
ref: \${{ github.event.workflow_run.head_sha }}
~~~
- [ ] Change deploy-render and deploy-vercel refs from @main to @v2.
- [ ] Preserve the exact workflow_run.head_sha as the deployment ref.
- [ ] Replace Prism's not-ready skip outputs with failed checks naming missing configuration keys without values.
- [ ] Preserve backend-before-frontend sequencing for Front-and-back, PAULUS, Prism, and WOOF; keep capstone's standalone frontend deployment.
- [ ] Commit in each product repository:

~~~powershell
git add .github/workflows/deploy.yml
git commit -m "ci: deploy staging and prod from tested commits"
~~~

### Task 6: Add promotion, history-scan, and rollback callers

**Files:** create promote.yml, security-gitleaks-history.yml, and rollback.yml in all five product .github/workflows directories.

**Interfaces:** Promotion runs after successful staging deployment and calls promote-to-prod.yml@v2 with the deployment head SHA. History callers use workflow_dispatch and a weekly schedule. Rollback callers take environment and ref.

- [ ] Create each promotion caller.

~~~yaml
name: Promote staging to prod

on:
  workflow_run:
    workflows: ["Deploy"]
    types: [completed]

permissions:
  contents: write
  pull-requests: write
  checks: write

jobs:
  promote:
    if: >-
      github.event.workflow_run.conclusion == 'success' &&
      github.event.workflow_run.head_branch == 'staging'
    uses: The-Team-CG/.github/.github/workflows/promote-to-prod.yml@v2
    with:
      source_branch: staging
      target_branch: prod
      head_sha: \${{ github.event.workflow_run.head_sha }}
      deployment_summary: staging deployment and smoke checks passed
    secrets: inherit
~~~

- [ ] Create each history caller with workflow_dispatch and a weekly schedule, invoking security-gitleaks-history.yml@v2.
- [ ] Create each rollback caller with environment and ref inputs. For multi-service products, rollback backend first, prove health, then rollback frontends.
- [ ] Validate callers and commit:

~~~powershell
git add .github/workflows/promote.yml .github/workflows/security-gitleaks-history.yml .github/workflows/rollback.yml
git commit -m "ci: add promotion history scan and rollback callers"
~~~

### Task 7: Rename product production branches and enforce PR policy

**Files:** all five release.yml files, Prism protect-main renamed to protect-prod, and GitHub default/protection settings.

**Interfaces:** Releases target prod using @v2. Product prod accepts staging promotion PRs and approved hotfix/* PRs. Central main is not renamed.

- [ ] Update every release caller.

~~~yaml
uses: The-Team-CG/.github/.github/workflows/release-tag.yml@v2
with:
  version: \${{ inputs.version }}
  target_ref: prod
~~~

- [ ] Rename and update Prism's branch-policy workflow to target prod and allow only staging or hotfix/* heads.

~~~bash
case "$HEAD_REF" in
  staging|hotfix/*) echo "OK: approved production PR source" ;;
  *) echo "::error::prod only accepts staging or hotfix/*"; exit 1 ;;
esac
~~~

- [ ] Fetch each product repository and create prod from current remote main without deleting main.

~~~powershell
git -C C:\Codes\cicg\<repo> fetch origin --prune
git -C C:\Codes\cicg\<repo> show-ref --verify refs/remotes/origin/main
git -C C:\Codes\cicg\<repo> push origin origin/main:refs/heads/prod
~~~

- [ ] Set staging as default, protect staging and prod, require PRs and required checks, require Code Owner review on prod, disable force pushes/deletions, and configure merge commit for promotion PRs.
- [ ] Verify origin/prod exists, no production PR targets main, all product workflow branches use prod, and all central refs use @v2.
- [ ] Delete old remote product main only after verification, using the exact repository and branch. Keep central .github main.
- [ ] Commit release and branch-policy workflow changes.

~~~powershell
git add .github/workflows/release.yml .github/workflows/protect-prod.yml .github/workflows/protect-main.yml
git commit -m "ci: protect prod promotion branch"
~~~

### Task 8: Configure migrations, environments, secrets, and provider gates

**Files:** central Render/setup/secret docs, Prism apps/api/package.json if required, and product deployment runbooks.

**Interfaces:** GitHub Environments are staging and production. Render runs provider-owned migration commands. Prism uses npm --workspace prism-api run db:migrate:deploy backed by prisma migrate deploy.

- [ ] Verify Prism's migration script.

~~~powershell
cd C:\Codes\cicg\prism
node -e "const p=require('./apps/api/package.json'); console.log(p.scripts['db:migrate:deploy'])"
~~~

Expected output: prisma migrate deploy.
- [ ] Document the Render pre-deploy command for Prism as npm --workspace prism-api run db:migrate:deploy. Document that the other current products do not receive automatic database migrations until they expose an explicit, reviewed migration command.
- [ ] Document variable and secret names only: separate runtime credentials, Render hooks, Vercel project IDs, health URLs, and provider runtime secrets.
- [ ] Verify configuration metadata without reading secret values or .env files.
- [ ] Commit documentation/configuration changes:

~~~powershell
git add docs C:\Codes\cicg\prism\apps\api\package.json
git commit -m "docs: define environment and migration deployment gates"
~~~

### Task 9: Publish immutable central workflow release v2

**Files:** final central workflow/validator files, final product callers, and central tag v2.

**Interfaces:** Product callers resolve @v2. v2 is created only after central validation and the default Render branch correction.

- [ ] Run central validation and git diff --check.
- [ ] Search active workflow files for sonar, SONAR_TOKEN, sonar-project, @main, staging/main branch lists, and production checks against main. Expected result: no active product Sonar or @main references; central main remains.
- [ ] Create and push v2 only after review.

~~~powershell
git tag -a v2 -m "Release v2: staging to prod promotion workflows"
git push origin v2
~~~

- [ ] Verify all product callers resolve @v2.

~~~powershell
rg -n "The-Team-CG/\.github/\.github/workflows/.*@v2" C:\Codes\cicg\capstone-system\.github C:\Codes\cicg\Front-and-back\.github C:\Codes\cicg\PAULUS\.github C:\Codes\cicg\prism\.github C:\Codes\cicg\WOOF_V1\.github
~~~

### Task 10: Run local validation and staged workflow rehearsal

**Files:** no source-file changes; validate central and five product repositories.

**Interfaces:** Validators pass, product tests/builds pass without Sonar, staging and production use exact SHAs, and rollback proves health without destructive migration behavior.

- [ ] Run central and caller validation and expect PASS for both validators.
- [ ] Run product commands:
  - capstone: from capstone-system\capstone-system\unified, npm ci, npm run test:coverage, npm run build.
  - Front-and-back: from Front-End-Dashboard and Back-End, npm ci, npm run test:coverage, npm run build.
  - PAULUS: npm ci, npm run typecheck, both Node workspace coverage commands, npm run build, analytics requirements install, pip-audit.
  - Prism: npm ci, npm run typecheck, API coverage, all four frontend coverage commands, boundary check, and build.
  - WOOF: frontend coverage/build and backend Jest coverage/build.
- [ ] Run current-tree Gitleaks with redacted output where available.

~~~powershell
gitleaks detect --no-git --source C:\Codes\cicg\<repo> --redact --exit-code 1
~~~

- [ ] Rehearse staging: push a controlled change, verify CI, exact-SHA deployment, backend health, frontend smoke, exactly one promotion PR, and staging-promotion success for that SHA.
- [ ] Rehearse promotion: verify promotion PR CI, reject failing checks, manually merge after checks pass, verify prod push CI, and verify production deployment uses the merged SHA.
- [ ] Rehearse rollback: target a verified commit/image digest, verify backend health before frontend rollback, and verify no reset, seed, or rollback migration runs.
- [ ] Record acceptance evidence without committing secrets, .env files, private configuration, deploy-hook URLs, or registry credentials.

## Self-review checklist

- [ ] Every approved design decision has an implementation task.
- [ ] Product branch references distinguish staging/prod from central main.
- [ ] Sonar is removed from active workflows, validators, product configuration, and operational docs.
- [ ] Promotion readiness is tied to the exact staging SHA.
- [ ] Production deployment is gated by merged-commit CI and exact SHA.
- [ ] Missing deployment configuration cannot create a false-green deployment.
- [ ] Backend health gates dependent frontend deployment.
- [ ] Migration execution remains provider-owned and forward-only.
- [ ] Hotfixes are back-merged into staging.
- [ ] Central v2 is published only after validation.
- [ ] Every plan step contains concrete files, commands, interfaces, and expected behavior with no unresolved placeholder markers.

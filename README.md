# The-Team-CG org `.github`

Reusable GitHub Actions workflows and org defaults for **The-Team-CG**.

**Runtime:** Node.js **24** (latest patch via `check-latest`), Python **3.13**, current stable Actions majors.

## Branch model (product repos)

| Branch | Role |
|--------|------|
| `staging` | Trunk / default / pre-prod |
| `main` | Production |

## Reusable workflows

Call from product repos (path includes the double `.github`):

```yaml
jobs:
  validate:
    uses: The-Team-CG/.github/.github/workflows/ci-node.yml@v1
    with:
      working_directory: .
      node_version: "24"
      build_command: npm run build
    secrets: inherit

  sonar:
    needs: validate
    uses: The-Team-CG/.github/.github/workflows/sonar.yml@v1
    with:
      project_key: The-Team-CG_MyApp
    secrets: inherit

  deploy-staging:
    if: github.ref == 'refs/heads/staging'
    needs: [validate, sonar]
    uses: The-Team-CG/.github/.github/workflows/deploy-vercel.yml@v1
    with:
      environment: staging
      working_directory: .
      node_version: "24"
    secrets: inherit

  deploy-production:
    if: github.ref == 'refs/heads/main'
    needs: [validate, sonar]
    uses: The-Team-CG/.github/.github/workflows/deploy-vercel.yml@v1
    with:
      environment: production
      working_directory: .
      node_version: "24"
    secrets: inherit
```

| Workflow | File | Purpose |
|----------|------|---------|
| Node CI | `.github/workflows/ci-node.yml` | install / npm audit / lint / typecheck / test (+ coverage) / build |
| Python CI | `.github/workflows/ci-python.yml` | optional Python packages |
| SonarCloud | `.github/workflows/sonar.yml` | scan + quality gate wait |
| Vercel deploy | `.github/workflows/deploy-vercel.yml` | deploy + smoke (`staging` / `production`) |
| Gitleaks | `.github/workflows/security-gitleaks.yml` | secret-leak scan |
| CodeQL | `.github/workflows/security-codeql.yml` | static analysis |
| Notify | `.github/workflows/notify.yml` | Discord/Slack webhook (`NOTIFY_WEBHOOK_URL`) |
| Release tag | `.github/workflows/release-tag.yml` | semver tags `vX.Y.Z` |

See **`docs/WHAT-WE-NEED.md`** and **`docs/YOU-MUST-SET.md`**.

## GitHub Environments (prod gate)

| Environment | Behavior | Used by |
|-------------|----------|---------|
| `staging` | Auto deploy after green CI | `deploy-vercel` `environment: staging` |
| `production` | Job uses `environment: production` (required reviewers when enabled on plan) | `deploy-vercel` `environment: production` |

When Environment required reviewers are not available, use **CODEOWNERS + required PR reviews** on `main` as the human gate. See `docs/ENVIRONMENTS.md`.

## Org secrets

| Secret | Purpose |
|--------|---------|
| `SONAR_TOKEN` | SonarCloud |
| `VERCEL_TOKEN` | Vercel CLI deploy |
| `VERCEL_ORG_ID` | Vercel team/org id |
| `VERCEL_PROJECT_ID` | Default project (or per-repo) |
| `NOTIFY_WEBHOOK_URL` | Discord/Slack webhook (optional) |

If secrets are missing, Sonar / deploy / notify **skip with a warning** so pipelines stay valid offline.

Coverage practice bar: **50%** lines/functions/statements, **40%** branches (see `docs/COVERAGE.md`).

## Docs

- `docs/YOU-MUST-SET.md` â€” what humans must configure  
- `docs/WHAT-WE-NEED.md` â€” backlog (coverage, security, versioning, notifications)  
- `docs/ENVIRONMENTS.md` â€” staging/prod gates  
- `templates/` â€” Dependabot, CODEOWNERS, release dispatch  

# The-Team-CG org `.github`

Reusable GitHub Actions workflows and org defaults for **The-Team-CG**.

**Budget:** free tier first for everything (GitHub Free, Vercel Hobby limits, SonarCloud free, free webhooks). Do not add paid-only gates without an explicit upgrade decision.

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
    uses: The-Team-CG/.github/.github/workflows/ci-node.yml@main
    with:
      working_directory: .
      node_version: "22"
      build_command: npm run build
    secrets: inherit

  sonar:
    needs: validate
    uses: The-Team-CG/.github/.github/workflows/sonar.yml@main
    with:
      project_key: The-Team-CG_MyApp
    secrets: inherit

  deploy-staging:
    if: github.ref == 'refs/heads/staging'
    needs: [validate, sonar]
    uses: The-Team-CG/.github/.github/workflows/deploy-vercel.yml@main
    with:
      environment: staging
      working_directory: .
    secrets: inherit

  deploy-production:
    if: github.ref == 'refs/heads/main'
    needs: [validate, sonar]
    uses: The-Team-CG/.github/.github/workflows/deploy-vercel.yml@main
    with:
      environment: production
      working_directory: .
    secrets: inherit
```

| Workflow | File | Purpose |
|----------|------|---------|
| Node CI | `.github/workflows/ci-node.yml` | install / **npm audit** / lint / typecheck / test (+ coverage) / build |
| Python CI | `.github/workflows/ci-python.yml` | optional Python packages |
| SonarCloud | `.github/workflows/sonar.yml` | scan + quality gate wait |
| Vercel deploy | `.github/workflows/deploy-vercel.yml` | deploy with `environment: staging` or `production` |
| Notify | `.github/workflows/notify.yml` | free Discord/Slack webhook (`NOTIFY_WEBHOOK_URL`) |
| Release tag | `.github/workflows/release-tag.yml` | free semver tags `vX.Y.Z` |

See **`docs/WHAT-WE-NEED.md`** for coverage (~80%), security, versioning, notifications backlog.

## GitHub Environments (prod gate)

Configure on **each product repo** (Settings → Environments):

| Environment | Free org | Used by |
|-------------|-------------------|---------|
| `staging` | Auto deploy | `deploy-vercel` with `environment: staging` |
| `production` | Env exists; **required reviewers usually need Team+** | `deploy-vercel` with `environment: production` |

**Free org (current):** use branch protection + PR reviews / CODEOWNERS on `main` as the human gate. See `docs/ENVIRONMENTS.md`.

**If you ever pay for Team+:** Required reviewers on `production` pause the job until **Review deployments**.

### CLI notes

```bash
# Create environments (reviewers may 422 on free plan)
gh api -X PUT repos/The-Team-CG/<repo>/environments/staging
gh api -X PUT repos/The-Team-CG/<repo>/environments/production
```

## Org secrets (recommended, free)

| Secret | Purpose |
|--------|---------|
| `SONAR_TOKEN` | SonarCloud free |
| `VERCEL_TOKEN` | Vercel CLI deploy |
| `VERCEL_ORG_ID` | Vercel team/org id |
| `VERCEL_PROJECT_ID` | Default project (or set per-repo / per-job input) |
| `NOTIFY_WEBHOOK_URL` | Discord/Slack incoming webhook (optional) |

If secrets are missing, Sonar / deploy / notify **skip with a warning** so pipelines stay valid offline.

## Docs

- `docs/WHAT-WE-NEED.md` — full free-tier backlog (coverage, security, versioning, notifications)
- `docs/ENVIRONMENTS.md` — staging/prod gates on free org
- `templates/` — Dependabot, CODEOWNERS, release dispatch

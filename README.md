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
| Node CI | `.github/workflows/ci-node.yml` | install / lint / typecheck / test / build |
| Python CI | `.github/workflows/ci-python.yml` | optional Python packages |
| SonarCloud | `.github/workflows/sonar.yml` | scan + quality gate wait |
| Vercel deploy | `.github/workflows/deploy-vercel.yml` | deploy with `environment: staging` or `production` |

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

## Org secrets (recommended)

| Secret | Purpose |
|--------|---------|
| `SONAR_TOKEN` | SonarCloud |
| `VERCEL_TOKEN` | Vercel CLI deploy |
| `VERCEL_ORG_ID` | Vercel team/org id |
| `VERCEL_PROJECT_ID` | Default project (or set per-repo / per-job input) |

If secrets are missing, Sonar and deploy jobs **skip with a warning** so pipelines stay valid offline.

## Docs

See `docs/ENVIRONMENTS.md` for the approval runbook.

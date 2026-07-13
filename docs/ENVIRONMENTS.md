# Environments & production approval runbook

**Cost rule:** free tier first (GitHub Free org, free Vercel, free SonarCloud). Do not assume Team/Enterprise features.

## Environments

| Name | Deploy behavior |
|------|-----------------|
| `staging` | Automatic after CI + Sonar on push to `staging` |
| `production` | Job uses `environment: production` (label + secrets scope). **Required reviewers often need GitHub Team+** |

## Free-org reality

`The-Team-CG` is on a **free** plan. Creating production **required reviewers** returned HTTP 422. Environments still exist for naming and future use.

### Free prod gate (use this now)

1. Branch protection on `main`: require PR, ≥1 approving review, required status checks (CI).  
2. Optional **CODEOWNERS** so designated owners must approve.  
3. Optional: change prod deploy to `workflow_dispatch` only (manual “Run workflow”) for a zero-cost human gate.  
4. Staging stays auto-deploy on green CI.

### Team+ path (only if you ever upgrade)

1. Environment `production` → Required reviewers.  
2. Actions shows **Review deployments** before Vercel `--prod`.

## Setup checklist (per product repo)

1. Settings → Environments → ensure `staging`, `production` exist  
2. **Free:** branch protection + reviews on `main` (do not rely on env reviewers)  
3. **If Team+:** on `production` enable Required reviewers  
4. Optionally restrict deployment branches to `main` for `production`  
5. Optionally restrict `staging` environment to branch `staging`  
6. Org secrets (free): `SONAR_TOKEN`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`  
7. Repo secret or input `VERCEL_PROJECT_ID` for each deployable app  

## SonarCloud (free)

- Org key (default in workflow): `the-team-cg` — change via `organization` input if SonarCloud org key differs  
- Project keys: `The-Team-CG_<RepoName>` (e.g. `The-Team-CG_PAULUS`)  
- Install SonarCloud GitHub App on The-Team-CG org for PR decoration  
- Stay within free analysis limits; prefer **in-CI coverage thresholds** so quality does not depend on paid SaaS  

## Notifications (free)

Prefer Discord or Slack **incoming webhooks** (no paid bot seats required). Wire later via org secret `NOTIFY_WEBHOOK_URL`.

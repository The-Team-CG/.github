# Environments & production approval runbook

## Environments

| Name | Deploy behavior |
|------|-----------------|
| `staging` | Automatic after CI + Sonar on push to `staging` |
| `production` | Job uses `environment: production` (required reviewers when enabled) |

## Production approval

**With Environment required reviewers enabled:**

1. PR `staging` → `main` merges (CI green).  
2. Deploy workflow runs with `environment: production`.  
3. Actions shows **Review deployments**.  
4. Approver confirms → Vercel `--prod` deploy.

**Without required reviewers (plan limitation):**

1. Branch protection + **CODEOWNERS** + required PR reviews on `main`.  
2. Optional: prod deploy only via `workflow_dispatch`.  
3. Staging stays auto-deploy on green CI.

## Setup checklist (per product repo)

1. Environments `staging` and `production` exist  
2. Prefer required reviewers on `production` when the plan allows  
3. Otherwise: PR reviews + CODEOWNERS on `main`  
4. Optionally restrict production deploys to branch `main`  
5. Org secrets: `SONAR_TOKEN`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`  
6. Repo secret or input `VERCEL_PROJECT_ID` per app  

## SonarCloud

- Default organization input: `the-team-cg`  
- Project keys: `The-Team-CG_<RepoName>`  
- Install SonarCloud GitHub App on the org  

## Notifications

Set org secret `NOTIFY_WEBHOOK_URL` (Discord or Slack incoming webhook).

# Environments & production approval runbook

## Environments

| Name | Deploy behavior |
|------|-----------------|
| `staging` | Automatic after CI + Sonar on push to `staging` |
| `production` | Job waits for **Required reviewers** before Vercel `--prod` deploy |

## How manual prod approval works

1. PR `staging` → `main` merges (CI green).
2. Deploy workflow runs job with `environment: production`.
3. GitHub Actions shows **Review deployments**.
4. Approver confirms → `deploy-vercel` continues.

This is a workflow Environment gate, not a chat-only process.

## Setup checklist (per product repo)

1. Settings → Environments → create `staging`, `production`
2. On `production`: enable **Required reviewers** (add org admins/team)
3. Optionally restrict deployment branches to `main` for `production`
4. Optionally restrict `staging` environment to branch `staging`
5. Ensure org secrets exist: `SONAR_TOKEN`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`
6. Set repo secret or input `VERCEL_PROJECT_ID` for each deployable app

## SonarCloud

- Org key (default in workflow): `the-team-cg` — change via `organization` input if SonarCloud org key differs
- Project keys: `The-Team-CG_<RepoName>` (e.g. `The-Team-CG_PAULUS`)
- Install SonarCloud GitHub App on The-Team-CG org for PR decoration

# CICG workflow delivery status

## Centralized workflow model

| Area | Status |
|---|---|
| Central reusable Node/Python CI | Implemented |
| Dependency audit and coverage artifacts | Implemented |
| Gitleaks current-tree and history workflows | Implemented/in migration |
| Advisory CodeQL | Implemented |
| Vercel exact-SHA deployment and smoke | Implemented/in migration |
| Render exact-SHA image deployment, Trivy, and health | Implemented/in migration |
| Staging-to-prod PR promotion | Implemented/in migration |
| Manual exact-target rollback | Implemented/in migration |
| SonarCloud | Removed |
| Provider secrets and project configuration | Operator setup required |
| Branch rename and branch protection | Operator/repository migration required |

## Runtime defaults

| Tool | Version |
|---|---|
| Node.js | 24 with check-latest |
| Python | 3.13 |
| actions/checkout | v7 |
| actions/setup-node | v6 |
| actions/setup-python | v5 |
| CodeQL action | v3 |

## Required delivery gates

Dependency audit, configured lint, typecheck, tests, coverage, build, current-tree Gitleaks, and exact-SHA deployment checks are required. CodeQL is advisory when private Advanced Security is unavailable. Missing deployment configuration fails deployment. Notifications are optional.

See README.md, ENVIRONMENTS.md, RENDER-SETUP.md, and YOU-MUST-SET.md for setup and operator steps.

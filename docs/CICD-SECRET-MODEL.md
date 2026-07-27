# CI/CD secret and deployment model

## What belongs where

Secret values are never committed, echoed, uploaded as artifacts, or passed as ordinary workflow inputs.

| Secret or value | Storage location | Safe exposure |
|---|---|---|
| VERCEL_TOKEN and VERCEL_ORG_ID | GitHub organization secret | Environment variables inside the reusable Vercel workflow only |
| VERCEL_PROJECT_ID_* | GitHub repository or organization variable | Non-secret project identifier |
| RENDER_*_DEPLOY_HOOK_URL | GitHub repository or organization secret | POST target only; never printed |
| *_API_*_URL health values | GitHub repository variable | URL used for smoke checks |
| DATABASE_URL, service-role keys, JWT signing keys, SMTP/API tokens | Render service environment secret | Runtime process environment only |
| NEXT_PUBLIC_* values | Vercel Preview or Production environment variable | Only publish values that are intentionally browser-visible |

## Workflow rules

- Pull requests run tests, dependency audit, Gitleaks, CodeQL, and Sonar; they do not deploy.
- A deployment workflow starts only from a successful CI workflow on staging or main.
- The deploy workflow checks out workflow_run.head_sha, so the deployed source is the commit that passed CI.
- Backend images are built in GitHub Actions, scanned with Trivy for HIGH/CRITICAL vulnerabilities, pushed to GHCR with the commit tag, and deployed to Render by an environment-scoped deploy hook.
- Render is the backend runtime for this portfolio. AWS and Google Cloud are not required.
- Production GitHub Environment reviewers remain the final deployment gate.
- Logs may show names, commit IDs, image digests, status codes, and URLs that are already public. They must not show secret values, authorization headers, or .env contents.

## Human setup still required

Create the Vercel projects, Render services, GitHub environments, repository variables, organization secrets, and repository secrets described in RENDER-SETUP.md and YOU-MUST-SET.md. The application workflows intentionally cannot create or print those values.

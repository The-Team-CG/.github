# Centralized CI/CD Portfolio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver one gated CI/CD model for all The-Team-CG products: every frontend deploys independently to Vercel, every required backend deploys to Render, tests and security gates run before deployment, and no AWS or Google Cloud runtime is introduced.

**Architecture:** GitHub Actions in `The-Team-CG/.github` owns reusable CI, security, Vercel, Render, smoke, and notification workflows. Product repositories keep their existing structure and provide thin callers. Vercel hosts browser-facing apps; Render hosts long-running Node/Python/Docker backends; existing Supabase or Mongo data services remain product-owned with separate staging and production credentials.

**Tech Stack:** GitHub Actions, Node.js 24, Python 3.13, npm, Vitest, Jest, Node built-in tests, SonarCloud, gitleaks, CodeQL, Trivy, Vercel, Render, GHCR, Supabase, MongoDB, Prisma, NestJS, Express, FastAPI.

## Global Constraints

- Do not use AWS or Google Cloud for new compute, container registry, database, secret, or deployment infrastructure.
- Never place secret values in Git, plans, workflow YAML, Dockerfiles, issue comments, terminal output, screenshots, or chat.
- GitHub Actions stores deployment credentials only; Vercel and Render store application runtime secrets.
- `NEXT_PUBLIC_*`, Supabase publishable/`anon` keys, and frontend API URLs are public values and must never be treated as private credentials.
- Supabase secret/`service_role` keys, database URLs, JWT/session secrets, payment keys, email keys, and provider tokens are backend-only.
- `staging` is the integration environment; `main` is production; production deploys require the existing PR/CODEOWNERS gate and Environment approval when available.
- Every deployment is tied to the exact CI-tested commit SHA.
- Every backend has a non-authenticated health endpoint that returns HTTP 200 without exposing configuration or data.
- Database changes use explicit, reviewable migrations; deploys never run development reset commands or seed production data.
- Backend deploy failures preserve the previous healthy revision and support rollback by image digest or commit SHA.

---

## Current Baseline and Gaps

The central workflow repository is `C:\Codes\cicg\.github-org`.

- `.github-org/.github/workflows/ci-node.yml` currently performs npm audit as an advisory warning; high/critical dependency findings must become a hard gate.
- `.github-org/.github/workflows/security-gitleaks.yml` hard-fails on current working-tree findings but intentionally does not scan historical commits; a scheduled redacted history scan is required.
- CodeQL is present but remains advisory when GitHub Advanced Security is unavailable on private repositories.
- There is no reusable Render deployment workflow.
- Current product deploy callers deploy only frontends and are triggered independently from CI.
- Prism deploys only `apps/client`; `apps/event`, `apps/guest`, and `apps/supplier` need separate Vercel deployments.
- Prism uses Vitest. Its API and client coverage run in CI, while event, guest, and supplier have tests but lack coverage scripts.
- WOOF has Jest coverage available, but its caller currently runs the smaller Node practice suite instead of the full backend Jest coverage command.
- PAULUS contains AWS-specific warehouse migration/configuration paths; the agreed deployment plan must not depend on them.

## Portfolio Target State

| Product | Frontends | Backend runtime | Render services | Data boundary |
|---|---|---|---|---|
| `capstone-system` | `capstone-system/unified` on Vercel | None | None | Existing Supabase only; no invented API service |
| `Front-and-back` | `Front-End-Dashboard` on Vercel | Express | `front-and-back-api-staging`, `front-and-back-api-production` | Existing Supabase/Postgres configuration, separate environment values |
| `PAULUS` | `src/frontend` on Vercel | NestJS gateway plus FastAPI analytics | `paulus-api-*`, `paulus-analytics-*` | Supabase operational and analytics paths; retire AWS warehouse dependency |
| `prism` | `apps/client`, `apps/event`, `apps/guest`, `apps/supplier` on four Vercel projects | Shared NestJS + Prisma API | `prism-api-staging`, `prism-api-production` | Separate Supabase/Postgres staging and production databases |
| `WOOF_V1` | `frontend` on Vercel; mobile remains separate | NestJS | `woof-api-staging`, `woof-api-production` | Existing Mongo/Supabase services with separate staging and production credentials |

## Secret Ownership Contract

| Secret class | Store | Examples | Must not appear in |
|---|---|---|---|
| CI/deploy credentials | GitHub organization or Environment secrets | `SONAR_TOKEN`, `VERCEL_TOKEN`, `RENDER_DEPLOY_HOOK_URL` | product `.env`, logs, plan files |
| Frontend public configuration | Vercel project variables | `NEXT_PUBLIC_API_BASE_URL`, publishable/anon key | backend-only secret stores are not required |
| Frontend server-only configuration | Vercel project variables without `NEXT_PUBLIC_` | server-only integration token when a Next server route truly needs it | browser bundles |
| Backend runtime secrets | Render service Environment variables | `DATABASE_URL`, `DIRECT_URL`, `JWT_SECRET`, email/payment/provider keys | GitHub workflow output, image layers, frontend variables |
| Database/service credentials | Supabase, Mongo provider, or Render service settings | database passwords, secret API keys, service-role keys | source code and Docker build arguments |
| Local development values | ignored `.env.local`/`.env` files or `vercel env run` | developer-only configuration | Git, chat, screenshots |

Secret verification reports names and presence only. It must never retrieve or print values. If gitleaks finds a live key, stop deployment, revoke/rotate it at the owning provider, then clean history if required.

## Implementation Tasks

### Task 1: Update the central policy and operator runbooks

**Files:**
- Modify: `.github-org/docs/WHAT-WE-NEED.md`
- Modify: `.github-org/docs/COVERAGE.md`
- Modify: `.github-org/docs/ENVIRONMENTS.md`
- Modify: `.github-org/docs/YOU-MUST-SET.md`
- Modify: `C:\Codes\cicg\CENTRALIZED-CICD-PLAN.md`
- Modify: `C:\Codes\cicg\WHAT-WE-NEED.md`
- Modify: `C:\Codes\cicg\COVERAGE.md`
- Modify: `C:\Codes\cicg\YOU-MUST-SET.md`

**Interfaces:**
- Produces the canonical product matrix, Render service matrix, secret ownership rules, coverage policy, and rollout order used by all later tasks.

- [ ] Replace the current “API host depends on the product” wording with Render as the default backend host, Supabase/Mongo as existing data services, and no AWS/Google Cloud runtime.
- [ ] Add all four Prism Vercel projects and remove the single-project `prism-client` assumption.
- [ ] Document that `deploy.yml` runs from successful CI for the exact `workflow_run.head_sha`, not from the latest branch tip.
- [ ] Document the exact GitHub secret names, Vercel variable classes, Render service variable classes, and the no-value-output rule.
- [ ] Record that gitleaks findings block deployment, audit high/critical findings block after remediation policy is enabled, and CodeQL remains advisory only when the GitHub plan cannot enforce it.
- [ ] Replace the current partial test table with Vitest for Prism, Jest for WOOF backend, Node built-in tests where already used, and explicit coverage commands for every product package.
- [ ] Add a final operator checklist: create services, add environment variables by name, configure Render registry credentials, verify health URLs, run staging, promote to production.
- [ ] Run `rg -n -i "aws|gcloud|google cloud|api host depends|prism-client" .github-org/docs C:\\Codes\\cicg\\CENTRALIZED-CICD-PLAN.md` and remove obsolete deployment claims while preserving historical migration notes that are explicitly marked retired.

### Task 2: Harden reusable CI and secret scanning

**Files:**
- Modify: `.github-org/.github/workflows/ci-node.yml`
- Modify: `.github-org/.github/workflows/ci-python.yml`
- Modify: `.github-org/.github/workflows/security-gitleaks.yml`
- Create: `.github-org/.github/workflows/security-gitleaks-history.yml`
- Modify: `.github-org/.github/workflows/security-codeql.yml`

**Interfaces:**
- Consumes product-provided `lint_command`, `typecheck_command`, `test_command`, and `audit_command` inputs.
- Produces hard-fail CI results for lint, tests, high/critical npm vulnerabilities, and current-tree secret findings.

- [ ] Change the Node dependency audit step from warning-only to `npm audit --audit-level=high` with the command exit code preserved.
- [ ] Keep install/build/test placeholder variables synthetic and public-looking; do not pass production secrets to CI validation jobs.
- [ ] Add Python dependency auditing with `pip-audit` after requirements installation, failing on unresolved vulnerabilities.
- [ ] Keep current-tree gitleaks scanning redacted and hard-failing; prohibit `printenv`, `env`, shell tracing, and raw file dumps in all reusable workflows.
- [ ] Add a weekly/manual full-history gitleaks workflow using `fetch-depth: 0`, redacted output, an artifact containing only the redacted report, and a security-owner notification on findings.
- [ ] Keep CodeQL language input defaulted to `javascript-typescript`; report unavailable Advanced Security as an explicit advisory status rather than silently claiming a completed scan.
- [ ] Add dependency-review documentation for pull requests and require a documented exception for any high/critical dependency that cannot be removed immediately.
- [ ] Validate the reusable workflows with `python .github-org/scripts/validate_workflows.py` and ensure no workflow step prints a secret-bearing environment object.

### Task 3: Add reusable backend image scanning and Render deployment

**Files:**
- Create: `.github-org/.github/workflows/security-trivy.yml`
- Create: `.github-org/.github/workflows/deploy-render.yml`
- Modify: `.github-org/.github/workflows/deploy-vercel.yml`
- Modify: `.github-org/scripts/validate_product_callers.py`

**Interfaces:**
- `security-trivy.yml` accepts `image` and returns a failing result for unfixed HIGH or CRITICAL OS/library vulnerabilities.
- `deploy-render.yml` accepts `environment`, `image_name`, `health_url`, and `deploy_hook_secret_name`; it builds the exact commit, scans it, pushes to GHCR, triggers the Render deploy hook with the immutable digest, polls the health URL, and exposes only the image digest and deployment status as outputs.
- `deploy-vercel.yml` gains a `ref` input and checks out that exact commit before `vercel pull`, `vercel build`, and `vercel deploy`.

- [ ] Build backend images for `linux/amd64` with commit-SHA tags and immutable digests.
- [ ] Authenticate to GHCR using the ephemeral GitHub Actions token with `packages: write`; do not add a personal registry password to GitHub secrets.
- [ ] Configure Render image-backed services to read GHCR images and keep the registry pull credential inside Render, never in repository files or workflow logs.
- [ ] Trigger Render through a per-environment deploy hook stored as a GitHub Environment secret; pass the image digest without printing the hook URL.
- [ ] Poll the configured health URL and fail the workflow if the service does not return HTTP 200 within the defined retry window.
- [ ] Add rollback documentation using the last successful image digest and Render deploy history.
- [ ] Extend caller validation to require exact-commit deployment, a backend health URL when a backend exists, separate staging/production service identifiers, and no AWS/GCP deploy references.

### Task 4: Make deploy workflows wait for successful CI

**Files:**
- Modify: `capstone-system/.github/workflows/deploy.yml`
- Modify: `Front-and-back/.github/workflows/deploy.yml`
- Modify: `PAULUS/.github/workflows/deploy.yml`
- Modify: `prism/.github/workflows/deploy.yml`
- Modify: `WOOF_V1/.github/workflows/deploy.yml`

**Interfaces:**
- Every product deploy workflow triggers from `workflow_run` for the named `CI` workflow, accepts only `success`, and deploys `workflow_run.head_sha` from `staging` or `main`.
- Frontend jobs call `deploy-vercel.yml`; backend jobs call `deploy-render.yml`.

- [ ] Remove independent push-triggered deploys that can run while CI is failing.
- [ ] Filter `workflow_run.head_branch` to `staging` and `main` and reject all other branches.
- [ ] Pass the exact `workflow_run.head_sha` through the reusable deployment workflow.
- [ ] Keep staging automatic and production behind the existing `production` Environment gate.
- [ ] Make backend deployment complete before frontend deployment for products with an API, so frontend environment URLs point to a healthy backend.
- [ ] Add a final notification job that reports product, environment, commit SHA, frontend URLs, backend health status, and rollback digest without exposing configuration values.

### Task 5: Complete test and coverage wiring for every product

**Files:**
- Modify: `prism/apps/client/package.json`
- Modify: `prism/apps/event/package.json`
- Modify: `prism/apps/guest/package.json`
- Modify: `prism/apps/supplier/package.json`
- Modify: `prism/apps/client/vitest.config.ts`
- Modify: `prism/apps/event/vitest.config.ts`
- Modify: `prism/apps/guest/vitest.config.ts`
- Modify: `prism/apps/supplier/vitest.config.ts`
- Modify: `prism/.github/workflows/ci.yml`
- Modify: `WOOF_V1/.github/workflows/ci.yml`
- Modify: `Front-and-back/.github/workflows/ci.yml`
- Modify: `PAULUS/.github/workflows/ci.yml`
- Modify: `capstone-system/.github/workflows/ci.yml`

**Interfaces:**
- Prism frontend packages expose `test:coverage` using Vitest with V8 coverage and thresholds of lines/statements/functions 50% and branches 40%.
- WOOF backend CI uses `npm run test:cov` for Jest and retains the practice suite as a separate smoke-level test if useful.

- [ ] Add `test:coverage: "vitest run --coverage"` to Prism event, guest, and supplier packages.
- [ ] Add V8 coverage configuration to all four Prism frontend Vitest configs with the common practice thresholds.
- [ ] Change Prism CI to run API coverage plus coverage for client, event, guest, and supplier.
- [ ] Change WOOF CI to run the full Jest coverage command and preserve the existing e2e command as an explicit non-production test target.
- [ ] Verify Front-and-back frontend/backend commands exist and add missing test scripts before making them required gates.
- [ ] Verify PAULUS frontend/backend tests and Python tests; add `pytest`/coverage only where a real suite exists, otherwise retain build/typecheck and record the missing suite as a tracked coverage gap.
- [ ] Keep capstone’s Node built-in/practice coverage command and add gitleaks to its caller.
- [ ] Upload all coverage artifacts and configure Sonar paths for each package without uploading environment files.
- [ ] Run the exact product commands locally before publishing each caller change.

### Task 6: Deploy all Prism frontends and the shared API

**Files:**
- Modify: `prism/.github/workflows/ci.yml`
- Modify: `prism/.github/workflows/deploy.yml`
- Modify: `prism/apps/api/package.json`
- Modify: `prism/Dockerfile`
- Modify: `prism/README.md`
- Modify: `prism/apps/api/.env.example`

**Interfaces:**
- Vercel project inputs: `PRISM_CLIENT`, `PRISM_EVENT`, `PRISM_GUEST`, and `PRISM_SUPPLIER` project IDs supplied as non-secret GitHub Environment variables.
- Render image: `ghcr.io/the-team-cg/prism-api:<commit-sha>` with a per-environment deploy hook.
- Migration command: `npm --workspace prism-api run db:migrate:deploy`.
- Health URL: `/health`.

- [ ] Add the missing Prism frontend coverage scripts/configuration before changing deployment.
- [ ] Add four matrix Vercel jobs with roots `apps/client`, `apps/event`, `apps/guest`, and `apps/supplier`.
- [ ] Give each frontend its own Vercel project and environment variables while keeping the shared API base URL environment-specific.
- [ ] Add `db:migrate:deploy` that runs only `prisma migrate deploy`; do not use `db:migrate`, `db:reset`, or `migrate dev` in Render.
- [ ] Build the existing Docker `api` target, scan it with Trivy, publish it to GHCR, and deploy the digest to Render.
- [ ] Configure Prisma runtime secrets only in Render and keep `.env.example` values as placeholders.
- [ ] Smoke-test `/health` and one representative API route after backend deployment, then smoke-test all four frontend roots.
- [ ] Document local production startup and the separation between the four browser apps and one shared API.

### Task 7: Add backend packaging and health contracts for the other products

**Files:**
- Create: `Front-and-back/Back-End/Dockerfile`
- Modify: `Front-and-back/Back-End/src/config/env.ts`
- Modify: `Front-and-back/.github/workflows/ci.yml`
- Create: `PAULUS/Dockerfile.backend`
- Create: `PAULUS/Dockerfile.analytics`
- Modify: `PAULUS/package.json`
- Modify: `PAULUS/src/analytics/app/config.py`
- Modify: `PAULUS/.github/workflows/ci.yml`
- Create: `WOOF_V1/backend/Dockerfile`
- Modify: `WOOF_V1/backend/src/app.controller.ts`
- Modify: `WOOF_V1/backend/src/main.ts`
- Modify: `WOOF_V1/.github/workflows/ci.yml`

**Interfaces:**
- Front-and-back backend image starts `node dist/server.js` and exposes `/api/health`.
- PAULUS backend image starts the compiled API gateway on `PORT` and exposes `/health`; analytics image starts FastAPI on `PORT` and exposes `/health`.
- WOOF backend image starts `node dist/main` and exposes `/api/health`.

- [ ] Build the Front-and-back Express image with Node 24, non-root runtime, `npm ci`, `npm run build`, and `npm start`.
- [ ] Ensure Front-and-back reads `PORT` from the Render environment and its health route does not require database credentials.
- [ ] Build the PAULUS Node gateway without `dotenv` file-path assumptions so Render variables are read directly from `process.env`.
- [ ] Build the PAULUS FastAPI service from `src/analytics/requirements.txt` and use `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- [ ] Remove the production dependency on AWS RDS, AWS migration scripts, and AWS warehouse flags; retain only provider-neutral analytics configuration backed by Supabase or Render Postgres after data ownership is reviewed.
- [ ] Do not run the existing AWS migration directory in staging or production.
- [ ] Add a WOOF `/api/health` endpoint returning a fixed `{ "status": "ok" }` payload and use `PORT` from Render.
- [ ] Configure WOOF Mongo/Supabase credentials only in Render, with separate staging and production databases.
- [ ] Build and smoke-test each image locally with Docker before connecting the Render service.

### Task 8: Provision Render services and Vercel projects without exposing values

**Files:**
- Modify: `.github-org/docs/YOU-MUST-SET.md`
- Modify: `.github-org/docs/ENVIRONMENTS.md`
- Modify: each product repository’s deployment runbook or README listed in the caller task

**Interfaces:**
- GitHub Environment names: `staging`, `production`.
- Vercel project IDs are GitHub Environment variables, not secrets.
- Render deploy hook URLs are GitHub Environment secrets.

- [ ] Create the five Vercel project groups: capstone one, Front-and-back one, PAULUS one, Prism four, and WOOF one.
- [ ] Create Render staging and production services using the exact service names in the target-state table.
- [ ] Configure Render image-backed services to pull the matching GHCR image and store the GHCR pull credential inside Render.
- [ ] Add Render health paths and pre-deploy commands in the provider UI; keep secret values out of `render.yaml`, GitHub, and the repository.
- [ ] Add only secret names to GitHub Environment configuration and verify presence by metadata without reading values.
- [ ] Configure Vercel Preview and Production variables separately; only public API URLs and publishable keys may be exposed to frontend bundles.
- [ ] Create separate Supabase/Mongo staging and production projects or databases and verify that staging credentials cannot access production data.
- [ ] Record the exact backend URLs and frontend project IDs in the runbook, never the secret values.

### Task 9: Add migration, smoke, rollback, and operational verification

**Files:**
- Create: `.github-org/.github/workflows/smoke-backend.yml` if reusable backend smoke is not contained in `deploy-render.yml`
- Modify: `.github-org/.github/workflows/notify.yml`
- Modify: product deployment workflows from Task 4
- Modify: product backend READMEs from Task 7

**Interfaces:**
- Backend smoke input: `health_url`, `expected_status=200`, and one safe public route.
- Rollback input: service identifier and previously successful image digest or commit SHA.

- [ ] Run Prism `prisma migrate deploy` from the Render pre-deploy command with production approval and no reset/seed behavior.
- [ ] Define migration ownership for each non-Prism product: tracked Supabase SQL for capstone/Front-and-back/PAULUS, Mongo index/setup scripts for WOOF, and no automatic destructive scripts.
- [ ] Make backend health smoke run before frontend deploy jobs.
- [ ] Smoke-test representative public pages for every Vercel project and verify the frontend points at the matching environment API.
- [ ] On deploy failure, report the failing stage and preserve the previous healthy service; do not automatically retry destructive migrations.
- [ ] Document rollback to the previous image digest/commit and verify rollback health before reopening traffic.
- [ ] Send notifications containing repository, commit SHA, environment, service/app name, result, and health URL status only.

### Task 10: Validate, publish, and hand off

**Files:**
- Modify: `.github-org/scripts/validate_product_callers.py`
- Modify: `.github-org/README.md`
- Modify: `.github-org/docs/WHAT-WE-NEED.md`

- [ ] Run central workflow validation:

```powershell
python .github-org/scripts/validate_workflows.py
python .github-org/scripts/validate_product_callers.py
```

- [ ] Run gitleaks against the working tree with redaction and confirm no secret values appear in output.
- [ ] Run each product’s CI commands on the exact branch/commit that will be published.
- [ ] Push central workflow changes first and verify reusable workflows are callable from product repositories.
- [ ] Publish product caller changes one repository at a time, starting with Front-and-back, then WOOF, PAULUS, capstone-system, and Prism.
- [ ] Run staging deployments and verify CI → security → Sonar → backend → backend smoke → frontend matrix → frontend smoke → notify.
- [ ] Promote only after staging acceptance and confirm production Environment approval behavior.
- [ ] Verify that `git status` and workflow artifacts contain no `.env`, secret report, registry credential, deploy hook URL, or generated private configuration.
- [ ] Commit central changes with `feat(ci): standardize portfolio frontend and Render backend delivery` and product changes with repository-specific conventional commits.

## Verification Matrix

| Area | Passing evidence |
|---|---|
| Frontends | Every declared Vercel project deploys from the exact SHA and returns a successful smoke response |
| Backends | Every required Render service is healthy on `/health` or `/api/health` |
| Tests | Product-specific Vitest/Jest/Node/Python commands pass and coverage artifacts upload |
| Dependencies | High/critical npm and Python audit findings fail CI unless explicitly remediated |
| Secrets | Gitleaks passes; no values appear in logs, artifacts, plan files, or images |
| Static security | CodeQL and Sonar results are visible; CodeQL limitation is explicit when plan features prevent enforcement |
| Containers | Backend images are built for `linux/amd64`, Trivy-clean at configured severity, and deployed by digest |
| Data | Staging and production credentials/databases are separate; migration history is consistent |
| Promotion | Production requires the configured review gate and can roll back to a verified previous revision |
| Provider boundary | No new AWS/GCP service, credential, registry, or deploy command exists in workflows or runtime configuration |

## Execution Order

1. Central docs and secret contract.
2. Central CI/security hardening.
3. Reusable Vercel/Render workflows.
4. Product CI caller/test updates.
5. Backend Docker/health contracts.
6. Render and Vercel provider provisioning.
7. Staging deployments and smoke verification.
8. Production promotion and rollback verification.

## Self-Review Checklist

- [ ] All five products have a frontend deployment decision.
- [ ] All required backends have a Render service decision.
- [ ] Prism has four frontend projects and one shared API service.
- [ ] Jest, Vitest, Node built-in tests, and Python checks are represented without forcing one runner.
- [ ] Secret values are never requested, copied, printed, or committed.
- [ ] AWS/GCP are excluded from new compute and data-plane decisions, including PAULUS’s AWS warehouse path.
- [ ] CI gates deployment by exact commit SHA.
- [ ] Migrations, health checks, rollback, and operator setup are explicit.
- [ ] No plan step depends on an unspecified host, command, secret value, or hidden manual action.

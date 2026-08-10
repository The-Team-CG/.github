# Environment Secret Synchronization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Synchronize explicitly bundled GitHub Repository Secrets into the correct Render services and Vercel projects before trusted staging and production deployments, without exposing secret values.

**Architecture:** The central `.github` repository owns a standard-library Python synchronization engine, a reusable workflow, validation, tests, and logging policy. Each product repository owns a value-free manifest template, two fixed bundle secrets (`ENV_SYNC_STAGING` and `ENV_SYNC_PRODUCTION`), a manual dry-run-first caller, and trusted push deployment jobs that call the central workflow before provider deployment. Product callers pin the reusable workflow to the exact central implementation commit SHA.

**Tech Stack:** GitHub Actions, Python 3.14-compatible standard library, `unittest`, Render REST API, Vercel REST API, JSON repository variables and secrets.

## Global Constraints

- Synchronization runs only from trusted `staging` and `prod` deployment flows or an explicitly dispatched workflow.
- Pull requests and feature branches never receive provider credentials or runtime secret bundles.
- Production synchronization uses the same exact merged-promotion SHA guard as production deployment.
- Manual production synchronization must be dispatched from `prod` and validate the exact selected commit.
- Product callers reference the central sync workflow by a full immutable commit SHA.
- GitHub secrets are fixed: `ENV_SYNC_STAGING`, `ENV_SYNC_PRODUCTION`, `RENDER_API_KEY`, and `VERCEL_TOKEN`.
- `ENV_SYNC_MANIFEST_JSON` and provider destination IDs are repository variables; secret values never appear in variables or committed files.
- Render updates read the complete current list, preserve unmanaged keys, merge managed keys, and replace the complete list.
- Vercel maps CICG `staging` to `preview` and CICG `production` to `production`, writes sensitive variables with upsert semantics, and never reads decrypted values.
- Validation finishes before any provider mutation. Dry-run performs no provider requests.
- Logs, errors, artifacts, outputs, summaries, and request diagnostics never contain secret values, authorization headers, request bodies, deploy hooks, or provider response bodies.
- `NEXT_PUBLIC_` values may be browser-visible and must not contain credentials, private tokens, or database URLs.
- Existing Render deploy hooks and Vercel deployment workflows remain responsible for creating a new deployment after synchronization.
- Existing uncommitted files are preserved, especially the five untracked `apps/agent-*` directories in `C:\Codes\cicg\prism`.

---

## Verified branch matrix

| Repository | Implementation branch | Verified base |
| --- | --- | --- |
| `.github-org` | `codex-cicg-workflow-implementation` | `origin/main` at `9b2103a` plus approved design `d791659` |
| `capstone-system` | `codex-cicg-workflow-implementation` | `origin/staging` at `29515cf` |
| `Front-and-back` | `codex-cicg-workflow-implementation` | `origin/staging` at `26356f7` |
| `PAULUS` | `codex-cicg-workflow-implementation` | `origin/staging` at `255d933` |
| `prism` | `codex-cicg-workflow-implementation` | `origin/staging` at `d7bbdb2` |
| `WOOF_V1` | `codex-cicg-workflow-implementation` | `origin/staging` at `e2b7fb4` |

All five product implementation branches were fetched and verified as zero commits behind their corresponding `origin/staging` refs before this plan was written.

## File map

Central repository:

- Create `scripts/env_sync.py`: parse, validate, plan, redact, and synchronize Render/Vercel targets.
- Create `tests/test_env_sync.py`: unit and adapter contract tests with an in-memory HTTP transport.
- Create `.github/workflows/sync-environment.yml`: reusable trusted sync workflow with production guard.
- Modify `scripts/validate_workflows.py`: validate the reusable workflow and secret-safe structure.
- Modify `scripts/validate_product_callers.py`: validate each product manifest template and caller/deployment agreement.
- Modify `docs/CICD-SECRET-MODEL.md`, `docs/ENVIRONMENTS.md`, `docs/YOU-MUST-SET.md`, and `README.md`: operator setup, limits, dry run, rollout, and failure behavior.

Each of `capstone-system`, `Front-and-back`, `PAULUS`, `prism`, and `WOOF_V1`:

- Create `.github/env-sync-manifest.json`: value-free canonical manifest copied to `ENV_SYNC_MANIFEST_JSON`.
- Create `.github/workflows/sync-environment.yml`: manual dry-run-first staging/production caller.
- Modify `.github/workflows/deploy.yml`: add staging and production sync jobs before deployments.

---

### Task 1: Implement manifest and bundle validation with TDD

**Files:**
- Create: `tests/test_env_sync.py`
- Create: `scripts/env_sync.py`

**Interfaces:**
- Produces `parse_manifest(text: str) -> Manifest`.
- Produces `build_sync_plan(manifest, bundle_text, variables_text, cicg_environment, target_name=None) -> SyncPlan`.
- `Manifest` supports version `1`, root `strict` defaulting to `True`, unique targets, `render` environments `staging|production`, and `vercel` environments `preview|production`.
- `SyncPlan` contains only the selected CICG environment and an optional selected logical target.

- [ ] **Step 1: Add failing schema and bundle tests.** Cover malformed JSON, unsupported version, duplicate target names, invalid provider/environment combinations, missing bundle keys, missing allowlisted names, strict unexpected keys, non-strict ignored keys, missing destination variables, staging-to-preview mapping, production mapping, unknown target selection, and `NEXT_PUBLIC_` credential-shaped values.
- [ ] **Step 2: Run `python -m unittest tests.test_env_sync -v` and verify failures are caused by the absent module.**
- [ ] **Step 3: Implement immutable dataclasses and generic public exceptions.** Error text may name target, provider, environment, bundle key, and key names; it must never include a value or raw JSON.
- [ ] **Step 4: Implement validation-before-selection.** Validate every target in the selected environment and the complete selected bundle before applying the optional target filter, so `target` cannot bypass missing/unexpected-key validation.
- [ ] **Step 5: Reject confidential-looking `NEXT_PUBLIC_` names.** At minimum reject names containing `SECRET`, `TOKEN`, `PASSWORD`, `PRIVATE_KEY`, `DATABASE_URL`, or `CREDENTIAL`.
- [ ] **Step 6: Run the focused tests and verify all validation cases pass.**

### Task 2: Implement Render synchronization with TDD

**Files:**
- Modify: `tests/test_env_sync.py`
- Modify: `scripts/env_sync.py`

**Interfaces:**
- Produces `HttpTransport.request(method, url, headers, body) -> tuple[int, object]`.
- Produces `merge_render_environment(current: list[dict[str, str]], managed: dict[str, str]) -> list[dict[str, str]]`.
- Render reads every paginated `/v1/services/{service_id}/env-vars` page, preserves unmanaged entries, replaces managed values, and sends the full merged list with `PUT`.

- [ ] **Step 1: Add failing tests for unmanaged-key preservation, managed-key replacement, pagination, idempotent no-op, full-list request construction, dry-run no requests, and secrets containing quotes, newlines, Unicode, and shell metacharacters.**
- [ ] **Step 2: Run the focused Render tests and confirm expected assertion failures.**
- [ ] **Step 3: Implement deterministic merge ordering and provider requests.** Use `Authorization: Bearer ...` in memory only. Never interpolate secrets into URLs, command lines, logs, outputs, or exceptions.
- [ ] **Step 4: Convert non-2xx provider failures to generic `SyncError` messages containing only target and operation stage.** Do not include response bodies.
- [ ] **Step 5: Run the focused Render tests and the complete unit suite.**

### Task 3: Implement Vercel synchronization and redacted CLI behavior with TDD

**Files:**
- Modify: `tests/test_env_sync.py`
- Modify: `scripts/env_sync.py`

**Interfaces:**
- Vercel uses `POST /v10/projects/{project_id}/env?teamId={team_id}&upsert=true`.
- Each payload entry is `{key, value, target: [preview|production], type: sensitive}`.
- Produces `run_sync(...) -> SyncResult` and `main() -> int`.

- [ ] **Step 1: Add failing tests for preview/production targets, sensitive upsert payloads, idempotent repeated upsert behavior, missing token/team/project failures, dry-run no requests, and no secret substrings in captured stdout/stderr.**
- [ ] **Step 2: Run the focused Vercel/redaction tests and verify the expected failures.**
- [ ] **Step 3: Implement batch upsert without retrieving existing Vercel values.** Resolve the project ID and team ID only through manifest-named repository variables.
- [ ] **Step 4: Mask parsed bundle leaf values before any status output.** Status output is limited to provider, target, provider environment, operation stage, and key names.
- [ ] **Step 5: Catch JSON, validation, HTTP, and unexpected errors at the CLI boundary and emit generic messages with no traceback or raw provider body.**
- [ ] **Step 6: Run `python -m unittest discover -s tests -v` and verify the complete suite passes.**

### Task 4: Add the reusable central workflow and structural validation

**Files:**
- Create: `.github/workflows/sync-environment.yml`
- Modify: `scripts/validate_workflows.py`
- Modify: `tests/test_env_sync.py`

**Interfaces:**
- Inputs: `environment`, `ref`, `manifest_json`, `repository_variables_json`, `dry_run` default `true`, and optional `target`.
- Secrets: `ENV_SYNC_BUNDLE` required; `RENDER_API_KEY` and `VERCEL_TOKEN` optional at declaration but enforced for selected non-dry-run targets.
- Permissions: `contents: read` and `pull-requests: read` only.

- [ ] **Step 1: Add failing structural tests for the workflow contract, least privileges, no artifacts/outputs/summaries, no `toJSON(secrets)`, full-SHA input, and production guard invocation.**
- [ ] **Step 2: Run the structural tests and confirm the missing workflow failure.**
- [ ] **Step 3: Create the reusable workflow.** Check out `The-Team-CG/.github` at `${{ github.workflow_sha }}`, run `scripts/env_sync.py`, pass secrets only through step environment variables, and never enable shell tracing.
- [ ] **Step 4: Invoke `validate-prod-promotion@v2.1` for production before the sync step.** Staging does not call the production guard.
- [ ] **Step 5: Extend `validate_workflows.py` with positive contract checks and forbidden patterns (`toJSON(secrets)`, artifact upload, step summary writes, secret output writes, request-body logging).
- [ ] **Step 6: Run `python scripts/validate_workflows.py`, unit tests, and `git diff --check`.**

### Task 5: Document setup, safety, dry run, and rollout

**Files:**
- Modify: `README.md`
- Modify: `docs/CICD-SECRET-MODEL.md`
- Modify: `docs/ENVIRONMENTS.md`
- Modify: `docs/YOU-MUST-SET.md`

**Interfaces:** Operators copy each product's `.github/env-sync-manifest.json` into `ENV_SYNC_MANIFEST_JSON`; create the two bundle secrets; set provider tokens and destination IDs; then manually dry-run, stage through a trusted push, verify health, and only then enable production values.

- [ ] **Step 1: Document the two fixed bundle secrets, JSON shape, GitHub secret-size limit, split-bundle escalation rule, and prohibition on putting values in repository variables.**
- [ ] **Step 2: Document Render full-list replacement/preservation, Vercel preview/production mapping, `NEXT_PUBLIC_` exposure, and post-sync deployment behavior.**
- [ ] **Step 3: Document manual dispatch branch rules, `dry_run=true` default, target filtering, generic failures, idempotent retries, and no rollback of current secrets during code rollback.**
- [ ] **Step 4: Run the central unit and structural validation suite.**
- [ ] **Step 5: Commit only central implementation files with `feat: synchronize deployment environment secrets`. Record the resulting full SHA for product callers.**

### Task 6: Add canonical manifests and manual callers to all five products

**Files:**
- Create in each product: `.github/env-sync-manifest.json`
- Create in each product: `.github/workflows/sync-environment.yml`

**Interfaces:** Every manual caller uses the exact central SHA from Task 5, passes `vars.ENV_SYNC_MANIFEST_JSON`, passes `toJSON(vars)` only (never secrets), and maps exactly one fixed bundle per environment.

- [ ] **Step 1: Add manifests with unique environment-specific target names and reusable logical bundle keys.**
  - `capstone-system`: Vercel frontend.
  - `Front-and-back`: Render API and Vercel frontend.
  - `PAULUS`: Render API, Render analytics, and Vercel frontend.
  - `prism`: Render API plus Vercel client, event, guest, and supplier.
  - `WOOF_V1`: Render API and Vercel frontend.
- [ ] **Step 2: For Vercel targets use `preview` for staging and `production` for production; use the same project ID variable as deployment and `VERCEL_ORG_ID` as the team variable.**
- [ ] **Step 3: For Render targets use environment-specific service ID variables matching the existing deploy-hook and health-variable prefixes.**
- [ ] **Step 4: Add `workflow_dispatch` callers with `environment`, `dry_run` default `true`, and optional `target`. Use separate staging and production jobs so bundle-secret selection is static.**
- [ ] **Step 5: Add a production preflight job that fails unless the dispatch ref is `refs/heads/prod`; pass the selected full `github.sha` into the central production guard.**

### Task 7: Gate trusted product deployments on synchronization

**Files:**
- Modify in each product: `.github/workflows/deploy.yml`

**Interfaces:** `workflow_run` remains restricted to the successful `CI` workflow. A staging sync job receives only `ENV_SYNC_STAGING`; a production sync job receives only `ENV_SYNC_PRODUCTION`; every deployment job depends on the corresponding successful sync job.

- [ ] **Step 1: Add `sync-staging` and `sync-production` reusable jobs gated by `workflow_run.conclusion == 'success'` and exact head branch `staging` or `prod`.**
- [ ] **Step 2: Pass `workflow_run.head_sha` as `ref`; never use the mutable branch name as the synchronization revision.**
- [ ] **Step 3: Add sync jobs to all relevant backend and frontend `needs` chains.** Existing Render deploy jobs still trigger deploy hooks and wait for health; Vercel jobs still build/deploy and smoke-check after sync.
- [ ] **Step 4: Confirm no sync reference exists in PR-triggered CI, promotion, release, or rollback workflows.** Rollback retains current selected environment secrets.

### Task 8: Validate product agreement and YAML

**Files:**
- Modify: central `scripts/validate_product_callers.py`
- Test: central `tests/test_env_sync.py`

**Interfaces:** The validator loads each product manifest template, checks it through the central schema, and proves expected bundle keys/destination variables match the repository's deploy caller.

- [ ] **Step 1: Add failing tests/fixtures for missing manual caller, mutable central ref, missing fixed bundle mapping, wrong Vercel target, missing Render service ID, manifest/deploy project-ID mismatch, and deploy job lacking sync dependency.**
- [ ] **Step 2: Implement validation for all five product shapes without reading any secret value.** Runtime `ENV_SYNC_MANIFEST_JSON` is validated again by the reusable workflow; the committed template is the operator source of truth.
- [ ] **Step 3: Parse every changed YAML file with an available YAML parser and run central regex/security validation.** If no parser is installed, install or invoke a pinned parser rather than claiming syntax from regex alone.
- [ ] **Step 4: Run `python scripts/validate_product_callers.py` across all five repositories, `python scripts/validate_workflows.py`, `python -m unittest discover -s tests -v`, and `git diff --check` in every repository.**
- [ ] **Step 5: Run touched-repository workflow/application checks required by each repository's instructions. Preserve unrelated generated or untracked files.**

### Task 9: Commit, publish, and verify handoff

**Files:** Only the manifest/workflow files from Tasks 6-7 in product repositories and central validation/docs from Tasks 1-8.

**Interfaces:** Conventional commits on the existing implementation branches; no direct push to protected `staging`, `prod`, or `main`.

- [ ] **Step 1: Review `git status`, `git diff --check`, and the exact staged file list separately in all six repositories.**
- [ ] **Step 2: Commit each product with `feat(ci): synchronize deployment environment secrets`. Do not stage Prism's `apps/agent-*` directories.**
- [ ] **Step 3: Push only the implementation branches and verify each remote tip matches the local commit.**
- [ ] **Step 4: Inspect or create PRs targeting the approved branch (`main` for central if repository policy requires it; `staging` for every product). Verify owner/repository/base/head identity before reporting any PR.**
- [ ] **Step 5: Report central and product SHAs, immutable workflow reference, test/YAML evidence, required repository variables/secrets, and the rollout gate: manual dry run on one product, trusted staging sync plus health/smoke verification, then production enablement.**

## Self-review

- Spec coverage: fixed bundles, manifest allowlist, Render full replacement, Vercel target mapping, trusted push-only execution, manual dry run, exact production guard, redaction, idempotence, rollback semantics, and staged rollout each map to a task above.
- Placeholder scan: no implementation step depends on a `TODO`, undefined later decision, or dynamic secret lookup.
- Interface consistency: central `environment` is `staging|production`; provider targets are Render `staging|production` and Vercel `preview|production`; product callers pass one `ENV_SYNC_BUNDLE` selected statically from the two fixed repository secrets.

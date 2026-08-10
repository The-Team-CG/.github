# The-Team-CG central GitHub workflows

This repository owns the reusable GitHub Actions used by the five CICG product repositories:

- capstone-system
- Front-and-back
- PAULUS
- prism
- WOOF_V1

Product repositories keep thin caller workflows. Shared CI, security, deployment, promotion, rollback, release, and notification behavior is changed here and published as an immutable workflow release such as v2.

The central workflow repository remains on main. Product repositories use staging for integration and prod for production.

## Product delivery flow

1. A feature pull request targets staging.
2. Pull request CI runs dependency audit, configured lint, typecheck, tests, coverage, build, Gitleaks, and advisory CodeQL.
3. A successful merge to staging runs push CI.
4. Staging deploys the backend first, checks health, deploys frontends, and runs smoke checks.
5. The successful staging SHA creates or updates one staging-to-prod pull request.
6. The promotion pull request reruns CI and requires manual review.
7. A manual merge to prod runs prod CI.
8. A successful prod CI run deploys the exact merged SHA to production.

SonarCloud is not part of the active workflow model.

## Reusable workflows

| Workflow | Purpose |
|---|---|
| ci-node.yml | Node install, npm audit, lint, typecheck, tests, coverage artifact, and build |
| ci-python.yml | Python install, pip-audit, and tests |
| security-gitleaks.yml | Redacted current-tree secret scan |
| security-gitleaks-history.yml | Manual/weekly redacted full-history scan |
| security-codeql.yml | Advisory CodeQL analysis |
| security-trivy.yml | HIGH/CRITICAL container scan |
| deploy-render.yml | Exact-SHA image build, GHCR push, Trivy scan, Render hook, and health polling |
| deploy-vercel.yml | Exact-SHA Vercel build, deployment, and smoke check |
| sync-environment.yml | Validate and synchronize managed Render/Vercel environment values before deployment |
| promote-to-prod.yml | Idempotent staging-to-prod PR and staging-promotion check |
| rollback-render.yml | Exact-target backend rollback |
| rollback-vercel.yml | Exact-target frontend rollback |
| release-tag.yml | Manual semantic release tag from prod |
| notify.yml | Optional webhook notification |

Callers should use a tagged central release:

~~~yaml
uses: The-Team-CG/.github/.github/workflows/ci-node.yml@v2
~~~

## Required configuration

Deployment uses GitHub Environments named staging and production. Required Vercel and Render credentials must be present; missing deployment configuration fails the deployment job rather than producing a successful skip.

Expected secret classes include VERCEL_TOKEN, VERCEL_ORG_ID, environment-specific Render deploy hooks, and optional NOTIFY_WEBHOOK_URL. Project IDs and public health URLs are variables. Runtime database and service credentials remain in the provider runtime environment.

Environment synchronization uses two fixed repository secrets per product, `ENV_SYNC_STAGING` and `ENV_SYNC_PRODUCTION`. Product repositories keep a value-free `.github/env-sync-manifest.json` template; operators copy that JSON into the `ENV_SYNC_MANIFEST_JSON` repository variable. Product callers pin `sync-environment.yml` to a full central commit SHA, validate with `dry_run: true` first, and run the same synchronization before trusted staging and production deployment jobs.

See docs/ENVIRONMENTS.md, docs/RENDER-SETUP.md, and docs/CICD-SECRET-MODEL.md.

## Validation

~~~powershell
python scripts/validate_workflows.py
python scripts/validate_product_callers.py
~~~

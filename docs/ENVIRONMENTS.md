# Environments and production approval

## Product branches

| Branch | Purpose | Deployment |
|---|---|---|
| staging | Integration and pre-production | Automatic after successful CI, backend health, and frontend smoke checks |
| prod | Production promotion target | Automatic after manual promotion merge and successful prod CI |

The central reusable-workflow repository keeps main as its workflow-library branch.

## Promotion flow

1. Feature PR targets staging.
2. PR CI must pass.
3. A merge to staging runs push CI and deploys staging.
4. The staging bundle is validated and synchronized before deployment; failed synchronization blocks deployment.
5. The exact healthy staging SHA creates or updates one staging-to-prod PR.
6. The promotion PR reruns CI and requires review.
7. Manual merge into prod creates the production deployment candidate.
8. Push CI runs on prod, validates the exact promotion SHA, synchronizes the production bundle, and deploys that same SHA.

The staging-to-prod PR has a required staging-promotion check. A staging deployment failure leaves the current promotion head without a successful readiness check.

## GitHub Environments

Create staging and production Environments in each product repository. Keep branch protection and deployment configuration separate:

- staging allows automatic deployment after green staging CI.
- production is used by the prod deployment and may require an Environment reviewer when available.
- manual promotion merge is the required production approval; a second deployment approval is not required by this design.
- when branch protection is available, both staging and prod reject direct pushes and force pushes; the current Free-plan fallback blocks unapproved production deployment.

Required product branch protection includes pull requests, required CI checks, Code Owner review on prod, and disabled branch deletion.

## Current GitHub plan limitation

The product repositories are private and the organization is on GitHub Free. GitHub rejects branch protection, repository rulesets, and required environment reviewers for private repositories on this plan. The desired branch policy remains the target configuration after a plan upgrade.

Until then, the central `v2.1` deployment workflows enforce the production invariant at the deployment boundary: a production deploy must use a full commit SHA that is the merge commit of a closed `staging -> prod` or approved `hotfix/* -> prod` pull request. A direct push may still change the ref because GitHub cannot lock it on this plan, but it cannot deploy through the production workflow.

## Configuration

Required configuration names are documented in YOU-MUST-SET.md and RENDER-SETUP.md. Missing deployment credentials, project IDs, deploy hooks, or health URLs fail deployment. Values are never printed.

Optional NOTIFY_WEBHOOK_URL may send CI/deployment notifications but cannot gate delivery.

## Manual environment synchronization

Every product exposes `Sync environment secrets` through `workflow_dispatch` with `environment`, `dry_run`, and optional `target` inputs. Dry run defaults to `true`, validates the complete selected bundle, lists only provider/target/environment/key names, and performs no provider request. Manual production runs must be dispatched from `prod`; the central workflow also applies the exact merged-promotion SHA guard.

A non-dry-run manual sync changes provider configuration but does not roll application code. Existing Render and Vercel deployment workflows remain responsible for creating a new deployment. The normal supported application path is a trusted staging/prod push: sync, Render deployment and health check, Vercel deployment and smoke check. Rollback redeploys a known-good application revision while retaining the environment's current synchronized values.

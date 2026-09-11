# Operator setup

The reusable workflows and product callers are repository configuration. Operators still need to configure GitHub, Vercel, Render, and provider runtime values.

## GitHub branch policy

For each product repository:

1. Keep staging as the default integration branch.
2. Create prod from the current production main commit during the migration.
3. Protect staging and prod.
4. Require pull requests and required CI checks.
5. Require Code Owner review on prod.
6. Disable force pushes and branch deletion.
7. Allow merge commits for the staging-to-prod promotion PR.
8. After verification, remove the old product main branch using the exact repository and branch name.

The central workflow repository remains on main.

## GitHub Environments and values

Create staging and production Environments in every product repository. Configure:

- VERCEL_TOKEN as an organization, repository, or Environment secret and VERCEL_ORG_ID as a repository variable.
- Product Vercel project IDs as variables.
- ENV_SYNC_MANIFEST_JSON as a repository variable copied exactly from `.github/env-sync-manifest.json`.
- ENV_SYNC_STAGING and ENV_SYNC_PRODUCTION as repository secrets containing only that environment's managed values.
- RENDER_API_KEY as a repository or Environment secret when the manifest has Render targets.
- Environment-specific Render deploy hooks as secrets. PAULUS uses `RENDER_PAULUS_DEPLOY_HOOKS_STAGING` and `RENDER_PAULUS_DEPLOY_HOOKS_PRODUCTION`, each containing the nine-key JSON map described in RENDER-SETUP.md.
- Environment-specific Render service IDs as repository variables.
- Product backend health URLs as variables.
- Optional NOTIFY_WEBHOOK_URL as an organization secret.
- Separate staging and production runtime credentials in the provider.

Required Render hook names and health variables are listed in RENDER-SETUP.md. Never paste secret values into this repository, workflow inputs, issues, logs, screenshots, or chat.

## Product setup

| Product | Frontend | Backend |
|---|---|---|
| capstone-system | capstone-system/unified on Vercel | None |
| Front-and-back | Front-End-Dashboard on Vercel | Back-End on Render |
| PAULUS | `src/frontend` on one Vercel project (Preview and Production environments) | Eight Node microservice services plus Python analytics on Render; one Node image is reused with a per-service `dockerCommand` |
| prism | apps/client, apps/event, apps/guest, apps/supplier on Vercel | shared API on Render |
| WOOF_V1 | frontend on Vercel | backend on Render |

Use Node.js 24 for Vercel builds. Configure Render registry access inside Render, not in repository files. Sync `PAULUS/render.yaml` after creating the `paulus-ghcr` registry credential; it provisions the existing service topology without changing the application microservices.

## Migration and verification

For Prism, configure Render's pre-deploy command as npm --workspace prism-api run db:migrate:deploy. This runs prisma migrate deploy and never resets or seeds production.

After setup, push a controlled change to staging and verify:

manual staging dry run -> CI -> staging sync -> staging deploy -> backend health -> frontend smoke -> one staging-to-prod PR -> promotion PR CI -> manual prod merge -> prod CI -> production sync -> production deploy -> production smoke.

Do not copy the production bundle until the staging dry run, provider update, backend health check, and frontend smoke checks have been verified. A dry run may display target names, provider names, provider environments, and managed key names only. It must never print values, tokens, authorization headers, request bodies, provider response bodies, deploy hooks, or secret-bearing URLs.

SonarCloud setup is not required.

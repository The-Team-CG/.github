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

- VERCEL_TOKEN and VERCEL_ORG_ID as organization or Environment secrets.
- Product Vercel project IDs as variables.
- Environment-specific Render deploy hooks as secrets.
- Product backend health URLs as variables.
- Optional NOTIFY_WEBHOOK_URL as an organization secret.
- Separate staging and production runtime credentials in the provider.

Required Render hook names and health variables are listed in RENDER-SETUP.md. Never paste secret values into this repository, workflow inputs, issues, logs, screenshots, or chat.

## Product setup

| Product | Frontend | Backend |
|---|---|---|
| capstone-system | capstone-system/unified on Vercel | None |
| Front-and-back | Front-End-Dashboard on Vercel | Back-End on Render |
| PAULUS | src/frontend on Vercel | API and analytics on Render |
| prism | apps/client, apps/event, apps/guest, apps/supplier on Vercel | shared API on Render |
| WOOF_V1 | frontend on Vercel | backend on Render |

Use Node.js 24 for Vercel builds. Configure Render registry access inside Render, not in repository files.

## Migration and verification

For Prism, configure Render's pre-deploy command as npm --workspace prism-api run db:migrate:deploy. This runs prisma migrate deploy and never resets or seeds production.

After setup, push a controlled change to staging and verify:

CI -> staging deploy -> backend health -> frontend smoke -> one staging-to-prod PR -> promotion PR CI -> manual prod merge -> prod CI -> production deploy -> production smoke.

SonarCloud setup is not required.

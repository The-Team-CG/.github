# CI/CD secret and deployment model

Secret values are never committed, echoed, uploaded as artifacts, or passed as ordinary workflow inputs.

| Secret/value | Storage | Workflow use |
|---|---|---|
| VERCEL_TOKEN and VERCEL_ORG_ID | GitHub organization or Environment secrets | Vercel CLI deployment only |
| VERCEL_PROJECT_ID per product | GitHub variable | Vercel project selection |
| RENDER_*_DEPLOY_HOOK_URL | GitHub Environment secret | Render trigger target only |
| *_API_*_URL health values | GitHub variable | Public health polling only |
| DATABASE_URL, service keys, JWT keys, provider tokens | Render runtime secrets | Application process only |
| NEXT_PUBLIC_* values | Vercel environment variables | Intentionally browser-visible configuration |
| NOTIFY_WEBHOOK_URL | Optional GitHub organization secret | Notification workflow only |

## Workflow rules

- Pull requests run tests, dependency audit, Gitleaks, and advisory CodeQL; they do not deploy.
- A successful staging push deploys the exact CI-tested SHA.
- A successful staging deployment and smoke check creates or updates one staging-to-prod PR.
- A merged prod commit runs prod CI before production deployment.
- Backend images are built for linux/amd64, scanned with Trivy for HIGH/CRITICAL vulnerabilities, pushed to GHCR with the tested commit tag, and deployed to Render by environment-scoped hook.
- Vercel deployments check out the exact commit, build prebuilt artifacts, deploy them, and run curl smoke checks.
- Provider runtime secrets stay in Render/Vercel settings; GitHub Actions stores deployment credentials only.
- Production rollback targets a previously verified commit or image digest and repeats health checks.
- SonarCloud is intentionally absent because the private repositories would require a paid plan.

## Migration rules

Product-owned migrations are explicit, forward-only provider pre-deploy commands. Prism uses npm --workspace prism-api run db:migrate:deploy, which runs prisma migrate deploy. Deployment never runs reset, seed, migrate dev, or destructive rollback commands.

## Logging rules

Logs may show repository names, commit IDs, image digests, status codes, and public URLs. They must not show secret values, authorization headers, deploy-hook URLs, environment files, or secret-bearing environment dumps.

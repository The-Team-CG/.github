# CI/CD secret and deployment model

Secret values are never committed, echoed, uploaded as artifacts, or passed as ordinary workflow inputs.

| Secret/value | Storage | Workflow use |
|---|---|---|
| VERCEL_TOKEN and VERCEL_ORG_ID | GitHub organization or Environment secrets | Vercel CLI deployment only |
| VERCEL_PROJECT_ID per product | GitHub variable | Vercel project selection |
| RENDER_*_DEPLOY_HOOK_URL | GitHub Environment secret | Render trigger target only for single-service products |
| RENDER_PAULUS_DEPLOY_HOOKS_STAGING / RENDER_PAULUS_DEPLOY_HOOKS_PRODUCTION | GitHub Environment secrets | JSON map of the nine PAULUS Render service keys to deploy-hook URLs |
| *_API_*_URL health values | GitHub variable | Public health polling only |
| DATABASE_URL, service keys, JWT keys, provider tokens | Render runtime secrets | Application process only |
| NEXT_PUBLIC_* values | Vercel environment variables | Intentionally browser-visible configuration |
| NOTIFY_WEBHOOK_URL | Optional GitHub organization secret | Notification workflow only |
| ENV_SYNC_STAGING | GitHub Repository Secret | Staging runtime values grouped by manifest bundle key |
| ENV_SYNC_PRODUCTION | GitHub Repository Secret | Production runtime values grouped by manifest bundle key |
| ENV_SYNC_MANIFEST_JSON | GitHub Repository Variable | Value-free destination and managed-key allowlist |
| RENDER_API_KEY | GitHub Repository or Environment Secret | Render environment API writes only |
| VERCEL_TOKEN | GitHub Repository or Environment Secret | Vercel environment API writes and deployment |

## Workflow rules

- Pull requests run tests, dependency audit, Gitleaks, and advisory CodeQL; they do not deploy.
- A successful staging push deploys the exact CI-tested SHA.
- A successful staging deployment and smoke check creates or updates one staging-to-prod PR.
- A merged prod commit runs prod CI before production deployment.
- Backend images are built for linux/amd64, scanned with Trivy for HIGH/CRITICAL vulnerabilities, pushed to GHCR with the tested commit tag, and deployed to Render by environment-scoped hook. PAULUS builds one Node image and one Python image, then deploys each of its nine service targets from the immutable image digest.
- Vercel deployments check out the exact commit, build prebuilt artifacts, deploy them, and run curl smoke checks.
- Provider runtime secrets stay in Render/Vercel settings; GitHub Actions stores deployment credentials only.
- Trusted staging/prod deployment callers synchronize the selected fixed bundle before provider deployment. Pull-request CI never receives a bundle or provider token.
- Production rollback targets a previously verified commit or image digest and repeats health checks. PAULUS rollback fans out to the same nine-service matrix.
- SonarCloud is intentionally absent because the private repositories would require a paid plan.

## Migration rules

Product-owned migrations are explicit, forward-only provider pre-deploy commands. Prism uses npm --workspace prism-api run db:migrate:deploy, which runs prisma migrate deploy. Deployment never runs reset, seed, migrate dev, or destructive rollback commands.

## Logging rules

Logs may show repository names, commit IDs, image digests, status codes, and public URLs. They must not show secret values, authorization headers, deploy-hook URLs, environment files, or secret-bearing environment dumps.

## Environment bundle rules

Each bundle is one JSON object grouped by logical target. The manifest contains only target names, provider environments, destination-variable names, bundle keys, and managed key names. GitHub Actions cannot safely resolve an arbitrary secret name from manifest text, so callers statically map either `ENV_SYNC_STAGING` or `ENV_SYNC_PRODUCTION` to the central workflow's `ENV_SYNC_BUNDLE` secret. `toJSON(secrets)` is prohibited.

Bundle values must remain below GitHub's repository-secret size limit. If one product exceeds that limit, create a reviewed design for multiple explicitly named bundles; never truncate, split implicitly, or store values in repository variables. Values containing quotes, newlines, Unicode, and shell metacharacters are passed as JSON through process environment variables and never evaluated by a shell.

Render's environment update replaces the complete list. The adapter therefore reads the current list, preserves unmanaged entries, replaces only allowlisted keys, and submits the complete merged list. Vercel variables use sensitive upsert requests targeted to `preview` for CICG staging and `production` for CICG production; existing decrypted values are never fetched or printed. Any `NEXT_PUBLIC_` value is intentionally browser-visible and must not contain credentials, private tokens, passwords, private keys, or database URLs.

# Render backend setup

Render receives immutable images from the successful staging or prod CI commit. Render must not deploy directly from a branch.

Create separate Render services for staging and production. Use the Docker image deploy flow from the central reusable workflow; do not connect Render directly to a branch. A service is still a separate Render runtime even when several services use the same image.

| Product | Service(s) per environment | Health path |
|---|---|---|
| Front-and-back | front-and-back-api | /api/health |
| PAULUS | 8 Node services plus paulus-analytics-python | gateway `/api/health`, Python `/health` |
| Prism | prism-api | /health |
| WOOF_V1 | woof-v1-api | /api/health |

Store each product’s deploy-hook URL as a GitHub Actions repository or organization secret. The product caller maps that secret into the reusable workflow without printing it.

PAULUS is the matrix exception because one workflow deploys nine Render services per environment. Its two matrix secrets are JSON objects whose keys are the service keys in `PAULUS/.github/render-services.json`:

```json
{
  "api-gateway": "https://api.render.com/deploy/srv-...?...",
  "auth": "https://api.render.com/deploy/srv-...?...",
  "entity": "https://api.render.com/deploy/srv-...?...",
  "financial": "https://api.render.com/deploy/srv-...?...",
  "project": "https://api.render.com/deploy/srv-...?...",
  "analytics-node": "https://api.render.com/deploy/srv-...?...",
  "announcement": "https://api.render.com/deploy/srv-...?...",
  "audit-log": "https://api.render.com/deploy/srv-...?...",
  "analytics-python": "https://api.render.com/deploy/srv-...?..."
}
```

Required product-specific secret names:

- RENDER_FRONT_AND_BACK_API_STAGING_DEPLOY_HOOK_URL
- RENDER_FRONT_AND_BACK_API_PRODUCTION_DEPLOY_HOOK_URL
- RENDER_PAULUS_DEPLOY_HOOKS_STAGING
- RENDER_PAULUS_DEPLOY_HOOKS_PRODUCTION
- RENDER_PRISM_API_STAGING_DEPLOY_HOOK_URL
- RENDER_PRISM_API_PRODUCTION_DEPLOY_HOOK_URL
- RENDER_WOOF_API_STAGING_DEPLOY_HOOK_URL
- RENDER_WOOF_API_PRODUCTION_DEPLOY_HOOK_URL

Required repository variables:

- FRONT_AND_BACK_API_STAGING_URL and FRONT_AND_BACK_API_PRODUCTION_URL
- PAULUS_API_STAGING_URL and PAULUS_API_PRODUCTION_URL
- PAULUS_ANALYTICS_STAGING_URL and PAULUS_ANALYTICS_PRODUCTION_URL
- PRISM_API_STAGING_URL and PRISM_API_PRODUCTION_URL
- WOOF_API_STAGING_URL and WOOF_API_PRODUCTION_URL

Put runtime values such as database URLs, Supabase service-role keys, JWT signing keys, and third-party API tokens in the matching Render service’s Environment settings. Keep staging and production values separate. Do not paste them into GitHub workflow inputs, issues, logs, or this repository.

## PAULUS Blueprint setup

`PAULUS/render.yaml` provisions nine services in each environment. The API gateway and Python analytics service are public web services. The seven supporting Node services are private services. All eight Node services use `ghcr.io/the-team-cg/paulus-api`; `dockerCommand` selects the existing compiled microservice entrypoint. Python analytics uses `ghcr.io/the-team-cg/paulus-analytics`.

Before the first Blueprint sync:

1. Create a workspace registry credential named `paulus-ghcr` with read access to the two GHCR images.
2. Create or attach staging and production Render environment groups containing the runtime secrets required by the existing services.
3. Sync the Blueprint, then create one Render deploy hook for each service in each environment and place the URLs in the matching matrix secret.
4. Set `PAULUS_API_*_URL` and `PAULUS_ANALYTICS_*_URL` repository variables to the public service URLs. The central workflow polls those two public services; private services stay reachable only through Render’s private network.

The Blueprint contains only non-secret topology and internal service URLs. It intentionally does not replace the existing runtime secret model.

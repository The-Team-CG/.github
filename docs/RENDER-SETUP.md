# Render backend setup

Create separate Render services for staging and production. Use the Docker image deploy flow from the central reusable workflow; do not connect Render directly to a branch.

| Product | Service(s) per environment | Health path |
|---|---|---|
| Front-and-back | front-and-back-api | /api/health |
| PAULUS | paulus-api, paulus-analytics | /api/health, /health |
| Prism | prism-api | /health |
| WOOF_V1 | woof-v1-api | /api/health |

Store each product’s deploy-hook URL as a GitHub Actions repository or organization secret. The product caller maps that secret into the reusable workflow without printing it.

Required product-specific secret names:

- RENDER_FRONT_AND_BACK_API_STAGING_DEPLOY_HOOK_URL
- RENDER_FRONT_AND_BACK_API_PRODUCTION_DEPLOY_HOOK_URL
- RENDER_PAULUS_API_STAGING_DEPLOY_HOOK_URL
- RENDER_PAULUS_API_PRODUCTION_DEPLOY_HOOK_URL
- RENDER_PAULUS_ANALYTICS_STAGING_DEPLOY_HOOK_URL
- RENDER_PAULUS_ANALYTICS_PRODUCTION_DEPLOY_HOOK_URL
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

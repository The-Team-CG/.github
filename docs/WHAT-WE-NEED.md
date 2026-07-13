# What we need — CI/CD backlog

Human setup only: **[YOU-MUST-SET.md](./YOU-MUST-SET.md)**.

## Status

| Area | Status |
|------|--------|
| Org reusable CI / Sonar / Vercel / notify / release-tag | **Done** (`@v1`, Node **24**) |
| Gitleaks + CodeQL reusable | **Done** |
| Post-deploy smoke (curl) | **Done** |
| Coverage artifact upload | **Done** |
| Product callers (tests where exist, security, notify) | **Done** |
| Dependabot / CODEOWNERS / CHANGELOG / release dispatch | **Done** |
| Secrets / Vercel projects / Sonar bind | **You set** → YOU-MUST-SET.md |
| ~80% new-code coverage | **You set** Sonar gate + grow tests; reporting wired |
| Staging ≠ prod data | **You set** separate backends |

## Runtime defaults

| Tool | Version |
|------|---------|
| Node.js | **24** (`check-latest: true` for current patch) |
| Python (analytics) | **3.13** |
| actions/checkout | **v7** |
| actions/setup-node | **v6** |
| actions/setup-python | **v5** |
| Sonar scan action | **v5** |
| CodeQL action | **v3** |

## Product test wiring

| Repo | Tests in CI |
|------|-------------|
| prism | `npm run test:api` |
| WOOF_V1 backend | `npm run test:cov` |
| Others | Build/lint until suites exist; then set `test_command` |

## Raise toward 80% coverage

1. Write tests product-by-product.  
2. Emit coverage from `test_command` (jest/vitest).  
3. Sonar quality gate on **new code** ≥80%.  
4. Later raise jest/vitest `coverageThreshold` global toward 80%.

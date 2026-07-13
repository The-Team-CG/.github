# What we need — free-tier CI/CD backlog

**Budget rule:** free for everything (GitHub Free, Vercel Hobby, SonarCloud free, free webhooks).

## Status legend

| Status | Meaning |
|--------|---------|
| **Done** | Landed in org workflows / product callers |
| **Partial** | Plumbing exists; product config or secrets still needed |
| **Todo** | Not enforced yet |

---

## A. Already done (platform)

| Need | Status | Notes |
|------|--------|-------|
| Org reusable workflows | **Done** | `ci-node`, `ci-python`, `sonar`, `deploy-vercel` |
| Trunk `staging` / prod `main` | **Done** | All 5 product repos; default = `staging` |
| Thin CI + deploy callers | **Done** | No app folder restructure |
| Sonar project keys under The-Team-CG | **Done** | PAULUS re-keyed |
| GitHub Environments `staging`/`production` | **Done** | Env *required reviewers* blocked on free plan |
| npm audit step in Node CI | **Done** | Soft-fail warning until teams clean deps |
| Notify reusable workflow | **Done** | Needs free `NOTIFY_WEBHOOK_URL` |
| Release tag reusable workflow | **Done** | Manual semver tags `vX.Y.Z` |
| Free-tier docs | **Done** | This file + `ENVIRONMENTS.md` |

---

## B. What we still need (prioritized)

### P0 — Make pipelines real (config, still free)

| Need | Status | How (free) | Owner action |
|------|--------|------------|--------------|
| Org secrets `SONAR_TOKEN`, `VERCEL_TOKEN`, `VERCEL_ORG_ID` | **Todo** | GitHub org secrets | Add tokens |
| Per-app `VERCEL_PROJECT_ID` | **Todo** | Repo secret or workflow input | Create Vercel Hobby projects |
| SonarCloud free org bind | **Todo** | SonarCloud GitHub App | Link The-Team-CG |
| Branch protection on `staging` + `main` | **Todo** | Free GitHub setting | Require CI status checks + PR |
| CODEOWNERS + required reviews on `main` | **Todo** | Free | Human prod gate without Team+ |
| Staging ≠ prod Supabase/API keys | **Todo** | Free Supabase projects | Separate env vars |

### P1 — Quality (~80% coverage path)

| Need | Status | How (free) |
|------|--------|------------|
| Run unit tests in every product CI | **Partial** | Set `test_command` on callers (many empty today) |
| Coverage reports (lcov) | **Todo** | `npm test -- --coverage` / vitest coverage |
| **~80% gate on new code** | **Todo** | Sonar free Clean-as-You-Code + jest/vitest `--coverageThreshold` when suite is ready |
| Overall 80% repo coverage | **Todo** | Raise only after suites exist — don’t fail empty repos |

**Policy:** Prefer **80% on changed/new code** first. Hard global 80% only when each product has meaningful tests.

Example `test_command` (when ready):

```text
npm test -- --coverage --coverageThreshold='{"global":{"lines":80,"statements":80,"functions":80,"branches":70}}'
```

### P2 — Security (free)

| Need | Status | How (free) |
|------|--------|------------|
| Dependency PRs | **Partial** | Dependabot configs in product repos |
| `npm audit` in CI | **Done** | Soft-fail; later set hard-fail when clean |
| Secret leak scan | **Todo** | Optional gitleaks Action; GitHub secret scanning if available |
| CodeQL | **Todo** | Enable free CodeQL where GitHub allows on plan/visibility |
| No paid Snyk/DAST by default | **N/A** | Out of free scope |

### P3 — Versioning (free)

| Need | Status | How (free) |
|------|--------|------------|
| Semver tags on release | **Partial** | Call `release-tag.yml` with version input |
| CHANGELOG.md | **Todo** | Manual or free changelog Action on tag |
| Vercel still deploys by git SHA | **Done** | Tags are for humans/audit |

### P4 — Notifications (free)

| Need | Status | How (free) |
|------|--------|------------|
| Webhook secret `NOTIFY_WEBHOOK_URL` | **Todo** | Discord or Slack **incoming webhook** (free) |
| Notify on CI failure | **Partial** | Call `notify.yml` from product workflows `if: failure()` |
| Notify on staging/prod deploy | **Partial** | Call after deploy job |
| GitHub email watch | **Free** | Users enable Watch on repos |

### P5 — Ops polish (free)

| Need | Status | How (free) |
|------|--------|------------|
| Post-deploy smoke (`curl` staging URL) | **Todo** | Step after deploy |
| PR preview within Vercel Hobby limits | **Todo** | Optional |
| Pin reusable workflows `@v1` | **Todo** | After stable |
| API deploy automation | **Todo** | Only free hosts |
| Mobile EAS | **Todo** | Free EAS tier if needed |
| Sentry | **Optional** | Free tier or skip |

---

## C. Explicit non-goals (paid)

Unless the team opts out of free-first:

- GitHub Team solely for Environment required reviewers  
- Codecov Pro, Sonar enterprise  
- Snyk paid, commercial DAST  
- Vercel Pro (unless Hobby blocks a hard requirement)  
- PagerDuty / paid incident tools  

**Free prod gate substitute:** CODEOWNERS + required PR reviews on `main` (+ optional `workflow_dispatch` prod deploy).

---

## D. Suggested rollout order

1. Secrets + Vercel Hobby projects + Sonar free bind  
2. Branch protection + CODEOWNERS  
3. Dependabot live + clean high `npm audit` issues  
4. Wire `test_command` + coverage thresholds product-by-product  
5. `NOTIFY_WEBHOOK_URL` + failure/deploy notify  
6. Tag releases on promote to `main`  
7. Smoke tests + pin `@v1` workflows  

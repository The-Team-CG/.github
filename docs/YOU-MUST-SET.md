# What you must set

Workflows and repo wiring are already in place. These steps need your accounts, tokens, and project settings.

## Where workflows live (Actions tab)

| What you see | Path on default branch `staging` |
|--------------|-----------------------------------|
| Product CI / Deploy / Release | Each product repo: **`.github/workflows/`** (`ci.yml`, `deploy.yml`, `release.yml`) |
| Shared pipeline logic | Org repo **https://github.com/The-Team-CG/.github** → `.github/workflows/` (`ci-node.yml`, `sonar.yml`, `deploy-vercel.yml`, …) |

Product workflows **call** the org reusable ones (`uses: The-Team-CG/.github/.github/workflows/...@main`).  
If Actions said the workflow file was invalid / jobs never started, that was fixed: org workflows repo is public + reusable access on, YAML is UTF-8 without BOM, ASCII-only.

---

## 1. GitHub org secrets

Org **The-Team-CG** → Settings → Secrets and variables → Actions → New organization secret

| Secret | Where to get it | Used for |
|--------|-----------------|----------|
| `SONAR_TOKEN` | [SonarCloud](https://sonarcloud.io) → My Account → Security → Generate token | Quality gate |
| `VERCEL_TOKEN` | [Vercel](https://vercel.com/account/tokens) → Create token | Deploy |
| `VERCEL_ORG_ID` | Vercel → Team Settings → General → Team ID | Deploy |
| `NOTIFY_WEBHOOK_URL` | Discord channel webhook or Slack incoming webhook | CI / deploy notifications |

Optional per-repo: `VERCEL_PROJECT_ID` when projects differ.

---

## 2. Vercel projects

1. Create a Vercel team (or personal account) and connect GitHub **The-Team-CG**.  
2. Create one project per frontend (root directories below).  
3. Set repo secret `VERCEL_PROJECT_ID` (or a shared org default).  
4. Configure **Preview/staging** vs **Production** environment variables separately.

| Repo | Root directory | Suggested project name |
|------|----------------|------------------------|
| capstone-system | `capstone-system/unified` | `capstone-system-web` |
| Front-and-back | `Front-End-Dashboard` | `front-and-back-dashboard` |
| PAULUS | `src/frontend` | `paulus-web` |
| prism | `apps/client` | `prism-client` |
| WOOF_V1 | `frontend` | `woof-web` |

Runtime for builds: **Node.js 24** (match Vercel project Node version to 24).

---

## 3. SonarCloud

1. Sign in at https://sonarcloud.io with GitHub.  
2. Create/import organization (workflow default key: `the-team-cg` — change if yours differs).  
3. Install the **SonarCloud GitHub App** on **The-Team-CG**.  
4. Projects (keys already in repos):

| Project key |
|-------------|
| `The-Team-CG_capstone-system` |
| `The-Team-CG_Front-and-back` |
| `The-Team-CG_PAULUS` |
| `The-Team-CG_prism` |
| `The-Team-CG_WOOF_V1` |

5. Enable **Clean as You Code**. For practice, set coverage on **new code ≥ 60%** (industry later: 80%).  
6. Put the token in org secret `SONAR_TOKEN`.  

CI unit thresholds (where tests exist): **50%** lines/statements/functions, **40%** branches — see `docs/COVERAGE.md`.

---

## 4. Branch protection

If your GitHub plan supports branch protection on these repos, enable on **`staging`** and **`main`**:

| Setting | Value |
|---------|--------|
| Require a pull request before merging | On |
| Required approving reviews | 1 |
| Require review from Code Owners | On |
| Require status checks to pass | On (after CI has run once) |
| Block force pushes / deletions | On |

If branch protection is unavailable on private repos, use team process: PR-only into `staging`/`main`, respect `CODEOWNERS`, no direct pushes to protected lines.

---

## 5. Staging vs production data

For Supabase / Mongo / APIs: separate projects and keys for staging and production. Never point staging at production service-role credentials.

---

## 6. Notifications (optional)

1. Create Discord or Slack incoming webhook.  
2. Set org secret `NOTIFY_WEBHOOK_URL`.  
3. CI failure and deploy result jobs already call the notify workflow.

---

## 7. Releases (optional)

Actions → **Release** → Run workflow → version e.g. `1.0.0` (creates `v1.0.0` on `main`). Update `CHANGELOG.md` when cutting a release.

---

## Quick checklist

- [ ] Org secrets: `SONAR_TOKEN`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`  
- [ ] Optional: `NOTIFY_WEBHOOK_URL`  
- [ ] Vercel projects + `VERCEL_PROJECT_ID` (Node **24**)  
- [ ] Vercel env vars (staging ≠ prod)  
- [ ] SonarCloud app + projects + quality gate  
- [ ] Branch protection on `staging` + `main` (if available)  
- [ ] Separate staging/prod backends  

After secrets exist, push to `staging` and confirm Actions: CI → security → Sonar → deploy → smoke → notify.

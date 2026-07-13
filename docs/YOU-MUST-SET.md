# What **you** must set (only human/account steps left)

Everything below is free-tier. Code and workflows are already in the repos; these need **your** accounts/tokens/UI.

---

## 1. GitHub org secrets (do once)

Org: **The-Team-CG** → Settings → Secrets and variables → Actions → **New organization secret**

| Secret name | Where to get it | Used for |
|-------------|-----------------|----------|
| `SONAR_TOKEN` | [SonarCloud](https://sonarcloud.io) → My Account → Security → Generate token | Quality gate |
| `VERCEL_TOKEN` | [Vercel](https://vercel.com/account/tokens) → Create token | Deploy |
| `VERCEL_ORG_ID` | Vercel → Team Settings → General → Team ID | Deploy |
| `NOTIFY_WEBHOOK_URL` | Discord: Channel → Integrations → Webhooks → Copy URL **or** Slack incoming webhook | CI/deploy pings |

Optional per-repo (if projects differ): repo secret `VERCEL_PROJECT_ID`.

---

## 2. Vercel (Hobby / free)

1. Create a Vercel account and a free team if you want shared access.  
2. Import each frontend (or `vercel link` from app root). Suggested projects:

| Repo | Root directory | Suggested project name |
|------|----------------|------------------------|
| capstone-system | `capstone-system/unified` | `capstone-system-web` |
| Front-and-back | `Front-End-Dashboard` | `front-and-back-dashboard` |
| PAULUS | `src/frontend` | `paulus-web` |
| prism | `apps/client` | `prism-client` |
| WOOF_V1 | `frontend` | `woof-web` |

3. For each project, copy **Project ID** → set as repo secret `VERCEL_PROJECT_ID`  
   (or one org default if you only deploy one app first).  
4. Add **Environment Variables** separately for **Preview/Staging** vs **Production**  
   (never point staging at production Supabase keys).

---

## 3. SonarCloud (free)

1. Sign in at https://sonarcloud.io with GitHub.  
2. Create/import org matching key used in workflows (default `the-team-cg` — change if Sonar shows a different key).  
3. Install **SonarCloud GitHub App** on **The-Team-CG** (all product repos).  
4. Create projects (or auto-provision on first scan):

| Project key (already in repo) |
|-------------------------------|
| `The-Team-CG_capstone-system` |
| `The-Team-CG_Front-and-back` |
| `The-Team-CG_PAULUS` |
| `The-Team-CG_prism` |
| `The-Team-CG_WOOF_V1` |

5. In each Sonar project quality gate: enable **Clean as You Code** (≈80% coverage on **new** code when coverage reports exist).  
6. Put token in org secret `SONAR_TOKEN`.

If your Sonar org key is not `the-team-cg`, tell CI via workflow input `organization:` or update the reusable default.

---

## 4. Branch protection (free — enable if not already)

Repo → Settings → Branches → Add rule (do for **`staging`** and **`main`**):

| Setting | Value |
|---------|--------|
| Require a pull request before merging | On |
| Required approving reviews | **1** |
| Require review from Code Owners | **On** (`CODEOWNERS` already present) |
| Require status checks to pass | On when CI has run once; pick **CI** jobs you care about |
| Do not allow force pushes | On |
| Do not allow deletions | On |

`main` = production path. `staging` = trunk.

*(Scripts may have applied a baseline via API; double-check in the UI.)*

---

## 5. Staging ≠ production data

For each product that uses Supabase / Mongo / APIs:

| Env | Create |
|-----|--------|
| Staging | Separate free Supabase (or DB) project + keys in Vercel **Preview** / staging env |
| Production | Separate project + keys in Vercel **Production** |

Never reuse production service role keys on staging.

---

## 6. Notifications (optional but ready)

1. Create Discord webhook (or Slack incoming webhook).  
2. Set org secret `NOTIFY_WEBHOOK_URL`.  
3. Failures and deploys already call the notify workflow (no-op until secret exists).

---

## 7. Releases (optional)

Actions → **Release** → Run workflow → enter version `1.0.0` (creates tag `v1.0.0` on `main`).  
Update `CHANGELOG.md` in the same PR when you cut a release.

---

## 8. What you do **not** need to buy

- GitHub Team (env required reviewers) — use CODEOWNERS + PR reviews  
- Codecov Pro / Snyk paid / Vercel Pro / paid Slack  

---

## Quick checklist

- [ ] Org secrets: `SONAR_TOKEN`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`  
- [ ] Optional: `NOTIFY_WEBHOOK_URL`  
- [ ] Vercel projects + per-repo `VERCEL_PROJECT_ID`  
- [ ] Vercel env vars (staging vs prod)  
- [ ] SonarCloud app + projects + quality gate  
- [ ] Branch protection on `staging` + `main`  
- [ ] Separate staging/prod backends  
- [ ] (Optional) Watch repos for email; confirm Discord/Slack pings  

After secrets exist, push any commit to `staging` to verify CI → Sonar → deploy → smoke → notify.

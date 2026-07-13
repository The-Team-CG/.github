from pathlib import Path
import re

plan = Path(r"C:\Codes\cicg\CENTRALIZED-CICD-PLAN.md")
c = plan.read_text(encoding="utf-8")
c = c.replace('node_version: "22"', 'node_version: "24"')

replacements = [
    (r"free-tier \+ full .what we need. backlog", "Node 24 + full backlog"),
    (r"\*\*Cost constraint:\*\*.*\n", ""),
    (
        r"\| \*\*Budget\*\* \|[^\n]*\n",
        "| **Node.js** | **24** (latest patch via `check-latest` on Actions) |\n",
    ),
    (r"Vercel Hobby / free team limits", "Vercel"),
    (r"SonarCloud free \(open-source/free tier limits apply\)", "SonarCloud"),
    (
        r"prefer free hosts \(e\.g\. free Render/Railway/Fly allowances, Supabase free\)",
        "prefer existing hosts (Render/Railway/Fly/Supabase as needed)",
    ),
    (
        r"on \*\*GitHub Free\*\* use free fallback \(see §0\.1\)",
        "use CODEOWNERS + PR reviews when Environment required reviewers are unavailable (see §0.1)",
    ),
    (r"### 0\.1 Free-tier constraint \(source of truth for tool choices\)", "### 0.1 Tooling defaults"),
    (
        r"\*\*Principle:\*\* Prefer \$0 tools and stay within free quotas\. Paid GitHub Team/Enterprise, paid Sonar, paid Vercel Pro, paid Slack, Codecov Pro, Snyk paid, etc\. are \*\*out of default scope\*\*\.",
        "**Principle:** Prefer GitHub Actions, Vercel, and SonarCloud. Use CODEOWNERS/PR gates when Environment required reviewers are unavailable.",
    ),
    (r"Free-friendly choice", "Default choice"),
    (r"Avoid / paid-only", "Notes"),
    (r"GitHub Free org \+ Actions minutes", "GitHub Actions"),
    (r"Features that require Team\+ only", "Plan-dependent features"),
    (
        r"Free fallback: \*\*CODEOWNERS \+ required PR reviews\*\* on `main`; optional `workflow_dispatch` prod deploy",
        "**CODEOWNERS + required PR reviews** on `main`; optional `workflow_dispatch` prod deploy",
    ),
    (
        r"Environment \*\*required reviewers\*\* \(often Team\+; already \*\*HTTP 422\*\* on free\)",
        "Environment **required reviewers** when available",
    ),
    (r"Vercel Hobby", "Vercel"),
    (r"Assuming unlimited team seats / commercial Pro", "—"),
    (
        r"SonarCloud free \+ \*\*in-CI coverage thresholds\*\* \(jest/vitest\)",
        "SonarCloud + **in-CI coverage thresholds** (jest/vitest)",
    ),
    (r"Codecov paid, Sonar enterprise", "Optional third-party coverage hosts"),
    (
        r"`npm audit`, \*\*Dependabot\*\* \(free\), \*\*CodeQL\*\* where free, gitleaks Action, secret scanning on public if applicable",
        "`npm audit`, **Dependabot**, **CodeQL**, gitleaks Action",
    ),
    (r"Snyk paid, commercial DAST", "Optional commercial scanners"),
    (
        r"\*\*git tags\*\* `vX\.Y\.Z` \+ CHANGELOG\.md \(manual or free GH Action\)",
        "**git tags** `vX.Y.Z` + CHANGELOG.md",
    ),
    (r"Paid release platforms", "—"),
    (
        r"\*\*Discord webhook\*\* or free Slack incoming webhook / GitHub email watch",
        "**Discord/Slack webhook** or GitHub notifications",
    ),
    (r"PagerDuty, paid Opsgenie", "Optional incident tools"),
    (r"Free tiers only; sleep/cold-start OK for student/capstone", "Per product host"),
    (r"Always-on paid dynos by default", "—"),
    (r"Actions artifacts \(retention limits\)", "Actions artifacts"),
    (r"Paid package registries", "—"),
    (r"\*\*GitHub Free implications already observed\*\*", "**Plan implications already observed**"),
    (
        r"Org plan is \*\*free\*\* → production Environment \*\*required reviewers\*\* failed with 422\.",
        "Production Environment **required reviewers** may be unavailable depending on plan (HTTP 422 observed).",
    ),
    (r"until then use free prod-gate alternatives below\.", "until then use prod-gate alternatives below."),
    (
        r"\*\*Free prod-gate alternatives \(use now\)\*\*",
        "**Prod-gate alternatives (when env reviewers unavailable)**",
    ),
    (r"free branch protection", "branch protection when available"),
    (r"stricter free manual step", "stricter manual step"),
    (r"deploy staging \(auto, free\)", "deploy staging (auto)"),
    (
        r"\(free gate = PR reviews; Team\+ gate = Environment required reviewers\)",
        "(PR reviews / CODEOWNERS; or Environment required reviewers when available)",
    ),
    (r"\*\*Initial gate \(free-friendly\):\*\*", "**Initial gate:**"),
    (r"no paid Codecov", "optional external coverage hosts"),
    (
        r"raising the bar for free is free, writing the tests is the real cost\.",
        "writing the tests is the real cost.",
    ),
    (r"Canonical free-tier backlog", "Canonical backlog"),
    (r"Vercel free", "Vercel"),
    (r"SonarCloud free org bind", "SonarCloud org bind"),
    (r"jest/vitest \+ Sonar free", "jest/vitest + Sonar"),
    (r"\*\*free:\*\* PR reviews", "PR reviews"),
    (r"Decision: \*\*free tier first for all tools\*\*", "Decision: **Node 24** + current stable Actions"),
    (
        r"\*\(blocked free — use CODEOWNERS/PR reviews instead\)\*",
        "*(use CODEOWNERS/PR reviews if env reviewers unavailable)*",
    ),
    (r"\*\(free — do this\)\*", "*(do this when plan allows)*"),
    (r"SonarCloud free org binding", "SonarCloud org binding"),
    (
        r"Staging vs prod backend/Supabase free-tier projects/credentials",
        "Staging vs prod backend/Supabase projects/credentials",
    ),
    (r"### Should-have soon \(all free\)", "### Should-have soon"),
    (r"### Later \(still free-preferring\)", "### Later"),
    (r"Expo EAS free tier", "Expo EAS"),
    (r"Sentry free tier or skip", "Sentry (optional)"),
    (r"`production` reviewers blocked on free plan", "`production` reviewers when plan allows"),
    (
        r"Env `production` path kept; \*\*free org uses PR reviews/CODEOWNERS\*\* \(required reviewers need Team\+\)",
        "Env `production` path kept; **PR reviews/CODEOWNERS** when required reviewers unavailable",
    ),
    (r"Sonar \| \*\*On\*\* \(free tier\); re-key PAULUS to org", "Sonar | **On**; re-key PAULUS to org"),
    (
        r"\| 10 \| Budget \| \*\*Free for everything\*\* by default \|",
        "| 10 | Node | **24** (latest patch via check-latest) |",
    ),
    (r"Go with free-tier recommendations", "Go with recommendations"),
    (r"free-friendly", "default"),
    (r"free-tier", "standard"),
    (r"Do not plan on:\*\* Codecov Pro, Snyk Team, GitHub Team only for env reviewers, Vercel Pro, paid Slack/APM—unless team upgrades\.",
     "Optional later: external coverage hosts, commercial scanners, incident tools."),
    (r"\*\*Do not plan on:\*\*[^\n]*", "Optional later: external coverage hosts, commercial scanners, incident tools."),
]

for a, b in replacements:
    c = re.sub(a, b, c)

# Remove remaining standalone "free" / "Free"
c = re.sub(r"(?i)\bfree-tier\b", "standard", c)
c = re.sub(r"(?i)\bfree\b", "", c)
c = re.sub(r"  +", " ", c)
c = re.sub(r"\(\s+", "(", c)
c = re.sub(r"\s+\)", ")", c)
c = re.sub(r"\s+,", ",", c)
c = re.sub(r",\s*\.", ".", c)

plan.write_text(c, encoding="utf-8")
text = plan.read_text(encoding="utf-8")
print("remaining free:", len(re.findall(r"(?i)\bfree\b", text)))
for m in re.finditer(r"(?i).{0,50}\bfree\b.{0,50}", text):
    print("...", m.group(0).replace("\n", " "))
print("done")

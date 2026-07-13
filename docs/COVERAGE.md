# Coverage policy (practice bar)

Thresholds are **looser than industry 80%** so teams can practice shipping tests.

## Practice thresholds

| Metric | Practice (CI now) | Industry later |
|--------|-------------------|----------------|
| Lines | **50%** | 80% |
| Statements | **50%** | 80% |
| Functions | **50%** | 80% |
| Branches | **40%** | 75% |
| Sonar new code (UI) | **≥ 60%** | ≥ 80% |

## Where CI enforces it

| Product | Package | How |
|---------|---------|-----|
| capstone-system | `capstone-system/unified` | Node built-in test + `practice/` + `test:coverage` |
| Front-and-back | `Front-End-Dashboard`, `Back-End` | same |
| PAULUS | `src/frontend`, `src/backend` | same (workspaces) |
| prism | API (vitest full suite) + `apps/client` practice | `test:api:coverage` + client `test:coverage` |
| WOOF_V1 | `frontend` practice + `backend` jest | `test:coverage` / `test:cov` |

Each app that did not already have a suite gets a small `practice/` folder (`sum.mjs` + tests).  
**Replace/expand `practice/` with real app tests over time** — keep the same thresholds.

## SonarCloud UI

Set quality gate on **new code** coverage to **≥ 60%** while practicing (raise to 80% later).

# Coverage policy (practice bar)

Teams are learning — thresholds are **looser than industry 80%** so people can practice shipping tests without an impossible cliff.

## CI thresholds (where suites already run)

| Metric | Practice gate | Industry target (later) |
|--------|---------------|-------------------------|
| Lines | **50%** | 80% |
| Statements | **50%** | 80% |
| Functions | **50%** | 80% |
| Branches | **40%** | 75% |

**Enforced today**

| Package | Tool | How |
|---------|------|-----|
| `prism` API | Vitest | `npm run test:api:coverage` + thresholds in `vitest.config.ts` |
| `WOOF_V1/backend` | Jest | `npm run test:cov` + `coverageThreshold` in `package.json` |

**Not enforced yet** (no meaningful suite): capstone-system, Front-and-back, PAULUS frontend, prism frontends, WOOF frontend — report when tests exist; then apply the same practice numbers.

## SonarCloud (you configure in UI)

Recommended quality gate for **new code** while practicing:

| Condition on new code | Practice | Later |
|----------------------|----------|--------|
| Coverage | **≥ 60%** | ≥ 80% |
| Duplications | ≤ 5% | ≤ 3% |
| Maintainability / reliability / security | defaults | tighten as needed |

Industry default is often **80% on new code**; we start lower so green CI is reachable while habits form.

## Raising the bar

1. Keep writing tests on every PR.  
2. When most packages sit comfortably above 50%, bump CI to **60/60/60/50**.  
3. When ready for industry parity, move to **80/80/80/75** and Sonar new code **80%**.

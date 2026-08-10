# Coverage policy

The practice floor remains intentionally below an industry 80% target while the products expand their real test suites.

| Metric | Required practice floor |
|---|---:|
| Lines | 50% |
| Statements | 50% |
| Functions | 50% |
| Branches | 40% |

## Product enforcement

| Product | Required coverage command |
|---|---|
| capstone-system | capstone-system/unified npm run test:coverage |
| Front-and-back | Front-End-Dashboard and Back-End npm run test:coverage |
| PAULUS | frontend and backend workspace coverage commands |
| prism | API coverage plus client, event, guest, and supplier coverage |
| WOOF_V1 | frontend practice coverage and backend Jest coverage |

Each coverage command must fail when its configured threshold fails. Coverage artifacts may be uploaded for review, but must not include environment files or secrets. SonarCloud is not used.

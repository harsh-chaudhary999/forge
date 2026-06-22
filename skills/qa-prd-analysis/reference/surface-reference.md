# qa-prd-analysis — Surface specification reference

**How to specify surfaces for test case generation and execution:**

| Surface | `/qa-write` flag | `/qa-run` flag | Driver used |
|---|---|---|---|
| Web browser | `--surface web` | `--surface web` | `eval-driver-web-cdp` |
| Android app | `--surface android` | `--surface android --env DEVICE_ID=emulator-5554` | `eval-driver-android-adb` |
| iOS app | `--surface ios` | `--surface ios --env IOS_SIMULATOR_ID=booted` | `eval-driver-ios-xctest` |
| REST/GraphQL API | `--surface api` | `--surface api` | `eval-driver-api-http` |
| Database | `--surface db` | `--surface db` | `eval-driver-db-mysql` |
| Cache | `--surface cache` | `--surface cache` | `eval-driver-cache-redis` |
| All surfaces | `--surface all` | `--surface all` | all drivers |
| Web + API only | `--surface web,api` | `--surface web,api` | web-cdp + api-http |

**Surface selection in this analysis step** determines which **Surface** values appear in **`qa/semantic-automation.csv`** and how hosts filter execution. The **`--surface`** flag on **`/qa-run`** filters which surfaces run.

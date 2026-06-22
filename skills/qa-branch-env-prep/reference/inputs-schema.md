# qa-branch-env-prep — Inputs schema

The skill accepts a structured input — either provided inline or read from
`~/forge/brain/prds/<task-id>/qa-run-config.yaml` if it exists:

```yaml
task_id: PRD-042
slug: shopapp                       # product slug — resolves repos from product.md
run_mode: url-only | branch-local | branch-code-validate | branch-tracking

# For branch-local, branch-code-validate, and branch-tracking: branch overrides per repo
branches:
  backend-api: feature/payment-v2
  web-dashboard: feature/payment-ui

# For branch-code-validate: test commands per repo (if not in product.md)
test_commands:
  backend-api: "npm test"
  web-dashboard: "npm run test:unit"
  # Fallback: if absent, read test_command from product.md Projects section for that repo

# Runtime env — injected into .eval-env for eval drivers (branch-local / url-only only)
env:
  BASE_URL: https://staging.shopapp.com
  API_BASE_URL: https://api.staging.shopapp.com
  DB_DSN: mysql://root:root@localhost:3306/shopapp_test
  REDIS_URL: redis://localhost:6379/1
  DEVICE_ID: emulator-5554
  IOS_SIMULATOR_ID: booted
  TEST_USER_EMAIL: qa@example.com
  TEST_USER_PASSWORD: qapassword123
```

**Required minimum per mode:**
- `url-only`: `task_id`, `slug`, `run_mode`, `BASE_URL`
- `branch-local`: `task_id`, `slug`, `run_mode`, at least one `branches` entry
- `branch-code-validate`: `task_id`, `slug`, `run_mode`, at least one `branches` entry (test commands from `product.md` or `test_commands` override)
- `branch-tracking`: `task_id`, `slug`, `run_mode`, `BASE_URL`, at least one `branches` entry

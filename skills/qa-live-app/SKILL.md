---
name: qa-live-app
description: "WHEN: A feature has shipped to staging or preview and you need to verify approved QA test cases against the live URL. Run after deployment, before sign-off."
type: flexible
version: 1.0.0
preamble-tier: 3
triggers:
  - "test against live"
  - "QA staging"
  - "verify on staging"
  - "run QA on live app"
  - "smoke test live"
allowed-tools:
  - Bash
---

# qa-live-app

Runs approved QA test cases from `manual-test-cases.csv` against a live application URL. Bridges the gap between the CSV acceptance inventory and actual live-environment verification.

**Not the same as forge-eval-gate:** eval-gate drives a local stack with automated multi-surface drivers. qa-live-app targets a live external URL and walks the approved test cases one by one.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "Eval passed, we don't need live app QA" | Eval runs against a local stack. Live staging has different config, different data, different infra. Different environment = different failures. |
| "I'll do it manually in the browser" | Manual checks leave no record. qa-live-app writes results to brain so they're traceable. |
| "The CSV is just documentation, not executable" | Approved CSV rows are the acceptance inventory. They must be verified, not assumed. |
| "One journey is enough to check" | Partial verification is incomplete verification. Run all approved rows unless explicitly scoped with --journey. |

**Read the CSV. Hit the URL. Write the results.**

## Invocation Modes

- `/qa-live-app <base-url>` — runs all approved test cases against the given URL
- `/qa-live-app <base-url> --journey <journey-id>` — runs only cases for a specific journey
- `/qa-live-app status` — shows path to last run results in brain

## Workflow

### For `/qa-live-app status`

```bash
BRAIN_DIR="${FORGE_BRAIN_PATH:-$HOME/forge/brain}"
TASK_DIR=$(ls -td "$BRAIN_DIR/prds"/*/ 2>/dev/null | head -1)
RESULTS_DIR="$TASK_DIR/qa-live-results"

if [ -d "$RESULTS_DIR" ] && [ "$(ls -A "$RESULTS_DIR" 2>/dev/null)" ]; then
  LAST=$(ls -1 "$RESULTS_DIR"/*.md 2>/dev/null | sort -r | head -1)
  echo "Last QA live run: $LAST"
  cat "$LAST"
else
  echo "No qa-live-app results found. Run /qa-live-app <base-url> first."
fi
```

Stop after displaying.

### For `/qa-live-app <base-url>` and `/qa-live-app <base-url> --journey <id>`

**Step 1 — Verify base URL is reachable:**

```bash
BASE_URL="<user-provided base URL>"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$BASE_URL" 2>/dev/null)
if [ "$HTTP_STATUS" = "000" ] || [ -z "$HTTP_STATUS" ]; then
  echo "ERROR: $BASE_URL is not reachable (no response). Verify the URL and try again."
  exit 1
fi
echo "Base URL reachable: $BASE_URL (HTTP $HTTP_STATUS)"
```

**Step 2 — Find and read the QA CSV:**

```bash
BRAIN_DIR="${FORGE_BRAIN_PATH:-$HOME/forge/brain}"
TASK_DIR=$(ls -td "$BRAIN_DIR/prds"/*/ 2>/dev/null | head -1)
TASK_ID=$(basename "$TASK_DIR")
QA_CSV=$(find "$TASK_DIR" -name "*.csv" 2>/dev/null | head -1)

if [ -z "$QA_CSV" ]; then
  echo "ERROR: No QA CSV found under $TASK_DIR. Run /qa-manual-test-cases-from-prd first."
  exit 1
fi

echo "QA CSV: $QA_CSV"
APPROVED_COUNT=$(grep -ci "approved" "$QA_CSV" 2>/dev/null || echo "0")
echo "Approved test cases: $APPROVED_COUNT"
```

**Step 3 — Read and group test cases by journey:**

Read the CSV rows where status is `approved`. If `--journey <id>` was provided, filter to rows matching that journey ID. Group the remaining rows by their Journey ID column.

For each test case row, extract: ID, Journey ID, Title, Steps, Expected Result.

**Step 4 — Execute test cases:**

For each test case in each journey group:

- **API test cases** (where Steps contain a URL path like `/api/`, `GET`, `POST`):
  ```bash
  # Example: test case steps contain "POST /api/auth/register with body {...}"
  RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"TestPass123!"}' \
    --max-time 15 2>/dev/null)
  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  BODY=$(echo "$RESPONSE" | head -n -1)
  # Compare HTTP_CODE and BODY against Expected Result
  ```

- **Web/UI test cases** (where Steps describe browser actions):
  - If `/eval-driver-web-cdp` is available: delegate to it
  - Otherwise: mark as MANUAL-REQUIRED and skip with a note

- **Visual check steps**: always mark as MANUAL-REQUIRED

For each test case, record: ID, PASS / FAIL / MANUAL-REQUIRED, actual result if FAIL.

**Step 5 — Write results to brain:**

```bash
RESULTS_DIR="$TASK_DIR/qa-live-results"
mkdir -p "$RESULTS_DIR"
TIMESTAMP=$(date -u +"%Y%m%d-%H%M%S")
SLUG=$(echo "$BASE_URL" | sed 's|https\?://||' | sed 's/[^a-z0-9-]/-/g' | cut -c1-30)
RESULT_FILE="$RESULTS_DIR/${TIMESTAMP}-${SLUG}.md"
```

Write the results file with this structure:

```markdown
---
base_url: <BASE_URL>
timestamp: <ISO8601>
task_id: <TASK_ID>
total: <N>
passed: <N>
failed: <N>
manual_required: <N>
---

# QA Live App Results

Base URL: <BASE_URL>
Run: <timestamp>

## Results by Journey

### <Journey ID>: <Journey Name>

| ID | Title | Result | Notes |
|----|-------|--------|-------|
| TC-001 | <title> | ✓ PASS | |
| TC-002 | <title> | ✗ FAIL | expected 200, got 500 |

## Summary

<N>/<total> passed. <N> failed. <N> manual-required.
```

Fill with actual test results. Do not write placeholder cells.

**Step 6 — Output summary:**

```
QA LIVE APP RESULTS
Base URL: <BASE_URL>
Run:      <timestamp>

<per-journey results table>

Summary: <passed>/<total> passed (<failed> failure(s), <manual_required> manual-required)
Results: <RESULT_FILE>
```

If any test failed: append `Action required: investigate failing test cases before sign-off.`

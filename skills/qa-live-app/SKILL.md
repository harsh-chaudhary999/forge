---
name: qa-live-app
description: "WHEN: A feature has shipped to staging or preview and you need to verify approved QA test cases against the live URL. Run after deployment, before sign-off."
type: flexible
version: 1.1.0
preamble-tier: 4
triggers:
  - "test against live"
  - "QA staging"
  - "verify on staging"
  - "run QA on live app"
  - "smoke test live"
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
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

Trigger by asking (no dedicated slash command ships for this skill):

- "run QA on live app `<base-url>`" — verify every CSV row against the given URL
- "...`<base-url>` for feature `<name>`" — filter to rows whose **Feature Categorization** matches `<name>`
- "qa-live-app status" — show the path to the last run's results in brain

## Workflow

### For `/qa-live-app status`

```bash
BRAIN_DIR="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}"
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
echo "Base URL: $BASE_URL (HTTP ${HTTP_STATUS:-no-response})"
```

If `HTTP_STATUS` is `000`/empty, **STOP** — do **not** `exit` (these blocks run in the
agent's own shell; `exit` would kill the session). Use **`AskUserQuestion`** to offer:
retry, fix the URL, or abort. Proceed only once the URL responds.

**Step 2 — Find and read the QA CSV:**

```bash
BRAIN_DIR="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}"
# Confirm the active task-id (set FORGE_TASK_ID when multiple tasks exist).
TASK_ID="${FORGE_TASK_ID:-$(ls -td "$BRAIN_DIR/prds"/*/ 2>/dev/null | head -1 | xargs -r basename)}"
TASK_DIR="$BRAIN_DIR/prds/$TASK_ID"
QA_CSV="$TASK_DIR/qa/manual-test-cases.csv"   # canonical path, not a *.csv glob

echo "Task: $TASK_ID"
if [ ! -f "$QA_CSV" ]; then
  echo "MISSING: $QA_CSV"
fi
# Count DATA rows (not a bogus "approved" substring grep — there is no approval column;
# approval is the qa-manual-test-cases-from-prd Step-7 count gate, recorded by commit).
ROWS=$(tail -n +2 "$QA_CSV" 2>/dev/null | grep -c . || echo 0)
echo "QA CSV: $QA_CSV  (data rows: $ROWS)"
```

If `qa/manual-test-cases.csv` is absent, **STOP** (do not `exit`) and use
**`AskUserQuestion`**: run `qa-manual-test-cases-from-prd` first, point at a
different task-id, or abort.

**Step 3 — Read and group test cases:**

Read the CSV with the canonical 8-column schema (`qa-manual-test-cases-from-prd`):
`Id, Platform, Summary, Description, Expected Result, Automatable, Type, Feature Categorization`
(plus optional `Preconditions`, `Source`). There is **no** `Journey`, `Steps`, or
`status` column — run **all** data rows. If a feature filter was given, keep rows whose
**Feature Categorization** matches. Group the remaining rows by **Feature Categorization**.

For each row, use: `Id`, `Platform`, `Summary`, `Description` (the numbered action
steps), `Expected Result`, and `Preconditions` (setup) when present.

**Step 4 — Execute test cases:**

For each test case in each feature group, branch on the **Platform** column:

- **API test cases** (`Platform` = `API`, or `Description` contains `/api/`, `GET`, `POST`):
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

- **Web/UI test cases** (`Platform` = `Web`, or `Description` describes browser actions):
  - If `eval-driver-web-cdp` (CDP) is available: drive it; for visual/UI cases, **capture a screenshot, Read it, and render a model-judged PASS/FAIL** with the image path as evidence.
  - Otherwise: mark as MANUAL-REQUIRED with a note.

- **Visual checks with no CDP**: mark MANUAL-REQUIRED. (Reserve MANUAL-REQUIRED only for cases that genuinely cannot be screenshot-judged — e.g. native-device-only behavior.)

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
type: eval
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

---

### Evidence HARD-GATE (Before Claiming QA Complete)

**HARD-GATE: You cannot claim QA complete or mark test cases as passed without the following artifacts:**

1. **Results file written to brain** — the **single** canonical artifact is the
   Step 5 file at `$TASK_DIR/qa-live-results/<timestamp>-<slug>.md` (with `type: eval`
   frontmatter). Do **not** write a second copy under `qa/logs/`. Update the
   `qa-live-results/index.md` row and append a dated `log.md` entry (OKF conventions,
   per `forge-brain-layout`).

2. **Every CSV data row executed** — not sampled. Every row in
   `qa/manual-test-cases.csv` must have a result row (PASS / FAIL / MANUAL-REQUIRED /
   SKIPPED). (There is no `approved` column — approval was the
   `qa-manual-test-cases-from-prd` Step-7 count gate.)

3. **Results committed to brain** — `git -C ~/forge/brain add` the
   `qa-live-results/` file + index.md + log.md and commit (the discipline the
   `brain-write` / `forge-brain-persist` skills describe).

4. **Claiming "tested and works" without these artifacts is a skill violation.**

If any test case cannot be executed (environment issue, surface unavailable): mark it `SKIPPED` with reason — do not omit it.

## Cross-References

- `qa-manual-test-cases-from-prd`: Produces the `qa/manual-test-cases.csv` (8-column acceptance inventory) that this skill reads and verifies against the live URL.
- `qa-prd-analysis`: Produces the coverage plan that determined which cases the CSV contains.
- `eval-driver-web-cdp`: Web/UI cases delegate to it when CDP is available (screenshot + DOM assertions); otherwise they are MANUAL-REQUIRED.
- `forge-eval-gate`: The local-stack automated eval gate — distinct from this live-URL walk (this skill does NOT produce a semantic-eval manifest).
- `forge-brain-layout`: results frontmatter follows the OKF `type:`/index.md/log.md conventions used under the task dir.

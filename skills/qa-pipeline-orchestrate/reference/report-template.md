# QA-P7 — Report template

The `qa-run-report-<ts>.md` body (full-execution variant):

```markdown
---
task_id: <task-id>
run_at: <ISO8601>
execution_scope: full | static_only
product_verdict: GREEN | RED | YELLOW | null
pipeline_verdict: GREEN | RED | YELLOW | NOT_EXECUTED
verdict: GREEN | RED | YELLOW | NOT_EXECUTED
brain_git_sha: <git -C ~/forge/brain rev-parse HEAD>
forge_task_id_env: <FORGE_TASK_ID or empty>
flake_suspected: false | true
static_validation: PASS | FAIL | SKIPPED | null
# Optional — set when terminology.md exists (see Phase QA-P7 body text)
terminology_status: draft | review | locked | null
terminology_open_doubts: none | pending | null
---

# QA Run Report

**task_id:** <task-id>
**run_at:** <ISO8601>
**execution_scope:** full | static_only
**product verdict (GREEN/RED/YELLOW):** … or **N/A — drivers did not run**
**pipeline verdict:** GREEN | RED | YELLOW | **NOT_EXECUTED**
**duration:** <total seconds>

## Branch State

| Repo | Branch | SHA |
|---|---|---|
| backend-api | feature/payment-v2 | a1b2c3d |
| web-dashboard | feature/payment-ui | e4f5a6b |

## Environment

| Variable | Value |
|---|---|
| BASE_URL | http://localhost:3000 |
| DEVICE_ID | emulator-5554 |

## Scenario Results

| Scenario ID | Surface | Status | Duration | Notes |
|---|---|---|---|---|
| SC-AUTH-001 | web + api + db | PASS | 2.4s | |
| SC-AUTH-001-negative | web | PASS | 0.8s | |
| SC-PAYMENT-001 | web + api + db | FAIL | 5.1s | DB row not written after checkout |

## Failures (if any)

### SC-PAYMENT-001 — FAIL
- **Step:** DB verification — `SELECT * FROM orders WHERE user_id = ...`
- **Expected:** 1 row
- **Got:** 0 rows
- **Evidence:** screenshot `eval-evidence/SC-PAYMENT-001-step-4.png`
- **Classification:** functional regression — backend did not persist order on checkout

## Next Actions

- [ ] Fix: `backend-api/src/services/payment.service.ts` — order persistence missing `await`
- [ ] Re-run `/qa-run` after fix to verify GREEN
```

**When `execution_scope: static_only`** — add the two sections below. Tone:
**expected limitation**, not failure.

```markdown
## Why automation did not run

| Gate | Status | Meaning |
|---|---|---|
| QA-P4 | SKIP | Stack-up not executed — nothing to open in browser or on device |
| QA-P5 | SKIP | Eval drivers not invoked — no resolved env / no stack |
| QA-P6 | NOT_EXECUTED | No driver payload for `eval-judge` — **not** the same as YELLOW |

## How to obtain GREEN / RED / YELLOW

1. Provide **`BASE_URL`** (or run mode **`url-only`** / **`branch-local`**) and any **`DEVICE_ID`** / simulator IDs required by scenarios.
2. Re-run **`/qa-run <task-id>`** from an environment that can start or reach the stack.
```

Commit to brain:
```bash
git -C ~/forge/brain add prds/<task-id>/qa/
git -C ~/forge/brain commit -m "qa: run report <task-id> — verdict=<GREEN|RED|YELLOW|NOT_EXECUTED>"
```

Log:
```
[QA-P7-REPORT] task_id=<task-id> report=qa/qa-run-report-<ts>.md status=COMMITTED
```

## Full Pipeline Log (end state)

At completion, `qa-pipeline.log` must contain phase gate lines in order. **Full execution path** example:

```
[QA-P1-LOAD]       task_id=PRD-042 ...
[QA-P2-SCENARIOS]  task_id=PRD-042 ...
[QA-BRANCH-ENV]    task_id=PRD-042 ...
[QA-P4-STACK]      task_id=PRD-042 ...
[QA-P5-EXEC]       task_id=PRD-042 ...
[QA-P6-VERDICT]    task_id=PRD-042 verdict=GREEN
[QA-P7-REPORT]     task_id=PRD-042 ...
```

**Static-only / execution blocked** path is valid when documented: QA-P4 or QA-P5 may log **SKIP**, then **`[QA-P6-VERDICT] … verdict=NOT_EXECUTED`** — still complete if QA-P7 records **`execution_scope: static_only`** and explains the gap. Do not treat **NOT_EXECUTED** as **YELLOW**.

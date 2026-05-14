# Semantic Eval Artifact Schema

Documents the JSON structure of `semantic-eval-manifest.json` and `semantic-eval-run.log` written by the Forge semantic evaluation pipeline.

**Brain paths:**
- `~/forge/brain/prds/<task-id>/qa/semantic-eval-manifest.json`
- `~/forge/brain/prds/<task-id>/qa/semantic-eval-run.log`

---

## semantic-eval-manifest.json

Written once per eval run. Machine gate artifact read by `eval-judge` and `verify_forge_task.py`.

```json
{
  "schema_version": 1,
  "kind": "semantic-csv-eval",
  "task_id": "<task-id>",
  "outcome": "pass | fail | yellow | RED_INFRA",
  "recorded_at": "YYYY-MM-DDTHH:MM:SSZ",
  "csv_path": "qa/semantic-automation.csv",
  "run_log_path": "qa/semantic-eval-run.log",
  "step_count": 12,
  "passed": 10,
  "failed": 1,
  "skipped": 1,
  "driver": "noop | web-cdp | api-http | android-adb | ios-xctest | bus-kafka | db-mysql | cache-redis | search-es"
}
```

**Field definitions:**

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | integer | yes | Always `1` for current format |
| `kind` | string | yes | Always `"semantic-csv-eval"` for CSV-driven eval |
| `task_id` | string | yes | Forge task identifier |
| `outcome` | enum | yes | `pass` = all steps PASS; `fail` = any FAIL; `yellow` = CONTEXT_GAP or BLOCKED_DEPENDENCY present; `RED_INFRA` = infrastructure failure |
| `recorded_at` | ISO-8601 UTC | yes | Timestamp when manifest was written |
| `csv_path` | string | yes | Relative path to the source CSV |
| `run_log_path` | string | yes | Relative path to the run log |
| `step_count` | integer | yes | Total rows in the CSV |
| `passed` | integer | yes | Steps with outcome PASS |
| `failed` | integer | yes | Steps with outcome FAIL |
| `skipped` | integer | no | Steps with SKIPPED (surface unavailable) |
| `driver` | string | yes | Which driver executed the steps |

---

## semantic-eval-run.log

Append-only JSON-lines file. One JSON object per line per step execution.

```json
{"stepId": "step-001", "surface": "web", "intent": "User logs in", "outcome": "PASS", "result": {"sessionToken": "tok_abc"}, "durationMs": 234, "recordedAt": "YYYY-MM-DDTHH:MM:SSZ"}
{"stepId": "step-002", "surface": "api", "intent": "Create resource", "outcome": "BLOCKED_DEPENDENCY", "blockedBy": "step-001", "reason": "step-001 failed", "result": {}, "recordedAt": "YYYY-MM-DDTHH:MM:SSZ"}
{"stepId": "step-003", "surface": "web", "intent": "Verify resource shown", "outcome": "CONTEXT_GAP", "blockedBy": "step-002", "reason": "dependency passed but result was empty", "result": {}, "recordedAt": "YYYY-MM-DDTHH:MM:SSZ"}
```

**Outcome enum values:**

| Outcome | Meaning |
|---|---|
| `PASS` | Step executed and assertions passed |
| `FAIL` | Step executed and assertions failed (product bug) |
| `BLOCKED_DEPENDENCY` | Dependency step failed or was blocked — this step skipped |
| `CONTEXT_GAP` | Dependency passed but returned empty `result: {}` — step attempted without interpolation |
| `SKIPPED` | Surface not available on this host (e.g., iOS on Linux) |

**Required fields per line:**

| Field | Type | Required | Description |
|---|---|---|---|
| `stepId` | string | yes | Matches `Id` column in `semantic-automation.csv` |
| `surface` | string | yes | `web`, `api`, `mobile`, `db`, `cache`, `search`, `bus` |
| `intent` | string | yes | Human-readable description of what was tested |
| `outcome` | enum | yes | See table above |
| `result` | object | yes | Step output data (may be `{}` if no data returned) |
| `recordedAt` | ISO-8601 UTC | yes | When the step completed |
| `durationMs` | integer | no | Execution time in milliseconds |
| `blockedBy` | string | conditional | Required when outcome is `BLOCKED_DEPENDENCY` or `CONTEXT_GAP` |
| `reason` | string | conditional | Required when outcome is not `PASS` |

---

## Verdict Logic (eval-judge)

| manifest.outcome | run.log contains | eval-judge verdict |
|---|---|---|
| `pass` | all PASS | GREEN |
| `pass` | any CONTEXT_GAP or BLOCKED_DEPENDENCY | YELLOW (incomplete execution) |
| `fail` | any FAIL | RED |
| `fail` | all non-PASS are BLOCKED_DEPENDENCY | YELLOW (dependency issue, not code bug) |
| `yellow` | mixed | YELLOW |
| `RED_INFRA` | any | RED_INFRA — escalate, no retry |

## Related Skills

- `qa-semantic-csv-orchestrate` — writes this manifest and log
- `eval-judge` — reads manifest + log to produce verdict
- `eval-product-stack-up` — orchestrates driver runs
- `verify_forge_task.py` — validates manifest schema and coherence with CSV

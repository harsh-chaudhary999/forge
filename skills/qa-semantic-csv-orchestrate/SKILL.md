---
name: qa-semantic-csv-orchestrate
description: "WHEN: Primary machine-eval path — NL-first automation (semantic-automation.csv): validate DependsOn, run the host driver loop, write semantic-eval-manifest.json + semantic-eval-run.log (CSV execution results) + conductor [P4.0-SEMANTIC-EVAL]."
type: rigid
requires: [brain-read, brain-write, forge-brain-layout, forge-verification]
version: 1.0.1
preamble-tier: 3
triggers:
  - "semantic eval csv"
  - "run semantic automation"
  - "semantic-automation.csv"
  - "P4.0-SEMANTIC-EVAL"
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - AskUserQuestion
  - mcp__*
---

# QA Semantic CSV Orchestrate

**Human input:** **`AskUserQuestion`** (in **`allowed-tools`**) is the canonical blocking affordance — see **[`skills/_shared/human-input.md`](../_shared/human-input.md)**.

Execute the **semantic automation** path: **`qa/semantic-automation.csv`** → validate DAG → run host driver → **`qa/semantic-eval-manifest.json`** + **`qa/semantic-eval-run.log`** → log **`[P4.0-SEMANTIC-EVAL]`** in **`conductor.log`**.

**Canonical schema:** **`docs/semantic-eval-csv.md`**. **Parser / surfaces:** **`tools/verify/semantic_csv.py`**. **CLI:** **`python3 tools/run_semantic_csv_eval.py`** (shim → **`tools/verify/run_semantic_csv_eval.py`** — implementation).

**HARD-GATE (host):** Before wiring **real** CDP, ADB, or MCP execution, ask the operator **MCP vs local driver** (and for mobile, **Appium MCP vs ADB vs XCTest**) per **CLAUDE.md** D5 — record the choice in the task brain.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I'll skip CSV validation — the manifest looks fine" | **`verify_forge_task.py`** validates **`semantic-automation.csv`** when present or when manifest **`kind`** is **`semantic-csv-eval`**. Bad DAG or typos fail CI. |
| "Semantic means no logs" | **Invalid.** Append **`qa/semantic-eval-run.log`** and a minimal **`semantic-eval-manifest.json`** — honesty gate for machine verification. |
| "I'll log [P4.0-SEMANTIC-EVAL] before the CSV exists" | Same ordering discipline as YAML: automation marker **after** the artifact path is real on disk. |
| "Default noop driver proves the product works" | **Noop** only proves **structure**; use **`--dry-run`** + **`outcome: yellow`** or run real drivers on the host for GREEN proof. |
| "YAML scenes cover it — I don't need CSV rows" | If **`verify_forge_task`** expects **`semantic-csv-eval`** for this task, missing or stale **`semantic-automation.csv`** still **fails** the gate — policy is per task, not assumed. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
VALIDATE semantic-automation.csv (tools/verify/semantic_csv.py OR run_semantic_csv_eval.py) BEFORE CLAIMING SEMANTIC EVAL COMPLETE.
WRITE semantic-eval-manifest.json WITH kind=semantic-csv-eval WHEN THIS PATH IS THE MACHINE EVAL ARTIFACT.
LOG [P4.0-SEMANTIC-EVAL] AFTER MANIFEST + CSV ARE ON DISK (TIMESTAMPED ISO-8601 UTC PER conductor-orchestrate).
ASK THE HUMAN FOR DRIVER STRATEGY (MCP vs LOCAL) BEFORE IMPLEMENTING REAL BROWSER/DEVICE AUTOMATION — D5.
```

## Procedure

1. **Load brain paths** — **`~/forge/brain/prds/<task-id>/qa/semantic-automation.csv`** (see **`forge-brain-layout`**). Prefer the read-only brain MCP when connected (`brain_read`/`brain_list` to locate the CSV + manifest, `brain_conductor_status` to confirm prior phase markers); fall back to `cat`/`ls`. If missing and the task chose semantic path, **STOP** — author CSV per **`docs/semantic-eval-csv.md`**.
2. **Validate locally** — From Forge repo root:  
   `python3 tools/run_semantic_csv_eval.py --task-id <id> --brain <brain> --dry-run`  
   Fix reported errors (unknown **Surface**, **DependsOn** cycles, unknown **Id** references).
3. **Host driver** — Default CLI **`noop`** records structure. For real execution, extend the operator environment (Playwright, **`eval-driver-*` skills**, MCP tools) **outside** Forge plugin core; keep **Intent** + **Surface** as the contract rows.
4. **Write artifacts** — Runner writes **`qa/semantic-eval-manifest.json`** (**`schema_version`**: **1**, **`kind`**: **`semantic-csv-eval`**, **`outcome`**, **`recorded_at`**). Append **`qa/semantic-eval-run.log`** (JSON lines per step).
5. **Conductor marker** — Append to **`conductor.log`**:  
   `YYYY-MM-DDTHH:MM:SSZ [P4.0-SEMANTIC-EVAL] task_id=<id> kind=semantic-csv-eval outcome=<pass|fail|yellow|red_infra> manifest=qa/semantic-eval-manifest.json`

   **`red_infra`** = the stack/driver/MCP was unreachable (ECONNREFUSED, Docker down, device offline) — an infrastructure failure, **not** a product-code failure. `eval-judge` renders it YELLOW (not RED) and self-heal-triage handles it per the RED_INFRA path; do not log it as `fail`.
6. **Verify** — Run **`python3 tools/verify/verify_forge_task.py --task-id <id> --brain <brain>`** and confirm exit **0**.

### Pre-Invocation Checklist: Do I Need This Skill?

- [ ] The task is using **`qa/semantic-automation.csv`** as the automation surface, **or** **`verify_forge_task.py`** / product policy expects **`kind: semantic-csv-eval`**.
- [ ] **`docs/semantic-eval-csv.md`** schema is the source of truth for columns (**Id**, **Surface**, **DependsOn**, etc.).
- [ ] You can run **`python3 tools/run_semantic_csv_eval.py`** from the Forge repo (or **`tools/verify/run_semantic_csv_eval.py`** directly).

If any NO: **STOP** — this skill is the machine-eval path; fix prerequisites or defer automation.

### Pre-Implementation Checklist: Am I Ready?

- [ ] **`~/forge/brain/prds/<task-id>/qa/semantic-automation.csv`** exists or is about to be written with valid headers.
- [ ] Task **`task_id`** and **`--brain`** root are correct for **`verify_forge_task.py`**.
- [ ] Operator answered **MCP vs local** (and mobile driver choice) **before** real automation — **D5**.
- [ ] **`forge-brain-layout`** paths for **`qa/`** (including **`logs/`**) are understood.

If any NO: **STOP** — fix inputs before claiming semantic eval.

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] **`semantic-automation.csv`** validates (**`--dry-run`** clean) and **`semantic-eval-manifest.json`** matches **`docs/forge-task-verification.md`**.
- [ ] **`semantic-eval-run.log`** appended for this run.
- [ ] **`[P4.0-SEMANTIC-EVAL]`** line exists in **`conductor.log`** **after** artifacts on disk.
- [ ] **`verify_forge_task.py`** exit **0** for this task/brain.
- [ ] No placeholder **Intent** rows: semantic path must be honest executable automation per **`docs/semantic-eval-csv.md`**.

If any NO: machine gate or conductor discipline failed — fix before merge.

## Red Flags — STOP

- **`DependsOn`** cycle or unknown **Id** reference — the `--dry-run` validator reports the cycle path (e.g., "Cycle: step-5 → step-8 → step-12 → step-5"). **Resolution options:**
  1. **Extract shared setup**: If steps 5 and 8 both need the same precondition, create a new `step-setup` that both depend on. Break the cycle by removing the mutual dependency.
  2. **Reorder the CSV**: If step 12 does not actually need step 5's output, remove `DependsOn: step-5` from step 12.
  3. **Merge steps**: If steps are truly inseparable, merge them into one atomic step with a compound Intent.
  Never proceed to real driver execution with a DependsOn cycle — results are undefined.
- **`semantic-eval-manifest.json`** **`kind`** is **`semantic-csv-eval`** but **`semantic-automation.csv`** is missing.
- Logging **`[P4.1-DISPATCH]`** before **`[P4.0-SEMANTIC-EVAL]`** when **`conductor.log`** is in use.
- Declaring semantic **GREEN** when only **`noop`** / **`--dry-run`** ran and product proof was required.
- **`FORGE_SEMANTIC_DRIVER`** or MCP secrets committed into **`conductor.log`** or **`semantic-eval-run.log`** — **redact** first.

## Edge Cases

| Scenario | Action | Why naive approach fails |
|---|---|---|
| Manifest **`outcome`** contradicts **`semantic-eval-run.log`** | Reconcile or **RED** — **`eval-judge`** requires consistent evidence. | Shipping on mismatched logs is false GREEN. |
| CSV references **Surface** not supported on this host (e.g. iOS on Linux) | Mark step **SKIPPED** in log with reason; document **N/A** in manifest outcome or narrow **`qa-analysis.md`** surfaces. | Blind **FAIL** blocks honest partial verification. |
| Stack / driver / MCP unreachable (ECONNREFUSED, Docker down, device offline) | Record per-step `status: BLOCKED_DEPENDENCY` and set manifest **`outcome=red_infra`**; escalate per **self-heal-triage** RED_INFRA path. | Logging infra failure as `fail` triggers product-bug self-heal on a healthy product. |
| **`DependsOn`** references a step **Id** in **`manual-test-cases.csv`** only | Ensure **`Id`** exists in **`semantic-automation.csv`** — DependsOn targets **CSV row Ids**, not TMS strings alone. | Resolver returns unknown Id → validation failure. |
| Large CSV (>100 rows) | Validate with **`semantic_csv.py`** first; batch driver runs with timeouts per **`eval-driver-*`** policy. | Timeouts mid-run without structured **SKIPPED** look like product bugs. |
| Operator refuses MCP — only local ADB | Record brain decision; use **`eval-driver-android-adb`** / CDP on host; keep **`semantic-eval-run.log`** evidence of driver choice. | **D5** violation if automation is assumed without recorded choice. |

### DependsOn Result Marshaling Contract

When step B lists `DependsOn: step-A-id`, the driver must pass step A's result to step B's execution context:

**Step result format (all drivers return).** Per-step uses **`status`** (matching the
shipped runner `run_semantic_csv_eval.py`, which emits per-step `status` =
`PASSED`/`VALIDATED`/`SKIPPED`/`FAILED`); the **top-level manifest** aggregates to
**`outcome`** (`pass`/`fail`/`yellow`) — that is the field `eval-judge` reads. Do not
confuse the two. Canonical schema: [`docs/semantic-eval-schema.md`](../../docs/semantic-eval-schema.md).
```json
{
  "stepId": "step-create-user",
  "surface": "api",
  "status": "PASSED",
  "result": {
    "userId": "user_abc123",
    "email": "test@example.com"
  }
}
```

**Result injection in CSV Intent field:** Reference a prior step's result value using `${stepId.result.fieldName}`:
```
Intent: "Log in as user created in step-create-user: email=${step-create-user.result.email}"
```

The driver resolves `${...}` references from the `semantic-eval-run.log` before executing the step. If the referenced step has no result or failed, the dependent step is classified `BLOCKED_DEPENDENCY` (not FAIL or PASS).

**Cross-surface marshaling:** Web driver returns DOM text; API driver returns JSON. Drivers are responsible for JSON-serializing their results into the standard format above. A web CDP step extracting a field value must produce:
```json
{ "result": { "fieldValue": "extracted text here" } }
```

**Missing result:** If step A passes but `result` is empty `{}`, and step B depends on A's result data, classify step B as `CONTEXT_GAP` — flag in run.log, continue to next step.

## Cross-References

**Prerequisite / layout**

- [**forge-brain-layout**](/skills/forge-brain-layout/SKILL.md) — **`qa/`**, **`semantic-automation.csv`**, manifest paths.
- [**forge-verification**](/skills/forge-verification/SKILL.md) — run verifier before claiming pass.

**Manual QA traceability**

- [**qa-manual-test-cases-from-prd**](/skills/qa-manual-test-cases-from-prd/SKILL.md) — optional **`TraceToCsvId`** links semantic steps to **`manual-test-cases.csv`** rows.

**Pipeline**

- [**qa-pipeline-orchestrate**](/skills/qa-pipeline-orchestrate/SKILL.md) — invokes this path at QA-P2 / QA-P5 per **`docs/forge-task-verification.md`**.

**Verification doc**

- [**docs/forge-task-verification.md**](/docs/forge-task-verification.md) — manifest schema, coherence with **`conductor.log`**.

## Output

| Artifact | Purpose |
|---|---|
| **`~/forge/brain/prds/<task-id>/qa/semantic-automation.csv`** | Step DAG + surfaces — source for runner |
| **`~/forge/brain/prds/<task-id>/qa/semantic-eval-manifest.json`** | Machine gate outcome (**`kind: semantic-csv-eval`**) |
| **`~/forge/brain/prds/<task-id>/qa/semantic-eval-run.log`** | Per-step transcript |
| **`~/forge/brain/prds/<task-id>/conductor.log`** (append) | **`[P4.0-SEMANTIC-EVAL]`** line |

**Verifier:** **`python3 tools/verify/verify_forge_task.py --task-id <id> --brain <brain>`** must exit **0** before merge readiness when this path is authoritative.

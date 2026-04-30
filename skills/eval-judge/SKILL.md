---
name: eval-judge
description: "WHEN: Phase 4.4 needs a final pass/fail verdict from qa/semantic-eval-manifest.json outcome + qa/semantic-eval-run.log (semantic CSV execution). Renders GREEN/RED/YELLOW."
type: rigid
requires: [brain-read]
version: 2.0.0
preamble-tier: 3
triggers:
  - "judge eval results"
  - "get eval verdict"
  - "final eval verdict"
  - "eval pass or fail"
allowed-tools:
  - Bash
  - Read
  - Write
---

# Eval Judge (HARD-GATE)

Forge machine-eval evidence is **only** the semantic path: **`qa/semantic-eval-manifest.json`** and **`qa/semantic-eval-run.log`** after **`qa-semantic-csv-orchestrate`** / **`tools/run_semantic_csv_eval.py`** with stack up (**`eval-product-stack-up`**). Host tools map **`qa/semantic-automation.csv`** **Surface** rows to **`eval-driver-***`** skills per **`docs/semantic-eval-csv.md`**.

No human, agent, or rationalization overrides a RED verdict.

## Iron Law

```
THE JUDGE NEVER ISSUES GREEN WITHOUT A RECORDED outcome IN qa/semantic-eval-manifest.json AND CONSISTENT qa/semantic-eval-run.log LINES FOR THE PHASE 4.4 RUN — outcome pass ⇒ GREEN; fail ⇒ RED; yellow ⇒ YELLOW. IF outcome IS ABSENT OR CONTRADICTS THE LOG, VERDICT RED (INCOMPLETE_DATA).
```

**When drivers never ran:** Do **not** invoke this skill to manufacture GREEN. If automation was not executed, verdict is **RED** or invoke **`qa-pipeline-orchestrate`** static-only paths per that skill.

## Anti-Pattern Preamble: Why Agents Fabricate Green Verdicts

| # | Rationalization | The Truth |
|---|---|---|
| 1 | "Most steps passed, one failure is minor" | A single critical-path failure is RED. Partial pass is not pass. |
| 2 | "I'll skip eval-judge because there are no YAML scenarios" | **Invalid.** Evidence is manifest + log — always run this skill when Phase 4.4 claims completion. |
| 3 | "The manifest says pass but the log shows FAILED" | **RED** — inconsistent evidence (`INCOMPLETE_DATA` or failure — treat as RED until reconciled). |

## Inputs (Phase 4.4)

- **`~/forge/brain/prds/<task-id>/qa/semantic-eval-manifest.json`** — includes **`outcome`**: **`pass`**, **`fail`**, or **`yellow`** after the stack-up run.
- **`~/forge/brain/prds/<task-id>/qa/semantic-eval-run.log`** — append-only JSON lines per step for the same run.

## HARD-GATE mapping

- **`outcome: pass`** and log has **no** contradictory hard failures for required steps → **GREEN**.
- **`outcome: fail`** → **RED** (self-heal per Phase 4.5).
- **`outcome: yellow`** → **YELLOW** (document gaps before merge).
- Missing **`outcome`** or empty/invalid manifest after claimed run → **RED**, reason **`INCOMPLETE_DATA`**.

## Verdict output (minimal schema)

Emit structured YAML or markdown with:

- **`verdict`**: GREEN \| RED \| YELLOW  
- **`timestamp`**: ISO-8601  
- **`evidence`**: pointers to manifest path, log path, and any cited step ids from **`semantic-automation.csv`**  
- **`reason`**: for RED/YELLOW — cite manifest **`outcome`** and log lines  

Record **RED** and **YELLOW** in brain via **`brain-write`** when your workflow requires an audit id.

## Red Flags — STOP

- Verdict changed after initial determination for the same run — re-run eval instead.
- **PASS** claimed when **`semantic-eval-run.log`** contains FAILED lines that contradict pass.
- Overriding RED without a new successful **`qa-semantic-csv-orchestrate`** run.

## Cross-References

| Related | Role |
|---|---|
| **`qa-semantic-csv-orchestrate`** | Produces manifest + run log. |
| **`docs/semantic-eval-csv.md`** | CSV schema and conductor **`[P4.0-SEMANTIC-EVAL]`**. |
| **`eval-product-stack-up`** | Stack before execution. |
| **`eval-driver-*`** | Host execution mapping from **Surface** — not a separate YAML scenario layer. |
| **`self-heal-locate-fault`** | Downstream on RED — use **`semantic-eval-run.log`** JSON lines as primary evidence. |
| **`forge-eval-gate`** | Parent workflow containing this judge. |

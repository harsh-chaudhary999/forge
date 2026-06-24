# Glossary — Eval Artifacts, Conductor Markers, Classifications & Verdicts

Semantic machine-eval artifacts, the `conductor.log` phase markers (`[P4.x-…]`), eval-step outcome classifications (RED_INFRA, CONTEXT_GAP, BLOCKED_DEPENDENCY), and the eval-judge verdict table.

---

## Semantic eval artifacts

### Semantic eval path

**Definition:** The **Forge** machine-eval path: **`qa/semantic-automation.csv`** executed to produce **`qa/semantic-eval-manifest.json`** + **`qa/semantic-eval-run.log`** (**CSV execution results**) — NL-first steps + **DependsOn** DAG. Orchestrated by **`qa-semantic-csv-orchestrate`** / **`tools/run_semantic_csv_eval.py`**. **`eval-judge`** reads manifest + **`semantic-eval-run.log`**.

**Usage Context:** Gates **`verify_forge_task.py`**, **`review-readiness`**, **`prompt-submit-gates`** (**`[P4.0-SEMANTIC-EVAL]`** / **`[P4.4-EVAL-GREEN] path=semantic`**). Self-heal uses **`semantic-eval-run.log`** JSON lines as primary evidence on RED — not driver tables.

**Cross-References:** [docs/semantic-eval-csv.md](../../../docs/semantic-eval-csv.md), [docs/forge-task-verification.md](../../../docs/forge-task-verification.md), **`qa-semantic-csv-orchestrate`**, **`eval-judge`** § Semantic path.

---

### semantic-automation.csv

**Definition:** Task-local CSV under **`~/forge/brain/prds/<task-id>/qa/semantic-automation.csv`** defining semantic automation steps (**Id**, **Surface**, **Intent**, **DependsOn**, …) per [docs/semantic-eval-csv.md](../../../docs/semantic-eval-csv.md). Validated by **`tools/verify/semantic_csv.py`**.

**What It's NOT:** Not **`manual-test-cases.csv`** (human TMS-style acceptance).

---

### semantic-eval-manifest.json

**Definition:** JSON under **`~/forge/brain/prds/<task-id>/qa/semantic-eval-manifest.json`** recording **`schema_version`**, **`task_id`**, **`kind`** (e.g. **`semantic-csv-eval`**), **`outcome`** (**`pass`** | **`fail`** | **`yellow`**), **`recorded_at`**. **Required** for machine verification. **`semantic-eval-run.log`** holds per-step JSON lines for the run.

---

### semantic-csv-eval (`kind`)

**Definition:** Value for **`kind`** in **`semantic-eval-manifest.json`** when the manifest describes **semantic CSV** automation. **`verify_forge_task.py`** expects **`qa/semantic-automation.csv`** when this **`kind`** is set.

---

## Conductor log markers

### [P4.0-QA-CSV]

**Definition:** `conductor.log` marker logged after `~/forge/brain/prds/<task-id>/qa/manual-test-cases.csv` has ≥1 approved row and Step 7 approval is granted in `qa-manual-test-cases-from-prd`. Format: `[P4.0-QA-CSV] task_id=<id> rows=<n> approved=yes`. When logging `skipped=not_required`, it is only valid on partial runs (`/plan`, `/build`, etc.) when `forge_qa_csv_before_eval` is `false`/unset in `forge-product.md`. **Never** log `skipped=not_required` on a full `/forge` run.

**Prerequisite for:** `[P4.0-SEMANTIC-EVAL]` must come after this marker. `conductor-orchestrate` State 4b enforces the ordering.

**Cross-References:** `qa-manual-test-cases-from-prd`; `docs/conductor-log-format.md`; `conductor-orchestrate` State 4b step 0.

---

### [P4.0-SEMANTIC-EVAL]

**Definition:** **`conductor.log`** marker logged after valid **`qa/semantic-eval-manifest.json`** exists on disk — **State 4b** machine-eval gate. **`qa/semantic-eval-run.log`** is the per-step **CSV execution trace**; commit it with the manifest whenever the runner produced it. Parsed by **`prompt-submit-gates.cjs`** (**`GATE_PATTERNS.SEMANTIC_EVAL`**).

---

### [P4.0-TDD-RED]

**Definition:** `conductor.log` marker logged after TDD RED phase is confirmed per repo — failing tests have been written and watched fail before any production implementation code is committed. Format: `[P4.0-TDD-RED] task_id=<id> repo=<role> test_files=<list> red_confirmed=yes`. One marker per repo involved in the task.

**Prerequisite for:** `[P4.1-DISPATCH]` — no production feature code dispatched until RED is confirmed.

**Written by:** `forge-tdd` Output section (per the skill's Output instruction).

**Cross-References:** `forge-tdd` § Output; `forge-verification` § Phase Authority Check; `conductor-orchestrate` State 4b step 2.

---

### [P4.2-DESIGN-PARITY]

**Definition:** `conductor.log` marker logged after design parity check completes per repo during Phase 4.2 Review. Format: `[P4.2-DESIGN-PARITY] task_id=<id> repo=<role> reviewer=design-implementation-reviewer|figma-design-sync|skipped result=PASS|FAIL|SKIP`. Only written when `design_new_work: yes` and the repo is `web` or `app` (no `design_waiver: prd_only`).

**When `result=SKIP`:** Harness not available — human sign-off required before advancing to Phase 4.3.

**Cross-References:** `conductor-orchestrate` § Phase 4.2; `docs/conductor-log-format.md`.

---

## Eval Classification Terms

### RED_INFRA

**Definition:** Eval failure classification for infrastructure failures that are not code bugs — `ECONNREFUSED`, Docker service down, MCP unavailable, device/emulator not running. Classified by `self-heal-triage` before consuming any retry budget. RED_INFRA bypasses the self-heal retry cap: infrastructure must be restored first, then eval re-runs from scratch (the failed attempt does not count against the 3-retry budget).

**Usage Context:** `self-heal-triage` checks for RED_INFRA symptoms before applying any other triage category. If RED_INFRA is detected: write BLOCKED escalation to `~/forge/brain/prds/<task-id>/blockers/`, log `[P4.4-RED-INFRA]` to `conductor.log`, and stop. Do NOT log the attempt as a self-heal retry.

**What It's NOT:** Not a code bug. Not a test failure. Not a flaky test. Not a race condition. RED_INFRA is always an environment issue — fix the environment, not the code.

**Cross-References:** `self-heal-triage` § RED_INFRA Pre-Check; `self-heal-loop-cap` § RED_INFRA bypass rule; `docs/conductor-log-format.md` `[P4.4-RED-INFRA]`.

---

### CONTEXT_GAP

**Definition:** Outcome value for a semantic eval step (in `qa/semantic-eval-run.log`) when the step could not be fully evaluated. Two forms: (1) an upstream dependency step passed but returned an empty `result: {}`, so downstream `${stepId.result.field}` interpolation had no data; (2) external context required by the step (credentials, device, URL, test account) was not available at runtime. In both cases the step result is indeterminate — not a pass, not a product bug. `eval-judge` maps any `CONTEXT_GAP` entries to a YELLOW verdict if all non-skipped steps otherwise pass.

**Usage Context:** When `eval-judge` sees `CONTEXT_GAP` in `semantic-eval-run.log`, the verdict is YELLOW (not RED). The appropriate response is to provide the missing context (credentials, device, test account) and re-run — not to enter the self-heal loop.

**What It's NOT:** Not a test failure. Not RED_INFRA. Not a code bug. CONTEXT_GAP means "we don't know yet" — the step was not executed, not failed.

**Cross-References:** `eval-judge` § Semantic path verdict table; `docs/semantic-eval-schema.md` § outcome enum; `qa-semantic-csv-orchestrate`.

---

### BLOCKED_DEPENDENCY

**Definition:** Outcome value for a semantic eval step when the step was skipped because a step it `DependsOn` returned a non-PASS result. Propagated automatically by the CSV eval runner when upstream steps fail. `eval-judge` maps runs where all non-PASS outcomes are BLOCKED_DEPENDENCY to a YELLOW verdict (dependency issue, not a code bug in the current step).

**Usage Context:** When debugging a RED eval run, distinguish BLOCKED_DEPENDENCY steps from genuine failures. A step marked BLOCKED_DEPENDENCY did not run — its result says nothing about the correctness of its own code. Fix the upstream failing step first, then re-run. When `manifest.outcome = fail` but **all** non-PASS steps are BLOCKED_DEPENDENCY, the eval-judge verdict is **YELLOW** (not RED) — the root failure is a dependency chain issue, not a code bug in the current implementation.

**What It's NOT:** Not the same as CONTEXT_GAP (empty result vs. upstream failure). Not a code bug in the blocked step. Not skippable — if the dependency step is genuinely broken, it must be fixed.

**Cross-References:** `eval-judge` § BLOCKED_DEPENDENCY verdict rule; `docs/semantic-eval-schema.md` § DependsOn propagation; `qa-semantic-csv-orchestrate` § dependency DAG.

---

## Eval Verdicts

| Verdict | Meaning | Next Step |
|---|---|---|
| **GREEN** | All critical scenarios passed. Ready to merge. | Proceed to Review stage. |
| **YELLOW** | All critical passed, some non-critical failed. Decide: fix or accept trade-off. | Review or return to Self-Heal. |
| **RED** | Critical scenario failed. Cannot merge. | Enter Self-Heal loop (max 3 retries). |
| **NOT_EXECUTED** | **QA pipeline / orchestrator** — no driver results (no stack, no env, agent session static check only). **Not** an **`eval-judge`** outcome; do not confuse with **YELLOW**. | Provide URL/device/credentials; re-run **`/qa-run`**. See **`qa-pipeline-orchestrate`** QA-P6, Edge case *Static validation only*. |

---
name: conductor-orchestrate
description: "WHEN: PRD is locked. You are the master state machine orchestrating the entire forge workflow. Routes the task through all phases, tracks state, manages escalations, and coordinates subagents."
type: rigid
requires: [intake-interrogate, product-context-load, brain-read, brain-write, forge-tdd, forge-eval-gate]
---

# Conductor Orchestrate — Master State Machine

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I'll skip council for this small change" | Small changes cause the biggest cross-service breakages. Council catches interface assumptions you haven't considered. |
| "The PRD is clear enough, I don't need intake" | Every PRD that "seemed clear" had at least one ambiguity. Intake exists to surface what you haven't thought to ask. |
| "I'll parallelize build and eval to save time" | Build must complete and commit before eval runs. Eval tests committed code, not in-progress work. |
| "Self-heal is stuck, I'll just skip that scenario" | Skipping a failing scenario means shipping a known bug. Escalate to BLOCKED — never silently drop failures. |
| "I'll merge the PRs without waiting for eval" | Eval is the only proof the system works end-to-end. Merging without eval is deploying hope. |
| "The conductor can adapt the order for this case" | The state machine order exists because each phase produces inputs the next phase requires. Skipping phases means missing inputs. |
| "We shipped dispatch / partial implement — good enough for now" | **Without P4.4 eval there is no proof the product works.** Stopping after P4.1 or P4.3 is an orchestration failure, not a shortcut. Same for skipping **RED** tests before feature code. |
| "Tests can be implied from the tech plan; no separate test pass" | Plans are prose until **failing tests exist** (`forge-tdd`). If no subagent run produced RED then GREEN, TDD was not executed. |
| "Tech plans are done when the markdown is saved — skip self-review and XALIGN" | **State 4** now requires **`tech-plan-self-review` rounds** and **`[TECH-PLAN-XALIGN]`** when multi-repo HTTP. Skipping that is the same failure class as skipping eval — integration bugs ship on **assumed** API wiring. |
| "Agent PASS is enough — skip human `HUMAN_SIGNOFF.md` before eval" | **Human tech-plan gate** is a **distinct phase** after agent review. Without **`[TECH-PLAN-HUMAN]`** (**`APPROVED`** or documented **`WAIVED`**), the pipeline is not intact — stakeholders never blessed the elaboration. STOP. |
| "`design_new_work: yes` but we can start UI code from the wiki/doc link" | Chat and external doc URLs are **not** the brain transport layer. Without **`[DESIGN-INGEST]`** evidence on disk, implementers invent pixels. Same failure class as skipping intake Q9 implementability. |
| "Eval YAML after the feature — faster to code first" | **State 4b is before State 5.** Without `~/forge/brain/prds/<task-id>/eval/*.yaml` and **`[P4.0-EVAL-YAML]`**, there is nothing for **`eval-coordinate-multi-surface`** to run in P4.4 and no proof the journey was agreed. Coding first is an orchestration failure. |
| "`WAIVE_EVAL_YAML` so we can ship" | **Not allowed** for normal delivery. Only **`ABORT_TASK`** (human, logged) ends the run without eval artifacts — that is **not** a shipped feature. |
| "`forge_qa_csv_before_eval: true` but we'll add the CSV after eval YAML" | Defeats the point: **RED** and **eval** must align to the **same** signed acceptance rows. CSV comes **first** when the flag is set. |
| "`/forge` but we'll skip CSV because `product.md` never set the flag" | **`commands/forge.md` (`/forge`) = full pipeline:** State 4b **mandates** **`qa-prd-analysis`** + **`qa-manual-test-cases-from-prd`** and **`[P4.0-QA-CSV]`** before **`[P4.0-EVAL-YAML]`** — same as **`forge_qa_csv_before_eval: true`**. Persist **`forge_qa_csv_before_eval: true`** in **`product.md`** if it was missing or false. |
| "Council can start without `[DISCOVERY]` — we'll grep branches during build" | **State 2.5** exists so **greenfield vs existing in-repo work** (topic branches, tags, open change requests) is resolved **before** contracts are negotiated. Skipping it repeats “two definitions of done.” STOP. Log **`[DISCOVERY]`** or an explicit skip per State 2.5 rules. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
THE ORCHESTRATOR IS THE SINGLE SOURCE OF STATE. NO PHASE IS SKIPPED, NO TRANSITION IS UNAUTHORIZED, AND NO SUBAGENT ESCALATION IS IGNORED.
NO P4.1 / IMPLEMENTATION DISPATCH WITHOUT [P4.0-EVAL-YAML] (scenario_files>=1) AND [P4.0-TDD-RED] PER POLICY — THERE IS NO STANDARD "WAIVE_EVAL_YAML" FOR SHIPPABLE WORK.
NO FULL /forge PIPELINE (commands/forge.md) WITHOUT [P4.0-QA-CSV] approved=yes BEFORE [P4.0-EVAL-YAML] — SET forge_qa_csv_before_eval: true IN product.md IF UNSET OR FALSE.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Conductor moves to Council before PRD is locked in brain** — Phase ordering is violated. STOP. Intake must produce a brain-recorded PRD lock before any other phase starts.
- **Build is dispatched while Council is still open** — Tech plans cannot be written against an unlocked spec. STOP. Lock the shared-dev-spec first, then write tech plans, then dispatch build.
- **Eval is running while tasks report NEEDS_CONTEXT or BLOCKED** — Eval against incomplete builds produces meaningless results. STOP. Resolve all subagent statuses before invoking eval.
- **PRs are raised while eval verdict is RED or YELLOW** — Merging without a GREEN eval means shipping known failures. STOP. Fix the failures and re-run eval.
- **Conductor proceeds after a BLOCKED subagent status without escalation** — Blocked tasks are silently dropped. STOP. Escalate BLOCKED status to human before any forward progress.
- **Brain state from a previous run is present in the current run's path** — State leakage between runs. STOP. Initialize a clean brain path for this orchestration run.
- **Conductor retries self-heal more than 3 times on the same failure** — Exceeds the cap defined in self-heal-loop-cap. STOP. Escalate to human with full failure context.
- **Orchestration stops after P4.1 dispatch or P4.3 QA without entering P4.4 eval** — Partial delivery leaves **no E2E proof** and violates `forge-eval-gate`. STOP unless the human explicitly **aborts the task** with a logged `ABORT` reason. "Ran out of time" is not a valid skip for eval on a claimed-complete feature.
- **No logged `P4.0-TDD-RED` (or equivalent) before production commits** — `forge-tdd` was not applied: no failing tests were written and run first. STOP. Back up to test authoring before more feature code.
- **P4.1 UI dispatch without `[DESIGN-INGEST]` when `design_new_work: yes`** — Net-new visual work requires materialized design in `~/forge/brain/prds/<task-id>/design/` **or** locked `figma_file_key` + `figma_root_node_ids` with MCP/API notes in brain — unless `design_waiver: prd_only` is explicit. STOP. Run **Phase 4.0b** first (see below).
- **`[P4.1-DISPATCH]` or `[DISPATCH]` implementation lines without prior `[P4.0-EVAL-YAML]`** — At least **one** `*.yaml` (or agreed extension) must exist under `~/forge/brain/prds/<task-id>/eval/` and the log must show **`[P4.0-EVAL-YAML] scenario_files=<n>`** with **n≥1**. If the log jumps from tech plan to `IMPLEMENTATION_STARTED`, STOP — you are replaying the known failure mode; back up to **`eval-scenario-format`** + **`eval-translate-english`**.

## Purpose

The Conductor is the master state machine that orchestrates a single task (PRD) through the entire Forge lifecycle:

```
Intake → Load Product → Council → Tech Plans → **QA CSV (when `forge_qa_csv_before_eval`)** → **Eval YAML + RED tests** → **Design ingest (when net-new UI)** → Dispatch (GREEN) → Review → **Eval (E2E)** → PR Set
```

The Conductor:
- Ensures each state completes before moving to the next
- Tracks progress in the brain (git-backed state)
- Escalates blockers and failures
- Dispatches subagents for parallel work
- Routes back to earlier states if issues detected (self-heal loop)
- Logs every transition

## State Machine Diagram: Phase 1-5 Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                   CONDUCTOR ORCHESTRATE                         │
│                    (Master State Machine)                       │
│                     PHASES 1-5 COMPLETE                         │
└─────────────────────────────────────────────────────────────────┘

                        [START: PRD Locked]
                               │
                    ┌──────────┴──────────┐
                    │   PHASE 1: INTAKE   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ 1. Intake Locked    │
                    │ 2. Load Context     │
                    │ 3. Council Negotiate│
                    │ 4. Tech Plans       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ P4.0a: QA CSV      │
                    │ (if product flag)  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  P4.0: EVAL YAML +  │
                    │  RED tests (TDD)    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ P4.0b: DESIGN INGEST │
                    │ (if net-new UI)      │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │  PHASE 4: DELIVERY  │
                    │  (Dev Execution)    │
                    └──────────┬──────────┘
                               │
                       ┌───────▼────────┐
                       │  P4.1: DISPATCH │
                       │ Create worktrees│
                       │ Dispatch devs   │
                       └───────┬────────┘
                               │
                       ┌───────▼────────┐
                       │  P4.2: REVIEW  │
                       │ • Spec Reviewer│
                       │ (all pass?)    │
                       └───────┬────────┘
                               │  (fail)
                               │◄─────────┐
                               │          │ (send back + fix)
                       ┌───────▼────────┐ │
                       │   P4.3: QA     │ │
                       │ • Code Quality │─┘ (fail)
                       │ (all pass?)    │
                       └───────┬────────┘
                               │  (fail)
                               │◄─────────┐
                               │          │ (send back + fix)
                       ┌───────▼────────┐ │
                       │  P4.4: EVAL    │ │
                       │ Run eval-      │ │
                       │ product-stack  │ │
                       │ + eval         │ │
                       │ scenarios      │ │
                       └───────┬────────┘ │
                               │  (fail)  │
                               │◄──────┐  │
                       ┌───────▼────────────┐
                       │  P4.5: SELF-HEAL   │
                       │ Max 3 retries:     │
                       │ 1. Locate Fault    │
                       │ 2. Triage Issue    │
                       │ 3. Fix + Verify    │
                       │ (all pass?)        │
                       └───────┬────────┘
                               │  (eval pass)
                    ┌──────────┴──────────┐
                    │  PHASE 5: SHIPPING  │
                    │  (Release Cycle)    │
                    └──────────┬──────────┘
                               │
                       ┌───────▼────────┐
                       │  P5.1: PR       │
                       │ Raise PRs in    │
                       │ merge order     │
                       └───────┬────────┘
                               │
                       ┌───────▼────────┐
                       │  P5.2: MERGE   │
                       │ Wait CI/CD,     │
                       │ all pass?       │
                       └───────┬────────┘
                               │  (fail)
                               │◄─────────┐
                               │          │ (retry/escalate)
                       ┌───────▼────────┐ │
                       │  P5.3: DREAM   │ │
                       │ Retrospective  │─┘
                       │ analysis of    │
                       │ all decisions  │
                       └───────┬────────┘
                               │
                       ┌───────▼────────┐
                       │  P5.4: SHIP    │
                       │ Feature live   │
                       └───────┬────────┘
                               │
                           [SUCCESS]

        ┌─────────── ESCALATION MATRIX ──────────────┐
        │                                             │
        │ Dev-implementer BLOCKED                    │
        │   → Escalate to user with logs             │
        │                                             │
        │ Spec-reviewer FAIL after fixes             │
        │   → Escalate to user with feedback         │
        │                                             │
        │ Self-heal BLOCKED after 3 tries            │
        │   → Escalate to user with diagnostics      │
        │                                             │
        │ PR fails after retries                     │
        │   → Escalate to user with CI logs          │
        │                                             │
        └─────────────────────────────────────────────┘
```

## Workflow States & Transitions

### State 1: Intake Interrogation
**ENTRY:** PRD provided by user.  
**ACTION:** Invoke `intake-interrogate` skill to lock scope, success criteria, and contracts.  
**ENTRY CONDITION:** PRD raw (user provided text/doc).  
**SUCCESS CONDITION:** `prd-locked.md` exists in `~/forge/brain/prds/<task-id>/`.  
**FAILURE CONDITION:** User declines to answer clarifying questions OR PRD is ambiguous after 2 rounds.  
**ESCALATION:** Ask user to clarify and provide answers in their own words.  
**LOGGING:**
```
[INTAKE] task_id=<id> timestamp=<ISO8601> status=START
[INTAKE] task_id=<id> question=1 prompt="Which product?"
[INTAKE] task_id=<id> question=1 answer=<user_answer>
...
[INTAKE] task_id=<id> timestamp=<ISO8601> status=LOCKED output=prd-locked.md
```

### State 2: Load Product Context
**ENTRY:** `prd-locked.md` exists.  
**ACTION:** Invoke `product-context-load` skill. Validate product slug, load repos, contracts, dependencies.  
**SUCCESS CONDITION:** `context-loaded.md` exists with all repos validated, no circular deps. When **`SCAN.json`** exists under **`codebase/`**, **`context-loaded.md`** must reflect **`verify_scan_outputs.py` PASS** (or **`SCAN_INCOMPLETE`** after 3 verify attempts) — never proceed to council treating a half-written scan as authoritative.  
**FAILURE CONDITION:** Product repo not found OR circular dependencies detected.  
**ESCALATION:** Product must be registered via `forge-product.md` first. User must add product to brain.  
**LOGGING:**
```
[CONTEXT-LOAD] task_id=<id> product=<slug> timestamp=<ISO8601> status=START
[CONTEXT-LOAD] task_id=<id> repo=<repo> validation=<pass|fail>
[CONTEXT-LOAD] task_id=<id> timestamp=<ISO8601> status=COMPLETE output=context-loaded.md
```

### State 2.5: Implementation discovery (before Council)
**ENTRY:** `context-loaded.md` exists. **Always** emit a discovery audit line before Council (see SUCCESS); depth of git commands follows obligation below.

**Obligation (full branch survey):** Run the ACTION in **each** Q4 repo when **any** of: **`intake-interrogate` Q10** is mandatory for this PRD **and** `implementation_closure` is **not** `not applicable`; **`implementation_reference`** is not `none`; PRD or Q4 naming suggests plausible prior in-repo work (product judgment).

**Obligation (waived):** When `prd-locked.md` records **`implementation_closure: not applicable`** with reason — log **`[DISCOVERY] task_id=<id> obligation=waived reason=implementation_closure_not_applicable`** (optional: `git rev-parse HEAD` in primary repo only for audit).

**ACTION (when obligation not waived):** In **each** repo path from `product.md` that is **in Q4 for this task**, run **read-only** git discovery and record evidence under `~/forge/brain/prds/<task-id>/discovery.md` (or append to `context-loaded.md`):

1. `git rev-parse --show-toplevel` and `git status -sb` and `git rev-parse HEAD`
2. `git branch -a` (or `git branch -a \| grep -iE '<tokens from PRD title>'`) — surface **existing** topic / release / integration branch names (including common `feat/*` / `feature/*` patterns where used) **before** council assumes greenfield.
3. If **`implementation_reference`** names `branch:<name>` or `pr:`, run `git merge-base --is-ancestor` / `git log -1 <branch>` only as needed to confirm the ref exists (do not checkout unless human-approved).

**SUCCESS CONDITION:** Log **`[DISCOVERY] task_id=<id> repos_checked=<n> implementation_reference=<branch|pr|none> branches_noted=<short summary>`** (or **`obligation=waived`** line above). If a likely canonical branch exists and PRD did not name it → **STOP** and reconcile with human (amend `implementation_reference` or document supersede) **before** Council locks shared assumptions.  
**FAILURE CONDITION:** Council starts with **no** `[DISCOVERY]` line while **full obligation** applied (per **Obligation (full branch survey)**) and work was not waived.  
**SKIP escalation (human STOP) when:** `implementation_reference: none` **and** greenfield rationale **and** discovery found **no** conflicting remote branches — still log **`[DISCOVERY] … matched=0`**; do **not** STOP.

### State 3: Council Negotiation
**ENTRY:** `context-loaded.md` exists; **State 2.5 complete** — a **`[DISCOVERY]`** line is logged (full survey or **`obligation=waived`** per State 2.5).  
**ACTION:** Invoke `council-multi-repo-negotiate` skill. For each repo, reason about:
  - REST API contracts
  - Event/Kafka schemas
  - MySQL schema changes
  - Redis cache key changes
  - Search index changes
  
Ensure **consensus** across all repos (no conflicting contracts).  

**SUCCESS CONDITION:** `contract-impact.md` exists with all surfaces negotiated, no conflicts, shared spec locked.  
**FAILURE CONDITION:** Two repos disagree on contract (e.g., API v2 in one, v1 in another) and no resolution found.  
**ESCALATION:** Dreamer tries inline resolution. If unresolvable, escalate to user with conflict summary.  
**LOGGING:**
```
[COUNCIL] task_id=<id> timestamp=<ISO8601> status=START
[COUNCIL] surface=<api|events|db|cache|search> repo1=<r1> repo2=<r2> decision=<choice>
[COUNCIL] task_id=<id> conflict=<desc> resolution=<inline_dreamer|escalate>
[COUNCIL] task_id=<id> timestamp=<ISO8601> status=COMPLETE output=contract-impact.md
```

### State 4: Tech Plans Per Project
**ENTRY:** `contract-impact.md` exists (contracts locked across all repos).  
**ACTION:** For each repo in the product:
  1. Invoke reasoning skill for the repo's role (backend, web, app, infra).
  2. Write **elaborative** tech plan per **`tech-plan-write-per-project`**: Section **0** (unlimited doubt-clearing **Q&A log** until confident), Section **1b** (data, reuse, trace, design→UI, **API↔consumer §1b.5**, **unknowns §1b.6**) + Section **1c** (status, revision log, review rounds, **XALIGN** when multi-repo HTTP) — then bite-sized tasks, tests, deployment. Plans must **not** be “tasks only”; include **which API in which component** for every HTTP consumer.
  3. Save to `~/forge/brain/prds/<task-id>/tech-plans/<repo-name>.md`.
  4. **Self-review (feedback loop):** Run **`tech-plan-self-review`** per repo file. On **CHANGES** or **BLOCKED**, revise the markdown (append **§1c revision log** row, bump `Rev`), re-run until **PASS** or **3 rounds** exhausted — then **ESCALATE** with consolidated blockers. Log each round:
     ```
     [TECH-PLAN-REVIEW] task_id=<id> repo=<repo> round=<1|2|3> result=PASS|CHANGES|BLOCKED
     ```
  5. **Cross-plan alignment:** When **≥2** repos have **§1b.5** HTTP tables, cross-walk all `tech-plans/*.md` for matching **METHOD+path** and consumer references; fix drift. Log:
     ```
     [TECH-PLAN-XALIGN] task_id=<id> result=PASS|FAIL notes=<short>
     ```
     **FAIL** → return to step 4 (revision) until **PASS** or escalate.
  6. Only after **all** `[TECH-PLAN-REVIEW] … PASS` and **`[TECH-PLAN-XALIGN] … PASS`** (or XALIGN `N/A` single-repo HTTP) may conductor proceed to the **human tech-plan gate** (step 7) — not yet State 4b.
  7. **Human tech-plan gate (feedback + go-ahead):** Ensure **`~/forge/brain/prds/<task-id>/tech-plans/HUMAN_SIGNOFF.md`** exists per **`docs/tech-plan-human-signoff.template.md`** with **`status: approved`** **or** **`waived`** (reason + actor required). If **`changes_requested`**, merge feedback into plans, return to **step 4** (self-review loop) until agent PASS + XALIGN + **new** human signoff. Log:
     ```
     [TECH-PLAN-HUMAN] task_id=<id> status=APPROVED|WAIVED|CHANGES_REQUESTED actor=<who>
     ```
     **Only** after **`APPROVED`** or **`WAIVED`** may conductor enter **State 4b**.

**SUCCESS CONDITION:** Tech plans written for ALL repos; each plan **> 500 words** where applicable, includes **§0, §1b–§1c**, tests, deployment; **self-review PASS** per repo; **XALIGN PASS** when multi-repo HTTP; **`tech-plans/HUMAN_SIGNOFF.md`** + **`[TECH-PLAN-HUMAN]`** (`APPROVED` or `WAIVED`) logged — then pipeline may enter **State 4b**.  
**FAILURE CONDITION:** Terse task-only plans; missing **§0 / §1b.5/1b.6/1c**; missing tests; self-review or XALIGN still failing after revision cap; human gate missing.  
**ESCALATION:** Re-write plans with full elaboration; if still fails after 3 review rounds per repo, escalate to user with checklist evidence.  
**LOGGING:**
```
[TECH-PLAN] task_id=<id> repo=<repo> timestamp=<ISO8601> status=START
[TECH-PLAN] task_id=<id> repo=<repo> words=<count> tests=<yes|no> deployment=<yes|no>
[TECH-PLAN-REVIEW] task_id=<id> repo=<repo> round=<n> result=PASS|CHANGES|BLOCKED
[TECH-PLAN-XALIGN] task_id=<id> result=PASS|FAIL|N/A notes=<short>
[TECH-PLAN-HUMAN] task_id=<id> status=APPROVED|WAIVED|CHANGES_REQUESTED actor=<who>
[TECH-PLAN] task_id=<id> timestamp=<ISO8601> status=ALL_REPOS_PLANNED
```

### State 4b: Eval scenarios + RED tests (HARD-GATE before implementation)
**ENTRY:** All tech plans written; **`tech-plan-self-review` PASS** per repo; **`[TECH-PLAN-XALIGN]`** **PASS** or **N/A**; **`[TECH-PLAN-HUMAN]`** with **`APPROVED`** or **`WAIVED`**; **`tech-plans/HUMAN_SIGNOFF.md`** on disk matching that log; `shared-dev-spec.md` locked.  
**ACTION:**
  0. **Manual QA CSV (acceptance inventory — before eval YAML and before feature TDD):**
  - **Full pipeline entrypoint (`/forge` — `commands/forge.md`):** The user chose **end-to-end automation**, not a partial phase. **Always** complete **`qa-prd-analysis`** + **`qa-manual-test-cases-from-prd`** through **Step 7 approval** so **`~/forge/brain/prds/<task-id>/qa/manual-test-cases.csv`** exists with **≥1** approved row. Log **`[P4.0-QA-CSV] task_id=<id> rows=<n> approved=yes`**. **Do not** log **`[P4.0-QA-CSV] skipped=not_required`**. If **`~/forge/brain/products/<slug>/product.md`** has **`forge_qa_csv_before_eval`** unset or **`false`**, **set it to `true`** when this step completes so **`verify_forge_task.py`** and later runs match **`/forge`** semantics.
  - **Partial runs** (orchestration **without** the **`/forge`** entrypoint — e.g. user only ran **`/plan`** or asked for “council only”): When **`forge_qa_csv_before_eval: true`** in **`product.md`**, or when the **task charter** explicitly requires a QA CSV deliverable, same requirements as the **`/forge`** bullet (mandatory CSV + log). If the flag is **false** or unset **and** the run is **partial**, this step is **recommended** — log **`[P4.0-QA-CSV] skipped=not_required`** only when intentionally omitted for that partial run.
  - **Escape:** When CSV is mandatory (**flag true** **or** **`/forge`**), the only escape is **`[ABORT_TASK]`** with human owner — not silent skip.
  1. **Eval scenarios (YAML) — before any feature dispatch, after step 0 when applicable:** Materialize **at least one** executable scenario file under `~/forge/brain/prds/<task-id>/eval/` using **`eval-scenario-format`** + **`eval-translate-english`** from PRD + shared-dev-spec **and** (when `manual-test-cases.csv` exists) **trace rows by `Id` in scenario names or comments**. **Do not** log implementation dispatch until this directory exists on disk. Log **`[P4.0-EVAL-YAML] scenario_files=<n>`** with **`n≥1`**. If the team truly cannot author scenarios yet, the only allowed escape is **`[ABORT_TASK]`** with human owner — not silent skip.
  2. **TDD — RED first:** For each repo, dispatch **`dev-implementer`** (or a test-focused subagent with the same rigor) with **`forge-tdd`** attached to the prompt. **First deliverable only:** automated tests that encode acceptance from the **tech plan** and, when present, **approved CSV rows** — **must run and fail (RED)** before any production feature code ships for that repo. Log `[P4.0-TDD-RED] repo=<repo> test_files=<list> red_confirmed=yes`.
  3. Conductor **does not** leave State 4b until **all** of the following hold: (a) **`[P4.0-QA-CSV]`** with `approved=yes` when **`forge_qa_csv_before_eval: true`** **or** the run is **full `/forge`** (`commands/forge.md`); when the flag is false/unset **and** the run is **partial** (not **`/forge`**), (a) may be `skipped=not_required` per step 0; (b) **`[P4.0-EVAL-YAML]`** with `scenario_files≥1`; (c) every in-scope repo has `red_confirmed=yes` (or explicit human **`WAIVE_TDD`** logged with reason — not default). Next: State **4b-design** when applicable, else State 5.

**SUCCESS CONDITION:** QA CSV satisfied when required (**`forge_qa_csv_before_eval: true`** or **full `/forge`**); `eval/` exists with ≥1 scenario file; **`[P4.0-EVAL-YAML]`** logged; every repo has logged RED (or waived TDD).  
**FAILURE CONDITION:** Missing QA CSV when required (**flag true** or **`/forge`**); missing `eval/`; missing `[P4.0-EVAL-YAML]`; skipped RED.  
**ESCALATION:** Missing deploy/runbook in `product.md` → user must fix workspace (`/workspace` Step 3b) before `eval-product-stack-up` can succeed.

### State 4b-design: Design ingestion (HARD-GATE before P4.1 when net-new UI)
**APPLIES WHEN:** `prd-locked.md` / `shared-dev-spec.md` → **Design source (from intake)** has **`design_new_work: yes`** AND the product includes a **web** or **app** repo — **unless** `design_waiver: prd_only` (with owner + risk) is locked.

**ENTRY:** State 4b complete (`[P4.0-TDD-RED]` per policy).

**ACTION:**
  1. Confirm **implementable design** per **`intake-interrogate` Q9**: files under `~/forge/brain/prds/<task-id>/design/` **or** locked **`lovable_github_repo`** (+ optional **`lovable_path_prefix`**) with a pinned ref and **`design/LOVABLE_SYNC.md`** or registry note (see **`docs/platforms/lovable.md`**) **or** locked **`figma_file_key`** + **`figma_root_node_ids`** with a written summary **`design/MCP_INGEST.md`** or **`design/README.md`** in that folder (what was pulled, when, which tool: Figma MCP vs REST vs exports).
  2. If **Figma MCP** is available in the host: **fetch target nodes first**; do not default to “please export PNG” while MCP can supply structure.
  3. If implementable inputs are still missing → **STOP**; return to intake or council to materialize design — **do not** enter State 5 / P4.1 for web/app UI work.

**LOGGING:**
```
[DESIGN-INGEST] task_id=<id> timestamp=<ISO8601> evidence=brain/prds/<task-id>/design/... figma_mcp=<yes|no|n/a> status=PASS|BLOCKED
```

**SUCCESS CONDITION:** `[DESIGN-INGEST] … status=PASS` logged, or gate **not applicable** (backend-only / `design_new_work: no` / `design_waiver: prd_only`).

### State 5: Dispatch Subagents (Dev Implementers — GREEN + completion)
**ENTRY:** **`[P4.0-EVAL-YAML]` logged with `scenario_files≥1`** **and** State 4b complete (RED logged per repo per policy, **and** **`[P4.0-QA-CSV]`** satisfied per step 0: **`approved=yes`** when **`forge_qa_csv_before_eval: true`** **or** full **`/forge`**, else **`skipped=not_required`** allowed **only** for **partial** runs) **and** State **4b-design** satisfied or not applicable. **If `[P4.0-EVAL-YAML]` is missing, State 5 is forbidden.**  
**ACTION:**
  1. Create a worktree per repo (if not already from 4b, reuse policy per `worktree-per-project-per-task`).
  2. Dispatch `dev-implementer` subagent for each repo IN PARALLEL (safe: no shared state between repos).
  3. Each subagent receives:
     - Task text (inline, full context from tech plan)
     - Repo path
     - Tech plan markdown
     - Contract impact for this repo
     - Success criteria
     - **`forge-tdd`:** implement **GREEN** to satisfy existing tests; extend tests only in new RED→GREEN cycles
     - Paths to eval YAML for this task
  4. Track completion per subagent.

**SUCCESS CONDITION:** All subagents complete. All repos have commits on their branch.  
**FAILURE CONDITION:** Subagent fails to implement OR implements code that breaks tests.  
**ESCALATION:** Self-heal attempts to diagnose. Up to 3 attempts. If all fail, escalate to user with logs.  
**LOGGING:**
```
[DISPATCH] task_id=<id> repo=<repo> subagent=dev-implementer timestamp=<ISO8601> status=DISPATCHED
[DISPATCH] task_id=<id> repo=<repo> timestamp=<ISO8601> status=COMPLETE commits=<count>
[DISPATCH] task_id=<id> all_repos=<count> completed=<count> status=<READY_FOR_REVIEW|BLOCKED>
```

### State 6: Two-Stage Review
**ENTRY:** All dev subagents complete.  
**ACTION:** In sequence (NOT parallel, to avoid wasted review work):
  1. **Stage 1: Spec Reviewer + design parity (when applicable)**
     - Dispatches `spec-reviewer` subagent per repo.
     - Checks: Does code implement the tech plan? Are all success criteria met?
     - If FAIL, send back to dev-implementer with detailed feedback.
     - If PASS and **`design_new_work: yes`** for a **web** or **app** repo (no `design_waiver: prd_only`), run **design parity** for that repo per **Phase 4.2** (`design-implementation-reviewer` / `figma-design-sync`, or `skipped=no_harness` + human sign-off).
  2. **Stage 2: Code-Quality Reviewer** (only if Stage 1 passes for all repos)
     - Dispatches `code-quality-reviewer` subagent per repo.
     - Checks: Code patterns, naming, file size, test coverage, comments.
     - If PASS, advance to Eval.
     - If FAIL, send back to dev-implementer.

**SUCCESS CONDITION:** All repos pass both stages.  
**FAILURE CONDITION:** Repeated failures (> 2 rounds per stage).  
**ESCALATION:** If dev can't fix after 2 rounds, escalate to user.  
**LOGGING:**
```
[REVIEW] task_id=<id> repo=<repo> stage=1 reviewer=spec-reviewer timestamp=<ISO8601> status=PASS|FAIL
[REVIEW] task_id=<id> repo=<repo> stage=2 reviewer=code-quality-reviewer timestamp=<ISO8601> status=PASS|FAIL
[REVIEW] task_id=<id> all_repos=<count> stage1_pass=<y> stage2_pass=<y> status=READY_FOR_EVAL|BLOCKED
```

### State 7: Eval (Multi-Surface)
**ENTRY:** All repos pass code review.  
**ACTION:** Run eval drivers for each surface defined in the product:
  - **HTTP/API:** `eval-driver-api-http` — Make HTTP requests, validate responses.
  - **Database:** `eval-driver-db-mysql` — Run queries, validate data.
  - **Web:** `eval-driver-web-cdp` — Puppeteer/Playwright checks.
  - **App:** `eval-driver-android-adb` — ADB checks.
  - **Cache:** `eval-driver-cache-redis` — Redis operations.
  - **Search:** `eval-driver-search-elasticsearch` — Elasticsearch queries.

**SUCCESS CONDITION:** All eval drivers pass (all assertions green).  
**FAILURE CONDITION:** Any eval driver fails (assertion fails, error raised, timeout).  
**SELF-HEAL (on failure):**
  1. Invoke `self-heal-locate-fault` to identify which repo/component failed.
  2. Invoke `self-heal-triage` to classify: "missing endpoint", "schema mismatch", "performance", etc.
  3. Invoke `self-heal-systematic-debug` to fix the issue.
  4. Re-run eval.
  5. If still fails, repeat up to 3 total attempts.
  6. After 3 attempts, escalate to user with full logs.

**ESCALATION:** Eval failure + 3 failed self-heal attempts = escalate to user with logs, eval output, and suggestions.  
**LOGGING:**
```
[EVAL] task_id=<id> driver=api-http timestamp=<ISO8601> status=START
[EVAL] task_id=<id> driver=api-http endpoint=/users method=GET status=200 response=<summary>
[EVAL] task_id=<id> driver=api-http timestamp=<ISO8601> status=<PASS|FAIL>
[EVAL] task_id=<id> all_drivers=<count> passed=<count> failed=<count>
[EVAL] task_id=<id> eval_status=<PASS|FAIL> self_heal_attempts=<n> escalation=<yes|no>
```

### State 8: PR Set Coordination
**ENTRY:** Eval passes (or self-healed successfully) and all repos are reviewed.  
**ACTION:**
  1. Coordinate PRs across all repos. Determine PR order (topological sort by dependencies).
  2. For each repo, create PR with:
     - Title: "[<task-id>] <one-line goal>"
     - Description: Link to prd-locked.md, contract-impact.md, tech plan, eval results.
     - Labels: `forge/<task-id>`, `forge-phase/<phase>`.
  3. Gate merges: Do not merge until all dependent repos are merged.
  4. Save coordination state to `~/forge/brain/prds/<task-id>/prs-coordinated.md`.

**SUCCESS CONDITION:** All PRs merged in dependency order.  
**FAILURE CONDITION:** PR merge blocked (code review failed, CI failed, merge conflict).  
**ESCALATION:** Blocked PR = escalate to user with reason.  
**LOGGING:**
```
[PR-SET] task_id=<id> repo=<repo> pr_number=<n> timestamp=<ISO8601> status=CREATED
[PR-SET] task_id=<id> pr_number=<n> status=READY_TO_MERGE depends_on=<pr_list>
[PR-SET] task_id=<id> pr_number=<n> timestamp=<ISO8601> status=MERGED
[PR-SET] task_id=<id> all_prs=<count> merged=<count> status=<ALL_MERGED|BLOCKED>
```

---

## Phase 4-5: Enhanced Workflow Orchestration

### Delivery & Verification (Development Cycle)

The Conductor manages the complete delivery cycle: dispatching dev work, reviewing code, running evals, and self-healing failures.

#### Phase 4.0: Eval YAML + RED tests (same as State 4b)
**ENTRY:** Tech plans + **`[TECH-PLAN-REVIEW]` PASS** per repo + **`[TECH-PLAN-XALIGN]`** PASS or N/A + **`[TECH-PLAN-HUMAN]`** APPROVED or WAIVED + **`tech-plans/HUMAN_SIGNOFF.md`** + `shared-dev-spec.md` locked.  
**ACTION:** Same as **State 4b** above — **step 0 QA CSV when required** (**`forge_qa_csv_before_eval: true`** **or** full **`/forge`**), then **`eval/` with ≥1 YAML**, **`[P4.0-EVAL-YAML]`** logged, then **forge-tdd** RED logged per repo **before** Phase 4.1 feature work. **Phase 4.1 is invalid without `[P4.0-EVAL-YAML]`** (and invalid without **`[P4.0-QA-CSV]`** **`approved=yes`** when **`forge_qa_csv_before_eval: true`** **or** full **`/forge`**).

#### Phase 4.0b: Design ingestion (same as State 4b-design)
**ENTRY:** Phase 4.0 complete.  
**ACTION:** Same as **State 4b-design** above — materialize design to `~/forge/brain/prds/<task-id>/design/` or lock figma key+nodes with ingest notes; log `[DESIGN-INGEST]`. **Blocks Phase 4.1** when applicable and not satisfied.

#### Phase 4.1: Dispatch (Create Worktrees, Dispatch Dev-Implementers — GREEN)
**ENTRY:** **`[P4.0-EVAL-YAML]` with `scenario_files≥1`** **and** **`[P4.0-QA-CSV]`** per step 0 policy **and** Phase 4.0 complete (`[P4.0-TDD-RED]` logged per repo per policy) **and** Phase **4.0b** satisfied or not applicable.  
**ACTION:**
  1. Invoke `worktree-per-project-per-task` skill to create isolated worktrees per repo.
  2. For each repo IN PARALLEL:
     - Dispatch `dev-implementer` subagent.
     - Pass: task_id, repo path, tech plan, contract impact, success criteria, **`forge-tdd`**, paths to eval YAML, confirmation that RED tests already exist.
     - Track worktree ID and branch name.
  3. Monitor all subagents for completion or failure.

**SUCCESS CONDITION:** All dev-implementer subagents complete. All repos have commits on their feature branch.  
**FAILURE CONDITION:** Subagent fails (code doesn't compile, tests fail, blocked).  
**ESCALATION:** Dev-implementer BLOCKED → escalate to user with full logs and context.  
**LOGGING:**
```
[P4.1-DISPATCH] task_id=<id> repo=<repo> worktree=<id> timestamp=<ISO8601> status=CREATED
[P4.1-DISPATCH] task_id=<id> repo=<repo> subagent=dev-implementer timestamp=<ISO8601> status=DISPATCHED
[P4.1-DISPATCH] task_id=<id> repo=<repo> timestamp=<ISO8601> status=COMPLETE commits=<count>
[P4.1-DISPATCH] task_id=<id> all_repos=<count> completed=<count> status=<READY_FOR_REVIEW|BLOCKED>
```

#### Phase 4.2: Review — Spec Reviewer (Code Matches Tech Plan)
**ENTRY:** All dev-implementer subagents complete.  
**ACTION:**
  1. For each repo IN SEQUENCE:
     - Dispatch `spec-reviewer` subagent.
     - Spec reviewer checks: Does code implement the tech plan? All success criteria met?
     - If **FAIL** → detailed feedback to dev-implementer; do not advance that repo toward Phase 4.3.
     - If **PASS** → when **`design_new_work: yes`** and this repo is **web** or **app** (and no `design_waiver: prd_only`), immediately run **design parity** on that repo:
       - Dispatch **`design-implementation-reviewer`** or **`figma-design-sync`** (Task tool / Cursor subagents **when the harness exposes them**) against locked Figma nodes or `~/forge/brain/prds/<task-id>/design/` baselines.
       - If neither exists, log `[P4.2-DESIGN-PARITY] skipped=no_harness` and **block merge** until a human records visual sign-off in brain or conductor log (or waive in writing).
       - Design parity **FAIL** → same handling as spec FAIL (feedback to dev-implementer).
     - When spec and (if applicable) design parity both **PASS** for that repo, it may advance toward Phase 4.3 with the batch.
  2. Dev-implementer fixes and re-commits. Conductor re-runs from spec review for failed repos.
  3. Max 2 rounds per repo per stage. If still failing, escalate.

**SUCCESS CONDITION:** All repos pass spec review.  
**FAILURE CONDITION:** Spec reviewer FAIL after 2 fix attempts.  
**ESCALATION:** Spec-reviewer FAIL → escalate to user with spec review feedback and dev logs.  
**LOGGING:**
```
[P4.2-REVIEW] task_id=<id> repo=<repo> reviewer=spec-reviewer timestamp=<ISO8601> status=START
[P4.2-REVIEW] task_id=<id> repo=<repo> reviewer=spec-reviewer check=<name> result=<PASS|FAIL>
[P4.2-REVIEW] task_id=<id> repo=<repo> reviewer=spec-reviewer timestamp=<ISO8601> status=PASS|FAIL
[P4.2-REVIEW] task_id=<id> repo=<repo> fix_attempt=<n> timestamp=<ISO8601> status=RE_REVIEW
[P4.2-REVIEW] task_id=<id> all_repos=<count> passed=<count> status=<ALL_PASS|BLOCKED>
[P4.2-DESIGN-PARITY] task_id=<id> repo=<repo> reviewer=design-implementation-reviewer|figma-design-sync|skipped result=<PASS|FAIL|SKIP>
```

#### Phase 4.3: QA — Code Quality Reviewer (Patterns, Naming, Coverage)
**ENTRY:** All repos pass spec review.  
**ACTION:**
  1. For each repo IN SEQUENCE:
     - Dispatch `code-quality-reviewer` subagent.
     - Checks: Code patterns, naming conventions, file size, test coverage, comments, refactoring.
     - If PASS → advance to Phase 4.4.
     - If FAIL → generate detailed feedback, send back to dev-implementer.
  2. Dev-implementer fixes and re-commits. Conductor re-runs code quality review.
  3. Max 2 rounds per repo. If still failing, escalate.

**SUCCESS CONDITION:** All repos pass code quality review.  
**FAILURE CONDITION:** Code-quality-reviewer FAIL after 2 fix attempts.  
**ESCALATION:** Code-quality FAIL → escalate to user with code quality feedback.  
**LOGGING:**
```
[P4.3-QA] task_id=<id> repo=<repo> reviewer=code-quality timestamp=<ISO8601> status=START
[P4.3-QA] task_id=<id> repo=<repo> check=<name> result=<PASS|FAIL> detail=<msg>
[P4.3-QA] task_id=<id> repo=<repo> reviewer=code-quality timestamp=<ISO8601> status=PASS|FAIL
[P4.3-QA] task_id=<id> repo=<repo> fix_attempt=<n> timestamp=<ISO8601> status=RE_REVIEW
[P4.3-QA] task_id=<id> all_repos=<count> passed=<count> status=<ALL_PASS|BLOCKED>
```

#### Phase 4.4: Eval — Multi-Surface Evaluation (mandatory invocation)
**ENTRY:** All repos pass code quality review.  
**MUST NOT SKIP:** This phase is **not optional** for a completed delivery. If stack-up cannot run (e.g. missing `deploy_doc` / `start`+`health` in `product.md`), **STOP** and fix `product.md` — do not pretend the task finished.

**ACTION:**
  1. Invoke `eval-product-stack-up` skill to bring up the entire product stack (all services, DBs, caches, etc.).
  2. Run eval scenario drivers:
     - HTTP API: `eval-driver-api-http`
     - Database: `eval-driver-db-mysql`
     - Web UI: `eval-driver-web-cdp`
     - App (Android): `eval-driver-android-adb`
     - Cache: `eval-driver-cache-redis`
     - Search: `eval-driver-search-es`
     - Event Bus: `eval-driver-bus-kafka`
  3. Execute all eval scenarios from `eval-scenario-format`.
  4. Collect results: PASS (all assertions green) or FAIL (any assertion red).

**SUCCESS CONDITION:** All eval drivers pass. All assertions green.  
**FAILURE CONDITION:** Any eval driver fails (assertion fails, error raised, timeout).  
**ON FAILURE:** Proceed to Phase 4.5 (Self-Heal).  
**LOGGING:**
```
[P4.4-EVAL] task_id=<id> timestamp=<ISO8601> status=STACK_UP_START
[P4.4-EVAL] task_id=<id> service=<svc> timestamp=<ISO8601> status=UP
[P4.4-EVAL] task_id=<id> driver=<driver> timestamp=<ISO8601> status=RUN_START
[P4.4-EVAL] task_id=<id> driver=<driver> scenario=<name> assertion=<desc> result=<PASS|FAIL>
[P4.4-EVAL] task_id=<id> driver=<driver> timestamp=<ISO8601> status=<PASS|FAIL>
[P4.4-EVAL] task_id=<id> all_drivers=<count> passed=<count> failed=<count> status=<PASS|FAIL>
```

#### Phase 4.5: Self-Heal (Locate, Triage, Fix, Verify — Max 3 Retries)
**ENTRY:** Eval fails.  
**ACTION:** Retry loop (max 3 attempts):
  1. **Attempt N (1-3):**
     - **Locate Fault:** Invoke `self-heal-locate-fault` to identify which service/component failed (parse eval output).
     - **Triage Issue:** Invoke `self-heal-triage` to classify the failure (missing endpoint, schema mismatch, performance, etc.).
     - **Fix:** Invoke `self-heal-systematic-debug` to generate fix suggestions. Send back to dev-implementer to implement fix.
     - **Verify:** Re-run eval to check if fix worked.
  2. If eval PASS → advance to Phase 5.1 (PR).
  3. If eval FAIL and attempts < 3 → loop back to Locate Fault.
  4. If eval FAIL and attempts = 3 → escalate.

**SUCCESS CONDITION:** Eval passes after self-heal fix.  
**FAILURE CONDITION:** Eval still fails after 3 attempts.  
**ESCALATION:** Self-heal BLOCKED after 3 tries → escalate to user with eval logs, fault diagnostics, and all attempts.  
**LOGGING:**
```
[P4.5-HEAL] task_id=<id> attempt=<n> timestamp=<ISO8601> status=LOCATE_START
[P4.5-HEAL] task_id=<id> attempt=<n> fault_location=<service:component> failure_type=<type>
[P4.5-HEAL] task_id=<id> attempt=<n> status=TRIAGE fault_class=<class> root_cause=<desc>
[P4.5-HEAL] task_id=<id> attempt=<n> status=FIX_SENT_TO_DEV dev_feedback=<summary>
[P4.5-HEAL] task_id=<id> attempt=<n> status=VERIFY_EVAL_START
[P4.5-HEAL] task_id=<id> attempt=<n> status=VERIFY_RESULT result=<PASS|FAIL>
[P4.5-HEAL] task_id=<id> max_attempts=3 final_status=<PASS|ESCALATE>
```

---

## Edge Cases & Fallback Paths

### Edge Case 1: Task fails in multiple phases (e.g., Spec fails, then after fix, Code Quality fails)

**Diagnosis**: Dev-implementer gets sent back to fix Spec Review issues, completes fixes and commits, but then fails Code Quality Review. Multiple fix-retry cycles eating time.

**Response**:
- **Attempt 1**: Route back to dev-implementer with clear issue categorization (Spec issues vs. Code Quality issues).
- **Track cumulative fixes**: Log all fix attempts across all phases. If total fix attempts >4 (2 per phase), escalate.
- **Escalation signal**: If dev-implementer fails 2 phases in sequence, escalate to user: "Multiple review phases failing. May indicate spec misunderstanding or architectural issue. Request clarification before continuing?"

**Escalation**: NEEDS_CONTEXT - If spec and code quality both fail repeatedly, user may need to clarify requirements or architecture before proceeding. Escalate with evidence that dev-implementer is not the bottleneck.

---

### Edge Case 2: Worktrees conflict or fail during parallel dispatch

**Diagnosis**: Two or more repos' worktrees clash (e.g., both trying to modify same file in shared dependency, or git worktree cleanup fails for one repo).

**Response**:
- **Detect**: Monitor worktree creation status in parallel dispatch. If any repo returns worktree creation failure, pause dispatch.
- **Diagnose**: Log which repos conflict and why (shared file? Same submodule? Git lock issue?).
- **Fallback**: 
  - Option A: Create worktrees sequentially instead of parallel (slower but avoids conflicts).
  - Option B: If conflict is on a shared file, route to council to negotiate who modifies it first, then re-order dispatch sequence.
- **Re-attempt**: Retry dispatch after resolving conflict.

**Escalation**: If conflicts cannot be resolved (e.g., two repos must edit same critical file), escalate to NEEDS_CONTEXT - User/council must decide which repo "owns" the shared code or refactor to avoid conflict.

---

### Edge Case 3: Spec reviewer succeeds, but dreamer (post-merge) discovers decision was flawed

**Diagnosis**: Code passes spec review and all phases, gets merged, then dreamer's retrospective analysis reveals the spec itself was incomplete or the decision contradicted hidden assumptions.

**Response**:
- **This is data for next cycle**, not a blocker for current task.
- Log in brain: `brain/gotchas/spec-incompleteness-[task-id].md` with details of what spec missed.
- **Escalation signal**: Flag for next task intake phase. When intake-interrogate runs next time, explicitly ask about the missed assumptions.
- **No code reversion**: Task is already shipped. Focus on learning, not rework.

**Escalation**: This is a process improvement, not a task failure. Route to brain-write for gotcha documentation.

---

### Edge Case 4: Eval drivers pass individually but fail together

**Diagnosis**: When running `eval-product-stack-up` (all services together), eval drivers that passed in isolation now fail due to service interactions, race conditions, or resource contention.

**Response**:
- **Root cause analysis**: Invoke `self-heal-locate-fault` with context: "Drivers passed in isolation but fail together. Check for: race conditions, shared resource contention, message ordering, cascading failures."
- **Triage**: Most likely causes: event ordering (Kafka driver publishes before consumer ready), cache invalidation across services, database locks on concurrent writes.
- **Fix strategy**: 
  - Add synchronization points between driver actions (wait for event before proceeding).
  - Adjust test data to reduce contention (use separate IDs per test).
  - Check service startup order (dependent services may not be ready).
- **Re-test**: Re-run eval drivers in sequence (not parallel) to isolate if ordering is the issue.

**Escalation**: If issue persists after 3 self-heal attempts, escalate to user with architecture diagram and driver interaction timeline.

---

### Edge Case 5: Dreamer escalates with conflicting recommendations

**Diagnosis**: During retrospective scoring, dreamer identifies conflicting insights: "Decision A was correct BUT it created technical debt, Decision B would have avoided debt BUT would have delayed shipping."

**Response**:
- **Escalation is valid**: Dreamer is doing its job. This is captured as a GOTCHA or PATTERN learning, not a failure.
- **Document both truths**: Write to brain: "Trade-off: shipped on time (Decision A) but took technical debt. Next time, weigh earlier shipping vs. technical debt budget."
- **No task rollback**: Task is complete. Learning is captured for future planning.

**Escalation**: Route escalation to brain-write. This is a learning capture, not a blocker.

---

### Edge Case 6: Multiple self-heal attempts fail; uncertain if issue is in code or eval driver

**Diagnosis**: Eval fails. Self-heal triage says "endpoint returns 500 error". Dev-implementer fixes the endpoint. Eval still fails. Triage now says "timeout on request". Is the code slow, or is the eval driver timeout too aggressive?

**Response**:
- **Separate concerns**: Ask: Is this a code issue or an eval driver configuration issue?
- **Strategy 1 (Assume code issue)**: Invoke `self-heal-systematic-debug` with: "Add logging to endpoint. Check response time in logs vs. eval driver timeout setting. Increase timeout if response time is near limit, OR optimize endpoint if slow."
- **Strategy 2 (Assume driver issue)**: Ask user: "Eval driver timeout is [Xms]. Expected endpoint latency is [Yms]. Should we increase timeout or optimize endpoint?"
- **Track assumption**: Log which assumption we're testing. If assumption 1 fails 2x, switch to assumption 2.

**Escalation**: If unclear whether code or driver is the issue after 2 attempts, escalate to user with both code logs and driver config for manual decision.

---

### Edge Case 7: PR coordination blocked; one repo's code depends on another repo's code, but second repo's PR is held up

**Diagnosis**: Topological sort determined PR order correctly, but while waiting for Repo A's PR to merge, Repo B's PR encounters unexpected CI failures (unrelated to Repo A).

**Response**:
- **Don't wait passively**: While Repo A's PR is merging, allow Repo B's PR self-heal to proceed (run tests, fix failures).
- **Track merge order**: Log that Repo B is ready to merge once Repo A merges, but don't block Repo B's preparation.
- **If Repo B's CI continues failing**: Escalate Repo B to user independently. Repo A's merge doesn't unblock Repo B if Repo B has its own issues.

**Escalation**: Escalate problematic repos independently. Don't let one repo's blockage cascade unnecessarily to others.

---

### Edge Case 8: Conductor state is lost/corrupted (e.g., brain directory not persisted between runs)

**Diagnosis**: Conductor resumes a task but can't find the brain state file (conductor.log, phase history, worktree IDs). Task state is unknown.

**Response**:
- **Recovery strategy**: Re-query brain-read to reconstruct state from git history. Check for most recent status commit.
- **Fallback**: If brain state is corrupt, ask user: "Current state unknown. Should I restart from Phase 1 (intake re-lock) or jump to Phase 4 (if tech plans are already written)?"
- **Log recovery attempt**: Note that state was recovered and from which point.

**Escalation**: NEEDS_CONTEXT - User must confirm safe recovery point. Don't guess and resume incorrectly.

---

### Edge Case 9: Conductor reaches Phase 5.3 (Dreamer retrospective) but code was emergency-patched in production before merge

**Diagnosis**: During Phase 5 (post-merge), dreamer is analyzing the decision, but user mentions: "We shipped an emergency hotfix to production before this PR merged. Should that be considered in retrospective?"

**Response**:
- **Yes**: Retrospective should acknowledge the hotfix as a branch in outcomes. Log: "Primary path: PR-123 merged [date]. Emergency hotfix: [describe]. Actual outcome reflects both."
- **Adjust decision scoring**: If decision was judged as "correct" but hotfix was needed, downgrade confidence or add GOTCHA: "Incomplete risk assessment; unforeseen production issue required hotfix."
- **Treat as learning**: Write GOTCHA: "Risk assessment missed [specific type of failure]. Next time, explicitly check for [specific condition]."

**Escalation**: This is a learning capture, not a task failure. Route to brain-write.

---

### Edge Case 10: Task is too large; progresses through all phases but takes >1 week, stakeholder loses context

**Diagnosis**: After Phase 1 intake is locked, conductor progresses through Phases 2-5 over 8+ days. By Phase 5, stakeholder context has drifted (they've moved on to other tasks, details fuzzy).

**Response**:
- **Not conductor's failure**: This is a task scoping issue (intake-interrogate should have caught scope too large).
- **Mitigation for future**: At end of retrospective, dreamer should capture GOTCHA: "Large task scope caused context drift by Phase 5. Recommendation: break into smaller tasks, each <3 days."
- **For current task**: Escalate to user: "Task duration exceeded 7 days. Recommend: 1) Document key decisions in brain for reference, 2) Require Phase 5 stakeholder re-confirmation, 3) Split future large tasks into smaller units."

**Escalation**: This is a process improvement signal, not a blocker. Route to brain for process adjustment.

---

### Shipping & Release (Production Cycle)

After Phase 4 completes successfully, the Conductor coordinates the release: PRs, merges, retrospective analysis, and ship.

#### Phase 5.1: PR (Raise Coordinated PRs in Merge Order)
**ENTRY:** All Phase 4 complete (dispatch, review, QA, eval, self-heal if needed).  
**ACTION:**
  1. Determine PR order using topological sort by repo dependencies.
  2. For each repo in order:
     - Create PR:
       - Title: "[<task-id>] <one-line goal>"
       - Description: Links to prd-locked.md, contract-impact.md, tech plan, eval results, self-heal logs (if any).
       - Labels: `forge/<task-id>`, `forge-phase/p5`, `forge-phase/p4`.
     - Push to remote if not already pushed.
     - Save PR metadata to `~/forge/brain/prds/<task-id>/pr-<repo>.md`.

**SUCCESS CONDITION:** All PRs created and pushed.  
**FAILURE CONDITION:** Cannot push or create PR (auth issue, repo locked, etc.).  
**LOGGING:**
```
[P5.1-PR] task_id=<id> repo=<repo> pr_number=<n> timestamp=<ISO8601> status=CREATED
[P5.1-PR] task_id=<id> repo=<repo> pr_number=<n> url=<url>
[P5.1-PR] task_id=<id> all_repos=<count> prs_created=<count> status=READY_FOR_MERGE
```

#### Phase 5.2: Merge (Wait for All PRs to Pass CI/CD)
**ENTRY:** All PRs created.  
**ACTION:**
  1. Poll each PR in merge order:
     - Check CI/CD status (GitHub Actions, Jenkins, etc.).
     - Wait for all checks to pass (green).
     - If any check fails: Log failure, attempt auto-retry (if safe), or escalate.
  2. Once all checks green:
     - Merge PRs in dependency order (respect gates).
     - Confirm merge to main/master.
  3. Delete feature branches after merge.

**SUCCESS CONDITION:** All PRs merged to main/master. All branches deleted.  
**FAILURE CONDITION:** PR CI fails. Merge blocked. Merge conflict.  
**ESCALATION:** PR fails after retries → escalate to user with CI logs and conflict details.  
**LOGGING:**
```
[P5.2-MERGE] task_id=<id> repo=<repo> pr_number=<n> timestamp=<ISO8601> status=WAITING_CI
[P5.2-MERGE] task_id=<id> repo=<repo> pr_number=<n> ci_status=<PENDING|PASS|FAIL>
[P5.2-MERGE] task_id=<id> repo=<repo> pr_number=<n> timestamp=<ISO8601> status=MERGED branch_deleted=<yes|no>
[P5.2-MERGE] task_id=<id> all_prs=<count> merged=<count> status=<ALL_MERGED|BLOCKED>
```

#### Phase 5.3: Dream (Retrospective Analysis of All Decisions)
**ENTRY:** All PRs merged.  
**ACTION:**
  1. Invoke `dreamer` subagent with full task context:
     - prd-locked.md (original PRD)
     - contract-impact.md (all contracts)
     - tech plans (all repos)
     - dev dispatch logs (what was built)
     - spec & QA review feedback (what changed)
     - eval results (what worked)
     - self-heal logs (what failed and how it was fixed)
  2. Dreamer performs retrospective analysis:
     - Score each decision (inline spec, council negotiation, tech plan, eval, self-heal).
     - Compare predicted vs. actual performance.
     - Identify learnings: what went well, what was unexpected, what to improve next time.
     - Generate brain links: connect decisions to outcomes.
  3. Save retrospective report to `~/forge/brain/prds/<task-id>/retrospective.md`.

**SUCCESS CONDITION:** Retrospective report written. Brain links created.  
**FAILURE CONDITION:** Cannot generate report (corrupted logs, missing context).  
**LOGGING:**
```
[P5.3-DREAM] task_id=<id> timestamp=<ISO8601> status=DREAMER_INVOKE
[P5.3-DREAM] task_id=<id> decision=<name> score=<0-100> rationale=<summary>
[P5.3-DREAM] task_id=<id> learning=<insight> impact=<positive|negative|neutral>
[P5.3-DREAM] task_id=<id> timestamp=<ISO8601> status=COMPLETE output=retrospective.md
```

#### Phase 5.4: Ship (Feature is Live)
**ENTRY:** All PRs merged. Retrospective complete.  
**ACTION:**
  1. Confirm that all merged code is deployed to production (or will be via normal deployment pipeline).
  2. Mark task as COMPLETE in conductor.log.
  3. Archive all task state to `~/forge/brain/prds/<task-id>/COMPLETE.md`.

**SUCCESS CONDITION:** Code is live in production.  
**FAILURE CONDITION:** Deployment fails (e.g., prod infra issue).  
**ESCALATION:** Escalate to user if deployment blocked.  
**LOGGING:**
```
[P5.4-SHIP] task_id=<id> timestamp=<ISO8601> status=DEPLOYED environment=production
[P5.4-SHIP] task_id=<id> timestamp=<ISO8601> status=COMPLETE
[FINAL] task_id=<id> total_duration=<HH:MM:SS> repos_shipped=<count> status=SUCCESS
```

---

## Escalation Points & Matrix

### Phase 1-3 Escalation

| Scenario | Detection | Escalation Action |
|----------|-----------|-------------------|
| **Ambiguous PRD** | Intake questions unanswered 2x | Ask user to clarify, provide prd-locked.md |
| **Product not found** | Context load fails | Direct user to register product via forge-product.md |
| **Circular repo deps** | Context load detects cycle | Escalate to user: "Product has circular deps" |
| **Council conflict** | 2+ repos disagree on contract | Inline dreamer tries to resolve; if fails, escalate to user with conflict summary |
| **Tech plan gaps** | Plan is terse (missing **§1b.5/1b.6/1c**), < 500 words where depth required, missing tests, **`[TECH-PLAN-REVIEW]`** not PASS, or **`[TECH-PLAN-XALIGN]`** FAIL | Revise plans per **`tech-plan-self-review`** (max 3 rounds/repo); if still fails, escalate with checklist evidence |

### Phase 4-5 Escalation Matrix (Dev Implementer Through Ship)

| Scenario | State | Detection | Escalation Action |
|----------|-------|-----------|-------------------|
| **Dev-Implementer BLOCKED** | P4.1 Dispatch | Subagent fails to implement, code doesn't compile, tests fail, or is truly blocked | **ESCALATE IMMEDIATELY** to user with: full subagent logs, code state, error messages, and reproduction steps. User decides next action (manual fix, restart, etc.) |
| **Spec Reviewer FAIL (After Fixes)** | P4.2 Review | Code fails spec review after 2 fix attempts from dev-implementer | **ESCALATE** to user with: detailed spec review feedback, what code is missing/incorrect, links to tech plan, and dev's attempted fixes. |
| **Code Quality FAIL (After Fixes)** | P4.3 QA | Code fails quality review after 2 fix attempts from dev-implementer | **ESCALATE** to user with: code quality feedback, specific violations, quality standards, and attempted fixes. User may override or request manual review. |
| **Eval FAIL (After Self-Heal)** | P4.4-P4.5 Eval + Self-Heal | Eval assertions fail even after 3 self-heal attempts (locate, triage, fix, verify) | **ESCALATE** to user with: eval output (which assertions failed, why), fault diagnostics (which service), all 3 self-heal attempts with root cause analysis and suggested fixes. |
| **Self-Heal BLOCKED** | P4.5 Self-Heal | After 3 attempts, self-heal cannot locate/fix the issue | **ESCALATE** to user with: failure diagnostics, attempted fixes, why they didn't work, and manual debugging suggestions. |
| **PR Creation Failed** | P5.1 PR | Cannot create PR (auth, branch not found, remote unreachable) | **ESCALATE** to user with: which repo, why PR creation failed, and manual PR creation instructions. |
| **PR CI Failed** | P5.2 Merge | PR CI/CD checks fail after code review | **ESCALATE** to user with: CI logs, which checks failed, error details, and whether retrying is safe or requires code changes. |
| **PR Merge Blocked** | P5.2 Merge | PR merge conflict or gated by user reviewers | **ESCALATE** to user with: merge conflict details or reviewer feedback. User approves or resolves conflict manually. |
| **Retrospective Generation Failed** | P5.3 Dream | Dreamer cannot generate retrospective (corrupted logs, missing context) | **LOG WARNING**, skip retrospective, continue to ship. Retrospective can be run post-ship if needed. |
| **Deployment Failed** | P5.4 Ship | Code is merged but production deployment fails | **ESCALATE** to user with: deployment error logs and infrastructure status. User coordinates deployment with infra team. |

### Escalation Flow Diagram

```
┌────────────────────────────────────────────────────┐
│           ESCALATION DECISION TREE                 │
└────────────────────────────────────────────────────┘

                    [FAILURE DETECTED]
                            │
                ┌───────────┴───────────┐
                │                       │
            [Dev-Impl]            [Review/QA]
                │                       │
                │                   ┌───┴────┐
                │                   │        │
            [BLOCKED]           [FAIL]   [FAIL]
                │               after    after
                │                2x       2x
                │                │        │
                ▼                ▼        ▼
         ╔═════════════╗   ╔════════╗ ╔════════╗
         ║ ESCALATE    ║   ║ ESC    ║ ║ ESC    ║
         ║ IMMEDIATELY ║   ║ (SPEC) ║ ║ (QA)   ║
         ╚═════════════╝   ╚════════╝ ╚════════╝

            [Eval/Self-Heal]
                │
            ┌───┴────┐
            │        │
         [FAIL]   [FAIL]
         after    after
         3x SH    SH setup
         │        │
         ▼        ▼
      ╔══════╗ ╔═════════╗
      ║ ESC  ║ ║ ESC     ║
      ║(EVAL)║ ║(BLOCKED)║
      ╚══════╝ ╚═════════╝

         [PR/Merge/Ship]
              │
         ┌────┼────┬───────┐
         │    │    │       │
      [CREATE] [CI] [CONFLICT] [DEPLOY]
         │    │    │       │
         ▼    ▼    ▼       ▼
      ╔════╗╔════╗╔═════╗╔═════╗
      ║ESC ║║ESC ║║ ESC ║║ ESC ║
      ║(PR)║║(CI)║║(MRG)║║(DPL)║
      ╚════╝╚════╝╚═════╝╚═════╝

All escalations → User with full context
User decides: retry, manual fix, or abort
```

---

## Logging Architecture

### Log Levels

- **INFO:** State transitions, actions taken, successful operations.
- **WARN:** Retry attempts, potential issues (e.g., slow test), upcoming escalations.
- **ERROR:** Failures, escalations, blockers.
- **DEBUG:** Subagent dispatch, contract details, eval assertions.

### Log Format

```
[<STATE>] task_id=<task-id> <key>=<value> timestamp=<ISO8601> status=<START|PROGRESS|COMPLETE|FAIL|ESCALATE>
```

### Log Storage

All logs written to: `~/forge/brain/prds/<task-id>/conductor.log`

### Machine verification (optional)

Forge ships **`tools/verify_forge_task.py`** (stdlib Python, no pip deps) to **fail CI or pre-push** when:

- `prds/<task-id>/eval/` has no scenario YAML, or
- `conductor.log` shows **`[P4.1-DISPATCH]`** before **`[P4.0-EVAL-YAML]`**, or
- `forge_qa_csv_before_eval: true` but CSV / log order is wrong, or
- Net-new design (per `prd-locked.md`) lacks **`design/`** files and/or **`[DESIGN-INGEST]`** before P4.1.

See **`docs/forge-task-verification.md`** and **`.github/workflows/forge-brain-guard.yml`**. This does not replace skills — it catches **committed** brain state that violates the same rules.

Example entry:
```
[INTAKE] task_id=task-001 timestamp=2026-04-08T14:23:45Z status=START
[INTAKE] task_id=task-001 question=1 prompt="Which product?" timestamp=2026-04-08T14:23:50Z
[INTAKE] task_id=task-001 question=1 answer="ShopApp" timestamp=2026-04-08T14:24:10Z
[INTAKE] task_id=task-001 timestamp=2026-04-08T14:28:35Z status=COMPLETE output=prd-locked.md
```

---

## Conductor Invocation

### Start a New Orchestration

```bash
# Given a PRD (locked or raw), invoke conductor:
# The user provides:
#   - task_id: Short identifier (e.g., "add-2fa", "search-v2")
#   - prd_text: PRD description (user input)

# Conductor runs:
conductor_start task_id=<id> prd_text=<text>
```

### Resume (after interruption)

```bash
# If conductor was interrupted, resume from the last successful state:
conductor_resume task_id=<id>
# Conductor reads conductor.log, finds last successful state, continues
```

### State Inspection

```bash
# Query current state of a task:
conductor_state task_id=<id>
# Output: Prints last 20 log entries, current state, next action
```

---

## Implementation Checklist

### Phase 1-3 (Intake Through Tech Plans)
- [ ] **`spec-freeze` Step 0 parity** satisfied (`parity/` or waiver) before treating `shared-dev-spec` as final for tech planning; optional **`delivery-plan.md`** for program shape.
- [ ] Conductor invokes intake-interrogate, product-context-load, council-multi-repo-negotiate sequentially.
- [ ] **State 4 tech plans:** Each `tech-plans/*.md` includes **§0, §1b–§1c** (API↔consumer **§1b.5**, unknowns **§1b.6**, review + XALIGN); **`[TECH-PLAN-REVIEW] … PASS`** per repo; **`[TECH-PLAN-XALIGN] … PASS`** or **N/A**; **`tech-plans/HUMAN_SIGNOFF.md`** + **`[TECH-PLAN-HUMAN]`** before State 4b.
- [ ] State transitions logged to conductor.log.
- [ ] Escalation paths clear and actionable.
- [ ] All states (Intake through Tech Plans) reachable.
- [ ] Logs human-readable, timestamped, machine-parseable.

### Phase 4 (Delivery & Verification)
- [ ] **P4.0 Prerequisites:** **`[P4.0-QA-CSV]`** with approved `manual-test-cases.csv` **before** `[P4.0-EVAL-YAML]` when **`forge_qa_csv_before_eval: true`** **or** entrypoint is **full `/forge`** (`commands/forge.md`); for **partial** runs with flag false/unset, log `skipped=not_required` only if CSV is intentionally omitted.
- [ ] **P4.0 Prerequisites:** `~/forge/brain/prds/<task-id>/eval/` contains **≥1** scenario file; **`[P4.0-EVAL-YAML] scenario_files≥1`** logged; **`forge-tdd` RED** logged per repo (`[P4.0-TDD-RED]`); conductor log shows subagent runs for tests-before-feature. **Never** log `[P4.1-DISPATCH]` before `[P4.0-EVAL-YAML]`.
- [ ] **P4.0b Design ingest:** When `design_new_work: yes` and web/app in scope, `[DESIGN-INGEST]` logged with brain `design/` or figma key+nodes evidence — before P4.1.
- [ ] **P4.1 Dispatch:** worktree-per-project-per-task invoked. Dev-implementers dispatched in parallel **after** RED and design gate (GREEN implementation).
- [ ] **P4.2 Review:** spec-reviewer invoked per repo; **design-implementation-reviewer** or **figma-design-sync** when harness exists and net-new UI. Max 2 fix rounds per repo. Escalation on final FAIL.
- [ ] **P4.3 QA:** code-quality-reviewer invoked per repo. Max 2 fix rounds per repo. Escalation on final FAIL.
- [ ] **P4.4 Eval:** **`eval-product-stack-up` explicitly invoked**; multi-surface eval drivers run (API, DB, Web, App, Cache, Search, Bus). Orchestration **invalid** if this step is skipped on a non-aborted task.
- [ ] **P4.5 Self-Heal:** On eval failure: locate fault → triage → fix → verify. Max 3 attempts. Escalate after 3 failures.
- [ ] Self-heal loop (3 attempts) integrated with proper diagnostics.
- [ ] Subagent dispatch via Task tool working.
- [ ] All Phase 4 states reachable and loggable.

### Phase 5 (Shipping & Release)
- [ ] **P5.1 PR:** PRs created in dependency order. All metadata saved.
- [ ] **P5.2 Merge:** CI/CD polling, merge gating, branch cleanup.
- [ ] **P5.3 Dream:** Dreamer subagent invoked post-merge. Retrospective analysis and brain links.
- [ ] **P5.4 Ship:** Deployment confirmation. Task marked COMPLETE.
- [ ] All Phase 5 states reachable and loggable.

### Validation (Full E2E: Phases 1-5)
- [ ] Run conductor on a test PRD. Follow all states to completion (Intake → Ship).
- [ ] Simulate Phase 4 failures:
  - [ ] Dev-implementer blocked. Verify escalation to user.
  - [ ] Spec reviewer fails after 2 fixes. Verify escalation to user.
  - [ ] Code quality fails after 2 fixes. Verify escalation to user.
  - [ ] Eval fails. Verify self-heal retries 3x. Verify escalation after 3 failures.
- [ ] Simulate Phase 5 issues:
  - [ ] PR creation fails. Verify escalation with manual instructions.
  - [ ] CI fails. Verify user is asked for action.
  - [ ] Merge conflict. Verify user is notified.
- [ ] Check conductor.log for proper format, all states, timestamps, and escalation log entries.
- [ ] Verify all subagent dispatches logged with task_id, repo, timestamp.
- [ ] Verify dreamer retrospective written and brain links created.
- [ ] Commit conductor.log to brain repo.

---

## Next Steps After Conductor Success

1. **Post-PR Dreamer:** Triggered by PR merge hook. Scores every decision (inline, council, eval, self-heal).
2. **Retrospective Scoring:** Dreamer compares actual performance to predicted.
3. **Brain Learning:** Decisions logged, future conductors learn from past runs.

## Checklist

Before claiming orchestration complete:

- [ ] PRD locked in brain before council was dispatched
- [ ] All 4 surfaces reasoned and all 5 contracts locked before build dispatch
- [ ] **P4.0:** `[P4.0-QA-CSV]` per product policy; `eval/*.yaml` (≥1) on disk; **`[P4.0-EVAL-YAML]`** logged; **`forge-tdd` RED** logged per repo before GREEN implementation
- [ ] **P4.0b:** `[DESIGN-INGEST]` when net-new UI; waived or N/A documented otherwise
- [ ] All subagent statuses resolved (no NEEDS_CONTEXT or BLOCKED outstanding) before eval
- [ ] **P4.4 eval invoked** (not skipped after partial implement); eval returned GREEN before any PRs were raised
- [ ] conductor.log committed with all phase transitions, subagent dispatches, and escalations
- [ ] Dreamer retrospective triggered post-merge

---
name: conductor-orchestrate
description: "WHEN: PRD is locked. You are the master state machine orchestrating the entire forge workflow. Routes the task through all phases, tracks state, manages escalations, and coordinates subagents."
type: rigid
requires: [intake-interrogate, product-context-load, brain-read, brain-write, forge-worktree-gate, council-multi-repo-negotiate, spec-freeze, tech-plan-write-per-project, tech-plan-self-review, qa-manual-test-cases-from-prd, forge-tdd, eval-product-stack-up, qa-semantic-csv-orchestrate, forge-eval-gate, pr-set-coordinate, dream-retrospect-post-pr]
version: 1.0.14
preamble-tier: 4
triggers:
  - "start the pipeline"
  - "PRD is locked"
  - "orchestrate the workflow"
  - "run conductor"
allowed-tools:
  - Bash
  - Edit
  - Write
  - AskUserQuestion
---

# Conductor Orchestrate — Master State Machine

## Human input

This skill lists **`AskUserQuestion`** in **`allowed-tools`** — canonical for Claude Code and skill lint. Blocking prompts follow **[`skills/_shared/human-input.md`](../_shared/human-input.md)**. See **`using-forge`** **Interactive human input** and **Stage-local questioning**. Assistant dialogue: **`docs/forge-one-step-horizon.md`** and **`using-forge`** **Multi-question elicitation** items **4–8** (same as the **`Assistant chat`** line in **`commands/`** — **no defensive downstream-gate narration** mid-elicitation).

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
| "Semantic eval / manifest after the feature — faster to code first" | **State 4b is before State 5.** Without valid **`qa/semantic-eval-manifest.json`** + **`[P4.0-SEMANTIC-EVAL]`** (CSV execution path per **`docs/semantic-eval-csv.md`**; commit **`semantic-eval-run.log`** when produced), there is no machine-eval record and P4.4 has nothing honest to run. **Acceptance + TDD** live in **`manual-test-cases.csv`** + **`forge-tdd`**. |
| "`WAIVE_SEMANTIC_EVAL` / skip manifest so we can ship" | **Not allowed** for normal delivery. Only **`ABORT_TASK`** (human, logged) ends the run without **`qa/semantic-eval-manifest.json`** — that is **not** a shipped feature. |
| "`forge_qa_csv_before_eval: true` but we'll add the CSV after the semantic manifest" | Defeats the point: **manual CSV** (acceptance) must precede machine-eval logging when the flag is set. |
| "`/forge` but we'll skip CSV because `forge-product.md` never set the flag" | **`commands/forge.md` (`/forge`) = full pipeline:** State 4b **mandates** **`qa-prd-analysis`** + **`qa-manual-test-cases-from-prd`** and **`[P4.0-QA-CSV]`** before **`[P4.0-SEMANTIC-EVAL]`** — same as **`forge_qa_csv_before_eval: true`**. Persist **`forge_qa_csv_before_eval: true`** in **`forge-product.md`** if it was missing or false. |
| "Council can start without `[DISCOVERY]` — we'll grep branches during build" | **State 2.5** exists so **greenfield vs existing in-repo work** (topic branches, tags, open change requests) is resolved **before** contracts are negotiated. Skipping it repeats “two definitions of done.” STOP. Log **`[DISCOVERY]`** or an explicit skip per State 2.5 rules. |
| "I'll use a blocking prompt about merge order / P4.4 eval / tech-plan sign-off / QA CSV while PRD isn't locked or discovery isn't done" | **Violates stage-local questioning** (`using-forge`). Prompts must unblock **only** the **current** authorized phase. Surface the **first** missing prerequisite; do not burn the user's attention on hypothetical downstream choices. |
| "I'll narrate the full pipeline (State 4b → P4.4 → PR set → …) in chat on every turn while the user is still on an earlier gate" | **`docs/forge-one-step-horizon.md`** — **one-step horizon** in assistant messages; full order belongs in **`commands/forge.md`** / **README**, not repeated dialogue. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
THE ORCHESTRATOR IS THE SINGLE SOURCE OF STATE. NO PHASE IS SKIPPED, NO TRANSITION IS UNAUTHORIZED, AND NO SUBAGENT ESCALATION IS IGNORED.
NO P4.1 / IMPLEMENTATION DISPATCH WITHOUT [P4.0-SEMANTIC-EVAL] WITH VALID qa/semantic-eval-manifest.json PER docs/forge-task-verification.md AND [P4.0-TDD-RED] PER POLICY. ACCEPTANCE ROWS FOR RED/GREEN TESTS COME FROM qa/manual-test-cases.csv + TECH PLANS.
NO FULL /forge PIPELINE (commands/forge.md) WITHOUT [P4.0-QA-CSV] approved=yes BEFORE [P4.0-SEMANTIC-EVAL] — SET forge_qa_csv_before_eval: true IN forge-product.md IF UNSET OR FALSE.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Phase markers are logged out of order in `conductor.log`** — e.g., `[P4.4-EVAL-PASS]` appears before `[P4.0-SEMANTIC-EVAL]` or `[P4.1-DISPATCH]`, or `[P3-TECH-PLAN-LOCKED]` appears before `[P2-SPEC-FROZEN]`. Phase markers must be logged in strictly ascending order: P1 → P2 → P3 → P4.0 → P4.1 → P4.2 → P4.3 → P4.4 → P5. STOP. If out-of-order markers are detected in `conductor.log`, the pipeline state is corrupt — do not proceed. Diagnose which phase was skipped and invoke the missing skill before continuing.
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
- **`[P4.1-DISPATCH]` or `[DISPATCH]` without prior eval artifact** — Valid **`qa/semantic-eval-manifest.json`** + **`[P4.0-SEMANTIC-EVAL]`**; commit **`qa/semantic-eval-run.log`** when the runner produced it (**`docs/forge-task-verification.md`**). If the log jumps from tech plan to `IMPLEMENTATION_STARTED`, STOP; back up to **`qa-semantic-csv-orchestrate`** / **`docs/semantic-eval-csv.md`**.
- **Worktree is missing when dev-implementer or forge-tdd is about to be dispatched** — An implementer or TDD subagent working without a worktree will write code directly into the main branch, contaminating shared history. STOP. Run `git worktree list` in each affected repo. If the task branch is not listed, invoke `worktree-per-project-per-task` first. No dispatch until every affected repo shows a task-branch worktree in `git worktree list`.

## Purpose

The Conductor is the master state machine that orchestrates a single task (PRD) through the entire Forge lifecycle:

```
Intake → Load Product → Council → Tech Plans → **QA CSV (acceptance + TDD basis)** → **Semantic CSV execution (manifest + run.log) + forge-tdd RED** → **Design ingest (when net-new UI)** → Dispatch (GREEN) → Review → **Eval (E2E)** → PR Set
```

The Conductor:
- Ensures each state completes before moving to the next
- Tracks progress in the brain (git-backed state)
- Escalates blockers and failures
- Dispatches subagents for parallel work
- Routes back to earlier states if issues detected (self-heal loop)
- Logs every transition

## Reference (load on demand)

Deep detail — worked examples, detailed section breakdowns, edge-case deep-dives, templates,
and decision trees — lives in **`reference/conductor-reference.md`** (Agent Skills progressive disclosure). This
SKILL.md is the operational contract: discipline, core workflow/decision logic, and checklists.

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
- [ ] **State 4 tech plans:** Each `tech-plans/*.md` includes **Section 0, Section 1b–Section 1c** (API↔consumer **Section 1b.5**, unknowns **Section 1b.6**, review + XALIGN); **`[TECH-PLAN-REVIEW] … PASS`** per repo; **`[TECH-PLAN-XALIGN] … PASS`** or **N/A**; **`tech-plans/HUMAN_SIGNOFF.md`** + **`[TECH-PLAN-HUMAN]`** before State 4b.
- [ ] State transitions logged to conductor.log.
- [ ] Escalation paths clear and actionable.
- [ ] All states (Intake through Tech Plans) reachable.
- [ ] Logs human-readable, timestamped, machine-parseable.

### Phase 4 (Delivery & Verification)
- [ ] **P4.0 Prerequisites:** **`[P4.0-QA-CSV]`** with approved `manual-test-cases.csv` **before** `[P4.0-SEMANTIC-EVAL]` when **`forge_qa_csv_before_eval: true`** **or** entrypoint is **full `/forge`** (`commands/forge.md`); for **partial** runs with flag false/unset, log `skipped=not_required` only if CSV is intentionally omitted.
- [ ] **P4.0 Prerequisites:** Valid **`qa/semantic-eval-manifest.json`** + **`[P4.0-SEMANTIC-EVAL]`**; **`forge-tdd` RED** logged per repo (`[P4.0-TDD-RED]`); conductor log shows subagent runs for tests-before-feature. **Never** log `[P4.1-DISPATCH]` before the semantic-eval gate.
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

## Continuous Checkpoint Mode

After each phase completion, commit a WIP context snapshot so the pipeline state survives context compaction:

```bash
PHASE="<current phase marker, e.g. P2-COUNCIL>"
BRANCH=$(git rev-parse --abbrev-ref HEAD)
REPO_ROOT=$(git rev-parse --show-toplevel)

# Create a WIP commit with forge-context body
git add -A 2>/dev/null
git diff --cached --quiet || git commit -m "wip: forge-context [$PHASE]" --allow-empty-message 2>/dev/null || true
```

The commit message format is `wip: forge-context [<PHASE>]`. These WIP commits are squashed before PR using:

```bash
# Before raising PR: squash all WIP commits since branch point
BASE=$(git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null)
WIP_COUNT=$(git log --oneline "$BASE"..HEAD | grep -c "wip: forge-context" || echo 0)
if [ "$WIP_COUNT" -gt 0 ]; then
  echo "$WIP_COUNT WIP commits to squash before PR"
  # Use /review-readiness to verify, then squash interactively
fi
```

**When to checkpoint:** After each conductor.log write (`[P1.*]`, `[P2.*]`, `[P2-SPEC-FROZEN]`, `[P4.0-*]`, `[P4.1-DISPATCH]`, `[P4.4-EVAL-GREEN]`, `[P5.*]`).

**Why:** If context compacts mid-orchestration, the next session runs `/context-restore` to load the checkpoint, reads the conductor.log for phase state, and resumes from the exact phase. Without WIP commits, partial work may be untracked.

## Checklist

Before claiming orchestration complete:

- [ ] PRD locked in brain before council was dispatched
- [ ] All 4 surfaces reasoned and all 5 contracts locked before build dispatch
- [ ] **P4.0:** `[P4.0-QA-CSV]` per product policy; valid **`qa/semantic-eval-manifest.json`** + **`[P4.0-SEMANTIC-EVAL]`**; **`forge-tdd` RED** logged per repo before GREEN implementation
- [ ] **P4.0b:** `[DESIGN-INGEST]` when net-new UI; waived or N/A documented otherwise
- [ ] All subagent statuses resolved (no NEEDS_CONTEXT or BLOCKED outstanding) before eval
- [ ] **P4.4 eval invoked** (not skipped after partial implement); eval returned GREEN before any PRs were raised
- [ ] conductor.log committed with all phase transitions, subagent dispatches, and escalations
- [ ] Dreamer retrospective triggered post-merge

## Post-Implementation Checklist

- [ ] Current pipeline stage matches the last `[P*]` marker in `conductor.log`.
- [ ] No phase marker is logged before its prerequisite phase marker (ordering constraint upheld).
- [ ] `conductor.log` is git-committed to brain (not just written to disk).
- [ ] No phase was skipped by claiming "already done in chat" — each phase has an artifact or marker.
- [ ] The next gate's prerequisite is met before invoking the next skill.

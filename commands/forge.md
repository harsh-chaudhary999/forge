---
name: forge
description: "You MUST use this for full end-to-end delivery — invokes conductor-orchestrate with entrypoint full pipeline (/forge): all phases through PR set, dream, and mandatory State 4b manual QA CSV before semantic machine-eval (qa/semantic-automation.csv + semantic-eval-manifest.json)."
---

## Pipeline Overview

```
P1: Intake          → prd-locked.md + terminology.md
P2: Product Context → context-loaded.md
P3: Council         → shared-dev-spec.md (all 5 contracts)
P3: Tech Plans      → tech-plans/<repo>.md (per repo)
P4.0: QA Analysis   → qa/qa-analysis.md
P4.0: Manual CSV    → qa/manual-test-cases.csv
P4.0: Semantic CSV  → qa/semantic-automation.csv + semantic-eval-manifest.json
P4.0b: TDD RED      → failing tests committed per repo
P4.1: Build         → GREEN implementation committed per repo
P4.2: Review        → spec-reviewer + code-quality-reviewer per repo
P4.4: Eval          → EVAL PASS (all scenarios GREEN)
P5: PRs             → coordinated PR set per repo
P5: Dream           → retrospective + brain learnings
```

Gates (canonical `conductor.log` markers — see `docs/conductor-log-format.md`): `[P1-PRD-LOCKED]` → `[P2-SPEC-FROZEN]` → `[P3-TECH-PLAN-LOCKED]` → `[QA-ANALYSIS-LOCKED]` → `[P4.0-QA-CSV]` → `[P4.0-SEMANTIC-EVAL]` → `[P4.0-TDD-RED]` → `[P4.1-DISPATCH]` → `[P4.3-REVIEW-PASS]` → `[P4.4-EVAL-PASS]` → `[P5-PR-RAISED]`

Abort: log `[ABORT_TASK: <task-id>]` to conductor.log at any point — see **Abort Workflow** below.

**Primary skills invoked (in pipeline order):** `forge-intake-gate` → `intake-interrogate` → `forge-council-gate` → `council-multi-repo-negotiate` (+ reasoning/contract skills) → `spec-freeze` → `tech-plan-write-per-project` → `qa-prd-analysis` → `qa-manual-test-cases-from-prd` → `qa-semantic-csv-orchestrate` → `forge-tdd` → `conductor-orchestrate` (dispatch) → `forge-verification` → `forge-eval-gate` (eval drivers) → `self-heal-*` (if RED) → `pr-set-coordinate` → `pr-set-merge-order` → `dream-retrospect-post-pr`.

Invoke the `conductor-orchestrate` skill to run the **full end-to-end** Forge pipeline for this task.

If the user provided a PRD or product description after this command, use it as the initial input.
If no PRD was provided, elicit one in chat (open-ended: describe goals, paste, or path to a doc). **Discrete forks** (which task, run **`/intake`** vs supply lock file, product slug) must use a **blocking interactive prompt** per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** — not runbook-only *What to do next* without **AskQuestion** / **numbered options** in the **same** turn.

**`/forge` = E2E (all stages + QA):** Continue until **`conductor-orchestrate`** completes **delivery and shipping** for a non-aborted task: **intake → product context → council → tech plans → State 4b (manual QA CSV + semantic CSV/manifest machine-eval + TDD RED + design ingest when applicable) → P4.1 dispatch (GREEN) → reviews → P4.4 multi-surface eval → self-heal if needed → coordinated PRs → merge order → dreamer retrospective / brain learnings** — not “planning only.” **Do not** treat tech plans as the finish line. **Do not** skip **P4.4 eval** or **PR set** on a claimed-complete feature unless the human logs **`[ABORT_TASK]`** per conductor.

**Partial vs full (this command = full):** Other slash commands (**`/intake`**, **`/council`**, **`/plan`**, **`/build`**, **`/eval`**, **`/heal`**, …) are **user-chosen slices** — run only what that command says and honor **`forge_qa_csv_before_eval`** in **`~/forge/brain/products/<slug>/product.md`** for whether manual QA CSV is a hard gate **on those runs**. **`/forge` is different:** automate the **entire** conductor path above, **including** mandatory manual QA CSV in State 4b (see next section). Do **not** stop after tech plans as if the job were done.

**State 4b on `/forge` (mandatory — not “recommended”):** After **`shared-dev-spec.md`** and per-repo tech plans are locked, **before** **`[P4.0-SEMANTIC-EVAL]`** and **before** feature **TDD RED** on production code, you **must** run **`qa-prd-analysis`** then **`qa-manual-test-cases-from-prd`** through **Step 7 approval**, produce **`~/forge/brain/prds/<task-id>/qa/manual-test-cases.csv`** (≥1 approved row), and log **`[P4.0-QA-CSV] task_id=<id> rows=<n> approved=yes`**. **Do not** log **`[P4.0-QA-CSV] skipped=not_required`** on a **`/forge`** run. If **`product.md`** omits **`forge_qa_csv_before_eval`** or sets **`false`**, **set it to `true`** in that file when you complete this step so CI (`verify_forge_task.py`) and future runs match what you did. Then semantic **`qa/semantic-automation.csv`** + valid **`qa/semantic-eval-manifest.json`** (+ **`qa/semantic-eval-run.log`** when produced) per **`docs/semantic-eval-csv.md`**, log **`[P4.0-SEMANTIC-EVAL]`**, **`[P4.0-TDD-RED]`**, design ingest when applicable, dispatch, reviews, eval, heal, PR set, dream — per **`conductor-orchestrate`**. **Acceptance + RED tests** trace **`manual-test-cases.csv`** + tech plans — not **`eval/*.yaml`**.

Tell the orchestrator explicitly: **entrypoint = full pipeline (`/forge`)** so State 4b step 0 applies the stricter CSV rule in **`conductor-orchestrate`**.

Single-line map (same as **`conductor-orchestrate`**): intake → council → tech plans → **State 4b (QA CSV + semantic CSV/manifest machine-eval + RED + design gate)** → human checkpoints where skills require them → implementation → reviews → **full product eval** → heal if RED → **PR set / merges** → dreamer / brain.

**Session style (all hosts — convention, not automatic):** For **intake through tech-plan review**, use **planning-style** sessions (host-specific: e.g. Cursor **Plan**, review-first prompts on CLI). For **build, eval, heal**, use **execution-style** sessions (e.g. Cursor **Agent**, full tool use). Forge cannot flip the host’s mode or permissions programmatically. Remind the user when the Forge phase changes. See **`docs/platforms/session-modes-forge.md`**.

**Do not misrepresent intake:** Forge **`intake-interrogate`** is **not** “exactly eight chat questions, no design.” It requires **concrete `prd-locked.md` sections** (product, goal, success, **repos + registry**, contracts, timeline, rollback, metrics) and **design / UI (Q9)** when web, app, or user-visible UI is in scope — including the **verbatim design source-of-truth blockquote** in the intake thread and **`design_intake_anchor`**. A Figma URL in the PRD alone is **insufficient**. If an earlier run skipped that, **re-run intake**; do not tell the user Forge forbade asking.

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns, **no defensive downstream-gate narration** mid-elicitation — **`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration (repo-wide)**); **one blocking affordance per unrelated fork** (no bundled prose obligations); **no dual prompts** — **never** **`AskQuestion`** / **Questions** widget on **one** topic **and** a **long markdown question** on **another** in the **same** message; **no chat–widget duplicate** — long lists / same question body **once** in **chat**; **`AskQuestion`** = **short** title + **options** only (**`docs/forge-one-step-horizon.md`** **Chat vs `AskQuestion` / Questions widget**); **headline / first § = immediate next artifact** — **not** *What unlocks machine eval*, **`qa/semantic-automation.csv`**, or Step −1 **as the main heading** when **manual CSV** / **`qa-manual-test-cases-from-prd`** / **`qa-prd-analysis`** is still the next gate (**`docs/forge-one-step-horizon.md`** **Headline = immediate next step**); **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

**Forge plugin scope:** Orchestration uses skills and **`agents/`** from **this** repository and artifacts under **`~/forge/brain/`** only — no external “Forge-compatible” frameworks.

<HARD-GATE>
Do NOT treat **`/forge`** as intake-only or planning-only; do NOT omit **State 4b manual QA CSV**, **P4.4 eval**, or **PR set** on a non-**`[ABORT_TASK]`** run. Pass **`entrypoint = full pipeline (/forge)`** into **`conductor-orchestrate`**.
</HARD-GATE>

## Abort Workflow

To stop a `/forge` run mid-pipeline without leaving the brain in a half-written state:

**Step 1 — Signal abort:** Write the marker to conductor.log:
```bash
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [ABORT_TASK] task_id=<id> reason=<one-line reason>" \
  >> ~/forge/brain/prds/<task-id>/conductor.log
```
Or say `[ABORT_TASK: <task-id>]` in chat — the agent will detect it.

**Step 2 — Agent behavior on abort detection:**
- STOP all new brain writes and subagent dispatches immediately
- Do NOT create new files in `~/forge/brain/prds/<task-id>/`
- Log `[ABORT_COMPLETED] task_id=<id>` to conductor.log
- List uncommitted brain changes for user review:
  ```bash
  git -C ~/forge/brain status prds/<task-id>/
  ```

**Step 3 — Cleanup (user-driven):**
```bash
# See what was written
git -C ~/forge/brain log --oneline prds/<task-id>/ | head -10

# Revert partial brain writes if needed
git -C ~/forge/brain revert HEAD  # or specific commit

# Remove worktrees created for this task
bash .claude/scripts/forge-worktree-cleanup.sh . 0 1
```

**What is NOT cleaned automatically:** Code commits on feature branches in product repos are NOT reverted by abort — those require manual `git reset` or branch deletion per repo. Abort only stops new brain writes; it does not undo implementation work.

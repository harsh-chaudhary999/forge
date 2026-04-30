---
name: forge
description: "You MUST use this for full end-to-end delivery — invokes conductor-orchestrate with entrypoint full pipeline (/forge): all phases through PR set, dream, and mandatory State 4b manual QA CSV before eval YAML."
---

Invoke the `conductor-orchestrate` skill to run the **full end-to-end** Forge pipeline for this task.

If the user provided a PRD or product description after this command, use it as the initial input.
If no PRD was provided, elicit one in chat (open-ended: describe goals, paste, or path to a doc). **Discrete forks** (which task, run **`/intake`** vs supply lock file, product slug) must use a **blocking interactive prompt** per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** — not runbook-only *What to do next* without **AskQuestion** / **numbered options** in the **same** turn.

**`/forge` = E2E (all stages + QA):** Continue until **`conductor-orchestrate`** completes **delivery and shipping** for a non-aborted task: **intake → product context → council → tech plans → State 4b (manual QA CSV + eval YAML + TDD RED + design ingest when applicable) → P4.1 dispatch (GREEN) → reviews → P4.4 multi-surface eval → self-heal if needed → coordinated PRs → merge order → dreamer retrospective / brain learnings** — not “planning only.” **Do not** treat tech plans as the finish line. **Do not** skip **P4.4 eval** or **PR set** on a claimed-complete feature unless the human logs **`[ABORT_TASK]`** per conductor.

**Partial vs full (this command = full):** Other slash commands (**`/intake`**, **`/council`**, **`/plan`**, **`/build`**, **`/eval`**, **`/heal`**, …) are **user-chosen slices** — run only what that command says and honor **`forge_qa_csv_before_eval`** in **`~/forge/brain/products/<slug>/product.md`** for whether manual QA CSV is a hard gate **on those runs**. **`/forge` is different:** automate the **entire** conductor path above, **including** mandatory manual QA CSV in State 4b (see next section). Do **not** stop after tech plans as if the job were done.

**State 4b on `/forge` (mandatory — not “recommended”):** After **`shared-dev-spec.md`** and per-repo tech plans are locked, **before** **`[P4.0-EVAL-YAML]`** and **before** feature **TDD RED** on production code, you **must** run **`qa-prd-analysis`** then **`qa-manual-test-cases-from-prd`** through **Step 7 approval**, produce **`~/forge/brain/prds/<task-id>/qa/manual-test-cases.csv`** (≥1 approved row), and log **`[P4.0-QA-CSV] task_id=<id> rows=<n> approved=yes`**. **Do not** log **`[P4.0-QA-CSV] skipped=not_required`** on a **`/forge`** run. If **`product.md`** omits **`forge_qa_csv_before_eval`** or sets **`false`**, **set it to `true`** in that file when you complete this step so CI (`verify_forge_task.py`) and future runs match what you did. Then **`eval/`** YAML, **`[P4.0-EVAL-YAML]`**, **`[P4.0-TDD-RED]`**, design ingest when applicable, dispatch, reviews, eval, heal, PR set, dream — per **`conductor-orchestrate`**. **Agent-facing canonical order** (no “last gate first”): **`qa-write-scenarios` Step −1** in **`skills/qa-write-scenarios/SKILL.md`**.

Tell the orchestrator explicitly: **entrypoint = full pipeline (`/forge`)** so State 4b step 0 applies the stricter CSV rule in **`conductor-orchestrate`**.

Single-line map (same as **`conductor-orchestrate`**): intake → council → tech plans → **State 4b (QA CSV + eval YAML + RED + design gate)** → human checkpoints where skills require them → implementation → reviews → **full product eval** → heal if RED → **PR set / merges** → dreamer / brain.

**Session style (all hosts — convention, not automatic):** For **intake through tech-plan review**, use **planning-style** sessions (host-specific: e.g. Cursor **Plan**, review-first prompts on CLI). For **build, eval, heal**, use **execution-style** sessions (e.g. Cursor **Agent**, full tool use). Forge cannot flip the host’s mode or permissions programmatically. Remind the user when the Forge phase changes. See **`docs/platforms/session-modes-forge.md`**.

**Do not misrepresent intake:** Forge **`intake-interrogate`** is **not** “exactly eight chat questions, no design.” It requires **concrete `prd-locked.md` sections** (product, goal, success, **repos + registry**, contracts, timeline, rollback, metrics) and **design / UI (Q9)** when web, app, or user-visible UI is in scope — including the **verbatim design source-of-truth blockquote** in the intake thread and **`design_intake_anchor`**. A Figma URL in the PRD alone is **insufficient**. If an earlier run skipped that, **re-run intake**; do not tell the user Forge forbade asking.

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns, **no defensive downstream-gate narration** mid-elicitation — **`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration (repo-wide)**); **one blocking affordance per unrelated fork** (no bundled prose obligations); **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

**Forge plugin scope:** Orchestration uses skills and **`agents/`** from **this** repository and artifacts under **`~/forge/brain/`** only — no external “Forge-compatible” frameworks.

<HARD-GATE>
Do NOT treat **`/forge`** as intake-only or planning-only; do NOT omit **State 4b manual QA CSV**, **P4.4 eval**, or **PR set** on a non-**`[ABORT_TASK]`** run. Pass **`entrypoint = full pipeline (/forge)`** into **`conductor-orchestrate`**.
</HARD-GATE>

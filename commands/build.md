---
name: build
description: "Partial slice — isolated worktrees + TDD implementation (GREEN after RED). Invoke forge-worktree-gate and forge-tdd; dev-implementer. Not a substitute for full /forge or for skipping State 4b gates."
---

Invoke **`forge-worktree-gate`**, then drive implementation with **`forge-tdd`** (and **`dev-implementer`** as appropriate): **RED → GREEN → refactor** in **fresh git worktrees** per repo.

This command assumes **approved tech plans** and that **orchestration gates** for the task are satisfied **before** production feature work — see **`agents/dev-implementer.md`** (**`BLOCKED_ORCHESTRATION`** if **`eval/`** is empty, missing **`[P4.0-EVAL-YAML]`**, or missing QA CSV / log when **`product.md`** requires it or the run was full **`/forge`**).

<HARD-GATE>
Do NOT ship production feature code that bypasses **`conductor-orchestrate` State 4b** when the task is under **full `/forge`** or when **`forge_qa_csv_before_eval: true`** — implementer must refuse; back up to **`qa-manual-test-cases-from-prd`**, **`eval-translate-english`**, or **`forge-tdd`** RED as needed.
</HARD-GATE>

**Forge plugin scope:** Worktrees and brain paths per **`worktree-per-project-per-task`**; this repo’s skills only.

**vs `/forge`:** **`/build`** is execution for **implementation** only. Full pipeline (including State 4b QA CSV first on **`/forge`**): **`commands/forge.md`**.

**Session style:** Prefer **execution-style** (edits, tests, terminals). See **`docs/platforms/session-modes-forge.md`**.

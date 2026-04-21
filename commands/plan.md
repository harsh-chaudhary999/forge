---
name: plan
description: "Partial slice — per-repo tech plans only. Invoke tech-plan-write-per-project from frozen shared-dev-spec. Does not run full E2E or QA CSV by itself (use /forge for mandatory QA+eval path on full runs)."
---

Invoke the **`tech-plan-write-per-project`** skill to author **per-repository tech plans** only.

This requires a **locked shared dev spec** from council. If **`shared-dev-spec.md`** is not locked for the task, direct the user to run **`/council`** first.

Each plan: bite-sized tasks (exact files, complete code where the skill requires it, exact commands), aligned to **`shared-dev-spec.md`**. Follow **`spec-freeze`** if the conductor phase is post-freeze.

<HARD-GATE>
Do NOT dispatch **`dev-implementer`** or open **Phase 4.1** from this command alone — tech plans are inputs to **State 4b** (QA CSV, eval YAML, RED) and then build. Per **`conductor-orchestrate`**, feature dispatch requires **`[P4.0-EVAL-YAML]`** and policy-complete **State 4b**.
</HARD-GATE>

**Forge plugin scope:** Plans live under the task’s brain path; skills from **`skills/`**.

**vs `/forge`:** **`/plan`** is a **partial** slice. Full E2E including mandatory manual QA CSV on the **`/forge`** entrypoint: **`commands/forge.md`**.

**Session style:** Prefer **planning-style** while authoring or **reviewing** tech plans; switch to **execution-style** for **`/build`**. See **`docs/platforms/session-modes-forge.md`**.

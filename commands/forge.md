---
description: "Run the full Forge pipeline: PRD → Intake → Council → Tech Plans → Build → Eval → Review → PR Set → Brain"
---

Invoke the `conductor-orchestrate` skill to run the full Forge pipeline.

If the user provided a PRD or product description after this command, use it as the initial input.
If no PRD was provided, ask the user to describe what they want to build or provide a path to an existing PRD document.

The conductor will orchestrate the entire flow: intake → council → tech plans → human approval → build → review → eval → self-heal (if needed) → PR coordination → dreamer retrospective.

**Session style (all hosts — convention, not automatic):** For **intake through tech-plan review**, use **planning-style** sessions (host-specific: e.g. Cursor **Plan**, review-first prompts on CLI). For **build, eval, heal**, use **execution-style** sessions (e.g. Cursor **Agent**, full tool use). Forge cannot flip the host’s mode or permissions programmatically. Remind the user when the phase changes. See **`docs/platforms/session-modes-forge.md`**.

**Do not misrepresent intake:** Forge **`intake-interrogate`** is **not** “exactly eight chat questions, no design.” It requires **concrete `prd-locked.md` sections** (product, goal, success, **repos + registry**, contracts, timeline, rollback, metrics) and **design / UI (Q9)** when web, app, or user-visible UI is in scope — including the **verbatim design source-of-truth blockquote** in the intake thread and **`design_intake_anchor`**. A Figma URL in the PRD alone is **insufficient**. If an earlier run skipped that, **re-run intake**; do not tell the user Forge forbade asking.

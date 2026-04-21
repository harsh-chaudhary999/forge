---
name: intake
description: "Partial slice — PRD intake only. Invoke forge-intake-gate and intake-interrogate; lock prd-locked.md in brain. Does NOT run council, tech plans, or full E2E (use /forge for that)."
---

Invoke the **`forge-intake-gate`** skill, then **`intake-interrogate`**, to run **PRD intake only** for this task.

If the user provided a PRD or description after this command, use it as the initial PRD input. If no PRD was provided, ask the user to describe what they want to build.

The intake process locks the PRD under **`~/forge/brain/prds/<task-id>/`** as **`prd-locked.md`**: **variable** number of user turns — confidence-first; **stop** when mandatory lock fields are concrete (no fixed “eight questions” quota). When web, app, or user-visible UI is in scope, **Q9 design / UI** is mandatory per **`intake-interrogate`**.

<HARD-GATE>
Do NOT claim intake is complete without **concrete** `prd-locked.md` sections (product, goal, success, **repos + registry**, contracts, timeline, rollback, metrics) and, when UI is in scope, the **verbatim** design source-of-truth from **Q9** in an assistant message plus **`design_intake_anchor`** in the lock. Do NOT jump to **`/council`** or implementation in the same turn unless the user explicitly asks — this command’s scope is intake through lock.
</HARD-GATE>

**Forge plugin scope:** Use skills and brain paths from **this** Forge repo only; brain root is **`~/forge/brain/`**.

**vs `/forge`:** **`/intake`** is a **partial** slice. Full E2E (intake → … → QA CSV → eval → merge → dream) is **`/forge`** — see **`commands/forge.md`**.

**Session style:** Prefer **planning-style**. See **`docs/platforms/session-modes-forge.md`**.

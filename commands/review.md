---
name: review
description: "Partial slice — two-stage review: forge-trust-code (spec compliance) then code quality. Read-heavy first; execution-style when applying fixes."
---

Invoke **`forge-trust-code`** to run the **two-stage review** pipeline.

**Stage 1 — Spec reviewer:** Maps requirements to **actual code**; rejects trust in implementer narrative alone.  
**Stage 2 — Code quality reviewer:** Runs only if Stage 1 passes; broader quality dimensions per project standards.

<HARD-GATE>
Do NOT skip Stage 1 for “small” diffs when **`forge-trust-code`** is in scope — spec claims must be verified against code.
</HARD-GATE>

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** (**`using-forge`** **Horizon narration**) — in dialogue, only the **immediate** next prerequisite unless the user asks what comes later or the current step truly depends on a downstream artifact.

**Forge plugin scope:** This repo’s review integration; brain + product repos as the skill specifies.

**vs `/forge`:** **`/review`** is a **partial** slice (post-implementation gate). Full E2E: **`commands/forge.md`**.

**Session style:** Bias **planning-style** for read-heavy spec review; **execution-style** when applying fixes. See **`docs/platforms/session-modes-forge.md`**.

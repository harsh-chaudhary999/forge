---
name: why
description: "Lookup — invoke brain-why to trace provenance of a decision (who, when, why, alternatives, outcomes)."
---

Invoke the **`brain-why`** skill.

The user’s argument is a **decision ID** (e.g. **`D20260410-001`**) or a **search term**. If nothing was provided, use a **blocking interactive prompt** per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** — e.g. **`AskQuestion`** or **numbered list** of recent decision IDs if you can list them from brain, else one field for ID or search term, then **stop** — not an open-ended *which decision?* with no structured reply path on hosts that need it.

Output: provenance chain — who decided → when → why → alternatives → what it blocked or unblocked → linked decisions — under **`~/forge/brain/`**.

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** (**`using-forge`** **Horizon narration**) — in dialogue, only the **immediate** next prerequisite unless the user asks what comes later or the current step truly depends on a downstream artifact.

**Forge plugin scope:** Brain read; **`brain-why`** skill only.

**vs `/forge`:** Lookup only, not delivery. Full E2E: **`commands/forge.md`**.

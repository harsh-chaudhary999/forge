---
name: why
description: "Lookup — invoke brain-why to trace provenance of a decision (who, when, why, alternatives, outcomes)."
---

Invoke the **`brain-why`** skill.

The user’s argument is a **decision ID** (e.g. **`D20260410-001`**) or a **search term**. If nothing was provided, ask which decision to trace.

Output: provenance chain — who decided → when → why → alternatives → what it blocked or unblocked → linked decisions — under **`~/forge/brain/`**.

**Forge plugin scope:** Brain read; **`brain-why`** skill only.

**vs `/forge`:** Lookup only, not delivery. Full E2E: **`commands/forge.md`**.

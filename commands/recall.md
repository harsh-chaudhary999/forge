---
name: recall
description: "Search — invoke brain-recall for past decisions, patterns, and gotchas in ~/forge/brain (hybrid search per skill)."
---

Invoke the **`brain-recall`** skill.

The user’s argument is a **search query** (topics, components, past incidents). If empty, ask what to search for.

**`brain-recall`** searches **`~/forge/brain/`** (grep, tags, recency) per the skill — read-only.

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** (**`using-forge`** **Horizon narration**) — in dialogue, only the **immediate** next prerequisite unless the user asks what comes later or the current step truly depends on a downstream artifact.

**Forge plugin scope:** Brain read only.

**vs `/forge`:** **`/recall`** does not run delivery. Full E2E: **`commands/forge.md`**.

---
name: recall
description: "Search — invoke brain-recall for past decisions, patterns, and gotchas in ~/forge/brain (hybrid search per skill)."
---

Invoke the **`brain-recall`** skill.

The user’s argument is a **search query** (topics, components, past incidents). If empty, ask what to search for.

**`brain-recall`** searches **`~/forge/brain/`** (grep, tags, recency) per the skill — read-only.

**Forge plugin scope:** Brain read only.

**vs `/forge`:** **`/recall`** does not run delivery. Full E2E: **`commands/forge.md`**.

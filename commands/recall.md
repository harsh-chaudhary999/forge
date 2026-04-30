---
name: recall
description: "Search — invoke brain-recall for past decisions, patterns, and gotchas in ~/forge/brain (hybrid search per skill)."
---

Invoke the **`brain-recall`** skill.

The user’s argument is a **search query** (topics, components, past incidents). If empty, ask what to search for.

**`brain-recall`** searches **`~/forge/brain/`** (grep, tags, recency) per the skill — read-only.

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns, **no defensive downstream-gate narration** mid-elicitation — **`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration (repo-wide)**); **one blocking affordance per unrelated fork** (no bundled prose obligations); **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

**Forge plugin scope:** Brain read only.

**vs `/forge`:** **`/recall`** does not run delivery. Full E2E: **`commands/forge.md`**.

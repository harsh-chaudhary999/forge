---
name: remember
description: "Write — invoke brain-write to record a decision, learning, or pattern to ~/forge/brain with provenance."
---

Invoke the **`brain-write`** skill.

The user’s message is the **content to record** (decision, learning, pattern). If empty, ask what to persist.

**`brain-write`** creates an auditable record (ID, timestamp, context, rationale, alternatives, confidence, links) and commits under **`~/forge/brain/`** per **`forge-brain-persist`** / **`forge-brain-layout`**.

<HARD-GATE>
Do NOT fabricate decision IDs or back-date entries — follow the skill’s numbering and frontmatter rules.
</HARD-GATE>

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns); **one blocking affordance per unrelated fork** (no bundled prose obligations); **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

**Forge plugin scope:** Brain writes only; no product-repo commits unless the user asked.

**vs `/forge`:** **`/remember`** is a **utility**; it does not advance the delivery pipeline. Full E2E: **`commands/forge.md`**.

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

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns, **no defensive downstream-gate narration** mid-elicitation — **`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration (repo-wide)**); **one blocking affordance per unrelated fork** (no bundled prose obligations); **no dual prompts** — **never** **`AskQuestion`** / **Questions** widget on **one** topic **and** a **long markdown question** on **another** in the **same** message; **no chat–widget duplicate** — long lists / same question body **once** in **chat**; **`AskQuestion`** = **short** title + **options** only (**`docs/forge-one-step-horizon.md`** **Chat vs `AskQuestion` / Questions widget**); **headline / first § = immediate next artifact** — **not** *What unlocks eval YAML*, **eval `*.yaml`**, or Step −1 **as the main heading** when **manual CSV** / **`qa-manual-test-cases-from-prd`** / **`qa-prd-analysis`** is still the next gate (**`docs/forge-one-step-horizon.md`** **Headline = immediate next step**); **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

**Forge plugin scope:** Brain writes only; no product-repo commits unless the user asked.

**vs `/forge`:** **`/remember`** is a **utility**; it does not advance the delivery pipeline. Full E2E: **`commands/forge.md`**.

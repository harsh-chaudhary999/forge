---
name: why
description: "Lookup — invoke brain-why to trace provenance of a decision (who, when, why, alternatives, outcomes)."
---

Invoke the **`brain-why`** skill.

The user’s argument is a **decision ID** (e.g. **`D20260410-001`**) or a **search term**. If nothing was provided, use a **blocking interactive prompt** per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** — e.g. **`AskQuestion`** or **numbered list** of recent decision IDs if you can list them from brain, else one field for ID or search term, then **stop** — not an open-ended *which decision?* with no structured reply path on hosts that need it.

Output: provenance chain — who decided → when → why → alternatives → what it blocked or unblocked → linked decisions — under **`~/forge/brain/`**.

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns, **no defensive downstream-gate narration** mid-elicitation — **`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration (repo-wide)**); **one blocking affordance per unrelated fork** (no bundled prose obligations); **no dual prompts** — **never** **`AskQuestion`** / **Questions** widget on **one** topic **and** a **long markdown question** on **another** in the **same** message; **no chat–widget duplicate** — long lists / same question body **once** in **chat**; **`AskQuestion`** = **short** title + **options** only (**`docs/forge-one-step-horizon.md`** **Chat vs `AskQuestion` / Questions widget**); **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

**Forge plugin scope:** Brain read; **`brain-why`** skill only.

**vs `/forge`:** Lookup only, not delivery. Full E2E: **`commands/forge.md`**.

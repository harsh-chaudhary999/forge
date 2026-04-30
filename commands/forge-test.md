---
name: forge-test
description: "Meta — invoke forge-self-test against the bundled seed product to validate this Forge repo’s skills and pipeline wiring (not your production product)."
---

Invoke the **`forge-self-test`** skill to run the **Forge repository self-test** only.

This exercises the **synthetic seed** product (**`seed-product/`**, seed PRDs under **`seed/prds/`**) to validate: intake → council → tech plans → build → eval → review → PR coordination **as implemented in this plugin repo**.

Reports: **pass/fail per phase**, timing, any skill invocation or output anomalies.

<HARD-GATE>
Do NOT confuse **`/forge-test`** with **`/forge`** — **`/forge-test`** validates **Forge itself**; **`/forge`** runs **your** task through **`conductor-orchestrate`** against **your** brain PRD and **`product.md`**.
</HARD-GATE>

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns, **no defensive downstream-gate narration** mid-elicitation — **`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration (repo-wide)**); **one blocking affordance per unrelated fork** (no bundled prose obligations); **no dual prompts** — **never** **`AskQuestion`** / **Questions** widget on **one** topic **and** a **long markdown question** on **another** in the **same** message; **no chat–widget duplicate** — long lists / same question body **once** in **chat**; **`AskQuestion`** = **short** title + **options** only (**`docs/forge-one-step-horizon.md`** **Chat vs `AskQuestion` / Questions widget**); **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

**Forge plugin scope:** This repo + **`seed-product`**; not a substitute for product-specific **`/forge`**.

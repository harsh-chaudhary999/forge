---
name: heal
description: "Partial slice — self-heal after eval RED: locate fault, triage, fix, verify (max 3 loops). Invoke self-heal-locate-fault then triage/debug skills per conductor."
---

Invoke **`self-heal-locate-fault`** to begin the **self-heal** loop after a failed **`/eval`** (or equivalent **`forge-eval-gate`** outcome).

Pipeline: **locate** failing service → **triage** (flaky test, bad test, real bug, environment) per **`self-heal-triage`** → **systematic debug** (**`self-heal-systematic-debug`**) → **fix** → **re-verify** (re-run eval). Cap: **3** attempts per **`self-heal-loop-cap`**; then **escalate** to the human with evidence.

**RED:** Fault evidence is **`~/forge/brain/prds/<task-id>/qa/semantic-eval-run.log`** — **JSON lines per step** after the header — plus **`semantic-eval-manifest.json`**. Pass those into **`self-heal-locate-fault`** / **`self-heal-triage`**.

<HARD-GATE>
Do NOT silently drop failing eval scenarios — after three failed heal loops, **STOP** and escalate; do not merge or declare success.
</HARD-GATE>

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns, **no defensive downstream-gate narration** mid-elicitation — **`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration (repo-wide)**); **one blocking affordance per unrelated fork** (no bundled prose obligations); **no dual prompts** — **never** **`AskQuestion`** / **Questions** widget on **one** topic **and** a **long markdown question** on **another** in the **same** message; **no chat–widget duplicate** — long lists / same question body **once** in **chat**; **`AskQuestion`** = **short** title + **options** only (**`docs/forge-one-step-horizon.md`** **Chat vs `AskQuestion` / Questions widget**); **headline / first § = immediate next artifact** — **not** *What unlocks machine eval*, **`qa/semantic-automation.csv`**, or Step −1 **as the main heading** when **manual CSV** / **`qa-manual-test-cases-from-prd`** / **`qa-prd-analysis`** is still the next gate (**`docs/forge-one-step-horizon.md`** **Headline = immediate next step**); **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

**Forge plugin scope:** Skills under **`skills/self-heal-*`**; evidence in brain and repo worktrees.

**vs `/forge`:** **`/heal`** is a **reactive** slice after eval. Full E2E including eval green path and PR set: **`commands/forge.md`** (`/forge`).

**Session style:** Prefer **execution-style**. See **`docs/platforms/session-modes-forge.md`**.

**Product terms:** When a failure is an **assertion on visible copy** (banner text, label, API error `message`) and **`~/forge/brain/prds/<task-id>/terminology.md`** exists, check for **mismatch** between scenario **`expected`**, app output, and the term sheet; fix **code**, **YAML**, or **terminology** with a logged decision — not ad hoc renames in chat only ([docs/terminology-review.md](../docs/terminology-review.md)).

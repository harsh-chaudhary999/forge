---
name: council
description: "Partial slice — multi-surface council only. Invoke forge-council-gate and council-multi-repo-negotiate; lock shared-dev-spec and contracts. Requires locked PRD first."
---

Invoke the **`forge-council-gate`** skill, then **`council-multi-repo-negotiate`**, to run **council only**.

This requires a **locked PRD** from intake. If no **`prd-locked.md`** exists for the current task, **STOP** and use a **blocking interactive prompt** per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** (e.g. **1)** run **`/intake`** in this session **2)** paste or point to a PRD to draft a lock **3)** abort) — not prose-only *run `/intake` first* with no same-turn choices.

**Product terms:** Read **`~/forge/brain/prds/<task-id>/terminology.md`** when present; align **contract** and **error-message** strings with **canonical** rows before freeze ([docs/terminology-review.md](../docs/terminology-review.md), **`council-multi-repo-negotiate`**). **Session-resume (standalone /council without full conductor):** **`[TERMINOLOGY] …` is appended in `council-multi-repo-negotiate` Step 5.4 only** (end of council — not in **`forge-council-gate`**, to avoid two conflicting lines). `prompt-submit-gates.cjs` uses the **last** [TERMINOLOGY] line in `conductor.log` for **NEXT GATE** hints.

**Review / checklist protocol (v1):** [docs/terminology-review.md](../docs/terminology-review.md) — *Interactive review protocol* and *Entrypoint matrix* sections. Cross-repo renames: log in **`planning-doubts.md`** and **`terminology.md`** (revision rows).

The council invokes the four surface reasoning skills (backend, web, app, infra) and negotiates cross-service contracts (REST, DB, events, cache, search). Unresolvable conflicts escalate per **`dream-resolve-inline`** / dreamer rules in **`conductor-orchestrate`**.

<HARD-GATE>
Do NOT write per-repo **tech plans** or start **State 4b** inside this command unless the user explicitly asks — council’s output is **`shared-dev-spec.md`** (and related contract artifacts), not implementation.
</HARD-GATE>

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns, **no defensive downstream-gate narration** mid-elicitation — **`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration (repo-wide)**); **one blocking affordance per unrelated fork** (no bundled prose obligations); **no dual prompts** — **never** **`AskQuestion`** / **Questions** widget on **one** topic **and** a **long markdown question** on **another** in the **same** message; **no chat–widget duplicate** — long lists / same question body **once** in **chat**; **`AskQuestion`** = **short** title + **options** only (**`docs/forge-one-step-horizon.md`** **Chat vs `AskQuestion` / Questions widget**); **headline / first § = immediate next artifact** — **not** *What unlocks machine eval*, **`qa/semantic-automation.csv`**, or Step −1 **as the main heading** when **manual CSV** / **`qa-manual-test-cases-from-prd`** / **`qa-prd-analysis`** is still the next gate (**`docs/forge-one-step-horizon.md`** **Headline = immediate next step**); **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

**Forge plugin scope:** Brain under **`~/forge/brain/`**; skills from this repo’s **`skills/`**.

**vs `/forge`:** **`/council`** is a **partial** slice. Full E2E is **`/forge`** — see **`commands/forge.md`**.

**Session style:** Prefer **planning-style**. See **`docs/platforms/session-modes-forge.md`**.

---
name: intake
description: "Partial slice — PRD intake only. Invoke forge-intake-gate and intake-interrogate; lock prd-locked.md in brain. Does NOT run council, tech plans, or full E2E (use /forge for that)."
---

Invoke the **`forge-intake-gate`** skill, then **`intake-interrogate`**, to run **PRD intake only** for this task.

If the user provided a PRD or description after this command, use it as the initial PRD input. If no PRD was provided, elicit one in chat (open-ended: goals, paste, or path to a doc). **Discrete forks** (task-id, product slug, confirm scope) must use a **blocking interactive prompt** per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** — **`AskQuestion`** / **`AskUserQuestion`** / **numbered options + stop** — not a runbook-only *reply with…* with no same-turn choices.

**No bundled turns:** Do **not** pair **one** **`AskQuestion`** (e.g. task-id only) with a **prose wall** that simultaneously demands Q9 design authority, Figma vs brain-path locks, net-new vs reuse, **and** unrelated roadmap or waiver copy — each distinct intake decision gets **its own** structured or sequential turn (**`using-forge`** **Multi-question elicitation** item **6**; **`docs/forge-one-step-horizon.md`** **No bundled unrelated decisions**).

The intake process locks the PRD under **`~/forge/brain/prds/<task-id>/`** as **`prd-locked.md`**: **variable** number of user turns — confidence-first; **stop** when mandatory lock fields are concrete (no fixed “eight questions” quota). When web, app, or user-visible UI is in scope, **Q9 design / UI** is mandatory per **`intake-interrogate`**.

**Product terms:** When the PRD names **concepts, features, or labels** that will appear in **UI, API, or support copy**, maintain **`terminology.md`** in the same task path per **`intake-interrogate`** and [docs/terminology-review.md](../docs/terminology-review.md) (interactive **AskQuestion**-style review; file is source of truth).

**Process “todos” (v1):** Long **Q&A** and follow-ups belong in **`planning-doubts.md`**; do **not** add a freestanding **`task-progress.md`** per [docs/terminology-review.md](../docs/terminology-review.md) unless the team later adopts and documents it in **`forge-brain-layout`**. **Entrypoint row:** same doc, **§ Entrypoint matrix — commands + slice skills (v1)**.

<HARD-GATE>
Do NOT claim intake is complete without **concrete** `prd-locked.md` sections (product, goal, success, **repos + registry**, contracts, timeline, rollback, metrics) and, when UI is in scope, the **verbatim** design source-of-truth from **Q9** in an assistant message plus **`design_intake_anchor`** in the lock. Do NOT jump to **`/council`** or implementation in the same turn unless the user explicitly asks — this command’s scope is intake through lock.
</HARD-GATE>

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns); **one blocking affordance per unrelated fork** (no bundled prose obligations); **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

**Forge plugin scope:** Use skills and brain paths from **this** Forge repo only; brain root is **`~/forge/brain/`**.

**vs `/forge`:** **`/intake`** is a **partial** slice. Full E2E is **`/forge`** — see **`commands/forge.md`**. In **live chat**, do not narrate the full downstream chain each turn — **`docs/forge-one-step-horizon.md`**.

**Session style:** Prefer **planning-style**. See **`docs/platforms/session-modes-forge.md`**.

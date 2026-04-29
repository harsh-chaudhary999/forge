---
name: intake
description: "Partial slice — PRD intake only. Invoke forge-intake-gate and intake-interrogate; lock prd-locked.md in brain. Does NOT run council, tech plans, or full E2E (use /forge for that)."
---

Invoke the **`forge-intake-gate`** skill, then **`intake-interrogate`**, to run **PRD intake only** for this task.

If the user provided a PRD or description after this command, use it as the initial PRD input. If no PRD was provided, elicit one in chat (open-ended: goals, paste, or path to a doc). **Discrete forks** (task-id, product slug, confirm scope) must use a **blocking interactive prompt** per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** — **`AskQuestion`** / **`AskUserQuestion`** / **numbered options + stop** — not a runbook-only *reply with…* with no same-turn choices.

**No bundled turns:** Do **not** pair **one** **`AskQuestion`** (e.g. task-id only) with a **prose wall** that simultaneously demands Q9 design authority, Figma vs brain-path locks, net-new vs reuse, **and** downstream QA→YAML roadmap — each distinct intake decision gets **its own** structured or sequential turn (**`using-forge`** **Multi-question elicitation** item **6**; **`docs/forge-one-step-horizon.md`** **Bundled intake turns**).

The intake process locks the PRD under **`~/forge/brain/prds/<task-id>/`** as **`prd-locked.md`**: **variable** number of user turns — confidence-first; **stop** when mandatory lock fields are concrete (no fixed “eight questions” quota). When web, app, or user-visible UI is in scope, **Q9 design / UI** is mandatory per **`intake-interrogate`**.

<HARD-GATE>
Do NOT claim intake is complete without **concrete** `prd-locked.md` sections (product, goal, success, **repos + registry**, contracts, timeline, rollback, metrics) and, when UI is in scope, the **verbatim** design source-of-truth from **Q9** in an assistant message plus **`design_intake_anchor`** in the lock. Do NOT jump to **`/council`** or implementation in the same turn unless the user explicitly asks — this command’s scope is intake through lock.
</HARD-GATE>

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** (**`using-forge`** **Horizon narration**) — in dialogue, only the **immediate** next prerequisite unless the user asks what comes later or the current step truly depends on a downstream artifact.

**Forge plugin scope:** Use skills and brain paths from **this** Forge repo only; brain root is **`~/forge/brain/`**.

**vs `/forge`:** **`/intake`** is a **partial** slice. Full E2E is **`/forge`** — see **`commands/forge.md`**. In **live chat**, do not narrate the full downstream chain each turn — **`docs/forge-one-step-horizon.md`**.

**Session style:** Prefer **planning-style**. See **`docs/platforms/session-modes-forge.md`**.

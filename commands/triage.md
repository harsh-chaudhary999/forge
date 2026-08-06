---
name: triage
description: "Partial slice — Lane & Risk classification only. Invoke lane-risk-triage to decide Scope-led vs Build-led and, for Build-led, Standard vs High-risk. Does NOT run intake, council, or full E2E (use /forge for that)."
---

Invoke the **`lane-risk-triage`** skill to classify a roadmap item **before** any PRD gets written.

If the user provided a roadmap item, ticket, or description after this command, use it as the input. If none was provided, ask for one (open-ended: paste the item, or a link/path to it).

**Confidence-first, usually fast:** most items resolve with zero extra turns — Gate 1 ("is deciding the *what* the core deliverable?") and Gate 2 ("is the outcome genuinely contested?") get classified silently from the item text when unambiguous, citing the source. Only ask a blocking question (**`AskUserQuestion`**, per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts**) when a gate is genuinely unclear — one question covering both gates, not two separate turns.

**Two possible clean outcomes, not one:**
- **`lane: scope-led`** — STOP here. Report that this item needs product/PM-led scoping outside Forge before it can become a PRD. Do **not** proceed to `/intake` or `/forge` in the same turn.
- **`lane: build-led`** — assess Risk Tier (Standard vs High-risk — "could a wrong first pass corrupt durable, shared-state data that's expensive or impossible to unwind?"), write `lane-lock.md`, and report the item is ready for `/intake`.

<HARD-GATE>
Do NOT invoke `intake-interrogate` for this item without a `lane-lock.md` recording `lane: build-led`. Do NOT jump to `/intake` or `/council` in the same turn unless the user explicitly asks — this command's scope is triage through lock.
</HARD-GATE>

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation; **one blocking affordance per unrelated fork**; **`AskUserQuestion`** = short title + options only.

**Forge plugin scope:** Use skills and brain paths from **this** Forge repo only; brain root is **`~/forge/brain/`**.

**vs `/forge`:** **`/triage`** is a **partial** slice — the first one, running before `/intake`. Full E2E is **`/forge`** — see **`commands/forge.md`**, which now runs this classification as its own State 0 before Intake.

**Session style:** Prefer **planning-style**. See **`docs/platforms/session-modes-forge.md`**.

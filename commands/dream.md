---
name: dream
description: "Partial slice — dreamer retrospective or inline conflict resolution per dream-retrospect-post-pr / dream-resolve-inline; writes learnings to brain."
---

Invoke the **dreamer** agent (or equivalent skills **`dream-retrospect-post-pr`**, **`dream-resolve-inline`**) as appropriate:

- **Post-ship retrospective:** After merges / feature complete — score decisions, extract patterns and gotchas into **`~/forge/brain/`**.
- **Inline during work:** When council or eval surfaces unresolved cross-service conflict — counterfactual / resolution path per **`dream-resolve-inline`**.

<HARD-GATE>
Do NOT use retrospective mode to **waive** **`forge-eval-gate`** or merge on **RED** eval — dreamer resolves **conflicts**, not quality gates.
</HARD-GATE>

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** (**`using-forge`** **Horizon narration**) — in dialogue, only the **immediate** next prerequisite unless the user asks what comes later or the current step truly depends on a downstream artifact.

**Forge plugin scope:** Agent definition **`agents/`** + skills **`dream-*`** in this repo; brain under **`~/forge/brain/`**.

**vs `/forge`:** **`/dream`** is often the **tail** of a full **`/forge`** run but can be invoked alone after delivery. Full pipeline ordering: **`conductor-orchestrate`** / **`commands/forge.md`**.

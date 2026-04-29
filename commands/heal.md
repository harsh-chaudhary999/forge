---
name: heal
description: "Partial slice — self-heal after eval RED: locate fault, triage, fix, verify (max 3 loops). Invoke self-heal-locate-fault then triage/debug skills per conductor."
---

Invoke **`self-heal-locate-fault`** to begin the **self-heal** loop after a failed **`/eval`** (or equivalent **`forge-eval-gate`** outcome).

Pipeline: **locate** failing service → **triage** (flaky test, bad test, real bug, environment) per **`self-heal-triage`** → **systematic debug** (**`self-heal-systematic-debug`**) → **fix** → **re-verify** (re-run eval). Cap: **3** attempts per **`self-heal-loop-cap`**; then **escalate** to the human with evidence.

<HARD-GATE>
Do NOT silently drop failing eval scenarios — after three failed heal loops, **STOP** and escalate; do not merge or declare success.
</HARD-GATE>

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** (**`using-forge`** **Horizon narration**) — in dialogue, only the **immediate** next prerequisite unless the user asks what comes later or the current step truly depends on a downstream artifact.

**Forge plugin scope:** Skills under **`skills/self-heal-*`**; evidence in brain and repo worktrees.

**vs `/forge`:** **`/heal`** is a **reactive** slice after eval. Full E2E including eval green path and PR set: **`commands/forge.md`** (`/forge`).

**Session style:** Prefer **execution-style**. See **`docs/platforms/session-modes-forge.md`**.

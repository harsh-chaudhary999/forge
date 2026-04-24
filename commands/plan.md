---
name: plan
description: "Partial slice — per-repo tech plans only. Invoke tech-plan-write-per-project from frozen shared-dev-spec. Does not run full E2E or QA CSV by itself (use /forge for mandatory QA+eval path on full runs)."
---

Invoke the **`tech-plan-write-per-project`** skill to author **per-repository tech plans** only.

**Default depth (MUST):** In the **same** `/plan` session, complete **silent exploration** (product repo **`Read`/`rg`**, brain **`codebase/`**, **`### 1b.2a`**, maximal **Section 1b** bodies) **without** asking the user “should I explore further?” — that is **not** optional depth. Only pause for **Section 0.1** / **Section 0.2** **judgment** questions in chat. If the model would otherwise stop at a short outline, **continue** until the write skill’s gates are met or **`BLOCKED`** with owner.

**Brevity split (MUST):** **Short** = **Section 0** + **chat** only. **Section 1b**, **`### 1b.2a`**, **Section 2** = **as verbose as completeness requires** — see **`tech-plan-write-per-project` Section 0.0**; do not compress elaboration for “readability.”

This requires a **locked shared dev spec** from council. If **`shared-dev-spec.md`** is not locked for the task, direct the user to run **`/council`** first.

**Interactive planning (MUST):** **Do not** add **Section 0** table rows **with answers** until numbered questions have been asked and resolved **in this chat** (**`tech-plan-write-per-project` Section 0.1** hard ordering). **Ask numbered questions in chat first**; after replies **in chat**, write the **Section 0 outcome table** (short **Question** topic lines + **`USER:`** / role / spec / **BLOCKED** / **WAIVER** answers — **not** pasted chat logs in the repo). Follow **Section 0.1** rule 3–4 — no **`Frozen spec:`** + **H** for judgment without **`USER:`**. Follow **Section 0.2 Interactive contract rounds** — do **not** paste a finished Section 2 task list first and add **persistence / search / API / events** questions later. Work in **rounds** with the user **only for surfaces this repo owns** (**synchronous API** — REST / GraphQL / SOAP / gRPC per lock → **persistence (whatever engine the contract names)** → **search (if any)** → **brokers + cache** **when applicable** per spec + repo); **skip** rounds that are **N/A** for this file (document the one-line N/A in Section 1b — no scavenger hunt for SQL migrations or index templates in a frontend-only plan). **Short messages + explicit questions**, then update Section 0 and **Section 1b** (incl. **Section 1b.0 PRD↔scan matrix**, then **1b.1** / **1b.1a** / **1b.5** each as **full detail or explicit N/A**) before expanding Section 2.

**Maximal detail (MUST), applicability-first:** Every **PRD** and **shared-dev-spec** case that touches **this** repo must land in **Section 1b.0** with **scan paths** and **task ids** (or **`N/A (other repo: …)`**). Where this repo owns persistence, search, **synchronous APIs**, or **message/cache** contracts, schemas and wire examples must be **concrete** in the **contract’s** language (no `TBD` when the contract is already locked). Default to **over-specification inside frozen contracts for applicable surfaces only** — not “always one SQL database + one Lucene-style index + REST-only.”

**Touchpoints & boundaries (MUST):** After **Section 1b.5** and **`#### 1b.5b`**, complete **`### 1b.2a`** — **full exploration mode** per **`tech-plan-write-per-project`**. Shallow **`### 1b.2a`** fails **`tech-plan-self-review`**. Cohort / adjacency / **`discovery-adjacency.md`**: **`docs/adjacency-and-cohorts.md`** + **`tech-plan-write-per-project` Section 0.1** rule 6.

Each plan: bite-sized tasks (exact files, complete code where the skill requires it, exact commands), aligned to **`shared-dev-spec.md`**. Follow **`spec-freeze`** if the conductor phase is post-freeze.

<HARD-GATE>
Do NOT dispatch **`dev-implementer`** or open **Phase 4.1** from this command alone — tech plans are inputs to **State 4b** (QA CSV, eval YAML, RED) and then build. Per **`conductor-orchestrate`**, feature dispatch requires **`[P4.0-EVAL-YAML]`** and policy-complete **State 4b**.
</HARD-GATE>

**Forge plugin scope:** Plans live under the task’s brain path; skills from **`skills/`**.

**vs `/forge`:** **`/plan`** is a **partial** slice. Full E2E including mandatory manual QA CSV on the **`/forge`** entrypoint: **`commands/forge.md`**.

**Session style:** Prefer **planning-style** while authoring or **reviewing** tech plans; switch to **execution-style** for **`/build`**. See **`docs/platforms/session-modes-forge.md`**.

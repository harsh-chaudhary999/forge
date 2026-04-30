---
name: tech-plan-write-per-project
description: "WHEN: Shared-dev-spec is frozen and per-project tech plans must be written before dev-implementer dispatch. Output: 1 maximal plan per repo with Section 1b detail, 1b.2a exploration, and Section 2 tasks fully elaborated."
type: rigid
requires: [brain-read]
version: 1.0.3
preamble-tier: 3
triggers:
  - "write tech plan"
  - "create implementation plan per repo"
  - "plan for each project"
allowed-tools:
  - Bash
  - Write
---

# tech-plan-write-per-project

## Human input (all hosts)

**Judgment rounds** (**Section 0.1** / **Section 0.2**) run **in chat** — the plan file summarizes outcomes, not a substitute for dialogue. Follow **`skills/using-forge/SKILL.md`** **Multi-question elicitation**: **transcript-visible** questions, **one coherent topic per message** when multiple decisions remain, **blocking interactive prompts** / **numbered options + stop** for discrete forks (**Cursor** **`AskQuestion`** maps canonical **`AskUserQuestion`**). Do **not** paste the whole interactive workshop into Section 0 as if the human answered inside the markdown (**Anti-Pattern** rows below).

**Cross-cutting assistant dialogue:** **`docs/forge-one-step-horizon.md`** — **`using-forge`** **Multi-question elicitation** items **4–8**.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "The implementer will figure out the details" | Vague tasks cause divergence. "Add the endpoint" is not a task — "Add POST /api/v1/orders to routes/orders.ts returning 201 with OrderResponse schema" is a task. |
| "I'll use pseudocode to keep the plan concise" | Pseudocode forces the implementer to make design decisions that should have been made in planning. Write complete code. |
| "The skill says *brief* / *concise* / *compact*, so I'll keep Section 1b and Section 2 short" | **Misread.** Those words apply to **Section 0 topic labels**, **chat messages**, and **prescribed one-line N/A** — **not** to **Section 1b** tables, fenced payloads, **`### 1b.2a`** evidence, or **Section 2**. Thin Section 1b is **incomplete**, not disciplined. |
| "This task is too small to write out" | If it takes 2 minutes to execute, it takes 30 seconds to write. Small tasks that are written out get done correctly. Small tasks left vague get done wrong. |
| "I'll group related changes into one big task" | Tasks over 5 minutes need splitting. Big tasks hide complexity and make progress tracking impossible. |
| "The bash commands are obvious" | "Obviously" wrong commands waste a self-heal loop iteration. Write the exact command including flags, paths, and environment variables. |
| "I'll reference the spec instead of repeating details" | The implementer (dev-implementer subagent) works in an isolated worktree with only the plan. Self-contained tasks prevent NEEDS_CONTEXT status. |
| "I'll approximate inventory scale (~60+ files / many services) to sound thorough" | **BLOCKED.** Plans need **what / where / how**: repo-relative **paths**, entrypoints, **how** each row was verified (`rg`/`Read`/scan path), not headline counts. **Enumerate** services/files/slices the implementer must touch, or cite **`codebase/`** + product paths per row. |
| "Source / export is huge — I'll skip deep reads or partial Section 1b" | **BLOCKED.** Line count and export volume are **not** discretionary relief. **AGENTS.md** Core rule **6** — batch reads, complete the skill’s required depth, or **BLOCKED** with evidence. |
| "I'll discover file paths by exploring the repo" | Duplicates work the scan already did and burns tokens. **Default:** read `~/forge/brain/products/<slug>/codebase/` first; put paths from `index.md` / `modules/*.md` / `api-surface.md` into tasks, then open sources when writing full file bodies. **Exception:** **Section 1b.6** lists an **UNKNOWN** — you **must** deepen discovery (targeted `rg`/glob, read hub files, route tables, OpenAPI, client wrappers, test names) until resolved or **BLOCKED** — do not ship “mystery meat” tasks. |
| "Elaboration is optional — bite-sized tasks are enough" | Tasks without **Section 1b.0**, **Section 1b.5** (**synchronous API** — REST / GraphQL / SOAP / … per lock) + **`#### 1b.5b`** when **events/cache** apply, **Section 1b.1 / 1b.1a** when **persistence or search** applies, **Section 1b.6 unknown closure**, and **Section 1c review rounds** hide integration risk. STOP. Elaboration is **mandatory** for E2E; micro-tasks execute the elaboration, they do not replace it. |
| "I've hit my question quota — ship the plan with lingering doubts" | **There is no maximum question count** during planning. Doubt left unasked becomes a gap in Section 2. STOP. Ask until **confidence is high** (see **Section 0**), then write the elaborative plan. |
| "Concise plan = professional" | **Professional** here means **complete**: the plan is the **only** input to sub-tasks. Concision that omits wiring, edge cases, or evidence is negligence. |
| "I'll cover PRD cases implicitly in tasks" | **Every** success criterion, edge case, and non-functional requirement from **`prd-locked.md`** + **`shared-dev-spec.md`** must appear in **Section 1b.0** and map to Section 1b subsections or Section 2 tasks. Implicit coverage is invisible to review and ships gaps. |
| "Mechanics without intent — tables and tasks have no **why** or **PRD trace**" | **BLOCKED.** Every **Section 1b.0** row needs a **Why (rationale)**; every **Section 2** task needs **`Traces to:`** + **`Rationale:`**; API / design / message rows must say **which PRD or acceptance obligation** they satisfy. Otherwise reviewers cannot tell *purpose* from *shape*. |
| "Schema / payload details can wait for implementation" | **Forbidden** when that subsection **applies** to this repo. **Section 1b.1** / **1b.5** / **1b.1a** must carry **concrete** persistence shapes (SQL DDL, Mongo validators/index specs, ClickHouse `CREATE`/mutation, … per contract), search/index definitions, or **API request/response/error** shapes (JSON, XML for SOAP, GraphQL operation + variables schema, … per lock) — or **verbatim** locked-contract excerpts — never `TBD` where the contract already decided them. **Corollary:** If this repo **does not** own persistence, search, or **that** API surface, a **one-line `N/A` + spec citation** (and sibling repo if needed) **is** the required elaboration — not empty tables and not invented schema. |
| "Every good plan has migrations and index mappings" | **Stack bias.** Many tasks are **UI-only**, **docs-only**, **config-only**, or **consumer-only**. Forcing relational-DDL + Elasticsearch-style sections when the product uses **Mongo**, **ClickHouse**, **BigQuery**, **Typesense**, etc. — or **none** in this repo — drives fake work or endless discovery. **Derive applicability** from the frozen spec + this repo’s role; elaborate **maximally** only on surfaces **in play**, in the **contract’s** schema language. |
| "Scan is optional if I know the repo" | The brain **`codebase/`** is the default authority for *where* code lives. Skipping **`index.md`**, relevant **`modules/*.md`**, **`api-surface.md`**, and route/OpenAPI stubs before writing tasks is **BLOCKED** unless **`SCAN_INCOMPLETE`** / **`BLOCKED`** is explicitly recorded with owner. |
| "Touchpoint table is boilerplate — I'll mark N/A for everything" | **`### 1b.2a`** is **full exploration**, not a formality. Every **Y** / **PARTIAL** needs **paths + tools + behavior delta**. Bulk N/A without opening the product repo is **BLOCKED** at self-review. |
| "I'll put the whole ‘interactive’ dialogue in Section 0 and ship" | **Wrong split.** The **human answers in chat**; Section 0 only **summarizes decisions** (short **Question** topic + **`USER:`** / **`TL:`** / verbatim-spec **Answer**). Nobody should answer planning questions **inside** the markdown file or paste walls of chat back into it — that defeats the point of an LLM-assisted **interactive** session. Rows with **`Frozen spec:`** + **H** for judgment without **`USER:`** are still **SPEC_ROLEPLAY**. |
| "I'll make the human review the plan file like a form" | **BLOCKED UX.** Rounds are **in chat**; the file is for **implementers** (outcomes + Section 1b + tasks). Do not require humans to “fill in” the plan as the primary Q&A surface. |
| "I'll wait for the user to say explore deeper / touchpoints / full plan" | **BLOCKED.** **`### 1b.2a`**, **Section 1b.6** deep discovery, and **maximal Section 1b** elaboration are **default** — run **`Read` / `rg` / glob** on the **product repo** + brain **`codebase/`** until evidence exists or **`BLOCKED`**. **Do not** ask “should I continue exploring?” **Judgment** (ownership, product tradeoff, waiver) pauses **only** for **Section 0.1** chat rounds — not for mechanical discovery. |
| "`REVIEW_PASS` without pasting FORGE-GATE markers" | **BLOCKED** for any pipeline that runs **`verify_forge_task.py --strict-tech-plans`**. Self-review inventory + recross must sit **in Section 1c** with the two **`<!-- FORGE-GATE:… -->`** lines — see **Section 1c** item **2b**. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
EVERY TASK IN A TECH PLAN IS SELF-CONTAINED, COMPLETE, AND EXECUTABLE IN ISOLATION. NO PLACEHOLDERS. NO PSEUDOCODE. NO "SEE SPEC" REFERENCES. THE PLAN IS THE ONLY THING THE DEV-IMPLEMENTER READS.
```

**Default execution posture (MUST — no follow-up prompt required):**

1. **Silent exploration first** — Before treating a plan as “draft complete,” run **full exploration mode**: brain scan + targeted **`rg` / `Read`** on the product repo until **`### 1b.2a`** has **non-empty Evidence** for every **Y** / **PARTIAL** row (or **`BLOCKED`**), **Section 1b.6** has no lazy **UNRESOLVED** where tools could answer, and **Section 1b.1** / **Section 1b.5** / **`#### 1b.5b`** carry **concrete** shapes where applicable. **Forbidden:** shipping a thin outline and expecting the user to prompt again for “touchpoints” or “full exploration.”
2. **Chat only for judgment** — Use **Section 0.1** / **Section 0.2** for **human** decisions (product owner, TL, contract confirm). **Do not** use chat to get permission to open files or run grep.

**Normative claims (companion rule):** Every **interface** claim in a task (path, field name, status code, topic name, column) must be **copied from** the **frozen** `shared-dev-spec.md` or the task-local inlined excerpt of **`contracts/*`** — **not invented** in the tech plan. If `shared-dev-spec` was thinner than reality, **fix the spec** (change request / re-council) — do not “paper over” in tasks. **Program / rollout / sequencing** lives in **`~/forge/brain/prds/<task-id>/delivery-plan.md`** (non-frozen); tech plans may **reference** it by heading but **must not** rely on it for interface truth.

**Product terminology (`terminology.md`):** When **`~/forge/brain/prds/<task-id>/terminology.md`** exists, treat it as the **per-task** product term sheet (distinct from the Forge plugin glossary — [forge-glossary](../forge-glossary/SKILL.md)). **Read** it before writing user-facing strings, error messages, or marketing-adjacent labels in **Section 1b** / **Section 2**; align renames with **`open_doubts`** resolution and [docs/terminology-review.md](../../docs/terminology-review.md). If the file is **absent** and the PRD introduces **named product concepts** or **branded labels**, follow **intake-interrogate** to create it or record **N/A** with **WAIVER** in **Section 0** when the task policy allows (see terminology-review **slice** table).

**Optional PM traceability (inside each `tech-plans/<repo>.md`):** You may group Section 2 tasks under IDs like **`REVERIF-<AREA>-<nn>`** with columns **Est / Deps / Acceptance / Spec refs** (link to `shared-dev-spec` heading or `contracts/` heading). This does **not** replace one-file-per-repo or self-contained task bodies.

## Quick-Reference Index

Cross-map between Anti-Pattern rows and Red Flags so you don't have to read both lists to find the relevant rule.

| Concern | Anti-Pattern row | Red Flag |
|---------|-----------------|----------|
| Completeness scope (brief vs maximal) | "The skill says *brief*…" | "Plan has no Section 0 / 1b / 1c" |
| PRD traceability | "I'll cover PRD cases implicitly" | "Section 1b.0 missing, empty, or has PRD/spec rows without Section 2 task ids" |
| Intent / why columns | "Mechanics without intent…" | "Missing product intent trace" |
| Schema / wire shapes | "Schema / payload details can wait" | "Section 1b.1 / Section 1b.5 / Section 1b.1a use vague language" |
| Async contracts | *(see Red Flags)* | "Async contracts missing" |
| Touchpoint exploration | "Touchpoint table is boilerplate…" | "`### 1b.2a` missing, shallow, or misplaced" |
| Interactive vs form UX | "I'll put the whole dialogue in Section 0" / "I'll make the human review the plan file" | "Section 0 fake interactive" / "Section 0 cohorts via `SPEC_INFERENCE`" |
| Scan authority | "Scan is optional if I know the repo" | *(see Overview — SCAN_INCOMPLETE failsafe)* |
| Review gate | "`REVIEW_PASS` without FORGE-GATE markers" | "`Tech plan status: REVIEW_PASS` with no self-review round" |
| Phantom backend work | "Every good plan has migrations and index mappings" | "Section 2 tasks exist before applicable Section 0.2 work is done" |

Jump to: [Anti-Pattern Preamble](#anti-pattern-preamble) · [Iron Law](#iron-law) · [Red Flags](#red-flags--stop) · [Section 0](#section-0-planning-doubt-clearance-before-section-1b-and-section-2) · [Section 1b](#section-1b-elaborative-preamble-mandatory-per-tech-plan-file) · [Section 2](#section-2-bite-sized-task-breakdown) · [Checklist](#checklist)

---

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Task contains "add the endpoint" or other vague verbs without file paths** — Vague tasks produce vague implementations. STOP. Rewrite with exact file path, function name, and complete code.
- **Inventory or coverage is described with headline counts, "N+", or "many" instead of named paths and verification** — STOP. **AGENTS.md** — *Written artifacts — precision* (**what / where / how**). Tables and bullets must cite **`codebase/`** or repo paths and **how** each row was confirmed (`rg`/`Read`/scan artifact); implementers cannot act on scale alone.
- **Large PRD, Confluence export, or `prd-source-confluence.md` is treated as “too big” to read end-to-end or to mirror into Section 0c / 1b** — STOP. **AGENTS.md** Core rule **6** — chunk reads, complete traceability work, or **BLOCKED** with a concrete tool limit — never self‑authorized truncation.
- **A task exceeds 5 minutes of execution** — Tasks over 5 minutes hide complexity and block progress tracking. STOP. Split into smaller tasks, each 2-5 minutes.
- **Plan has no Section 0 / 1b / 1c** — Missing **doubt log** table (outcome rows), **Section 1b.0 PRD coverage matrix**, **`### 1b.0b` implementation at-a-glance** (surface table + cross-repo deps + prose summary), **Section 1b.1–1b.6** (each with either **delta content** or the skill’s **explicit one-line N/A** where not applicable), **`#### 1b.5b`** when **round D** applies (or its one-line N/A), **`### 1b.2a` touchpoint & boundary inventory** (full exploration table + **Exploration notes**), or **Section 1c**. Micro-tasks without inventory and without cleared doubts hide gaps. STOP. Add **Section 0** (incl. **Section 0.2** rounds **that apply**) then **Section 1b.0** → **Section 1b.0b** → … → **`### 1b.2a`** → **`### 1b.6`** before Task 1.
- **Migration or schema-change tasks exist but the data model delta table is empty or claims “none”** — Contradiction with locked **contract-schema-db** / persistence contract. STOP. Align the table and tasks.
- **Plan references the shared-dev-spec with "see spec" instead of repeating the details** — Dev-implementer works in isolation without spec access. STOP. Make every task fully self-contained with all needed details inline.
- **Bash commands lack flags, paths, or environment variables** — Incomplete commands produce incorrect results or fail silently. STOP. Write the exact, complete command.
- **Tech plan is written before shared-dev-spec is frozen** — Plans written against an unlocked spec will drift. STOP. Confirm spec-freeze before writing any tech plan.
- **Multiple repos share a single tech plan** — One plan per repo. Cross-repo plans create cross-task dependencies that block independent dispatch. STOP. Write one plan per repo.
- **Test task is listed after implementation task** — TDD requires test first. STOP. Reorder: test task always precedes the implementation task it covers.
- **Web or app tech plan skips Section 1b.4 or omits design anchors while intake locked Figma / `design_brain_paths` / Lovable repo** — Figma captured in Q9 is **not** decorative; it must drive the component/screen plan. STOP. Add the design→UI table and align tasks to nodes or brain paths.
- **UI tasks cite neither a design anchor nor `design_waiver: prd_only` + scan reuse** — Implementers cannot verify pixels or reuse. STOP.
- **API-consuming plan has no Section 1b.5 consumer map** — No way to verify which component calls which **operation** (REST `METHOD+path`, GraphQL operation, SOAP action, …). STOP.
- **API-serving backend plan has no Section 1b.5 owner rows** for new/changed **operations** — Consumers cannot be aligned. STOP.
- **Section 1b.6 lists UNRESOLVED unknowns but Section 2 still has executable tasks depending on them** — Discovery incomplete. STOP. Resolve, escalate **BLOCKED**, or remove tasks until evidence exists.
- **`Tech plan status: REVIEW_PASS` with no `tech-plan-self-review` round logged in Section 1c revision log** — Rubber-stamp. STOP.
- **State 4b or implementation started without `tech-plans/HUMAN_SIGNOFF.md` + `[TECH-PLAN-HUMAN]`** — Human feedback phase skipped. STOP.
- **Section 0 doubt log has open items** (unanswered questions, `UNCONFIRMED` rows) but Section 2 tasks are already written — Planning was short-circuited. STOP. Resolve or **BLOCK** before tasks.
- **Section 0 “fake interactive”** — Rows resolve **ownership / schedule / who publishes** with only **`Frozen spec:`** paraphrase and **Confidence H** but **no** **`USER:`** / **`PO:`** / **`TL:`** prefix and **no** verbatim single-paragraph quote (**Section 0.1** rule 3). That is **SPEC_ROLEPLAY**, not cleared doubt. STOP. Re-ask in chat or downgrade to **M** + **`SPEC_INFERENCE`**.
- **Section 0 cohorts via `SPEC_INFERENCE`** — Product segmentation, eligibility, or batch exclusions locked with **`SPEC_INFERENCE`** / **H** without **`USER:`** / **`PO:`** / **`TL:`** or brain **`touchpoints/COHORT-AND-ADJACENCY.md`**. STOP. **`REVIEW_PASS`** forbidden until fixed (**Section 0.1** rule 6).
- **Async contracts missing** — Locked spec or **`contract-event-bus`** names **topics / queues / exchanges / JMS destinations / partitions** this repo **produces or consumes**, but **`#### 1b.5b`** is absent, **N/A without citation**, or **prose-only** (no fenced payload in the **contract’s format** — JSON, XML, Protobuf text, … — or verbatim contract). STOP. **Section 1b.5** synchronous **N/A** does not remove the obligation to document messages/cache when in scope.
- **Section 2 tasks exist before applicable Section 0.2 work is done** — For every surface **in play** for this repo (**synchronous API** serve/consume, persistence, search, cache/events per spec), either **Section 0.2** alignment with the user **or** logged **BLOCKED** / **N/A + citation** is recorded **before** tasks. **Skip** Section 0.2 rounds that do not apply (e.g. no **B** when Section 1b.1 is N/A). STOP if tasks assume contracts you never confirmed. **Also STOP:** Phantom backend work — Section 1b.1 / **1b.1a** filled with speculative persistence or search definitions when the frozen spec assigns those to **another repo** or explicitly excludes them here.
- **Section 1b.0 missing, empty, or has PRD/spec rows without Section 2 task ids** — A requirement or acceptance path is untracked. STOP. Add rows or tasks until **bidirectional** coverage (no orphan rows, no orphan tasks for in-scope work).
- **Section 1b.1 / Section 1b.5 / Section 1b.1a use vague language** (no field names, types, keys, partitions, TTLs, or error shapes) **where that subsection applies** and the spec already decided them — Implementers will invent. STOP. Inline **store-native** schema / index-definition / **API wire examples** (JSON, XML, GraphQL snippets, …) or verbatim contract text. **Not a red flag:** Prescribed **one-line N/A** when this repo does not own that surface.
- **Missing product intent trace** — **Section 1b.0** rows lack **Why (rationale)**; or **Section 1b.3** bullets lack **`Why:`** clause; or **Section 1b.4** / **Section 1b.5** / **`#### 1b.5b`** tables omit **PRD / rationale** where the skill prescribes them; or any **Section 2** task omits **`Traces to:`** or **`Rationale:`** — STOP. Add intent lines until every change is tied to **`prd-locked.md`** / spec / contract obligation.
- **`### 1b.2a` missing, shallow, or misplaced** — No touchpoint inventory; table rows with **empty Evidence** / **no repo paths** for **Y** categories; **Exploration notes** missing or generic (“looked at repo”); or **`### 1b.2a`** appears **before** **Section 1b.5** / **`#### 1b.5b`** (cannot cite concrete ops/topics) — STOP. Run **full exploration mode** per **`### 1b.2a`**.
- **`### 1b.2b` missing when gate applies** — Elaborative work (multi-file net-new, **≥3** integrations, or multiple **PARTIAL** touchpoints) but no **first-session reconnaissance** (git block, **≥5** minimum reads, **≥2** discovery commands) — STOP. Brain scan alone is not a work order.

## Overview

This skill converts a locked shared-dev-spec into bite-sized, executable technical implementation plans per project. Each task is 2-5 minutes of execution with exact file paths, complete code (no placeholders), and exact bash commands.

**Primary audience:** A human or agent who **does not** already know the product repos. The plan must stand alone: **brain scan** supplies *where things live today*; **locked intake design** (`prd-locked.md` and the **Design source (from intake)** section in **shared-dev-spec**) supplies *what net-new UI should match* (Figma nodes, `design_brain_paths`, Lovable GitHub tree, or an explicit waiver). **Taking Figma in intake but omitting it from the tech plan** is the same class of failure as skipping migrations — implementers will invent components and ship visual bugs.

**Order of operations for paths:** Before naming files in tasks, load **`~/forge/brain/products/<slug>/codebase/`** (at least `index.md`, `SCAN.json`, and the `modules/*.md` files that match the spec’s surfaces). **Failsafe:** if `SCAN.json` exists, run **`python3 tools/verify_scan_outputs.py <that/codebase>`** (up to **3** tries, **1s** backoff). On persistent failure, prefix the plan with **`SCAN_INCOMPLETE`** and **do not** treat brain paths as authoritative until `/scan` passes verify — deepen with targeted `rg`/reads or **BLOCKED** per Section 1b.6. Derive **exact repo-relative paths** from verified brain material, then read the product repo only to pull current file contents for “complete code” blocks. If scan is missing or >7 days old, note it and align with `product-context-load` / user on **`/scan <slug>`** before finalizing paths.

**Order of operations for UI:** When this repo is **web** or **app**, read **Design source (from intake)** in the locked spec **and** any **`~/forge/brain/prds/<task-id>/design/`** ingest notes (`MCP_INGEST.md`, `README.md`, …). Complete **Section 1b.4** before writing UI tasks so every screen/component change is tied to **design anchors** and/or **scan-backed** reuse paths — not to memory of a Figma URL from chat.

**Elaboration bar (default = maximal where applicable):** Tech plans are **exhaustive by default** for **surfaces this repo owns**, not minimal. **Every** PRD success path, edge case, failure mode, and non-functional requirement (latency, security, audit, rollback) that touches this repo must be **visible** in **Section 1b.0** + Section 1b tables + **`### 1b.2a` touchpoints** + Section 2 — if it is only in the planner’s head, the plan is **incomplete**. Prefer **over-specifying** (field names, types, indexes, status codes, idempotency keys) within the **frozen** contracts for **those** surfaces over leaving "reasonable defaults" to the implementer. Surfaces **not** owned here get **explicit N/A**, not filler. If the frozen spec is silent on a detail, record **Section 1b.6** unknown or **Section 0** question — do not silently invent.

---

## Section 0: Planning doubt clearance (before Section 1b and Section 2)

**Purpose:** Sub-tasks inherit every gap you skip while “planning.” This section **forces** questions until doubt is low — **no artificial cap** on how many you ask.

### 0.0 Brevity vs elaboration (normative — read before Section 0.1)

- **Words like *brief*, *concise*, *compact*, *short*, *one-line*** in this skill refer **only** to: **(a)** **Chat** prompts to the human (numbered, tight), **(b)** **Section 0** *Question* cells (one topic line each) and *Answer* outcomes (one-line **`USER:`** / role / spec / **WAIVER**), **(c)** **Explicit one-line `N/A`** for a Section 1b subsection this repo does **not** own. They **do not** mean the overall tech plan should be short.
- **Section 1b.0**, **Section 1b.0b** narrative, **Section 1b.1** / **1b.1a** / **1b.5** / **`#### 1b.5b`** bodies, **`### 1b.2a`** (including **Exploration notes**), **Section 1b.3**, **Section 1b.6**, and **Section 2** must be **as long as required for completeness** — **maximal** where this repo owns the surface (**Elaboration bar** above). **Forbidden:** Trimming tables, skipping fenced examples, or thinning **1b.2a** to “look professional.”

### 0.1 Rules

1. **Ask freely:** Raise **every** ambiguity (ownership, edge case, failure mode, idempotency, auth, rollout, test data, environment flag, naming, which repo owns what). Prefer **over-asking** to under-asking. There is **no** “max questions per task” in Forge.
2. **Answer channels:** Product owner, tech lead, **`delivery-plan.md`**, **`parity/`** material, brain scan, another repo’s plan draft, or **explicit `BLOCKED`** with who must answer — all valid. Chat history alone is **not** durable; **write outcomes** into this plan or `~/forge/brain/prds/<task-id>/planning-doubts.md` (optional file) and **summarize** in **Section 1b.6** when they affect code paths.
3. **Interactive session in chat; Section 0 = outcomes only (MUST):** **Do not** use the markdown plan as the primary place to **pose** planning questions or to collect human answers. **Ask in chat** (short, numbered), **wait** for replies (or explicit in-chat delegate / waiver from **`PO:`** / **`TL:`**). **Then** append rows to Section 0 that record **what was decided** — not a transcript of the whole thread. **Hard ordering:** Do **not** add **Section 0** rows with **answers** until the corresponding topic has been **resolved in this chat session**. Do **not** add rows whose **Answer** pretends a human spoke when only the spec was read (see **Red flags** — **Section 0 “fake interactive”** / **SPEC_ROLEPLAY**). **Question** column: **one short line** naming the topic (e.g. “Who owns cron vs MQ for schedule?”) — **not** multi-paragraph copy-paste from chat or from the file as a fake “questionnaire.” **Answer** column: **`USER:`** / **`PO:`** / **`TL:`** + one-line outcome, **or** verbatim spec quote + path for non-judgment facts, **`BLOCKED`**, or **`WAIVER`**. **Confidence H** on judgment rows requires **`USER:`** / role prefix **or** verbatim spec — else **M** + **`SPEC_INFERENCE`**. **Forbidden:** Asking the human to “answer in the plan file” or requiring **verbatim paste of chat into the repo** — the value of the LLM is **running the interactive round in the session**; the file is the **durable decision record** for implementers.
4. **Start the elaborative plan only when:** You would stake implementation on it — i.e. no remaining **high-impact** unknowns without an owner, or they are recorded as **BLOCKED** / **WAIVER** with risk.
5. **Trace questions to coverage:** Each resolved doubt should visibly affect **Section 1b** tables or a specific Section 2 task — or be explicitly **out of scope** with spec citation.
6. **Product cohorts & segmentation (HARD — Section 0):** Any row that locks **who sees what**, **eligibility**, **regional or source-based behavior**, **trust / risk tier UX**, **batch inclusion/exclusion**, or **variant APIs** by **segment** must use **`USER:`** / **`PO:`** / **`TL:`** (or verbatim spec quote that explicitly encodes the segment rule) — **not** **`SPEC_INFERENCE`** with **Confidence H**. **`REVIEW_PASS` is forbidden** until **`touchpoints/COHORT-AND-ADJACENCY.md`** is USER-backed or waived (**`docs/adjacency-and-cohorts.md`**). **Optional:** If **`discovery-adjacency.md`** lists hits for a shared entity this PRD touches but **`### 1b.2a`** omits them → **CHANGES**.

### 0.2 Interactive contract rounds (MUST — live session behavior)

**Forbidden:** Dump a **full Section 2** task list first, then add “follow-up questions” for **persistence**, **search**, or **API** contracts in an appendix. That inverts risk: implementers see tasks without locked contracts.

**Required cadence with the human:** Work in **rounds** — each round ends with **explicit questions** and a **pause for answers** before the next contract surface is finalized in **Section 1b** and Section 0.

**Skip rounds that do not apply to this repo:** If **Section 1b.1** will be the one-line **no persistence** N/A, **do not** run round **B** as a “find migrations / collections / CH migrations” scavenger hunt — write the N/A ground (spec section / affected projects) and proceed. Same for **C** when **Section 1b.1a** is N/A, and **A** when **Section 1b.5** is fully N/A (**no** synchronous API server or client work for REST/GraphQL/SOAP/etc.). When **A** is partial (e.g. **consumer-only**), run **A** only for **client** contract alignment — not for persistence another repo owns.

| Round | When to run | Cover | Before proceeding |
|-------|-------------|-------|-------------------|
| **A — Synchronous API surface** | This repo **serves** or **consumes** a **locked** synchronous API for this task (**REST** over HTTP, **GraphQL**, **SOAP** / WSDL, **gRPC**, … — whatever **`shared-dev-spec`** + **`contract-api-*`** name) | **REST:** paths, methods, bodies, errors; **GraphQL:** operations, variables, errors; **SOAP:** operations, SOAPAction / QName, XML envelope samples or XSD refs; auth, versioning, idempotency | **Section 1b.5** draft owner + consumer rows + **fenced** payloads in the **contract’s wire format**; user confirms or **BLOCKED**. If **no** synchronous API surface: **skip** — **Section 1b.5** one-line N/A only. |
| **B — Persistence / durable store** | This repo **owns schema or migration work** for this task (any engine: relational SQL, **MongoDB**, **ClickHouse**, Dynamo, Redis persistence, … per **contract-schema-db**) | Collections/tables/partitions, indexes, TTL, nullability / sharding / backfill strategy as locked | **Section 1b.0** rows for persistence + **Section 1b.1** delta + **verbatim** or **fenced** schema in the **contract’s native language** per **Section 1b.1** rules; user confirms or **BLOCKED**. If **not** owning persistence: **skip** — **Section 1b.1** one-line N/A + sibling repo if applicable. |
| **C — Search / ranked retrieval** | This repo **owns** index, mapping, or ingest for this task (Elasticsearch, OpenSearch, Solr, Typesense, Meilisearch, vector DB index, … per **contract-search**) | Index or collection name, field definitions, analyzers / embedders, reindex or dual-write | **Section 1b.0** rows for search + **Section 1b.1a** + **fenced** definition (often JSON; use XML/YAML if that is what the contract locks) **or verbatim** contract per **Section 1b.1a** rules; user confirms or **BLOCKED**. If **not** in scope: **skip** — **Section 1b.1a** one-line N/A with spec citation. |
| **D — Cache / events** | Contracts or spec assign cache/event work **to this repo** | Key patterns, TTL, **destinations** (Kafka topic, RabbitMQ queue+exchange+routing key, JMS queue, …), ordering, idempotency, **payload keys** (**contract-cache** / **contract-event-bus**) | **`#### 1b.5b`** (below) filled with tables + **fenced** payload (JSON / XML / …) or verbatim contract per rules **or** one-line N/A with citation; Section 0 ties open questions here; **skip** round **D** only when both contracts are out of scope for this repo. |

**Chat style:** Prefer **short messages** with **numbered questions** **in chat** (not a megabyte of Q&A in the thread). After **chat** resolutions, **write** Section 0 as **compact outcome rows**, then **fully elaborate** **Section 1b** (including **Section 1b.0** synced to the latest PRD/spec rows) — **Section 1b** may be **long**; length is not a failure mode. Only then add/expand **Section 2** tasks so they inherit the locked shapes.

### 0.3 Artifact (required in each `tech-plans/<repo>.md` or linked file)

Include **before** `## Section 1b`:

```markdown
## Section 0: Planning doubt log

<!-- Optional one line: Planning rounds completed in chat (date) — rows below are outcomes for implementers, not the live Q&A transcript. -->

| Q# | Question (short topic — what was decided about) | Answer / resolution | Confidence (H/M/L) | Affects (Section 1b.x / Task ids) |
|----|---------------------------------------------------|----------------------|--------------------|----------------------------|
| Q1 | e.g. Schedule ownership (cron vs MQ)            | USER: …              | H                  | 1b.5b, T1–T4               |
```

- **Question** cells: **one line** topic labels — **not** full multi-part questionnaires (those stay **in chat**).
- Add rows until **high-impact** doubts are **H** or **M** with an owner, or **BLOCKED** / **WAIVER**.
- If zero open questions: one row stating **`No material doubts — ready to elaborate.`** (after confirming in chat per **Section 0.1** rule 3).
- **Reviewers:** If judgment-heavy **Answer** cells lack **`USER:`** / role / verbatim-spec discipline (**Section 0.1**), fail self-review. **Do not** require users or agents to paste entire chat logs into the repo.

---

## Section 1: Parse shared-dev-spec

### Input
- Locked spec location: `~/forge/brain/prds/<task-id>/shared-dev-spec.md` (or the task’s frozen spec path from `brain-read`)
- **`prd-locked.md`** at `~/forge/brain/prds/<task-id>/prd-locked.md` — success criteria, scope, design/Q10, and acceptance language (must be reflected in **Section 1b.0**)
- Status: LOCKED (spec is immutable at this stage)

### Process
1. **Read the spec file** to understand:
   - Feature requirements (functional + non-functional)
   - Success criteria and acceptance tests
   - Affected projects (which repos need changes)
   - Contracts and interfaces (API shapes, schema changes, event formats)

2. **Extract per-project work items** by identifying:
   - Database migrations (schema changes)
   - API endpoints (routes, handlers, validation)
   - Data models and business logic
   - Frontend components and views
   - Integration points and dependencies

3. **Map to repositories** (standard Forge topology):
   - `shared-schemas/` — Shared TypeScript types, validation schemas, contracts
   - `backend-api/` — Node/Express REST API, database migrations, business logic
   - `web-dashboard/` — React SPA, UI components, state management
   - `app-mobile/` — React Native app, mobile UI, offline-first patterns

### Output
- Structured list of per-project tasks (raw)
- Dependency graph (which project depends on which)
- Identified contracts (API, schema, events)

---

## Section 1b: Elaborative preamble (mandatory per tech-plan file)

**Authoring order in the saved `tech-plans/<repo>.md` file:** (1) `#` title line, then **`Tech plan status: DRAFT`** (or `REVIEW_CHANGES` / `REVIEW_PASS` per **Section 1c**); (2) **`## Section 0: Planning doubt log`** (outcome table after **chat** rounds; see **Section 0**, including **Section 0.2** interactive rounds **for applicable surfaces only**); (3) this **Section 1b** starting with **`### 1b.0`**, then **`### 1b.0b`**, then **`### 1b.1`** and **`### 1b.1a`** each as **either** the delta table **or** the skill’s **one-line N/A**, then **`### 1b.2`** (reuse vs net-new), **`### 1b.2b`** (first-session reconnaissance **or** one-line N/A per gate), **`### 1b.3`** (spec trace bullets), **`### 1b.4`** as applicable, **`### 1b.5`** (synchronous API **or** one-line N/A), **`#### 1b.5b`** (brokers + cache **or** one-line N/A) when **round A / D** or contracts apply, then **`### 1b.2a` touchpoint & boundary inventory** (**full exploration mode** — after wire maps so evidence cites real paths/operations), then **`### 1b.6`**); (4) **Section 1c** body (revision log table + cross-repo notes); (5) **Section 2** tasks.

**Surface applicability (generic — no stack bias):** Before deep-diving persistence, search, **synchronous APIs**, or **message brokers**, decide **what this repo actually owns** for this task using **`shared-dev-spec.md`** (affected projects / ownership), **`prd-locked.md`**, and **`~/forge/brain/products/<slug>/codebase/`** (e.g. SQL migrations, ORM models, **Mongo** migrations/validators, **ClickHouse** `.sql` / `ALTER`, **Kafka**/AMQP client usage, ingest workers, `api-surface.md`, GraphQL schema folders, WSDL paths, client modules). **Maximal detail** applies **per applicable surface** — not “always one RDBMS + one Lucene-derived search + REST-only.” **Complete** means: every in-scope case is in **Section 1b.0**, and every Section 1b subsection is either **fully elaborated** (tables + fenced blocks in the **contract’s** language — SQL, JSON, YAML, XML, **SOAP**, SDL, `.proto`, …) **or** an **explicit one-line `N/A` + spec citation** (and optional **`N/A (other repo: tech-plans/<file>.md)`** pointer). **Forbidden:** (a) leaving Section 1b.1 / **1b.1a** / **1b.5** / **`#### 1b.5b`** blank without the prescribed N/A line; (b) **inventing** persistence schema, search definitions, **operations**, or **destinations** for a **frontend-only** (or otherwise non-owning) repo; (c) **discovery loops** (hunting migrations or index templates for engines **this repo does not use**) when the frozen spec + topology already show **no ownership** here — record N/A and move on.

Bite-sized tasks exist so a **dev-implementer in isolation** can execute without guessing. They **do not** replace **Section 0** (cleared doubts + **Section 0.2** user rounds **where applicable**), nor **`### 1b.2b`** (ordered **git + minimum reads + discovery commands** when elaboration gate applies), nor **`### 1b.2a` touchpoint & boundary inventory** (**full exploration** — every integration surface enumerated with **evidence**, not vibes), nor a short, explicit narrative of **what changes in the world** for **this repo** (data, **search indices**, reuse, design, **synchronous API wiring** (REST/GraphQL/SOAP/gRPC/…), **broker destinations & payloads**, **cache**, unknowns, review trail — **omit** subsections that are N/A, do not pad them). **Subsection 1b.4** follows web/app rules; **1b.5** follows the **locked API style** when this repo serves or consumes that surface; **`#### 1b.5b`** follows **contract-event-bus** / **contract-cache** when this repo touches those surfaces; **1b.1a** follows search when this repo owns index/mapping work; **1b.6** is always required (may be a single “no unknowns” line). **Section 1c** is always required. All of the above **before Section 2**.

Skipping them because “the tasks are obvious” or “only micro-steps matter” is **BLOCKED** — that is how schema drift, duplicate persistence shapes, wrong screens, **wrong API wiring**, and silent greenfield work slip through.

### 1b.0 PRD & acceptance coverage matrix (mandatory — no missed cases)

**Purpose:** Prove **every** in-scope requirement, success criterion, edge case, and non-functional constraint from **`prd-locked.md`** and **`shared-dev-spec.md`** is either implemented in this repo’s Section 2 or explicitly **out of scope** with a citation. **Scan** proves *where* work lands.

**Build this table before `### 1b.1`** (add rows until nothing material is missing):

| PRD / spec ref (id or heading) | Requirement or acceptance (one line) | **Why (rationale)** — what user/system outcome this row serves; what goes wrong if skipped (≠ restating the requirement cell) | Brain scan evidence (`codebase/...` path or `SCAN.json` note) | Owner Section 1b subsection(s) | Section 2 task id(s) or `N/A (other repo)` |
|-------------------------|----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------|-------------------------|---------------------------------------------|
| e.g. `prd Q5`, `spec FR-2` | e.g. "User can revoke session" | e.g. "Stops stale tokens after compromise; audit trail for SOC2" | e.g. `modules/web-auth-svc.md` → `src/auth/Revoke.ts` | 1b.2, 1b.5 | T12–T18 |

**Rules (MUST):**

1. **Bidirectional:** No row without **Section 1b** + **tasks** (or `N/A` + sibling repo file). No Section 2 task that does not tie back to a **row** or an explicit **tech-debt / chore** exception with human approval in Section 0.
2. **Edge & negative paths:** Include error handling, empty states, permission denied, rollback, idempotency retries — wherever the PRD or spec calls them out — as their own rows or explicit bullets under a single row’s "Requirement" cell.
3. **Non-functionals:** Performance budgets, SLOs, PII redaction, audit logging, feature flags — each gets a row or a **WAIVER** row pointing to **`prd-locked.md`** / spec text.
4. **Scan discipline:** For each row, the **evidence** column must cite **actual** `codebase/` paths (or `UNKNOWN` → **Section 1b.6** until resolved). Guessing paths without scan is **BLOCKED**.
5. **Cross-repo honesty:** A PRD row that needs **backend persistence schema** or **search ingest** but **this file** is e.g. `web-dashboard` must use **`N/A (other repo: …)`** in the task column and list **only** the Section 1b subsections **this** repo will touch (e.g. **1b.4**, **1b.5** consumer rows). Do **not** duplicate backend **Section 1b.1** / **1b.1a** bodies here — point at the owning plan file instead.
6. **Why column:** **Non-empty** for every row (except explicit **WAIVER** rows, where **Why** states risk accepted). **Forbidden:** copying the requirement cell into **Why**, or only writing “per PRD” / “spec says so” with no product consequence.

**PRD trace gate (MUST — before the matrix is “done”):** Read **`prd-locked.md`** end-to-end for this task. **Every** material bullet under scope, **success criteria**, **acceptance** / test language, **NFRs**, and **edge / negative** cases must land as a **Section 1b.0** row (or a row pointing at **`shared-dev-spec.md`** / contract text that carries the same obligation), **or** as an explicit **WAIVER** row with citation. **Silent omission** of PRD language is **BLOCKED** at **`tech-plan-self-review`** — the matrix is not a summary of “main flows” only.

### 1b.0b Implementation at-a-glance (MUST)

**Purpose:** One place—**before** dense **Section 1b.1** / **Section 1b.5** / **`#### 1b.5b`**—that states **what changes**, **what this repo owns vs a sibling `tech-plans/*.md`**, **which locked contracts** apply, and **merge / land ordering** across repos. **Forbidden:** Empty subsection, “see spec”, or only a link to `shared-dev-spec.md` without row-level ✓/N/A.

**1 — Surface ownership (every row: ✓ = this repo elaborates in the cited subsection(s); N/A = one-line reason + spec section or sibling plan):**

| Delta class | This repo | Detailed in subsection | If N/A: sibling plan / owner |
|-------------|-----------|----------------|------------------------------|
| Persistence / DDL / migrations | ✓ / N/A | Section 1b.1 | e.g. `blue-ocean-server.md` |
| Search / index / ingest | ✓ / N/A | Section 1b.1a | … |
| Synchronous API **serve** | ✓ / N/A | Section 1b.5 | … |
| Synchronous API **consume** | ✓ / N/A | Section 1b.5 | … |
| Async messages **publish** | ✓ / N/A | **`#### 1b.5b`** | … |
| Async messages **consume** | ✓ / N/A | **`#### 1b.5b`** | … |
| Cache (invalidate / read) | ✓ / N/A | **`#### 1b.5b`** | … |
| Cron / jobs / internal-only HTTP | ✓ / N/A | Section 1b.5 + Section 2 | … |
| Shared types / packages | ✓ / N/A | Section 1b.2 + tasks | … |
| Web / app UI | ✓ / N/A | Section 1b.4 | … |

**2 — Cross-repo dependencies (add rows until none left implicit):**

| Needs from (repo / plan file) | Interface (contract path, OpenAPI path/operation id, topic, table) | Blocks this plan? (Y / N / parallel OK) |
|-------------------------------|------------------------------------------------------|------------------------------------------|
| … | … | … |

If **none:** one line — **`No cross-repo ordering risk — all interfaces frozen under task contracts/ + shared-dev-spec.md.`**

**3 — Implementation summary (3–8 sentences, MUST):** Prose for **this repo only**—runtime behavior change, main entrypoints (routes, workers, UI surfaces), data written/read, **failure modes** called out in PRD/spec, env / feature flags. Not marketing copy; enough that a cold implementer knows **why** Section 2 exists.

### 1b.1 Data model delta (persistence — any durable store)

**Store-agnostic:** The frozen **`contract-schema-db`** names the engine(s) — relational (PostgreSQL, MySQL, …), **document** (MongoDB, …), **columnar** (ClickHouse, BigQuery table DDL, …), key-value, graph, etc. **Match the contract’s vocabulary** (table, collection, merge tree, materialized view, …); do not assume SQL unless the contract is SQL.

Ground this in the **locked shared-dev-spec** and any **`db-contract` / `contract-schema-db`** material — do not invent persistence objects here that the spec did not lock.

| Logical object (table / collection / topic / bucket / …) | Change type | Rationale (one line — **product / PRD**: cite `prd-locked` section/Q when not obvious from contract title alone) | Rollback or backward-compat note |
|--------------------------------------------------------|-------------|----------------------|----------------------------------|
| *(one row per schema-affecting change: CREATE, ALTER, DROP, new index, validator, TTL, partition, …)* | *use contract terminology* | *why this persistence exists for the user journey / compliance* | *e.g. nullable-first, dual-write, backfill, irreversible — link to contract if long* |

- If this repo has **no** persistence ownership for this task (e.g. pure UI repo), state exactly: **`No database or durable storage schema changes in this repo.`**
- If persistence lives in another repo, say **which repo owns schema migrations** and keep this table empty with that cross-reference — do not imply this repo runs migrations it does not own.

Every later **migration / schema-change task** in this file MUST correspond to a row above (same logical object + change type). Orphans either way are a planning defect.

**Schema detail (MUST — not optional):** Applies **only** to rows in the delta table. For each such row, include **either** (a) the **full** proposed change in a **fenced code block** using the **same language the frozen contract uses** — e.g. **SQL** (`CREATE TABLE` / `ALTER` for relational or ClickHouse SQL dialect), **JSON** (Mongo validators, `createIndexes`, collection JSON Schema if locked in **contract-schema-db**), **YAML/XML/DSL** if the contract locks that — immediately under the table (or per-row sub-blocks), **or** (b) a **verbatim** paste from the locked **`contract-schema-db`** / shared-dev-spec excerpt with **heading + file path**. Spell out **fields** (columns, BSON paths, nested docs), **types**, **nullability** / required keys, **defaults**, **indexes**, **sharding/partition/TTL**, and **referential rules** (FKs, `$lookup`, weak refs) per what the store actually supports and the contract locks. **Forbidden:** "Add fields as needed", "migration per ORM", or deferring shape to Section 2 without an inlined or verbatim contract body here. **When the section opens with the one-line N/A** (no persistence in this repo), **no** schema block is required — do not fabricate persistence shapes to satisfy this skill.

### 1b.1a Search / ranked-retrieval index delta (any engine)

**When N/A:** One line: **`1b.1a not applicable — no search index ownership or contract-search surface in this repo for this task.`** (cite spec section if ambiguous.)

**When the locked spec includes search / `contract-search`:** Mirror the contract — do not invent fields in the plan that the spec did not lock.

| Index, alias, or collection (per **contract-search**) | Definition / mapping / schema change | Reindex, dual-write, refresh, or vector rebuild policy | Rollback / compat | **PRD / rationale (one line)** |
|-------------------------------------------------------|----------------------------------------|--------------------------------------------------------|---------------------|----------------------------------|
| *(row per search surface touched)* | *e.g. new field spec, analyzer, vector params, Solr `fieldType`* | *e.g. reindex job, blue/green, incremental backfill* | *e.g. read old alias until drain* | *which search UX / reporting obligation this index serves* |

Every later **index / mapping / ingest task** in Section 2 MUST correspond to a row above.

**Index-definition detail (MUST — not optional):** Applies **only** to rows in the table. For each such row, include **either** (a) the **full** proposed definition in a **fenced block** using the **format the contract locks** — often **JSON** (Elasticsearch, OpenSearch, Typesense, Meilisearch, Algolia index settings, many vector DB APIs), sometimes **XML** (Solr `schema.xml` snippets), **YAML**, or another DSL — immediately under the table (or per-row), **or** (b) a **verbatim** paste from the locked **`contract-search`** / shared-dev-spec with **heading + file path**. Cover **field names**, **types**, **analyzers** / **tokenizers** / **normalizers** (when applicable), **vector** / **embedding** dimensions and distance (when applicable), and **dynamic** / **nested** policies per engine. **Forbidden:** "mapping per team norm", "see dashboard X", or deferring shapes to Section 2 without an inlined or verbatim contract body here. **When the one-line N/A** applies, **no** definition block is required.

### 1b.2 Implementation reuse vs net-new

Summarize so **reuse is not taken for granted** from task ordering alone. **Prefer evidence from `~/forge/brain/products/<slug>/codebase/`** (`index.md`, `modules/*.md`, `api-surface.md`): reuse bullets should cite paths that **appear in the scan** when the repo was scanned. If the scan is missing or stale, state **`SCAN_MISSING_OR_STALE`** and trigger **`/scan <slug>`** (or equivalent) before claiming paths.

- **Reuse (extend, call, wrap, configure):** bullets with **repo-relative paths** and symbol/module names (existing services, models, components, shared validators).
- **Net-new:** bullets — new files, new tables, new public routes/events — also with paths or names.
- **Unknown / scan gap:** if brain scan or spec does not prove a reuse target, say **`DISCOVERY_REQUIRED`** or **`HUMAN_CONFIRM`** — do not silently pick a module.

### 1b.2b First-session reconnaissance (MUST when elaboration applies)

**Why this exists:** `scan-codebase` + `codebase/index.md` / `modules/*.md` answer *where things probably live*. They do **not** replace an implementer’s **first hour** in the product repo — the failure mode you feel as “scan/review don’t work” is often **only brain stubs, no ordered assignment**. This block is the **handoff from navigation → execution**.

**HARD-GATE — fill when **any** of:** net-new **≥2** files or packages in this repo for the task; **≥3** distinct integration touchpoints (HTTP, DB, bus, cron, third party); or **`### 1b.2a`** marks **PARTIAL** for **≥2** categories. **One-line N/A** only when the repo change is trivial (single-file, single-call-site) **and** Section 1b.6 has no **UNKNOWN** for those paths.

1. **Branch / tree sanity** — Copy-paste block: `git fetch` + `git branch -a` (or equivalent) scoped to branches that might collide with this work; `git log -1 --oneline` on the branch the plan assumes. Use **real** remote/default names from **`discovery.md`** / **`context-loaded.md`** / product convention — not placeholders.
2. **Minimum read list** — **≥5** **repo-relative** paths the implementer must **Read** before editing (utilities, models, **one complete** route/controller block showing `validateSchema` + auth pattern, controller index). For each path: **one clause** what to extract (e.g. “every exported symbol you will call”, “middleware order”). **Forbidden:** only `[[wikilinks]]` to brain `codebase/` with no product-repo path.
3. **Discovery commands** — **≥2** copy-paste **`rg` / `grep`** (or `fd`) lines that **locate extension points** (e.g. banner system, layout shell, existing `Modal` import). Must run from repo root shown in the block.

**Self-review:** If this subsection is missing when the gate applies, or paths are generic (`controllers/foo.js` without naming the real hub), → **CHANGES** — same bar as shallow **`### 1b.2a`**.

### 1b.3 Trace to locked spec

Bullets mapping **`prd-locked.md`** bullets / Q ids, **`shared-dev-spec.md`** requirement headings, and **`contracts/*`** IDs **to Section 2 task ids** in this file.

**Format (MUST — every bullet):**  
`- **<source id>** (e.g. prd success #2, spec FR-3, contracts/api-rest POST /foo) → **Tasks T…** — **Why:** <one sentence — product or integrity reason this slice exists; what PRD pain is removed>`  

If a requirement has no task, **STOP** — fix coverage before dispatch. **Forbidden:** bullets that only list “FR-3 → T1–T4” with no **`Why:`** clause.

### 1b.4 Design source → UI / component plan (web & app repos)

**Purpose:** Intake may lock **`figma_file_key` + `figma_root_node_ids`**, **`design_brain_paths`**, **`lovable_github_repo`**, or **`design_waiver: prd_only`**. Council may copy that into **Design source (from intake)** in `shared-dev-spec.md`. None of that helps E2E delivery if the **tech plan** never maps design to **concrete components, routes, or files**. This subsection is the handoff from **design transport** to **implementation tasks**.

**When to fill the table vs one-line N/A**

| Situation | Required content |
|-----------|-------------------|
| This file is for a **backend**, **worker**, **shared-schema**, or other **non-UI** repo | One line: **`1b.4 not applicable — not a web/app repo.`** |
| **`design_ui_scope: not applicable`** in lock (no user-visible UI for this slice) | One line: **`1b.4 not applicable — no user-visible UI in this repo for this task.`** |
| **`design_new_work: yes`** OR implementable design paths/keys exist (Figma, `design_brain_paths`, Lovable repo) | **Full table** (below) + ensure **each UI task** later references a **row id** (e.g. `D1`) in its title or header |
| **`design_new_work: no`** but UI still changes | Table or bullet list: **which existing components** (from **scan**) are extended; if any **new** file is unavoidable, say why PRD/engineering-only still requires it |

**Design → implementation mapping table** (add rows until every net-new or changed screen in scope is covered):

| Id | Design anchor (Figma node id / frame name / path under `.../design/` / Lovable route) | UI deliverable (screen, component, layout region) | Existing code (path from **brain scan**) **or** `NET_NEW` | **PRD section / Q / success criterion — rationale (what obligation this UI closes)** | Design parity, tokens, a11y |
|----|----------------------------------------------------------------------------------------|---------------------------------------------------|-------------------------------------------------------------|--------------------------------------------------------------------------------|------------------------------|
| D1 | *(e.g. `123:456` or `design/wireframes/checkout.png`)* | *(e.g. Checkout summary card)* | *(e.g. `src/features/cart/Summary.tsx` or `NET_NEW`)* | *(e.g. `prd success #2` — recruiter sees verification state before posting)* | *(states, contrast, keyboard)* |

**Rules**

- Do **not** write “see Figma” without **node id(s)** or **brain path** that appear in the **locked** PRD/spec — chat URLs are not a transport layer.
- If **`design_waiver: prd_only`** is locked, the table still lists **screens/components** and maps them to **scan-backed** files or `NET_NEW`, with **one line** citing the waiver for pixel latitude.
- **Every** UI implementation task in Section 2 should reference **`D<n>`** or explicitly say **waiver + PRD section** so reviewers can trace intake → plan → code.

### 1b.5 API ↔ consumer map (synchronous contracts — REST, GraphQL, SOAP, gRPC, …)

**Purpose:** E2E delivery requires a **written** answer to: *which component calls which **operation***, and *where the handler / resolver / service implementation lives* — using the **same style the frozen contract uses** (not “everything is REST”).

**When N/A:** This repo has **no** synchronous API **server** and **no** synchronous API **client** changes for this task — one line: **`1b.5 not applicable — no synchronous API surface (REST/GraphQL/SOAP/gRPC/…) in this repo for this task.`** (cite spec section if needed.)

**Contract styles (fill the tables that apply; omit styles the spec marks N/A):**

**REST (HTTP + JSON/XML as locked):** When the repo **implements or changes** REST handlers:

| Endpoint (METHOD `path`) | Handler (repo-relative path : symbol or class#method) | Auth / versioning / idempotency | **PRD / spec trace + rationale (one line — which acceptance or FR this operation fulfills; why it exists)** | Consumers — component path **or** `tech-plans/<other>.md` Section 1b.5 row id |

When the repo **consumes** REST only (or add consumer rows in addition to the owner table above):

| Consumer (path : component or hook) | When it runs | METHOD + `path` | Client module (path) | Success + error handling (status / body shape) | **PRD / rationale (one line)** |

**GraphQL:** When the repo **serves or consumes** GraphQL per lock — add a final column **`PRD / rationale (one line)`** to each table you fill (same rule as REST).

| Operation (`query` / `mutation` / `subscription` + name) | Schema entry point or document id | Server handler or client call site (path : symbol) | Variables shape | Auth / errors (`errors[]` / `extensions`) | **PRD / rationale (one line)** |

**SOAP / XML-RPC:** When the repo **serves or consumes** SOAP per lock — append column **`PRD / rationale (one line)`** (same rule as REST).

| Service / port / binding (WSDL ref) | Operation (QName or SOAPAction) | Handler or client (path : symbol) | Request XML sample or XSD element ref | Response XML sample or fault shape | **PRD / rationale (one line)** |

**gRPC / protobuf:** When locked — append column **`PRD / rationale (one line)`**.

| Package.`Service`/`Method` | `.proto` ref | Server impl / client stub (path) | Request / response message fields (or verbatim `.proto` excerpt) | **PRD / rationale (one line)** |

**Cross-reference:** If the owning plan is in another repo, cite **`tech-plans/<other>.md` Section 1b.5** + **stable operation key** (`METHOD+path`, GraphQL operation name, SOAP QName, gRPC `FullMethodName`) so **`tech-plan-self-review` Section 1d** can diff them.

**Wire shapes (MUST):** For **each** new or materially changed **operation** in the tables above, add **fenced** examples in the **contract’s format**: **`json`** for typical REST/GraphQL variables and payloads, **`xml`** for SOAP bodies/faults, **`protobuf`** / **`text proto`** blocks if that is how the contract is written — **or** a **verbatim** OpenAPI / GraphQL SDL / WSDL / `.proto` excerpt with file path. Include **errors**, **pagination**, **headers**, or **metadata** when the spec defines them. **Forbidden:** "See WSDL / SDL / OpenAPI" without inlined shape, or `TBD` where the contract already decided.

#### 1b.5b Message brokers, topics, queues, and cache (`contract-event-bus` / `contract-cache`)

**Purpose:** Services integrate through **Kafka**, **RabbitMQ**, **ActiveMQ** / **JMS**, **Azure Service Bus**, **NATS**, **SQS**, etc. — not only HTTP. **Section 1b.5** synchronous **N/A** does **not** excuse missing **`#### 1b.5b`** when this repo **publishes, consumes, or invalidates** messages or cache entries named in the lock.

**When N/A:** One line: **`1b.5b not applicable — no cache key or message-bus ownership in this repo for this task.`** (cite spec section / contract IDs.)

**When applicable:** Mirror **`contract-event-bus`** / **`contract-cache`** (or locked spec sections) — do not invent topic names or payload shapes.

| Kind | Destination id (**Kafka** topic[+partition strategy]; **RabbitMQ** exchange+queue+routing key; **ActiveMQ**/JMS queue/topic; **SQS** ARN/url; cache key pattern — **verbatim from contract**) | Producer (path : symbol) **or** `EXTERNAL` | Consumer or invalidator (path : symbol) **or** `NONE` | Ordering / TTL / idempotency / retry | **PRD / rationale (one line — e.g. “prd section6 — notify recruiter of tier change”)** |
|------|--------------------------------------------------------|-------------------------------------------|------------------------------------------------------|--------------------------------------|--------------------------------------|
| *(row per changed contract item)* | *verbatim from contract* | … | … | *per lock* | *why this message/cache touch exists for the product* |

**Payload & key shape (MUST):** For **each** new or materially changed **message** row, add a **fenced** block in the **broker’s on-wire format** as locked — commonly **`json`** (Kafka JSON, Rabbit JSON payloads), often **`xml`** (JMS/SOAP-wrapped bodies, legacy XML), or **hex / text proto** if binary contracts are documented that way — or **verbatim** paste from **`contract-event-bus`**. For **cache** rows, include **value shape** or **invalidation rule** as locked. **Forbidden:** Prose-only (“listens on queue X”) **without** inlined payload or verbatim contract when the contract defines it. If the **PRD/spec never locked** payloads, **BLOCKED** or **`SPEC_INFERENCE`** in Section 0 — do not silently invent in tasks.

### 1b.2a Touchpoint & boundary inventory (MUST — full exploration mode)

**Placement (read carefully):** **`### 1b.2a`** is written **after** **`### 1b.5`** and **`#### 1b.5b`** in the markdown file so rows cite **real** operations, topics, and handlers from those sections. **Naming:** `2a` = **integration / boundary exploration pass** — not “optional appendix.”

**Purpose:** **Full exploration** — enumerate **every class of external touchpoint** this repo hits for **this task**, with **scan-backed evidence** and **what changes**. Rationale columns explain *intent*; **this section** proves you *walked the walls* (routes, auth, jobs, buses, third parties, flags, observability, …). **Forbidden:** empty table, “N/A all”, or rows with **no** `codebase/` path / `rg` note / file:line.

**Process (MUST — same planning session before `REVIEW_PASS`):**

1. Walk **`~/forge/brain/products/<slug>/codebase/`** (`index.md`, `modules/*.md`, **`api-surface.md`**, route indexes, consumer registration files).
2. For **each category** below that **could** apply to this repo + task: run **targeted** **`rg` / `Read`** on the **product repo** (not only brain stubs) until you can mark **Y** (touched this task), **N** (out of scope + **one-line** why + `prd` or `spec` section), or **PARTIAL** (what remains → **Section 1b.6** or Section 0).
3. **Edge / failure touchpoints:** Add extra rows for **retry**, **idempotency**, **DLQ**, **circuit breaker**, **rate limit**, **PII logging**, **multi-tenant isolation** if PRD/spec calls them out — same table schema.

**Inventory table (MUST — one row per category that is Y or PARTIAL; N requires one consolidated row per *cluster* or one row per N with citation):**

| # | Touchpoint category | Y / N / PARTIAL | Evidence (repo paths + tool: e.g. `rg pattern` → `src/...`) | Current behavior (1 line) | What changes for this task (1–2 lines) | PRD / spec section | Section 1b subsection(s) + Section 2 task ids |
|---|---------------------|-----------------|-------------------------------------------------------------|-----------------------------|------------------------------------------|--------------|-----------------------------|
| 1 | **HTTP ingress** (router mount, gateway, version prefix) | | | | | | Section 1b.5, … |
| 2 | **Authn / authz** (session, JWT, API key, RBAC, moderator vs recruiter) | | | | | | |
| 3 | **Middleware chain** (CORS, body parser, rate limit, request id) | | | | | | |
| 4 | **Feature flags / kill switches / env-driven behavior** | | | | | | |
| 5 | **Cron / scheduler / delayed jobs / internal-only HTTP** | | | | | | |
| 6 | **Outbound HTTP / RPC** (other services, payment, KYC, webhooks you call) | | | | | | |
| 7 | **Inbound webhooks** (signatures, replay, idempotency stores) | | | | | | |
| 8 | **Persistence** (new migrations, triggers, read replicas, backfill jobs) | | | | | | Section 1b.1, … |
| 9 | **Search / index / ingest workers** | | | | | | Section 1b.1a |
| 10 | **Message bus** (publish, consume, outbox, ordering, DLQ) | | | | | | **`#### 1b.5b`**, … |
| 11 | **Cache** (read-through, invalidate-on-event, TTL races) | | | | | | |
| 12 | **Email / SMS / push / in-app notification templates** | | | | | | |
| 13 | **File / object storage** (S3, GCS, signed URLs, virus scan) | | | | | | |
| 14 | **Observability** (structured logs, metrics, traces, alerts touched) | | | | | | |
| 15 | **Security** (secrets manager, encryption at rest, CSRF, SSRF guards) | | | | | | |
| 16 | **Compliance / audit** (append-only logs, data retention, export) | | | | | | |
| 17 | **i18n / l10n / copy tokens** (if user-visible copy changes) | | | | | | Section 1b.4 |
| 18 | **Mobile / web sibling consumers** (deeplinks, App Links, shared cookies) | | | | | | XALIGN / Section 1b.5 |
| 19 | **Shared libs / monorepo packages** this repo imports | | | | | | |
| 20 | **Build / deploy / runtime config** (Docker, k8s, PM2, systemd — if this task changes them) | | | | | | |

**Narrative (MUST):** After the table, **3–10 bullets** titled **`Exploration notes`** — surprises from `rg`/reads (e.g. “duplicate route registration in `legacyRoutes.js`”, “AMQP reconnect hides publish errors”). Each bullet ends with **→** task id or **Section 1b.6** U#.

**Minimum bar:** If the task is **non-trivial** (≥3 Section 2 tasks or any **Y** on rows **1, 2, 5, 6, 8, 10**), **PARTIAL** or empty **Evidence** on those rows is **BLOCKED** until resolved or **`BLOCKED`** with owner.

### 1b.6 Unknowns & deep discovery closure

**Purpose:** Scans and specs leave **gaps**. **Elaborative** planning means **closing** gaps with repo evidence, not leaving them for implementers.

1. Start a table (zero rows = fine only if you genuinely have **no** unknowns — then write **`No material unknowns — scan + spec sufficient for every Section 2 path.`**):

| U# | Unknown | Why it matters if wrong |
|----|---------|-------------------------|

2. For **each** row, append columns (same table or continuation):

| … | Deep discovery performed (tools: e.g. `rg`, `Read`, hub file) | Resolution (`RESOLVED: …` \| `BLOCKED: …`) |

**Rules**

- **RESOLVED** must cite **concrete evidence** (file paths, line ranges, grep pattern hit counts, test file name) — not “I checked.”  
- **BLOCKED** must state the **exact** decision needed from a human or from **`/scan`** refresh — and **Section 2 must not** contain tasks that depend on that unknown until resolved.  
- **Deep exploration is required** when scan/`api-surface.md` does not show registration, client wrapper, middleware chain, or feature flag gate: open those files in the product repo until the unknown is mapped or escalated.

## Section 1c: Plan lifecycle, cross-repo alignment, and feedback

Tech plans are **not one-shot** documents. They go through **review → revise → re-align** until integration is legible on paper.

1. **Status line** — Placed immediately under the `#` title (see **Section 1b** authoring order). Values: **`DRAFT`** | **`REVIEW_CHANGES`** | **`REVIEW_PASS`**. Start at **`DRAFT`**. After **`tech-plan-self-review`**: all PASS → **`REVIEW_PASS`**; any CHANGES or BLOCKER → **`REVIEW_CHANGES`**, fix plans, set **`DRAFT`**, re-run review.

2. **Revision log** (append one row per meaningful edit):

   | Rev | When (ISO8601 approx) | Who | Trigger (e.g. self-review Section 1b.5 FAIL, XALIGN drift) | What changed |

2b. **FORGE machine gates (HARD-GATE when `Tech plan status: REVIEW_PASS`)** — **`tech-plan-self-review` Section 0c** must be **materialized in this file** so CI can detect rubber-stamps (`tools/verify_tech_plans.py` / **`verify_forge_task.py --strict-tech-plans`**). **Omit on `DRAFT` / `REVIEW_CHANGES`.** Before flipping to **`REVIEW_PASS`**, append to **Section 1c** (above or below the revision log table, but **inside Section 1c**):

   - On its **own line**, immediately **above** the Section 0c requirement inventory table:

     `<!-- FORGE-GATE:SECTION-0C-INVENTORY:v1 -->`

   - On its **own line**, immediately **above** the code recross-check evidence (paths + tools used, one bullet or row per checked path / sample rule from **`tech-plan-self-review` Section 0c** step 4):

     `<!-- FORGE-GATE:CODE-RECROSS:v1 -->`

   **Why:** Skills are prose; agents optimize for “sounds done.” Anchors force **inventory + recross** to exist in the same artifact the implementer reads — the failure mode you get without them is chat-only PASS.

   **First-class inputs (Section 0c inventory — HARD):** If any of these exist under **`~/forge/brain/prds/<task-id>/`**, the Section 0c requirement inventory (the markdown table **immediately below** **`<!-- FORGE-GATE:SECTION-0C-INVENTORY:v1 -->`**) **must** include **≥1 row** that cites that source (source id / short text / trace columns — machine CI uses substring presence in the inventory block): **`prd-locked.md`**, **`prd-source-confluence.md`** or **`source-confluence.md`** (Confluence mirror / normative PRD body), **`shared-dev-spec.md`**, **`touchpoints/*.md`** (especially **`COHORT-AND-ADJACENCY`**, **`PRD-SIGNAL-REGISTRY`**), **`qa/manual-test-cases.csv`**. An inventory that only traces **`prd-locked.md`** while **`prd-source-confluence.md`**, **`touchpoints/*.md`**, or populated **QA CSV** exists is **BLOCKED** for **`REVIEW_PASS`** when CI enables **`verify_forge_task.py --strict-0c-inventory`** (see **`docs/forge-task-verification.md`**).

3. **Minimum feedback loop**

   - Run **`tech-plan-self-review`** on this file **before** treating the plan as final for dispatch.  
   - Record in the log: **`self-review round=<n> result=PASS|CHANGES|BLOCKED`** (short note).  
   - Default **max 3** review rounds per repo per task; then **ESCALATE** with consolidated blockers.

4. **Cross-repo alignment** (when this product task has **≥2** repos touching the **same synchronous API** or **≥2** repos with **split producer/consumer** message plans):

   - After **all** sibling `tech-plans/*.md` are in **`DRAFT`** with **Section 1b.5** filled (for the API styles in play), perform one **cross-walk** using the **contract’s stable keys**: e.g. consumer **METHOD+path** ↔ owner **METHOD+path**; **GraphQL** operation name ↔ server registration; **SOAP** QName / SOAPAction ↔ server operation; **gRPC** `FullMethodName` ↔ `.proto` method. Version/prefix/auth/metadata must match the lock.  
   - For **messages**, verify **destination strings** (topic, queue, exchange+routing key, …) and **payload version** fields match across producer and consumer plans (or cite explicit **compat matrix** in spec).  
   - Append to **each** affected plan’s revision log: **`XALIGN PASS`** or **`XALIGN FAIL: <drift>`** and fix drift before setting **`REVIEW_PASS`**.

5. **Conductor logging** (when orchestrated): emit **`[TECH-PLAN-REVIEW]`** and **`[TECH-PLAN-XALIGN]`** lines as specified in **`conductor-orchestrate`** State 4.

6. **Human go-ahead (pipeline phase — after agent loops, before State 4b)**  
   Automated **`tech-plan-self-review` PASS** + **`XALIGN` PASS** are **not** the same as stakeholder acceptance. **Before** eval YAML / RED (State 4b), a **human** must record one of:
   - **`~/forge/brain/prds/<task-id>/tech-plans/HUMAN_SIGNOFF.md`** from **`docs/tech-plan-human-signoff.template.md`** with **`status: approved`** (or **`changes_requested`** → revise plans → re-run steps 3–5 → new signoff), **or**
   - **`status: waived`** with actor + reason (solo / unattended policy only).  
   Append the same decision as a **revision-log row** in each affected `tech-plans/<repo>.md` for traceability.  
   **Conductor** logs **`[TECH-PLAN-HUMAN] task_id=<id> status=APPROVED|CHANGES_REQUESTED|WAIVED`**. **No State 4b** until **`APPROVED`** or documented **`WAIVED`**.

**Interconnection (no gaps):** `intake` → `parity` (spec-freeze Step 0) → **frozen** `shared-dev-spec` → **Section 0** doubt log → **Section 1b** (data, reuse, design, API map, unknowns) → **Section 1c** (agent review + XALIGN) → **`HUMAN_SIGNOFF.md`** → **State 4b** (QA CSV / eval YAML / RED) → implementation. Skipping a box forwards **hidden** gaps backward into cheaper phases — forbidden.

---

## Section 2: Bite-Sized Task Breakdown

### Traceability & rationale (MUST — every task)

Immediately under each **`## Task …`** title (before **Files affected**), include **both** blocks:

1. **`Traces to:`** — Bullet list of **stable ids**: `prd-locked.md` section / Q / numbered success or acceptance line; `shared-dev-spec.md` heading or FR id; `contracts/<file>.md` heading or operation id. Must tie to ≥1 **Section 1b.0** row (or explicit chore exception approved in Section 0).
2. **`Rationale:`** — **1–4 sentences**: **why** this task exists (design intent, risk removed, user-visible outcome); **what PRD or acceptance obligation** it implements; **what breaks in prod** (or what review fails) if omitted. **Forbidden:** empty, or only repeating the task title.

### Definition
Each task must satisfy:
- **Duration**: 2-5 minutes of focused execution
- **Scope**: Single feature increment (add one endpoint, one component, one migration)
- **Completeness**: Every file shown in full, no abbreviations, no "..."
- **Specificity**: Exact file paths, exact bash commands, exact test assertions
- **Intent:** **`Traces to:`** + **`Rationale:`** present per **Traceability & rationale** above

### Non-Examples (What NOT to do)
```markdown
## ❌ Task: Add validation
- Files: backend-api/routes/auth.js
- Code: "Add validation logic here"
- Test: "Run npm test"

## ❌ Task: Create user model
- Files: backend-api/models/user.js
- Code: 
  ```js
  class User {
    ...
    validateEmail() { /* validation */ }
  }
  ```
```

### Correct Example
```markdown
## ✓ Task: Add email validation to User model
- Files: backend-api/models/user.js
- Code: (complete class with method)
  ```js
  class User {
    constructor(data) {
      this.id = data.id;
      this.email = data.email;
    }
    
    validateEmail() {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(this.email)) {
        throw new Error('Invalid email format');
      }
      return true;
    }
  }
  
  module.exports = User;
  ```
- Test: `npm test -- models/user.test.js` (expect: email validation throws on invalid)
- Commit: "feat: add email validation to User model"
```

### Task Template
```markdown
## Task N: [Specific action] in [file/module]

**Traces to:**
- `prd-locked.md` — … (section / Q / success line id)
- `shared-dev-spec.md` and/or `contracts/…` — …

**Rationale:**
1–4 sentences: why this change; which PRD obligation it closes; what fails if skipped.

**Files affected:**
- /path/to/file1.js
- /path/to/file2.ts
- etc.

**Complete code for each file:**
(Show every line, no abbreviations)

**Exact bash command to test:**
```bash
npm test -- specific-test-file.test.js
```

**Expected output:** (What success looks like)

**Git commit message:**
```
feat: [action description]
```
```

---

## Section 3: Task Ordering

### Dependency-First Approach
Tasks must respect this order:

1. **Layer 0: Shared Schemas** (no dependencies)
   - TypeScript types
   - Validation schemas (zod/joi)
   - Contract definitions
   - Shared constants and enums

2. **Layer 1: Backend Infrastructure** (depends on schemas)
   - Database migrations
   - Models and DAOs
   - Business logic services
   - Error handling and middleware

3. **Layer 2: Backend APIs** (depends on models)
   - REST endpoints
   - Request/response handlers
   - Authentication and authorization

4. **Layer 3: Web Frontend** (depends on API contracts)
   - API client (generated or manual)
   - State management (Redux, Zustand)
   - Components and views
   - Forms and validation

5. **Layer 4: Mobile App** (depends on API contracts)
   - API client
   - Navigation structure
   - Screens and components
   - Offline-first setup

### Within-Project Ordering
Order by dependency:
- Shared types → Constants → Validation → Models → Services → Routes → Middleware → Integration

### Dependency Markers
Mark explicit dependencies:
```markdown
## Task 3: Create user repository
**Depends on:** Task 1 (User schema), Task 2 (database connection)

## Task 5: Add POST /users endpoint
**Depends on:** Task 3 (user repository), Task 4 (authentication middleware)
```

---

## Section 4: Code Completeness

### Every file must be 100% complete
No:
- `import { Todo } from '../types'` without defining Todo in this plan
- `function validateUser() { /* validation logic */ }`
- `// Add error handling here`
- `...rest of the file...`

### Every import must be resolvable
If a file imports from another file, ensure that file is created earlier in the plan or it already exists in the repo.

### Example: Bad Plan
```markdown
## Task 2: Create user service
- Files: backend-api/services/userService.js
- Code:
  ```js
  const { UserRepository } = require('../models/user');
  
  class UserService {
    async createUser(userData) {
      return UserRepository.create(userData); // Not implemented yet!
    }
  }
  ```
```

### Example: Good Plan
```markdown
## Task 1: Create user repository
- Files: backend-api/models/userRepository.js
- Code:
  ```js
  class UserRepository {
    static async create(userData) {
      const db = require('../db');
      const query = 'INSERT INTO users (email, name) VALUES (?, ?)';
      const result = await db.run(query, [userData.email, userData.name]);
      return { id: result.lastID, ...userData };
    }
  }
  module.exports = { UserRepository };
  ```

## Task 2: Create user service
- Files: backend-api/services/userService.js
- Code:
  ```js
  const { UserRepository } = require('../models/userRepository');
  
  class UserService {
    async createUser(userData) {
      return UserRepository.create(userData);
    }
  }
  module.exports = { UserService };
  ```
```

### Complete Code Checklist
- ✓ All imports are defined or pre-existing
- ✓ All functions have complete bodies (no // TODO or // TODO: implement)
- ✓ All class methods are implemented
- ✓ All error cases are handled
- ✓ No placeholder strings or fake data

---

## Section 5: Verification Checklist

Every task must include:

### 1. Test Command
An exact, runnable bash command:
```bash
npm test -- users.test.js
npm run migrate:test
npm run build && npm run test:integration
jest --testPathPattern=userService.test.js
```

### 2. Expected Output
What the developer sees on success:
```
PASS  tests/userService.test.js
  UserService
    ✓ creates user with valid email (2ms)
    ✓ throws error on invalid email (1ms)
    ✓ returns user with id (3ms)

Test Suites: 1 passed, 1 total
Tests: 3 passed, 3 total
```

### 3. Commit Message
Standard format:
```
feat: [action] [what changed]
fix: [bug] [how it's fixed]
refactor: [what] [why simplified]
test: [what] [coverage added]
docs: [what] [clarity improved]
```

Example:
```
feat: add email validation to User model
```

### 4. Integration Checkpoint
After each task, verify:
- [ ] Code compiles/lints (no syntax errors)
- [ ] Test passes (assert expected output)
- [ ] No new import errors
- [ ] No breaking changes to previous tasks

### Task Verification Template
```markdown
## Task 7: Add POST /users endpoint

**Files affected:**
- backend-api/routes/auth.js

**Complete code:**
(Full route handler, no abbreviations)

**Test command:**
```bash
npm test -- routes/auth.test.js -- --testNamePattern="POST /users"
```

**Expected output:**
```
✓ POST /users creates new user (10ms)
✓ POST /users returns 400 on invalid email (5ms)
✓ POST /users returns 409 on duplicate email (8ms)
```

**Commit message:**
```
feat: add POST /users endpoint with validation
```

**Breaking changes:** None
**Backward compatible:** Yes (new endpoint, no changes to existing)
```

---

## Usage

### When Called
1. `brain-read` has provided locked spec from `~/forge/brain/prds/<task-id>/shared-dev-spec.md`
2. Phase 2.10 (shared-dev-spec) is complete and immutable

### How to Use
```bash
# As a subagent in conductor-orchestrate flow:
skill tech-plan-write-per-project <task-id>

# Or manually:
cd ~/forge
# 1. Read the spec
# 2. Break into bite-sized tasks
# 3. Order by dependency
# 4. Write complete code (no placeholders)
# 5. Add test + commit message
# 6. Output to: brain/prds/<task-id>/tech-plans/
```

### Output Structure
```
brain/prds/<task-id>/tech-plans/
├── shared-schemas.md      (layer 0 tasks)
├── backend-api.md         (layers 1-2 tasks)
├── web-dashboard.md       (layer 3 tasks)
└── app-mobile.md          (layer 4 tasks)
```

Each file:
- **Section 0** doubt log present (outcome rows per **Section 0.3**); no **high-impact** `L` confidence rows without **BLOCKED** / **WAIVER** / follow-up owner
- **Section 1b + 1c** preamble is present (**1b.0** with **Why** column, **`1b.0b`**, **1b.1** + **1b.1a** each as delta **or** prescribed one-line N/A, **1b.2**, **`1b.2b`** **or** N/A per gate, **1b.3** with **`Why:`** per bullet, **1b.4**/**1b.5**/**`#### 1b.5b`** with **PRD / rationale** columns where applicable, **`### 1b.2a`** touchpoint table + **Exploration notes** after wire maps, **1b.6** per rules; **1c** status + revision log)
- **Section 2** every task has **`Traces to:`** + **`Rationale:`** immediately under the task title
- Task ordering respects dependencies
- Every task is 2-5 min executable
- Every code block is complete
- Every test is exact and runnable
- Every commit message is standard

---

## Quality Gates

A tech plan passes if:
1. **Completeness**: No "...", no "TODO", no placeholders
2. **Preamble**: **Section 0** cleared for planning; Sections **1b + 1c** present; **Section 1b.0** matrix complete (**PRD trace gate** + **Why** column satisfied — no silent omission of material **`prd-locked.md`** bullets); **`Section 1b.0b`** present with ✓/N/A aligned to **1b.1** / **1b.5** / **`#### 1b.5b`** (no row marked ✓ without matching elaboration in that subsection); **Section 1b.3** bullets each include **`Why:`**; **1b.1** rows match persistence **schema-change** tasks **or** N/A with no phantom migrations; reuse + spec trace; **1b.4** / **1b.5** / **`#### 1b.5b`** include **PRD / rationale** columns when those tables apply; **1b.4** for web/app; **1b.5** when a **synchronous API** applies **or** explicit N/A (consumer↔owner **operation keys** align across repos per Section 1c); **`#### 1b.5b`** when brokers/cache apply **or** explicit N/A; **`### 1b.2a`** present **after** **Section 1b.5**/**`#### 1b.5b`**, with **Y**/**PARTIAL** rows carrying **non-empty Evidence** (paths + tools) and **Exploration notes** (≥3 bullets for non-trivial tasks); **1b.6** has no silent UNRESOLVED; **1c** shows review rounds + **XALIGN** when multi-repo **API or message** surfaces split across plans; **Section 2** tasks each have **`Traces to:`** + **`Rationale:`**
3. **Specificity**: Every file path is absolute, every command is exact
4. **Testability**: Every task has a runnable test command and expected output
5. **Ordering**: No task depends on later tasks (DAG)
6. **Atomicity**: Each task is independent-executable (dev can run task N without running 1-N-1, given task setup is complete)

---

## Example: Complete Tech Plan Entry

```markdown
# Tech Plan: backend-api

## Task 1: Create user_profiles table migration
**Depends on:** None (schema layer 0)

**Files affected:**
- backend-api/migrations/001_create_user_profiles.sql

**Complete SQL migration:**
```sql
CREATE TABLE IF NOT EXISTS user_profiles (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  first_name VARCHAR(255),
  last_name VARCHAR(255),
  bio TEXT,
  avatar_url VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_user_id (user_id)
);
```

**Test command:**
```bash
npm run migrate:test
npm test -- migrations/001_create_user_profiles.test.js
```

**Expected output:**
```
PASS  migrations/001_create_user_profiles.test.js
  ✓ creates user_profiles table (15ms)
  ✓ enforces user_id uniqueness (8ms)
  ✓ cascades delete on user deletion (12ms)

Test Suites: 1 passed, 1 total
Tests: 3 passed, 3 total
```

**Git commit message:**
```
feat: add user_profiles table migration
```

---

## Task 2: Create UserProfile model
**Depends on:** Task 1 (migration)

**Files affected:**
- backend-api/models/UserProfile.js
- backend-api/models/UserProfile.test.js

**Complete UserProfile.js:**
```js
const db = require('../db');

class UserProfile {
  constructor(data) {
    this.id = data.id;
    this.userId = data.user_id;
    this.firstName = data.first_name;
    this.lastName = data.last_name;
    this.bio = data.bio;
    this.avatarUrl = data.avatar_url;
    this.createdAt = data.created_at;
    this.updatedAt = data.updated_at;
  }

  static async findByUserId(userId) {
    const query = 'SELECT * FROM user_profiles WHERE user_id = ?';
    const row = await db.get(query, [userId]);
    return row ? new UserProfile(row) : null;
  }

  static async create(userId, profileData) {
    const { firstName, lastName, bio, avatarUrl } = profileData;
    const query = `
      INSERT INTO user_profiles (user_id, first_name, last_name, bio, avatar_url)
      VALUES (?, ?, ?, ?, ?)
    `;
    const result = await db.run(
      query,
      [userId, firstName, lastName, bio, avatarUrl]
    );
    return {
      id: result.lastID,
      userId,
      firstName,
      lastName,
      bio,
      avatarUrl,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
  }

  async update(updateData) {
    const { firstName, lastName, bio, avatarUrl } = updateData;
    const query = `
      UPDATE user_profiles
      SET first_name = ?, last_name = ?, bio = ?, avatar_url = ?
      WHERE id = ?
    `;
    await db.run(
      query,
      [firstName, lastName, bio, avatarUrl, this.id]
    );
    this.firstName = firstName;
    this.lastName = lastName;
    this.bio = bio;
    this.avatarUrl = avatarUrl;
    this.updatedAt = new Date().toISOString();
    return this;
  }

  async delete() {
    const query = 'DELETE FROM user_profiles WHERE id = ?';
    await db.run(query, [this.id]);
  }

  toJSON() {
    return {
      id: this.id,
      userId: this.userId,
      firstName: this.firstName,
      lastName: this.lastName,
      bio: this.bio,
      avatarUrl: this.avatarUrl,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt
    };
  }
}

module.exports = UserProfile;
```

**Complete UserProfile.test.js:**
```js
const UserProfile = require('./UserProfile');
const db = require('../db');

jest.mock('../db');

describe('UserProfile', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('findByUserId', () => {
    test('returns user profile when found', async () => {
      const mockProfile = {
        id: 1,
        user_id: 10,
        first_name: 'John',
        last_name: 'Doe',
        bio: 'Developer',
        avatar_url: 'https://example.com/avatar.jpg',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };
      db.get.mockResolvedValue(mockProfile);

      const result = await UserProfile.findByUserId(10);

      expect(result).toBeInstanceOf(UserProfile);
      expect(result.firstName).toBe('John');
      expect(db.get).toHaveBeenCalledWith(
        expect.stringContaining('SELECT * FROM user_profiles WHERE user_id = ?'),
        [10]
      );
    });

    test('returns null when profile not found', async () => {
      db.get.mockResolvedValue(null);

      const result = await UserProfile.findByUserId(999);

      expect(result).toBeNull();
    });
  });

  describe('create', () => {
    test('creates a new user profile', async () => {
      db.run.mockResolvedValue({ lastID: 5 });

      const result = await UserProfile.create(10, {
        firstName: 'Jane',
        lastName: 'Smith',
        bio: 'Designer',
        avatarUrl: 'https://example.com/jane.jpg'
      });

      expect(result.id).toBe(5);
      expect(result.userId).toBe(10);
      expect(result.firstName).toBe('Jane');
      expect(db.run).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO user_profiles'),
        expect.arrayContaining([10, 'Jane', 'Smith', 'Designer'])
      );
    });
  });

  describe('update', () => {
    test('updates user profile', async () => {
      const profile = new UserProfile({
        id: 1,
        user_id: 10,
        first_name: 'John',
        last_name: 'Doe',
        bio: 'Developer',
        avatar_url: 'https://example.com/avatar.jpg',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      });

      db.run.mockResolvedValue({ changes: 1 });

      const updated = await profile.update({
        firstName: 'John',
        lastName: 'Doe Updated',
        bio: 'Senior Developer',
        avatarUrl: 'https://example.com/avatar-new.jpg'
      });

      expect(updated.lastName).toBe('Doe Updated');
      expect(db.run).toHaveBeenCalledWith(
        expect.stringContaining('UPDATE user_profiles'),
        expect.arrayContaining(['Doe Updated'])
      );
    });
  });

  describe('toJSON', () => {
    test('returns serializable object', () => {
      const profile = new UserProfile({
        id: 1,
        user_id: 10,
        first_name: 'John',
        last_name: 'Doe',
        bio: 'Developer',
        avatar_url: 'https://example.com/avatar.jpg',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      });

      const json = profile.toJSON();

      expect(json).toEqual({
        id: 1,
        userId: 10,
        firstName: 'John',
        lastName: 'Doe',
        bio: 'Developer',
        avatarUrl: 'https://example.com/avatar.jpg',
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z'
      });
    });
  });
});
```

**Test command:**
```bash
npm test -- models/UserProfile.test.js
```

**Expected output:**
```
PASS  models/UserProfile.test.js
  UserProfile
    findByUserId
      ✓ returns user profile when found (5ms)
      ✓ returns null when profile not found (3ms)
    create
      ✓ creates a new user profile (4ms)
    update
      ✓ updates user profile (6ms)
    toJSON
      ✓ returns serializable object (2ms)

Test Suites: 1 passed, 1 total
Tests: 5 passed, 5 total
Snapshots: 0 total
Time: 0.847 s
```

**Git commit message:**
```
feat: add UserProfile model with CRUD operations
```

---

## Task 3: Add GET /users/:userId/profile endpoint
**Depends on:** Task 2 (UserProfile model)

**Files affected:**
- backend-api/routes/profile.js
- backend-api/routes/profile.test.js

**Complete profile.js:**
```js
const express = require('express');
const router = express.Router();
const UserProfile = require('../models/UserProfile');
const { authenticateToken } = require('../middleware/auth');

// GET /users/:userId/profile
router.get('/:userId/profile', authenticateToken, async (req, res) => {
  try {
    const { userId } = req.params;

    // Validate userId is a number
    if (!Number.isInteger(parseInt(userId))) {
      return res.status(400).json({
        error: 'Invalid user ID format',
        code: 'INVALID_USER_ID'
      });
    }

    const profile = await UserProfile.findByUserId(parseInt(userId));

    if (!profile) {
      return res.status(404).json({
        error: 'User profile not found',
        code: 'PROFILE_NOT_FOUND'
      });
    }

    res.json(profile.toJSON());
  } catch (error) {
    console.error('Error fetching user profile:', error);
    res.status(500).json({
      error: 'Internal server error',
      code: 'INTERNAL_ERROR'
    });
  }
});

module.exports = router;
```

**Complete profile.test.js:**
```js
const request = require('supertest');
const express = require('express');
const profileRouter = require('./profile');
const UserProfile = require('../models/UserProfile');

// Mock UserProfile
jest.mock('../models/UserProfile');

// Mock auth middleware
jest.mock('../middleware/auth', () => ({
  authenticateToken: (req, res, next) => {
    req.user = { id: 1 };
    next();
  }
}));

const app = express();
app.use(express.json());
app.use('/users', profileRouter);

describe('Profile Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('GET /users/:userId/profile', () => {
    test('returns user profile for valid userId', async () => {
      const mockProfile = {
        id: 1,
        userId: 10,
        firstName: 'John',
        lastName: 'Doe',
        bio: 'Developer',
        avatarUrl: 'https://example.com/avatar.jpg',
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
        toJSON: () => ({
          id: 1,
          userId: 10,
          firstName: 'John',
          lastName: 'Doe',
          bio: 'Developer',
          avatarUrl: 'https://example.com/avatar.jpg',
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z'
        })
      };

      UserProfile.findByUserId.mockResolvedValue(mockProfile);

      const response = await request(app).get('/users/10/profile');

      expect(response.status).toBe(200);
      expect(response.body).toEqual(mockProfile.toJSON());
      expect(UserProfile.findByUserId).toHaveBeenCalledWith(10);
    });

    test('returns 404 when profile not found', async () => {
      UserProfile.findByUserId.mockResolvedValue(null);

      const response = await request(app).get('/users/999/profile');

      expect(response.status).toBe(404);
      expect(response.body.code).toBe('PROFILE_NOT_FOUND');
    });

    test('returns 400 for invalid userId format', async () => {
      const response = await request(app).get('/users/invalid/profile');

      expect(response.status).toBe(400);
      expect(response.body.code).toBe('INVALID_USER_ID');
    });

    test('returns 500 on database error', async () => {
      UserProfile.findByUserId.mockRejectedValue(
        new Error('Database connection failed')
      );

      const response = await request(app).get('/users/10/profile');

      expect(response.status).toBe(500);
      expect(response.body.code).toBe('INTERNAL_ERROR');
    });
  });
});
```

**Test command:**
```bash
npm test -- routes/profile.test.js
```

**Expected output:**
```
PASS  routes/profile.test.js
  Profile Routes
    GET /users/:userId/profile
      ✓ returns user profile for valid userId (12ms)
      ✓ returns 404 when profile not found (8ms)
      ✓ returns 400 for invalid userId format (6ms)
      ✓ returns 500 on database error (5ms)

Test Suites: 1 passed, 1 total
Tests: 4 passed, 4 total
Snapshots: 0 total
Time: 1.204 s
```

**Git commit message:**
```
feat: add GET /users/:userId/profile endpoint
```

---

## Task 4: Register profile routes in main app
**Depends on:** Task 3 (profile routes)

**Files affected:**
- backend-api/index.js

**Complete index.js (update section):**
```js
const express = require('express');
const cors = require('cors');
const authRoutes = require('./routes/auth');
const profileRoutes = require('./routes/profile');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', profileRoutes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({
    error: 'Internal server error',
    code: 'INTERNAL_ERROR'
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;
```

**Test command:**
```bash
npm test -- integration/routes.test.js
```

**Expected output:**
```
PASS  integration/routes.test.js
  App Routes
    ✓ GET /health returns 200 (4ms)
    ✓ GET /api/users/:userId/profile is registered (8ms)
    ✓ POST /api/auth/login is registered (6ms)

Test Suites: 1 passed, 1 total
Tests: 3 passed, 3 total
Snapshots: 0 total
Time: 0.923 s
```

**Git commit message:**
```
feat: register profile routes in main app
```

---
```

---

## Edge Cases & Fallback Paths

### Edge Case 1: Spec has holes in one project (missing implementation details)

**Diagnosis**: Shared spec says "add user authentication" but doesn't specify: which auth mechanism (OAuth, JWT, API key)? Web project has no guidance.

**Response**:
- **Escalate for spec clarification**: "Spec missing detail: authentication mechanism for web project. Options: OAuth2, JWT, API key. Which applies here?"
- **Default not allowed**: Do NOT fill in missing details without confirming with spec owner.
- **Lock clarification**: Once confirmed, document in tech plan: "Authentication: [chosen mechanism] per spec clarification [date]."

**Escalation**: NEEDS_CONTEXT - Cannot write tech plan without clarity. Ask spec owner for missing detail.

---

### Edge Case 2: Tasks cannot be 2-5 minutes (some tasks are inherently larger)

**Diagnosis**: Tech plan says "Task: implement OAuth2 flow: 3 minutes". Realistically, this takes 30+ minutes (API calls, token management, error handling).

**Response**:
- **Break down into smaller tasks**:
  1. "Set up OAuth2 library and dependencies" (2-3 min)
  2. "Implement token request flow" (3-4 min)
  3. "Implement token refresh logic" (3-4 min)
  4. "Add error handling and edge cases" (2-3 min)
- **If task cannot be broken down further**: Escalate to tech-plan-self-review, which will flag it as too large.
- **Justification**: Each task should be completable and reviewable in isolation.

**Escalation**: If a task cannot be broken below 5 minutes without becoming trivial, escalate: "Task is too large. Recommend: split into subtasks or adjust scope."

---

### Edge Case 3: Placeholder cannot be avoided (external dependency, research needed)

**Diagnosis**: Tech plan says "Task: integrate with [Third-Party API]". But API docs are not yet available. Placeholder: "Wait for API docs".

**Response**:
- **Document the blocker**: "Task blocked by: [Third-Party API docs]. Cannot proceed until [condition]."
- **Plan around it**: If possible, write tests/stubs for the API before it's available.
- **Track risk**: Flag in tech plan: "Critical path blocker: [API]. Delay risk: if not available by [date], project at risk."
- **Escalation to tech-plan-self-review**: Self-review will flag this as a risk and escalate if needed.

**Escalation**: BLOCKED - Task has unresolvable external dependency. Flag in tech plan and escalate to conductor if it impacts timeline.

---

### Edge Case 4: Tech Plan Has Cross-Repo Task Ordering Conflict

**Diagnosis**: Project A's task 3 requires a type from Project B's task 5. But the merge order puts Project A first. The tech plan as written cannot execute without breaking the dependency.

**Do NOT:** Silently reorder tasks across repos without flagging the cycle.

**Action:**
1. Identify the cross-repo dependency: which task in which project depends on output from another project?
2. Check if the dependency is a compile-time type, a runtime API call, or a shared contract
3. For compile-time types: require shared/common package task to complete first — update merge order
4. For runtime API: the dependency is satisfied at runtime, not compile-time — no task reordering needed, just document
5. For shared contracts: extract the shared type to a `shared/` or `lib/` project task that runs before both dependent tasks
6. Escalation: NEEDS_COORDINATION — cross-repo task ordering must be approved by both project leads

---

### Edge Case 5: Spec Has No Clear Test Boundary (Integration vs Unit)

**Diagnosis**: The shared-dev-spec defines a feature that spans multiple services (e.g., "user creates order, inventory decrements, notification sent"). The tech plan needs tests, but it's unclear which service owns which assertion.

**Do NOT:** Duplicate assertions across all services, or skip cross-service assertions entirely.

**Action:**
1. Each service owns assertions for its own state changes only (inventory service asserts decrement, not the notification)
2. The eval scenario (not the unit test) owns end-to-end assertions across services
3. Unit tests: pure function behavior, mocked external calls
4. Integration tests (within a service): real DB/cache, mocked external service clients
5. Eval scenarios: real services, real infrastructure, no mocks
6. Escalation: NEEDS_CONTEXT if a service boundary is ambiguous — ask the conductor which service owns the shared state

---

## End of Example

This example shows how each task:
1. Has complete, runnable code (not placeholders)
2. Specifies exact file paths
3. Includes a test command and expected output
4. Has a standard commit message
5. Respects dependencies (Task 2 depends on Task 1)

## Checklist

Before handing plans to tech-plan-self-review:

- [ ] One plan file written per affected repo (not one shared plan)
- [ ] Shared-dev-spec frozen (spec-freeze) before writing began
- [ ] Every spec requirement has at least one task that implements it
- [ ] All code in task blocks is complete and runnable (no `TODO`, no pseudocode)
- [ ] Each task has exact file paths (relative to project root)
- [ ] Test task precedes implementation task for each feature (TDD order)
- [ ] External dependencies identified and flagged if unresolvable

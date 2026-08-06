---
name: tech-plan-write-per-project
description: "WHEN: Shared-dev-spec is frozen and per-project tech plans must be written before dev-implementer dispatch. Output: 1 maximal plan per repo with Section 1b detail, 1b.2a exploration, and Section 2 tasks fully elaborated."
type: rigid
effort: high
requires: [brain-read]
version: 1.1.0
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

## Human input

**Judgment rounds** (**Section 0.1** / **Section 0.2**) run **in chat** — the plan file summarizes outcomes, not a substitute for dialogue. Follow **`skills/using-forge/SKILL.md`** **Multi-question elicitation**: **transcript-visible** questions, **one coherent topic per message** when multiple decisions remain, **blocking interactive prompts** for discrete forks (see **[`skills/_shared/human-input.md`](../_shared/human-input.md)**). Do **not** paste the whole interactive workshop into Section 0 as if the human answered inside the markdown (**Anti-Pattern** rows below).

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
- **`lane-lock.md` records `risk_tier: high-risk` but the plan has no Risk Tier Rigor section** — A wrong first pass on financial/identity/attribution/org-mapping data is expensive or impossible to unwind; skipping the dry-run + staged-rollout plan is exactly the gap `lane-risk-triage` exists to close. STOP. Add the section below before `tech-plan-self-review` can PASS.

## Risk Tier Rigor (when `lane-lock.md` records `risk_tier: high-risk`)

Add this section to the plan, after Section 1b and before Section 2 tasks. Skip entirely (one-line `Risk Tier: standard — N/A`) when `risk_tier: standard`.

- **Data-integrity + rollback plan:** exact tables/records/fields the first pass touches, and the precise steps to undo a bad write (not "redeploy the old version" — that doesn't undo already-written data).
- **Dry-run-on-a-copy approach:** how the first pass gets exercised against a copy of the real data (or an equivalently representative fixture) before touching production, and what "the copy behaved correctly" is verified against.
- **Staged rollout plan:** the rollout is split into stages (e.g. by cohort, region, or percentage) with an explicit **validation query** run between stages — name the query and its expected result, not just "check it looks right."
- **Sign-off:** name who outside the dev+AI loop must approve the validation results before the next stage or full ship (per `lane-lock.md`'s recorded risk reason — the human closest to the data this item touches).

**INSUFFICIENT:** "we'll be careful," a rollback plan that only covers code (not data already written), or a staged rollout with no named validation query between stages.

## Overview

This skill converts a locked shared-dev-spec into bite-sized, executable technical implementation plans per project. Each task is 2-5 minutes of execution with exact file paths, complete code (no placeholders), and exact bash commands.

**Primary audience:** A human or agent who **does not** already know the product repos. The plan must stand alone: **brain scan** supplies *where things live today*; **locked intake design** (`prd-locked.md` and the **Design source (from intake)** section in **shared-dev-spec**) supplies *what net-new UI should match* (Figma nodes, `design_brain_paths`, Lovable GitHub tree, or an explicit waiver). **Taking Figma in intake but omitting it from the tech plan** is the same class of failure as skipping migrations — implementers will invent components and ship visual bugs.

**Order of operations for paths:** Before naming files in tasks, load **`~/forge/brain/products/<slug>/codebase/`** (at least `index.md`, `SCAN.json`, and the `modules/*.md` files that match the spec’s surfaces). **Failsafe:** if `SCAN.json` exists, run **`python3 tools/verify_scan_outputs.py <that/codebase>`** (up to **3** tries, **1s** backoff). On persistent failure, prefix the plan with **`SCAN_INCOMPLETE`** and **do not** treat brain paths as authoritative until `/scan` passes verify — deepen with targeted `rg`/reads or **BLOCKED** per Section 1b.6. Derive **exact repo-relative paths** from verified brain material, then read the product repo only to pull current file contents for “complete code” blocks. If scan is missing or >7 days old, note it and align with `product-context-load` / user on **`/scan <slug>`** before finalizing paths.

**Order of operations for UI:** When this repo is **web** or **app**, read **Design source (from intake)** in the locked spec **and** any **`~/forge/brain/prds/<task-id>/design/`** ingest notes (`MCP_INGEST.md`, `README.md`, …). Complete **Section 1b.4** before writing UI tasks so every screen/component change is tied to **design anchors** and/or **scan-backed** reuse paths — not to memory of a Figma URL from chat.

**Order of operations for naming conventions:** Before writing any task file paths, function names, class names, or variable names in Section 1b or Section 2, read **`~/forge/brain/products/<slug>/codebase/code-style.md`**. All names, import shapes, async patterns, and error handling patterns in the plan must conform to this file. **Fallback if absent (scan not yet run):** open the 3 most recently modified source files in the product repo (`git -C <repo> log --diff-filter=M --name-only -3 -- '*.ts' '*.py' '*.kt' | grep '\.'`) and infer conventions. Log `[WARN] code-style.md absent — naming conventions inferred from recent files` in Section 0 of the plan.

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

## Reference (load on demand)

Deep detail — worked examples, detailed section breakdowns, edge-case deep-dives, templates,
and decision trees — lives in **`reference/tech-plan-reference.md`** (Agent Skills progressive disclosure). This
SKILL.md is the operational contract: discipline, core workflow/decision logic, and checklists.

## Post-Implementation Checklist

- [ ] Plan reads `code-style.md` from brain before naming any functions, classes, or files.
- [ ] All net-new declarations have grep evidence they don't already exist in the codebase.
- [ ] Cross-task duplicate check ran (`grep | awk | sort | uniq -d`) — no duplicated function names across tasks.
- [ ] `[P3-TECH-PLAN-LOCKED]` logged to conductor.log after plan is committed to brain.
- [ ] Plan committed to brain at `tech-plans/<repo-role>-plan.md` with task_id: anchor.

## Checklist

Before handing plans to tech-plan-self-review:

- [ ] One plan file written per affected repo (not one shared plan)
- [ ] Shared-dev-spec frozen (spec-freeze) before writing began
- [ ] Every spec requirement has at least one task that implements it
- [ ] All code in task blocks is complete and runnable (no `TODO`, no pseudocode)
- [ ] Each task has exact file paths (relative to project root)
- [ ] Test task precedes implementation task for each feature (TDD order)
- [ ] External dependencies identified and flagged if unresolvable

## Cross-References

- `lane-risk-triage`: Provides `lane-lock.md`'s `risk_tier` — when `high-risk`, this skill's Risk Tier Rigor section is mandatory before `tech-plan-self-review` can PASS.
- `forge-council-gate`: Provides the locked `shared-dev-spec.md` (all 5 contracts) that this skill decomposes into per-repo tech plans.
- `spec-freeze`: Immutable spec after `[P2-SPEC-FROZEN]` — tech-plan-write-per-project must not diverge from the frozen spec.
- `conductor-orchestrate`: Sequences `[P3-TECH-PLAN-LOCKED]` after tech plans pass review; consuming the plans produced here.
- `worktree-per-project-per-task`: Creates isolated branches for each repo plan produced by this skill.
- `forge-tdd`: Implements the per-repo plan in TDD order; tech-plan-write-per-project must specify test-first steps.
- `docs/conductor-log-format.md`: `[P3-TECH-PLAN-LOCKED]`, `[P3-TECH-PLAN-REVIEW]`, `[P3-TECH-PLAN-HUMAN]` marker formats.

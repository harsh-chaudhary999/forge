---
name: tech-plan-self-review
description: "WHEN: A per-project tech plan has been written and needs verification before dispatch to dev-implementer. HARD-GATE: Section 0c inventory, codebase path recross-check, and 1b.2a touchpoint evidence must be written into the plan file before REVIEW_PASS."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers:
  - "review tech plan"
  - "self-review plan"
  - "check plan before dispatch"
allowed-tools:
  - Bash
  - Edit
  - Read
---

# Tech Plan Self-Review Skill

This skill verifies technical implementation plans against **all authoritative development sources** (not only `shared-dev-spec.md`) before dispatch to dev-implementers. It **must** start from a **full requirement inventory** (PRD + spec + parity/design/contracts as applicable), prove **bidirectional** coverage via **Section 1b.0** and Section 2, **recross-check** brain scan paths against real code, **extend the plan** when gaps are found, then run the structural Section 1b–Section 1c checks. It catches missing requirements, stale scan evidence, incomplete specifications, placeholder code, missing tests, and malformed commit messages.

## Iron Law

```
EVERY TECH PLAN IS VERIFIED AGAINST PRD-LOCKED + SHARED-DEV-SPEC + ANY OTHER TASK-BOUND SOURCES, LINE BY LINE, BEFORE DISPATCH. EVERY MATERIAL REQUIREMENT MUST MAP TO Section 1b.0 AND SECTION 2 (OR WAIVER). A PLAN WITH A PLACEHOLDER OR TODO IS NOT A PLAN — IT IS UNFINISHED WORK. DISPATCH NOTHING THAT FAILS THIS REVIEW. SECTION 0C INVENTORY + CODE RECROSS MUST LIVE IN THE PLAN FILE (FORGE-GATE MARKERS) BEFORE REVIEW_PASS — NOT IN CHAT. A PLAN WITHOUT Section 1c REVIEW HISTORY OR WITH DRIFTING Section 1b.5 OPERATION KEYS (REST, GraphQL, SOAP, gRPC, …) OR Section 1b.5b DESTINATIONS ACROSS REPOS IS NOT READY — RUN THE FEEDBACK LOOP UNTIL PASS OR ESCALATE. AGENT PASS ALONE IS NOT ENOUGH: HUMAN_SIGNOFF (APPROVED OR DOCUMENTED WAIVED) MUST EXIST BEFORE STATE 4B.
```

## Anti-Pattern Preamble: Why Plans Get Rubber-Stamped

**Violating the letter of this review is violating the spirit of this review.**

Plans that pass self-review with placeholders, vague code, or missing tests will generate 3-5x more back-and-forth during build. A 10-minute self-review saves 2 hours of implementer confusion. These rationalizations will block your dispatch:

| Rationalization | The Truth |
|---|---|
| "The implementer will figure out the details" | Implementers work from specs, not intuition. Vague plans produce vague code. Every placeholder you ship becomes a question that blocks the implementer. |
| "It's obvious what the code should do" | Obvious to you NOW, with full context loaded. The implementer starts cold, in a fresh worktree, with only the plan. What's obvious to you is ambiguous to them. |
| "We can iterate during build" | Iteration during build is rework, not iteration. The plan is the contract. Changing it mid-build invalidates tests, breaks assumptions, and wastes time already spent. |
| "This is just a rough draft, I'll polish later" | Later never comes. The plan goes to dispatch as-is. If it has TODOs now, it will have TODOs when the implementer reads it. Review NOW or pay later. |
| "The tests will catch any gaps" | Tests validate what's written in the plan. If the plan is wrong, the tests validate the wrong thing. Self-review catches spec-plan mismatches that tests cannot. |
| "Type mismatches are minor, the compiler will catch them" | Type mismatches between plan tasks mean the integration will fail. Compiler catches single-file issues; self-review catches cross-task contract breaks. |
| "I already reviewed this mentally" | Mental reviews have zero evidence trail. You cannot prove you checked every line. Run the checklist. Mark each item. Evidence beats confidence. |
| "Self-review is one-and-done — I'll fix gaps in code" | **CHANGES REQUESTED** must produce **plan revisions** (Section 1c log + status). Coding without updating the plan invalidates TDD and eval traceability. |
| "Self-review only re-reads the tech plan markdown" | **BLOCKED process.** Review **starts** from **`prd-locked.md`** + **`shared-dev-spec.md`** + any other locked task sources, builds a **requirement checklist**, and only **then** compares the plan. Missing requirements must produce **new Section 1b.0 rows + Section 2 tasks** (or explicit **WAIVER**), not a silent PASS. |
| "I'll keep Section 0c in chat — the plan file is long enough" | **BLOCKED.** **`REVIEW_PASS`** requires machine anchors in-repo (**`<!-- FORGE-GATE:SECTION-0C-INVENTORY:v1 -->`** + **`<!-- FORGE-GATE:CODE-RECROSS:v1 -->`** per **`tech-plan-write-per-project` Section 1c**). **`verify_forge_task.py --strict-tech-plans`** fails otherwise. Chat is not auditable. |
| "Section 1b / Section 2 is too long — ask for a shorter plan" | **Wrong bar.** Length is **not** a defect when **`tech-plan-write-per-project` Section 0.0** applies — only **gaps**, **placeholders**, or **missing evidence** are. Prefer **more** Section 1b detail when surfaces are in scope. |
| "The matrix looked full — I skipped spot-checking paths" | **Section 1b.0** evidence paths can be wrong or stale. Self-review **must** recross-check a **sample** of cited `codebase/` → repo paths (and **all** paths for small plans) with **`Read` / `rg`** on the product repo — failures → **CHANGES** or **`SCAN_MISSING_OR_STALE`**. |

## Red Flags — STOP and Re-Review

- Plan has `TODO`, `TBD`, `FIXME`, or `...` anywhere in code blocks
- Task description says "similar to Task N" instead of showing actual code
- Import references a function that doesn't exist in the target file
- Test command is "verify it works" instead of an executable command
- Commit message is generic ("update code", "fix stuff", "misc changes")
- Performance requirement in spec has no corresponding benchmark in plan
- Plan references an API endpoint not defined in shared-dev-spec contracts
- **Missing Section 0 / Section 1b / Section 1c or wrong file order** (`tech-plan-write-per-project`): no **Section 0** planning doubt log (outcome table per **Section 0.3**; incl. **Section 0.2** interactive rounds when contracts are in play); no `Tech plan status:` under title; missing **Section 1b.0 PRD coverage matrix**, **1b.1–1b.6** plus **1b.1a** when search applies, **`#### 1b.5b`** when brokers/cache apply, **1c** revision log, or **web/app** missing **1b.4** / **synchronous API** work missing **1b.5**
- **Section 0 SPEC_ROLEPLAY** — Judgment questions answered with **`Frozen spec:`** + **H** and no **`USER:`** / role prefix per **Section 0.1** rule 3
- **Section 0 “questionnaire in the file”** — **Question** cells are multi-paragraph dumps or full Q&A pasted from chat into the repo instead of **one-line topic labels** + compact **Answer** outcomes (**`tech-plan-write-per-project` Section 0.1** rule 3 / **Section 0.3**) — **BLOCKED**
- **Section 1b.0 orphan rows or orphan Section 2 tasks** — PRD/spec case not mapped to tasks, or tasks not tied to **Section 1b.0** / spec (implicit coverage)
- **Requirement inventory not performed or not recorded** — Reviewer did not enumerate obligations from **`prd-locked.md`** + **`shared-dev-spec.md`** (+ other task sources) before judging PASS — **CHANGES** (run **Section 0c** process below) or **BLOCKED**
- **`REVIEW_PASS` without FORGE-GATE anchors** — Plan status is **`REVIEW_PASS`** but file lacks **`<!-- FORGE-GATE:SECTION-0C-INVENTORY:v1 -->`** and/or **`<!-- FORGE-GATE:CODE-RECROSS:v1 -->`** above the mandated tables/evidence — **CHANGES** (paste markers + tables into **`tech-plan-write-per-project` Section 1c**) or **BLOCKED**
- **PRD bullet drift (spot-check)** — Count of **material** bullets / numbered items under **`prd-locked.md`** success criteria, acceptance, NFRs, and edge-case language **materially exceeds** **Section 0c** inventory rows + **Section 1b.0** rows (e.g. ≥2 orphan PRD bullets with no inventory line and no **WAIVER**) — **CHANGES** or **BLOCKED** until each bullet maps or is waived with citation
- **`### 1b.0b` missing, placeholder, or inconsistent** — No **implementation at-a-glance** subsection; or a row marked **✓** in the surface table has **no** matching elaboration in **Section 1b.1** / **Section 1b.1a** / **Section 1b.5** / **`#### 1b.5b`**; or cross-repo dependency table contradicts **XALIGN** / sibling plans — **CHANGES**
- **PRD / acceptance / NFR gap** — A **material** line from **`prd-locked.md`** (success criteria, acceptance tests, NFRs, edge cases) or from the frozen spec has **no** matching **Section 1b.0** row **and** no **WAIVER** with citation — plan is incomplete until rows + tasks added or source amended via council
- **Scan ↔ code drift** — **Section 1b.0** cites a `codebase/` path that does not exist in the product repo, points at the wrong module for the stated behavior, or contradicts current registration/routes after recross-check — **CHANGES** (fix matrix + tasks) or escalate **`/scan`**
- **Product intent / PRD rationale missing (`tech-plan-write-per-project`)** — **Section 1b.0** **Why (rationale)** column empty, copies the requirement cell, or is only “per PRD”; **Section 1b.3** bullets lack a **`Why:`** clause; **Section 1b.4** / **Section 1b.5** / **`#### 1b.5b`** / **Section 1b.1a** tables omit **PRD / rationale** (or equivalent) columns where the write skill prescribes them; any **Section 2** task omits **`Traces to:`** or **`Rationale:`**, or **Rationale** only restates the task title — **CHANGES**
- **Touchpoint exploration missing or shallow (`### 1b.2a`)** — Subsection absent; appears **before** **Section 1b.5** / **`#### 1b.5b`**; **Y**/**PARTIAL** rows with **empty Evidence** or no repo paths/`rg` notes; **Exploration notes** missing or fewer than **3** bullets when the write skill’s **minimum bar** applies; bulk **N** without per-category justification — **CHANGES** or **BLOCKED**
- **Thin schema or API / message wire shapes (in-scope surfaces)** — **Section 1b.1** / **Section 1b.1a** / **Section 1b.5** / **`#### 1b.5b`** lack required persistence schema, search index definitions, **REST/GraphQL/SOAP/gRPC** examples, or **broker payloads** **where this repo owns that work** and the frozen contract already defines them
- **False applicability** — Invented persistence, search, **API operations**, or **broker destinations**, in a repo that should be **N/A** for those surfaces, or **blank** Section 1b.1 / **1b.1a** / **1b.5** / **`#### 1b.5b`** without the skill’s **explicit N/A** line
- **Data model delta contradicts migration tasks** — Delta says “none” but tasks add DDL, or delta lists tables with no matching migration task
- **Figma / `design_brain_paths` / Lovable locked in intake but 1b.4 empty or generic** — “See Figma” without node ids or brain paths, or no **`D<n>`** linkage from UI tasks
- **Missing Section 1b.5** when the repo implements or consumes a **locked synchronous API** (REST, GraphQL, SOAP, gRPC, …) for this task — No API↔component map
- **Section 1b.6 unknowns UNRESOLVED** but Section 2 tasks depend on them
- **Missing Section 1c** status banner, revision log, or **REVIEW_PASS** without a logged self-review round in the log
- **Multi-repo API drift:** consumer **operation keys** in this plan’s Section 1b.5 (e.g. `METHOD+path`, GraphQL operation name, SOAP QName, gRPC full method) do not match sibling `tech-plans/*.md` owner rows (after XALIGN should have fixed — still FAIL → BLOCKED)
- **`tech-plans/HUMAN_SIGNOFF.md` missing** after agent **PASS** + **XALIGN** — Human feedback / go-ahead phase skipped; pipeline must not advance to State 4b. STOP. Create signoff per **`docs/tech-plan-human-signoff.template.md`** (or **`waived`** with reason).
- **`SCAN_INCOMPLETE` / verify failure ignored:** `SCAN.json` exists but **`python3 tools/verify_scan_outputs.py …/codebase`** did not exit **0** (after retries per **`tech-plan-write-per-project`**) and the plan still cites brain paths as ground truth — STOP. Re-run **`/scan`** or mark paths **`OUT_OF_MANIFEST`** with evidence.
- **Cohort / segmentation via `SPEC_INFERENCE` in Section 0** — Product-visible segment, eligibility, or batch-exclusion decisions recorded with **`SPEC_INFERENCE`** and/or **Confidence H** without **`USER:`** / **`PO:`** / **`TL:`** / verbatim spec — **forbidden for `REVIEW_PASS`** per **`tech-plan-write-per-project` Section 0.1** rule 6. **CHANGES** until **`touchpoints/COHORT-AND-ADJACENCY.md`** exists with human-backed rows or **`WAIVER`**.
- **Missing adjacency / signal artifacts when PRD implies them** — Task lacks **`touchpoints/COHORT-AND-ADJACENCY.md`** or **`touchpoints/PRD-SIGNAL-REGISTRY.md`** (or documented waivers) while **`prd-locked.md`** **`pipeline_adjacency_notes`** or PRD text implies multi-pipeline or trust-line persistence — **CHANGES** or **BLOCKED** until council outputs or waivers land in brain.

**Any of these mean: BLOCKED. Fix before dispatch.**

---

## Verification Checklist

### 0c. PRD, all development sources, requirement inventory, and code recross-check (MUST — run first)

**Order:** Do **not** start with Section 2 task wording. **Sources → inventory → plan mapping → code evidence → fix gaps →** then proceed to **Section 0a** onward.

**Inputs to load (all that exist for this `task-id`):**
- `~/forge/brain/prds/<task-id>/prd-locked.md` — scope, success criteria, acceptance language, Q&A, NFRs, design locks, implementation reference
- `~/forge/brain/prds/<task-id>/shared-dev-spec.md` — requirements, contracts, acceptance
- **`prd-source-confluence.md`** or **`source-confluence.md`** (verbatim / mirror PRD body — **must** appear as Section 0c inventory rows when present; CI **`--strict-0c-inventory`** rejects **prd-locked-only** omission)
- **`touchpoints/*.md`** — cohort/adjacency, signal registry, etc. (**must** appear as inventory rows when any such files exist; cite paths like **`touchpoints/COHORT-AND-ADJACENCY.md`**)
- **`qa/manual-test-cases.csv`** — when it has data rows, inventory **must** cite it (substring **`manual-test-cases`** or **`qa/manual`**)
- Parity / delivery / design artifacts under the same task path when referenced by **`spec-freeze`** or the plan (e.g. `parity/checklist.md`, `design/README.md`)
- Any **explicit** “development source” files the plan’s header or Section 0 cites (treat as authoritative for trace)

**MUST produce in each `tech-plans/<repo>.md` (Section 1c — see `tech-plan-write-per-project` gate subsection). Chat summaries are supplementary evidence only, never a substitute for the file.**

1. **Requirement inventory table** — Place **`<!-- FORGE-GATE:SECTION-0C-INVENTORY:v1 -->`** on its own line **immediately above** the table. One row per **material** obligation: source id (e.g. `prd Q7`, `spec FR-3`, `acceptance A2`, **`prd` success-criterion bullet text**), short text, **Section 1b.0 row id or “MISSING”**, **Section 2 task id(s) or “MISSING”**, **evidence path** (`codebase/...` from plan or `NONE`), **PASS / GAP**. **Do not** collapse multiple distinct PRD acceptance bullets into one vague inventory row — each testable obligation deserves its own row or an explicit **WAIVER**.
2. **Bidirectional check** — Every **Section 1b.0** row must tie to ≥1 inventory line (or be explained as chore/tech-debt with Section 0 approval). Every Section 2 task must tie to ≥1 **Section 1b.0** row or inventory line — **no orphan tasks**.
3. **`### 1b.0b` cross-check** — **`tech-plan-write-per-project` Section 1b.0b** must exist. For **every** surface row marked **✓**, confirm the cited subsection(s) (**1b.1**, **1b.1a**, **1b.5**, **`#### 1b.5b`**, **1b.4**) contains **concrete** elaboration (not “see contract” only). **N/A** rows must name sibling **`tech-plans/*.md`** or spec section. The **cross-repo dependency** table must align with **XALIGN** (if present) — contradictions → **CHANGES** or **BLOCKED**.
3b. **`### 1b.2a` touchpoint pass** — Exists **after** **Section 1b.5** / **`#### 1b.5b`**. Spot-check **≥5** table rows (or all rows if fewer): **Y**/**PARTIAL** must have **Evidence** with real paths + tool notes; **Exploration notes** must contain **integration surprises**, not filler. Mismatch → **CHANGES**.
4. **Code recross-check** — Place **`<!-- FORGE-GATE:CODE-RECROSS:v1 -->`** on its own line **immediately above** the evidence block (table or bullet list). For each **Section 1b.0** evidence cell that cites `~/forge/brain/products/<slug>/codebase/` (or repo-relative path in tasks), verify against the **actual product repository**: file exists, symbol/route matches the plan’s claim (use **`Read`**, **`rg`**, or tests as appropriate). **Small plan:** check **every** cited path. **Large plan:** check **every** P0/P1 path + **random sample** of P2+ with min **5** paths or **20%** of rows (whichever is larger). Mismatch → **CHANGES** (update matrix + tasks) or **`SCAN_MISSING_OR_STALE`** + `/scan` recommendation.
5. **Close gaps in the plan (not only in review prose)** — For each **GAP** row: **edit** `tech-plans/<repo>.md` — add **Section 1b.0** matrix row(s), extend Section 1b tables if needed, and add/reorder **Section 2** tasks with scan-backed paths and contract shapes per **`tech-plan-write-per-project`**. If the **source** is wrong or incomplete, **BLOCKED** — council / spec amendment, do not invent requirements in the plan.
6. **Section 1c revision log** — When you applied fixes, append a row: requirement trace + code recheck, files touched, `GAP→CLOSED` summary.

**Checklist:**
- [ ] **`prd-locked.md`** read end-to-end; **success criteria / acceptance / NFR / edge** bullets each appear as their own inventory line (or explicit **WAIVER** with citation) — **no silent merge** of multiple PRD tests into one hand-wavy row
- [ ] **`shared-dev-spec.md`** read for this repo’s scope; contract sections reconciled with **Section 1b.5** / **`#### 1b.5b`** / **1b.1** / **1b.1a**
- [ ] **Inventory table** completed; **zero GAP** rows remain before declaring checklist **PASS** for this section (unless **BLOCKED** with owner)
- [ ] **Code recross-check** executed with evidence (paths checked, tool notes); drift corrected in-plan or escalated
- [ ] **Gaps fixed** in the markdown plan (not “will add later” in chat only)
- [ ] **`### 1b.0b` implementation at-a-glance** present; ✓ rows match elaborated **Section 1b.1** / **1b.1a** / **1b.5** / **`#### 1b.5b`** / **1b.4**; cross-repo table matches **XALIGN** / sibling plans
- [ ] **`### 1b.2a` touchpoint inventory** present **after** **Section 1b.5** / **`#### 1b.5b`**; **Exploration notes** exercised; **Y**/**PARTIAL** rows have evidence (spot-check per **Section 0c** step **3b**)

### 0a. Planning doubt log (`tech-plan-write-per-project` Section 0)

**Checklist:**
- [ ] **`## Section 0: Planning doubt log`** exists **before** Section 1b with the **outcome** doubt table (**Section 0.3**) — **no** required verbatim chat transcript subsection in the repo
- [ ] **Question** cells are **short topic labels** (one line each); **Answer** cells show **`USER:`** / **`PO:`** / **`TL:`** / spec quote / **BLOCKED** / **WAIVER** per **`tech-plan-write-per-project` Section 0.1** rule 3 — not walls of pasted chat
- [ ] **`No material doubts`** row only when trivial / confirmed in chat per **Section 0.1** rule 3; if used, **Answer** still follows prefix discipline where judgment was involved
- [ ] Doubt table has columns **Q# / Question / Answer / Confidence / Affects**
- [ ] **No artificial silence:** multiple substantive questions when the feature is complex — or one explicit row **`No material doubts`** when truly trivial
- [ ] **No high-impact `L` (low) confidence** without **BLOCKED**, **WAIVER**, or named owner + next step
- [ ] Answers tie to **Section 1b** rows and/or **Section 2** task ids — orphan answers are cleaned up
- [ ] **Binary — adjacency pack:** Per **`docs/adjacency-and-cohorts.md`**: no Section 0 **`SPEC_INFERENCE`**-only **cohort** rows when segmentation applies; **`touchpoints/COHORT-AND-ADJACENCY.md`** + **`PRD-SIGNAL-REGISTRY.md`** (or waivers) when required; **`discovery-adjacency.md`** or logged **`[ADJACENCY-SCAN] … SKIPPED`**; scan hits reflected in **`### 1b.2a`** or waived. Tables: **`docs/templates/adjacency-cohort-and-signals.template.md`**.

### 0. Parity & delivery context (task brain)

**Checklist:**
- [ ] **`~/forge/brain/prds/<task-id>/parity/`** satisfies **`spec-freeze`** Step 0 (**`external-plan.md`** OR completed **`checklist.md`** OR **`waiver.md`**) — not missing when the task is “serious” multi-repo delivery
- [ ] If **`parity/risk-register.md`** exists: rows consistent with **Section 1b.2a** and Section 2 — or **N/A** with reason (template Section C in **`docs/templates/adjacency-cohort-and-signals.template.md`**)
- [ ] If **`delivery-plan.md`** exists: tech plan **Section 1b.3** or tasks reference rollout / flag / pyramid items **only** as pointers — **interfaces** still match frozen spec

### 0d. Implementation readiness (artifacts — separate from human signoff)

**Purpose:** Agent-verifiable gates before **`REVIEW_PASS`** or conductor **State 4b** prep — does **not** replace **`HUMAN_SIGNOFF.md`**.

**Checklist (task-level paths under `~/forge/brain/prds/<task-id>/`):**
- [ ] **`prd-locked.md`** present; authoritative PRD body in brain (**`prd-source-confluence.md`**, wiki export, or equivalent per **`forge-intake-gate`**) **or** documented **`prd_body_waiver`** with owner + risk
- [ ] **`context-loaded.md`** present (from **`product-context-load`**)
- [ ] **`[DISCOVERY]`** + **`[ADJACENCY-SCAN]`** logged (or documented skip) per **`docs/adjacency-and-cohorts.md`**; cohort/signal touchpoints when required — same doc + Section 0a **Binary — adjacency pack**

### 0b. Implementation discovery & delivery locks (when `prd-locked.md` Q10 applies)

**Checklist:**
- [ ] **`implementation_reference`** from intake is echoed in the tech plan’s first page (branch / PR / explicit `none` + rationale) — not implied.
- [ ] **`delivery_mechanism`** and **`implementation_stack`** (or legacy **`ui_implementation_stack`**) from `prd-locked.md` appear verbatim or by reference — tasks must not contradict the locked authoritative boundary or stack.
- [ ] **Discovery evidence:** Plan states that **`git branch -a`** (or equivalent) was reviewed **or** links `discovery.md` / `context-loaded.md` git subsection from product-context-load — not “assumed greenfield.”
- [ ] **RED tests (see `forge-tdd`):** First failing tests must assert **observable behavior** at the chosen boundary (API contract, persistence, job output, or UI), not only registry/enum membership, when the feature is user-visible or Q10 applied.

### 1. Spec & PRD coverage (after Section 0c inventory)

**Checklist:**
- [ ] **Section 0c inventory is a subset check:** Every row from **Section 0c** is still **PASS** after deeper Section 1b review (no regressions)
- [ ] **Every material requirement in `shared-dev-spec.md` relevant to this repo** has at least one **Section 1b.0** row **and** Section 2 task(s) (or **N/A (other repo)** + pointer) — see **`tech-plan-write-per-project` Section 1b.0**
- [ ] **Every material line in `prd-locked.md`** (success criteria, locked Q&A, acceptance tests, NFRs) relevant to this repo is either in **Section 0c inventory** as **PASS** or **WAIVER** with citation — no “PRD is background” hand-waving

- [ ] **No orphan requirements**
  - No requirement is left without a task **and** Section 1b.0 trace
  - No task description is vague enough to accidentally cover something

- [ ] **Priority ordering respected**
  - If shared-dev-spec lists priorities (P0/P1/P2 or similar), tasks follow same order
  - Critical path tasks listed before optional-to-nice-to-have tasks

### 1b. Data model delta, reuse narrative, design trace, preamble (`tech-plan-write-per-project` Section 1b)

**Checklist:**
- [ ] **File layout:** `Tech plan status:` line immediately under `#` title; **Section 0** doubt log (**Section 0.2** when applicable; judgment rows must follow **Section 0.1** rule 3 — **`USER:`** / role prefix or **M** + **`SPEC_INFERENCE`**); **Section 1b** (**`1b.0` PRD↔scan matrix** with **Why (rationale)** column + bidirectional task ids, **`### 1b.0b`**, then **`1b.1` and `1b.1a`** each as table **or** skill-prescribed one-line N/A, then **`1b.2`**, **`1b.3`**, **`1b.4`–`1b.5`**, **`#### 1b.5b`** or its N/A when events/cache in scope, **`### 1b.2a`** touchpoint inventory **after** wire maps, then **`1b.6`**) and **Section 1c** appear **before Task 1**
- [ ] **Section 1b.0 completeness:** Every material **PRD / spec** requirement for this repo has a matrix row with **brain path evidence**, **non-empty Why (rationale)** (not a copy-paste of the requirement cell), and **Section 2** task ids (or explicit `N/A` + sibling repo); edge/negative/NFR rows exist or are **waived** with citation
- [ ] **Section 1b.3 trace bullets:** Each bullet includes **`Why:`** per **`tech-plan-write-per-project`**
- [ ] **`### 1b.0b`:** Surface ownership table + cross-repo deps + **3–8 sentence** implementation summary present; **no ✓** without matching detail in the cited subsection(s); **N/A** rows cite owner plan or spec
- [ ] **Schema & payload depth (where applicable):** If **Section 1b.1** has persistence delta rows, **store-native** schema (SQL / JSON / YAML / XML / DSL per **contract-schema-db**) is inlined or verbatim-contract; if **Section 1b.1** is the prescribed **one-line N/A**, no fabricated persistence shapes. Same for **Section 1b.1a** (index definition in contract format vs N/A). If **Section 1b.5** applies, **fenced** wire examples in the **locked format** (JSON, XML, SDL, `.proto`, …) for each **changed operation** — no `TBD` where the contract is already concrete; if **Section 1b.5** is **one-line N/A**, no forced API tables
- [ ] **Data model delta** is either a table with one row per CREATE/ALTER/DROP/index (or equivalent storage change), or an explicit one-line statement that this repo has **no** persistence/schema work — consistent with **shared-dev-spec** / DB contract
- [ ] **Cross-repo DDL:** If migrations run elsewhere, the delta says so; this plan does not silently own another service’s tables
- [ ] **Every migration/DDL task** in the plan has a matching row in the delta (or the repo correctly claims no persistence and has no such tasks)
- [ ] **Reuse vs net-new** lists concrete repo-relative paths for extended or called code; where a **brain scan** exists for this product, reuse bullets **align** with `codebase/` modules — or the plan flags **`SCAN_MISSING_OR_STALE`**; net-new surfaces are explicit — no implied reuse without a path
- [ ] **`### 1b.2b` first-session reconnaissance** present when **`tech-plan-write-per-project`** gate applies (net-new / multi-touchpoint / multiple **PARTIAL**); else **explicit one-line N/A** with why trivial; **≥5** minimum-read paths + **≥2** discovery commands are real (spot-check paths exist in product repo)
- [ ] **Trace to spec** maps requirements or contract headings to task numbers; combined with Section 1, no orphan requirements
- [ ] **1b.4 (web/app):** When **`design_new_work: yes`** or implementable design is locked (Figma keys, `design_brain_paths`, Lovable repo), the **design→UI table** lists anchors → deliverable → scan path or `NET_NEW` **and** the **PRD section / rationale** column is filled per write skill; **UI tasks** reference **`D<n>`** or cite **`design_waiver: prd_only`** plus PRD anchor — not chat-only Figma URLs
- [ ] **1b.5 (synchronous API):** If this repo serves or consumes a **locked** REST / GraphQL / SOAP / gRPC / … surface, **API↔consumer** tables exist for **that style**, include **PRD / rationale** (or equivalent) column per write skill, and **operation keys** match **`shared-dev-spec`** / contract artifacts; **N/A** line only when truly no synchronous API surface
- [ ] **`#### 1b.5b` (brokers/cache):** If **`contract-event-bus`** or **`contract-cache`** (or spec) assigns destinations to this repo, **tables + fenced** payload (JSON / XML / … per lock) or verbatim contract exist, **and** **PRD / rationale** column is filled per write skill; **N/A** only with citation — not prose-only destination names
- [ ] **`### 1b.2a` (touchpoints):** Full exploration table + **Exploration notes** per **`tech-plan-write-per-project`**; placement **after** **Section 1b.5** / **`#### 1b.5b`**; **Y**/**PARTIAL** rows have non-empty **Evidence**; notes surface real integration surprises (not generic filler)
- [ ] **1b.6:** Unknown table present; every row **RESOLVED** with evidence or **BLOCKED** with escalation — **no** dependency tasks on unresolved unknowns
- [ ] **1c:** `Tech plan status` + **revision log** present; latest log line records this review round and **PASS|CHANGES|BLOCKED**; if multi-repo **API or split message producer/consumer** plans exist, **XALIGN** noted **PASS** or open FAIL items are listed as blockers

### 1d. Cross-plan API & message consistency (run when ≥2 tech plans touch the same integration)

**When to skip:** Only one repo’s plan owns the whole **synchronous API** surface **and** no sibling consumes it in another plan **and** no **split** producer/consumer **message** plans — mark “N/A”.

**Checklist:**
- [ ] Load **all** `~/forge/brain/prds/<task-id>/tech-plans/*.md` that have **non-N/A** **Section 1b.5** or **`#### 1b.5b`**
- [ ] **REST:** **Consumer → owner:** every consumer `METHOD+path` appears on an owner row (same spelling, prefix/version). **Owner → consumer:** every new/changed endpoint has ≥1 consumer or explicit “no consumer / public / batch” with spec citation.
- [ ] **GraphQL / SOAP / gRPC:** same **consumer ↔ owner** discipline using **operation name**, **QName/SOAPAction**, or **`FullMethodName`** as the stable key — no drift across repos.
- [ ] **Messages:** producer plan **destination + payload version** fields match consumer plan (or cite the same **compat** subsection in spec).
- [ ] **Drift = BLOCKER** until plans revised and XALIGN re-run (`XALIGN PASS` in logs)

### 1e. Human tech-plan signoff (task-level — once per `task-id`)

**When to skip:** Never for full conductor **`State 4b`** entry — file must exist with **`approved`** or **`waived`**.

**Checklist:**
- [ ] **`~/forge/brain/prds/<task-id>/tech-plans/HUMAN_SIGNOFF.md`** present; frontmatter **`status`** is **`approved`** or **`waived`**
- [ ] **`repos_acknowledged`** covers all repo plans for this task (or waiver explains)
- [ ] **`[TECH-PLAN-HUMAN]`** log line can be emitted without contradicting the file

### 1f. Section 2 traceability & rationale (`tech-plan-write-per-project`)

**Checklist:**
- [ ] **Every** `## Task …` block begins with **`Traces to:`** (bullets naming `prd-locked.md` / `shared-dev-spec.md` / `contracts/*` ids) **and** **`Rationale:`** (1–4 sentences: why; which PRD obligation; prod/review failure if skipped)
- [ ] **Rationale** is not empty and does **not** only paraphrase the task title
- [ ] **`Traces to:`** ids are consistent with **Section 1b.0** rows and **Section 0c** inventory (spot-check ≥3 tasks)

### 2. Code Completeness

**Checklist:**
- [ ] **No "..." or "elided" code**
  - All code blocks are complete implementations
  - No "// ... rest of code" or "// ... other fields"
  - Example FAIL: `const obj = { foo: 1, ... };`
  - Example PASS: `const obj = { foo: 1, bar: 2, baz: 3 };`

- [ ] **No TODO or TODO(future) markers**
  - All code is ready to execute now
  - No "// TODO: implement validation" in code samples
  - Example FAIL: `// TODO: add error handling`
  - Example PASS: `if (!value) throw new Error("value required");`

- [ ] **No unresolved imports**
  - Every `import { X } from "module"` has X defined before use
  - No imports of functions that don't exist in the module
  - Example FAIL: `import { validateEmail } from "./helpers";` (if helpers.js doesn't export validateEmail)
  - Example PASS: `import { validateEmail } from "./helpers";` (helpers.js exports validateEmail)

- [ ] **All variables declared before use**
  - No forward references in code
  - All dependencies are defined in scope
  - Example FAIL: `return calculateTotal(items);` (calculateTotal not defined above)
  - Example PASS: `function calculateTotal(items) { ... } return calculateTotal(items);`

### 3. No Placeholder Code

**Checklist:**
- [ ] **Validation logic is complete, not stubbed**
  - Not: "add validation logic"
  - Is: Complete validation code with specific checks
  - Example FAIL: `// validate email address`
  - Example PASS: `const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/; if (!emailRegex.test(email)) throw new Error("Invalid email");`

- [ ] **Database queries are exact, not sketchy**
  - Not: "fetch from DB"
  - Is: Complete SQL query with table name, columns, WHERE clause
  - Example FAIL: `// query the user table`
  - Example PASS: `SELECT id, email, created_at FROM users WHERE status = 'active' AND deleted_at IS NULL;`

- [ ] **API calls are concrete, not abstract**
  - Not: "call the payment service"
  - Is: Exact endpoint, method, headers, payload
  - Example FAIL: `// contact payment API to charge card`
  - Example PASS: `POST /v1/charges { amount: 5000, currency: "usd", source: token }`

- [ ] **Configuration values are explicit, not variables**
  - Not: "set timeout to appropriate value"
  - Is: Exact timeout in seconds/ms
  - Example FAIL: `setTimeout(() => { ... }, TIMEOUT);`
  - Example PASS: `setTimeout(() => { ... }, 5000);` (5 seconds explicit)

- [ ] **Error messages are specific, not generic**
  - Not: "handle errors gracefully"
  - Is: Specific error message and recovery strategy
  - Example FAIL: `catch (e) { console.log("error"); }`
  - Example PASS: `catch (e) { logger.error("Failed to fetch user details", { userId, error: e.message }); res.status(500).json({ error: "Internal server error" }); }`

### 4. Test & Commit

**Checklist:**
- [ ] **Each task has a runnable test command**
  - Test is executable in the environment (npm test, python -m pytest, etc.)
  - Test actually validates the requirement
  - Example FAIL: `Test: "verify it works"`
  - Example PASS: `Test: npm test -- --testNamePattern="validateEmail rejects invalid formats"`

- [ ] **Each task has a commit message**
  - Follows conventional commits (feat:, fix:, test:, etc.)
  - References the requirement or task description
  - Is actionable and specific
  - Example FAIL: `git commit -m "update code"`
  - Example PASS: `git commit -m "feat: add email validation with regex pattern"`

- [ ] **Commit messages follow your project convention**
  - Check recent commits for style (git log --oneline)
  - Example: If repo uses "feat(auth): ...", replicate that format
  - Example FAIL: `chore: misc updates`
  - Example PASS: `feat(auth): add 2FA token caching with 300s TTL`

### 5. Output Format

**Checklist:**
- [ ] **Expected output is described for each test**
  - Exit code (0 = success, non-zero = failure)
  - stdout content (exact text or pattern)
  - File changes (which files created/modified, content)
  - Example:
    ```
    Test passes with:
    - Exit code: 0
    - stdout: "All tests passed: 12 passed, 0 failed"
    - Files created: src/validators/email.test.js
    ```

- [ ] **Failure modes are documented**
  - If test fails, what's the likely cause?
  - How does the error message guide troubleshooting?
  - Example:
    ```
    If test fails:
    - "validateEmail is not defined" → Function not exported from helpers.js
    - "regex pattern mismatch" → Email pattern needs update
    ```

- [ ] **Performance expectations are explicit**
  - If there's a performance requirement, test must measure it
  - Not: "ensure it's fast"
  - Is: "response time < 100ms" (measured in test)
  - Example:
    ```
    Test validates performance:
    - Query execution: < 50ms
    - API response: < 200ms p95
    ```

## Review Process

### Step 1: Load sources and plan
```bash
# Read PRD + frozen spec + plan (paths from task context — never skip PRD)
cat /path/to/prd-locked.md
cat /path/to/shared-dev-spec.md
cat /path/to/tech-plan.md
# Optional: parity, design, contracts cited by the plan
```

### Step 2: Checklist verification
Complete **Section 0c first** (requirement inventory + code recross-check + in-plan gap fixes). Then for each remaining section (**Section 0a** onward through Code Completeness, etc.):
1. Read the requirement
2. Search the tech plan for matching content
3. Mark as ✅ (pass) or ❌ (fail) with evidence
4. If fail: note the specific issue and line/section

### Step 3: Evidence Collection
For each failed check, collect:
- Line number or section in tech plan
- What it says (exact quote)
- What should be there instead
- Severity: BLOCKER (blocks dispatch) or WARNING (minor fix needed)

### Step 4: Decision (agent self-review)

- **APPROVED (agent):** **Section 0c** + **all** remaining checklist sections pass (no open **GAP** rows, no unresolved scan drift) → Update this plan file: **`Tech plan status: REVIEW_PASS`**, append **revision log** row with `self-review round=<n> result=PASS` (and **`XALIGN PASS`** if multi-repo **API or message** alignment ran). **This alone does not clear the Forge pipeline** — **Step 5 (human gate)** is still required before **State 4b** (eval / RED).
- **CHANGES REQUESTED:** Some warnings → Set plan **`REVIEW_CHANGES`** / **`DRAFT`**, append revision log with **failed section references**, **edit the tech plan** (not only mental note), re-run this skill from Step 1 — **max 3 rounds** per repo then escalate.
- **BLOCKED:** Any blockers → Cannot dispatch until fixed; log **`result=BLOCKED`** in revision log and escalate with evidence.

**Feedback loop (mandatory):** **CHANGES** or **BLOCKED** must **never** skip straight to dev-implementer without a **new plan revision** (`Rev`++) and a **re-review**. Treat “approved in chat” without file updates as **invalid**.

### Step 5: Human tech-plan gate (orchestration handoff)

**Checklist:**
- [ ] **`~/forge/brain/prds/<task-id>/tech-plans/HUMAN_SIGNOFF.md`** exists and matches **`docs/tech-plan-human-signoff.template.md`**
- [ ] **`status`** is **`approved`** or **`waived`** (with reason) — not left blank
- [ ] **`repos_acknowledged`** lists every `tech-plans/<repo>.md` stem for this task (or signoff explains omission)
- [ ] If **`changes_requested`**: plans were edited after this file’s prior version — do not treat pipeline as clear until a **new** signoff shows **`approved`** or **`waived`**
- [ ] Conductor logs **`[TECH-PLAN-HUMAN]`** consistent with the file

### Step 6: Final pipeline readiness (per repo + task)

- **APPROVED (full):** **Step 4** = **APPROVED (agent)** for this repo’s plan **and** **Step 5** satisfied at **task** level (**`HUMAN_SIGNOFF.md`** applies once per task, not per repo file) → Conductor may proceed to **State 4b** for this task once **all** repos + human gate + logs align per **`conductor-orchestrate`**.

## Common Patterns to Check

### Example: Cache TTL
**Spec says:** "Cache 2FA codes for 5 minutes"
**Plan says:** "Add Redis key with TTL"
**Check:**
- ❌ TTL value not specified (BLOCKER)
- Fix: "Redis SET key value EX 300" (300 = 300 seconds = 5 minutes)

### Example: Soft Delete
**Spec says:** "Soft-delete users when account closed"
**Plan has SQL:** `UPDATE users SET deleted_at = NOW() WHERE id = ?`
**Check:**
- ✅ No hard DELETE (good)
- ✅ Timestamp is set (good)
- ❌ Query doesn't check for existing delete (WARNING)
- Fix: Add `AND deleted_at IS NULL` or handle idempotency

### Example: API Contract
**Spec says:** "GET /users/:id returns user object with email, created_at, status"
**Plan says:** "Implement GET endpoint for user details"
**Check:**
- ❌ Fields not specified (BLOCKER)
- ❌ Error cases not documented (BLOCKER)
- ❌ 404 vs 403 handling not clear (BLOCKER)
- Fix: Exact response shape and error codes

## Output Template

When submitting review results:

```
## Tech Plan Self-Review: [Project Name] - [Task Name]

### Status: ✅ APPROVED (agent) / ⚠️ CHANGES REQUESTED / ❌ BLOCKED  
### Human gate: ⏳ PENDING / ✅ APPROVED or WAIVED (see `tech-plans/HUMAN_SIGNOFF.md`)

### Verification Summary
- [✅/❌] Section 0c: PRD + spec inventory (per-bullet, not hand-waved), **`### 1b.0b`** cross-check, bidirectional Section 1b.0 ↔ tasks, code recross-check, gaps closed in-plan
- [✅/❌] Spec & PRD coverage (Section 1): No orphan requirements vs sources
- [✅/❌] Section 0a–Section 1c: **Section 0** outcome doubt log + Section 1b (**Why**, **PRD / rationale**, **`### 1b.2a` touchpoints**) + unknowns + review log (+ XALIGN when applicable)
- [✅/❌] Section 1f: Section 2 **Traces to** + **Rationale** on every task
- [✅/❌] Section 1e Human signoff file + log (`HUMAN_SIGNOFF.md`, `[TECH-PLAN-HUMAN]`)
- [✅/❌] Code Completeness: No placeholders
- [✅/❌] No Placeholder Code: All implementations concrete
- [✅/❌] Test & Commit: All tests runnable, commits clear
- [✅/❌] Output Format: Expected outputs documented

### Issues Found
1. [Line X] Code completeness issue: "..." found in [section]
2. [Section Y] Placeholder code: "TODO" found, needs full implementation
3. [Task Z] Missing test command

### Recommendations
- (if **APPROVED (agent)**) Update plans + logs; obtain **`tech-plans/HUMAN_SIGNOFF.md`** then **`[TECH-PLAN-HUMAN]`** — only then State 4b / dispatch
- (if CHANGES REQUESTED) Fix issues above and resubmit
- (if BLOCKED) Cannot proceed until blockers resolved

### Evidence
- Spec: [shared-dev-spec reference]
- Plan: [tech-plan reference]
- Checked: [timestamp]
```

## Edge Cases & Fallback Paths

### Edge Case 1: Placeholder is discovered during self-review

**Diagnosis**: Tech plan includes a task with placeholder like "TODO: wait for API docs" or "Use TBD auth mechanism".

**Response**:
- **Flag as BLOCKER**: Placeholders block deployment.
- **Escalate**: "Plan contains [N] placeholders. Cannot dispatch until resolved: [list details]."
- **Recovery options**:
  1. Remove placeholder task and reduce scope.
  2. Replace placeholder with concrete implementation (possibly temporary workaround).
  3. Add task to unblock placeholder (e.g., "Request API docs from vendor").
- **Track resolution**: When placeholder is resolved, re-run self-review.

**Escalation**: BLOCKED - Placeholders must be resolved. Escalate to tech-plan-write-per-project to fix.

---

### Edge Case 2: Scope is too broad (tasks cannot realistically be completed in sprint)

**Diagnosis**: Self-review calculates total task time: sum of all 2-5 minute tasks = 47 minutes of implementation. But spec is complex, review will add time. Scope may not fit in available sprint time.

**Response**:
- **Calculate realistic timeline**: Estimate = task time + review buffer (20-30%) + unknowns (10-15%).
- **Realistic estimate**: 47 min tasks + 15 min buffer + 5 min unknowns = ~67 minutes. 
- **If fits sprint**: Proceed.
- **If exceeds available time**: Escalate: "Estimated implementation time: [X] min. Available time: [Y] min. Scope is [over/under]."
- **Recovery**:
  1. Reduce scope: Remove lower-priority tasks.
  2. Extend timeline: Ask stakeholders if deadline can slip.
  3. Add resources: Can another developer help?

**Escalation**: NEEDS_TIMELINE_ADJUSTMENT - Scope vs. time mismatch must be resolved by stakeholders.

---

### Edge Case 3: Dependencies are missing (Task A depends on Task B from different repo, not captured)

**Diagnosis**: Web project plan has Task 5: "Integrate with API endpoint". But that endpoint is defined in backend plan's Task 3. Dependency is implicit, not documented.

**Response**:
- **Detect**: Cross-check all tasks against shared-dev-spec. If a task references work from another repo, mark as dependent.
- **Document explicitly**: "Task 5 (Web) depends on: backend-api Task 3. Cannot start until backend Task 3 is done."
- **Sequencing**: Ensure backend Task 3 is scheduled before web Task 5 in dispatch phase.
- **Add blocker check**: "If backend Task 3 blocked, web Task 5 automatically blocked."

**Escalation**: NEEDS_SEQUENCING - If dependencies are complex, escalate to conductor to verify correct task ordering.

---

### Edge Case 4: Plan conflicts with other repo's plan (simultaneous writes to shared resource)

**Diagnosis**: Frontend plan says "Task 2: Modify shared schema migration file". Backend plan also says "Task 3: Modify shared schema migration file". Both repos try to edit the same file simultaneously.

**Response**:
- **Detect**: Cross-repo plan validation. Scan all plans for conflicting files.
- **Resolution**:
  1. **Merge tasks**: Combine into one schema migration task (backend owns it, frontend waits for it).
  2. **Split file**: Create separate migration files (backend_migration_v1, frontend_migration_v1).
  3. **Sequence**: Backend does schema migration, frontend does schema usage changes after.
- **Document**: "Shared resource: [file]. Owner: backend. Frontend waits for completion before Task [X]."

**Escalation**: NEEDS_COORDINATION - If repos must edit same file, escalate to conductor to coordinate task sequencing.

---

### Edge Case 5: Tech Plan Is Correct but Spec Has Changed Since Plan Was Written

**Diagnosis**: Tech plan was written on day 1. On day 3, Council amended the shared-dev-spec (a cache contract changed, an API field was renamed). The tech plan still references the old field names and the old cache contract. The plan is now stale.

**Response**:
- **Detect**: Before self-review, check the spec's last-modified timestamp against the plan's creation timestamp. If spec is newer, diff carefully.
- **Reconcile**: For each changed spec field, find the task that implements it and update the task's code, file path, and test assertions
- **Do NOT** approve a plan against a stale spec — implementation against the wrong spec creates bugs that survive code review
- **Document**: Note in the plan header: "Reconciled with spec amendment [date]: changed X → Y in tasks 3, 7, and 9"

**Escalation**: NEEDS_CONTEXT - If the spec change is large enough that more than 30% of tasks need updating, the plan should be rewritten rather than patched. Escalate to the dreamer to confirm scope before rewriting.

---

## Notes for Dev-Implementers

- This skill is a gate: tech plans must pass self-review before dispatch
- Blockers must be fixed before proceeding
- Warnings can be fixed during implementation if agreed by implementer
- Clear, complete plans reduce back-and-forth during development
- Exact specs + exact tests = faster implementation + fewer bugs

## Checklist

Before approving a tech plan for dispatch:

- [ ] Every spec requirement in shared-dev-spec is covered by at least one task
- [ ] No `TODO`, `TBD`, `FIXME`, or `...` in any code block
- [ ] All tasks have exact file paths (not vague "add to the service")
- [ ] All bash commands are complete with flags, paths, and environment variables
- [ ] Each task has a concrete test command and expected output (not "verify it works")
- [ ] Commit messages are specific (not "update code" or "misc changes")
- [ ] Tasks are ordered: test task before implementation task for each feature (TDD)

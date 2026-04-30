---
name: qa-manual-test-cases-from-prd
description: "WHEN: You need atomic manual QA test cases in CSV from a PRD plus optional existing suite and knowledge base, with estimation, reuse/deprecation tracking, review, and a final report — any product, any TMS."
type: rigid
requires: [qa-prd-analysis, brain-read, brain-write]
version: 1.4.3
preamble-tier: 3
triggers:
  - "generate test cases"
  - "QA test cases from PRD"
  - "write manual tests"
  - "create QA CSV"
allowed-tools:
  - Bash
  - Write
  - AskUserQuestion
  - mcp__*
---

# Manual QA Test Cases from PRD (CSV)

## Human input (all hosts)

**`AskUserQuestion`** in **`allowed-tools`** is canonical; map per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** on every IDE (sample/count approvals, branch choices). See **`using-forge`** **Interactive human input**.

**Cross-cutting assistant dialogue:** **`docs/forge-one-step-horizon.md`** — **`using-forge`** **Multi-question elicitation** items **4–8**.

**HARD-GATE:** Do not append production CSV rows until **Step 3 (samples) is approved**; do not ship the final report until **Step 7 (count) is approved**. When **`forge_qa_csv_before_eval: true`**, do not author **`eval/*.yaml`** or start feature **TDD** until this skill’s CSV path is approved and logged per **`conductor-orchestrate`**.

---

Turn analyzed requirements into **atomic**, **traceable** manual test cases (default: CSV). Plug-and-play: you supply **base URLs**, **test management export or MCP**, and **output path**; the workflow does not assume a specific vendor beyond optional tool hooks.

**Not the same as Forge eval YAML:** Automated multi-surface eval uses **`eval-scenario-format`** (YAML drivers). This skill produces **human/manual (and automation-ready) step lists** in **CSV** for QA backlogs, Jira/Xray/TestRail import, or spreadsheets.

## Position in the delivery pipeline (why timing matters)

Approved manual test cases are **acceptance inventory**: they define *what* must pass before the slice is real.

**Target order (downstream of tech plan + locked `shared-dev-spec.md`, upstream of code and eval execution):**

1. **`qa-prd-analysis`** → **`qa-manual-test-cases-from-prd`** through **Step 7 count approval** and finalized **`manual-test-cases.csv`** (atomic rows with **Source**).
2. **`eval-translate-english`** + **`eval-scenario-format`** — author **`eval/*.yaml`** so each scenario **names or comments traceability** to CSV **Id** rows where applicable (same user journeys, automatable drivers).
3. **`forge-tdd` RED** — repo automated tests encode acceptance from **tech plan + CSV rows** (one RED test per critical row or grouped by journey per team convention, but must be **traceable**).
4. **P4.1 implementation (GREEN)** — production code only after RED exists.
5. **P4.4 eval** — **real execution** of the YAML against the stack; results should align with the same acceptance inventory.

**HARD-GATE (team opt-in):** If `~/forge/brain/products/<slug>/product.md` sets **`forge_qa_csv_before_eval: true`** for this product, **`conductor-orchestrate` State 4b** requires a logged **`[P4.0-QA-CSV]`** *before* **`[P4.0-EVAL-YAML]`** or **`[P4.0-SEMANTIC-EVAL]`**. Without that, do not author machine-eval artifacts or dispatch feature work.

**Anti-pattern:** Writing eval YAML or TDD tests **only** from prose tech plans while ignoring an in-flight QA CSV for the same task — you will double-specify and drift.

**Prerequisite order (agents):** This skill is **step 3** of **`qa-write-scenarios` Step −1** (`prd-locked` → **`qa-prd-analysis`** → **this CSV / waiver** → eval YAML). Upstream **`qa-prd-analysis`** must complete **`using-forge`** **Multi-question elicitation** for coverage (Step 0.5 — see **`qa-prd-analysis`**). **Do not** open with a **blocking interactive prompt** (**`AskUserQuestion`** / host equivalent per **`using-forge`**) about YAML-before-CSV or eval paths while **`prd-locked.md`** or valid **`qa-analysis.md`** (post–Step 0.5 chat) is missing.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "One big end-to-end CSV row covers the feature" | Violates atomicity; failures are un-diagnosable; automation flakes. |
| "I'll skip samples and user approval — we're in a hurry" | Format drift and wrong assumptions multiply rework cost past any “saved” time. |
| "Expected result only in the Description column" | Breaks import pipelines and double-entry rules; always separate column **and** appendix per format. |
| "Source column is optional" | Traceability to PRD vs KB vs regression is lost; audits fail. |
| "Deprecation in Jira can wait" | Stale tests run in regression and hide real failures; document at least in report, execute TMS updates when your org uses them. |
| "XRAY/Atlassian MCP unavailable — I'll guess prior cases" | STOP. Use exports the user provides or block until Source 2 exists. |
| "Step 7 count review is bureaucratic" | Estimation vs actual drift catches systematic under-coverage; skipping it ships silent gaps. |
| "We'll publish the CSV after developers start" | When **`forge_qa_csv_before_eval: true`**, the CSV is **before** eval YAML and **before** TDD feature work — late CSV means rework and eval that does not match what RED asserted. |
| "`qa-analysis.md` is enough — I don't need prd-locked / tech plans / contracts again" | **`qa-analysis.md` is an index and interrogation record, not a substitute for primary sources.** Rows must trace to **prd-locked**, **shared-dev-spec**, **tech-plans**, and **contracts** where those contain the actual acceptance rules, routes, and edge cases. Re-load the full task bundle before Step 5 (see Step 1b). |
| "User hasn't locked PRD — I'll ask about eval YAML / waiver anyway" | **Violates Step −1.** Fix **`prd-locked`** (**`/intake`**) and **`qa-prd-analysis`** first; this skill comes **after** those. |
| "Summary + Expected Result are enough — testers know how to execute" | **Invalid.** **Description** must be **numbered action steps** (`1.` … `2.` …) per field rules — **not** a vague paragraph. **Summary** is one line; **execution lives in Description** (+ **Preconditions** for setup). |
| "I'll pipe rows from a throwaway script without validating steps and preconditions" | **Invalid.** Scripts often emit **thin** rows; every row must pass **Description** / **Preconditions** HARD-GATEs **before** samples approval. **Never** commit **`eval/_generate*.py`**-style junk under **`qa/`** as the CSV source of truth. |
| "Preconditions can be empty / TBD — we'll fill later" | **Invalid** for any case that is **not** default anonymous happy path. Undocumented setup → **`CONTEXT_GAP`** or **blocking** user clarification **before** final rows — see **Preconditions — explicit coverage**. |
| "`coverage_depth: comprehensive` but I'll ship an 8-column CSV with no **Preconditions** header — setup can live only in Description" | **Invalid.** **Preconditions column — mandatory for comprehensive** — comprehensive runs **must** expose setup in its own column; burying setup only inside **Description** fails review and hides the **highest-signal** field. |
| "I'll leave **Preconditions** cells **blank** for default happy path when the column exists" | **Invalid.** Use **`None`** or **`N/A — default happy path`** — **blank** is ambiguous vs forgotten setup (**Field rules**). |
| "Summary is a cryptic title — EQ low FRS, BVA edge, PRD14 — testers know what we mean" | **Invalid.** **Summary** must be **plain English** understandable by a **QA reader who did not author the PRD** within **one or two reads** — see **Summary — readability (HARD-GATE)**. Internal codes belong expanded once + **`terminology.md`** alignment. |
| "I'll ship 50–80 one-line summaries — row count proves coverage" | **Invalid.** **High count of unreadable rows is worse than fewer complete rows.** Coverage is proven by **traceability + executable Description**, not title spam. Inflate count without steps → rework and hides real gaps. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
EACH TEST CASE TESTS EXACTLY ONE VERIFIABLE OUTCOME; EVERY ROW HAS A SOURCE (PRD | KB | REGRESSION | …); BEFORE STEP 5, RE-LOAD THE FULL REQUIREMENT BUNDLE (STEP 1b) — NOT JUST qa-analysis.md; EVERY NEW ROW MUST BE ANCHORABLE TO A PRD BULLET, SPEC SECTION, TECH-PLAN TASK, OR CONTRACT CLAUSE; DO NOT APPEND ROWS TO THE CSV UNTIL STEP 3 (SAMPLES) IS APPROVED — AND NEVER SKIP STEP 7 COUNT APPROVAL BEFORE THE FINAL REPORT (STEP 8). FOR TEAMS THAT OPT IN (forge_qa_csv_before_eval: true), THIS CSV MUST BE APPROVED BEFORE MACHINE-EVAL ARTIFACTS (DECLARATIVE YAML OR SEMANTIC CSV/MANIFEST) AND BEFORE TDD FEATURE WORK SO RED TESTS AND P4.4 EXECUTION TRACE TO THE SAME ACCEPTANCE SET.
DESCRIPTION IS NEVER “PLAIN PROSE SUMMARY.” UI/API CASES: DESCRIPTION MUST CONTAIN NUMBERED STEPS (1. Navigate… OR 1. Call …); PRECONDITIONS EXPLICIT (COLUMN OR “Preconditions:” LEAD-IN) WHEN STATE ≠ DEFAULT HAPPY PATH; SUMMARY+EXPECTED ALONE WITHOUT EXECUTABLE STEPS IS REJECTED AT SAMPLE REVIEW.
WHEN qa-analysis.md HAS coverage_depth: comprehensive, CSV HEADER MUST INCLUDE “Preconditions” (AND “Source”) — NOT 8-COLUMN-ONLY; PRECONDITIONS CELL PER ROW = EXPLICIT SETUP OR “None” / “N/A — default happy path”, NEVER BLANK SILENCE.
SUMMARY MUST READ AS PLAIN ENGLISH TO A NEW QA READER (NO ACRONYM SOUP / INTERNAL TICKET SHORTHAND WITHOUT DEFINITION); A LIST OF CUTE TITLES WITHOUT NUMBERED DESCRIPTION IS NOT A TEST SUITE — FIX BEFORE STEP 3 APPROVAL.
```

## Red Flags — STOP

- **`qa-prd-analysis` output missing or stale** — STOP. Run or refresh **`qa-prd-analysis`** first.
- **Proceeding to Step 5 without Step 3 approval** — STOP.
- **CSV rows without all 8 required fields** — STOP. Fix or split rows.
- **First step of Description is not navigation** (when UI applies) — STOP. Fix platform URLs from config.
- **Multiple verification points in one Expected Result** — STOP. Split into atomic cases.
- **Deprecation labels applied in TMS without user sign-off on uncertain cases** — STOP. List for review first.
- **Generating Step 5 rows from memory or from `qa-analysis.md` alone** — STOP. Complete **Step 1b** (fresh read of prd-locked, shared-dev-spec, tech-plans, contracts, scan index when present).
- **`qa-analysis.md`** has **`coverage_depth: comprehensive`** (or equivalent maximum-coverage commitment in body) **but** the CSV uses **only** the **8 base columns** — STOP. Add **`Source`** + **`Preconditions`** columns per **Preconditions column — mandatory for comprehensive**.
- **`Preconditions`** column **present** but **blank** cells on rows that are **not** obviously default-only — STOP. Use explicit **`None`** / **`N/A — default happy path`** or fill setup; **blank ≠ documented default**.

## Configuration (set once per task — ask if missing)

| Token | Meaning | Example |
|---|---|---|
| `<TASK_ID>` | Forge / task folder | `feature-auth-mfa` |
| `<PRD_SOURCE>` | PRD location | wiki URL, PDF path, markdown |
| `<EXISTING_TESTS>` | Prior cases | Xray folder via MCP, TestRail export CSV, or “none” |
| `<KB_PATH>` | Internal rules/docs | `@docs/recruiter` style path or “none” |
| `<WEB_BASE_URL>` | Default web entry | from `product.md` or user |
| `<ADMIN_BASE_URL>` | Optional | user-supplied |
| `<OUTPUT_CSV>` | Writable output | default: `~/forge/brain/prds/<TASK_ID>/qa/manual-test-cases.csv` |
| `<VALIDATION_CODE>` | Team secret to prove rules were read | e.g. `TESTCASE_FORMAT_<TEAM>` — user provides |

**MCP tools (optional):** If the host provides Atlassian, Xray, or other TMS MCPs, read the **live tool schema** before calling. If MCPs are absent, require **exported** JSON/CSV from the user for `<EXISTING_TESTS>`.

## Required CSV Fields (8 columns + optionals)

**Base** header row **exactly** (8 columns — works with strict TMS importers):

```text
"Id","Platform","Summary","Description","Expected Result","Automatable","Type","Feature Categorization"
```

**Recommended** ninth column:

```text
"Source"
```

**Source** values (constrained): `PRD` | `KB` | `REGRESSION` | `HYBRID` (document in Summary why hybrid).

**Optional** tenth column (use for **all** rows in a file when you use it — **do not** mix blank and filled inconsistently without reason):

```text
"Preconditions"
```

- If **`Preconditions`** is **absent** as a column: put preconditions in the **Description** cell only (see **Description** row below).
- If **`Preconditions`** is **present**: that cell holds **setup state**; **Description** is **numbered action steps only** (start with `1. Navigate…` for UI). Do **not** duplicate the full precondition paragraph in both columns. Use `None` (or `N/A — default happy path`) when the case assumes only baseline authenticated user / default config with **no** special seed, flags, or prior workflow. **Forbidden:** **blank** Preconditions when the column exists — empty reads as *unknown*, not *default*; always write **`None`** / **`N/A — default happy path`** for true baseline-only cases.

### Preconditions column — mandatory for comprehensive (HARD-GATE)

When **`~/forge/brain/prds/<task-id>/qa/qa-analysis.md`** frontmatter has **`coverage_depth: comprehensive`**, **or** the interrogation body commits this task to **full / maximum / matrix** coverage (same intent as comprehensive), the CSV **must** use a header that includes **`"Source"`** and **`"Preconditions"`** — i.e. **not** an **8-column-only** file. Setup is the **highest-signal** field for reproducibility; it must be **scannable** without parsing long **Description** cells.

**Lean / non-comprehensive runs:** The **`Preconditions`** column may remain **omitted** if the team chose a minimal header; non-default setup **still** must appear via **`Preconditions:`** lead-in at the start of **Description** (**Field rules**).

**Reviewer signal:** Step 3 **samples** for comprehensive tasks **must** already show the **full header** (with **`Preconditions`**). If samples use **only** eight columns while **`coverage_depth: comprehensive`**, **STOP** — fix header **before** bulk Step 5.

### Preconditions — explicit coverage (HARD-GATE)

**Every** test case must make setup **executable** by a human or automation team. Preconditions are **not** optional when the verification depends on anything other than “default user on default stack.”

| Precondition domain | Examples | When unclear |
|---|---|---|
| **Identity / session** | Role, permissions, account tier, org | **Ask** which persona applies; do not invent credentials. |
| **Data / seed** | DB rows, CMS content, queue depth, “user has already completed step X” | **Ask** seed recipe, fixture id, or admin path — or record **`CONTEXT_GAP`** if unknown. |
| **Feature flags / config** | Flag on/off, kill switch, A/B bucket | **Ask** default for this QA cycle if PRD does not lock it. |
| **Time / scheduling** | Business hours, expiry windows, cron-relative state | **Ask** how testers should simulate or freeze time. |
| **External integrations** | Partner sandbox, webhook replay, third-party error injection | **Ask** stub vs live and **environment** (staging URL scope). |
| **Prior workflow** | “Order already placed,” “invoice overdue” | State as precondition steps or seed — **split** into a separate case if the setup is itself a full journey. |

**Human clarification (blocking):** If the PRD or brain artifacts **do not** specify how to reach the starting state (e.g. “suspended recruiter” with no suspension mechanism documented), use **`AskUserQuestion`** / **`AskQuestion`** / **numbered options + stop** per **`using-forge`** — **before** writing final CSV rows that assume that state. **Forbidden:** silent placeholders like *“appropriate test user”* without definition agreed in chat or KB.

### Where test data lives (no extra column in the 8-column base)

The **8 required columns** do not include a separate **“Test data”** field — data is **distributed** so importers stay standard:

| Kind of data | Where it goes |
|---|---|
| **Roles, accounts, tokens, org/tenant** | **`Preconditions`** column **or** `Preconditions: …` lead-in at start of **Description** |
| **Seeded entities** (user id, job id, fixture name, queue depth) | **Preconditions** (how seed was created or **CONTEXT_GAP** if unknown) |
| **Feature flags / config / environment** | **Preconditions** + **Platform** + step **1** URL scope |
| **Inputs during the flow** (strings typed, files uploaded, API JSON bodies) | **Inside numbered Description steps** — e.g. `3. Enter subject line "Suspicious pattern — review"` or `2. POST body {"recruiterId":"..."}` |
| **Expected payloads / error codes** | **Expected Result** + final step assertion text |

If an agent only fills **Summary** and **Expected Result**, **Description** is **missing test steps and input data** — that violates this skill.

### Field rules

| Field | Rule |
|---|---|
| **Id** | Unique: `TC-<FeatureSlug>-<NNN>` (use your project’s slug, not a fixed vendor prefix). |
| **Platform** | One of: `Web`, `iOS`, `Android`, `API`, or project-defined labels — **consistent** within the file. |
| **Summary** | Single-sentence purpose; one verification focus. **Readability (HARD-GATE):** A **manual tester or reviewer** who understands the product area but **not** your team’s Slack shorthand must grasp **what** is being exercised **without** opening five other rows. Use **full phrases**, not acronym piles (**EQ**, **FRS**, **BVA**, **PRD14**) unless you **spell out** on first use in that Summary or rely on **canonical names** from **`~/forge/brain/prds/<task-id>/terminology.md`** ([docs/terminology-review.md](../../docs/terminology-review.md)). **Forbidden:** titles that read like **internal smoke codes** (*SMOKE: GET …* alone with no user-visible intent). **Summary complements Description** — if Summary is vague, the row fails review even when Description exists. |
| **Preconditions** (optional column **unless comprehensive**) | **If `coverage_depth: comprehensive`** in **`qa-analysis.md`**: column is **required** in header — see **Preconditions column — mandatory for comprehensive**. When present: concise setup — auth + data + flags + environment references. Must align with **Description** steps. **No blank cells** when the column exists — use **`None`** / **`N/A — default happy path`** for true default-only cases. |
| **Description** | **Numbered** step list — **this is where execution lives** (not only Summary). **HARD-GATE:** For UI, step **1** must be navigation: `1. Navigate to <platform base URL> …` using configured URLs. **Forbidden:** a single sentence like *“User verifies reverification flow”* with **no** `1.` / `2.` steps — that row is **not** a test case. **If no `Preconditions` column:** when the case depends on non-default **account/data/flag** state, begin the cell with `Preconditions: <explicit setup>.` then `1. Navigate…`. Map screens/selectors to **`qa-prd-analysis` Q8** / design when applicable. No line breaks inside the CSV cell; use spaces between steps. **Append** at end: `EXPECTED RESULT: <same text as Expected Result column>`. |
| **Expected Result** | **One** outcome; must **match** the `EXPECTED RESULT:` appendix in Description character-for-character. |
| **Automatable** | `Yes` \| `No` \| `Partial`. |
| **Type** | e.g. `Positive`, `Negative`, `Edge Case`, `API`, `Security`, `Performance`, `Smoke`, `Sanity`, `Regression`, … |
| **Feature Categorization** | Module / epic name for filtering imports. |
| **Source** (optional column) | `PRD` \| `KB` \| `REGRESSION` \| `HYBRID` — when column present, **every** data row must set it. |

**Full header with both optionals** (when team wants Source + Preconditions separated):

```text
"Id","Platform","Summary","Description","Expected Result","Automatable","Type","Feature Categorization","Source","Preconditions"
```

**Comprehensive / maximum-coverage runs:** **`Source` + `Preconditions`** in the header are **mandatory** (not merely preferred) when **`coverage_depth: comprehensive`** — see **Preconditions column — mandatory for comprehensive**. **Preconditions** holds seeds, accounts, flags; **Description** stays **numbered steps** + **`EXPECTED RESULT:`** appendix.

### CSV mechanics

- Entire row double-quoted; commas between fields.
- **Single line per test case** (no embedded newlines in fields).

## Atomicity (non-negotiable)

- **One test case = one primary verification.**
- Split when: multiple unrelated assertions, multiple integrations independently testable, multiple error classes, or multiple user goals.

### Row count vs usefulness (non-negotiable)

- **A large CSV full of one-line Summary titles** (even if unique) **without** numbered **Description** steps and clear **Expected Result** is **not** acceptable output — it wastes reviewers’ time and **cannot** be executed.
- **Do not optimize for headline count** when that means **stub titles**. **Do** produce **large** row counts when **`qa-analysis.md`** (and the PRD/tech-plan bundle) calls for **comprehensive** coverage across **many** surfaces, types, and routes — there is **no Forge maximum** (not 100, not 200). **500+** or **1000+** atomic rows can be **correct** for a large multi-surface slice if each row meets **Field rules** and maps to the coverage matrix.
- **Under-shipping** because the assistant “doesn’t want too many rows” or hits **soft token anxiety** is **invalid** when the user asked for **maximum** coverage and **`coverage_depth: comprehensive`** — **batch** writes, work **per feature area**, reload Step 1b, then continue until the matrix is satisfied or gaps are explicit (**CONTEXT_GAP**).
- At **Step 3 (samples)** and **Step 7 (count)**, if the human says cases are **unreadable** or **too thin**, **stop** — rewrite Summaries and Descriptions per **Field rules** before arguing about numeric targets.

## Workflow (sequential — do not skip steps)

### Step 1 — Comprehensive analysis and clarification

**HARD-GATE:** Complete or refresh **`qa-prd-analysis`**; attach `qa-analysis.md` (`~/forge/brain/prds/<task-id>/qa/qa-analysis.md`) as the ground truth.

1. Summarize PRD scope from `<PRD_SOURCE>` **and** from **`~/forge/brain/prds/<task-id>/prd-locked.md`** (must align — brain wins if they differ; flag drift).
2. Ingest `<EXISTING_TESTS>` (MCP or file); index summaries for reuse and gaps.
3. Ingest `<KB_PATH>` if present; note rules not stated in the PRD.
4. Synthesize: gaps, reuse, deprecated candidates, conflicts.
5. **MANDATORY:** Ask the user **all** clarifying questions; get verbatim answers. For **discrete** clarifications (yes/no, pick scope, approve assumption), use **blocking interactive prompts** per **`skills/using-forge`** (**`AskQuestion`** / **numbered options + stop**); open-ended follow-ups may be plain chat after those forks resolve.
6. **MANDATORY:** **Read `qa-analysis.md`** for **`coverage_depth`**. If **`comprehensive`** (or equivalent maximum-coverage commitment), **lock** the planned CSV header to include **`Source`** + **`Preconditions`** columns — **Preconditions column — mandatory for comprehensive**. Do **not** plan an **8-column-only** deliverable for that task.
7. **MANDATORY:** Confirm **new feature vs change to existing** — quote the user.
8. **Preconditions pass:** From PRD + contracts + tech plans, list **starting states** each case will need (roles, seeded entities, flags, environments). Where the doc is silent or ambiguous on **how** testers establish that state — **stop** and elicit answers with **blocking prompts** (same as item 5); do **not** bake guessed seeds into CSV.

### Step 1b — Full requirement context reload (HARD-GATE before Step 5)

**Why:** `qa-prd-analysis` already loads the brain once; this skill **must not** collapse that work into a short summary when writing cases. **Primary artifacts** hold acceptance wording, routes, error codes, SLAs, and integration edges — **`qa-analysis.md` alone cannot substitute.**

Resolve **`<slug>`** from `prd-locked.md` or `product.md` reference. Then **Read/cat each path that exists** (skip missing paths only after recording a **`CONTEXT_GAP`** line for Step 8):

```bash
BRAIN=~/forge/brain
TASK=<task-id>
SLUG=<product-slug>

# Already required for orientation — re-read before authoring rows in Step 5
cat "$BRAIN/prds/$TASK/qa/qa-analysis.md"
cat "$BRAIN/prds/$TASK/prd-locked.md"
cat "$BRAIN/prds/$TASK/terminology.md" 2>/dev/null
cat "$BRAIN/prds/$TASK/shared-dev-spec.md" 2>/dev/null

for f in "$BRAIN/prds/$TASK/tech-plans/"*.md; do [ -f "$f" ] && echo "=== $f ===" && cat "$f"; done

for f in "$BRAIN/products/$SLUG/contracts/"*.md; do [ -f "$f" ] && echo "=== $f ===" && cat "$f"; done

cat "$BRAIN/products/$SLUG/product.md" 2>/dev/null

# Scan — architecture / API surface / hubs (when present)
cat "$BRAIN/products/$SLUG/codebase/index.md" 2>/dev/null
head -c 24000 "$BRAIN/products/$SLUG/codebase/SCAN.json" 2>/dev/null
```

**Extract for test authoring (written notes before Step 2):**

| Layer | Use in CSV rows |
|---|---|
| **prd-locked** | Success criteria, roles, out-of-scope, NFRs → positive/negative/edge cases + **preconditions** (who can act, what must already be true) |
| **terminology.md** (if present) | **Canonical** product names, labels, and disallowed variants → **Expected result** and step text consistent with [docs/terminology-review.md](../../docs/terminology-review.md) |
| **shared-dev-spec** | Cross-surface behaviors, versioning, idempotency, SLAs → API/integration cases |
| **tech-plans** | Concrete routes, schemas, component names, task IDs → **Summary/Description** specificity and traceability |
| **contracts** | Error shapes, cache keys, event schemas → contract-driven cases |
| **product.md** | Platforms, URLs, repo roles → **Platform** column and navigation prefixes |
| **SCAN / index** | Real paths, hubs, known fragile modules → regression-suggested cases (tag Source appropriately) |
| **qa-analysis.md** | Which **types** and **surfaces** to prioritize — not the only source of *what* to assert |

**HARD-GATE:** Do not start **Step 5 (Generate new cases)** until Step 1b is complete **for this invocation** (fresh read, not session memory). If a file is missing and the PRD implies that layer (e.g. API feature but no `shared-dev-spec.md`), record **`CONTEXT_GAP`** and resolve or risk-accept before bulk row generation.

### Step 2 — Test plan and estimation

Deliver:

- Test approach (functional, regression, API, UI, …).
- Categories (smoke, sanity, positive, negative, …).
- **Counts (estimates):** reusable from existing suite, new from PRD, new from KB only, **total new**.

### Step 3 — Rules acknowledgment and samples

1. State `<VALIDATION_CODE>` from the team’s rule doc (user must supply the code string — there is no global Forge default).
2. Complete checklist: 8 fields; if **`coverage_depth: comprehensive`**, **Source** + **Preconditions** columns are **not** optional — see **Preconditions column — mandatory for comprehensive**. Otherwise: 8 fields (+ **Source** / **Preconditions** if using optionals). Navigation first, **explicit preconditions** (column or `Preconditions:` lead-in), **no blank Preconditions** when the column exists (use **`None`** / **`N/A — default happy path`** for default-only), Expected Result duality, quoting, atomicity — and **Summary readability** (**stranger QA** bar: understandable without tribal acronyms — see **Summary** field rule).
3. Present **exactly two** sample rows in final CSV shape — one **PRD-sourced**, one **KB-sourced** if possible. **When comprehensive:** samples **must** use the **full header** including **`Preconditions`** (and **`Source`**). At least **one** sample must demonstrate **non-trivial preconditions** (or explicitly state **`None` / default baseline**) so reviewers see the pattern. **Samples must not** be **title-only** — both must include full **Description** numbered steps so the human can reject **acronym-soup** Summaries **before** bulk generation.
4. **HARD-GATE:** **Wait for explicit user approval** before Step 4.

### Step 4 — Reusable cases (reference list)

List IDs/keys from `<EXISTING_TESTS>` that are reusable (not copied into the new CSV — reference only), each with one-line rationale.

### Step 4.5 — Deprecated cases (TMS when applicable)

1. List cases contradicted or superseded by the PRD.
2. If uncertain → user review list **before** any TMS write.
3. If your TMS is **Jira** and policy allows: add label `Deprecated` via API/MCP **merging** with existing labels.
4. If no TMS automation: document deprecation list in `~/forge/brain/prds/<TASK_ID>/qa/DEPRECATED_TESTS.md` and treat manual follow-up as a **tracked action**.

### Step 5 — Generate new cases

**Pre-batch:** Confirm Step 1b was executed this session. Each new row must be **anchorable**: you can name **one** of — PRD section/bullet, `shared-dev-spec` heading, tech-plan task id line, contract section, or KB rule (for `Source=KB`). If you cannot anchor, **do not add the row** — clarify in Step 2 style or record gap.

1. Ensure `<OUTPUT_CSV>` directory exists (`qa/` under task).
2. Write UTF-8 CSV with header; append in **batches** to avoid tool limits. If **`coverage_depth: comprehensive`**, header **must** include **`Source`** and **`Preconditions`** — **do not** write 8-column-only CSV.
3. **Every** new row: populate **Source** (`PRD` / `KB` / …). Prefer **`Feature Categorization`** / **Summary** text that reflects **actual** names from tech plans and contracts (routes, fields), not generic placeholders.
4. **Every** new row: **preconditions written** — either **`Preconditions`** column (if that header is present) **or** `Preconditions:` prefix inside **Description**. When the **`Preconditions`** column exists, **never** leave the cell **blank** for “default” — write **`None`** or **`N/A — default happy path`**. Rows that need special setup must **not** ship with vague setup text; unresolved setup → **`CONTEXT_GAP`** or user clarification **before** the CSV is treated as approved.

### Step 6 — Final review pass

Re-walk **prd-locked + shared-dev-spec + tech-plans + contracts** (Step 1b set) **and** KB; add missing atomic rows; fix format violations; verify **each** row has **clear preconditions** for non-default paths. Use **`qa-analysis.md`** coverage map as a **checklist**, not as the only definition of “done.”

### Step 7 — Test count review

1. Count rows in `<OUTPUT_CSV>` (excluding header).
2. Compare to Step 2 **total new** estimate; explain material variance.
3. **Quality over headline count:** If the user is **dissatisfied** with the suite — **too many shallow titles**, **unreadable Summaries**, or **too few** *meaningful* executable cases — **do not** defend the integer alone. **Merge, rewrite Summaries, split/merge rows**, and add missing **Description** depth until the user agrees the suite is **runnable**, then re-approve count.
4. **HARD-GATE:** Ask user to approve final count **before** Step 8.

### Step 8 — Final report

After count approval, deliver a summary with:

- **Sources consulted** — bullet list of brain paths whose content informed row text (minimum: `prd-locked.md`, `qa-analysis.md`, every `tech-plans/*.md` read, `shared-dev-spec.md` if present, `contracts/*.md` if read, `product.md`, scan `index.md` if used).
- **`CONTEXT_GAP` entries** — any required artifact that was missing or stale and how it was handled; include **precondition** gaps (e.g. seed/flag undefined after user could not answer). If **any** gap is still **open** (unresolved, not risk-accepted, not deferred-with-owner), you **must** run **CONTEXT_GAP closure (interactive)** below **before** treating the suite as **execution-ready** — not only listing gaps in the report.
- Total reusable (Step 4).
- Total deprecated (Step 4.5) + reasons + replacements.
- Total new in CSV; split **Source=PRD** vs **Source=KB** counts.
- Outstanding manual actions (e.g. TMS labels not applied).

## Output Artifacts

| Artifact | Path (default) |
|---|---|
| Manual cases CSV | `<OUTPUT_CSV>` |
| Deprecation log | `~/forge/brain/prds/<TASK_ID>/qa/DEPRECATED_TESTS.md` (when TMS not updated) |
| Final report | `~/forge/brain/prds/<TASK_ID>/qa/TEST_SUITE_REPORT.md` |

Commit to brain when your workflow uses git-backed brain.

### CONTEXT_GAP closure (interactive) (HARD-GATE when list non-empty)

**When:** Step 8’s **`CONTEXT_GAP` section** lists **one or more** unresolved items, **or** `manual-test-cases.csv` / preconditions still depend on **unknown** seeds, flags, or missing specs that were recorded as gaps during Step 5–6.

**Do not** end the session with a **prose-only** *“please provide X, Y, Z”* list — that is not **interactive** (**`using-forge`** **Interactive human input**).

1. **One gap per assistant turn** — same norm as **`qa-prd-analysis`** sequential elicitation: **no** multi-gap essay + *reply in chat* without **`AskQuestion`**.
2. For the **current** gap, use **`AskUserQuestion`** / **`AskQuestion`** (or **numbered options + stop**) with **discrete** options, e.g.: (a) user **supplies** the missing value (seed id, admin path, flag default, contract section); (b) user **authorizes** a **brain write** with pasted content; (c) **Risk-accept** with **owner + date** (log in **`TEST_SUITE_REPORT.md`**); (d) **Defer** with **named** follow-up and **log** — still one **blocking** choice per turn.
3. After each answer, **update** **`manual-test-cases.csv`** (Preconditions / Description) and **remove or mark resolved** that gap in the report. Continue until **no** **open** **CONTEXT_GAP** remains **or** the user **explicitly** approves shipping with **only** **risk-accepted** / **deferred** rows (via **one** summary **`AskQuestion`** after per-gap turns have been offered).

**Why this exists:** Gaps in **test cases** are the **highest-risk** omissions — they look like coverage but are not reproducible. Interactive closure forces **traceable** resolution.

## Edge Cases

1. **API-only feature** — Navigation step becomes “Invoke `<METHOD> <URL>` …”; base URLs may be API host.
2. **Multi-tenant URLs** — Parameterize per tenant; never hardcode a competitor’s domain.
3. **PRD in non-English** — Keep steps in PRD language or team convention; note in report.
4. **Huge existing suite** — Sample statistically + full pass on PRD-touched modules; document sampling.
5. **No KB** — Source column only `PRD` / `REGRESSION`; Step 3 second sample may be two PRD scenarios of different types.

## Checklist (before claiming done)

- [ ] `qa-prd-analysis` artifact exists and is referenced
- [ ] **Step 1b** full bundle re-read completed before Step 5; Step 8 lists **Sources consulted** + **CONTEXT_GAP** (or explicit “none”)
- [ ] User approved samples (Step 3) and final count (Step 7)
- [ ] CSV validates: 8 columns + **`Source`** + **`Preconditions`** when **`coverage_depth: comprehensive`**; else optional **Source** / **Preconditions** per **Preconditions column — mandatory for comprehensive**; **no blank Preconditions** when column present; quoting, navigation rule, EXPECTED RESULT appendix
- [ ] Atomicity spot-check: random 10% of rows read for split violations
- [ ] Report (Step 8) delivered
- [ ] If **CONTEXT_GAP** was non-empty: **CONTEXT_GAP closure (interactive)** completed — **no** unresolved open gaps without explicit human **risk-accept** / **defer** per **`using-forge`**

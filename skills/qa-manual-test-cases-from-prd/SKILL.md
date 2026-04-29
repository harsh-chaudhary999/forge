---
name: qa-manual-test-cases-from-prd
description: "WHEN: You need atomic manual QA test cases in CSV from a PRD plus optional existing suite and knowledge base, with estimation, reuse/deprecation tracking, review, and a final report — any product, any TMS."
type: rigid
requires: [qa-prd-analysis, brain-read, brain-write]
version: 1.3.2
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

**HARD-GATE (team opt-in):** If `~/forge/brain/products/<slug>/product.md` sets **`forge_qa_csv_before_eval: true`** for this product, **`conductor-orchestrate` State 4b** requires a logged **`[P4.0-QA-CSV]`** *before* **`[P4.0-EVAL-YAML]`**. Without that, do not author eval YAML or dispatch feature work.

**Anti-pattern:** Writing eval YAML or TDD tests **only** from prose tech plans while ignoring an in-flight QA CSV for the same task — you will double-specify and drift.

**Prerequisite order (agents):** This skill is **step 3** of **`qa-write-scenarios` Step −1** (`prd-locked` → **`qa-prd-analysis`** → **this CSV / waiver** → eval YAML). **Do not** open with a **blocking interactive prompt** (**`AskUserQuestion`** / host equivalent per **`using-forge`**) about YAML-before-CSV or eval paths while **`prd-locked.md`** or valid **`qa-analysis.md`** (post–Step 0.5 chat) is missing.

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

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
EACH TEST CASE TESTS EXACTLY ONE VERIFIABLE OUTCOME; EVERY ROW HAS A SOURCE (PRD | KB | REGRESSION | …); BEFORE STEP 5, RE-LOAD THE FULL REQUIREMENT BUNDLE (STEP 1b) — NOT JUST qa-analysis.md; EVERY NEW ROW MUST BE ANCHORABLE TO A PRD BULLET, SPEC SECTION, TECH-PLAN TASK, OR CONTRACT CLAUSE; DO NOT APPEND ROWS TO THE CSV UNTIL STEP 3 (SAMPLES) IS APPROVED — AND NEVER SKIP STEP 7 COUNT APPROVAL BEFORE THE FINAL REPORT (STEP 8). FOR TEAMS THAT OPT IN (forge_qa_csv_before_eval: true), THIS CSV MUST BE APPROVED BEFORE EVAL YAML AND BEFORE TDD FEATURE WORK SO RED TESTS AND P4.4 EXECUTION TRACE TO THE SAME ACCEPTANCE SET.
```

## Red Flags — STOP

- **`qa-prd-analysis` output missing or stale** — STOP. Run or refresh **`qa-prd-analysis`** first.
- **Proceeding to Step 5 without Step 3 approval** — STOP.
- **CSV rows without all 8 required fields** — STOP. Fix or split rows.
- **First step of Description is not navigation** (when UI applies) — STOP. Fix platform URLs from config.
- **Multiple verification points in one Expected Result** — STOP. Split into atomic cases.
- **Deprecation labels applied in TMS without user sign-off on uncertain cases** — STOP. List for review first.
- **Generating Step 5 rows from memory or from `qa-analysis.md` alone** — STOP. Complete **Step 1b** (fresh read of prd-locked, shared-dev-spec, tech-plans, contracts, scan index when present).

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

## Required CSV Fields (8 columns)

Header row **exactly**:

```text
"Id","Platform","Summary","Description","Expected Result","Automatable","Type","Feature Categorization"
```

Optional ninth column (recommended):

```text
"Source"
```

**Source** values (constrained): `PRD` | `KB` | `REGRESSION` | `HYBRID` (document in Summary why hybrid).

### Field rules

| Field | Rule |
|---|---|
| **Id** | Unique: `TC-<FeatureSlug>-<NNN>` (use your project’s slug, not a fixed vendor prefix). |
| **Platform** | One of: `Web`, `iOS`, `Android`, `API`, or project-defined labels — **consistent** within the file. |
| **Summary** | Single-sentence purpose; one verification focus. |
| **Description** | Step list. **HARD-GATE:** Step 1 must be navigation when UI: `1. Navigate to <platform base URL> …` using configured URLs. **When the case depends on account state** (blacklisted user, tier, overdue, feature flag), begin with explicit **Preconditions:** in the same cell (e.g. `Preconditions: Seeded recruiter R with L1 pending and crawl reason; valid session. 1. Navigate…`). Map screens/selectors to **`qa-prd-analysis` Q8** / design when applicable. No line breaks inside the CSV cell; use spaces between steps. **Append** at end: `EXPECTED RESULT: <same text as Expected Result column>`. |
| **Expected Result** | **One** outcome; must **match** the `EXPECTED RESULT:` appendix in Description character-for-character. |
| **Automatable** | `Yes` \| `No` \| `Partial`. |
| **Type** | e.g. `Positive`, `Negative`, `Edge Case`, `API`, `Security`, `Performance`, `Smoke`, `Sanity`, `Regression`, … |
| **Feature Categorization** | Module / epic name for filtering imports. |

### CSV mechanics

- Entire row double-quoted; commas between fields.
- **Single line per test case** (no embedded newlines in fields).

## Atomicity (non-negotiable)

- **One test case = one primary verification.**
- Split when: multiple unrelated assertions, multiple integrations independently testable, multiple error classes, or multiple user goals.

## Workflow (sequential — do not skip steps)

### Step 1 — Comprehensive analysis and clarification

**HARD-GATE:** Complete or refresh **`qa-prd-analysis`**; attach `qa-analysis.md` (`~/forge/brain/prds/<task-id>/qa/qa-analysis.md`) as the ground truth.

1. Summarize PRD scope from `<PRD_SOURCE>` **and** from **`~/forge/brain/prds/<task-id>/prd-locked.md`** (must align — brain wins if they differ; flag drift).
2. Ingest `<EXISTING_TESTS>` (MCP or file); index summaries for reuse and gaps.
3. Ingest `<KB_PATH>` if present; note rules not stated in the PRD.
4. Synthesize: gaps, reuse, deprecated candidates, conflicts.
5. **MANDATORY:** Ask the user **all** clarifying questions; get verbatim answers.
6. **MANDATORY:** Confirm **new feature vs change to existing** — quote the user.

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
| **prd-locked** | Success criteria, roles, out-of-scope, NFRs → positive/negative/edge cases |
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
2. Complete checklist: 8 fields, navigation first, Expected Result duality, quoting, atomicity.
3. Present **exactly two** sample rows in final CSV shape — one **PRD-sourced**, one **KB-sourced** if possible.
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
2. Write UTF-8 CSV with header; append in **batches** to avoid tool limits.
3. **Every** new row: populate **Source** (`PRD` / `KB` / …). Prefer **`Feature Categorization`** / **Summary** text that reflects **actual** names from tech plans and contracts (routes, fields), not generic placeholders.

### Step 6 — Final review pass

Re-walk **prd-locked + shared-dev-spec + tech-plans + contracts** (Step 1b set) **and** KB; add missing atomic rows; fix format violations. Use **`qa-analysis.md`** coverage map as a **checklist**, not as the only definition of “done.”

### Step 7 — Test count review

1. Count rows in `<OUTPUT_CSV>` (excluding header).
2. Compare to Step 2 **total new** estimate; explain material variance.
3. **HARD-GATE:** Ask user to approve final count **before** Step 8.

### Step 8 — Final report

After count approval, deliver a summary with:

- **Sources consulted** — bullet list of brain paths whose content informed row text (minimum: `prd-locked.md`, `qa-analysis.md`, every `tech-plans/*.md` read, `shared-dev-spec.md` if present, `contracts/*.md` if read, `product.md`, scan `index.md` if used).
- **`CONTEXT_GAP` entries** — any required artifact that was missing or stale and how it was handled.
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
- [ ] CSV validates: 8 columns, optional Source, quoting, navigation rule, EXPECTED RESULT appendix
- [ ] Atomicity spot-check: random 10% of rows read for split violations
- [ ] Report (Step 8) delivered

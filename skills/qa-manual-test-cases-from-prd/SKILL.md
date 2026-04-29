---
name: qa-manual-test-cases-from-prd
description: "WHEN: You need atomic manual QA test cases in CSV from a PRD plus optional existing suite and knowledge base, with estimation, reuse/deprecation tracking, review, and a final report — any product, any TMS."
type: rigid
requires: [qa-prd-analysis, brain-write]
version: 1.0.0
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

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
EACH TEST CASE TESTS EXACTLY ONE VERIFIABLE OUTCOME; EVERY ROW HAS A SOURCE (PRD | KB | REGRESSION | …); DO NOT APPEND ROWS TO THE CSV UNTIL STEP 3 (SAMPLES) IS APPROVED — AND NEVER SKIP STEP 7 COUNT APPROVAL BEFORE THE FINAL REPORT (STEP 8). FOR TEAMS THAT OPT IN (forge_qa_csv_before_eval: true), THIS CSV MUST BE APPROVED BEFORE EVAL YAML AND BEFORE TDD FEATURE WORK SO RED TESTS AND P4.4 EXECUTION TRACE TO THE SAME ACCEPTANCE SET.
```

## Red Flags — STOP

- **`qa-prd-analysis` output missing or stale** — STOP. Run or refresh **`qa-prd-analysis`** first.
- **Proceeding to Step 5 without Step 3 approval** — STOP.
- **CSV rows without all 8 required fields** — STOP. Fix or split rows.
- **First step of Description is not navigation** (when UI applies) — STOP. Fix platform URLs from config.
- **Multiple verification points in one Expected Result** — STOP. Split into atomic cases.
- **Deprecation labels applied in TMS without user sign-off on uncertain cases** — STOP. List for review first.

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
| **Description** | Step list. **HARD-GATE:** Step 1 must be navigation when UI: `1. Navigate to <platform base URL> …` using configured URLs. No line breaks inside the CSV cell; use spaces between steps. **Append** at end: `EXPECTED RESULT: <same text as Expected Result column>`. |
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

1. Summarize PRD scope from `<PRD_SOURCE>`.
2. Ingest `<EXISTING_TESTS>` (MCP or file); index summaries for reuse and gaps.
3. Ingest `<KB_PATH>` if present; note rules not stated in the PRD.
4. Synthesize: gaps, reuse, deprecated candidates, conflicts.
5. **MANDATORY:** Ask the user **all** clarifying questions; get verbatim answers.
6. **MANDATORY:** Confirm **new feature vs change to existing** — quote the user.

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

1. Ensure `<OUTPUT_CSV>` directory exists (`qa/` under task).
2. Write UTF-8 CSV with header; append in **batches** to avoid tool limits.
3. **Every** new row: populate **Source** (`PRD` / `KB` / …).

### Step 6 — Final review pass

Re-walk PRD + KB; add missing atomic rows; fix format violations.

### Step 7 — Test count review

1. Count rows in `<OUTPUT_CSV>` (excluding header).
2. Compare to Step 2 **total new** estimate; explain material variance.
3. **HARD-GATE:** Ask user to approve final count **before** Step 8.

### Step 8 — Final report

After count approval, deliver a summary with:

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
- [ ] User approved samples (Step 3) and final count (Step 7)
- [ ] CSV validates: 8 columns, optional Source, quoting, navigation rule, EXPECTED RESULT appendix
- [ ] Atomicity spot-check: random 10% of rows read for split violations
- [ ] Report (Step 8) delivered

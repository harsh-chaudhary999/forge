---
name: qa-prd-analysis
description: "WHEN: Before generating manual QA test cases or a formal test plan from a PRD, you need systematic requirement analysis, coverage mapping, and explicit clarifications — product-agnostic."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers:
  - "analyze PRD for QA"
  - "PRD test analysis"
  - "QA requirements analysis"
allowed-tools:
  - Write
---

# QA PRD Analysis

**HARD-GATE:** Structured PRD analysis must be **written to the brain** before bulk manual test case generation (`qa-manual-test-cases-from-prd`) proceeds. Chat-only analysis is not valid.

---

Systematic analysis of a Product Requirements Document **before** any test case authoring. Works for any product or stack; replace org-specific names with your project’s surfaces, TMS keys, and knowledge-base paths.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "The PRD is short, I can infer coverage" | Short PRDs hide implicit business rules and integration edges. Skipped analysis becomes missing tests and production defects. |
| "I'll write tests while I read the PRD" | Parallel read-and-write produces shallow cases and wrong priorities. Analysis must finish (or checkpoint) before bulk generation. |
| "Assumptions are fine if they're reasonable" | Reasonable to whom? Unvalidated assumptions are not lockable. Every ambiguity must be **asked** or **explicitly waived** by the stakeholder. |
| "We only need happy path for MVP" | Negative, permission, and data-integrity paths dominate incident volume. Omitting them is not scope discipline; it is risk denial. |
| "Jira/Confluence already documents behavior" | External tools are not your analysis artifact. If it is not summarized in **your** analysis output, downstream steps cannot trace coverage. |
| "Cross-functional impact is backend's problem" | UI, API, cache, events, and search all change together. QA analysis that ignores surfaces ships blind spots. |
| "I'll skip the checklist to save tokens" | The checklist exists because teams repeatedly missed the same categories. Skipping it repeats those failures. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
NO BULK TEST CASE AUTHORING UNTIL PRD ANALYSIS IS WRITTEN, CHECKLISTED, AND OPEN GAPS ARE EITHER CLARIFIED WITH THE USER OR EXPLICITLY LOGGED AS ACCEPTED RISK WITH OWNER.
```

## Red Flags — STOP

- **You cannot list the PRD’s primary user types and surfaces** — STOP. Resolve scope with the stakeholder before mapping scenarios.
- **Business rules are copied as prose without “testable implication” notes** — STOP. Each rule needs an observable pass/fail signal.
- **Zero integration or dependency section** — STOP. Real features always touch more than one system.
- **You are about to generate tests without asking at least one clarification** when the PRD has any ambiguity — STOP. Ask; do not assume.
- **Analysis output is only in chat** — STOP. Write analysis to the brain (see Output) so `qa-manual-test-cases-from-prd` and reviewers have a durable artifact.

## Purpose

Produce a **structured PRD analysis** that downstream QA work (manual CSV cases, test plans, or automation backlogs) can trace to requirements — without embedding vendor-specific tools in the logic.

## Inputs (configure per project)

| Input | Description |
|---|---|
| **PRD** | Link, export, Confluence/Wiki page, PDF, or markdown — whatever the project uses |
| **Product context** | Optional: `product.md`, architecture notes, API catalog |
| **Existing coverage** | Optional: export from test management (Xray, Zephyr, TestRail, spreadsheets) or “none” |

## Workflow

### Step 1 — Ingest and scope

1. Read the full PRD (all sections).
2. Record **product name / feature name**, **version or slice**, and **in-scope vs out-of-scope** bullets.

### Step 2 — Section-by-section extraction

For **each** major PRD section:

1. **Main scenarios** — user-visible flows and admin/operator flows.
2. **Business rules** — validations, limits, entitlements, state transitions.
3. **System interactions** — APIs, DB, cache, search, queues, third parties.
4. **Edge cases** — boundaries, empty states, concurrency hints.
5. **Error conditions** — expected failures, codes, messages (or “not specified”).

### Step 3 — Cross-functional impact

For each feature or change:

1. Dependencies on existing systems.
2. Data flow changes (create/read/update/delete).
3. Permission / role changes.
4. Integration points (contracts).
5. **Preservation**: what must **not** regress.

### Step 4 — User journey map (platform-agnostic)

1. Surfaces in scope (e.g. web, iOS, Android, API-only, admin).
2. User states (new, returning, degraded, recovery).
3. Cross-surface flows if applicable.

### Step 5 — Test scenario matrix (planning only)

Build a matrix skeleton:

`User types × Surfaces × Scenarios × States × Critical integrations`

Use it to spot gaps — **do not** treat the matrix cells as final test case IDs yet.

### Step 6 — Gaps, reuse, conflicts

1. **Gaps** — PRD requirements not reflected in existing tests (if Source 2 provided).
2. **Reuse** — existing tests that still apply unchanged or with minor edits.
3. **Deprecated / superseded** — existing tests contradicted by the PRD (flag for stakeholder; TMS updates happen in `qa-manual-test-cases-from-prd` when applicable).
4. **Conflicts** — contradictions between PRD, KB, and existing tests.

### Step 7 — Mandatory clarifications

**HARD-GATE:** Before closing analysis:

1. List **every** open question for the user (no “TBD” buried in prose).
2. **HARD-GATE:** Ask explicitly: **“Is this net-new functionality or a change to existing behavior?”** — record the answer verbatim (even if you believe you know).

## PRD Analysis Validation Checklist

Before handing off to test case generation:

- [ ] Every major PRD requirement has been categorized (functional / non-functional / N/A).
- [ ] Business rules are listed with testable implications.
- [ ] Integrations and data flows are mapped.
- [ ] User types, roles, and surfaces are explicit.
- [ ] Error and edge cases are listed or marked “not specified — risk”.
- [ ] Cross-functional impacts documented.
- [ ] Regression / preservation requirements noted.
- [ ] **Clarifications** sent and answers recorded (or risks logged with owner).
- [ ] **New vs existing feature** confirmed by the user and quoted.

## Output

Write to the brain (path is project convention; default pattern):

`~/forge/brain/prds/<task-id>/qa/PRD_ANALYSIS.md`

Include YAML frontmatter when your brain convention supports it:

```yaml
---
id: QA-PRD-<task-id>
product: <slug>
source_prd: <uri or path>
analysis_date: <ISO8601>
feature_class: new | existing_change
---
```

Body: sections matching Steps 2–7 above, plus a short **Executive summary** (5–10 bullets).

## Edge Cases

1. **PRD is a one-pager** — Still run Steps 2–7; matrix may be small; explicitly state “minimal doc — high clarification load.”
2. **No existing test export** — Source 2 empty; reuse/deprecation sections state “none provided.”
3. **Conflicting legal/compliance vs UX** — STOP; escalate in writing; do not invent resolution in tests.
4. **PRD references unreleased backend** — Flag environment prerequisites for later execution notes.
5. **Multiple PRDs for one slice** — Produce one merged analysis or separate files with explicit linkage; never silently merge scopes.

## Relationship to Other Skills

- **`qa-manual-test-cases-from-prd`** consumes this artifact for CSV generation and counts.
- **`eval-scenario-format`** / **`eval-translate-english`** produce **YAML for automated Forge eval drivers** — different artifact, same need for clear requirements; PRD analysis still helps both.

---
name: qa-write-scenarios
description: "WHEN: qa-prd-analysis is complete and you need to write the maximum possible number of executable eval YAML scenarios — one per test type × surface × scenario variant. No gaps. No shortcuts."
type: rigid
requires: [brain-read, qa-prd-analysis, eval-scenario-format]
version: 2.4.7
preamble-tier: 3
triggers:
  - "write eval scenarios"
  - "generate test scenarios from PRD"
  - "generate eval YAML"
  - "create automation scenarios"
  - "write maximum test cases"
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
  - mcp__*
---

# QA Write Scenarios

Generates the **maximum possible number of executable eval YAML scenarios** from brain artifacts. Every test type confirmed in `qa-analysis.md` produces its own scenario set per surface. No test type is merged, collapsed, or abbreviated.

**Count is a quality signal.** Low scenario counts are a sign of incomplete analysis, not conciseness. A 20-scenario output for a payment feature is always wrong.

## Human input (all hosts)

**`AskUserQuestion`** in **`allowed-tools`** is canonical; map per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** on every IDE. **Step −1** governs *when* to prompt; **`using-forge`** governs *how* (**Interactive human input**, **Multi-question elicitation** for sequences, **Stage-local questioning**).

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "20-30 scenarios covers this feature" | For any non-trivial feature, 20-30 is incomplete. A login form alone requires 40+ (positive, negative, BVA, security, accessibility). |
| "I'll combine positive + negative into one scenario" | Combined scenarios mask failures. When the negative step fails in a positive scenario, the failure root cause is ambiguous. One assertion per scenario. |
| "Happy path is enough for smoke" | Smoke covers critical paths. All other types still require their own scenarios. Smoke is additive, not a substitute. |
| "Security testing is someone else's job" | OWASP Top 10 for the relevant surface is always in scope. If not confirmed in Q1, ask before omitting — do not silently skip. |
| "Accessibility scenarios can't be automated" | Keyboard navigation, ARIA attribute presence, focus order, and contrast ratios can all be asserted via CDP or device automation. |
| "I'll skip the count audit at the end" | The count audit is the proof that no type was silently omitted. Skip it and you ship gaps. |
| "Existing eval YAML is close enough, I'll add a few" | Read the existing files first. If test types are missing, add full sets — not a few patches. |
| "I'll write scenarios from memory" | Memory drifts from the PRD. Read prd-locked.md, tech-plans, and qa-analysis.md fresh on every invocation. |
| "I'll generate eval YAML before manual CSV — PRD is enough" | **Automation without an approved human baseline is orphan automation.** You cannot faithfully prioritize coverage or trace YAML rows to acceptance IDs until **`manual-test-cases.csv`** exists (skill **`qa-manual-test-cases-from-prd`** through approval). YAML then maps journeys to those rows where applicable. |
| "`qa-analysis.md` + CSV is enough — I won't re-open tech plans or contracts" | **`qa-analysis.md` prioritizes types/surfaces; concrete routes, payloads, cache keys, and error codes live in shared-dev-spec, tech-plans, and contracts.** Shallow YAML repeats generic steps. Use the same primary-source bundle as **`qa-manual-test-cases-from-prd`** Step 1b (see Step 0.1 below). |
| "I'll drop a Python/bash generator in `eval/` to emit YAML" | **`eval/` is only for driver-readable `*.yaml` (and manifests).** Generators like `_generate_scenarios.py` are not part of Forge, confuse CI/review, and usually produce **`preconditions: []`** and weak UI coverage. Author YAML directly (or use a **repo-local** `tools/` script **outside** `eval/` if you must codegen). **Never** commit `eval/_generate*.py` without team agreement — prefer deleting after one-off use. |
| "Prerequisites are missing — I'll open with a blocking prompt about eval YAML / CSV waiver" | **Violates dependency order.** The **first** interaction must not be the **last** gate (automation-only waiver). Walk **forward** from **`prd-locked.md`** → **`qa-prd-analysis`** (**sequential interactive** Step 0.5 per **`using-forge`** / **`qa-prd-analysis`**) → **`manual-test-cases.csv`** (or waiver **after** PRD+QA exist). See **Step −1** below. |
| "During **`qa-prd-analysis`** Step 0.5, I'll paste the *orphan automation / why eval YAML isn't written yet* essay **between** Q1, Q2, …" | **Invalid.** That explanation is for **gate-order violations** (Step −1), **not** between every interrogation turn. During Step 0.5, stay on the **current** question — one short forward sentence max. |
| "I'll list the whole QA→CSV→eval→merge chain in chat while the user is still on an upstream step" | **Invalid.** **`using-forge`** — **one-step horizon** in assistant messages: name **only** the **immediate** next artifact/skill unless the user asked for the roadmap. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
MANUAL BASELINE FIRST: APPROVED manual-test-cases.csv (qa-manual-test-cases-from-prd) BEFORE bulk eval YAML UNLESS qa-analysis.md RECORDS WAIVER KEYS PLUS VERBATIM USER QUOTE (csv_baseline_waiver_user_quote) — NO AGENT-ONLY PARAPHRASE.
EVERY CONFIRMED TEST TYPE FROM qa-analysis.md GETS ITS OWN SCENARIO SET.
EVERY CONFIRMED SURFACE GETS ITS OWN SCENARIO FILE.
EVERY SCENARIO HAS EXACTLY ONE ASSERTION — NO MULTI-ASSERTION MEGA-SCENARIOS.
WHERE CSV ROW IDS EXIST, REFERENCE THEM IN SCENARIO METADATA / COMMENTS FOR TRACEABILITY.
SCENARIO STEPS AND TARGETS MUST BE GROUNDED IN prd-locked + shared-dev-spec + tech-plans + contracts (NOT qa-analysis.md ALONE).
THE FINAL COUNT MUST BE AUDITED AGAINST THE COVERAGE MATRIX BEFORE COMMIT.
A LOW COUNT IS A BUG IN THIS SKILL — TREAT IT AS A FAILURE, NOT A FEATURE.
```

## Step −1 — Prerequisite order before any blocking interactive prompt (HARD-GATE)

**General rule (all phases, all hosts):** This is the **QA → eval YAML** slice of **`using-forge`** **Stage-local questioning** — ask only what unblocks the **current** stage; never front-load a **blocking interactive prompt** (**`AskUserQuestion`** / host equivalent — **`using-forge`** **Blocking interactive prompts**) about **later** pipeline steps while **earlier** prerequisites are missing (same discipline applies to intake, council, tech plans, merge, …).

**Run checks in this order.** Address **only the first failing step** in your **first** reply — do **not** bundle “eval cannot emit until everything exists — how proceed?” and do **not** lead with a **blocking prompt** about CSV waiver / YAML-only when upstream artifacts are absent.

**Human expectation:** If gate **N** is missing, say what gate **N** is and offer **primary fix + alternatives** (below) — not only “run `/intake`” as if no other path existed.

| Order | Gate | Primary fix if missing | Alternatives if user can’t / won’t run the primary (still need human approval) |
|------:|------|------------------------|--------------------------------------------------------------------------------|
| 1 | **`~/forge/brain/prds/<task-id>/prd-locked.md`** | **`/intake`** (or **`intake-interrogate`**) to produce lock | User **pastes** PRD/wiki excerpt in chat → assistant **drafts** `prd-locked.md` → user **reviews** → **Write** to brain. **Or** user confirms copying lock from another **`prds/<task-id>/`** when scope is the **same**. **Not valid:** YAML or QA prompts **without** any on-disk `prd-locked` after explicit approval path. |
| 2 | **`qa/qa-analysis.md`** from **`qa-prd-analysis`** with Step 0.5 interrogation completed in chat | Run **`qa-prd-analysis`** (**`using-forge`** **Multi-question elicitation** for Q1–Q8 — one topic per turn, reconcile; see **QA PRD analysis** in **`using-forge`**) | User answers **turn-by-turn** in thread; dimensions may be **subsumed** + logged per skill. Assistant writes **`qa-analysis.md`** consistent with HARD-GATEs (no fake “confirmed”). **Not valid:** skipping chat-visible interrogation, or dumping full Q1–Q8 + meta-modal in one turn. |
| 3 | **`qa/manual-test-cases.csv`** with ≥1 data row **or** valid waiver (**`csv_baseline_waiver_user_quote`** after explicit approval) | **`qa-manual-test-cases-from-prd`** through approvals | Documented **YAML-before-CSV waiver** in **`qa-analysis.md`** with verbatim quote **only after** 1–2 satisfied — **Step 0.0** in this skill. |

**Not prerequisites for this skill chain:** Council, **`shared-dev-spec.md`**, tech plans — use them when present for **better targets**; they do **not** replace gate **1–3**.

**Forbidden opening:** *“Forge cannot emit `eval/*.yaml` until prd-locked + QA interrogation + manual CSV (or waiver) exist. How should we proceed?”* when **1 or 2** is missing — that asks the user to decide **downstream** tradeoffs before **upstream** work exists. Replace with: *“Missing `<first artifact>` — do `<first skill/command>` first.”*

---

## Red Flags — STOP

- **Opening with a CSV/evYAML waiver blocking interactive prompt while `prd-locked.md` or `qa-analysis.md` is missing** — STOP. Execute **Step −1** order.
- **`manual-test-cases.csv` missing or has no data rows** (only header / empty) — STOP. Run **`qa-manual-test-cases-from-prd`** through Step 7 approval first — unless CSV waiver is **valid** (next bullet) **and** steps 1–2 above satisfied.
- **Invalid CSV baseline waiver** — **`eval_yaml_without_manual_csv_baseline: true`** is **not** satisfied by the agent paraphrasing "user wanted automation only." **Valid only if** **`csv_baseline_waiver_user_quote:`** in frontmatter contains a **verbatim substring** from the **user's message** in this thread approving YAML-before-CSV, **or** the assistant logs the exact **blocking interactive prompt** option the user chose (**`AskUserQuestion`** / host equivalent per **`using-forge`**). Otherwise STOP — complete manual CSV first or get explicit chat approval and **then** record both keys + quote.
- **Scenario targets invented without tech-plan / contract / CSV grounding** — STOP. Complete **Step 0.1** or record **`CONTEXT_GAP`** in **`qa/scenarios-manifest.md`**.
- **`qa-analysis.md` absent from brain** — STOP. Run `qa-prd-analysis` first.
- **Test types from Q1 not listed in `qa-analysis.md`** — STOP. The selection must be written before generation.
- **Scenario has no `test_type` field** — STOP. Every scenario must declare its type for filtering and reporting.
- **Any scenario step has `target: TODO` or `expected: TBD`** — STOP. Every target must be concrete.
- **Total count < 50 for a medium-complexity feature** — STOP. Audit which types are missing.
- **Security scenarios absent and security was selected in Q1** — STOP. Generate OWASP-mapped scenarios.
- **Accessibility scenarios absent and accessibility was selected** — STOP. Generate WCAG-mapped scenarios.

---

## Pre-Invocation Checklist

Before invoking this skill, verify:

- [ ] **`qa-manual-test-cases-from-prd`** completed and **`qa/manual-test-cases.csv`** has ≥1 data row — **or** documented waiver in **`qa-analysis.md`** (see Red Flags)
- [ ] `qa-prd-analysis` has been run and `qa/qa-analysis.md` exists in brain
- [ ] `qa-analysis.md` reflects **real interrogation** (**qa-prd-analysis** Step 0.5: **sequential adaptive** in chat per **`using-forge`**) — not agent-self-confirmed defaults; if **`eval_yaml_without_manual_csv_baseline`**, **`csv_baseline_waiver_user_quote`** present per Step 0.0
- [ ] `qa-analysis.md` contains `test_types`, `surfaces`, `coverage_depth`, and feature priorities **as actually confirmed in chat**
- [ ] `prd-locked.md` exists for the task — no PRD = no valid scenario generation
- [ ] All tech plans exist in `brain/prds/<task-id>/tech-plans/` (scenarios without concrete routes/schemas will have placeholder targets)
- [ ] You know the task_id and product slug before starting

## Pre-Implementation Checklist

Before writing the first scenario:

- [ ] Brain artifacts loaded fresh (**Step 0 + Step 0.1** complete) — do not write from memory or from **`qa-analysis.md`** alone
- [ ] Scenario ID convention understood: `SC-{AREA}-{TYPE}-{NNN}`
- [ ] Surface-to-driver map built from confirmed surfaces
- [ ] Existing eval YAML checked — diff against it before adding new scenarios
- [ ] Minimum scenario floors noted per feature complexity level

## Post-Implementation Checklist

Before marking this skill complete:

- [ ] Count audit passed — every confirmed test type has at least 1 scenario per in-scope feature area
- [ ] No `TODO`, `TBD`, or placeholder targets in any scenario file
- [ ] Coverage matrix written and all cells non-zero for confirmed types
- [ ] `scenarios-manifest.md` written and committed to brain
- [ ] `[QA-SCENARIOS]` gate line logged to `qa-pipeline.log` with total count
- [ ] If **`manual-test-cases.csv`** exists: scenarios reference CSV **`Id`** in YAML comments or metadata where a row maps 1:1 to a journey
- [ ] If MCP TMS (Jira/Xray/TestRail) was used: test cases pushed to TMS and links recorded in manifest

---

## Cross-References

- **`qa-prd-analysis`** — writes `qa/qa-analysis.md` that this skill reads to determine which test types, surfaces, and feature areas are in scope. Must run before this skill.
- **`qa-manual-test-cases-from-prd`** — produces **`manual-test-cases.csv`** (QA engineering baseline). **Must complete before this skill** unless waiver recorded in **`qa-analysis.md`** — eval YAML should trace to CSV **`Id`** columns where applicable. Its **Step 1b** requirement-bundle reload is the same primary-source bar **Step 0.1** here must meet for routes, payloads, and assertions.
- **`eval-scenario-format`** — canonical YAML schema every scenario file produced here must follow. Read it before writing the first file.
- **`qa-pipeline-orchestrate`** — the orchestrator that invokes this skill as phase QA-P2. Results feed directly into QA-P5 multi-surface execution.
- **`eval-coordinate-multi-surface`** — downstream consumer: reads the YAML files this skill writes and dispatches them to surface-specific drivers.

---

## MCP Integration

This skill may invoke MCP tools when configured:

| MCP Server | Use |
|---|---|
| Jira / Xray MCP | Push generated test cases to Jira as Xray test issues; link scenario IDs to Jira tickets |
| TestRail MCP | Create test runs and upload scenarios to TestRail test cases |
| Figma MCP (`mcp__claude_ai_Figma__get_design_context`) | Read design context for UI-surface scenarios to produce accurate `data-testid` selectors and visual assertions |

**When to invoke Jira/Xray MCP:** If `qa-analysis.md` contains a `tms: jira-xray` field, push each generated scenario as a Jira Xray test issue after the count audit passes. Record the Jira issue key back in the scenario YAML as `jira_ref`.

**When to invoke Figma MCP:** If `qa-analysis.md` `surfaces` includes `web` or `android`/`ios` and a `figma_file_key` is recorded in `prd-locked.md`, fetch the design context for the feature flow before writing UI selector steps.

---

## Step 0 — Pre-Flight: Load Brain Artifacts

```bash
BRAIN=~/forge/brain/prds/<task-id>

# Required — cannot proceed without these
cat "$BRAIN/prd-locked.md"
cat "$BRAIN/qa/qa-analysis.md"

# Manual QA baseline — REQUIRED unless qa-analysis.md waives (see Red Flags)
cat "$BRAIN/qa/manual-test-cases.csv" 2>/dev/null

# Primary requirement sources — REQUIRED for concrete targets (Step 0.1); without these you emit generic YAML
for f in "$BRAIN/tech-plans/"*.md; do echo "=== $f ===" && cat "$f"; done
cat "$BRAIN/shared-dev-spec.md" 2>/dev/null

# Contracts + product (use SLUG from prd-locked product field — same as qa-prd-analysis / qa-manual Step 1b)
SLUG=<product-slug>
PROD=~/forge/brain/products/$SLUG
for f in "$PROD/contracts/"*.md; do [ -f "$f" ] && echo "=== $f ===" && cat "$f"; done
cat "$PROD/product.md" 2>/dev/null

# Check existing eval YAML
ls "$BRAIN/eval/" 2>/dev/null && echo "EXISTING SCENARIOS — diff before adding"
```

### Step 0.0 — Manual baseline gate (HARD-GATE)

**Intent:** Eval YAML is **not** a substitute for an approved manual case inventory. PRD + `qa-analysis.md` drive **what** to automate; **`manual-test-cases.csv`** is the **numbered acceptance baseline** you trace YAML rows to.

1. Read YAML frontmatter at the top of **`qa/qa-analysis.md`** (if present).
2. **Pass** if **either**:
   - **`eval_yaml_without_manual_csv_baseline: true`** **and** **`csv_baseline_waiver_reason:`** is non-empty **and** **`csv_baseline_waiver_user_quote:`** matches verbatim text from the user's approval message **or** from the blocking prompt option text — **not** agent-authored paraphrase alone, **or**
   - **`qa/manual-test-cases.csv`** exists **and** contains **≥1 line after the header row** (non-empty data row).

3. **Fail (STOP)** if neither condition holds:
   - Tell the user to complete **`qa-manual-test-cases-from-prd`** through Step 7 approval so **`manual-test-cases.csv`** exists with data rows, **or**
   - If they insist on YAML-only, use a **blocking interactive prompt** with explicit YAML-before-CSV warning options; after approval, record **`eval_yaml_without_manual_csv_baseline: true`**, **`csv_baseline_waiver_reason:`**, and **`csv_baseline_waiver_user_quote:`** (verbatim) in **`qa-analysis.md` frontmatter** — then re-invoke this skill.

**Concrete check (evidence before proceeding):** `wc -l` / `Read` on **`manual-test-cases.csv`**, **or** frontmatter shows all three waiver keys with a **user-origin** quote field.

**Ordering truth:** If **`eval_yaml_without_manual_csv_baseline`** was set without valid evidence, **YAML before manual CSV** is a **process violation** — fix brain metadata or run **`qa-manual-test-cases-from-prd`** first; do not treat generated YAML as aligned with an approved human baseline.

### Step 0.1 — Ground scenarios in primary sources (HARD-GATE)

**`qa-analysis.md`** tells you **which test types and surfaces** apply; it does **not** replace **prd-locked**, **shared-dev-spec**, **tech-plans**, **contracts**, or **manual-test-cases.csv** for **what** to type into `target`, paths, HTTP bodies, DB assertions, cache keys, or topic names.

Before **Step 3**, resolve **product `<slug>`** and ensure you have **Read** (this invocation):

| Artifact | Why |
|---|---|
| **`prd-locked.md`** | Success criteria wording drives expected results. |
| **`shared-dev-spec.md`** | Cross-service SLAs, error codes, versioning. |
| **`tech-plans/*.md`** | Routes, schemas, component/task IDs — **mandatory** for non-placeholder targets. |
| **`products/<slug>/contracts/*.md`** | Required whenever API/cache/event/search surfaces appear in confirmed surfaces. |
| **`products/<slug>/product.md`** | Base URLs, platform list, deploy facts. |
| **`qa/manual-test-cases.csv`** | Row **Id** linkage and step wording to mirror in automation. |
| **`codebase/index.md` or SCAN.json`** (if present) | Hub files / API surface hints — use when tech plan lacks a selector (prefer tech plan + CSV first). |

**HARD-GATE:** No scenario step may use **`TODO` / generic path** where a **tech plan**, **contract**, or **CSV row** already names the real resource. **STOP** and complete **`CONTEXT_GAP`** (brain path + what is missing) in **`qa/scenarios-manifest.md`** if you cannot ground a step.

From `qa-analysis.md`, extract and record:
- `test_types: [...]` — the confirmed list from Q1
- `surfaces: [...]` — the confirmed list from Q2
- `coverage_depth: smoke|standard|comprehensive`
- Feature areas and priorities (Q4)
- Interrogation Q&A (open ambiguities and their answers)
- **Q8 design mapping** (when UI in scope): PRD→component→precondition from **`qa-analysis.md`**

### Step 0.2 — Preconditions for auth-gated and stateful UI/API flows (HARD-GATE)

When a scenario asserts **post-login** UI, **tier-specific** API behavior, **blacklist/overdue** states, or anything other than a cold anonymous call, the scenario **must** list **preconditions** (YAML `preconditions:` array of strings, or per **`eval-scenario-format`**) that name:

- **Account / token / role** (e.g. recruiter with `L1_Verification_Pending` + crawl reason, blacklisted test user from Q8 fixtures).
- **Data** already in DB or **env** (feature flag, `RECRUITER_FIXTURE_ID` meaning).
- **Prior steps** if not expressed as API calls in the same file (e.g. "Session established via login" only when the driver cannot perform login in-step — then split scenarios or add login step).

**Do not** ship **`preconditions: []`** for journeys that require a specific user state — that was the failure mode in codegen scripts.

---

## Step 1 — Surface-to-Driver Map

Build the active driver map from confirmed surfaces:

```yaml
surface_drivers:
  web:     eval-driver-web-cdp
  android: eval-driver-android-adb
  ios:     eval-driver-ios-xctest
  api:     eval-driver-api-http
  db:      eval-driver-db-mysql
  cache:   eval-driver-cache-redis
  kafka:   eval-driver-bus-kafka
  es:      eval-driver-search-es
```

Only include surfaces from the confirmed list. Every other surface: note as N/A in manifest.

---

## Step 2 — Scenario ID Convention

```
SC-{AREA}-{TYPE}-{NNN}

Examples:
  SC-AUTH-POS-001    (positive)
  SC-AUTH-NEG-003    (negative)
  SC-AUTH-BVA-002    (boundary value)
  SC-AUTH-SEC-001    (security)
  SC-AUTH-A11Y-002   (accessibility)
  SC-AUTH-SMOKE-001  (smoke)
  SC-AUTH-REG-001    (regression)
  SC-AUTH-EDGE-001   (edge case)
  SC-AUTH-PERF-001   (performance)
```

`AREA` = short code for the feature area (AUTH, PAYMENT, ORDER, PROFILE, ADMIN, etc.)
`TYPE` = test type abbreviation
`NNN` = zero-padded sequential within type

---

## Step 3 — Generate Scenarios Per Test Type

For every type in the confirmed `test_types` list, generate a full scenario set. **Do not stop early. Do not merge types.**

---

### 3A — Positive Scenarios

**Goal:** Every valid input combination that should succeed.

For each user flow, user role, and valid input class:
1. Identify all distinct valid input classes (equivalence partitioning)
2. Write one scenario per class × role × flow variant
3. Include a secondary DB/API verification step for every write action

**Minimum yield:** 1 scenario per user role × per user flow entry point × per valid input class.

Example set for a login flow with 2 roles, 3 login methods:
```
SC-AUTH-POS-001: recruiter logs in via email+password
SC-AUTH-POS-002: recruiter logs in via Google OAuth
SC-AUTH-POS-003: recruiter logs in via SSO
SC-AUTH-POS-004: admin logs in via email+password
SC-AUTH-POS-005: admin logs in via Google OAuth
SC-AUTH-POS-006: admin logs in with remember-me → 30d session
SC-AUTH-POS-007: user with previously locked account (now unlocked) logs in
SC-AUTH-POS-008: user on mobile viewport logs in (responsive check)
```

---

### 3B — Negative Scenarios

**Goal:** Every invalid input or unauthorized action that should fail with the correct error.

Generate from:
1. Each required field: empty, whitespace-only, null
2. Each field: wrong type (number where string expected, string where number expected)
3. Each credential: wrong value, expired, revoked, mismatched
4. Each permission boundary: authenticated but unauthorized role
5. Each business rule: violated precondition, out-of-range value
6. Each state: wrong state for the action (e.g. paying for an already-paid order)

**Every negative scenario must assert the exact error message or HTTP status code from the PRD or tech plan.** "Error is shown" is not an assertion. "Error message 'Invalid email or password' is shown" is.

Minimum: 3–5 negative scenarios per input field, 2–3 per business rule, 2–3 per permission boundary.

---

### 3C — Boundary Value Analysis

**Goal:** Test at and around every numeric, length, date, or count boundary.

For every bounded input in the PRD or tech plan, generate 4 scenarios:
- At minimum (min) → should succeed
- At minimum − 1 (min−1) → should fail
- At maximum (max) → should succeed
- At maximum + 1 (max+1) → should fail or be clamped

Additional boundaries: first valid, last valid, first invalid below, first invalid above.

Example: password length 8–128 chars:
```
SC-AUTH-BVA-001: 8-char password → accepted
SC-AUTH-BVA-002: 7-char password → rejected ("Password must be at least 8 characters")
SC-AUTH-BVA-003: 128-char password → accepted
SC-AUTH-BVA-004: 129-char password → rejected or truncated
SC-AUTH-BVA-005: 1-char password → rejected
SC-AUTH-BVA-006: 0-char password → same as empty → validation error
```

---

### 3D — Edge Case Scenarios

**Goal:** Unusual-but-valid inputs, race conditions, empty states, data extremes.

Generate from:
1. Empty states (no data yet — first use, empty list, zero results)
2. Unicode, emoji, RTL text, special characters in text fields
3. Concurrent actions (two users modifying same record simultaneously)
4. Large payloads (maximum file size, maximum list length)
5. Network interruption mid-flow (if testable — mark `may_be_manual: true` if not automatable)
6. Timezone / locale edge cases if dates are involved
7. Duplicate submission (double-click, double-POST)
8. Session expiry mid-flow

---

### 3E — Smoke Scenarios

**Goal:** Fastest possible sanity check — critical paths only.

Pick 1–2 scenarios per major feature area that prove the feature is basically working. These run first in every CI pipeline.

```yaml
test_type: smoke
critical: true
timeout_ms: 5000   # faster than standard scenarios
```

Smoke scenarios are a SUBSET of positive scenarios, not a separate test. Re-use the most representative positive scenario ID as a smoke tag rather than writing new scenarios, or write minimal new ones.

---

### 3F — Regression Scenarios

**Goal:** Verify existing functionality that must not break due to this change.

From `qa-analysis.md` Q5 answers (existing flows + codebase scan Tier 1 hubs):
1. Map each existing flow to at least 1 regression scenario
2. Focus on integration points that this change touches (shared DB tables, shared API routes, shared cache keys)
3. Reference existing scenario IDs from the previous test suite where possible

```yaml
test_type: regression
regression_for: "SC-EXISTING-AUTH-001 — login flow before this change"
```

---

### 3G — Security Scenarios (OWASP Top 10)

**Goal:** Test each relevant OWASP category against every input surface.

For web and API surfaces, generate scenarios for each applicable category:

| OWASP Category | Scenario types to generate |
|---|---|
| A01 Broken Access Control | Access protected route without auth; access other user's resource |
| A02 Cryptographic Failures | Check session token not in URL; check sensitive fields masked in logs/responses |
| A03 Injection | SQLi in every text input; XSS payload in every text input; path traversal in file inputs |
| A04 Insecure Design | Business logic bypass (skip payment step, skip verification step) |
| A05 Security Misconfiguration | Error messages don't expose stack traces or DB details |
| A07 Auth Failures | Brute force → lockout; expired token rejected; password reset token single-use |
| A09 Logging Failures | Verify failed login is logged; verify PII not in logs |

Generate at minimum 2 scenarios per applicable OWASP category per input surface.

```yaml
scenario_id: SC-AUTH-SEC-003
test_type: security
owasp_ref: "A07 — Identification and Authentication Failures"
description: "10 consecutive failed logins trigger account lockout"
```

---

### 3H — Accessibility Scenarios (WCAG 2.1 AA)

**Goal:** Test WCAG 2.1 Level AA compliance for every interactive component.

For web and mobile surfaces:

| WCAG Criterion | Scenario |
|---|---|
| 1.4.3 Contrast | Assert text elements meet 4.5:1 contrast ratio |
| 2.1.1 Keyboard | Tab through entire flow without mouse — every action reachable |
| 2.4.3 Focus Order | Tab order matches visual order |
| 2.4.7 Focus Visible | Focus indicator visible on every interactive element |
| 3.3.1 Error Identification | Error messages identify the field with the error |
| 3.3.2 Labels | Every input has an associated label |
| 4.1.2 ARIA | Buttons, inputs, dialogs have correct ARIA roles |
| 4.1.3 Status Messages | Success/error status announced to screen reader |

```yaml
scenario_id: SC-AUTH-A11Y-001
test_type: accessibility
wcag_ref: "2.1.1 Keyboard"
description: "Login form fully operable via keyboard only"
steps:
  - action: navigate
    target: "{{ BASE_URL }}/login"
    expected: "login page loaded"
  - action: keyboard_tab
    target: "body"
    expected: "focus on email input"
  - action: keyboard_tab
    target: "email-input"
    expected: "focus moves to password input"
  - action: keyboard_tab
    target: "password-input"
    expected: "focus moves to submit button"
  - action: keyboard_enter
    target: "submit-button"
    expected: "form submitted"
```

---

### 3I — Performance Scenarios

Generate only if `performance` was selected in Q1. For each SLA specified in `shared-dev-spec.md`:

```yaml
scenario_id: SC-AUTH-PERF-001
test_type: performance
sla_ref: "shared-dev-spec.md § SLA: login API P95 < 300ms"
description: "Login API responds within SLA under normal load"
steps:
  - action: http_post
    target: "{{ API_BASE_URL }}/api/v1/auth/login"
    body: { email: "{{ TEST_USER_EMAIL }}", password: "{{ TEST_PASSWORD }}" }
    expected_status: 200
    assert_duration_ms_lte: 300
```

---

## Step 4 — Write YAML Files

**One file per surface per feature area.** Do not bundle all types into one file.

```
eval/
  web-auth-positive.yaml
  web-auth-negative.yaml
  web-auth-boundary.yaml
  web-auth-edge.yaml
  web-auth-smoke.yaml
  web-auth-regression.yaml
  web-auth-security.yaml
  web-auth-accessibility.yaml
  api-auth-positive.yaml
  api-auth-negative.yaml
  api-auth-security.yaml
  db-auth-positive.yaml
  ...
```

Each file header:

```yaml
# Generated by qa-write-scenarios v2.0
# task_id: <task-id>
# generated_at: <ISO8601>
# test_type: positive
# surface: web
# feature_area: auth
# prd_ref: prd-locked.md
# tech_plans: [backend-api-tech-plan.md, web-dashboard-tech-plan.md]
# scenario_count: N

scenarios:
```

---

## Step 5 — Count Audit

After all files are written, run a mandatory count audit:

```bash
echo "=== SCENARIO COUNT AUDIT ==="
for f in ~/forge/brain/prds/<task-id>/eval/*.yaml; do
  COUNT=$(grep -c "scenario_id:" "$f")
  echo "$f: $COUNT scenarios"
done
TOTAL=$(grep -rh "scenario_id:" ~/forge/brain/prds/<task-id>/eval/ | wc -l)
echo "TOTAL: $TOTAL scenarios"
```

Produce a coverage matrix:

```markdown
## Coverage Matrix

| Feature Area | Positive | Negative | BVA | Edge | Smoke | Regression | Security | A11Y | Total |
|---|---|---|---|---|---|---|---|---|---|
| Auth         | 8        | 12       | 6   | 5    | 2     | 4          | 8        | 6    | 51    |
| Payment      | 10       | 15       | 8   | 6    | 2     | 5          | 10       | 4    | 60    |
| Orders       | 7        | 10       | 5   | 4    | 2     | 3          | 6        | 3    | 40    |
| **Total**    | 25       | 37       | 19  | 15   | 6     | 12         | 24       | 13   | **151** |
```

**If any confirmed test type has 0 scenarios for an in-scope feature area: STOP. Fill the gap before committing.**

---

## Step 6 — Scenarios Manifest

Write `~/forge/brain/prds/<task-id>/qa/scenarios-manifest.md`:

```markdown
# Scenarios Manifest

**task_id:** <task-id>
**generated_at:** <ISO8601>
**total_scenarios:** <N>
**test_types:** [list]
**surfaces:** [list]

## Coverage Matrix
[paste from count audit]

## Runtime Variables Required
| Variable | Used in |
|---|---|
| BASE_URL | all web scenarios |
| API_BASE_URL | all api scenarios |
| TEST_USER_EMAIL | auth scenarios |
| TEST_PASSWORD | auth scenarios |
| DEVICE_ID | android scenarios |

## Surfaces N/A
- ios: not in PRD scope (confirmed in qa-analysis.md Q2)
- kafka: no event bus in tech plans
```

---

## Step 7 — Log Gate

```bash
echo "[QA-SCENARIOS] task_id=<task-id> scenarios=<N> types=<list> surfaces=<list> files=<n> status=WRITTEN" \
  >> ~/forge/brain/prds/<task-id>/qa-pipeline.log

git -C ~/forge/brain add prds/<task-id>/eval/ prds/<task-id>/qa/scenarios-manifest.md
git -C ~/forge/brain commit -m "qa: scenarios for <task-id> — <N> total, types=<list>"
```

**HARD-GATE:** Do not mark complete until:
- [ ] Count audit passed — no confirmed type has 0 scenarios for in-scope features
- [ ] No `TODO`, `TBD`, or placeholder targets anywhere
- [ ] Coverage matrix written and complete
- [ ] `scenarios-manifest.md` committed
- [ ] `[QA-SCENARIOS]` logged with total count

---

## Scenario YAML Full Template

```yaml
scenario_id: SC-AUTH-NEG-003
test_type: negative
feature_area: auth
surface: web
driver: eval-driver-web-cdp
prd_ref: "prd-locked.md § Requirement 4.2"
tech_plan_task: "web-dashboard-tech-plan.md § Task W-08"
description: "Login attempt with empty password field shows validation error"
critical: false
timeout_ms: 8000
failure_mode: continue
requires_device: false

steps:
  - action: navigate
    target: "{{ BASE_URL }}/login"
    expected: "login page loaded"
  - action: type
    target: "[data-testid='email-input']"
    value: "{{ TEST_USER_EMAIL }}"
    expected: "email populated"
  - action: click
    target: "[data-testid='submit-btn']"
    expected: "form submit attempted"
  - action: assert_element
    target: "[data-testid='password-error']"
    expected: "error message 'Password is required' visible"
  - action: assert_element_absent
    target: "[data-testid='dashboard']"
    expected: "user NOT redirected to dashboard"
```

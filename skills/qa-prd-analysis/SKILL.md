---
name: qa-prd-analysis
description: "WHEN: Before generating QA test cases from a PRD. Loads ALL brain artifacts first (PRD, tech plans, scan, contracts, product topology), then runs a structured interrogation to lock test types, surfaces, coverage depth, and all open ambiguities before a single scenario is written."
type: rigid
requires: [brain-read]
version: 2.0.1
preamble-tier: 3
triggers:
  - "analyze PRD for QA"
  - "PRD test analysis"
  - "QA requirements analysis"
  - "what test cases should we write"
  - "start QA analysis"
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
  - mcp__*
---

# QA PRD Analysis

**HARD-GATE:** ALL brain artifacts must be loaded BEFORE asking the user any question. Questions asked without brain context are generic and waste the user's time. Brain-loaded questions are specific, informed, and resolve real ambiguities.

**HARD-GATE:** PRD analysis + interrogation answers must be written to brain before bulk scenario generation (`qa-write-scenarios`) proceeds. Chat-only analysis is not valid.

---

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I'll ask the user about test types before reading the PRD" | Questions without context are guesses. The PRD, tech plans, and scan tell you which test types actually apply. Ask after loading. |
| "The PRD is short, I can infer coverage" | Short PRDs hide implicit business rules and integration edges. Every gap is a future production defect. |
| "Happy path + one negative is enough" | Incident postmortems consistently show permission, boundary, concurrency, and error-recovery paths cause the most P1s. |
| "I'll write tests while I read" | Parallel read-and-write produces shallow cases with wrong priorities. Analysis must close before authoring. |
| "20-30 test cases is reasonable" | A single feature with 5 input fields, 3 user roles, and 4 error conditions yields 50+ cases with proper technique. 20-30 is always incomplete. |
| "I'll skip accessibility/security — not in scope" | Accessibility is a legal requirement in many jurisdictions. Security is always in scope for any data-handling feature. Both require explicit user waiver to omit, not silent skipping. |
| "Cross-functional impact is backend's problem" | UI, API, cache, events, and search change together. Analysis that ignores surfaces ships blind spots. |
| "I'll skip the brain load — I remember the PRD" | Memory is not a brain artifact. The scan, contracts, and tech plans change the picture every time. Load fresh. |

**If you are thinking any of the above, you are about to violate this skill.**

## Pre-Invocation Checklist

Before invoking this skill, verify:

- [ ] `task_id` is known — `prd-locked.md` must exist in brain before analysis begins
- [ ] Product slug is known — needed to resolve `product.md` and surface list for Q2
- [ ] Brain is accessible: `~/forge/brain/prds/<task-id>/` and `~/forge/brain/products/<slug>/` readable
- [ ] You have NOT already asked the user any test-related questions this session — Step 0 brain load comes first

## Pre-Implementation Checklist

Before asking the first question (Step 0.5):

- [ ] All sub-steps of Step 0 completed: product topology, PRD, shared-dev-spec, tech plans, contracts, SCAN.json, existing QA artifacts all read
- [ ] Internal summary built (features in scope, surfaces, existing coverage, SLAs, Tier 1 hubs)
- [ ] Q1 pre-selections derived from actual PRD content — not from generic defaults
- [ ] Q2 surface list filtered to what appears in `product.md` — not a generic list

## Post-Implementation Checklist

Before marking this skill complete:

- [ ] All 7 questions answered (or risk-accepted with owner name on unanswered items)
- [ ] `qa-analysis.md` written to `brain/prds/<task-id>/qa/qa-analysis.md`
- [ ] `test_types`, `surfaces`, and `coverage_depth` fields present in `qa-analysis.md` frontmatter
- [ ] Coverage map per test type written in `qa-analysis.md` body (Step 6)
- [ ] `qa-analysis.md` committed to brain with descriptive commit message
- [ ] If MCP TMS used: existing test cases from Jira/TestRail loaded and referenced in Step 5 gaps analysis

---

## Cross-References

- **`brain-read`** — prerequisite skill; ensures product topology, PRD, tech plans, and SCAN.json are loaded before this analysis begins.
- **`qa-write-scenarios`** — downstream skill; consumes `qa-analysis.md` written here to generate the maximum-count eval YAML scenario set.
- **`qa-pipeline-orchestrate`** — the orchestrator that invokes this skill at QA-P2 (scenario generation phase).
- **`eval-scenario-format`** — the canonical YAML schema that the coverage plan in Step 6 must anticipate (scenario IDs, test_type fields, surface routing).

---

## MCP Integration

This skill may invoke MCP tools when configured:

| MCP Server | Use |
|---|---|
| Jira MCP (`mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql`) | Search for existing Jira test issues (Xray) linked to the PRD's Jira epic; use results in Step 5 (Reuse section) to avoid duplicating existing coverage |
| Confluence MCP (`mcp__claude_ai_Atlassian__getConfluencePage`) | Read acceptance criteria or test strategy pages linked from the PRD |
| TestRail MCP | Fetch existing test case IDs for the feature to populate the Reuse section in Step 5 |

**When to invoke Jira MCP:** If `prd-locked.md` contains a `jira_epic:` or `jira_issue:` field, search for existing Xray test issues before writing the coverage map. Record found test IDs in `qa-analysis.md` under `existing_tests`.

---

## Iron Law

```
LOAD BRAIN FIRST. ASK QUESTIONS SECOND. WRITE ANALYSIS THIRD.
NO QUESTION IS ASKED UNTIL EVERY AVAILABLE BRAIN ARTIFACT IS READ.
NO TEST CASE IS AUTHORED UNTIL EVERY OPEN QUESTION IS ANSWERED OR EXPLICITLY RISK-ACCEPTED.
7 QUESTIONS IS THE MINIMUM — NOT THE MAXIMUM. KEEP ASKING UNTIL ZERO AMBIGUITIES REMAIN.
20-30 SCENARIOS IS A FAILURE. EXHAUSTIVE COVERAGE IS THE ONLY ACCEPTABLE STANDARD.
```

## Red Flags — STOP

- **You are about to ask the user a question without having read prd-locked.md first** — STOP. Load brain. Then ask.
- **Business rules copied as prose with no testable implication** — STOP. Every rule needs an observable pass/fail signal.
- **Zero integration or dependency section** — STOP. Real features touch more than one system. Always.
- **Test type selection not recorded in qa-analysis.md** — STOP. Downstream skills must know which types were selected to generate the right scenarios.
- **Surface selection not explicit** — STOP. "Web" and "mobile" are not the same surface. Both must be called out if both are in scope.
- **Analysis written only in chat** — STOP. Write to brain. Chat is ephemeral.
- **Questions only in `qa-analysis.md` or only via AskQuestion modal with no pasted text in the assistant message** — STOP. User must see Q1–Q7 in the visible reply (**Step 0.5 HARD-GATE — Questions visible in chat**).

---

## Step 0 — Brain Preflight: Load Everything Before Asking Anything

**This step is mandatory. Do not skip any sub-step. Do not ask the user anything until this step is complete.**

```bash
BRAIN=~/forge/brain
TASK=<task-id>

# 1. Product topology
cat "$BRAIN/products/$SLUG/product.md" 2>/dev/null

# 2. Locked PRD — the source of all requirements
cat "$BRAIN/prds/$TASK/prd-locked.md"

# 3. Shared dev spec — cross-surface contracts and SLAs
cat "$BRAIN/prds/$TASK/shared-dev-spec.md" 2>/dev/null

# 4. All tech plans — concrete routes, schemas, components, task IDs
ls "$BRAIN/prds/$TASK/tech-plans/" 2>/dev/null
for f in "$BRAIN/prds/$TASK/tech-plans/"*.md; do
  echo "=== $f ===" && cat "$f"
done

# 5. Contracts
ls "$BRAIN/products/$SLUG/contracts/" 2>/dev/null
for f in "$BRAIN/products/$SLUG/contracts/"*.md; do
  echo "=== $f ===" && cat "$f"
done

# 6. Codebase scan (architecture context)
cat "$BRAIN/products/$SLUG/codebase/SCAN.json" 2>/dev/null
cat "$BRAIN/products/$SLUG/codebase/index.md" 2>/dev/null

# 7. Existing QA artifacts (avoid duplication)
ls "$BRAIN/prds/$TASK/qa/" 2>/dev/null
cat "$BRAIN/prds/$TASK/qa/manual-test-cases.csv" 2>/dev/null
ls "$BRAIN/prds/$TASK/eval/" 2>/dev/null
```

After reading, build an internal summary:
- Features in scope (from PRD)
- Surfaces present in product (from product.md)
- Existing test coverage (from qa/ and eval/)
- Contracts and SLAs in play (response time, data retention, error codes)
- Architecture complexity (from scan — Tier 1 hubs = highest-risk surfaces)

**Do NOT proceed to Step 0.5 until this summary is built.**

---

## Step 0.5 — QA Session Interrogation

Using the brain context from Step 0, run a structured interrogation. Every question is informed by what was just read. Do not ask questions the brain already answers.

**HARD-GATE — Questions visible in chat:** The human must **see the full interrogation in the chat transcript**. In the **same assistant turn** where you ask anything:

1. **Paste the complete Q1–Q7 blocks** (headings + bullets + checkboxes / options as written below) **in normal assistant markdown** — the thread must read clearly without opening `qa-analysis.md` or the brain.
2. **Then** you may use **`AskUserQuestion`** / **`AskQuestion`** (Cursor) for structured answers — but **never** as a substitute for (1). If the UI only shows a modal, the user still gets the full text above it in the message.
3. **Never** put questions only in `qa-analysis.md`, only inside a tool call, or only in a file write — chat-first, brain second.

**Ask ALL of the following in a single message — do not drip questions one at a time. These 7 questions are the mandatory minimum. After the user answers, review those answers alongside your brain analysis and ask any additional questions that arise — in a single follow-up message. Keep asking until zero ambiguities remain. There is no upper question limit.**

---

### Q1 — Test Types (mandatory)

Show the full menu with brain-informed recommendations:

```
Which test types do you want for this QA run?
[Based on reading the PRD + tech plans, I recommend: ✓ items below]

Functional Testing
  ☑ Positive / Happy Path     — valid inputs, expected success flows
  ☑ Negative                  — invalid inputs, error handling, rejections
  ☑ Boundary Value Analysis   — at and around input limits (min, max, min±1, max±1)
  ☑ Equivalence Partitioning  — representative values per input class
  ☑ Edge Cases                — unusual-but-valid inputs, empty states, concurrency

Non-Functional Testing
  ☑ Smoke                     — critical path quick sanity (run first, fast)
  ☑ Regression                — verify existing behavior not broken by this change
  ○ Performance / SLA         — response times against SLA thresholds [recommend if SLA in spec]
  ○ Compatibility             — cross-browser, device sizes, OS versions [recommend if multi-platform]

Security Testing (OWASP Top 10 for this surface)
  ☑ Authentication / AuthZ    — login bypass, privilege escalation, session fixation
  ☑ Input Validation          — SQLi, XSS, path traversal in all input fields
  ○ Sensitive Data Exposure   — tokens in logs, unmasked fields, insecure storage [recommend if PII]
  ○ Rate Limiting / DoS       — brute force, request flooding protection [recommend if auth surface]

Accessibility (WCAG 2.1 AA)
  ○ Keyboard Navigation       — all flows reachable without mouse
  ○ Screen Reader             — ARIA labels, landmark roles, focus management
  ○ Color Contrast            — 4.5:1 for normal text, 3:1 for large text
  ○ Focus Indicators          — visible focus ring on all interactive elements

Select all that apply. Mark ○ items as yes/no. Or type "all" for maximum coverage.
```

Adjust the pre-checked (☑) items based on what the PRD actually contains. Pre-check an item if the PRD or tech plans have clear scope for it. Leave ○ if absent from PRD unless it is always required (positive, negative, edge case are always required).

---

### Q2 — Surfaces (mandatory)

Show only surfaces that exist in `product.md` for this product:

```
Which surfaces should scenarios be generated for?
[Surfaces registered in product.md for <slug>:]

  ☑ Web ({{ web-dashboard repo }}) — browser via Chrome DevTools Protocol
  ☑ API ({{ backend-api repo }})   — REST/GraphQL via HTTP driver
  ○ Android ({{ app-mobile repo }}) — ADB + UIAutomator / Appium MCP
  ○ iOS ({{ app-mobile repo }})     — XCTest / Appium MCP
  ☑ Database (MySQL/Postgres)       — schema and data integrity checks
  ○ Cache (Redis)                   — key presence, TTL, invalidation
  ○ Event Bus (Kafka)               — event publish/consume verification
  ○ Search (Elasticsearch)          — index update, query result checks

Pre-checked surfaces appear in both the PRD and product.md.
Answer: which surfaces should have scenarios generated? (or "all")
```

---

### Q3 — Coverage Depth

```
Coverage depth for this run?

  A) Smoke only       — critical path, fast (10–20 scenarios total)
  B) Standard         — happy + negative + boundary per feature (50–100+ scenarios)
  C) Comprehensive    — all types selected in Q1, maximum coverage, no gaps
                        (100–300+ scenarios depending on PRD size)

[Recommended: C — Comprehensive, based on <reason from PRD e.g. "payment feature with PII"]
```

---

### Q4 — Feature Priority

Based on the PRD sections read, list the top feature areas and ask:

```
Which feature areas need the highest test density?
[From PRD, I identified these feature areas:]

  1. Authentication (login/logout/session)
  2. Payment checkout flow
  3. Order management
  4. User profile / settings
  5. Admin dashboard

Mark priority: High / Medium / Low per area, or "all high".
High = maximum scenario count. Medium = standard. Low = smoke only.
```

---

### Q5 — Regression Scope

```
For regression testing, which existing functionality must not break?
[From codebase scan, I see these Tier 1 architectural hubs that touch this feature:]
  - auth.service.ts (referenced by 12 modules)
  - payment.service.ts (referenced by 8 modules)
  - user.repository.ts (referenced by 9 modules)

List any additional areas to regression-test, or confirm the above is complete.
```

Only ask this if codebase scan is present. If absent, ask: "List any existing flows that must not break with this change."

---

### Q6 — Open Ambiguities

Based on PRD reading, list every ambiguity found:

```
I found the following open questions in the PRD. Answer each:

  1. [<specific ambiguity from PRD, e.g. "PRD says 'validate email' but doesn't specify the format rule">]
  2. [<specific ambiguity, e.g. "SLA not specified for checkout API — what is the P95 target?">]
  3. [<specific ambiguity, e.g. "Error message for duplicate email: what exact text?">]
  ...

Answer each, or mark as 'accept risk' with your name.
```

Generate this list entirely from the PRD read in Step 0 — do not ask generic questions like "any edge cases I should know about?" that the user must answer from scratch. You read the PRD — find the gaps yourself.

---

### Q7 — Environment and Data

```
Test environment details (I'll use these to write concrete test data into scenarios):

  a) Test user credentials format? (e.g. qa+{n}@example.com / password format)
  b) Test data state: seeded DB or agent creates data during the test?
  c) Any third-party services to stub/mock? (e.g. payment gateway, SMS OTP)
  d) Known flaky areas or test isolation issues to work around?
```

---

**Wait for answers before proceeding to Step 1. After the user replies, review all answers against your brain analysis and identify any new ambiguities the answers surfaced. If any exist, ask them all in one follow-up message. Repeat until no ambiguities remain. Only then proceed to Step 1.**

Record all Q&A verbatim in the output artifact. Do not proceed on partial answers — ask again for any unanswered item. There is no question limit: every open ambiguity must be resolved before a single scenario is written.

---

## Step 1 — Ingest and Scope

After interrogation answers are received:

1. Record product name / feature name, version or slice, in-scope vs out-of-scope.
2. Record confirmed test types (from Q1 answers).
3. Record confirmed surfaces (from Q2 answers).
4. Record coverage depth (from Q3).
5. Record feature priorities (from Q4).

---

## Step 2 — Section-by-Section Extraction

For **each** major PRD section:

1. **Main scenarios** — user-visible flows and admin/operator flows.
2. **Business rules** — each rule gets a "testable implication" note (observable pass/fail signal).
3. **System interactions** — APIs, DB, cache, search, queues, third parties.
4. **Edge cases** — boundaries, empty states, concurrency, race condition hints.
5. **Error conditions** — expected HTTP codes, error messages, rollback behavior.

---

## Step 3 — Cross-Functional Impact

For each feature or change:

1. Dependencies on existing systems (from tech plans).
2. Data flow changes (create/read/update/delete — from DB tech plan).
3. Permission/role changes (entitlement matrix if applicable).
4. Integration contracts that are touched (from contracts/).
5. **Preservation list**: what must NOT regress (from Q5 answers + codebase scan hubs).

---

## Step 4 — Test Scenario Matrix

Build a full matrix:

`Feature Areas × Test Types × Surfaces × User Roles × States × Input Partitions`

Use **test design techniques** to ensure completeness:

| Technique | When to apply |
|---|---|
| **Equivalence Partitioning** | Any input field — group valid and invalid classes |
| **Boundary Value Analysis** | Any numeric, string-length, or date input — test min, max, min−1, max+1 |
| **Decision Table** | Business rules with multiple conditions (e.g. role=admin AND status=active) |
| **State Transition** | Any entity with a state machine (order status, user status, payment state) |
| **Pairwise / Combinatorial** | Multiple independent inputs — use pairwise to cover interactions without factorial explosion |
| **Error Guessing** | Known failure patterns from production, similar features, OWASP |
| **Use Case Testing** | All alternate and exception flows in every use case, not just main flow |

**Minimum scenario expectations per feature area (enforce, do not reduce):**

| Feature complexity | Minimum scenarios |
|---|---|
| Simple CRUD (1 entity, 2-3 fields) | 25–40 |
| Medium (multi-field form, validation, roles) | 50–80 |
| Complex (multi-step flow, payment, auth) | 100–150 |
| Cross-surface end-to-end | +20–30 per surface added |

These are **floors**, not targets. Exceed them freely; never fall below.

---

## Step 5 — Gaps, Reuse, Conflicts

1. **Gaps** — PRD requirements not yet covered by any existing test.
2. **Reuse** — existing scenarios that still apply (list by ID).
3. **Deprecated** — existing scenarios contradicted by the PRD (flag for user).
4. **Conflicts** — PRD vs contract vs tech plan contradictions (STOP; resolve before proceeding).

---

## Step 6 — Coverage Map by Test Type

For each confirmed test type from Q1, write an explicit coverage plan:

```markdown
### Smoke Coverage
- SC-AUTH-SMOKE-001: Login success → dashboard loads
- SC-PAYMENT-SMOKE-001: Add to cart → checkout → order created

### Positive Coverage
- SC-AUTH-POS-001: Login with valid email + password
- SC-AUTH-POS-002: Login via Google OAuth
- SC-AUTH-POS-003: Login with "remember me" checked → session persists 30d
...

### Negative Coverage
- SC-AUTH-NEG-001: Login with wrong password → error message shown
- SC-AUTH-NEG-002: Login with unregistered email → error message shown
- SC-AUTH-NEG-003: Login with empty email → field validation
- SC-AUTH-NEG-004: Login with empty password → field validation
- SC-AUTH-NEG-005: Login with SQL injection in email field → rejected
...

### Boundary Coverage
- SC-AUTH-BVA-001: Password at minimum length (8 chars) → accepted
- SC-AUTH-BVA-002: Password at min−1 (7 chars) → rejected
- SC-AUTH-BVA-003: Password at maximum length (128 chars) → accepted
- SC-AUTH-BVA-004: Password at max+1 (129 chars) → truncated or rejected
- SC-AUTH-BVA-005: Email at maximum length (254 chars) → accepted
...

### Security Coverage
- SC-AUTH-SEC-001: SQL injection in email field
- SC-AUTH-SEC-002: XSS payload in email field
- SC-AUTH-SEC-003: Brute force 10 attempts → account locked
- SC-AUTH-SEC-004: Session token in URL → rejected
- SC-AUTH-SEC-005: Expired JWT → 401 returned
...

### Accessibility Coverage
- SC-AUTH-A11Y-001: Tab through login form → all fields reachable
- SC-AUTH-A11Y-002: Error message announced by screen reader
- SC-AUTH-A11Y-003: Submit button accessible via keyboard Enter
...
```

Complete this map for every feature area before calling this skill done.

---

## Step 7 — Final Clearance

**HARD-GATE:** Before writing output:

- [ ] Every open Q from Step 0.5 is answered or risk-accepted with owner name
- [ ] Test types are confirmed and listed
- [ ] Surfaces are confirmed and listed
- [ ] Feature priorities are confirmed
- [ ] No remaining ambiguity in PRD business rules, error messages, or SLAs
- [ ] At least one question was asked and answered (no assumptions)

Confirm: **"Is this net-new functionality or a change to existing behavior?"** — record the answer verbatim even if the PRD implies the answer. User must say it.

---

## Output

Write to: `~/forge/brain/prds/<task-id>/qa/qa-analysis.md`

```yaml
---
id: QA-PRD-<task-id>
product: <slug>
source_prd: prd-locked.md
analysis_date: <ISO8601>
feature_class: new | existing_change
test_types: [smoke, positive, negative, boundary, edge_case, regression, security, accessibility]
surfaces: [web, api, android, ios, db, cache]
coverage_depth: comprehensive
# optional urgent patch scope (omit normally):
# hotfix_surfaces: [api, web]
---
```

Body: Executive summary (10 bullets) + all sections from Steps 1–6 + interrogation Q&A verbatim (must match what was already shown and answered in **chat** per Step 0.5).

Commit to brain:
```bash
git -C ~/forge/brain add prds/<task-id>/qa/qa-analysis.md
git -C ~/forge/brain commit -m "qa: PRD analysis for <task-id> — types=<list> surfaces=<list>"
```

---

## Surface Specification Reference

**How to specify surfaces for test case generation and execution:**

| Surface | `/qa-write` flag | `/qa-run` flag | Driver used |
|---|---|---|---|
| Web browser | `--surface web` | `--surface web` | `eval-driver-web-cdp` |
| Android app | `--surface android` | `--surface android --env DEVICE_ID=emulator-5554` | `eval-driver-android-adb` |
| iOS app | `--surface ios` | `--surface ios --env IOS_SIMULATOR_ID=booted` | `eval-driver-ios-xctest` |
| REST/GraphQL API | `--surface api` | `--surface api` | `eval-driver-api-http` |
| Database | `--surface db` | `--surface db` | `eval-driver-db-mysql` |
| Cache | `--surface cache` | `--surface cache` | `eval-driver-cache-redis` |
| All surfaces | `--surface all` | `--surface all` | all drivers |
| Web + API only | `--surface web,api` | `--surface web,api` | web-cdp + api-http |

**Surface selection in this analysis step** determines which scenario files `qa-write-scenarios` will produce. The `--surface` flag on `/qa-run` then filters which files are executed.

---

## Edge Cases

1. **PRD is a one-pager** — Still run all steps. High clarification load. Minimum scenario counts still apply.
2. **No existing test export** — Reuse/deprecation sections state "none provided." Do not reduce scope.
3. **Conflicting legal/compliance vs UX** — STOP. Escalate in writing. Do not invent resolution.
4. **PRD references unreleased backend** — Flag as environment prerequisite. Write scenarios anyway; mark `requires_env: staging-only`.
5. **User selects "smoke only"** — Acknowledge but note: smoke is not a substitute for regression and negative coverage. Write the smoke set, then ask: "Do you want to add negative + regression in the next run?"
6. **No codebase scan in brain** — Q5 falls back to asking user to name regression areas. Note `⚠ No scan — regression scope from user only`.

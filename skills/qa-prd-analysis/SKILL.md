---
name: qa-prd-analysis
description: "WHEN: Before generating QA test cases from a PRD. Loads ALL brain artifacts first (PRD, tech plans, scan, contracts, product topology), then runs a structured interrogation to lock test types, surfaces, coverage depth, and all open ambiguities before a single scenario is written."
type: rigid
requires: [brain-read]
version: 2.2.5
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

## Human input (all hosts)

**`AskUserQuestion`** in **`allowed-tools`** is canonical; map per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** on every IDE. **Step 0.5** applies **`using-forge`** **Multi-question elicitation** to coverage templates **Q1–Q8** (see **`using-forge`** **QA PRD analysis** specialization). **One primary topic per assistant turn**; after each answer **reconcile**. **Never** a full Q1–Q8 wall **plus** a meta-prompt in the **same** turn.

**Cross-cutting assistant dialogue:** **`docs/forge-one-step-horizon.md`** — **`using-forge`** **Multi-question elicitation** items **4–8** (all coverage turns; same norms repository-wide).

**HARD-GATE:** ALL brain artifacts must be loaded BEFORE asking the user any question. Questions asked without brain context are generic and waste the user's time. Brain-loaded questions are specific, informed, and resolve real ambiguities.

**HARD-GATE:** PRD analysis + interrogation answers must be written to brain before bulk scenario generation (`qa-write-scenarios`) proceeds. Chat-only analysis is not valid.

**Upstream of eval YAML:** **`qa-write-scenarios`** **Step −1** defines forward order: **`prd-locked.md`** → **this skill** (`qa-analysis.md` + chat interrogation) → **`qa-manual-test-cases-from-prd`** / CSV or waiver → **then** eval YAML. Agents must **not** ask users about **CSV/evYAML waivers** before **`prd-locked`** exists or before Step 0.5 ran in chat.

**Forbidden during Step 0.5 (Q1–Q8):** Scripted copy about **YAML before manual CSV**, **`csv_baseline_waiver_user_quote`**, “say so explicitly in your own words,” or **Forge** forbidding agent paraphrase — that is **`qa-write-scenarios`** **Step 0.0** only (scenario authoring gate after **`qa-analysis.md`** exists). Do **not** paste waiver boilerplate during coverage interrogation.

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
| "Figma is in frontmatter / PRD — I don't need to ask about design in QA interrogation" | **UI test quality needs traceability from PRD to what testers assert** — but if **planning / intake / tech plans / design/** already documented PRD↔screen↔fixture mapping, **QA must inherit and cite those artifacts**, not duplicate a second full mapping workshop. Use Q8 to **confirm + fill gaps only**. |
| "QA must rebuild the whole PRD→design matrix from zero every time" | **Violates reuse.** Council, tech plans, `shared-dev-spec`, `prd-locked` design fields, and `design/` exist precisely so downstream phases do not re-specify. Q8 is **verify completeness for test authoring**, not replace planning. |
| "I'll write `qa-analysis.md` with Q1–Q8 marked confirmed from PRD alone — user wasn't available" | **Invalid.** Step 0.5 requires interrogation **completed in chat** (**sequential / adaptive** per this skill) with real answers or explicit risk-accept. Frontmatter **`test_types` / `surfaces`** copied from defaults without a user turn is **not** confirmation — downstream YAML will claim false legitimacy. |
| "I'll paste the entire Q1–Q8 in one message **and** append **`AskQuestion`** *How should we proceed…* with options that overlap Q3/Q4 or bundle **CSV/YAML waiver**" | **Invalid UX + wrong gate.** One **primary** interaction model per turn; **waivers** belong to **`qa-write-scenarios`** / **`qa-manual-test-cases-from-prd`**, not **`qa-prd-analysis`**. **Sequential** turns only — never wall + unrelated modal. |
| "I'll offer **single bulk**, **approve recommendations**, or **hybrid** so the user can skip the back-and-forth" | **Invalid for Step 0.5.** Interrogation is **mandatorily sequential and interactive** — no menu to bypass dialogue. Speed is not a substitute for doubt closure. |
| "I must ask Q2 verbatim even though Q1 already fixed surfaces and depth" | **Invalid.** **Adaptive reconciliation** — skip or shorten template prompts when already answered; ask **net-new** doubts instead. |
| "I'll ask Q1 using only **Full / Lean / Custom** (or similar presets) **without** showing the full test-type checklist" | **Invalid.** The human must **see** every category (functional, non-functional, security, accessibility rows) to choose or waive — presets **hide capability**. Show the **full fenced Q1 menu** below first; optional presets **below** the menu are OK as shortcuts **after** visibility. |
| "I'll prepend *Why eval YAML isn't written yet* / *orphan automation* between every Step 0.5 answer" | **Invalid UX.** That ordering lecture belongs in **`qa-write-scenarios`** **Step −1** when the user **skips ahead** — **not** between Q1→Q2→Q3. Stay on the **current** question only; one-line forward pointers are OK, not essays. |
| "I'll narrate the path *QA analysis → CSV → eval YAML → /qa-run* in every Q1–Q8 message so the user sees the ‘big picture’" | **Invalid.** **`using-forge`** — **do not** mention downstream stages unless **immediate** next dependency or user asked. Step 0.5 stays **coverage-only**; **`manual-test-cases.csv`** is the **next** artifact after **`qa-analysis.md`** — name it **only** when closing Step 0.5 / handing off, **not** before every answer. |

**If you are thinking any of the above, you are about to violate this skill.**

## Pre-Invocation Checklist

Before invoking this skill, verify:

- [ ] `task_id` is known — `prd-locked.md` must exist in brain before analysis begins
- [ ] Product slug is known — needed to resolve `product.md` and surface list for Q2
- [ ] Brain is accessible: `~/forge/brain/prds/<task-id>/` and `~/forge/brain/products/<slug>/` readable
- [ ] You have NOT already asked the user any test-related questions this session — Step 0 brain load comes first

## Pre-Implementation Checklist

Before asking the first question (Step 0.5):

- [ ] All sub-steps of Step 0 completed: product topology, PRD, **terminology.md (if present)**, shared-dev-spec, tech plans, contracts, SCAN.json, existing QA artifacts all read
- [ ] Internal summary built (features in scope, surfaces, existing coverage, SLAs, Tier 1 hubs)
- [ ] Q1 pre-selections derived from actual PRD content — not from generic defaults
- [ ] Q2 surface list filtered to what appears in `product.md` — not a generic list

## Post-Implementation Checklist

Before marking this skill complete:

- [ ] Minimum **Q1–Q7** answered (or risk-accepted); **Q8** answered when **web**, **android**, or **ios** is in confirmed surfaces — or explicitly **N/A** with reason if UI truly out of scope
- [ ] **Interrogation actually happened in chat** — Q1–Q7 (+ **Q8 when Web/Android/iOS**, including **design source of truth** / reuse vs gap-fill) were **resolved turn-by-turn** (template skipped when subsumed — **document in thread**). User replied to each asked topic (or explicitly risk-accepted). **Do not** publish **`qa-analysis.md`** that says "confirmed" for interrogation items based only on agent inference from Confluence/PRD without that thread (**Step 0.5 HARD-GATE**).
- [ ] **Design / Q8:** If **web**, **android**, or **ios** in surfaces, **`design_source` in frontmatter is only valid after** the user has **seen Q8** (short reuse form or full workshop) **in chat** — not pre-filled from PRD/Figma fields alone.
- [ ] `qa-analysis.md` written to `brain/prds/<task-id>/qa/qa-analysis.md`
- [ ] `test_types`, `surfaces`, and `coverage_depth` fields present in `qa-analysis.md` frontmatter; **when UI in scope:** frontmatter or body records **`design_source`** (Figma key / brain path / MCP_INGEST) and **PRD→component mapping** summary (Step 1 expansion)
- [ ] Coverage map per test type written in `qa-analysis.md` body (Step 6)
- [ ] `qa-analysis.md` committed to brain with descriptive commit message
- [ ] If MCP TMS used: existing test cases from Jira/TestRail loaded and referenced in Step 5 gaps analysis

---

## Cross-References

- **`brain-read`** — prerequisite skill; ensures product topology, PRD, tech plans, and SCAN.json are loaded before this analysis begins.
- **`qa-write-scenarios`** — downstream skill; consumes `qa-analysis.md` written here to generate the maximum-count eval YAML scenario set. **Prerequisite order:** see **`qa-write-scenarios`** **Step −1** (never prompt eval/CSV waiver before **`prd-locked`** + this interrogation).
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
STEP 0.5: ONE INTERACTIVE TURN PER QUESTION (OR ONE FOCUSED DOUBT). AFTER EACH ANSWER — RECONCILE: SKIP REDUNDANT TEMPLATE PROMPTS; CHASE NEW DOUBTS BEFORE THE NEXT DEFAULT Q.
NO TEST CASE IS AUTHORED UNTIL EVERY OPEN QUESTION IS ANSWERED OR EXPLICITLY RISK-ACCEPTED.
ALL DIMENSIONS IN Q1–Q7 MUST BE RESOLVED (OR SUBSUMED + LOGGED); Q8 WHEN WEB/ANDROID/IOS — **REUSE** PLANNING/DESIGN ARTIFACTS WHEN PRESENT (CITE PATHS); FULL WORKSHOP ONLY FOR GAPS OR MISSING MAPPING; ELSE RECORD N/A.
KEEP ASKING UNTIL ZERO AMBIGUITIES REMAIN — NOT UNTIL YOU'VE ASKED EXACTLY EIGHT MESSAGES.
20-30 SCENARIOS IS A FAILURE. EXHAUSTIVE COVERAGE IS THE ONLY ACCEPTABLE STANDARD.
```

## Red Flags — STOP

- **You are about to ask the user a question without having read prd-locked.md first** — STOP. Load brain. Then ask.
- **Business rules copied as prose with no testable implication** — STOP. Every rule needs an observable pass/fail signal.
- **Zero integration or dependency section** — STOP. Real features touch more than one system. Always.
- **Test type selection not recorded in qa-analysis.md** — STOP. Downstream skills must know which types were selected to generate the right scenarios.
- **Surface selection not explicit** — STOP. "Web" and "mobile" are not the same surface. Both must be called out if both are in scope.
- **Analysis written only in chat** — STOP. Write to brain. Chat is ephemeral.
- **Questions only in `qa-analysis.md` or only via a blocking prompt UI with no pasted text in the assistant message** — STOP. User must see each interrogation topic **in the visible thread** before “confirmed” analysis — **one topic per turn** (plus adaptive follow-ups); **forbidden:** modal-only with no chat text (**Step 0.5 HARD-GATE — Questions visible in chat**).
- **Full Q1–Q8 wall in one message, or “single bulk / approve all” shortcuts** — STOP. Step 0.5 is **sequential interactive** only; **no** dump of all templates, **no** opt-out of turn-by-turn dialogue.
- **Full Q1–Q8 wall + a second meta `AskQuestion` (*How should we proceed…*) in the same turn** — STOP. Overloads the human and makes the modal incoherent (**Step 0.5**).
- **`design_source` / Figma / `figma_file_key` filled in `qa-analysis.md` frontmatter or body but the user never saw Q8 in chat** — STOP. Copying keys from **`prd-locked.md`** or Confluence **does not** replace the **Q8** question: the human must still **confirm** authoritative design source, reuse path, or **N/A** in thread.
- **Web/app in scope but neither inherited mapping citations nor Q8 gap-fill recorded** — STOP. Either planning already owns PRD↔UI traceability (cite it) or Q8 must supply it.
- **`qa-analysis.md` claims Q1–Q8 "confirmed" but there was no Step 0.5 chat turn** — STOP. Analysis is **invalid** for downstream **`qa-write-scenarios`** strict gates; re-run interrogation or mark body **`PROVISIONAL — interrogation not completed in chat`** and do not treat frontmatter as user-approved.

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

# 2a. Product terminology (when present) — canonical labels for assertions / steps
cat "$BRAIN/prds/$TASK/terminology.md" 2>/dev/null

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

# 8. Design / UI source (when PRD or frontmatter references UI — do not skip if figma_file_key or design_intake exists)
ls "$BRAIN/prds/$TASK/design/" 2>/dev/null
for f in "$BRAIN/prds/$TASK/design/"*.md; do [ -f "$f" ] && echo "=== $f ===" && cat "$f"; done
```

After reading, build an internal summary:
- Features in scope (from PRD)
- **Product terms** — if **`terminology.md`** exists, note `status` / `open_doubts` and which **canonical** names to use in **Q1–Q8** and downstream **Expected result** text ([docs/terminology-review.md](../../docs/terminology-review.md) — not [forge-glossary](../forge-glossary/SKILL.md))
- Surfaces present in product (from product.md)
- **PRD ↔ design / UI mapping already captured elsewhere** — `tech-plans/*.md` (components, routes, testids), `shared-dev-spec.md`, `prd-locked.md` design / Q9 anchors, `design/*.md`, Confluence/PRD tables linked in lock — note **paths + whether traceability is complete enough for test steps**
- Existing test coverage (from qa/ and eval/)
- Contracts and SLAs in play (response time, data retention, error codes)
- Architecture complexity (from scan — Tier 1 hubs = highest-risk surfaces)

**Do NOT proceed to Step 0.5 until this summary is built.**

---

## Step 0.5 — QA Session Interrogation

Using the brain context from Step 0, run a structured interrogation. Every question is informed by what was just read. Do not ask questions the brain already answers — **especially** do not re-elicit PRD↔design mapping that is **already written** in tech plans, shared spec, or `design/`; **cite it and ask for confirmation or deltas only**.

### HARD-GATE — Chat transcript before `qa-analysis.md`

The human must **see Q1–Q7 and Q8 (when UI in scope)** in the **chat thread** and answer (or risk-accept) before you write **`qa-analysis.md`** with interrogation **confirmed**. **Never** “confirm” from PRD inference alone. **Chat first, brain file second.**

### HARD-GATE — Sequential interactive interrogation (mandatory)

**How the dialogue runs**

1. **One assistant message ≈ one coverage dimension** — usually **one** of Q1–Q8 at a time, using the templates below. **Each dimension’s message includes that dimension’s full template** (e.g. **Q1** = entire test-type fence below — that is **one** topic, not “Q1–Q8”). Use **`AskUserQuestion`** / **`AskQuestion`** / **numbered options + stop** per **`using-forge`** for optional **shortcuts** only **after** the full checklist is visible where this skill requires it. **Do not** paste Q2–Q8 in the same turn as Q1.

2. **Optional opener** — You may send **one** short line of context after Step 0 (e.g. “Brain loaded for `<task-id>`; starting coverage interrogation.”) **without** any fork like “how do you want to answer?” **There is no user choice** between bulk vs sequential — sequential is **required**.

3. **After every user reply — reconcile (adaptive)**  
   - **Skip** the next template question if the answer **already resolves** that dimension (e.g. “full regression + all surfaces + exhaustive” may subsume **Q3** depth). In chat, state explicitly: *Skipped Q3 — covered by Q1/Q2 answers: …*  
   - **Insert** tailored questions for **new doubts** the reply surfaced (security edge, env constraint, design gap) **before** mechanically advancing to the next default label — **zero ambiguities** beats **checking every box**.  
   - If brain artifacts already answered a dimension (e.g. surfaces in **`product.md`**), **confirm in one short interactive prompt** rather than re-reading the entire Q2 wall verbatim.

4. **Coverage obligation** — Every **dimension** represented by Q1–Q7 must be **resolved or risk-accepted** in the transcript; **Q8** when Web/Android/iOS is in scope (or **N/A** with reason). Dimensions may be satisfied **without** asking the corresponding template if subsumed — **must** still appear in **`qa-analysis.md`** with *source: user reply Q1* or *subsumed by …*.

**Forbidden**

- Pasting **full** Q1–Q8 in one message, or offering **single bulk / approve-all-recommendations / hybrid** flows — **not allowed**.  
- A **second** blocking prompt in the same turn that **duplicates** coverage choices or bundles **CSV/YAML waiver** (that belongs to **`qa-write-scenarios`** / **`qa-manual-test-cases-from-prd`** after `qa-analysis.md`).
- **Pipeline horizon in every turn** — do **not** restate *…then manual CSV, then `eval/*.yaml`, then `/qa-run`…* while asking Q1–Q8. Per **`using-forge`**: mention **only** the **immediate** next dependency; full chain lives in **README** / **commands**, not repeated in chat.

**After** all dimensions are closed: if brain vs answers still disagree, **one** short clarification turn is OK — still **not** a full template dump.

**Never** put questions only in `qa-analysis.md`, only inside a tool call, or only in a file write — chat-first, brain second.

---

### Q1 — Test Types (mandatory)

Ask as the **first** interrogation turn after Step 0 (after optional one-line context). **Only** Q1 content in that turn — then **wait**.

**HARD-GATE — Full checklist visible:** Paste the **complete** fenced menu below (Functional → Accessibility) with brain-informed ☑/○ — **every row the skill lists**. **Forbidden:** replacing Q1 with **only** prose plus **Full / Lean CI / Custom** (or similar) **without** the full structured list above it — users cannot consent to types they cannot see. **Allowed:** **after** the full menu, add optional shortcuts (*e.g.* “Reply **All recommended**, **Lean CI**, or line-by-line yes/no”) **below** the fence — shortcuts may **not** substitute for the checklist.

Show the menu with brain-informed recommendations:

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

### Q8 — Design source of truth & PRD → UI mapping (mandatory if Web, Android, or iOS is in scope)

**Skip only if** confirmed surfaces are exclusively API/DB/cache/events/search with **no** user-visible UI for this feature — state **N/A** in chat and in `qa-analysis.md`.

**Reuse-first (do this before the full questionnaire):** If **planning / development already produced** PRD↔UI traceability — e.g. **tech plans** with screens and testids, **`shared-dev-spec.md`** user-visible behaviors, **`prd-locked.md`** design/Q9 fields, **`design/MCP_INGEST.md`** or Figma refs — then **Q8 is not a greenfield mapping exercise**. You **summarize what exists** (brain paths + section titles), list **only gaps** (missing component for a PRD bullet, unknown fixture, conflicting testid), and elicit **confirm or patch** for those gaps with **blocking interactive prompts** per **`using-forge`** when the gap is a **discrete** choice. Paste this **short form** in chat when reuse applies:

```
Q8 — Inherited PRD ↔ design mapping (confirm / gap-fill)

Already documented (read in Step 0):
  - <path#heading> — what it covers
  - ...

For QA test authoring, confirm:
  (A) Accurate as-is — proceed to cases using citations above
  (B) Needs updates — list only deltas: <gap 1>, <gap 2>, ...

If (B): answer only the gaps (authoritative source, testid, fixture, E2E order).
```

**Full Q8 workshop** — use **only** when no adequate mapping exists in brain artifacts, or after **(B)** to capture **remaining** items:

```
Design & UI (maps PRD language to what testers assert on screen):

  a) **Authoritative design source** — Figma file/key + node(s), and/or paths under brain/prds/<task-id>/design/ (e.g. MCP_INGEST.md), Lovable export — which wins when they disagree?
  b) **For each major PRD user-visible requirement** (e.g. "blacklisted banner after login", "Step 1 tab", "restricted crawl"): name the **screen or component**, **data-testid** or accessibility label if known, and **preconditions** (account state, tier, due date, feature flag).
  c) **End-to-end flow** — ordered steps from entry (e.g. login) through the assertion (e.g. banner visible on home), including **where** copy/layout must match design vs PRD prose only.
  d) **Fixtures** — which seeded users / tokens / DB rows are required so the UI can reach each state (blacklisted, overdue, L2 only, etc.)?

If Figma MCP or design files are unavailable: record **CONTEXT_GAP** and the minimum **user-supplied** screenshots or testids needed before writing UI eval YAML or manual web rows.
```

---

**Wait until every dimension** for Q1–Q7 (+ Q8 when UI in scope) is **resolved or explicitly risk-accepted**, using **sequential turns** and **adaptive skips/substitutions** as above, before proceeding to Step 1. After **each** reply, reconcile; chase **new doubts** before advancing the default Q sequence.

Record all Q&A verbatim in the output artifact (including *skipped — subsumed by …*). Do not proceed on partial answers — ask again for any unanswered item. There is no upper limit on **tailored** follow-up questions: **zero ambiguities** is the stop condition, not “asked Q8 verbatim.”

---

## Step 1 — Ingest and Scope

After interrogation answers are received:

1. Record product name / feature name, version or slice, in-scope vs out-of-scope.
2. Record confirmed test types (from Q1 or from adaptive reconciliation — cite thread).
3. Record confirmed surfaces (from Q2 / confirmation — cite thread).
4. Record coverage depth (from Q3 **or** from subsuming answers — cite *subsumed by Q…*).
5. Record feature priorities (from Q4 **or** equivalent tailored answers).
6. When UI surfaces confirmed: record **`design_source`** and the **PRD → component → precondition** matrix in `qa-analysis.md` — **either** citations to existing planning/design docs **plus** any Q8 gap-fill **or** the full Q8 matrix when none existed upstream.

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

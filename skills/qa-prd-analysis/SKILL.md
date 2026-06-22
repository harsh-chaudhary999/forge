---
name: qa-prd-analysis
description: "WHEN: Before generating QA test cases from a PRD. Loads ALL brain artifacts first (PRD, tech plans, scan, contracts, product topology), then runs a structured interrogation to lock test types, surfaces, coverage depth, and all open ambiguities before a single scenario is written."
type: rigid
requires: [brain-read]
version: 2.2.8
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

## Human input

**`AskUserQuestion`** (in **`allowed-tools`**) is the canonical blocking affordance — see **[`skills/_shared/human-input.md`](../_shared/human-input.md)**. **Step 0.5** applies **`using-forge`** **Multi-question elicitation** to coverage templates **Q1–Q8** (see **`using-forge`** **QA PRD analysis** specialization). **One primary topic per assistant turn**; after each answer **reconcile**. **Never** a full Q1–Q8 wall **plus** a meta-prompt in the **same** turn.

**Cross-cutting assistant dialogue:** **`docs/forge-one-step-horizon.md`** — **`using-forge`** **Multi-question elicitation** items **4–8**; **No defensive downstream-gate narration (repo-wide)** (no *why semantic machine eval isn’t ready* essays between Q1→Q2→… — **any** Forge phase).

**HARD-GATE:** ALL brain artifacts must be loaded BEFORE asking the user any question. Questions asked without brain context are generic and waste the user's time. Brain-loaded questions are specific, informed, and resolve real ambiguities.

**HARD-GATE:** PRD analysis + interrogation answers must be written to brain before bulk semantic automation authoring (**`/qa-write`**, **`qa-semantic-csv-orchestrate`**) proceeds. Chat-only analysis is not valid.

**Upstream of machine eval:** **`commands/qa-write.md`** / **`conductor-orchestrate`** ordering defines forward order: **`prd-locked.md`** → **this skill** (`qa-analysis.md` + chat interrogation) → **`qa-manual-test-cases-from-prd`** / CSV or waiver → **then** **`qa/semantic-automation.csv`** + manifest. Agents must **not** ask users about **CSV / automation-order waivers** before **`prd-locked`** exists or before Step 0.5 ran in chat.

**Forbidden during Step 0.5 (Q1–Q8):** Scripted copy about **automation before manual CSV**, **`csv_baseline_waiver_user_quote`**, “say so explicitly in your own words,” or **Forge** forbidding agent paraphrase — that is **`qa-manual-test-cases-from-prd`** / **`/qa-write`** **only** when that flow is active (after **`qa-analysis.md`** exists). Do **not** paste waiver boilerplate during coverage interrogation.

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
| "Figma is in frontmatter — I either skip design in QA, or rebuild the whole PRD→design matrix from zero" | **Both wrong — violates reuse.** UI test quality needs PRD→assert traceability, but council / tech plans / `shared-dev-spec` / `prd-locked` design fields / `design/` already document it. **Inherit and cite** those artifacts; Q8 is **confirm + fill gaps only**, not a second full mapping workshop. |
| "I'll write `qa-analysis.md` with Q1–Q8 marked confirmed from PRD alone — user wasn't available" | **Invalid.** Step 0.5 requires interrogation **completed in chat** (**sequential / adaptive** per this skill) with real answers or explicit risk-accept. Frontmatter **`test_types` / `surfaces`** copied from defaults without a user turn is **not** confirmation — downstream automation rows will claim false legitimacy. |
| "I'll combine a Q-template with a second **`AskUserQuestion`** in the same turn — bundling prerequisites (task-id/prd-locked), CSV/automation-order waivers, *how should we proceed* meta-options, or repeating the full chat text inside the widget" | **Invalid — dual prompt / wrong gate.** **One turn = one primary question.** Prerequisite confirms are their **own preceding turn**; **waivers** belong to **`qa-manual-test-cases-from-prd`** / **`/qa-write`**, not here. The widget carries a **short** title + options only — the long list lives in chat **once** (see **`docs/forge-one-step-horizon.md`** **No bundled unrelated decisions**). |
| "I'll offer **single bulk**, **approve recommendations**, or **hybrid** so the user can skip the back-and-forth" | **Invalid for Step 0.5.** Interrogation is **mandatorily sequential and interactive** — no menu to bypass dialogue. Speed is not a substitute for doubt closure. |
| "I must ask Q2 verbatim even though Q1 already fixed surfaces and depth" | **Invalid.** **Adaptive reconciliation** — skip or shorten template prompts when already answered; ask **net-new** doubts instead. |
| "I'll ask Q1 using only **Full / Lean / Custom** (or similar presets) **without** showing the full test-type checklist" | **Invalid.** The human must **see** every category (functional, non-functional, security, accessibility rows) to choose or waive — presets **hide capability**. Show the **full fenced Q1 menu** below first; optional presets **below** the menu are OK as shortcuts **after** visibility. |
| "Between every Step 0.5 answer I'll narrate the downstream path (*why semantic eval isn't ready*, *QA analysis → CSV → /qa-run*) so the user sees the big picture" | **Invalid — repo-wide norm** (**`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration**). Stay on the **current** question; Step 0.5 is **coverage-only**. Name the **immediate** next dependency (**`manual-test-cases.csv`**) **only** at handoff — not before every answer. |

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
- **`qa-manual-test-cases-from-prd`** — consumes **`qa-analysis.md`** to produce **`manual-test-cases.csv`**; **`qa-semantic-csv-orchestrate`** later maps automation from the same analysis where applicable.
- **`qa-pipeline-orchestrate`** — the orchestrator that invokes this skill at QA-P2 (scenario generation phase).
- **`docs/semantic-eval-csv.md`** — **Surface** / **Intent** coverage in Step 6 should anticipate how rows will map to automation (**web**, **api**, …).

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
- **Full Q1–Q8 wall + a second meta `AskUserQuestion` (*How should we proceed…*) in the same turn** — STOP. Overloads the human and makes the modal incoherent (**Step 0.5**).
- **`design_source` / Figma / `figma_file_key` filled in `qa-analysis.md` frontmatter or body but the user never saw Q8 in chat** — STOP. Copying keys from **`prd-locked.md`** or Confluence **does not** replace the **Q8** question: the human must still **confirm** authoritative design source, reuse path, or **N/A** in thread.
- **Web/app in scope but neither inherited mapping citations nor Q8 gap-fill recorded** — STOP. Either planning already owns PRD↔UI traceability (cite it) or Q8 must supply it.
- **`qa-analysis.md` claims Q1–Q8 "confirmed" but there was no Step 0.5 chat turn** — STOP. Analysis is **invalid** for downstream **`/qa-write`** / **`qa-semantic-csv-orchestrate`** strict gates; re-run interrogation or mark body **`PROVISIONAL — interrogation not completed in chat`** and do not treat frontmatter as user-approved.

---

## Step 0 — Brain Preflight: Load Everything Before Asking Anything

**This step is mandatory. Do not skip any sub-step. Do not ask the user anything until this step is complete.**

**Prefer the read-only brain MCP** when it is connected (`brain_read` for files,
`brain_list` for directory trees, `brain_recall` to find existing QA artifacts /
Jira-linked tests) — it honours the same `FORGE_BRAIN` root. The raw `cat`/`ls` block
below is the fallback when the MCP is not available.

```bash
BRAIN="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}"
TASK=<task-id>

# GUARD: the locked PRD is the source of all requirements. If it is missing/empty,
# STOP — do not interrogate. Escalate BLOCKED/NEEDS_CONTEXT back to forge-intake-gate
# / intake-interrogate (the PRD must be locked before QA analysis).
[ -s "$BRAIN/prds/$TASK/prd-locked.md" ] || echo "BLOCKED: prd-locked.md missing/empty for $TASK"

cat "$BRAIN/products/$SLUG/product.md" 2>/dev/null            # 1. product topology
cat "$BRAIN/prds/$TASK/prd-locked.md"                          # 2. locked PRD (requirements)
cat "$BRAIN/prds/$TASK/terminology.md" 2>/dev/null             # 2a. canonical labels for asserts
cat "$BRAIN/prds/$TASK/shared-dev-spec.md" 2>/dev/null         # 3. cross-surface contracts + SLAs
cat "$BRAIN/prds/$TASK/qa/manual-test-cases.csv" 2>/dev/null   # 7. existing QA (avoid dup)
for d in "prds/$TASK/tech-plans" "products/$SLUG/contracts" "prds/$TASK/design"; do
  # 4 tech-plans (routes/schemas/testids), 5 contracts, 8 design/UI (don't skip if figma_file_key set)
  for f in "$BRAIN/$d/"*.md; do [ -f "$f" ] && echo "=== $f ===" && cat "$f"; done
done
cat "$BRAIN/products/$SLUG/codebase/SCAN.json" 2>/dev/null     # 6. architecture (Tier-1 hubs)
cat "$BRAIN/products/$SLUG/codebase/index.md" 2>/dev/null
```

After reading, build an internal summary:
- Features in scope (from PRD)
- **Product terms** — if **`terminology.md`** exists, note `status` / `open_doubts` and which **canonical** names to use in **Q1–Q8** and downstream **Expected result** text ([docs/terminology-review.md](../../docs/terminology-review.md) — not [forge-glossary](../forge-glossary/SKILL.md))
- Surfaces present in product (from product.md)
- **PRD ↔ design / UI mapping already captured elsewhere** — `tech-plans/*.md` (components, routes, testids), `shared-dev-spec.md`, `prd-locked.md` design / Q9 anchors, `design/*.md`, Confluence/PRD tables linked in lock — note **paths + whether traceability is complete enough for test steps**
- Existing test coverage (from **`qa/`** — manual CSV, semantic automation, logs)
- Contracts and SLAs in play (response time, data retention, error codes)
- Architecture complexity (from scan — Tier 1 hubs = highest-risk surfaces)

**Do NOT proceed to Step 0.5 until this summary is built.**

---

## Step 0.5 — QA Session Interrogation

Using the brain context from Step 0, run a structured interrogation. Every question is informed by what was just read. Do not ask questions the brain already answers — **especially** do not re-elicit PRD↔design mapping that is **already written** in tech plans, shared spec, or `design/`; **cite it and ask for confirmation or deltas only**.

### HARD-GATE — Chat transcript before `qa-analysis.md`

The human must **see Q1–Q7 and Q8 (when UI in scope)** in the **chat thread** and answer (or risk-accept) before you write **`qa-analysis.md`** with interrogation **confirmed**. **Never** “confirm” from PRD inference alone. **Chat first, brain file second.**

**Multi-session tracking:** If Q1–Q8 span multiple chat sessions (e.g., Q1–Q3 in Session 1, Q4–Q8 in Session 2), record session boundaries in `qa-analysis.md` frontmatter:

```yaml
interrogation_sessions:
  - date: "<ISO8601-date>"
    session_note: "Q1–Q3 covered (test types, surfaces, scope)"
  - date: "<ISO8601-date>"
    session_note: "Q4–Q8 covered (security, performance, design mapping)"
```

This field is informational (no machine validation) but enables auditors to verify which questions were answered when. If all questions were answered in one session, a single entry suffices.

### HARD-GATE — Sequential interactive interrogation (mandatory)

**How the dialogue runs**

1. **One assistant message ≈ one coverage dimension** — usually **one** of Q1–Q8 at a time, using the templates in [reference/interrogation-templates.md](reference/interrogation-templates.md). **Each dimension’s message includes that dimension’s full template** (e.g. **Q1** = entire test-type fence — that is **one** topic, not “Q1–Q8”). Use **`AskUserQuestion`** (see [`skills/_shared/human-input.md`](../_shared/human-input.md)) for optional **shortcuts** only **after** the full checklist is visible where this skill requires it. **Do not** paste Q2–Q8 in the same turn as Q1.

2. **Optional opener** — You may send **one** short line of context after Step 0 (e.g. “Brain loaded for `<task-id>`; starting coverage interrogation.”) **without** any fork like “how do you want to answer?” **There is no user choice** between bulk vs sequential — sequential is **required**.

3. **After every user reply — reconcile (adaptive)**  
   - **Skip** the next template question if the answer **already resolves** that dimension (e.g. “full regression + all surfaces + exhaustive” may subsume **Q3** depth). In chat, state explicitly: *Skipped Q3 — covered by Q1/Q2 answers: …*  
   - **Insert** tailored questions for **new doubts** the reply surfaced (security edge, env constraint, design gap) **before** mechanically advancing to the next default label — **zero ambiguities** beats **checking every box**.  
   - If brain artifacts already answered a dimension (e.g. surfaces in **`product.md`**), **confirm in one short interactive prompt** rather than re-reading the entire Q2 wall verbatim.

4. **Coverage obligation** — Every **dimension** represented by Q1–Q7 must be **resolved or risk-accepted** in the transcript; **Q8** when Web/Android/iOS is in scope (or **N/A** with reason). Dimensions may be satisfied **without** asking the corresponding template if subsumed — **must** still appear in **`qa-analysis.md`** with *source: user reply Q1* or *subsumed by …*.

**Forbidden**

- Pasting **full** Q1–Q8 in one message, or offering **single bulk / approve-all-recommendations / hybrid** flows — **not allowed**.  
- A **second** blocking prompt in the same turn that **duplicates** coverage choices or bundles **CSV / automation-order waiver** (that belongs to **`qa-manual-test-cases-from-prd`** / **`/qa-write`** after `qa-analysis.md`).
- **Pipeline horizon in every turn** — do **not** restate *…then manual CSV, then `qa/semantic-automation.csv`, then `/qa-run`…* while asking Q1–Q8. Per **`using-forge`**: mention **only** the **immediate** next dependency; full chain lives in **README** / **commands**, not repeated in chat.

**After** all dimensions are closed: if brain vs answers still disagree, **one** short clarification turn is OK — still **not** a full template dump.

**Never** put questions only in `qa-analysis.md`, only inside a tool call, or only in a file write — chat-first, brain second.

---

**The full Q1–Q8 fenced templates** (with brain-informed ☑/○, the Q8 reuse-first
short form + full workshop, the D5 mobile-driver note on Q2, and the Lovable
GitHub-repo design-source phrasing on Q8) live in
**[reference/interrogation-templates.md](reference/interrogation-templates.md)**:

| # | Dimension | Mandatory? |
|---|---|---|
| Q1 | Test Types (Functional / Non-Functional / Security / Accessibility menu) | yes |
| Q2 | Surfaces (web/api/android/ios/db/cache/events/search) | yes |
| Q3 | Coverage Depth (smoke / standard / comprehensive) | — |
| Q4 | Feature Priority (test density per area) | — |
| Q5 | Regression Scope (Tier-1 hubs from scan) | — |
| Q6 | Open Ambiguities (enumerated from the PRD read) | — |
| Q7 | Environment and Data (creds, seed state, stubs, flakes) | — |
| Q8 | Design source of truth & PRD → UI mapping | yes if Web/Android/iOS in scope |

Run them as **sequential** turns (one dimension per message, full template each),
reconciling after every reply. **Wait until every Q1–Q7 dimension (+ Q8 when UI in
scope) is resolved or explicitly risk-accepted** before Step 1 — zero ambiguities is
the stop condition, not "asked Q8 verbatim." Record all Q&A verbatim in the output
(including *skipped — subsumed by …*).

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

Build a full matrix: `Feature Areas × Test Types × Surfaces × User Roles × States ×
Input Partitions`. The **test-design techniques** (EP, BVA, decision table, state
transition, pairwise, error guessing, use-case) and the **per-complexity minimum
scenario floors** (enforce, never fall below) are in
**[reference/coverage-techniques.md](reference/coverage-techniques.md)**.

---

## Step 5 — Gaps, Reuse, Conflicts

1. **Gaps** — PRD requirements not yet covered by any existing test.
2. **Reuse** — existing scenarios that still apply (list by ID).
3. **Deprecated** — existing scenarios contradicted by the PRD (flag for user).
4. **Conflicts** — PRD vs contract vs tech plan contradictions (STOP; resolve before proceeding).

---

## Step 6 — Coverage Map by Test Type

For each confirmed test type from Q1, write an explicit coverage plan
(`### Smoke / Positive / Negative / Boundary / Security / Accessibility Coverage`
with `SC-<AREA>-<TYPE>-NNN` scenario IDs). A worked example for an auth feature is in
**[reference/coverage-techniques.md](reference/coverage-techniques.md)**. Complete this
map for **every** feature area before calling this skill done.

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

The surface→`/qa-write`/`/qa-run` flag → driver mapping table is in
**[reference/surface-reference.md](reference/surface-reference.md)**. Surface selection
here determines which **Surface** values appear in **`qa/semantic-automation.csv`**;
the **`--surface`** flag on **`/qa-run`** filters which surfaces run.

---

## Edge Cases

1. **PRD is a one-pager** — Still run all steps. High clarification load. Minimum scenario counts still apply.
2. **No existing test export** — Reuse/deprecation sections state "none provided." Do not reduce scope.
3. **Conflicting legal/compliance vs UX** — STOP. Escalate in writing. Do not invent resolution.
4. **PRD references unreleased backend** — Flag as environment prerequisite. Write scenarios anyway; mark `requires_env: staging-only`.
5. **User selects "smoke only"** — Acknowledge but note: smoke is not a substitute for regression and negative coverage. Write the smoke set, then ask: "Do you want to add negative + regression in the next run?"
6. **No codebase scan in brain** — Q5 falls back to asking user to name regression areas. Note `⚠ No scan — regression scope from user only`.

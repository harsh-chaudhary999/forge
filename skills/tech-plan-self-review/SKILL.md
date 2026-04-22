---
name: tech-plan-self-review
description: "WHEN: A per-project tech plan has been written and needs verification before dispatch to dev-implementer. Check spec coverage, elaborative §1b–§1c (incl. API↔consumer map, unknown closure, review log, XALIGN), placeholders, code, commands."
type: rigid
requires: [brain-read]
---

# Tech Plan Self-Review Skill

This skill verifies technical implementation plans against their corresponding shared-dev-spec before dispatch to dev-implementers. It catches incomplete specifications, placeholder code, missing tests, and malformed commit messages.

## Iron Law

```
EVERY TECH PLAN IS VERIFIED AGAINST THE FROZEN SHARED-DEV-SPEC LINE BY LINE BEFORE DISPATCH. A PLAN WITH A PLACEHOLDER OR TODO IS NOT A PLAN — IT IS UNFINISHED WORK. DISPATCH NOTHING THAT FAILS THIS REVIEW. A PLAN WITHOUT §1c REVIEW HISTORY OR WITH DRIFTING §1b.5 ROWS ACROSS REPOS IS NOT READY — RUN THE FEEDBACK LOOP UNTIL PASS OR ESCALATE. AGENT PASS ALONE IS NOT ENOUGH: HUMAN_SIGNOFF (APPROVED OR DOCUMENTED WAIVED) MUST EXIST BEFORE STATE 4B.
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
| "Self-review is one-and-done — I'll fix gaps in code" | **CHANGES REQUESTED** must produce **plan revisions** (§1c log + status). Coding without updating the plan invalidates TDD and eval traceability. |

## Red Flags — STOP and Re-Review

- Plan has `TODO`, `TBD`, `FIXME`, or `...` anywhere in code blocks
- Task description says "similar to Task N" instead of showing actual code
- Import references a function that doesn't exist in the target file
- Test command is "verify it works" instead of an executable command
- Commit message is generic ("update code", "fix stuff", "misc changes")
- Performance requirement in spec has no corresponding benchmark in plan
- Plan references an API endpoint not defined in shared-dev-spec contracts
- **Missing §0 / §1b / §1c or wrong file order** (`tech-plan-write-per-project`): no **Section 0** doubt log; no `Tech plan status:` under title; missing **1b.1–1b.6** (per applicability), **1c** revision log, or **web/app** missing **1b.4** / **HTTP** missing **1b.5**
- **Data model delta contradicts migration tasks** — Delta says “none” but tasks add DDL, or delta lists tables with no matching migration task
- **Figma / `design_brain_paths` / Lovable locked in intake but 1b.4 empty or generic** — “See Figma” without node ids or brain paths, or no **`D<n>`** linkage from UI tasks
- **Missing §1b.5** when the repo implements or consumes REST/HTTP for this task — No API↔component map
- **§1b.6 unknowns UNRESOLVED** but Section 2 tasks depend on them
- **Missing §1c** status banner, revision log, or **REVIEW_PASS** without a logged self-review round in the log
- **Multi-repo HTTP drift:** consumer `METHOD+path` in this plan’s §1b.5 does not match sibling `tech-plans/*.md` owner rows (after XALIGN should have fixed — still FAIL → BLOCKED)
- **`tech-plans/HUMAN_SIGNOFF.md` missing** after agent **PASS** + **XALIGN** — Human feedback / go-ahead phase skipped; pipeline must not advance to State 4b. STOP. Create signoff per **`docs/tech-plan-human-signoff.template.md`** (or **`waived`** with reason).

**Any of these mean: BLOCKED. Fix before dispatch.**

---

## Verification Checklist

### 0a. Planning doubt log (`tech-plan-write-per-project` Section 0)

**Checklist:**
- [ ] **`## Section 0: Planning doubt log`** exists **before** §1b with table **Q# / Question / Answer / Confidence / Affects**
- [ ] **No artificial silence:** multiple substantive questions when the feature is complex — or one explicit row **`No material doubts`** when truly trivial
- [ ] **No high-impact `L` (low) confidence** without **BLOCKED**, **WAIVER**, or named owner + next step
- [ ] Answers tie to **§1b** rows and/or **Section 2** task ids — orphan answers are cleaned up

### 0. Parity & delivery context (task brain)

**Checklist:**
- [ ] **`~/forge/brain/prds/<task-id>/parity/`** satisfies **`spec-freeze`** Step 0 (**`external-plan.md`** OR completed **`checklist.md`** OR **`waiver.md`**) — not missing when the task is “serious” multi-repo delivery
- [ ] If **`delivery-plan.md`** exists: tech plan **§1b.3** or tasks reference rollout / flag / pyramid items **only** as pointers — **interfaces** still match frozen spec

### 0b. Implementation discovery & delivery locks (when `prd-locked.md` Q10 applies)

**Checklist:**
- [ ] **`implementation_reference`** from intake is echoed in the tech plan’s first page (branch / PR / explicit `none` + rationale) — not implied.
- [ ] **`delivery_mechanism`** and **`implementation_stack`** (or legacy **`ui_implementation_stack`**) from `prd-locked.md` appear verbatim or by reference — tasks must not contradict the locked authoritative boundary or stack.
- [ ] **Discovery evidence:** Plan states that **`git branch -a`** (or equivalent) was reviewed **or** links `discovery.md` / `context-loaded.md` git subsection from product-context-load — not “assumed greenfield.”
- [ ] **RED tests (see `forge-tdd`):** First failing tests must assert **observable behavior** at the chosen boundary (API contract, persistence, job output, or UI), not only registry/enum membership, when the feature is user-visible or Q10 applied.

### 1. Spec Coverage

**Checklist:**
- [ ] **Every requirement in shared-dev-spec has at least one corresponding task**
  - Scan the shared-dev-spec Requirements section
  - For each requirement, find at least one task that addresses it
  - Mark as covered only if the task description mentions the requirement by name or clearly implements it

- [ ] **No orphan requirements**
  - No requirement is left without a task
  - No task description is vague enough to accidentally cover something

- [ ] **Priority ordering respected**
  - If shared-dev-spec lists priorities (P0/P1/P2 or similar), tasks follow same order
  - Critical path tasks listed before optional-to-nice-to-have tasks

### 1b. Data model delta, reuse narrative, design trace, preamble (`tech-plan-write-per-project` Section 1b)

**Checklist:**
- [ ] **File layout:** `Tech plan status:` line immediately under `#` title; **Section 0** doubt log; **Section 1b** (`1b.1`–`1b.6` per applicability) and **§Section 1c** appear **before Task 1**
- [ ] **Data model delta** is either a table with one row per CREATE/ALTER/DROP/index (or equivalent storage change), or an explicit one-line statement that this repo has **no** persistence/schema work — consistent with **shared-dev-spec** / DB contract
- [ ] **Cross-repo DDL:** If migrations run elsewhere, the delta says so; this plan does not silently own another service’s tables
- [ ] **Every migration/DDL task** in the plan has a matching row in the delta (or the repo correctly claims no persistence and has no such tasks)
- [ ] **Reuse vs net-new** lists concrete repo-relative paths for extended or called code; where a **brain scan** exists for this product, reuse bullets **align** with `codebase/` modules — or the plan flags **`SCAN_MISSING_OR_STALE`**; net-new surfaces are explicit — no implied reuse without a path
- [ ] **Trace to spec** maps requirements or contract headings to task numbers; combined with §1, no orphan requirements
- [ ] **1b.4 (web/app):** When **`design_new_work: yes`** or implementable design is locked (Figma keys, `design_brain_paths`, Lovable repo), the **design→UI table** lists anchors → deliverable → scan path or `NET_NEW`; **UI tasks** reference **`D<n>`** or cite **`design_waiver: prd_only`** plus PRD anchor — not chat-only Figma URLs
- [ ] **1b.5 (HTTP):** If this repo serves or consumes REST for the task, **API↔consumer** tables exist and **METHOD+path** strings match **shared-dev-spec** REST; **N/A** line only when truly no HTTP surface
- [ ] **1b.6:** Unknown table present; every row **RESOLVED** with evidence or **BLOCKED** with escalation — **no** dependency tasks on unresolved unknowns
- [ ] **1c:** `Tech plan status` + **revision log** present; latest log line records this review round and **PASS|CHANGES|BLOCKED**; if multi-repo HTTP, **XALIGN** noted **PASS** or open FAIL items are listed as blockers

### 1d. Cross-plan HTTP consistency (run when ≥2 tech plans include §1b.5)

**When to skip:** Only one repo in the product task touches HTTP — mark “N/A”.

**Checklist:**
- [ ] Load **all** `~/forge/brain/prds/<task-id>/tech-plans/*.md` that claim HTTP in §1b.5
- [ ] **Consumer → owner:** Every `METHOD+path` in a **web/app** plan appears in the **API-owning** plan (same spelling, including prefix/version), or an explicit “external API” row cites a non-product host documented in spec
- [ ] **Owner → consumer:** Every **new/changed** endpoint in the API plan is referenced by ≥1 consumer row **or** documented as “no consumer yet / batch only / public” with spec citation
- [ ] **Drift = BLOCKER** until plans revised and XALIGN re-run (`XALIGN PASS` in logs)

### 1e. Human tech-plan signoff (task-level — once per `task-id`)

**When to skip:** Never for full conductor **`State 4b`** entry — file must exist with **`approved`** or **`waived`**.

**Checklist:**
- [ ] **`~/forge/brain/prds/<task-id>/tech-plans/HUMAN_SIGNOFF.md`** present; frontmatter **`status`** is **`approved`** or **`waived`**
- [ ] **`repos_acknowledged`** covers all repo plans for this task (or waiver explains)
- [ ] **`[TECH-PLAN-HUMAN]`** log line can be emitted without contradicting the file

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

### Step 1: Load Spec and Plan
```bash
# Read the shared-dev-spec (referenced in task context)
cat /path/to/shared-dev-spec.md

# Read the tech plan (provided by task context)
cat /path/to/tech-plan.md
```

### Step 2: Checklist Verification
For each section above (Spec Coverage, Code Completeness, etc.):
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

- **APPROVED (agent):** All checklist sections pass → Update this plan file: **`Tech plan status: REVIEW_PASS`**, append **revision log** row with `self-review round=<n> result=PASS` (and **`XALIGN PASS`** if multi-repo HTTP). **This alone does not clear the Forge pipeline** — **Step 5 (human gate)** is still required before **State 4b** (eval / RED).
- **CHANGES REQUESTED:** Some warnings → Set plan **`REVIEW_CHANGES`** / **`DRAFT`**, append revision log with **failed § references**, **edit the tech plan** (not only mental note), re-run this skill from Step 1 — **max 3 rounds** per repo then escalate.
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
- [✅/❌] Spec Coverage: All requirements covered
- [✅/❌] §0–§1c: Doubt log + data/design/API map/unknowns/review log (+ XALIGN when applicable)
- [✅/❌] §1e Human signoff file + log (`HUMAN_SIGNOFF.md`, `[TECH-PLAN-HUMAN]`)
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

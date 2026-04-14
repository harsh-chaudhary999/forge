---
name: tech-plan-self-review
description: "WHEN: A per-project tech plan has been written and needs verification before dispatch to dev-implementer. Check all requirements covered, no placeholders, complete code, exact commands."
type: rigid
requires: [brain-read]
---

# Tech Plan Self-Review Skill

This skill verifies technical implementation plans against their corresponding shared-dev-spec before dispatch to dev-implementers. It catches incomplete specifications, placeholder code, missing tests, and malformed commit messages.

## Iron Law

```
EVERY TECH PLAN IS VERIFIED AGAINST THE FROZEN SHARED-DEV-SPEC LINE BY LINE BEFORE DISPATCH. A PLAN WITH A PLACEHOLDER OR TODO IS NOT A PLAN — IT IS UNFINISHED WORK. DISPATCH NOTHING THAT FAILS THIS REVIEW.
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

## Red Flags — STOP and Re-Review

- Plan has `TODO`, `TBD`, `FIXME`, or `...` anywhere in code blocks
- Task description says "similar to Task N" instead of showing actual code
- Import references a function that doesn't exist in the target file
- Test command is "verify it works" instead of an executable command
- Commit message is generic ("update code", "fix stuff", "misc changes")
- Performance requirement in spec has no corresponding benchmark in plan
- Plan references an API endpoint not defined in shared-dev-spec contracts

**Any of these mean: BLOCKED. Fix before dispatch.**

---

## Verification Checklist

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

### Step 4: Decision
- **APPROVED:** All checks pass → Ready for dispatch to dev-implementers
- **CHANGES REQUESTED:** Some warnings → Fix and resubmit
- **BLOCKED:** Any blockers → Cannot dispatch until fixed

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

### Status: ✅ APPROVED / ⚠️ CHANGES REQUESTED / ❌ BLOCKED

### Verification Summary
- [✅/❌] Spec Coverage: All requirements covered
- [✅/❌] Code Completeness: No placeholders
- [✅/❌] No Placeholder Code: All implementations concrete
- [✅/❌] Test & Commit: All tests runnable, commits clear
- [✅/❌] Output Format: Expected outputs documented

### Issues Found
1. [Line X] Code completeness issue: "..." found in [section]
2. [Section Y] Placeholder code: "TODO" found, needs full implementation
3. [Task Z] Missing test command

### Recommendations
- (if APPROVED) Ready for dispatch
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

---
name: forge-tdd
description: "WHEN: About to write any production code. HARD-GATE: Iron law - write test first, watch fail, write minimal code, watch pass. No exceptions."
type: rigid
version: 1.0.0
preamble-tier: 3
triggers:
  - "write test first"
  - "TDD"
  - "test-driven development"
  - "RED test before code"
allowed-tools:
  - Bash
  - Write
---

# Test-Driven Development (Iron Law)

**HARD-GATE: Non-negotiable. No production code without failing test first.**

---

## Anti-Pattern Preamble: Why You Think TDD Is Optional (It Isn't)

| Rationalization | The Truth |
|---|---|
| "This is a simple feature, TDD feels slow" | Simplicity hides the hardest bugs. TDD catches them. Slow startup, faster debugging. Net win. |
| "I'll write tests after to save time" | You won't. Post-hoc tests miss 40% of edge cases TDD would have caught. Write first. |
| "The spec is clear enough, I don't need tests to clarify it" | No spec is ever clear enough. Test is the spec. Test forces you to think through edge cases. |
| "I can skip the test-run-fail step, I know it will fail" | NO. You MUST run it and see the failure. Seeing the failure teaches you what you're fixing. |
| "Our codebase doesn't do TDD, I'll follow convention" | YOU are disciplined. Convention doesn't override discipline. Do it. |
| "I'll test as I code (test-parallel) instead of test-first" | Wrong order. Test FIRST, then code. The order matters. Test-first catches what test-parallel misses. |
| "This code is internal/hidden, no one will use it, I'll skip TDD" | Internal code is harder to test and debug. TDD is MORE important, not less. |
| "I already know what tests to write, I'll code first" | You don't. Writing code first blinds you to edge cases. Test first clarifies. |
| "The test infrastructure is broken, I'll work around it" | STOP. Report BLOCKED. Don't workaround. Fix or escalate. |
| "I wrote a test that passes but it doesn't actually test anything" | Weak tests are worse than no tests. Test must verify behavior, not just syntax. |
| "RED tests only mirror the tech plan, not approved QA cases" | When **`qa/manual-test-cases.csv`** exists for the task, RED should **map to those atomic rows** (or explicitly document gaps). Otherwise TDD and **P4.4 semantic machine eval** drift from the acceptance inventory the team signed. |

---

## Iron Law

```
NO PRODUCTION CODE EXISTS BEFORE THE TEST.
```

If you write 1 line of code without a test first, you have failed.

---

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Implementation code is written before a test file exists** — The Iron Law is violated. STOP. Delete the implementation, write the test first, watch it fail, then reimplement.
- **Test passes on first run without ever seeing it fail (RED step skipped)** — A test that never fails is a test that doesn't test anything. STOP. Verify the test actually fails when the implementation is removed.
- **Multiple tests are written at once before any implementation** — Multiple tests at once hide which test drives which implementation. STOP. Write one test, see it fail, implement, see it pass, then write the next.
- **RED only asserts registry / enum / opaque “id exists” for user-visible UI** — That passes while alternate delivery paths, stacks, and layout remain unsettled. STOP. Rewrite RED to assert **one observable behavior** under test doubles (e.g. when input X, rendered count / bound data / visible state), aligned with **`delivery_mechanism`** + **`implementation_stack`** (or legacy **`ui_implementation_stack`**) from `prd-locked.md` Q10 and approved QA rows when present.
- **Agent says "I'll write tests after" or "tests follow the implementation"** — Post-hoc tests cannot drive design. STOP. Tests must be written first, always.
- **Refactoring adds new behavior** — Refactor is for clarity, not features. STOP. If the refactor adds functionality, extract that as a new RED-GREEN cycle.
- **Test infrastructure is broken and agent proceeds without tests** — Working without tests is not a valid workaround. STOP. Report BLOCKED. Do not write production code in a broken test environment.

---

## The RED-GREEN-REFACTOR Cycle

### RED — Write Test, Watch It Fail

1. **Write a test** that describes the desired behavior
   - Test is minimal and focused on the specific task
   - Test should fail with current code
   - Use existing test patterns in the project
   
2. **Run the test**
   - MUST run and MUST see it fail
   - Failure message should be clear and sensible
   - If test doesn't fail → test is useless (rewrite it)
   - If test runs at all but crashes → infrastructure issue (escalate BLOCKED)

**Success Criterion:** Red test fails with clear, meaningful error.

### GREEN — Write Minimal Code, Watch It Pass

1. **Write minimal code** to make test pass
   - Minimal means: no extra features, no "future-proofing", no refactoring yet
   - YAGNI: You Aren't Gonna Need It
   - If you wrote code thinking "this might be useful later", DELETE it
   
2. **Run the test**
   - MUST run and MUST see it pass
   - If test still fails → adjust code (iterate)
   - If different test fails now → investigate (you may have broken something)

**Success Criterion:** Test passes. Only minimal code added.

### REFACTOR — Improve Code While Tests Still Pass

1. **Refactor the implementation** (not the test)
   - Extract duplicated logic
   - Rename for clarity
   - Restructure for maintainability
   - Clean up comments and formatting
   
2. **Run tests again**
   - All tests must still pass
   - If any test fails → undo refactor (your refactor broke something)
   - Never refactor beyond the task scope

3. **Stop refactoring**
   - Refactor is NOT an excuse to redesign the whole system
   - Refactor is NOT an excuse to optimize prematurely
   - Refactor ONLY if: it makes code clearer/simpler (YAGNI still applies)

**Success Criterion:** Tests still pass, code is cleaner, scope unchanged.

---

## Detailed Workflow

### Step 1: Understand the Task
- Read the task text completely
- If unclear → ask questions (don't guess)
- Understand: what behavior should exist? What does "done" look like?

### Step 2: Find or Write the Test
- Look for existing test files
- Identify the test pattern used in the project
- Write ONE test for this task
- Test should be small enough to understand in 30 seconds
- Test should verify exactly the behavior you're implementing

**Example:**
```python
# TASK: Add method to validate email format
# BAD TEST: Tests that function exists and returns something
def test_validate_email():
    assert email_validator.validate_email("test@example.com") is not None

# GOOD TEST: Tests the specific behavior
def test_validate_email_accepts_valid_address():
    assert email_validator.validate_email("test@example.com") == True
    
def test_validate_email_rejects_invalid_address():
    assert email_validator.validate_email("invalid") == False
    
def test_validate_email_rejects_missing_at_symbol():
    assert email_validator.validate_email("testexample.com") == False
```

### Step 3: Run the Test (RED phase)
```bash
# Run your new test
$ npm test -- test_email_validator.js
# MUST see: Test FAILED / Red
```

Do not proceed until you see the test fail.

### Step 4: Write Code to Pass the Test (GREEN phase)
- Write only what's needed
- Follow existing code style
- No extra features
- No premature optimization

```python
# MINIMAL implementation
def validate_email(email: str) -> bool:
    return "@" in email and "." in email.split("@")[1]
```

### Step 5: Run the Test Again (verify GREEN)
```bash
$ npm test -- test_email_validator.js
# MUST see: Test PASSED / Green
```

Do not proceed until the test passes.

### Step 6: Run All Tests
```bash
$ npm test  # All tests, not just the new one
# MUST see: All tests still pass
```

If existing tests now fail, you broke something. Fix it before proceeding.

### Step 7: Refactor (if needed)
Only after tests pass:
- Is the code clear?
- Are there duplicated patterns?
- Can variable names be better?
- Can the logic be simpler?

If yes → refactor. Then re-run all tests to verify.

### Step 8: Done
- New test passes ✅
- All existing tests pass ✅
- Code is minimal ✅
- Code is clear ✅

---

## Edge Cases & Escalation

### What if I'm not sure how to write a test?
Read existing tests in the project. Copy the pattern. Ask for clarification if needed.

### What if the test infrastructure is broken?
Report `BLOCKED: Test infrastructure broken [details]`. Do not attempt workarounds. Escalate.

### What if the task is "add logging" or "update documentation"?
These are typically not TDD-able. But: if possible, write a test that verifies the logging/docs exist and are correct. If not possible, report `NEEDS_CONTEXT: Task not TDD-compatible [reason]`.

### What if the test takes longer than the code?
That's normal and correct. Complex behavior requires complex tests. Tests are not overhead; they're part of the implementation.

### What if I don't know what the behavior should be?
Stop. Report `NEEDS_CONTEXT: Unclear acceptance criteria [details]`. Don't guess.

### What if multiple tests fail now?
You probably wrote too much code. Roll back. Write LESS code. Make the first test pass. Then write the next test.

### What if I finish the task but want to refactor the whole file?
Don't. Refactor ONLY the code you touched. Out-of-scope refactoring is not part of the task.

### What if the project doesn't have tests?
Create a test file. Use standard test framework for the language. Start with one test. But: if test infrastructure is fundamentally broken, report `BLOCKED`.

---

## Success Criteria

✅ **PASS:**
- Test written before any code
- Test fails when run (RED phase observed)
- Minimal code written to pass test
- Test passes when run (GREEN phase observed)
- All existing tests still pass
- Code is refactored for clarity (if needed)
- Task behavior is correct

❌ **BLOCKED:**
- Test infrastructure broken/missing
- Task is not TDD-compatible
- Acceptance criteria unclear

---

## Verification

Before claiming task is done, verify:

```bash
# 1. New test exists
$ grep -r "def test_" <test_file>  # New test present?

# 2. Test passes
$ npm test -- <test_file>  # All tests in file pass?

# 3. All tests pass
$ npm test  # No regressions?

# 4. Code is minimal
$ git diff <file>  # Only necessary changes? No extra features?

# 5. Code is clear
# Read the code. Is it obvious what it does?
```

If all 5 pass → done. Otherwise → iterate.

---

## Edge Cases & Escalation Paths

### Edge Case 1: Test Is Too Slow (10+ Seconds Per Run, Blocks Development)
**Situation:** Test is valid and correct, but takes 15+ seconds to run. Each RED-GREEN cycle takes minutes instead of seconds.

**Example:** Database integration test that creates 1000 records and validates queries. Valid test, but too slow for fast feedback loop.

**Do NOT:** Skip the test or reduce test scope because it's slow. Slow tests catch real issues.

**Action:**
1. Run test once to verify it works (see GREEN)
2. Identify bottleneck (where does time go?)
   - Database setup/teardown?
   - Large data set creation?
   - Network calls?
3. Options:
   - **Option A (Preferred):** Refactor test to be faster without losing coverage
     - Use fixtures instead of creating data
     - Mock external services
     - Reduce data set size (still tests behavior)
   - **Option B:** Split into two tests
     - Unit test (fast, < 100ms)
     - Integration test (slow, but run less frequently)
4. If cannot optimize: escalate as **NEEDS_CONTEXT** (test infrastructure too slow)
5. Do NOT reduce verification rigor to gain speed

---

### Edge Case 2: Test Is Flaky (Fails 20% of Time Unpredictably)
**Situation:** Test passes sometimes, fails sometimes. No clear pattern (timing, state, environment).

**Example:** Test that polls for eventual consistency; sometimes data appears in 10ms, sometimes 500ms. Test has hard-coded 50ms wait.

**Do NOT:** Accept flakiness or increase timeouts. Flakiness is a real bug in code or test.

**Action:**
1. Run test 10 times in succession; note pass/fail pattern
2. Classify flakiness type:
   - **Timing-dependent:** Add explicit waits, remove hard-coded delays
   - **Order-dependent:** Tests run in different order; state leaks between tests
   - **Concurrency:** Race condition in code or test
   - **Environment:** Infrastructure variability (network, database)
3. Fix root cause (not the test, the code):
   - Code: add synchronization, remove race condition
   - Test: add proper setup/teardown, isolate tests
4. Re-run test 10 times again; must pass all 10
5. If cannot stabilize: escalate as **BLOCKED** (flaky infrastructure or untestable code)

---

### Edge Case 3: Test Requires Infrastructure Not Available (Database, API Service)
**Situation:** Test is valid, but requires external service that's not running or accessible.

**Example:** Test for payment gateway integration requires live API connection. API service is down.

**Do NOT:** Skip the test or mock the service permanently. Integration tests must eventually test real integration.

**Action:**
1. Determine: is the service _always_ required or only for this test?
   - Always: you need the infrastructure restored before proceeding
   - Only this test: can you mock it temporarily?
2. If service can be restored (local database, stub server):
   - Restore/start the service
   - Re-run test
3. If service cannot be restored (external API, vendor service):
   - **Option A:** Mock the service for now, add comment "TODO: verify with real API"
   - **Option B:** Escalate as **NEEDS_CONTEXT** (cannot run full integration test)
   - **Option C:** Split test into unit (mocked) + integration (real API, run later)
4. Document the dependency in code comments
5. If mocking: create follow-up task to remove mock and verify against real service

---

### Edge Case 4: Legacy Code Path Has No Way to Unit Test (Tightly Coupled)
**Situation:** Code to test is tightly coupled to global state, static calls, or framework internals. Cannot unit test without refactoring code itself.

**Example:** Class that calls `Database.getInstance().query()` globally; Database is a singleton with no way to inject a test double.

**Do NOT:** Skip TDD or write test after code. Tight coupling is the problem.

**Action:**
1. Acknowledge: this code cannot be unit tested in current form
2. Refactor first (extract dependency, inject it):
   ```
   // BEFORE: tightly coupled
   class UserRepository {
       def getUser(id) { Database.getInstance().query(...) }
   }
   
   // AFTER: injectable
   class UserRepository {
       constructor(database) { this.db = database }
       def getUser(id) { this.db.query(...) }
   }
   ```
3. Then follow normal TDD: test first, code second
4. If refactoring is not possible (framework limitation):
   - Escalate as **NEEDS_CONTEXT** (code untestable, needs architecture change)
   - Mark code as "legacy, cannot unit test"
   - Use integration tests instead
5. Going forward: enforce testable design (dependency injection, loose coupling)

---

### Edge Case 5: Integration Test Required > Unit Test (Distributed System Testing)
**Situation:** Behavior cannot be verified with unit test alone. Service boundary requires integration test (multiple services, eventual consistency, network behavior).

**Example:** Feature: "Cache invalidated when user data changes". Requires backend write → cache invalidation → frontend read. One service cannot test alone.

**Do NOT:** Force a unit test for inherently distributed behavior. Integration tests are valid TDD.

**Action:**
1. Recognize: this is an integration test, not a unit test
2. Follow TDD at integration level:
   - RED: write integration test (bring up services, exercise end-to-end flow, verify cache behavior)
   - GREEN: implement feature
   - REFACTOR: optimize services without breaking integration test
3. May be slower than unit test (that's expected)
4. Integration test still drives design (discover contracts, dependencies)
5. Run integration tests less frequently (as gate, not per-commit), but still TDD
6. Do NOT skip the test because "it's just integration"

---

## Decision Tree: When to Unit Test vs. Integration Test

**Use this tree to decide which test to write first:**

```
START: I need to test behavior X

Q1: Does X require multiple services/processes?
├─ YES → Q2
└─ NO → UNIT TEST (test single component in isolation)

Q2: Does X depend on eventual consistency, timing, or network?
├─ YES → INTEGRATION TEST (test end-to-end, multiple services)
└─ NO → Could be unit test with mocks (see Q3)

Q3: Is the external service/boundary testable in isolation?
├─ NO → INTEGRATION TEST (no way around it)
├─ YES, easy to mock → UNIT TEST (mock the boundary)
└─ YES, but mocking loses important behavior → INTEGRATION TEST (test real behavior)

Q4: Is the integration test too slow (>5 sec)?
├─ YES → Split: UNIT TEST (fast path) + INTEGRATION TEST (slow path, run separately)
└─ NO → Single INTEGRATION TEST suffices

DECISION RULE:
- Unit test for single component logic (validation, calculation, formatting)
- Integration test for multi-component behavior (contracts, APIs, eventual consistency)
- Always write test first (RED), regardless of type
- Fast feedback: prefer unit tests for development
- Final verification: integration tests before merge
```

---

Output: **TDD PASS** (test first, minimal code, all tests pass) or **BLOCKED** (test infrastructure broken, untestable legacy code, infrastructure unavailable after attempts to restore)

TDD is not about writing tests. It's about:
1. **Clarifying requirements** — Test forces you to think through edge cases before coding
2. **Preventing bugs** — Test catches bugs at write time, not debug time
3. **Enabling refactoring** — Tests let you refactor safely
4. **Documenting behavior** — Test is the executable spec
5. **Reducing rework** — Upfront clarity saves debugging time later

TDD feels slow at first. After the RED phase (writing the test), you're 60% done. The code is the easy 40%.

---

## Iron Law Enforcement

This skill is RIGID: type=rigid. Do not bend it.

- If you're tempted to skip the test → invoke this skill
- If you're tempted to code first → invoke this skill
- If you're tempted to skip seeing the test fail → invoke this skill
- If you're tempted to refactor outside your task → invoke this skill

TDD is the foundation. Every other discipline depends on it.

---

Note: This version includes edge cases and decision tree for complex testing scenarios (slow tests, flaky tests, infrastructure dependencies, legacy code, integration vs. unit testing).

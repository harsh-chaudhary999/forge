---
name: forge-tdd
description: HARD-GATE: Iron law - write test first, watch fail, write minimal code, watch pass. No exceptions. Non-negotiable discipline enforcer.
type: rigid
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

## Why TDD

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

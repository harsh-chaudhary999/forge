# Failure classification catalogs — reference for `self-heal-triage`

> Progressive-disclosure Level 3 (loaded on demand). Detailed per-category evidence catalogs, the classification algorithm, and confidence-scoring bands relocated from SKILL.md. The SKILL.md retains the operational decision spine; this file is the full lookup.

## Classification Categories

### 1. Flaky Test
**Definition:** A test that sometimes passes and sometimes fails without code changes.

**Identifying Evidence:**
- Timeout or deadline exceeded errors
- Race condition indicators (non-deterministic ordering)
- Async/await issues (promises not awaited, race windows)
- Timing-dependent assertions (e.g., checking elapsed time)
- Intermittent network timeouts
- Random test data generation without seeding
- Sleep/delay assertions
- Test order dependency
- External service inconsistent response times

**Common Error Patterns:**
```
- "timeout"
- "deadline"
- "race condition"
- "flaky"
- "sometimes passes"
- "async operation never completed"
- "expected X, got Y (inconsistently)"
- "context deadline exceeded"
```

**Suggested Actions:**
- Add explicit wait/retry logic with backoff
- Remove time-dependent assertions
- Add test isolation (setup/teardown)
- Mock external services with deterministic responses
- Fix race conditions with proper locking
- Increase timeouts with justified defaults
- Add test data seeding

---

### 2. Bad Test
**Definition:** The test itself contains errors or incorrect expectations. The code under test works correctly, but the test doesn't validate it properly.

**Identifying Evidence:**
- Assertion mismatch (expected != actual in a way that makes sense)
- Wrong expectations in mock/stub setup
- Incorrect expected values hardcoded
- Test doesn't match actual behavior spec
- Off-by-one errors in assertions
- Type mismatch in assertions
- Inverted logic (testing for failure instead of success)
- Copy-paste errors from other tests
- Missing required test setup

**Common Error Patterns:**
```
- "AssertionError: expected X but got Y" (where the code is correct)
- "expected call to foo() not found" (but code doesn't call it)
- "expected property 'status' to be 200 but got 201" (and 201 is correct)
- "comparison failed: expected [1,2,3] got [3,2,1]" (wrong order in test)
- "stub not called as expected"
```

**Suggested Actions:**
- Fix the assertion to match correct behavior
- Update mock setup to match actual API
- Correct expected values
- Simplify test logic
- Add comments explaining why assertion is correct
- Align test with API documentation
- Remove incorrect assumptions

---

### 3. Real Bug
**Definition:** The code under test is actually broken. The test correctly identifies a defect in the implementation.

**Identifying Evidence:**
- Exception or error thrown (NullPointerException, TypeError, etc.)
- Unhandled edge case
- Logic error in implementation
- Invalid state transitions
- Resource leak or improper cleanup
- Incorrect algorithm output
- Missing validation
- Broken dependency
- Memory or performance regression

**Common Error Patterns:**
```
- "NullPointerException"
- "TypeError: Cannot read property X of undefined"
- "ReferenceError: X is not defined"
- "Segmentation fault"
- "Stack overflow"
- "Out of memory"
- "Invalid operation: X"
- "Precondition violated"
- "Invariant broken"
```

**Suggested Actions:**
- Fix the bug in implementation code
- Add proper error handling
- Add input validation
- Fix algorithm logic
- Add missing null checks
- Improve state management
- Fix resource cleanup (close files, connections, etc.)

---

### 4. Environment Issue
**Definition:** External system or service is unavailable or misconfigured. Code and tests are correct, but runtime dependencies fail.

**Identifying Evidence:**
- Connection refused (host/port unreachable)
- Service timeout (when service is slow)
- DNS resolution failure
- Database/cache unavailable
- Network unreachable
- Service auth failure
- Wrong service endpoint
- Insufficient resources (disk, memory)
- Misconfigured environment variables
- Port already in use
- Firewall blocking

**Common Error Patterns:**
```
- "Connection refused"
- "Service unavailable"
- "Cannot reach database"
- "ECONNREFUSED"
- "getaddrinfo ENOTFOUND"
- "port already in use"
- "permission denied"
- "cannot open shared object file"
- "no such host"
```

**Suggested Actions:**
- Restart the service
- Check service health endpoints
- Verify network connectivity
- Validate configuration (env vars, ports)
- Check firewall rules
- Verify DNS resolution
- Increase system resources
- Wait for service recovery
- Reconfigure endpoint

---

## Classification Algorithm

```
INPUT: failure_message, error_type, test_context

CLASSIFY:
  IF (contains "timeout" OR contains "deadline" OR contains "race" OR contains "async") THEN
    RETURN Flaky Test

  ELSE IF (contains "AssertionError" AND assertion_mismatch) THEN
    RETURN Bad Test

  ELSE IF (contains exception_pattern like "NullPointer", "TypeError", "ReferenceError") THEN
    RETURN Real Bug

  ELSE IF (contains connection_pattern like "ECONNREFUSED", "ENOTFOUND", "refused") THEN
    RETURN Environment Issue

  ELSE IF (error_type in ["expected", "expected to be", "should have"] AND logic_clear) THEN
    RETURN Bad Test

  ELSE IF (error_type in ["exception", "error", "thrown", "crashed"]) THEN
    RETURN Real Bug

  ELSE IF (error_type in ["timeout", "unavailable", "connection"]) THEN
    RETURN Environment Issue

  ELSE
    RETURN Uncertain (requires human review)
```

---

## Confidence Scoring

**High Confidence (85-100%):**
- Clear, unambiguous error pattern
- Multiple matching indicators
- Previously classified failures of same type
- Error message is descriptive and specific
- Context clearly supports classification

**Medium Confidence (50-85%):**
- Some ambiguity in error message
- Single primary indicator + contextual clues
- Could be one of two types
- Error message partially descriptive
- Requires minor context interpretation

**Low Confidence (0-50%):**
- Vague error message
- Multiple conflicting indicators
- Unclear error context
- Requires human review
- Novel error type

---

## Confidence Rules

### High Confidence Indicators
1. Error message explicitly names category (timeout, assertion, exception, connection)
2. Multiple patterns match same classification
3. Context strongly supports interpretation
4. Clear separation from other categories
5. Previous similar classifications exist

### Medium Confidence Degradation
1. Only one primary pattern matches
2. Slight ambiguity in error message
3. Could plausibly be another category
4. Context partially supports classification
5. Novel error type

### Low Confidence Triggers
1. Generic error message (e.g., "Error")
2. Conflicting patterns (flaky + real bug signals)
3. Insufficient context
4. Unfamiliar error code
5. Human review explicitly needed
</content>
</invoke>

---
name: self-heal-triage
description: Classify failure: flaky (timing), bad test (wrong), real bug (code broken), environment (service down). Output: classification with evidence.
type: rigid
requires: [brain-read]
---

# Self-Heal Triage Skill

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "It's obviously a flaky test" | "Obviously flaky" is the most common misclassification. Intermittent failures often reveal real timing bugs, race conditions, or resource leaks. Collect evidence before classifying. |
| "The test passed on re-run, so it's not a real bug" | A test that fails once and passes on retry is the definition of a flaky test — but the flakiness itself may be a real bug (race condition, resource contention). |
| "It's an environment issue, not our code" | Environment issues that affect your eval will affect production. If the environment broke your test, understand why and whether production is similarly vulnerable. |
| "I'll classify it later, let me fix it first" | Fixing before classifying means you might fix a flaky test with a code change (wrong) or fix a real bug with a retry (also wrong). Classification determines the correct fix strategy. |
| "Low confidence is fine for triage" | Low-confidence triage sends the wrong fix strategy downstream. If you can't classify with MEDIUM+ confidence, collect more evidence — don't guess. |

**If you are thinking any of the above, you are about to violate this skill.**

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Triage classification is "probably flaky" with no timing evidence** — Probability-based triage is a guess. STOP. Collect actual timing data (retry counts, timestamps, test duration) before classifying as flaky.
- **Classification is made after only 1 data point (1 failure)** — Single-occurrence failures are unclassifiable without more data. STOP. Run the test 3 times to distinguish flaky from real.
- **"Environment issue" is used to dismiss a failure without a root cause** — Environment failures have root causes. STOP. Identify what specifically broke in the environment and whether it's also broken in production.
- **Triage confidence is LOW and triage proceeds anyway** — Low-confidence triage sends the wrong fix strategy downstream. STOP. Gather more evidence until confidence is MEDIUM or higher.
- **Fix is applied before triage completes** — Fixing before classifying means applying the wrong fix strategy. STOP. Always complete triage before prescribing a fix.
- **Same failure is classified differently on two consecutive runs** — Classification instability means the evidence is insufficient. STOP. Rerun with more isolation and additional log capture.

## Purpose
Automatically classify test and system failures into one of four categories to enable rapid remediation. Each classification provides evidence, confidence scoring, and a suggested action.

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

## Examples

### Example 1: Flaky Test (HIGH confidence)
```
Failure Message: "timeout waiting for promise resolution after 5000ms"
Error Type: TimeoutError
Test: async function waiting for API response

Classification: FLAKY TEST
Evidence: 
  - Explicit timeout error
  - Async operation issue
  - Time-dependent assertion
Confidence: HIGH (92%)
Suggested Action: Increase timeout or add retry logic with exponential backoff
```

### Example 2: Bad Test (HIGH confidence)
```
Failure Message: "AssertionError: expected status 200 but got 201"
Error Type: AssertionError
Test: validateStatusCode()
Context: API returns 201 for POST requests (documented)

Classification: BAD TEST
Evidence:
  - Assertion mismatch
  - Expected value contradicts API spec
  - Test assertion is simply wrong
Confidence: HIGH (95%)
Suggested Action: Update assertion from 200 to 201 or add comment explaining why 200 is expected
```

### Example 3: Real Bug (HIGH confidence)
```
Failure Message: "TypeError: Cannot read property 'id' of undefined"
Error Type: TypeError
Test: getUserData() should return user with id

Classification: REAL BUG
Evidence:
  - Explicit TypeError
  - Null/undefined reference
  - Code is crashing on valid input
Confidence: HIGH (98%)
Suggested Action: Fix getUserData() to handle undefined case or ensure initialization
```

### Example 4: Environment Issue (HIGH confidence)
```
Failure Message: "ECONNREFUSED: Connection refused 127.0.0.1:5432"
Error Type: Connection Error
Test: database connection test
Context: Postgres service should be running on port 5432

Classification: ENVIRONMENT ISSUE
Evidence:
  - Connection refused error
  - Database service unreachable
  - Network connectivity failure
Confidence: HIGH (96%)
Suggested Action: Start PostgreSQL service or verify it's running: systemctl start postgresql
```

### Example 5: Medium Confidence (AMBIGUOUS)
```
Failure Message: "Expected X to be called but wasn't"
Error Type: Mock Assertion
Test: validateServiceCall()
Context: Service is mocked but test setup incomplete

Classification: BAD TEST (or possibly REAL BUG)
Evidence:
  - Mock assertion failed
  - Could be incorrect mock setup (BAD TEST)
  - Could be service not being called due to logic error (REAL BUG)
  - Need to review both test setup and implementation
Confidence: MEDIUM (65%)
Suggested Action: Review mock setup first, then implementation. Check: (1) mock configured correctly, (2) implementation calls service as expected
```

---

## Implementation Workflow

### 1. Input Validation
- Validate failure message exists
- Extract error type from stack trace
- Gather test context (timeout settings, environment)
- Check for previous similar failures

### 2. Pattern Matching
- Check against all defined error patterns
- Calculate match score for each category
- Weight evidence by priority

### 3. Context Analysis
- Review test setup and teardown
- Check for timing-dependent code
- Verify mock/stub configuration
- Analyze implementation code

### 4. Confidence Calculation
- Count matching indicators (weighted)
- Check for conflicting signals
- Apply confidence scoring rules
- Add human review flag if < 50%

### 5. Output Generation
- Return classification with evidence
- Include confidence score
- Suggest actionable remediation
- Provide links to relevant code/logs

---

## Usage in Forge Pipeline

### Trigger Points
1. **Test Failure:** Automatically classify when test fails
2. **Flaky Detection:** Run when test passes then fails repeatedly
3. **Manual Triage:** User requests classification of specific failure
4. **Batch Analysis:** Process multiple failures from CI/CD runs

### Output Format
```yaml
classification:
  type: "flaky|bad_test|real_bug|environment"
  confidence: "high|medium|low"
  score: 0.92
  evidence:
    - pattern: "timeout error"
      match: true
    - pattern: "async issue"
      match: true
  suggested_action: "Add retry logic with exponential backoff"
  links:
    - test_file: "path/to/test.js"
    - impl_file: "path/to/impl.js"
    - error_log: "path/to/log"
```

### Integration with Self-Heal
- **Flaky:** Route to flaky-test-fixer skill
- **Bad Test:** Route to test-corrector skill
- **Real Bug:** Route to bug-fixer skill with real_bug tag
- **Environment:** Route to environment-recover skill

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

---

## Future Enhancements

1. **Machine Learning:** Train classifier on historical failures
2. **Semantic Analysis:** Use NLP for error message understanding
3. **Cross-Correlation:** Link related failures across tests
4. **Trend Analysis:** Detect newly flaky or newly broken tests
5. **Automated Repair:** Suggest specific code fixes, not just actions
6. **Integration with Debugger:** Auto-launch debug session for real bugs

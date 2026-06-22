# Worked triage examples & edge cases — reference for `self-heal-triage`

> Progressive-disclosure Level 3 (loaded on demand). Deep detail relocated from the SKILL.md: worked examples, detailed breakdowns, edge-case deep-dives, decision trees, templates.

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

## Edge Cases

### Edge Case 1: Ambiguous Classification (Two Categories Equal Evidence)

**Symptom**

Confidence score is tied at 50/50 between two categories (e.g., CODE_BUG vs CONFIG_ERROR). Both have equally strong evidence:
```
Example: "Failed to initialize service"
  - Could be CODE_BUG (null initialization)
  - Could be CONFIG_ERROR (missing config file)
  - Both have 3 matching patterns each
  - Score: 50% CODE_BUG, 50% CONFIG_ERROR
```

**Do NOT**

- Do NOT pick at random (flipping a coin introduces noise into triage history)
- Do NOT default to the more common category (statistical bias)
- Do NOT ask for manual review immediately (you have tools)

**Action**

1. Apply evidence weighting: primary (60%) > secondary (30%) > tertiary (10%)
2. Re-score both categories with weights applied
3. Select the category with highest weighted score
4. Document tiebreaker evidence in output
5. Apply both mitigations sequentially if weights still tied:
   - Try CONFIG_ERROR fix first (faster, lower risk)
   - Re-triage after fix
   - If still failing, try CODE_BUG fix (code change, higher risk)
   - Re-triage after second fix

**Escalation**

If tied after weighting AND both fixes attempted without resolution: **NEEDS_CONTEXT**

---

### Edge Case 2: Cascading Failure (Multiple Faults Simultaneously)

**Symptom**

Eval output contains 3+ distinct error types simultaneously:
```
Example: Build fails with:
  - "cannot find module X" (CODE_BUG or CONFIG_ERROR)
  - "timeout waiting for service Y" (FLAKY or ENVIRONMENT)
  - "assertion on line 42 failed" (BAD_TEST)
```

**Do NOT**

- Do NOT triage all failures at once as a single classification (you lose causality)
- Do NOT try to find one "root cause" (cascading means multiple independent faults)

**Action**

1. Isolate failures by service/component
2. Triage each service independently
3. Determine fix sequence by dependency order:
   - CONFIG errors first (enable subsequent services)
   - CODE bugs second (enable functionality)
   - ENVIRONMENT issues third (enable runtime)
   - FLAKY issues last (improve stability after core functions work)
4. Apply fixes in sequence, re-evaluate after each
5. Document the dependency chain in output

**Escalation**

If 3+ services show cascading faults: **NEEDS_COORDINATION** (requires orchestrated fix sequence)

---

### Edge Case 3: Missing Evidence (Logs Unavailable)

**Symptom**

Service logs show no output for the failure window:
```
Example:
  - Service crashed at 10:05:32
  - Service logs are empty from 10:00:00 to 10:10:00
  - No error messages, no stack traces, no context
```

**Do NOT**

- Do NOT guess the failure classification from symptoms alone (no evidence = no triage)
- Do NOT default to ENVIRONMENT (missing logs might be logging failure, not service failure)

**Action**

1. Switch to state-based triage (evidence beyond logs):
   - Check database for incomplete transactions (unfinished work = CODE_BUG)
   - Check API state (unexpected state = CODE_BUG, unreachable = ENVIRONMENT)
   - Check file system for partial outputs (incomplete write = CODE_BUG)
   - Check process state (zombie process = CODE_BUG, missing = ENVIRONMENT)
2. Cross-reference system logs (syslog, kernel logs, container logs)
3. Check service exit code if available (non-zero = CODE_BUG, missing = ENVIRONMENT)
4. If state also empty (no evidence available at all): escalate

**Escalation**

If logs AND state both unavailable: **NEEDS_CONTEXT** (requires external investigation)

---

### Edge Case 4: New Error Pattern (Unrecognized Signature)

**Symptom**

Error doesn't match any known Classification Category error pattern:
```
Example:
  - Error: "Widget assertion failed with code XYZ_ERR_9847"
  - Pattern doesn't match any known pattern
  - No stack trace, no obvious type indicator
```

**Do NOT**

- Do NOT default to UNKNOWN (you have tools to parse it)
- Do NOT ignore recent code changes (new errors often correlate with recent changes)

**Action**

1. Parse error message into components (code, type, message, context)
2. Extract the error code/type portion (XYZ_ERR_9847)
3. Cross-reference with recent code changes (grep for code in diffs)
4. Check error handling code (where is this error thrown?)
5. Map error to the code location that throws it
6. Classify based on location:
   - If thrown in test setup → BAD_TEST
   - If thrown in app code with unhandled edge case → CODE_BUG
   - If thrown as service connectivity error → ENVIRONMENT
   - If thrown intermittently → FLAKY
7. Document the new error pattern in output for future reference

**Escalation**

If error code cannot be found in codebase: **NEEDS_CONTEXT** (unknown error source)

---

### Edge Case 5: Fault Disappears Before Triage Completes (Transient)

**Symptom**

Error was present in eval output, but absent in all logs and state by the time triage begins:
```
Example:
  - Eval run at 10:05:32 reported: "Database connection timeout"
  - Triage starts at 10:05:45 (13 seconds later)
  - Query current logs: no timeout present
  - Database health check: responding normally
  - No evidence the error ever occurred
```

**Do NOT**

- Do NOT mark failure as resolved (disappearing errors need investigation)
- Do NOT skip classification (transient behavior itself is a classification signal)

**Action**

1. Classify as TRANSIENT (explicit classification, not default)
2. Document the fault fingerprint (exact error message, timestamp, context)
3. Check if this error pattern appeared in recent history:
   - Same error in last 10 evals? → Pattern emerging
   - Same error once before? → Coincidence
   - First occurrence of this pattern? → One-off
4. Set monitoring flag for next eval run (watch for recurrence)
5. Assign confidence based on recurrence:
   - First occurrence: LOW confidence (can't confirm pattern)
   - Second occurrence: MEDIUM confidence (pattern emerging)
   - Third+ occurrence: HIGH confidence (established pattern)
6. Do not retry automatically (transient may indicate timing issue or race condition that retry masks)

**Escalation**

If transient appears 3+ times in 10 evals: **NEEDS_INVESTIGATION** (emerging transient pattern requires triage)

If transient is a one-off: Mark as **DONE_WITH_CONCERNS** (resolved, but note concern in logs)

---


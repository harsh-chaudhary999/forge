---
name: forge-verification
description: HARD-GATE: Run verification, see output, THEN claim success. Never "should pass", "confident", "should work".
type: rigid
---
# Verification Before Completion

**Iron Law:** Evidence before assertions. Always.

## Anti-Pattern Preamble: Why Agents Skip Verification

| Rationalization | The Truth |
|---|---|
| "I'm confident the code works, the logic is sound" | Confidence is not evidence. Production requires proof from actual test runs. |
| "The previous test run passed, this shouldn't have changed" | Previous runs prove nothing about current state. Dependencies, cache, timing all matter. |
| "The changes are small, I should verify manually" | Manual spot-checks miss edge cases. Automated verification is the only complete record. |
| "Unit tests pass, that's sufficient proof" | Unit tests verify components in isolation. Full verification tests integration, real conditions, end-to-end flows. |
| "It should work based on my understanding of the code" | Understanding is subjective. Output is objective. Never substitute belief for evidence. |
| "Verification takes too long, I'll assume it passes" | The time cost of verification is negligible vs. the cost of undetected failures in production. |
| "The code review looked good, that's verification enough" | Code review is about correctness; verification is about observable behavior. They are orthogonal. |
| "I tested locally, it works there" | Local testing != production verification. Environment differences, ordering, concurrency, state matter. |
| "These are boring infrastructure tests, probably fine" | Boring tests catch boring bugs that break production in boring ways. Skip none. |
| "I can just describe what passed instead of showing logs" | Logs are the only source of truth. Descriptions are filtered through human interpretation. |
| "Running verification a second time would just duplicate effort" | Running verification confirms repeatability. Flaky tests need investigation. Do not skip. |

## Detailed Workflow

### Identify What to Verify
- **Input:** Task completed, code written, tests written
- **Action:** Enumerate all verification targets (unit tests, integration tests, e2e scenarios, performance baselines)
- **Output:** Verification checklist (tasks below depend on this list)

### Execute Verification
For each verification target:

1. **Run the command exactly as written** (no shortcuts, no assumptions)
   ```
   # Example: full test suite
   npm test -- --coverage --verbose
   
   # Example: integration suite
   cargo test --release -- --test-threads=1
   
   # Example: e2e eval
   /invoke forge-eval-gate
   ```

2. **Observe and capture output**
   - Take note of test framework output (PASS/FAIL counts)
   - Capture error messages (stack traces, assertions)
   - Note timing and performance metrics
   - Record environment info (Node version, database state, network availability)

3. **Do NOT interpret** — just record facts:
   - ✗ "This probably works"
   - ✓ "9/9 tests passed, 0 skipped, 0 flaky"

### Validate Against Expectations
- **Input:** Verification output + acceptance criteria
- **Check each criterion:**
  - Expected pass count == actual pass count
  - Expected failures (if any) are present and explain-able
  - No unexpected warnings or deprecations
  - Performance within SLA (if benchmarked)
  - Coverage meets minimum threshold (if set)

- **If gap found:**
  - Do NOT claim partial success
  - Document the gap (test name, assertion, expected vs. actual)
  - Return to implementation phase
  - Re-run verification after fix
  - Repeat until all criteria met

### Claim Success (Evidence-Backed)
- **Output statement format:**
  ```
  VERIFICATION PASS
  - Test suite: 47/47 passed, 0 skipped
  - Coverage: 92% lines, 88% branches
  - E2E eval: all 8 scenarios green
  - Performance: p95 latency 145ms (SLA: 200ms)
  Evidence: [link to full test output log]
  ```

### Edge Cases & Fallback Paths

#### Case 1: Flaky Tests (Intermittent Failures)
- **Symptom:** Test passes on 1st run, fails on 2nd run
- **Do NOT:** Ignore flakiness, run once and claim success
- **Action:** 
  1. Run verification 3 times in succession
  2. If all 3 pass: document flakiness in brain (decision link)
  3. If any fail: investigate timing, isolation, state leaks
  4. Fix root cause or quarantine test (don't hide it)
  5. Re-run 3x again after fix

#### Case 2: Verification Infrastructure Down (CI/CD, test runner)
- **Symptom:** "Cannot reach test server", "Docker daemon not running"
- **Do NOT:** Claim verification passed because "it should work"
- **Action:**
  1. Restore infrastructure (restart service, reconnect VPN, etc.)
  2. Re-run verification after restoration
  3. If cannot restore: escalate as BLOCKED
  4. Document the infrastructure dependency in brain

#### Case 3: Test Timeouts or Resource Exhaustion
- **Symptom:** Tests hang, OOM, or exceed timeout
- **Do NOT:** Reduce timeout, remove resource-heavy tests
- **Action:**
  1. Investigate: is this a real bottleneck or a test environment issue?
  2. If test is too slow for product: refactor code or test
  3. If environment is too constrained: upgrade infrastructure
  4. Do not reduce verification rigor to fit constraints

#### Case 4: Verification Passes but Contradicts Earlier Assumptions
- **Symptom:** "Tests pass but I thought this would fail", or "More tests pass than I expected"
- **Do NOT:** Assume you miscounted or misunderstood earlier
- **Action:**
  1. Re-examine the actual test code (not names, not descriptions)
  2. Verify the test environment hasn't changed unexpectedly
  3. Update your mental model based on evidence
  4. Link this decision in brain (why assumption was wrong)

#### Case 5: Partial Verification (Some Suites Pass, Others Blocked)
- **Symptom:** Unit tests pass, but integration tests can't run (DB unavailable)
- **Do NOT:** Claim PASS based on unit tests alone
- **Action:**
  1. Restore the blocking constraint (DB, service, API)
  2. Re-run all suites
  3. Output is PASS only if ALL relevant suites pass
  4. If blocking constraint cannot be restored: escalate to BLOCKED

### Verification Checklist

Before claiming success, complete all items:

- [ ] All test suites identified and listed
- [ ] Each suite executed (not assumed, not predicted)
- [ ] Full output captured (logs, metrics, assertions)
- [ ] Expected vs. actual reconciled (no gaps)
- [ ] No flaky tests (or documented + escalated)
- [ ] Performance within SLA (if applicable)
- [ ] Coverage meets threshold (if set)
- [ ] Environment stable (no transient failures)
- [ ] Success statement includes evidence (not confidence)
- [ ] Brain decision recorded (verification outcome link)

Output: **PASS** (with evidence) or **BLOCKED** (can't verify, infrastructure down, unresolvable flakiness)

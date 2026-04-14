---
name: forge-verification
description: "HARD-GATE: Run verification, see output, THEN claim success. Never \"should pass\", \"confident\", \"should work\"."
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

## Iron Law

```
RUN THE VERIFICATION COMMAND AND OBSERVE THE OUTPUT BEFORE CLAIMING SUCCESS. CONFIDENCE IS NOT EVIDENCE — OBSERVED OUTPUT IS EVIDENCE.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Agent says "should pass", "confident it works", or "looks correct"** — These are beliefs, not evidence. STOP. Run the verification and show actual output before any claim of success.
- **Verification output is summarized in words instead of shown as logs** — Summaries hide failures. "Tests passed" is not evidence. STOP. Show the raw test runner output.
- **Test count drops between runs without explanation** — Tests are being silently skipped or filtered. A lower count is not a better result. STOP. Investigate why tests disappeared.
- **Agent runs only a subset of tests ("these are the relevant ones")** — Selective verification misses cross-cutting regressions. STOP. Run the full suite or explicitly justify each exclusion.
- **Infrastructure is unreachable and verification is skipped** — "Can't connect to DB" means the test ran in an invalid environment. STOP. Fix infrastructure and re-run from scratch.
- **A "flaky" test is dismissed without investigation** — Flakiness is a real bug. A flaky test means the system has nondeterministic behavior. STOP. Investigate and fix before claiming pass.
- **Verification is claimed complete but checklist items are unmarked** — Partial verification is not verification. STOP. Every checklist item must be independently confirmed.

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

## Additional Edge Cases

### Edge Case 1: Verification Tool Is Broken (False Positives, Crashes, Invalid Output)
**Situation:** Verification tool itself is buggy or invalid. It crashes, produces nonsensical output, or has false positives.

**Example:** Test framework hangs on invalid assertion syntax. Verification script crashes mid-test. Coverage report shows 200% coverage (mathematically impossible).

**Do NOT:** Trust output from broken tools or claim verification passed based on suspect output.

**Action:**
1. Identify: is the tool broken or is the code broken?
   - Run tool on known-good code (previous commit, simple example)
   - Does tool work on that code? Then your code is broken (not the tool)
   - Does tool still fail on known-good code? Then tool is broken
2. If tool is broken:
   - Do NOT use it to verify your code
   - Escalate as **BLOCKED** (verification tool unavailable)
   - Find alternate verification method or wait for tool fix
   - Document tool failure in brain
3. If code is broken:
   - Fix code
   - Re-run verification
   - Proceed normally
4. Never ship based on verification from broken tools

---

### Edge Case 2: Verification Output Is Unreadable (Logs Too Large, Format Unclear, Summary Insufficient)
**Situation:** Verification runs, produces output, but output is hard to parse or understand.

**Example:** Test output is 50MB log with no summary. Test names are cryptic (test_0001, test_0002). Output format differs from expected (JSON instead of TAP, etc.).

**Do NOT:** Summarize output in words ("looks like it passed"). Output must be human-readable.

**Action:**
1. Examine raw output:
   - Is it parseable? (valid JSON, TAP format, etc.)
   - Is it complete? (no truncation, all assertions visible)
   - Is it meaningful? (test names describe what they test)
2. If output is too large:
   - Filter to relevant sections (failures, summary, stats)
   - Or re-run with verbose=false, summary-only
   - Document what was filtered and why
3. If output format is unclear:
   - Re-run with standard format (TAP, JSON, human-readable)
   - Or write parser to convert to readable format
4. If output is still unclear:
   - Escalate as **BLOCKED** (verification output uninterpretable)
   - Tool maintainers must improve output readability
5. Document readable output in brain (with context)

---

### Edge Case 3: Verification Passes but Humans Spot Issues (Tool Missed Bugs)
**Situation:** Verification suite passes all tests, but human testing or production finds bugs. Tool missed real issues.

**Example:** All unit tests pass. Integration tests pass. Manual testing discovers "user can't export data" feature doesn't work.

**Do NOT:** Ignore human findings. Verification tools are not infallible.

**Action:**
1. Investigate: why did verification miss this?
   - Was the scenario not tested? (missing test case)
   - Was test written incorrectly? (false positive)
   - Was behavior regression not caught? (old test, changed code)
2. Add test case:
   - Write test that reproduces the human-found issue
   - Verify test fails on current code
   - Fix code
   - Verify test passes
   - Re-run all verification (not just new test)
3. Document in brain:
   - What was missed by verification
   - Why test was missing
   - Action taken (added test, fixed code)
4. Review verification coverage:
   - Are there other scenarios humans would test that verification misses?
   - Add them to verification suite
5. Key lesson: Verification catches what you test. Humans catch what you didn't test.

---

Output: **PASS** (with evidence from working tools) or **BLOCKED** (verification tool broken, output unreadable, infrastructure down, unresolvable flakiness)

## Checklist

Before claiming a task complete:

- [ ] Verification command executed and raw output observed (not summarized)
- [ ] Test count is equal to or higher than the previous run (no silent skips)
- [ ] Full test suite run, not a subset
- [ ] No "should pass" or "confident it works" language used — evidence shown
- [ ] Infrastructure is reachable (DB, cache, services confirmed up before testing)
- [ ] If human found an issue not caught by verification: test added to prevent recurrence

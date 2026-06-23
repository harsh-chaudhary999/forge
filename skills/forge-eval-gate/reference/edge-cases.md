# forge-eval-gate — Additional Edge Cases

## Additional Edge Cases

### Edge Case 1: Eval Infrastructure Unavailable (CI/CD Runner Down, Services Broken)
**Situation:** Cannot run eval because supporting infrastructure is down (Kafka broker, test runner, database service).

**Example:** "Docker daemon not running" or "Cannot connect to Redis" or "CI/CD pipeline agent offline"

**Do NOT:** Claim eval pass because "it should work if infrastructure was up"

**Action:**
1. Identify failing infrastructure component
2. Attempt restoration (restart service, reconnect, failover)
3. If restorable: restore and re-run eval from scratch
4. If NOT restorable: escalate as **BLOCKED** (with infrastructure dependency documented)
5. Record in brain: "Eval blocked due to [component] failure; cannot evaluate without infrastructure"

---

### Edge Case 2: Eval Passes but with Warnings (Flakiness, Tolerable Failures, Timeouts)
**Situation:** All scenarios technically pass, but output contains warnings (test ran twice to pass, timeouts, deprecation warnings, known flakiness).

**Example:** "Scenario passed on retry after 3s timeout" or "Test passed but took 35s, SLA is 30s"

**Do NOT:** Treat YELLOW (warnings) as GREEN (clean pass)

**Action:**
1. Categorize each warning:
   - **Transient (timing):** retry scenario 3 more times; if all pass, document flakiness, continue
   - **Performance (SLA miss):** investigate bottleneck, optimize, re-run; if cannot meet SLA, escalate to dreamer
   - **Deprecation:** fix deprecated code before merge
2. Do NOT claim "PASS" — claim **DONE_WITH_CONCERNS** + list all warnings
3. Document in brain: which warnings exist, why acceptable (or not), plan to fix
4. Code review must acknowledge warnings before approval

---

### Edge Case 3: Eval Takes Too Long (Hangs, Timeout > 1 Hour)
**Situation:** Eval scenarios hang or timeout before completion (> 60 min total runtime).

**Example:** "Test scenario deadlocked waiting for response" or "Performance test still running after 90 minutes"

**Do NOT:** Increase timeout limits to make eval pass. Long timeouts hide real bugs (deadlocks, infinite loops, incorrect waits).

**Action:**
1. Kill hanging eval (timeout it aggressively)
2. Investigate: where did eval hang?
   - Use `/self-heal-locate-fault` to identify hanging service/scenario
   - Check logs for deadlocks, infinite loops, stack traces
3. Root cause analysis:
   - Code bug (infinite loop, race condition)?
   - Test bug (incorrect wait condition)?
   - Infrastructure (slow response, contention)?
4. Fix root cause, re-run eval
5. If cannot fix within 3 attempts: escalate as **BLOCKED** (eval infrastructure too slow to validate code)

**Partial result preservation (HARD-GATE):**
Before killing a hanging eval, capture completed scenario results so re-runs don't start from scratch:

```bash
# Capture completed scenarios from semantic-eval-run.log before killing
grep '"outcome": "PASS"' qa/semantic-eval-run.log | \
  python3 -c "import sys,json; [print(json.loads(l)['stepId']) for l in sys.stdin]" \
  > qa/semantic-eval-completed-steps.txt

echo "Completed $(wc -l < qa/semantic-eval-completed-steps.txt) steps before timeout"
```

On re-run, the driver should skip steps listed in `semantic-eval-completed-steps.txt` (pass-through with prior PASS result). If the driver does not support resume, note the count so the re-run progress is tracked. Do NOT re-run 100 scenarios when 80 passed — document and re-run only the TIMED_OUT remainder.

---

Output: **EVAL PASS** (ready to merge) or **DONE_WITH_CONCERNS** (passes with warnings, must be documented) or **BLOCKED** (eval failing after 3 retries, infrastructure down, scale/perf infeasible, eval hangs)

---

### Edge Case 4: Eval Passes on Retry But Not First Run (Intermittent Flakiness)

**Symptom:** Eval fails on run 1 with a timing assertion or connection error, passes on run 2 with no code change. Dreamer wants to treat this as a pass.

**Do NOT:** Accept a retry pass as evidence of correctness. A pass on retry after an unexplained first-run failure is evidence of flakiness, not correctness.

**Action:**
1. Classify the failure as FAIL_FLAKY per `eval-judge` rules — requires 3 retries with mixed outcomes
2. Invoke `self-heal-locate-fault` with flaky flag to identify the root cause (race condition, timing window, state leak)
3. Require a root-cause fix before accepting eval pass as gate-clearing evidence
4. If root cause is in the eval scenario itself (not product code), fix the scenario and re-run
5. Escalation: **DONE_WITH_CONCERNS** if flakiness is scenario-level and documented; **BLOCKED** if product code is the cause and no fix is applied

---

### Edge Case 5: Eval Passes but Coverage Is Incomplete (Missing Surface)

**Symptom:** Eval completes with GREEN verdict but only the API driver ran — mobile driver was not configured, web driver was skipped, or a scenario surface was excluded.

**Do NOT:** Accept partial surface coverage as full eval gate passage.

**Action:**
1. Check that all surfaces defined in the scenario file were actually executed by a driver
2. If a driver was skipped intentionally (e.g., mobile not applicable to this feature), the scenario file must explicitly mark those steps as `status: SKIP` with `reason: not_applicable`
3. If a driver was skipped due to missing configuration, treat as BLOCKED — configure the driver before re-running
4. Emit DONE_WITH_CONCERNS if a non-critical surface was skipped with documented reason
5. Escalation: **BLOCKED** if a critical surface (API or DB) has zero coverage

---

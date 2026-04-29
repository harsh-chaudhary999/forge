---
name: forge-eval-gate
description: "WHEN: Implementation is complete and PRs are ready to merge. HARD-GATE: Nothing merges without eval passing. E2E product eval is the final gate."
type: rigid
version: 1.0.3
preamble-tier: 4
triggers:
  - "eval gate"
  - "nothing merges without eval"
  - "check eval before merge"
allowed-tools:
  - Bash
---
# Eval Gate (HARD-GATE)

**Rule:** No feature ships without e2e eval passing.

## Anti-Pattern Preamble: Why Agents Skip Eval

| Rationalization | The Truth |
|---|---|
| "Unit tests all pass, we don't need e2e eval" | Unit tests verify components in isolation. Eval tests integration, real services, real conditions. Different gates, not redundant. |
| "Eval is slow, we can test manually" | Manual testing is incomplete (you can't test all paths) and unrepeatable (tomorrow it might fail). Eval is the only source of truth. |
| "The code review was thorough, eval is redundant" | Code review is static analysis. Eval is dynamic behavior. A reviewed function can fail at runtime due to environment, concurrency, state. |
| "We've deployed similar features before, eval isn't needed" | Similar != identical. Dependencies changed, services upgraded, scale increased. Every feature needs eval. |
| "The 3-retry limit is too strict, we should allow more retries" | 3 retries is not a limitation, it's a signal. If eval fails after 3 attempts, the feature is broken, not the eval. Fix the feature. |
| "This is just a config change, it doesn't need full eval" | Config changes affect all downstream consumers. Eval catches config mismatches that code review never will. |
| "We can defer eval to post-merge, do it in staging" | Once merged, the bug is in main. Eval is pre-merge only. Post-merge eval is incident response, not quality control. |
| "Conductor / agent stopped after implement or review — eval was never run" | **Orchestration is incomplete.** `conductor-orchestrate` **must** enter **P4.4** (`eval-product-stack-up` + drivers) after reviews unless the human **logs an explicit task ABORT**. Partial runs are not shippable. |
| "We skipped writing `eval/*.yaml` and went straight to implementation" | **Invalid orchestration.** **State 4b** requires **`[P4.0-EVAL-YAML]`** with **≥1** file under `~/forge/brain/prds/<task-id>/eval/` **before** P4.1. No eval scenarios → P4.4 has nothing faithful to run; you only have ad-hoc manual checks. **CI:** wire **`tools/verify_forge_task.py`** (`docs/forge-task-verification.md`) so this state fails the merge, not just the session. |
| "We led the session with a blocking interactive prompt about a downstream gate before upstream prerequisites existed" | **Inverted order — violates `using-forge` Stage-local questioning.** Examples: eval/CSV waiver before **`prd-locked`** or **`qa-analysis`**; merge strategy before council; tech-plan approval before plans exist. Fix the **first** missing prerequisite for the **current** phase only. **`qa-write-scenarios` Step −1** applies to the QA→eval slice. |
| "Eval passed but nobody checked against approved QA CSV" | When **`forge_qa_csv_before_eval: true`**, GREEN eval should **exercise the same journeys** as **`qa/manual-test-cases.csv`** (IDs referenced in YAML). Otherwise “passing eval” is not proof the signed acceptance set ran. |
| "The performance test results look good from the code, we don't need eval" | Code metrics don't equal runtime behavior. Network latency, contention, GC pauses all appear at runtime, not in code. |
| "Eval caught a flaky test, we can just remove the flaky test" | A flaky test is a symptom of real behavior. Removing the test hides the problem. Fix the underlying flakiness. |
| "This change doesn't touch user flows, eval isn't critical" | Internal changes affect reliability. All changes affect user experience eventually (latency, availability, correctness). Eval all. |
| "Eval is GREEN so layout must match Figma" | Default eval drivers are **behavior-first**. **`design_new_work: yes`** tasks still need **design parity** (`design-implementation-reviewer` / **figma-design-sync** in conductor P4.2, or human visual sign-off when the harness has no design subagent). Do not treat API-green as pixel-perfect. |

## Iron Law

```
NOTHING MERGES WITHOUT EVAL PASSING. A PASSING TEST SUITE IS NOT A PASSING EVAL. EVAL IS THE ONLY PROOF THE SYSTEM WORKS END-TO-END.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **A PR is raised before eval passes** — Merging without eval means deploying untested code. STOP. Eval must return GREEN before any PR is raised.
- **Eval is run against uncommitted code** — Eval must test what will be merged, not what is in progress. STOP. Commit all changes before running eval.
- **Eval driver is skipped because the service is "not changed"** — Unchanged services still verify integration. STOP. All drivers must run regardless of which services changed.
- **Feature code or `[P4.1-DISPATCH]` appears in logs without `[P4.0-EVAL-YAML]`** — Eval scenarios were never authored. STOP. Back up to **`eval-scenario-format`** + **`eval-translate-english`**; do not treat the task as shippable.
- **Eval fails but team proceeds citing "it's a known flaky test"** — Known flakiness is a real bug. STOP. Fix the flakiness or remove the test; do not proceed past a failing eval.
- **Self-heal has run 3 times and eval still fails** — The cap has been reached. STOP. Escalate to human with full failure context. Do not attempt a 4th self-heal cycle.
- **Eval verdict is YELLOW and team treats it as GREEN** — YELLOW means non-critical failures. STOP. Investigate YELLOW scenarios before merging; do not treat YELLOW as acceptable.

## Detailed Workflow

### Prepare Eval Scenarios
- **Input:** Locked shared-dev-spec (from council)
- **Action:** Generate or retrieve eval scenarios for all user journeys
  - Use `/eval-translate-english` to convert spec requirements to YAML scenarios
  - Identify critical paths (auth, checkout, data integrity, scale)
  - Identify edge cases (timeouts, network failures, concurrent operations)
- **QA CSV Traceability Check** (if `qa/manual-test-cases.csv` exists):
  - For each row with status `approved`, verify at least one eval YAML scenario references its journey ID
  - Log coverage: `X/Y approved journeys covered by eval scenarios`
  - Block if any approved journey has no corresponding eval scenario — do not proceed to stack-up until coverage is complete
  - Write coverage report to brain: `~/forge/brain/prds/<task-id>/eval/qa-csv-coverage-<YYYYMMDD>.md`
- **Output:** Eval scenario file (YAML format) with verified QA CSV coverage

### Bring Up Stack
- **Input:** Eval scenarios
- **Action:** Stand up all services required by eval
  1. Invoke `/eval-product-stack-up` (reads forge-product.yaml)
     - Spins up database (with schema migrations)
     - Spins up caches (Redis, etc.)
     - Spins up event bus (Kafka, RabbitMQ)
     - Spins up search (Elasticsearch)
     - Spins up all app services (backend, web, mobile via ADB)
  2. Verify all services healthy (health checks pass)
- **Output:** All services running, ready for eval

### Execute Eval Scenarios
- **Input:** Running stack + eval scenarios
- **Action:** Drive all scenarios through the stack
  1. Invoke `/eval-coordinate-multi-surface` (orchestrates multi-driver scenarios)
     - Web driver (Chrome DevTools Protocol via `/eval-driver-web-cdp`)
     - API driver (HTTP requests via `/eval-driver-api-http`)
     - DB driver (MySQL queries via `/eval-driver-db-mysql`)
     - Cache driver (Redis commands via `/eval-driver-cache-redis`)
     - Event bus driver (Kafka produce/consume via `/eval-driver-bus-kafka`)
     - Search driver (Elasticsearch queries via `/eval-driver-search-es`)
     - Mobile driver (ADB via `/eval-driver-android-adb`)
  2. Each scenario runs end-to-end:
     - Step 1: User takes action in web (or API call)
     - Step 2: Backend processes request
     - Step 3: Data persists in DB
     - Step 4: Cache updates (or invalidates)
     - Step 5: Events published to bus
     - Step 6: Search index updated
     - Step 7: User sees result (web driver verifies)
  3. Verify each step produces expected output
- **Output:** Eval results (PASS all scenarios, or FAIL on specific scenario + step)

### YELLOW Verdict Triage

**YELLOW means non-critical failures detected.** Do not treat YELLOW as GREEN.

For each YELLOW scenario:

1. **Identify** the scenario name and failing assertion from eval output
2. **Classify** — run the scenario 3× in isolation:
   - If 3/3 pass → flake. Document and proceed (step 3)
   - If any of 3 fail → real regression. Treat as RED. Do not merge.
3. **Document** each YELLOW decision in brain:
   - Path: `~/forge/brain/prds/<task-id>/eval/yellow-triage-<YYYYMMDD>.md`
   - Content: scenario name, classification (flake/regression), 3× run results, decision
4. **YELLOW is only acceptable** when all 3× isolation runs pass. One failure in 3 = RED.
5. After triaging all YELLOWs: all cleared → proceed to Claim Eval Pass. Any RED → enter Self-Heal Loop.

### Diagnose Failures
**IF any scenario fails:**

- **Do NOT claim eval pass, do NOT merge**
- Invoke `/self-heal-locate-fault` to identify which service failed
  - Parse eval output, find first failure point (e.g., "DB query returned wrong count")
  - Identify service responsible (e.g., "backend service didn't validate input")
- Invoke `/self-heal-triage` to classify the failure
  - Flaky (timing-dependent, retry may pass)
  - Bad test (test itself is wrong, not the code)
  - Real bug (code is broken, needs fix)

### Self-Heal Loop (Max 3 Retries)
- **Attempt 1:**
  1. If flaky: re-run scenario
  2. If bad test: fix test, re-run scenario
  3. If real bug: locate bug in code, fix, re-run scenario
  4. Re-run all scenarios (not just failed one)

- **Attempt 2:**
  1. If still failing: diagnose deeper
  2. Invoke `/self-heal-systematic-debug` (4-phase debugging)
     - Investigate (read logs, traces)
     - Hypothesize (what could cause this?)
     - Test hypothesis (add logging, re-run)
     - Verify fix (all scenarios pass again)
  3. Re-run all scenarios

- **Attempt 3:**
  1. If still failing: this is a real blocker
  2. Document the failure in brain (decision ID: EVALFAIL-...)
  3. Escalate: BLOCKED (eval failing, can't fix after 3 retries)

### Ship-Readiness Score

After all scenarios complete, compute a 0-10 ship-readiness score:

```bash
python3 -c "
total = <total_scenarios>
passed = <passed_count>
yellow = <yellow_count>
failed = <failed_count>
manual_skipped = <manual_skipped_count>

# Weight: failed = -1.5pt, yellow = -0.5pt, manual_skipped = -0.25pt per scenario
score = 10.0
if total > 0:
    score -= (failed / total) * 10 * 1.5
    score -= (yellow / total) * 10 * 0.5
    score -= (manual_skipped / total) * 10 * 0.25
score = max(0.0, min(10.0, round(score, 1)))

tier = 'GREEN' if score >= 8.0 else 'YELLOW' if score >= 5.0 else 'RED'
print(f'Ship-readiness: {score}/10 ({tier})')
print(f'  Passed: {passed} | Yellow: {yellow} | Failed: {failed} | Skipped: {manual_skipped}')
if tier == 'RED':
    print('  Action: Do not merge. Fix failing scenarios.')
elif tier == 'YELLOW':
    print('  Action: Investigate yellow scenarios before merging.')
else:
    print('  Action: Safe to proceed to PR.')
"
```

**Score tiers:**
- **8–10 (GREEN):** Safe to merge
- **5–7.9 (YELLOW):** Investigate before merging
- **0–4.9 (RED):** Do not merge

Write the score to brain alongside the eval results:
```bash
# Append to existing eval result file:
echo "ship_readiness_score: <score>" >> "$EVAL_RESULT_FILE"
echo "ship_readiness_tier: <tier>" >> "$EVAL_RESULT_FILE"
```

### Claim Eval Pass
- **Input:** All scenarios PASS (3 consecutive runs if flaky history)
- **Output statement:**
  ```
  EVAL PASS
  - All X scenarios passed end-to-end
  - All services healthy throughout eval
  - Critical paths verified: [list]
  - Edge cases tested: [list]
  - Performance within SLA: [metrics]
  Evidence: [link to eval output logs]
  Ready for merge.
  ```

### Edge Cases & Fallback Paths

#### Case 1: Eval Infrastructure Down (CI/CD Runner, Kafka Broker)
- **Symptom:** "Cannot connect to Kafka broker" or "Docker daemon not running"
- **Do NOT:** Claim eval pass because "it would work if infrastructure was up"
- **Action:**
  1. Restore the failing infrastructure
  2. Verify health checks pass
  3. Re-run eval from scratch
  4. If cannot restore: escalate as BLOCKED

#### Case 2: Flaky Test (Passes Sometimes, Fails Sometimes)
- **Symptom:** "Scenario fails on run 1, passes on run 2"
- **Do NOT:** Accept flakiness as "just how it is"
- **Action:**
  1. Run scenario 5 times in succession
  2. Classify flakiness type:
     - Timing issue: add explicit waits, fix race condition
     - Cleanup issue: clear state between runs
     - Concurrency issue: add locks or constraints
  3. Fix root cause in code
  4. Re-run scenario 5 times again (must be stable)

#### Case 3: Test Itself Is Wrong (Bad Assertion)
- **Symptom:** Eval expects X but spec says Y; code implements Y correctly
- **Do NOT:** Change code to match wrong test
- **Action:**
  1. Verify spec and code both match intended behavior
  2. Update test assertion to match spec
  3. Re-run eval
  4. Document: "Test was incorrect, not code"

#### Case 4: External Service Unavailable (Third-Party API, Dependency)
- **Symptom:** "Payment service is down, eval can't complete"
- **Do NOT:** Mock the service to make eval pass
- **Action:**
  1. If service is critical path: escalate as BLOCKED
  2. If service is optional: skip that scenario, eval rest
  3. For optional services: document dependency in brain
  4. Create follow-up task: "Verify with payment service after they recover"

#### Case 5: Performance Test Fails (Latency > SLA)
- **Symptom:** "API endpoint p95 latency is 450ms, SLA is 300ms"
- **Do NOT:** Relax the SLA to make eval pass
- **Action:**
  1. Profile the endpoint (where is time spent?)
  2. Optimize: DB query, algorithmic complexity, service call chaining
  3. Re-run perf eval
  4. If cannot meet SLA: escalate to dreamer (requirement vs. implementation trade-off)

#### Case 6: Scale Test Fails (System buckles under load)
- **Symptom:** "System handles 100 users fine, but fails at 500 concurrent users"
- **Do NOT:** Reduce scale requirement to make test pass
- **Action:**
  1. Identify bottleneck (DB connection pool, service instance count, queue depth)
  2. Scale infrastructure (more servers, connection pool size, etc.)
  3. Re-run scale eval
  4. If scale goal is not feasible with reasonable cost: escalate to dreamer

### Eval Checklist

Before merging, verify:

- [ ] Eval scenarios defined and in YAML format
- [ ] All services running (DB, cache, bus, search, apps)
- [ ] All services health checks passing
- [ ] All eval scenarios executed (not assumed, not skipped)
- [ ] All scenarios PASS (100%, not partial)
- [ ] No flaky tests (stable across 3+ runs if history)
- [ ] Performance within SLA (or escalated)
- [ ] Scale targets verified (or escalated)
- [ ] Integration verified: UI → API → DB → Cache → Events → Search
- [ ] Edge cases tested (concurrent ops, failures, recovery)
- [ ] All services remain healthy after eval
- [ ] Eval output captured and linked in brain
- [ ] Self-heal loop retries <= 3 (or escalated as BLOCKED)

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

## Non-Interactive Ship Policy

After eval passes and the ship-readiness score is GREEN (≥8.0), the conductor should auto-proceed through phase 5 without requiring human confirmation for these mechanical steps:

| Step | Auto-proceed? | Condition |
|------|--------------|-----------|
| Create PR | ✓ Yes | Score ≥ 8.0, no open review findings |
| Set PR description | ✓ Yes | Always |
| Request reviewers | ✓ Yes | If reviewer list is in brain |
| Merge PR | ✗ Human gate | Always requires human approval |
| Deploy to staging | ✗ Human gate | Always requires human approval |

**Only stop for:**
- Merge conflicts (unresolvable without human judgment)
- Test failures (can't proceed)
- Review findings marked ASK tier or MUST-FIX
- MAJOR or MINOR version bumps on shared contracts
- Plan items with status NOT DONE
- Ship-readiness score < 8.0

**Everything else is auto.** Do not pause to ask "should I proceed?" for GREEN eval results. Pausing for non-judgment calls wastes human attention on mechanical steps.

## Checklist

Before claiming eval gate passed:

- [ ] Eval ran against committed code (not in-progress work)
- [ ] All scenario surfaces returned results
- [ ] eval-judge returned GREEN or DONE_WITH_CONCERNS with documented concerns
- [ ] Self-heal attempted on any failures before declaring BLOCKED
- [ ] Eval verdict written to brain before PRs are raised

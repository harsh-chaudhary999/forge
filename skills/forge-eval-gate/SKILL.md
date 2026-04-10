---
name: forge-eval-gate
description: HARD-GATE: Nothing merges without eval passing. E2E product eval is the final gate.
type: rigid
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
| "The performance test results look good from the code, we don't need eval" | Code metrics don't equal runtime behavior. Network latency, contention, GC pauses all appear at runtime, not in code. |
| "Eval caught a flaky test, we can just remove the flaky test" | A flaky test is a symptom of real behavior. Removing the test hides the problem. Fix the underlying flakiness. |
| "This change doesn't touch user flows, eval isn't critical" | Internal changes affect reliability. All changes affect user experience eventually (latency, availability, correctness). Eval all. |

## Detailed Workflow

### Prepare Eval Scenarios
- **Input:** Locked shared-dev-spec (from council)
- **Action:** Generate or retrieve eval scenarios for all user journeys
  - Use `/eval-translate-english` to convert spec requirements to YAML scenarios
  - Identify critical paths (auth, checkout, data integrity, scale)
  - Identify edge cases (timeouts, network failures, concurrent operations)
- **Output:** Eval scenario file (YAML format)

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

Output: **EVAL PASS** (ready to merge) or **BLOCKED** (eval failing, real bug after 3 retries, infrastructure down, scale/perf infeasible)

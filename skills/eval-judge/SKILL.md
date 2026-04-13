---
name: eval-judge
description: "WHEN all eval drivers have returned results and you need a final pass/fail verdict. Receives driver outputs from eval-coordinate-multi-surface and renders GREEN/RED/YELLOW judgment."
type: rigid
requires: [brain-read]
---

# Eval Judge (HARD-GATE)

**Iron Law:** NO CODE MERGES WITHOUT EVAL GREEN.

The eval-judge is the terminal gate in the eval pipeline. It receives results from every eval driver (API, DB, cache, search, message bus, web, mobile), applies the judgment algorithm, and emits a verdict. No human, no agent, and no rationalization overrides a RED verdict.

## Anti-Pattern Preamble: Why Agents Fabricate Green Verdicts

| # | Rationalization | The Truth |
|---|---|---|
| 1 | "Most drivers passed, the one failure is minor" | A single critical-path failure is RED. Partial pass is not pass. Severity classification exists for a reason -- use it, don't override it. |
| 2 | "The failure is flaky, I saw it pass last time" | Flaky is a classification that requires 3x retry evidence. One prior pass is anecdote, not evidence. Run the retries. |
| 3 | "The performance numbers are close enough to SLA" | Close is not within. 305ms against a 300ms SLA is a fail. Tolerances are defined in the scenario, not invented at judgment time. |
| 4 | "All functional tests pass, the bus event delay is just infrastructure noise" | Event delivery timing is product behavior. If the consumer depends on sub-second delivery and you measured 4 seconds, the product is broken. |
| 5 | "I already fixed the bug, re-running eval is redundant" | Fixing is not verifying. The fix must flow through eval to become evidence. No shortcutting the feedback loop. |
| 6 | "The RED is from a non-critical driver so I can merge and fix later" | Non-critical failures produce YELLOW, not GREEN. YELLOW requires documentation and explicit acceptance. Silently merging is not acceptance. |
| 7 | "The eval environment differs from production so this failure does not count" | Eval environment is the canonical test surface. If it differs from production, fix the environment -- do not discard the result. |

## Judgment Algorithm

### Phase 1: Collect Driver Results

Receive the result payload from `/eval-coordinate-multi-surface`. Each driver reports:

```yaml
driver: <driver-name>        # e.g. eval-driver-api-http
scenario: <scenario-id>       # e.g. SC-AUTH-001
step: <step-number>           # e.g. 3
status: PASS | FAIL | SKIP | ERROR
failure_mode: stop | continue | log   # from scenario definition
critical: true | false        # from scenario definition
duration_ms: <int>
evidence: <string>            # assertion detail, HTTP status, query result
error: <string | null>        # stack trace or error message if FAIL/ERROR
retry_count: <int>            # number of times this step was retried
retry_history: [...]          # outcomes of prior retries
```

**HARD-GATE:** If the result payload is missing or malformed, verdict is RED with reason `INCOMPLETE_DATA`. Do not guess.

### Phase 2: Classify Each Step

For every step in every scenario, assign a classification:

| Step Status | Critical Flag | Classification |
|---|---|---|
| PASS | any | STEP_PASS |
| FAIL | true | STEP_FAIL_CRITICAL |
| FAIL | false | STEP_FAIL_NON_CRITICAL |
| SKIP | any | STEP_SKIPPED |
| ERROR | any | STEP_ERROR (treat as STEP_FAIL_CRITICAL) |

### Phase 3: Apply Failure Mode

Each step carries a `failure_mode` from the scenario definition:

| Failure Mode | On FAIL Behavior |
|---|---|
| `stop` | Halt scenario execution immediately. Record all remaining steps as STEP_SKIPPED. |
| `continue` | Record failure, proceed to next step. |
| `log` | Record failure as warning, proceed. Does not affect verdict unless critical. |

### Phase 4: Aggregate to Verdict

Scan all classified steps and determine the overall verdict:

**ALL_PASS** -- Every step across every scenario is STEP_PASS.
- Verdict: **GREEN**
- Action: Eval complete. Ready for merge.

**FAIL_CRITICAL** -- One or more steps classified as STEP_FAIL_CRITICAL or STEP_ERROR.
- Verdict: **RED**
- Action: Halt. Report evidence. Invoke `/self-heal-locate-fault`. No merge.

**FAIL_FLAKY** -- Step(s) failed, but retry_history shows intermittent pass/fail pattern AND retry_count >= 3.
- Verdict: **RED** (flaky is still RED until root cause is fixed)
- Action: Classify as flaky in report. Invoke `/self-heal-locate-fault` with flaky flag. Require root-cause fix before re-eval.
- **HARD-GATE:** Flaky classification requires exactly 3+ retries with mixed pass/fail outcomes. Fewer than 3 retries means the step is FAIL_CRITICAL, not flaky.

**PARTIAL_PASS_NON_CRITICAL** -- All critical steps pass, but one or more non-critical steps failed.
- Verdict: **YELLOW**
- Action: Document which non-critical steps failed, the driver that reported the failure, the evidence, and the reason the step is classified non-critical. Write to brain via `/brain-write` with decision ID `EVALJUDGE-YYYY-MM-DD-HH`. YELLOW requires explicit dreamer acknowledgment before merge proceeds.

### Phase 5: Compile Output

The judge emits a structured verdict:

```yaml
verdict: GREEN | RED | YELLOW
timestamp: <ISO-8601>
scenario_count: <int>
step_count: <int>
pass_count: <int>
fail_count: <int>
skip_count: <int>
affected_services: [<service-name>, ...]
evidence_summary:
  - scenario: <scenario-id>
    step: <step-number>
    driver: <driver-name>
    status: <PASS|FAIL|SKIP|ERROR>
    evidence: <string>
    classification: <ALL_PASS|FAIL_CRITICAL|FAIL_FLAKY|PARTIAL_PASS_NON_CRITICAL>
retry_history:
  - scenario: <scenario-id>
    step: <step-number>
    attempts: <int>
    outcomes: [PASS, FAIL, FAIL, ...]
decision_id: <EVALJUDGE-YYYY-MM-DD-HH | null>
```

## Adjudication Rules

These rules are applied in order. First match wins.

1. **Any STEP_ERROR present** -- Verdict RED. Errors are infrastructure or driver failures; they invalidate the entire run.
2. **Any STEP_FAIL_CRITICAL present** -- Verdict RED. Critical path is broken.
3. **Any STEP_FAIL with retry_count >= 3 and mixed outcomes** -- Verdict RED (FAIL_FLAKY). Flaky but still RED.
4. **Any STEP_FAIL_NON_CRITICAL present, zero critical failures** -- Verdict YELLOW. Partial pass.
5. **All steps STEP_PASS or STEP_SKIPPED (where skip is due to upstream stop, not failure)** -- Verdict GREEN.
6. **All steps STEP_SKIPPED (no steps actually ran)** -- Verdict RED with reason `NO_EXECUTION`. An eval that did not execute is not a pass.

## Edge Cases

| # | Edge Case | Symptom | Action | Fallback |
|---|---|---|---|---|
| 1 | **Timing-dependent assertion** | Cache TTL assertion fails because eval checked 1ms before expiry; passes on retry | Retry step 3x with exponential backoff (100ms, 500ms, 2s). If 2 of 3 retries pass, classify as timing-sensitive and flag for scenario hardening. | If all 3 retries fail, classify as FAIL_CRITICAL. Do not invent wider timing tolerances at judgment time. Escalate to scenario author to fix assertion window. |
| 2 | **Flaky vs real failure** | Step fails intermittently across retries with no obvious pattern | Require exactly 3 retries. Inspect retry_history: if outcomes are mixed (e.g., FAIL, PASS, FAIL), classify FAIL_FLAKY. If all 3 fail, classify FAIL_CRITICAL. | Invoke `/self-heal-locate-fault` with full retry evidence. If fault locator identifies a race condition or state leak, document and require code fix before re-eval. |
| 3 | **Partial pass across drivers** | API driver passes, DB driver passes, but cache driver reports stale data after write | Verdict is YELLOW only if cache step is marked non-critical in the scenario. If cache consistency is critical-path, verdict is RED regardless of other drivers passing. | Cross-check the scenario definition for critical flag. If the scenario author omitted the critical flag, treat as critical (fail-safe default). Document the gap. |
| 4 | **Conflicting driver results** | Web driver sees success page, but DB driver shows no row inserted | Verdict RED. Conflicting evidence across drivers indicates a real bug (e.g., frontend optimistic update without backend commit). Both driver results are included in evidence. | Invoke `/self-heal-locate-fault` targeting the gap between the two drivers. Typical root causes: async write not flushed, transaction rollback after UI response, eventual consistency window exceeded. |
| 5 | **Performance degradation without functional failure** | All assertions pass, but p95 latency is 2x the SLA threshold | If the scenario defines an `sla_ms` field, compare measured `duration_ms` against it. Breach means FAIL for that step. If no SLA defined, log a warning but do not fail. | Emit YELLOW with performance advisory. Flag the scenario for SLA definition if missing. Do not silently pass a slow endpoint -- surface the data so the dreamer can decide. |
| 6 | **Driver timeout / no response** | A driver does not return a result within the scenario timeout | Treat as STEP_ERROR. The judge does not distinguish between "driver crashed" and "service hung." Both produce RED. | Invoke `/eval-coordinate-multi-surface` to check driver health. If the driver process is alive but the target service is unresponsive, the fault is in the service, not the driver. Document accordingly. |
| 7 | **Empty scenario list** | Eval is invoked but no scenarios are provided | Verdict RED with reason `NO_SCENARIOS`. An eval with no scenarios is not a pass -- it is a configuration error. | Check brain for expected scenario count. If scenarios should exist but are missing, invoke `/eval-scenario-format` to regenerate from spec. |

## Red Flags -- STOP

Stop immediately and escalate if any of these are true:

- **Verdict changed after initial determination.** Once the judge emits GREEN/RED/YELLOW, the verdict is final for that run. Do not retroactively change it. Re-run eval to get a new verdict.
- **Evidence is missing from a FAIL step.** Every FAIL must carry evidence (error message, assertion detail, HTTP status). A FAIL without evidence is a judge bug -- fix the judge, do not emit a verdict.
- **retry_count exceeds 3 without explicit escalation.** The self-heal loop cap is 3. If a step has been retried more than 3 times, something is wrong with the retry logic, not the eval. Halt and investigate.
- **A driver reports PASS but the evidence contradicts.** If the API driver says PASS but the evidence field says "HTTP 500", the driver is broken. Verdict RED, investigate driver correctness.
- **Agent attempts to override verdict manually.** No agent, subagent, or orchestrator may change a RED to GREEN. The only path from RED to GREEN is a new eval run that passes.
- **Scenario definitions modified between eval run and judgment.** If scenarios change mid-pipeline, the results are invalid. Verdict RED with reason `SCENARIO_TAMPER`.

## Verification Checklist

Before emitting the final verdict, verify:

- [ ] All driver results received (no missing drivers from the expected set)
- [ ] Every step in every scenario has a classification (no unclassified steps)
- [ ] Critical flag respected: all critical-step failures produce RED
- [ ] Failure modes applied: stop/continue/log honored per step definition
- [ ] Flaky classification backed by 3x retry evidence (not assumed)
- [ ] YELLOW verdicts include full non-critical failure documentation
- [ ] Evidence field populated for every FAIL and ERROR step
- [ ] Performance SLA checked where `sla_ms` is defined in scenario
- [ ] Verdict output is valid YAML matching the schema in Phase 5
- [ ] Decision recorded in brain for YELLOW and RED verdicts
- [ ] Affected services list is accurate (derived from driver + scenario metadata)
- [ ] No verdict override occurred after initial determination

## Cross-References

| Related Skill | Relationship |
|---|---|
| `/eval-coordinate-multi-surface` | Upstream. Provides the driver result payload that this skill judges. |
| `/eval-scenario-format` | Defines the scenario YAML schema including `failure_mode`, `critical`, and `sla_ms` fields consumed by the judge. |
| `/self-heal-locate-fault` | Downstream. Invoked by the judge on RED/FAIL_FLAKY verdicts to diagnose which service caused the failure. |
| `/forge-eval-gate` | Parent gate. The eval-judge is the decision engine inside the eval gate workflow. |
| `/brain-write` | Used to persist YELLOW and RED verdict decisions with full evidence for audit trail. |

---
name: self-heal-triage
description: "WHEN: An eval scenario has failed and a fault has been located. Classify the failure — flaky, bad test, real bug, or environment — for YAML driver runs or semantic `semantic-eval-run.log` / manifest outcomes, with evidence and confidence score."
type: rigid
requires: [brain-read]
version: 1.0.2
preamble-tier: 3
triggers:
  - "triage eval failure"
  - "classify failure type"
  - "is this a bug or flake"
allowed-tools:
  - Bash
---

# Self-Heal Triage Skill

## Anti-Pattern Preamble

### Anti-Pattern 1: "The error message says DB error so it's a DB fault"

**Why This Fails**

Surface error often misidentifies root cause. A "DB connection error" might originate from:
- Application timeout causing DB query to fail
- Network layer misconfiguration preventing connection
- Query performance issue (hanging query, not failed connection)
- Connection pool exhaustion (app-side resource leak)
- Authentication token expiration (not DB unavailability)

The error type you see is the symptom, not the diagnosis.

If the latest **`qa-run-report-*.md`** has YAML **`flake_suspected: true`** (same scenario IDs failed on consecutive runs), treat **flake** as a **leading** hypothesis — still verify evidence; do not downgrade triage rigor.

**Enforcement — MUST Do All:**
- MUST trace the error back 3+ layers (where did DB error originate?)
- MUST check application logs for pre-DB errors (timeout, pool exhaustion)
- MUST verify connectivity to DB independently (ping, telnet, health check)
- MUST review query performance metrics (query duration, lock contention)
- MUST check authentication/credentials separately from DB availability

---

### Anti-Pattern 2: "Triage once and assume the category is stable"

**Why This Fails**

Multiple faults can coexist simultaneously. After applying a fix:
- A CONFIG_ERROR fix may reveal a hidden CODE_BUG
- Fixing flakiness in one component exposes flakiness in another
- Evidence quality changes as fixes are applied (state changes, logs grow)
- Initial classification is based on available evidence at one point in time

A single triage is a snapshot, not ground truth.

**Enforcement — MUST Do All:**
- MUST retriage after each fix is applied (do not assume category remains stable)
- MUST document evidence changes as state evolves (before/after comparison)
- MUST track category migration if classification changes (log the transition)
- MUST cross-check confidence score after each step (does it stay MEDIUM+?)
- MUST escalate if category changes more than once (indicates cascading faults)

---

### Anti-Pattern 3: "Low confidence score means skip to manual fix"

**Why This Fails**

Low confidence doesn't mean abandon — it means gather more evidence. Skipping to manual fix when confidence is low means:
- Losing opportunity to improve classification signals
- Applying wrong remediation strategy
- Missing patterns that future automated triage could catch

Low confidence is a request for more data, not permission to exit.

**Enforcement — MUST Do All:**
- MUST expand evidence collection before escalating (logs, state, traces)
- MUST refine classification rules based on new evidence (revisit patterns)
- MUST increase sample size if single failure (re-run 3+ times for signals)
- MUST document confidence gaps (why could confidence not reach MEDIUM+?)
- MUST attach low-confidence evidence to escalation ticket (human can review it)

---

### Anti-Pattern 4: "Infrastructure faults always need escalation"

**Why This Fails**

Many infra faults are transient and self-heal within one retry cycle:
- Network timeouts often recover on retry
- Service overload resolves as load decreases
- Transient DNS failures resolve on retry
- Temporary resource exhaustion recovers
- Brief service restarts complete within seconds

Not all infra faults require immediate escalation.

**Enforcement — MUST Do All:**
- MUST retry before escalating (one deterministic retry, not random retries)
- MUST check transience patterns (does error recur or resolve?)
- MUST document behavior (transient = self-heals, persistent = needs escalation)
- MUST set retry limits (max 1 retry for transient, no retries for persistent)
- MUST escalate only persistent infra faults to NEEDS_CONTEXT

---

### Anti-Pattern 5: "Ambiguous classifications are uncategorizable"

**Why This Fails**

Ambiguity (two categories tied in evidence) doesn't mean uncategorizable — it means apply evidence weighting:
- Primary evidence (direct error type) should weight 60%
- Secondary evidence (context) should weight 30%
- Tertiary evidence (patterns) should weight 10%

Triage always has a strongest signal if you weight properly.

**Enforcement — MUST Do All:**
- MUST apply evidence weights (primary > secondary > tertiary)
- MUST pick the category with highest weighted score (never random)
- MUST document tiebreaker reasoning (which evidence decided it)
- MUST escalate only if weighted scores remain tied after weighting
- MUST attach confidence penalty if tiebreaker was necessary (note in evidence)

---

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
TRIAGE COMPLETES BEFORE ANY FIX IS APPLIED. CLASSIFY WITH EVIDENCE AT MEDIUM OR HIGHER CONFIDENCE OR ESCALATE. A CLASSIFICATION WITHOUT EVIDENCE IS A GUESS — GUESSES WASTE SELF-HEAL LOOP ATTEMPTS.
```

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

## Semantic path (Phase 4.4) — triage without driver payloads

**When:** **`self-heal-locate-fault`** traced RED using **`qa/semantic-eval-run.log`** (JSON lines) and **`qa/semantic-eval-manifest.json`**.

**Evidence priority:**
1. **`semantic-eval-run.log`** — per-step **`status`**, **`error`** / **`message`**, **`surface`**, **`id`**.
2. **`semantic-automation.csv`** — **`Intent`**, **`DependsOn`**, **`Surface`** for the failed **`id`**.
3. **`semantic-eval-manifest.json`** **`outcome`** — must align with log; mismatch → treat as **environment / tooling** or incomplete run (**BAD TEST** / harness).

**Classification hints:**
- **`status: FAILED`** + stack/message pointing at product code → **REAL BUG** on the service mapped from **`surface`** (see **`product.md`**).
- Assertion text in **`intent`** wrong vs spec but app correct → **BAD TEST** (semantic row or expectation drift).
- Empty **`semantic-eval-run.log`** but **`outcome: fail`** → **ENVIRONMENT** or aborted runner; gather host/driver logs.
- Intermittent passes across re-runs with same manifest → **FLAKY** (driver or external dependency).

Do **not** require YAML scenario IDs — use semantic **`id`** fields consistently.

### RED_INFRA Pre-Check (runs BEFORE classification)

Before classifying any failure, check whether `forge-eval-gate` has logged a `RED_INFRA` outcome:

1. Read `~/forge/brain/prds/<task-id>/qa/semantic-eval-manifest.json` or `conductor.log`.
2. If `outcome: RED_INFRA` is present (ECONNREFUSED, Docker daemon down, MCP unavailable, dependent service not reachable):
   - **Do NOT classify this as a code bug, flaky test, or bad test.**
   - **Do NOT consume a self-heal retry attempt.**
   - Immediately write a BLOCKED escalation to `~/forge/brain/prds/<task-id>/blockers/<timestamp>-infra-failure.md` with the infrastructure symptom.
   - Output: `BLOCKED — RED_INFRA: <symptom>. No retry consumed. Human must resolve infrastructure before re-running eval.`
   - Stop. Do not proceed to the classification procedure below.
3. Only if `outcome` is NOT `RED_INFRA`: proceed to the classification procedure.

**Why:** Infrastructure failures cannot be fixed by code changes. Consuming self-heal retries on infra failures wastes the entire retry budget on unfixable symptoms, leaving zero retries for the real code bug that will surface once infra is restored.

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

## Reference (load on demand)

Deep detail — worked examples, detailed section breakdowns, edge-case deep-dives, templates,
and decision trees — lives in **`reference/triage-examples-edge-cases.md`** (Agent Skills progressive disclosure). This
SKILL.md is the operational contract: discipline, core workflow/decision logic, and checklists.

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

## Decision Tree: Confidence Handling

When classification confidence is below MEDIUM (< 60%), use this decision tree:

```
START: Classification complete, confidence score calculated
  |
  +-- Confidence >= 85% (HIGH)?
  |    YES → STOP. Classification ready for downstream routing.
  |    NO  → Continue
  |
  +-- Confidence >= 60% (MEDIUM)?
  |    YES → STOP. Classification ready, note confidence penalty in output.
  |    NO  → Continue (confidence < 60%, LOW)
  |
  +-- LOW Confidence (< 60%)
       |
       +-- Can we collect more evidence?
       |    YES:
       |      1. Expand evidence search:
       |         - Check logs from ±5 minutes around failure
       |         - Query service state (DB, cache, API)
       |         - Check process state and resource metrics
       |         - Review recent code changes in that area
       |      2. Re-run pattern matching with expanded evidence
       |      3. Recalculate confidence
       |      4. LOOP back to "Confidence >= 60%?" check
       |
       |    NO:
       |      1. Document evidence gaps (what prevented gathering more evidence?)
       |      2. Apply evidence weighting to maximize signal from available evidence
       |      3. Re-score with weights applied
       |      4. If confidence still < 60%:
       |         a. Mark output with ESCALATION: NEEDS_CONTEXT
       |         b. Attach all evidence collected
       |         c. Include confidence score and reasoning
       |         d. Route to human triage
       |      5. If confidence now >= 60%:
       |         a. STOP. Classification ready with confidence note.
```

**Key Branches Explained:**

1. **HIGH Confidence (>= 85%):** Clear signals, low ambiguity. Proceed to fix routing without additional checks.

2. **MEDIUM Confidence (60-84%):** Acceptable for automated fix attempt. Note: if first fix doesn't resolve, re-triage before second fix.

3. **LOW Confidence (< 60%) with Available Evidence:**
   - Expand search scope (logs, state, metrics)
   - Re-score with complete evidence
   - Often raises confidence to MEDIUM with just more data
   - Re-check after each evidence collection round

4. **LOW Confidence with No Additional Evidence:**
   - Apply evidence weighting to maximize signal
   - If still LOW after weighting: escalate
   - Document gaps for human investigator
   - Include confidence and evidence in escalation ticket

---

## Quick Reference Card

| Category | Primary Signals | Secondary Evidence | Confidence Triggers | High Confidence | Escalation Route |
|---|---|---|---|---|---|
| **FLAKY TEST** | timeout, deadline, race, async, intermittent | timing patterns, test isolation, external service mock | 1+ explicit timing errors + context | timeout + deadline, clear async/await issue, test passes on retry | flaky-test-fixer skill |
| **BAD TEST** | AssertionError, assertion mismatch, expected != actual | test setup, mock config, expected values | 1+ assertion mismatch + context shows it's wrong | assertion fails + API spec contradicts expectation, mock config clearly wrong | test-corrector skill |
| **REAL BUG** | Exception, TypeError, NullPointer, ReferenceError, crash | unhandled edge case, logic error, uninitialized resource | 1+ exception type + code path is valid | exception in app code + null/undefined with valid input | bug-fixer skill + tag: real_bug |
| **ENVIRONMENT** | ECONNREFUSED, ENOTFOUND, connection refused, service timeout | DNS resolution, port verification, firewall/auth | 1+ connection error + external service involved | connection refused + verified service down, DNS fails to resolve | environment-recover skill |
| **TRANSIENT** | error present in eval, absent in logs/state by triage time | one-off occurrence, no pattern history | no logging evidence but timing suggests transience | first occurrence, disappears from state before investigation | monitor + re-triage next run |
| **NEEDS_CONTEXT** | ambiguous patterns, missing evidence, unrecognized error | low confidence, conflicting signals, unable to expand evidence | < 50% confidence after evidence expansion, unresolvable ambiguity | multiple categories tied, logs missing, error code not found | human escalation ticket |

**How to Use:**

1. **Find your error in "Primary Signals"** column → identifies likely category
2. **Check "Secondary Evidence"** column → confirm with additional signals
3. **Count confidence signals from "Confidence Triggers"** → is confidence >= 60%?
4. **If HIGH confidence** (>= 85%) → proceed to "High Confidence" action
5. **If LOW confidence** (< 60%) → row indicates "NEEDS_CONTEXT"
6. **Route to skill** listed in "Escalation Route" column

**Examples:**

- Error: "timeout waiting for response" → FLAKY TEST (timeout in Primary Signals)
  - Check: is it async operation? (Secondary Evidence) → yes? → HIGH confidence
  - Route to: flaky-test-fixer skill

- Error: "ECONNREFUSED 127.0.0.1:5432" → ENVIRONMENT (ECONNREFUSED in Primary)
  - Check: is external service involved? (Secondary) → yes, DB → HIGH confidence
  - Route to: environment-recover skill

- Error: "Widget assertion failed with code XYZ_ERR_9847" → NEEDS_CONTEXT (not in Primary)
  - No primary signal match → LOW confidence
  - Try expanding evidence → check code, error handling, recent changes
  - If still can't identify → escalate as NEEDS_CONTEXT

---

## Post-Implementation Checklist

- [ ] Triage decision is one of: fix-code / fix-test / fix-config / escalate — not "investigate more".
- [ ] Fix strategy written to brain with task_id: anchor before any code is changed.
- [ ] If fix-code: specific files and lines to change are named (not "update the handler").
- [ ] If escalate: BLOCKED written to brain with blocker description and next step for human.
- [ ] Self-heal iteration counter checked — triage does not proceed on iteration > 3.

## Cross-References

- **`self-heal-locate-fault`** — **Semantic path triage** depends on its parse of **`semantic-eval-run.log`**.
- **`eval-judge`**, **`qa-semantic-csv-orchestrate`**, [docs/semantic-eval-csv.md](../../docs/semantic-eval-csv.md)

## Checklist

Before routing to a fix strategy:

- [ ] **Source artifact identified** — driver payload vs **`semantic-eval-run.log`** JSON lines
- [ ] Failure message and error type extracted from eval output
- [ ] At least 3 data points collected before classifying as flaky (not single-occurrence)
- [ ] Classification supported by primary evidence pattern (timeout, assertion, exception, connection)
- [ ] Confidence score is MEDIUM (≥60%) or higher — LOW triggers escalation, not fix
- [ ] Evidence and confidence score documented in triage output
- [ ] Fix strategy routed based on classification (not assumed)

**Related Skills in Self-Heal Workflow:**

1. **self-heal-locate-fault** — Diagnose which service failed in eval. Run this BEFORE triage to identify failure scope. Triage works on failures identified by locate-fault.

2. **self-heal-loop-cap** — Max 3 retries per failure. Implements retry cap and sequencing. Triage output feeds into loop-cap to determine if failure is retryable.

3. **self-heal-systematic-debug** — 4-phase debugging workflow (investigate, hypothesize, test, confirm). Use this for deep-dive when triage routes to CODE_BUG with real_bug tag. Systematic-debug handles investigation phase.

---

## Future Enhancements

1. **Machine Learning:** Train classifier on historical failures
2. **Semantic Analysis:** Use NLP for error message understanding
3. **Cross-Correlation:** Link related failures across tests
4. **Trend Analysis:** Detect newly flaky or newly broken tests
5. **Automated Repair:** Suggest specific code fixes, not just actions
6. **Integration with Debugger:** Auto-launch debug session for real bugs

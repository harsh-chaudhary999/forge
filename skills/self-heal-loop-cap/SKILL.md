---
name: self-heal-loop-cap
description: "Max 3 retries per failure. Loop: locate → triage → fix → verify. After 3 tries, escalate (BLOCKED). Prevents infinite loops."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers:
  - "self-heal limit reached"
  - "stop self-heal loop"
  - "3 retries exceeded"
allowed-tools:
  - Bash
---

# Self-Heal Loop Cap Skill

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "One more try and it'll pass" | That's what iteration 4, 5, and 6 say too. The cap exists because unbounded retries waste time and hide fundamental issues. |
| "This is a different fix, so the counter should reset" | The counter tracks attempts per failure, not per fix strategy. Three different wrong fixes still means BLOCKED. |
| "Escalating feels like giving up" | Escalation is the correct engineering response to a problem that resists three systematic attempts. It's not failure — it's efficient triage. |
| "The fix is almost working, just needs a tweak" | "Almost working" after 3 tries means the diagnosis is wrong, not that the fix needs a tweak. Escalate for fresh eyes. |
| "I'll increase the cap just this once" | The cap is a HARD-GATE. Increasing it normalizes infinite loops. If 3 tries can't fix it, the 4th won't either. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
THE SELF-HEAL LOOP CAPS AT 3 ATTEMPTS. EACH ATTEMPT REQUIRES A FULL LOCATE → TRIAGE → FIX → VERIFY CYCLE WITH FRESH EVIDENCE. AFTER 3 FAILURES, ESCALATE — DO NOT RETRY.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Attempt counter is at 3 and you're about to run a 4th fix** — You have hit the hard cap. Running more attempts violates the skill. Escalate immediately with all diagnostic context.
- **You are resetting or ignoring the attempt counter** — Counter manipulation defeats the entire purpose. The count is sacred; treat each attempt as non-renewable.
- **The same fix strategy is being applied again with minor variations** — Repeated similar fixes mean the root cause diagnosis is wrong. Stop, escalate, and document what three attempts revealed.
- **A new failure appeared mid-loop and you are folding it into the current retry** — Each distinct failure gets its own cap. Do not merge failure contexts. Log the new failure separately.
- **You are describing the fix as "almost there"** — "Almost there" after attempt 3 is the exact moment to escalate. Confidence in a near-fix does not override the cap.
- **The verify step was skipped or abbreviated** — Skipped verification means the attempt is incomplete and the result is invalid. Each attempt requires a full locate → triage → fix → verify cycle.
- **No evidence was captured between attempts** — Attempts without documented evidence cannot inform escalation. Stop and reconstruct what each attempt found before continuing.

Enforces a maximum of 3 retry attempts per failure scenario. Implements a structured locate → triage → fix → verify loop with automatic escalation to user when auto-healing fails.

## HARD-GATE Anti-Patterns (Violation Criteria)

### Anti-Pattern 1: "3 attempts is conservative — just try more"

**Why It Fails:**
The 3-attempt cap prevents infinite loops that consume tokens, delay pipeline delivery, and mask fundamental architectural issues. Unbounded retries create false confidence in fix validity. After 3 systematic attempts using evidence from each cycle, attempting more is debugging theater, not engineering.

**Enforcement (MUST):**
1. MUST honor the hard cap: 3 retry attempts maximum
2. MUST track attempt counter accurately; no skipping or resetting
3. MUST escalate immediately when attempt_count reaches 3 and verification fails
4. MUST document why you believe a 4th attempt would differ (if tempted)
5. MUST rely on escalation for fresh human perspective, not retry loop hunger

---

### Anti-Pattern 2: "If the fix looks right, skip verify and move on"

**Why It Fails:**
Self-heal fixes are only valid after re-running the exact evaluation scenario that initially failed. A theoretically correct fix is not proven correct until the original failure reproduces and passes. Skipping verify means you cannot distinguish lucky silence from actual healing.

**Enforcement (MUST):**
1. MUST always re-run the evaluation after applying any fix
2. MUST verify using the identical scenario/inputs that triggered the original failure
3. MUST capture the full verify result (pass/fail, output, logs, timing)
4. MUST fail the attempt if verify was skipped or abbreviated
5. MUST treat incomplete verify cycles as attempt waste; they do not count toward completion

---

### Anti-Pattern 3: "BLOCKED means we failed — try one more time"

**Why It Fails:**
BLOCKED is an explicit escalation signal indicating that the current attempt vector is unsafe or impossible. Overriding BLOCKED to squeeze in another retry violates the escalation protocol and often repeats the same failure under different framing.

**Enforcement (MUST):**
1. MUST respect BLOCKED status from any phase (locate, triage, fix, verify)
2. MUST NOT retry after BLOCKED; immediately escalate
3. MUST include the BLOCKED reason and phase in escalation report
4. MUST treat BLOCKED as terminal within the current loop iteration
5. MUST document why BLOCKED was triggered before escalating

---

### Anti-Pattern 4: "Evidence from attempt 1 is still valid for attempt 3"

**Why It Fails:**
System state changes between attempts. Services restart, caches clear, environment variables shift, deployment progresses. Evidence stale by 2 attempts may point to a fault that no longer exists or mask a new fault. Reusing old evidence causes retriage of ghosts and fixes for problems that changed shape.

**Enforcement (MUST):**
1. MUST collect fresh evidence on each attempt (logs, state, error messages)
2. MUST re-triage failure on each attempt using current evidence
3. MUST recheck system state before applying each fix
4. MUST document state changes observed between attempts
5. MUST discard previous attempt evidence from active decision making; use only for escalation trail

---

### Anti-Pattern 5: "Loop cap only applies to code bugs, not infra faults"

**Why It Fails:**
The 3-attempt cap applies uniformly to all fault categories: code bugs, configuration errors, infrastructure faults, flaky tests, integration failures. Infra faults have the same limit because persistent infra problems require ops escalation, not retry loops. No category gets a free pass.

**Enforcement (MUST):**
1. MUST apply 3-attempt cap to code faults, config errors, infra failures equally
2. MUST NOT increment loop counter differently by fault type
3. MUST escalate infra faults to operations after 3 attempts (no exception)
4. MUST document fault category in escalation for proper routing
5. MUST treat "it's an infra problem so we can retry more" as anti-pattern violation

---

## Overview

This skill prevents infinite retry loops by capping attempts at 3 retries. When an evaluation fails, the skill enters a controlled retry cycle, tracking all attempts and evidence. After 3 failed retry cycles, it escalates the issue to the user with full context and diagnostic data.

## Loop Flow

```
Initial Failure
       ↓
   Retry 1: locate-fault → triage → fix → verify
       ↓
   Pass? → YES → DONE ✅
       ↓
      NO
       ↓
   Retry 2: locate-fault → triage → fix → verify
       ↓
   Pass? → YES → DONE ✅
       ↓
      NO
       ↓
   Retry 3: locate-fault → triage → fix → verify
       ↓
   Pass? → YES → DONE ✅
       ↓
      NO
       ↓
   BLOCKED → Escalate to User
```

## State Tracking

The loop maintains state throughout all retries:

```yaml
LoopState:
  attempt_count: 0-3          # Current retry attempt (0 = initial, 1-3 = retries)
  max_attempts: 3             # Hard cap on retry attempts
  previous_fixes: []          # List of fixes already tried (avoid repetition)
  failure_logs: []            # All failure evidence from each attempt
  current_eval_scenario: {}   # The failing evaluation scenario
  blocked: false              # Set to true if all retries exhausted
```

## Detailed Loop Cycle

### Locate Fault
- Parse error messages from the failed evaluation
- Identify root cause category:
  - Code logic error
  - Configuration issue
  - Environment/dependency problem
  - Test assertion mismatch
  - Integration point failure

### Triage
- Categorize severity and scope
- Determine if issue is auto-fixable
- Check against `previous_fixes` to avoid repeated attempts
- Estimate confidence in fix approach

### Fix
- Apply targeted fix based on triage
- Document the fix applied
- Add fix to `previous_fixes` list
- Make minimal, isolated changes

### Verify
- Re-run the evaluation scenario
- Check if original failure is resolved
- Capture pass/fail result with full logs
- If fail, collect evidence for next retry

## Escalation Protocol

When `attempt_count >= max_attempts` and verification still fails, escalate to user with:

### Escalation Report

**What Failed:**
- Evaluation scenario ID/name
- Brief description of what was being tested
- Initial failure message

**What We Tried:**
- Attempt 1: [fix description] → [result]
- Attempt 2: [fix description] → [result]
- Attempt 3: [fix description] → [result]

**Why It's Blocked:**
- All 3 auto-fix attempts exhausted
- Unable to determine next safe fix
- Risk of infinite loop reached
- Human judgment needed

**Evidence:**
- Full error log from each attempt
- Code changes applied per attempt
- Timeline of all 3 retries
- Environment/context information

## Edge Cases

### Edge Case 1: Fix Applied, Verify Still Fails (Same Error)

**Symptom:**
Attempt N: Fix applied successfully, eval re-run executed, but fails with identical error as before the fix.

**Root Cause Hypothesis:**
- Fix addressed a symptom, not the root cause
- Hidden dependency not detected during triage
- Fix incomplete or applied to wrong scope
- Error message masks a deeper issue

**Do NOT:**
- Apply the same fix again with minor variation
- Assume the fix partially worked
- Increase attempt counter and continue

**Action:**
1. Log the repeated error with timestamp and attempt number
2. Run deeper triage: search for dependencies, side effects, transitive failures
3. Cross-reference with previous failure logs to identify patterns
4. Consider if fix was applied to correct layer (e.g., frontend vs backend vs infra)
5. Document the evidence gap that caused misdiagnosis

**Escalation Keyword:**
- If N < 3: Continue to next attempt with revised triage
- If N = 3: Escalate as BLOCKED with full three-attempt evidence trail

---

### Edge Case 2: Fix Applied, Verify Fails (Different Error)

**Symptom:**
Attempt N: Fix applied, eval re-run executes, original error is gone but a new error appeared.

**Root Cause Hypothesis:**
- Fix was correct but exposed a downstream failure
- Fix broke a different code path
- Environment state changed mid-attempt
- Dependency cascade triggered by the fix

**Do NOT:**
- Count this as progress toward cap or completion
- Merge new error into current retry attempt
- Treat new error as ripple damage

**Action:**
1. Document new error separately with clear cause-link to the fix
2. Treat new error as independent fault entry (new loop if needed)
3. Determine if new error is acceptable (e.g., better error message, informational)
4. If new error blocks eval, escalate current failure first
5. Open ticket for new error as separate remediation

**Escalation Keyword:**
- NEEDS_CONTEXT (new failure introduced by fix requires human decision)

---

### Edge Case 3: Triage and Locate Give Conflicting Outputs

**Symptom:**
Locate phase identifies fault as CODE_BUG in service A, but Triage phase categorizes it as CONFIG_ERROR in service B.

**Root Cause Hypothesis:**
- Error message origin and actual root cause differ
- Multi-service failure with conflicting evidence
- Triage heuristics misclassified the fault
- Both are partially correct (code calls bad config)

**Do NOT:**
- Pick one arbitrarily and proceed
- Blame the tool that produced first evidence
- Ignore the conflict

**Action:**
1. Stop and re-examine evidence from locate and triage independently
2. Cross-validate: which phase has more direct evidence (error logs, stack traces)?
3. If code-vs-config split: check if code is correct but config is wrong
4. Run test with good config to verify code path works
5. Document conflict and resolution method in attempt log

**Escalation Keyword:**
- NEEDS_CONTEXT (conflicting diagnostics require clarification before fix)

---

### Edge Case 4: Stack State Changes Between Attempts

**Symptom:**
Attempt 1: Locate identifies fault in Service A (unhealthy logs, high latency). Attempt 2 runs: Service A now healthy, but Service B is failing with the same error.

**Root Cause Hypothesis:**
- Environment is flaky or rolling updates in progress
- Fault is environment-dependent, not code-dependent
- Previous fix accidentally masked a broader instability
- Multiple independent faults cascading

**Do NOT:**
- Discard Attempt 1 evidence as invalid
- Assume Attempt 1 was a false positive
- Chase the moving target without documenting instability

**Action:**
1. Document state change with timestamps: Service A timeline, Service B timeline
2. Check deployment/scaling logs: did something roll out between attempts?
3. Flag as environment instability in escalation report
4. Treat as escalation signal: code retries are ineffective against unstable infra
5. Include state drift evidence in escalation for ops review

**Escalation Keyword:**
- NEEDS_COORDINATION (environment instability requires ops or infra team)

---

### Edge Case 5: All 3 Attempts BLOCKED

**Symptom:**
Attempt 1 enters BLOCKED state in Triage phase. Attempt 2 enters BLOCKED in Fix phase. Attempt 3 enters BLOCKED in Locate phase. Loop exhausted with no fix ever attempted.

**Root Cause Hypothesis:**
- Fundamental incompatibility in auto-heal approach
- Eval scenario is malformed or unsupported
- Recurring blocker across multiple strategies
- Human decision needed on strategy or scenario validity

**Do NOT:**
- Silently exit or return generic BLOCKED status
- Pretend a fix was attempted
- Omit the phase/reason for each BLOCKED state

**Action:**
1. Emit BLOCKED with full three-attempt summary including:
   - Attempt 1: Triage phase, BLOCKED reason, evidence
   - Attempt 2: Fix phase, BLOCKED reason, evidence
   - Attempt 3: Locate phase, BLOCKED reason, evidence
2. Identify common pattern across three BLOCKED states
3. Flag as escalation requiring human review of scenario validity or tool capability
4. Recommend: review eval scenario format, constraints, or consider manual path

**Escalation Keyword:**
- BLOCKED (requires human decision on scenario viability)

---

## Decision Tree: Loop Continuation Logic

After each verify phase, given RESULT, determine what to do:

```
┌─ START (attempt_count = 0)
│
├─ Run Evaluation
│  └─ RESULT?
│     ├─ PASS → DONE ✅ (no retry needed)
│     └─ FAIL → Enter Retry Loop
│
└─ RETRY LOOP (attempt_count < 3)
   │
   ├─ Increment attempt_count (1, 2, or 3)
   │
   ├─ LOCATE FAULT
   │  └─ Status?
   │     ├─ BLOCKED → Escalate, exit ⛔
   │     ├─ NO_FIX_AVAILABLE → Escalate, exit ⛔
   │     └─ LOCATED → Continue to Triage
   │
   ├─ TRIAGE
   │  └─ Status?
   │     ├─ BLOCKED → Escalate, exit ⛔
   │     ├─ NOT_AUTO_FIXABLE → Escalate, exit ⛔
   │     ├─ FIX_ALREADY_TRIED → Escalate, exit ⛔
   │     └─ AUTO_FIXABLE → Continue to Fix
   │
   ├─ FIX
   │  └─ Status?
   │     ├─ BLOCKED → Escalate, exit ⛔
   │     ├─ APPLY_FAILED → Escalate, exit ⛔
   │     └─ APPLIED → Continue to Verify
   │
   ├─ VERIFY (Re-run Eval)
   │  └─ RESULT?
   │     ├─ PASS → DONE ✅ (fix successful, exit)
   │     ├─ BLOCKED → Escalate, exit ⛔
   │     ├─ SAME_ERROR → 
   │     │  └─ attempt_count < 3?
   │     │     ├─ YES → Loop back to LOCATE (deepen triage)
   │     │     └─ NO → Escalate (attempt_count = 3), exit ⛔
   │     ├─ NEW_ERROR →
   │     │  └─ Escalate as NEEDS_CONTEXT, exit (new fault)
   │     └─ DIFFERENT_FAILURE →
   │        └─ attempt_count < 3?
   │           ├─ YES → Loop back to LOCATE (new fault entry)
   │           └─ NO → Escalate, exit ⛔
   │
   └─ EXIT CONDITIONS:
      ├─ ✅ DONE: Eval passes
      ├─ ⛔ BLOCKED: No more retries or escalation triggered
      ├─ ⛔ NEEDS_CONTEXT: Human decision needed
      ├─ ⛔ NEEDS_COORDINATION: Ops/team involvement required
      └─ ⛔ (attempt_count = 3, no pass): Loop exhausted
```

---

## Quick Reference Card

| Attempt # | Phase | Expected Output | Safe to Continue? | Escalation If Stuck |
|---|---|---|---|---|
| 1 | Locate | Fault identified, root cause clear | YES if located | BLOCKED, escalate |
| 1 | Triage | Auto-fixable? High confidence? | YES if fixable | NOT_AUTO_FIXABLE, escalate |
| 1 | Fix | Changes applied, previous_fixes logged | YES if applied | APPLY_FAILED, escalate |
| 1 | Verify | Re-run eval, check original error | YES if PASS, retry if FAIL | BLOCKED, escalate |
| 2 | Locate | New triage angle, fresh evidence | YES if located and different | BLOCKED, escalate |
| 2 | Triage | Different fix strategy than Attempt 1 | YES if not already tried | FIX_ALREADY_TRIED, escalate |
| 2 | Fix | Apply revised fix, check scope | YES if applied | APPLY_FAILED, escalate |
| 2 | Verify | Re-run eval with same scenario | YES if PASS, retry if FAIL | BLOCKED, escalate |
| 3 | Locate | Last chance; deepest triage | YES if located | BLOCKED, escalate |
| 3 | Triage | Highest confidence fix remaining | YES if fixable | NOT_AUTO_FIXABLE, escalate |
| 3 | Fix | Final attempt; validate application | YES if applied | APPLY_FAILED, escalate |
| 3 | Verify | Re-run eval; capture full evidence | **FINAL** if FAIL: BLOCKED | BLOCKED (mandatory escalate) |

---

## Implementation Pseudocode

```
function runSelfHealLoop(evalScenario):
    loopState = {
        attempt_count: 0,
        max_attempts: 3,
        previous_fixes: [],
        failure_logs: [],
        current_eval_scenario: evalScenario,
        blocked: false
    }
    
    result = runEvaluation(evalScenario)
    
    while result.status == FAILED and loopState.attempt_count < loopState.max_attempts:
        loopState.attempt_count += 1
        
        # Locate
        fault = locateFault(result.error)
        loopState.failure_logs.append({
            attempt: loopState.attempt_count,
            error: result.error,
            fault: fault
        })
        
        # Triage
        triage = triageFault(fault)
        if triage.autoFixable == false:
            loopState.blocked = true
            break
        
        if isFix AlreadyTried(triage.fix, loopState.previous_fixes):
            # Skip repeated fix, mark as blocked
            loopState.blocked = true
            break
        
        # Fix
        applyFix(triage.fix)
        loopState.previous_fixes.append(triage.fix)
        
        # Verify
        result = runEvaluation(evalScenario)
        
        if result.status == PASSED:
            return {
                status: SUCCESS,
                retries_needed: loopState.attempt_count,
                evidence: loopState.failure_logs
            }
    
    # All retries exhausted
    if loopState.attempt_count >= loopState.max_attempts or loopState.blocked:
        return escalateToUser({
            status: BLOCKED,
            eval_scenario: evalScenario,
            attempts_tried: loopState.attempt_count,
            fixes_attempted: loopState.previous_fixes,
            all_failure_logs: loopState.failure_logs,
            reason: "Auto-fix exhausted or blocked"
        })
    
    return {
        status: BLOCKED,
        reason: "Unknown"
    }
```

## Output States

### SUCCESS
```yaml
status: SUCCESS
retries_needed: N                    # 1-3 (or 0 if passed on first try)
final_fix: <fix description>
evidence:
  - attempt: 1
    error: <error message>
  - attempt: 2
    error: <error message>
  # ... etc if needed
```

### BLOCKED
```yaml
status: BLOCKED
eval_scenario: <scenario details>
attempts_tried: 3
fixes_attempted:
  - fix 1 description
  - fix 2 description
  - fix 3 description
all_failure_logs:
  - attempt: 1
    error: <full error>
    timestamp: <ISO timestamp>
  - attempt: 2
    error: <full error>
    timestamp: <ISO timestamp>
  - attempt: 3
    error: <full error>
    timestamp: <ISO timestamp>
reason: "Could not auto-fix after 3 attempts"
escalation_required: true
needs_human_review: true
```

## Safety Guarantees

1. **Hard Cap:** Loop never exceeds 3 retry attempts
2. **No Repetition:** `previous_fixes` prevents trying the same fix twice
3. **Evidence Trail:** Every attempt logged with full error context
4. **User Escalation:** All blocked cases reported to user with actionable data
5. **Timeout Safety:** Each retry cycle has implicit timeout from outer eval driver

## Integration Points

- **Trigger:** Invoked when any evaluation fails
- **Dependency:** Requires `brain-read` to access eval scenario metadata
- **Output:** Reports to user via standard escalation channel
- **State:** Local to current evaluation context (not persisted across sessions)

## Example Usage

### Scenario: API Endpoint Returns Wrong Status Code

```yaml
Initial Eval Fails:
  error: "Expected 200, got 500"

Retry 1: Locate → triage → fix
  located: "Server error in authentication handler"
  fix: "Added missing error handling in auth middleware"
  verify: Still failing → "Expected 200, got 500"

Retry 2: Locate → triage → fix
  located: "Database connection timeout"
  fix: "Increased connection pool size"
  verify: Still failing → "Expected 200, got 500"

Retry 3: Locate → triage → fix
  located: "Wrong environment variable in deployment"
  fix: "Updated ENV var to correct database host"
  verify: Still failing → "Expected 200, got 500"

All Retries Exhausted:
  status: BLOCKED
  escalate: true
  message: "API endpoint still returning 500 after 3 fix attempts.
           Likely requires manual debugging or infrastructure changes."
```

## Checklist

Before declaring BLOCKED and escalating:

- [ ] Attempt counter verified — exactly 3 full locate → triage → fix → verify cycles completed
- [ ] Fresh evidence collected on each attempt (not reusing stale logs from attempt 1)
- [ ] Same fix strategy not repeated — each attempt used a distinct diagnosis angle
- [ ] Each verify step ran the full original failing eval scenario (not abbreviated)
- [ ] All three attempts documented with fix description and result
- [ ] Escalation report includes: failing scenario, all fixes tried, failure evidence per attempt

## Cross-References

This skill depends on and coordinates with:

1. **self-heal-locate-fault**
   - **How:** Located faults feed into triage phase of each loop attempt
   - **Why:** Accurate fault location is prerequisite for targeted fix
   - **Sync Point:** Output of locate-fault is input to triage phase

2. **self-heal-triage**
   - **How:** Triage classifies fault type (CODE_BUG, CONFIG_ERROR, etc.) and determines auto-fixability
   - **Why:** Triage output determines if auto-fix can proceed or escalate
   - **Sync Point:** Triage confidence score influences retry decision

3. **self-heal-systematic-debug**
   - **How:** Invoked when loop reaches BLOCKED to provide deeper 4-phase investigation
   - **Why:** Loop cap escalation may benefit from systematic debugging approach
   - **Sync Point:** BLOCKED with insufficient evidence routes to systematic-debug

4. **forge-eval-gate**
   - **How:** Eval gate receives BLOCKED/DONE result from loop-cap; gates merge based on final status
   - **Why:** Loop cap status determines if eval passes for merge gate
   - **Sync Point:** Loop completion status reported to eval-gate

---

## Version History

- **v1.0:** Initial implementation with 3-retry cap, locate-triage-fix-verify loop, escalation protocol

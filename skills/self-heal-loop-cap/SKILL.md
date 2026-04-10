---
name: self-heal-loop-cap
description: Max 3 retries per failure. Loop: locate → triage → fix → verify. After 3 tries, escalate (BLOCKED). Prevents infinite loops.
type: rigid
requires: [brain-read]
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

## Version History

- **v1.0:** Initial implementation with 3-retry cap, locate-triage-fix-verify loop, escalation protocol

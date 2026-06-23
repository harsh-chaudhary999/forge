# Self-Heal Loop Cap — Pseudocode & Worked Example

Reference implementation pseudocode for the bounded loop and a full worked failure scenario
showing all three attempts exhausting into BLOCKED. Load when implementing the loop driver or
when you need a concrete end-to-end example of the cap in action.

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

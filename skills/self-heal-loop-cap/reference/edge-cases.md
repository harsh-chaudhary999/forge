# Self-Heal Loop Cap — Edge Cases

Extended edge-case catalog for the 3-attempt self-heal loop. Each case lists symptom,
root-cause hypotheses, do-NOT actions, the required action sequence, and the escalation
keyword that terminates or advances the loop. Load when an attempt produces an ambiguous
or non-standard verify result.

## Edge Case 1: Fix Applied, Verify Still Fails (Same Error)

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

## Edge Case 2: Fix Applied, Verify Fails (Different Error)

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

## Edge Case 3: Triage and Locate Give Conflicting Outputs

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

## Edge Case 4: Stack State Changes Between Attempts

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

## Edge Case 5: All 3 Attempts BLOCKED

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

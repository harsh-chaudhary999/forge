# Edge Cases & Fallback Paths

## Edge Case 1: Logs are missing or truncated (investigation blocked)

**Diagnosis**: Failure occurred, but logs have been rotated away or were never captured for this scenario.

**Response**:
- **Fallback investigation methods**:
  1. **Recreate the failure**: Run eval scenario again, capture logs this time.
  2. **Use system metrics**: If logs missing, check system metrics (CPU, memory, disk) for clues.
  3. **Binary search**: Run scenario with half the data/requests, narrowing down failure point.
  4. **Ask dev-implementer**: "What changed in this code? What was the last working state?" Reasoning from code changes.
- **Log retention policy**: Document for future: all eval runs must capture logs for [X hours].

**Escalation**: NEEDS_CONTEXT - If cannot recreate failure and logs are gone, cannot diagnose. Escalate to user: "Unable to diagnose without logs. Please retain eval logs or re-run scenario."

---

## Edge Case 2: Root cause is in infrastructure (not in code)

**Diagnosis**: After investigation, root cause is "database was OOM" or "network timeout between services" or "kernel killed process due to memory pressure".

**Response**:
- **Not a code fix**: Issue is infra-level, not code-level.
- **Escalate to infra team**: "Issue is infrastructure-level. [Detail: database configuration, network config, resource limits]."
- **Possible fixes**:
  1. **Increase resources**: More RAM, more CPU, more disk for database.
  2. **Optimize infra config**: Tune database connection pooling, increase timeouts, adjust buffer sizes.
  3. **Code optimization**: Could code be optimized to use less memory? But this is secondary.
- **Fallback**: If infra team cannot resolve quickly, escalate to user: "Infrastructure bottleneck blocking eval. Requires [specific resource change]."

**Escalation**: NEEDS_INFRA_CHANGE - Cannot be fixed in code. Requires infrastructure change.

---

## Edge Case 3: Fix affects other services (unintended side effect)

**Diagnosis**: Self-heal proposes fix: "Add index to users table to speed up query". Fix works for eval, but breaks another service that wasn't part of this task.

**Response**:
- **Detect side effects**: Before applying fix, ask: "Are there other services that touch this code/database/table?"
- **Scope analysis**: If fix affects shared infrastructure, must coordinate with other services.
- **Options**:
  1. **Narrow fix**: Can we fix just this service without touching shared code? (Wrapper, override, conditional logic)
  2. **Coordinate fix**: Fix is good, but requires careful rollout coordination with other services.
  3. **Alternative fix**: Is there a different fix that doesn't have side effects?
- **Document**: Record that fix requires coordination or has side effects.

**Escalation**: NEEDS_COORDINATION - If fix affects other services, escalate to conductor to coordinate rollout or escalate to user for manual decision.

---

## Edge Case 4: Multiple possible fixes; unclear which is correct

**Diagnosis**: Investigation narrows failure to: "User ID mismatch in cache". Three possible fixes: 1) Change cache key format, 2) Change how user ID is extracted, 3) Add validation before caching.

**Response**:
- **Prioritize fixes by risk/scope**:
  1. **Safest**: Add validation (new code, doesn't change existing behavior)
  2. **Medium**: Change extraction logic (affects this service, limited blast radius)
  3. **Riskiest**: Change cache key format (affects all services using cache, wide blast radius)
- **Start with safest**: Apply fix #1 (validation). If that solves it, done.
- **If #1 doesn't work**: Move to #2. Then #3 only if necessary.
- **Document decision**: Why you chose this fix over others.

**Escalation**: If multiple plausible fixes and unclear which is correct, escalate to NEEDS_ANALYSIS - May need deeper investigation or expert judgment.

---

## Edge Case 5: Fix works in isolation but fails in full stack

**Diagnosis**: Dev-implementer applies fix. Tests pass in isolation. But when full eval stack runs, failure still happens (different failure mode or same failure).

**Response**:
- **Investigate full-stack context**: Fix works in unit tests but fails in integration. Something about full stack interaction breaks assumption.
- **Root cause**: Likely due to timing, ordering, or resource contention that doesn't happen in isolation.
- **Recovery**:
  1. **Add synchronization**: If timing issue, add waits/locks between services.
  2. **Increase resources**: If resource contention, may need more memory/CPU in full stack.
  3. **Adjust test timing**: Unit test may not be testing the right scenario.
- **Re-verify**: Apply fix, re-run full eval, verify it passes in full stack context.

**Escalation**: If fix works in isolation but fails in full stack, escalate: "Fix needs full-stack testing. Cannot verify in isolation."

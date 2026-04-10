---
name: self-heal-systematic-debug
description: 4-phase debugging workflow: investigate (logs, traces) → hypothesize (root cause) → fix (minimal) → verify (re-eval). Output: fixed code, commit.
type: rigid
requires: [brain-read]
---

# Self-Heal Systematic Debug

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I can see the bug, I'll just fix it" | What you see is a symptom. The systematic 4-phase workflow exists because root causes hide behind obvious symptoms. |
| "I'll fix multiple things while I'm in here" | Multiple fixes in one pass make it impossible to verify which fix resolved the issue. Fix ONE thing, verify, then proceed. |
| "Let me refactor this messy code while debugging" | Refactoring during debugging introduces new variables. If the test still fails after your refactor, you can't tell if the refactor broke it or the original bug persists. |
| "The hypothesis is obvious, skip to fix" | Obvious hypotheses are wrong >50% of the time. Write it down, collect evidence, then fix. Skipping investigation is guessing. |
| "I'll verify later after fixing a few things" | Verification after each fix is the only way to know which fix worked. Batched fixes + late verification = correlation, not causation. |

**If you are thinking any of the above, you are about to violate this skill.**

## Overview

Systematic debugging framework that applies the scientific method to code failures. When a test fails, an API returns 500, or eval breaks, use this skill to isolate the root cause, apply a minimal fix, and verify resolution.

**Philosophy:** Fix ONE thing at a time. No refactoring. No speculative changes. Let the evidence guide the fix.

---

## 4-Phase Workflow

### Investigate
**Goal:** Find the exact failure point and capture evidence.

**Actions:**
- Read error logs and stack traces
- Identify the service/function that failed
- Trace the request path from entry to failure
- Capture the exact error message and line number
- Note what was the last successful operation before failure
- Document environment state (config, versions, data state)

**Output:** Clear failure signature
- *What failed?* (function, endpoint, test)
- *Where did it fail?* (file, line number)
- *How did it fail?* (error message, exception type)

**Example:**
```
Test: POST /auth/2fa/enable
Failed at: /app/src/routes/auth.ts:145
Error: "ReferenceError: generateSecret is not defined"
Stack: at enableTwoFactor (/app/src/routes/auth.ts:145)
```

---

### Hypothesize
**Goal:** Determine root cause from evidence, not intuition.

**Actions:**
- Analyze the failure signature
- Ask: What changed recently that could cause this?
- Check: Is the required dependency imported?
- Check: Is the required service running?
- Check: Is configuration correct?
- Check: Is the data in the expected state?
- Form a single, testable hypothesis

**Output:** Root cause statement
- *"The X is missing/broken/misconfigured because..."*
- Confidence: High/Medium/Low
- Test strategy: How to verify this hypothesis

**Example:**
```
Hypothesis: generateSecret function is not imported in auth.ts
Evidence: ReferenceError says "generateSecret is not defined"
Location: /app/src/lib/crypto exports generateSecret but auth.ts doesn't import it
Confidence: HIGH
Test: Add import, re-run test
```

---

### Fix
**Goal:** Apply ONE minimal change. No refactoring, no optimization.

**Actions:**
1. Locate the exact lines to change
2. Apply ONLY what's needed to test the hypothesis
3. Make one atomic change
4. Do NOT:
   - Refactor surrounding code
   - Optimize performance
   - "While you're at it" improvements
   - Clean up unrelated issues

**Output:** Minimal code change

**Example:**
```typescript
// BEFORE
import { hash, verify } from './lib/crypto';
// ← generateSecret is missing

// AFTER
import { hash, verify, generateSecret } from './lib/crypto';
// ← Added generateSecret import only

// Do NOT do:
import { hash, verify, generateSecret } from './lib/crypto';
// + cleanup exports
// + reorganize imports alphabetically
// + refactor function signatures
```

---

### Verify
**Goal:** Confirm the fix works and no new failures appear.

**Actions:**
1. Re-run the exact same test/eval that failed
2. Confirm success
3. Run related tests to catch regressions
4. Check logs for new errors
5. If fix worked → Commit
6. If fix didn't work → Return to Phase 1 with new evidence

**Output:** Green test + clean logs

**Example:**
```bash
# Test the fix
npm test -- auth.test.ts

# Expected output
✓ POST /auth/2fa/enable returns 201
✓ 2FA secret is generated correctly
✓ QR code is valid

# Commit if all green
git add src/routes/auth.ts
git commit -m "fix: import generateSecret in auth.ts"
```

---

## When to Use This Skill

- ❌ A test is failing
- ❌ An API endpoint returns 500
- ❌ Eval scenario breaks
- ❌ Feature doesn't work as specified
- ❌ Mysterious error in logs
- ❌ Service won't start

---

## When NOT to Use This Skill

- ✓ Feature is working, making improvements (use refactoring skill)
- ✓ Writing new code from scratch (use TDD skill)
- ✓ Performance optimization without a failure (use profiling skill)

---

## Minimal Fix Philosophy

### The Problem with Large Changes
```typescript
// ❌ WRONG: "Fix" is actually a refactor
function enableTwoFactor(req) {
  // Renamed parameter for clarity
  const userRequest = req;
  
  // Added validation
  if (!userRequest.userId) throw new Error('User ID required');
  
  // Reorganized error handling
  try {
    const secret = generateSecret(); // ← the actual fix buried
    return success(secret);
  } catch (err) {
    handleError(err);
  }
}

// ✓ RIGHT: One minimal change
import { generateSecret } from './lib/crypto'; // ← Only this line was added
```

### Why Minimal Fixes Matter
1. **Easier to verify:** One change = one verification
2. **Easier to revert:** If it breaks, reverting doesn't lose other work
3. **Easier to understand:** Reviewers see exactly what fixed the issue
4. **Fewer regressions:** Less code changed = fewer new bugs

---

## Common Debugging Patterns

### Pattern 1: Missing Import/Export
```
Symptom: ReferenceError: X is not defined
Investigation: X exists in another file but not imported
Fix: Add import statement
```

### Pattern 2: Wrong Function Call
```
Symptom: TypeError: X.method is not a function
Investigation: X is wrong object or doesn't have method
Fix: Change X to correct object or method name
```

### Pattern 3: Missing Environment Variable
```
Symptom: TypeError: Cannot read property 'X' of undefined
Investigation: Config.X is undefined because env var not set
Fix: Add env var to .env or set in deployment
```

### Pattern 4: Broken Dependency
```
Symptom: Error during require/import
Investigation: Dependency version changed or module not installed
Fix: npm install or lock to correct version
```

### Pattern 5: Wrong Data Format
```
Symptom: Error in validation or processing
Investigation: Input data doesn't match expected schema
Fix: Transform data before processing or fix source
```

### Pattern 6: Service Not Running
```
Symptom: ECONNREFUSED on port X
Investigation: Database/cache/queue service not started
Fix: Start service or fix connection string
```

---

## Workflow: Step-by-Step

### When You Encounter a Failure

**Step 1: Pause**
- Don't immediately start coding
- Don't guess at the fix
- Don't refactor

**Step 2: Investigate**
```bash
# Read the error carefully
# Look at full stack trace
# Check logs around failure time
# Trace the request/operation path
```

**Step 3: Form hypothesis**
- What one thing could cause this exact error?
- Why would that cause this error?
- Is it the only explanation?

**Step 4: Design minimal test**
- What single change would test this hypothesis?
- What's the smallest code change?

**Step 5: Apply fix**
- Make ONLY the change you identified
- Commit separately (don't mix with other changes)

**Step 6: Verify**
- Run the failing test/scenario
- Check it passes
- Run related tests
- Check logs are clean

**Step 7: Done**
- Commit the minimal fix
- Move to next issue

---

## Example: Full 4-Phase Debug Session

### Failure Report
```
Test: Integration test for user registration
Failed: POST /api/users/register
Status: 500 Internal Server Error
Time: 2025-02-15 14:23:45Z
```

### Investigate
```bash
# Read error logs
tail -100 /var/log/app.log | grep "2025-02-15 14:23"

# Output:
# 2025-02-15T14:23:45Z ERROR POST /api/users/register failed
# Error: ENOMEM: Out of memory, Cannot allocate memory
# at processUserData (/app/src/services/user-service.ts:87)

# Check memory state at time
free -h # Shows memory was exhausted
```

**Finding:** User service tried to allocate memory and failed at line 87.

### Hypothesize
```bash
# Look at line 87
sed -n '80,95p' /app/src/services/user-service.ts

# Output shows:
# const userData = Array(10_000_000).fill(defaultUser);
# ↑ Allocating 10 million objects

# Check git history for recent changes
git log -p src/services/user-service.ts | head -50

# Shows: Recently added memory optimization that created giant array
```

**Hypothesis:** Memory optimization created array that's too large. Array fills entire heap on test system.

**Root cause:** Default test config has limited heap size (256MB), but user service tries to allocate 10M objects.

### Fix
```typescript
// Option A: Refactor entire data structure ❌ (too big)
// Option B: Use pagination ❌ (too big)
// Option C: Reduce test data size ✓ (minimal)

// BEFORE
const userData = Array(10_000_000).fill(defaultUser);

// AFTER
const userData = Array(1000).fill(defaultUser); // ← Changed one number
```

### Verify
```bash
# Run the failing test
npm test -- register.test.ts

# Output:
✓ POST /api/users/register returns 201
✓ User created with correct email
✓ Welcome email sent
✓ 3 tests passed

# Run related tests
npm test -- auth.test.ts
npm test -- user-service.test.ts

# All green ✅

# Commit the fix
git add src/services/user-service.ts
git commit -m "fix: reduce test data size to fit 256MB heap"
```

---

## Troubleshooting: Fix Didn't Work

If after Phase 4 the test still fails:

1. **Don't give up** - return to Phase 1
2. **Gather new evidence** - what changed?
3. **Different hypothesis** - was my first guess wrong?
4. **Smaller fix** - was my fix too big?

```typescript
// If you changed 3 things but test still fails
// Revert and change 1 thing at a time

git revert HEAD
// Change only X
npm test
// Change only Y
npm test
// Change only Z
npm test
```

---

## Commands

### Investigate
```bash
# Read recent errors
tail -100 app.log | grep ERROR

# Get full stack trace
app.log | jq '.[] | select(.level=="error")' | jq '.stack' | head -50

# Find where function is defined
grep -r "function generateSecret" src/

# Check imports in failing file
grep "^import\|^require" src/routes/auth.ts
```

### Hypothesize
```bash
# Check git blame for recent changes
git blame src/routes/auth.ts | grep -A5 -B5 "line 145"

# See what was there before
git show HEAD~1:src/routes/auth.ts | sed -n '140,150p'

# Check if function exists elsewhere
grep -r "export.*generateSecret" src/
```

### Fix
```bash
# Make minimal change
# Verify syntax
npm run lint src/routes/auth.ts

# Don't commit yet
```

### Verify
```bash
# Run specific test
npm test -- auth.test.ts -t "POST /auth/2fa/enable"

# Run full test suite
npm test

# Check logs after running
tail -50 app.log
```

---

## Success Criteria

- ✅ Found exact failure point (file, line, error)
- ✅ Identified root cause with evidence
- ✅ Applied ONE minimal code change
- ✅ Original test/eval now passes
- ✅ No new test failures introduced
- ✅ Minimal fix is committed with clear message

---

## Related Skills

- **brain-read:** Look up past debugging decisions and patterns
- **eval-driver-api-http:** Re-run API eval scenarios
- **forge-verification:** Broader verification framework
- **forge-tdd:** Prevent bugs with tests

---

## Quick Reference Card

| Phase | Goal | Key Question |
|-------|------|---|
| **Investigate** | Find failure point | What broke and where? |
| **Hypothesize** | Root cause | Why did it break? |
| **Fix** | Minimal change | What ONE thing fixes it? |
| **Verify** | Confirm working | Does it work now? |

---

## Edge Cases & Fallback Paths

### Edge Case 1: Logs are missing or truncated (investigation blocked)

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

### Edge Case 2: Root cause is in infrastructure (not in code)

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

### Edge Case 3: Fix affects other services (unintended side effect)

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

### Edge Case 4: Multiple possible fixes; unclear which is correct

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

### Edge Case 5: Fix works in isolation but fails in full stack

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

---

## Quick Reference Card

**Remember:** Evidence → Hypothesis → Minimal Fix → Verification. Follow the chain.

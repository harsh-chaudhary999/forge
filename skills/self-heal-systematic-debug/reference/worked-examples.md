# Worked Examples & Step-by-Step Walkthrough

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

# Minimal Fix Philosophy

## The Problem with Large Changes
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

## Why Minimal Fixes Matter
1. **Easier to verify:** One change = one verification
2. **Easier to revert:** If it breaks, reverting doesn't lose other work
3. **Easier to understand:** Reviewers see exactly what fixed the issue
4. **Fewer regressions:** Less code changed = fewer new bugs

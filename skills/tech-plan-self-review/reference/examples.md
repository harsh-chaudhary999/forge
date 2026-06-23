# Common Patterns to Check — Worked Review Examples

Spec-says / plan-says / check triplets showing how a reviewer turns a vague plan line into a BLOCKER or WARNING with a concrete fix. Apply these during `## Review Process` Step 2/Step 3 evidence collection.

## Example: Cache TTL
**Spec says:** "Cache 2FA codes for 5 minutes"
**Plan says:** "Add Redis key with TTL"
**Check:**
- ❌ TTL value not specified (BLOCKER)
- Fix: "Redis SET key value EX 300" (300 = 300 seconds = 5 minutes)

## Example: Soft Delete
**Spec says:** "Soft-delete users when account closed"
**Plan has SQL:** `UPDATE users SET deleted_at = NOW() WHERE id = ?`
**Check:**
- ✅ No hard DELETE (good)
- ✅ Timestamp is set (good)
- ❌ Query doesn't check for existing delete (WARNING)
- Fix: Add `AND deleted_at IS NULL` or handle idempotency

## Example: API Contract
**Spec says:** "GET /users/:id returns user object with email, created_at, status"
**Plan says:** "Implement GET endpoint for user details"
**Check:**
- ❌ Fields not specified (BLOCKER)
- ❌ Error cases not documented (BLOCKER)
- ❌ 404 vs 403 handling not clear (BLOCKER)
- Fix: Exact response shape and error codes

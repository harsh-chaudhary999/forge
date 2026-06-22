# Worked Example, Key Principles, Common Mistakes

## Example: Full Schema Contract

Below is a complete example contract for a 2FA feature migration:

```markdown
# Database Schema Contract: 2FA Feature

## Current Schema
```sql
CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_2fa (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  enabled BOOLEAN DEFAULT FALSE,
  secret VARCHAR(255),
  recovery_codes JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_user_id (user_id)
);
```

## Safe Changes

### Schema Change (Day 1)
```sql
ALTER TABLE user_2fa ADD COLUMN verified BOOLEAN DEFAULT FALSE;
ALTER TABLE user_2fa ADD INDEX idx_enabled (enabled);
```

- **Why safe:** Default value supplied, no data loss, new column is optional
- **Backward compatible:** Old code ignores new column

### Code Deployment (Day 1-2)
- Code updated to:
  - Write `verified = TRUE` when 2FA is confirmed
  - Read `verified` to check 2FA status
  - Dual-write: both `enabled` and `verified` initially

### Cleanup (Day 90)
- After 3-month deprecation:
  ```sql
  ALTER TABLE user_2fa DROP COLUMN enabled;
  ```

## Rollback Plan

### If migration fails (before Day 2):
```sql
-- Rollback snapshot (from Day 1 00:00 UTC)
SELECT 
  COUNT(*) as total_rows,
  COUNT(CASE WHEN enabled = TRUE THEN 1 END) as enabled_2fa
FROM user_2fa;
-- Result: 10,000 total, 2,500 enabled

-- Rollback
ALTER TABLE user_2fa DROP COLUMN verified;
ALTER TABLE user_2fa DROP INDEX idx_enabled;

-- Verification (should match snapshot)
SELECT 
  COUNT(*) as total_rows,
  COUNT(CASE WHEN enabled = TRUE THEN 1 END) as enabled_2fa
FROM user_2fa;
-- Result: 10,000 total, 2,500 enabled (MATCH = OK)
```

### If code deployment fails (after Day 2):
1. Revert code to previous version (uses `enabled` column only)
2. No schema rollback needed (new `verified` column unused)
3. Retry code deployment after fix

## Timeline & Checkpoints

| Date | Action | Owner | Verification |
|------|--------|-------|--------------|
| Jan 15 | Schema change deployed | DB team | `DESCRIBE user_2fa` shows `verified` column |
| Jan 15 | Code deployed with dual-write | Dev team | Logs show both `enabled` and `verified` being written |
| Jan 22 | Data validation | QA team | `SELECT COUNT(*) WHERE verified IS NULL` = 0 |
| Jan 29 | Monitoring period ends | Ops team | No errors in last 7 days |
| Apr 15 | Cleanup: drop `enabled` column | DB team | Verify all code uses `verified` only |

## Ready for: Shared-dev-spec lock
```

---

## Key Principles

1. **Migrations are code**: Treat schema changes like code reviews and deployments
2. **Backward compatibility first**: Code should work with both old and new schema during transition
3. **Verify before and after**: Snapshot row counts, integrity checks, query plans
4. **Test rollback**: Never deploy a migration without testing the rollback
5. **Document decision**: Every constraint and index should have a comment explaining why
6. **Monitor impact**: Watch INSERT/UPDATE speeds, query latencies during migration
7. **Deprecation period**: Never delete without warning developers first

## Common Mistakes to Avoid

- Adding NOT NULL without default on table with rows (table lock, fails)
- Dropping columns without deprecation period (data loss, code breaks)
- Adding UNIQUE constraint without checking duplicates first (fails)
- Forgetting to index foreign keys (slow deletes, slow joins)
- Over-indexing tables (slows down writes, bloats storage)
- Rollback script that doesn't match schema state (fails, data corruption)
- Deploying schema before code change (code breaks)
- Deploying code before schema (migrations fail)

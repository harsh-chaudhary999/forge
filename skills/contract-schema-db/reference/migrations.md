# Migration Patterns: Safe Changes, Backward Compatibility, Rollback

## 1. Safe Migrations

Safe migrations are schema changes that can be deployed without downtime and with minimal risk of data loss or integrity issues.

### ADD COLUMN (Safe)

Adding a new column is the safest operation when done correctly:

```sql
-- SAFE: Add with default value
ALTER TABLE users ADD COLUMN phone_verified BOOLEAN DEFAULT FALSE;

-- SAFE: Add optional column (nullable)
ALTER TABLE users ADD COLUMN phone_number VARCHAR(20) NULL;

-- NOT SAFE: Add NOT NULL without default
ALTER TABLE users ADD COLUMN country VARCHAR(2) NOT NULL;  -- WILL FAIL if table has rows
```

**Rules:**
- Always include a DEFAULT value for NOT NULL columns, or make the column NULL
- On MySQL 8.0.12+, `ADD COLUMN ... DEFAULT` is `ALGORITHM=INSTANT` (metadata-only, no table rewrite); on 5.7/earlier it rebuilds the table (use `INPLACE`/pt-online-schema-change)
- Backward compatible: old code ignores the new column

**Timeline:**
- Schema change: immediate
- Code deployment: within 1 week
- No cleanup needed

### DROP COLUMN (Backward-Incompatible)

Dropping columns is dangerous and requires a deprecation period:

```sql
-- STEP 1: Mark column as deprecated (documented, not removed)
-- No schema change - just update documentation and code

-- STEP 2: After 3-month deprecation period, schedule removal
ALTER TABLE users DROP COLUMN legacy_field;
```

**Rules:**
- Warn developers 3 months before dropping
- All code must stop writing to the column before drop
- Monitor logs for any remaining references
- Rollback: use backup or schema versioning system

**Timeline:**
- Month 1: Mark as deprecated in documentation
- Month 2: Code deployed to stop reading/writing
- Month 3: DROP COLUMN
- Month 4+: Safe to remove from backups

### RENAME COLUMN (Backward-Incompatible)

Renaming requires a dual-write pattern to maintain compatibility:

```sql
-- STEP 1: Add new column alongside old
ALTER TABLE users ADD COLUMN email_address VARCHAR(255) NULL;

-- STEP 2: Deploy code that writes to BOTH columns
-- Pseudo-code:
-- INSERT: copy `email` → `email_address` during insert
// if (email) {
//   user.email = email;
//   user.email_address = email;  // dual-write
// }

-- STEP 3: Backfill existing data
UPDATE users SET email_address = email WHERE email_address IS NULL;

-- STEP 4: After full deployment, drop old column
ALTER TABLE users DROP COLUMN email;
```

**Rules:**
- Use dual-write pattern during transition
- Verify 100% of code uses both columns
- Backfill with verification queries
- Old column can be dropped after 2-week verification period

**Rollback:**
- If new column fails validation, revert code and drop new column
- Keep old column available for 2 weeks

### ALTER TABLE CONSTRAINTS (Safe)

Adding constraints is safe if applied correctly:

```sql
-- SAFE: Add PRIMARY KEY to table without one
ALTER TABLE sessions ADD PRIMARY KEY (id);

-- SAFE: Add FOREIGN KEY if all current values are valid
ALTER TABLE orders ADD CONSTRAINT fk_customer 
  FOREIGN KEY (customer_id) REFERENCES customers(id);

-- NOT SAFE: Add CHECK constraint that violates existing data
ALTER TABLE users ADD CONSTRAINT chk_age CHECK (age >= 18);  -- Fails if users.age < 18 exist
```

**Rules:**
- Validate all existing data before adding constraints
- Add constraints off-peak
- For CHECK/UNIQUE constraints, first run: `SELECT COUNT(*) FROM table WHERE constraint_fails`
- Document why constraint exists in migration comment

## 2. Backward Compatibility Patterns

Backward compatibility ensures old code continues working while new code is deployed.

### Dual-Write Pattern

Used when migrating to a new schema while keeping old one:

```sql
-- New schema
ALTER TABLE users ADD COLUMN email_canonical VARCHAR(255) NULL;
```

```javascript
// Code change: write to both old and new columns
async function updateUserEmail(userId, email) {
  const canonicalEmail = email.toLowerCase().trim();
  
  // Dual-write: old and new
  await db.query(
    'UPDATE users SET email = ?, email_canonical = ? WHERE id = ?',
    [email, canonicalEmail, userId]
  );
}
```

**Advantages:**
- Old code can be rolled back safely
- New code works with both columns
- Data is always in sync
- No downtime

**Duration:**
- Dual-write active: 1-4 weeks
- After verification: deploy code to use only new column
- After 1-2 weeks: remove dual-write logic

### Dual-Read Pattern

Used when migrating reads from old to new:

```javascript
// Code: read new, fallback to old
async function getUserEmail(userId) {
  try {
    // Try new column first
    const user = await db.query(
      'SELECT email_canonical FROM users WHERE id = ?',
      [userId]
    );
    
    if (user.email_canonical) {
      return user.email_canonical;
    }
  } catch (e) {
    // Fallback to old column if new doesn't exist yet
  }
  
  // Fallback: read from old column
  const user = await db.query(
    'SELECT email FROM users WHERE id = ?',
    [userId]
  );
  return user.email;
}
```

**Advantages:**
- Code works with both old and new schema
- Gradual migration possible
- Easy rollback

**Duration:**
- Dual-read active: 2-4 weeks
- After migration complete: switch to new column only

### Migration Timeline

The standard timeline for schema migrations with backward compatibility:

```
Day 1: Schema change deployed
  ├─ New column added (with default)
  ├─ Old code continues working
  └─ Monitoring active

Day 1-2: Code deployed with dual-write/dual-read
  ├─ New code writes to both columns
  ├─ Reads prefer new, fallback to old
  └─ Existing records continue using old column

Day 14: Verification and monitoring
  ├─ All writes now hit new column
  ├─ Backfill any missed records
  ├─ Run verification queries
  └─ Data integrity checks pass

Day 21+: Cleanup deployed
  ├─ Code updated to use only new column
  ├─ Old column deprecated in docs
  └─ (Optional) Drop old column after 2-4 weeks

Month 3: Deprecation period ends
  ├─ Safe to remove from backups
  └─ Document in changelog
```

## 5. Rollback Procedures

Every migration must have a tested rollback plan.

### Rollback Script Template

```sql
-- Rollback for: "Add is_2fa_enabled column to users"
-- Migration date: 2026-04-15
-- Backward compatibility: code supports both old+new until 2026-05-15

-- STEP 1: Verify pre-migration state
SELECT COUNT(*) as total_users FROM users;  -- Should match expected count
SELECT COUNT(*) as with_2fa FROM users WHERE is_2fa_enabled = TRUE;  -- Check data

-- STEP 2: Drop new column
ALTER TABLE users DROP COLUMN is_2fa_enabled;

-- STEP 3: Deploy old code that doesn't reference column
-- (Done separately by dev team)

-- STEP 4: Verify rollback
DESCRIBE users;  -- Should NOT have is_2fa_enabled column
```

### Rollback for Backward-Compatible Schema

For migrations using dual-write pattern:

```sql
-- Rollback for: "Migrate user emails to canonical format"
-- Timing: Can rollback for 2 weeks after migration (until dual-write removed)

-- STEP 1: Verify current state
SELECT COUNT(*) FROM users WHERE email IS NOT NULL;  -- Old column still in use
SELECT COUNT(*) FROM users WHERE email_canonical IS NOT NULL;  -- New column populated

-- STEP 2: Deploy code to use old column only
// Code reverts to:
// async function getUserEmail(userId) {
//   return db.query('SELECT email FROM users WHERE id = ?', [userId]);
// }

-- STEP 3: Drop new column
ALTER TABLE users DROP COLUMN email_canonical;

-- STEP 4: Verification
DESCRIBE users;  -- Should only have 'email' column
```

### Verification Queries

Always include verification queries in rollback:

```sql
-- Before rollback snapshot
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT user_id) as unique_users,
  MIN(created_at) as oldest_record,
  MAX(updated_at) as most_recent
FROM user_sessions;
-- Result: 1,245,000 rows, 50,000 users, 2026-04-01, 2026-04-15

-- After rollback (should match):
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT user_id) as unique_users,
  MIN(created_at) as oldest_record,
  MAX(updated_at) as most_recent
FROM user_sessions;
-- Result: 1,245,000 rows, 50,000 users, 2026-04-01, 2026-04-15

-- If mismatch: rollback failed, DO NOT proceed
```

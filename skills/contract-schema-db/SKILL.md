---
name: contract-schema-db
description: "WHEN: Council has identified database schema conflicts across services and needs a locked contract. Defines migrations, backward compatibility, indexing, constraints, and safe change procedures."
type: rigid
requires: [brain-read]
---

# Database Schema Contract Negotiation

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "It's just adding a column, no contract needed" | ALTER TABLE on a large table can lock writes for minutes. Even "simple" changes need migration safety review. |
| "We'll add the index later when it's slow" | Missing indexes in production cause cascading failures under load. Index decisions are contract decisions — make them at council. |
| "Both services can read/write the same table" | Shared table ownership without contracts creates schema conflicts, migration races, and implicit coupling. One owner per table. |
| "Rollback is just DROP COLUMN" | DROP COLUMN is destructive and irreversible. Safe rollback requires a plan before the migration runs, not after it fails. |
| "The ORM handles schema compatibility" | ORMs hide but don't solve backward compatibility. A NOT NULL column added without a default breaks every existing row. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
NO SCHEMA MIGRATION SHIPS WITHOUT A VERIFIED BACKWARD-COMPATIBLE ROLLBACK PLAN. A MIGRATION WITH NO ROLLBACK IS A MIGRATION THAT WILL CAUSE AN INCIDENT.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Migration adds a NOT NULL column without a DEFAULT or backfill** — This will fail on any row that existed before the migration. STOP. Add a DEFAULT or perform a 3-step migration (add nullable → backfill → add NOT NULL constraint).
- **Migration plan has no rollback procedure** — Irreversible migrations with no rollback = production incident with no recovery. STOP. Write rollback steps before any migration runs.
- **Two services are documented as owning the same table** — Shared table ownership causes schema conflicts and migration races. STOP. Establish single ownership per table before locking the contract.
- **Index is not specified for a column used in WHERE clauses** — Missing indexes cause full table scans under load. STOP. Define indexes for all query patterns at contract time.
- **Breaking schema change is introduced without a deprecation window** — Clients using the old schema will break on deploy. STOP. Plan a backward-compatible migration (add new columns, deprecate old ones, remove after transition).
- **Migration locks the table without a lock timeout** — Long locks block all reads/writes. STOP. Set explicit lock wait timeouts and use online DDL strategies for large tables.

This skill teaches teams to safely negotiate and implement MySQL database schema changes using contracts. It covers safe migration patterns, backward compatibility strategies, indexing best practices, constraint handling, and comprehensive rollback procedures.

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
- Default values are applied immediately to existing rows (instant operation)
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

## 3. Indexing Strategy

Proper indexing ensures performance and prevents database bloat.

### Primary Key Design

**Auto-increment (INT/BIGINT):**
```sql
-- Traditional: simple, small, sequential
CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Advantages: small storage, fast lookups
-- Disadvantages: sequential (security risk?), max 2^63 values
```

**UUID (VARCHAR(36)):**
```sql
-- UUID: globally unique, distributed
CREATE TABLE sessions (
  id CHAR(36) PRIMARY KEY,  -- UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  user_id BIGINT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Advantages: distributed, no collisions, secure
-- Disadvantages: larger storage (36 bytes), slower joins
```

**Rules:**
- Use BIGINT for most tables (8 bytes)
- Use UUID only if distributed generation needed
- Use INT (4 bytes) only for small tables (< 2 billion rows)
- Primary key should never change (use surrogate key)

### Foreign Key Indexes

Always index foreign keys:

```sql
-- Foreign key automatically creates index on the same side
-- BUT you must also index the child side:
CREATE TABLE orders (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  customer_id BIGINT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  INDEX idx_customer_id (customer_id)  -- IMPORTANT: for lookups, deletes
);

-- Query: Find all orders for a customer
EXPLAIN SELECT * FROM orders WHERE customer_id = 123;  -- Uses idx_customer_id
```

**Rules:**
- Every FOREIGN KEY must have an INDEX on the same column
- Index improves DELETE performance (CASCADE deletes)
- Index improves JOIN performance
- Naming convention: `idx_<table>_<column>` or `idx_<column>`

### Query Performance Indexes

Indexes should be based on actual query patterns:

```sql
CREATE TABLE user_sessions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  status VARCHAR(20) DEFAULT 'active',
  last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  device_type VARCHAR(50),
  
  INDEX idx_user_id (user_id),  -- For lookups
  INDEX idx_status (status),     -- For filtering
  INDEX idx_last_activity (last_activity),  -- For ORDER BY
  INDEX idx_user_status (user_id, status)   -- Composite: both WHERE clauses
);

-- Query patterns (inform indexing):
-- 1. Find active sessions for user
EXPLAIN SELECT * FROM user_sessions 
  WHERE user_id = 123 AND status = 'active';
-- Uses: idx_user_status (composite)

-- 2. Find oldest inactive sessions
EXPLAIN SELECT * FROM user_sessions 
  WHERE status = 'inactive' 
  ORDER BY last_activity ASC 
  LIMIT 10;
-- Uses: idx_status, then sorts by last_activity

-- 3. Find devices used in last 7 days
EXPLAIN SELECT DISTINCT device_type FROM user_sessions 
  WHERE last_activity > NOW() - INTERVAL 7 DAY;
-- Uses: idx_last_activity
```

**Rules:**
- Index columns in WHERE clauses (filtering)
- Index columns in JOIN conditions
- Index ORDER BY columns
- Composite indexes: most selective first (user_id before status)
- Monitor EXPLAIN output for "Using index" vs "Using temporary"

### Index Bloat Monitoring

Over-indexing causes INSERT/UPDATE slowdowns:

```sql
-- Find unused indexes
SELECT OBJECT_SCHEMA, OBJECT_NAME, INDEX_NAME, COUNT_READ, COUNT_INSERT, COUNT_UPDATE, COUNT_DELETE
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE OBJECT_SCHEMA != 'mysql'
  AND COUNT_READ = 0  -- Never read
  AND (COUNT_INSERT > 0 OR COUNT_UPDATE > 0 OR COUNT_DELETE > 0)
ORDER BY COUNT_INSERT + COUNT_UPDATE + COUNT_DELETE DESC;

-- Find slow indexes
SHOW INDEXES FROM users;
-- Manually review index coverage and selectivity

-- Drop unused index
ALTER TABLE user_sessions DROP INDEX idx_device_type;
```

**Rules:**
- Review index usage monthly
- Drop indexes with COUNT_READ = 0
- Each index costs ~1-5% on INSERT/UPDATE
- Aim for 3-7 indexes per table maximum
- Document why each index exists in migration comment

## 4. Constraints & Triggers

Constraints enforce data integrity and should be added carefully.

### NOT NULL Constraints

NOT NULL constraints prevent NULL values. Adding them requires care:

```sql
-- STEP 1: Add column as NULL
ALTER TABLE users ADD COLUMN country VARCHAR(2) NULL;

-- STEP 2: Backfill with default value
UPDATE users SET country = 'US' WHERE country IS NULL;

-- STEP 3: Add NOT NULL constraint
ALTER TABLE users MODIFY country VARCHAR(2) NOT NULL;

-- STEP 4: Code now must provide value
-- INSERT users(email, country) VALUES ('user@example.com', 'US');  -- OK
-- INSERT users(email) VALUES ('user@example.com');  -- ERROR
```

**Rules:**
- Always add NULL first, then tighten
- Backfill before constraint
- Verify: `SELECT COUNT(*) FROM users WHERE country IS NULL` (should be 0)
- Document in migration comment

### UNIQUE Constraints

UNIQUE constraints are generally safe:

```sql
-- Safe: add UNIQUE to column with no duplicates
-- First verify: SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1;
ALTER TABLE users ADD CONSTRAINT uq_email UNIQUE (email);

-- Also creates automatic index (useful!)
-- Query: SELECT * FROM users WHERE email = 'test@example.com';  -- Very fast
```

**Rules:**
- Verify no existing duplicates before adding
- UNIQUE constraints also act as indexes
- Rollback: `ALTER TABLE users DROP INDEX uq_email;`

### CHECK Constraints

CHECK constraints enforce conditions on data:

```sql
-- Safe: add CHECK that all existing data satisfies
ALTER TABLE users ADD CONSTRAINT chk_age CHECK (age >= 0 AND age < 150);

-- Safe: add CHECK on future values only
ALTER TABLE orders ADD CONSTRAINT chk_total CHECK (total > 0);

-- NOT SAFE without data validation
-- ALTER TABLE users ADD CONSTRAINT chk_age CHECK (age >= 18);  -- Fails if young users exist!
```

**Rules:**
- Verify all existing data satisfies check: `SELECT COUNT(*) FROM users WHERE NOT (age >= 0 AND age < 150);` (should be 0)
- Use for business rules (age range, positive amounts, valid status values)
- Rollback: `ALTER TABLE users DROP CHECK chk_age;`

### FOREIGN KEY Constraints

FOREIGN KEY constraints ensure referential integrity:

```sql
-- Safe: add FOREIGN KEY if all values reference valid rows
CREATE TABLE orders (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  customer_id BIGINT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Verification before adding:
SELECT COUNT(*) FROM orders o 
WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.id = o.customer_id);
-- Should be 0

-- CASCADE options:
-- ON DELETE CASCADE: delete order when customer deleted
-- ON DELETE RESTRICT: prevent customer deletion if orders exist
-- ON DELETE SET NULL: set customer_id = NULL when customer deleted (only if nullable!)
```

**Rules:**
- Always verify referential integrity before adding constraint
- Use CASCADE if child rows should be deleted with parent
- Use RESTRICT if child rows should prevent parent deletion
- Index the foreign key column (for join performance and cascade delete)
- Rollback: `ALTER TABLE orders DROP FOREIGN KEY fk_customer;`

## 5. Rollback Procedures

Every migration must have a tested rollback plan.

### Rollback Script Template

```sql
-- Rollback for: "Add 2fa_enabled column to users"
-- Migration date: 2024-01-15
-- Backward compatibility: code supports both old+new until 2024-02-15

-- STEP 1: Verify pre-migration state
SELECT COUNT(*) as total_users FROM users;  -- Should match expected count
SELECT COUNT(*) as with_2fa FROM users WHERE 2fa_enabled = TRUE;  -- Check data

-- STEP 2: Drop new column
ALTER TABLE users DROP COLUMN 2fa_enabled;

-- STEP 3: Deploy old code that doesn't reference column
-- (Done separately by dev team)

-- STEP 4: Verify rollback
DESCRIBE users;  -- Should NOT have 2fa_enabled column
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
-- Result: 1,245,000 rows, 50,000 users, 2024-01-01, 2024-01-15

-- After rollback (should match):
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT user_id) as unique_users,
  MIN(created_at) as oldest_record,
  MAX(updated_at) as most_recent
FROM user_sessions;
-- Result: 1,245,000 rows, 50,000 users, 2024-01-01, 2024-01-15

-- If mismatch: rollback failed, DO NOT proceed
```

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

---

## Edge Cases & Fallback Paths

### Edge Case 1: Migration is not reversible (one-way change)

**Diagnosis**: Migration drops a column (`DROP COLUMN user_legacy_id`). Rollback script would need to restore data, but dropped data is gone. Migration is one-way.

**Response**:
- **Detect**: During contract negotiation, explicitly ask: "Is this migration reversible? Can we roll it back?"
- **Non-reversible migrations require extra caution**:
  1. **Backup strategy**: Require full database backup before migration.
  2. **Extended testing**: Must test rollback on production-like data volume.
  3. **Data retention period**: If rolling back requires data, keep dropped column in a separate archive table for [X weeks].
  4. **Approval**: Non-reversible migrations require explicit sign-off from infra team and product.
- **Reversible alternative**: Instead of `DROP COLUMN`, `ALTER COLUMN legacy_id to NULL and add trigger to hide from app`. This is reversible.

**Escalation**: If migration must be non-reversible, escalate to NEEDS_APPROVAL - Infra team and product must explicitly approve the risk of no rollback.

---

### Edge Case 2: Existing data violates new constraints

**Diagnosis**: New migration adds `UNIQUE constraint on email` field. But existing data has 5 rows with NULL emails and 2 rows with duplicate emails. Migration fails.

**Response**:
- **Pre-migration validation**: Run SELECT to identify constraint violations.
- **Resolution strategies**:
  1. **Clean data first**: UPDATE existing rows to satisfy constraint before adding constraint.
  2. **Backfill NULL values**: `UPDATE users SET email = CONCAT('no-email-', id) WHERE email IS NULL`.
  3. **Handle duplicates**: Keep first occurrence, UPDATE others to add suffix: `email_1@..., email_2@...`.
  4. **Conditional constraint**: Make constraint conditional: `UNIQUE KEY (email) WHERE email IS NOT NULL`.
- **Migration steps**:
  1. Identify violations: `SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1`.
  2. Fix violations: UPDATE statements.
  3. Add constraint: `ALTER TABLE users ADD UNIQUE (email)`.
- **Document**: Explain why violations existed and how they were resolved.

**Escalation**: If violations are widespread (>10% of data) and fixing them is complex, escalate to user: "Cannot add constraint without data cleanup. Should we soften constraint or run separate data cleanup migration first?"

---

### Edge Case 3: Multiple services touch the same table (coordination needed)

**Diagnosis**: Service A (Orders) and Service B (Payments) both write to `payments` table. New PRD wants to add a column `payment_status_v2`. Both services need to coordinate on when to start writing the new column.

**Response**:
- **Detect**: Identify all services that touch the affected table.
- **Coordination strategy**:
  1. **Phase 1**: Add column with NULL default (schema migration).
  2. **Phase 2**: Service A starts writing to new column (code change in Service A).
  3. **Phase 3**: Service B starts writing to new column (code change in Service B).
  4. **Phase 4**: Deprecate old column (after both services migrated).
  5. **Phase 5**: Drop old column (after deprecation period).
- **Lock coordination**: Document in contract: "This table is owned by [Service]. Other services can write but must coordinate schema changes through [Owner Service team]."
- **Migration window**: All services must be deployed within [X hours] to maintain consistency.

**Escalation**: If services cannot coordinate (team unreachable, unavailable for deployment), escalate to user: "Schema change requires coordination from Service B team. Cannot proceed without their commitment."

---

### Edge Case 4: Large table migration (>100M rows) takes too long

**Diagnosis**: Migration needs to ALTER TABLE with ADD COLUMN on a 500M-row table. Estimated time: 4 hours. This is a production table serving live traffic.

**Response**:
- **Zero-downtime migration strategy**:
  1. **Add column with default**: This creates the column but may lock table during ALTER.
  2. **Use online DDL tool**: MySQL 5.7+ supports `ALGORITHM=INPLACE, LOCK=NONE` to do non-locking migration.
  3. **Pt-online-schema-change**: Use Percona tool to do migration with shadow table, no locks.
  4. **Staging environment**: Dry-run on production-like data volume to measure actual time.
- **Decision**: 
  - If online migration works, use that.
  - If migration would lock table >30min during peak hours, schedule for low-traffic window.
  - If no low-traffic window exists, escalate.

**Escalation**: If migration cannot be completed without significant downtime, escalate to user: "Large table migration would cause [X min] of downtime. Options: 1) Schedule for planned maintenance window, 2) Use more complex zero-downtime approach, 3) Defer migration."

---

### Edge Case 5: Schema change breaks dependent services (hidden constraint)

**Diagnosis**: Migration adds NOT NULL constraint on `user_id` in `orders` table. Dev team thinks all existing rows have `user_id`, but Service C (legacy API) inserts test rows with NULL user_id. After migration, Service C's inserts fail.

**Response**:
- **Detect**: Before committing migration, run impact analysis:
  - Query: "Which services INSERT/UPDATE this table?"
  - For each service, verify: "Does code guarantee NOT NULL value before inserting?"
  - If code doesn't guarantee it, constraint will break that service.
- **Coordination**: Communicate with all services that touch this table: "Adding NOT NULL constraint to [column]. Verify your code handles this before migration."
- **Fallback**:
  - Option 1: Add constraint only for NEW rows: `CHECK (user_id IS NOT NULL)` on future inserts.
  - Option 2: Add constraint but allow NULL for legacy service: `UNIQUE KEY (order_id, user_id) WHERE user_id IS NOT NULL` (partial index).
  - Option 3: Change legacy service code to not insert NULL.

**Escalation**: If multiple services depend on NULL values, escalate to NEEDS_COORD - Services must agree on constraint level before migration.

---

## Decision Tree 1: Schema Migration Strategy

**Q: Does this change break existing code?**

→ **Additive change (new column, new table, new index)**
  - Model: **Expand Phase**
  - Risk: Low (old code ignores new columns)
  - Process:
    1. Deploy schema change (new column with default)
    2. Code updates within 1 week (starts using new column)
    3. No rollback needed (backward compatible)
  - Timeline: 1-2 weeks total
  - Example: Add `email_verified` column with `DEFAULT FALSE`

→ **Breaking change (remove column, rename, type change)**
  - Model: **Expand-Contract Cycle**
  - Risk: High (old code fails when reading/writing)
  - Process:
    1. Expand: Add new column, don't remove old
    2. Dual-write: Code writes to both old+new during transition
    3. Backfill: Fill new column from old data
    4. Contract: Switch code to use new column only
    5. Cleanup: Drop old column after deprecation period
  - Timeline: 4-8 weeks (allows rollback window)
  - Example: Migrate `email` → `email_canonical` (normalize to lowercase)

→ **Urgent breaking change (security, data corruption, compliance)**
  - Model: **Coordinated Cutover**
  - Risk: Very high (requires synchronized deployment)
  - Process:
    1. Expand: Add new column
    2. Parallel deployment: All services deploy code + schema simultaneously
    3. Quick cutover: Traffic switches to new column
    4. Rollback plan: If critical failure, revert all services within 15 minutes
  - Timeline: Hours (not days)
  - Cost: Requires rehearsal, on-call team, high coordination
  - Example: Add `password_hash_v2` using bcrypt, replace insecure hashing

**Decision Flow:**
```
Will old code fail if you deploy this migration?
├─ NO (new column, new table, new index)
│  └─ Expand Only
│     Timeline: 1-2 weeks
│     Risk: Low
│     Rollback: Revert code (not schema)
│
├─ YES, but can be fixed incrementally
│  └─ Expand → Contract Cycle
│     Timeline: 4-8 weeks
│     Risk: Medium
│     Rollback window: 2-4 weeks
│     Code must support dual-read/dual-write
│
└─ YES, critical, must change NOW
   └─ Coordinated Cutover
      Timeline: Hours
      Risk: High
      Requires: On-call team, rollback plan, rehearsal
      Cannot be async or incremental
```

**Key Commitment in Contract:**
```markdown
# Migration Strategy

- **Type**: [Expand Only | Expand-Contract | Coordinated Cutover]
- **Breaking Changes**: [Yes/No]
- **Timeline**: [1-2 weeks | 4-8 weeks | Same-day cutover]
- **Rollback Window**: [Until code deployed | 2-4 weeks | 15 minutes]

## Timeline for Expand-Contract Migration

Day 1: Schema change deployed
  ├─ New column added with default
  ├─ Old code continues working (ignores new column)
  └─ Monitoring active

Day 1-7: Code deployment with dual-write/dual-read
  ├─ New code writes to both old+new columns
  ├─ Reads prefer new, fallback to old
  └─ Backfill any missed records

Day 14: Verification
  ├─ All new writes complete
  ├─ Backfill validation finished
  ├─ Sample data spot-checks passed
  └─ Ready for contract phase

Day 21: Contract phase (optional)
  ├─ Code updated to use new column only (old column deprecated)
  ├─ Monitoring for any old column references
  └─ Deprecation notice sent to team

Day 90: Cleanup (optional)
  ├─ Code fully uses new column
  ├─ Safe to drop old column
  └─ Backups retain old schema for 30 days post-drop
```

---

## Decision Tree 2: Constraint Enforcement Layer

**Q: Where should data validation live (database or application)?**

→ **Database layer (MySQL constraints: NOT NULL, UNIQUE, CHECK, FOREIGN KEY)**
  - Model: **Database-Enforced**
  - Pros:
    - Guarantees data integrity at source
    - Works even if app bypassed (direct SQL, batch jobs)
    - Clear audit trail of invalid attempts
    - No code bugs can violate constraint
  - Cons:
    - Breaks application easily (surprise errors)
    - Harder to roll back (schema change required)
    - Complex constraints hard to express in SQL
  - Use when: Data integrity is non-negotiable (financial, identity, payment)
  - Example: `UNIQUE (email)`, `NOT NULL phone_number`, `FOREIGN KEY (user_id)`

→ **Application layer (ORM validation, business logic checks)**
  - Model: **App-Enforced**
  - Pros:
    - Easy to change without schema migration
    - Better error messages to users
    - Complex validation logic possible (regex, API calls, async checks)
    - Fast feedback (fail fast before DB round-trip)
  - Cons:
    - Bugs in app code violate constraint
    - Direct DB access (batch jobs, migrations) bypass checks
    - No guarantee of consistency
  - Use when: Constraint is domain-specific or user experience is critical
  - Example: "Email must be company domain" (requires DNS lookup), "Username length 3-20 chars"

→ **Dual layer (Both database AND application)**
  - Model: **Redundant Safety**
  - Pros:
    - Database catches bugs in app code
    - App provides better error messages
    - Layers protect each other
    - Most robust for critical data
  - Cons:
    - Double maintenance (two validation paths)
    - Inconsistent error messages between layers
    - App errors differ from DB errors
  - Cost: Higher complexity
  - Use when: Data is critical AND user experience matters
  - Example: UNIQUE constraint in DB, app checks first with better message

**Decision Flow:**
```
How critical is this constraint to data integrity?
├─ Critical (money, identity, compliance)
│  └─ Database-Enforced
│     Add constraint: NOT NULL, UNIQUE, CHECK, FOREIGN KEY
│     App cannot bypass
│
├─ Important (user preference, soft business rule)
│  └─ Dual-Layer
│     DB: Constraint for safety
│     App: Validation for UX
│
└─ Nice-to-have (user experience, optimization)
   └─ App-Enforced Only
      Validation in ORM or business logic
      No DB constraint (allows schema flexibility)
```

**Key Commitment in Contract:**
```markdown
# Constraint Enforcement

## Database-Enforced Constraints
- `NOT NULL phone_number`: Phone required for 2FA
- `UNIQUE (email)`: Prevent duplicate accounts
- `FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE`
- `CHECK (age >= 18)`: Adult-only access
- Rationale: Critical for data integrity, app cannot bypass

## Application-Enforced Validations
- Email format: Regex validation in ORM
- Username length: 3-20 characters checked in app
- Company domain: DNS lookup for company verification
- Rationale: Better UX, easy to change without DB migration

## Dual-Layer (Critical Data)
- Email: DB UNIQUE + App format validation + DNS check
- Password: DB NOT NULL + App min-length + complexity checker
- Rationale: Prevent invalid data at multiple layers

## Error Handling
- If DB constraint fails: Return 409 Conflict (app expected this)
- If app validation fails: Return 400 Bad Request with specific field
- Document for clients: "409 means constraint violation (duplicate, invalid FK)"
```

---

**Escalation**: If multiple services depend on NULL values, escalate to NEEDS_COORD - Services must agree on constraint level before migration.

## Checklist

Before locking a database schema contract:

- [ ] All new columns have explicit NOT NULL/NULL declared with rationale
- [ ] All foreign key constraints reference the correct table and column
- [ ] All indexes specified with type and rationale (covering, partial, composite)
- [ ] Migration plan included for every schema change (additive before destructive)
- [ ] Rollback procedure defined for every destructive migration step
- [ ] Constraint level chosen (DB-enforced vs app-enforced vs dual-layer) with rationale
- [ ] No schema change marked TBD or "to be decided later"

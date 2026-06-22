# Edge Cases, Fallback Paths & Decision Trees

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

**Escalation**: If migration must be non-reversible, escalate to BLOCKED - Infra team and product must explicitly approve the risk of no rollback.

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

**Escalation**: If multiple services depend on NULL values, escalate to NEEDS_COORDINATION - Services must agree on constraint level before migration.

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

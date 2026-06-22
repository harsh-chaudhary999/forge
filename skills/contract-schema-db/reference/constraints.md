# Constraints & Triggers

Constraints enforce data integrity and should be added carefully.

## NOT NULL Constraints

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

## UNIQUE Constraints

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

## CHECK Constraints

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

## FOREIGN KEY Constraints

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

---
name: eval-driver-db-mysql
description: "WHEN: qa-semantic-csv-orchestrate or run_semantic_csv_eval dispatches an automation step that requires database state verification. Functions: setup(), execute(query), verify(assertion), teardown()."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers:
  - "eval MySQL"
  - "run database eval"
  - "DB eval driver"
allowed-tools:
  - Bash
  - Write
---

# Eval Driver: MySQL

**Runner dispatch:** **`qa-semantic-csv-orchestrate`** / **`run_semantic_csv_eval.py`** routes **`Surface: mysql`** rows in **`qa/semantic-automation.csv`** to this driver. Do not invoke this skill directly unless you are implementing or debugging the runner.

Provides a complete driver for executing and verifying SQL queries against MySQL databases during e2e evaluation. Enables deterministic testing of database state, data integrity, and query results in eval scenarios.

## Anti-Pattern Preamble: MySQL Eval Failures You Will Hit

**These misconceptions will break your eval scenarios.** Read carefully.

1. **"DB is separate from eval"** — WRONG. The database IS part of your eval. If your code writes to the database without atomicity, your eval will see inconsistent state. **Always verify database state transactionally.**

2. **"We'll just check if the row exists"** — WRONG. Row existence doesn't guarantee data correctness. A row can exist but have wrong values, NULL violations, or constraint failures. **Always check both existence AND content.**

3. **"Migrations will run automatically"** — WRONG. Schema migrations are NOT automatic during eval. If you expect a table or column that doesn't exist, execute() will fail with `QueryExecutionError`. **Always verify schema state before queries.**

4. **"Connection pool errors are transient"** — WRONG. If your eval exhausts the connection pool (too many open connections), you cannot retry into recovery without closing connections first. **Always cleanup connections explicitly in teardown().**

5. **"We can ignore transaction isolation"** — WRONG. Dirty reads (isolation level READ UNCOMMITTED) can cause race conditions in multi-step evals. **Always use appropriate isolation levels for your scenario.**

6. **"Query timeouts don't matter for eval"** — WRONG. A slow query can timeout, leaving locks or orphaned transactions. Deadlocks also trigger timeouts. **Investigate slow queries; don't just increase timeout.**

---

## Iron Law

```
TEARDOWN ALWAYS RUNS AND RESTORES CLEAN STATE — EVERY EVAL LEAVES THE DATABASE IN THE SAME STATE IT FOUND IT. NO EVAL LEAVES TEST DATA BEHIND.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Queries run against the production database instead of an isolated eval database** — Eval queries that modify data will corrupt production state. STOP. Verify the connection string targets a dedicated eval/test database before calling any `execute()`.
- **`teardown()` is not called after scenario completion** — Open connections and uncommitted transactions left behind will starve the connection pool for the next scenario. STOP. `teardown()` must always run in all paths: success, failure, and timeout.
- **Assertion checks for row existence only (`COUNT(*) > 0`) without verifying column values** — A row existing is not the same as the row containing correct data. STOP. Every `verify()` call must assert specific column values, not just row presence.
- **Schema state is assumed without verification before queries** — If a migration hasn't run, a query against a missing table will fail with a cryptic error instead of a clear "migration not applied" failure. STOP. Always run `setup()` to verify schema state before executing any scenario queries.
- **Queries are executed outside a transaction when testing multi-step writes** — Non-transactional multi-step writes may leave partial state if interrupted, contaminating subsequent scenarios. STOP. Wrap related write steps in a transaction and roll back in teardown unless committed state is required for downstream drivers.
- **Assertion failure shows "got X, expected Y" but the test proceeds to the next step** — A failed assertion on DB state means the system is in unexpected state. Continuing will make subsequent steps produce meaningless results. STOP. Any failed `verify()` must abort the scenario immediately.

## Overview

The MySQL eval driver implements the native wire protocol to connect, authenticate, execute queries, and verify results. Designed for isolation (test databases), determinism (fixtures + verification), and observability (detailed error reporting).

---

## Edge Cases & Failure Modes (Critical for Robustness)

### 1. Connection Pool Exhaustion

**Scenario**: You open many connections without closing them. Eventually, the connection pool is exhausted (default max_connections=151 for MySQL).

**Symptom**: `ConnectionError: Too many connections` or connection request hangs indefinitely.

**Prevention**:
- Always call `teardown()` after every test, even on assertion failure (use try/finally)
- Reuse a single connection across multiple `execute()` and `verify()` calls instead of creating new connections
- Set `max_connections` appropriately in your MySQL config based on concurrent test parallelism
- For stress tests, use a connection pool with explicit limits: `maxConnections: 10` in setup config

**Recovery**:
```javascript
// WRONG: Creates 100 connections, leaks them all
for (let i = 0; i < 100; i++) {
  const conn = await setup({ database: 'test' })
  await execute(conn, "SELECT 1")
  // BUG: no teardown!
}

// RIGHT: Reuse single connection
const conn = await setup({ database: 'test' })
try {
  for (let i = 0; i < 100; i++) {
    await execute(conn, "SELECT 1")
  }
} finally {
  await teardown(conn)
}
```

### 2. Transaction Rollback on Constraint Violation

**Scenario**: Your eval inserts a row that violates a FOREIGN KEY, UNIQUE, or CHECK constraint. The transaction is rolled back automatically by MySQL.

**Symptom**: `QueryExecutionError: 1452 (23000): Cannot add or update a child row; a foreign key constraint fails`

**Impact on subsequent queries**: If you don't handle this properly, your subsequent queries may see partial state (some rows inserted, some rolled back).

**Prevention**:
- Use transactions explicitly with `BEGIN`, `COMMIT`, `ROLLBACK` for multi-step operations
- Check constraint dependencies before INSERT/UPDATE. Example: verify foreign key exists before inserting child row
- Test constraint violations as part of your eval, not as surprises

**Example**:
```javascript
const conn = await setup({ database: 'test' })

// Step 1: Create parent table
await execute(conn, `
  CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))
`)
await execute(conn, `
  CREATE TABLE orders (id INT, user_id INT, FOREIGN KEY(user_id) REFERENCES users(id))
`)

// Step 2: Insert parent
await execute(conn, "INSERT INTO users (id, name) VALUES (1, 'Alice')")

// Step 3: Try to insert child with invalid foreign key
const badInsert = await execute(conn, 
  "INSERT INTO orders (id, user_id) VALUES (1, 999)"
)
// This fails! user_id=999 doesn't exist in users table
// Catch and verify the constraint was enforced

await teardown(conn)
```

### 3. Migration Failures & Schema Incompatibility

**Scenario**: Your eval assumes a table or column exists, but the migration failed or wasn't run. Or you run ALTER TABLE that's incompatible with existing data.

**Symptom**: `QuerySyntaxError: 1054 (42S22): Unknown column 'phone' in 'field list'` or `QueryExecutionError: 1062 (23000): Duplicate entry` during ALTER.

**Prevention**:
- Always verify schema before queries. Use `SHOW TABLES` and `DESCRIBE table_name` to inspect state
- Run migrations explicitly before eval starts, don't assume they're automatic
- Test schema changes in a separate step before data operations
- Use `IF NOT EXISTS` clauses to make DDL idempotent

**Example**:
```javascript
const conn = await setup({ database: 'test' })

// Step 1: Verify schema exists
const tableExists = await execute(conn, 
  "SHOW TABLES LIKE 'users'"
)
if (tableExists.rows.length === 0) {
  throw new Error("Schema not initialized. Run migrations first.")
}

// Step 2: Verify column exists before using it
const schema = await execute(conn, "DESCRIBE users")
const hasPhoneColumn = schema.rows.some(col => col.Field === 'phone')
if (!hasPhoneColumn) {
  throw new Error("'phone' column missing. Schema migration incomplete.")
}

// Step 3: Now safe to query
const result = await execute(conn, "SELECT id, phone FROM users WHERE phone IS NOT NULL")
```

### 4. Query Timeout vs. Deadlock Detection

**Scenario**: A query times out. But was it slow, or was it deadlocked? Deadlocks should be detected and reported differently.

**Symptom**: `QueryTimeoutError: 1317 (70100): Query execution was interrupted` after 10s timeout.

**How to distinguish**:
- **Slow query**: Takes 15 seconds to scan 1M rows. Solution: add index, optimize query, or increase timeout.
- **Deadlock**: Two queries lock each other's rows in circular wait. Solution: change transaction isolation level, add explicit locks, or retry with exponential backoff.

**Prevention**:
- Enable the slow query log: `SET SESSION long_query_time = 1`
- Monitor lock conflicts: `SHOW PROCESSLIST` shows locks in progress
- Use `START TRANSACTION` with explicit isolation levels for deterministic locking

**Example**:
```javascript
const conn = await setup({ database: 'test' })

// Create a scenario prone to deadlock
await execute(conn, `
  CREATE TABLE accounts (id INT PRIMARY KEY, balance DECIMAL(10,2))
`)
await execute(conn, `
  INSERT INTO accounts (id, balance) VALUES (1, 100), (2, 200)
`)

// Transaction 1: Lock account 1, then account 2
await execute(conn, `
  START TRANSACTION
`)
await execute(conn, `
  UPDATE accounts SET balance = balance - 50 WHERE id = 1
`)
// Simulate other transaction locking account 2 first...
// If other transaction then tries to lock account 1, DEADLOCK!

// Solution: Always lock in same order
await execute(conn, `
  UPDATE accounts SET balance = balance + 50 
  WHERE id IN (1, 2) 
  ORDER BY id
`)
```

### 5. Large Result Sets & Memory Exhaustion

**Scenario**: Your SELECT query returns 1M rows. The driver loads all rows into memory at once.

**Symptom**: `OutOfMemoryError` or process killed by OOM killer.

**Prevention**:
- Use pagination: `LIMIT 1000 OFFSET 0` to fetch chunks
- Use `verify()` with `min_count`/`max_count` instead of loading all rows
- For large exports, use `mysql -e "SELECT ..." > file.csv` and process offline

**Example**:
```javascript
const conn = await setup({ database: 'test' })

// WRONG: Loads all 1M rows at once
const allRows = await execute(conn, 
  "SELECT * FROM huge_table"  // Returns 1M rows = ~1GB memory!
)

// RIGHT: Paginate
let offset = 0
let hasMore = true
while (hasMore) {
  const batch = await execute(conn, 
    `SELECT * FROM huge_table LIMIT 1000 OFFSET ${offset}`
  )
  // Process batch of 1000 rows
  offset += 1000
  hasMore = batch.rows.length === 1000
}

// ALSO RIGHT: Just verify count without loading rows
await verify(conn, {
  query: "SELECT COUNT(*) as cnt FROM huge_table",
  expected_count: 1000000,
  description: "Table should have exactly 1M rows"
})
```

### 6. Stale Query Results & Dirty Reads

**Scenario**: Your eval reads data that another transaction is modifying. You see inconsistent snapshots (dirty reads).

**Symptom**: First query returns 5 rows, second query returns 3 rows, but no INSERT/DELETE happened between them. Or you read a value before a COMMIT happens.

**Root cause**: Isolation level is `READ UNCOMMITTED` or `READ COMMITTED`, which allow dirty reads and non-repeatable reads.

**Prevention**:
- Use appropriate isolation levels:
  - `READ UNCOMMITTED`: Never use in evals (allows dirty reads)
  - `READ COMMITTED`: (default) OK for simple evals, but non-repeatable reads possible
  - `REPEATABLE READ`: (MySQL default) Phantom reads possible but consistent snapshot within transaction
  - `SERIALIZABLE`: Highest safety, but slowest (all transactions run sequentially)
- For deterministic evals, use `REPEATABLE READ` or `SERIALIZABLE`

**Example**:
```javascript
const conn = await setup({ database: 'test' })

// Set isolation level to ensure consistent reads
await execute(conn, `
  SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ
`)

// Now all reads within this transaction are consistent
await execute(conn, `
  START TRANSACTION
`)

const result1 = await execute(conn, "SELECT COUNT(*) as cnt FROM orders")
console.log(`Read 1: ${result1.rows[0].cnt} orders`)

// Even if another transaction inserts rows here...
// We still see the same count (phantom read prevented)
const result2 = await execute(conn, "SELECT COUNT(*) as cnt FROM orders")
console.log(`Read 2: ${result2.rows[0].cnt} orders`)

// result1 === result2 guaranteed!

await execute(conn, `
  COMMIT
`)

await teardown(conn)
```

### 7. Schema Mismatch (Migration Not Applied)

**Scenario**: Your eval executes a query against a table that doesn't exist or is missing expected columns because the migration hasn't run.

**Symptom**: `QuerySyntaxError: 1054 (42S22): Unknown table 'products'` or `Unknown column 'sku' in 'field list'`.

**Do NOT**: Assume migrations have run. Do NOT catch the error and silently continue. Do NOT use table names without verification.

**Mitigation**:
- Always verify schema state before executing dependent queries via `SHOW TABLES` and `DESCRIBE`
- Create a `verifySchema()` helper that checks all required tables and columns before eval starts
- Use `IF NOT EXISTS` clauses for idempotent DDL when you control table creation
- Return clear error messages showing which table/column is missing to aid debugging

**Example**:
```javascript
const conn = await setup({ database: 'eval_db' })

// GOOD: Verify schema before using it
const requiredTables = ['products', 'orders', 'inventory']
for (const table of requiredTables) {
  const result = await execute(conn, `SHOW TABLES LIKE '${table}'`)
  if (result.rows.length === 0) {
    throw new Error(`BLOCKED: Required table '${table}' does not exist. Run migrations first.`)
  }
}

const schemaResult = await execute(conn, "DESCRIBE products")
const hasSkuColumn = schemaResult.rows.some(col => col.Field === 'sku')
if (!hasSkuColumn) {
  throw new Error(`BLOCKED: Column 'sku' missing from products table. Schema incomplete.`)
}

// Now safe to query
await execute(conn, "SELECT id, sku FROM products")

// BAD: No verification
await execute(conn, "SELECT id, sku FROM products")  // Fails if schema incomplete
```

**Escalation**: `BLOCKED` — Eval cannot proceed without complete schema. Coordinate with infrastructure team to ensure migrations run before eval.

### 8. Deadlock Detection (Concurrent Transactions)

**Scenario**: Two concurrent transactions lock each other in circular wait. Transaction 1 locks row A then tries to lock row B, while Transaction 2 locks row B then tries to lock row A.

**Symptom**: `QueryExecutionError: 1213 (40P01): Deadlock found when trying to get lock; try restarting transaction`.

**Do NOT**: Ignore the deadlock and assume it won't happen in production. Do NOT increase timeout indefinitely. Do NOT leave deadlock-prone code without retry logic.

**Mitigation**:
- Always lock rows in consistent order (both transactions lock A, then B, not one A-then-B and other B-then-A)
- Use explicit locks with `FOR UPDATE` and `FOR SHARE` clauses
- Implement retry logic with exponential backoff for deadlock errors (code 1213)
- Enable deadlock logging: `SHOW ENGINE INNODB STATUS` to diagnose deadlock graph
- Test concurrent scenarios explicitly to surface deadlock-prone code

**Example**:
```javascript
const conn = await setup({ database: 'eval_db' })

// GOOD: Lock rows in consistent order to prevent deadlock
await execute(conn, `
  CREATE TABLE accounts (id INT PRIMARY KEY, balance DECIMAL(10,2))
`)
await execute(conn, `
  INSERT INTO accounts (id, balance) VALUES (1, 100), (2, 200)
`)

let retries = 0
const maxRetries = 3

while (retries < maxRetries) {
  try {
    await execute(conn, "START TRANSACTION")
    
    // Always lock in ID order (1, then 2) - prevents deadlock
    await execute(conn, `
      SELECT balance FROM accounts WHERE id = 1 FOR UPDATE
    `)
    await execute(conn, `
      SELECT balance FROM accounts WHERE id = 2 FOR UPDATE
    `)
    
    await execute(conn, `
      UPDATE accounts SET balance = balance - 50 WHERE id = 1
    `)
    await execute(conn, `
      UPDATE accounts SET balance = balance + 50 WHERE id = 2
    `)
    
    await execute(conn, "COMMIT")
    break
  } catch (err) {
    if (err.code === 1213) {  // Deadlock error
      retries++
      if (retries >= maxRetries) {
        throw new Error(`NEEDS_COORDINATION: Deadlock persists after ${maxRetries} retries. Check for other competing transactions.`)
      }
      await new Promise(r => setTimeout(r, 100 * Math.pow(2, retries)))  // Exponential backoff
    } else {
      throw err
    }
  }
}

await teardown(conn)
```

**Escalation**: `NEEDS_COORDINATION` — Deadlock indicates transaction design issue. Coordinate with backend team on lock ordering.

### 9. Replication Lag (Master-Slave Consistency)

**Scenario**: Your eval writes to the master database, then immediately reads from a read-replica. The replica is behind the master and hasn't replicated the change yet.

**Symptom**: `ExecutionError: Verification failed. Expected row after INSERT, but SELECT returned 0 rows from replica`.

**Do NOT**: Assume reads from replicas are always up-to-date. Do NOT ignore replication lag in SLOs. Do NOT hardcode delays as a workaround.

**Mitigation**:
- Always write to master and verify writes on master before reading from replicas
- If you must read from replicas, use `SHOW SLAVE STATUS` to check replication lag
- For critical assertions, read from the master database even if slower
- Document the acceptable replication lag in your eval scenario comments
- Use `MASTER_POS_WAIT()` to wait for replica to catch up (requires binary log coordinates)

**Example**:
```javascript
const connMaster = await setup({ 
  host: 'master.db.internal',
  database: 'eval_db' 
})
const connReplica = await setup({ 
  host: 'replica.db.internal',
  database: 'eval_db' 
})

try {
  // GOOD: Write to master
  await execute(connMaster, `
    INSERT INTO products (id, name, sku) VALUES (1, 'Widget', 'SKU-001')
  `)
  
  // Verify write succeeded on master
  await verify(connMaster, {
    query: "SELECT name FROM products WHERE id = 1",
    expected_first_row: { name: 'Widget' }
  })
  
  // Wait for replica to catch up (max 5 seconds)
  const waitResult = await execute(connMaster, `
    SELECT MASTER_POS_WAIT(@@global.binlog_file, @@global.binlog_position, 5)
  `)
  
  if (waitResult.rows[0]['MASTER_POS_WAIT()'] === -1) {
    throw new Error(`NEEDS_INFRA_CHANGE: Replication lag > 5 seconds. Replica not catching up. Check replication status.`)
  }
  
  // Now safe to read from replica
  await verify(connReplica, {
    query: "SELECT name FROM products WHERE id = 1",
    expected_first_row: { name: 'Widget' }
  })
} finally {
  await teardown(connMaster)
  await teardown(connReplica)
}
```

**Escalation**: `NEEDS_INFRA_CHANGE` — If replication lag is excessive, coordinate with infrastructure to increase replica resources or adjust replication settings.

### 10. Query Result Memory Overflow (Large Result Sets)

**Scenario**: A SELECT query returns a massive result set (1M+ rows) that consumes all available memory, causing OOM killer to terminate the process.

**Symptom**: `OutOfMemoryError` or process killed by system OOM killer. Eval hangs and never completes.

**Do NOT**: Load all rows into memory at once. Do NOT assume result sets are small. Do NOT skip pagination for "just this once."

**Mitigation**:
- Always use `LIMIT` and `OFFSET` for large queries, processing in chunks
- Use `COUNT(*)` to verify row counts before loading full results
- For large exports, use `mysql -e "SELECT ..." | gzip > file.sql.gz` to write directly to disk
- Set reasonable timeout on queries to prevent them from running indefinitely
- Monitor query execution plan with `EXPLAIN` to ensure queries use indexes

**Example**:
```javascript
const conn = await setup({ database: 'eval_db' })

// WRONG: Load 1M rows at once
// const allRows = await execute(conn, "SELECT * FROM huge_table")

// RIGHT: Paginate through results
const pageSize = 1000
let offset = 0
let totalCount = 0

// First, verify total count
const countResult = await execute(conn, "SELECT COUNT(*) as cnt FROM huge_table")
const expectedCount = 1000000

await verify(conn, {
  query: "SELECT COUNT(*) as cnt FROM huge_table",
  expected_count: expectedCount,
  description: `Table should have ${expectedCount} rows`
})

// Then process in chunks
while (true) {
  const batch = await execute(conn, `
    SELECT id, name FROM huge_table 
    ORDER BY id
    LIMIT ${pageSize} OFFSET ${offset}
  `)
  
  if (batch.rows.length === 0) break
  
  // Process batch (verify content without holding all in memory)
  for (const row of batch.rows) {
    // Verify row format
    if (!row.id || !row.name) {
      throw new Error(`DONE_WITH_CONCERNS: Row ${row.id} missing required field`)
    }
  }
  
  totalCount += batch.rows.length
  offset += pageSize
  console.log(`Processed ${totalCount} of ${expectedCount} rows`)
}

await teardown(conn)
```

**Escalation**: `DONE_WITH_CONCERNS` — Eval completed but with manual verification of large result sets. Document pagination strategy and memory usage for future evals.

---

## Transaction Guidance: All-or-Nothing Atomicity

**Every eval scenario with multiple steps MUST use transactions.** Transactions ensure atomicity: either all steps succeed and commit, or all roll back on failure.

### Three Transaction Patterns

#### Pattern A: Single-Connection Explicit Transaction (Recommended for Evals)

Use when you have 2+ SQL operations that must succeed or fail together.

```javascript
const conn = await setup({ database: 'eval_db' })

try {
  await execute(conn, "START TRANSACTION")
  
  // Step 1: Insert parent record
  const userResult = await execute(conn, 
    "INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com')"
  )
  const userId = userResult.insertId
  
  // Step 2: Insert related child records
  await execute(conn, 
    `INSERT INTO user_preferences (user_id, theme) VALUES (${userId}, 'dark')`
  )
  await execute(conn, 
    `INSERT INTO user_settings (user_id, notifications) VALUES (${userId}, 1)`
  )
  
  // Step 3: Verify all inserts succeeded
  const verifyResult = await verify(conn, {
    query: `SELECT COUNT(*) as cnt FROM users WHERE id = ${userId}`,
    expected_count: 1
  })
  
  // If we reach here, all succeeded. Commit.
  await execute(conn, "COMMIT")
  
} catch (err) {
  // Any failure? Rollback everything.
  await execute(conn, "ROLLBACK")
  throw err
} finally {
  await teardown(conn)
}
```

#### Pattern B: Savepoints for Partial Rollback

Use when you want to rollback only part of a transaction.

```javascript
const conn = await setup({ database: 'eval_db' })

try {
  await execute(conn, "START TRANSACTION")
  
  // Insert step 1
  await execute(conn, `
    INSERT INTO orders (user_id, total) VALUES (1, 100)
  `)
  
  // Create a savepoint
  await execute(conn, "SAVEPOINT before_discount")
  
  // Try to apply discount (might fail)
  const discountResult = await execute(conn, 
    "UPDATE orders SET total = total - 50 WHERE total >= 100",
    { timeout: 5000 }
  )
  
  if (discountResult.affected === 0) {
    // Rollback only to savepoint, not entire transaction
    await execute(conn, "ROLLBACK TO SAVEPOINT before_discount")
    console.log("Discount failed, rolled back. Order kept original price.")
  }
  
  // Commit the whole transaction
  await execute(conn, "COMMIT")
  
} catch (err) {
  await execute(conn, "ROLLBACK")
  throw err
} finally {
  await teardown(conn)
}
```

#### Pattern C: Isolation Levels for Race Condition Testing

Use when you need to test concurrent scenarios or prevent phantom reads.

```javascript
const conn = await setup({ database: 'eval_db' })

try {
  // Set isolation level BEFORE starting transaction
  await execute(conn, 
    "SET SESSION TRANSACTION ISOLATION LEVEL SERIALIZABLE"
  )
  
  await execute(conn, "START TRANSACTION")
  
  // All reads/writes in this transaction are isolated
  // Even if other transactions are modifying the same rows
  
  const count1 = await execute(conn, "SELECT COUNT(*) as cnt FROM orders")
  
  // Even if another transaction inserts rows here...
  // We'll still get the same count (phantom reads prevented)
  
  const count2 = await execute(conn, "SELECT COUNT(*) as cnt FROM orders")
  
  console.assert(count1.rows[0].cnt === count2.rows[0].cnt, 
    "Phantom read detected!")
  
  await execute(conn, "COMMIT")
  
} finally {
  await teardown(conn)
}
```

### Isolation Levels & When to Use Them

| Level | Dirty Reads | Non-Repeatable Reads | Phantom Reads | Performance | Use Case |
|---|---|---|---|---|---|
| READ UNCOMMITTED | Yes | Yes | Yes | Fastest | Never for evals (unsafe) |
| READ COMMITTED | No | Yes | Yes | Fast | Simple evals, no race conditions |
| REPEATABLE READ | No | No | Yes | Medium | **MySQL default**, most evals |
| SERIALIZABLE | No | No | No | Slowest | Race condition testing, critical data |

**For eval scenarios:** Use `REPEATABLE READ` (MySQL default) unless you're specifically testing race conditions or concurrent modifications.

### Rollback Strategies

1. **Automatic rollback on error**: If any `execute()` throws an exception, catch it and call `ROLLBACK`
2. **Assertion-based rollback**: If `verify()` fails, call `ROLLBACK` to undo the test scenario
3. **Savepoint rollback**: Roll back partial changes without undoing entire transaction
4. **Never silently ignore rollback failures**: If `ROLLBACK` fails, your connection is in undefined state. Reconnect.

---

## Connection Management: Pool Sizing & Cleanup

### Pool Sizing Based on Concurrency

The connection pool prevents resource exhaustion. Size it based on your concurrent eval scenarios.

```javascript
// Example 1: Sequential eval (single connection reused)
const conn = await setup({
  database: 'eval_db',
  maxConnections: 1  // One connection, sequential queries
})
// Sequential evals are slower but use minimal resources

// Example 2: Parallel eval scenarios (multiple connections)
const conn = await setup({
  database: 'eval_db',
  maxConnections: 10  // Allow up to 10 concurrent eval scenarios
})
// Parallel evals are faster but use more resources

// Example 3: Under load testing (stress test connections)
const conn = await setup({
  database: 'eval_db',
  maxConnections: 50  // Allow many concurrent scenarios
})
// Monitor actual usage: MySQL default is max_connections=151
```

### Connection Cleanup Between Steps

Always explicitly close connections. Use try/finally to guarantee cleanup.

```javascript
// WRONG: Connection leaked if exception occurs
async function badExample() {
  const conn = await setup({ database: 'test' })
  const result = await execute(conn, "SELECT * FROM users")
  await teardown(conn)  // Never reached if execute() throws!
}

// RIGHT: Guaranteed cleanup with try/finally
async function goodExample() {
  const conn = await setup({ database: 'test' })
  try {
    const result = await execute(conn, "SELECT * FROM users")
    return result
  } finally {
    await teardown(conn)  // Always runs, even on error
  }
}

// ALSO RIGHT: Async-await with explicit error handling
async function goodExampleV2() {
  const conn = await setup({ database: 'test' })
  
  try {
    const result = await execute(conn, "SELECT * FROM users")
    await teardown(conn)
    return result
  } catch (err) {
    // Cleanup on error
    try {
      await teardown(conn)
    } catch (cleanupErr) {
      console.error("Cleanup also failed:", cleanupErr)
    }
    throw err
  }
}
```

### Graceful Connection Closure

The `teardown()` function sends `COM_QUIT` to cleanly close the connection, but explicitly set cleanup options:

```javascript
const conn = await setup({ database: 'eval_db' })

try {
  // ... run eval ...
  
  // Option 1: Just close connection (default)
  await teardown(conn)
  // Connection closed, test database remains
  
  // Option 2: Drop tables before closing
  await teardown(conn, {
    dropTables: ['test_users', 'test_orders']
  })
  // Tables dropped, then connection closed
  
  // Option 3: Drop entire database before closing
  await teardown(conn, {
    dropDatabase: true
  })
  // Database dropped, then connection closed
} catch (err) {
  // Even on error, attempt cleanup
  try {
    await teardown(conn, { dropDatabase: true })
  } catch {}  // Suppress cleanup errors
  throw err
}
```

---

## Core Functions

### setup(config) → connection

Establishes a connection to MySQL and verifies reachability.

**Parameters:**
- `config` (object)
  - `host` (string): MySQL server hostname. Default: `'localhost'`
  - `port` (number): MySQL server port. Default: `3306`
  - `user` (string): Database user. Default: `'root'`
  - `password` (string): Database password. Default: `''`
  - `database` (string): Database name to use. If doesn't exist, will be created.
  - `timeout` (number): Connection timeout in milliseconds. Default: `5000`
  - `retries` (number): Number of retry attempts on connection failure. Default: `3`
  - `retryDelayMs` (number): Delay between retries in milliseconds. Default: `1000`

**Returns:**
- `connection` (object): Active MySQL connection handle
  - `.connected` (boolean): Connection status
  - `.database` (string): Active database name
  - `.host` (string): Connected host
  - `.port` (number): Connected port
  - `.timezone` (string): Server timezone

**Throws:**
- `ConnectionError`: If unable to connect after retries
- `DatabaseError`: If database creation fails
- `AuthenticationError`: If credentials are invalid

**Implementation Details:**

The setup function uses the MySQL wire protocol (port 3306) with the following steps:

1. **Initial handshake**: Connect to TCP socket, perform MySQL handshake authentication
2. **Credential exchange**: Send username/password using native authentication plugin
3. **Database selection**: Switch to target database; create if doesn't exist and `createIfMissing: true`
4. **Verification query**: Run `SELECT 1` to confirm connection state
5. **Timezone sync**: Detect server timezone and set session timezone to UTC
6. **Charset**: Set UTF-8MB4 charset for query results

With `retries: 3` and `retryDelayMs: 1000`, total timeout is ~8 seconds (initial 5s + 3 retries × 1s).

**Example:**
```javascript
const conn = await setup({
  host: 'localhost',
  port: 3306,
  user: 'eval_user',
  password: 'eval_pass',
  database: 'shopapp_eval',
  timeout: 5000,
  retries: 3
})

if (conn.connected) {
  console.log(`Connected to ${conn.database} at ${conn.host}:${conn.port}`)
}
```

---

### execute(connection, query, options) → {rows, affected, duration}

Executes a SQL query and returns raw results.

**Parameters:**
- `connection` (object): Active connection from `setup()`
- `query` (string): SQL statement (SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, etc.)
- `options` (object, optional)
  - `timeout` (number): Query timeout in milliseconds. Default: `10000`
  - `parseJSON` (boolean): Auto-parse JSON strings in result columns. Default: `true`
  - `castNumeric` (boolean): Cast numeric-looking strings to numbers. Default: `true`

**Returns:**
- `result` (object)
  - `.rows` (array): Result rows. Empty array for INSERT/UPDATE/DELETE with no result set.
  - `.affected` (number): Rows affected by INSERT/UPDATE/DELETE. 0 for SELECT.
  - `.duration` (number): Query execution time in milliseconds
  - `.columns` (array): Column names from SELECT queries
  - `.insertId` (number): Last inserted AUTO_INCREMENT ID for INSERT queries

**Throws:**
- `QueryTimeoutError`: If query exceeds timeout
- `QuerySyntaxError`: If SQL is invalid
- `QueryExecutionError`: If database constraint violation or permission error occurs

**Implementation Details:**

Uses the MySQL command protocol to send queries and parse response packets:

1. **Send**: Write COM_QUERY command packet with query string
2. **Result parsing**: Read response packets, distinguish between:
   - OK packet (INSERT/UPDATE/DELETE): Contains affected rows, insert ID
   - Resultset packet (SELECT): Contains column definitions and data rows
   - Error packet: Contains error code and message
3. **Type inference**: Automatically detect column types (INT, VARCHAR, DATETIME, JSON, DECIMAL, etc.)
4. **Conversion**: Parse TEXT results according to inferred type, with `castNumeric` and `parseJSON` options
5. **Duration**: Record wall-clock time from send to completion

**Timeout strategy**: Each query has independent timeout. Network packets are monitored; if no data arrives within timeout window, connection is marked stale and query fails.

**Example:**
```javascript
// SELECT query
const selectResult = await execute(conn, 
  "SELECT id, name, created_at FROM users WHERE active = true"
)
console.log(`Found ${selectResult.rows.length} active users in ${selectResult.duration}ms`)

// INSERT query
const insertResult = await execute(conn,
  "INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com')"
)
console.log(`Inserted row with ID: ${insertResult.insertId}`)

// UPDATE query
const updateResult = await execute(conn,
  "UPDATE users SET active = false WHERE id > 100"
)
console.log(`Updated ${updateResult.affected} rows`)
```

---

### verify(connection, assertion) → {passed, evidence}

Asserts conditions on query results and returns detailed evidence.

**Parameters:**
- `connection` (object): Active connection from `setup()`
- `assertion` (object)
  - `query` (string): SQL query to run for assertion
  - `expected_count` (number, optional): Expected number of rows. Fails if mismatch.
  - `expected_columns` (array, optional): Expected column names in order. Fails if mismatch.
  - `expected_first_row` (object, optional): First row must match these column:value pairs. Partial match allowed.
  - `expected_rows` (array, optional): All rows must match array (in order). Each array element is column:value object.
  - `min_count` (number, optional): Minimum row count. Fails if count < min_count.
  - `max_count` (number, optional): Maximum row count. Fails if count > max_count.
  - `column_values` (object, optional): All rows' named column must equal value (homogeneous assertion)
  - `description` (string, optional): Human-readable assertion description for error messages
  - `timeout` (number, optional): Query timeout. Default: `10000`

**Returns:**
- `result` (object)
  - `.passed` (boolean): True if all assertions passed
  - `.evidence` (string): Detailed explanation of what was checked and what failed
  - `.actual_count` (number): Actual row count
  - `.actual_columns` (array): Actual column names
  - `.actual_rows` (array): Actual result rows (up to 100 rows in evidence)
  - `.assertion_details` (object): Which sub-assertions passed/failed

**Throws:**
- `AssertionError`: If assertion structure is invalid
- `QueryError`: If the underlying query fails

**Implementation Details:**

Verify runs the query and systematically checks each assertion:

1. **Run query**: Execute the assertion query
2. **Count check**: If `expected_count`, `min_count`, or `max_count` specified, compare row count
3. **Column check**: If `expected_columns` specified, compare column names and order
4. **Row shape check**: If `expected_first_row`, verify first row matches (subset match)
5. **Homogeneous check**: If `column_values`, verify all rows have same value in named column
6. **Full row match**: If `expected_rows`, verify all rows match expected array in order
7. **Evidence**: Construct detailed report including actual vs. expected and failure reason

All checks are AND'd together; if any assertion fails, `passed: false`.

**Example:**
```javascript
// Assertion 1: Verify row count
await verify(conn, {
  query: "SELECT COUNT(*) as cnt FROM users WHERE 2fa_enabled = true",
  expected_count: 1,
  description: "Exactly 1 user has 2FA enabled"
})

// Assertion 2: Verify column values
await verify(conn, {
  query: "SELECT user_id, status FROM orders WHERE total > 1000",
  expected_first_row: { status: 'premium' },
  min_count: 5,
  description: "At least 5 premium orders with total > $1000"
})

// Assertion 3: Verify all rows match
await verify(conn, {
  query: "SELECT id, name, role FROM admins",
  expected_rows: [
    { id: 1, name: 'Alice', role: 'superuser' },
    { id: 2, name: 'Bob', role: 'superuser' }
  ],
  description: "Exactly 2 admin users with correct roles"
})

// Assertion 4: Homogeneous column check
await verify(conn, {
  query: "SELECT id, status FROM accounts WHERE deleted_at IS NOT NULL",
  column_values: { status: 'inactive' },
  description: "All deleted accounts must be marked inactive"
})
```

---

### teardown(connection) → void

Closes the connection and optionally cleans up test data.

**Parameters:**
- `connection` (object): Active connection from `setup()`
- `options` (object, optional)
  - `dropDatabase` (boolean): Drop the test database on teardown. Default: `false`
  - `dropTables` (array, optional): List of table names to drop before closing
  - `timeout` (number): Cleanup timeout in milliseconds. Default: `5000`

**Returns:**
- None

**Throws:**
- `TeardownError`: If cleanup fails (database still in use, permission denied, etc.)

**Implementation Details:**

Teardown performs safe cleanup:

1. **Drop tables** (if specified): For each table in `dropTables`, run `DROP TABLE IF EXISTS table_name`
2. **Drop database** (if specified): Run `DROP DATABASE IF EXISTS database_name`
3. **Close connection**: Send COM_QUIT command packet and close TCP socket
4. **Verify**: Check that connection is fully closed

**Safety**: Uses `DROP TABLE IF EXISTS` and `DROP DATABASE IF EXISTS` to prevent errors if objects don't exist. Always safe to call multiple times.

**Example:**
```javascript
// Cleanup approach 1: Just close connection
await teardown(conn)

// Cleanup approach 2: Drop test tables
await teardown(conn, {
  dropTables: ['users_test', 'orders_test', 'audit_log_test']
})

// Cleanup approach 3: Drop entire test database
await teardown(conn, {
  dropDatabase: true
})
```

---

## Wire Protocol Details

### Connection Handshake

1. Client connects to TCP 3306
2. Server sends handshake packet:
   - Protocol version (10)
   - Server version string
   - Connection ID
   - Auth plugin seed (8 bytes)
   - Capability flags
3. Client sends authentication response:
   - Capability flags
   - Username
   - Password hash (SHA1(SHA1(password)))
   - Database name
4. Server sends OK packet or error packet

### Query Execution Protocol

1. Client sends COM_QUERY (0x03) packet with query string
2. Server responds with:
   - **For SELECT/SHOW**: Column count, column definitions, rows, EOF packet
   - **For INSERT/UPDATE/DELETE**: OK packet with affected rows count
   - **For errors**: Error packet with code and message

### Error Handling

All MySQL errors are caught and translated:

| MySQL Error Code | Translated Error | Handling |
|---|---|---|
| 1045 | AuthenticationError | Credentials rejected; check user/password |
| 1049 | DatabaseError | Unknown database; create if needed |
| 1064 | QuerySyntaxError | Malformed SQL; check query syntax |
| 1205 | QueryTimeoutError | Lock wait timeout; retry or check locks |
| 1317 | QueryTimeoutError | Query interrupted by timeout |
| 2006 | ConnectionError | Connection lost; reconnect required |
| 2013 | ConnectionError | Lost connection during query |

---

## Timeout & Retry Strategy

### Connection Timeout
- **Initial timeout**: 5000ms per connection attempt
- **Retry attempts**: 3 (configurable)
- **Retry delay**: 1000ms (configurable)
- **Total timeout**: ~8 seconds for setup with full retries

### Query Timeout
- **Default timeout**: 10000ms per query
- **Configurable**: Per execute/verify call
- **Behavior**: Query is killed server-side if not completed by timeout

### Stale Connection Detection
- **Heartbeat check**: Send `SELECT 1` every 30 seconds if idle
- **Auto-reconnect**: If connection lost, attempt 1 reconnect before failing
- **Circuit breaker**: After 3 consecutive failures, mark connection as dead

---

## Usage Patterns

### Pattern 1: Basic Data Verification
```javascript
// Setup
const conn = await setup({
  host: 'localhost',
  database: 'shopapp_eval'
})

// Execute query
const result = await execute(conn, 
  "SELECT COUNT(*) as cnt FROM users"
)
console.log(`Total users: ${result.rows[0].cnt}`)

// Verify
await verify(conn, {
  query: "SELECT COUNT(*) as cnt FROM users",
  expected_count: 1,
  description: "Database should have exactly 1 test user"
})

// Cleanup
await teardown(conn)
```

### Pattern 2: State Assertion in Eval Scenario
```javascript
const conn = await setup({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: 'eval_db'
})

// After executing a business logic operation:
await verify(conn, {
  query: "SELECT id, status FROM orders WHERE id = ?",
  expected_first_row: { status: 'completed' },
  description: "Order should be marked completed after fulfillment"
})

// Verify side effects:
await verify(conn, {
  query: "SELECT COUNT(*) as cnt FROM audit_log WHERE order_id = ? AND action = ?",
  expected_count: 1,
  description: "Exactly one audit log entry for order completion"
})

await teardown(conn)
```

### Pattern 3: Multi-Table Consistency
```javascript
const conn = await setup({ database: 'eval_db' })

// Verify referential integrity
const orphans = await execute(conn,
  "SELECT order_id FROM order_items WHERE order_id NOT IN (SELECT id FROM orders)"
)
if (orphans.rows.length > 0) {
  throw new Error(`Found ${orphans.rows.length} orphaned order items`)
}

// Verify aggregate consistency
await verify(conn, {
  query: `
    SELECT o.id, o.total, SUM(oi.price * oi.quantity) as calculated_total
    FROM orders o
    LEFT JOIN order_items oi ON oi.order_id = o.id
    GROUP BY o.id
    HAVING o.total != calculated_total
  `,
  expected_count: 0,
  description: "Order totals must match sum of line items"
})

await teardown(conn)
```

### Pattern 4: Setup With Test Fixtures
```javascript
const conn = await setup({ database: 'eval_db' })

// Create test data
await execute(conn, `
  INSERT INTO users (id, name, email) VALUES
  (1, 'Alice', 'alice@test.com'),
  (2, 'Bob', 'bob@test.com'),
  (3, 'Charlie', 'charlie@test.com')
`)

// Run application code under test...

// Verify results
await verify(conn, {
  query: "SELECT COUNT(*) as cnt FROM audit_log WHERE action = 'user_created'",
  expected_count: 3,
  description: "All 3 users should have creation audit logs"
})

await teardown(conn, { dropTables: ['users', 'audit_log'] })
```

---

## Error Messages & Debugging

### Connection Errors
```
ConnectionError: Failed to connect to localhost:3306 after 3 retries
  Cause: ECONNREFUSED (Connection refused)
  Last error: Connection attempt 3: Socket timeout after 5000ms
```

### Authentication Errors
```
AuthenticationError: MySQL server at localhost:3306 rejected credentials
  User: 'eval_user'
  Message: Access denied for user 'eval_user'@'localhost' (using password: YES)
```

### Query Errors
```
QuerySyntaxError: Syntax error in query
  Query: SELECT COUNT(*) FROM users WHERE id = ?
  Position: 10
  Message: Unexpected token '?' (use parameterized queries for safety)
```

### Assertion Errors
```
AssertionError: Row count mismatch in verify()
  Expected count: 1
  Actual count: 0
  Query: SELECT * FROM users WHERE 2fa_enabled = true
  Description: User 2FA enabled should have exactly 1 row
```

---

## Security Considerations

1. **Prepared statements**: Use parameterized queries with `?` placeholders for user input
2. **Connection pooling**: For multi-query scenarios, reuse connection across multiple execute/verify calls
3. **Credentials**: Load DB credentials from environment variables, never hardcode in test files
4. **Database isolation**: Always use dedicated test databases, never eval against production
5. **Cleanup**: Always call teardown(); use try/finally to ensure cleanup even on test failure

---

## Performance Characteristics

| Operation | Time (typical) | Notes |
|---|---|---|
| setup() | 100-500ms | Includes handshake + verification query |
| execute() for SELECT 1000 rows | 50-200ms | Depends on network, data size |
| execute() for INSERT 1000 rows | 100-500ms | Batch operations faster than individual |
| verify() | 50-200ms | Same as execute + assertion checks |
| teardown() | 10-50ms | Just connection close |

---

## Compatibility

- **MySQL versions**: 5.7, 8.0, 8.1+
- **MariaDB**: 10.3+ (compatible wire protocol)
- **Authentication**: Native plugin (default), supports MD5 legacy plugin
- **Charsets**: UTF-8MB4 (default), configurable
- **TLS**: Not yet supported; use for dev/test environments only

---

## Best Practices

### 1. Transactions Are Your Safety Net

Every eval with multiple database operations must be wrapped in a transaction. Transactions are the ONLY way to guarantee atomicity.

**Rule: If your eval has 2+ database operations, use explicit `BEGIN`/`COMMIT` or `ROLLBACK`.**

```javascript
// GOOD: All-or-nothing semantics
const conn = await setup({ database: 'eval_db' })
try {
  await execute(conn, "BEGIN")
  
  await execute(conn, "INSERT INTO accounts (name) VALUES ('Alice')")
  await execute(conn, "INSERT INTO account_settings (account_id) VALUES (1)")
  
  await verify(conn, {
    query: "SELECT COUNT(*) as cnt FROM account_settings",
    expected_count: 1
  })
  
  await execute(conn, "COMMIT")
} catch (err) {
  await execute(conn, "ROLLBACK")
  throw err
} finally {
  await teardown(conn)
}

// BAD: No transaction, inconsistent state on failure
const conn2 = await setup({ database: 'eval_db' })
await execute(conn2, "INSERT INTO accounts (name) VALUES ('Bob')")
// If next line fails, account exists but settings don't
await execute(conn2, "INSERT INTO account_settings (account_id) VALUES (2)")
await teardown(conn2)
```

### 2. Isolation Levels Matter for Race Conditions

Dirty reads and phantom reads are real. Use appropriate isolation levels.

**Rule: For deterministic evals, use `REPEATABLE READ`. For race condition testing, use `SERIALIZABLE`.**

```javascript
// GOOD: Explicit isolation level
await execute(conn, 
  "SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ"
)
await execute(conn, "START TRANSACTION")
// Now all reads are consistent within this transaction

// BAD: Relying on defaults
await execute(conn, "START TRANSACTION")
// What isolation level? (Depends on MySQL config, not explicit)
```

### 3. Always Cleanup Connections

Connection leaks exhaust the pool and cause eval failures for subsequent tests.

**Rule: Use try/finally with `teardown()` to guarantee cleanup, even on errors.**

```javascript
// GOOD: Guaranteed cleanup
async function runEval(evalName) {
  const conn = await setup({ database: 'eval_db' })
  try {
    console.log(`Running eval: ${evalName}`)
    // ... your eval code ...
  } finally {
    await teardown(conn)
  }
}

// BAD: Connection leaked if exception occurs
async function badEval() {
  const conn = await setup({ database: 'eval_db' })
  // ... code ...
  await teardown(conn)  // Never reached if exception!
}
```

### 4. Verify Both Existence AND Content

Checking that a row exists is not enough. Verify the actual data.

**Rule: Always use `verify()` with specific assertions, not just row count.**

```javascript
// GOOD: Verify existence + content
await verify(conn, {
  query: "SELECT status, created_at FROM orders WHERE id = 1",
  expected_first_row: {
    status: 'completed',
    created_at: '2026-04-10 12:00:00'
  },
  description: "Order 1 should be completed with correct timestamp"
})

// BAD: Only checking existence
const result = await execute(conn, "SELECT * FROM orders WHERE id = 1")
if (result.rows.length > 0) {
  console.log("Order exists!")
  // But is it correct? We don't know!
}
```

### 5. Verify Schema Before Querying

Never assume a table or column exists. Always verify schema state.

**Rule: Check schema with `SHOW TABLES` and `DESCRIBE` before dependent queries.**

```javascript
// GOOD: Schema validation first
const tableExists = await execute(conn, 
  "SHOW TABLES LIKE 'orders'"
)
if (tableExists.rows.length === 0) {
  throw new Error("orders table missing! Run schema migrations first.")
}

const schema = await execute(conn, "DESCRIBE orders")
const hasStatusColumn = schema.rows.some(col => col.Field === 'status')
if (!hasStatusColumn) {
  throw new Error("'status' column missing. Schema incomplete.")
}

// Now safe to query
await execute(conn, "SELECT status FROM orders")

// BAD: Blind query (fails if table or column missing)
await execute(conn, "SELECT status FROM orders")
// QuerySyntaxError if table missing, QueryExecutionError if column missing
```

### 6. Monitor Query Performance

Slow queries block other transactions and can cause timeouts.

**Rule: Log query duration. Queries > 1s should be investigated.**

```javascript
// GOOD: Track slow queries
const result = await execute(conn, 
  "SELECT * FROM large_table WHERE complex_condition"
)
console.log(`Query took ${result.duration}ms`)

if (result.duration > 1000) {
  console.warn(`SLOW QUERY (${result.duration}ms): Add index or optimize`)
}

// BAD: Ignore duration, just hope query is fast
const result2 = await execute(conn, "SELECT * FROM large_table")
// Is it fast? No way to know!
```

### 7. Test Constraint Violations Explicitly

Your eval should test that constraints are enforced, not silently fail.

**Rule: Write specific tests for constraint violations (FK, UNIQUE, CHECK, NOT NULL).**

```javascript
// GOOD: Explicitly test constraint enforcement
const conn = await setup({ database: 'eval_db' })

// Create schema with constraint
await execute(conn, `
  CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100) NOT NULL)
`)
await execute(conn, `
  CREATE TABLE orders (id INT PRIMARY KEY, user_id INT, 
    FOREIGN KEY(user_id) REFERENCES users(id))
`)

// Test 1: Valid insert (should succeed)
const validInsert = await execute(conn, 
  "INSERT INTO users (id, name) VALUES (1, 'Alice')"
)
if (validInsert.affected !== 1) {
  throw new Error("Valid insert failed!")
}

// Test 2: FK constraint violation (should fail)
try {
  await execute(conn, 
    "INSERT INTO orders (id, user_id) VALUES (1, 999)"
  )
  throw new Error("FK constraint not enforced!")
} catch (err) {
  if (!err.message.includes("Foreign key constraint fails")) {
    throw err
  }
  console.log("FK constraint correctly enforced")
}

// Test 3: NOT NULL violation (should fail)
try {
  await execute(conn, 
    "INSERT INTO users (id, name) VALUES (2, NULL)"
  )
  throw new Error("NOT NULL constraint not enforced!")
} catch (err) {
  if (!err.message.includes("NOT NULL")) {
    throw err
  }
  console.log("NOT NULL constraint correctly enforced")
}

await teardown(conn)
```

### 8. Use Paginated Queries for Large Results

Never load millions of rows into memory at once.

**Rule: For results > 10,000 rows, use `LIMIT` and `OFFSET` pagination.**

```javascript
// GOOD: Paginate large result sets
const pageSize = 1000
let offset = 0
let totalProcessed = 0

while (true) {
  const batch = await execute(conn, 
    `SELECT id, name FROM users LIMIT ${pageSize} OFFSET ${offset}`
  )
  
  if (batch.rows.length === 0) break
  
  // Process batch
  for (const row of batch.rows) {
    // ... do something with row ...
  }
  
  totalProcessed += batch.rows.length
  offset += pageSize
}

console.log(`Processed ${totalProcessed} rows`)

// BAD: Load all rows at once
const allRows = await execute(conn, 
  "SELECT id, name FROM users"  // Could be 1M rows = 1GB memory!
)
for (const row of allRows.rows) {
  // Memory exhaustion risk!
}
```

---

## Decision Tree: Transaction Isolation Level Selection

When designing your eval scenario, choose the appropriate isolation level based on your data consistency requirements and test objectives.

```
DO YOU NEED TO TEST CONCURRENT MODIFICATIONS OR RACE CONDITIONS?
│
├─ YES → Is perfect isolation required (no dirty reads, phantom reads)?
│        │
│        ├─ YES → Use SERIALIZABLE (slowest, but bulletproof)
│        │        └─ All transactions run in strict sequence
│        │        └─ No dirty reads, non-repeatable reads, or phantom reads
│        │        └─ Example: Payment processing, critical account transfers
│        │
│        └─ NO → Use REPEATABLE READ (MySQL default, balanced)
│               └─ Consistent snapshot within transaction
│               └─ Phantom reads possible but rare in practice
│               └─ Example: Most evals, multi-step data consistency checks
│
└─ NO → Are you doing simple, single-step reads without concurrent modification?
       │
       ├─ YES, and speed is critical → Use READ COMMITTED (fast)
       │                                └─ Non-repeatable reads possible
       │                                └─ Only for simple scenarios (avoid for eval)
       │
       └─ NO, or you're unsure → Stick with REPEATABLE READ (default)
                                  └─ Safe choice for 95% of eval scenarios
                                  └─ Minimal performance penalty
```

**Implementation**:
```javascript
// Before START TRANSACTION, set isolation level explicitly
await execute(conn, `
  SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ
`)

await execute(conn, "START TRANSACTION")
// All reads/writes now use REPEATABLE READ isolation
```

---

## Related Skills

- `eval-driver-api-http`: For REST API evaluation
- `brain-read`: Load product topology and past decisions
- `contract-schema-db`: Negotiate database schema contracts

---

## Checklist

Before claiming MySQL eval complete:

- [ ] `setup()` ran and schema state verified before any queries
- [ ] All assertions verify both row existence AND data values
- [ ] Transactional isolation confirmed (no dirty reads between eval steps)
- [ ] `teardown()` called unconditionally — test data removed and DB in clean state
- [ ] No eval leaves behind uncommitted transactions or orphaned rows

---
name: eval-driver-db-mysql
description: "WHEN: qa-semantic-csv-orchestrate or run_semantic_csv_eval dispatches an automation step that requires database state verification. Functions: setup(), execute(query), verify(assertion), teardown()."
type: rigid
requires: [brain-read]
version: 1.0.1
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

## Reference (load on demand)

The full API, examples, protocol details, edge-case code, and deep guidance live in
**`reference/mysql-reference.md`** (Agent Skills progressive disclosure). This SKILL.md is the operational
contract: runner dispatch, discipline (anti-pattern / iron law / red flags), and decision logic.

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

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] Every scenario step has an entry in `qa/semantic-eval-run.log` (no silent skips).
- [ ] Each step outcome is one of: `PASS`, `FAIL`, `BLOCKED_DEPENDENCY`, `SKIPPED` (with reason), `CONTEXT_GAP` — no unclassified results.
- [ ] `qa/semantic-eval-manifest.json` written with `kind: semantic-csv-eval` and a non-placeholder `outcome`.
- [ ] Database connection string validated; queries run in a transaction rolled back after eval (no side effects).
- [ ] `python3 tools/verify/verify_forge_task.py --task-id <id> --brain <brain>` exits 0.

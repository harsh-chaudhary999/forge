---
name: eval-driver-cache-redis
description: "WHEN: qa-semantic-csv-orchestrate or run_semantic_csv_eval dispatches an automation step that requires Redis cache state verification. Functions: connect(), execute(command), verify(key, assertion), teardown()."
type: rigid
requires: [brain-read]
version: 1.0.1
preamble-tier: 3
triggers:
  - "eval Redis cache"
  - "run cache eval"
  - "Redis eval driver"
allowed-tools:
  - Bash
---

# Eval Driver: Redis Cache (RESP Protocol)

**Runner dispatch:** **`qa-semantic-csv-orchestrate`** / **`run_semantic_csv_eval.py`** routes **`Surface: redis`** rows in **`qa/semantic-automation.csv`** to this driver. Do not invoke this skill directly unless you are implementing or debugging the runner.

Evaluation driver for Redis cache state verification during test execution. Supports Redis RESP protocol, command execution, TTL verification, and atomic assertions.

## HARD-GATE: Anti-Pattern Preambles

### 1. "Just SET and GET — if the key exists, eval passes"
**Why This Fails:**
- TTL expiry during test execution causes key disappearance
- Eviction policy (LRU/LFU) removes key when memory pressure occurs
- Connection interruption loses in-flight SET before durability
- Replica lag causes GET to read stale data from follower
- AOF rewrite or RDB snapshot can trigger brief unavailability

**Enforcement:**
- MUST verify TTL is appropriate for test duration (not shorter than longest operation)
- MUST monitor memory usage and eviction events during eval
- MUST use persistence mode that guarantees durability (AOF or RDB before assertions)
- MUST read from primary replica, not followers
- MUST handle connection timeout gracefully

### 2. "Redis is in-memory so it's always fast"
**Why This Fails:**
- RDB persistence writes to disk (blocking during snapshot, 100ms-1s pauses)
- AOF fsync can block when disk I/O is slow
- Memory pressure triggers swap which degrades performance 100x
- Replication lag means followers lag behind master
- Max-memory eviction policies cause pause when reaching threshold

**Enforcement:**
- MUST set appropriate max-memory-policy (volatile-lru for eval)
- MUST monitor response time and flag latency spikes
- MUST verify persistence mode matches eval requirements
- MUST ensure sufficient memory to prevent swapping
- MUST check master-replica lag with INFO replication

### 3. "Clear all keys before tests using FLUSHALL"
**Why This Fails:**
- FLUSHALL on shared Redis instance deletes production data
- No selectivity — affects all databases if eval uses DB 0
- Concurrent tests race: one test flushes while another reads
- Blocking operation locks Redis for 100ms-10s on large datasets
- No recovery if flush was accidental

**Enforcement:**
- MUST use FLUSHDB (current DB only), not FLUSHALL
- MUST use dedicated eval Redis instance or isolated DB number
- MUST pre-allocate eval DB (e.g., DB 15) and document in eval config
- MUST prefix keys with test identifier to enable selective cleanup
- MUST never use FLUSHALL in shared environment

### 4. "TTL doesn't matter for eval"
**Why This Fails:**
- Key expiration during assertion causes "key not found" false failure
- Incorrect TTL means cache never warms up (expires before consumer uses it)
- EXPIRE command ignored if key doesn't exist yet
- TTL=0 means "persist forever" in some Redis versions
- Millisecond-precision TTL is required for fast assertions

**Enforcement:**
- MUST set TTL longer than max eval runtime + safety margin
- MUST use PEXPIRE (millisecond precision) for sub-second assertions
- MUST verify key still exists before every assertion
- MUST document TTL strategy in eval scenario
- MUST test TTL boundary conditions (key expiring during poll)

### 5. "Skip connection pool teardown, it's automatic"
**Why This Fails:**
- Connection leaks accumulate: next eval hits "max number of clients" error
- Uncommitted transactions block other clients
- Stale locks persist if UNLINK is not called
- Memory buffers in connection pool are never freed
- Client list grows unbounded

**Enforcement:**
- MUST call QUIT or RESET on every connection after eval
- MUST close connection pool explicitly in teardown
- MUST verify client list doesn't grow with `CLIENT LIST`
- MUST delete any locks created during eval (UNLINK + TTL check)
- MUST audit client count before and after eval

---

## Iron Law

```
EVERY CACHE ASSERTION VERIFIES BOTH KEY EXISTENCE AND VALUE — EXISTENCE ALONE IS NOT EVIDENCE. TEARDOWN ALWAYS RUNS AND REMOVES ALL EVAL KEYS.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Assertion checks only that a key exists, not its value** — Key existence without value verification misses TTL-reset bugs, wrong serialization, and stale data. STOP. Verify key value and TTL together.
- **`teardown()` is skipped when eval fails** — Orphaned keys pollute subsequent evals and cause false positives. STOP. Teardown must run unconditionally in a finally block.
- **TTL is not verified after SET** — A key with wrong TTL will expire during the next eval and cause intermittent failures. STOP. Verify TTL immediately after every write that sets expiry.
- **Connection is assumed open without verifying `ping`** — Redis connections drop silently under timeout or network partition. STOP. Always verify connection with `PING` before issuing eval commands.
- **Eval assumes in-memory state from a previous eval** — Evals must be independent. STOP. Always set up required state in the current eval's setup phase.

## Overview

The eval-driver-cache-redis skill provides a complete Redis evaluation framework for:
- Connecting to Redis servers via TCP socket
- Executing Redis commands (GET, SET, DEL, INCR, etc.)
- Verifying cache state with assertions (exists, value match, TTL range)
- Tearing down test keys and connections
- Error handling with descriptive messages
- TTL verification to validate expiration windows

## Installation

```bash
npm install redis
```

Or using Yarn/PNPM:
```bash
yarn add redis
pnpm add redis
```

## Reference (load on demand)

The full API, examples, protocol details, edge-case code, and deep guidance live in
**`reference/redis-reference.md`** (Agent Skills progressive disclosure). This SKILL.md is the operational
contract: runner dispatch, discipline (anti-pattern / iron law / red flags), and decision logic.

## Checklist

- [ ] Unique key prefix generated for this test run
- [ ] Target Redis instance verified (not production)
- [ ] Max-memory-policy appropriate (volatile-lru for eval)
- [ ] Persistence mode understood (AOF/RDB/none)
- [ ] TTL strategy documented (exact vs range vs ignore)
- [ ] Master-replica lag checked (INFO replication)
- [ ] Key type verified before assertions
- [ ] Data presence AND content asserted (not just existence)
- [ ] TTL assertions within expected boundaries
- [ ] Cleanup: DEL or FLUSHDB in teardown
- [ ] Connection pool closed (CLIENT LIST audit)
- [ ] No uncommitted transactions left behind

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] Every scenario step has an entry in `qa/semantic-eval-run.log` (no silent skips).
- [ ] Each step outcome is one of: `PASS`, `FAIL`, `BLOCKED_DEPENDENCY`, `SKIPPED` (with reason), `CONTEXT_GAP` — no unclassified results.
- [ ] `qa/semantic-eval-manifest.json` written with `kind: semantic-csv-eval` and a non-placeholder `outcome`.
- [ ] Redis `PING` returned `PONG` before test; TTL verified via `TTL <key>` command after write.
- [ ] `python3 tools/verify/verify_forge_task.py --task-id <id> --brain <brain>` exits 0.

## Cross-References

- **eval-driver-api-http** — HTTP trigger for cache-busting endpoints
- **eval-product-stack-up** — Bring up Redis before eval
- **qa-semantic-csv-orchestrate** — Coordinate Redis eval with API/DB assertions in **`qa/semantic-automation.csv`**
- **deploy-driver-docker-compose** — Redis service definition
- **reasoning-as-infra** — Cache architecture patterns, TTL tuning, eviction policies
- **contract-cache** — Negotiate cache contracts with services

---

## Summary

**Key Functions:**
- `connect(host, port)` - Establish RESP connection
- `execute(redis, command, args)` - Run Redis commands
- `verify(redis, key, assertion)` - Assert cache state
- `teardown(redis, options)` - Close connection and cleanup

**Supported Assertions:**
- Existence checks
- Value matching (exact, contains, regex)
- TTL range/exact verification
- Type checking
- Collection size verification

**RESP Protocol:** Full Redis Serialization Protocol support for binary-safe operations across all data types.

---
name: eval-driver-cache-redis
description: "WHEN: Eval scenario requires cache state verification against Redis. Functions: connect(), execute(command), verify(key, assertion), teardown()."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers: []
allowed-tools:
  - Bash
---

# Eval Driver: Redis Cache (RESP Protocol)

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

## API Reference

### `connect(host, port) → Promise<RedisClient>`

Establishes a connection to a Redis server using RESP protocol.

**Parameters:**
- `host` (string): Redis server hostname. Default: `'localhost'`
- `port` (number): Redis server port. Default: `6379`

**Returns:** Promise that resolves to a RedisClient instance.

**Example:**
```javascript
const redis = await connect('localhost', 6379)
// or with defaults
const redis = await connect()
```

**Error Handling:**
- Throws error if server is unreachable
- Logs connection details to evaluation context
- Validates RESP protocol handshake

---

### `execute(redis, command, args) → Promise<any>`

Executes a Redis command via RESP protocol.

**Parameters:**
- `redis` (RedisClient): Connected Redis client
- `command` (string): Redis command name (case-insensitive)
- `args` (Array): Command arguments

**Returns:** Promise that resolves to command result.

**Supported Commands:**
- **String Operations:** SET, GET, APPEND, GETRANGE, SETRANGE, STRLEN, INCR, DECR, INCRBY, DECRBY
- **Key Operations:** DEL, EXISTS, EXPIRE, EXPIREAT, TTL, PTTL, KEYS, SCAN, TYPE, RENAME
- **List Operations:** LPUSH, RPUSH, LPOP, RPOP, LLEN, LRANGE, LINDEX, LSET, LTRIM
- **Hash Operations:** HSET, HGET, HMGET, HGETALL, HDEL, HEXISTS, HLEN, HKEYS, HVALS
- **Set Operations:** SADD, SREM, SMEMBERS, SCARD, SISMEMBER, SINTER, SUNION, SDIFF
- **Sorted Set Operations:** ZADD, ZREM, ZRANGE, ZCARD, ZSCORE, ZRANK, ZCOUNT

**Examples:**

```javascript
// String operations
await execute(redis, 'SET', ['user:123:name', 'Alice'])
const name = await execute(redis, 'GET', ['user:123:name'])

// With expiration
await execute(redis, 'SET', ['session:abc', 'token_xyz', 'EX', '3600'])

// Increment
await execute(redis, 'INCR', ['counter:views'])
const count = await execute(redis, 'GET', ['counter:views'])

// List operations
await execute(redis, 'LPUSH', ['queue:tasks', 'task1', 'task2'])
const tasks = await execute(redis, 'LRANGE', ['queue:tasks', '0', '-1'])

// Hash operations
await execute(redis, 'HSET', ['user:123:profile', 'age', '30', 'city', 'NYC'])
const profile = await execute(redis, 'HGETALL', ['user:123:profile'])

// Delete key
await execute(redis, 'DEL', ['user:123:name'])
```

**Error Handling:**
- Throws error on invalid command syntax
- Returns nil/null for non-existent keys
- Propagates Redis server errors

---

### `verify(redis, key, assertion) → Promise<{passed: boolean, actual: any, ttl: number}>`

Verifies cache state with atomic assertions. Returns detailed verification result.

**Parameters:**
- `redis` (RedisClient): Connected Redis client
- `key` (string): Key to verify
- `assertion` (Object): Assertion configuration

**Assertion Properties:**
- `exists` (boolean, optional): Key must exist (true) or not exist (false)
- `value` (any, optional): Exact value match (uses JSON comparison for objects)
- `value_contains` (string, optional): Value must contain this substring
- `value_match` (RegExp, optional): Value must match regex pattern
- `type` (string, optional): Key type (string, list, hash, set, zset, none)
- `ttl_min` (number, optional): TTL must be >= this value (seconds)
- `ttl_max` (number, optional): TTL must be <= this value (seconds)
- `ttl_range` (Array<number>, optional): TTL must be in [min, max] range
- `ttl_exact` (number, optional): TTL must be exactly this value (±1 second tolerance)
- `length` (number, optional): List/Hash/Set size must equal this
- `length_min` (number, optional): Collection size must be >= this
- `length_max` (number, optional): Collection size must be <= this
- `description` (string, optional): Human-readable assertion description

**Returns:** Promise resolving to:
```javascript
{
  passed: boolean,           // Assertion passed
  actual: any,              // Actual value or null if key doesn't exist
  ttl: number,              // TTL in seconds (-1 if no expiration, -2 if key doesn't exist)
  type: string,             // Key type
  length: number,           // Collection length if applicable
  details: string           // Detailed assertion result
}
```

**Examples:**

```javascript
// Verify key exists
const result = await verify(redis, 'user:123:name', {
  exists: true,
  description: 'User name should exist'
})

// Verify exact value
const result = await verify(redis, 'user:123:name', {
  value: 'Alice',
  description: 'User name must be Alice'
})

// Verify value contains substring
const result = await verify(redis, 'user:123:email', {
  value_contains: '@example.com',
  description: 'Email must be from example.com domain'
})

// Verify TTL range
const result = await verify(redis, 'session:abc', {
  exists: true,
  ttl_range: [295, 305],
  description: 'Session should expire in 5 minutes (±5 sec tolerance)'
})

// Verify TTL exact
const result = await verify(redis, 'otp:123', {
  ttl_exact: 300,
  description: '2FA code must expire in exactly 5 minutes'
})

// Verify collection size
const result = await verify(redis, 'queue:tasks', {
  type: 'list',
  length: 3,
  description: 'Queue must have exactly 3 tasks'
})

// Complex assertion
const result = await verify(redis, 'user:123:2fa_codes', {
  exists: true,
  type: 'string',
  ttl_range: [295, 305],
  value_contains: 'codes',
  description: '2FA codes should exist with 5min TTL'
})

if (!result.passed) {
  console.error(`Assertion failed: ${result.details}`)
  console.error(`Actual value: ${result.actual}, TTL: ${result.ttl}s`)
}
```

**Verification Logic:**
1. Check key existence
2. Fetch TTL (PTTL for precision)
3. Verify type if specified
4. Verify value assertions
5. Verify TTL assertions
6. Return detailed result

---

### `teardown(redis) → Promise<void>`

Closes Redis connection and optionally flushes test keys.

**Parameters:**
- `redis` (RedisClient): Connected Redis client

**Options (optional):**
- `flush` (boolean): Flush all test database keys. Default: false
- `keys` (Array<string>): Specific keys to delete. Default: []

**Examples:**

```javascript
// Close connection only
await teardown(redis)

// Close and delete specific test keys
await teardown(redis, {
  keys: ['user:123:name', 'user:123:email', 'session:abc']
})

// Close and flush test database
await teardown(redis, {
  flush: true
})
```

**Behavior:**
- Gracefully closes RESP connection
- Deletes specified keys if provided
- Flushes database if flush=true
- Logs teardown completion

---

## RESP Protocol Implementation

The eval-driver uses Redis Serialization Protocol (RESP) for communication:

**RESP Data Types:**
- **Simple Strings:** +OK\r\n
- **Errors:** -ERR error message\r\n
- **Integers:** :1000\r\n
- **Bulk Strings:** $6\r\nfoobar\r\n
- **Arrays:** *2\r\n$3\r\nGET\r\n$3\r\nkey\r\n

**Command Format:**
All commands use RESP Array format:
```
*<number-of-args>\r\n
$<length-of-arg-1>\r\n
<arg-1>\r\n
...
```

The driver automatically encodes/decodes RESP format for all operations.

---

## Usage Patterns

### Pattern 1: Single Key Verification

```javascript
const redis = await connect('localhost', 6379)

// Set a value
await execute(redis, 'SET', ['counter', '42'])

// Verify it
const result = await verify(redis, 'counter', {
  value: '42',
  description: 'Counter should be 42'
})

assert(result.passed, result.details)
await teardown(redis)
```

### Pattern 2: TTL-Based Verification

```javascript
const redis = await connect()

// Set with expiration
await execute(redis, 'SET', ['otp:123', '654321', 'EX', '300'])

// Verify TTL window
const result = await verify(redis, 'otp:123', {
  exists: true,
  value: '654321',
  ttl_range: [295, 305],
  description: 'OTP should expire in ~5 minutes'
})

assert(result.passed)
await teardown(redis)
```

### Pattern 3: Multi-Key Workflow

```javascript
const redis = await connect()

// Execute multi-step workflow
await execute(redis, 'SET', ['user:123:profile:name', 'Alice'])
await execute(redis, 'SET', ['user:123:profile:email', 'alice@example.com'])
await execute(redis, 'SET', ['user:123:profile:verified', '1', 'EX', '3600'])

// Batch verify
const verifications = await Promise.all([
  verify(redis, 'user:123:profile:name', {
    value: 'Alice',
    description: 'User name must be Alice'
  }),
  verify(redis, 'user:123:profile:email', {
    value_contains: '@example.com',
    description: 'Email must be valid domain'
  }),
  verify(redis, 'user:123:profile:verified', {
    exists: true,
    ttl_min: 3590,
    description: 'Verification flag with TTL'
  })
])

const allPassed = verifications.every(v => v.passed)
assert(allPassed, `Some assertions failed: ${verifications.map(v => v.details).join(', ')}`)

await teardown(redis, {
  keys: ['user:123:profile:name', 'user:123:profile:email', 'user:123:profile:verified']
})
```

### Pattern 4: Collection Verification

```javascript
const redis = await connect()

// Build collection
await execute(redis, 'LPUSH', ['notifications:queue', 'msg1', 'msg2', 'msg3'])

// Verify collection state
const result = await verify(redis, 'notifications:queue', {
  type: 'list',
  length: 3,
  description: 'Notification queue should have 3 messages'
})

assert(result.passed)

// Get content and verify
const messages = await execute(redis, 'LRANGE', ['notifications:queue', '0', '-1'])
assert(messages.length === 3, 'Expected 3 messages')

await teardown(redis, {
  keys: ['notifications:queue']
})
```

### Pattern 5: Conditional Verification

```javascript
const redis = await connect()

// Set conditional data
await execute(redis, 'SET', ['feature:beta:enabled', '1', 'EX', '1800'])

// Verify with optional conditions
const result = await verify(redis, 'feature:beta:enabled', {
  exists: true,
  type: 'string',
  value_match: /^[01]$/,
  ttl_min: 1790,
  description: 'Feature flag should be set and expire soon'
})

if (result.passed) {
  // Feature is enabled in cache
  console.log('Beta feature is active in cache')
} else {
  // Feature is missing or misconfigured
  console.error('Beta feature config invalid:', result.details)
}

await teardown(redis)
```

---

## Error Handling

### Connection Errors

```javascript
try {
  const redis = await connect('unreachable.host', 6379)
} catch (error) {
  console.error('Connection failed:', error.message)
  // Handle connection failure (e.g., Redis not running)
}
```

### Assertion Failures

```javascript
const result = await verify(redis, 'missing_key', {
  exists: true,
  description: 'Key should exist'
})

if (!result.passed) {
  console.error('Assertion failed:')
  console.error(`  Expected: key exists`)
  console.error(`  Actual: TTL=${result.ttl}, Exists=${result.ttl !== -2}`)
  console.error(`  Details: ${result.details}`)
}
```

### Command Errors

```javascript
try {
  // Invalid command
  await execute(redis, 'INVALID', ['key'])
} catch (error) {
  console.error('Command error:', error.message)
  // Handle invalid command
}

try {
  // Invalid operation (e.g., LPUSH on string)
  await execute(redis, 'SET', ['mykey', 'value'])
  await execute(redis, 'LPUSH', ['mykey', 'item']) // WRONGTYPE Error
} catch (error) {
  console.error('Type error:', error.message)
}
```

### Verification Timeout

```javascript
const timeout = new Promise((_, reject) =>
  setTimeout(() => reject(new Error('Verification timeout')), 5000)
)

try {
  const result = await Promise.race([
    verify(redis, 'key', { exists: true }),
    timeout
  ])
} catch (error) {
  console.error('Verification took too long:', error.message)
}
```

---

## Testing Redis with Multiple Data Types

```javascript
const redis = await connect()

// String
await execute(redis, 'SET', ['str:key', 'hello'])

// List
await execute(redis, 'RPUSH', ['list:key', 'a', 'b', 'c'])

// Hash
await execute(redis, 'HSET', ['hash:key', 'field1', 'value1', 'field2', 'value2'])

// Set
await execute(redis, 'SADD', ['set:key', 'member1', 'member2'])

// Sorted Set
await execute(redis, 'ZADD', ['zset:key', '1', 'one', '2', 'two'])

// Verify all types
const verifications = await Promise.all([
  verify(redis, 'str:key', { type: 'string', value: 'hello' }),
  verify(redis, 'list:key', { type: 'list', length: 3 }),
  verify(redis, 'hash:key', { type: 'hash', length: 2 }),
  verify(redis, 'set:key', { type: 'set', length: 2 }),
  verify(redis, 'zset:key', { type: 'zset', length: 2 })
])

assert(verifications.every(v => v.passed), 'All type verifications should pass')

await teardown(redis, {
  keys: ['str:key', 'list:key', 'hash:key', 'set:key', 'zset:key']
})
```

---

## Advanced: Custom Assertion Composition

```javascript
async function verifySessionValid(redis, sessionId) {
  return verify(redis, `session:${sessionId}`, {
    exists: true,
    type: 'hash',
    ttl_min: 0,  // Must have TTL set
    description: `Session ${sessionId} must be valid and not expired`
  })
}

async function verifyCacheWarmup(redis, cacheKey) {
  const result = await verify(redis, cacheKey, {
    exists: true,
    value_match: /.*/, // Any non-empty value
    ttl_range: [0, 86400], // 0 to 24 hours
    description: `Cache ${cacheKey} must be warmed up`
  })
  
  return {
    ...result,
    isCold: result.ttl > 43200, // Over 12 hours
    isExpiringSoon: result.ttl < 3600 // Under 1 hour
  }
}

// Usage
const redis = await connect()
const sessionValid = await verifySessionValid(redis, 'user123')
const cacheState = await verifyCacheWarmup(redis, 'product:456')

if (cacheState.isCold) {
  console.warn('Cache is getting stale, may need refresh')
}
```

---

## Integration with Evaluation Framework

This skill integrates with the broader Forge evaluation framework:

- **brain-read:** Lookup cache contracts and TTL policies
- **eval-driver-api-http:** Verify API responses match cached values
- **contract-cache:** Reference Redis key patterns and TTL strategies

---

## Debugging Tips

1. **Connection Issues:**
   - Verify Redis is running: `redis-cli ping`
   - Check host/port configuration
   - Review firewall rules

2. **Command Failures:**
   - Check command syntax against Redis documentation
   - Verify key types match operations (no LPUSH on strings)
   - Use KEYS pattern to explore cache contents

3. **TTL Verification:**
   - Remember TTL is in seconds, PTTL in milliseconds
   - TTL=-1 means key has no expiration
   - TTL=-2 means key doesn't exist
   - Use ttl_range for tolerance around expected expiration

4. **Network Issues:**
   - Use connection pooling for multiple operations
   - Handle timeouts gracefully
   - Implement retry logic for transient failures

---

## Edge Cases with Mitigation

### Edge Case 1: Key Evicted During Test Run
**Scenario:** Key is SET successfully, then during test execution, memory pressure triggers eviction and the key disappears.

**Symptom:** GET returns nil after SET succeeded 2 seconds earlier. `INFO memory` shows used_memory near maxmemory.

**Do NOT:** Assume SET failed — the key was evicted after success.

**Mitigation:**
1. Check eviction policy: `CONFIG GET maxmemory-policy`
2. If using allkeys-lru: either delete test keys before assertions, or monitor memory
3. Set high max-memory limit for eval (sufficient for test data + Redis overhead)
4. Use PERSIST key before assertion to remove TTL
5. If persistent: implement custom eviction callback to skip eval-prefixed keys

**Escalation:** `NEEDS_INFRA_CHANGE` if maxmemory-policy is wrong or max-memory is too low.

---

### Edge Case 2: Redis Cluster Redirect (MOVED error)
**Scenario:** Eval uses Redis Cluster but client is not configured for cluster mode.

**Symptom:** `MOVED 1234 127.0.0.1:6380` error on first command. Client needs to redirect to correct slot.

**Do NOT:** Retry same slot — MOVED means the key is on a different node.

**Mitigation:**
1. Enable cluster mode in Redis client: `cluster: { nodes: [...] }`
2. Client automatically follows MOVED redirects
3. Verify cluster topology before eval: `CLUSTER NODES`
4. Verify test keys hash to same slot (use CRC16 calculator if needed)
5. For single-node eval: disable cluster mode

**Escalation:** `NEEDS_CONTEXT` — clarify whether eval is against cluster or standalone.

---

### Edge Case 3: Type Mismatch (WRONGTYPE error)
**Scenario:** Eval expects string value but previous test left a hash or list at that key.

**Symptom:** `WRONGTYPE Operation against a key holding the wrong kind of value` on GET after SET.

**Do NOT:** Assume key doesn't exist — it exists but has wrong type.

**Mitigation:**
1. DEL key before SET to clear previous value
2. Check key type before read: `TYPE key`
3. Use unique key names per test to avoid collision
4. Add type assertion: verify TYPE returns "string" before GET
5. In setup: scan for test keys and verify they match expected type

**Escalation:** `BLOCKED` if type mismatch persists after DEL — indicates shared key namespace collision.

---

### Edge Case 4: Persistence Write Delay
**Scenario:** Eval uses SAVE or BGSAVE for durability. The write blocks or delays completion.

**Symptom:** `Background saving started` on BGSAVE, but value doesn't appear in RDB until 1-10s later.

**Do NOT:** Assume value is durable immediately after SET.

**Mitigation:**
1. Use WAIT command for synchronous replication acknowledgment
2. For AOF persistence: `CONFIG SET appendfsync always` before eval
3. After critical SET: poll `LASTSAVE` to verify snapshot includes the key
4. Check `BGSAVE` status: `BGSAVE` returns immediately, verify completion via `LASTSAVE` polling
5. Use transactional approach: WATCH/MULTI/EXEC for multi-key consistency

**Escalation:** `NEEDS_INFRA_CHANGE` if persistence is required but not configured correctly.

---

### Edge Case 5: Lua Script Timeout
**Scenario:** Eval runs Lua script that blocks Redis execution.

**Symptom:** `BUSY Redis is busy running a script` — subsequent commands fail until script completes.

**Do NOT:** Retry the command while script is still running.

**Mitigation:**
1. If script hangs: use SCRIPT KILL command
2. Set EVAL timeout: `CONFIG SET lua-time-limit 1000` (1s max per script)
3. Redesign assertion as pipeline instead of Lua (faster, no blocking)
4. Break multi-key assertion into separate WATCH/MULTI/EXEC transactions
5. Add timeout wrapper: run script in separate thread with abort on timeout

**Escalation:** `NEEDS_COORDINATION` — investigate why Lua script is hanging.

---

### Edge Case 6: Keyspace Notification Race
**Scenario:** Eval subscribes to key expiration notifications (keyspace events) but misses the expiration event.

**Symptom:** Key expired but notification never arrived. Or: notification arrives after assertion already ran.

**Do NOT:** Assume keyspace notifications are synchronous.

**Mitigation:**
1. Subscribe to keyspace events BEFORE setting key with TTL
2. Use blocking POP pattern instead of notifications (more reliable)
3. Enable keyspace events: `CONFIG SET notify-keyspace-events Ex` (keyspace + expiration events)
4. Set TTL margin: expiration notification may arrive 50-500ms after actual expiry
5. Add timeout to notification listener: if no notification after TTL+1s, assume key expired

**Escalation:** `BLOCKED` if keyspace notifications are unreliable — switch to polling approach.

---

## Decision Trees and Patterns

### Decision Tree 1: Cache Isolation Strategy

```
HOW SHOULD THIS EVAL USE REDIS?
│
├── Shared Redis instance (staging/production-like)
│   ├── Need to isolate eval keys from other services
│   │   └── STRATEGY: unique DB number (e.g., DB 15 reserved for eval)
│   │       CONFIG: SELECT 15, use FLUSHDB not FLUSHALL, prefix keys
│   │
│   └── Need concurrent evals to not interfere
│       └── STRATEGY: key prefix by test ID
│           CONFIG: prefix keys with eval-{uuid}, cleanup with UNLINK pattern
│
├── Dedicated eval Redis instance
│   ├── Single eval at a time
│   │   └── STRATEGY: FLUSHDB before eval, DEL after
│   │       CONFIG: use default DB 0, cleanup is simple
│   │
│   └── Concurrent evals
│       └── STRATEGY: multiple Redis instances OR dedicated DB per eval
│           CONFIG: start Redis in Docker with unique port per eval
│
└── In-memory mock (no persistence)
    └── STRATEGY: simpler API, trade-off: no persistence testing
        CONFIG: use mock library (fakeredis), no network latency
```

---

### Decision Tree 2: TTL Assertion Approach

```
HOW SHOULD EVAL VERIFY TTL?
│
├── TTL must be exact (e.g., countdown timer)
│   └── STRATEGY: PTTL (millisecond precision), poll within range
│       VERIFY: TTL decreases over time, KEY not yet expired
│
├── TTL must be within a range (e.g., cache expires in 5±1 minutes)
│   └── STRATEGY: set TTL, wait margin, then assert still exists
│       VERIFY: PTTL > expected_min, PTTL < expected_max
│
├── TTL must NOT expire during eval (persistent cache)
│   └── STRATEGY: PERSIST key before assertions
│       VERIFY: TTL -1 means no expiration
│
└── Eval does NOT care about TTL (cache warming only)
    └── STRATEGY: ignore TTL, focus on data presence
        VERIFY: GET succeeds, no TTL assertion
```

---

## Common Pitfalls

### Pitfall 1: Using FLUSHALL on Shared Redis
**Mistake:** Eval runs FLUSHALL to clear previous test data.
```
// WRONG
await redis.FLUSHALL();
```

**Fix:** Use FLUSHDB with dedicated DB number.
```
// CORRECT
await redis.SELECT(15); // dedicated eval DB
await redis.FLUSHDB();
```

---

### Pitfall 2: Not Waiting for AOF fsync Before Read Assertion
**Mistake:** SET completes, but AOF hasn't fsynced to disk yet.
```
// WRONG
await redis.SET('key', 'value');
const val = await redis.GET('key'); // may be correct but not durable
```

**Fix:** Use WAIT for replication durability.
```
// CORRECT
await redis.SET('key', 'value');
await redis.WAIT(1, 1000); // wait for 1 replica with 1s timeout
const val = await redis.GET('key');
```

---

### Pitfall 3: Asserting Full HGETALL Without Accounting for Field Ordering
**Mistake:** Hash field order is non-deterministic across Redis versions.
```
// WRONG
const result = await redis.HGETALL('hash-key');
assert.deepEqual(result, {field1: 'a', field2: 'b'}); // fails on different order
```

**Fix:** Check field presence, not order.
```
// CORRECT
const result = await redis.HGETALL('hash-key');
assert.equal(result['field1'], 'a');
assert.equal(result['field2'], 'b');
assert.equal(Object.keys(result).length, 2);
```

---

### Pitfall 4: Missing DISCARD on MULTI/EXEC Failure in Teardown
**Mistake:** Transaction is started but never completed.
```
// WRONG
const cleanup = async () => {
  await redis.MULTI();
  await redis.DEL('key1');
  // error happens — EXEC never called, transaction abandoned
};
```

**Fix:** Always complete or abort transaction.
```
// CORRECT
const cleanup = async () => {
  await redis.MULTI();
  try {
    await redis.DEL('key1');
    await redis.EXEC();
  } catch (e) {
    await redis.DISCARD();
    throw e;
  }
};
```

---

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

## Cross-References

- **eval-driver-api-http** — HTTP trigger for cache-busting endpoints
- **eval-product-stack-up** — Bring up Redis before eval
- **eval-coordinate-multi-surface** — Coordinate Redis eval with API/DB assertions
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

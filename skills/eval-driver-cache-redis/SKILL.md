---
name: eval-driver-cache-redis
description: Eval driver for Redis via RESP protocol. Functions: connect(), execute(command), verify(key, assertion), teardown().
type: rigid
requires: [brain-read]
---

# Eval Driver: Redis Cache (RESP Protocol)

Evaluation driver for Redis cache state verification during test execution. Supports Redis RESP protocol, command execution, TTL verification, and atomic assertions.

## Anti-Pattern Preamble: Cache Eval Failures You Will Hit

| Rationalization | The Truth |
|---|---|
| "Cache is just key-value, nothing can go wrong" | Redis has 6+ data types, TTL semantics, eviction policies, and cluster routing. A key existing doesn't mean it has the right value, type, or TTL. Verify all three. |
| "TTL doesn't matter for eval" | TTL IS the contract. A cache entry with wrong TTL means stale data in production or premature eviction under load. Always verify TTL within expected range, not just existence. |
| "We can skip cache verification if API tests pass" | API success with wrong cache state means the next request will serve stale data. Cache verification catches write-through failures, invalidation bugs, and TTL drift that API tests cannot see. |
| "Redis is local so it's always fast" | Local Redis still has connection overhead, pipeline latency, and Lua script execution time. In eval, connection pool exhaustion and AUTH failures are real. Always set timeouts. |
| "FLUSHDB before each test is fine" | FLUSHDB destroys other tests' state if running in parallel. Use namespaced keys with deterministic cleanup. Never flush in shared environments. |

---

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

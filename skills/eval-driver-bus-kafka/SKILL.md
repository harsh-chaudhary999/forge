---
name: eval-driver-bus-kafka
description: "WHEN: Eval scenario requires Kafka message verification. Functions: connect(), produce(topic, message), consume(topic, assertion), verify(topic, schema), teardown()."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers:
  - "eval Kafka bus"
  - "run Kafka eval"
  - "event bus eval"
allowed-tools:
  - Bash
---

# eval-driver-bus-kafka

Evaluation driver for Apache Kafka using the wire protocol. Produces and consumes messages during evaluation, with support for offset management, message verification, schema validation, and idempotency checks.

## Anti-Pattern Preamble: Kafka Eval Failures You Will Hit

| Rationalization | The Truth |
|---|---|
| "Just check if the message was produced" | Production confirmation means the broker accepted the message. It does NOT mean the consumer received it, processed it, or committed the offset. Verify the full produce→consume→process chain. |
| "Message ordering doesn't matter in eval" | Kafka guarantees ordering within a partition. If your eval ignores partition assignment, you'll see messages out of order and blame the code. Always specify partition keys and verify ordering within partition. |
| "Consumer group offsets will auto-reset" | `auto.offset.reset` only applies when no committed offset exists. If a previous test committed offsets, your consumer starts AFTER those offsets and misses messages. Always manage offsets explicitly in eval. |
| "Schema validation is optional for testing" | Schema drift between producer and consumer is the #1 cause of silent data corruption. If eval doesn't validate schemas, you ship incompatible message formats. Always verify against registered schema. |
| "Timeouts don't matter, Kafka is fast" | Kafka consumer poll has a timeout that determines how long to wait for messages. Too short = false "no messages" result. Too long = slow tests. Set consume timeout to 2-3x your expected produce-to-consume latency. |
| "We can share topics across tests" | Shared topics mean one test's messages pollute another's assertions. Use unique topic names per test or unique consumer groups with explicit offset management. |

---

## Iron Law

```
TEARDOWN ALWAYS RUNS — EVEN WHEN EVAL FAILS. NO ORPHANED CONSUMER GROUPS OR UNCOMMITTED OFFSETS SURVIVE AFTER EVAL COMPLETES.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Consumer is polled without resetting offsets to the start of the eval run** — If a previous scenario committed offsets on this topic, the consumer starts after those messages and silently "misses" the messages produced in the current scenario. STOP. Always seek to the beginning of the relevant offset range before consuming in eval.
- **`teardown()` is not called after scenario completion** — An unclosed Kafka consumer with uncommitted offsets leaves the consumer group in an inconsistent state for the next run. STOP. `teardown()` must always be called to close consumers, flush producers, and release connections.
- **Scenario asserts "message received" without verifying message content** — A message arriving is not the same as the correct message arriving. A stale message from a prior run can satisfy an existence assertion. STOP. Every `consume()` assertion must verify the message payload, key, and schema — not just that a message exists.
- **Topic used in eval was not created with explicit partition count** — Auto-created topics may use broker defaults that don't match the partition strategy required by the consumer group, causing message distribution to be unpredictable. STOP. Verify the topic exists with the expected partition count before producing.
- **Schema validation is skipped because "we're just testing the flow"** — Schema drift is invisible at the flow level. A producer sending a v2 schema while the consumer expects v1 produces silent data corruption, not a test failure. STOP. Always call `verify(topic, schema)` as part of every produce/consume cycle.
- **Consumer timeout is shorter than the produce-to-consume propagation time** — If the consumer polls before the producer's message has been replicated to the partition the consumer is reading, it times out and reports "no messages" — a false failure. STOP. Set consume timeout to at least 3x the expected end-to-end propagation latency.

## Overview

This skill provides a complete evaluation harness for Kafka-based event-driven systems. It enables:
- Connection to Kafka brokers (local or remote)
- Message production with optional partition keys
- Message consumption with timeout handling
- Message verification with schema and idempotency validation
- Graceful teardown and resource cleanup

## Functions

### connect(brokers) → kafka

Establish a connection to Kafka broker(s).

**Parameters:**
- `brokers` (string[]): Array of broker addresses (e.g., `['localhost:9092']` or `['kafka1:9092', 'kafka2:9092']`)

**Returns:**
- `kafka` (object): Kafka client instance with connection state

**Throws:**
- `KafkaConnectionError`: If unable to connect to any broker after retries

**Example:**
```javascript
const kafka = await connect(['localhost:9092'])
// or for cluster:
const kafka = await connect(['kafka1:9092', 'kafka2:9092', 'kafka3:9092'])
```

**Implementation Details:**
- Establishes TCP connection to broker(s)
- Implements exponential backoff (max 3 retries, 500ms initial delay)
- Validates broker availability via metadata request
- Stores offset tracking state for consumption

---

### produce(kafka, topic, message, key?) → {offset: number}

Send a message to a Kafka topic.

**Parameters:**
- `kafka` (object): Kafka client from `connect()`
- `topic` (string): Topic name (auto-created if allowed by broker)
- `message` (object|string): Message payload (JSON serialized if object)
- `key` (string|null, optional): Partition key for routing. If omitted, round-robin by partition

**Returns:**
- `{offset: number}`: Object containing:
  - `offset`: Broker-assigned offset in target partition
  - `partition`: Partition message was written to
  - `timestamp`: Broker timestamp (ms since epoch)

**Throws:**
- `KafkaProduceError`: If broker rejects message or network error
- `SerializationError`: If message cannot be serialized to JSON

**Example:**
```javascript
const result = await produce(kafka, 'user-lifecycle', {
  user_id: '123',
  event: 'user.2fa_enabled',
  timestamp: Date.now(),
  idempotency_id: 'evt_789abc'
})
// result: { offset: 42, partition: 1, timestamp: 1712761234567 }

// With partition key:
const result2 = await produce(kafka, 'user-lifecycle', {
  user_id: '456',
  event: 'user.login'
}, '456')  // key ensures all user_id 456 events go to same partition
```

**Implementation Details:**
- Serializes message to JSON with UTF-8 encoding
- Sends Produce API v1+ request
- Handles broker acknowledgment (waits for min.insync.replicas acks)
- Returns immediately after broker confirmation
- Implements compression if topic broker supports it

---

### consume(kafka, topic, timeout_ms) → {messages: [], highWaterMark: number}

Read messages from a topic starting from the latest committed offset.

**Parameters:**
- `kafka` (object): Kafka client from `connect()`
- `topic` (string): Topic name
- `timeout_ms` (number): Max wait time for messages (0 = return immediately with available messages)

**Returns:**
- `{messages: [], highWaterMark: number}`: Object containing:
  - `messages[]` (array of objects):
    - `offset`: Message offset
    - `partition`: Partition number
    - `key`: Message key (null if not set)
    - `value`: Deserialized message object/string
    - `timestamp`: Broker timestamp (ms)
    - `headers`: Map of message headers
  - `highWaterMark`: Latest offset in topic (may be ahead of consumed messages)

**Throws:**
- `KafkaConsumeError`: If connection lost during consumption
- `DeserializationError`: If message value cannot be parsed as JSON

**Example:**
```javascript
const messages = await consume(kafka, 'user-lifecycle', 5000)
// Returns messages received within 5 seconds
// messages.messages[0] = { offset: 42, partition: 1, value: {...}, timestamp: 1712761234567 }

// Poll with no wait (get available immediately):
const immediate = await consume(kafka, 'user-lifecycle', 0)
```

**Implementation Details:**
- Fetches from first unconsumed offset (tracked per topic/partition)
- Sends Fetch API v0+ request
- Polls up to `timeout_ms` or until broker has data
- Handles broker socket timeout gracefully
- Auto-advances offset tracking after successful read
- Returns empty array if no new messages available

---

### verify(kafka, topic, assertion) → {passed: bool, messages: [], details: {}}

Verify message(s) exist in topic matching assertion criteria.

**Parameters:**
- `kafka` (object): Kafka client from `connect()`
- `topic` (string): Topic name
- `assertion` (object): Verification criteria:
  - `event_type` (string, optional): Match message.event_type field
  - `user_id` (string, optional): Match message.user_id field
  - `idempotency_id` (string, optional): Match message.idempotency_id (ensures exactly-once processing)
  - `schema` (object, optional): JSON schema to validate message against
  - `description` (string): Human description of what's being verified
  - `count` (number, optional): Exact number of matching messages expected (default: >=1)

**Returns:**
- `{passed: bool, messages: [], details: {}}`: Object containing:
  - `passed`: True if assertion matched
  - `messages[]`: All messages matching the assertion
  - `details`:
    - `matchCount`: Number of matches found
    - `totalMessages`: Total messages scanned in topic
    - `schemaErrors`: Array of schema validation errors (if any)
    - `idempotencyCheck`: "duplicate" | "unique" | "not_found"

**Throws:**
- `VerificationError`: If assertion format is invalid
- `SchemaValidationError`: If schema parameter is malformed JSON schema

**Example:**
```javascript
const verified = await verify(kafka, 'user-lifecycle', {
  event_type: 'user.2fa_enabled',
  user_id: '123',
  idempotency_id: 'evt_789abc',
  description: '2FA enabled event should be in topic with correct idempotency_id'
})
// verified.passed = true
// verified.details.idempotencyCheck = "unique"

// With schema validation:
const schemaVerify = await verify(kafka, 'user-lifecycle', {
  event_type: 'user.2fa_enabled',
  schema: {
    type: 'object',
    required: ['user_id', 'event_type', 'timestamp'],
    properties: {
      user_id: { type: 'string' },
      event_type: { type: 'string' },
      timestamp: { type: 'number' }
    }
  },
  count: 1,
  description: 'Exactly one valid 2FA event'
})
```

**Implementation Details:**
- Scans topic partition(s) from beginning (or last verified offset)
- Matches messages using field equality
- Validates each message against JSON schema if provided
- Tracks idempotency_id to detect duplicates (returns "duplicate" if id seen before)
- Caches verification results to avoid re-scanning
- Supports wildcard matching for event_type (e.g., "user.*")

---

### teardown(kafka) → void

Disconnect from Kafka and clean up resources.

**Parameters:**
- `kafka` (object): Kafka client from `connect()`

**Returns:**
- Nothing (void)

**Throws:**
- `KafkaDisconnectError`: If already disconnected or timeout during graceful shutdown

**Example:**
```javascript
await teardown(kafka)
// All connections closed, resources released
```

**Implementation Details:**
- Commits final offsets to broker
- Closes all open sockets
- Cancels pending produce/consume operations
- Releases memory for offset tracking
- Safe to call multiple times (idempotent)
- Implements 5s graceful shutdown window

---

## Error Handling

All functions follow standard error convention:

```javascript
try {
  const kafka = await connect(['localhost:9092'])
  const produced = await produce(kafka, 'test', { data: 'value' })
  const consumed = await consume(kafka, 'test', 3000)
  const verified = await verify(kafka, 'test', { data: 'value' })
  await teardown(kafka)
} catch (error) {
  if (error.name === 'KafkaConnectionError') {
    console.error('Failed to connect to broker', error.brokers)
  } else if (error.name === 'KafkaProduceError') {
    console.error('Message rejected by broker', error.reason)
  } else if (error.name === 'KafkaConsumeError') {
    console.error('Consumption failed', error.message)
  } else if (error.name === 'VerificationError') {
    console.error('Assertion failed', error.assertion)
  }
}
```

**Error Types:**
- `KafkaConnectionError`: Broker unreachable, invalid brokers array
- `KafkaProduceError`: Message too large, serialization failed, broker rejected
- `KafkaConsumeError`: Connection lost, corrupted message
- `VerificationError`: Assertion format invalid, no matches
- `SchemaValidationError`: Schema is not valid JSON schema
- `DeserializationError`: Message value is not valid JSON
- `SerializationError`: Message object cannot be converted to JSON
- `KafkaDisconnectError`: Already disconnected or shutdown timeout

---

## Offset Management

The Kafka client maintains offset state per-topic to enable incremental consumption:

1. **Initial Offset**: First `consume()` call reads from latest offset (newly produced messages)
2. **Tracking**: After successful consumption, offset is advanced
3. **Persistence**: Offsets are committed to broker (enables recovery if client crashes)
4. **Reset**: Call `connect()` again to reset offset tracking to latest

```javascript
const kafka = await connect(['localhost:9092'])

// Produce message
await produce(kafka, 'test', { seq: 1 })

// Consume it
const msg1 = await consume(kafka, 'test', 1000)  // Gets seq:1

// Produce another
await produce(kafka, 'test', { seq: 2 })

// Consume again - gets seq:2 (not seq:1 again)
const msg2 = await consume(kafka, 'test', 1000)  // Gets seq:2

await teardown(kafka)
```

---

## Schema Validation

JSON schema validation is performed during `verify()`:

```javascript
const assertion = {
  schema: {
    $schema: 'http://json-schema.org/draft-07/schema#',
    type: 'object',
    required: ['user_id', 'event_type', 'timestamp'],
    properties: {
      user_id: { type: 'string', minLength: 1 },
      event_type: { type: 'string', enum: ['user.2fa_enabled', 'user.2fa_disabled'] },
      timestamp: { type: 'number', minimum: 0 },
      metadata: {
        type: 'object',
        properties: {
          source: { type: 'string' }
        }
      }
    },
    additionalProperties: true
  }
}

const result = await verify(kafka, 'user-lifecycle', assertion)
if (!result.passed) {
  result.details.schemaErrors.forEach(err => {
    console.error(`Schema error: ${err.path} - ${err.message}`)
  })
}
```

---

## Idempotency Verification

Detect duplicate messages using idempotency_id field:

```javascript
const idempotency_id = 'evt_unique_123'

// Produce with idempotency_id
await produce(kafka, 'events', {
  user_id: '456',
  action: 'subscribe',
  idempotency_id
})

// Verify uniqueness
const result = await verify(kafka, 'events', {
  idempotency_id,
  description: 'Idempotency check'
})

console.log(result.details.idempotencyCheck)
// "unique" = not a duplicate
// "duplicate" = this id already exists in topic
// "not_found" = no message with this id
```

---

## Complete Workflow Example

```javascript
const kafka = await connect(['localhost:9092'])

try {
  // 1. Produce a user lifecycle event
  const produced = await produce(kafka, 'user-lifecycle', {
    user_id: 'user_789',
    event: 'user.2fa_enabled',
    timestamp: Date.now(),
    idempotency_id: 'evt_abc123'
  }, 'user_789')  // partition key = user_id
  
  console.log(`Message produced at offset ${produced.offset}`)

  // 2. Consume messages from topic
  const consumed = await consume(kafka, 'user-lifecycle', 5000)
  console.log(`Consumed ${consumed.messages.length} messages`)

  // 3. Verify the event exists with correct schema
  const verified = await verify(kafka, 'user-lifecycle', {
    user_id: 'user_789',
    event_type: 'user.2fa_enabled',
    idempotency_id: 'evt_abc123',
    schema: {
      type: 'object',
      required: ['user_id', 'event', 'timestamp', 'idempotency_id'],
      properties: {
        user_id: { type: 'string' },
        event: { type: 'string' },
        timestamp: { type: 'number' },
        idempotency_id: { type: 'string' }
      }
    },
    description: '2FA enabled event should exist with valid schema and unique idempotency_id'
  })

  if (verified.passed) {
    console.log(`✓ Verification passed (${verified.details.matchCount} match)`)
    console.log(`✓ Idempotency: ${verified.details.idempotencyCheck}`)
  } else {
    console.log(`✗ Verification failed`)
  }

} finally {
  await teardown(kafka)
}
```

---

## Wire Protocol Implementation

This skill uses Kafka protocol v1+ for compatibility:

- **Connect**: ApiVersion request to detect broker capabilities
- **Produce**: Produce API (v1+) with required acks
- **Consume**: Fetch API (v0+) with configurable max_bytes
- **Metadata**: Metadata API to discover partitions and brokers
- **Offsets**: OffsetCommit/OffsetFetch APIs for tracking

All requests include:
- Client ID: "eval-driver-bus-kafka"
- Correlation ID: Auto-incremented per request
- Request timeout: 30 seconds
- Compression: SNAPPY if supported

---

## Configuration

### Environment Variables (optional)
- `KAFKA_BROKERS`: Comma-separated list of brokers (overrides connect() parameter)
- `KAFKA_TIMEOUT_MS`: Request timeout (default: 30000)
- `KAFKA_COMPRESSION`: Compression codec - "none", "snappy", "lz4", "zstd" (default: "none")

### Defaults
- Connection retries: 3
- Backoff: exponential (500ms → 1s → 2s)
- Fetch max bytes: 1MB per partition
- Produce acks: "all" (wait for all in-sync replicas)
- Consumer group: "eval-driver-${UUID}"

---

## Notes for Evaluation

1. **Determinism**: Messages are consumed in committed order; offset tracking ensures no duplicates
2. **Isolation**: Each `connect()` creates independent consumer group (UUID-based)
3. **Idempotency**: Duplicate production (same key, same message) results in duplicate offsets (Kafka semantic)
4. **Schema Flexibility**: Supports JSON schema draft-7; additionalProperties=true allows extra fields
5. **Partition Awareness**: Respects partition key for sharding; round-robins if key is null
6. **Async-Safe**: All operations are promise-based; safe for concurrent calls with different topics

---

## Dependencies

Requires:
- Node.js 16+ (async/await, Buffer, crypto)
- Apache Kafka 2.0+ (or compatible, e.g., Confluent, Amazon MSK)
- Network access to broker(s)

No external npm packages required - uses native Node.js modules only.

---

## Edge Cases with Mitigation

### Edge Case 1: Consumer Group Rebalance During Read

**Scenario:** New consumer joins the same group mid-test, triggering partition rebalance. Existing consumer loses partition assignments.

**Symptom:** `RebalanceInProgressException` thrown during `consume()`. Partial message consumption — some messages read, others missed. Consumer returns 0 messages despite offset lag > 0.

**Do NOT:** Retry the same consume() call without handling the rebalance. This extends the rebalance window and starves the partition.

**Mitigation:**
1. Detect rebalance via consumer rebalance listener callback
2. Commit current offsets before partition revocation completes
3. Wait for rebalance to complete: poll until consumer group state = STABLE (max 30s)
4. Resume consumption from last committed offset after partition reassignment
5. If persistent: use manual `assign()` instead of `subscribe()` to bypass group coordination

**Escalation:** `NEEDS_INFRA_CHANGE` if rebalance frequency > 1/minute — indicates broker instability.

---

### Edge Case 2: Offset Lag Spike After Produce

**Scenario:** Message was produced successfully (broker acknowledged), but consumer reads 0 messages.

**Symptom:** `produce()` returns success with offset N. `consume()` returns empty. `kafka-consumer-groups --describe` shows lag = 1 but offset never advances.

**Do NOT:** Assume the message was lost and reproduce. This creates duplicate messages.

**Mitigation:**
1. Snapshot consumer group committed offset BEFORE produce call
2. After produce, verify offset exists at expected partition/offset via admin API
3. Seek consumer to exact partition+offset returned by producer
4. If offset not found after 5s: verify producer `acks=all` was set, check in-sync replica count
5. Use explicit `seek()` to read exactly the produced message

**Escalation:** `BLOCKED` if lag > 100 messages and topic replication factor = 1 — data may be unrecoverable.

---

### Edge Case 3: Schema Registry Connection Failure

**Scenario:** Eval uses Avro or Protobuf serialization. Schema Registry is down or unreachable.

**Symptom:** `SchemaRegistryException: Connect refused` during produce. Or: message produced as raw bytes, consumer fails to deserialize.

**Do NOT:** Fall back to raw JSON silently. This masks serialization bugs that will surface in production.

**Mitigation:**
1. Check Schema Registry connectivity in `connect()` before any produce/consume
2. For JSON eval scenarios: explicitly set `value.serializer=StringSerializer` to avoid registry dependency
3. For Avro/Protobuf: fail fast with clear error if registry unreachable
4. Cache schema locally after first successful fetch (valid for eval session duration)
5. If Schema Registry is flaky: use local schema file strategy instead

**Escalation:** `NEEDS_INFRA_CHANGE` — Schema Registry is infrastructure; eval cannot proceed without it.

---

### Edge Case 4: Partition Leadership Change

**Scenario:** Kafka broker hosting the partition leader restarts or fails during eval. Leadership election takes 5-30s.

**Symptom:** `NotLeaderOrFollowerException` or `LEADER_NOT_AVAILABLE` error on produce. Fetch errors on consume.

**Do NOT:** Retry immediately in a tight loop. This floods the broker during election and delays recovery.

**Mitigation:**
1. Catch `NotLeaderOrFollowerException` and wait 500ms before retry
2. Refresh producer metadata: call `partitionsFor(topic)` to force metadata update
3. Retry produce up to 3 times with exponential backoff (500ms, 1s, 2s)
4. Verify broker count after error: if `brokers < replication.factor`, escalate immediately
5. If partition remains unavailable after 30s: topic is unhealthy, eval cannot proceed

**Escalation:** `NEEDS_CONTEXT` if broker count < 2. `NEEDS_INFRA_CHANGE` if leadership election takes > 30s.

---

### Edge Case 5: Message Deduplication Failure

**Scenario:** Eval expects exactly N messages but consumer reads N+M due to producer retries without idempotency.

**Symptom:** Consumer reads more messages than expected. Duplicate messages have identical content but different offsets.

**Do NOT:** Assert only on message content equality — this masks duplicates.

**Mitigation:**
1. Enable idempotent producer: `enable.idempotence=true` + `acks=all` + `max.in.flight.requests=5`
2. Track produced message offsets; assert consumer reads only those exact offsets
3. For exactly-once semantics: use transactional producer (`transactional.id=eval-{uuid}`)
4. Assert exact message count, not just content match
5. In teardown: verify no uncommitted transactional messages remain

**Escalation:** `BLOCKED` if duplicate messages found and idempotency is enabled — indicates broker-level deduplication failure.

---

### Edge Case 6: Topic Does Not Exist

**Scenario:** Eval tries to produce/consume from a topic that hasn't been created yet, or was deleted between test runs.

**Symptom:** `UnknownTopicOrPartitionException` on first produce. Or: `auto.create.topics.enable=false` on broker prevents automatic creation.

**Do NOT:** Enable `auto.create.topics.enable=true` in eval — this creates topics with wrong config.

**Mitigation:**
1. Verify topic existence in `connect()`: use admin client to list topics
2. If topic missing and auto-create is required: create with explicit config (partitions, replication, retention)
3. Create topic with `eval-` prefix to distinguish from production topics
4. Wait for topic to become AVAILABLE before producing (leader election may take 2-5s)
5. In teardown: delete eval-prefixed topics to avoid accumulation

**Escalation:** `NEEDS_INFRA_CHANGE` if topic must pre-exist. `NEEDS_CONTEXT` if topic naming is unclear.

---

## Decision Trees and Patterns

### Decision Tree 1: Consumer Offset Strategy

```
WHAT IS THE EVAL SCENARIO?
│
├── Reading messages produced BY THIS TEST RUN
│   ├── Topic has prior messages (contamination risk)
│   │   └── STRATEGY: snapshot offset BEFORE produce → seek to snapshot+1 after
│   │       CONFIG: auto.offset.reset=none, unique consumer group
│   │
│   └── Topic is empty (freshly created eval topic)
│       └── STRATEGY: auto.offset.reset=earliest, subscribe and poll
│           CONFIG: unique consumer group, cleanup topic after
│
├── Verifying messages from a PRIOR PRODUCER (async pipeline)
│   ├── Producer offset is known
│   │   └── STRATEGY: seek to exact partition+offset
│   │       CONFIG: manual assign(), no group coordination
│   │
│   └── Producer offset is unknown (only message content known)
│       └── STRATEGY: read from timestamp (offsetsForTimes)
│           CONFIG: auto.offset.reset=earliest, scan from known time window
│
└── Verifying NO messages were produced (negative assertion)
    └── STRATEGY: snapshot offset, trigger action, poll for 5s, verify offset unchanged
        CONFIG: short poll.timeout.ms (100ms), auto.offset.reset=latest
```

**Key Factors:**
- Always use unique consumer group per test run to prevent offset contamination
- `seek()` is more reliable than `auto.offset.reset` for deterministic eval
- For async pipeline testing: prefer timestamp-based offset lookup

---

### Decision Tree 2: Partition Key Strategy

```
DOES THE EVAL REQUIRE MESSAGE ORDERING?
│
├── YES — ordered processing required
│   ├── Single consumer scenario
│   │   └── USE: explicit partition key (e.g., user_id, order_id)
│   │       VERIFY: all related messages in same partition
│   │
│   └── Multi-consumer scenario
│       └── USE: consistent hash partition key
│           VERIFY: consumer count ≤ partition count
│
├── NO — ordering irrelevant
│   ├── Load distribution needed
│   │   └── USE: null key (round-robin distribution)
│   │       NOTE: offsets non-deterministic; assert by content not position
│   │
│   └── Single topic, single producer
│       └── USE: null key acceptable
│           NOTE: document in eval that ordering is not asserted
│
└── MAYBE — depends on downstream consumer behavior
    └── CHECK: does consumer assume ordering?
        IF YES → treat as ordered, use explicit key
        IF NO  → use null key, document assumption
```

---

## Common Pitfalls

### Pitfall 1: Shared Consumer Group Across Test Runs

**Mistake:** Using a hardcoded consumer group ID like `eval-consumer` across all test runs.

```javascript
// WRONG
const consumer = kafka.consumer({ groupId: 'eval-consumer' });
```

**Fix:** Generate a unique group ID per test run.

```javascript
// CORRECT
const testRunId = `eval-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
const consumer = kafka.consumer({ groupId: testRunId });
```

**Why it matters:** Committed offsets from previous test runs cause subsequent tests to skip messages, leading to false "0 messages consumed" results.

---

### Pitfall 2: Not Flushing Producer Before Reading

**Mistake:** Reading from consumer immediately after `produce()` before flush completes.

```javascript
// WRONG
await produce(kafka, 'test', { data: 'value' });
const messages = await consume(kafka, 'test', 1000); // may return empty
```

**Fix:** Always flush producer before switching to consumer.

```javascript
// CORRECT
await produce(kafka, 'test', { data: 'value' });
await producer.flush(); // wait for all messages acknowledged
const messages = await consume(kafka, 'test', 1000);
```

**Why it matters:** Messages may still be in the producer's internal buffer when consumer polls, leading to empty reads.

---

### Pitfall 3: Asserting Message Count Without Accounting for Compaction

**Mistake:** Assuming topic message count equals produced message count.

```javascript
// WRONG — fails on compacted topics
assert.equal(messages.length, expectedCount);
```

**Fix:** Use unique keys per eval run; verify by key.

```javascript
// CORRECT
const evalKey = `eval-${Date.now()}`;
await produce(kafka, 'test', { data: 'value' }, evalKey);
const found = messages.find(m => m.key === evalKey);
assert.ok(found, `Message with key ${evalKey} not found`);
```

**Why it matters:** Log compaction removes duplicate-key messages; count-based assertions break on compacted topics.

---

### Pitfall 4: Consumer Group Leak on Test Failure

**Mistake:** Not cleaning up consumer group when test fails mid-run.

```javascript
// WRONG — no cleanup on error path
const consumer = kafka.consumer({ groupId: runId });
await consumer.connect();
await riskyOperation(); // throws — disconnect never called
```

**Fix:** Use try/finally for consumer lifecycle.

```javascript
// CORRECT
const consumer = kafka.consumer({ groupId: runId });
try {
  await consumer.connect();
  return await riskyOperation();
} finally {
  await consumer.disconnect();
  await adminClient.deleteGroups([runId]);
}
```

**Why it matters:** Leaked consumer groups accumulate committed offsets that contaminate future test runs.

---

## Eval Checklist: Kafka Driver

Before marking eval pass for any Kafka-backed feature:

- [ ] Unique consumer group generated for this test run
- [ ] Consumer group offsets verified as new (no prior commits)
- [ ] Producer configured with `acks=all` and `enable.idempotence=true`
- [ ] Schema validated (round-trip serialize/deserialize for Avro/Protobuf)
- [ ] Producer flushed before consumer poll
- [ ] Exact partition+offset of produced message verified
- [ ] Message content asserted (not just existence)
- [ ] Message count asserted (no duplicates)
- [ ] Consumer group offsets cleaned up in teardown
- [ ] Eval-prefixed topic deleted or retained per policy

## Cross-References

- **eval-driver-api-http** — HTTP trigger for message-producing endpoints
- **eval-product-stack-up** — Bring up Kafka broker before eval
- **eval-coordinate-multi-surface** — Coordinate Kafka eval with API/DB assertions
- **deploy-driver-docker-compose** — Kafka + ZooKeeper service definition
- **reasoning-as-infra** — Event bus architecture patterns and partition sizing
- **contract-event-bus** — Negotiate event bus contracts for Kafka topics

## Checklist

Before claiming Kafka eval complete:

- [ ] `connect()` succeeded and broker is reachable
- [ ] All produced messages verified consumed within assertion timeout
- [ ] Schema validation passed for all message payloads
- [ ] Offset committed after successful consumption assertions
- [ ] `teardown()` called unconditionally — no orphaned consumer groups remaining
- [ ] Topic deleted or retained per documented eval policy

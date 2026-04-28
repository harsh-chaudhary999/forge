---
name: contract-event-bus
description: "WHEN: Council has identified event bus conflicts across services and needs a locked contract. Negotiates topic schema, versioning, idempotency, ordering, retention, consumer groups, and dead-letter queues before any producer or consumer is written."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers:
  - "design event contract"
  - "define event schema"
  - "event bus spec"
  - "message schema"
allowed-tools:
  - Write
---

# Contract Event Bus Skill

Teaches teams to negotiate Kafka/event-bus contracts systematically. Covers schema versioning, topic design, consumer guarantees, idempotency, and ordering semantics. Output is a locked event bus contract that all producers and consumers sign off on.

## Anti-Pattern Preamble: Why Event Bus Contracts Are Skipped

| Rationalization | The Truth |
|---|---|
| "We'll define the topic schema during implementation" | Implementation-time schema decisions cause producer/consumer drift. Schema must be agreed before any code is written or the contract is already broken. |
| "At-least-once is fine, the consumer will handle duplicates" | Consumers cannot handle duplicates they don't know are coming. The contract must specify delivery semantics AND the deduplication strategy before consumer code is written. |
| "We don't need a dead-letter queue yet" | The first poison message will block the partition indefinitely without a DLQ. The DLQ must be defined at contract time, not after production incidents. |
| "Topic naming can be generic, we'll namespace it later" | Generic topic names cause cross-domain collisions. Naming is a contract decision — changing it after producers are live requires coordinated migration. |
| "Schema evolution is a later problem" | Schema evolution policy (forward/backward/full compatibility) must be defined before the first message is produced. Retrofitting compatibility is painful and breaking. |
| "Consumer groups can be named by convention" | Unnamed or ad-hoc consumer group names cause offset loss on restarts and rebalancing failures. Consumer group IDs are part of the contract. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
NO PRODUCER OR CONSUMER IS WRITTEN BEFORE THE TOPIC SCHEMA, DELIVERY SEMANTICS, AND CONSUMER GROUP CONTRACT ARE LOCKED. AN UNCONTRACTED EVENT BUS IS AN UNTESTABLE SYSTEM.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Topic name is generic ("events", "messages", "updates")** — Generic topic names cause producers and consumers from different domains to collide. STOP. Name topics with domain + entity + action (e.g., `payments.order.paid`).
- **Payload schema is described in prose only, not a formal schema** — Prose schemas cause producer/consumer drift. STOP. Define a formal schema (Avro, Protobuf, or JSON Schema) before the contract is locked.
- **Delivery semantics are listed as "TBD"** — At-most-once, at-least-once, and exactly-once require different idempotency and offset strategies. STOP. Lock delivery semantics before any producer or consumer is implemented.
- **No dead-letter queue (DLQ) is defined** — Poison messages with no DLQ will block a partition indefinitely. STOP. Define DLQ topic, routing rules, and alert threshold before the contract is accepted.
- **Retention period is not specified** — Default retention may drop messages before all consumers have read them. STOP. Set explicit retention based on slowest consumer's expected lag.
- **Consumer group naming is left unspecified** — Unnamed consumer groups default to arbitrary names, causing rebalancing and offset loss. STOP. Assign stable, service-namespaced consumer group IDs.
- **Schema evolution policy is absent** — Field additions without compatibility rules break existing consumers. STOP. Specify forward/backward/full compatibility policy before any schema is shipped.

## Minimum depth before the event contract is LOCK

**Purpose:** Avoid hand-wavy “we use Kafka” specs. Before locking, the contract **must** document:

1. **Topology:** Exchange type (or “none / broker default”), **topic and/or queue names**, **routing keys** — **or** explicit pattern: **single topic + message discriminator field** (name + allowed values).
2. **Payload:** Formal schema reference (Avro / Protobuf / JSON Schema id) — not prose-only.
3. **Idempotency:** Consumer idempotency key (field name + where stored / TTL) **or** proof that duplicates are harmless — stated per consumer group.
4. **Ordering:** Per-partition / per-key / best-effort-none — pick one and justify.
5. **DLQ:** Destination topic/queue + when messages land there + alert expectation.
6. **State authority (one explicit sentence):** e.g. “**Only** service `orders-api` commits order state to MySQL; consumers **must not** write those tables — they call `POST /internal/orders/...` or emit `order.requested` for retry.” Or: “Consumer X **may** update projection table `…` because …” Ambiguity here is a production incident.

If any row is unknown, use **`WAIVER: … until <ticket/ref>`** — not silence.

---

## When to Use

- **Negotiating async integration between services** — Different teams need to exchange events (payments, user lifecycle, notifications)
- **Designing Kafka topic architecture** — Naming, partitioning, retention, compression policy
- **Schema evolution** — How to version events safely without breaking existing consumers
- **Idempotency & ordering requirements** — Exactly-once vs at-least-once, per-partition vs global ordering
- **Consumer reliability** — Offset management, max in-flight, rebalancing, dead-letter queues
- **Cross-team alignment** — Lock producer expectations and consumer responsibilities

## Contract Structure

### 1. Topic Design

**Purpose:** Define the physical topic(s), partitioning strategy, retention, and compression.

**Key fields:**

- **Topic name:** Follow `<domain>.<entity>.<event>` or `<entity>.<verb>` convention
  - ✅ `user.lifecycle.created`, `payment.transaction.failed`, `orders.shipped`
  - ❌ `events`, `data`, `topic1`
  
- **Partition key:** Strategy for distributing load
  - `user_id` (events from same user stay together)
  - `order_id` (events from same order stay together)
  - `timestamp` (round-robin for global ordering attempt)
  - `null` (random distribution)

- **Partition count:** Number of parallel consumers
  - 3–5 for low-throughput events (< 1k/sec)
  - 10–20 for medium (1k–10k/sec)
  - 50+ for high (> 10k/sec)

- **Retention policy:**
  - `7 days` — Most transient events (logs, metrics)
  - `30 days` — Standard events (orders, payments)
  - `90 days` — Compliance-critical events (audit logs, transactions)
  - `infinite` — Never delete (replay scenarios)

- **Compression:** Reduce disk/network overhead
  - `gzip` — Best ratio, slower (events < 1MB each)
  - `snappy` — Better balance, faster (default)
  - `lz4` — Fastest, lower ratio
  - `none` — Debugging only

**Example:**
```
Topic: payment.transaction.completed
Partitions: 12 (partition key: user_id)
Retention: 30 days
Compression: snappy
Replication factor: 3
```

### 2. Schema Versioning

**Purpose:** Evolve event schemas without breaking existing consumers.

**Schema format (Avro/Protobuf/JSON):** Define each field with type, nullability, and order.

**Example event schema:**
```json
{
  "namespace": "com.payment",
  "type": "record",
  "name": "TransactionCompleted",
  "version": 1,
  "fields": [
    { "name": "transaction_id", "type": "string", "doc": "UUID, idempotency key" },
    { "name": "user_id", "type": "string", "doc": "Partition key" },
    { "name": "amount_cents", "type": "long", "doc": "Amount in cents, always positive" },
    { "name": "currency", "type": "string", "default": "USD", "doc": "ISO-4217 code" },
    { "name": "timestamp_ms", "type": "long", "doc": "Epoch milliseconds" },
    { "name": "merchant_id", "type": ["null", "string"], "default": null, "doc": "Optional, added v1.1" },
    { "name": "metadata", "type": ["null", "string"], "default": null, "doc": "JSON blob, optional" }
  ]
}
```

**Versioning rules (backward + forward compatible):**

- **v1 → v1.1 (minor, non-breaking):** Add optional field with default value
  - Old producers (v1.0) can write, new consumers (v1.1) read with default
  - New producers (v1.1) can write, old consumers (v1.0) ignore unknown fields

- **v1 → v2 (major, breaking):** Remove field, change type, or make optional required
  - Old consumers will fail
  - Plan: dual-write period (v1 + v2), migrate consumers, switch producer

- **Never:**
  - Remove a field without a major version bump
  - Change field type without explicit mapping (string → int fails)
  - Make a field required that was optional

**Schema registry:** Store schemas centrally (Confluent Schema Registry, AWS Glue)
- Versioning enforced by tooling
- Compatibility level set per subject (backward, forward, full)
- Clients validate on produce/consume

### 3. Idempotency & Ordering

**Purpose:** Ensure exactly-once semantics and correct event ordering for consistency.

**Idempotency:**

- **Idempotency key field:** UUID or `<service>-<timestamp>-<sequence>` generated by producer
  - Consumer maintains idempotency window (24 hours, 7 days, configurable)
  - Duplicate event with same key is ignored (deduplicated at consumer)
  - Fallback: keyed state store (Redis, DynamoDB) with TTL

- **Example producer code:**
  ```python
  import uuid
  producer.send(
    topic="payment.transaction.completed",
    key=user_id,
    value={
      "idempotency_id": str(uuid.uuid4()),
      "user_id": user_id,
      "amount_cents": 5000,
      "timestamp_ms": int(time.time() * 1000)
    }
  )
  ```

- **Example consumer deduplication:**
  ```python
  idempotency_cache = {}  # or Redis
  
  def process_event(event):
    key = event["idempotency_id"]
    if key in idempotency_cache:
      return  # Already processed
    
    # Do work (e.g., credit account)
    do_work(event)
    
    # Store key with 24h TTL
    idempotency_cache[key] = time.time()
  ```

**Ordering guarantees:**

- **Per-partition (within partition key):** All events with same partition key (e.g., user_id) are processed in order
  - Example: `user_1` creates account → enables 2FA → disables 2FA (must happen in order)
  - Use when: Order matters within an entity

- **Global (no ordering guarantee):** Events can be processed in any order
  - Example: Different users' transactions (order doesn't matter across users)
  - Default for Kafka (partitions process independently)

- **Ordering guarantee matrix:**
  ```
  Requirement          | Partition Key | Notes
  ---------------------|---------------|------------------------------------------
  Per-user ordering    | user_id       | User's events always in order (FIFO)
  Per-order ordering   | order_id      | Order's events always in order
  Global order         | timestamp     | Single partition, throughput bottleneck
  No requirement       | null/random   | Highest throughput, any order OK
  ```

**Exactly-once vs At-least-once:**

- **Exactly-once:** Event processed precisely once (+ idempotency key + transactional offset commit)
  - Harder to implement, requires distributed transactions
  - Use for: Payments, inventory, financial transactions

- **At-least-once:** Event processed at least once (+ idempotency key for safety)
  - Easier, standard default
  - Use for: Notifications, analytics, non-critical updates

### 4. Consumer Guarantees

**Purpose:** Define how consumers behave, handle failures, and recover.

**Consumer group strategy:**

- **One consumer group per consumer application** (not per consumer instance)
  - Example: `payments-2fa-processor` (all instances share one group)
  - Kafka automatically balances partitions across group members
  
- **Parallel consumers:** Number of instances ≤ number of partitions (rebalance overhead)

**Offset management:**

- **Auto-commit:** Consumer automatically saves offset every N seconds
  - Pro: Simple, automatic recovery
  - Con: Risk of processing same message twice if consumer crashes before commit
  - Setting: `enable.auto.commit=true`, `auto.commit.interval.ms=5000`

- **Manual commit:** Consumer explicitly commits after processing
  - Pro: Exact control, only commit after successful processing
  - Con: More code, risk of offset drift if not careful
  - Pattern: Process → Store result → Commit offset (transactional)

- **Offset reset policy:** What to do if offset is lost/corrupted
  - `earliest` — Replay all events from start (dangerous, can reprocess)
  - `latest` — Skip to end, lose messages (safest for recovery)
  - Use: `auto.offset.reset=latest` for production

**Rebalancing behavior:**

- **Rebalancing:** Kafka rebalances partitions when consumer added/removed
  - Pause processing during rebalance (seconds to minutes)
  - Can cause duplicate processing if offset not committed before rebalance

- **Stop-the-world rebalance:** All consumers pause
  - Use: When order/exactly-once semantics critical

- **Cooperative rebalance:** Gradual partition reassignment (Kafka 2.4+)
  - Use: When throughput > consistency

**Max in-flight messages:**

- **Max concurrent messages per consumer:** Limits memory, controls backpressure
  - `fetch.max.bytes=52428800` (50MB)
  - `max.poll.records=500` (max messages per poll)
  
- **Recommended:** 100–500 in-flight for most workloads
  - Low (10–50): Strict ordering, bounded memory
  - High (500+): Maximize throughput, risk burst failures

**Example consumer config:**
```yaml
group.id: payments-2fa-processor
enable.auto.commit: false          # Manual commit
auto.offset.reset: latest          # Skip lost offsets
max.poll.records: 100              # Batch size
session.timeout.ms: 30000          # Rebalance timeout
partition.assignment.strategy: RoundRobin
```

### 5. Dead-Letter Queues & Retry Strategy

**Purpose:** Safely handle messages that fail processing, with bounded retries and observability.

**DLQ topic naming:**
- `<original-topic>-dlq` or `<original-topic>-dead-letter`
- Example: `payment.transaction.completed-dlq`
- Same schema as source topic + metadata (error_message, retry_count, timestamp)

**Retry strategy:**

1. **Transient failure (network timeout, temporary DB down):**
   - Retry immediately (0–100ms) with exponential backoff
   - Max retries: 3–5
   - If all fail → Move to DLQ

2. **Permanent failure (invalid event, schema mismatch):**
   - Do NOT retry
   - Log + Alert + Move to DLQ immediately
   - Operator reviews, fixes, replays

3. **Exponential backoff formula:**
   ```
   delay_ms = base_delay_ms * (2 ^ retry_count) + jitter
   
   Retry 1: 100ms
   Retry 2: 200ms
   Retry 3: 400ms
   Retry 4: 800ms (then DLQ)
   ```

**DLQ processing:**

- **Manual review:** Operator/on-call reviews DLQ messages, decides:
  - Fix bug → Replay from original topic
  - Alert team → Incident ticket
  - Archive → Event no longer relevant

- **Automatic replay (careful):** Some systems auto-replay after fix deployed
  - Set replay flag/topic to prevent duplicate events
  - Use: When fix is simple (e.g., dependency restored)

- **DLQ schema (extended):**
  ```json
  {
    "original_event": { ... },  // Original payload
    "error_message": "string",   // Why it failed
    "error_code": "string",      // Categorize (INVALID_SCHEMA, DB_ERROR, TIMEOUT)
    "retry_count": "int",        // How many times retried
    "first_failure_ms": "long",  // When first failed
    "final_failure_ms": "long",  // When moved to DLQ
    "consumer_group": "string"   // Which consumer group failed
  }
  ```

**Example retry code:**
```python
import time
from kafka import KafkaConsumer, KafkaProducer

consumer = KafkaConsumer('payment.transaction.completed', group_id='processor')
dlq_producer = KafkaProducer()

for message in consumer:
  retry_count = 0
  max_retries = 3
  
  while retry_count < max_retries:
    try:
      process_event(message.value)
      consumer.commit()  # Success, commit offset
      break
    except TransientError as e:
      retry_count += 1
      if retry_count < max_retries:
        delay = 100 * (2 ** retry_count)  # Exponential backoff
        time.sleep(delay / 1000)
      else:
        # Max retries reached, move to DLQ
        dlq_producer.send('payment.transaction.completed-dlq', value={
          'original_event': message.value,
          'error_message': str(e),
          'error_code': 'TRANSIENT_ERROR',
          'retry_count': retry_count
        })
        consumer.commit()
    except PermanentError as e:
      # Don't retry permanent errors
      dlq_producer.send('payment.transaction.completed-dlq', value={
        'original_event': message.value,
        'error_message': str(e),
        'error_code': 'INVALID_EVENT',
        'retry_count': 0
      })
      consumer.commit()
      break
```

---

## Anti-Patterns

1. **No partition key** (random distribution)
   - ❌ Violates ordering guarantees, harder to scale consumers
   - ✅ Use `user_id` or `order_id` as partition key

2. **Infinite retention without cleanup**
   - ❌ Disk fills up, rebalancing slow, recovery slow
   - ✅ Set retention to business need (30 days typical)

3. **Removing fields without major version bump**
   - ❌ Old producers write new events, new consumers fail on old events
   - ✅ Always bump major version, coordinate dual-write period

4. **Auto-commit without error handling**
   - ❌ Offset commits before processing done, message lost on crash
   - ✅ Use manual commit after processing succeeds

5. **No DLQ or retry strategy**
   - ❌ Failed events vanish silently, no observability
   - ✅ DLQ + retry + alerting for every consumer

6. **Single partition for global ordering**
   - ❌ Throughput bottleneck, no parallelism
   - ✅ Accept per-partition ordering, use timestamp if needed

7. **No idempotency key**
   - ❌ Exactly-once semantics impossible
   - ✅ Always include UUID or deterministic key

---

## Example Output: Complete Event Bus Contract

**File:** `~/forge/brain/prds/<task-id>/contracts/event-bus.md`

```markdown
# Event Bus Contract: Payment Service

**Status:** Locked (v1.0) | **Signed:** PaymentService, BillingService, NotificationService

---

## 1. Topics

| Topic | Partition Key | Partitions | Retention | Compression | Replication |
|-------|---------------|-----------|-----------|-----------|------------|
| payment.transaction.created | user_id | 12 | 30d | snappy | 3 |
| payment.transaction.completed | user_id | 12 | 30d | snappy | 3 |
| payment.transaction.failed | user_id | 8 | 30d | snappy | 3 |
| user.lifecycle.2fa_enabled | user_id | 6 | 90d | gzip | 3 |
| billing.invoice.generated | account_id | 10 | 90d | snappy | 3 |

---

## 2. Schema: payment.transaction.completed (v1.0)

**Registry:** Confluent Schema Registry (AWS)

**Avro Schema:**
```json
{
  "namespace": "com.payment",
  "type": "record",
  "name": "TransactionCompleted",
  "doc": "Payment transaction completed successfully",
  "fields": [
    {
      "name": "transaction_id",
      "type": "string",
      "doc": "UUID, serves as idempotency key"
    },
    {
      "name": "user_id",
      "type": "string",
      "doc": "Partition key, identifies customer"
    },
    {
      "name": "amount_cents",
      "type": "long",
      "doc": "Transaction amount in cents USD"
    },
    {
      "name": "currency",
      "type": "string",
      "default": "USD",
      "doc": "ISO 4217 currency code"
    },
    {
      "name": "timestamp_ms",
      "type": "long",
      "doc": "Event timestamp, epoch milliseconds"
    },
    {
      "name": "merchant_id",
      "type": ["null", "string"],
      "default": null,
      "doc": "Merchant identifier (optional)"
    },
    {
      "name": "payment_method",
      "type": {
        "type": "enum",
        "name": "PaymentMethod",
        "symbols": ["CREDIT_CARD", "DEBIT_CARD", "BANK_TRANSFER", "PAYPAL"]
      },
      "doc": "Payment method used"
    },
    {
      "name": "metadata",
      "type": ["null", "string"],
      "default": null,
      "doc": "JSON-encoded additional context"
    }
  ]
}
```

**Compatibility:** `BACKWARD_TRANSITIVE` (old consumers read new events)
- v1.0 → v1.1: Add optional fields only
- v1 → v2: Major version required if removing/changing fields

---

## 3. Idempotency

**Idempotency key field:** `transaction_id` (UUID)

**Window:** 24 hours

**Semantics:** Exactly-once delivery per producer

**Deduplication implementation:**
- Consumer maintains Redis cache: `{transaction_id} → {processed_timestamp}`
- TTL: 24 hours
- On receive: Check cache, if hit skip processing, else process + cache

**Producer guarantee:**
```python
import uuid
event = {
  'transaction_id': str(uuid.uuid4()),
  'user_id': user_id,
  'amount_cents': amount,
  'timestamp_ms': int(time.time() * 1000)
}
producer.send('payment.transaction.completed', 
              key=user_id, 
              value=event)
```

---

## 4. Ordering

**Per-partition ordering:** YES (within partition key)
- All events for same `user_id` processed in FIFO order
- Guarantees user's transactions processed sequentially

**Global ordering:** NO (not required)
- Different users' transactions can process in parallel
- Reduces throughput bottleneck

**Ordering guarantee:** `user_id` partition key ensures user-level FIFO

---

## 5. Consumer Setup

### Consumer Group: `payment-transaction-processor`

| Setting | Value | Reason |
|---------|-------|--------|
| `group.id` | payment-transaction-processor | Shared group ID across all instances |
| `enable.auto.commit` | false | Manual commit after processing |
| `auto.offset.reset` | latest | Skip corrupted/lost offsets |
| `max.poll.records` | 100 | Batch 100 messages per poll |
| `session.timeout.ms` | 30000 | 30s timeout for rebalance |
| `partition.assignment.strategy` | RoundRobin | Balanced distribution |
| `max.in.flight.requests.per.connection` | 5 | Bounded concurrency |

### Processing pattern:
```python
for message in consumer:
  try:
    # Process atomically
    result = update_billing_ledger(message.value)
    
    # Commit after success
    consumer.commit()
    
  except RecoverableError:
    # Transient failure, DLQ handles retry
    send_to_dlq(message, 'TRANSIENT_ERROR')
    consumer.commit()
```

---

## 6. Dead-Letter Queue: `payment.transaction.completed-dlq`

**Schema (extends original):**
```json
{
  "original_event": { /* full TransactionCompleted event */ },
  "error_message": "string",
  "error_code": "enum [TRANSIENT_ERROR, INVALID_SCHEMA, TIMEOUT, DB_UNAVAILABLE]",
  "retry_count": "int",
  "first_failure_ms": "long",
  "final_failure_ms": "long",
  "consumer_group": "payment-transaction-processor"
}
```

**Retry strategy:**
- Transient errors: Retry 3x with exponential backoff (100ms, 200ms, 400ms)
- Permanent errors: No retry, DLQ immediately
- Max in-flight during retry: 10 (slow drain)

**On-call SLA:**
- Monitor DLQ every 5 minutes
- Alert if DLQ queue depth > 100 messages
- Review + resolve within 1 hour for production

**Replay process:**
1. Fix root cause (dependency restored, bug fixed)
2. Operator manually replays DLQ messages via replay tool
3. Mark message as replayed (idempotency_id tracked)
4. Verify no duplicates in billing ledger

---

## Sign-Off

- **Producer Owner:** payment-service-team (signed)
- **Consumer 1:** billing-service-team (signed)
- **Consumer 2:** notification-service-team (signed)
- **Infra Owner:** platform-team (signed)

**Locked by:** contract-event-bus skill | **Date:** 2026-04-10

---

Ready for: Shared-dev-spec lock
```

---

## Implementation Checklist

- [ ] Topic created in Kafka cluster
- [ ] Schema registered in Schema Registry
- [ ] Producer validates before sending
- [ ] Consumer implements deduplication + manual commit
- [ ] DLQ topic created, monitoring + alerting in place
- [ ] Integration tests pass (idempotency, ordering, retry)
- [ ] Runbook created: How to replay DLQ, diagnose failures
- [ ] Team sign-off obtained (all producers + consumers)

---

## Edge Cases & Escalation Keywords

### Edge Case 1: Schema evolution adds required field mid-stream

**Symptom:** Event schema v1 has `{transaction_id, user_id, amount_cents}`. New requirement: add `merchant_id` as required field. Old producers (still running v1) emit events without merchant_id. New consumers expect it. Deserialization fails or values are null.

**Do NOT:** Make fields required without migration window.

**Mitigation:**
- Add field as optional first: `merchant_id: ["null", "string"] default: null`
- Producers upgrade to write merchant_id (within 1 week)
- Backfill old events: Consumer scans past N days of events, adds merchant_id via lookup
- Only then: Make field required in v2 schema
- Document timeline: "merchant_id added optional in v1.1. Mandatory in v2.0 (6 weeks later)."

**Escalation:** NEEDS_COORDINATION — If old events exist without field, need backfill plan. Cannot make field required without coordinating with all consuming services.

---

### Edge Case 2: Ordering guarantees differ between services

**Symptom:** Contract specifies partition key = `user_id` (per-user ordering). Payment service depends on strict ordering: charge created → payment processed → refund issued (must be in order). Notification service publishes user.created → user.updated → user.deleted (order doesn't matter to subscribers). Both partition by user_id. Under heavy load, notification service slow, causes rebalance, payment messages delivered out of order, refund before charge.

**Do NOT:** Assume all consumers need same ordering guarantees.

**Mitigation:**
- Define ordering requirement per topic:
  - `payment.transaction.*`: Partition by user_id (strict per-user ordering, 1 partition = 1 consumer)
  - `user.lifecycle.*`: Partition by user_id OR round-robin (order doesn't matter, parallelizable)
- Document in contract: "payment.transaction.* guarantees per-user FIFO. user.lifecycle.* is unordered."
- Alternative: Critical topics (payment, inventory) use single partition (throughput bottleneck acceptable). Non-critical topics (notifications) are distributed.

**Escalation:** NEEDS_CONTEXT — What ordering does consumer require? If strict, single partition needed (throughput cost). If eventual, distribute.

---

### Edge Case 3: Dead-letter queue handling causes silent data loss

**Symptom:** Event bus contract defines DLQ, but no one monitors it. Messages fail silently, pile up in DLQ, hit 100k backlog, on-call wakes up at 3am. RCA: notification consumer bug from 6 days ago. Meanwhile, 100k users never got notifications.

**Do NOT:** Define DLQ without monitoring and replay procedure.

**Mitigation:**
- DLQ monitoring mandatory: "Alert if DLQ depth > 100 messages"
- SLA: "DLQ messages must be reviewed and decision made (retry or archive) within 2 hours"
- Replay procedure documented: "How to replay DLQ message back to main topic (with idempotency check)"
- Monitoring dashboard: Track DLQ depth per consumer group, alert on thresholds
- On-call runbook: Steps to diagnose DLQ failure, replay, verify

**Escalation:** NEEDS_INFRA_CHANGE — If monitoring infrastructure missing, BLOCKED. Cannot accept contract without DLQ monitoring.

---

### Edge Case 4: Consumer group rebalancing causes duplicate processing

**Symptom:** Two payment consumers in group `payment-processor`. During deployment, one instance restarts, Kafka rebalances partitions (10 second pause). New instance starts, reads offset 12345 which was already processed by old instance (before offset was committed). Charges same transaction twice.

**Do NOT:** Assume offset commits are always timely.

**Mitigation:**
- Lock offset commit policy in contract: "Manual commit after processing succeeds (not auto-commit)"
- Idempotency required: "Every message must include idempotency_id (UUID). Consumer deduplicates via Redis key cache (24 hour TTL)."
- Rebalancing SLA: "Max in-flight = 5 messages. If rebalance occurs, max 5 messages reprocessed (idempotency handles duplicates)."
- Document: "Auto-commit is forbidden for payment topics. Manual commit required."

**Escalation:** NEEDS_COORDINATION — If consumer cannot implement manual commit (legacy system), cannot consume from payment topics. Escalate to BLOCKED.

---

### Edge Case 5: Partition key selection breaks scaling assumptions

**Symptom:** Topic partitions by `order_id` (thought it would distribute evenly). Black Friday sale: 1000 mega-orders placed, all partition to same key. One consumer processes 99% of traffic, others idle. Consumer lag grows, becomes 1 hour behind. Notifications delayed 1 hour.

**Do NOT:** Assume partition key distributes evenly without validation.

**Mitigation:**
- Document partition key skew risk: "order_id may skew during sales events. Max throughput per partition: 10k msg/sec."
- Fallback: "If single partition becomes bottleneck (lag > 5 min), switch to hash(order_id, shard_id) to spread across partitions."
- Monitoring: "Alert if partition lag differs by >100k messages (indicates skew)."
- Alternative: "For orders, consider round-robin (null key) if ordering not required, or hierarchical: partition by customer_id (higher cardinality)."

**Escalation:** NEEDS_INFRA_CHANGE — If partition skew expected, may need custom partitioner or topic redesign. Cannot accept default partitioning without simulation.

---

### Edge Case 6: Consumer lag grows indefinitely

**Symptom:** Notification consumer processes events at 100 msg/sec. Producer publishes at 1000 msg/sec. Consumer lag grows from 0 → 10k → 100k → 1M messages. At 1M, consumer can't catch up (Kafka retention = 7 days, messages expire). Notifications lost forever.

**Do NOT:** Assume consumer can always catch up.

**Mitigation:**
- Lock consumer throughput in contract: "Notification consumer must process >= producer rate (at least 1000 msg/sec)"
- Capacity planning: "Allowable consumer lag = retention_period * (1 - throughput_headroom). If retention = 7 days and headroom = 20%, max lag = 5.6 days."
- SLA: "Consumer lag must never exceed 1 hour. If lag > 1 hour, scale consumers or throttle producer."
- Monitoring: Track consumer lag per group, alert at 50% of acceptable lag

**Escalation:** NEEDS_INFRA_CHANGE — If consumer cannot match producer throughput, BLOCKED. Requires consumer scaling or producer rate limiting before contract lock.

---

### Edge Case 7: Schema registry unavailability breaks all consumers

**Symptom:** All topics use Confluent Schema Registry for validation. Registry goes down. Producers cannot validate schemas, fail all writes. Consumers cannot deserialize, fail all reads. Topic effectively dead for 30 minutes.

**Do NOT:** Make schema registry a hard dependency.

**Mitigation:**
- Cache schema locally: "Consumers must cache schemas from registry (5 minute TTL). If registry unavailable, use cached schema."
- Fallback: "If schema validation fails, pass raw bytes to consumer logic. Consumer handles schema mismatch gracefully (log, skip, or DLQ)."
- Monitoring: "Track schema registry availability. Alert if unavailable for >1 minute."
- SLA: "Schema registry must be highly available (99.9%). Maintain redundant registry instances."

**Escalation:** NEEDS_INFRA_CHANGE — If schema registry not highly available, BLOCKED. Requires redundancy or fallback before accepting contract.

---

## Decision Tree: Event Delivery Guarantee

**Q: What happens if a message is processed twice?**

→ **Duplicate processing is acceptable (notifications, analytics, logs)**
  - Model: **At-Least-Once** delivery
  - Guarantee: Message delivered at least once (may be duplicated)
  - Consumer responsibility: None (duplicates OK)
  - Implementation: Easier, auto-commit OK, no idempotency needed
  - Pros: Simple, high throughput
  - Cons: Duplicates possible, notification spam risk
  - Cost: Customers may see duplicate email/SMS notifications
  - Mitigation: "Consumers should deduplicate on client-side (e.g., UI hides duplicate notifications within 1s)"

→ **Duplicate processing must not happen (payments, inventory, ledger)**
  - Model: **Exactly-Once** delivery
  - Guarantee: Message processed exactly once (never duplicated, never lost)
  - Consumer responsibility: Implement idempotency (deduplicate via ID, TTL cache, or database)
  - Implementation: Harder, manual commit, idempotency key required
  - Pros: Safe, no duplicates, audit trail
  - Cons: Complex, slower (idempotency overhead)
  - Cost: Additional Redis/database for dedup cache
  - Mitigation: "Every message includes UUID. Consumer deduplicates via 24-hour TTL cache (Redis). If duplicate, return cached result."

→ **At most one message delivery required (but duplicates impossible)**
  - Model: **At-Most-Once** delivery
  - Guarantee: Message processed at most once (may be lost, never duplicated)
  - Consumer responsibility: Process or commit offset (not both)
  - Implementation: Commit offset BEFORE processing (dangerous)
  - Pros: Impossible to duplicate
  - Cons: Messages lost if consumer crashes after commit
  - Cost: Data loss acceptable?
  - Use: Analytics sampling (loss of 0.1% is acceptable), non-critical events only
  - NOT for: Payments, inventory, orders, financial ledgers

**Decision Flow:**
```
Is duplicate processing acceptable?
├─ YES (Notifications, Analytics, Non-critical)
│  └─ At-Least-Once
│     No idempotency key needed
│     Auto-commit OK
│     Simple to implement
│
├─ NO (Payments, Inventory, Ledger)
│  └─ Exactly-Once
│     Idempotency key mandatory
│     Manual commit after processing
│     Dedup cache required (Redis 24h TTL)
│
└─ CRITICAL: No message must be lost
   └─ At-Least-Once + Idempotency
      Idempotency key mandatory
      Manual commit after processing
      Dedup cache required
      Fallback: Replay from Kafka (audit trail)
```

**Key Commitment in Contract:**
```markdown
# Delivery Guarantee

- **Model**: [At-Least-Once | Exactly-Once | At-Most-Once]
- **Duplicate Handling**: 
  - If Exactly-Once: Idempotency key field, dedup cache (Redis, 24h TTL)
  - If At-Least-Once: Consumer must handle duplicates gracefully
  - If At-Most-Once: Data loss acceptable up to [X]%

- **Consumer Implementation**:
  - Offset commit: [auto | manual after processing]
  - Idempotency: [required | optional | not needed]
  - Dedup window: [24 hours | 7 days | never]
  - SLA: "99.9% of messages processed exactly once"

- **Monitoring**:
  - Track duplicate rate: "Should be < 0.1%"
  - Track message loss rate: "Should be 0%"
  - Track reprocessing rate: "If > 5%, investigate consumer lag"
```

---

## Related Skills

- **brain-read:** Load topology and existing contracts
- **reasoning-as-infra:** Design Kafka cluster topology and resource allocation
- **code-review:** Review producer/consumer implementations for idempotency + offset handling

## Checklist

Before claiming event bus contract locked:

- [ ] Topic naming follows domain.entity.action convention (e.g., `payments.order.paid`)
- [ ] Payload schema defined in formal format (Avro, Protobuf, or JSON Schema)
- [ ] Delivery semantics specified (at-least-once, exactly-once, or at-most-once)
- [ ] Idempotency strategy documented for all consumers
- [ ] Dead-letter queue defined with routing rules and alert thresholds
- [ ] Retention period set based on slowest consumer's expected lag
- [ ] Consumer group IDs specified with stable, service-namespaced names
- [ ] Schema evolution/compatibility policy documented
- [ ] Contract locked and written to brain

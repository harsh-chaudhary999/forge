# Event Bus Contract — Examples, Anti-Patterns & Delivery Decision Tree

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

**File:** `~/forge/brain/prds/<task-id>/contracts/event-contract.md` (council convention: `<domain>-contract.md`)

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

**Semantics:** At-least-once delivery + idempotent processing = effectively-once (true exactly-once delivery requires Kafka transactions/EOS; the dedup mechanism below is the effectively-once pattern)

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
| `partition.assignment.strategy` | CooperativeStickyAssignor | Incremental rebalance (default); eager RoundRobin/Range only if forced |
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

## Decision Tree: Event Delivery Guarantee

**Q: What happens if a message is processed twice?**

→ **Duplicate processing is acceptable (notifications, analytics, logs)**
  - Model: **At-Least-Once** delivery
  - Guarantee: Message delivered at least once (may be duplicated)
  - Consumer responsibility: idempotent processing REQUIRED unless the op is naturally idempotent or duplicate side-effects are provably harmless (see Edge Case 4 — rebalancing can re-deliver and double-charge)
  - Implementation: commit offsets only after the side-effect is committed; use an idempotency key when the op is not naturally idempotent
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
  - SLA: "<example — derive from slowest-consumer lag + business criticality, e.g. 99.9% of messages processed effectively-once (at-least-once delivery + idempotent processing)>"

- **Monitoring**:
  - Track duplicate rate: "Should be < 0.1%"
  - Track message loss rate: "Should be 0%"
  - Track reprocessing rate: "If > 5%, investigate consumer lag"
```

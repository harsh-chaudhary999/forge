# Event Bus Contract — Edge Cases & Escalation Keywords

Seven failure modes that a locked event bus contract must pre-empt. Each carries a symptom, a "Do NOT", a mitigation, and the escalation keyword to raise (resolve every fork via `AskUserQuestion` — see [`skills/_shared/human-input.md`](../../_shared/human-input.md)).

## Edge Case 1: Schema evolution adds required field mid-stream

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

## Edge Case 2: Ordering guarantees differ between services

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

## Edge Case 3: Dead-letter queue handling causes silent data loss

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

## Edge Case 4: Consumer group rebalancing causes duplicate processing

**Symptom:** Two payment consumers in group `payment-processor`. During deployment, one instance restarts, Kafka rebalances partitions (10 second pause). New instance starts, reads offset 12345 which was already processed by old instance (before offset was committed). Charges same transaction twice.

**Do NOT:** Assume offset commits are always timely.

**Mitigation:**
- Lock offset commit policy in contract: "Manual commit after processing succeeds (not auto-commit)"
- Idempotency required: "Every message must include idempotency_id (UUID). Consumer deduplicates via Redis key cache (24 hour TTL)."
- Rebalancing SLA: "Max in-flight = 5 messages. If rebalance occurs, max 5 messages reprocessed (idempotency handles duplicates)."
- Document: "Auto-commit is forbidden for payment topics. Manual commit required."

**Escalation:** NEEDS_COORDINATION — If consumer cannot implement manual commit (legacy system), cannot consume from payment topics. Escalate to BLOCKED.

---

## Edge Case 5: Partition key selection breaks scaling assumptions

**Symptom:** Topic partitions by `order_id` (thought it would distribute evenly). Black Friday sale: 1000 mega-orders placed, all partition to same key. One consumer processes 99% of traffic, others idle. Consumer lag grows, becomes 1 hour behind. Notifications delayed 1 hour.

**Do NOT:** Assume partition key distributes evenly without validation.

**Mitigation:**
- Document partition key skew risk: "order_id may skew during sales events. Max throughput per partition: 10k msg/sec."
- Fallback: "If single partition becomes bottleneck (lag > 5 min), switch to hash(order_id, shard_id) to spread across partitions."
- Monitoring: "Alert if partition lag differs by >100k messages (indicates skew)."
- Alternative: "For orders, consider round-robin (null key) if ordering not required, or hierarchical: partition by customer_id (higher cardinality)."

**Escalation:** NEEDS_INFRA_CHANGE — If partition skew expected, may need custom partitioner or topic redesign. Cannot accept default partitioning without simulation.

---

## Edge Case 6: Consumer lag grows indefinitely

**Symptom:** Notification consumer processes events at 100 msg/sec. Producer publishes at 1000 msg/sec. Consumer lag grows from 0 → 10k → 100k → 1M messages. At 1M, consumer can't catch up (Kafka retention = 7 days, messages expire). Notifications lost forever.

**Do NOT:** Assume consumer can always catch up.

**Mitigation:**
- Lock consumer throughput in contract: "Notification consumer must process >= producer rate (at least 1000 msg/sec)"
- Capacity planning: "Allowable consumer lag = retention_period * (1 - throughput_headroom). If retention = 7 days and headroom = 20%, max lag = 5.6 days."
- SLA: "Consumer lag must never exceed 1 hour. If lag > 1 hour, scale consumers or throttle producer."
- Monitoring: Track consumer lag per group, alert at 50% of acceptable lag

**Escalation:** NEEDS_INFRA_CHANGE — If consumer cannot match producer throughput, BLOCKED. Requires consumer scaling or producer rate limiting before contract lock.

---

## Edge Case 7: Schema registry unavailability breaks all consumers

**Symptom:** All topics use Confluent Schema Registry for validation. Registry goes down. Producers cannot validate schemas, fail all writes. Consumers cannot deserialize, fail all reads. Topic effectively dead for 30 minutes.

**Do NOT:** Make schema registry a hard dependency.

**Mitigation:**
- Cache schema locally: "Consumers must cache schemas from registry (5 minute TTL). If registry unavailable, use cached schema."
- Fallback: "If schema validation fails, pass raw bytes to consumer logic. Consumer handles schema mismatch gracefully (log, skip, or DLQ)."
- Monitoring: "Track schema registry availability. Alert if unavailable for >1 minute."
- SLA: "Schema registry must be highly available (99.9%). Maintain redundant registry instances."

**Escalation:** NEEDS_INFRA_CHANGE — If schema registry not highly available, BLOCKED. Requires redundancy or fallback before accepting contract.

---
name: contract-event-bus
description: "WHEN: Council has identified event bus conflicts across services and needs a locked contract. Negotiates topic schema, versioning, idempotency, ordering, retention, consumer groups, and dead-letter queues before any producer or consumer is written."
type: rigid
effort: high
requires: [brain-read]
version: 1.0.1
preamble-tier: 3
triggers:
  - "design event contract"
  - "define event schema"
  - "event bus spec"
  - "message schema"
allowed-tools:
  - Read
  - Edit
  - Write
  - AskUserQuestion
---

# Contract Event Bus Skill

## Human input

Resolve every human-decision fork (NEEDS_CONTEXT / NEEDS_COORDINATION / NEEDS_INFRA_CHANGE / BLOCKED / WAIVER) through **`AskUserQuestion`** (in `allowed-tools`) — never a prose-only "reply if…". Canonical convention: [`skills/_shared/human-input.md`](../_shared/human-input.md).

## Step 0 — Recall prior contracts (before negotiating)

This skill declares `requires: [brain-read]` — exercise it. Before proposing the event contract: `brain_recall`/grep the product topology (`products/<slug>/forge-product.md`) and any existing `event-contract.md` + prior event/topic decisions for the affected domain, so this contract supersedes rather than duplicates prior locks. Record the resulting `contract_id` (brain decision id / commit SHA) in the LOCK checklist.

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

The locked contract documents five areas: **(1) Topic Design** (name convention, partition key/count, retention, compression), **(2) Schema Versioning** (formal schema + forward/backward/full compatibility rules + registry), **(3) Idempotency & Ordering** (key field, dedup window, per-partition vs global ordering matrix, exactly-once vs at-least-once), **(4) Consumer Guarantees** (consumer-group strategy, offset/commit policy, rebalance behavior, max in-flight), and **(5) Dead-Letter Queues & Retry** (DLQ naming, transient vs permanent classification, exponential backoff, replay).

Full fields, options, config blocks, and worked code for all five areas in [reference/contract-structure.md](reference/contract-structure.md). Anti-patterns catalog (no partition key, infinite retention, field removal without major bump, auto-commit without error handling, no DLQ, single-partition ordering, no idempotency key) in [reference/examples.md](reference/examples.md).

---

## Example Output: Complete Event Bus Contract

**File:** `~/forge/brain/prds/<task-id>/contracts/event-contract.md` (council convention: `<domain>-contract.md`)

A complete, signed-off worked contract for a Payment Service (topics table, full Avro schema with enum + compatibility level, idempotency window, ordering guarantees, consumer-group config table, DLQ schema + retry + on-call SLA + replay process, sign-off block) is in [reference/examples.md](reference/examples.md).

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

Seven failure modes the contract must pre-empt. Resolve every escalation fork via `AskUserQuestion` ([`skills/_shared/human-input.md`](../_shared/human-input.md)). Full symptom / Do-NOT / mitigation for each in [reference/edge-cases.md](reference/edge-cases.md).

| # | Edge case | Escalation |
|---|---|---|
| 1 | Schema evolution adds a required field mid-stream (old producers omit it) | NEEDS_COORDINATION — backfill + add-optional-first plan |
| 2 | Ordering guarantees differ between services sharing a partition key | NEEDS_CONTEXT — per-topic ordering requirement |
| 3 | DLQ defined but unmonitored → silent data loss | NEEDS_INFRA_CHANGE — DLQ monitoring is mandatory; else BLOCKED |
| 4 | Consumer-group rebalancing causes duplicate processing (double-charge) | NEEDS_COORDINATION — manual commit + idempotency; else BLOCKED |
| 5 | Partition-key skew breaks scaling assumptions (hot partition) | NEEDS_INFRA_CHANGE — custom partitioner / redesign |
| 6 | Consumer lag grows indefinitely past retention → messages lost | NEEDS_INFRA_CHANGE — consumer scaling / producer rate limit; else BLOCKED |
| 7 | Schema registry unavailability breaks all producers + consumers | NEEDS_INFRA_CHANGE — local cache + HA registry; else BLOCKED |

---

## Decision Tree: Event Delivery Guarantee

**Q: What happens if a message is processed twice?**

- **Duplicate processing is acceptable** (notifications, analytics, logs) → **At-Least-Once**. Idempotent processing required unless the op is naturally idempotent or duplicate side-effects are provably harmless (see Edge Case 4 — rebalancing can re-deliver and double-charge). Commit offsets only after the side-effect commits.
- **Duplicate processing must not happen** (payments, inventory, ledger) → **Exactly-Once** (effectively-once via idempotency key + dedup cache, e.g. Redis 24h TTL + manual commit; true EOS needs Kafka transactions).
- **At most one delivery, duplicates impossible** → **At-Most-Once** (commit before processing; messages lost on crash). Analytics sampling only — NOT for payments/inventory/orders/ledgers.

Full per-model pros/cons/cost, the decision-flow diagram, and the "Delivery Guarantee" contract-commitment template (model, duplicate handling, consumer implementation, monitoring thresholds) in [reference/examples.md](reference/examples.md).

---

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] All topic names follow the `domain.entity.action` convention and are agreed by both producer and all consumer teams — no generic names like `events` or `updates`
- [ ] Event schema is locked in a formal format (Avro, Protobuf, or JSON Schema) registered in the schema registry — not prose-only description
- [ ] Delivery guarantee (at-least-once, exactly-once, or at-most-once) is documented per consumer group, with the matching idempotency and deduplication strategy specified
- [ ] `contract_event_status: negotiated` is set in the `shared-dev-spec.md` frontmatter — not `draft` or `open`
- [ ] No unresolved producer/consumer disagreements remain: DLQ destination, retention period, consumer group IDs, and schema evolution/compatibility policy are all locked and signed off by every affected team

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

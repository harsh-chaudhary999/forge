---
name: eval-driver-bus-kafka
description: "WHEN: qa-semantic-csv-orchestrate or run_semantic_csv_eval dispatches an automation step that requires Kafka message verification. Functions: connect(), produce(topic, message), consume(topic, assertion), verify(topic, schema), teardown()."
type: rigid
requires: [brain-read]
version: 1.0.1
preamble-tier: 3
triggers:
  - "eval Kafka bus"
  - "run Kafka eval"
  - "event bus eval"
allowed-tools:
  - Bash
---

# eval-driver-bus-kafka

**Runner dispatch:** **`qa-semantic-csv-orchestrate`** / **`run_semantic_csv_eval.py`** routes **`Surface: kafka`** rows in **`qa/semantic-automation.csv`** to this driver. Do not invoke this skill directly unless you are implementing or debugging the runner.

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

## Reference (load on demand)

The full API, examples, protocol details, edge-case code, and deep guidance live in
**`reference/kafka-reference.md`** (Agent Skills progressive disclosure). This SKILL.md is the operational
contract: runner dispatch, discipline (anti-pattern / iron law / red flags), and decision logic.

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

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] Every scenario step has an entry in `qa/semantic-eval-run.log` (no silent skips).
- [ ] Each step outcome is one of: `PASS`, `FAIL`, `BLOCKED_DEPENDENCY`, `SKIPPED` (with reason), `CONTEXT_GAP` — no unclassified results.
- [ ] `qa/semantic-eval-manifest.json` written with `kind: semantic-csv-eval` and a non-placeholder `outcome`.
- [ ] Kafka consumer group confirmed at correct offset before publish; message schema validated after consume.
- [ ] `python3 tools/verify/verify_forge_task.py --task-id <id> --brain <brain>` exits 0.

## Cross-References

- **eval-driver-api-http** — HTTP trigger for message-producing endpoints
- **eval-product-stack-up** — Bring up Kafka broker before eval
- **qa-semantic-csv-orchestrate** — Coordinate Kafka eval with API/DB assertions in **`qa/semantic-automation.csv`**
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

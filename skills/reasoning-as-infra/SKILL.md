---
name: reasoning-as-infra
description: "WHEN: Council is reasoning about a PRD. You are the infra perspective (MySQL/Redis/Kafka/ES). Analyze for database, caching, events, search, monitoring, scaling."
type: rigid
effort: high
requires: [brain-read]
version: 1.0.2
preamble-tier: 1
triggers:
  - "reasoning for infra"
  - "how should infrastructure work"
  - "infra architecture"
allowed-tools:
  - Write
  - mcp__*
---

# Reasoning as Infrastructure

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "No infra changes needed for this PRD" | Every PRD that touches data touches infra. Silence is not analysis — it is a missed dependency that surfaces as a production incident. |
| "We'll tune the cache later" | Cache TTL and invalidation strategy must match consistency requirements. Post-launch tuning creates production incidents when stale data causes silent failures. |
| "Schema is flexible, we'll adjust" | Every schema adjustment after launch is a migration. Unplanned migrations block rolling deploys and risk data loss without a rollback plan. |
| "Monitoring can wait until launch" | Post-launch monitoring means no baseline. Without a baseline, you cannot distinguish anomaly from normal. Instrument during build. |
| "Kafka config is just operational detail" | Partition count and retention cannot be changed after messages start flowing. Lock topic decisions before spec freeze or rebuild later under load. |

## Iron Law

```
INFRA PRODUCES ANALYSIS ON EVERY PRD. EVERY SCHEMA CHANGE HAS A MIGRATION PLAN. EVERY CACHE KEY HAS A NAMING PATTERN AND TTL. EVERY KAFKA TOPIC HAS PARTITION COUNT AND RETENTION LOCKED BEFORE SPEC FREEZE.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Infra surface says "no infrastructure changes needed"** — Every PRD that touches data, caching, or events touches infra. STOP. Produce analysis even if it confirms no new tables, cache keys, or topics are required.
- **Schema migration plan is absent from infra analysis** — Schema changes without migration plans cause data loss or downtime. STOP. Enumerate every migration step (add column, backfill, drop old, cut over) before spec freeze.
- **Redis key naming pattern is not specified** — Unspecified key patterns cause key collisions between services. STOP. Define the full key pattern and TTL for every cache entry before locking.
- **Kafka topic naming and partitioning are left unspecified** — Topic decisions cannot be changed after messages start flowing. STOP. Lock topic names, partition count, retention, and compression before spec freeze.
- **"We'll scale it later" appears in infra analysis** — Scaling decisions made at design time are cheap. Scaling decisions made under production load are expensive and risky. STOP. State explicit scaling approach.
- **Rollback procedure for schema migration is absent** — Irreversible migrations with no rollback plan mean production incidents with no recovery path. STOP. Define rollback for every destructive migration step.
- **Infra reasoning depends on app/web surface outputs before they are available** — Sequential reasoning means missed cross-dependencies. STOP. Run all surfaces in parallel, then resolve conflicts in negotiation.

**Before reasoning about any infrastructure component (Dockerfile, nginx config, terraform, CI pipeline, port allocation):** Read the scan-codebase output for this repo:
- `~/forge/brain/prds/<task-id>/codebase/<role>/structure.txt` — full file inventory including existing Dockerfiles, configs, and scripts
- `~/forge/brain/prds/<task-id>/codebase/<role>/code-style.md` — existing naming conventions for services, volumes, networks, and environment variables
- `SCAN.json` hub scores (if present) — identifies shared infrastructure files referenced by multiple services

Never assume service names, port numbers, or environment variable names — always derive from existing infra files. If `code-style.md` is absent, run `/scan-codebase` first.

---

You are the infrastructure team (database, caching, events, search, observability). Given a locked PRD, reason about:

## 1. Database (MySQL)

What schema changes? What migrations? What safety gates?

Example:
- PRD: "Users can save favorites"
- Infra says: "CREATE TABLE favorites (id BIGINT, user_id BIGINT, product_id BIGINT, created_at TIMESTAMP, updated_at TIMESTAMP, PRIMARY KEY(id), UNIQUE(user_id, product_id), INDEX(user_id), INDEX(product_id))"
- Backward compatibility: column is nullable on old code, code rolls out first
- Migration: downtime-free (add column, backfill, remove old column) OR feature-flagged

What indexes? What partitioning?

## 2. Caching (Redis)

What gets cached? What are the keys? What's the TTL? When does it invalidate?

Example:
- User profile: `user:{user_id}` → expires 1h
- Favorites list: `user:{user_id}:favorites` → expires 30m, invalidates on POST/DELETE
- Product hot-zone: `product:{product_id}:summary` → expires 10m
- Invalidation: publish to Kafka `cache.invalidated` topic, listeners refresh

What about thundering herd? What about stale-while-revalidate?

## 3. Events (Kafka)

What events? What's the schema? What about idempotency and ordering?

Example:
- Topic: `favorites.changed`
- Schema: `{ event_id, user_id, product_id, action: "added"|"removed", timestamp, idempotency_key }`
- Ordering: by `user_id` partition key (all one user's events are ordered)
- Idempotency: deduplication window 24h, key = `{idempotency_key}`, consume-deduplicate pattern

What's the publish guarantee? (at-most-once, at-least-once, exactly-once)?

## 4. Search (Elasticsearch)

What gets indexed? How does it stay consistent with the database?

Example:
- Index: `products`
- Mapping: `{ id, name, description, category, price, availability, last_updated }`
- Refresh policy: 1s (near real-time)
- Consistency: dual-write (MySQL write + ES write in same transaction) OR event-sourced (Kafka → ES consumer)
- Reindex strategy: blue-green or rolling

## 5. Monitoring

What metrics? What alerts? What SLOs?

Example:
- Metrics:
  - DB: query latency p50/p95/p99, connections, slow queries, replication lag
  - Cache: hit rate, evictions, memory usage
  - Events: lag, failures, dead letters
  - Search: query latency, indexing lag, index size
- Alerts:
  - DB replication lag > 5s
  - Cache hit rate < 80%
  - Event lag > 1m
  - ES indexing lag > 30s
- SLOs:
  - Query latency p99 < 100ms
  - Event delivery within 10s
  - Search freshness < 5s

---

## Escalation transport (council subagent)

This skill runs as an **autonomous council subagent** that does **not** share the
human's chat — so it does **not** call `AskUserQuestion`. To escalate, write a
flagged marker block into `council/infra.md`: `[BLOCKED] …`, `[NEEDS-COORDINATION] …`,
or — critically — `[CONFLICT] …` when infra reasoning surfaces a constraint that
**breaks an already-negotiated contract** (e.g. a replication/partition limit that
violates the locked DB or cache contract). That `[CONFLICT]` block signals
`council-multi-repo-negotiate` **Edge Case 4** (re-negotiation), rather than silently
proposing a workaround. Never imply a live UI prompt; human tradeoff forks are
surfaced by the conductor (see [`skills/_shared/human-input.md`](../_shared/human-input.md)).

## Output

Write to `~/forge/brain/prds/<task-id>/council/infra.md`:

```markdown
# Infra Perspective

## Reference (load on demand)

The worked output example, edge-case / failure handling, common pitfalls, decision trees,
and deep domain guidance live in **`reference/infra-reasoning-reference.md`** (Agent Skills progressive disclosure).
This SKILL.md is the operational contract: the surface's reasoning framework, discipline,
output spec, and cross-references.

## Post-Implementation Checklist

- [ ] Infrastructure change is idempotent (applying it twice produces the same result).
- [ ] No hardcoded secrets or credentials in IaC files — secrets come from env vars or a secrets manager.
- [ ] Rollback procedure documented for the infra change.
- [ ] Change tested in a staging/dev environment before being applied to production config.
- [ ] Diff of the infra change reviewed by a human before conductor marks deploy complete.

## Cross-References & Sister Skills

### Sister Skills

**scan-codebase:**
- Use before reasoning: Produces `structure.txt`, `code-style.md`, and `SCAN.json` for the target repo
- Required: Read scan outputs before making any naming, port, or convention decisions
- Link: `code-style.md` is the authoritative source for service names, env var naming patterns, and existing Dockerfile conventions

**reasoning-as-backend:**
- Database: Coordinates query patterns, indexes, partitioning strategy
- Cache: Coordinates cache invalidation, read-through caching
- Events: Coordinates event schema, consumer patterns
- Link: Backend reasoning determines data flow, infra supports it

**reasoning-as-web-frontend:**
- Latency SLA: Frontend specifies max acceptable latency (p99 < 200ms)
- Cache TTL: Frontend determines data freshness need
- Retry logic: Frontend implements retries, infra must be idempotent
- Link: Frontend sets constraints, infra provides SLO targets

**reasoning-as-app-frontend:**
- Storage limits: Mobile app storage constraints (cache size < 50MB)
- Offline capability: Requires event sourcing, eventual consistency
- Battery life: Requires efficient network (compression, batching)
- Link: App frontend determines storage/network efficiency requirements

---

### Brain Tools

**Recall prior infra decisions (read) — preferred path: the read-only brain MCP**
(`brain_recall`, `brain_read`, `brain_why`; see [`docs/brain-mcp.md`](../../docs/brain-mcp.md)).
- Use when: starting infra reasoning — check whether the replication strategy,
  caching policy, or partitioning is already locked before proposing a new one.
- `brain_recall "<entity> replication|cache|partition"` (or grep `~/forge/brain/prds/<task-id>/` and `decisions/`). Caveat: the bundled `.mcp.json` ships `mcpServers: {}` — enable with `claude mcp add forge-brain`; cat/grep is the live fallback.

**Record the infra decision (write) — via `brain-write`**, which writes a **markdown
decision file** (not a key=value pair):
- Use when: locking an infra decision (schema, cache strategy, deployment topology).
- Write the surface's reasoning to `~/forge/brain/prds/<task-id>/council/infra.md`
  (and a `decisions/<category>/D<NNN>_<topic>.md` if it's a durable decision), with
  rationale + alternatives. There is no `brain-write key=… value=…` CLI.

---

### D14: Persuasion & Tradeoffs

**When negotiating with other surfaces:**

- **Causal reasoning:** "If we use strong consistency, every read hits primary → we lose read scaling. With eventual consistency + 30s cache, we can read from replica → 5x faster, but data may lag 30s. Cost-benefit: users see slightly old data for 5x speedup."

- **Constraint acknowledgment:** "Web frontend needs p99 latency < 100ms. With database alone (50ms avg, 200ms p99), we need caching. Cache TTL = 5m gives 90% hit rate, keeps latency < 30ms."

- **Risk clarity:** "Single-zone deployment saves 40% cost but risks complete downtime if zone fails. Multi-zone costs 40% more but protects against zone failure. Trade-off: cost vs availability."

---

### Production Readiness Checklist

Before launching:

- [ ] Database schema locked (brain-write)
- [ ] All queries have indexes (explain plan reviewed)
- [ ] Replication lag monitoring set up (alert at 5s)
- [ ] Cache strategy locked (TTL, invalidation, hitrate target)
- [ ] Connection pool sized for 2x peak load
- [ ] Kafka idempotency keys implemented
- [ ] Elasticsearch schema designed (no future reindex surprises)
- [ ] Monitoring deployed (latency, hits, lag, pool utilization)
- [ ] Alerts configured (actionable, low false-positive)
- [ ] Failover tested (manual or automatic)
- [ ] Rollback plan written (code rollback, feature flag disable, data rollback)
- [ ] Load test passed (2x expected peak, latency stable)
- [ ] Runbook written (what to do if alert fires)

---

## Council Questions to Ask

When reviewing other surfaces' proposals:

**To Backend:**
- What's the query pattern? (so we can design indexes)
- Max size of the data? (so we can partition MySQL)
- Consistency requirements? (so we know the cache TTL)
- Volume expectations? (so we tune pool sizes)

**To Web/App:**
- What's the user-facing latency SLA? (so we know the cache TTL)
- How often do you need fresh data? (so we know refresh_interval)
- Do you need full-text search or exact match? (so we know ES analyzer)

**To Self:**
- Will the cache strategy cause thundering herd on miss?
- Is the idempotency window long enough?
- Are the MySQL indexes sufficient for the query patterns?
- Will ES lag cause visible stale data?
- Are the alerts actionable and low-false-positive?

## Checklist

Before submitting infra reasoning to council:

- [ ] All schema changes include migration steps, rollback plan, and backward-compatibility check
- [ ] All Redis keys have naming patterns and explicit TTLs locked
- [ ] All Kafka topics have partition count, retention policy, and compression defined
- [ ] Scaling approach documented with explicit numbers (no "scale later")
- [ ] Monitoring and alerts specified with concrete thresholds before spec freeze
- [ ] Consistency model selected (strong/causal/eventual) with rationale
- [ ] No infra decision marked TBD, "to be determined," or deferred to post-launch

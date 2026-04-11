---
name: reasoning-as-infra
description: WHEN: Council is reasoning about a PRD. You are the infra perspective (MySQL/Redis/Kafka/ES). Analyze for database, caching, events, search, monitoring, scaling.
type: rigid
requires: [brain-read]
---

# Reasoning as Infrastructure

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Infra surface says "no infrastructure changes needed"** — Every PRD that touches data, caching, or events touches infra. STOP. Produce analysis even if it confirms no new tables, cache keys, or topics are required.
- **Schema migration plan is absent from infra analysis** — Schema changes without migration plans cause data loss or downtime. STOP. Enumerate every migration step (add column, backfill, drop old, cut over) before spec freeze.
- **Redis key naming pattern is not specified** — Unspecified key patterns cause key collisions between services. STOP. Define the full key pattern and TTL for every cache entry before locking.
- **Kafka topic naming and partitioning are left unspecified** — Topic decisions cannot be changed after messages start flowing. STOP. Lock topic names, partition count, retention, and compression before spec freeze.
- **"We'll scale it later" appears in infra analysis** — Scaling decisions made at design time are cheap. Scaling decisions made under production load are expensive and risky. STOP. State explicit scaling approach.
- **Rollback procedure for schema migration is absent** — Irreversible migrations with no rollback plan mean production incidents with no recovery path. STOP. Define rollback for every destructive migration step.
- **Infra reasoning depends on app/web surface outputs before they are available** — Sequential reasoning means missed cross-dependencies. STOP. Run all surfaces in parallel, then resolve conflicts in negotiation.

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

## Output

Write to `~/forge/brain/prds/<task-id>/council/infra.md`:

```markdown
# Infra Perspective

## Database (MySQL)

### Schema Changes
```sql
CREATE TABLE favorites (
  id BIGINT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  product_id BIGINT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_user_product (user_id, product_id),
  KEY idx_user_id (user_id),
  KEY idx_product_id (product_id)
);
```

### Migration Plan
1. Add column (nullable) on running db
2. Code deploys with feature flag OFF (reads/writes old column)
3. Backfill in batches (10k rows at a time, 1s sleep)
4. Feature flag ON
5. Drop old column in next release

### Backward Compatibility
- Column is nullable during transition
- Code checks both old and new column, prefers new
- Rollback safe: code reverts to old column, data still there

## Caching (Redis)

### Key Strategy
- `user:{user_id}` → user profile, TTL 1h
- `user:{user_id}:favorites` → user's favorite IDs (array), TTL 30m
- `product:{product_id}:summary` → product view-model, TTL 10m

### Invalidation
- On POST favorites: del `user:{user_id}:favorites`, publish to `cache.invalidated` topic
- On DELETE favorites: same
- On product update: del `product:{product_id}:summary`, publish event

### Thundering Herd
- Use `SET key value EX 1 NX` with exponential backoff on cache miss
- Secondary cache: stale-while-revalidate for 5s (serve stale, refresh in background)

## Events (Kafka)

### Topics & Schemas
- Topic: `favorites.changed`
  - Partition key: `user_id` (ordered per user)
  - Schema:
    ```json
    {
      "event_id": "uuid",
      "user_id": 123,
      "product_id": 456,
      "action": "added",
      "timestamp": "2026-04-10T12:00:00Z",
      "idempotency_key": "req-abc123"
    }
    ```

### Idempotency
- Deduplication window: 24h
- Store: Redis set `dedup:{idempotency_key}` with EX 86400
- Logic: on consume, check redis, if exists skip, else process & set key

### Ordering Guarantee
- By partition key (user_id): all of one user's events are ordered
- Cross-user events are independent

## Search (Elasticsearch)

### Index Structure
- Index: `products`
- Mapping:
  ```json
  {
    "id": { "type": "keyword" },
    "name": { "type": "text", "analyzer": "standard" },
    "description": { "type": "text" },
    "category": { "type": "keyword" },
    "price": { "type": "float" },
    "availability": { "type": "keyword" },
    "last_updated": { "type": "date" }
  }
  ```

### Consistency Strategy
- Dual-write: MySQL write → Kafka event → ES consumer
- Kafka consumer: batch index (bulk API), 100ms window, retry on 5xx
- Reindex: blue-green (create new index, reindex all, switch alias)

### Refresh Policy
- `refresh_interval: 1s` (near real-time, balance latency/load)

## Monitoring & Observability

### Key Metrics
- DB:
  - Query latency: p50, p95, p99
  - Connections: current, max pool
  - Slow queries: queries > 1s
  - Replication lag: in seconds
- Cache:
  - Hit rate: % of reads from cache vs db
  - Evictions: per minute
  - Memory usage: % of max
  - TTL expiry rate: per minute
- Events:
  - Lag: latest offset vs consumer offset (seconds)
  - Failures: failed publishes per minute
  - Dead letters: messages in DLQ per minute
  - Throughput: messages per second
- Search:
  - Query latency: p50, p95, p99
  - Indexing lag: time from Kafka to indexed (seconds)
  - Index size: bytes
  - Shard health: unassigned shards

### Alerts
- DB replication lag > 5s (page)
- Cache hit rate < 80% for 5m (warn)
- Event lag > 1m (page)
- ES indexing lag > 30s (page)
- DB slow queries > 10 per minute (warn)
- Redis memory > 90% (warn)

### SLOs
- Query latency p99 < 100ms (99.9% uptime)
- Event delivery within 10s (99.95% uptime)
- Search freshness < 5s (99% uptime)
- Cache availability 99.99% (failures < 1 per million)

---

**Ready for:** Council negotiation
```

## Anti-Pattern: "We'll figure it out in Prod"

Do NOT write:
- "Schema TBD"
- "We'll cache something"
- "Events later"
- "Search can be best-effort"

Every detail must be decided and written down BEFORE code starts. Infra changes are the hardest to roll back.

---

## Edge Cases & Failure Scenarios

### Edge Case 1: Database Connection Pool Exhaustion

**Scenario:** Slow queries block new connections. A single bad query holds 20 connections for 30s. All 100 pool connections are claimed. New requests queue infinitely.

**Detection:**
- Metric: Connection pool utilization > 95% for 1m
- Metric: Queued requests > 10
- Metric: Average query latency p99 > 2s (vs baseline 50ms)
- Alert: "DB connection pool > 90% utilization" (warn at 90%, page at 95%)

**Immediate Action:**
1. Kill slow queries: identify queries in state "running" > 30s via `SHOW PROCESSLIST`
2. Lower connection pool size gracefully: set max_connections temporarily to 80, drain excess
3. Degrade features: disable non-critical queries (search filters, analytics)
4. Page oncall: escalate to database team

**Recovery:**
1. Root cause: find slow query in logs, check query plan with EXPLAIN
2. Fix: add missing index, rewrite query, or update statistics
3. Monitor: verify query latency returns to baseline before reopening feature
4. Prevent: add query timeout (max 5s for user-facing reads)

---

### Edge Case 2: Cache Stampede / Thundering Herd

**Scenario:** User's profile cached at key `user:{user_id}`, TTL 1h. At exactly 1h, 1000 concurrent requests hit. Cache miss triggers 1000 database queries simultaneously. DB CPU spikes to 95%.

**Detection:**
- Metric: Cache hit rate drops from 85% to 20% in 1m
- Metric: DB query count spike > 500 QPS (vs baseline 100 QPS)
- Metric: DB CPU > 80%
- Alert: "Cache hit rate < 70% for 5m" (page)

**Immediate Action:**
1. Increase TTL: from 1h to 2h to spread misses
2. Enable stale-while-revalidate: serve stale cache for 5m, refresh async
3. Implement jitter: add ±10% random offset to TTL so misses don't align
4. Rate limit refresh: use SET key EX TTL NX to prevent duplicate writes

**Recovery:**
1. Monitor: verify cache hit rate returns to 80%+
2. Prevent: implement cache warming job (refresh hot keys every 50m, before expiry)
3. Long-term: use consistent hashing or predictive refresh

---

### Edge Case 3: Event Consumer Lag Spike

**Scenario:** Kafka topic `orders.created` has 10k msg/s producer. Consumer processes at 8k msg/s. Lag grows 2k msg every second. After 5m, lag = 600k messages. Consumer takes 10m to catch up.

**Detection:**
- Metric: Consumer lag seconds = (latest_offset - consumer_offset) / 1000 msg/s
- Alert threshold: lag > 1m (60s) → warn, > 5m (300s) → page
- Metric: Consumer processing latency p99 > baseline by 50%
- Alert: "Kafka consumer lag > 5m" (page)

**Immediate Action:**
1. Scale consumer: add 2 more consumer instances (if parallelizable by partition key)
2. Check for rebalancing: look for "consumer group rebalancing" in logs (stop/start cycle)
3. Check processor: if avg processing time > 1s, find blocking operation
4. Degrade features: if order processing is non-critical, pause and resume later
5. Page: escalate to platform team

**Recovery:**
1. Root cause: identify why throughput dropped (code change, database slow, external API timeout)
2. Fix: revert code, optimize query, increase external API timeout
3. Backfill: consumer will catch up once lag is flowing
4. Prevent: add pre-deploy load test, alert on consumer latency p99

---

### Edge Case 4: Elasticsearch Reindex Timeout

**Scenario:** Products index has 500M documents. Reindex operation (blue-green migrate) starts. After 2h, only 60% reindexed. 4h timeout approaches. Heap memory at 85%. JVM GC pauses hit 2s every 30s.

**Detection:**
- Metric: Reindex progress < 50% after 2h (expected: 100M docs/h)
- Metric: ES heap memory > 80%
- Metric: GC pause time > 1s (indicates memory pressure)
- Alert: "ES reindex lag > 2h for 500M docs" (page)

**Immediate Action:**
1. Pause reindex: stop reindex task, keep intermediate index
2. Increase heap: if allowed, bump JVM heap from 16GB to 24GB
3. Tune reindex: reduce batch size from 5000 to 2000, add throttle (slice_max_concurrent=1)
4. Extend timeout: modify reindex request timeout from 4h to 8h

**Recovery:**
1. Resume reindex with tuned parameters
2. Monitor progress: should hit 20-30M docs/h now
3. Root cause: data model changed (larger docs), need to adjust expectations
4. Prevent: pre-test reindex on production-scale data, measure throughput

---

### Edge Case 5: MySQL Replication Lag During Write Spike

**Scenario:** E-commerce site flash sale. 50k writes/s hit primary. Secondary replica can only handle 40k/s. Replication lag grows 10k/s. After 2m, lag = 1.2M events. Readers on secondary see stale inventory (false "out of stock").

**Detection:**
- Metric: Replication lag seconds > 5 → warn, > 30 → page
- Metric: Write latency on primary p99 > baseline by 100%
- Metric: Apply time on secondary > 2s/s
- Alert: "DB replication lag > 30s" (page)

**Immediate Action:**
1. Route reads to primary: disable read-only replicas, failover read traffic
2. Scale secondary: increase replica instance size (CPU, disk I/O)
3. Degrade inventory checks: cache inventory, disable real-time updates
4. Throttle writes: add client-side backpressure (rate limit to 40k/s)

**Recovery:**
1. Monitor replica: apply lag should decrease as writes normalize
2. Wait for convergence: once lag < 5s, safe to route reads back to secondary
3. Root cause: replica hardware undersized for write volume
4. Prevent: capacity plan for 2x peak load on replicas

---

### Edge Case 6: Partition Key Skew in Kafka

**Scenario:** Events published to `user-actions` topic partitioned by `user_id`. One influencer user has 1M followers. All their events go to partition 0. Partition 0 gets 50k msg/s, partition 9 gets 100 msg/s. Consumer group has 10 instances but partition 0 falls behind, lag = 5m while partition 9 is current.

**Detection:**
- Metric: Partition lag varies by > 10x (partition 0 lag=300s, partition 9 lag=10s)
- Metric: Consumer instance for partition 0 has latency p99 > 5s
- Alert: "Kafka partition skew > 10x" (warn)

**Immediate Action:**
1. Add sub-partitioning: change partition key from `user_id` to hash(`user_id` + `timestamp/60`) to distribute hot user
2. Add dedicated consumer: assign 3 instances to partition 0, 1 to others
3. Degrade features: if follower events non-critical, sample (process 1 in 10)

**Recovery:**
1. Rebalance: after code deploy, rebalance consumer group
2. Monitor: verify partition lag converges
3. Prevent: monitor partition size distribution, alert if any partition > 2x average

---

### Edge Case 7: Redis Out-of-Memory (OOM) Eviction

**Scenario:** Redis max memory 64GB. Cache fills to 95%. New cache writes trigger LRU eviction. Hit rate drops from 90% to 70%. Application latency increases 3x.

**Detection:**
- Metric: Redis memory > 95% of max
- Metric: Evictions per minute > 1000
- Metric: Cache hit rate drops > 20% within 5m
- Alert: "Redis memory > 90%" (warn), "> 95%" (page)

**Immediate Action:**
1. Reduce TTLs: from 1h to 30m cache expiration
2. Selective purge: delete low-value caches (product recommendations TTL → 5m)
3. Scale Redis: add new node, migrate shards
4. Feature degrade: disable optional caches (analytics)

**Recovery:**
1. Monitor: memory should drop to 70-80% after TTL reduction
2. Root cause: data size grew 50%, cache strategy didn't scale
3. Prevent: implement cache eviction budget (never exceed 80% memory)

---

### Edge Case 8: Migration Blocking Issue

**Scenario:** Add `status` column to `orders` table. Migration locks table for 2h on 5B row table. All read/write traffic blocks. User-facing latency increases to 30s. Site functionally down.

**Detection:**
- Metric: Table lock detected (via `SHOW OPEN TABLES WHERE In_use > 0`)
- Metric: Query queue > 100 (queries waiting for lock)
- Metric: User latency p99 > 5s (vs 100ms baseline)
- Alert: "Query queue > 50" (page)

**Immediate Action:**
1. Kill migration: cancel ALTER TABLE
2. Rollback: table lock released, traffic normalizes
3. Route traffic: temporarily route to read replica for reads

**Recovery:**
1. Use online migration tool: MySQL 5.7+ supports instant ADD COLUMN for some cases
2. Use gh-ost: ghost tool for online migrations (no table lock)
3. Dark rollout: deploy code to read new column, backfill async, cutover later
4. Schedule: run migration during maintenance window (low traffic)

---

### Edge Case 9: Disk Space Running Out

**Scenario:** MySQL data directory 2TB. Database grows 100GB/month. After 20m, 2.05TB used. Disk full. Writes start failing. Replication breaks.

**Detection:**
- Metric: Disk usage > 90% → warn, > 98% → page
- Metric: Write failures (error "disk full")
- Metric: Replication lag > 60s (replication fails on secondary)
- Alert: "Disk usage > 90%" (warn)

**Immediate Action:**
1. Emergency cleanup: delete old transaction logs, temporary tables
2. Expand volume: increase EBS/disk size (if on cloud, resize online)
3. Pause writes: if disk still full, degrade to read-only
4. Page: escalate immediately

**Recovery:**
1. Add capacity: scale to 5TB (2.5x current)
2. Prevent: set up alerting at 80%, weekly monitoring
3. Root cause: data retention policy too long, need to archive old data

---

## Common Pitfalls in Infrastructure Reasoning

### Pitfall 1: "Assume Cache Hit Rate Will Be 95%+"

**Reality:** Typical cache hit rates for diverse workloads are 70-85%. New features often start at 40-50%.

**Why it matters:** If you design assuming 95% hit rate, your database will be undersized for the real 75% rate. You'll hit connection exhaustion or slow query problems.

**Right approach:**
- Design for realistic hit rates: 70-80% for user-specific data, 85-90% for hot products
- Monitor actual hit rate in staging: test with real traffic patterns
- Set alert thresholds at 75% (page if below), to catch misses before latency degrades
- Over-provision database: assume worst-case 60% cache hit rate

---

### Pitfall 2: "Connection Pool Large Enough to Handle 10x Traffic"

**Reality:** Connection pools have hard limits (MySQL default max_connections = 151). Oversizing causes memory bloat, GC pauses, and eventual exhaustion under spike.

**Why it matters:** A pool sized for 10x will use 10x memory, cause context switching, and still exhaust under 50x spike. Better to fail fast with a right-sized pool than slowly degrade with an oversized one.

**Right approach:**
- Size pool for 2x expected peak: if 100 QPS, use pool of 20-30 (200ms avg latency per connection)
- Use queue with timeout: new requests wait max 5s, then fail gracefully
- Alert when utilization > 80%: gives 5m to scale before exhaustion
- Add circuit breaker: if connection wait > 5s, degrade features rather than queue infinitely

---

### Pitfall 3: "Ignoring Replication Lag for Eventual Consistency"

**Reality:** Even with "eventual consistency", users see inconsistencies. User updates password, immediately logs in, gets 404 on secondary replica (password not synced yet).

**Why it matters:** Reads on stale replicas cause application errors, user confusion, data loss (if they retry and create duplicates).

**Right approach:**
- After writes: route reads to primary for 10s (window where replication completes)
- For user-specific data: always read from primary if write < 1m ago
- Measure replication lag: alert if > 5s, page if > 30s
- Accept lower QPS: never push replica to limits, keep headroom for lag

---

### Pitfall 4: "Retry Logic Without Idempotency"

**Reality:** Network request fails. Client retries. Server processes the same request twice. Duplicate charges, duplicate orders, data corruption.

**Why it matters:** Retries are essential for reliability, but they create duplicates without idempotency keys. The system appears to work in happy path (95% of traffic), fails in retry path (5% of traffic). Hard to debug.

**Right approach:**
- Every API request has idempotency_key (UUID): request + key = atomic
- Deduplication window ≥ 24h: server stores key → result, returns cached result on retry
- Kafka events have idempotency_key: dedup consumer tracks key in Redis/DB
- Document contract: "Retries are safe, guaranteed exactly-once"

---

### Pitfall 5: "Single Availability Zone is Fine (Save Cost)"

**Reality:** Zone goes down (network issue, hardware failure, AWS maintenance). All databases, caches, and services in that zone are unreachable.

**Why it matters:** Single-zone architecture causes complete downtime in event of zone failure. Recovery from backup takes hours. Users lose data.

**Right approach:**
- Distribute across ≥ 2 zones: primary in zone A, replica in zone B
- Replication must be cross-zone: allow one zone to fail completely
- Test failover quarterly: simulate zone failure, ensure automatic failover works
- Accept cost: HA costs 50% more (2 zones, 2 databases), but prevents catastrophic failure

---

### Pitfall 6: "Elasticsearch Schema Design is Flexible (Ship Fast)"

**Reality:** After 3 months, realize you need a field you didn't index. Need to reindex 2B documents (takes 8h, site slow). Or document structure changes, breaks existing queries.

**Why it matters:** ES schema changes are painful and slow. Early design mistakes compound.

**Right approach:**
- Design schema upfront: list all fields that might be searched/filtered/sorted
- Index everything: disk space is cheap, indexing time is expensive
- Use versioning: if schema must change, create new index, switch alias gradually
- Review with backend: coordinate schema with application query patterns

---

### Pitfall 7: "No Monitoring Until Post-Launch"

**Reality:** Launch the feature. Users report slowness. You don't have latency metrics. You can't find the bottleneck (is it DB? Cache? Network?). Site is down, you're debugging in dark.

**Why it matters:** Monitoring during normal operation is 100x easier than during crisis. You need baselines to detect anomalies.

**Right approach:**
- Deploy monitoring code with feature code: instrument every critical path
- Set SLOs before launch: p99 latency < 200ms, cache hit > 80%, replication lag < 5s
- Alert on deviation from baseline: not just absolute thresholds
- Weekly metrics review: spot trends before they become incidents

---

## Scaling Decision Tree

**Question 1: What's the bottleneck?**

| Bottleneck | Signal | Solution |
|---|---|---|
| CPU | DB CPU > 80% | Optimize queries (add index, rewrite), vertical scale (bigger instance) |
| Memory | Cache evictions increasing, hit rate dropping | Scale cache (more nodes), reduce TTL, optimize cache key strategy |
| I/O (disk) | DB disk util > 90%, slow queries latency > 5s | Add replicas (read scaling), partition data (write scaling), vertical scale |
| Network | Bandwidth > 80% capacity | Compress data (cache compression), reduce batch size, add more nodes |
| Connections | Pool utilization > 95% | Increase pool size, add connection pooler (PgBouncer), optimize app connection usage |

**Question 2: Vertical vs Horizontal Scaling?**

| Axis | Vertical (Bigger) | Horizontal (More Nodes) |
|---|---|---|
| Database | Works up to 2-4TB data. Beyond needs sharding. | Not possible for single-node (no horizontal MySQL). Use replicas for read scaling only. |
| Cache | Works up to 1TB per instance. Beyond ~256GB, memory cost high. | Distribute cache across 10+ nodes (Redis Cluster, Memcached). |
| Kafka | Single broker: up to 50k msg/s. Beyond needs more brokers. | Add brokers (scales linearly), partition data (parallelism). |
| Elasticsearch | Single shard: 50M-200M docs, up to 200GB. | Add shards (parallelism) or nodes (replication). |

**Question 3: Partitioning Strategy?**

| Strategy | When to Use | Trade-offs |
|---|---|---|
| **By user_id** (most common) | User-centric data (profiles, preferences, orders). Ensures all user data on same shard. | Load skew if some users >> others. Hot users bottleneck single shard. |
| **By time** (time-series) | Logs, events, metrics. New data in new partition. | Hard to query across time ranges. Need to union results from multiple partitions. |
| **By hash** (consistent hash) | Distribute evenly regardless of data. | All user data scattered across shards. Need to query all shards for user. |
| **By range** (range-based) | Customer ID ranges (1-1M, 1M-2M, ...). | Requires manual rebalancing as ranges grow/shrink. |
| **By geography** | Multi-region deployment. | Cross-region queries slow. Data residency compliance. |

**Question 4: Connection Pool Sizing Formula**

```
Pool Size = (Num Connections Needed) × (Avg Query Time ms) / 1000 ms

Example:
- Need to handle 100 QPS
- Avg query time = 50ms
- Pool Size = 100 × 0.05 = 5 connections

Conservative (2x buffer):
- Pool Size = 100 × 0.05 × 2 = 10 connections
- Max pool = 20 (queue excess requests)
```

**Question 5: Cache TTL Tuning Strategy**

| Data Freshness Need | Suggested TTL | Rationale |
|---|---|---|
| Real-time (< 1s stale) | 10-30s | Frequent misses. Expensive. Use for critical data. |
| Near real-time (< 1m stale) | 1-5m | Balance. Most user-facing data. |
| Eventually consistent (< 1h stale) | 10m-1h | Low freshness need. Long TTL saves DB. |
| Static (doesn't change) | 24h+ or never expire | Product info, reference data. Invalidate on update only. |
| Hot data (read 1000x/s) | 5-10m | Even 1m misses cause DB spike. Shorter TTL. |
| Cold data (read 1x/min) | 30m-1h | Longer TTL saves space. Misses rare. |

**Trade-off: Shorter TTL = more cache misses = more DB load. Longer TTL = stale data = poor UX.**

---

## Failure Scenario Handbook

### Database Failures

#### Failure: Connection Exhaustion

**Metrics to Watch:**
- `mysql_global_status_threads_connected` (current connections)
- `db.connection_pool.utilization_percent` (pool fullness)
- `db.connection_pool.queued_requests` (requests waiting)

**Immediate Action (< 5 min):**
1. Identify slow queries: `SHOW FULL PROCESSLIST WHERE time > 30`
2. Kill suspects: `KILL QUERY process_id` (stops query, keeps connection)
3. Set max_connections lower: `SET GLOBAL max_connections = 80` (stops new connections, prevents crash)
4. Degrade features: stop non-critical queries (search, analytics)

**Recovery (5-30 min):**
1. Root cause: add logging to identify slow queries
2. Add index or optimize query: re-run, verify latency < 100ms
3. Increase pool size: if legitimate load, adjust pool from 20 → 30
4. Test: load test to verify no regression

**Prevention:**
- Alert at 80% utilization (pool of 20: alert at 16 connections)
- Add query timeout: `SET SESSION max_execution_time = 5000` (5s max)
- Monitor slow query log: queries > 1s logged, reviewed daily

---

#### Failure: Replication Lag

**Metrics to Watch:**
- `mysql_slave_status_seconds_behind_master` (replication lag in seconds)
- `mysql_slave_status_seconds_behind_master > 5` (warn), `> 30` (page)
- `mysql_slave_sql_running_seconds` (time to apply events)

**Immediate Action (< 5 min):**
1. Check secondary status: `SHOW SLAVE STATUS\G` → look for `Seconds_Behind_Master`
2. Check for slow query on secondary: `SHOW FULL PROCESSLIST` → identify blocking apply
3. Route reads to primary: disable secondary in connection pool
4. Page: escalate to database team

**Recovery (5-30 min):**
1. Kill slow query on secondary (if safe): `KILL QUERY process_id`
2. Increase replica resources: bigger CPU/memory for binary log processing
3. Wait for lag to converge: monitor until < 5s
4. Root cause: was secondary undersized? Was there a data sync issue?

**Prevention:**
- Capacity plan: replica CPU = primary CPU (can't be slower at same throughput)
- Monitor replica lag continuously: alert at > 5s
- Test failover: quarterly failover to ensure replicas can take over

---

#### Failure: Slow Query Spike

**Metrics to Watch:**
- `db.query_latency_ms.p99` (99th percentile query time)
- `db.queries_per_second` (throughput)
- `db.slow_queries_count` (queries > 1s)

**Immediate Action (< 5 min):**
1. Identify slow queries: tail slow query log or query `performance_schema.events_statements_summary`
2. Check EXPLAIN: `EXPLAIN SELECT ...` → look for full table scan (rows >> expected)
3. Add missing index: identify columns in WHERE/JOIN that lack indexes
4. Rewrite query: if index doesn't help, rewrite (push filter earlier, add covering index)

**Recovery (5-30 min):**
1. Deploy index change: `CREATE INDEX idx_name ON table(column)` (online in MySQL 5.7+)
2. Verify improvement: re-run slow query, latency should drop
3. Test on staging: ensure query plan is stable
4. Monitor: ensure no regression in other queries

**Prevention:**
- Review query patterns before code ship: backend reasoning discusses query plan
- Monitor index creation success: alert if `Creating index ... ` runs > 10m
- Weekly slow query review: top 10 slow queries analyzed

---

### Cache Failures

#### Failure: Cache Miss Spike

**Metrics to Watch:**
- `cache.hit_rate_percent` (should be 80%+, alert if < 70%)
- `cache.miss_count_per_minute` (sudden increase = spike)
- `db.queries_per_second` (should drop when cache hits increase)

**Immediate Action (< 5 min):**
1. Check cache connection: `redis-cli PING` → should respond PONG
2. Check cache memory: `redis-cli INFO memory` → look for `used_memory_human`
3. Check hit rate trend: spike today vs yesterday?
4. If memory full: evictions_per_minute > 1000 → scale cache

**Recovery (5-30 min):**
1. If cache process dead: restart Redis instance
2. If memory full: add new cache node, migrate data
3. If query pattern changed: rebuild cache keys (full database scan)
4. Warm cache: pre-fill hot keys from database before traffic spike

**Prevention:**
- Monitor cache memory: alert at 80%, page at 95%
- Alert on hit rate drop: page if < 75% for 5+ minutes
- Auto-scaling: trigger cache scale-out when memory > 80%

---

#### Failure: Cache Stampede

**Metrics to Watch:**
- `cache.hit_rate_percent` drops 20%+ in < 1m
- `db.queries_per_second` spikes 5x+ suddenly
- `db.cpu_percent` spikes from 30% → 80%

**Immediate Action (< 1 min):**
1. Enable stale-while-revalidate: serve expired keys for 5s while refreshing async
2. Increase cache TTL: from 1h → 2h (spreads expirations)
3. Add jitter: TTL = base_ttl + random(0, base_ttl * 0.1) (±10% randomness)
4. Implement distributed lock: use Redis SET key EX 1 NX to ensure only 1 refresh

**Recovery (1-10 min):**
1. Verify cache hit rate returns to 80%+
2. Root cause: was there a cache flush? A code deploy that cleared keys?
3. Prevent: implement cache warming (refresh hot keys every 50m before expiry)

**Prevention:**
- Use consistent TTLs: avoid multiple keys expiring at same time
- Monitor hit rate volatility: alert if variance > 20%
- Load test: simulate cache eviction under load

---

### Event Bus Failures

#### Failure: Consumer Lag Spike

**Metrics to Watch:**
- `kafka.consumer.lag_offset` (how many messages behind)
- `kafka.consumer.lag_seconds` = lag_offset / producer_rate (seconds to catch up)
- `kafka.consumer.processing_latency_ms.p99` (time per message)

**Immediate Action (< 5 min):**
1. Check consumer group status: `kafka-consumer-groups --group group_name --describe` → see lag per partition
2. Check for rebalancing: `consumer group rebalancing` in logs (stops processing during rebalance)
3. Check processing latency: if p99 > 1s, find blocking operation (DB query, external API)
4. Scale consumers: if lag growing, add consumer instances

**Recovery (5-30 min):**
1. If rebalancing: check for crashes/network issues, restart consumers
2. If processing slow: optimize code (reduce database queries, cache external API)
3. If producer rate spiked: add more consumer instances to parallelize
4. Monitor lag: should decrease once processing normalizes

**Prevention:**
- Alert on consumer lag: warn at > 1m, page at > 5m
- Monitor processing latency: alert if p99 > 1s (baseline should be < 100ms)
- Capacity plan: ensure consumer throughput ≥ producer throughput * 1.2x (20% headroom)
- Weekly lag review: check max lag per partition, identify skew

---

#### Failure: Message Loss

**Metrics to Watch:**
- `kafka.producer.failures_count` (messages that failed to send)
- `kafka.broker.under_replicated_partitions` (replicas not in-sync)
- `kafka.consumer.committed_offset` vs `broker.latest_offset` (gaps indicate loss)

**Immediate Action (< 5 min):**
1. Check broker status: are all brokers healthy? (broker logs for errors)
2. Check replication: `kafka-topics --describe --topic topic_name` → in-sync replicas < expected = loss risk
3. Check producer: is producer sending with acks=all? (required for durability)
4. Page: escalate immediately

**Recovery (1-60 min):**
1. If broker down: restart or failover to replica
2. If replication broken: repair replica (may require re-sync)
3. If producer bug: fix code to use acks=all (default is acks=1, can lose messages)
4. Assess damage: how many messages lost? Can we replay from backup?

**Prevention:**
- Configure durability: acks=all (wait for all replicas), min.insync.replicas=2
- Monitor under-replicated partitions: alert if any partition < 2 replicas
- Test failover: kill broker, ensure replicas take over without message loss
- Backup events: store events in S3 for recovery

---

### Search Failures

#### Failure: Indexing Lag

**Metrics to Watch:**
- `elasticsearch.indexing_lag_ms` (time from event to indexed)
- Alert: lag > 30s (warn), > 2m (page)
- `elasticsearch.documents_indexed_per_second` (should match producer rate)

**Immediate Action (< 5 min):**
1. Check consumer status: is ES consumer running? (check process, logs)
2. Check indexing latency: `_stats` endpoint → look for indexing rate
3. Check index size: if huge, indexing will be slow
4. Check ES health: `_cluster/health` → look for unassigned shards
5. Degrade feature: if lag > 5m, disable search features temporarily

**Recovery (5-30 min):**
1. If consumer crashed: restart consumer, lag will catch up
2. If indexing slow: check heap memory (> 90% causes GC), reduce batch size
3. If shard failed: ES will re-allocate, wait for recovery
4. Monitor: verify lag drops back to < 30s

**Prevention:**
- Alert on indexing lag: page if > 2m
- Monitor ES heap: alert if > 85%
- Capacity plan: ES should handle 2x expected indexing rate
- Test reindex: pre-test large reindex operations for time estimate

---

#### Failure: Shard Allocation Failure

**Metrics to Watch:**
- `elasticsearch.unassigned_shards_count` (shards without home)
- `elasticsearch.active_shards_percent_as_number` (should be 100%)
- Alert: unassigned_shards > 0 (warn immediately)

**Immediate Action (< 5 min):**
1. Check cluster health: `GET _cluster/health` → see which index has unassigned
2. Check node status: are all nodes up? (nodes join/leave cluster)
3. Try to allocate: `POST _cluster/reroute --retry-failed` (retry failed allocations)
4. If disk full: free space on nodes (delete old indices, increase capacity)
5. Page: escalate to search team

**Recovery (5-60 min):**
1. Root cause: node crash, disk full, network partition?
2. Fix: bring node back online, free disk space, resolve network issue
3. Rebalance: ES will automatically re-allocate shards
4. Verify: wait for all shards to be assigned

**Prevention:**
- Monitor shard allocation: alert if unassigned_shards > 0
- Capacity plan: keep disk usage < 85%, headroom for shard allocation
- Multi-zone deployment: distribute shards across zones

---

## Consistency Model Decision Tree

**Question 1: What's the user expectation?**

| User Expectation | Consistency Model | Example |
|---|---|---|
| "Immediate" (write then read same value) | Strong | Bank transfer, account balance, inventory |
| "Soon" (read within seconds of write) | Causal | User profile update, preference change |
| "Eventually" (read may be stale for minutes) | Eventual | Product recommendations, view count |
| "Best effort" (read may be old or missing) | Weak | Analytics, audit logs |

**Question 2: How to implement each model?**

### Strong Consistency

**Definition:** Read always sees the latest write, even by other users.

**How:**
- Always read from primary database (never replicas)
- Serialize writes (transactions)
- Cache TTL = 0 (no cache, or cache only after read-your-write)

**Cost:** High latency (no replicas for read scaling), high database load

**Example:**
```
POST /account/transfer (write)
  → INSERT transaction in primary
  → Commit (durable)
  
GET /account/balance (read)
  → Query primary (always latest)
  → Return balance
```

---

### Causal Consistency

**Definition:** If B depends on A, reads must see A before B. But independent events can be stale.

**How:**
- Write to primary, wait for replication to ≥1 replica (typically < 100ms)
- Read from primary for 1m after write, then replicas
- Use vector clocks or version numbers

**Cost:** Moderate latency, moderate database load

**Example:**
```
POST /profile/update (user updates name)
  → Write to primary
  → Wait for replication (replica ack)
  → Return to client (took 50ms)
  
GET /profile (user immediately reads own profile)
  → Read from primary for next 60s (reads own write)
  
GET /profile/:user_id (another user reads the profile)
  → Can read from replica (after 60s window)
```

---

### Eventual Consistency

**Definition:** Reads may be stale. All events eventually propagate.

**How:**
- Write to primary, return immediately (async replication)
- Replication lag typically < 5s
- Cache aggressively (long TTL)
- Replicas lag by 5-30 seconds

**Cost:** Low latency, low database load, stale reads

**Example:**
```
POST /product/:id/view (user views product)
  → Increment counter in primary (async)
  → Return immediately
  
GET /product/:id (user reads product, may see old view count)
  → Read from replica (fast, but view count lag 5-30s)
```

---

### Weak Consistency

**Definition:** Reads may be arbitrarily old. Fire-and-forget.

**How:**
- Write to cache only (no database)
- No replication
- Data loss acceptable

**Cost:** Minimal latency, high data loss risk

**Example:**
```
POST /analytics/event (log user click)
  → Write to Redis only (async flush to DB)
  → Return immediately
  → Data loss OK (analytics, not critical)
```

---

**Question 3: Cache TTL by Consistency Model**

| Model | Cache TTL | Rationale |
|---|---|---|
| Strong | 0 or invalidate on write | No stale cache. Defeats purpose of caching. Rarely used. |
| Causal | 1m for read-your-write, then 10m | Cache writes for 1m (user sees own write), then longer for others |
| Eventual | 5-30m | Stale cache acceptable, long TTL saves DB |
| Weak | 1h+ or no expiry | Data loss OK, maximize cache benefit |

---

**Question 4: Choosing Consistency for Common Features**

| Feature | Consistency | Why |
|---|---|---|
| Account balance | Strong | User expects immediate accuracy, errors cause complaints |
| Inventory count | Strong | Prevent overselling, customer trust |
| User profile | Causal | User expects own edits immediate, others see within 1m |
| Product recommendations | Eventual | Stale OK, user doesn't expect perfect freshness |
| Order status | Eventual | May lag 30s, user refreshes manually |
| Analytics | Weak | Complete accuracy not required, speed matters |
| Search results | Eventual | Indexing lag OK (1-2m), user refreshes if needed |

---

## Deployment & Migration Patterns

### Pattern 1: Zero-Downtime Database Migrations

**Scenario:** Add new column to `users` table. Migrate data. Keep service running.

**Timeline:**
```
Phase 1: Prepare (pre-deployment, 30 min)
  - Create column (nullable): ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT NULL
  - Verify column created, not used yet

Phase 2: Code Deploy (0-5 min downtime if needed)
  - Code deployed with feature flag OFF
  - Code reads/writes old column only
  - New column is present but unused
  
Phase 3: Backfill (1-2 hours, running in background)
  - Backfill job: SELECT id FROM users WHERE status IS NULL LIMIT 10000
  - Update in batches of 10k, sleep 1s between batches
  - Monitor progress, ensure replication not lagging
  
Phase 4: Cutover (5 min)
  - Feature flag ON
  - Code now reads/writes new column
  - Old column still present for rollback
  
Phase 5: Cleanup (next release, 5 min)
  - Drop old column: ALTER TABLE users DROP COLUMN old_column
  - Verify code doesn't reference old column
```

**Safety:**
- Rollback safe: old column exists, code checks both, prefers new
- Replication safe: backfill is slow to not overload secondary
- Feature flag safe: if new column broken, flip flag OFF, revert reads to old

---

### Pattern 2: Blue-Green Elasticsearch Reindex

**Scenario:** Elasticsearch index schema changes. Reindex 2B documents without downtime.

**Timeline:**
```
Phase 1: Create green index
  - Create new index "products_green" with new schema
  - Apply reindex: POST _reindex source=products_blue, dest=products_green
  - Reindex runs in background (takes 2-4 hours for 2B docs)
  
Phase 2: Verify green
  - When green 100% reindexed: run validation
  - Sample 1000 random docs, verify schema correct
  - Run test queries on green, verify results match blue
  
Phase 3: Switch alias
  - Update alias: products → products_green (was products_blue)
  - All traffic switches to green immediately
  - Blue still exists for rollback
  
Phase 4: Cleanup
  - After 24h: delete blue index (save disk space)
```

**Safety:**
- No downtime: alias switch is atomic
- Rollback easy: alias points back to blue if green broken
- Parallel: reindexing doesn't affect blue (normal read/write traffic continues)

---

### Pattern 3: Feature Flag Driven Rollout

**Scenario:** Add new caching layer. Gradually increase traffic without full deployment.

**Code:**
```python
def get_user_profile(user_id):
  if feature_flag_enabled('use_cache_v2'):
    try:
      return redis_v2.get(f'user:{user_id}')
    except Exception:
      # fall back to database
      pass
  return database.query(f'SELECT * FROM users WHERE id={user_id}')
```

**Rollout:**
```
Canary (5% of traffic):
  - Feature flag: use_cache_v2 = 5%
  - Monitor: cache hit rate, latency, errors
  - Wait 30m: ensure stable
  
Ramp (25% of traffic):
  - Feature flag: use_cache_v2 = 25%
  - Monitor: cache memory, evictions
  - Wait 1h: ensure stable
  
Production (100%):
  - Feature flag: use_cache_v2 = 100%
  - All traffic uses v2
  - Continue monitoring for 24h
```

**Rollback:**
- Feature flag: use_cache_v2 = 0
- All traffic reverts to database
- Instant, no code redeploy needed

---

### Pattern 4: Canary Deployment (Kubernetes)

**Scenario:** Deploy new MySQL connection pool logic. Test on 10% of replicas first.

**Strategy:**
```
Canary (1 replica, 10% traffic):
  - Deploy new code to 1 replica instance
  - Route 10% of read traffic to this replica
  - Monitor latency, errors, CPU
  - Threshold: if p99 latency > baseline + 20%, auto-rollback canary
  
Ramp (3 replicas, 30% traffic):
  - If canary stable for 30m: deploy to 3 more replicas
  - Route 30% of traffic to these 4
  
Production (all replicas, 100%):
  - Deploy to all replicas
  - Monitor for 24h for regression
```

**Metrics to Monitor:**
- Latency p99, p95 (should stay within ±5% of baseline)
- Error rate (should be < 0.1% vs baseline)
- Connection pool utilization (should be ±10% of baseline)
- CPU usage (should be ±10% of baseline)

---

### Pattern 5: Kafka Consumer Group Upgrade

**Scenario:** Consumer code has bug (doesn't handle certain event types). Fix code, deploy with new consumer group.

**Timeline:**
```
Phase 1: Deploy new consumer group
  - New code in parallel branch: consumer_group_v2
  - Both v1 (old, in prod) and v2 (new, in staging) read same topic
  - v2 doesn't commit offsets yet (run in shadow mode)
  
Phase 2: Validate new consumer
  - v2 runs for 24h without committing
  - Compare v2 output with v1: ensure same messages processed
  - If v2 correct: proceed
  
Phase 3: Switch
  - v1: stop consuming (stop deployment, don't crash)
  - v2: start consuming from v1's last offset (resume processing)
  - If v2 breaks: kill v2, restart v1 (only lost 1-2m of messages)
  
Phase 4: Cleanup
  - After 7 days: delete v1 consumer group (stop alerting)
```

**Safety:**
- No message loss: v1 and v2 read same topic, v2 catches up
- Easy rollback: restart v1 if v2 broken
- Validation: 24h dry-run ensures correctness

---

### Pattern 6: Database Failover & Switchback

**Scenario:** Primary database failing. Failover to replica. Repair primary. Switchback.

**Emergency Failover (< 5 min):**
```
Step 1: Detect failure
  - Alert: primary not responding
  - Confirm: can't connect from multiple regions
  
Step 2: Promote replica
  - Replica becomes new primary
  - DNS: primary → replica (updates in 5-30s)
  - App: automatically reconnects (connection pooler does retry)
  
Step 3: Disable old primary (prevent split-brain)
  - Firewall: block old primary from cluster
  - Or: stop MySQL process
  
Step 4: Monitor new primary
  - Verify writes working: insert test record
  - Verify replicas replicating from new primary
  - Alert: page oncall team
```

**Repair & Switchback (1-4 hours):**
```
Step 1: Repair old primary
  - Hardware: replace disk, reboot
  - MySQL: `RESET MASTER` (clear binary logs), start fresh
  
Step 2: Resync old primary as replica
  - Configure old primary to replicate from new primary
  - Monitor: replication lag until caught up
  
Step 3: Switchback (optional)
  - If old primary healthy: switchback (requires downtime)
  - Or: keep new primary in place, old as replica
```

**Metrics to Monitor:**
- Connection count on new primary (should match old)
- Replication lag on new replicas (should converge < 5s)
- Error rate (should return to normal)

---

## Cross-References & Sister Skills

### Sister Skills

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

**brain-read:**
- Use when: Starting infra reasoning, need to recall prior decisions
- Link: Check if replication strategy, caching policy, partitioning already locked
- Command: `brain-read product={product_id}` → returns prior infra decisions

**brain-write:**
- Use when: Locking infra decision (database schema, cache strategy)
- Link: Record decision + rationale for future reference
- Command: `brain-write key=infra.database.schema value={decision}` → locks decision

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

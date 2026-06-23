# Infra Edge Cases, Failure Scenarios & Common Pitfalls

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

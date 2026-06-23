# Failure Scenario Handbook

## Database Failures

### Failure: Connection Exhaustion

**Metrics to Watch:**
- `db.active_connections` (current connections)
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

### Failure: Replication Lag

**Metrics to Watch:**
- `db.replication.lag_seconds` (replication lag in seconds)
- `db.replication.lag_seconds > 5` (warn), `> 30` (page)
- `db.replication.apply_lag_seconds` (time to apply events)

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

### Failure: Slow Query Spike

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

## Cache Failures

### Failure: Cache Miss Spike

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

### Failure: Cache Stampede

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

## Event Bus Failures

### Failure: Consumer Lag Spike

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

### Failure: Message Loss

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

## Search Failures

### Failure: Indexing Lag

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

### Failure: Shard Allocation Failure

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

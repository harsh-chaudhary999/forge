# Scaling Decision Tree

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

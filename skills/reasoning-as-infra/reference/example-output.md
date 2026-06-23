# Infra Perspective — worked output example

The full `~/forge/brain/prds/<task-id>/council/infra.md` the skill produces:

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

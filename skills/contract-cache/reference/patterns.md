# Cache Contract Patterns — Key Concepts

## 1. Key Structure

Cache keys must follow consistent naming patterns to enable analytics, expiration, and invalidation.

**Namespace Prefixes:**
- `user:` — User-scoped data
- `session:` — Session tokens and state
- `cart:` — Shopping cart operations
- `order:` — Order details and history
- `inventory:` — Stock and availability
- `config:` — Application configuration
- `feed:` — User feed and timeline data

**Key Composition Rules:**
- Use colons (`:`) as delimiters for hierarchical structure
- Include identifiers at the second level: `user:{id}:profile`, `order:{id}:items`
- Add sub-keys for fine-grained access: `user:{id}:profile:avatar`
- Avoid spaces; use underscores for multi-word segments: `user:{id}:two_factor_codes`

**Key Expiration Tagging:**
- Optionally prefix with version for migrations: `v1:user:{id}:profile`, `v2:user:{id}:profile`
- Include expiration strategy hints in documentation: `user:{id}:profile [TTL: 1h, pattern: write-through]`

**Example Structure:**
```
user:{user_id}:profile
user:{user_id}:2fa_codes
user:{user_id}:preferences
session:{session_id}
session:{session_id}:tokens
order:{order_id}:items
order:{order_id}:status
inventory:{product_id}:stock
feed:{user_id}:timeline
feed:{user_id}:notifications:unread
```

---

## 2. TTL Strategy

TTL (Time To Live) should match data freshness requirements and change frequency.

**Freshness Tiers:**

| Tier | TTL Range | Use Case | Examples |
|------|-----------|----------|----------|
| **Hot** | 30 sec–5 min | Frequently accessed, changes often | Inventory counts, user notifications, feed |
| **Warm** | 5–30 min | Regular access, moderate change rate | User profile, session data, order status |
| **Cool** | 1–6 hours | Less frequent access, stable data | Configurations, country lists, category trees |
| **Cold** | 6–24 hours | Rarely accessed, historical data | User statistics, archived orders |
| **Never** | No TTL | Manually invalidated or reference data | Feature flags, static lookups, service registry |

**Rules for Choosing TTL:**

1. **Match business requirements:** If data must be fresh within 5 minutes, set TTL to 5 minutes or less
2. **Account for database load:** Shorter TTLs increase cache misses and DB queries; balance with SLOs
3. **Use probabilistic expiration:** Set TTL slightly higher than requirement, use xfetch (see Stampede Prevention)
4. **Cluster consistency:** For distributed caches, TTL should account for clock skew (add 5-10%)
5. **Version with schema:** If cache format changes, version keys (v1:, v2:) to avoid corruption

**Example TTL Assignment:**
```
user:123:profile → 1 hour (warm, updated when user changes settings)
session:abc123 → 24 hours (warm, extends on activity)
2fa:{user_id}:codes → 5 minutes (hot, security-critical)
order:999:items → 30 minutes (warm, order finalized)
inventory:{product_id}:stock → 1 minute (hot, changes frequently)
config:feature_flags → 6 hours (cool, rarely changes)
user:123:recommendations → 24 hours (cold, computed offline)
```

---

## 3. Invalidation Patterns

Choose invalidation pattern based on consistency requirements and write frequency.

**Cache-Aside (Lazy Loading)**
- **Pattern:** Application checks cache; on miss, fetch from DB and populate cache
- **Pros:** Decouples cache from DB; only caches accessed data; simple to implement
- **Cons:** Cache misses add latency; stale reads possible; thundering herd risk
- **Use When:** Read-heavy workloads; acceptable staleness; variable access patterns
- **Example:**
  ```
  GET user:123:profile
    → Cache miss
    → Fetch from DB
    → SET user:123:profile [data] EX 3600
    → Return to client
  ```

**Write-Through (Synchronous)**
- **Pattern:** Application writes to cache AND database synchronously; both must succeed
- **Pros:** Cache and DB always consistent; no stale reads
- **Cons:** Slower writes (dual latency); cache failures block writes
- **Use When:** Strong consistency required; write-heavy workloads; correctness critical
- **Example:**
  ```
  UPDATE user:123:profile = {email: "new@example.com"}
    → SET user:123:profile [data] (cache)
    → UPDATE profiles WHERE id=123 (DB)
    → Both succeed or both rollback
  ```

**Write-Back (Asynchronous Writeback)**
- **Pattern:** Application writes to cache first; async process flushes to DB later
- **Pros:** Fast writes; cache serves as buffer; reduces DB load
- **Cons:** Data loss risk if cache crashes before flush; eventual consistency only
- **Use When:** Write-heavy analytics; acceptable data loss for seconds/minutes; eventual consistency OK
- **Example:**
  ```
  INCR user:123:activity:count (cache)
    → Async job: flush to DB every 10 seconds or 10K updates
  ```

**Event-Based Invalidation**
- **Pattern:** Cache keys invalidated by domain events (publish-subscribe)
- **Pros:** Decoupled; other services can invalidate cache; reactive
- **Cons:** Eventual consistency; requires event infrastructure
- **Use When:** Microservices architecture; cross-service mutations; eventual consistency acceptable
- **Example:**
  ```
  Event: user.profile_updated → Listener: DEL user:{id}:profile
  Event: order.completed → Listener: DEL feed:{user_id}:timeline (invalidate user feed)
  ```

**Hybrid Patterns:**
- Write-through for critical data + event-based for related cache entries
- Write-back for high-volume metrics + cache-aside for reads

---

## 4. Stampede Prevention

Cache stampede (thundering herd) occurs when many clients miss cache simultaneously and hammer the DB.

**Probabilistic Early Expiration (xfetch)**
- **Concept:** Start refetching cache at 80% TTL with small probability
- **Benefit:** Smooths refetch across time window; reduces spike probability
- **Example:**
  ```
  if (time_since_set > TTL * 0.8) && random() < 0.1:
    → Async refetch from DB
    → Probability of refetch: 10%
    → Evens load over final 20% of TTL
  ```

**Locking/Mutex During Refill**
- **Concept:** Only one client refetches; others wait or use stale value
- **Implementation:**
  ```
  GET user:123:profile
    → Cache miss
    → SET user:123:profile:lock NX EX 5 (acquire lock)
    → If lock acquired: fetch DB, SET user:123:profile
    → If lock failed: wait 100ms, GET user:123:profile (other client is refilling)
    → DEL user:123:profile:lock (release lock)
  ```
- **Benefit:** Single DB query instead of N queries; prevents thundering herd
- **Trade-off:** Adds latency for waiters; requires lock timeout to prevent deadlock

**Fallback Stale Data**
- **Concept:** Serve stale cache while refetching in background
- **Implementation:**
  ```
  GET user:123:profile
    → Cache hit (expired but not deleted)
    → Return stale data to client
    → Background job: async refetch and update
  ```
- **Benefit:** Instant response; no client latency waiting for refetch
- **Trade-off:** Client gets stale data for brief period; acceptable for non-critical reads

**Composite Strategy:**
```
1. Try cache (if fresh, return)
2. If stale + not locked:
   → Acquire lock (SETNX)
   → Trigger async refetch
   → Return stale data immediately
3. If stale + locked (other client refetching):
   → Return stale data (don't wait)
4. If missing:
   → Try lock + fetch (cache-aside)
   → If lock fails, wait for other's refetch
```

---

## 5. Serialization & Consistency

**Serialization Formats:**

| Format | Pros | Cons | Use Case |
|--------|------|------|----------|
| **JSON** | Human-readable, language-agnostic, schema-flexible | Larger size, slower parse | Most services, interop |
| **Binary** (Msgpack, Protobuf) | Compact, fast, schema-strict | Not human-readable, requires definition | High-throughput, size-critical |
| **String** | Simplest, smallest (numeric IDs) | No nested data, manual parsing | Simple values, counters |

**Version Tagging for Migrations:**
- Prefix keys with version when cache format changes: `v1:user:{id}:profile`, `v2:user:{id}:profile`
- Old services read `v1:...`, new services write `v2:...`
- After all services upgraded, delete v1 keys
- Prevents deserialization errors during rolling deployments

**Example Serialization:**
```
// JSON (human-readable)
user:123:profile = {
  "id": 123,
  "email": "john@example.com",
  "created_at": "2025-10-15T10:30:00Z"
}

// Versioned during migration
v1:user:123:profile → old schema (3 fields)
v2:user:123:profile → new schema (5 fields, adds verified_at, role)

// Binary (Msgpack, for hot paths)
inventory:456:stock = <binary msgpack>
  → Smaller footprint, faster encode/decode
```

**Consistency Models:**

| Model | Guarantee | Latency | Use Case |
|-------|-----------|---------|----------|
| **Strong** | Cache and DB always identical | Higher (write-through) | Financial, identity data |
| **Eventual** | Cache and DB converge over seconds | Lower (cache-aside, write-back) | User profiles, feeds, analytics |
| **Probabilistic** | Staleness bounded by xfetch/TTL | Very low (stale reads) | Non-critical: recommendations, counts |

**Choosing Consistency:**
- **Strong:** User auth tokens, payment records, password hashes
- **Eventual:** User profile, session data, order items (refetch-safe)
- **Probabilistic:** View counts, recommendation feeds, feature flag percentiles

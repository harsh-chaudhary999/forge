---
name: contract-cache
description: Negotiate cache contracts (Redis/Memcached). Defines key patterns, TTL strategy, invalidation, stampede prevention, serialization, consistency model.
type: rigid
requires: [brain-read]
---

# contract-cache Skill

Teaches teams to negotiate Redis/Memcached cache contracts. Covers key structure, TTL strategy, invalidation patterns, cache stampede prevention, and serialization for production cache systems.

## Anti-Pattern Preamble: Cache Contract Failures

| Rationalization | The Truth |
|---|---|
| "We'll figure out TTLs later" | TTL IS the contract. Wrong TTL means stale data served to users (too long) or cache misses under load (too short). Every key MUST have an explicit TTL in the contract. No defaults. |
| "Invalidation is simple — just delete the key" | Simple DELETE causes stampede: 1000 concurrent requests all miss cache simultaneously, hammering the database. You need stampede prevention (lock-and-refresh, probabilistic early expiry, or write-through). |
| "Cache is just a performance optimization, not critical" | Cache failures cascade. If Redis goes down and you have no fallback, every request hits the database. Cache IS part of your architecture. Contract must specify fallback behavior (degrade gracefully vs. fail fast). |
| "Both services can write to the same cache key" | Two writers to the same key create race conditions: last-write-wins with no ordering guarantee. The contract must specify exactly ONE owner per key. Cross-service cache access requires read-only contracts. |
| "Serialization format doesn't matter" | Service A writes JSON, Service B expects MessagePack. Service A writes `{user_id: 123}`, Service B expects `{userId: 123}`. Serialization format and field naming must be explicitly contracted. |

---

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Any cache key is specified without an explicit TTL** — A key without a TTL is a memory leak waiting to happen, or stale data served indefinitely. STOP. Every key in the contract must have a concrete TTL value — no "default", no "TBD", no "same as session".
- **Two services are specified as writers to the same cache key** — Two writers create a last-write-wins race with no ordering guarantee, producing unpredictable data. STOP. Each key must have exactly one owner service. Other services may only read.
- **Cache stampede prevention is absent from the contract** — A cache miss under load sends all concurrent requests simultaneously to the database. STOP. Every high-traffic key must specify its stampede prevention strategy (lock-and-refresh, probabilistic early expiry, or write-through).
- **Fallback behavior when cache is unavailable is not specified** — When Redis or Memcached goes down, the system must decide: fail fast or degrade to direct DB reads. Without a specified fallback, behavior is undefined and inconsistent across services. STOP. Every key type must specify its cache-miss fallback.
- **Key naming pattern is not specified with a namespace prefix** — Unnamespaced keys from different services collide silently. STOP. Every key pattern must include a namespace that uniquely identifies the owning service (e.g., `auth:session:{id}`, not just `session:{id}`).
- **Invalidation trigger is described as "on deploy" or "manually"** — Manual invalidation is not a strategy; it will not happen consistently. STOP. Every key must have a programmatic invalidation trigger tied to a specific data mutation event.

## When to Use This Skill

Use this skill when:
- Designing cache layers for high-traffic systems
- Integrating Redis or Memcached into microservices
- Preventing cache stampedes and ensuring consistency
- Documenting cache behavior across teams
- Negotiating service-to-cache contracts

## Key Concepts

### 1. Key Structure

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

### 2. TTL Strategy

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

### 3. Invalidation Patterns

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

### 4. Stampede Prevention

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

### 5. Serialization & Consistency

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

---

## Example: Full Cache Contract

```markdown
# Cache Contract for E-Commerce Service

## Key Structure
- **user:{user_id}:profile** → User account details (email, name, preferences)
- **user:{user_id}:2fa_codes** → Two-factor authentication codes
- **session:{session_id}** → User session token and metadata
- **order:{order_id}:items** → Order line items and quantities
- **order:{order_id}:status** → Current fulfillment status
- **inventory:{product_id}:stock** → Current stock level
- **feed:{user_id}:timeline** → Personalized product recommendations

## TTL Strategy
| Key | TTL | Tier | Reason |
|-----|-----|------|--------|
| user:{id}:profile | 1 hour | Warm | Updated infrequently; acceptable 1h stale |
| user:{id}:2fa_codes | 5 min | Hot | Security-critical; must refresh frequently |
| session:{id} | 24 hours | Warm | Extends on activity; survives across sessions |
| order:{id}:items | 30 min | Warm | Order frozen; infrequent updates |
| inventory:{id}:stock | 1 min | Hot | Changes on every sale; high traffic |
| feed:{id}:timeline | 6 hours | Cool | Computed offline; users accept stale feeds |

## Invalidation
- **Pattern:** Cache-aside for reads; Write-through for profile updates
- **Trigger:** POST /user/{id}/profile → DELETE user:{id}:profile
- **Event-based:** user.profile_updated event → Pubsub trigger invalidates session:{id} (force re-auth)
- **Time-based:** TTL ensures eventual freshness

## Stampede Prevention
- **xfetch:** Refresh inventory:{id}:stock at 80% TTL (every 0.8 sec), 5% probability
- **Mutex:** inventory:{id}:stock:lock (SETNX, 2 sec timeout) during DB refetch
- **Stale fallback:** Return stale inventory count while refetching (brief inconsistency acceptable)

## Serialization
- **Format:** JSON (standard; human-readable for debugging)
- **Version:** v1: prefix for major schema changes (e.g., v2:user:{id}:profile after adding role field)
- **Consistency:** Eventual for most keys; strong consistency for session tokens (write-through)

---
Ready for: Shared dev-spec lock
```

---

## Checklist for Implementation

When implementing a cache contract:

- [ ] Define namespace prefixes for each domain entity
- [ ] Document key composition rules with examples
- [ ] Assign TTL for each key pattern (match freshness SLOs)
- [ ] Choose invalidation pattern (cache-aside, write-through, write-back, event-based)
- [ ] Implement stampede prevention (xfetch + mutex or stale fallback)
- [ ] Choose serialization format (JSON, binary, string)
- [ ] Plan version tagging for schema migrations
- [ ] Document consistency model (strong, eventual, probabilistic)
- [ ] Set up monitoring: cache hit rate, miss rate, latency, evictions
- [ ] Test under load: verify stampede prevention works
- [ ] Document in service contract; share with dependent teams

---

## References & Related Skills

- **brain-read:** Look up past cache contracts and domain decisions
- **reasoning-as-infra:** Analyze caching, database, and scaling requirements
- **contract-api:** Define REST contracts that interact with cached data
- **contract-db:** Define database schemas and denormalization for cache warming

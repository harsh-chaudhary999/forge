---
name: contract-cache
description: "WHEN: Council has identified cache design conflicts across surfaces and needs a locked contract. Negotiates key patterns, TTL strategy, invalidation, stampede prevention, serialization, and consistency model across all services."
type: rigid
requires: [brain-read]
---

# contract-cache Skill

Teaches teams to negotiate Redis/Memcached cache contracts. Covers key structure, TTL strategy, invalidation patterns, cache stampede prevention, and serialization for production cache systems.

## Iron Law

```
EVERY CACHE KEY'S TTL AND INVALIDATION STRATEGY MUST BE NEGOTIATED AT COUNCIL AND LOCKED IN THE CONTRACT BEFORE ANY IMPLEMENTATION BEGINS. NO SERVICE MAY UNILATERALLY CHOOSE ITS OWN TTL OR INVALIDATION LOGIC FOR SHARED KEYS.
```

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

## Checklist

Before claiming completion:

- [ ] Every cache key in the contract has an explicit TTL value — no "default", no "TBD", no "same as session"
- [ ] Each key has exactly one owner service documented — no two services listed as writers to the same key
- [ ] Stampede prevention strategy is specified per high-traffic key (lock-and-refresh, xfetch, or stale fallback)
- [ ] Fallback behavior when cache is unavailable is documented for every key type (fail fast vs. degrade to DB reads)
- [ ] All key patterns include a namespace prefix that uniquely identifies the owning service
- [ ] Invalidation trigger is a programmatic event tied to a specific data mutation — not "on deploy" or "manually"
- [ ] Serialization format and field naming convention are locked and agreed by all consuming services
- [ ] Consistency model is documented per key (strong, eventual, or probabilistic) with staleness SLA

---

## Edge Cases & Escalation Keywords

### Edge Case 1: Key naming collision between two services

**Symptom:** Service A (User Profile) and Service B (User Preferences) both use cache key `user:{user_id}` without namespace. Service A stores `{name: "Alice", age: 30}`. Service B stores `{theme: "dark", notifications_enabled: true}`. On read, Service A gets Service B's data.

**Do NOT:** Assume unique ownership without namespace prefixes.

**Mitigation:**
- Enforce namespace prefixes in contract: `profile:user:{user_id}`, `preferences:user:{user_id}`
- Document ownership: "User Profile service owns `profile:*` keys. User Preferences service owns `preferences:*` keys. No cross-ownership."
- Add validation: If service tries to write/read wrong namespace, reject with error
- TTL tied to namespace: `profile:*` expires in 1 hour, `preferences:*` expires in 6 hours

**Escalation:** BLOCKED if namespace collision detected. Audit all keys in contract before lock.

---

### Edge Case 2: TTL mismatch creates stale data across services

**Symptom:** Cache contract specifies `user:123:profile` TTL = 60 seconds for freshness. Service A reads at 0s, caches locally for 60s. Service B writes update at 30s. Service A doesn't refetch until 60s, serving stale data for 30s beyond TTL.

**Do NOT:** Assume client-side caching respects server TTL.

**Mitigation:**
- Lock contract TTL and document its semantics: "TTL is server-side only. Clients must not cache responses locally beyond server TTL."
- Add cache-control headers: `Cache-Control: max-age=60, must-revalidate` (enforce client-side TTL)
- Alternative: Use shorter server TTL (30s) + `ETag` for client validation without refetch
- Document: "If client caches, multiply server TTL by 0.8 to prevent data older than TTL"

**Escalation:** NEEDS_CONTEXT — Do clients implement their own caching? If yes, coordinate TTLs before lock.

---

### Edge Case 3: Data format incompatibility during serialization

**Symptom:** Service A stores user profile as JSON: `{"user_id": 123, "email": "alice@example.com"}`. Service B expects the same key but deserializes it as Msgpack binary. Deserialization fails silently.

**Do NOT:** Assume serialization format is universal.

**Mitigation:**
- Lock serialization format in contract: "All values use JSON (UTF-8 encoded). No binary formats."
- Document field naming consistency: "All fields use snake_case: `user_id`, `email`, `created_at` (not userId, createdAt)"
- Version keys during format migration: `v1:user:123:profile` (JSON) → `v2:user:123:profile` (new format)
- Validation: Deserialize sample payloads with all consuming services before lock

**Escalation:** BLOCKED if services disagree on serialization. Lock format and validate all services before contract lock.

---

### Edge Case 4: Eviction policy conflict causes unpredictable behavior

**Symptom:** Redis contract specifies `maxmemory-policy: allkeys-lru` (evict least recently used). Service A relies on specific keys never being evicted (expects TTL enforcement). Under memory pressure, Redis evicts Service A's "important" key anyway. Service A crashes.

**Do NOT:** Assume TTL always protects from eviction.

**Mitigation:**
- Define maxmemory policy in contract: "maxmemory-policy = volatile-ttl (only evict keys with TTL, respect TTL)"
- Alternative: Use `allkeys-lru` but document: "Under memory pressure, no key is guaranteed. Services must handle missing keys gracefully."
- Capacity planning: Contract must include memory budget and growth projection
- SLA: "Eviction rate < 0.1% under normal load. If higher, scale Redis cluster."

**Escalation:** NEEDS_INFRA_CHANGE — If Redis memory insufficient for SLA, BLOCKED until infrastructure upgraded.

---

### Edge Case 5: Cache invalidation semantics differ across services

**Symptom:** Service A deletes `user:123:profile` via direct DEL. Service B published `user.profile_updated` event expecting all consumers to invalidate the key. Service B's event handler tries to delete already-deleted key (no-op in Redis, but log spam). Service C subscribes to event, tries to refetch from cache, gets stale data because event arrived late.

**Do NOT:** Mix direct invalidation and event-based invalidation.

**Mitigation:**
- Choose ONE invalidation strategy per key:
  - **Direct**: Service writes to key, owns invalidation via DEL. No events needed.
  - **Event-based**: Service publishes event, other services subscribe and invalidate. Requires event bus contract.
- Lock in contract: "user:{id}:profile is invalidated by direct DEL from Profile Service only."
- Document event delivery guarantee: "Events not guaranteed to arrive before reads. Clients must verify cache freshness via version field."

**Escalation:** NEEDS_COORDINATION — If multiple services invalidate same key, must agree on single strategy before lock.

---

### Edge Case 6: Cache stampede under unexpected traffic spike

**Symptom:** `inventory:{product_id}:stock` TTL = 5 minutes, stampede prevention = xfetch (5% probability at 80% TTL). Under normal load, works fine. Holiday sale causes 100x traffic spike. Xfetch probability insufficient: 1000 requests hit cache simultaneously at 4:00, it expires at 4:05, all 1000 refetch simultaneously, database overloaded.

**Do NOT:** Set stampede prevention probability statically without load headroom.

**Mitigation:**
- Stampede prevention must scale with load: "Use lock-and-refresh (SETNX) for traffic > 100 req/sec on a key. For lower traffic, xfetch 5% is sufficient."
- Document load headroom in contract: "Assumes max 100 requests/sec per key. If higher, increase stampede prevention strength."
- Fallback: "If lock-and-refresh fails, return stale value (serve 1-minute-old data rather than wait)."
- Monitoring: "Alert if cache miss rate > 1% (possible stampede). Add lock-and-refresh immediately."

**Escalation:** NEEDS_CONTEXT — What's the expected peak load? If >100 req/sec per key, lock-and-refresh required, not xfetch.

---

## Decision Tree: Cache Isolation Strategy

**Q: How many services will access each cache key?**

→ **Single service owns key (User Profile service owns all `profile:*` keys)**
  - Model: **Owned Cache**
  - Isolation: Service reads/writes own namespace only
  - Ownership: Clear, documented in contract
  - Invalidation: Owner service controls, direct DEL or write-through
  - Pros: Simple, fast, no coordination needed
  - Cons: Requires careful namespace enforcement
  - Risk: Other services accidentally writing wrong keys
  - Mitigation: Code review + ACLs in Redis (if supported)

→ **Multiple services read, one writes (Inventory service writes, Order/Cart services read)**
  - Model: **Read-Shared Cache**
  - Isolation: Writer owns key, readers are read-only
  - Invalidation: Writer DELs key after mutation
  - Pros: Decouples services, reduces database load
  - Cons: Eventual consistency, readers must handle stale data
  - Consistency: Acceptable staleness depends on key (inventory can be 1min stale, payment cannot)
  - Mitigation: Lock consistency model in contract, document staleness SLA

→ **Multiple services read AND write same key (Distributed counter)**
  - Model: **Shared Mutable Cache**
  - Isolation: Conflict-free data structures only (counters, sets, append-only lists)
  - Invalidation: Event-based (application-level conflict resolution)
  - Pros: Highest throughput for high-contention keys
  - Cons: Complex concurrency, eventual consistency
  - Risk: Last-write-wins causes lost updates, race conditions
  - Mitigation: Use Redis INCR/RPUSH (atomic ops), not read-modify-write, version field to detect conflicts

**Decision Flow:**
```
Who needs to write to this key?
├─ One service only
│  └─ Owned Cache (single namespace)
│     Clear ownership in contract
│     Fast, simple invalidation
│
├─ One writer, multiple readers
│  └─ Read-Shared Cache
│     Define consistency SLA (staleness acceptable?)
│     Invalidation: writer-controlled
│     Must document read-after-write latency
│
└─ Multiple writers
   └─ Shared Mutable Cache
      Use only conflict-free data structures
      INCR for counters, RPUSH for logs (not read-modify-write)
      Eventual consistency only
      Document conflict resolution strategy
```

**Key Commitment in Contract:**
```markdown
# Cache Isolation

## Ownership Model: [Owned | Read-Shared | Shared-Mutable]

### Owned Cache Keys (e.g., profile:user:{id})
- Owner: Profile Service
- Writers: Profile Service only
- Readers: Public (any service can read)
- Invalidation: Profile Service DELs on update
- Consistency: Strong (write-through)

### Read-Shared Cache Keys (e.g., inventory:{product_id}:stock)
- Owner: Inventory Service
- Writers: Inventory Service only
- Readers: Order, Cart, Search services (read-only)
- Invalidation: Inventory Service DELs on stock change
- Consistency: Eventual (1-minute stale acceptable)
- SLA: 95% cache hits, <5% miss rate

### Shared Mutable Cache Keys (e.g., analytics:user:{id}:pageview_count)
- Writers: All services can increment
- Operation: INCR only (atomic, no read-modify-write)
- Consistency: Eventual (counter eventually consistent across servers)
- Conflict resolution: Last-write-wins per INCR (acceptable for metrics)
```

---

## References & Related Skills

- **brain-read:** Look up past cache contracts and domain decisions
- **reasoning-as-infra:** Analyze caching, database, and scaling requirements
- **contract-api:** Define REST contracts that interact with cached data
- **contract-db:** Define database schemas and denormalization for cache warming

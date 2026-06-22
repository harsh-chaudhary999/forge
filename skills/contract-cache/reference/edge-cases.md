# Cache Contract Edge Cases & Escalation Keywords

## Edge Case 1: Key naming collision between two services

**Symptom:** Service A (User Profile) and Service B (User Preferences) both use cache key `user:{user_id}` without namespace. Service A stores `{name: "Alice", age: 30}`. Service B stores `{theme: "dark", notifications_enabled: true}`. On read, Service A gets Service B's data.

**Do NOT:** Assume unique ownership without namespace prefixes.

**Mitigation:**
- Enforce namespace prefixes in contract: `profile:user:{user_id}`, `preferences:user:{user_id}`
- Document ownership: "User Profile service owns `profile:*` keys. User Preferences service owns `preferences:*` keys. No cross-ownership."
- Add validation: If service tries to write/read wrong namespace, reject with error
- TTL tied to namespace: `profile:*` expires in 1 hour, `preferences:*` expires in 6 hours

**Escalation:** BLOCKED if namespace collision detected. Audit all keys in contract before lock.

---

## Edge Case 2: TTL mismatch creates stale data across services

**Symptom:** Cache contract specifies `user:123:profile` TTL = 60 seconds for freshness. Service A reads at 0s, caches locally for 60s. Service B writes update at 30s. Service A doesn't refetch until 60s, serving stale data for 30s beyond TTL.

**Do NOT:** Assume client-side caching respects server TTL.

**Mitigation:**
- Lock contract TTL and document its semantics: "TTL is server-side only. Clients must not cache responses locally beyond server TTL."
- **Server-assisted client-side caching (Redis 7+/RESP3):** `CLIENT TRACKING` + invalidation push lets the server notify RESP3-capable clients the instant a key changes — the purpose-built primitive when clients cache beyond TTL. Trade-off: requires RESP3 clients and server tracking-table memory. Specify it in the contract when clients hold their own cache.
- HTTP-layer fallback: `Cache-Control: max-age=60, must-revalidate`, or a shorter server TTL (30s) + `ETag` for client validation without refetch.

**Escalation:** NEEDS_CONTEXT — Do clients implement their own caching? If yes, coordinate TTLs before lock.

---

## Edge Case 3: Data format incompatibility during serialization

**Symptom:** Service A stores user profile as JSON: `{"user_id": 123, "email": "alice@example.com"}`. Service B expects the same key but deserializes it as Msgpack binary. Deserialization fails silently.

**Do NOT:** Assume serialization format is universal.

**Mitigation:**
- Lock serialization format in contract: "All values use JSON (UTF-8 encoded). No binary formats."
- Document field naming consistency: "All fields use snake_case: `user_id`, `email`, `created_at` (not userId, createdAt)"
- Version keys during format migration: `v1:user:123:profile` (JSON) → `v2:user:123:profile` (new format)
- Validation: Deserialize sample payloads with all consuming services before lock

**Escalation:** BLOCKED if services disagree on serialization. Lock format and validate all services before contract lock.

---

## Edge Case 4: Eviction policy conflict causes unpredictable behavior

**Symptom:** Redis contract specifies `maxmemory-policy: allkeys-lru` (evict least recently used). Service A relies on specific keys never being evicted (expects TTL enforcement). Under memory pressure, Redis evicts Service A's "important" key anyway. Service A crashes.

**Do NOT:** Assume TTL always protects from eviction.

**Mitigation:**
- Define maxmemory policy in contract: "maxmemory-policy = volatile-ttl (only evict keys with TTL, respect TTL)"
- Alternative: Use `allkeys-lru` but document: "Under memory pressure, no key is guaranteed. Services must handle missing keys gracefully."
- Capacity planning: Contract must include memory budget and growth projection
- SLA: "Eviction rate < 0.1% under normal load. If higher, scale Redis cluster."

**Escalation:** NEEDS_INFRA_CHANGE — If Redis memory insufficient for SLA, BLOCKED until infrastructure upgraded.

---

## Edge Case 5: Cache invalidation semantics differ across services

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

## Edge Case 6: Cache stampede under unexpected traffic spike

**Symptom:** `inventory:{product_id}:stock` TTL = 5 minutes, stampede prevention = xfetch (5% probability at 80% TTL). Under normal load, works fine. Holiday sale causes 100x traffic spike. Xfetch probability insufficient: 1000 requests hit cache simultaneously at 4:00, it expires at 4:05, all 1000 refetch simultaneously, database overloaded.

**Do NOT:** Set stampede prevention probability statically without load headroom.

**Mitigation:**
- Stampede prevention must scale with load: "Use lock-and-refresh (SETNX) for traffic > 100 req/sec on a key. For lower traffic, xfetch 5% is sufficient."
- Document load headroom in contract: "Assumes max 100 requests/sec per key. If higher, increase stampede prevention strength."
- Fallback: "If lock-and-refresh fails, return stale value (serve 1-minute-old data rather than wait)."
- Monitoring: "Alert if cache miss rate > 1% (possible stampede). Add lock-and-refresh immediately."

**Escalation:** NEEDS_CONTEXT — What's the expected peak load? If >100 req/sec per key, lock-and-refresh required, not xfetch.

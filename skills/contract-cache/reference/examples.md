# Cache Contract Examples & Isolation Decision Tree

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
- **xfetch:** probabilistic early refresh as the key approaches expiry (e.g. for a 60s-TTL key, the refresh probability rises over the last ~20% of the TTL window — there is no fixed interval; it is computed per read from time-to-expiry and the recompute cost)
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

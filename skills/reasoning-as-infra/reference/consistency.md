# Consistency Model Decision Tree

**Question 1: What's the user expectation?**

| User Expectation | Consistency Model | Example |
|---|---|---|
| "Immediate" (write then read same value) | Strong | Bank transfer, account balance, inventory |
| "Soon" (read within seconds of write) | Causal | User profile update, preference change |
| "Eventually" (read may be stale for minutes) | Eventual | Product recommendations, view count |
| "Best effort" (read may be old or missing) | Weak | Analytics, audit logs |

**Question 2: How to implement each model?**

## Strong Consistency

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

## Causal Consistency

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

## Eventual Consistency

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

## Weak Consistency

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

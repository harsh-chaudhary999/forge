# Backend Reasoning — Edge Cases & Failure Modes

Extended edge-case tables and failure-mode playbooks. The Red Flags / STOP list
that gates reasoning lives in `../SKILL.md`; this file is the deep catalog of
strategies and mitigations.

## Edge Cases (Strategies)

**1. Schema Changes Breaking API Contracts**
- **Problem:** Remove a column from users table → old clients still request that field → silent failures or 500 errors.
- **Strategy:**
  - Add nullable fields first (backward compatible)
  - Deprecate in API (v1 still returns field, v2 removes it)
  - Give clients 6 months migration window before removing old API version
  - Example: User adds `profile_picture` field
    ```sql
    ALTER TABLE users ADD COLUMN profile_picture VARCHAR(255) NULL;
    ```
    API v1: always returns `profile_picture` (null or value)
    API v2: removes `profile_picture` from response
    Deprecation: v1 EOL announced, supported 6 months

**2. Async Workers Delay Consistency (Eventual Consistency Windows)**
- **Problem:** Publish `auth.2fa_enabled` event → Audit Service processes 500ms later → user queries `/auth/2fa/status` within that window → sees stale data.
- **Strategy:**
  - Define SLA: "Audit log visible within 5 seconds of event publication"
  - If faster needed, update primary record synchronously, publish event async
  - Document the eventual consistency window in API response headers:
    ```
    X-Consistency-Window: 5000ms
    X-Event-ID: uuid
    ```
  - Example: 2FA enable endpoint
    ```
    Synchronous: Update users.mfa_enabled = true (blocks response)
    Asynchronous: Publish auth.2fa_enabled event → audit consumer (non-blocking)
    Client sees mfa_enabled = true immediately, audit log appears within 5s
    ```

**3. Rate Limiting and Backpressure Handling**
- **Problem:** Client hammers POST /auth/2fa/verify endpoint → auth service queues requests → downstream event bus fills up → dropped events.
- **Strategy:**
  - Rate limit at API gateway (fail fast with 429)
  - Rate limit at database (connection pool exhaustion → queue requests)
  - Backpressure on event publishing (fail if Kafka queue > threshold)
  - Example:
    ```
    POST /auth/2fa/verify rate limit: 5/min per user
    Returns 429 with:
    {
      "error": "rate_limit_exceeded",
      "retry_after_ms": 12000,
      "limit": 5,
      "window_ms": 60000
    }
    ```
  - Event publishing backpressure:
    ```
    If Kafka lag > 10s, circuit breaker opens
    Instead of publishing to topic, write to DLQ
    Monitoring alert triggered to investigate lag
    ```

**4. Database Migration + Backward Compatibility (Rolling Deploys)**
- **Problem:** Add NOT NULL column without default → rolling deploy starts new code (requires field) before migration finishes → old code (no field) crashes.
- **Strategy:**
  - Step 1: Add nullable column with default
    ```sql
    ALTER TABLE users ADD COLUMN billing_tier VARCHAR(20) NULL DEFAULT 'free';
    ```
  - Step 2: Deploy code that writes to new column (reads old + new, prefers new)
  - Step 3: Backfill existing rows with migration job
  - Step 4: Remove code that writes to old column
  - Step 5: Drop old column (if replacing)
  - Example for renaming column:
    ```
    -- Phase 1: Add new column (backward compat)
    ALTER TABLE users ADD COLUMN created_at_utc TIMESTAMP NULL;
    -- Code now writes to both created_at AND created_at_utc
    
    -- Phase 2: Backfill (jobs/migrate.sql)
    UPDATE users SET created_at_utc = created_at WHERE created_at_utc IS NULL;
    
    -- Phase 3: Cleanup
    -- Code now reads from created_at_utc only
    -- ALTER TABLE users DROP COLUMN created_at; (later, after validation)
    ```

**5. Cross-Service Dependency Failures (Fallback Strategies)**
- **Problem:** User Service calls Auth Service to verify session → Auth Service down → User Service returns 500 → entire app broken.
- **Strategy:**
  - Circuit breaker: if Auth Service fails 5x in 10s, fail open (allow request, log warning)
  - Fallback cache: cache session verification for 30s, use stale data if service down
  - Graceful degradation: if Auth Service down, return `X-Session-Stale: true` header
  - Timeout: all service calls timeout 5s (don't wait forever)
  - Example:
    ```
    GET /user/profile
    
    1. Try to verify session from Auth Service (5s timeout)
    2. If Auth Service down/slow:
       - Check Redis cache for session (30s TTL)
       - If hit: return user profile with header X-Session-Verified: false
       - If miss: return 401 Unauthorized
    3. If Auth Service succeeds: update Redis cache, return profile
    ```

---

## Edge Cases & Failure Modes

### Edge Case 1: Circular Dependency in Backend Logic

**Scenario**: Service A calls Service B, which calls Service C, which calls Service A. This creates a circular dependency that will deadlock or infinitely loop.

**Symptom**: `CircularDependencyError` or request timeout after traversing the same service chain repeatedly. Distributed trace shows: A → B → C → A → B → C → ...

**Do NOT**: Ignore circular dependencies. Do NOT add retry logic as a workaround. Do NOT assume "it won't happen in practice."

**Mitigation**:
- Map all service-to-service calls during backend reasoning to visualize dependency graph
- Verify the graph is acyclic (no service calls itself, directly or indirectly)
- Use dependency inversion: if A needs data from C, have B fetch from C and return to A (don't have B call A)
- For unavoidable circular patterns, use an intermediary queue (A publishes event, B consumes and publishes to C, C publishes back to queue for A)
- Add cycle detection in request headers: if X-Called-By header already contains current service, reject the call

**Example**:
```
# BAD: Circular dependency
User Service calls Order Service
Order Service calls Payment Service
Payment Service calls User Service (to get user details)
→ Deadlock: payment.get_user() → user.verify_payment() → order.get_status() → ... infinite loop

# GOOD: Dependency inversion
User Service calls Order Service
Order Service calls Payment Service
Payment Service calls User Service via in-memory cache (no circular call)
→ User Service pre-populates cache with user details before calling Order Service
```

**Escalation**: `NEEDS_COORDINATION` — Circular dependency indicates service boundary design issue. Coordinate with team to restructure services.

---

### Edge Case 2: Distributed Trace Broken (Missing Correlation ID)

**Scenario**: A request flows through multiple services (A → B → C), but the correlation ID is lost somewhere. Backend team can no longer trace the complete request flow across all services.

**Symptom**: `TraceError: Request arrives at Service B but X-Correlation-ID is missing or changed`. Observability team cannot find complete trace in tracing system (Jaeger, DataDog, etc.).

**Do NOT**: Propagate traces inconsistently. Do NOT assume correlation IDs will be preserved automatically. Do NOT skip tracing "for now" with intention to add later.

**Mitigation**:
- Every request must include `X-Correlation-ID` header (or equivalent: `X-Trace-ID`, `X-Request-ID`)
- Every service-to-service call MUST copy correlation ID to outbound request headers
- Database writes and cache updates must include correlation ID for audit trail
- Async events must include correlation ID in payload (so consumers can associate with original request)
- Test correlation ID propagation explicitly: mock distributed request and verify trace reaches all services

**Example**:
```javascript
# Service A receives request with X-Correlation-ID: abc-123
GET /api/order/123
X-Correlation-ID: abc-123

# Service A calls Service B (MUST propagate correlation ID)
POST /internal/payment/authorize
X-Correlation-ID: abc-123  // MUST be same!
Authorization: Bearer ...

# Service B calls Service C (MUST propagate)
GET /internal/user/456
X-Correlation-ID: abc-123  // MUST be same!

# Service B publishes async event (MUST include in event payload)
{
  "event_id": "uuid",
  "correlation_id": "abc-123",  // REQUIRED
  "user_id": 456,
  "action": "payment_authorized"
}

# Without correlation ID:
# Tracing system cannot link events from A → B → C
# If something fails mid-flow, debugging becomes "where did it fail?" guessing game
```

**Escalation**: `NEEDS_COORDINATION` — Implement correlation ID propagation across all services before launch.

---

### Edge Case 3: Event Bus Ordering Violation (Out-of-Order Processing)

**Scenario**: You publish events to a message bus (Kafka, RabbitMQ) without specifying partition key or consumer group. Events meant to be processed in order (Event A before Event B) arrive out of order.

**Symptom**: `OrderingError: Event B processed before Event A`. Business logic fails (e.g., user account created before user exists, order shipped before payment cleared).

**Do NOT**: Assume event buses guarantee order. Do NOT skip partition key specification. Do NOT use fire-and-forget without tracking.

**Mitigation**:
- Use partition key (Kafka) or message routing key to ensure related events go to same partition/queue
- For user-scoped events, use `user_id` as partition key (all user events process serially)
- For order-scoped events, use `order_id` as partition key
- In consumer, check event ordering: if receiving Event B before Event A, retry or DLQ the out-of-order event
- Document event ordering constraints in event schema (e.g., "user.created must arrive before user.updated")

**Example**:
```javascript
# BAD: No partition key, events arrive out of order
kafka.produce({
  topic: 'user-events',
  // NO partitionKey!
  messages: [
    { event: 'user.created', user_id: 123, timestamp: '2026-04-10T10:00:00Z' },
    { event: 'user.updated', user_id: 123, timestamp: '2026-04-10T10:05:00Z' }
  ]
})
// Consumer might see: user.updated (fails, user doesn't exist!) then user.created

# GOOD: Partition key ensures ordering
kafka.produce({
  topic: 'user-events',
  partitionKey: '123',  // user_id → all events for user 123 go to same partition
  messages: [
    { event: 'user.created', user_id: 123, timestamp: '2026-04-10T10:00:00Z' },
    { event: 'user.updated', user_id: 123, timestamp: '2026-04-10T10:05:00Z' }
  ]
})
// Consumer guaranteed to see: user.created, then user.updated (in order!)
```

**Escalation**: `NEEDS_COORDINATION` — Event bus configuration requires cross-team consensus on partition strategy.

---

### Edge Case 4: Cache Invalidation Race Between Services

**Scenario**: Two services (Service A and Service B) update related data independently. Service A updates the database and invalidates cache. Service B also updates the database and invalidates its own cache. But between A's invalidation and B's invalidation, a read hits the cache and gets stale data from before A's update.

**Symptom**: `ConsistencyError: User sees stale cached value after update. Expected user.name = 'Bob', got 'Alice'`.

**Do NOT**: Assume cache invalidation is atomic across services. Do NOT use client-side polling for consistency. Do NOT skip cache invalidation "it'll update eventually."

**Mitigation**:
- Use event-driven cache invalidation: publish `entity.updated` event, ALL services invalidate their caches from that event
- Define cache ownership clearly: only one service owns the cache for an entity (e.g., User Service caches user data, not Order Service)
- Use cache versioning: when updating entity, increment version number, invalidate all caches tagged with old version
- For critical reads, bypass cache: add flag to request `X-Bypass-Cache: true` for strong consistency needs
- Use cache TTL as safety net: even if invalidation fails, stale cache expires after TTL (e.g., 30s)

**Example**:
```javascript
# BAD: Distributed cache invalidation without coordination
// Service A updates user name
UPDATE users SET name = 'Bob' WHERE id = 123
INVALIDATE CACHE user:123

// Service B might read cache before INVALIDATE completes!
GET user:123 from cache  // Still sees name = 'Alice'!

# GOOD: Event-driven cache invalidation
// Service A updates and publishes event
BEGIN TRANSACTION
  UPDATE users SET name = 'Bob' WHERE id = 123
  PUBLISH EVENT { type: 'user.updated', user_id: 123, version: 2 }
COMMIT

// Service B subscribes to user.updated event
ON user.updated(user_id, version):
  DELETE CACHE user:${user_id}
  RELOAD FROM DATABASE (on next request)

// Now all services invalidate consistently
```

**Escalation**: `NEEDS_COORDINATION` — Cache invalidation strategy must be consistent across all services.

---

### Edge Case 5: Inconsistent Request/Response Validation Between Services

**Scenario**: Service A accepts a request with field `user_type: 'admin' | 'user' | 'guest'`, validates and stores it. Service B reads the same field but validates against a different enum: `user_role: 'superuser' | 'editor' | 'viewer'`. Service A's 'admin' doesn't map to any value in Service B's enum.

**Symptom**: `ValidationError: Service B rejects valid data from Service A because enums don't match`.

**Do NOT**: Assume services will validate consistently. Do NOT hardcode enum values; define them in shared schema. Do NOT skip validation between services.

**Mitigation**:
- Define shared enums in a central schema (OpenAPI, Protobuf, shared constants)
- Every service validates BOTH input (what it receives) and output (what it sends)
- Use versioned API contracts: if enum changes, increment API version and support both old + new
- Document enum transformations between services: if Service A uses 'admin' but Service B expects 'superuser', document the mapping
- Test enum changes explicitly: simulate old client sending old enum value, verify service handles gracefully

**Example**:
```javascript
# BAD: Inconsistent enums
// Service A: user_type in ['admin', 'user', 'guest']
// Service B: user_role in ['superuser', 'editor', 'viewer']
// Service A returns user_type: 'admin'
// Service B receives and tries to match against user_role enum
// → Validation fails, error is confusing

# GOOD: Shared enum definition
// shared-types.ts (shared across services)
export const USER_ROLES = {
  ADMIN: 'admin',
  USER: 'user',
  GUEST: 'guest'
} as const

// Service A validates using shared enum
if (!Object.values(USER_ROLES).includes(userType)) {
  throw new Error('Invalid user type')
}

// Service B validates using same shared enum
if (!Object.values(USER_ROLES).includes(userRole)) {
  throw new Error('Invalid user role')
}

// Now both services agree on valid values
```

**Escalation**: `NEEDS_CONTEXT` — Share schema definitions across services to prevent validation mismatches.

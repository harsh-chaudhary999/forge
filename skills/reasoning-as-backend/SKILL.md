---
name: reasoning-as-backend
description: "WHEN: Council is reasoning about a PRD. You are the backend perspective (REST/gRPC/SQL). Analyze the PRD for API endpoints, data models, service boundaries, async patterns, performance SLOs."
type: rigid
requires: [brain-read]
---

# Reasoning as Backend

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **API endpoints are proposed without versioning strategy** — Unversioned APIs will break clients the moment a field is renamed or a behavior changes. STOP. Every endpoint must include its version (e.g., `v1`, `v2`) and the deprecation policy for old versions.
- **Backend is reasoning in isolation before hearing web/mobile/infra surfaces** — Unilateral backend decisions create mismatched API shapes that web or mobile must work around. STOP. Backend reasoning is input to council negotiation, not a final decision — surfaces must hear each other before contracts lock.
- **Data model is proposed without a migration plan** — A new table or a column change requires migration steps that must be backward-compatible with the running system. STOP. Every schema change must include the migration procedure and rollback plan.
- **Performance SLOs are absent from the reasoning output** — "Fast" is not an SLO. STOP. Every endpoint must state its p95 latency target and maximum throughput in concrete numbers that can be evaluated in an eval scenario.
- **Async patterns are described as "fire and forget" without dead letter queue** — A message that cannot be delivered without a DLQ is permanently lost. STOP. Every async flow must specify what happens to messages that fail delivery: DLQ, retry policy, and alert threshold.
- **Auth requirements are deferred** — An endpoint without explicit auth requirements will be implemented inconsistently across services. STOP. Every endpoint must state its authentication mechanism (Bearer token, API key, session) and authorization check (ownership, role, scope) before council closes.
- **Error codes and response shapes are not specified** — Inconsistent error formats force every client to implement unique parsing logic. STOP. Every endpoint must specify its error response schema and the full set of possible HTTP status codes.

You are the backend team (API design, databases, services, async processing). Given a locked PRD, reason about:

## 1. API Endpoints

What endpoints are required? What's the contract? Versioning? Auth?

Example:
- PRD: "Users can enable 2FA"
- Backend says:
  - POST /auth/2fa/enable (v2, idempotent, token-gated, returns 2fa_secret + recovery_codes)
  - POST /auth/2fa/verify (v2, rate-limited 3/min, returns session token)
  - DELETE /auth/2fa/disable (v2, requires re-auth)
  - GET /auth/2fa/status (v2, cached 10s)

What about request/response schemas? Error codes? Headers?

Example:
```
POST /auth/2fa/enable
Authorization: Bearer {token}
Content-Type: application/json

{
  "method": "totp" | "sms"
}

200 OK
{
  "secret": "JBSWY3DPEBLW64TMMQ======",
  "recovery_codes": ["code1", "code2", ...],
  "qr_code_url": "..."
}

400 Bad Request (invalid method)
401 Unauthorized (expired token)
429 Too Many Requests (rate limit)
```

## 2. Data Models

What's the schema shape? Primary keys? Relationships? Indexes?

Example:
- User table:
  ```sql
  CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_email (email)
  );
  ```

- Sessions table:
  ```sql
  CREATE TABLE sessions (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY idx_user_id (user_id),
    KEY idx_expires_at (expires_at),
    FOREIGN KEY (user_id) REFERENCES users(id)
  );
  ```

- 2FA Recovery Codes table:
  ```sql
  CREATE TABLE mfa_recovery_codes (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    code_hash VARCHAR(255) NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY idx_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
  );
  ```

What about constraints, denormalization, soft deletes?

## 3. Service Boundaries

What service owns what data? What calls which service?

Example:
- **Auth Service** owns: credentials, sessions, 2FA settings, recovery codes
  - Internal APIs: POST /internal/auth/verify-session, GET /internal/auth/user/{id}
  - Owns the source-of-truth for user sessions

- **User Service** owns: profiles, preferences, settings (non-auth)
  - Calls Auth Service for session verification
  - Does NOT call Auth Service for every request (caches session info)

- **Audit Service** owns: audit logs of security events
  - Consumes events from Auth Service (2FA enabled, login, session expired)

What about service-to-service auth? (mTLS, service tokens, API keys)?

## 4. Async Patterns

What happens asynchronously? Queues? Events? Eventual consistency?

Example:
- **On 2FA Enabled:**
  - Publish event: `auth.2fa_enabled` → user-lifecycle topic (partition key: user_id)
  - Event schema:
    ```json
    {
      "event_id": "uuid",
      "user_id": 123,
      "mfa_method": "totp",
      "timestamp": "2026-04-10T12:00:00Z",
      "idempotency_key": "req-abc123"
    }
    ```
  - Audit Service consumes: logs event, doesn't block
  - User Service consumes: updates user preferences async, publishes notification event

- **Session Expiry:**
  - Publish event: `auth.session_expired` → audit topic
  - No consumers block critical path

- **Deadletter handling:**
  - Failed events go to DLQ (dead-letter queue)
  - Monitor and manually replay

What's the publish guarantee? (at-most-once, at-least-once, exactly-once)?

## 5. Performance SLOs

What are the latency targets? Throughput? Storage?

Example:
- **Auth endpoints:**
  - POST /auth/2fa/enable: < 200ms p99 (includes secret generation)
  - POST /auth/2fa/verify: < 100ms p99 (rate-limited, cached lookup)
  - GET /auth/2fa/status: < 50ms p99 (cached 10s)

- **Database:**
  - Single row select (user by ID): < 50ms p99
  - Session lookup by token: < 50ms p99 (on indexed token_hash)
  - Batch insert recovery codes: < 100ms p99

- **Throughput:**
  - Auth service: 10k req/s (with 10x headroom = 100k req/s capacity)
  - Database connection pool: 100 connections, 1000 queries per second per DB

- **Storage:**
  - Users table: 1M rows → ~500MB
  - Sessions table: 100M active sessions → ~5GB (partitioned by expires_at)
  - Recovery codes: 100M codes → ~1GB

What about retry budgets? Timeouts? Circuit breakers?

---

## Output

Write to `~/forge/brain/prds/<task-id>/council/backend.md`:

```markdown
# Backend Perspective

## API Endpoints

### POST /auth/2fa/enable (v2)
- Auth: Bearer token, requires valid session
- Idempotent: yes (idempotency_key header)
- Rate limit: 10/hour per user
- Request:
  ```json
  {
    "method": "totp" | "sms"
  }
  ```
- Response (200):
  ```json
  {
    "secret": "JBSWY3DPEBLW64TMMQ======",
    "recovery_codes": ["code1", "code2", ...],
    "qr_code_url": "https://..."
  }
  ```
- Errors:
  - 400: invalid method
  - 401: expired token
  - 429: rate limited

### POST /auth/2fa/verify (v2)
- Auth: Bearer token (temporary session)
- Idempotent: no
- Rate limit: 5/minute per user (brute-force protection)
- Request:
  ```json
  {
    "code": "123456"
  }
  ```
- Response (200):
  ```json
  {
    "session_token": "...",
    "expires_at": "2026-04-17T12:00:00Z"
  }
  ```
- Errors:
  - 400: invalid code format
  - 401: invalid code
  - 429: rate limited

### DELETE /auth/2fa/disable (v2)
- Auth: Bearer token + password confirmation
- Request:
  ```json
  {
    "password": "..."
  }
  ```
- Response: 204 No Content

### GET /auth/2fa/status (v2)
- Auth: Bearer token
- Cached: 10s
- Response:
  ```json
  {
    "enabled": true,
    "method": "totp",
    "last_verified": "2026-04-10T10:00:00Z"
  }
  ```

## Data Models

### Users Table
```sql
CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  mfa_enabled BOOLEAN DEFAULT FALSE,
  mfa_method VARCHAR(20),
  mfa_secret VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_email (email)
);
```

### Sessions Table
```sql
CREATE TABLE sessions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  token_hash VARCHAR(255) NOT NULL UNIQUE,
  mfa_verified BOOLEAN DEFAULT FALSE,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_user_id (user_id),
  KEY idx_expires_at (expires_at),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### MFA Recovery Codes Table
```sql
CREATE TABLE mfa_recovery_codes (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  code_hash VARCHAR(255) NOT NULL,
  used_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_user_id (user_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

## Service Boundaries

### Auth Service
- **Owns:** users, sessions, MFA settings, recovery codes
- **Exposes (public):**
  - POST /auth/login, POST /auth/logout
  - POST /auth/2fa/enable, POST /auth/2fa/verify, DELETE /auth/2fa/disable
  - GET /auth/2fa/status
- **Exposes (internal):**
  - GET /internal/auth/verify-session/{token} → {user_id, mfa_verified}
  - GET /internal/auth/users/{id} → minimal user info
  - POST /internal/auth/invalidate-sessions/{user_id} → batch invalidate
- **Calls:** User Service (GET /internal/users/{id} for preferences)
- **Auth:** Internal calls use mTLS or service tokens

### User Service
- **Owns:** profiles, preferences, device info
- **Does NOT own:** credentials, sessions
- **Calls:** Auth Service for session verification (caches for 10s)
- **Publishes:** user.profile_updated events

### Audit Service
- **Owns:** audit logs
- **Consumes:** auth.*, user.* events
- **Does NOT call:** any other service (async only)

## Async Patterns

### Event: auth.2fa_enabled
- Topic: `user-lifecycle`
- Partition key: `user_id`
- Schema:
  ```json
  {
    "event_id": "uuid",
    "user_id": 123,
    "mfa_method": "totp",
    "timestamp": "2026-04-10T12:00:00Z",
    "idempotency_key": "req-abc123"
  }
  ```
- Consumers:
  - Audit Service: log event (doesn't block critical path)
  - User Service: notify user (via push/email)
- Publish guarantee: at-least-once (deduplication window 24h)
- Retention: 7 days

### Event: auth.session_created
- Topic: `auth-events`
- Schema: {event_id, user_id, mfa_verified, timestamp, idempotency_key}
- Consumers: Audit Service only
- Guarantee: at-least-once

### Event: auth.session_expired
- Topic: `auth-events`
- Automatic publish when session.expires_at < NOW()
- Consumers: Audit Service, cache invalidation

## Performance SLOs

### API Latency
- POST /auth/2fa/enable: < 200ms p99 (secret generation cost)
- POST /auth/2fa/verify: < 100ms p99 (cache hit on user lookup)
- GET /auth/2fa/status: < 50ms p99 (cached in Redis)
- DELETE /auth/2fa/disable: < 150ms p99 (password verification cost)

### Database Performance
- Single-row select: < 50ms p99
- Session lookup by token_hash: < 50ms p99
- Batch insert 10 recovery codes: < 100ms p99
- Expired session cleanup: < 1s for 1000 rows

### Throughput
- Auth service: 10k req/s nominal, 100k req/s peak capacity
- Session table QPS: 1000 req/s nominal per DB instance
- Event publishing: 1000 events/s nominal

### Storage
- Users table (1M rows): ~500MB
- Sessions table (100M active): ~5GB (partitioned by user_id)
- MFA recovery codes (100M): ~1GB
- Audit logs (1B events/year): ~100GB (archived after 1 year)

### Caching
- User MFA status in Redis: TTL 10s, eviction policy LRU
- Cache hit rate target: > 80%
- Session token lookup: primary key, no cache needed

### Errors & Retries
- Max retries: 3 (for event publishing failures)
- Retry backoff: exponential (100ms, 1s, 10s)
- Timeout: 30s for all public APIs, 5s for internal APIs
- Circuit breaker: fail open if User Service is down (no profile fetch block)

---

**Ready for:** Council negotiation
```

## Anti-Pattern: "We'll figure it out in Backend"

Do NOT write:
- "API endpoints TBD"
- "We'll cache the important stuff"
- "Async later, sync for now"
- "We can denormalize if it's slow"
- "SLOs TBD"

Every detail must be locked before code starts. API contracts and database schema changes are the hardest to roll back.

---

## Edge Cases

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

## Common Pitfalls

**1. Changing DB Schema Without Migration Path (Blocks Rolling Deploy)**
- **Bad:** Drop `legacy_token` column from sessions table → deploy code that doesn't use it → old code still reads it → 500 error mid-deploy
- **Good:** Deprecate column first (mark in code), support both old + new code paths, then drop in separate release

**2. Adding Required Fields Without Defaults (Breaks Old Clients)**
- **Bad:** Add `preferred_timezone` VARCHAR NOT NULL to users → old code creates users without it → insert fails
- **Good:** Add `preferred_timezone` VARCHAR NULL DEFAULT 'UTC' → new code populates it, old code doesn't need it

**3. Removing Deprecated Endpoints Too Quickly (Old Clients Still Using)**
- **Bad:** API v1 deprecated 6 months ago, you remove it → 5% of clients still on v1 → they all break
- **Good:** Announce deprecation + support window (12-18 months), monitor v1 usage, only remove when < 1% traffic

**4. Not Validating Input (Garbage In → Garbage Out)**
- **Bad:** POST /auth/2fa/enable with `method: "xyz"` → silently accepts, stores invalid value → verify endpoint fails mysteriously
- **Good:** Validate method ∈ {"totp", "sms"}, return 400 with error message: `{"error": "invalid_method", "valid_methods": ["totp", "sms"]}`

**5. Silent Failures in Async Jobs (No Observability)**
- **Bad:** Event consumer silently crashes on malformed event → audit logs stop appearing → nobody notices for days
- **Good:** All async jobs log errors, metric emit on failure:
  ```
  LOG ERROR: Failed to process auth.2fa_enabled event_id=xyz user_id=123 error="..."
  METRIC emit: kafka_consumer_error_total{topic=user-lifecycle, handler=audit_service}
  DLQ: Forward to dead-letter queue for manual inspection
  ALERT: Pager goes off if error rate > 1% per minute
  ```

---

## Contract Thinking

**API Versioning Strategy**
- **v1 (Deprecated):** Old clients using 2FA via TOTP only
  - Endpoint: POST /auth/2fa/enable → {method: implicit "totp"}
  - Sunset: 2026-10-01 (6 months from now)
  - Monitoring: Emit `api_version_usage{version=v1}` metric

- **v2 (Current):** New clients with SMS + TOTP + recovery codes
  - Endpoints: POST /auth/2fa/enable, POST /auth/2fa/verify, DELETE /auth/2fa/disable, GET /auth/2fa/status
  - Request: {method: "totp" | "sms"}
  - Response: includes recovery_codes, qr_code_url
  - Migration path: v1 clients get 429 "Unsupported version" after sunset date

**Event Schema Evolution**
- **Current:** `auth.2fa_enabled` event
  ```json
  {
    "event_id": "uuid",
    "user_id": 123,
    "mfa_method": "totp",
    "timestamp": "2026-04-10T12:00:00Z",
    "idempotency_key": "req-abc123"
  }
  ```
- **Future need:** Add `auth_method` (password, oauth, saml)
  - Add as optional field: `"auth_method": "password" | null`
  - Old consumers ignore it, new consumers use it
  - No breaking change to schema

**Database Schema Backward Compatibility**
- **Adding column:** Always nullable + default (old code doesn't know about it)
  ```sql
  ALTER TABLE users ADD COLUMN verified_email BOOLEAN DEFAULT FALSE;
  ```
- **Removing column:** Deprecate first (support 2 code versions), then remove
  ```
  v1.4: mfa_secret stored in users table (support both old + new location)
  v1.5: mfa_secret only in mfa_settings table (announce deprecation)
  v1.6: Remove old column after 6 months support
  ```
- **Renaming column:** Create new column, backfill, drop old column (3-phase)

**Cache Key Strategy & Invalidation Complexity**
- **Keys:** `session:{token_hash}` (primary), `user:{user_id}:mfa_status` (secondary)
- **TTL:**
  - Session cache: 0s (no cache, query database, too sensitive)
  - MFA status cache: 10s (acceptable 10s stale window)
  - User profile cache: 60s (frontend can tolerate 1min stale)
- **Invalidation:**
  - Explicit: `DELETE session:{token_hash}` when user logs out
  - Event-driven: Subscribe to `auth.2fa_enabled` → invalidate `user:{user_id}:mfa_status`
  - Time-based: TTL expires naturally

---

## Dependency Chain Thinking

**Dependency: Auth Service → User Service (for profile)**

**Scenario 1: User Service is Down (Full outage)**
- **What happens?** Auth Service tries to GET /internal/users/{id} → timeout/error
- **Without fallback:** Return 500 Unauthorized to client
- **With fallback:** Circuit breaker opens after 3 failures
  - Return 202 Accepted, minimal session (user_id only, no profile)
  - Client shows partial UI ("Loading profile...")
  - User Service comes back up → cache updates → UI refreshes
  ```
  GET /user/profile when Auth Service can't reach User Service:
  Response 202 Accepted (degraded mode):
  {
    "user_id": 123,
    "name": null,
    "email": null,
    "X-Degraded": "true",
    "X-Retry-After": "10s"
  }
  ```

**Scenario 2: User Service is Slow (> 5s response time)**
- **What happens?** Request timeout → circuit breaker logs latency spike
- **Without timeout:** Client waits forever, connection pool exhausted, cascading failure
- **With timeout:** All calls timeout after 5s
  - Fallback to cached data (if available)
  - Return 504 Gateway Timeout + retry header
  - Metric emit: `upstream_latency_exceeded{service=user_service}`
  ```
  if latency > 5000ms:
    close connection
    return 504 with X-Retry-After: 10s
    emit metric: upstream_latency{service=user_service, latency_ms=5234}
  ```

**Scenario 3: User Service Returns Bad Data**
- **What happens?** User Service returns malformed profile (missing required fields)
- **Without validation:** Store garbage in cache → subsequent requests fail
- **With validation:** Validate schema, reject if invalid
  ```
  Response from User Service: {"user_id": 123} (missing name)
  
  // Validate
  if !response.name || typeof response.name !== 'string':
    LOG ERROR: Invalid profile from User Service
    Don't cache this response
    Return 500 with message "User service returned invalid data"
    DLQ to monitoring team
  ```

**Dependency: Sessions Table → Redis Cache (for token lookup)**

**Scenario 1: Redis is Down**
- **What happens?** Can't check cache → hit database for every session lookup
- **Impact:** Database QPS spikes 10x (every request now hits DB)
- **Without fallback:** Database connection pool exhausted → cascading failure
- **With fallback:** If Redis fails, go straight to DB with degraded SLO
  ```
  GET /internal/auth/verify-session/{token}
  
  1. Try Redis (50ms timeout)
  2. If Redis down:
     - Hit database directly
     - SLO degrades from 50ms p99 to 200ms p99
     - Emit metric: cache_miss{reason=cache_down}
  ```

**Scenario 2: Cache Gets Out of Sync with Database**
- **What happens?** Session invalidated in DB, but Redis still has old token → user stays logged in
- **Without invalidation:** User logs out, but cache says still logged in (security issue)
- **With invalidation:** Delete key from cache when session invalidated in DB
  ```
  DELETE /auth/logout
  1. Delete from sessions table
  2. Delete from Redis (session:{token_hash})
  3. Publish auth.session_invalidated event
  4. If Redis delete fails, retry 3x with backoff
  5. If retry fails, log critical alert
  ```

**Scenario 3: Cache Key Collision (Unlikely but Possible)**
- **What happens?** Two different tokens hash to same cache key → one user accesses another user's session
- **Prevention:** Cache key includes full token hash (not truncated)
  ```
  session:{sha256(full_token)} (not session:{token[0:8]})
  ```
- **Detection:** In verify-session, compare retrieved token hash with requested token (never trust cache alone for sensitive data)

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

---

## Decision Tree: Synchronous vs. Asynchronous Reasoning

When designing backend logic, choose between synchronous (blocking) and asynchronous (non-blocking) patterns based on your latency requirements, consistency needs, and failure recovery strategies.

```
DOES THE OPERATION NEED AN IMMEDIATE RESPONSE TO THE CLIENT?
│
├─ YES, client is waiting (user submitted form, waiting for result) → SYNCHRONOUS
│  │
│  ├─ Operation must complete within SLO (e.g., < 200ms p99)
│  ├─ Client sees success/failure immediately
│  ├─ Use database transactions to ensure atomicity
│  ├─ If operation fails, client sees error and can retry
│  │
│  └─ Example: User signup, payment authorization, login
│
└─ NO, client is NOT waiting (background job, notifications, audit logs) → ASYNCHRONOUS
   │
   ├─ Publish event to queue, return success immediately
   ├─ Consumer processes event asynchronously
   ├─ Use eventual consistency with retry/DLQ strategy
   ├─ If processing fails, event goes to DLQ for manual replay
   │
   ├─ Is order important (Event A must be processed before Event B)?
   │ │
   │ ├─ YES → Use partitioned queue with partition key
   │ │       └─ Example: All user events for user 123 go to same partition
   │ │
   │ └─ NO → Use standard queue
   │        └─ Example: Notification sent to 1000 users (no ordering needed)
   │
   └─ Example: Email notifications, audit logging, analytics events
```

**Implementation Decision Matrix**:

| Scenario | Pattern | SLO | Consistency | Complexity |
|----------|---------|-----|-------------|-----------|
| User login | Sync | < 100ms p99 | Strong | Low |
| Payment processing | Sync | < 500ms p99 | Strong | High |
| Send welcome email | Async | No SLO (best effort) | Eventual | Low |
| Update user profile + notify followers | Sync (profile) + Async (notifications) | < 200ms p99 | Strong (profile), Eventual (notifications) | Medium |
| Financial audit log | Async (eventually consistent) | Acceptable 5-60min | Eventual (replay from DLQ if needed) | Medium |
| Real-time notification | Async (but fast, <1s) | < 1s p99 | Eventual | Medium |

---

## Council Questions to Ask

When reviewing other surfaces' proposals:

**To Frontend/App:**
- What's the user-facing latency SLA? (so we know cache TTL and acceptable sync delays)
- How often do you refresh data? (so we size connection pools)
- Do you need strong consistency or eventual consistency? (so we know cache invalidation strategy)
- Will you retry failed requests? (so we plan for idempotency)
- What's your oldest deployed client version? (so we know how far back to support API versions)

**To Infra:**
- Can MySQL handle the query patterns? (so we design indexes)
- How long can cache be stale? (so we set Redis TTL)
- What's your event delivery latency target? (so we know if Kafka lag is acceptable)
- Can you handle 10x traffic spike? (so we know if we need sharding)
- What's your circuit breaker strategy for service failures? (so we know SLO degradation bounds)
- How long does database migration take? (so we plan our rollout window)

**To Self:**
- Are all endpoints idempotent when they should be? (critical for retries)
- Is the service boundary clear and non-circular?
- Can service A be down without bringing down service B? (so we know circuit breaker strategy)
- Do the SLOs match the data model complexity? (e.g., if queries are complex, SLOs must be looser)
- Is there any data that needs to be consistent across services? (if yes, are we handling it correctly?)
- What happens if a dependency is down/slow/broken? (have we tested each fallback?)
- Are async events guaranteed to process in order? (or do we need idempotency deduplication?)

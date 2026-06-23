# Backend Reasoning — Worked Examples

Worked-example outputs for each reasoning dimension and the full council-output
contract structure. The reasoning spine (the question set the surface works
through) lives in `../SKILL.md`; this file holds the long illustrative outputs.

## 1. API Endpoints — Worked Example

- PRD: "Users can enable 2FA"
- Backend says:
  - POST /auth/2fa/enable (v2, idempotent, token-gated, returns 2fa_secret + recovery_codes)
  - POST /auth/2fa/verify (v2, rate-limited 3/min, returns session token)
  - DELETE /auth/2fa/disable (v2, requires re-auth)
  - GET /auth/2fa/status (v2, cached 10s)

Request/response schemas, error codes, headers:

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

## 2. Data Models — Worked Example

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

## 3. Service Boundaries — Worked Example

- **Auth Service** owns: credentials, sessions, 2FA settings, recovery codes
  - Internal APIs: POST /internal/auth/verify-session, GET /internal/auth/user/{id}
  - Owns the source-of-truth for user sessions

- **User Service** owns: profiles, preferences, settings (non-auth)
  - Calls Auth Service for session verification
  - Does NOT call Auth Service for every request (caches session info)

- **Audit Service** owns: audit logs of security events
  - Consumes events from Auth Service (2FA enabled, login, session expired)

## 4. Async Patterns — Worked Example

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

## 5. Performance SLOs — Worked Example

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

---

## Full Council-Output Example (`council/backend.md`)

Write to `~/forge/brain/prds/<task-id>/council/backend.md`. The output contract
structure (required sections) is in `../SKILL.md`; this is a fully worked
instance of it.

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

  Headers:
    X-Degraded: true
    Retry-After: 10        # standard header, seconds — not an X- body field
  JSON body:
  {
    "user_id": 123,
    "name": null,
    "email": null
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
    return 504 with Retry-After: 10   (standard header, seconds)
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

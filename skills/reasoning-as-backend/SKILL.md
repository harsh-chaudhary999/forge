---
name: reasoning-as-backend
description: "WHEN: Council is reasoning about a PRD. You are the backend perspective (REST/gRPC/SQL). Analyze the PRD for API endpoints, data models, service boundaries, async patterns, performance SLOs."
type: rigid
effort: high
requires: [brain-read]
version: 1.0.2
preamble-tier: 1
triggers:
  - "reasoning for backend"
  - "how should backend work"
  - "backend architecture reasoning"
allowed-tools:
  - Write
  - mcp__*
---

# Reasoning as Backend

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "We'll add auth later" | Endpoints without auth ship insecure. Auth is a contract, not an afterthought. Every endpoint must state its auth mechanism before council closes. |
| "SLOs can be defined after build" | Unspecified SLOs mean no eval criteria. Build completes and eval has nothing to measure against. Concrete numbers now or wasted eval later. |
| "The schema can evolve" | Schema changes after shipping require migrations. Every unplanned migration is a production risk and a rolling-deploy hazard. |
| "We can decide sync vs async later" | Sync vs async is an architectural decision. Changing it after clients integrate requires coordinating every consumer. Lock it at council. |
| "Error codes are obvious" | Every client that parses errors will implement its own interpretation. Specify error shapes or get inconsistent error handling across all surfaces. |

## Iron Law

```
BACKEND REASONING COVERS ALL API CONTRACTS, MIGRATION PLANS, AND SLOs BEFORE COUNCIL CLOSES. AN ENDPOINT WITHOUT AUTH, VERSIONING, OR ERROR CODES IS AN INCOMPLETE CONTRACT.
```

## Adjacent domains & pipelines (MUST — one explicit block)

Before listing endpoints or schema, add a short subsection **“Adjacent domains & pipelines”** naming **other** backend or batch domains the PRD might collide with (**use neutral names from the PRD**). For each: **read/write touchpoints**, **shared tables or flags**, **ordering or exclusion rules**, **explicit “no interaction”** where true. Follow **`docs/adjacency-and-cohorts.md`** and produce this per the template **`docs/templates/adjacency-cohort-and-signals.template.md`** (council/tech-plan emit the per-task `touchpoints/` artifact from it — it is something this surface helps *produce*, not an existing doc to read) — silence here is unreviewed integration risk.

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **API endpoints are proposed without versioning strategy** — Unversioned APIs will break clients the moment a field is renamed or a behavior changes. STOP. Every endpoint must include its version (e.g., `v1`, `v2`) and the deprecation policy for old versions.
- **Backend is reasoning in isolation before hearing web/mobile/infra surfaces** — Unilateral backend decisions create mismatched API shapes that web or mobile must work around. STOP. Backend reasoning is input to council negotiation, not a final decision — surfaces must hear each other before contracts lock.
- **Data model is proposed without a migration plan** — A new table or a column change requires migration steps that must be backward-compatible with the running system. STOP. Every schema change must include the migration procedure and rollback plan.
- **Performance SLOs are absent from the reasoning output** — "Fast" is not an SLO. STOP. Every endpoint must state its p95 latency target and maximum throughput in concrete numbers that can be evaluated in an eval scenario.
- **Async patterns are described as "fire and forget" without dead letter queue** — A message that cannot be delivered without a DLQ is permanently lost. STOP. Every async flow must specify what happens to messages that fail delivery: DLQ, retry policy, and alert threshold.
- **Auth requirements are deferred** — An endpoint without explicit auth requirements will be implemented inconsistently across services. STOP. Every endpoint must state its authentication mechanism (Bearer token, API key, session) and authorization check (ownership, role, scope) before council closes.
- **Error codes and response shapes are not specified** — Inconsistent error formats force every client to implement unique parsing logic. STOP. Every endpoint must specify its error response schema and the full set of possible HTTP status codes.

**Before reasoning about any module, class, or function:** Read the scan-codebase output for this repo:
- `~/forge/brain/prds/<task-id>/codebase/<role>/structure.txt` — full file inventory
- `~/forge/brain/prds/<task-id>/codebase/<role>/code-style.md` — naming conventions, async pattern, import style
- `SCAN.json` hub scores (if present) — identifies Tier 1 hub files that must not be broken

Never invent naming conventions or import patterns — always derive from `code-style.md`. If `code-style.md` is absent, run `/scan-codebase` first.

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

## Post-Implementation Checklist

- [ ] All new endpoints have input validation at the boundary (not assumed valid from caller).
- [ ] Database queries use parameterized statements (no string interpolation in SQL).
- [ ] Error responses return structured JSON with an error code (not raw exception messages).
- [ ] Service does not silently swallow exceptions — all catch blocks log or re-throw.
- [ ] Integration test covers the new endpoint with a real (or test-scoped) database connection.

## Output

Write to `~/forge/brain/prds/<task-id>/council/backend.md`:

```markdown
# Backend Perspective

## Reference (load on demand)

The worked output example, edge-case / failure handling, common pitfalls, decision trees,
and deep domain guidance live in **`reference/backend-reasoning-reference.md`** (Agent Skills progressive disclosure).
This SKILL.md is the operational contract: the surface's reasoning framework, discipline,
output spec, and cross-references.

## Cross-References

- **scan-codebase** — Must be run (and output read) before reasoning starts. Provides `structure.txt`, `code-style.md`, and `SCAN.json` hub scores for the target repo.

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

## Checklist

Before submitting backend reasoning to council:

- [ ] All API endpoints have version, auth mechanism, request/response schema, and full error code set
- [ ] All data model changes include migration steps and rollback procedure
- [ ] All async patterns specify partition key, DLQ, retry policy, and dead-letter behavior
- [ ] All performance SLOs are in concrete numbers (p95/p99 latency and throughput)
- [ ] Service boundaries are defined with no circular dependencies
- [ ] Cache TTLs and invalidation triggers are locked
- [ ] No endpoint marked TBD, "to be defined," or "similar to existing"

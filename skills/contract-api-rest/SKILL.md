---
name: contract-api-rest
description: "WHEN: Council has identified REST API conflicts across surfaces and needs a locked contract. Negotiates versioning strategy, endpoint shape, error codes, auth, rate limits, idempotency, and deprecation across all consumer teams."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers:
  - "design REST API"
  - "define API contract"
  - "REST contract"
  - "API endpoints spec"
allowed-tools:
  - Bash
  - Write
---

# Contract-API-REST Skill

## Anti-Pattern Preamble: REST Contract Failures

| "Rationalization" | Counter-truth |
|---|---|
| "The backend team knows best, they'll design the API" | Every consumer surface has constraints the backend team doesn't know about. Mobile has size limits, web has CORS restrictions, infra has routing rules. Unilateral API design guarantees at least one surface will hit a wall during implementation. |
| "We'll figure out versioning after launch, the API is simple now" | There is no such thing as an API that stays simple. Once clients exist, changing the contract costs 10x more than designing versioning upfront. Launch with /v1 or pay the migration tax forever. |
| "Error codes are just HTTP status codes, no need to document them" | HTTP status codes tell clients the class of failure. They cannot tell clients whether to retry, show a user-facing message, or escalate. Without machine-readable error codes in the contract, every consumer invents its own error handling logic. |
| "We'll add rate limits later when we need them" | Rate limits added after launch require client changes to handle 429s. Clients that were never designed to back off will hammer the API, get blocked, and file bugs. Rate limit contracts must be in place before the first client ships. |
| "Authentication is obvious — just use JWT" | JWTs have expiry, rotation, scope, and clock-skew semantics that differ across implementations. If the contract doesn't specify exactly how tokens are issued, validated, and refreshed, every service will implement different assumptions. |
| "Idempotency is only for payment endpoints" | Any mutating endpoint called over an unreliable network needs idempotency. Mobile clients on flaky connections will retry POST requests. Without an idempotency key contract, retries cause duplicate creates, double-charges, or duplicate emails. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
NO ENDPOINT MAY BE IMPLEMENTED UNTIL ITS CONTRACT — VERSIONING, SHAPE, ERROR CODES, AUTH, RATE LIMITS, AND IDEMPOTENCY — HAS BEEN NEGOTIATED AND SIGNED OFF BY EVERY CONSUMER SURFACE. CODE THAT PRECEDES CONTRACT IS TECH DEBT FROM THE FIRST COMMIT.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **API versioning strategy is absent from the contract** — Unversioned APIs cannot evolve without breaking clients. STOP. Define versioning strategy (URL path `/v1`, header, or content-type) before any endpoint is implemented.
- **Error response shape is not specified** — Error formats that differ by endpoint confuse clients and break error handling. STOP. Define a single error envelope format for all endpoints before locking.
- **Authentication mechanism is listed as "TBD"** — Unspecified auth means clients implement assumptions. STOP. Lock auth mechanism (JWT, API key, OAuth) before contract is accepted.
- **No rate limit policy is defined** — Unspecified rate limits cause client implementations that hammer the API and get blocked in production. STOP. Specify rate limits per endpoint or per client tier.
- **Deprecation policy is absent** — APIs without deprecation policy cannot be versioned safely. STOP. Define deprecation timeline and sunset headers before freezing the contract.
- **Contract is created unilaterally by backend without frontend/mobile input** — Client requirements will not be met. STOP. All consumer surfaces must approve the contract shape before it is locked.
- **Idempotency behavior is not specified for mutating endpoints** — Non-idempotent mutations cause duplicate writes on retry. STOP. Specify idempotency key requirements for all POST/PUT/PATCH endpoints.

## Overview

This skill teaches teams to negotiate REST API contracts **before** implementing endpoints. Once clients exist, changing API contracts becomes costly and breaks production systems. This skill prevents design debt by establishing clear contracts upfront.

**Core principle:** Contract first, implementation second.

---

## Minimum depth before the REST contract is LOCK

**Purpose:** Prevent “table of paths only” specs that miss what a competing implementation plan would include. **Forge normative surface** is still `shared-dev-spec.md` + contract files — this section raises the **minimum bar** before council locks.

For **each surface-relevant** new or materially changed endpoint, the locked contract (in `shared-dev-spec` and/or `contracts/api-rest.md`) **must** include:

1. **METHOD + full path** + **auth** (mechanism + scopes or roles, or `public` with explicit rate limit).
2. **Versioning:** URL prefix (`/v1/...`) **or** header strategy — **one line** tying the rule to the **actual mount** in code (repo-relative **`path:line`** from brain scan or product repo, e.g. `src/server/app.js:42`).
3. **Request JSON example** and **response JSON example** (success) — real keys and types, not `{}`.
4. **At least one error example** using the **agreed error envelope** (HTTP status + body shape + machine-readable `code` if applicable).
5. **Idempotency** for mutating verbs: header name or body field + expected server behaviour on replay.

If an endpoint is intentionally deferred, add a row **`DEFERRED out of MVP`** with **owner + risk** — not an empty cell.

---

## 1. API Versioning Strategy

### Understanding Versioning Needs

Versioning is **required** from day one. Without it, you'll face impossible choices: break all clients or maintain multiple incompatible implementations forever.

### Versioning Approaches

#### URL Versioning (Recommended)

```
GET /v1/users/123
GET /v2/users/123
```

**Advantages:**
- Explicit in logs, metrics, and caches
- Easy to route to different backends
- Clear in documentation
- Clients can't accidentally use wrong version

**Disadvantages:**
- Longer URLs
- Code duplication if versions are similar

#### Header Versioning

```
GET /users/123
Accept: application/vnd.api+json;version=2
```

**Advantages:**
- Cleaner URLs
- Single code path for minor differences

**Disadvantages:**
- Hidden from logs (easy to miss version mismatches)
- Cache-unfriendly (same URL, different responses)
- Clients often forget headers

#### Query Parameter Versioning

```
GET /users/123?api_version=2
```

**Disadvantages:** Not recommended. Hard to cache, easy to forget, violates REST principles.

### Graduated Deprecation Timeline

**Active Support (12 months)**
- Both v1 and v2 fully supported
- All new features go to v2
- Bugs fixed in both versions
- Header: `Deprecation: false`

**Deprecation Window (6 months)**
- v1 still works but no new features
- Bugs fixed only if critical
- Header: `Deprecation: true, Sunset: <date>`
- Email warnings sent to clients

**Sunset (Month 18)**
- v1 APIs return 410 Gone
- Support only via legacy integration support

**Example Timeline:**
```
v1 Launch: 2024-01-01
v2 Launch: 2025-01-01 (v1 still active)
v1 Deprecation Notice: 2025-01-01
v1 Sunset Date: 2026-01-01 (12 months support)
v1 Shut Down: 2026-01-01
```

### Backward Compatibility Guarantees

**Semantic Versioning:**
- Major (breaking): /v1 → /v2 (clients must update)
- Minor (additive): new fields, new endpoints (backward compat)
- Patch (bugfix): no API changes

**Guarantee Template:**
```markdown
v2 Backward Compatibility Guarantee:
- All request fields in v2.0 will remain in v2.x
- New fields are optional (will have defaults)
- Old response fields will not be removed
- Field types will not change
- Endpoint URLs will not change
- Error codes will only be added, not removed
```

**What changes are safe in v2.x:**
- Adding optional request fields
- Adding new response fields
- Adding new error codes
- Adding new endpoints
- Adding query parameters (must be optional)

**What requires v3:**
- Removing a field
- Changing field type (string → integer)
- Making a field required
- Changing endpoint path
- Removing an endpoint
- Changing HTTP status code semantics

---

## 2. Endpoint Specification

### Naming Conventions

#### Resource-Oriented (Preferred)

```
POST /v2/users          # Create
GET /v2/users           # List
GET /v2/users/123       # Read
PUT /v2/users/123       # Replace
PATCH /v2/users/123     # Partial update
DELETE /v2/users/123    # Delete
```

**Advantages:** Predictable, scalable, follows REST principles.

#### Action-Oriented

```
POST /v2/users/create
POST /v2/users/123/update
POST /v2/users/123/delete
```

**Disadvantages:** Verbose, mixing nouns and verbs, harder to cache.

#### Nested Resources

```
GET /v2/users/123/projects        # List user's projects
POST /v2/users/123/projects       # Create project for user
GET /v2/users/123/projects/456    # Get specific project
```

**Rule:** Max 2-level nesting. Beyond that, use query parameters.

```
# Instead of: GET /v2/orgs/1/teams/2/members/3/projects/4
# Use: GET /v2/projects/4?org_id=1&team_id=2&member_id=3
```

### Request/Response Schema Specification

**Template for each endpoint:**

```markdown
## POST /v2/users

**Purpose:** Create a new user account.

**Authentication:** Bearer token (OAuth2)

**Rate Limit:** 100 req/min per user

**Request Body:**
```json
{
  "email": "string (required, email format, unique)",
  "name": "string (required, 1-255 chars)",
  "role": "enum: 'admin'|'member'|'viewer' (optional, default: 'member')",
  "metadata": "object (optional, user-defined, max 1MB)"
}
```

**Response (201 Created):**
```json
{
  "id": "string (UUID)",
  "email": "string",
  "name": "string",
  "role": "string",
  "created_at": "string (ISO 8601)",
  "metadata": "object"
}
```

**Response (400 Bad Request):**
```json
{
  "error": "string",
  "code": "string",
  "details": {
    "field": "string",
    "message": "string"
  }
}
```

**Errors:**
- `INVALID_EMAIL` (400): Email format invalid
- `EMAIL_TAKEN` (409): Email already exists
- `INVALID_ROLE` (400): Role not recognized
- `METADATA_TOO_LARGE` (413): Metadata exceeds 1MB

**Idempotency:** Yes (use `Idempotency-Key` header)

**Example Request:**
```bash
curl -X POST https://api.example.com/v2/users \
  -H "Authorization: Bearer token_123" \
  -H "Idempotency-Key: req_abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "name": "Alice Smith",
    "role": "member"
  }'
```
```

### Query Parameter Standards

**Filtering:**
```
GET /v2/users?status=active
GET /v2/users?role=admin&status=active  # Multiple filters (AND)
GET /v2/users?emails=alice@example.com,bob@example.com  # CSV for membership
```

**Pagination:**
```
GET /v2/users?page=1&page_size=50       # Offset pagination
GET /v2/users?limit=50&offset=100       # Alternative offset style
GET /v2/users?limit=50&cursor=abc123    # Cursor pagination (preferred for large datasets)
```

**Response includes:**
```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 1500,
    "has_more": true
  }
}
```

**Sorting:**
```
GET /v2/users?sort=-created_at,name  # Comma-separated, - prefix for descending
GET /v2/users?sort=created_at:desc,name:asc  # Alternative syntax
```

**Expansion:**
```
GET /v2/users/123?expand=projects,teams  # Embed related resources
```

**Response:**
```json
{
  "id": "123",
  "name": "Alice",
  "projects": [...]  # Embedded instead of just ID
}
```

### Path Parameter Rules

**Format:**
```
GET /v2/users/{user_id}
GET /v2/users/{user_id}/projects/{project_id}
```

**Validation:**
- `{user_id}` must be a valid UUID format
- Path params are required (no defaults)
- Document validation rules in spec

**Bad practices:**
```
GET /v2/users/{user_id?}        # Optional path params (not valid)
GET /v2/users/{user-id}         # Use underscores, not hyphens
```

---

## 3. Error Handling

### Standard Error Response Format

**All 4xx and 5xx responses must follow this format:**

```json
{
  "error": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE",
  "status": 400,
  "request_id": "req_abc123xyz",
  "timestamp": "2026-01-15T10:30:00Z",
  "details": {
    "field": "email",
    "message": "Must be valid email format"
  },
  "trace_url": "https://logs.example.com/traces/req_abc123xyz"
}
```

**Fields:**
- `error`: Human message for debugging
- `code`: Machine code for routing/handling (never changes)
- `status`: HTTP status code (redundant but useful in apps)
- `request_id`: Correlation ID for support
- `timestamp`: When error occurred
- `details`: Additional context (optional)
- `trace_url`: Link to detailed logs (optional, internal only)

### Error Code Taxonomy

**Authentication & Authorization:**
```
AUTH_REQUIRED          → 401 Unauthorized (missing/invalid token)
AUTH_INVALID           → 401 Unauthorized (malformed token)
AUTH_EXPIRED           → 401 Unauthorized (token expired)
INSUFFICIENT_SCOPE     → 403 Forbidden (token lacks required scopes)
RESOURCE_FORBIDDEN     → 403 Forbidden (authenticated but not permitted)
```

**Validation Errors:**
```
INVALID_REQUEST        → 400 Bad Request (malformed JSON/params)
INVALID_FIELD          → 400 Bad Request (specific field invalid)
MISSING_FIELD          → 400 Bad Request (required field missing)
INVALID_ENUM           → 400 Bad Request (enum value not recognized)
CONSTRAINT_VIOLATION   → 400 Bad Request (constraint failed)
```

**Resource Errors:**
```
RESOURCE_NOT_FOUND     → 404 Not Found
RESOURCE_CONFLICT      → 409 Conflict (duplicate key, state violation)
RESOURCE_GONE          → 410 Gone (deleted, deprecated)
```

**Rate Limiting & Quota:**
```
RATE_LIMITED           → 429 Too Many Requests
QUOTA_EXCEEDED         → 429 Too Many Requests (different from rate limit but same status)
```

**Server Errors:**
```
INTERNAL_ERROR         → 500 Internal Server Error
SERVICE_UNAVAILABLE    → 503 Service Unavailable
```

### HTTP Status Code Mapping

**2xx Success:**
```
200 OK              → GET, PUT, PATCH, DELETE successful
201 Created         → POST created new resource
202 Accepted        → Async operation queued
204 No Content      → DELETE or PATCH with no response body
```

**3xx Redirect:**
```
301 Moved Permanently  → Use new URL permanently
307 Temporary Redirect → Retry same request at new URL
```

**4xx Client Error:**
```
400 Bad Request        → Validation or syntax error
401 Unauthorized       → Authentication required
403 Forbidden          → Authenticated but not permitted
404 Not Found          → Resource doesn't exist
409 Conflict           → State violation or duplicate
410 Gone               → Resource deleted or endpoint sunset
413 Payload Too Large  → Request body too large
429 Too Many Requests  → Rate limited
```

**5xx Server Error:**
```
500 Internal Server Error  → Unexpected server error
502 Bad Gateway            → Upstream service error
503 Service Unavailable    → Maintenance or overload
```

### Retry-ability Classification

**Mark each endpoint as retryable or idempotent in spec:**

```markdown
## POST /v2/charge-payment

**Idempotent:** YES (use Idempotency-Key header)
**Retryable:** YES
**Idempotent Timeout:** 24 hours (after 24h, same key = different charge)

Automatic retry rules:
- 408 Request Timeout → retry after 1s
- 429 Rate Limit → retry after Retry-After header
- 500, 502, 503 → retry after exponential backoff (1s, 2s, 4s max)
- Other 4xx → do not retry (client error, won't succeed)
```

**Decision tree:**
```
Is operation idempotent? (multiple executions = same result)
├─ YES → Use Idempotency-Key header
│        Automatic retries safe
│        Timeout: 24 hours typical
└─ NO  → No automatic retries
         Require manual retry decision
         Examples: state transitions, calculations
```

---

## 4. Rate Limiting & Idempotency

### Rate Limit Strategy

**Dimension options:**

```markdown
## Per-User Rate Limiting (Recommended)

User: 1,000 requests/hour
Endpoint-specific:
  - POST /auth/login: 5 requests/minute
  - POST /send-email: 100 requests/hour
  - GET /search: 10 requests/second

Headers:
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1610702400  # Unix timestamp
```

**Alternative: Per-IP Rate Limiting (for public APIs)**
```
IP: 100 requests/hour (unauthenticated)
Authenticated user: 1,000 requests/hour
```

**Alternative: Per-API-Key Rate Limiting (for integrations)**
```
Key: 10,000 requests/day
Burst: 100 requests/minute
```

### Idempotency Implementation

**Idempotency-Key Header:**

```bash
POST /v2/charge-payment
Idempotency-Key: req_alice_2026_01_15_charge_123

Body:
{
  "amount": 9999,
  "currency": "USD",
  "account_id": "acc_123"
}
```

**Server behavior:**
1. Client sends request with `Idempotency-Key` header
2. Server generates unique key from header
3. Server stores key → response mapping (24 hour TTL)
4. Client retries with same key
5. Server returns cached response instead of re-executing

**Response includes:**
```
Idempotency-Key: req_alice_2026_01_15_charge_123
```

**Implementation checklist:**
- [ ] Idempotency key stored in request cache
- [ ] Cache TTL: 24 hours minimum
- [ ] If request succeeds, cache the response
- [ ] If retried with same key, return cached response
- [ ] If request fails, do NOT cache (retry should retry the operation)
- [ ] Return 422 if key used with different request body

**Example scenario:**

```
Request 1 (Idempotency-Key: req_1):
POST /v2/charge-payment → 201 Created, charged $100

Request 2 (network timeout, client retries):
POST /v2/charge-payment
Idempotency-Key: req_1 → 201 Created (cached), NOT charged again

Request 3 (different body, same key):
POST /v2/charge-payment
Idempotency-Key: req_1
Body: {amount: 200} → 422 Unprocessable Entity (key already used)
```

### Exactly-Once Delivery Semantics

**For idempotent endpoints:**
- Client can safely retry without side effects
- Server handles duplicates transparently
- Useful for financial operations, critical state changes

**For non-idempotent endpoints:**
- Mark explicitly in spec
- Document why they can't be idempotent
- Provide alternative (e.g., check state first)

**Example:**
```markdown
## GET /v2/user/123/next-job (Non-idempotent)

Warning: Each call advances to the next job.
Not idempotent by nature.

Workaround:
- Query /v2/user/123/current-job first
- Then POST /v2/jobs/123/complete to move to next
```

---

## 5. Deprecation Strategy

### Deprecation Headers

**RFC 8594 - Deprecation Header:**

```
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sun, 31 Dec 2026 23:59:59 GMT
Link: </v2/users>; rel="successor-version"
```

**Headers breakdown:**
- `Deprecation: true` → This endpoint is deprecated
- `Sunset: <date>` → When endpoint will be unavailable
- `Link: <url>; rel="successor-version"` → Where to migrate

### Migration Period

**Standard timeline: 12 months**

```
Month 0: Announcement
- Blog post: "Sunsetting /v1 in 12 months"
- Email all API consumers
- Add Deprecation headers to responses
- Update documentation

Month 6: Reminder
- Email reminder: 6 months until sunset
- Flag in dashboard
- Provide migration guide

Month 11: Final Notice
- Final email warning
- Only 1 month left to migrate
- Support team on alert

Month 12: Sunset
- /v1 endpoints return 410 Gone
- No longer supported
```

**Exception: 6-month deprecation for critical security fixes**
```
"For critical security issues affecting v1, we may
accelerate sunset to 6 months after disclosure."
```

### Forced Upgrade Timeline

**Graceful shutdown:**
```
Day 1-330: /v1 fully functional, returns Deprecation header
Day 331-360: /v1 returns 200 but with warning body:
{
  "warning": "v1 will sunset in 30 days. Migrate to /v2 now.",
  "sunset_date": "2026-12-31"
}
Day 361+: /v1 returns 410 Gone
```

**Example error after sunset:**
```json
{
  "error": "This API version is no longer supported",
  "code": "ENDPOINT_DEPRECATED",
  "status": 410,
  "sunset_date": "2026-12-31",
  "migration_guide": "https://docs.example.com/migrate-v1-to-v2"
}
```

---

## Anti-Patterns to Prevent

### Anti-Pattern 1: "We'll figure out versioning later"

**Problem:** Once 50 clients use your API, changing contract becomes impossible.

**Evidence:**
- Twilio spent 6+ months supporting v1 while building v2
- AWS EC2 still supports deprecated query API alongside modern JSON
- Breaking change = emergency support tickets = revenue risk

**Solution:** Version from endpoint 1. Use `/v1` even for initial release.

### Anti-Pattern 2: Inconsistent Error Formats

**Bad:**
```json
// Some endpoints:
{"error": "Invalid"}

// Other endpoints:
{"message": "Something went wrong"}

// Others:
"Invalid request"
```

**Impact:**
- Clients write inconsistent error handling
- Debugging becomes painful
- Support tickets increase

**Solution:** Define single error format. Enforce in code review.

### Anti-Pattern 3: No Deprecation Timeline

**Bad:**
```
"We'll remove the old endpoint when we feel like it"
```

**Impact:**
- Clients can't plan migrations
- You can't turn off old servers
- Technical debt accumulates
- Support burden increases

**Solution:** Public timeline. "v1 sunset 2026-12-31."

### Anti-Pattern 4: Silent Field Additions

**Bad:**
```json
// v1.0 response:
{"id": 123, "name": "Alice"}

// v1.5 response (no version bump):
{"id": 123, "name": "Alice", "email": "alice@example.com"}
```

**Impact:**
- Clients with strict schema validation break
- Parsing errors in different environments
- Clients can't track changes

**Solution:** Document all response schema changes. Bump minor version if adding fields.

### Anti-Pattern 5: Mixing Versioning Strategies

**Bad:**
```
GET /v1/users          # URL versioning
GET /projects?api_version=2  # Query versioning
POST /teams
Accept: application/vnd.api+json;version=3  # Header versioning
```

**Impact:**
- Clients confused about which version they're using
- Caching broken (same URL, different versions)
- Logs hard to parse

**Solution:** Pick ONE strategy. Enforce across all endpoints.

### Anti-Pattern 6: No Rate Limit Communication

**Bad:**
```
Client hits rate limit, gets 429 with no context.
No Retry-After header.
Client has to guess when to retry.
```

**Solution:** Include rate limit headers in every response:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1610702400
Retry-After: 60
```

### Anti-Pattern 7: Idempotency Without Semantics

**Bad:**
```
"Use Idempotency-Key header"
(but spec doesn't say what happens on retry)
```

**Impact:**
- Clients don't know if second request = no charge
- Financial operations charged twice
- Data corruption

**Solution:** Explicit semantics in spec:
```
"Same Idempotency-Key within 24h = same response,
 no duplicate charge, state unchanged"
```

---

## Checklist: Before You Write Code

Use this checklist when designing a new API:

- [ ] **Versioning**
  - [ ] Chosen: URL / Header / Query versioning
  - [ ] URL format: /v1, /v2 (or /api/v2, /api-v2)
  - [ ] Deprecation timeline documented
  - [ ] Backward compatibility guarantees written
  - [ ] Sunset date chosen (12 months from launch)

- [ ] **Endpoints**
  - [ ] Resource names clear (nouns, not verbs)
  - [ ] HTTP methods correct (POST=create, PUT=replace, PATCH=update)
  - [ ] Nesting max 2 levels (users/{id}/projects)
  - [ ] Query params for filters, not path params
  - [ ] Pagination strategy chosen (offset, cursor, keyset)
  - [ ] Response schema locked down (JSON examples provided)

- [ ] **Errors**
  - [ ] Standard error response format defined
  - [ ] Error codes documented (INVALID_EMAIL, etc.)
  - [ ] HTTP status codes chosen (400, 401, 403, 404, 409, 429, 500)
  - [ ] Each endpoint lists possible errors
  - [ ] Retry-ability classified (retryable vs. non-retryable)
  - [ ] Trace URL in error response for debugging

- [ ] **Rate Limiting & Idempotency**
  - [ ] Rate limit strategy chosen (per-user, per-IP, per-key)
  - [ ] Rate limit values set (1000 req/hour, etc.)
  - [ ] Idempotent endpoints identified (POST /charge, etc.)
  - [ ] Idempotency-Key header required where needed
  - [ ] Idempotency cache TTL set (24 hours)
  - [ ] Rate limit headers documented (X-RateLimit-*)

- [ ] **Deprecation**
  - [ ] Deprecation header added to v1 after launch of v2
  - [ ] Migration guide written
  - [ ] Sunset header includes exact date
  - [ ] Notification email prepared
  - [ ] Support runbook for sunset date prepared

- [ ] **Documentation**
  - [ ] Spec written using standard format
  - [ ] Example cURL requests provided
  - [ ] Error scenarios documented
  - [ ] Performance SLOs documented (e.g., <100ms p99)

- [ ] **Code Review**
  - [ ] Spec approved by at least 2 teams (frontend, backend)
  - [ ] PM signs off on timeline
  - [ ] Compliance reviews for auth, data handling
  - [ ] Security review for rate limiting, auth

---

## Example Contract Output

### REST API Contract: Authentication & User Management

**Project:** ShopApp Recruiter Platform
**Version:** v2.0
**Launch Date:** 2026-01-15
**Sunset Date:** v1 endpoint sunset 2027-01-15

---

## Versioning

- **Strategy:** URL versioning (`/v1`, `/v2`)
- **Current:** v2 (active)
- **Previous:** v1 (deprecated, sunset 2027-01-15)
- **Backward Compatibility:** v2 fully backward compatible with v1 for 12 months
- **Safe Changes in v2.x:** New optional fields, new endpoints, new error codes
- **Breaking Changes Require:** v3

**Deprecation Timeline:**
- v1 Launched: 2025-01-15
- v2 Launched: 2026-01-15 (both active)
- v1 Deprecation Notice: 2026-01-15 (Deprecation header, Sunset header)
- v1 Sunset: 2027-01-15 (returns 410 Gone)

---

## Endpoints

### POST /v2/auth/register

**Purpose:** Register a new recruiter account

**Authentication:** None (public endpoint)

**Request Body:**
```json
{
  "email": "string (required, email format, unique)",
  "password": "string (required, min 12 chars, must include uppercase, lowercase, number, special char)",
  "first_name": "string (required, 1-50 chars)",
  "last_name": "string (required, 1-50 chars)",
  "company": "string (optional, company name)"
}
```

**Response (201 Created):**
```json
{
  "id": "string (UUID)",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "company": "string",
  "created_at": "string (ISO 8601)",
  "email_verified": false,
  "verification_token_expires_at": "string (ISO 8601)"
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "status": 400,
  "request_id": "req_abc123",
  "details": [
    {"field": "email", "message": "Invalid email format"},
    {"field": "password", "message": "Must include at least one special character"}
  ]
}
```

**Response (409 Conflict):**
```json
{
  "error": "Email already registered",
  "code": "EMAIL_TAKEN",
  "status": 409,
  "request_id": "req_abc123"
}
```

**Possible Errors:**
- `VALIDATION_ERROR` (400): Field validation failed
- `EMAIL_TAKEN` (409): Email already registered
- `INTERNAL_ERROR` (500): Server error during registration

**Rate Limit:** 10 registrations per IP per hour

**Idempotent:** No

---

### POST /v2/auth/login

**Purpose:** Authenticate recruiter and return access token

**Authentication:** None

**Request Body:**
```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

**Response (200 OK):**
```json
{
  "access_token": "string (JWT, expires in 1 hour)",
  "refresh_token": "string (JWT, expires in 30 days)",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "string (UUID)",
    "email": "string",
    "first_name": "string",
    "last_name": "string"
  }
}
```

**Response (401 Unauthorized):**
```json
{
  "error": "Invalid email or password",
  "code": "AUTH_INVALID",
  "status": 401,
  "request_id": "req_abc123"
}
```

**Response (429 Too Many Requests):**
```json
{
  "error": "Too many login attempts. Try again in 15 minutes.",
  "code": "RATE_LIMITED",
  "status": 429,
  "request_id": "req_abc123",
  "retry_after": 900
}
```

**Possible Errors:**
- `AUTH_INVALID` (401): Email or password incorrect
- `RATE_LIMITED` (429): Too many failed attempts
- `ACCOUNT_DISABLED` (403): Account has been disabled
- `EMAIL_NOT_VERIFIED` (403): Email verification required

**Rate Limit:** 5 login attempts per IP per minute; 10 failed attempts → 15 min lockout

**Idempotent:** No

---

### GET /v2/auth/verify-email/{token}

**Purpose:** Verify email with token sent at registration

**Authentication:** None

**Path Parameters:**
- `token` (string, required): Email verification token from registration email

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Email verified successfully",
  "user": {
    "id": "string (UUID)",
    "email": "string",
    "email_verified": true
  }
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Token is invalid or expired",
  "code": "INVALID_TOKEN",
  "status": 400,
  "request_id": "req_abc123"
}
```

**Possible Errors:**
- `INVALID_TOKEN` (400): Token format invalid
- `TOKEN_EXPIRED` (400): Token has expired (24 hour TTL)
- `EMAIL_ALREADY_VERIFIED` (400): Email already verified

**Rate Limit:** 100 per hour per IP

**Idempotent:** Yes (multiple verifications with same token = same result)

---

### GET /v2/users/me

**Purpose:** Get current authenticated recruiter's profile

**Authentication:** Bearer token (required)

**Response (200 OK):**
```json
{
  "id": "string (UUID)",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "company": "string",
  "email_verified": true,
  "created_at": "string (ISO 8601)",
  "last_login_at": "string (ISO 8601)",
  "preferences": {
    "email_notifications": true,
    "two_factor_enabled": false
  }
}
```

**Response (401 Unauthorized):**
```json
{
  "error": "Authentication required",
  "code": "AUTH_REQUIRED",
  "status": 401,
  "request_id": "req_abc123"
}
```

**Response (401 Unauthorized - Expired Token):**
```json
{
  "error": "Token has expired",
  "code": "AUTH_EXPIRED",
  "status": 401,
  "request_id": "req_abc123",
  "refresh_url": "/v2/auth/refresh"
}
```

**Possible Errors:**
- `AUTH_REQUIRED` (401): No token provided
- `AUTH_INVALID` (401): Token malformed
- `AUTH_EXPIRED` (401): Token expired (use refresh_token)

**Rate Limit:** 1000 per hour per user

**Idempotent:** Yes

---

### POST /v2/auth/refresh

**Purpose:** Refresh expired access token using refresh token

**Authentication:** None (uses refresh_token in body)

**Request Body:**
```json
{
  "refresh_token": "string (required, from login response)"
}
```

**Response (200 OK):**
```json
{
  "access_token": "string (new JWT, expires in 1 hour)",
  "refresh_token": "string (rotated, expires in 30 days)",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Response (401 Unauthorized):**
```json
{
  "error": "Refresh token is invalid or expired",
  "code": "AUTH_INVALID",
  "status": 401,
  "request_id": "req_abc123",
  "login_url": "/v2/auth/login"
}
```

**Possible Errors:**
- `AUTH_INVALID` (401): Refresh token invalid or expired
- `AUTH_REQUIRED` (401): No refresh token provided

**Rate Limit:** 100 per hour per user

**Idempotent:** No (each call rotates refresh_token)

---

### GET /v2/users

**Purpose:** List recruiters (admin only)

**Authentication:** Bearer token with `admin` scope

**Query Parameters:**
```
page: int (optional, default: 1, min: 1)
page_size: int (optional, default: 50, min: 1, max: 100)
sort: string (optional, "created_at", "-created_at", default: "-created_at")
status: enum (optional, "active"|"inactive"|"suspended")
search: string (optional, searches email and name)
company: string (optional, filter by company)
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "string (UUID)",
      "email": "string",
      "first_name": "string",
      "last_name": "string",
      "company": "string",
      "status": "string",
      "created_at": "string (ISO 8601)",
      "last_login_at": "string (ISO 8601)"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 1200,
    "has_more": true
  }
}
```

**Response (403 Forbidden):**
```json
{
  "error": "Insufficient permissions",
  "code": "INSUFFICIENT_SCOPE",
  "status": 403,
  "request_id": "req_abc123",
  "required_scope": "admin"
}
```

**Possible Errors:**
- `AUTH_REQUIRED` (401): No token
- `INSUFFICIENT_SCOPE` (403): Token lacks `admin` scope
- `INTERNAL_ERROR` (500): Server error

**Rate Limit:** 100 per hour per user

**Idempotent:** Yes

---

## Error Handling

**Standard Error Format:**
All errors follow this structure:
```json
{
  "error": "Human-readable message",
  "code": "MACHINE_CODE",
  "status": 400,
  "request_id": "req_unique_id",
  "timestamp": "2026-01-15T10:30:00Z",
  "details": {}
}
```

**Error Codes:**

Authentication:
- `AUTH_REQUIRED`: Missing auth token
- `AUTH_INVALID`: Token malformed or invalid
- `AUTH_EXPIRED`: Token expired (use refresh)
- `INSUFFICIENT_SCOPE`: Token lacks required scope

Validation:
- `VALIDATION_ERROR`: Field validation failed
- `INVALID_EMAIL`: Email format invalid
- `INVALID_FIELD`: Specific field invalid
- `MISSING_FIELD`: Required field missing

Resource:
- `RESOURCE_NOT_FOUND`: Resource doesn't exist
- `EMAIL_TAKEN`: Email already registered
- `ACCOUNT_DISABLED`: Account disabled by admin

Rate Limit & Quota:
- `RATE_LIMITED`: Too many requests
- `QUOTA_EXCEEDED`: Usage quota exceeded

Server:
- `INTERNAL_ERROR`: Unexpected server error
- `SERVICE_UNAVAILABLE`: Service temporarily unavailable

---

## Rate Limiting & Idempotency

**Rate Limits (per authenticated user):**
- Login endpoint: 5 attempts/min, 10 failed attempts → 15 min lockout
- Registration: 10 per IP per hour
- General endpoints: 1000 per hour
- Search/List: 100 per hour

**Rate Limit Headers (in all responses):**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1610702400
Retry-After: 60  (if 429)
```

**Idempotency:**
- Email verification: Idempotent (same token = same result)
- Get endpoints: Idempotent (no side effects)
- Login, Registration, Token refresh: Non-idempotent
- No Idempotency-Key header required for these endpoints

---

## Deprecation

**API Versions:**
- v1: Deprecated since 2026-01-15, sunset 2027-01-15
- v2: Current (active, fully supported)

**Deprecation Headers (on v1 responses):**
```
Deprecation: true
Sunset: Sun, 15 Jan 2027 23:59:59 GMT
Link: </v2/auth/login>; rel="successor-version"
```

**Migration Guide:** See [API Migration v1 to v2](#)

**Support Timeline:**
- v1 Deprecated: 2026-01-15 (12 months support)
- v1 Sunset: 2027-01-15 (endpoints return 410 Gone)

---

## Performance SLOs

- Authentication endpoints (login, register): < 200ms p99
- Get user profile: < 100ms p99
- List users: < 500ms p99
- Error responses: < 50ms p99

---

## Edge Cases & Escalation Keywords

### Edge Case 1: Client request-response size limits exceed network MTU

**Symptom:** API contract specifies large response payloads (>10MB) but clients report frequent timeouts and dropped connections on mobile networks.

**Do NOT:** Assume clients should retry indefinitely or increase timeouts.

**Mitigation:**
- Add response size limits to contract: `max_response_size: 5MB`
- Require pagination for large datasets (cursor-based, max 1000 items per page)
- Compression mandatory: `gzip` for responses > 1MB
- Document in contract: "Responses exceeding 5MB require explicit pagination support in client"

**Escalation:** NEEDS_CONTEXT — Does client support compression and pagination? If not, BLOCKED until client implementation updated.

---

### Edge Case 2: Token expiration semantics differ across services

**Symptom:** Authentication contract specifies `expires_in: 3600` but service A interprets as "invalidate token after 3600s" and service B interprets as "token valid until epoch_time + 3600". Different behavior under load.

**Do NOT:** Assume all services interpret TTL the same way.

**Mitigation:**
- Use explicit UTC timestamps: `access_token_expires_at: "2026-01-15T15:30:00Z"` (not relative)
- Document clock sync requirement: "All services must sync NTP, maximum 5s clock skew"
- Include `issued_at` timestamp: allows client verification of token age
- Specify behavior on clock skew: "If server time < token issue time, reject as invalid"

**Escalation:** NEEDS_COORDINATION — Services must verify NTP sync before contract lock.

---

### Edge Case 3: Rate limit headers missing during burst traffic

**Symptom:** API hits rate limit during legitimate burst (e.g., mobile app sync), returns 429 without `Retry-After` header. Client guesses 1s, sends 1000 requests in parallel, making problem worse.

**Do NOT:** Assume clients will honor missing headers or implement smart backoff.

**Mitigation:**
- Make `Retry-After` and `X-RateLimit-Reset` mandatory in every 429 response
- `Retry-After` in seconds: `Retry-After: 60`
- Include millisecond precision in `X-RateLimit-Reset`: `X-RateLimit-Reset: 1610702400123`
- Document in contract: "429 without Retry-After is client bug — verify with backend team"

**Escalation:** NEEDS_INFRA_CHANGE — If rate limiter cannot emit headers, BLOCKED. Requires rate limiter upgrade.

---

### Edge Case 4: Idempotency key collision across multiple products

**Symptom:** Shared microservices infrastructure. Two products independently choose idempotency key format `{timestamp}-{sequence}`. Keys collide. Charge-payment endpoint applies charge from Product A to Product B's transaction.

**Do NOT:** Trust idempotency keys without namespace prefixes.

**Mitigation:**
- Require namespaced idempotency keys: `{service}-{product}-{timestamp}-{uuid}`
  - Example: `payment-shopapp-1610702400-abc123def456`
  - Prevents cross-product collisions
- Document in contract: "Idempotency keys must include product prefix"
- Validate prefix in implementation: if missing or wrong product, reject

**Escalation:** NEEDS_COORDINATION — All services must use agreed idempotency key format. Cannot lock contract until format agreed.

---

### Edge Case 5: Inconsistent field naming in nested objects

**Symptom:** Contract specifies nested error response `details` with `field: string`. Service A sends `details[0].field_name`, Service B sends `details[0].fieldName` (camelCase). Client JSON parsers fail.

**Do NOT:** Assume field naming is self-evident.

**Mitigation:**
- Lock field naming convention in contract: "All JSON fields use snake_case: `field_name`, `error_code`, `request_id`"
- Nested objects follow same rule: `details[0].field_name` (not `fieldName`)
- Example valid response:
  ```json
  {
    "error": "Validation failed",
    "code": "VALIDATION_ERROR",
    "details": [
      {"field_name": "email", "error_message": "Must be valid"}
    ]
  }
  ```
- List all field names in response schema examples

**Escalation:** BLOCKED if any service deviates. Code review must enforce naming.

---

### Edge Case 6: Partial success semantics for batch endpoints

**Symptom:** Contract defines `POST /v2/users/batch` accepting 100 user records. 95 succeed, 5 fail (email duplicates). Service A returns 400 (rejects entire batch), Service B returns 207 (partial success with error list). Clients implement different batch rollback logic.

**Do NOT:** Leave partial success semantics undefined.

**Mitigation:**
- Lock response status for batch endpoints:
  - `200 OK`: All records succeeded
  - `207 Multi-Status`: Partial success (include per-item status in response)
  - `400 Bad Request`: Batch syntax error, entire batch rejected
- Response format for 207:
  ```json
  {
    "status": 207,
    "summary": {"total": 100, "succeeded": 95, "failed": 5},
    "items": [
      {"index": 0, "status": 201, "id": "user_123"},
      {"index": 47, "status": 409, "error": "EMAIL_DUPLICATE"}
    ]
  }
  ```
- Document idempotency for partial success: "Retrying with same Idempotency-Key returns same 207 response"

**Escalation:** NEEDS_COORDINATION — Batch semantics must be agreed before lock. Some services may need to re-implement rollback logic.

---

### Edge Case 7: Deprecated endpoint still used by legacy mobile client

**Symptom:** Contract sunsets `/v1/auth/login` on 2027-01-15. 30% of mobile users still on app version from 2025 (6 months old). After sunset, they can't log in. No way to force upgrade.

**Do NOT:** Assume all clients will upgrade before sunset.

**Mitigation:**
- Extend deprecation period for mobile: 18 months (not 12) due to App Store review delays
- Set up graceful degradation: After sunset, `/v1/auth/login` redirects to `/v2/auth/login` (307) with migration instructions
- Monitoring: Track `/v1` usage by client version for 6 months pre-sunset
- Decision: If >5% traffic on `/v1` at 3 months pre-sunset, delay sunset 3 more months
- Announce in app: In-app notification 30 days before sunset with forced upgrade reminder

**Escalation:** NEEDS_CONTEXT — What's the oldest app version still in use? If >6 months old, extend deprecation.

---

## Decision Tree 1: API Versioning Strategy

**Q: How will your API evolve over the next 2 years?**

→ **Small changes to response structure (add fields, endpoints)**
  - Use: **URL Versioning** (`/v1`, `/v2`)
  - Reason: Explicit in logs, easy to cache, simple routing
  - Timeline: Launch v2 when breaking change needed (12 months typical)
  - Cost: Slight URL duplication, but clear and cacheable

→ **Frequent schema evolution, clients control version**
  - Use: **Header Versioning** (`Accept: application/vnd.api+json;version=2`)
  - Reason: Cleaner URLs, one code path per logic
  - Trade-off: Hidden from logs, cache-unfriendly, clients often forget headers
  - Best for: Clients with sophisticated header support (native apps, browser APIs)

→ **Unstable API (research/beta)**
  - Use: **Subdomain Versioning** (`v1.api.example.com`, `v2.api.example.com`)
  - Reason: Separate infrastructure, easier to deprecate
  - Cost: Additional DNS, TLS certs, CDN configuration
  - Use when: Running multiple API generations simultaneously

**Decision Flow:**
```
Is your API expected to evolve frequently (>2 breaking changes/year)?
├─ YES  → Use URL versioning (easiest to rotate)
│        Backward compatibility window: 12 months
│        Sunset date locked at launch
│
└─ NO   → Use Header versioning (simpler URLs)
         Backward compatibility window: 18 months (allows slower adoption)
         Sunset date can be flexible within bounds
```

**Key Commitment in Contract:**
```markdown
# Versioning Strategy

- **Method**: [URL | Header | Subdomain] versioning
- **Active Support Duration**: [12|18|24] months per version
- **Backward Compatibility**: [All v2.x releases compatible with v2.0 requests]
- **Sunset Date for v1**: [Explicit ISO 8601 date]
- **Migration Path**: [Explicit link to v2 migration guide]
```

---

## Decision Tree 2: Error Contract Definition

**Q: What types of errors must your API handle?**

→ **Standard validation errors only (missing fields, wrong types)**
  - Response format:
    ```json
    {
      "error": "Validation failed",
      "code": "VALIDATION_ERROR",
      "status": 400,
      "details": [
        {"field": "email", "message": "Must be valid email format"}
      ]
    }
    ```
  - Status codes: `400` (validation), `401` (auth), `404` (not found)
  - Retry policy: No retry on validation errors
  - Cost: Simple, client-side checks prevent most errors

→ **Validation + custom business errors (duplicate email, quota exceeded)**
  - Response format:
    ```json
    {
      "error": "Email already registered",
      "code": "EMAIL_TAKEN",
      "status": 409,
      "request_id": "req_abc123",
      "details": {
        "field": "email",
        "message": "Choose a different email address"
      }
    }
    ```
  - Status codes: `400` (validation), `409` (conflict), `429` (quota), `401`, `404`
  - Error codes: Domain-specific (`EMAIL_TAKEN`, `QUOTA_EXCEEDED`, `ACCOUNT_DISABLED`)
  - Retry policy: No retry on `409` (conflict is permanent), retry on `429` with backoff
  - Cost: More error codes to document and maintain

→ **Validation + business errors + transient failures with retry**
  - Status codes: All above + `408` (timeout), `502` (bad gateway), `503` (unavailable)
  - Response includes retry guidance:
    ```json
    {
      "error": "Temporary service unavailable",
      "code": "SERVICE_UNAVAILABLE",
      "status": 503,
      "retry_after_seconds": 60,
      "request_id": "req_abc123"
    }
    ```
  - Retry policy: `408`, `429`, `502`, `503` are retryable; others are not
  - Client responsibility: Implement exponential backoff, max 3 retries
  - Cost: Complex error handling, client confusion without clear docs

**Decision Flow:**
```
How many distinct error scenarios must clients handle?
├─ <10   → Use Standard Error Format
│        Status codes: 400, 401, 403, 404, 500
│        One error code per HTTP status
│
├─ 10-30 → Use Custom Error Codes
│        Preserve HTTP status for class (4xx = client, 5xx = server)
│        Domain-specific codes for handling (EMAIL_TAKEN, QUOTA_EXCEEDED)
│        Define retry policy per code
│
└─ >30   → Use Hierarchical Error Taxonomy
          Parent category: VALIDATION, AUTH, RESOURCE, SERVER
          Subcategory: Specific error (INVALID_EMAIL, EMAIL_TAKEN, MISSING_FIELD)
          Error code: VALIDATION::INVALID_EMAIL
          Retry policy tied to subcategory
```

**Key Commitment in Contract:**
```markdown
# Error Contract

## Standard Codes (Required)
- AUTH_REQUIRED (401)
- AUTH_INVALID (401)
- INSUFFICIENT_SCOPE (403)
- INVALID_REQUEST (400)
- RESOURCE_NOT_FOUND (404)
- RATE_LIMITED (429)
- INTERNAL_ERROR (500)

## Custom Codes (Domain-Specific)
- EMAIL_TAKEN (409)
- INVALID_EMAIL (400)
- QUOTA_EXCEEDED (429)
- [Add domain-specific codes]

## Retry Policy
- Retryable: 429, 503, 408 (with Retry-After header)
- Non-retryable: 400, 401, 403, 404, 409
- Idempotent endpoint: Can retry with Idempotency-Key

## Response Format (All Errors)
```json
{
  "error": "Human message",
  "code": "MACHINE_CODE",
  "status": <HTTP status>,
  "request_id": "req_...",
  "retry_after": <seconds if retryable>
}
```
```

---

## Edge Cases & Fallback Paths

### Edge Case 1: Old API version still needs backward compatibility support

**Diagnosis**: New PRD requires API v2 with breaking changes, but v1 is still live in production with active clients. Cannot deprecate immediately.

**Response**:
- **Dual support strategy**: Support both v1 and v2 simultaneously.
- **Versioning approach**: 
  - v1 endpoints: `/api/v1/users`, `/api/v1/orders` (frozen, no new changes)
  - v2 endpoints: `/api/v2/users`, `/api/v2/orders` (new breaking changes)
- **Migration window**: Document deprecation path: "v1 will be sunset at [date]. Clients must migrate by [deadline]."
- **Contract specification**: Explicitly list which endpoints are v1-only, v2-only, and shared.
- **Fallback**: If one team still depends on v1, versioning window extends until they migrate.

**Escalation**: If v1 and v2 must coexist indefinitely, escalate to user: "Indefinite dual-version support increases maintenance cost. Recommend: set firm v1 sunset date or find alternative versioning approach."

---

### Edge Case 2: Endpoint already exists with different signature

**Diagnosis**: New PRD wants to add `POST /users/{id}/avatar`, but that endpoint already exists with different request body shape (old: `{ url: string }`, new: `{ file: multipart, size: int }`).

**Response**:
- **Detect**: Scan existing API contract for conflicting paths.
- **Options**:
  1. **Use query param to distinguish**: `POST /users/{id}/avatar?mode=url|multipart` — Not ideal, but allows coexistence.
  2. **Create new endpoint**: `POST /users/{id}/avatar-file` (new, separate) vs `/users/{id}/avatar-url` (old). More explicit.
  3. **Deprecate old**: Mark old endpoint as deprecated, migrate all callers to new signature, then sunset old.
  4. **Support both**: Accept both request shapes, detect based on content. More complex, but backward-compatible.
- **Decision**: Document which approach was chosen and why.

**Escalation**: If no clear winner (e.g., too many clients on old format, new format incompatible), escalate to NEEDS_CONTEXT - Team must decide compatibility strategy.

---

### Edge Case 3: Versioning strategy conflicts between teams

**Diagnosis**: Backend team wants URL versioning (`/api/v2/...`). Frontend team prefers header versioning (`Accept: application/vnd.api+json;version=2`). Mobile team says "just add a query param."

**Response**:
- **Document conflict**: Flag it in the contract.
- **Standards check**: What's the existing pattern in the product? Stick with it for consistency.
- **Decision criteria**:
  - URL versioning: Most explicit, works with caching, easy for debugging.
  - Header versioning: Cleaner URLs, better for semantic versioning, harder to debug.
  - Query param: Simple to add, but often considered anti-pattern.
- **Recommend**: Use existing product standard. If product has no standard, URL versioning is safest default.
- **Escalate to dreamer**: If teams genuinely disagree, use dreamer conflict resolution to score each approach.

**Escalation**: NEEDS_CONTEXT - Team must align on versioning strategy before proceeding. If blocked, escalate to dreamer.

---

### Edge Case 4: Error response format conflicts with other contracts

**Diagnosis**: API contract specifies error format `{ code: string, message: string }`. But schema contract specifies error format `{ error_code: int, error_text: string }`. Inconsistent across services.

**Response**:
- **Detect**: Cross-contract validation. Check if error formats are consistent across API, schema, event bus, cache contracts.
- **Normalize**: Pick one canonical error format and apply across all contracts.
- **Decision**: Typically, REST API error format is canonical (most visible to clients). Apply that format to internal contracts too.
- **Document mapping**: If internal services use different format, document the mapping: "API errors: { code, message }. Internal MySQL errors: { error_code, error_text }. Mapping: error_code → code, error_text → message."

**Escalation**: If error format spans multiple teams' contracts, escalate to council: "Error format inconsistency across contracts. Requires negotiation between API, DB, and event bus teams."

---

### Edge Case 5: Payload size or complexity makes endpoint unfeasible

**Diagnosis**: New endpoint requires accepting a deeply nested JSON structure (50+ fields, 5 levels deep) with circular references possible. Server-side validation becomes complex, parsing is slow, storage is expensive.

**Response**:
- **Feasibility check**: Assess if endpoint can realistically be built in timeline.
- **Options**:
  1. **Simplify payload**: Reduce nesting, remove optional fields, flatten structure.
  2. **Split into multiple endpoints**: Instead of one complex endpoint, create 3-4 simpler ones.
  3. **Stream/chunked upload**: For large payloads, use streaming or multipart upload.
  4. **Async processing**: Accept request, queue for async processing, return job ID. Client polls for result.
- **Decision**: Document trade-offs.

**Escalation**: If payload is truly too complex and cannot be simplified, escalate to user: "Endpoint complexity exceeds feasibility estimate. Recommend: redesign data model or split into multiple simpler endpoints."

---

## Commit

**Ready for:** Shared-dev-spec lock

**Next Steps:**
1. Frontend team reviews endpoint shapes
2. Backend team confirms feasibility
3. Mobile team checks error handling
4. PM confirms timeline and sunset date
5. All teams sign off on contract

## Checklist

Before claiming completion:

- [ ] All endpoints have a versioning strategy defined (URL path `/v1`, header, or content-type — one strategy, applied consistently)
- [ ] Error codes are standardized in a single envelope format agreed across all consumer teams
- [ ] Authentication mechanism is locked (JWT, API key, OAuth) with token lifetime, rotation, and clock-skew tolerances specified
- [ ] Rate limit values are set per endpoint or per client tier, with all required headers (`X-RateLimit-*`, `Retry-After`) documented
- [ ] Every mutating endpoint (POST/PUT/PATCH) has idempotency semantics specified: key format, TTL, and behavior on duplicate
- [ ] Deprecation timeline is written into the contract: notice date, sunset date, migration guide URL
- [ ] All consumer surfaces (backend, web, app) have signed off on the contract shape before it is locked
- [ ] Backward compatibility guarantees are written explicitly: what changes are safe in minor versions, what requires a major bump


# REST Contract Patterns: Versioning, Endpoints, Rate Limiting, Idempotency, Deprecation

Pattern catalog and decision matrices for negotiating a REST API contract. The SKILL.md
operational spine points here for the full technique depth.

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
v1 Launch:             2024-01-01
v2 Launch:             2025-01-01 (v1 still active)
v1 Deprecation Notice: 2026-01-15
v1 Sunset (shut down): 2027-01-15  (12 months after the deprecation notice)
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

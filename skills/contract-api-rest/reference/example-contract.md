# Worked Example: Full REST API Contract Output

A complete, locked REST API contract for a realistic surface (auth + user management).
The SKILL.md spine points here as the model output shape — real keys, real error
envelopes, real rate-limit and deprecation sections.

## REST API Contract: Authentication & User Management

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

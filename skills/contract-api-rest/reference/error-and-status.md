# REST Error Envelope, Error Code Taxonomy & HTTP Status Mapping

Full error-handling depth for the REST contract. The SKILL.md spine points here for the
locked error envelope, the error-code catalog, the HTTP status-code mapping, and
retry-ability rules.

## Standard Error Response Format

**Baseline: [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457) (`application/problem+json`)** is the interoperable error envelope — prefer it, or map the fields below onto its members (`type`, `title`, `status`, `detail`, `instance` + extensions). The contract MUST state which envelope is locked and why. The bespoke shape below maps to problem-details as: `error`→`detail`, `code`→a `type` URI (or an extension), `status`→`status`, `details`→extension members, `request_id`/`trace_url`→extensions.

**All 4xx and 5xx responses must follow the locked format** (example, bespoke shape):

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

## Error Code Taxonomy

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

## HTTP Status Code Mapping

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

## Retry-ability Classification

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

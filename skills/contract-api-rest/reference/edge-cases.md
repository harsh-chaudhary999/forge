# REST Contract Edge Cases, Escalation Keywords & Fallback Paths

Extended edge-case catalog for the REST contract. Each entry names the symptom, the
"do NOT" trap, the mitigation, and the escalation fork (NEEDS_CONTEXT /
NEEDS_COORDINATION / NEEDS_INFRA_CHANGE / BLOCKED). Resolve every fork through
`AskUserQuestion` — see [`skills/_shared/human-input.md`](../../_shared/human-input.md).

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

# Backend Reasoning — Contract & Anti-Pattern Catalog

Contract-thinking patterns (versioning, schema evolution, cache strategy) and
the common pitfalls catalog. The discipline guards (Iron Law, Red Flags,
Anti-Pattern Preamble) stay in `../SKILL.md`; this file is the deep reference.

## Contract Thinking

**API Versioning Strategy**
- **v1 (Deprecated):** Old clients using 2FA via TOTP only
  - Endpoint: POST /auth/2fa/enable → {method: implicit "totp"}
  - Sunset: 2026-10-01 (≈6 months after v2 GA)
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

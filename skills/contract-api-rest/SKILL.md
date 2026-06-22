---
name: contract-api-rest
description: "WHEN: Council has identified REST API conflicts across surfaces and needs a locked contract. Negotiates versioning strategy, endpoint shape, error codes, auth, rate limits, idempotency, and deprecation across all consumer teams."
type: rigid
effort: high
requires: [brain-read]
version: 1.0.1
preamble-tier: 3
triggers:
  - "design REST API"
  - "define API contract"
  - "REST contract"
  - "API endpoints spec"
allowed-tools:
  - Write
  - AskUserQuestion
---

# Contract-API-REST Skill

## Human input

Resolve every human-decision fork (NEEDS_CONTEXT / NEEDS_COORDINATION / NEEDS_INFRA_CHANGE / BLOCKED) through **`AskUserQuestion`** (in `allowed-tools`) — never a prose-only "reply if…". Canonical convention: [`skills/_shared/human-input.md`](../_shared/human-input.md).

## Step 0 — Recall prior contracts (before negotiating)

This skill declares `requires: [brain-read]` — exercise it. Before proposing the REST contract: `brain_recall`/grep the product topology (`products/<slug>/product.md`) and any existing `api-rest-contract.md` + prior API decisions for the affected entity, so this contract supersedes rather than duplicates prior locks. Record the resulting `contract_id` (brain decision id / commit SHA) in the LOCK checklist.

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

## Contract dimensions (full technique depth in reference)

Negotiate each dimension below to the minimum-depth bar above. Pull the pattern detail, decision matrices, and worked templates from the reference files only when you need them:

1. **Versioning** — URL vs header vs query, graduated deprecation timeline, backward-compat guarantees (safe-in-minor vs requires-major). Full detail in [reference/patterns.md](reference/patterns.md) §1 + Decision Tree 1.
2. **Endpoint specification** — resource vs action naming, max-2-level nesting, request/response schema template, query-parameter standards (filter, paginate, sort, expand), path-parameter rules. Full detail in [reference/patterns.md](reference/patterns.md) §2.
3. **Error handling** — locked error envelope (RFC 9457 baseline + bespoke mapping), error-code taxonomy, full HTTP status-code mapping, retry-ability classification. Full detail in [reference/error-and-status.md](reference/error-and-status.md) + Decision Tree 2 in [reference/patterns.md](reference/patterns.md).
4. **Rate limiting & idempotency** — per-user/per-IP/per-key strategies, rate-limit headers, `Idempotency-Key` server behavior, exactly-once vs non-idempotent semantics. Full detail in [reference/patterns.md](reference/patterns.md) §4.
5. **Deprecation** — RFC 8594 headers, 12-month migration period, forced-upgrade graceful shutdown, post-sunset 410 body. Full detail in [reference/patterns.md](reference/patterns.md) §5.

**Anti-patterns to prevent** (versioning-later, inconsistent error formats, no deprecation timeline, silent field additions, mixed versioning strategies, no rate-limit communication, idempotency without semantics): full catalog with bad/solution pairs in [reference/patterns.md](reference/patterns.md) → "Anti-Patterns to Prevent".

**Worked example** — a complete locked contract (auth + user management: register, login, verify-email, /users/me, refresh, list users) with real request/response bodies, error envelopes, rate-limit section, deprecation section, and performance SLOs: [reference/example-contract.md](reference/example-contract.md).

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

## Edge Cases & Escalation

Extended edge-case catalog — symptom, the "do NOT" trap, mitigation, and escalation fork (NEEDS_CONTEXT / NEEDS_COORDINATION / NEEDS_INFRA_CHANGE / BLOCKED) — lives in [reference/edge-cases.md](reference/edge-cases.md). It covers two groups:

- **Escalation keywords** (7 cases): response-size vs MTU, token-expiration semantics, missing rate-limit headers in burst, idempotency-key collision across products, inconsistent nested-field naming, partial-success batch semantics (207), deprecated endpoint still used by legacy mobile.
- **Fallback paths** (5 cases): dual v1/v2 support, endpoint already exists with different signature, versioning-strategy conflict between teams, error-format conflict across contracts, payload too complex to be feasible.

Resolve every escalation fork through **`AskUserQuestion`** (see the Human input pointer above and [`skills/_shared/human-input.md`](../_shared/human-input.md)).

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

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] Every endpoint in the contract is agreed by both producer and all consumer surfaces — no endpoint was added unilaterally
- [ ] Request and response schemas (including all error envelopes) are locked in `shared-dev-spec.md` with real JSON examples, not prose descriptions
- [ ] `contract_api_status: negotiated` is set in the `shared-dev-spec.md` frontmatter (or the contract file heading) — not `draft` or `TBD`
- [ ] No `TBD` fields remain in any endpoint schema — every field has a name, type, nullability, and example value
- [ ] A `contract_id` anchor (brain decision ID or commit SHA) is recorded in the brain commit, linking the locked contract to its negotiation record


## Cross-References

| Skill / Doc | Relationship |
|---|---|
| `council-multi-repo-negotiate` | **Caller** — invokes this skill when REST API conflict is identified during council |
| `spec-freeze` | **Downstream** — `shared-dev-spec.md` contract section is locked after this skill's output |
| `forge-council-gate` | **Gate** — all 5 contracts (including REST API) must be negotiated before spec freeze |
| `contract-event-bus` | **Sibling contract** — event bus contracts often depend on REST API payload shape |
| `tech-plan-write-per-project` | **Consumer** — Section 1b.5 traces synchronous API wiring from this contract |
| `spec-reviewer` | **Verifier** — checks implementation matches the locked REST API contract line-by-line |

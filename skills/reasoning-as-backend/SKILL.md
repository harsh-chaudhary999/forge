---
name: reasoning-as-backend
description: "WHEN: Council is reasoning about a PRD. You are the backend perspective (REST/gRPC/SQL). Analyze the PRD for API endpoints, data models, service boundaries, async patterns, performance SLOs."
type: rigid
effort: high
requires: [brain-read]
version: 1.0.1
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
What about request/response schemas? Error codes? Headers?

Worked example (2FA endpoints + full request/response/error block) in [reference/examples.md](reference/examples.md#1-api-endpoints--worked-example).

## 2. Data Models

What's the schema shape? Primary keys? Relationships? Indexes?
What about constraints, denormalization, soft deletes?

Worked example (users/sessions/recovery-codes DDL) in [reference/examples.md](reference/examples.md#2-data-models--worked-example).

## 3. Service Boundaries

What service owns what data? What calls which service?
What about service-to-service auth? (mTLS, service tokens, API keys)?

Worked example (Auth/User/Audit ownership map) in [reference/examples.md](reference/examples.md#3-service-boundaries--worked-example).

## 4. Async Patterns

What happens asynchronously? Queues? Events? Eventual consistency?
What's the publish guarantee? (at-most-once, at-least-once, exactly-once)?

Worked example (event schemas, consumers, DLQ handling) in [reference/examples.md](reference/examples.md#4-async-patterns--worked-example).

## 5. Performance SLOs

What are the latency targets? Throughput? Storage?
What about retry budgets? Timeouts? Circuit breakers?

Worked example (endpoint/DB/throughput/storage SLOs) in [reference/examples.md](reference/examples.md#5-performance-slos--worked-example).

---

## Post-Implementation Checklist

- [ ] All new endpoints have input validation at the boundary (not assumed valid from caller).
- [ ] Database queries use parameterized statements (no string interpolation in SQL).
- [ ] Error responses return structured JSON with an error code (not raw exception messages).
- [ ] Service does not silently swallow exceptions — all catch blocks log or re-throw.
- [ ] Integration test covers the new endpoint with a real (or test-scoped) database connection.

## Output

Write to `~/forge/brain/prds/<task-id>/council/backend.md`. The document MUST
emit these sections, each fully concrete (no TBDs):

1. **# Backend Perspective** (title)
2. **## API Endpoints** — per endpoint: method+path+version, auth mechanism, idempotency, rate limit, request schema, response schema, full error-code set.
3. **## Data Models** — every table's DDL (PK, columns, indexes, FK + ON DELETE behavior).
4. **## Service Boundaries** — per service: what it Owns, what it Exposes (public + internal), what it Calls, service-to-service auth.
5. **## Async Patterns** — per event: topic, partition key, schema, consumers, publish guarantee, retention.
6. **## Performance SLOs** — API latency, database performance, throughput, storage, caching, errors & retries (all concrete p95/p99 + numbers).
7. Closing line: **`**Ready for:** Council negotiation`**

Full worked `council/backend.md` instance in [reference/examples.md](reference/examples.md#full-council-output-example-councilbackendmd).

## Anti-Pattern: "We'll figure it out in Backend"

Do NOT write:
- "API endpoints TBD"
- "We'll cache the important stuff"
- "Async later, sync for now"
- "We can denormalize if it's slow"
- "SLOs TBD"

Every detail must be locked before code starts. API contracts and database schema changes are the hardest to roll back.

---

## Edge Cases & Failure Modes

Reason through these before closing. Full strategies, symptoms, mitigations, and
worked examples in [reference/edge-cases.md](reference/edge-cases.md):

- Schema changes breaking API contracts; eventual-consistency windows; rate limiting & backpressure; DB migration + backward compatibility on rolling deploys; cross-service dependency fallbacks (Edge Cases 1–5 strategies).
- Cross-service failure modes with escalation codes: circular dependency (`NEEDS_COORDINATION`), broken distributed trace / missing correlation ID (`NEEDS_COORDINATION`), event-bus ordering violation (`NEEDS_COORDINATION`), cache-invalidation race (`NEEDS_COORDINATION`), inconsistent request/response validation between services (`NEEDS_CONTEXT`).

## Common Pitfalls

Catalog (schema-without-migration, required-fields-without-defaults, removing deprecated endpoints too fast, unvalidated input, silent async-job failures) in [reference/patterns.md](reference/patterns.md#common-pitfalls).

## Contract Thinking

API versioning, event-schema evolution, DB backward-compat, and cache key/invalidation strategy in [reference/patterns.md](reference/patterns.md#contract-thinking).

## Dependency Chain Thinking

Worked failure scenarios (Auth→User Service down/slow/bad-data; Sessions→Redis down/out-of-sync/key-collision) in [reference/examples.md](reference/examples.md#dependency-chain-thinking).

## Decision Tree: Synchronous vs. Asynchronous Reasoning

Choose sync (blocking, client-waiting, within-SLO, transactional) vs. async (queue + eventual consistency + retry/DLQ; partition key when ordering matters). Full decision tree and the implementation decision matrix in [reference/decision-matrices.md](reference/decision-matrices.md).

---

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

---
name: contract-cache
description: "WHEN: Council has identified cache design conflicts across surfaces and needs a locked contract. Negotiates key patterns, TTL strategy, invalidation, stampede prevention, serialization, and consistency model across all services."
type: rigid
effort: high
requires: [brain-read]
version: 1.0.1
preamble-tier: 3
triggers:
  - "design cache contract"
  - "define cache strategy"
  - "cache layer spec"
allowed-tools:
  - Write
  - AskUserQuestion
---

# contract-cache Skill

## Human input

Resolve every human-decision fork (NEEDS_CONTEXT / NEEDS_COORDINATION / NEEDS_INFRA_CHANGE / BLOCKED) through **`AskUserQuestion`** (in `allowed-tools`) — never a prose-only "reply if…". Canonical convention: [`skills/_shared/human-input.md`](../_shared/human-input.md).

Teaches teams to negotiate Redis/Memcached cache contracts. Covers key structure, TTL strategy, invalidation patterns, cache stampede prevention, and serialization for production cache systems.

## Iron Law

```
EVERY CACHE KEY'S TTL AND INVALIDATION STRATEGY MUST BE NEGOTIATED AT COUNCIL AND LOCKED IN THE CONTRACT BEFORE ANY IMPLEMENTATION BEGINS. NO SERVICE MAY UNILATERALLY CHOOSE ITS OWN TTL OR INVALIDATION LOGIC FOR SHARED KEYS.
```

## Anti-Pattern Preamble: Cache Contract Failures

| Rationalization | The Truth |
|---|---|
| "We'll figure out TTLs later" | TTL IS the contract. Wrong TTL means stale data served to users (too long) or cache misses under load (too short). Every key MUST have an explicit TTL in the contract. No defaults. |
| "Invalidation is simple — just delete the key" | Simple DELETE causes stampede: 1000 concurrent requests all miss cache simultaneously, hammering the database. You need stampede prevention (lock-and-refresh, probabilistic early expiry, or write-through). |
| "Cache is just a performance optimization, not critical" | Cache failures cascade. If Redis goes down and you have no fallback, every request hits the database. Cache IS part of your architecture. Contract must specify fallback behavior (degrade gracefully vs. fail fast). |
| "Both services can write to the same cache key" | Two writers to the same key create race conditions: last-write-wins with no ordering guarantee. The contract must specify exactly ONE owner per key. Cross-service cache access requires read-only contracts. |
| "Serialization format doesn't matter" | Service A writes JSON, Service B expects MessagePack. Service A writes `{user_id: 123}`, Service B expects `{userId: 123}`. Serialization format and field naming must be explicitly contracted. |

---

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Any cache key is specified without an explicit TTL** — A key without a TTL is a memory leak waiting to happen, or stale data served indefinitely. STOP. Every key in the contract must have a concrete TTL value — no "default", no "TBD", no "same as session".
- **Two services are specified as writers to the same cache key** — Two writers create a last-write-wins race with no ordering guarantee, producing unpredictable data. STOP. Each key must have exactly one owner service. Other services may only read.
- **Cache stampede prevention is absent from the contract** — A cache miss under load sends all concurrent requests simultaneously to the database. STOP. Every high-traffic key must specify its stampede prevention strategy (lock-and-refresh, probabilistic early expiry, or write-through).
- **Fallback behavior when cache is unavailable is not specified** — When Redis or Memcached goes down, the system must decide: fail fast or degrade to direct DB reads. Without a specified fallback, behavior is undefined and inconsistent across services. STOP. Every key type must specify its cache-miss fallback.
- **Key naming pattern is not specified with a namespace prefix** — Unnamespaced keys from different services collide silently. STOP. Every key pattern must include a namespace that uniquely identifies the owning service (e.g., `auth:session:{id}`, not just `session:{id}`).
- **Invalidation trigger is described as "on deploy" or "manually"** — Manual invalidation is not a strategy; it will not happen consistently. STOP. Every key must have a programmatic invalidation trigger tied to a specific data mutation event.

## When to Use This Skill

Use this skill when:
- Designing cache layers for high-traffic systems
- Integrating Redis or Memcached into microservices
- Preventing cache stampedes and ensuring consistency
- Documenting cache behavior across teams
- Negotiating service-to-cache contracts

## Key Concepts

Full key-concept depth — key structure & namespacing, TTL freshness tiers, the four invalidation patterns (cache-aside / write-through / write-back / event-based), stampede prevention (xfetch / mutex / stale fallback), and serialization & consistency models — in [reference/patterns.md](reference/patterns.md).

---

## Example: Full Cache Contract

Full worked cache contract (e-commerce service: key structure, TTL table, invalidation, stampede prevention, serialization) plus the **Decision Tree: Cache Isolation Strategy** (Owned / Read-Shared / Shared-Mutable models, decision flow, and the Cache Isolation commitment template) in [reference/examples.md](reference/examples.md).

---

## Checklist for Implementation

When implementing a cache contract:

- [ ] Define namespace prefixes for each domain entity
- [ ] Document key composition rules with examples
- [ ] Assign TTL for each key pattern (match freshness SLOs)
- [ ] Choose invalidation pattern (cache-aside, write-through, write-back, event-based)
- [ ] Implement stampede prevention (xfetch + mutex or stale fallback)
- [ ] Choose serialization format (JSON, binary, string)
- [ ] Plan version tagging for schema migrations
- [ ] Document consistency model (strong, eventual, probabilistic)
- [ ] Set up monitoring: cache hit rate, miss rate, latency, evictions
- [ ] Test under load: verify stampede prevention works
- [ ] Document in service contract; share with dependent teams

## Checklist

Before claiming completion:

- [ ] Every cache key in the contract has an explicit TTL value — no "default", no "TBD", no "same as session"
- [ ] Each key has exactly one owner service documented — no two services listed as writers to the same key
- [ ] Stampede prevention strategy is specified per high-traffic key (lock-and-refresh, xfetch, or stale fallback)
- [ ] Fallback behavior when cache is unavailable is documented for every key type (fail fast vs. degrade to DB reads)
- [ ] All key patterns include a namespace prefix that uniquely identifies the owning service
- [ ] Invalidation trigger is a programmatic event tied to a specific data mutation — not "on deploy" or "manually"
- [ ] Serialization format and field naming convention are locked and agreed by all consuming services
- [ ] Consistency model is documented per key (strong, eventual, or probabilistic) with staleness SLA

---

## Edge Cases & Escalation Keywords

Full edge-case catalog — namespace collision (BLOCKED), TTL mismatch with client-side caching (NEEDS_CONTEXT), serialization-format incompatibility (BLOCKED), eviction-policy conflict (NEEDS_INFRA_CHANGE), mixed direct/event-based invalidation (NEEDS_COORDINATION), and stampede under traffic spike (NEEDS_CONTEXT) — each with symptom, mitigation, and escalation keyword in [reference/edge-cases.md](reference/edge-cases.md). Resolve every escalation fork through `AskUserQuestion` per [`skills/_shared/human-input.md`](../_shared/human-input.md).

---

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] Cache key pattern (namespace prefix, delimiter, entity segments) is agreed by all services that read or write the key — no service coined its own pattern
- [ ] TTL policy for every key is explicitly agreed and written into `shared-dev-spec.md` — no key has a "default" or "TBD" TTL
- [ ] Eviction strategy (LRU, volatile-ttl, etc.) and stampede-prevention approach (lock-and-refresh, xfetch, stale fallback) are documented per high-traffic key
- [ ] `contract_cache_status: negotiated` is set in the `shared-dev-spec.md` frontmatter — not `draft` or `open`
- [ ] No open items remain: every key has a single named owner service, a serialization format, an invalidation trigger, and a fallback behavior when cache is unavailable

**Persistence (how the locked contract is recorded):** write the cache contract into `~/forge/brain/prds/<task-id>/shared-dev-spec.md` (cache section) with `contract_cache_status: negotiated`, via `brain-write`/`forge-brain-persist` — then it is locked by `spec-freeze` at the `[P2-SPEC-FROZEN]` handshake (see `council-multi-repo-negotiate`). The status key alone is not the persistence step; the committed brain file is.

## References & Related Skills

- **brain-read:** Look up past cache contracts and domain decisions
- **reasoning-as-infra:** Analyze caching, database, and scaling requirements
- **contract-api-rest:** Define REST contracts that interact with cached data
- **contract-schema-db:** Define database schemas and denormalization for cache warming

## Cross-References

- `council-multi-repo-negotiate`: Drives contract negotiation that produces the cache contract this skill implements.
- `spec-freeze`: Locks all 5 contracts (including cache) after council completes — no changes after `[P2-SPEC-FROZEN]`.
- `forge-council-gate`: Gate that enforces contract completeness before spec-freeze.
- `contract-api-rest`: REST API contract that reads/writes cached data; cache contract and API contract must align on TTL and invalidation.
- `contract-schema-db`: DB schema contract for cache-warming source data; coordinate denormalization.
- `eval-driver-cache-redis`: Executes Redis surface steps in `semantic-automation.csv` — validates contract compliance at eval time.
- `spec-reviewer`: Verifies that implemented cache layer matches the locked cache contract.
- `tech-plan-write-per-project`: References the cache contract when generating per-repo implementation plans.

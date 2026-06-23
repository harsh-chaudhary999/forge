# Conflict Identification, Categorization & Routing Catalog

Depth for Sections 2–4: the cross-surface comparison matrix, the four conflict
categories with examples and severities, the conflict-log and decision-trail
entry templates, and the contract-skill routing table.

## Comparison Matrix (Step 2.1)

Read all 4 reasoning outputs and compare systematically:

| Dimension | Backend | Web | App | Infra | Conflict? |
|-----------|---------|-----|-----|-------|-----------|
| API protocol | REST + gRPC? | REST only? | REST + gRPC? | routing | YES if mismatch |
| Async pattern | Kafka events? | sync wait? | offline queue? | topic topology | YES if mismatch |
| Caching | Redis TTL? | browser cache? | device storage? | eviction policy | YES if mismatch |
| Data model | SQL schema? | normalized state? | local first? | indexing | YES if mismatch |
| Search | ES indexes? | client-side? | no search? | ES refresh | YES if mismatch |

## Conflict Categories (Step 2.2)

For each identified conflict, label it:

1. **Architectural Conflict**: Fundamental disagreement on pattern (e.g., sync vs async)
   - Example: Backend wants async Kafka events, but web expects synchronous API response
   - Severity: HIGH (blocks all surfaces)

2. **Contract Conflict**: Disagreement on shared interface format
   - Example: App says offline cache keys use `user:{id}:profile`, but backend uses `user_{id}_profile`
   - Severity: MEDIUM (fixable with normalization)

3. **Priority/Scope Conflict**: Surface asks for feature others don't support
   - Example: App wants offline-first, but infra says no local storage budget
   - Severity: MEDIUM (requires trade-off)

4. **Non-blocking Mismatch**: Minor differences, surfaces can adapt
   - Example: Web prefers REST pagination via offset/limit, app prefers cursor-based
   - Severity: LOW (either works, pick one)

## Conflict Log Entry Template (Step 2.3)

For each conflict, create an entry:

```markdown
### Conflict: [name]
- **Surfaces affected**: backend, web, app, infra
- **Category**: [Architectural | Contract | Priority | Non-blocking]
- **Description**: [what is the disagreement?]
- **Backend position**: [what does backend reasoning say?]
- **Web position**: [what does web reasoning say?]
- **App position**: [what does app reasoning say?]
- **Infra position**: [what does infra reasoning say?]
- **Severity**: [HIGH | MEDIUM | LOW]
- **Status**: UNRESOLVED (to be resolved in Section 3)
```

## Contract-Skill Routing Table (Step 3.1)

For each HIGH or MEDIUM severity conflict, invoke the relevant contract skill:

| Conflict Type | Contract Skill | Input | Output |
|---------------|----------------|-------|--------|
| API versioning, sync/async API | `/contract-api-rest` | conflict log + surface positions | api-contract.md |
| Event schema, ordering, retention | `/contract-event-bus` | conflict log + surface positions | event-contract.md |
| Cache key patterns, TTL, consistency | `/contract-cache` | conflict log + surface positions | cache-contract.md |
| Schema migration, indexing, constraints | `/contract-schema-db` | conflict log + surface positions | db-contract.md |
| Index mapping, analyzer, refresh | `/contract-search` | conflict log + surface positions | search-contract.md |

## Decision Trail Entry Template (Step 4.3)

For each resolved conflict, update the conflict log:

```markdown
### Conflict: [name]
- **Status**: RESOLVED
- **Resolution**: [what decision was made?]
- **Reasoning**: [why this decision?]
- **Decided by**: [contract-api-rest | contract-event-bus | dreamer | etc.]
- **Surfaces sign-off**: [backend ✅ | web ✅ | app ✅ | infra ✅]
```

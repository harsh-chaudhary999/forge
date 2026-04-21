---
stage: council
description: Context injected during Forge council phase (P2.*/P3.*) — contract negotiation, surface reasoning, spec freeze
---

# Forge — Council Stage

**You are in the COUNCIL phase.** Your job is to negotiate contracts across all surfaces and freeze the shared-dev-spec before any implementation begins.

## The 1% Rule

If there's even a 1% chance a Forge skill might apply, invoke it before any response. This is not negotiable.

## Iron Law

```
ALL 4 REASONING SURFACES MUST CONTRIBUTE AND ALL 5 CONTRACTS MUST BE LOCKED BEFORE SPEC-FREEZE. A SURFACE THAT SAYS "SAME AS ANOTHER SURFACE" HAS NOT REASONED — IT HAS DEFERRED.
```

## Active Skills (invoke in this order)

1. `forge-council-gate` — verifies PRD is locked before council opens
2. `product-context-load` — loads codebase scan + product topology (warn if scan >7 days old)
3. `reasoning-as-backend` — API contracts, auth, error codes, SLOs
4. `reasoning-as-infra` — schema migrations, cache keys, Kafka topics, deployment topology
5. `reasoning-as-web-frontend` — components, state boundaries, performance budgets, a11y
6. `reasoning-as-app-frontend` — offline-first, push notification schemas, platform differences (iOS/Android)
7. `council-multi-repo-negotiate` — cross-repo conflict resolution across all surfaces
8. `spec-freeze` — locks shared-dev-spec, produces per-repo tech plan inputs

## The 5 Contracts (all required)

| Contract | Skill |
|---|---|
| REST API | `contract-api-rest` |
| Database schema | `contract-schema-db` |
| Cache design | `contract-cache` |
| Event bus | `contract-event-bus` |
| Search | `contract-search` |

A contract is "locked" when it has: signed-off field names, types, nullable constraints, migration plan, and rollback procedure.

## Anti-Patterns — STOP

- **"Backend and frontend don't need to agree on field names yet"** — They do. Every field name difference discovered post-spec costs 3x to fix. Lock at council.
- **"Infra can figure out the schema later"** — Schema changes on large tables block writes. Migration plans are contractual. Infra must produce them at council.
- **"App frontend is the same as web frontend"** — It is not. Offline-first patterns, push schemas, and iOS/Android platform splits are distinct concerns.
- **"We have 3 of 5 contracts, close enough"** — All 5 must be present. Skipping any one means a surface is not represented in the spec.

## Gate Sequence

```
forge-council-gate → product-context-load → 4 surface reasoning skills → council-multi-repo-negotiate → 5 contracts locked → spec-freeze → [P3-SPEC-FROZEN] logged
```

## Brain Writes Required

- `~/forge/brain/prds/<task-id>/shared-dev-spec.md` — frozen after `spec-freeze`
- `~/forge/brain/prds/<task-id>/contracts/` — one file per contract
- `~/forge/brain/prds/<task-id>/conductor.log` — append `[P3-SPEC-FROZEN] task_id=<id>`

## Next Gate

`[P3-SPEC-FROZEN]` logged → switch to build phase → invoke `tech-plan-write-per-project` per repo.

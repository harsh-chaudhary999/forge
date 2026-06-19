# Commit Message Patterns

Every write to brain is a git commit. Use these patterns to ensure commits are meaningful, linkable, and auditable.

### Pattern 1: Spec Lock (shared-dev-spec.md)
Template structure:
```
spec: lock shared dev spec for <task-id>

Converged on: [list teams/surfaces]
Contracts locked: [list specs being locked: API v2, DB schema, cache keys]
Assumptions validated: [key assumptions that were verified]
Next: [pointer to next skill: tech-plan-write-per-project]
```

Example:
```
spec: lock shared dev spec for PRD-2025-11-streaming

Converged on: backend, web, app, infra
Contracts locked: gRPC service definitions, PostgreSQL schema v3, Redis cluster config
Assumptions validated: QPS projections (100k RPS sustainable), latency SLA (p99 < 50ms)
Next: Run tech-plan-write-per-project per team
Resolves: D087 (gRPC adoption)
```

**Key sections in commit:**
- What converged (who agreed)
- What's locked (contracts, schemas, configs)
- What assumptions matter
- Next step (unblocks downstream work)

### Pattern 2: Decision Record (decisions/D###.md)
Template structure:
```
decision: record D<id> <title>

Why: [problem statement, what triggered this decision]
What: [the actual decision, in imperative form]
Alternatives: [options considered, why rejected]
Impact: [affected systems, rollback, timeline]
Approval: [who signed off, when]
Next: [pointer to next decision or implementation]
```

Example:
```
decision: record D087 adopt gRPC for service-to-service

Why: REST polling causes 2.5s p95 latency; gRPC reduces to <100ms; scales to 100k RPS
What: All new services (ID ≥ 100) MUST use gRPC; existing services migrate by Dec 31, 2026
Alternatives: WebSocket upgrade (too complex), Kafka (overkill), status quo (unacceptable latency)
Impact: 47 services affected; 6-month parallel run; rollback via service-mesh fallback
Approval: VP Eng (2025-11-16), Principal Architect (2025-11-16), Security (2025-11-18)
Parent: D042 (service mesh)
Children: D088 (gRPC auth), D089 (service discovery), D090 (tracing)
Next: tech-plan-write-per-project to define per-service migration schedule
```

**Key sections in commit:**
- Why (problem, trigger, evidence)
- What (decision, in active voice)
- Alternatives (prevent rework)
- Approval (who signed off)
- Parent/children (decision graph)

### Pattern 3: Contract Negotiation (contracts/api-rest.md)
Template structure:
```
contract: negotiate <contract-type> for <scope>

Participants: [teams involved]
Agreement: [what was agreed]
Versions: [versioning strategy, SLA timeline]
Fallback: [how to handle breaking changes, deprecation plan]
Next: [implementation skill or code review]
```

Example:
```
contract: negotiate REST API v2 contract for public API

Participants: web, mobile-app, partner-integrations, backend
Agreement: Supports streaming subscriptions, pagination with cursor, null coalescing
Versions: v2 supported until 2026-12-31; v1 deprecated 2026-06-30
Fallback: Clients get 410 Gone with Location header to v2 migration docs
Breaking changes: 8 fields renamed for consistency; all documented with examples
Next: api-contract-translate to OpenAPI spec; code-review with partners
Resolves: D025 (API versioning strategy)
```

**Key sections in commit:**
- Participants (who agreed)
- Agreement (what's in the contract)
- Versions (timeline, support window)
- Fallback (how to handle breaks)

### Pattern 4: Retrospective & Learning (learnings/incident-XYZ.md)
Template structure:
```
learning: capture incident-<id> <title>

What happened: [timeline, severity, impact]
Root cause: [why, with evidence/logs]
Action items: [what we'll do differently]
Decisions locked: [decisions made to prevent recurrence]
Affected decisions: [decisions that need review because of this incident]
Next: [follow-up skill or code review]
```

Example:
```
learning: capture incident-2025-11-14 database connection pool exhaustion

What happened: 2025-11-14 14:30-15:45 UTC; 45 minute outage; 99.2% of requests failed
Root cause: New streaming feature didn't release connections; pool hit max=100 by 14:31
Action items: Add connection leak detection to service startup; code review for pool usage
Decisions locked: D091 (connection pool max=500 with warnings at 400); D092 (metrics for conn pool state)
Affected decisions: D087 (gRPC streaming — now with explicit connection management)
Timeline: Incident → diagnosis (15 min) → rollback (20 min) → root cause (4 hours) → fix (3 hours)
Next: Post code review on D091 implementation; add to runbook-database-operations
Resolves: outage ticket INFRA-2847
```

**Key sections in commit:**
- Timeline (when, how long, impact)
- Root cause (with evidence)
- Action items (prevent recurrence)
- Decisions locked (learnings → decisions)
- Affected decisions (what else might break the same way)

### Pattern 5: Migration & Migration Plan (migrations/schema-v2.md)
Template structure:
```
migration: plan <migration-type> to <new-state>

Current state: [what exists now]
Target state: [what we want]
Migration steps: [step by step, reversible]
Rollback procedure: [how to undo at each step]
Timeline: [schedule, milestones, blockers]
Risk: [what can go wrong, mitigations]
Next: [code review, deployment driver invocation]
```

Example:
```
migration: plan schema upgrade from v1 to v2

Current state: users table with email, name, phone as VARCHAR; 2.1M rows
Target state: New columns: email_verified, phone_verified (BOOL); name split into first/last
Migration steps:
  1. Add new columns (NOT NULL false) to users; deploy, soak 24h
  2. Backfill: copy name to first_name (truncate at space); backfill middle/last=NULL
  3. Deploy code: new inserts use first_name, last_name; reads concat for compatibility
  4. Backfill remaining: compute first/last for historical rows via batch job
  5. Remove compatibility layer; make first_name, last_name primary
Rollback: Revert columns; swap code; maintain aliases for 6 months
Timeline: Phase 1 (2025-12-01 to 2025-12-07); Phase 2 (2025-12-08 to 2025-12-14)
Risk: Backfill timeout if batch is too large; mitigation: max 10k rows per iteration, 30s sleep
Next: Contract schema with backend; code-review schema changes; run eval-driver-db-mysql
Resolves: D088 (unified name format)
```

**Key sections in commit:**
- Current and target state (scope)
- Step-by-step with reversibility (can roll back at any step)
- Rollback procedure (explicit)
- Timeline and risk (know the plan)

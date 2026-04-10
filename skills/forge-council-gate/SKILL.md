---
name: forge-council-gate
description: HARD-GATE: Every locked PRD goes through Council (4 surfaces + 5 contracts negotiated). No skipping.
type: rigid
---
# Council Gate (HARD-GATE)

**Rule:** Every locked PRD must be negotiated by Council.

## Anti-Pattern Preamble: Why Agents Skip Council

| Rationalization | The Truth |
|---|---|
| "This is a backend-only change, we don't need all 4 surfaces" | Backend changes affect caching, APIs, schemas, infra. All 4 surfaces always matter. |
| "We already have API contracts, council will just rubber-stamp them" | Council doesn't rubber-stamp. It negotiates: backend may need different schema, web may need different API shape. |
| "Single-surface reasoning is sufficient, council is overkill" | Single-surface reasoning is local optimization. Council finds conflicts (trade-offs) that single-surface misses. |
| "The contracts are straightforward, we can skip negotiation" | Straightforward to whom? Backend finds performance issues that web didn't see. Web finds usability issues backend didn't anticipate. |
| "Council takes too long, we're on a deadline" | A day in council prevents a month of integration rework. Council schedule is non-negotiable. |
| "The previous spec passed council, this is just a patch" | Every PRD gets fresh council. Patches can break prior assumptions. Re-negotiate or escalate. |
| "We can do council discussions async, no need to synchronize" | Async discussion misses real-time insight. Surfaces need to hear each other. Council is synchronous or it's not council. |
| "Just one surface can't attend council this sprint, we'll get them next time" | All 4 surfaces must be present. Missing surface = missing veto. No exceptions. |
| "The contracts are defined by the previous system, we can't change them" | Every contract is renegotiable. If the new PRD requires a different contract, negotiate it. Don't lock to old contracts. |
| "We already negotiated with stakeholders, council is redundant" | Stakeholder agreement != technical consensus. Council surfaces conflicts in tech that stakeholder agreement misses. |

## Detailed Workflow

### Gather Inputs (Pre-Council)
- **Input:** Locked PRD (from intake-gate)
- **Action:** Prepare council materials
  - Summarize PRD in 1 page (problem, surfaces, acceptance criteria)
  - List known constraints (performance, compliance, backwards-compat)
  - Enumerate existing contracts (API, events, cache, DB, search)
  - Identify potential conflicts (what we know will be hard to reconcile)
- **Output:** Council agenda + materials

### Invoke Council Multi-Repo Negotiate Skill
**ALWAYS invoke `/council-multi-repo-negotiate` — do not run individual surface reasonings.**

The skill will:
1. Spawn 4 surface reasoners (backend, web, app, infra) in parallel
2. Each surface reviews the PRD and proposes:
   - Implementation approach
   - Contract requirements (API shape, event schema, cache keys, DB schema, search index)
   - Performance & cost impact
   - Risk & unknowns
3. Identify conflicts (where surfaces disagree on contracts)

### Negotiate Conflicts
- **Input:** Surface proposals (from skill output)
- **For each conflict:**
  - Identify the root disagreement (not just different proposals)
  - Understand trade-off space (speed vs. storage, availability vs. consistency, etc.)
  - Reach consensus or escalate

- **Consensus paths:**
  - Backend & web agree on API shape, infra provides infrastructure
  - App & web agree on cache strategy, backend provides data
  - All surfaces agree on DB schema (most crucial)
  - All surfaces agree on event topics/schemas

- **Escalation triggers (invoke dreamer):**
  - Backend proposes monolithic DB schema, web proposes multiple tables (schema conflict)
  - API performance requirement contradicts cache strategy (trade-off)
  - Compliance requirement conflicts with performance goal (policy vs. spec)
  - Budget constraint requires different infra than tech plan (resource allocation)

### Lock Shared-Dev-Spec
- **Input:** Negotiated contracts + surface agreements
- **Action:** Create shared-dev-spec document (in brain, decision ID: SPECLOCK-YYYY-MM-DD-HH)
  - Lock all 5 contracts with exact specifications
  - Record each surface's scope (what they will implement)
  - Document resolved conflicts (and reasoning behind resolution)
  - Record escalations (if any) and dreamer decisions
- **Output:** SPEC LOCKED (ready for per-project tech plans)

### Validate Completeness
- **Check:**
  - All 4 surfaces attended and proposed
  - All 5 contracts negotiated (no "TBD")
  - No unresolved conflicts (all either consensus or escalated)
  - Each surface agrees to their scope
  - Surfaces agree to contract specifications
- **If incomplete:** Return to Phase 3 (continue negotiation or escalate)

### Edge Cases & Fallback Paths

#### Case 1: Surfaces Reach Deadlock (Cannot Agree)
- **Symptom:** Backend insists on schema X, web insists on schema Y, neither will compromise
- **Do NOT:** Pick one and override the other
- **Action:**
  1. Document the disagreement in detail (both proposals, both rationales)
  2. Escalate to dreamer (architecture decision, not engineering compromise)
  3. Dreamer decides (or requests third option)
  4. Return to council with dreamer decision
  5. Lock spec with dreamer arbitration recorded

#### Case 2: New Surface-Level Concern Emerges During Council
- **Symptom:** "Wait, this API change requires a DB migration, which takes 4 hours"
- **Do NOT:** Accept the concern and move on; address it then and there
- **Action:**
  1. Immediately revisit the contract
  2. Surfaces propose revised contract (faster migration, phased rollout, etc.)
  3. Re-negotiate until all surfaces agree
  4. Lock revised contract

#### Case 3: One Surface Cannot Attend Council (Unavailable)
- **Symptom:** Infra engineer is busy, we'll do council without them
- **Do NOT:** Proceed without all 4 surfaces present
- **Action:**
  1. Reschedule council (don't skip a surface)
  2. If surface remains unavailable: escalate as BLOCKED
  3. Dreamer decides: do we proceed with contingency or wait?

#### Case 4: Contract Negotiation Reveals PRD Is Infeasible
- **Symptom:** "The performance requirement requires infrastructure that costs $50k/month, but PRD budget is $10k"
- **Do NOT:** Lock a spec you can't afford
- **Action:**
  1. Flag the infeasibility in brain (SPECLOCK decision, with cost/perf trade-off)
  2. Escalate to dreamer (requirement vs. resource conflict)
  3. Dreamer decides: change requirement, increase budget, or kill feature
  4. If requirement changes: restart council with new PRD
  5. If dreamer approves higher budget: continue council
  6. If feature killed: record decision and close PRD

#### Case 5: Council Reveals Hidden Dependency (Feature X blocks Feature Y)
- **Symptom:** "We can't implement this auth feature until we ship Feature Y first"
- **Do NOT:** Ignore the dependency, lock spec anyway
- **Action:**
  1. Document the dependency in brain (with reason)
  2. Determine: is Feature Y in scope? In progress? Shipped?
  3. If Y not shipped: escalate to dreamer (sequencing, scope, budget)
  4. If Y in progress: coordinate with Y's team
  5. If Y shipped: proceed with council (dependency satisfied)

### Council Checklist

Before locking spec, verify:

- [ ] Locked PRD provided (from intake-gate)
- [ ] Council materials prepared (agenda, 1-pager, constraints)
- [ ] `/council-multi-repo-negotiate` skill invoked
- [ ] All 4 surfaces attended (backend, web, app, infra)
- [ ] All 4 surfaces proposed implementation approach
- [ ] All 5 contracts negotiated:
  - [ ] API (shape, versioning, error codes)
  - [ ] Events (topics, schemas, retention)
  - [ ] Cache (keys, TTL, invalidation)
  - [ ] Database (schema, migrations, indexing)
  - [ ] Search (index structure, query syntax)
- [ ] All conflicts resolved (or escalated to dreamer with decision)
- [ ] Each surface agrees to their scope
- [ ] Each surface agrees to contract specifications
- [ ] No "TBD" in contracts (all details locked)
- [ ] Shared-dev-spec created in brain (SPECLOCK decision ID)
- [ ] Per-project tech plan inputs ready (surface scope + contracts)

Output: **SPEC LOCKED** (ready for per-project tech planning) or **BLOCKED** (deadlock, resource infeasibility, unresolved conflict awaiting dreamer)

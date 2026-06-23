# Edge Cases & Fallback Paths

Eight diagnosis/response/escalation cards for council negotiation. Each names a
failure mode, how to detect it, the response strategy, and the escalation route
(NEEDS_CONTEXT / BLOCKED / dreamer).

### Edge Case 1: Two services have incompatible technical requirements (API versioning conflict)

**Diagnosis**: Service A (backend) requires RESTful API v2 with breaking changes. Service B (web frontend) cannot handle v2 breaking changes without major refactor. Both requirements are valid but incompatible.

**Response**:
- **Identify incompatibility**: Reasoning surfaces have flagged this. Contract-api-rest shows: "v2 has breaking change X. Service B depends on old behavior of X."
- **Negotiation options**:
  1. **Gradual migration**: Support both v1 and v2 simultaneously. Service B uses v1, migrate later.
  2. **Unified change**: Break both services in coordinated way. Refactor Service B at same time as v2 deployment.
  3. **Refactor third option**: Design v2 to be backward-compatible with v1 (possible but may compromise design).
- **Decision path**: Use dreamer to analyze trade-offs. Lock decision in spec.
- **Track**: Document in `shared-dev-spec.md` why this trade-off was chosen.

**Escalation**: If dreamer cannot resolve (both options have equal trade-offs), escalate to NEEDS_CONTEXT - Stakeholder must choose which service's priority wins.

---

### Edge Case 2: Spec is changing during council negotiation (PRD updated mid-discussion)

**Diagnosis**: While council is negotiating contracts, someone updates the PRD with new requirements that invalidate prior reasoning outputs.

**Response**:
- **Detect**: Reasoning outputs are timestamped. If PRD timestamp is newer than reasoning outputs, spec has changed.
- **Recovery**:
  1. Pause council negotiation.
  2. Ask: "PRD updated at [time]. Prior reasoning was at [earlier time]. Should we re-run reasoning with new PRD?"
  3. If yes: Invoke reasoning skills again with new PRD.
  4. If no: Document what changed and why it doesn't affect negotiated contracts.
- **Re-negotiate**: If new requirements affect contracts, re-run affected contract skills.

**Escalation**: If PRD changes fundamentally (e.g., adds new service dependency), escalate to user: "PRD changes mid-negotiation. Recommend: lock PRD before council, or restart council negotiation."

---

### Edge Case 3: Council produces no conflicts (all surfaces agree perfectly)

**Diagnosis**: After running all 4 reasoning surfaces, outputs are identical or fully compatible. No negotiation needed.

**Response**:
- **This is valid**: Sometimes consensus happens. Not a failure.
- **Still run contracts**: Even though no conflicts exist, run contract skills to formalize agreements (they may catch constraints that reasoning didn't).
- **Consolidate spec**: Still produce `shared-dev-spec.md` with all reasoning outputs included (for traceability).
- **Escalate**: Not needed. Mark as "NO_CONFLICTS_DETECTED" in logs and proceed to tech-planning.

**Escalation**: None. Fast path to tech-planning.

---

### Edge Case 4: New surface reasoning changes contract (e.g., infra team discovers scaling constraint)

**Diagnosis**: Reasoning is complete and contracts are negotiated. Then infra reasoning comes back with a new constraint: "Database cannot scale to projected load with current schema." This violates the DB contract that was just negotiated.

**Response**:
- **Retroactive constraint**: This is valid. New information should trigger re-negotiation.
- **Strategy 1 (Re-negotiate)**: Re-run contract-schema-db with new constraint included. Update contract.
- **Strategy 2 (Find workaround)**: Ask: "Can we work around the scaling constraint? (E.g., sharding, caching, different technology)"
- **Track decision**: Document in spec why contract was or was not changed.
- **Update timestamp**: If contract is re-negotiated, update lock timestamp. Spec must be re-locked.

**Escalation**: Escalate to user: "New constraint discovered mid-negotiation. Requires contract re-negotiation. Proceed with updated contract or pause for deeper architectural review?"

---

### Edge Case 5: Council cannot converge; reasoning surfaces produce incompatible recommendations

**Diagnosis**: Backend reasoning says "microservices architecture". Infra reasoning says "monolith for simplicity at current scale". Web frontend says "we need both, it's feasible with strangler pattern".

**Response**:
- **Document incompatibility**: Log all three positions with evidence.
- **Escalate to dreamer**: "Three architectural positions, no consensus. Request: counterfactual analysis + recommendation."
- **Dreamer output**: Either clear winner or "decision depends on priority [cost vs. time vs. scalability]. Choose priority, then decision follows."
- **Proceed with dreamer recommendation**: Lock that decision in spec.
- **Alternative**: If dreamer also can't resolve, escalate to NEEDS_CONTEXT - Stakeholder must set priorities.

**Escalation**: NEEDS_CONTEXT - Requires human stakeholder to break the tie or define priority criteria.

---

### Edge Case 6: Contract negotiation reveals missing service (service not listed in PRD)

**Diagnosis**: During contract negotiation, reasoning surfaces identify that a new service is needed (e.g., "We need a cache-invalidation service"). But this service wasn't in the original PRD.

**Response**:
- **Scope creep detection**: This is a scope expansion signal.
- **Options**:
  1. **Add to scope**: Include new service in PRD and re-plan.
  2. **Defer**: Mark as future work ("v2 feature"). Use a simpler workaround for v1.
  3. **Rethink design**: Maybe new service can be avoided by redesigning existing ones.
- **Decision**: Escalate to user: "New service discovered during negotiation. Should we add to scope, defer, or redesign to avoid?"

**Escalation**: NEEDS_CONTEXT - Scope decision required before proceeding.

---

### Edge Case 7: Spec completeness check fails; dependencies are circular

**Diagnosis**: During spec validation, a circular dependency is found: Service A depends on Contract X, which requires Service B, which depends on Contract Y that requires Service A.

**Response**:
- **Detect**: Spec validator should catch this. Flag as critical.
- **Resolve circular dependency**:
  1. Break the circle by deferring one dependency (Service A will depend on Contract X v1.0, will upgrade to v2.0 after Service B ships).
  2. Or redesign to eliminate one dependency entirely.
  3. Or introduce an intermediate service to break the cycle.
- **Document decision**: Spec must explicitly note why the circle was broken and when/if it will be re-evaluated.

**Escalation**: Escalate to user if no clear way to break the circle. May indicate fundamental design issue.

---

### Edge Case 8: Brain-write fails; spec cannot be locked (e.g., git conflict in brain repo)

**Diagnosis**: At the end of council, trying to write `shared-dev-spec.md` to brain fails because of a git conflict or permissions issue.

**Response**:
- **Root cause**: Usually means brain repo is not up-to-date or another process wrote to same file.
- **Recovery**:
  1. Pull latest brain state.
  2. Merge conflicts manually (spec + other concurrent write).
  3. Retry brain-write.
- **If unresolvable**: Escalate to user: "Brain write failed. Manual intervention needed. Spec is not locked until this is resolved."

**Escalation**: BLOCKED - Requires user to resolve brain state before proceeding.

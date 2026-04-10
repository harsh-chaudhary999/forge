---
name: dream-resolve-inline
description: "WHEN: eval reveals cross-service conflict — two services disagree on contract, data format, or behavior. Dreamer analyzes both sides and proposes resolution."
type: rigid
requires: [brain-read, brain-write]
---

# Dream Resolve Inline

## Anti-Pattern Preamble

Before resolving any cross-service conflict, reject these rationalizations:

1. **"Just pick the newer service's version."** Recency is not correctness. The older service may hold the canonical contract that downstream consumers depend on. Choosing based on timestamp skips root-cause analysis and buries the real disagreement.

2. **"Force both sides to match and move on."** Forcing alignment without understanding why they diverged creates a shallow fix. The divergence happened for a reason — a missed spec update, a unilateral schema change, a misread contract. Papering over it guarantees recurrence.

3. **"The service with more tests is probably right."** Test coverage measures thoroughness, not correctness. A service can have 100% coverage against the wrong spec. Always validate against the locked contract, not against test count.

4. **"We'll fix it in the next sprint."** Deferring conflict resolution means shipping a broken contract to production. Conflicts compound — by next sprint, a third service will have built on the broken assumption. Resolve now or pay triple later.

5. **"It's close enough — the difference is cosmetic."** A field named `user_id` (integer) vs `userId` (string) is not cosmetic. Serialization, validation, indexing, and caching all diverge on naming and type. "Close enough" is the root cause of silent data corruption.

6. **"Let the downstream consumer handle the mismatch."** Pushing resolution to the consumer scatters the fix across every client. The contract owner must resolve at the source. One fix at the origin beats forty patches at the edges.

---

## Purpose

When eval runs detect that two or more services disagree on a shared contract — field names, data types, response shapes, event payloads, error codes, or behavioral semantics — this skill provides a structured framework for the dreamer agent to analyze, reason about, and resolve the conflict inline during the self-heal cycle.

---

## Conflict Analysis Framework

### Step 1: Identify the Conflict Boundary

Determine the exact surface where disagreement occurs:

```
Conflict boundary types:
  - CONTRACT: Field name, type, or shape mismatch in API contract
  - PAYLOAD: Event bus message schema disagreement
  - BEHAVIOR: Same input, different output between services
  - TIMING: Services expect different ordering or sequencing
  - STATE: Services hold contradictory views of shared state
  - VERSION: Services target different contract versions
```

For each conflict, extract:
- **Service A**: Name, version, the value/behavior it asserts
- **Service B**: Name, version, the value/behavior it asserts
- **Contract reference**: The locked spec both should conform to (brain path)
- **Divergence point**: The specific field, endpoint, event, or behavior that differs
- **Discovery method**: Which eval step surfaced the conflict

### Step 2: Establish Ground Truth

Query the brain for the authoritative contract:

```
brain-read: contracts/{contract-type}/{contract-name}.md
brain-read: prds/{task-id}/shared-dev-spec.md
brain-read: decisions/{relevant-decision-id}.md
```

Compare each service's implementation against the locked contract:
- If one service matches the contract and the other does not, the non-conforming service is at fault.
- If neither matches, the contract itself may be ambiguous or outdated.
- If both match different versions, a version reconciliation is needed.

### Step 3: Gather Evidence

Collect from each conflicting service:

| Evidence Type | Source | Purpose |
|---|---|---|
| Eval output | eval-result.json | What failed and how |
| Service logs | service stdout/stderr | Internal errors or warnings |
| Request/response | eval driver captures | Actual vs expected payloads |
| Contract snapshot | brain/ | What was agreed |
| Commit history | git log of service | When divergence was introduced |
| Decision record | brain/decisions/ | Why the contract was shaped this way |

### Step 4: Counterfactual Reasoning

Before choosing a resolution, run counterfactual analysis:

**"What would have happened if we chose differently?"**

For each resolution candidate, trace forward:
1. If we revert Service A to match Service B, what downstream consumers break?
2. If we adapt Service B to match Service A, what upstream producers break?
3. If we version the contract, how many services need to support both versions and for how long?
4. If we mediate (new shared format), what is the migration cost across all services?

Document each counterfactual with:
- **Assumption**: What we assume about the downstream impact
- **Evidence**: What data supports or contradicts the assumption
- **Risk**: What could go wrong if the assumption is wrong
- **Blast radius**: How many services, endpoints, or data flows are affected

---

## Resolution Strategies

### Strategy 1: REVERT

**When to use:** One service clearly deviated from the locked contract. The other service and all downstream consumers conform to the original spec.

**Procedure:**
1. Identify the non-conforming service
2. Locate the commit that introduced the divergence
3. Revert the divergent implementation to match the locked contract
4. Re-run eval to confirm resolution
5. Write brain record explaining why revert was chosen

**Risk:** Low if divergence was recent and no consumers adapted to the broken version.

### Strategy 2: ADAPT

**When to use:** One service has a legitimate improvement that should propagate. The locked contract was underspecified or the improvement is clearly correct (e.g., fixing a type from string to integer for an ID field).

**Procedure:**
1. Validate the improvement against product requirements
2. Update the locked contract in brain (brain-write)
3. Propagate the change to all affected services
4. Update all downstream consumers
5. Re-run eval across full service chain
6. Write brain record documenting the contract evolution

**Risk:** Medium. Propagation may miss consumers. Requires full eval pass.

### Strategy 3: VERSION

**When to use:** Both implementations are valid for different use cases. A breaking change is needed but cannot be applied atomically across all services.

**Procedure:**
1. Create a new contract version (v1 -> v2)
2. Service A continues on v1; Service B targets v2
3. Define a graduated migration timeline (see contract-api-rest deprecation rules)
4. Implement version negotiation (Accept headers, URL versioning)
5. Set sunset date for old version
6. Write brain record with version timeline and migration plan

**Risk:** High complexity. Two versions must coexist. Testing surface doubles.

### Strategy 4: MEDIATE

**When to use:** Both services have valid but incompatible approaches. Neither is strictly wrong. A new shared format resolves the disagreement better than either original.

**Procedure:**
1. Analyze both approaches for strengths and weaknesses
2. Design a new shared format that preserves the intent of both
3. Get sign-off from both service owners (council negotiation if needed)
4. Update the locked contract to the mediated version
5. Implement in both services simultaneously
6. Re-run eval across all affected services
7. Write brain record documenting the mediation rationale

**Risk:** Highest. New format introduces new assumptions. Requires thorough eval.

---

## Edge Cases

### Edge Case 1: Both Services Are Correct (Spec Ambiguity)

**Scenario:** The locked contract says `timestamp` without specifying format. Service A sends ISO-8601 (`2026-04-10T14:30:00Z`), Service B sends Unix epoch (`1744292400`).

**Resolution:** This is a spec defect, not a service defect. Do NOT blame either service.
1. Identify the ambiguity in the locked contract
2. Choose the format that aligns with existing consumers (check brain for precedent)
3. Update the contract with explicit format specification
4. Apply ADAPT strategy to the non-chosen service
5. Add a brain decision record: "Resolved spec ambiguity: timestamps are ISO-8601"
6. Flag the spec-writing process for improvement (pattern candidate)

### Edge Case 2: One Service Already Deployed to Production

**Scenario:** Service A is live in production serving real traffic. Service B is in staging and contradicts Service A's contract.

**Resolution:** Production always wins in the short term.
1. Service B must conform to the production contract immediately
2. If Service B's approach is actually better, schedule a versioned migration
3. Never break production to match staging — the blast radius is unacceptable
4. Write brain record: "Production constraint forced REVERT on Service B; VERSION migration planned for {date}"

### Edge Case 3: Resolution Breaks a Third Service

**Scenario:** Resolving the conflict between Service A and B causes Service C to fail because Service C depends on the broken behavior.

**Resolution:** Expand the conflict scope.
1. Add Service C to the conflict analysis
2. Re-run counterfactual reasoning with three services
3. Prefer the resolution that minimizes total change across all three
4. If no single strategy works, use MEDIATE with input from all three service owners
5. Write brain record documenting the cascading conflict and multi-service resolution

### Edge Case 4: Performance vs Correctness Tradeoff

**Scenario:** Service A sends paginated results (correct per contract, slower). Service B sends full results in a single response (violates contract, but 10x faster).

**Resolution:** Correctness wins. Performance is optimized within the correct contract.
1. Service B must conform to the paginated contract
2. If pagination causes unacceptable latency, open a contract amendment (not a violation)
3. Investigate performance optimizations within the paginated approach (cursor-based pagination, pre-fetching, caching)
4. Write brain record: "Performance concern logged; contract compliance enforced; optimization ticket created"

### Edge Case 5: Data Migration Needed

**Scenario:** Service A stores `name` as a single string. Service B expects `first_name` and `last_name` (per updated contract). Existing data in Service A cannot be split without heuristics.

**Resolution:** Data migration is required but must not block the conflict resolution.
1. Resolve the contract conflict first (ADAPT to the split-name format)
2. Service A adds new fields (`first_name`, `last_name`) alongside the legacy `name` field
3. Implement a backfill migration with explicit heuristics (split on first space, flag ambiguous names for manual review)
4. Set a deprecation date for the legacy `name` field
5. Write brain record documenting: migration plan, heuristic rules, manual review queue, deprecation timeline

### Edge Case 6: Circular Dependency in Resolution

**Scenario:** Resolving A's conflict with B requires updating C, but C depends on A's current format. Updating A breaks C, updating C requires the new A.

**Resolution:** Break the cycle with a compatibility shim.
1. Introduce a temporary adapter/shim that translates between old and new formats
2. Update services in order: A (new format + shim for C), then C (consume new format), then remove shim
3. Each step must pass eval independently
4. Write brain record documenting the shim, its purpose, and its removal date

---

## Resolution Output Format

Every resolution MUST produce a structured output written to the brain:

```yaml
conflict_resolution:
  id: "CR-{task-id}-{sequence}"
  timestamp: "2026-04-10T14:30:00Z"
  
  conflict:
    type: "CONTRACT | PAYLOAD | BEHAVIOR | TIMING | STATE | VERSION"
    service_a:
      name: "<service-name>"
      version: "<version>"
      assertion: "<what service A claims/does>"
    service_b:
      name: "<service-name>"
      version: "<version>"
      assertion: "<what service B claims/does>"
    divergence_point: "<specific field, endpoint, event>"
    contract_reference: "brain/contracts/{path}"
    discovered_by: "<eval scenario and step>"

  analysis:
    ground_truth: "<what the locked contract says>"
    conforming_service: "<A | B | neither | both-different-versions>"
    root_cause: "<why divergence occurred>"
    counterfactuals:
      - strategy: "REVERT"
        impact: "<what happens>"
        blast_radius: <number-of-affected-services>
        risk: "low | medium | high"
      - strategy: "ADAPT"
        impact: "<what happens>"
        blast_radius: <number-of-affected-services>
        risk: "low | medium | high"

  resolution:
    chosen_strategy: "REVERT | ADAPT | VERSION | MEDIATE"
    justification: "<why this strategy was chosen over alternatives>"
    evidence:
      - type: "<contract | eval-output | commit-history | decision-record>"
        reference: "<path or identifier>"
        finding: "<what it shows>"
    changes_required:
      - service: "<service-name>"
        change: "<description of required change>"
        files: ["<file-path>"]
    affected_services: ["<service-1>", "<service-2>"]
    migration_needed: true | false
    migration_plan: "<if needed, reference to migration record>"

  brain_record:
    decision_id: "D{id}"
    path: "brain/decisions/D{id}.md"
    commit_message: "decision: resolve cross-service conflict CR-{id} via {strategy}"
    tags: ["#conflict-resolution", "#contract", "#self-heal"]
    related_decisions: ["<parent-decision>", "<contract-decision>"]
```

---

## Workflow Integration

### Trigger
This skill is invoked by the dreamer agent during the self-heal cycle when:
- `self-heal-locate-fault` identifies a cross-service contract mismatch
- `self-heal-triage` classifies the failure as a contract disagreement (not a bug, flaky test, or environment issue)

### Sequence
```
self-heal-locate-fault  (identifies which services conflict)
       |
self-heal-triage        (classifies as contract conflict)
       |
dream-resolve-inline    (THIS SKILL — analyzes and resolves)
       |
brain-write             (records resolution decision)
       |
eval re-run             (verifies resolution)
```

### Cross-References
- **self-heal-locate-fault**: Provides the fault diagnosis that triggers this skill
- **self-heal-triage**: Classifies the failure type; only CONTRACT/PAYLOAD/BEHAVIOR types route here
- **contract-api-rest**: Defines the contract negotiation rules this skill enforces
- **brain-read**: Retrieves the locked contracts and decision history
- **brain-write**: Records the resolution decision and rationale

---

## HARD-GATE Checklist

Before marking a conflict as resolved, ALL of the following must be true:

- [ ] Ground truth established (locked contract retrieved from brain)
- [ ] Both services' implementations compared against ground truth
- [ ] Evidence collected from eval output, logs, and commit history
- [ ] Counterfactual reasoning completed for at least two strategies
- [ ] Chosen strategy has documented justification
- [ ] All affected services identified (not just the two in conflict)
- [ ] Resolution output written in the structured format above
- [ ] Brain record committed with full provenance
- [ ] Eval re-run passes for all affected services

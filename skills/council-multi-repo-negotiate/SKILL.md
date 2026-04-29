---
name: council-multi-repo-negotiate
description: "WHEN: A locked PRD needs to be negotiated across all surfaces before implementation begins. Invokes all 4 surface reasoning skills, all 5 contract skills, resolves conflicts, outputs locked shared-dev-spec.md."
type: rigid
requires: [brain-read, reasoning-as-backend, reasoning-as-web-frontend, reasoning-as-app-frontend, reasoning-as-infra, contract-api-rest, contract-event-bus, contract-cache, contract-schema-db, contract-search]
version: 1.0.0
preamble-tier: 3
triggers:
  - "negotiate across repos"
  - "multi-repo council"
  - "cross-repo spec alignment"
allowed-tools:
  - Bash
  - Write
  - AskUserQuestion
---

# Council Multi-Repo Negotiate

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "Only 2 surfaces are affected, skip the other 2" | Surfaces you skip are surfaces that discover conflicts during build instead of council. All 4 must reason, even if their contribution is "no impact." |
| "The contracts are obvious from the PRD" | PRDs describe features, not interfaces. Contracts emerge from negotiation — they cannot be inferred unilaterally. |
| "We'll resolve conflicts during build" | Build-time conflict resolution means rework, re-testing, and re-eval. Council-time resolution costs minutes, not hours. |
| "Backend can decide the API shape alone" | Every surface consumes or produces data. Unilateral API design creates contracts the frontend can't fulfill. |
| "This is a single-repo change, council is overkill" | Single-repo changes still affect contracts (cache keys, event schemas, DB migrations). Council validates cross-service impact even for single-repo PRDs. |
| "I'll lock the spec now and amend it later if needed" | Amendments after spec-freeze require full re-negotiation. Get it right in council or pay the re-negotiation cost. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
NO IMPLEMENTATION STARTS BEFORE ALL 4 SURFACES HAVE REASONED AND ALL 5 CONTRACTS ARE LOCKED. A PARTIAL COUNCIL IS NOT A COUNCIL.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Fewer than 4 surfaces produced reasoning outputs** — A skipped surface is a surface that will surface conflicts during build. STOP. All 4 surfaces must produce reasoning, even if "no impact."
- **Fewer than 5 contracts are negotiated** — Any unagreed contract becomes an integration failure during build. STOP. All 5 contracts (REST, events, cache, DB, search) must be explicitly negotiated.
- **Shared-dev-spec contains "TBD" in any field** — Unresolved TBDs become undiscovered bugs. STOP. Resolve every TBD before spec-freeze is called.
- **Conflict between two surfaces is "deferred to implementation"** — Build-time conflict resolution costs 10x more than council-time resolution. STOP. Invoke dreamer to resolve the conflict now.
- **Spec is frozen before all surface reasoning files are written to brain** — Provenance is lost. STOP. Write all surface outputs to brain before calling spec-freeze.
- **Council is invoked before PRD is locked** — Unlocked PRD means the scope can change mid-council. STOP. Confirm PRD lock (brain decision ID) before invoking any surface reasoning.
- **Web or app is in scope but intake design fields never reach `shared-dev-spec.md`** — Subagents and parallel surface skills only see what is written down. If `design_new_work` / `design_assets` from `prd-locked.md` are not copied into the spec, autonomous reasoning invents UI from prose alone. STOP. Paste the intake **Design / UI** block verbatim under `## Design source (from intake)` before surface work is treated as complete.
- **`design_new_work: yes` but `shared-dev-spec.md` lacks implementable design** — Missing **`design_brain_paths`** and missing **`lovable_github_repo`** (+ pinned ref) and missing **`figma_file_key` + `figma_root_node_ids`**, with no **`design_waiver: prd_only`**, means council cannot lock pixels. STOP. Re-open intake or add materialized `design/` artifacts before treating negotiation as complete.
- **Only 1-2 surfaces are "affected" so the rest are skipped** — Surfaces that appear unaffected often discover hidden dependencies. STOP. All surfaces must reason, even if briefly.
- **External parity gate skipped** — No `~/forge/brain/prds/<task-id>/parity/external-plan.md`, no completed `parity/checklist.md` (from **`docs/parity-checklist-template.md`**), and no `parity/waiver.md` with `parity_waiver: true` before **`spec-freeze`**. STOP. Materialize parity or record waiver (see **`spec-freeze`** Step 0).
- **PRD implies gated / variant UI or post-condition behaviour (e.g. after deadline), web in scope, but spec lacks a locked surface matrix** — No enum / flag / route allow-list describing which UI exists in which state. STOP. Add contract text or **`WAIVER: …`** + owner + ticket until intake supplies it.
- **PRD names a third-party verifier / identity or document provider, but spec lacks retention + secret handling** — No rows for token lifetime, hash vs raw storage, encryption boundary, audit. STOP. Lock in **`shared-dev-spec`** or **`contract-*`** or **`WAIVER`** — not silence.
- **PRD puts message broker on critical path, but spec lacks choreography** — Unclear what advances the next stage (sync HTTP vs which consumer), idempotency, DLQ. STOP. Lock in **`contract-event-bus`** or **`WAIVER`** — not silence.
- **Product cohorts / segmentation without a locked matrix** — PRD implies segment-specific behavior but brain lacks **`touchpoints/COHORT-AND-ADJACENCY.md`** (see **`docs/adjacency-and-cohorts.md`** + template **`docs/templates/adjacency-cohort-and-signals.template.md`** Section A) with **USER/PO-backed** rows or **waivers**. STOP. No **`SPEC_INFERENCE`**-only cohort policy at council close.
- **Trust / persistence claims without signal anchors** — PRD lines assert stored truth but there is no **`touchpoints/PRD-SIGNAL-REGISTRY.md`** (same doc + template Section B) mapping to **table.column**, **topic+schema**, **cache key**, or **eval fixture**. STOP. Add rows or **`WAIVER`**.

Master orchestration skill that brings together all 4 surface reasoning skills and all 5 contract skills to negotiate conflicts and lock the shared-dev-spec.

## Section 1: Load PRD & Surfaces

### Step 1.1: Read Locked PRD
Use `/brain-read` to load the locked PRD from intake:
```
/brain-read [product-id] [task-id]
```

Verify the PRD is locked (status = LOCKED). Extract:
- Scope: what are we building?
- Success criteria: what must work?
- Affected repos: which codebases change?
- Interfaces: what contracts matter (API, events, cache, DB, search)?
- **Design / UI (from intake `prd-locked.md`):** `design_new_work`, `design_assets`, optional `design_waiver`, or `design_ui_scope: not applicable`. When web or app repos are in scope, these fields **must exist** (per `intake-interrogate` Q9). **Pass the full locked PRD text (including the Design / UI section) into every surface reasoning invocation** so agents do not rely on chat memory alone.
- **Cohort & adjacency (before surface work completes):** Follow **`docs/adjacency-and-cohorts.md`** — read **`discovery-adjacency.md`** if present; **`touchpoints/COHORT-AND-ADJACENCY.md`** must be **drafted or waived** before council is treated as done when the PRD segments users or data.

### Step 1.2: Invoke All 4 Surface Reasoning Skills in Parallel
Invoke these skills in parallel (no dependencies between them):

```
/reasoning-as-backend [locked-prd]
/reasoning-as-web-frontend [locked-prd]
/reasoning-as-app-frontend [locked-prd]
/reasoning-as-infra [locked-prd]
```

**What each reasoning skill returns:**

- **backend.md**: REST/gRPC endpoints, data models, service boundaries, async patterns, performance SLOs
- **web.md**: React/Next.js components, state management, API client contracts, performance budgets, accessibility
- **app.md**: React Native/Kotlin/Swift UI, offline-first patterns, native constraints, push notifications, device storage
- **infra.md**: MySQL schema, Redis caching strategy, Kafka topics, Elasticsearch indexes, monitoring, scaling

Store outputs in: `/home/lordvoldemort/Videos/forge/brain/prds/[task-id]/reasoning/`

---

## Section 2: Identify Conflicts

### Step 2.1: Compare Across Surfaces

Read all 4 reasoning outputs and compare systematically:

#### Comparison Matrix

| Dimension | Backend | Web | App | Infra | Conflict? |
|-----------|---------|-----|-----|-------|-----------|
| API protocol | REST + gRPC? | REST only? | REST + gRPC? | routing | YES if mismatch |
| Async pattern | Kafka events? | sync wait? | offline queue? | topic topology | YES if mismatch |
| Caching | Redis TTL? | browser cache? | device storage? | eviction policy | YES if mismatch |
| Data model | SQL schema? | normalized state? | local first? | indexing | YES if mismatch |
| Search | ES indexes? | client-side? | no search? | ES refresh | YES if mismatch |

### Step 2.2: Categorize Conflicts

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

### Step 2.3: Document Conflict Log

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

---

## Section 3: Invoke Contract Skills

### Step 3.1: Route Conflicts to Contract Skills

For each HIGH or MEDIUM severity conflict, invoke the relevant contract skill:

| Conflict Type | Contract Skill | Input | Output |
|---------------|----------------|-------|--------|
| API versioning, sync/async API | `/contract-api-rest` | conflict log + surface positions | api-contract.md |
| Event schema, ordering, retention | `/contract-event-bus` | conflict log + surface positions | event-contract.md |
| Cache key patterns, TTL, consistency | `/contract-cache` | conflict log + surface positions | cache-contract.md |
| Schema migration, indexing, constraints | `/contract-schema-db` | conflict log + surface positions | db-contract.md |
| Index mapping, analyzer, refresh | `/contract-search` | conflict log + surface positions | search-contract.md |

### Step 3.2: Invoke Contract Skills in Parallel

```
/contract-api-rest [conflict-log] [surface-positions]
/contract-event-bus [conflict-log] [surface-positions]
/contract-cache [conflict-log] [surface-positions]
/contract-schema-db [conflict-log] [surface-positions]
/contract-search [conflict-log] [surface-positions]
```

Each contract skill will:
1. Analyze the conflict positions
2. Propose a negotiated solution that satisfies all surfaces
3. Document trade-offs and rationale
4. Return a locked contract that all surfaces can sign off on

### Step 3.3: Collect Negotiated Contracts

Store outputs:
- `/home/lordvoldemort/Videos/forge/brain/prds/[task-id]/contracts/api-contract.md`
- `/home/lordvoldemort/Videos/forge/brain/prds/[task-id]/contracts/event-contract.md`
- `/home/lordvoldemort/Videos/forge/brain/prds/[task-id]/contracts/cache-contract.md`
- `/home/lordvoldemort/Videos/forge/brain/prds/[task-id]/contracts/db-contract.md`
- `/home/lordvoldemort/Videos/forge/brain/prds/[task-id]/contracts/search-contract.md`

---

## Section 4: Resolve Unresolved Conflicts

### Step 4.1: Identify Unresolved Conflicts

After contract skill invocation, check if all conflicts are resolved:
- If contract skill found a negotiated solution, mark as RESOLVED
- If contract skill could not negotiate a solution, mark as UNRESOLVED

### Step 4.2: Escalate to Dreamer (if needed)

For UNRESOLVED conflicts that require human-level counterfactual reasoning:

```
/inline-dreamer [unresolved-conflict]
```

Provide to dreamer:
- The conflict description
- All surface positions (backend, web, app, infra)
- Contract skill's attempt to negotiate
- Request: counterfactual reasoning to find creative solutions or trade-offs

Dreamer will return:
- Counterfactual scenario (e.g., "what if we accept offline-first but sync critical paths?")
- Recommended resolution with rationale
- Signed-off decision

### Step 4.3: Document Decision Trail

For each resolved conflict, update the conflict log:

```markdown
### Conflict: [name]
- **Status**: RESOLVED
- **Resolution**: [what decision was made?]
- **Reasoning**: [why this decision?]
- **Decided by**: [contract-api-rest | contract-event-bus | dreamer | etc.]
- **Surfaces sign-off**: [backend ✅ | web ✅ | app ✅ | infra ✅]
```

---

## Section 5: Output Shared-Dev-Spec

### Step 5.1: Consolidate All Agreements

Create the master `~/forge/brain/prds/<task-id>/shared-dev-spec.md`:

```markdown
# Shared Development Spec

**Status**: LOCKED — Immutable, ready for tech-planning  
**Locked at**: [ISO timestamp]  
**Locked by**: council-multi-repo-negotiate

---

## Product Request Document (PRD)

[Locked PRD from intake, all surfaces agree on scope & success criteria]

---

## Design source (from intake)

**HARD-GATE:** Copy verbatim from `prd-locked.md` the subsection **Design / UI (Q9)** (or `design_ui_scope: not applicable` when backend-only).

- `design_intake_anchor:` (verbatim from `prd-locked.md` — user’s answer to single design source of truth)
- `design_new_work:` (yes | no / engineering-only)
- `design_assets:` (human pointers: links, Confluence — optional for people)
- **`design_brain_paths`:** (paths under `~/forge/brain/prds/<task-id>/design/` — **required when `design_new_work: yes`** unless lovable repo or figma keys below are present)
- **`lovable_github_repo` + `lovable_path_prefix` (optional) + pinned ref:** (when [Lovable](https://lovable.dev) UI is authoritative — GitHub-synced code; see **`docs/platforms/lovable.md`**)
- **`figma_file_key` + `figma_root_node_ids`:** (when Figma is authoritative — enables MCP/REST)
- `design_waiver: prd_only` + owner + risk (only if present)

**Council must add one line of implementable contract for net-new UI:** e.g. “Implementation spacing/typography/component states for [feature] must match Figma nodes `<ids>` or files under `design/` listed above.”

**Downstream:** `web.md` / `app.md` (council) should name **screens and major components** implied by the PRD + design anchors so **`tech-plan-write-per-project` Section 1b.4** can map each anchor → file or `NET_NEW` without guesswork. Figma in intake is wasted if council leaves only prose and tech planning never tables nodes → components.

Surface reasoning (web, app) and tech plans **must** treat this block as authoritative for “is there new visual work?” and “where are the pixels?” — not inferred from hallway chat. **Wiki-only URLs without brain paths or figma key+nodes are not sufficient** when `design_new_work: yes` — return to intake before treating council output as complete.

---

## REST API Contract

[From contract-api-rest negotiation]

### Endpoints
- [endpoint pattern]
- [endpoint pattern]

### Versioning Strategy
[how do we version the API?]

### Error Codes
[standard error response format]

### Auth & Rate Limits
[authentication, rate limits, idempotency]

---

## Event Bus Contract

[From contract-event-bus negotiation]

### Topics & Schema
- [topic name: schema & versioning]
- [topic name: schema & versioning]

### Idempotency & Ordering
[consumer group strategy, dead-letter queues]

### Retention Policy
[topic retention, compaction]

---

## Cache Contract

[From contract-cache negotiation]

### Key Patterns
- [namespace:entity:id pattern]
- [namespace:aggregate pattern]

### TTL Strategy
[how long do cached values live?]

### Invalidation Rules
[when and how to invalidate?]

### Consistency Model
[eventual | strong | write-through]

---

## Database Schema Contract

[From contract-schema-db negotiation]

### Core Tables
- [table name]: [purpose]
- [table name]: [purpose]

### Migration Strategy
[how do we evolve the schema safely?]

### Backward Compatibility
[what schema versions coexist?]

### Indexing & Constraints
[indexes, foreign keys, unique constraints]

---

## Search Contract

[From contract-search negotiation]

### Index Mapping
- [index name]: [field mapping]
- [index name]: [field mapping]

### Analyzer Strategy
[tokenization, stemming, synonyms]

### Consistency & Refresh Policy
[how fresh is search index?]

### Reindex Procedures
[how do we reindex without downtime?]

---

## Conflict Resolution Log

[All conflicts from Section 2, with resolutions from Section 3 & 4]

### Example:

**Conflict: Sync vs Async API**
- **Surfaces affected**: backend, web, app
- **Category**: Architectural
- **Description**: Backend prefers async Kafka events for scalability. Web expects synchronous API response for immediate UI feedback. App wants offline-first queue.
- **Backend position**: Emit events to Kafka, decouple frontend from service processing
- **Web position**: Need sync API response to show confirmation to user immediately
- **App position**: Queue events locally, sync when online
- **Severity**: HIGH

**Resolution**: Hybrid approach
- Sync API responds immediately with accepted status (no processing wait)
- Backend processes async via Kafka event
- Web shows optimistic UI update, listens for webhook/event for final status
- App queues locally, syncs on reconnect
- **Decided by**: contract-api-rest + dreamer
- **Surfaces sign-off**: backend ✅ | web ✅ | app ✅ | infra ✅

---

## Surface Sign-Offs

| Surface | Reasoning Output | Contracts Signed | Status |
|---------|------------------|------------------|--------|
| Backend | backend.md | ✅ API, Events, DB, Cache, Search | LOCKED |
| Web | web.md | ✅ API, Cache | LOCKED |
| App | app.md | ✅ API, Cache, DB (local) | LOCKED |
| Infra | infra.md | ✅ DB, Cache, Events, Search | LOCKED |

---

## Status

**LOCKED** — All surfaces agree. All contracts locked. Immutable.  
Ready for → **Phase 2.11: tech-planning** (architecture review & task breakdown)

```

### Step 5.2: Validate Spec Completeness

Before marking LOCKED, verify:
- [ ] All 4 surface reasoning outputs included/summarized
- [ ] All 5 contracts included and negotiated
- [ ] All conflicts documented and resolved
- [ ] All surfaces have signed off (✅ status)
- [ ] No open questions or TODO items
- [ ] Spec is internally consistent (e.g., API endpoints match DB schema, cache keys match what infra supports)

### Step 5.3: Use brain-write to Lock Spec

```
/brain-write [task-id] [shared-dev-spec.md]
```

This marks the spec as immutable in the brain.

---

## Edge Cases & Fallback Paths

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

---

## Execution Checklist

- [ ] Read locked PRD via `/brain-read`
- [ ] Invoke all 4 reasoning skills in parallel
- [ ] Collect outputs to `reasoning/` folder
- [ ] Compare surfaces, identify conflicts
- [ ] Categorize conflicts (Architectural, Contract, Priority, Non-blocking)
- [ ] Document conflict log
- [ ] Invoke relevant contract skills in parallel
- [ ] Collect negotiated contracts
- [ ] Identify any unresolved conflicts
- [ ] Escalate unresolved conflicts to `/inline-dreamer`
- [ ] Document decision trail for all conflicts
- [ ] Consolidate shared-dev-spec.md with all sections (including **Design source (from intake)** when web or app is in scope)
- [ ] **Parity:** Create `parity/` with **`external-plan.md`** OR completed **`checklist.md`** (from **`docs/parity-checklist-template.md`**) OR **`waiver.md`** — before **`spec-freeze`**
- [ ] **Optional:** Write **`delivery-plan.md`** (rollout, flags, pyramid targets, open questions) — non-frozen; links spec headings only
- [ ] Validate spec completeness
- [ ] Use `/brain-write` to lock spec
- [ ] Report: DONE, spec locked, parity satisfied — ready for **`spec-freeze`** then tech-planning

---

## Notes

- **Parallelization**: Sections 1.2 and 3.2 can run in parallel within the skill (no inter-dependencies)
- **Escalation**: Unresolved conflicts are escalated to dreamer, not left hanging
- **Immutability**: Once locked, the shared-dev-spec cannot be modified without explicit unlock + re-negotiation
- **Next Phase**: Output of this skill feeds directly into Phase 2.11 (tech-planning), which breaks the spec into implementation tasks

## Checklist

Before claiming council complete:

- [ ] All 4 surfaces (backend, web frontend, app frontend, infra) produced reasoning outputs
- [ ] All 5 contracts negotiated (REST API, event bus, cache, DB schema, search)
- [ ] No TBD fields remain in shared-dev-spec
- [ ] **Design source** subsection present or explicitly `not applicable` when scope includes web/app
- [ ] All cross-surface conflicts resolved — none deferred to implementation
- [ ] shared-dev-spec.md locked and written to brain via brain-write
- [ ] spec-freeze invoked to prevent post-council mutations

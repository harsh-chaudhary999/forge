---
name: forge-council-gate
description: "WHEN: A PRD has been locked by intake and needs Council negotiation. HARD-GATE: Every locked PRD goes through Council (4 surfaces + 5 contracts negotiated). No skipping."
type: rigid
version: 1.0.6
preamble-tier: 3
triggers:
  - "council gate"
  - "spec is ready for build"
  - "freeze spec gate"
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---
# Council Gate (HARD-GATE)

## Human input

This skill lists **`AskUserQuestion`** in **`allowed-tools`** — canonical for Claude Code and skill lint. Blocking prompts follow **[`skills/_shared/human-input.md`](../_shared/human-input.md)**. See **`using-forge`** **Interactive human input**.

**Cross-cutting assistant dialogue:** **`docs/forge-one-step-horizon.md`** — **`using-forge`** **Multi-question elicitation** items **4–8**.

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

## Iron Law

```
NO IMPLEMENTATION STARTS BEFORE COUNCIL COMPLETES. A SHARED-DEV-SPEC WITH ANY UNRESOLVED TBD OR MISSING CONTRACT IS NOT A LOCKED SPEC — IT IS A DRAFT.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Fewer than 4 surfaces are present in the council session** — Missing any surface means its constraints, vetos, and integration requirements go unheard. STOP. All 4 surfaces (backend, web, mobile, infra) must be represented before council can begin.
- **Council is starting before the PRD is locked in brain** — An unlocked PRD means intake hasn't completed. Council negotiates contracts on top of assumptions, not validated requirements. STOP. Verify the PRD exists and is locked in `~/forge/brain/prds/` before invoking council.
- **A conflict between two surfaces is being deferred with "we'll resolve it post-merge"** — Deferred conflicts become integration bugs. Council exists to surface and resolve these conflicts before any code is written. STOP. Every conflict must be resolved or escalated during council.
- **Contracts contain "TBD" fields after council closes** — A "TBD" in a contract is an open negotiation item, not a closed one. STOP. Every contract field must be filled with a concrete, agreed value before the shared-dev-spec is frozen.
- **The shared-dev-spec is frozen without a brain commit** — Spec freeze without a brain-write means the decision has no audit trail. STOP. Commit the frozen spec to `~/forge/brain/` before any surface proceeds to tech planning.
- **Tech planning has begun for any surface before spec is frozen** — If any surface starts writing tasks before spec-freeze, they are planning against a moving target. STOP. Freeze the spec first.
- **Council is skipped because "this is a patch to an existing feature"** — Patches modify behavior, touch contracts, and affect other surfaces. Every PRD — no matter how small — goes through council. STOP. No exceptions.
- **Council closes without cohort/adjacency material when the PRD requires it** — Missing **`[ADJACENCY-SCAN]`**, missing cohort artifacts, or **`SPEC_INFERENCE`**-only segmentation per **`docs/adjacency-and-cohorts.md`**. STOP. Complete **State 2.6** + council checks before **`spec-freeze`**.
- **`terminology.md` (product/domain) has unresolved open doubts** when those terms appear in **success criteria or contract-facing copy** — STOP. Resolve per [docs/terminology-review.md](../../docs/terminology-review.md) or **[intake-interrogate](../intake-interrogate/SKILL.md)**; do not lock **shared-dev-spec** on ambiguous customer-facing names. (Forge process terms: [forge-glossary](../forge-glossary/SKILL.md).)

**`[TERMINOLOGY]` in `conductor.log` (standalone `/council`):** **Do not append** from this skill — only **[council-multi-repo-negotiate](../council-multi-repo-negotiate/SKILL.md) Step 5.4** (end of council) writes the line, so a council run does not leave **two** [TERMINOLOGY] lines with conflicting `open_doubts`. The hook `prompt-submit-gates.cjs` uses the **last** [TERMINOLOGY] line in the file only.

## Detailed Workflow

### Pre-Council: Codebase Scan Freshness Check (Existing Codebases)

Before preparing council materials, check whether a codebase scan exists and is fresh. Council surface agents need the module map to reason about where to place new code, which hubs will be affected, and what the existing architecture patterns are.

```bash
SCAN_FILE=~/forge/brain/products/<slug>/codebase/SCAN.json
if [ -f "$SCAN_FILE" ]; then
  SCAN_DATE=$(cat "$SCAN_FILE" | grep '"scanned_at"' | grep -o '"[0-9T:Z-]*"' | tr -d '"')
  SCAN_AGE=$(( ( $(date -u +%s) - $(date -d "$SCAN_DATE" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%SZ" "$SCAN_DATE" +%s 2>/dev/null) ) / 86400 ))
  echo "Codebase scan: $SCAN_DATE ($SCAN_AGE days ago)"
else
  echo "Codebase scan: NOT FOUND"
fi
```

`SCAN.json` may use a **nested** shape: per-role data lives under `repos.<role>` with **top-level** aggregates (`scanned_at`, `source_files`, …) for backward compatibility. The `grep` snippet above still finds `scanned_at` on typical files; when reading the file in full, prefer `repos.<role>` for role-specific freshness.

**Decision:**

| Situation | Action |
|---|---|
| Scan not found AND this is a greenfield product (first PRD) | No scan needed. Proceed to council. |
| Scan not found AND this is an existing codebase | Warn surface agents: ⚠️ No codebase scan. Surface agents will reason without architecture context — tech plans may conflict with existing structure. Recommend: run `/scan <slug>` before council. Do NOT block council. |
| Scan is <7 days old | Surface scan context to agents. Proceed to council. |
| Scan is 7-30 days old | Warn: ⚠️ Scan is N days old — refresh recommended (`/scan <slug>`). Do NOT block council if user acknowledges. |
| Scan is >30 days old | Prompt user: "Codebase scan is N days old. Running council on stale architecture data risks tech plans that don't fit the codebase. Refresh now? (yes / proceed anyway)" |

**Never block council** — the scan gate is advisory. Flag staleness, provide the data you have, proceed.

**When `SCAN.json` exists:** Run **`python3 tools/verify_scan_outputs.py ~/forge/brain/products/<slug>/codebase`** (up to **3** attempts, **1s** apart). If it **still fails**, warn loudly: consolidated markdown/JSON did not land — **re-run `/scan`** before relying on `modules/*.md` for council file paths. Proceeding without refresh is allowed only if the human acknowledges **explicit risk** in writing (e.g. `context-loaded.md`).

---

### Gather Inputs (Pre-Council)
- **Parity (before `spec-freeze`):** Ensure the task folder will receive **`~/forge/brain/prds/<task-id>/parity/`** with **`external-plan.md`** OR completed **`checklist.md`** (copy **`docs/parity-checklist-template.md`**) OR **`waiver.md`** (`parity_waiver: true` + owner + reason). Council + contracts must not be treated as “done” if the only artifact is a thin `shared-dev-spec` that never absorbed the org’s detailed plan — see **`spec-freeze`** Step 0.
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
  **Resumption rule:** At session start, read `shared-dev-spec.md` frontmatter. Contracts with `status: negotiated` are already closed — do not re-open them. Start from the first `open` contract.

#### Disputed Contract Recovery

When a contract is in `disputed` state and a dreamer escalation is pending:

1. Record the dreamer escalation ID in the contract's frontmatter:
   ```yaml
   contract_api_status: disputed
   dispute_escalation_id: DREAM-<timestamp>-<slug>
   dispute_reason: <one-line description of the disagreement>
   ```
2. Do NOT re-open or re-negotiate contracts already marked `negotiated` while a dispute is pending.
3. Continue negotiating any remaining `open` contracts that are not party to the dispute.
4. When the dreamer decision arrives: update the contract status to `negotiated` (if resolved) or `open` (if sent back for re-negotiation), remove `dispute_escalation_id`, and log `[P2-DISPUTE-RESOLVED] task_id=<id> contract=<name> decision=DREAM-<id>` to `conductor.log`.
5. **HARD-GATE:** Do not invoke `spec-freeze` while any contract is in `disputed` state, even if all others are `negotiated`.

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
- [ ] If web/app or user-visible UI: **`design_intake_anchor`** present in `prd-locked.md` per **`intake-interrogate` Q9** (proves design source-of-truth was asked)
- [ ] Codebase scan checked — fresh (<7 days), stale (warned), or absent (warned with greenfield exception)
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
- [ ] Per-contract status written to `shared-dev-spec.md` YAML frontmatter after each contract closes:
  ```yaml
  contract_api_status: negotiated       # or: open | disputed
  contract_events_status: negotiated
  contract_cache_status: negotiated
  contract_db_status: negotiated
  contract_search_status: negotiated
  ```
  **Why:** If the session is interrupted after 3/5 contracts, the next session reads frontmatter and skips re-negotiating already-closed contracts. `open` = not yet discussed; `disputed` = dreamer escalation pending; `negotiated` = locked.
- [ ] All conflicts resolved (or escalated to dreamer with decision)
- [ ] Each surface agrees to their scope
- [ ] Each surface agrees to contract specifications
- [ ] No "TBD" in contracts (all details locked)
- [ ] Shared-dev-spec created in brain (SPECLOCK decision ID)
- [ ] Per-project tech plan inputs ready (surface scope + contracts)

## Additional Edge Cases

Full edge-case catalog in [reference/edge-cases.md](reference/edge-cases.md).

## Checklist

Before claiming council complete:

- [ ] All 4 surfaces (backend, web frontend, app frontend, infra) attended and produced outputs
- [ ] All 5 contracts negotiated (REST API, event bus, cache, DB schema, search)
  **Resumption rule:** At session start, read `shared-dev-spec.md` frontmatter. Contracts with `status: negotiated` are already closed — do not re-open them. Start from the first `open` contract.
- [ ] Per-contract status written to `shared-dev-spec.md` YAML frontmatter after each contract closes:
  ```yaml
  contract_api_status: negotiated       # or: open | disputed
  contract_events_status: negotiated
  contract_cache_status: negotiated
  contract_db_status: negotiated
  contract_search_status: negotiated
  ```
  **Why:** If the session is interrupted after 3/5 contracts, the next session reads frontmatter and skips re-negotiating already-closed contracts. `open` = not yet discussed; `disputed` = dreamer escalation pending; `negotiated` = locked.

**Example `shared-dev-spec.md` frontmatter with per-contract status:**

```yaml
---
task_id: my-feature-task
schema_version: 1

contract_api_status: negotiated      # REST endpoints agreed
contract_cache_status: open          # TTL policy still disputed
contract_event_status: negotiated    # Topic names + schema locked
contract_schema_status: negotiated   # DB migration approved
contract_search_status: open         # Index mapping TBD

spec_frozen: false                   # set to true only when ALL contracts = negotiated
---
```

On session resumption: skip any contract where `status: negotiated`. Re-enter negotiation only for `open` or `disputed` contracts.

- [ ] All cross-surface conflicts resolved — none deferred to implementation
- [ ] shared-dev-spec.md has no TBD fields
- [ ] spec-freeze invoked after spec is written to brain

## Post-Implementation Checklist

- [ ] All 5 contracts show `status: negotiated` in `shared-dev-spec.md` frontmatter.
- [ ] `[P2-SPEC-FROZEN]` logged to `conductor.log` after last contract negotiated.
- [ ] `shared-dev-spec.md` committed to brain with `task_id:` anchor.
- [ ] No contract left in `open` or `disputed` state.
- [ ] On session resumption: only contracts not yet `negotiated` were re-negotiated.

## Cross-References

- `council-multi-repo-negotiate`: Called by forge-council-gate to run contract negotiation per repo pair; gate validates negotiation is complete.
- `spec-freeze`: Triggered by forge-council-gate when all 5 contracts reach `status: negotiated`; logs `[P2-SPEC-FROZEN]`.
- `contract-api-rest`: First contract validated by the gate; REST API contract between repos.
- `contract-event-bus`: Second contract validated by the gate; event/message contracts.
- `contract-cache`: Third contract validated by the gate; cache key and TTL contracts.
- `contract-schema-db`: Fourth contract validated by the gate; database schema contracts.
- `contract-search`: Fifth contract validated by the gate; search index contracts.
- `conductor-orchestrate`: Sequences `[P2-SPEC-FROZEN]` in the pipeline; forge-council-gate produces the output conductor consumes.
- `docs/conductor-log-format.md`: `[P2-SPEC-FROZEN]` and `[P2-SPEC-AMENDED]` marker formats logged after council completes.

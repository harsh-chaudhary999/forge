---
name: brain-why
description: "WHEN: You need to trace the full provenance of a specific decision — who made it, when, why, and what alternatives were considered. Shows why, when, by whom, evidence, alternatives, outcome."
type: flexible
requires: [brain-read]
version: 1.0.0
preamble-tier: 2
triggers:
  - "why was this decided"
  - "explain this decision"
  - "trace decision rationale"
allowed-tools:
  - Bash
  - Write
  - AskUserQuestion
---

# brain-why Skill

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I know why this decision was made" | You know your interpretation. The brain stores the actual reasoning, evidence, and alternatives. They may differ. |
| "The commit message explains it" | Commit messages explain what changed, not why it was chosen over alternatives. brain-why provides full provenance. |
| "This decision is straightforward, no need to trace it" | "Straightforward" decisions are the ones most likely to have hidden constraints. Trace it anyway. |
| "I'll just ask the team" | People forget. People rationalize. The brain's record is contemporaneous evidence, not reconstructed memory. |
| "The alternative section is empty, so there was only one option" | Missing alternatives means the decision wasn't fully explored, not that no alternatives existed. Flag it. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
TRACE EVERY DECISION TO ITS RECORDED SOURCE BEFORE ACTING ON IT. AN UNDOCUMENTED DECISION HAS NO AUTHORITY — ABSENCE OF EVIDENCE IS NOT EVIDENCE OF CORRECTNESS.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Provenance is being reconstructed from git log instead of brain files** — Git history shows what changed, not why it was chosen. STOP. Always query `~/forge/brain/` directly — the brain file is the authoritative provenance record, not the commit message.
- **Decision ID is not found in brain but agent proceeds with "best guess" reasoning** — If the brain has no record of a decision, the provenance is unknown — not guessable. STOP. Report that provenance is unrecorded and escalate for documentation. Do not invent a rationale.
- **Alternatives section of a decision is empty and agent treats this as "one option existed"** — An empty alternatives section means the decision was underspecified, not that no alternatives were possible. STOP. Flag the gap: "Decision recorded without alternatives — provenance is incomplete."
- **brain-why is being skipped because "the decision is recent"** — Recency does not substitute for documentation. What seems obvious today will be opaque in 6 months. STOP. Trace every decision, regardless of age.
- **Agent uses brain-recall results instead of brain-why to answer a provenance question** — brain-recall searches for related decisions; brain-why traces a specific decision's chain of reasoning and alternatives. They are not interchangeable. STOP. For provenance questions, use brain-why with the specific decision ID.
- **Provenance trace stops at the most recent decision without checking for superseded predecessors** — A current decision may supersede an earlier one; the full chain matters for understanding the evolution of thinking. STOP. Always check for `supersedes` links and follow them to the origin.

Trace the provenance of any decision. Given a decision ID, this skill walks through the complete decision history, from motivation to outcome, showing why the decision was made, when, by whom, what evidence justified it, what alternatives were considered, and what actually happened.

## 1. Decision Lookup

> **Preferred path: the brain MCP `brain_why` tool** (read-only) returns a
> decision's frontmatter + git history in one call — exactly what this skill does
> by hand. See [`forge-brain-layout`](../forge-brain-layout/SKILL.md) (MCP query map)
> and [`docs/brain-mcp.md`](../../docs/brain-mcp.md). Caveat: enable with
> `claude mcp add forge-brain` (bundled `.mcp.json` ships `mcpServers: {}`); the
> manual `git log` / `grep` walk below is the live fallback.

When invoked with a decision ID (e.g., `D42`, `D123`), the skill performs:

- **Query the decision index** in the brain (via `brain-read`) to locate the decision file
- **Load the decision record** with all linked context
- **Verify decision exists** and is accessible
- **Flag if partially documented** or missing sections
- **Return location** for direct inspection if needed

Example:
```
/brain-why D42
→ Loads: ~/forge/brain/decisions/architecture/D042_api-versioning.md
→ Linked context: D41 (parent), D43, D44 (children)
```

## 2. Provenance Walk

A complete walk through the decision's history, presented in 5 layers:

### Why
- **Problem statement** — what problem motivated this decision?
- **Goal** — what outcome was sought?
- **Motivation** — business, technical, or operational driver?
- **Evidence** — research, data, or proof that led to this choice?

Example:
```
Why: 
  Problem: Clients break when we deprecate endpoints (0-notice deprecations)
  Goal: Provide predictable migration window
  Motivation: Zero production incidents, improve trust with partners
  Evidence: AWS/Stripe/GitHub all graduated (12mo min), our 2024 incident report
```

### When
- **Date decided** — when was the decision locked?
- **Phase** — what Forge phase or project cycle?
- **Project context** — which product/service was this for?
- **Deadline** — when did implementation need to complete?

Example:
```
When:
  Date: 2026-03-15
  Phase: Phase 2 (Council reasoning)
  Project: shopapp (backend + web + app)
  Deadline: 2026-04-30 (before Q2 launch)
```

### By Whom
- **Decision maker(s)** — who had final say? (individual, team, council)
- **Champion** — who advocated most strongly?
- **Stakeholders** — who else had input or was affected?
- **Veto holders** — who had blocking authority?

Example:
```
By Whom:
  Decision maker: Backend + Web + App + Infra council (unanimous)
  Champion: Backend team lead (Alex K)
  Stakeholders: Mobile app (offline-first concerns), API clients
  Veto holders: Backend, Infra (API stability)
```

### Evidence
- **Data cited** — test results, logs, metrics, customer feedback?
- **Comparisons** — how do competitors solve this?
- **Internal history** — past successes or failures with similar patterns?
- **Proof of concept** — was anything prototyped?

Example:
```
Evidence:
  Competitor analysis: AWS (12mo), Stripe (18mo), GitHub (12mo), Twilio (6mo)
  Internal: 2024 incident log (32 outages from rapid deprecation)
  POC: contract-api-rest prototype tested with 3 client libraries
  Customer feedback: "6+ month notice preferred" (6/8 surveyed)
```

### Alternatives Considered
For each alternative:
- **Option name & description**
- **Why rejected** — cost, risk, implementation complexity?
- **Trade-offs** — what would we have gained/lost?
- **Who argued for it** — was there dissent?

Example:
```
Alternatives Considered:

1. URL Versioning (v1, v2, /v3/users)
   Rejected: Cognitive load on clients, duplicated routes in code
   Trade-off: Simpler for server (no deprecation logic), harder for clients
   Argued by: Some backend engineers (voted down 3-2)

2. Header Versioning (Accept: application/vnd.v2+json)
   Rejected: Cache invalidation complexity, CDN problems
   Trade-off: Invisible to clients, harder to debug
   Argued by: Infra team (concerns about cache headers)

3. Rapid Removal (no deprecation, version bumps weekly)
   Rejected: Breaks client contracts, forces constant updates
   Trade-off: Simpler for us, unacceptable for partners
   Voted: Rejected unanimously (broke mobile app in simulation)
```

## 3. Dependency Chain

Show the "why tree" — what decisions led to this, and what this decision enabled:

### Parent Decisions
- List decisions that this one depends on
- Show how they constrained this choice
- Example: "D42 depends on D41 (REST API design principles)"

### Child Decisions
- List decisions that this one enabled or triggered
- Show what was unlocked
- Example: "D42 enabled D43 (Sunset header strategy) and D44 (Error code taxonomy)"

### Impact Map
- Trace transitive impacts: D42 → D43 → D45
- Show which projects are affected
- Highlight critical paths (decisions that many others depend on)

Example:
```
Dependency Chain:
  
  D41 (REST API design principles)
    ↓
  D42 (Graduated API versioning) ← YOU ARE HERE
    ├→ D43 (Sunset header strategy)
    ├→ D44 (Error code taxonomy)
    └→ D45 (Client library SLA)
        ├→ D46 (SDK release cadence)
        └→ D47 (Docs versioning)
  
  Affected projects: shopapp, vendorapp, partner-api
  Critical path: D42 → D43 → API launch (2026-04-30)
```

## 4. Lessons Learned

Capture what was actually discovered during execution:

### Did It Work?
- **Status** — fully delivered, partially delivered, failed, ongoing?
- **Metrics** — what did we measure? How did it perform?
- **Incidents** — what went wrong (if anything)?
- **Wins** — what went better than expected?

Example:
```
Did It Work?
  Status: Fully delivered, in production since 2026-03-20
  Metrics:
    - Client migration time: avg 3 weeks (better than 6 weeks estimated)
    - Deprecation incidents: 0 (target: <2)
    - Adoption of new version: 95% within 2 months
  Incidents: None in production
  Wins: Client feedback very positive ("felt respected")
```

### If Failed: What Was Learned?
- **Root cause** — where did the plan break?
- **Recovery** — how did we fix it?
- **New insight** — what would we do differently?

Example:
```
If Failed: What Was Learned?
  (N/A — this decision succeeded)
```

### Gotchas Discovered
- **Surprises** — what was harder than expected?
- **Dependencies** — what other systems mattered more than we thought?
- **Edge cases** — what special cases emerged during rollout?
- **Future cautions** — what should the next similar decision watch out for?

Example:
```
Gotchas Discovered:
  
  1. Client library upgrades took 4 weeks longer than estimated
     → Issue: Mobile app CI/CD was slower than web/backend
     → Lesson: Never estimate client adoption without knowing their pipeline
  
  2. 12-month deprecation window was too generous
     → We could have used 6 months (most clients migrated in 8 weeks)
     → Lesson: Graduated deprecation works, but shorter timeline acceptable
  
  3. Internal API clients didn't know about deprecation schedule
     → Required ad-hoc notifications (should have automated)
     → Lesson: Deprecation schedule must be visible in API docs & SDK changelogs
```

## 5. Comparative Analysis

Learn from similar decisions across the product portfolio:

### Similar Decisions on Other Products
- What patterns are repeated?
- Same decision, different outcomes?
- Example: "API versioning via graduated deprecation" used in 3+ products

### Different Outcomes on Similar Choices
- When did we choose A and it worked?
- When did we choose B and it failed?
- What was different?

Example:
```
Comparative Analysis:

Pattern: "API versioning via graduated deprecation"
  ✅ shopapp (2026) → 0 incidents, clients happy
  ✅ vendorapp (2025) → 1 minor incident, resolved in 2 hours
  ✅ partner-api (2024) → smooth rollout, baseline for this decision
  ⚠️  legacy-service (2023) → rapid removal, 4 incidents (why D42 was needed)

Anti-pattern: "Rapid version removal (no deprecation)"
  ❌ legacy-service (2023) → 4 major incidents, 2 week client outage
  ❌ internal-tools (2022) → forced 3 teams to emergency updates
  ✅ experimental-api (2024) → worked because no external clients

Pattern: "Header versioning"
  ⚠️  micro-service (2023) → cache invalidation issues, CDN bugs
  ❌ cdn-api (2024) → complexity not worth the benefit

Insight: Graduated deprecation is "tried and true". Header versioning adds
risk without benefit. Rapid removal only safe for internal-only APIs.
```

---

## Worked Examples, Walk Patterns, Evidence, Pitfalls, Integration (reference)

These deep sections were moved to `reference/*.md` to keep this SKILL.md as the operational contract. Load them on demand:

- See [reference/examples.md](reference/examples.md) for the 3 complete worked decision walks (D42 API versioning, D89 gRPC migration, D156 Docker Compose vs Kubernetes) — full provenance structure, dependency graphs, and "how to navigate from here" for each.
- See [reference/walk-patterns.md](reference/walk-patterns.md) for the 5 decision-walk patterns (root-cause, precedent, cascading-impact, alternative-evaluation, timeline) with graph-traversal steps and real example queries.
- See [reference/evidence-quality.md](reference/evidence-quality.md) for evidence-strength tiers (data/authority/experience/weak), the read-time evaluation checklist, red flags, and the "challenge stale evidence" checklist.
- See [reference/pitfalls.md](reference/pitfalls.md) for the 5 common decision-walk pitfalls (stale decisions, missing superseded links, broken evidence links, single-source evidence, circular graphs) with detect/fix/prevent steps.
- See [reference/brain-skill-integration.md](reference/brain-skill-integration.md) for how brain-why composes with brain-read, brain-write, brain-recall, brain-link, and brain-forget, plus the full cross-skill tracing example.

---



## Usage

Invoke this skill with a decision ID:

```
/brain-why D42
```

Returns a formatted walk through all 5 sections, with linked references to:
- Parent decisions (for context)
- Child decisions (for downstream impact)
- Related decisions (same pattern, different products)
- Brain files (for deep dive)

## Integration Points

- **brain-read**: Queries the decision index and loads decision files
- **Decision format**: Must follow the standardized DECISION.md schema
- **Dependency tracking**: Links to parent and child decision IDs
- **Pattern library**: Cross-references similar decisions across products

## Edge Cases

### Edge Case 1: Circular dependency in decision links (A→B→A)

**Symptom:** Provenance trace loops back on itself (parent → child → parent creates cycle).

**Do NOT:** Follow cycle infinitely. Do NOT treat circular dependency as acceptable.

**Mitigation:**
1. Detect cycle: Track visited decision IDs during traverse
2. Report when found: "Circular dependency detected: D42 → D43 → D42"
3. Break cycle by reporting at cycle detection point (not following back edge)
4. Escalate: This indicates decision graph corruption

**Escalation:** BLOCKED — Circular dependency in decision graph. Indicates data corruption or modeling error. One decision references the other incorrectly. Contact decision owners to remove circular reference and restore linear provenance chain.

---

### Edge Case 2: Decision has no parent (orphaned decision)

**Symptom:** Decision lacks `parent_decision:` field, showing no upstream context or justification.

**Do NOT:** Assume decision stands alone. Do NOT treat missing parent as authoritative.

**Mitigation:**
1. Check for `parent_decision:` field in frontmatter
2. If empty or missing, search for implicit parent: `grep -r "related.*D<id>" ~/forge/brain --include="*.md"`
3. If truly orphaned, document: "Decision D### has no recorded parent (orphan or root decision)"
4. For orphan: Review decision title and problem statement — may be foundational decision (no parent needed)

**Escalation:** NEEDS_CONTEXT — Orphaned decision may be root decision (acceptable) or indicate incomplete decision graph. Verify with decision author whether parent is missing or decision is intentionally foundational.

---

### Edge Case 3: Provenance chain broken (linked decision deleted)

**Symptom:** Decision references parent/child that no longer exists (file was archived or moved).

**Do NOT:** Ignore broken reference. Do NOT proceed with incomplete provenance.

**Mitigation:**
1. Verify referenced decision exists: `grep -r "^decision_id: D<parent-id>" ~/forge/brain --include="*.md"`
2. If not found, check archive: `grep -r "^decision_id: D<parent-id>" ~/forge/brain/archived --include="*.md"`
3. If archived: Note in provenance that parent was archived; flag for investigation
4. If truly deleted: Flag as data integrity issue — decisions should never be deleted

**Escalation:** BLOCKED — Broken provenance chain. Parent/child decision missing or archived. Cannot trace complete lineage. Contact brain maintainers to restore reference or document why parent was removed.

---

### Edge Case 4: Too many hops to root (provenance path > 5 levels)

**Symptom:** Provenance trace requires traversing > 5 parent decisions (D1 → D2 → D3 → D4 → D5 → D6 → ...).

**Do NOT:** Treat excessively deep chains as normal. Deep chains indicate poor decision granularity.

**Mitigation:**
1. Count hops while tracing parent chain
2. If > 5 hops, warn: "Long provenance chain detected (6+ decisions)"
3. Report intermediate decisions at each level (help readers understand path)
4. Recommend decision consolidation: consider merging some decisions

**Escalation:** NEEDS_COORDINATION — Very deep provenance chain suggests decision graph could be simplified. Consult decision owners about consolidating related decisions or creating summary decision at intermediate level.

---

### Edge Case 5: (EXISTING) Partially documented decisions missing sections

**Symptom:** Decision file lacks expected sections (Why, When, By Whom, Alternatives, Evidence).

**Do NOT:** Ignore gaps. Do NOT guess missing information.

**Mitigation:**
1. Check for required sections: grep for "^##" (heading level 2) in decision file
2. List missing sections: "Decision D### missing: Evidence, Alternatives Considered"
3. Flag as incomplete: "Provenance incomplete — cannot fully trace reasoning"
4. Point to original author: "Contact <decision_author> to document missing sections"

**Escalation:** NEEDS_CONTEXT — Decision partially documented. Cannot trace full provenance without missing sections. Notify decision author to complete documentation.

---

## Decision Tree: Trace Depth Strategy

```
Asked to trace provenance of decision D###
    ↓
Is decision marked as Active or Warm?
├─ NO (Cold/Archived) → Proceed with warning that decision is no longer current
└─ YES → Continue below

Is full parent chain available (all parent → parent → ... → root)?
├─ YES → Trace to root and report full chain
└─ NO → Identify break point and escalate

Do you need shallow trace (immediate parent only)?
├─ YES → Return 1 level: "D### depends on <parent>"
└─ NO → Continue below

Do you need deep trace (full decision graph from root)?
├─ YES → Check depth; warn if > 5 levels
└─ NO → Continue below

Is this decision a root decision (no parent)?
├─ YES → Check evergreen status; if not evergreen, flag as orphan
└─ NO → Continue below

Is provenance complete (all sections documented)?
├─ YES → Trace and return full Why/When/By Whom/Evidence/Alternatives
└─ NO → Trace what's available, flag gaps, escalate for completion

Result:
- Default: Trace to root, report all 5 sections (Why/When/By Whom/Evidence/Alternatives)
- If incomplete: Report available sections, flag gaps
- If deep (>5 levels): Warn about chain depth, still return full trace
- If broken reference: Flag and escalate to brain maintainers
- If circular: Detect and break at cycle point, escalate
```

---

**Linked Skills:**
- `brain-read` — load decision index and decision files
- `brain-write` — record new decisions and lessons learned
- `conductor-orchestrate` — track Phase assignments to decisions

**Example Invocation:**
```bash
/brain-why D42
/brain-why D100
/brain-why D15
```

**Output Format:** Structured markdown with 5 main sections, dependencies, lessons, and patterns.

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] The why explanation references the specific `decision_id` (e.g., `D42`) by name — not a vague description like "the API versioning decision"
- [ ] The source artifact (prd-locked.md, spec doc, or equivalent brain file) is cited by its brain path or git-resolvable link in the Evidence or By Whom section — not paraphrased from memory
- [ ] The reasoning is not vague or placeholder — the Alternatives Considered section lists at least one rejected option with a stated reason for rejection
- [ ] The provenance trace was sourced from the actual brain file at `~/forge/brain/` (or the product brain path), not reconstructed from git log messages or conversation recall
- [ ] If a superseded predecessor exists (a `supersedes:` link in the decision), that predecessor was also read and its chain was followed to confirm the full evolution of the decision

## Checklist

Before claiming provenance trace complete:

- [ ] Decision ID located in brain files (not reconstructed from memory or git log)
- [ ] Full decision chain traced to root decision
- [ ] Alternatives section reviewed; empty alternatives section flagged as incomplete
- [ ] Evidence and contemporaneous reasoning documented as output
- [ ] Linked decisions and downstream lessons surfaced
- [ ] Circular or broken references flagged and escalated

## Cross-References

- `brain-read`: Fetches the raw decision file for a given ID; brain-why calls it to get the full decision record.
- `brain-write`: Records new decisions; brain-why surfaces the provenance of decisions created by brain-write.
- `brain-recall`: Searches the brain for prior art before a new decision; brain-why digs deeper into a specific result.
- `brain-forget`: Archives a decision when superseded; check brain-why first to understand downstream dependents.
- `brain-link`: Traces semantic edges between decisions; brain-why walks the `related_decisions` chains brain-link creates.

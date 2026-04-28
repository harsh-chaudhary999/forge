---
name: brain-write
description: "WHEN: You need to record a decision, lock a spec, log an eval run, or document learnings in the brain."
type: flexible
version: 1.0.0
preamble-tier: 2
triggers:
  - "record a decision"
  - "write to brain"
  - "log to brain"
  - "lock a spec"
  - "document in brain"
allowed-tools:
  - Bash
  - Edit
  - Read
  - Write
---

# Brain Write

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I'll commit the decision later" | Uncommitted decisions are invisible decisions. If it's not in git, it didn't happen. |
| "The commit message can be brief" | Commit messages are the primary search surface for brain-recall. Vague messages make past decisions unfindable. |
| "I'll update the existing decision file" | Brain decisions are append-only. Editing a locked decision destroys provenance. Create a new decision that supersedes the old one. |
| "This doesn't need a full decision record" | Every decision needs who, when, why, evidence. "Quick notes" become orphaned context that no one can trace. |
| "I'll write it to a scratch file first" | Scratch files bypass the brain's git-backed audit trail. Write directly to the correct brain path. |

**If you are thinking any of the above, you are about to violate this skill.**

Every write is a git commit. Pattern:

## 1. Write the file
```bash
cat > ~/forge/brain/prds/<task-id>/shared-dev-spec.md <<'EOF'
# Shared Dev Spec

[content]
EOF
```

## 2. Commit with context
```bash
git -C ~/forge/brain add prds/<task-id>/shared-dev-spec.md
git -C ~/forge/brain commit -m "spec: lock shared dev spec for <task-id>

Converged across: backend, web, app, infra
Contracts locked: API v2, MySQL schema changes, Redis invalidation
Next: tech-plan-write-per-project"
```

## Key Guidelines

- **One file per decision** (prd-locked.md, shared-dev-spec.md, retrospective.md, etc.)
- **Descriptive commit messages** — why this decision, what it depends on, next step
- **Markup:** Markdown always
- **Paths:** Follow `~/forge/brain/` structure exactly
- **No binary files**

## Provenance Tracking Checklist

When writing a decision to the brain, capture these elements systematically. Each ensures future readers understand not just the decision, but why it was made and what context matters.

### 1. Decision ID
- **Why capture:** Unique reference for linking, searching, auditing
- **How to document:** Prefix filename with ID (D123.md), include in frontmatter, reference in commit message
- **Example:** `decisions/D087.md` for "Switch from REST to gRPC for service mesh"
- **Format:** Auto-generate with prefix (D001, D002, ...) or use semantic ID (API-REST-v2, SCHEMA-MIGRATION-v1)

### 2. Decision Title
- **Why capture:** Quick summary for brain-recall searches and human scanning
- **How to document:** H1 heading in markdown, title field in YAML frontmatter
- **Example:** `# API Contract Negotiation: REST v2 with streaming support`
- **Production pattern:** Title describes what, not how; include version/scope in title

### 3. Decision Description & Problem Statement
- **Why capture:** Context for future team members who weren't in the room; audit trail for "why did we do this?"
- **How to document:** Prose paragraph after title explaining the problem, constraints, and goals
- **Example:** "Traffic patterns showed 95th percentile latency of 2.5s with REST polling. Streaming reduces to <100ms. Infra team constraint: must support existing web clients for 6 months during transition."
- **Production pattern:** Write for readers unfamiliar with the decision; link to metrics/evidence

### 4. When Made (Date & Phase)
- **Why capture:** Understand context drift over time; know if decision is time-bound
- **How to document:** YAML frontmatter `date:` field and `phase:` if relevant; commit date in git
- **Example:** `date: 2025-11-15`, `phase: scaling` (or omit phase if decision is always-valid)
- **Production pattern:** Always include ISO date; phase is optional (omit if decision is evergreen)

### 5. By Whom (Decision Maker & Stakeholders)
- **Why capture:** Know who was in the room, who signed off, who dissented; accountability
- **How to document:** YAML `owner:`, `stakeholders:`, `decision_maker:` fields; mention approval in prose
- **Example:**
  ```yaml
  owner: platform-infra
  decision_maker: Alice Chen (Principal Architect)
  stakeholders: [backend-team, web-team, app-team, devops]
  approved_by: [VP Eng, Principal Database Architect]
  ```
- **Production pattern:** Be explicit about who decided vs. who influenced vs. who approved

### 6. What Was Decided (The Actual Decision)
- **Why capture:** Core decision record; what actually changed/locked
- **How to document:** Explicitly stated section or table; include version numbers, SLAs, rollback dates
- **Example:**
  ```markdown
  ## Decision
  Adopt gRPC over REST for service-to-service communication:
  - New services (ID ≥ 100) MUST use gRPC
  - Existing services can migrate on schedule (Q2 2026 target)
  - Keep REST public API unchanged
  - Deadline: Dec 31, 2026 (all services gRPC-native)
  ```
- **Production pattern:** Use declarative language ("MUST", "SHOULD", "MAY"); include deadlines

### 7. What Were Alternatives (Options Considered & Why Rejected)
- **Why capture:** Prevents rework (avoids re-litigating); shows thinking; audit trail
- **How to document:** Table or numbered section with option, pros, cons, verdict
- **Example:**
  ```markdown
  ## Alternatives Considered
  1. **REST with WebSocket upgrade** — Complexity high, reduces team velocity. Rejected.
  2. **Kafka event streaming** — Overkill for RPC. Chose gRPC instead.
  3. **Status quo (REST polling)** — 2.5s latency unacceptable for voice features. Rejected.
  ```
- **Production pattern:** Don't document "we considered X"; document "we considered X, pros [Y], cons [Z], rejected because [W]"

### 8. What's the Impact (Affected Systems, Rollback Strategy)
- **Why capture:** Scope of change; risk assessment; how to undo if wrong
- **How to document:** Section listing affected services, API changes, migration steps, rollback procedure
- **Example:**
  ```markdown
  ## Impact
  - Affected systems: 47 services, 3 data planes
  - Breaking changes: ServiceA.GetUser changes from REST HTTP/1.1 to gRPC
  - Rollback: Revert to commit HASH, re-enable REST fallback, maintain 7-day soak period
  - Timeline: 3 months parallel run (both REST+gRPC active), then REST deprecation
  ```
- **Production pattern:** Always include explicit rollback procedure; understand blast radius

### 9. Linked Decisions (Parent/Child, Related)
- **Why capture:** Trace decision trees; understand dependencies; avoid orphaned decisions
- **How to document:** YAML `related_decisions:` field with links and relationship type
- **Example:**
  ```yaml
  parent_decision: D042  # "Adopt service mesh architecture"
  children_decisions: [D088, D089, D090]  # "gRPC auth strategy", "service discovery config", etc.
  related_decisions:
    - D023: "API versioning contract" (informs gRPC API structure)
    - D055: "Observability stack" (shares tracing instrumentation)
  ```
- **Production pattern:** Use decision links to construct decision graph; enables brain-link and brain-why

### 10. Status (Active, Warm, Cold, Archived)
- **Why capture:** Know if decision still applies; signals to review or deprecate
- **How to document:** YAML `status:` field; update as decision ages or changes
- **Example:**
  ```yaml
  status: active  # In force until Dec 31, 2026
  review_date: 2026-06-15  # Quarterly review of gRPC adoption metrics
  deprecation_planned: 2027-01-01  # REST API fully sunset
  ```
- **Production pattern:** `active` (in force), `warm` (being phased out), `cold` (deprecated, kept for ref), `archived` (historical only)

### 11. Review & Approval Status
- **Why capture:** Governance trail; who signed off; when (for compliance/audit)
- **How to document:** YAML approval fields; update as reviews complete
- **Example:**
  ```yaml
  approval_status: approved
  approved_by: [VP Engineering (2025-11-16), Security Review Board (2025-11-18)]
  review_checklist:
    - security: passed
    - performance: passed (load test: 10k RPS gRPC vs 2k RPS REST)
    - backwards_compat: no breaking changes for 6 months
  ```
- **Production pattern:** Track who reviewed, when, and with what verdict; enables brain-recall "show me all decisions approved by <person>"

---

## Commit Message Patterns

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

---

## Metadata Frontmatter Template

Use this YAML frontmatter in decision records, specs, and contracts. Standardize field names to enable brain-recall, brain-link, and brain-why.

Valid decision `type` values:

| type | Use for |
|---|---|
| architecture | System structure, service boundaries, component topology |
| api | External/internal interface contracts and versioning choices |
| database | Schema, migration, indexing, and data-model decisions |
| infra | Deployment/runtime/platform choices (compute, network, ops) |
| process | Workflow/governance/pipeline decisions |
| decision | General decision record when none of the above is a precise fit |

```yaml
---
decision_id: D087
title: Adopt gRPC for Service-to-Service Communication
type: architecture
status: active  # active, warm, cold, archived
date: 2025-11-15
phase: scaling  # optional; omit if decision is evergreen
owner: platform-infra
decision_maker: Alice Chen (Principal Architect)
stakeholders: [backend-team, web-team, app-team, devops]
approved_by:
  - name: VP Engineering
    date: 2025-11-16
  - name: Principal Database Architect
    date: 2025-11-16
  - name: Security Review Board
    date: 2025-11-18
related_decisions:
  parent: D042  # "Adopt service mesh architecture"
  children: [D088, D089, D090]  # "gRPC auth", "service discovery", "tracing"
  related: [D023, D055]  # "API versioning", "Observability stack"
tags: [#api, #performance, #architecture, #scaling]
evidence:
  - type: load-test
    link: https://metrics.internal/reports/grpc-vs-rest-2025-11
    finding: gRPC 10x RPS improvement, p99 latency 50x reduction
  - type: incident
    link: "incident-2025-11-14"  # Link to learning in brain
    finding: REST polling exhausted connection pools; gRPC uses multiplexed streams
  - type: contract
    link: "contracts/grpc-service-definitions.proto"
    finding: All 47 services can express APIs in gRPC
review_date: 2026-06-15  # Quarterly review of adoption metrics
deprecation_planned: 2027-01-01  # REST API fully sunset
---
```

**Field definitions:**

| Field | Purpose | Example |
|-------|---------|---------|
| `decision_id` | Unique identifier for linking | D087 |
| `title` | One-line summary | "Adopt gRPC for Service-to-Service Communication" |
| `type` | Category for filtering | architecture, api, database, infra, process |
| `status` | Current state of decision | active, warm, cold, archived |
| `date` | ISO date when decided | 2025-11-15 |
| `phase` | Optional project/roadmap phase | scaling, launch, stability |
| `owner` | Team responsible for execution | platform-infra |
| `decision_maker` | Person/role who made final call | Alice Chen (Principal Architect) |
| `stakeholders` | Teams/people impacted | [backend-team, web-team, app-team] |
| `approved_by` | Formal sign-offs with dates | [{name: VP Eng, date: 2025-11-16}] |
| `related_decisions` | Links to parent/child/related | parent: D042, children: [D088, ...] |
| `tags` | Searchable tags for brain-recall | #api, #performance, #scaling |
| `evidence` | Links to proof (tests, metrics, incidents) | load-test: URL, incident: link |
| `review_date` | When to revisit this decision | 2026-06-15 (quarterly) |
| `deprecation_planned` | When to sunset if applicable | 2027-01-01 |

**Link conventions for decision graphs:**
```yaml
related_decisions:
  parent: D042                    # Single parent (this decision is a child of D042)
  children: [D088, D089, D090]    # Multiple children (D088, D089, D090 are children of this)
  related: [D023, D055]           # Sibling/peer decisions (influence but don't depend)
  supersedes: D040                # This decision replaces D040
  superseded_by: D100             # This decision was replaced by D100
```

**Tag structure** (use consistently):
- Infrastructure: `#infra`, `#kubernetes`, `#database`, `#cache`, `#messaging`
- API & Services: `#api`, `#grpc`, `#rest`, `#graphql`, `#service-mesh`
- Data & Scaling: `#performance`, `#scaling`, `#sharding`, `#replication`, `#caching`
- Process: `#process`, `#tooling`, `#testing`, `#deployment`, `#incident-response`
- Architecture: `#architecture`, `#design-pattern`, `#refactoring`, `#migration`

---

## Common Pitfalls

### Pitfall 1: Incomplete Commit Messages
**Problem:** Commit says "update spec" with no context. Future readers can't understand why.

**Example (BAD):**
```
git commit -m "spec: update shared dev spec"
```

**Example (GOOD):**
```
git commit -m "spec: lock shared dev spec for PRD-2025-11-streaming

Converged on: backend, web, app, infra
Contracts locked: gRPC v1 service definitions, PostgreSQL schema v3, Redis config
Key assumption: 100k RPS sustainable with 3 service instances per region
Next: Run tech-plan-write-per-project; unblocks implementation

Resolves: D087"
```

**How to avoid:** Always include: WHY (problem/goal), WHAT (what changed), CONTRACTS (what's locked), NEXT (what's unblocked)

---

### Pitfall 2: Missing Alternatives Section
**Problem:** Only document the chosen path. Future team re-litigates the same decision or doesn't understand constraints.

**Example (BAD):**
```markdown
# Decision
Use gRPC for service communication.
```

**Example (GOOD):**
```markdown
# Decision
Use gRPC for service communication (not REST polling, not Kafka, not WebSocket).

## Alternatives Considered
1. **REST with WebSocket upgrade** — Eliminates polling latency. Con: adds protocol complexity; web team would need 2x effort to maintain. Rejected due to dev velocity impact.
2. **Kafka for events** — Would decouple services. Con: wrong pattern for synchronous RPC; would add queuing latency (100ms+). Rejected as wrong tool.
3. **Status quo (REST polling)** — Existing, simple. Con: 2.5s p95 latency breaks real-time features; unacceptable. Rejected.
```

**How to avoid:** For each decision, spend 10 minutes brainstorming alternatives. Document all, explain why each was rejected. Spend as much time on the rejection reasoning as on the chosen path.

---

### Pitfall 3: No Evidence Links
**Problem:** Decision claims "this is better" without data. Auditor or skeptic has no way to verify.

**Example (BAD):**
```markdown
## Why
gRPC is much faster than REST and scales better.
```

**Example (GOOD):**
```markdown
## Why
Load test results (link: https://metrics.internal/reports/grpc-vs-rest-2025-11):
- REST polling: 2k RPS, p95 latency 2.5s, 100% connection pool exhaustion at peak
- gRPC streaming: 20k RPS, p99 latency 50ms, 12% CPU utilization at peak
- Incident analysis (link: incident-2025-11-14): Exactly 45-minute outage caused by connection pool exhaustion in REST polling feature; gRPC would have prevented via stream multiplexing

These results justify the 3-month migration cost.
```

**How to avoid:** Link to load test results, incident reports, metrics dashboards, code benchmarks. Every claim should be citable. Use `evidence:` section in frontmatter.

---

### Pitfall 4: Decisions Without IDs (Can't Reference Later)
**Problem:** Write decision as free-form markdown with no ID. Later, team can't say "let's re-check D087" because there's no D087.

**Example (BAD):**
File: `brain/decisions/gRPC-adoption.md` (no ID in filename or frontmatter)

**Example (GOOD):**
File: `brain/decisions/D087.md` (ID in filename)
```yaml
---
decision_id: D087
title: Adopt gRPC for Service-to-Service Communication
---
```

Later, in a PR comment: "This service needs to follow D087 (gRPC for service-to-service). See /why D087 for full context."

**How to avoid:** Always assign a sequential decision ID before committing. Use `decision_id:` in frontmatter. Reference the ID in commit messages and cross-links. Enable brain-why and brain-link to work.

---

### Pitfall 5: Stale Decisions Never Marked for Archival
**Problem:** Decision was valid in 2024, but situation changed in 2025. New team doesn't know to ignore it or update it. They waste time deciding whether to follow an obsolete decision.

**Example (BAD):**
```yaml
status: active  # Actually invalid since 2025-09 due to new SLA requirements
```

**Example (GOOD):**
```yaml
status: warm  # Being phased out; superseded by D095 (new SLA strategy)
superseded_by: D095
review_date: 2026-06-15  # Quarterly check on status
deprecation_planned: 2027-01-01  # Final sunset; still referenced in runbooks
```

Or, if decision is now archival (historical only):
```yaml
status: cold  # Kept for audit trail; design changed significantly in D095
superseded_by: D095
```

**How to avoid:** Set `review_date:` on every decision (quarterly, or sooner if known change is coming). Include `deprecation_planned:` if decision is time-bound. On review date, update status to `warm` (being phased out) or `cold` (superseded, keep for history). Let brain-forget handle final archival.

---

## Coordination with Other Brain Skills

### brain-write → brain-read
**What you write, others read.** brain-read queries the brain and returns decision records. Your job: write with clarity, using metadata and prose that brain-read can find and present.

- **Implication:** Structure every decision with consistent YAML frontmatter so brain-read can filter by `status:`, `type:`, `tags:`, `owner:`
- **Example:** brain-read query "show me all active infrastructure decisions" only works if you tagged your decisions with `type: infra` or similar
- **Best practice:** Include one-line description in every decision title; brain-read surfaces this for quick scanning

### brain-write → brain-recall
**What you write, others recall.** brain-recall uses hybrid search (grep + semantic) to find relevant past decisions.

- **Implication:** Write prose using concrete language, not jargon. Use consistent terminology across decisions
- **Example:** If you call it "gRPC" in D087 but "microservice RPC" in D089, brain-recall won't find the semantic link. Use consistent naming
- **Best practice:** In prose, explain technical terms on first use. Use `tags:` to cluster related decisions. Link related decisions using `related_decisions:` field

### brain-write → brain-why
**What you write, why walks it backward.** brain-why invokes `/why <commit-hash>` to return the full provenance tree (who, when, why, what decision).

- **Implication:** Write commit messages that answer "why did we do this?" Not just "what changed"
- **Example:** Commit message "spec: lock shared dev spec" is not enough. Use: "spec: lock shared dev spec for PRD-2025-11-streaming — converged on gRPC (resolves D087)"
- **Best practice:** Every commit message should include the decision ID or problem it solves. Link to parent decisions in frontmatter (`parent_decision:` field)

### brain-write → brain-link
**What you write, link connects semantically.** brain-link creates edges between decisions based on shared tags, parent/child, and cross-references.

- **Implication:** Use consistent `tags:` and explicit `related_decisions:` so brain-link has good signals
- **Example:** If you tag D087 (gRPC) with `#api` and `#performance`, brain-link can find other decisions tagged the same way and suggest connections
- **Best practice:** Every decision should have 3-5 tags from the standard set. Always fill in `related_decisions:` field (even if it's just `related: []`). Update links whenever you reference a related decision

### brain-write → brain-forget
**What you write, forget archivizes.** brain-forget scans for decisions with `status: cold` or `deprecation_planned:` in the past and moves them to archive.

- **Implication:** Set `status:` and `deprecation_planned:` on every decision; brain-forget can't act without these signals
- **Example:** If D040 (old API versioning strategy) was superseded by D087, set `status: cold` and `deprecation_planned: 2026-12-31`. brain-forget will surface D040 for archival when the date passes
- **Best practice:** Proactively mark decisions as `warm` or `cold` when you know they're being phased out. Include `superseded_by:` field. Make brain-forget's job easy by giving it clear signals

---

## Edge Cases

### Edge Case 1: File already exists (D001_feature.md exists)

**Symptom:** Decision file exists at target path; write would overwrite it.

**Do NOT:** Overwrite existing decision. Do NOT edit a locked decision directly.

**Mitigation:**
1. Check if decision is locked: `grep "status:" <existing-file.md> | grep "active\|warm"`
2. If locked, create NEW decision that supersedes it (set `superseded_by:` in new decision, `superseded_by:` in old)
3. If file is draft (status: draft), OK to update — but still prefer new decision for clear lineage
4. Use semantic ID pattern: D001 (original), D001_v2 (revision), or D002 (next decision)

**Escalation:** NEEDS_CONTEXT — Verify whether to overwrite (draft status) or supersede (active/locked status). Consult decision author if unsure.

---

### Edge Case 2: Brain not in git (lost version control)

**Symptom:** `git -C ~/forge/brain status` returns "not a git repository" or fails.

**Do NOT:** Write decision anyway (loses audit trail). Do NOT bypass git.

**Mitigation:**
1. Check git state: `cd ~/forge/brain && git status`
2. Verify remote: `git remote -v`
3. If .git missing, relink: `git clone <remote-url> ~/forge/brain`
4. If uncommitted changes exist: `git add . && git commit -m "WIP"`

**Escalation:** BLOCKED — Cannot write decision without git backing. Brain must be in git repository. Contact platform team to restore/reinitialize brain repo.

---

### Edge Case 3: Invalid frontmatter (missing required fields)

**Symptom:** Decision file lacks required YAML fields (decision_id, title, status, date, owner).

**Do NOT:** Write incomplete frontmatter. Do NOT assume defaults.

**Mitigation:**
1. Use template with all required fields (see "Metadata Frontmatter Template" above)
2. Validate frontmatter before commit: `head -30 <file> | grep -E "^decision_id:|^title:|^status:|^date:|^owner:"`
3. Use linter if available: `yamllint <file>` (checks YAML syntax)

**Escalation:** NEEDS_CONTEXT — Frontmatter incomplete. Verify all required fields before committing. Use provided template to ensure consistency.

---

### Edge Case 4: Concurrent write conflict (two people writing same decision)

**Symptom:** Git merge conflict on same decision file (both people edited D042.md).

**Do NOT:** Merge conflicted versions. Do NOT lose either person's changes.

**Mitigation:**
1. Resolve conflict manually: `git status` shows which files have conflicts
2. Review both versions: `git show :<version-number> <file>` to see both sides
3. Merge intelligently: Keep both versions' metadata, append one to "supersedes" or "related" field
4. If both added alternatives/evidence: Consolidate under single decision (not duplicate)
5. After merge: `git add <file> && git commit -m "resolve: merge concurrent edits to D042"`

**Escalation:** NEEDS_COORDINATION — Concurrent writes to same decision. Coordinate with other author to understand intent. Decide: merge into single decision or split into two related decisions (parent/child).

---

### Edge Case 5: Decision locked too early (stakeholders not consulted)

**Symptom:** Decision marked `status: active` but stakeholders report lack of input or alternative not considered.

**Do NOT:** Lock decision with hidden dissent. Do NOT ignore stakeholder objections.

**Mitigation:**
1. Check stakeholders field: `grep "stakeholders:" <file>`
2. If stakeholders missing or incomplete, set `status: draft` and re-circulate
3. Add approval_status field: confirm all stakeholders reviewed
4. Use decision review process: circulate to stakeholders before locking
5. If already locked: downgrade to `status: warm` with note "awaiting stakeholder review"

**Escalation:** NEEDS_COORDINATION — Decision locked without consensus. Downgrade status and re-circulate for review. Document any dissent in decision file (add dissent field with names/concerns).

---

## Decision Tree: Lock vs Draft Strategy

```
About to write a decision, should you lock it immediately?
    ↓
Are all stakeholders present and consulted?
├─ NO → Set `status: draft`; circulate for review before locking
└─ YES → Continue below

Have alternatives been evaluated and documented?
├─ NO → Set `status: draft`; return to evaluate alternatives
└─ YES → Continue below

Is this decision blocking downstream work?
├─ YES → Lock immediately (`status: active`); note deadline
└─ NO → Continue below

Is this a major architectural or API decision?
├─ YES → Lock only after council review (`status: active`); include council approval in frontmatter
└─ NO → Continue below

Is this a time-sensitive decision (hot fix, incident response)?
├─ YES → Lock immediately (`status: active`); document urgency and any shortcuts taken
└─ NO → Continue below

Is this a standard operational decision (deployment strategy, naming convention)?
├─ YES → Lock after team alignment (`status: active`)
└─ NO → Continue below

Result:
- If any answer suggests incompleteness: `status: draft` + circulate for input
- If all checks pass and stakeholders aligned: `status: active` + commit with context
- Milestone-based: lock when blocker is cleared, not when written
- Default: When in doubt, start as `status: draft` and upgrade after review
```

---

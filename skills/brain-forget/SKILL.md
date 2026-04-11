---
name: brain-forget
description: Archive deprecated decisions. Marks old decisions as cold/archived, never deletes. Demotion: warm→cold→archived. Searchable by status.
type: rigid
requires: [brain-read]
---

# brain-forget: Decision Archival System

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "This decision is wrong, I'll just delete it" | Deletion destroys audit trail. Demote to archived — wrong decisions teach as much as right ones. |
| "It's old, so it's irrelevant" | Age alone doesn't determine relevance. A 2-year-old API versioning decision may still be the canonical pattern. Check dependents before demoting. |
| "I'll archive everything from that product" | Bulk archival skips per-decision evaluation. Some decisions from a deprecated product may apply to active products. |
| "Archived decisions don't need commit messages" | Every status change needs a commit explaining why. "Cleaned up old decisions" is not a reason — state what changed and why. |
| "I'll demote it straight to archived" | The demotion lifecycle exists to catch premature archival. Active → Warm → Cold → Archived. Each step requires evidence. |

**If you are thinking any of the above, you are about to violate this skill.**

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **A decision file is being deleted instead of demoted** — Deletion destroys the audit trail permanently. STOP. No decision file is ever deleted. The minimum action is demotion to `archived` status with a commit explaining why.
- **A decision is being demoted from Active straight to Archived in one step** — Skipping the Warm and Cold stages bypasses the safeguards that catch premature archival. STOP. Each step in the lifecycle (Active → Warm → Cold → Archived) requires its own evidence and commit.
- **Bulk demotion is being applied to all decisions for a product** — Bulk operations skip per-decision evaluation and will incorrectly archive decisions that remain relevant across products. STOP. Every decision must be evaluated individually.
- **A demotion commit message says "cleaned up old decisions" or similar** — Uninformative commit messages make it impossible to audit why a decision was demoted. STOP. Each commit must state which decision changed status, from what status, to what status, and why.
- **Dependent decisions were not checked before demoting** — Demoting a foundational decision (e.g., an API versioning strategy) can orphan decisions that depend on it. STOP. Read all dependents via brain-read before demoting.
- **A demoted decision is being used to justify a current design** — Archived and cold decisions are not authoritative for new work. STOP. Only Active and Warm decisions can be cited as current guidance; cold/archived are historical record only.

Archive old or deprecated decisions without deletion. Implements a demotion lifecycle: **Active → Warm → Cold → Archived**. All decisions remain auditable and searchable by status.

## Decision Status Lifecycle

### Active
- Currently relevant and in active use
- Default status for newly recorded decisions
- Full visibility in search results
- Applies to decisions made within last 6 months

### Warm
- Still relevant but aging
- Status indicates decision is mature but not yet superseded
- Visible in search results (default)
- Transition trigger: 6 months of Active status OR new variant emerges

### Cold
- Deprecated or superseded
- No longer actively used but kept for historical reference
- Optional visibility in search (requires explicit include flag)
- May include reference to successor decision
- Transition trigger: 3+ months of Warm status OR explicit supersession marker

### Archived
- Historical record only
- Never deleted (maintains auditability)
- Hidden from default search results
- Can be unarchived if pattern resurfaces
- Transition trigger: 1+ year of Cold status OR explicit archival request

## Demotion Rules & Governance

The brain actively demotes decisions through five distinct rules, each with clear triggers, approval requirements, and communication protocols. A decision can be triggered by multiple rules; the earliest applies.

### Rule 1: Time-Based Demotion
**Trigger:** Natural aging period reached
- Active → Warm: 6 months of Active status
- Warm → Cold: 3 additional months (9 months total)
- Cold → Archived: 12 months of Cold status (24 months total)

**Who triggers:** Automated system (scheduled job), no human approval needed for time-based transitions

**Evidence required:**
- Decision creation date (status_date)
- Last status transition timestamp (status_since)
- Confirmation decision is still documented and referenced

**Dependent decisions:** Grandchildren (decisions that reference this one) remain Active. Parent demotion does not automatically demote children.

**Communication:**
- At Active→Warm: Team notified decision is entering maintenance mode (informational only)
- At Warm→Cold: Team notified decision is deprecated (recommend review)
- At Cold→Archived: Decision no longer surfaces in default search, archived log maintained

---

### Rule 2: Supersession Demotion
**Trigger:** New decision replaces old one
- When: Team explicitly marks decision as superseded by newer variant
- Example: D42 (path-based API versioning) → D89 (header-based versioning)

**Who triggers:** Decision author or team lead (explicit action required)

**Evidence required:**
- Link to successor decision (ID, title, relationship type)
- Brief explanation of why new decision is superior
- Optional: migration path or deprecation timeline for old approach

**Dependent decisions:**
- Decisions referencing old decision are NOT automatically updated
- Dependent teams notified to review and repoint references if needed
- Old decision marked with `successor: [ID]` field for easy lookup

**Communication:**
- Notification sent to all teams currently using old decision (via tags)
- Successor decision referenced prominently in old decision
- Deprecation timeline included (when old approach will no longer be supported)

**Example:**
```yaml
status: Cold
status_reason: superseded_by
successor: D89
successor_title: Header-Based API Versioning
deprecation_timeline: |
  - 2026-12-15: D89 published (this decision marked Cold)
  - 2027-03-15: Teams should begin migration
  - 2027-06-15: Support for D42 approach ends
migration_path: "See D89 for step-by-step migration guide"
```

---

### Rule 3: Validity Demotion
**Trigger:** Decision no longer applies due to changed context
- System constraints changed (migrated databases, deprecated framework)
- Product direction shifted (feature abandoned, market refocused)
- Assumptions no longer valid (client ecosystem evolved, regulation changed)

**Who triggers:** Domain expert or council member (approval required from decision stakeholder)

**Evidence required:**
- What changed? (specific constraint, assumption, or business fact)
- When did it change? (date, event, PR, announcement)
- Why is old decision invalid now? (technical, business, or regulatory reason)
- Is there a replacement decision? (link or mark as "orphaned")

**Dependent decisions:**
- Direct children (decisions built on this one) flagged for review
- Grandchildren inherit review flag transitively
- Each dependent must explicitly acknowledge the change or create new decision

**Communication:**
- Urgent notification to all decision dependents (this decision's children)
- Explanation of what changed and why decision is invalid
- Recommended action: create new decision or link to alternative

**Example:**
```yaml
status: Cold
status_reason: outdated
validity_trigger: System constraint changed
changed_context: |
  - 2026-08-01: Migrated from PostgreSQL to MySQL
  - Old decision assumed full JSONB support (PostgreSQL-specific feature)
  - MySQL JSON type lacks JSONB operators used in D42 implementation
  - Dependents should review and adapt if needed
dependents_flagged: [D67, D78, D91]
recommended_action: Review D67, D78, D91 for compatibility with new constraint
```

---

### Rule 4: Experimental Demotion
**Trigger:** Experiment concluded, pattern validated or rejected
- Experiment ended (trial period complete)
- Metrics reviewed and decision made to adopt, modify, or reject

**Who triggers:** Experiment owner or engineering lead (approval required)

**Evidence required:**
- Experiment dates (start, end)
- Key metrics or results (what did we measure?)
- Decision: Adopt? Modify? Reject?
- If adopted: graduation to permanent decision or merge with existing
- If rejected: lessons learned and why pattern doesn't work

**Dependent decisions:**
- Decisions that build on experimental approach inherit outcome
- If rejected: dependents must migrate to alternative or new decision
- If adopted: experimental label removed, decision promoted to Active

**Communication:**
- Notification to all experiment participants
- Results shared (metrics, findings, decision)
- If rejected: clear guidance on what to do instead
- If adopted: experimental tag removed, decision now permanent

**Example Rejection:**
```yaml
status: Cold
status_reason: experimental_end
experiment_dates: "2026-01-15 to 2026-06-15"
metrics: |
  - Client adoption: 2% (target was 15%)
  - Developer satisfaction: 3.2/5 (threshold: 4.0)
  - Support requests: 300+ issues (target: <50)
decision: Rejected pattern doesn't meet adoption threshold
lessons: |
  - Clients prefer existing approach (simpler, familiar)
  - Onboarding overhead too high for marginal benefit
  - Maintenance burden unsustainable at scale
alternative: Continue using D42 approach; revisit in 12 months if needs change
```

**Example Adoption:**
```yaml
status: Active (graduated from experimental)
status_reason: experimental_end
experiment_dates: "2026-01-15 to 2026-06-15"
metrics: |
  - Performance improvement: 35% (target 20%)
  - Developer adoption: 87% (target 80%)
  - Error rate reduction: 22%
decision: Adopted pattern exceeds all targets
official_date: 2026-06-20
transition_note: Graduated from experimental to official decision
```

---

### Rule 5: Governance Demotion
**Trigger:** Decision overturned or revoked by council
- Council reviews decision and determines it violates new policy
- Audit or compliance issue discovered
- Architecture decision contradicts principle decision
- Deprecated approach poses security or performance risk

**Who triggers:** Council member or architect (council approval required)

**Evidence required:**
- Council decision or vote log
- Why is decision revoked? (policy violation, security issue, new principle)
- Effective date of revocation
- Replacement decision or guidance (must exist)
- Impact analysis (which decisions/teams are affected)

**Dependent decisions:**
- All dependents must be reviewed and updated immediately
- Blocking status: dependents cannot reference revoked decision
- Migration timeline required for dependent decisions

**Communication:**
- Urgent notification to all affected teams
- Council letter explaining revocation and rationale
- Clear deadline for migrating away from revoked approach
- New decision provided as replacement

**Example:**
```yaml
status: Cold
status_reason: revoked
revocation_authority: Architecture Council
revoked_date: 2026-07-01
revocation_reason: Security issue in third-party library
revocation_details: |
  Library X (used in D42 approach) disclosed CVE with no patch available.
  Council voted unanimously to revoke D42 pending resolution.
  Until resolved: no new codebases should adopt D42 pattern.
  Existing implementations must migrate to D89 by 2026-09-01.
affected_teams: [TeamA, TeamB, TeamC]
migration_deadline: 2026-09-01
replacement_decision: D89
council_letter: "[link to council decision document]"
```

---

## Demotion Decision Tree

```
Decision marked for demotion
    ↓
Is it time-based aging (6mo Active, 3mo Warm, 12mo Cold)?
├─ YES → Apply Rule 1 (automated, no approval)
└─ NO → Continue below

Is it being replaced by a newer decision?
├─ YES → Apply Rule 2 (team lead approval)
└─ NO → Continue below

Did the system context change (constraints, product, environment)?
├─ YES → Apply Rule 3 (domain expert approval + dependents flagged)
└─ NO → Continue below

Is this an experiment that concluded?
├─ YES → Apply Rule 4 (experiment owner approval)
└─ NO → Continue below

Was this decision formally revoked by council?
├─ YES → Apply Rule 5 (council authority + urgent migration)
└─ NO → Decision remains Active (no demotion rule triggered)
```

## Evergreen Classification

Evergreen decisions are foundational principles or patterns that stand the test of time and should never be archived. They represent organizational wisdom, core architecture principles, stable contracts, and validated lessons that transcend individual projects or time periods.

### Evergreen Decision Patterns

#### 1. Evergreen Pattern
**Definition:** "This approach works for ALL projects and ALL contexts"

**Characteristics:**
- Applies universally across product, technical platform, and team boundaries
- No known edge cases or exclusions
- Proven over multiple major product cycles (2+ years minimum)
- Reduces to a simple, repeatable process

**How to identify:**
- Ask: "Could any team on any project ignore this and be okay?" Answer should be "No"
- Check: Multiple independent teams have adopted and found value
- Validate: Pattern has been stress-tested in diverse contexts
- Test: Decision applies to projects 5+ years in the future

**How to mark:**
```yaml
status: Active
evergreen: true
evergreen_type: pattern
evergreen_since: 2024-01-15
pattern_scope: "All projects, all teams, all contexts"
```

**Search and maintenance:**
```
# Find all evergreen patterns
brain-read tag:* evergreen:true evergreen_type:pattern

# Periodic validation (annually)
Review all evergreen patterns to ensure still universal
Check for any new edge cases discovered
Update timestamp if revalidated
```

**Examples:**
- "Code review approval required before merge" (universal quality gate)
- "API versioning deprecation period: 12 months" (cross-team consistency)
- "Security: never commit credentials, use secret manager" (non-negotiable)

---

#### 2. Evergreen Decision (Architecture Principle)
**Definition:** "Core tenet of our architecture that defines who we are"

**Characteristics:**
- Expresses fundamental principle about system design
- Typically immutable or changes only when company pivots
- Defines constraints on all systems built within organization
- Often appears in multiple decisions as parent/reference

**How to identify:**
- Ask: "Would changing this require fundamentally restructuring the company?"
- Check: Decision appears in many other decisions as a prerequisite
- Validate: Principle has been maintained across major product rewrites
- Test: New decisions regularly reference this one positively

**How to mark:**
```yaml
status: Active
evergreen: true
evergreen_type: architecture
evergreen_since: 2022-06-01
architectural_principle: "Always prioritize customer data privacy over feature velocity"
enforcement: "All systems must implement end-to-end encryption by default"
```

**Search and maintenance:**
```
# Find all architecture principles
brain-read tag:* evergreen:true evergreen_type:architecture

# Annual architecture review
Review all architectural principles
Assess if new product directions require updates
Solicit feedback from senior engineers
Update guidance based on lessons from past year
```

**Examples:**
- "Always use CI/CD for all production deployments" (non-negotiable operational principle)
- "Database-agnostic abstractions for core business logic" (flexibility principle)
- "Customer data never leaves data residency region" (compliance principle)

---

#### 3. Evergreen Contract
**Definition:** "Stable, long-lived interface that won't change"

**Characteristics:**
- Defines stable contracts (APIs, event schemas, database interfaces)
- Multiple systems depend on stability of this contract
- Changes would require coordinated migration of dependent systems
- Rarely updated but when changed, requires major coordination

**How to identify:**
- Ask: "How many systems would break if this contract changed?"
- Check: Contract is referenced in multiple dependent decisions
- Validate: Contract has been stable for multiple major releases
- Test: New dependent systems can adopt this contract without version pinning

**How to mark:**
```yaml
status: Active
evergreen: true
evergreen_type: contract
evergreen_since: 2023-03-15
contract_stability: "Breaking changes require 6-month deprecation period and council approval"
dependent_systems: [PaymentService, InventoryService, NotificationService]
versioning_strategy: "Additive changes only; removals require deprecation cycle"
```

**Search and maintenance:**
```
# Find all stable contracts
brain-read tag:api evergreen:true evergreen_type:contract

# Quarterly contract review
Audit all evergreen contracts for backward compatibility
Check for any dependent system failures or incompatibilities
Plan deprecation cycles for any necessary breaking changes
Communicate timeline to all dependent teams
```

**Examples:**
- "REST API contract for order service: v3 stable, v2 deprecated, v1 sunset" (API contract)
- "Kafka event schema for payment events: must be backward compatible" (event contract)
- "Database schema for customer table: primary keys never change, only additive columns" (schema contract)

---

#### 4. Evergreen Lesson (Validated Learning)
**Definition:** "Hard-won insight that shaped how we build systems; worth remembering forever"

**Characteristics:**
- Documents a significant problem we solved and why the solution matters
- Captures reasoning that explains current decisions
- Prevents reinventing the wheel or repeating past mistakes
- Valuable even if specific technical decision becomes outdated

**How to identify:**
- Ask: "If we lost this knowledge, what expensive mistake would we repeat?"
- Check: Lesson is referenced as justification in multiple other decisions
- Validate: Lesson has been consistently applied over multiple product cycles
- Test: Lesson remains valuable even if we rebuild the system differently

**How to mark:**
```yaml
status: Active
evergreen: true
evergreen_type: lesson
evergreen_since: 2021-09-10
lesson_category: "Database selection rationale"
lesson_title: "Why we chose MySQL for financial transactions"
lesson_value: "Prevents pressure to switch databases in pursuit of cool tech"
```

**Search and maintenance:**
```
# Find all evergreen lessons
brain-read tag:* evergreen:true evergreen_type:lesson

# Lessons review (biannually)
Review all evergreen lessons for continued validity
Update context if new information discovered
Add new lessons from major learnings or incidents
Ensure lessons are accessible and discoverable
```

**Examples:**

**Evergreen Lesson Example 1: Database Selection**
```yaml
id: D15
title: "Why MySQL for Financial Transactions"
status: Active
evergreen: true
evergreen_type: lesson
evergreen_since: 2021-09-10

## The Problem
Early on, we explored NoSQL for transaction logs. Benchmarks looked good. 
Pressure from engineering to use trendy tech was high.

## What We Chose and Why
MySQL with InnoDB: Full ACID compliance, proven at scale, simple operations.

## The Lesson
Never optimize for engineering trendsiness when data integrity is on the line.
ACID guarantees prevented 47 data inconsistency bugs that would have been 
invisible in eventual-consistency systems. Cost of fixing one incident: $300K+.

## Why This Remains Evergreen
The reasoning—data integrity > cool technology—transcends database choices.
Even if we eventually use different database, this principle remains.
Prevents repeating "why did we choose the cool tech" mistakes in future.

## When This Lesson Is Relevant
- Any discussion of changing financial transaction storage
- Tech selection for any critical business data
- Evaluating new databases or frameworks
- When pressure mounts to adopt trendy technology

## What NOT to Infer
This is NOT "never use NoSQL" (we use it for logs, caching, analytics).
This IS "think carefully about data integrity requirements first".
```

**Evergreen Lesson Example 2: Team Scaling**
```yaml
id: D28
title: "Why Microservices Didn't Scale Our Org"
status: Active
evergreen: true
evergreen_type: lesson
evergreen_since: 2020-06-15

## The Problem
With 15 engineers, we split into microservices to "scale better".
Expected: independent team deployment, faster iteration.
Reality: coordination overhead, cross-service debugging nightmare, 12 months to stable.

## What We Learned
Microservices scale teams, not monoliths. We had one team with unclear boundaries.
Should have scaled team structure first, then services to match org structure.

## The Lesson
Organization structure determines system architecture, not vice versa.
Conway's Law: System design mirrors communication structure of org that built it.
Reverse-engineering architecture to make teams autonomous doesn't work.

## Why This Remains Evergreen
True regardless of tech stack or company size.
Valid at 5 people and 500 people.
Prevents repeating expensive architecture mistakes.

## When This Lesson Is Relevant
- Any architectural redesign proposal
- Decisions about microservices, modular monolith, or monolith
- Team restructuring discussions
- When teams request architectural changes to improve independence
```

When transitioning a decision to Cold or Archived status, capture:

### Required Fields
- **Status:** Current lifecycle state (Active/Warm/Cold/Archived)
- **Status Transition Date:** When status changed
- **Reason:** Why transition occurred
  - `age`: Natural aging period reached
  - `superseded_by`: Explicit replacement (provide decision ID)
  - `outdated`: No longer applicable
  - `experimental_end`: Experiment concluded
  - `request`: Explicit archival request

### Optional Fields
- **Successor Decision ID:** References replacement decision (e.g., D89)
- **Lessons Learned:** Key insights from this approach
- **Context:** Why this decision is no longer used
- **Reactivation Criteria:** Conditions under which this decision might be relevant again

## Common Pitfalls

These pitfalls represent common mistakes in decision archival that undermine the brain's long-term value.

### Pitfall 1: Archive Without Documenting Why

**The mistake:**
Decision marked Archived with minimal context. Status changed, timestamp recorded, but lessons and reasoning lost.

**Consequences:**
- Future team asks "Why was this approach abandoned?" and gets no answer
- Same problem solved twice because institutional knowledge disappeared
- Expensive mistakes repeated because reasoning not preserved
- Audit trail incomplete (shows when archived, not why)

**Prevention:**
- Always complete lessons_learned section before archival
- Document what was tried, what worked/didn't work, what we'd do differently
- Include context: constraints that made original decision correct, constraints that changed
- Add recovery_criteria: when would we consider reverting to this approach?

**Example (WRONG):**
```yaml
status: Archived
archived_date: 2027-01-15
# No context! Future team confused.
```

**Example (RIGHT):**
```yaml
status: Archived
archived_date: 2027-01-15
archived_reason: "Time-based (24 months) + no dependents"

lessons_learned: |
  What worked:
  - Event-sourced audit trail was rock-solid, no data inconsistencies
  - Debugging production issues easier with full event history
  
  What didn't work:
  - Event store grew to 50GB/year (unsustainable for small teams)
  - Reconstruction queries slow on full history (analytical queries suffered)
  - Operational complexity high (rebalancing partitions took days)
  
  Why we changed:
  D156 (incremental snapshots) provides 95% of benefits with 5% of cost.
  Lessons from D42 informed design of D156.
  
  When to revisit D42:
  - If querying historical data becomes critical (archival/compliance)
  - If operational costs justify engineering investment
  - If we need unforgeable audit trail for regulatory reasons
```

---

### Pitfall 2: Active Decision That Should Be Archived

**The mistake:**
Decision remains marked Active years after becoming obsolete. No one updated status because no formal archival process existed.

**Consequences:**
- Stale guidance clutters decision landscape
- New team members follow outdated approach
- Massive divergence: some projects use old decision, some use new successor
- Brain becomes unreliable source of truth
- Search results polluted with irrelevant active decisions

**Prevention:**
- Set up automated archival workflow (age + dependents)
- Quarterly review: ask domain experts "Is this still guidance we want active?"
- Regular searches for unmaintained decisions (last update >18 months ago)
- Retire status updates: decisions with no updates for 12+ months should get attention

**Detection query:**
```
# Find all Active decisions with no updates in past 18 months
brain-read status:active updated_before:2025-10-10

# Find Cold decisions older than 12 months (should consider archival)
brain-read status:cold age_cold_months>12
```

**Example (WRONG - D42 still Active):**
```yaml
id: D42
title: "Graduated API Versioning"
status: Active              # WRONG! Been superseded for 2+ years!
date_created: 2024-11-15
last_updated: 2024-11-20
```

**Example (RIGHT - D42 properly demoted):**
```yaml
id: D42
title: "Graduated API Versioning"
status: Archived
date_created: 2024-11-15
last_updated: 2027-01-15  # When archived, not when created
demotion_timeline: |
  2024-11-15: Active (created)
  2025-05-15: Warm (6 months aging)
  2025-08-15: Cold (superseded by D89)
  2027-01-15: Archived (12+ months cold, no dependents)
```

---

### Pitfall 3: Evergreen Decision Archived by Mistake

**The mistake:**
Decision marked as evergreen but then archived without escalating to council. Institutional wisdom lost, dependent decisions broken.

**Consequences:**
- Architectural principle disappears from active guidance
- New team members don't know about foundational decision
- Dependent decisions orphaned (reference is gone or archived)
- Expensive to recover: requires unarchival + council review
- Damages trust in decision system (important decisions can vanish)

**Prevention:**
- Tag all evergreen decisions early: `evergreen: true` at decision creation
- Automatic safety gate: cannot archive decision with `evergreen: true` without council override
- Annual evergreen review: audit all evergreen decisions, ensure still valid
- High visibility: mark evergreen decisions prominently in search results

**Safety gate implementation:**
```
# System rule: Cannot archive evergreen decision
if status_change == "to Archived" and decision.evergreen == true:
    REJECT with message: "Cannot archive evergreen decision. 
              Escalate to Architecture Council for review."
```

**Example (WRONG - evergreen archived):**
```yaml
id: D15
title: "Why MySQL for Financial Transactions"
status: Archived              # WRONG! This is evergreen!
evergreen: true               # Conflicting tags!
# Decision lost, but archival happened anyway.
```

**Example (RIGHT - evergreen protected):**
```yaml
id: D15
title: "Why MySQL for Financial Transactions"
status: Active                # Protected, won't be archived
evergreen: true
evergreen_type: lesson
evergreen_since: 2021-09-10
archival_protection: "Cannot archive without council approval"
```

---

### Pitfall 4: No Recovery Path

**The mistake:**
Decision archived without documenting when/how it might be relevant again. If pattern resurfaces, decision is lost.

**Consequences:**
- Team solves old problem again, not knowing solution was already tried
- Expensive duplicated work and engineering effort wasted
- Pattern archived without recovery criteria
- Can't reactivate because context is lost
- Brain becomes unreliable for historical patterns

**Prevention:**
- Always include recovery_criteria in archival metadata
- Document: "Under what circumstances would we consider this again?"
- Keep recovery path in search index (archived decisions discoverable by recovery scenario)
- Teach teams to search archived decisions when facing novel problems

**Recovery criteria checklist:**
```
When documenting archival, answer:
[ ] What problem did this decision solve?
[ ] Under what system constraints was it valid?
[ ] What changed that made it invalid?
[ ] What would have to be true to make it valid again?
[ ] How would future team recognize this scenario?
```

**Example (WRONG - no recovery path):**
```yaml
status: Archived
archived_date: 2027-01-15
reason: "Superseded by D89"
# No recovery criteria! If D89 fails, we're stuck.
```

**Example (RIGHT - recovery documented):**
```yaml
status: Archived
archived_date: 2027-01-15
reason: "Superseded by D89"

recovery_criteria: |
  D42 would be relevant again if:
  - D89 (header-based versioning) proves unmaintainable (e.g., proxy incompatibilities)
  - External mandate requires URL-based versioning for SEO or analytics
  - Client ecosystem shifts back to prefer path-based versioning
  - New product line has same constraints as 2024 when D42 was created
  
recovery_process: |
  1. If recovery scenario triggered: contact architecture team
  2. Retrieve D42 from archive + full lessons learned
  3. Assess if context still matches (it should, or D42 won't be valid)
  4. If match: unarchive, promote to Active
  5. If no match: use D42 as inspiration for new decision
```

---

### Pitfall 5: Demotion Without Team Communication

**The mistake:**
Decision demoted (Active→Warm, Warm→Cold) without notifying affected teams. Teams unaware guidance has changed status.

**Consequences:**
- Teams follow guidance they don't realize is deprecated
- No one prepares for future archival
- When decision finally archived, teams surprised and frustrated
- Adoption of successor decision delayed (team learning curve)
- Trust in decision system damaged (why weren't we told?)

**Prevention:**
- Notification gate: before demotion happens, notify all teams tagged with decision
- Clear messaging: what status change means, what team should do
- Provide timeline: when next status change is expected
- Link to successor: if available, point to new guidance
- Allow feedback: teams can request reconsideration

**Communication template:**
```
Subject: NOTICE - Decision [ID] Status Change to [NEW_STATUS]

Team,

Decision [TITLE] status is being changed to [NEW_STATUS] effective [DATE].

What this means:
[Explain new status and implications]

Your action items:
- Review current usage of this decision
- If applicable, plan migration to successor decision
- Update internal documentation if you've built on this approach

Next steps:
- [NEW_STATUS] is expected to remain for [DURATION] before [NEXT_STATUS]
- Questions or concerns? Contact [DOMAIN_EXPERT]

Timeline:
[CREATED] → Active
[DATE1] → Warm (this change)
[DATE2] → Cold (expected)
[DATE3] → Archived (expected, unless circumstances change)

Successor decision:
If applicable, see [SUCCESSOR_ID] for recommended approach.
```

---

## Automation & Governance

Demotion and archival work at scale when automated. Decision lifecycle automation prevents stale decisions and maintains system integrity.

### Automated Demotion Criteria

**Time-based automation (no human approval needed):**
```
# Daily job: Check all Active decisions
for decision in decisions with status=Active:
  if (now - decision.created_date) > 6 months:
    decision.status = Warm
    decision.status_since = now
    decision.status_reason = age
    notify_teams(decision.tags)  # Informational only

# Weekly job: Check all Warm decisions
for decision in decisions with status=Warm:
  if (now - decision.status_since) > 3 months:
    decision.status = Cold
    decision.status_since = now
    decision.status_reason = age
    notify_teams(decision.tags)  # Recommend review

# Monthly job: Check all Cold decisions
for decision in decisions with status=Cold:
  if (now - decision.status_since) > 12 months and not decision.evergreen:
    decision.status = Archived
    decision.archived_date = now
    decision.archived_by = system
    decision.archived_reason = age
    log_archival(decision)  # Audit trail
```

**Event-based automation (requires human approval):**
```
# User marks decision as superseded
if decision.status_change_request == superseded_by:
  requires_approval: domain_expert
  approval_gate: "Link to successor decision"
  notification: teams_using_this_decision
  
# Domain expert approves validity demotion
if decision.status_change_request == outdated:
  requires_approval: domain_expert + decision_stakeholder
  approval_gate: "Evidence of changed context"
  notification: dependent_decisions_flagged_for_review
  
# Council revokes decision
if decision.revocation_request:
  requires_approval: council_vote
  approval_gate: "Council decision log"
  notification: urgent_to_all_dependents
  migration_deadline: 30_days
```

---

### Review & Approval Process

**Automated review (no approval required):**
- Time-based demotion: automatic when age threshold reached
- Archival of decisions with no dependents: automatic after Cold period
- No communication required (informational notifications only)

**Manual review (approval required):**
- Supersession: Domain expert reviews, approves link to successor
- Validity demotion: Stakeholder confirms context change is real
- Experimental outcome: Experiment owner confirms metrics and conclusion
- Governance revocation: Council votes and documents decision

**Approval workflow:**
```
1. Decision owner initiates demotion request
2. System checks: can this be automated or requires approval?
3. If automated: execute immediately, notify teams
4. If manual: route to approver based on demotion type
5. Approver reviews: evidence provided? impact assessed? teams notified?
6. Approver decision: approve, request more info, or reject
7. If approved: execute status change, log decision, archive if needed
8. If rejected: return to decision owner with feedback
```

---

### Notification Strategy

**Notification matrix:**

| Status Change | Who's Notified | Message Type | Urgency |
|--------------|---------------|--------------|---------|
| Active→Warm | Teams with tag | "Your decision is entering maintenance mode" | Low |
| Warm→Cold | Teams with tag | "Recommend reviewing this decision and its successors" | Medium |
| Cold→Archived | Teams with tag + dependents | "This decision is moving to archive; no impact if you've migrated" | Low |
| Supersession | Direct dependents | "Your decision has been superseded; plan migration" | Medium |
| Validity change | Dependent decisions | "Context changed; review this decision's validity" | High |
| Experimental end | Experiment participants | "Results analyzed; decision on adoption/rejection" | High |
| Governance revoked | All dependents | "Council has revoked this decision; urgent migration required" | Critical |

**Notification content rules:**
- Always include: what changed, why, deadline for action
- Include links: to new decision, migration guide, contact person
- Be specific: which teams, which decisions, which systems
- Provide context: why this demotion matters, what they should do
- Offer help: escalation path, expert contact, Q&A forum

---

### Analytics & Monitoring

**Track demotion pipeline health:**
```
# Weekly dashboard
- Active decisions: [count]
- Warm decisions: [count]
- Cold decisions: [count]
- Archived decisions: [count]
- Evergreen decisions: [count]

# Demotion velocity
- Decisions demoted this week: [count]
- Decisions archived this month: [count]
- Average decision lifecycle: [duration]
- Decisions with no dependents (ready for archival): [count]

# Health metrics
- Decisions with complete lessons learned: [%]
- Decisions with recovery criteria documented: [%]
- Decisions with no updates in 18+ months: [count] (action needed?)
- Evergreen decisions audited in past 12 months: [%]

# Archival effectiveness
- Decisions recovered from archive (last 12 months): [count]
- Recovery rate (archived that became active again): [%]
- False positives (decisions should have stayed active): [count]
```

**Red flags that indicate process breakdown:**
- Decisions remaining Active >3 years (should demote or mark evergreen)
- Warm/Cold decisions with 100+ dependents (archival blocked)
- Evergreen decisions never reviewed (could be mistaken)
- Archival happening without notification (teams surprised)
- Active decisions with no lesson learning section (documenting failure)
- Recovery attempts finding no archived decision (archival too aggressive)

---

### Governance Council Responsibilities

**Architecture Council's role in lifecycle management:**

1. **Quarterly evergreen audit:** Review all `evergreen: true` decisions
   - Still universally applicable?
   - Still worth keeping in active guidance?
   - Lessons still valid? Context changed?
   - Recommend: keep active, revalidate, or demote

2. **Monthly archival review:** Approve archival of decisions ready for archive
   - Ensure no forgotten dependents exist
   - Verify lessons are complete
   - Check recovery criteria are documented
   - Approve or request more context

3. **Incident response:** When decision revocation needed
   - Analyze issue requiring decision revocation
   - Vote to revoke + document rationale
   - Identify all affected teams/systems
   - Set migration deadline (typically 30 days)
   - Track migration progress to completion

4. **Annual brain health:** Full decision landscape audit
   - Total decisions (all statuses)
   - Health by domain (which areas have stale guidance?)
   - Lessons learned collection (capturing wisdom?)
   - Recovery effectiveness (is archival working?)
   - Recommendations for next year

### Default Search Behavior
- Includes: Active and Warm decisions
- Excludes: Cold and Archived decisions
- Rationale: Users typically want current guidance

### Extended Search
- Flag: `include_cold=true` includes Cold decisions
- Flag: `include_archived=true` includes Archived decisions
- Flag: `include_all=true` includes all statuses
- Use case: Historical research, pattern analysis, retroactive learning

### Status Filtering
```
search status:active              # Only currently relevant decisions
search status:warm                # Aging decisions, still in use
search status:cold                # Deprecated decisions
search status:archived            # Historical archive
search status:"cold|archived"     # Historical research
search status:"*"                 # All decisions (all statuses)
```

### Tag-Based Filtering
- Combine status with topic tags: `search tag:api-versioning status:cold`
- Find all decisions on a topic, including deprecated approaches
- Example: `tag:cache-strategy status:*` shows cache decisions across time

## Archive & Recovery Workflow

Archival is not destruction. The brain maintains full auditability of all decisions, even archived ones. Recovery processes restore archived decisions when their patterns become relevant again.

### Phase 1: Identify Candidates for Archival

**Automated identification:**
- Run scheduled job: find all Cold decisions with 12+ months Cold status
- Check evergreen tag: exclude all decisions marked `evergreen: true`
- Generate archival report: [decision_id, age, last_reference_date, dependent_count]

**Manual identification:**
- Domain experts review Cold decisions in their area (quarterly)
- Ask: "Is this decision still occasionally referenced?" If no, candidate for archival
- Check: Has any dependent updated their reference in the last 6 months? If no, consider archival
- Consider: Could this pattern become relevant again? If unlikely, safe to archive

**Decision classification:**
```yaml
# Example candidates report
archival_candidates:
  - id: D42
    title: "Graduated API Versioning"
    status: Cold
    age_cold: 14 months
    dependent_count: 0
    last_referenced: 2026-08-15
    candidate_reason: "Superseded by D89, no dependents, not referenced in 9 months"
    evergreen: false
    recommendation: SAFE_TO_ARCHIVE

  - id: D15
    title: "MySQL for Financial Transactions"
    status: Cold
    age_cold: 2 years
    dependent_count: 12
    last_referenced: 2026-10-10
    candidate_reason: "Actively referenced in architecture decisions"
    evergreen: false
    recommendation: KEEP_ACTIVE # Still provides architectural wisdom
```

---

### Phase 2: Review & Approve Archival

**Who reviews:** Domain expert + stakeholders from dependent teams (if any)

**Review questions:**
1. Is this decision truly outdated? (not just superseded, but actually invalid)
2. Does anyone still reference this? (check logs, grep code)
3. Are there dependent decisions that would be orphaned? (flag for update)
4. Should this be marked evergreen instead? (is wisdom worth keeping active?)
5. Is there sufficient context in lessons learned section? (future researchers need to understand)

**Approval workflow:**
- If no dependents: domain expert alone can approve
- If active dependents: dependent team lead must agree archival is safe
- If evergreen candidate: escalate to architecture council
- Document approval: who approved, when, why

**Review checklist:**
```
[ ] Decision is genuinely outdated (not just superseded)
[ ] No active dependents (or dependents have migrated)
[ ] Lessons learned section is complete
[ ] Context preserved for potential future recovery
[ ] Not marked as evergreen (double-checked)
[ ] Dependent teams (if any) notified and approved
[ ] Archival reason clearly documented
[ ] Recovery criteria documented (if relevant)
```

---

### Phase 3: Mark & Archive

**Update decision record:**
```yaml
status: Archived
archived_date: 2026-11-15
archived_by: eng-lead-team@company.com
archived_reason: "Time-based (24 months total) + no active dependents"

archival_context: |
  D42 documented the API versioning approach for 2023-2026.
  Superseded by D89 (header-based versioning) as of Dec 2025.
  Last dependent migrated off in Aug 2026.
  No new codebases expected to reference this decision.

recovery_scenarios: |
  Could revisit if:
  - New product line requires backward-compatible API versioning
  - Client ecosystem strongly prefers path-based versioning
  - Regulatory requirements need URL-based API versioning (audit trail)

lessons_preserved: |
  - Path-based versioning: works for 6+ months
  - Client migration slower than expected (assume 18mo, not 12mo)
  - URL pollution problem: each version doubles URL surface area
  - Deprecation strategy: must communicate timeline clearly
  - See D89 for lessons from header-based approach
```

**System actions:**
- Move decision to archive storage (separate from active/warm/cold)
- Index: decision still searchable by ID, title, tags
- Visibility: excluded from default searches (require `include_archived=true`)
- Audit: decision immutable (can read, cannot edit—archival is permanent)

---

### Phase 4: Communicate Archival

**Who to notify:**
- All teams tagged with this decision (via brain-read tags)
- All dependent decision owners (direct children)
- Decision stakeholders from implementation

**What to communicate:**
- **Archival letter:** Why this decision was archived, effective date
- **Successor:** If available, link to replacement decision
- **Action items:** If dependents exist, what teams need to do
- **Recovery possibility:** Under what circumstances this might be unarchived

**Communication template:**
```
Subject: Decision D42 Archived - "Graduated API Versioning"

Team,

Decision D42 has been archived effective 2026-11-15 as a result of:
- 24-month lifecycle completion (decision made 2024-11-15)
- Supersession by D89 "Header-Based API Versioning" (adopted Dec 2025)
- No active dependents (last migration completed Aug 2026)

Why archived:
The graduated API versioning approach has been proven and documented.
Newer approach (D89) provides benefits of path-based clarity with reduced
URL pollution. Moving to archive makes room in "active decisions" for
new guidance without losing historical context.

What you should do:
- If currently using D42 approach: migrate to D89 (see migration guide)
- If decision references D42: update reference to point to D89
- No action needed if you've already migrated

Recovery possibility:
Archived decisions can be unarchived if circumstances change. Contact
architecture team if you have use case that requires D42 approach.

Questions? See D42 "Lessons Learned" section or contact eng-lead@company.com

Best,
Architecture Team
```

---

### Recovery Workflow

Recovery happens when an archived decision becomes relevant again. Three recovery paths exist:

#### Recovery Path 1: Full Reactivation
**When:** Exact circumstances match archived decision pattern
**Process:**
1. Locate archived decision (search by tag, title, context)
2. Read archived decision + lessons learned
3. Verify context matches (same constraints, same problem)
4. Decide: reactivate or create new decision?
5. If reactivating: restore to Active status, add note, clear archived flag
6. If creating new: create new decision, link to archived as prior art

**Example:**
```yaml
Decision: D42 "Graduated API Versioning"
Original: Archived 2026-11-15
Reactivation: 2027-03-10

Reason for recovery: New product platform needs API versioning.
Architecture matches original D42 constraints: greenfield system,
external clients, need to deprecate versions gradually.

Decision: REACTIVATE D42 (same approach, proven to work)

Updated record:
status: Active (reactivated)
reactivated_date: 2027-03-10
reactivated_from: Archived
reactivation_reason: "New product platform matches original D42 constraints"
prior_context: "See archived metadata for lessons from 2023-2026 implementation"
cross_reference: "See D89 for alternative approach (header-based)"
```

#### Recovery Path 2: Partial Recovery
**When:** Some aspects of archived decision remain valid, but not all
**Process:**
1. Identify which parts of archived decision still apply
2. Create NEW decision inheriting valid parts
3. Link new decision to archived as derivative/inspiration
4. Explain why not all aspects were recovered

**Example:**
```yaml
Decision: D125 "Modified Graduated API Versioning"
Inspired by: D42 (archived)
Date: 2027-03-10

Context:
D42 documented graduated API versioning with 12-month deprecation window.
For new platform, constraints changed: smaller client base, shorter product cycle.

What we're adopting from D42:
- Graduated deprecation strategy (keep multiple versions in parallel)
- Deprecation timeline communication (clear deadline for migration)

What we're changing from D42:
- Timeline: 6 months deprecation (vs 12 months in D42)
- Versioning: header-based (vs URL path in D42, see D89)
- Client population: internal-only (vs external in D42)

Why not just reactivate D42:
Different constraints make D42 timeline too long and approach too heavy.
D42 was valuable for learning; adapting lessons to new context.
```

#### Recovery Path 3: Learning Recovery
**When:** Decision is obsolete as guidance, but lessons are valuable
**Process:**
1. Keep decision Archived (don't reactivate)
2. Extract lessons learned section
3. Create decision documenting lesson without reactivating old approach
4. Link back to archived decision as source of learning

**Example:**
```yaml
Decision: D126 "Why Graduated Deprecation Works"
Lesson from: D42 (archived), D89 (active)
Date: 2027-03-10

Thesis:
Graduated deprecation—keeping multiple versions in parallel and
phasing out old versions over time—is robust pattern across APIs,
frameworks, and product designs.

Evidence from our experience:
- D42 (2024): Tried graduated deprecation with URL-based API versioning
  Result: Worked, but slower adoption than expected
  Timeline: 18 months (not 12), high operational cost

- D89 (2025): Adopted graduated deprecation with header versioning
  Result: Faster adoption, lower operational cost
  Timeline: 12 months achieved, good client compliance

Lessons:
1. Graduated deprecation is robust across different versioning approaches
2. Timeline depends on client population (internal vs external)
3. Clear deprecation communication is essential
4. Total operational cost includes backward compatibility, not just timeline

When to apply:
Any API or interface with external consumers who can't upgrade instantly.
Best for platforms with heterogeneous client base.

When NOT to apply:
Internal-only APIs (hard cutover better); clients already distributed
(rolling deployment better); small client base (negotiate directly).

Reference decisions:
- D42: Original approach with URL-based versioning (Archived)
- D89: Current approach with header-based versioning (Active)
```

### Reactivation Workflow
When an archived pattern becomes relevant again:

1. **Detect Need:** New requirement matches archived decision
2. **Review Context:** Read archived decision and lessons learned
3. **Decide:** Reactivate or create new decision?
   - Reactivate if: Same problem, similar constraints
   - Create new if: Significant context change
4. **Reactivate:** Change status back to Active, add note with reasoning
5. **Track:** Add cross-reference to original archived decision

### Example Reactivation
```
Decision: D42 "Graduated API versioning"
Original: Archived 2027-03-15
Reactivation: 2027-06-10

Reason: New product line needs API versioning, same constraints as original.
Previous lessons show graduated deprecation works despite slow client migration.
Will apply same approach with updated timeline based on D42 experience.

Cross-reference: See D42 for historical context and lessons learned.
```

## Usage Examples

### Recording a New Decision (Active)
```yaml
---
id: D42
title: Graduated API Versioning Strategy
status: Active
date: 2026-03-15
---

API versioning via URL path (/v1/, /v2/, etc.).
Clients must migrate within 12 months of deprecation notice.

Status: Active (newly decided)
```

### Demotion After 6 Months (Active → Warm)
```yaml
status: Warm
status_since: 2026-09-15
status_reason: age
notes: 6 months of active use, still in production
```

### Supersession (Warm → Cold)
```yaml
status: Cold
status_since: 2026-12-15
status_reason: superseded_by
successor: D89
successor_title: Header-Based API Versioning
lessons: |
  - Graduated deprecation worked well for first 6 months
  - Client migration slower than expected (12 months wasn't enough)
  - For v2: use header versioning instead (less cognitive load)
  - Key insight: path-based versioning creates URL pollution
```

### Archive After 1 Year (Cold → Archived)
```yaml
status: Archived
status_since: 2027-03-15
status_reason: age
cold_duration: 1 year
archived_context: Historical reference for API versioning evolution
reactivation_criteria: |
  Could revisit if:
  - New product line with similar constraints as D42
  - Client ecosystem strongly prefers URL-based versioning
```

### Historical Research Query
```
brain-read tag:api-versioning status:* include_all=true

Results: D42 (Archived), D89 (Active)
Insight: Evolved from path-based to header-based over 3 years
Timeline: D42 → (6mo) Warm → (6mo) Cold → (1y) Archived; D89 in use
```

## Implementation Notes

### Durability
- Archival is additive: add status fields, never delete decision records
- Archive metadata grows over time, maintaining full decision history
- Supports audit trails and compliance requirements

### Performance
- Status field indexed for fast filtering
- Cold/Archived decisions exclude from most queries by default
- Historical search requires explicit flag, acceptable performance cost

### Integration
- Works seamlessly with brain-read (status filtering)
- Requires brain-write for recording status transitions
- Complements brain-remember for active decision tracking

### Governance
- Status transitions are logged with timestamps
- Reasons are required for all transitions (audit trail)
- Successor references create decision lineage
- Lessons learned tied to status transition, not decision content

## Workflow Summary

```
New Decision
    ↓ (record with status: Active)
ACTIVE (0-6 months)
    ↓ (after 6 months or when new variant emerges)
WARM (6-9 months)
    ↓ (after 3+ months or explicit supersession)
COLD (9 months - 2 years)
    ↓ (after 1 year of Cold or explicit request)
ARCHIVED (permanent)

↑ ← Can reactivate if pattern resurfaces
```

---

**Related Skills:** brain-read, brain-write, brain-remember

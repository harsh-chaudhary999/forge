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

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

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

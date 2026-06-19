---
name: brain-forget
description: "WHEN: A decision is being superseded, deprecated, or has aged out. Archive it without deletion — marks as warm→cold→archived with full audit trail."
type: flexible
requires: [brain-read, brain-write, brain-link]
version: 1.0.0
preamble-tier: 2
triggers:
  - "remove a decision"
  - "delete brain entry"
  - "forget a decision"
  - "archive brain file"
allowed-tools:
  - Bash
  - Write
  - AskUserQuestion
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

## Iron Law

```
NEVER DELETE A DECISION. EVERY DEPRECATED DECISION MUST BE ARCHIVED WITH ITS FULL CONTEXT, DEMOTION REASON, AND LESSONS LEARNED COMMITTED TO GIT SO THE AUDIT TRAIL IS PERMANENTLY PRESERVED.
```

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

Five demotion rules govern status changes: Rule 1 Time-Based, Rule 2 Supersession, Rule 3 Validity, Rule 4 Experimental, Rule 5 Governance — each with triggers, approval owners, evidence, and a Demotion Decision Tree. See [reference/demotion-rules.md](reference/demotion-rules.md) for the full five-rule spec, YAML examples, and the demotion decision tree.

## Evergreen Classification

Evergreen decisions are foundational principles or patterns that stand the test of time and should never be archived. Four evergreen types — pattern, architecture, contract, lesson — each have identification tests, `evergreen: true` marking YAML, and search/maintenance cadences. See [reference/evergreen.md](reference/evergreen.md) for all four evergreen types, marking YAML, search/maintenance routines, and the two worked evergreen-lesson examples (D15 MySQL, D28 microservices).

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

Five archival pitfalls undermine the brain's long-term value: (1) archive without documenting why, (2) Active decision that should be archived, (3) evergreen decision archived by mistake, (4) no recovery path, (5) demotion without team communication. See [reference/common-pitfalls.md](reference/common-pitfalls.md) for each pitfall's consequences, prevention, WRONG/RIGHT YAML examples, detection queries, and the team communication template.

## Automation & Governance

Demotion and archival work at scale when automated. Automated (time-based, no approval) vs event-based (approval-gated) criteria, the review/approval workflow, the notification matrix, analytics dashboards, council responsibilities, and search/status/tag filtering all live in reference. See [reference/automation-governance.md](reference/automation-governance.md) for automated/event-based demotion criteria, approval workflow, notification matrix, analytics & monitoring, governance council responsibilities, and default/extended/status/tag search behavior.

## Archive & Recovery Workflow

Archival is not destruction. The brain maintains full auditability of all decisions, even archived ones. The four-phase archival flow (identify candidates → review/approve → mark & archive → communicate), the three recovery paths (full reactivation, partial recovery, learning recovery), and the reactivation workflow all live in reference. See [reference/archive-recovery.md](reference/archive-recovery.md) for the four archival phases, three recovery paths with YAML examples, and the reactivation workflow + example.

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

## Edge Cases

### Edge Case 1: Decision is still referenced (supersession dependency)

**Symptom:** Attempt to archive decision, but other active decisions still reference it as parent or prerequisite.

**Do NOT:** Archive if dependents are still active. Do NOT orphan child decisions.

**Mitigation:**
1. Check dependents before demotion: `grep -r "parent_decision: D<id>\|depends.*D<id>" ~/forge/brain --include="*.md"`
2. If dependents found: List them — they must be reviewed/updated before archival
3. Two paths:
   - Demote parent only to Warm, not Cold (leave time for children to migrate)
   - Update all children to point to new parent before archiving old parent
4. If decision has many dependents: Consider marking Warm instead of Cold (softer deprecation)

**Escalation:** NEEDS_COORDINATION — Decision has active dependents. Cannot archive without updating them first. Notify dependent teams to migrate to successor decision or update parent references.

---

### Edge Case 2: Archived decision needed again (restore from archive)

**Symptom:** Pattern that was archived resurfaces; new context makes archived approach relevant again.

**Do NOT:** Create duplicate decision with same content. Do NOT ignore archived decision.

**Mitigation:**
1. Search archive for similar decisions: `grep -r "keyword" ~/forge/brain/archived --include="*.md"`
2. If exact match found: Reactivate by changing `status: archived` → `status: warm` or `status: active`
3. Add reactivation note: `reactivated_date: <date>`, `reactivation_reason: "Pattern needed again due to <context>"`
4. Update links if children were reparented during archival
5. Commit: `decision: reactivate D<id> <title> — pattern relevant again for <new-context>`

**Escalation:** NEEDS_CONTEXT — Archived decision pattern needed again. Verify context has truly changed (not just forgotten). If reactivating, update dependent decisions and document why archived decision is now valid.

---

### Edge Case 3: Archive reason not documented (audit trail gap)

**Symptom:** Decision marked Archived with no explanation of why (missing `archived_reason`, `lessons_learned`).

**Do NOT:** Archive without documenting reason. Do NOT create undocumented archival.

**Mitigation:**
1. Always include when demoting to Cold or Archived:
   - `status_reason`: age, superseded_by, outdated, experimental_end, revoked
   - `lessons_learned`: what worked, what didn't, what we'd do differently
   - `reactivation_criteria`: when would we reconsider this approach?
2. For each reason type:
   - **age**: "Naturally aged out after 24 months"
   - **superseded**: "Replaced by D<new-id> which uses <new-approach>"
   - **outdated**: "No longer applicable due to <constraint-change>"
   - **experimental**: "Experiment concluded: <result>, adopt/reject decision"
   - **revoked**: "Council revocation: <reason>; migrate to D<replacement>"

**Escalation:** NEEDS_INFRA_CHANGE — If discovered during audit, add retroactive documentation with commit message explaining why decision was archived and what lessons were learned.

---

### Edge Case 4: Multiple decisions can replace this one (parallel supersession)

**Symptom:** Decision being archived but multiple successors exist (no single D<new-id> replaces it).

**Do NOT:** Pick arbitrary replacement. Do NOT leave ambiguous.

**Mitigation:**
1. Identify replacement candidates: `grep -r "parent: D<id>\|related.*D<id>" ~/forge/brain --include="*.md" | grep -v archived`
2. If multiple candidates, document each:
   - `successor_decision_1: D<id1>` — use this for scenario A
   - `successor_decision_2: D<id2>` — use this for scenario B
3. Add migration guidance: "Choose successor based on context: If A then D<id1>, if B then D<id2>"
4. Or: Create NEW consolidation decision that references both predecessors

**Escalation:** NEEDS_COORDINATION — Multiple successors for one decision. Coordinate with teams using original decision to determine which successor applies to their context. May require creating new decision that synthesizes approaches.

---

### Edge Case 5: (EXISTING) Decision being demoted straight to archived in one step

**Symptom:** Attempt to move Active → Archived without passing through Warm and Cold stages.

**Do NOT:** Skip lifecycle stages. Do NOT archive without giving teams transition time.

**Mitigation:**
1. Enforce lifecycle: Active → Warm (6 mo) → Cold (3 mo) → Archived (12 mo)
2. Unless explicit council approval for emergency revocation (security, compliance)
3. Each transition requires:
   - Evidence (aged, superseded, outdated, experimental, revoked)
   - Commit message explaining reason
   - Notification to dependent teams
4. Shortcut only for revoked decisions (security issue, policy violation)

**Escalation:** NEEDS_CONTEXT — Direct archival skipped lifecycle safeguards. Revert to Warm status and follow proper demotion timeline, OR escalate to council for emergency revocation approval if revocation reason is valid.

---

## Decision Tree: Archive vs Delete Decision

```
Decision marked for removal
    ↓
Should this decision be permanently deleted from history?
├─ YES → STOP. Decisions are never deleted. Demote to archived instead.
└─ NO → Continue below

Has the decision aged naturally (6mo Active, 3mo Warm, 12mo Cold)?
├─ YES → Apply Rule 1 (Time-Based): Demote to Archived
└─ NO → Continue below

Is there a successor decision that replaces it?
├─ YES → Apply Rule 2 (Supersession): Mark `successor: D<id>`, demote through Warm→Cold→Archived
└─ NO → Continue below

Did the system context change (constraints, product direction, regulation)?
├─ YES → Apply Rule 3 (Validity): Document what changed, demote through Warm→Cold
└─ NO → Continue below

Was this an experiment that concluded?
├─ YES → Apply Rule 4 (Experimental): Document results, demote through Warm→Cold
└─ NO → Continue below

Was this decision formally revoked by council (security, policy)?
├─ YES → Apply Rule 5 (Governance): Urgent notification, may skip to Archived if critical
└─ NO → Decision remains Active (no demotion rule triggered)

Result:
- Default lifecycle: Active → Warm (6mo) → Cold (3mo) → Archived (12mo)
- With successor: mark supersession, follow lifecycle
- With broken context: mark outdated, follow lifecycle
- With experimental conclusion: mark experimental_end, follow lifecycle
- With council revocation: can skip Warm/Cold if critical (security), escalate for approval
- Never delete: always demote, always document reason, always preserve audit trail
```

---

**Related Skills:** brain-read, brain-write, brain-remember

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] The target decision file still exists at its brain path — only status fields were updated, no file was deleted
- [ ] The demotion (status change) was committed to git with `git -C ~/forge/brain commit`, and `git log --oneline -1` shows the commit
- [ ] The commit message specifies which decision, from what status, to what status, and the demotion rule that triggered it — no vague "cleaned up" messages
- [ ] A grep for cross-references to the demoted decision ID returned no dangling Active decisions that depended on it without a migration path
- [ ] If the conductor required a brain-mutation marker for this demotion, the agreed marker line appears in `conductor.log` before claiming the demotion complete (there is no dedicated `[P*-BRAIN-FORGET]` marker in the registry — use the marker the active conductor phase specifies, or none)

## Checklist

Before claiming completion:

- [ ] No decision file was deleted — only status fields updated
- [ ] Demotion followed the correct lifecycle stage (Active → Warm → Cold → Archived), not a single jump
- [ ] Every dependent decision checked via brain-read before demotion
- [ ] Demotion commit message specifies which decision, from what status, to what status, and why
- [ ] `lessons_learned` and `status_reason` fields are populated in the decision file
- [ ] Successor decision (if applicable) is linked via `successor:` field
- [ ] Affected teams notified of the demotion per the communication protocol for the rule applied

## Cross-References

- `brain-read`: Fetches the current decision file before demotion; brain-forget requires reading the file to confirm status.
- `brain-write`: Creates the decision record that brain-forget later archives; successor decisions are recorded via brain-write.
- `brain-recall`: Search before forget — confirm no active decision depends on the one being demoted.
- `brain-why`: Trace provenance before archiving; use brain-why to identify downstream decisions that reference the one being forgotten.
- `brain-link`: Checks and updates `successor:` and `related:` edges when a decision is archived.

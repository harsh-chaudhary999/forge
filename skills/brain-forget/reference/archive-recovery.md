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

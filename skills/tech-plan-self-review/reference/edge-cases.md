# Edge Cases & Fallback Paths

The five non-happy-path scenarios a self-review can hit, each with Diagnosis / Response / Escalation. When one of these triggers, follow the escalation keyword named here and route every human decision through `AskUserQuestion` per [`skills/_shared/human-input.md`](../../_shared/human-input.md).

## Edge Case 1: Placeholder is discovered during self-review

**Diagnosis**: Tech plan includes a task with placeholder like "TODO: wait for API docs" or "Use TBD auth mechanism".

**Response**:
- **Flag as BLOCKER**: Placeholders block deployment.
- **Escalate**: "Plan contains [N] placeholders. Cannot dispatch until resolved: [list details]."
- **Recovery options**:
  1. Remove placeholder task and reduce scope.
  2. Replace placeholder with concrete implementation (possibly temporary workaround).
  3. Add task to unblock placeholder (e.g., "Request API docs from vendor").
- **Track resolution**: When placeholder is resolved, re-run self-review.

**Escalation**: BLOCKED - Placeholders must be resolved. Escalate to tech-plan-write-per-project to fix.

---

## Edge Case 2: Scope is too broad (tasks cannot realistically be completed in sprint)

**Diagnosis**: Self-review calculates total task time: sum of all 2-5 minute tasks = 47 minutes of implementation. But spec is complex, review will add time. Scope may not fit in available sprint time.

**Response**:
- **Calculate realistic timeline**: Estimate = task time + review buffer (20-30%) + unknowns (10-15%).
- **Realistic estimate**: 47 min tasks + 15 min buffer + 5 min unknowns = ~67 minutes. 
- **If fits sprint**: Proceed.
- **If exceeds available time**: Escalate: "Estimated implementation time: [X] min. Available time: [Y] min. Scope is [over/under]."
- **Recovery**:
  1. Reduce scope: Remove lower-priority tasks.
  2. Extend timeline: Ask stakeholders if deadline can slip.
  3. Add resources: Can another developer help?

**Escalation**: NEEDS_TIMELINE_ADJUSTMENT - Scope vs. time mismatch must be resolved by stakeholders.

---

## Edge Case 3: Dependencies are missing (Task A depends on Task B from different repo, not captured)

**Diagnosis**: Web project plan has Task 5: "Integrate with API endpoint". But that endpoint is defined in backend plan's Task 3. Dependency is implicit, not documented.

**Response**:
- **Detect**: Cross-check all tasks against shared-dev-spec. If a task references work from another repo, mark as dependent.
- **Document explicitly**: "Task 5 (Web) depends on: backend-api Task 3. Cannot start until backend Task 3 is done."
- **Sequencing**: Ensure backend Task 3 is scheduled before web Task 5 in dispatch phase.
- **Add blocker check**: "If backend Task 3 blocked, web Task 5 automatically blocked."

**Escalation**: NEEDS_SEQUENCING - If dependencies are complex, escalate to conductor to verify correct task ordering.

---

## Edge Case 4: Plan conflicts with other repo's plan (simultaneous writes to shared resource)

**Diagnosis**: Frontend plan says "Task 2: Modify shared schema migration file". Backend plan also says "Task 3: Modify shared schema migration file". Both repos try to edit the same file simultaneously.

**Response**:
- **Detect**: Cross-repo plan validation. Scan all plans for conflicting files.
- **Resolution**:
  1. **Merge tasks**: Combine into one schema migration task (backend owns it, frontend waits for it).
  2. **Split file**: Create separate migration files (backend_migration_v1, frontend_migration_v1).
  3. **Sequence**: Backend does schema migration, frontend does schema usage changes after.
- **Document**: "Shared resource: [file]. Owner: backend. Frontend waits for completion before Task [X]."

**Escalation**: NEEDS_COORDINATION - If repos must edit same file, escalate to conductor to coordinate task sequencing.

---

## Edge Case 5: Tech Plan Is Correct but Spec Has Changed Since Plan Was Written

**Diagnosis**: Tech plan was written on day 1. On day 3, Council amended the shared-dev-spec (a cache contract changed, an API field was renamed). The tech plan still references the old field names and the old cache contract. The plan is now stale.

**Response**:
- **Detect**: Before self-review, check the spec's last-modified timestamp against the plan's creation timestamp. If spec is newer, diff carefully.
- **Reconcile**: For each changed spec field, find the task that implements it and update the task's code, file path, and test assertions
- **Do NOT** approve a plan against a stale spec — implementation against the wrong spec creates bugs that survive code review
- **Document**: Note in the plan header: "Reconciled with spec amendment [date]: changed X → Y in tasks 3, 7, and 9"

**Escalation**: NEEDS_CONTEXT - If the spec change is large enough that more than 30% of tasks need updating, the plan should be rewritten rather than patched. Escalate to the dreamer to confirm scope before rewriting.

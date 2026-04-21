---
name: spec-freeze
description: "WHEN the shared-dev-spec is locked after council negotiation. Prevents all spec mutations during build phase. Invoke before per-project tech planning begins."
type: rigid
requires: [brain-read, brain-write]
---
# Spec Freeze (HARD-GATE)

**Rule:** NO SPEC CHANGES AFTER FREEZE WITHOUT FULL COUNCIL RE-NEGOTIATION.

Once the shared-dev-spec is frozen, it is immutable. Any behavioral change requires a full council re-vote with evidence. No exceptions, no "small tweaks," no scope additions.

## Iron Law

```
NO SPEC CHANGES AFTER FREEZE WITHOUT FULL COUNCIL RE-NEGOTIATION. A SMALL TWEAK TO A FROZEN SPEC IS A SPEC CHANGE. URGENCY IS NOT AUTHORIZATION.
```

## Anti-Pattern Preamble: Why Agents Try to Change Specs After Freeze

| Rationalization | The Truth |
|---|---|
| "It's just a small tweak, not a real spec change" | Small tweaks are spec changes. A "small" API field addition ripples through 4 surfaces, 5 contracts, and every tech plan. There is no small tweak to a frozen spec. |
| "We discovered a better approach during implementation" | Better approaches belong in the next PRD cycle. The frozen spec reflects negotiated consensus across all surfaces. Unilateral improvement is unilateral risk. |
| "The stakeholder asked for this, we can't push back" | Stakeholders don't override council consensus. If the request has merit, it goes through the change request process with evidence. Urgency is not authorization. |
| "This won't affect other surfaces, it's isolated to my project" | Nothing is isolated in a multi-repo product. Backend changes affect cache keys, API shapes, event schemas. If you think it's isolated, you haven't checked. |
| "We'll just update the spec and notify everyone" | Notification is not negotiation. Council exists because surfaces disagree when they actually discuss. Notification skips the disagreement and ships the conflict. |
| "The spec was wrong, we're fixing it, not changing it" | Wrong specs get fixed through the change request process. Self-diagnosed "fixes" are unreviewed changes wearing a trustworthy label. |
| "We're behind schedule, we can't afford to re-negotiate" | Re-negotiation takes hours. Shipping against a broken spec takes weeks of rework. Schedule pressure is the worst reason to skip process. |
| "Everyone informally agrees this change is fine" | Informal agreement is not council consensus. Informal agreement is the absence of structured dissent. Run the process. |

## Freeze Protocol

### Step 1: Validate Council Sign-Off

**HARD-GATE: All council surfaces must have signed off before freeze.**

- **Input:** Shared-dev-spec from `forge-council-gate` (SPECLOCK decision)
- **Check:**
  - All 4 surfaces attended council and proposed (backend, web, app, infra)
  - All 5 contracts negotiated and locked (API, events, cache, DB, search)
  - No unresolved conflicts (all consensus or escalated with dreamer decision)
  - Each surface agreed to their scope and contract specifications
  - No "TBD" remains anywhere in the spec
  - **Design implementability:** When **Design source (from intake)** has **`design_new_work: yes`**, the spec must include **`design_brain_paths`** and/or **`figma_file_key` + `figma_root_node_ids`** (or explicit `design_waiver: prd_only`) plus a one-line **implementable UI contract** (which frames/nodes/files implementation must match). If only wiki/Figma URLs without those fields → STOP. Return to intake or council — do not freeze.
- **If any check fails:** STOP. Return to `forge-council-gate`. Do not freeze an incomplete spec.

### Step 2: Generate Spec Hash

- **Action:** Commit the shared-dev-spec to git and capture the commit SHA
  ```bash
  git add brain/prds/<task-id>/shared-dev-spec.md
  git commit -m "SPECFREEZE: Lock shared-dev-spec for <task-id>"
  ```
- **Output:** Spec hash = git commit SHA (immutable, verifiable, auditable)
- **Why SHA:** Any future mutation changes the hash. Drift is detectable by comparing current file hash against freeze record.

### Step 3: Write Freeze Record to Brain

- **Action:** Invoke `brain-write` to create freeze record
  - Decision ID: `SPECFRZ-YYYY-MM-DD-HH`
  - Contents:
    - Spec hash (commit SHA)
    - Timestamp of freeze
    - List of council surfaces that signed off
    - Link to SPECLOCK decision ID (from council-gate)
    - Frozen contract summaries (API version, event topics, cache keys, DB schema version, search index)
    - Freeze status: `FROZEN`
- **Output:** Freeze record persisted in brain, linked to SPECLOCK

### Step 4: Classify Change Boundaries

Once frozen, all proposed changes fall into exactly one category:

| Category | Definition | Action |
|---|---|---|
| **Cosmetic** | Typo fixes, formatting, clarifying comments that do not alter behavior or contracts | Allowed. Commit with prefix `SPECFIX-COSMETIC:`. No re-freeze required. |
| **Behavioral** | Any change to acceptance criteria, contract shapes, surface scope, or data flow | Blocked until full council re-negotiation. Requires change request (Step 5). Triggers re-freeze. |
| **Scope Addition** | New feature, new endpoint, new event, new surface responsibility not in original spec | Blocked unconditionally. Must be a new PRD through `forge-intake-gate`. Separate track entirely. |

**When in doubt, classify as Behavioral.** Over-caution is correct. Under-caution ships conflicts.

### Step 5: Change Request Process

If a behavioral change is genuinely required:

1. **Document the evidence** in brain (decision ID: `SPECCHG-YYYY-MM-DD-HH`)
   - What changed (exact spec section affected)
   - Why it must change (technical evidence, not opinion)
   - Impact on each surface (all 4 must be assessed)
   - Impact on each contract (all 5 must be assessed)

2. **Submit to council re-vote**
   - Invoke `forge-council-gate` with the change request
   - All 4 surfaces must attend and vote
   - Majority is not sufficient -- unanimous consent or dreamer escalation

3. **If approved:** Re-execute freeze protocol (Steps 1-3) with updated spec
   - New spec hash generated
   - New freeze record written (links to prior SPECFRZ and SPECCHG)
   - Old freeze record marked `SUPERSEDED`

4. **If rejected:** Change is dead. Document rejection reason. Proceed with original frozen spec.

## Edge Cases & Fallback Paths

### Case 1: Bug in Spec Discovered During Build
- **Symptom:** "The spec says use endpoint `/v2/users` but `/v2/users` doesn't exist yet -- spec assumed it would"
- **Do NOT:** Quietly patch the spec and keep building
- **Action:**
  1. Halt work on affected surface
  2. Classify: is this cosmetic (typo in endpoint name) or behavioral (endpoint doesn't exist, need different approach)?
  3. If cosmetic: fix with `SPECFIX-COSMETIC` commit, document in brain, continue
  4. If behavioral: file change request (Step 5), block affected work until council re-votes
- **Fallback:** If build is fully blocked across all surfaces, escalate to dreamer as CRITICAL with timeline impact

### Case 2: External Dependency Changes API
- **Symptom:** "Third-party payment API deprecated v3, our spec is built on v3"
- **Do NOT:** Update the spec to v4 and assume contracts still hold
- **Action:**
  1. Document the external change with evidence (deprecation notice, timeline, migration guide)
  2. Assess impact on all 5 contracts (API shape change cascades to events, cache, DB, search)
  3. File change request with external evidence attached
  4. Council re-votes with full impact assessment
  5. If v4 migration is trivial (same shape, different URL): may classify as cosmetic after council review
- **Fallback:** If deprecation deadline is before council can convene, escalate to dreamer as URGENT with evidence

### Case 3: Stakeholder Requests "Small Tweak"
- **Symptom:** "Can we just add one more field to the response? It's tiny."
- **Do NOT:** Add the field because it seems harmless
- **Action:**
  1. Classify the request: cosmetic, behavioral, or scope addition
  2. A new field in an API response is behavioral (changes contract shape, affects all consumers)
  3. Explain to stakeholder: frozen spec requires change request process
  4. If stakeholder insists: file change request with their justification as evidence
  5. Council decides, not the stakeholder
- **Fallback:** If stakeholder escalates above council, dreamer arbitrates. Council decision stands until dreamer overrides.

### Case 4: Performance Requirement Proves Impossible
- **Symptom:** "Spec says p95 < 50ms but with the negotiated DB schema, best we can achieve is p95 < 200ms"
- **Do NOT:** Silently relax the performance requirement and ship
- **Action:**
  1. Document the impossibility with benchmarks (not estimates -- measured data)
  2. File change request with benchmark evidence
  3. Council re-votes on revised performance target (may require schema renegotiation)
  4. If schema change needed: full contract renegotiation across all 5 contracts
  5. Re-freeze with revised spec
- **Fallback:** If no acceptable performance target exists, escalate to dreamer for requirement vs. architecture trade-off

### Case 5: Security Vulnerability Requires Spec Change
- **Symptom:** "The auth flow in the spec is vulnerable to token replay attacks"
- **Do NOT:** Fix the vulnerability and update spec unilaterally, even if it's a security issue
- **Action:**
  1. Document the vulnerability with severity assessment (CVSS or equivalent)
  2. File change request with security evidence -- this is behavioral (auth flow change)
  3. Council re-votes with security team input (security is not a shortcut around process)
  4. If CRITICAL severity (active exploit): escalate to dreamer for emergency freeze override
  5. Dreamer may authorize expedited re-freeze (council async review within 24h)
- **Fallback:** Emergency freeze override is documented as `SPECFRZ-EMERGENCY` with mandatory post-incident council review

---

## Edge Cases & Escalation Paths

### Edge Case 1: Freeze Lock File Already Exists — Another Process Is Holding the Freeze Lock

**Scenario**: You are attempting to freeze the spec. You create the freeze lock file at `brain/pds/<task-id>/FREEZE.lock` to prevent concurrent freeze operations. However, the file already exists with a timestamp from 8 hours ago, suggesting another freeze process is stuck or crashed.

**Symptom**: `mkdir -p brain/pds/<task-id>/FREEZE.lock` returns "file already exists" or lock file contains old timestamp. You cannot determine if another process still holds the lock or if the process crashed while holding it.

**Do NOT**: Delete the lock file immediately. Another freeze operation may still be in progress, and deleting the lock creates a race condition.

**Mitigation**:
1. Read the lock file to extract the process ID (PID) and timestamp of the lock holder.
2. Check if the PID is still running: `ps -p $PID`. If process is running, wait 60 seconds and retry (exponential backoff, max 5 minutes).
3. If process is NOT running (stale lock), log the orphaned lock event in brain. Remove the stale lock file.
4. Create a new lock file with current PID and timestamp.
5. If you cannot determine lock owner, escalate to BLOCKED and notify an administrator to inspect the lock file manually.

**Escalation**: BLOCKED (if lock state is ambiguous and cannot be resolved automatically)

---

### Edge Case 2: PRD Changes After Freeze Declared — Someone Modifies PRD After Freeze Lock Recorded

**Scenario**: You have frozen the spec and written the freeze record to brain with spec hash `abc123`. The freeze is declared. One hour later, a product manager updates `shared-dev-spec.md` to add a new feature field (a behavioral change). The spec file hash is now `def456`, but the freeze record still references `abc123`.

**Symptom**: During build phase, a tech planner runs a verification that compares current spec hash against the freeze record. Hashes do not match. Git diff shows behavioral changes (new fields, modified acceptance criteria) in the spec file since the freeze time.

**Do NOT**: Assume the change is cosmetic and allow the tech plans to proceed. Mismatched hashes indicate unauthorized mutation.

**Mitigation**:
1. Immediately halt all per-project tech planning that depends on this spec.
2. Investigate what changed: `git diff abc123 def456 shared-dev-spec.md`
3. Classify the change: cosmetic (typo, formatting) or behavioral (contract change, scope addition)?
4. If behavioral: revert the spec to the frozen hash: `git checkout abc123 -- shared-dev-spec.md`
5. File a change request (SPECCHG-*) if the mutation is justified. Require council re-vote.
6. If cosmetic: apply the change with SPECFIX-COSMETIC prefix. No re-vote required, but document in brain.
7. Resume tech planning only after hash verification passes again.

**Escalation**: BLOCKED (unauthorized mutation detected; requires revert or change request)

---

### Edge Case 3: Incomplete Dependencies at Freeze Time — Required Upstream Specs Not Yet Locked

**Scenario**: The product has a dependency hierarchy: shared-schemas spec must be locked before backend-api spec. You attempt to freeze the shared-dev-spec for a feature that includes both projects. However, the shared-schemas spec is still in negotiation (council is still debating the data model). You cannot freeze backend-api because its spec depends on the shared-schemas output.

**Symptom**: Freeze checklist item "All 5 contracts locked (API, events, cache, DB, search)" fails. The API contract references an entity type defined in shared-schemas, but that entity is still marked TBD.

**Do NOT**: Proceed with freeze on incomplete contracts. Downstream tech plans will have dangling references.

**Mitigation**:
1. Halt the freeze. Do not write freeze record yet.
2. Identify which upstream specs are not yet locked. Return to `forge-council-gate` to complete negotiation for upstream specs first.
3. Once upstream specs are locked and frozen, resume the freeze for the dependent spec.
4. Verify all 5 contracts are now complete (no TBD) before writing the freeze record.
5. Chain the freeze records: link the dependent spec's freeze record to the upstream freeze record (frozen_depends_on field).

**Escalation**: NEEDS_COORDINATION (upstream specs must be frozen first; requires council sequencing)

---

### Edge Case 4: Recovery From Crashed Freeze State — Previous Freeze Left System in Partial State

**Scenario**: A freeze operation was initiated 6 hours ago. It crashed after committing the spec to git but before writing the freeze record to brain. Now the git repository has a `SPECFREEZE:` commit, but no corresponding freeze record exists in brain. The system is in an ambiguous state: is the spec frozen or not?

**Symptom**: Spec file exists with hash `abc123`. A git commit with message `SPECFREEZE: ...` exists with that hash. But `brain-read --key "specfrz.*"` returns no freeze records. Tech planners don't know if they should treat the spec as frozen or open.

**Do NOT**: Assume the freeze succeeded just because the git commit exists. Partial state means the spec is not fully locked until the brain record is written.

**Mitigation**:
1. Verify the git commit: `git log --oneline | grep SPECFREEZE`. Confirm the spec hash in the commit.
2. Check brain: `brain-read --key "specfrz-$(date +%Y-%m-%d)"*"`. If freeze record exists, the freeze is valid.
3. If freeze record does NOT exist: you have two options:
   - Option A: Complete the freeze by writing the freeze record now (provide all required fields: spec hash, council surfaces, contracts).
   - Option B: Revert the spec commit and start the freeze process again.
4. Choose Option A if the council sign-off is still valid (within 24 hours). Otherwise, Option B (re-negotiate).
5. Once freeze record is written, mark the recovery in brain with event: "FREEZE_RECOVERY: completed at <timestamp>".

**Escalation**: NEEDS_CONTEXT (requires manual inspection of git commit and decision: complete or retry)

---

### Edge Case 5: Multiple Cosmetic Fixes Accumulating — May Be Behavioral Changes Disguised as Cosmetic

**Scenario**: During build phase, 5 cosmetic fixes have been committed to the spec: fix typo in endpoint name, clarify field description, add missing example, adjust parameter range, reorder sections. Each commit includes `SPECFIX-COSMETIC:` prefix and was approved individually. But the cumulative effect is a significant change to the contract shape.

**Symptom**: Comparing the spec at freeze time to the current spec after 5 cosmetic commits, you notice the API contract has drifted significantly. A field type was "clarified" from `string` to `string (UUID format)`, which is behavioral, not cosmetic.

**Do NOT**: Allow the cosmetic fixes to accumulate without periodic audit. Cosmetic fixes can disguise behavioral changes.

**Mitigation**:
1. Establish a threshold: after every 3 cosmetic fixes, run an audit: `git diff abc123 HEAD -- shared-dev-spec.md | wc -l`. If diff exceeds 50 lines, escalate.
2. For each accumulated cosmetic fix, re-classify: is it truly cosmetic (typo, formatting only) or behavioral (contract shape, acceptance criteria)?
3. If any fix is reclassified as behavioral: revert it and file a change request (SPECCHG-*). Require council re-vote.
4. Update the spec hash in brain after each revert or major change. Freeze record now references the revised hash.
5. Resume tech planning only after audit confirms no hidden behavioral changes.

**Escalation**: DONE_WITH_CONCERNS (if cosmetic fixes are legitimate but require documentation) or BLOCKED (if behavioral changes are disguised)

---

## Decision Tree: Freeze Enforcement Scope Selection

```
┌─ ARE ALL 4 SURFACES IN A SINGLE PRODUCT?
│  ├─ YES ─→ Scope: SINGLE PROJECT SPEC FREEZE
│  │  (Lock this project's spec; other projects continue negotiating)
│  │  (Typical: locking backend-api while web negotiates)
│  │
│  └─ NO ─→ ARE ALL CONTRACTS INTERDEPENDENT (API shapes change together)?
│     ├─ YES ─→ Scope: MULTI-REPO COORDINATED FREEZE
│     │  (Lock all affected projects' specs together)
│     │  (All 5 contracts locked simultaneously)
│     │  (Typical: shared-schemas + backend-api + web freeze together)
│     │
│     └─ NO ─→ ARE THERE SEQUENTIAL DEPENDENCIES?
│        ├─ YES ─→ Scope: SEQUENTIAL FREEZE
│        │  (Freeze upstream specs first, then downstream)
│        │  (Freeze order: shared-schemas → backend-api → web → app)
│        │
│        └─ UNSURE ─→ Default: MULTI-REPO COORDINATED FREEZE
│           (Safest default; if specs affect each other, lock together)
└─ FINAL CHECK: Is the entire product shipping as one unit?
   ├─ YES ─→ PRODUCT-WIDE FREEZE
   │  (Freeze all project specs, all contracts, all surfaces together)
   │
   └─ NO ─→ Use scope determined above
```

---

## Red Flags — STOP

Stop immediately and escalate if you observe any of the following:

- **Spec file modified after freeze without a `SPECFIX-COSMETIC` or `SPECFRZ` commit prefix** -- unauthorized mutation
- **Tech plan references contracts not in the frozen spec** -- spec drift or shadow negotiation
- **Surface claims "we agreed to change X" without a SPECCHG decision record** -- informal override, process violation
- **Multiple cosmetic fixes accumulating** -- may be behavioral changes disguised as cosmetic. Audit each one.
- **Change request filed without evidence** -- opinion is not evidence. Reject and require measured data.
- **Council re-vote conducted without all 4 surfaces** -- invalid vote. Re-run with full attendance.
- **Spec hash in freeze record does not match current file hash** -- spec was mutated outside process. Revert to frozen version.

## Freeze Checklist

Before declaring spec frozen, verify:

- [ ] Shared-dev-spec exists and is complete (from `forge-council-gate`)
- [ ] All 4 surfaces signed off (backend, web, app, infra)
- [ ] All 5 contracts locked (API, events, cache, DB, search) -- no "TBD"
- [ ] No unresolved conflicts in spec (all consensus or dreamer-resolved)
- [ ] Spec committed to git with `SPECFREEZE:` prefix
- [ ] Spec hash (commit SHA) captured
- [ ] Freeze record written to brain (`SPECFRZ-YYYY-MM-DD-HH`)
- [ ] Freeze record links to SPECLOCK decision ID
- [ ] Change boundary categories documented (cosmetic / behavioral / scope addition)
- [ ] All surfaces notified of freeze (with spec hash for verification)
- [ ] Per-project tech planning may now begin (invoke `tech-plan-write-per-project`)

Output: **SPEC FROZEN** (hash verified, brain record written, ready for per-project tech planning) or **BLOCKED** (council sign-off incomplete, unresolved conflicts, spec contains TBDs)

## Cross-References

- `forge-council-gate` -- produces the SPECLOCK that this skill freezes
- `forge-letter-spirit` -- governs how freeze rules are interpreted (no rationalizations)
- `tech-plan-write-per-project` -- consumes the frozen spec as immutable input

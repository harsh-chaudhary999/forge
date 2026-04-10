---
name: spec-freeze
description: WHEN the shared-dev-spec is locked after council negotiation. Prevents all spec mutations during build phase. Invoke before per-project tech planning begins.
type: rigid
requires: [brain-read, brain-write]
---
# Spec Freeze (HARD-GATE)

**Rule:** NO SPEC CHANGES AFTER FREEZE WITHOUT FULL COUNCIL RE-NEGOTIATION.

Once the shared-dev-spec is frozen, it is immutable. Any behavioral change requires a full council re-vote with evidence. No exceptions, no "small tweaks," no scope additions.

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

## Red Flags - STOP

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

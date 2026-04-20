---
name: forge-intake-gate
description: "WHEN: A new PRD arrives for implementation. HARD-GATE: Every PRD goes through intake (Q1–Q8 always; Q9 design/UI lock mandatory when web or app is in scope). No skipping, no exceptions, no \"trivial\" PRDs."
type: rigid
---
# Intake Gate (HARD-GATE)

**Rule:** Every single PRD must pass through intake-interrogate skill. No exceptions.

## Anti-Pattern Preamble: Why Agents Skip Intake

| Rationalization | The Truth |
|---|---|
| "This PRD is just a bug fix, not a feature, so intake is unnecessary" | Bug fixes require intake just like features. They change behavior, affect contracts, need scoping. |
| "The requirements are crystal clear, everyone understands what to build" | Clarity is illusion. Hidden assumptions live in unchallenged requirements. Intake surfaces them. |
| "We've built similar features before, we can skip intake" | Each product state is unique. Prior success != current success. Context shifts require fresh intake. |
| "This is a tiny change, intake is overkill" | Size is irrelevant. A 3-line config change can break production. Intake doesn't scale with size; it's binary. |
| "I already talked to the user, I know what they want" | Conversation != interrogation. Intake asks the locked questions conversation never gets to (contracts, edge cases, tradeoffs, **design when web/app**). |
| "The spec is already written and approved, intake is redundant now" | Approval without interrogation is not validation. Intake locks the spec, not stamps it. |
| "Intake will take too long, we need to move fast" | Intake takes 1-2 hours. Wrong implementation takes days. Fast wrong is slower than slow right. |
| "We can do intake retrospectively if something goes wrong" | Intake prevents the wrong. Retrospective interrogation doesn't undo shipped bugs. |
| "No one will notice if we skip intake on this one" | Skipping intake once makes it easy to skip twice. Systems degrade through exceptions. |
| "This is internal-only, not user-facing, so less rigor" | Internal changes affect platform reliability. Risk doesn't scale with audience. |

## Iron Law

```
ALL MANDATORY INTAKE QUESTIONS MUST BE ANSWERED AND SCOPE LOCKED BEFORE THE PRD ADVANCES TO COUNCIL.
Q1–Q8 ALWAYS; Q9 (DESIGN / UI CHANGE CLASS) IS MANDATORY WHEN WEB OR APP WORK IS IN SCOPE (SEE intake-interrogate Q9).
PARTIAL INTAKE IS NO INTAKE.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **PRD is being handed to council before intake is complete** — Council requires a locked PRD. Intake produces the lock. Council before intake means negotiating on unvalidated assumptions. STOP. Complete intake and brain-write before council.
- **Any mandatory intake question has a "TBD" or blank answer** — An unanswered question is not a skipped question — it is an unknown risk that will surface at the worst moment. STOP. All of Q1–Q8 must have concrete answers; **when web or app is in scope, Q9 must also be locked** (see `intake-interrogate` — not optional for UI-scoped PRDs).
- **`prd-locked.md` is missing Q4 registry fields** — `intake-interrogate` requires **`repo_registry_confidence`** and **`repo_naming_mismatch_notes`** (and **`product_md_update_required`** when needed) alongside **Repos Affected**. STOP. Re-run Q4; do not accept letter-only MCQ without those locks.
- **The intake document was not written to brain** — Verbal intake is not intake. If it's not committed to `~/forge/brain/prds/`, it didn't happen and cannot be referenced downstream. STOP. Write and commit before locking.
- **"This is a continuation of a previous PRD, we can skip intake"** — Continuation PRDs introduce new behavior, change existing contracts, or extend scope. Each one gets independent intake. STOP. Run intake for the new PRD.
- **Rollback plan is "revert the commit"** — A one-line rollback plan is not a rollback plan. It doesn't address data migrations, cache invalidation, or external service state. STOP. Require a concrete rollback procedure before locking.
- **Success criteria are behavioral descriptions instead of verifiable conditions** — "User should be able to see their orders" is not a success criterion — it cannot be objectively passed or failed. STOP. Require measurable, testable criteria.
- **Intake is being run after tech plans have started** — Tech plans derive from locked PRDs. If intake runs after planning begins, the plans are built on unlocked sand. STOP. Invalidate plans and re-run intake first.

## Detailed Workflow

### Identify PRD (Input Validation)
- **Input:** Raw requirement (email, Slack, document, conversation)
- **Check:**
  - Is there a formal PRD document or is it implicit?
  - Who owns the PRD (product, stakeholder, user)?
  - What is the requested delivery date?
- **Output:** PRD identified, ownership clear

### Invoke Intake-Interrogate Skill
**ALWAYS invoke `/intake-interrogate` — do not paraphrase or summarize the intake questions yourself** (Q1–Q8 always; **Q9 mandatory when web or app is in scope**).

The skill will ask:

1. **What is the core user problem?** (not the solution)
2. **What surfaces does this touch?** (web, app, backend, infra, admin)
3. **What contracts must change?** (API versions, events, schema, cache keys)
4. **What are the acceptance criteria?** (not "works", but "user can X in <time>")
5. **What are the anti-goals?** (what must NOT happen)
6. **What does success look like in 3 months?** (metrics, usage patterns)
7. **What are the hard constraints?** (compliance, performance, cost, backwards-compat)
8. **What assumptions are we making?** (about user behavior, scale, tech stack)

### Lock the PRD
- **Input:** Answers to all mandatory questions (Q1–Q8; Q9 when web/app in scope)
- **Action:** Create PRD lock record in brain (decision ID: PRDLK-YYYY-MM-DD-HH)
  - Document each answer
  - Link to original requirement
  - Record who asked, who answered, timestamp
- **Output:** PRD LOCKED (status = frozen, ready for council)

### Validate Completeness
- **Check:**
  - All mandatory questions answered (Q1–Q8; Q9 when web/app in scope — not skipped, not "TBD")
  - Answers are not contradictory
  - No answer defers decision to later ("we'll decide during impl")
  - Surfaces and contracts are exhaustive (nothing forgotten)
- **If incomplete:** Return to Phase 2 (re-invoke intake-interrogate for missing pieces)

### Edge Cases & Fallback Paths

#### Case 1: PRD Changes During Development
- **Symptom:** Stakeholder asks for new requirement mid-sprint
- **Do NOT:** Merge it into existing PRD, patch the locked spec
- **Action:**
  1. Treat new requirement as separate PRD
  2. Run intake on the new requirement
  3. Determine: is it in scope of current PRD or new work?
  4. If new: create separate track (separate worktree, separate eval)
  5. If scope creep: escalate to dreamer (prioritization)

#### Case 2: PRD Spans Multiple Projects/Services
- **Symptom:** Feature requires changes to backend, web, app, infra
- **Do NOT:** Intake only the "main" project
- **Action:**
  1. Run intake once (covers all surfaces at once)
  2. Question 2 explicitly asks about all surfaces
  3. Question 3 (contracts) identifies inter-service dependencies
  4. All surface teams see the same locked PRD
  5. Council negotiates across surfaces (not intake, but depends on intake)

#### Case 3: User Submits Vague Requirement
- **Symptom:** "Make the search faster" or "Improve the dashboard"
- **Do NOT:** Make assumptions about what "faster" means
- **Action:**
  1. Invoke intake-interrogate anyway
  2. In Question 1 (core problem), probe until concrete problem surfaces
  3. In Question 4 (acceptance criteria), quantify "faster" (p95 latency < X)
  4. In Question 5 (anti-goals), capture "but don't sacrifice accuracy"
  5. Lock the concrete PRD (not the vague one)

#### Case 4: PRD Conflicts with Company Policy
- **Symptom:** Intake reveals requirement violates compliance rule or tech standard
- **Do NOT:** Lock a non-compliant PRD
- **Action:**
  1. During Phase 3, flag the conflict in brain
  2. Escalate to dreamer (policy vs. requirement trade-off decision)
  3. Wait for dreamer resolution
  4. If dreamer says: keep requirement, file policy exception (with reason)
  5. If dreamer says: drop requirement, update PRD
  6. Then lock PRD

#### Case 5: Requirement for "Trivial" One-Liner Change
- **Symptom:** "Change button color from blue to green" or "Update email domain"
- **Do NOT:** Skip intake because it's small
- **Action:**
  1. Run full intake (all mandatory questions per `intake-interrogate`)
  2. Question 4 (acceptance) will be simple: "button is green on all pages"
  3. Question 3 (contracts): "does green affect brand guidelines or accessibility?"
  4. Lock it. Small PRDs still need interrogation (catches hidden impacts).

### Intake Checklist

Before locking, verify:

- [ ] PRD document identified (or raw requirement captured)
- [ ] Ownership and stakeholder clear
- [ ] `/intake-interrogate` skill invoked (questions 1-8 asked)
- [ ] All 8 answers provided (no "TBD" or "TK")
- [ ] Answers are complete (not circular, not deferring decisions)
- [ ] Surfaces enumerated (web, app, backend, infra, admin)
- [ ] Contracts identified (API, events, cache, DB, search)
- [ ] Acceptance criteria quantified (not just "it works")
- [ ] Anti-goals explicit (what must NOT happen)
- [ ] Assumptions documented (and challengeable)
- [ ] No policy conflicts (or escalated to dreamer)
- [ ] PRD lock record created in brain (PRDLK decision ID)

## Edge Cases

### Edge Case 1: PRD is Vague but Stakeholders Insist on Proceeding
**Situation:** Requirements are ambiguous (e.g., "make the system faster" with no metrics), stakeholder demands we proceed immediately.

**Do NOT:** Lock a vague PRD. Vagueness creates divergent implementations.

**Action:**
1. During intake-interrogate, flag each vague answer
2. In Question 4 (acceptance criteria), demand concrete metrics ("faster by what %? in what timeframe?")
3. In Question 7 (constraints), identify what "fast enough" means
4. If stakeholder resists quantification: escalate as **NEEDS_CONTEXT**
5. Dreamer decides: clarify requirements or accept ambiguity risk
6. Lock only after vagueness is resolved or escalation is documented

---

### Edge Case 2: Required Context Unavailable (No Persona Data, No User Research)
**Situation:** Intake requires user research or persona data that doesn't exist or is stale.

**Example:** "Improve user onboarding" but persona definitions are 2 years old and no recent user interviews exist.

**Do NOT:** Proceed with outdated context. Requirements built on stale personas diverge from reality.

**Action:**
1. Flag the missing context during Question 1 (core problem) and Question 6 (success metrics)
2. Either:
   - **Option A:** Conduct fresh research/interviews before locking (timeline impact)
   - **Option B:** Escalate to dreamer with context gap (proceed with risk noted)
3. If Option B chosen: lock PRD with explicit assumption: "Context based on [date] personas; may need refresh post-launch"
4. Record decision in brain with context freshness date
5. Escalation keyword: **NEEDS_CONTEXT**

---

### Edge Case 3: Requirement Conflicts with Existing Product (Breaking Change Risk)
**Situation:** New requirement fundamentally changes existing behavior or breaks backwards compatibility.

**Example:** "Change password reset flow" but millions of users rely on existing flow; no deprecation plan exists.

**Do NOT:** Lock a breaking-change PRD without explicit approval and migration plan.

**Action:**
1. During intake, identify in Question 7 (constraints): "Does this break existing behavior? Who is affected?"
2. In Question 5 (anti-goals): explicit anti-goal: "Must not break current user flows without migration"
3. If breaking change is necessary:
   - Require rollback/deprecation plan (Question 7)
   - Require communication plan (who gets notified?)
   - Require phased rollout strategy (v1 with toggle, v2 deprecation, v3 removal)
4. Lock PRD with explicit breaking-change flag
5. Escalation keyword: **BLOCKED** (until migration plan is concrete)

---

Output: **PRD LOCKED** (ready for council) or **BLOCKED** (intake incomplete, policy conflict, cannot resolve vagueness) or **NEEDS_CONTEXT** (missing prerequisites, context unavailable)

---

### Edge Case 4: Stakeholder Answers Contradict Each Other Mid-Intake

**Symptom:** Question 3 answer (scope) conflicts with Question 7 answer (success criteria) — e.g., "no new UI" was agreed in scope, but success criteria includes a metric visible only in a UI component.

**Do NOT:** Accept both answers and defer the conflict to Council. Contradictions in the PRD create ambiguous contracts downstream.

**Action:**
1. Surface the contradiction explicitly: "Answer to Q3 says no new UI. Answer to Q7 requires a UI metric. These cannot both be true."
2. Ask the stakeholder to resolve: either expand scope to include UI, or change the success metric
3. Do not lock the PRD until the contradiction is resolved
4. Document the resolution in the PRD with a note: "Scope conflict between Q3 and Q7 resolved on [date]: [resolution]"
5. Escalation: **BLOCKED** if stakeholder cannot resolve the contradiction without external sign-off

---

### Edge Case 5: PRD Is Submitted for the Second Time with Scope Expansion

**Symptom:** A previously locked PRD for feature X is re-submitted with additional scope (e.g., "also add Y while we're at it"). The re-submission is framed as a minor update.

**Do NOT:** Treat scope expansion as an amendment. Any scope change to a locked PRD requires a full restart.

**Action:**
1. Reject the re-submission as a PRD amendment — locked PRDs are immutable
2. Create a new PRD for the new scope (Y), with its own intake run
3. Evaluate whether Y is a dependency of X or independent — if dependency, Y's intake must complete before X's council
4. If X's implementation is already in progress, assess impact of the new PRD on in-flight work
5. Escalation: **NEEDS_COORDINATION** — notify the dreamer that the in-flight feature may need to pause while Y's intake runs

---

## Checklist

Before claiming intake complete:

- [ ] All 8 intake questions answered (no skipped, no TBD answers)
- [ ] Scope boundaries explicitly defined
- [ ] Success criteria measurable and agreed upon
- [ ] PRD locked and written to brain
- [ ] Conductor notified that PRD is ready for Council

---
name: forge-intake-gate
description: HARD-GATE: Every PRD goes through intake (8 questions, locked). No skipping, no exceptions, no "trivial" PRDs.
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
| "I already talked to the user, I know what they want" | Conversation != interrogation. Intake asks the 8 questions conversation never gets to (contracts, edge cases, tradeoffs). |
| "The spec is already written and approved, intake is redundant now" | Approval without interrogation is not validation. Intake locks the spec, not stamps it. |
| "Intake will take too long, we need to move fast" | Intake takes 1-2 hours. Wrong implementation takes days. Fast wrong is slower than slow right. |
| "We can do intake retrospectively if something goes wrong" | Intake prevents the wrong. Retrospective interrogation doesn't undo shipped bugs. |
| "No one will notice if we skip intake on this one" | Skipping intake once makes it easy to skip twice. Systems degrade through exceptions. |
| "This is internal-only, not user-facing, so less rigor" | Internal changes affect platform reliability. Risk doesn't scale with audience. |

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **PRD is being handed to council before intake is complete** — Council requires a locked PRD. Intake produces the lock. Council before intake means negotiating on unvalidated assumptions. STOP. Complete intake and brain-write before council.
- **Any of the 8 intake questions has a "TBD" or blank answer** — An unanswered question is not a skipped question — it is an unknown risk that will surface at the worst moment. STOP. All 8 questions must have concrete answers before locking.
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
**ALWAYS invoke `/intake-interrogate` — do not paraphrase or summarize the 8 questions yourself.**

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
- **Input:** Answers to all 8 questions
- **Action:** Create PRD lock record in brain (decision ID: PRDLK-YYYY-MM-DD-HH)
  - Document each answer
  - Link to original requirement
  - Record who asked, who answered, timestamp
- **Output:** PRD LOCKED (status = frozen, ready for council)

### Validate Completeness
- **Check:**
  - All 8 questions answered (not skipped, not "TBD")
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
  1. Run full intake (all 8 questions)
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

Output: **PRD LOCKED** (ready for council) or **BLOCKED** (intake incomplete, policy conflict, cannot resolve vagueness)

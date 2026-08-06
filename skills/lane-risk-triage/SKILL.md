---
name: lane-risk-triage
description: "WHEN: A roadmap item exists and you need to decide, before any PRD gets written, whether it needs product/PM-led scoping (Scope-led) or is ready for Forge's build pipeline (Build-led) — and separately, how much execution rigor it needs (Risk Tier). Confidence-first: two gates decide the lane; blast radius decides the tier; the tier never decides the lane."
type: rigid
requires: [brain-write]
version: 1.0.0
preamble-tier: 2
triggers:
  - "which lane is this"
  - "is this scope-led or build-led"
  - "classify this roadmap item"
  - "how risky is this change"
allowed-tools:
  - Read
  - Bash
  - Write
  - AskUserQuestion
---

# Lane & Risk Triage

## Human input

**`AskUserQuestion`** is the canonical blocking-input tool — see [`skills/_shared/human-input.md`](../_shared/human-input.md). This skill asks at most 2 questions in sequence (Lane, then Risk Tier only if Build-led) — never bundle them into one prompt, since Risk Tier is only meaningful once Lane is settled.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "This touches sensitive/financial data, so it must be Scope-led" | **Blast radius is not a lane signal.** A high-risk item with an agreed outcome is still Build-led — it just gets a High-risk Risk Tier, which adds rigor to *how* Build-led runs, not who drives it. |
| "There's some disagreement, so let's call it contested" | Disagreement on **how** to implement an agreed outcome does not trip Gate 2. Gate 2 only trips when the **outcome itself** is contested — more than one legitimate stakeholder view on what "done" should look like. |
| "The team argued about this in a meeting, so it's obviously Scope-led" | Argument ≠ contested outcome. Check whether the disagreement is about the *what* (Gate 2) or the *how* (does not trip). If it's purely "how," it's Build-led with an open solution space. |
| "It's a small change, so we don't need to run both gates" | Size is not a gate. A one-line config change to a material user-facing behavior still trips Gate 1. Apply both gates to every item, regardless of perceived size. |
| "We'll decide the Risk Tier later, once it's built" | Risk Tier changes what the Solution Review before build must include — a dry-run + rollback plan, if High-risk. Deciding it after the build starts means the riskiest items got the least scrutiny at the point where scrutiny is cheapest. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
APPLY BOTH LANE GATES TO EVERY ROADMAP ITEM. EITHER GATE TRIPPING → SCOPE-LED. NEITHER TRIPPING → BUILD-LED.
RISK TIER IS ASSESSED SEPARATELY FROM LANE AND NEVER CHANGES THE LANE — IT ONLY CHANGES HOW MUCH RIGOR BUILD-LED EXECUTION REQUIRES.
A SCOPE-LED ITEM DOES NOT GET A prd-locked.md FROM THIS PIPELINE UNTIL ITS OUTCOME HAS BEEN DECIDED OUTSIDE FORGE AND IT RE-ENTERS AS A NEW, BUILD-LED ITEM.
```

## HARD-GATE

Do not skip triage for any roadmap item that is about to become a Forge PRD. **`intake-interrogate` MUST NOT run** until this skill has recorded `lane: build-led` for the item — running full intake on a Scope-led item produces a PRD for a decision nobody has actually made yet.

## Gate 1 — Is deciding the "what" the core deliverable?

Trips when the primary work of the item is a **material change to a user-facing experience or to how the team operates** — not just a side effect of an internal fix. Ask: if you handed a fully-specified answer to a developer today, would there be any real work left besides building it? If yes, the "what" isn't the hard part — Gate 1 does not trip.

## Gate 2 — Is the right outcome genuinely contested?

Trips when **more than one legitimate stakeholder view exists on what the correct outcome should be** — not just disagreement on how to get there. An open solution space where the goal is agreed but the implementation method is open does **not** trip this gate.

**Either gate trips → Scope-led.** Record the reason, do not proceed to `intake-interrogate`. This item needs product/PM-led scoping outside Forge before it can become a PRD.

**Neither trips → Build-led.** Proceed to Risk Tier assessment below, then to `intake-interrogate`.

## Risk Tier (Build-led items only)

Ask: **could a wrong first pass corrupt durable, shared-state data that is expensive or impossible to unwind** — the operator names what counts for their product (financial records, identity/attribution mappings, inventory ledgers, org-structure data, or anything else where corruption propagates beyond the one item)?

- **No →** `risk_tier: standard`. Normal Forge pipeline; `intake-interrogate` Q7's rollback plan is sufficient.
- **Yes →** `risk_tier: high-risk`. Downstream `tech-plan-write-per-project` MUST include a documented dry-run-on-a-copy approach and a staged-rollout plan with an explicit validation checkpoint before `tech-plan-self-review` can PASS.

## Red Flags — STOP

- **Classifying by blast radius instead of the two gates** — STOP. Re-run Gate 1 and Gate 2 on their own terms; assess Risk Tier separately afterward.
- **Skipping straight to `intake-interrogate` without a recorded lane** — STOP. No PRD gets written for an item that hasn't been triaged.
- **Calling an item Scope-led because deciding the *how* is hard** — STOP. Gate 2 is about the outcome, not the implementation path. A hard, wide-open solution space with an agreed goal is still Build-led.
- **Assessing Risk Tier before Lane is settled** — STOP. Risk Tier is meaningless for a Scope-led item that has no build yet.

## Workflow

1. **Silent audit first:** Read the roadmap item's description (and any linked doc). Assess Gate 1 and Gate 2 against the definitions above.
2. **High confidence:** If the item text makes the answer to both gates unambiguous, pre-fill the classification and cite the passage — do not ask.
3. **Low confidence:** If either gate is genuinely unclear, ask **one** `AskUserQuestion` covering both gates together (they're tightly coupled — the same "what does done look like, and who might disagree" answer resolves both).
4. **Lane decided.** If Scope-led: write the lock file with `lane: scope-led` and the reason, and STOP — do not proceed to intake.
5. **If Build-led:** assess Risk Tier (ask if unclear; infer if the item text explicitly names financial/identity/attribution/org-mapping data).
6. **Write the lock file** (see Output) and hand off to `intake-interrogate`.

## Edge Cases & Fallback Paths

### Edge Case 1: An item looks Build-led but the developer discovers mid-build that the outcome is actually contested

**Diagnosis**: During `tech-plan-write-per-project` or dispatch, it becomes clear stakeholders disagree on what the right outcome even is — Gate 2 should have tripped.

**Response**: STOP the build. Re-open this skill, re-run Gate 2 with the new information, and if it now trips, downgrade to Scope-led — write an updated lock file and escalate to the human with the specific disagreement found.

**Escalation**: Treat as NEEDS_CONTEXT, not a build failure. The classification was wrong, not the code.

### Edge Case 2: Risk Tier is ambiguous — the item touches sensitive data but corruption would be trivially reversible

**Diagnosis**: E.g., a cosmetic display field sourced from financial data, where a wrong value is visible but a redeploy fixes it instantly with no downstream propagation.

**Response**: Ask explicitly: "if this is wrong for a day, what has to happen to fix it, and does anything else depend on the wrong value in the meantime?" Tier by the answer, not by the data category alone.

**Escalation**: If truly unclear, default to `high-risk` — the cost of over-tiering (more review) is bounded; the cost of under-tiering a real corruption is not.

### Edge Case 3: Multiple roadmap items share a data layer

**Diagnosis**: Several Build-led items touch the same identity/attribution/schema surface.

**Response**: Note the shared surface in each item's lock file (`shared_data_layer_with: [other-task-ids]`) so `tech-plan-write-per-project` can sequence them as one workstream rather than risking conflicting first passes on the same data.

**Escalation**: Recommend, don't force, sequencing — the human may have reasons to run them independently.

## Output

Write `~/forge/brain/prds/<task-id>/lane-lock.md`:

```markdown
# Lane & Risk Lock

**Item:** <roadmap item title>
**Gate 1 (what is the deliverable?):** tripped=<yes|no> — <one-line reason, cite source>
**Gate 2 (is the outcome contested?):** tripped=<yes|no> — <one-line reason, cite source>
**Lane:** <scope-led|build-led>

<!-- Build-led only, below -->
**Risk Tier:** <standard|high-risk>
**Risk Tier reason:** <one line — what data, what's the corruption/reversal cost>
**shared_data_layer_with:** <other task-ids, or none>

**Locked by:** [Claude]
**Date:** <ISO8601>
**Next:** <intake-interrogate | product/PM-led scoping (outside Forge) — item is not Forge-ready>
```

If `lane: scope-led`, stop here — do not write a `prd-locked.md`, do not invoke `intake-interrogate`. If `lane: build-led`, hand `lane-lock.md` to `intake-interrogate`, which reads `risk_tier` to scale Q7's rollback-plan rigor.

## Commit

```bash
git -C ~/forge/brain add prds/<task-id>/lane-lock.md
git -C ~/forge/brain commit -m "triage: lock lane/risk for <task-id>"
```

## Cross-References

- `intake-interrogate`: Only runs after this skill records `lane: build-led`; reads `risk_tier` to scale Q7's rollback-plan rigor.
- `tech-plan-write-per-project`: When `risk_tier: high-risk`, must include a dry-run-on-a-copy approach and staged-rollout validation checkpoint before `tech-plan-self-review` can PASS.
- `conductor-orchestrate`: Runs this skill as State 0, before State 1 (Intake) — see `reference/conductor-reference.md`.
- `brain-write`: Persists `lane-lock.md` with provenance.

---
name: intake-interrogate
description: WHEN to invoke: You've been given a PRD for a multi-repo product and need to lock scope, success criteria, and contracts. Asks 5–8 clarifying questions one at a time.
type: rigid
requires: [brain-write]
---

# Intake Interrogation — PRD Lock

## Anti-Pattern: "I Can Infer This"

You cannot. The biggest projects fail because teams assume they agree on a spec and discover otherwise in code review. Intake enforces lock. No exceptions. No "trivial" shortcuts.

## HARD-GATE

Do not skip intake. Every PRD goes through this. No matter how simple it seems.

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Any question is answered with "TBD" or "we'll figure it out later"** — Unanswered questions become undiscovered requirements. STOP. Get the answer now or the PRD cannot be locked.
- **Agent fires multiple questions in a single message** — Simultaneous questions produce short answers. STOP. One question at a time, always.
- **Product slug is not found in `~/forge/brain/products/`** — PRD references an unregistered product. STOP. Register the product or ask the user to provide forge-product.md before proceeding.
- **Success criteria is stated in vague terms ("fast", "good UX", "reliable")** — Unmeasurable criteria cannot be evaluated. STOP. Get specific, testable criteria (e.g., "< 200ms p99 latency") before locking.
- **Rollback plan is "just redeploy the old version"** — Not a real rollback plan for schema changes, cache migrations, or event stream additions. STOP. Get a concrete rollback procedure.
- **User skips a question saying "that's not relevant"** — Every question was added because of a real project failure. STOP. Ask the question anyway; the user decides what's in scope, not which questions get asked.
- **PRD is locked without brain-write recording the decision** — The lock exists only in chat context and will be lost. STOP. Write to brain before calling PRD locked.

## Process

1. **One question at a time** — ask, wait for answer, move to next. No multi-question dumps.
2. **Multiple-choice preferred** — easier to answer than open-ended.
3. **Lock answers** — write each to `prd-locked.md` as you go.
4. **Converge on consensus** — get the answer in the user's own words, write it back, confirm.

## Questions (in order)

**Q1: Which product?**
"This PRD affects which product? (e.g., 'ShopApp', 'InvoicingPlatform')"
→ Look up the product in `~/forge/brain/products/<slug>/product.md` to validate it exists.
→ If not found, ask user to provide `forge-product.md` or register the product first.

**Q2: What's the one-sentence goal?**
"In one sentence, what is this PRD trying to ship?"
→ Lock the answer.

**Q3: Success criteria?**
"How will you know this shipped successfully? (e.g., 'user can log in with 2FA', 'search returns results under 100ms')"
→ 2–3 criteria. Lock them.

**Q4: Which repos will change?**
"Which repos from [product list] will this PRD touch? (List 2–5 expected repos)"
→ Validate against product.md. Flag if a repo is mentioned but not in product.md.
→ Lock the list.

**Q5: Any contract changes?**
"Will this PRD require changes to any contracts? (API endpoints, DB schema, event schemas, cache keys, search indexes)"
→ Examples: "REST API v2 migration", "Add Order event to Kafka", "New MySQL table"
→ Lock the contracts affected.

**Q6: What's the timeline?**
"When does this need to ship? (e.g., 'by EOW', 'no hard deadline')"
→ Lock the date or note "no hard deadline".

**Q7: Rollback plan?**
"If this breaks prod, how do we roll it back? (e.g., 'API v1 is still live', 'DB migration is backward-compat')"
→ Lock the rollback strategy.

**Q8: Success metrics?**
"How will you measure if this succeeded post-launch? (e.g., 'login rate > 90%', 'search latency < 500ms')"
→ Lock the metrics.

## Output

Write all answers to `~/forge/brain/prds/<task-id>/prd-locked.md`:

```markdown
# PRD Locked

**Product:** ShopApp  
**Goal:** Users can log in with two-factor authentication.  
**Success Criteria:**
- Users can enable 2FA in settings
- Login requires 2FA code if enabled
- 2FA code delivered via SMS in < 5 seconds

**Repos Affected:**
- backend-api
- web-dashboard
- app-mobile

**Contracts Affected:**
- REST: Add POST /auth/2fa/enable, POST /auth/2fa/verify
- MySQL: Add user_2fa_enabled bool, user_2fa_secret string
- Redis: 2fa_codes key for temp storage, 5min TTL

**Timeline:** EOW  
**Rollback:** API v1 is still live, 2FA is optional, no DB breaking changes.  
**Success Metrics:** 2FA adoption > 50% within 2 weeks.

---

**Locked by:** [Claude]  
**Date:** 2026-04-08  
**Ready for:** Council reasoning
```

## Edge Cases & Fallback Paths

### Edge Case 1: User answers are contradictory (Q2 vs Q3, or Q5 vs Q7)

**Diagnosis**: User says goal is "Add 2FA" (Q2), but success criteria is "Users can log in without 2FA" (Q3). Or contracts affected are "Add DB table" but rollback plan is "No breaking changes".

**Response**:
- **Detect**: Flag the contradiction explicitly.
- **Read back**: "I hear you want [Q2 answer] but success looks like [Q3 answer]. These seem incompatible. Can you clarify which one is correct?"
- **Wait for clarification**: Don't write to `prd-locked.md` until contradiction is resolved.
- **Reword**: Once clarified, rewrite both answers to be consistent.
- **Document**: Note in prd-locked.md: "Clarification required on [question]. Original answers were contradictory; locked version reflects [final answer]."

**Escalation**: If user cannot resolve contradiction (e.g., "I don't know, let me ask stakeholders"), escalate to NEEDS_CONTEXT. Pause intake until user returns with clarified answers.

---

### Edge Case 2: PRD changes during intake (scope expands mid-interrogation)

**Diagnosis**: While answering Q3 (success criteria), user adds three new requirements that weren't in the original PRD. "Actually, we also need..." scope creep.

**Response**:
- **Detect**: Flag the scope expansion.
- **Clarify**: "Original PRD scope was [original list]. You've now added [new items]. Is this still one task, or should we split into two?"
- **Options**:
  1. **Accept scope expansion**: Revise answers. Document what changed and why.
  2. **Defer new items**: "Let's ship original scope. New items become a separate PRD."
- **Decision**: User chooses. Write final answers to prd-locked.md with note about scope decision.

**Escalation**: If scope expands significantly (e.g., goes from 1 repo to 5 repos), escalate to user: "Scope has tripled. Recommend: split into two PRDs. Proceed with Phase 1 only?"

---

### Edge Case 3: Eight questions reveal infeasibility (Q4 + Q5 + timeline = impossible)

**Diagnosis**: During Q4-Q6, you realize: repos needed are not owned by team, contracts required are incompatible with existing code, and timeline is 1 week. Task is infeasible.

**Response**:
- **Escalate early**: "I've locked answers to Q4-Q6. Based on this, the task appears infeasible: [specific blockers]. Recommend: discuss with stakeholders before council."
- **Don't force lock**: If you have genuine concerns about feasibility, report them.
- **Escalation paths**:
  1. User acknowledges infeasibility, task is canceled or descoped.
  2. User says constraints can be changed (e.g., timeline extended, repos reassigned), revise answers.
  3. User insists on proceeding despite concerns, lock as-is with escalation note.

**Escalation**: NEEDS_CONTEXT - Feasibility concern raised. User must decide: proceed, descope, or reschedule.

---

### Edge Case 4: Product doesn't exist in brain (Q1 lookup fails)

**Diagnosis**: User says PRD affects "AlphaProduct", but `~/forge/brain/products/alpha-product/` doesn't exist.

**Response**:
- **Ask**: "Product 'AlphaProduct' not found in brain. Do you have a `forge-product.md` for this? If not, we need to register it first."
- **Options**:
  1. **User provides product file**: Import it. Validate repos and surfaces are defined.
  2. **User says "I'll register it later"**: Cannot proceed. Intake requires valid product. Escalate.
  3. **User wants to continue anyway**: Document risk in prd-locked.md: "Product not registered. Proceeding with unvalidated product definition."

**Escalation**: BLOCKED - Cannot lock PRD without validating product exists. Route to product registration or ask user to provide product.md.

---

### Edge Case 5: User cannot identify affected contracts (Q5)

**Diagnosis**: User says "I don't know if this affects contracts" or "Maybe? Not sure". No clear contracts identified.

**Response**:
- **Clarify**: "Contracts include: REST API changes, database schema changes, event schemas, cache keys, search indexes. Does this PRD touch any of those?"
- **Guiding questions**:
  - "Will this PRD create new endpoints or modify existing ones?" → Contract: REST API
  - "Will this PRD add/modify database tables or columns?" → Contract: MySQL schema
  - "Will this PRD publish or consume events?" → Contract: Event schema
  - "Will this PRD use cache or change cache patterns?" → Contract: Cache keys
- **If still unclear**: Lock as "Contracts: TBD - to be determined during council reasoning". Escalate to council to investigate.

**Escalation**: If contracts truly cannot be identified, proceed with "TBD" in lock. Council will discover them during reasoning.

---

### Edge Case 6: Timeline is vague ("ASAP", "no hard deadline", or conflicting urgencies)

**Diagnosis**: User says "ASAP" but also "no hard deadline". Or says "ship by EOW" but also "low priority".

**Response**:
- **Push for clarity**: "I need a specific date or clear relative priority. Is this EOD? EOW? Next month? Or is timing flexible?"
- **Lock specific date**: "Let's lock this as: [specific date] OR [no deadline, low priority]."
- **Document assumptions**: Note in prd-locked.md: "Timeline: EOW (March 15). If date slips, impacts [downstream work/no impact]."

**Escalation**: If user cannot commit to a timeline, lock as "No hard deadline" and note that this affects prioritization against other work.

---

## Commit

After locking all 8 questions, commit the prd-locked.md:

```bash
git -C ~/forge/brain add prds/<task-id>/prd-locked.md
git -C ~/forge/brain commit -m "intake: lock PRD for <task-id>"
```

Next: Council reasoning to negotiate contracts across surfaces.

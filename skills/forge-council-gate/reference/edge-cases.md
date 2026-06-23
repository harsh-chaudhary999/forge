# forge-council-gate — Additional Edge Cases

## Additional Edge Cases

### Edge Case 1: Surfaces Cannot Reach Consensus (Deadlock, Split Vote)
**Situation:** Two or more surfaces have irreconcilable positions. Backend insists on schema X, web insists on schema Y, neither will move.

**Example:** Backend: "Single monolithic table for performance"; Web: "Normalized tables for flexibility" — both have valid technical reasons.

**Do NOT:** Pick one arbitrarily. Deadlock is a signal that the decision matters and needs authority to resolve.

**Action:**
1. Document both positions in detail:
   - Backend proposal + rationale + performance metrics
   - Web proposal + rationale + usability concerns
   - Why they conflict (what's the core trade-off?)
2. Escalate to dreamer (architectural decision, not engineering compromise)
3. Dreamer evaluates trade-off space:
   - Can we hybrid? (partial normalization, compromise schema)
   - Which is right for product strategy?
   - Cost-benefit of each approach?
4. Dreamer decides; record decision in brain (SPECLOCK with arbitration noted)
5. Return to council with dreamer decision, lock spec
6. Escalation keyword: **NEEDS_COORDINATION** (surfaces can't self-resolve)

---

### Edge Case 2: Stakeholders Appear or Disappear Mid-Council (Attendance Conflict)
**Situation:** Required stakeholder or surface representative is unavailable during council session.

**Example:** Infra engineer called to incident; web stakeholder dropped off call; new requirement surfaces from product who wasn't initially consulted.

**Do NOT:** Proceed with incomplete council. Missing surface = missing constraints, vetos, requirements.

**Action:**
1. Identify who is missing and why (unavailable, didn't attend, left mid-session)
2. If critical path surface is missing:
   - Pause council
   - Reschedule with all attendees present
   - Do NOT make agreements without complete representation
3. If new stakeholder surfaces mid-council:
   - Add them to session (represent their surface concerns)
   - May require re-negotiating contracts to account for their input
   - Document late entry in brain (why they joined late)
4. Lock spec only after all 4 surfaces have been heard AND agree
5. Escalation keyword: **BLOCKED** (incomplete council, must reschedule with full attendance)

---

### Edge Case 3: Conflict Unresolvable in One Council Session (Needs Multiple Rounds)
**Situation:** Council runs but key conflicts surface late. Surfaces need time to research alternatives or consult external teams. One session is insufficient.

**Example:** "This API contract requires infrastructure we haven't built yet; we need 2 days to scope the work" — valid concern, but not resolvable in 1-hour council.

**Do NOT:** Force consensus under time pressure. Premature lock creates technical debt later.

**Action:**
1. Acknowledge the conflict is real and important
2. Identify what needs to be resolved in the gap:
   - Infrastructure feasibility study?
   - Design exploration of hybrid approach?
   - Consultation with external team?
3. Plan the follow-up:
   - Who owns the research/design?
   - Timeline (target: 2-3 days max)
   - What will be brought to council round 2?
4. Document in brain: "SPECLOCK pending" + list of open items
5. Schedule council round 2 (with same attendees + research results)
6. In round 2: resolve conflicts using research/designs, lock spec
7. Escalation keyword: **NEEDS_COORDINATION** (multi-round negotiation required)

---

Output: **SPEC LOCKED** (ready for per-project tech planning) or **BLOCKED** (deadlock without dreamer input, incomplete attendance, unresolvable conflict awaiting follow-up research)

---

### Edge Case 4: Surface Produces a Contract That Conflicts with an Existing Brain Decision

**Symptom:** The backend surface proposes a new REST API contract (e.g., `POST /auth/mfa/enable`) but a prior brain decision D007 defines `POST /auth/2fa/setup` for the same intent. The new contract would create a naming collision or semantic overlap.

**Do NOT:** Allow the new contract to land without resolving the conflict with the prior decision.

**Action:**
1. Load the prior decision with `brain-read` — read D007 in full, including its rationale
2. If the new contract is compatible (different resource, different intent), proceed — document the distinction
3. If the new contract supersedes D007, invoke `brain-forget` to retire D007 and document the supersession reason
4. If the contracts conflict (same resource, different semantics), surface the conflict to all surfaces before locking
5. Escalation: **NEEDS_CONTEXT** — the surface that proposed the conflicting contract must justify why the prior decision is being overridden

---

### Edge Case 5: Spec Is Locked but a Surface Later Discovers It Cannot Implement Its Contract

**Symptom:** Council locked the spec with `shared-dev-spec.md`. Two days later, the mobile surface discovers the agreed event bus contract requires a native library not available on iOS.

**Do NOT:** Let the surface silently deviate from the spec during implementation. And do NOT let it quietly drop the feature.

**Action:**
1. This is a post-lock discovery — requires a council amendment, not an implementation decision
2. The surface raises a `council_amendment` request to the dreamer: "iOS cannot implement X because Y"
3. If the amendment is minor (alternative protocol, same semantics), run a focused council re-negotiation between the mobile and infra surfaces only
4. If the amendment is significant (feature scope changes), re-run full council for affected contracts
5. Escalation: **NEEDS_COORDINATION** — all surfaces must acknowledge the amendment before implementation continues

---

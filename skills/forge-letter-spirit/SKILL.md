---
name: forge-letter-spirit
description: HARD-GATE: Follow both letter AND spirit. No rationalizations, no shortcuts, no exceptions.
type: rigid
---
# Letter Equals Spirit (Foundational)

**Rule:** No rationalizations. Follow both the letter (exact wording) and the spirit (intent).

## Anti-Pattern Preamble: Why Agents Rationalize Away Rules

| Rationalization | The Truth |
|---|---|
| "The rule says X, but the spirit is Y, so I'll do Y instead of X" | If letter and spirit diverge, you've misunderstood the rule. Do both or escalate. Never pick one. |
| "This exception is too small to matter, so I can skip this rule" | Small exceptions compound. The second exception is easier to rationalize. By the fifth, the rule is dead. No exceptions. |
| "The spirit of this rule doesn't apply here because this situation is different" | Situations are always different. That's not an exception, that's reality. The rule still applies. If it doesn't, escalate. |
| "I understand the rule well enough that I don't need to follow it exactly" | Understanding does not equal compliance. Follow exactly or your understanding is incomplete. |
| "We've broken this rule before and nothing bad happened" | Empirical luck is not a safety margin. The probability of harm doesn't decrease because past violations succeeded. Follow the rule. |
| "The rule is old, we've evolved past needing it" | Rules persist for reasons you may not see. Violate only after explicit escalation and decision to retire the rule. |
| "The letter requires X but that's inefficient, I'll do Y instead" | Inefficiency is the cost of compliance. If the cost is too high, escalate; don't rationalize away. |
| "The spirit wants us to be careful, I'm being careful, so the letter is optional" | Being careful is not the same as following the rule. Both are required. Careful AND compliant. |
| "This is internal-only, the rule doesn't apply to internal work" | The rule is unchanged by audience. Apply the rule everywhere or retract the rule. No hidden exceptions. |
| "The rule is a good-to-have, not a must-have, so I can skip it if pressed for time" | No rule is a good-to-have in Forge. All rules are must-haves. If time pressure is real, escalate (don't rationalize). |

## Detailed Workflow

### Understand the Rule (Letter + Spirit)

For any rule or gate:

1. **Read the letter** (exact wording)
   - What does it say I must do? (not interpret, not guess)
   - What are the explicit requirements?

2. **Understand the spirit** (intent)
   - Why does this rule exist?
   - What problem is it preventing?
   - What is the rule protecting?

3. **Reconcile** (both must be true)
   - If letter and spirit are aligned: proceed (both satisfied)
   - If letter and spirit diverge: escalate (see Phase 4)

### Apply the Rule (No Shortcuts)

**Example 1: Verification gate (forge-verification)**
- Letter: "Run verification command, see output, then claim success"
- Spirit: "Evidence of actual correctness, not confidence"
- Application: Run command (not assume), observe output (not predict), claim only when visible proof exists
- Shortcut temptation: "Tests must pass, I trust them, I don't need to run them"
- Correct response: No. Run anyway. See output.

**Example 2: Intake gate (forge-intake-gate)**
- Letter: "Every PRD goes through intake (8 questions, locked)"
- Spirit: "Discover hidden assumptions, lock requirements before building"
- Application: Ask all 8 questions (not 4), lock answers (not "TBD"), ensure completeness
- Shortcut temptation: "This is a simple feature, the requirements are obvious"
- Correct response: No. Ask all 8. Simple features often hide complex requirements.

**Example 3: Worktree gate (forge-worktree-gate)**
- Letter: "Every task gets fresh worktree"
- Spirit: "Isolation prevents cross-contamination and reveals hidden dependencies"
- Application: Create new worktree per task (not reuse), fresh environment (not shared node_modules)
- Shortcut temptation: "My change is tiny, I can work in main"
- Correct response: No. Fresh worktree. Isolation is non-negotiable.

### Recognize Rationalization Patterns

Common rationalizations and how to reject them:

| Pattern | Sound Rejection |
|---|---|
| "This is [special case], the rule doesn't apply" | The rule applies to all cases. If this case is truly exceptional, escalate. Don't unilaterally carve out exceptions. |
| "We've done this before, it was fine" | Past success is not future permission. Comply with the current rule. |
| "The letter says X but I'll do Y because it's faster/easier" | Compliance is not negotiable for speed. Escalate if deadline is unrealistic. |
| "The rule is meant to prevent Z, not Y, so it doesn't apply here" | If you understand the rule's scope better than the rule writer, escalate. Don't self-interpret exceptions. |
| "I can skip this because I'll be extra careful" | Vigilance ≠ compliance. Do both. No shortcuts. |
| "Just this once, I'll break this rule, then go back to following it" | Rules do not have "just this once" clauses. Violating once makes violating twice easier. Comply always. |

### When Letter and Spirit Conflict (Escalation Path)

**If letter and spirit truly diverge:**

1. **Document the conflict** (in brain, decision ID: LTSP-YYYY-MM-DD-HH)
   - Exact wording of the letter
   - Stated or inferred spirit
   - Why they conflict
   - Impact if you follow letter only
   - Impact if you follow spirit only

2. **Do NOT choose** (don't rationalize away either one)

3. **Escalate to dreamer** (architecture/policy decision)
   - Present the conflict
   - Request clarification (which takes precedence?)
   - Or request rule revision (if rule itself is flawed)

4. **Wait for decision**
   - Dreamer clarifies: "Follow letter, spirit is secondary" or vice versa
   - Or dreamer revises rule to remove ambiguity
   - Document decision (link in brain)

5. **Then comply** (with clarified rule)

### Auditing Compliance

To verify you're not rationalizing:

- **Check 1:** Are you breaking the rule to gain speed/convenience? (If yes: stop, escalate if time pressure is real)
- **Check 2:** Are you redefining "this situation is different"? (If yes: stop, the rule applies)
- **Check 3:** Are you trusting your understanding over the rule? (If yes: stop, follow rule exactly)
- **Check 4:** Have you seen this exception rationalized before? (If yes: stop, this is a slippery slope)
- **Check 5:** Would you accept this exception if someone else was violating? (If no: stop, don't violate yourself)

### Edge Cases & Fallback Paths

#### Case 1: Rule Explicitly States Exception (e.g., "Except in emergency")
- **Situation:** Rule says "X is required, except in emergency"
- **Do NOT:** Declare yourself in emergency without evidence
- **Action:**
  1. Verify emergency condition is actually true (objectively, not felt)
  2. Document emergency in brain (with timestamp, impact, reason)
  3. Follow letter while in emergency (use explicit exception)
  4. After emergency resolves: return to normal rule compliance
  5. Review how to prevent future emergencies

#### Case 2: Rule Conflicts with Team Pressure (Deadline, Stakeholder Urgency)
- **Situation:** "Team says we don't have time for intake gate"
- **Do NOT:** Rationalize skipping intake because of pressure
- **Action:**
  1. State the rule: "Intake is non-negotiable"
  2. Acknowledge pressure: "I understand the deadline is tight"
  3. Present the trade-off: "Intake takes 2 hours, but missing it risks 4 days of rework"
  4. Escalate to dreamer if pressure persists: "Deadline vs. quality trade-off"
  5. Let dreamer decide (not you)

#### Case 3: Rule Conflicts with Technical Constraint (Can't Meet Letter in Current Setup)
- **Situation:** "We can't run eval because CI/CD is down, should we skip eval gate?"
- **Do NOT:** Rationalize skipping eval because infrastructure is unavailable
- **Action:**
  1. Restore infrastructure (fix CI/CD)
  2. If infrastructure cannot be restored: escalate as BLOCKED
  3. Do not ship without meeting the gate
  4. Escalate to dreamer for trade-off decision (quality vs. timeline)

#### Case 4: Rule Seems to Conflict with Another Rule
- **Situation:** "Worktree gate says create fresh worktree; but coordination gate says reuse worktree for dependencies"
- **Do NOT:** Resolve yourself by picking one rule over another
- **Action:**
  1. Document both rule requirements
  2. Identify: do they actually conflict, or are they for different scenarios?
  3. If true conflict: escalate to dreamer (clarify rule hierarchy)
  4. Follow dreamer's guidance

### Compliance Checklist

Before claiming compliance, verify:

- [ ] Rule letter is understood (exact wording, explicit requirements)
- [ ] Rule spirit is understood (intent, problem being prevented)
- [ ] Letter and spirit are aligned (or escalated if conflict)
- [ ] Rule is being applied without exceptions (no shortcuts, no rationalizations)
- [ ] No pattern-matching to past violations ("we did it before")
- [ ] No redefining of rule scope ("this situation is different")
- [ ] No trading compliance for speed ("I don't have time")
- [ ] If pressure exists: escalated to dreamer (not rationalized away)
- [ ] Escalation documented in brain (if any conflict or pressure)

Output: **COMPLIANT** (rule followed, both letter and spirit) or **ESCALATED** (letter/spirit conflict, pressure, or constraint preventing compliance)

---
name: forge-letter-spirit
description: "WHEN: A Forge rule or skill is being applied. HARD-GATE: Follow both letter AND spirit. No rationalizations, no shortcuts, no exceptions."
type: rigid
version: 1.0.0
preamble-tier: 2
triggers:
  - "check rule application"
  - "letter vs spirit"
  - "is this in the spirit of the rule"
allowed-tools:
  - Bash
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
| "Vague scale (~60+ items) is honest enough for scans / plans / tests" | **Not honest enough.** Letter **and** spirit require **what / where / how** — paths, anchors, commands — not counts alone. **AGENTS.md** / **CLAUDE.md** — *Written artifacts — precision*. |
| "The export / file is 5k–8k lines — I'll sample or skip the heavy step" | **Violation** unless that **exact** sampling is prescribed by the skill. **Size is not a skip lever** — complete the instruction set or **BLOCKED** with evidence. **AGENTS.md** Core rule **6**. |

## Iron Law

```
FOLLOW BOTH THE LETTER AND THE SPIRIT. A TECHNICALLY COMPLIANT SHORTCUT THAT VIOLATES INTENT IS A VIOLATION. RATIONALIZATIONS DO NOT BECOME EXCEPTIONS.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Agent says "technically the rule says X but…"** — The word "but" is the start of a rationalization. STOP. Either follow the rule exactly or escalate. No alternatives.
- **Agent invokes the "spirit" of a rule to skip a step in the "letter"** — Spirit is not a license to modify letter. Both must be followed. STOP. Do both or escalate.
- **A rule is silently applied to only some situations** — Selective compliance is non-compliance. STOP. Apply every rule in every context it covers, without exception.
- **A HARD-GATE step is labeled "optional for this case"** — HARD-GATE means non-optional. There is no case where a HARD-GATE is optional. STOP. Follow the HARD-GATE or escalate to human.
- **Repeated past exceptions are cited as precedent** — Prior violations are not a precedent. They are prior violations. STOP. Follow the rule today regardless of what happened before.
- **Agent proceeds without understanding why the rule exists** — Rules without understood intent are the first to be rationalized away. STOP. Read the rule until you understand both letter and intent.

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
- Letter: "Every PRD goes through intake (mandatory lock fields in prd-locked.md, confidence-first elicitation)"
- Spirit: "Discover hidden assumptions, lock requirements before building"
- Application: Satisfy every mandatory lock field (not "TBD"); ask **doubts and low-confidence gaps**, not a ritual questionnaire when the PRD already states the answer
- Shortcut temptation: "This is a simple feature, the requirements are obvious"
- Correct response: No. Still run **intake** and satisfy **mandatory lock fields** — but **probe doubts** (contracts, rollback, Q4 mismatch, Q9 implementability) even when the PRD “looks obvious”; do not equate “simple” with “skip locking.”

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

## Additional Edge Cases

### Edge Case 1: Spec Is Ambiguous (Letter and Spirit Diverge)
**Situation:** Rule text is unclear or contradictory. Literal reading conflicts with apparent intent.

**Example:** Spec says "validate user input" (letter is vague). Spirit seems to be "reject invalid formats" but could also mean "coerce to valid format". Both are valid interpretations.

**Do NOT:** Guess which interpretation is correct. Ambiguity breaks compliance.

**Action:**
1. Document the ambiguity:
   - Exact wording of spec
   - Possible interpretations of letter
   - What spirit seems to be
   - Why they conflict
2. Escalate to spec-owner (dreamer or council):
   - Ask for clarification: which interpretation is correct?
   - Or ask to revise spec to remove ambiguity
3. Wait for clarification before proceeding
4. Once clarified: document decision in brain
5. Then comply with clarified spec (both letter and spirit)
6. Escalation keyword: **NEEDS_CONTEXT** (spec ambiguous, need clarification)

---

### Edge Case 2: Strict Letter Compliance Breaks Spirit (Rule Technically Met, Outcome Wrong)
**Situation:** Code technically satisfies the letter of the rule/spec but violates the spirit/intent.

**Example:** 
- Spec: "Cache invalidation when user data changes"
- Letter interpretation: invalidate cache on ANY data change (even unrelated fields)
- Spirit: invalidate only relevant data (e.g., if user's email changes, invalidate email cache, not order cache)
- Code: invalidates entire cache on any change (technically compliant, but wasteful and violates spirit)

**Do NOT:** Ship code that technically complies but violates intent.

**Action:**
1. Identify: what is the spirit of the rule? (Why does the rule exist?)
   - Cache invalidation spirit: "avoid stale data without excessive invalidation"
   - Code: "invalidate everything" violates this spirit (excessive invalidation)
2. Re-implement to satisfy both letter and spirit:
   - Invalidate only relevant cache entries
   - Document the distinction in code comments
3. Escalate if letter cannot be satisfied AND spirit must be broken:
   - Escalation keyword: **NEEDS_COORDINATION**
   - Dreamer clarifies: which is more important?
4. Document decision in brain: what was changed, why, reasoning

---

### Edge Case 3: Spirit Requires Breaking Letter (Backwards Compatibility Impossible)
**Situation:** Rule requires breaking change but spirit is about "gradual, non-breaking evolution".

**Example:**
- Rule: "All user IDs must be 64-bit integers"
- Letter: change current string IDs to integers (breaking change)
- Spirit: "maintain backwards compatibility"
- Letter and spirit conflict directly

**Do NOT:** Rationalize away one or the other. Escalate.

**Action:**
1. Document the conflict:
   - Letter requirement (64-bit integer IDs)
   - Spirit (backwards compatible)
   - Why they cannot both be true
2. Propose solutions that satisfy both:
   - Option A: Support both string and integer IDs (dual mode)
   - Option B: Deprecation period (string IDs → integer IDs gradually)
   - Option C: Phased rollout with feature flags
3. If no hybrid solution exists:
   - Escalate to dreamer: which is more important?
   - Dreamer decides: letter takes precedence, or spirit takes precedence
4. Implement according to dreamer decision
5. Document decision in brain: what was chosen, why, reasoning

---

Output: **COMPLIANT** (rule followed, both letter and spirit aligned) or **ESCALATED** (letter/spirit conflict requiring clarification, pressure, or architectural constraint preventing compliance)

---

### Edge Case 4: New Forge Version Changes the Spirit of an Existing Rule

**Symptom:** A rule in CLAUDE.md says "no hardcoded delays" (letter). The spirit was originally "prevent flaky tests." A new Forge update adds context: the rule now explicitly allows hardcoded delays in integration teardown steps where services need time to flush. An agent enforcing the old spirit would reject valid teardown code.

**Do NOT:** Apply the spirit as remembered from a prior session — spirits evolve with rule updates.

**Action:**
1. Always read the current CLAUDE.md before evaluating any rule compliance
2. If a new clarification changes the spirit, update your enforcement: the clarification is authoritative
3. If existing brain decisions were made under the old spirit, flag them as potentially stale: "D019 was decided under the old spirit of this rule — may need re-evaluation"
4. Do not retroactively re-enforce old spirit against code that was already approved under the new interpretation
5. Escalation: NEEDS_CONTEXT if the rule update's intent is unclear — ask the dreamer before enforcing a changed spirit

---

### Edge Case 5: Rule Letter Is Clear but Spirit Is Silent on the Current Scenario

**Symptom:** Rule says "commit after every task" (letter clear). The spirit is presumably "maintain reviewable history." But the current scenario is a hotfix where 5 one-line changes to the same file are needed. Should they be 5 commits or 1?

**Do NOT:** Invent a spirit interpretation that overrides the letter without evidence.

**Action:**
1. When the spirit is silent on the specific scenario, default to following the letter exactly
2. Only deviate from the letter if applying it literally produces an outcome that clearly contradicts the stated purpose of the rule
3. For the hotfix example: 5 commits is correct per the letter — one commit per task. The spirit (reviewable history) is served by 5 focused commits, not violated
4. If you believe the letter is producing a bad outcome, escalate to the dreamer for explicit guidance rather than self-interpreting the spirit
5. Escalation: NEEDS_CONTEXT — request the dreamer's preference when the spirit is genuinely ambiguous for the scenario

---

## Checklist

Before claiming compliance:

- [ ] Rule applied in full — not a subset or paraphrased version
- [ ] Intent of the rule honored, not just the literal text
- [ ] No rationalizations accepted as exceptions
- [ ] If letter/spirit conflict detected: escalated, not silently resolved
- [ ] Compliance documented if non-obvious

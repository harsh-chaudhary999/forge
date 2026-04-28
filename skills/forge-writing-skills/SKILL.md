---
name: forge-writing-skills
description: "WHEN: You need to write a new Forge skill or substantially improve an existing one. Methodology for skill authoring — TDD-for-skills workflow, pressure testing, persuasion-grounded design, rigor enforcement."
type: rigid
requires: [forge-skill-anatomy]
version: 1.0.0
preamble-tier: 2
triggers:
  - "writing guidelines"
  - "how to write a skill"
  - "skill writing rules"
allowed-tools:
  - Read
  - Write
---

# Writing Forge Skills

**HARD-GATE: No skill ships without passing the pressure test and rigor checklist.**

---

## Anti-Pattern Preamble: Why Skills Fail

| Rationalization | The Truth |
|---|---|
| "The skill is simple enough that the workflow is obvious" | Simple skills are the ones most likely to be bypassed. Obvious workflows get rationalized away. Be explicit or the skill will be ignored. |
| "I'll document edge cases later, let's ship the core first" | Edge cases are the core. The skill is for when things go wrong. If edge cases are undocumented, the skill fails exactly when it's needed most. |
| "The anti-pattern preamble is optional for this skill" | Anti-pattern preambles are mandatory for all rigid and flexible skills (D25). If you're skipping it, you haven't understood the rule. |
| "5 rationalizations is too many, I can think of 2" | If you can only think of 2 rationalizations, you haven't pressure-tested the skill. Try to break it — you'll find more. |
| "This skill is for reference, it doesn't need an Iron Law" | Reference skills don't need Iron Law. Rigid and flexible do. Know your skill type before writing. |
| "The description is clear enough without WHEN:" | Descriptions without WHEN: are capability descriptions, not trigger descriptions. The AI invokes on triggers, not capabilities. Always start with WHEN. |
| "I know what the skill needs, I don't need to write examples" | Examples are how you discover gaps. Write examples first; the gaps will find you. |
| "I'll pressure-test it later once it's in use" | Real usage reveals gaps too late. Pressure-test before shipping. Finding gaps in prod is expensive. |
| "The checklist in forge-skill-anatomy is optional guidance" | The rigor checklist is a hard gate. Every item is required. If you skipped items, the skill is incomplete. |

---

## Iron Law

```
NO SKILL SHIPS UNTIL IT HAS PASSED THE PRESSURE TEST AND THE RIGOR CHECKLIST.
A SKILL WITH "TBD", MISSING ANTI-PATTERNS, OR NO EDGE CASES IS NOT A SKILL — IT IS A STUB.
```

---

## Red Flags — STOP

If you notice any of these while writing or reviewing a skill, STOP:

- **Description doesn't start with WHEN:** — The AI won't know when to invoke it. Rewrite description.
- **Anti-pattern preamble has fewer than 5 rows** — You haven't pressure-tested it. Find more rationalizations.
- **Edge cases section has fewer than 3 entries for flexible, 5 for rigid** — The skill is incomplete. Add more.
- **Iron Law is missing from a rigid skill** — Add it. One non-negotiable rule, in a code block.
- **Red Flags — STOP section is missing from a rigid skill** — Add it. 5+ warning signs.
- **Any "TBD", "TODO", or "..." in the skill body** — Not a skill. A draft. Complete it before shipping.
- **Skill type says "rigid" but workflow has optional steps** — Rigid means zero optionality. Make every step required or downgrade to flexible.
- **Checklist is absent from a rigid skill** — Add it. Every rigid skill ends with a completion checklist.
- **`requires:` field is absent but skill references other skills** — Add the dependency. Missing requires breaks skill discovery.

---

## Skill Types — Decide First

Before writing a single line, decide the skill type. This determines required sections.

| Type | When to Use | Optionality | Requires Anti-Patterns? | Requires Red Flags? |
|---|---|---|---|---|
| **rigid** | Discipline enforcement. Compliance is binary. Skipping breaks the system. | Zero — every step mandatory | Yes (5+) | Yes (5+) |
| **flexible** | Technique application. Adapt to context while preserving intent. | Some — decision points allowed | Yes (3+) | No |
| **reference** | Information lookup. No prescription. | N/A | No | No |

**Default to rigid.** If you're unsure, it's rigid. Downgrade to flexible only when adaptation is genuinely required.

---

## Detailed Workflow

### Step 1: Pressure Test (Before Writing)

Before writing the skill, try to break it.

**Ask:**
1. What rationalizations would an agent use to skip this skill?
2. What edge cases would cause the workflow to fail?
3. What happens if the skill is invoked at the wrong pipeline stage?
4. What does "done" look like, and how would you verify it?
5. What does abuse look like — correct output, wrong method?

**Record findings:**
- Rationalizations → anti-pattern preamble rows
- Edge cases → edge case section
- Wrong stage invocation → workflow preconditions
- "Done" definition → output section + checklist
- Abuse detection → red flags section

**Minimum pressure test output:**
- 5+ rationalizations (rigid) or 3+ (flexible)
- 5+ edge cases (rigid) or 3+ (flexible)
- 3+ red flags (rigid)
- 1 clear output definition

---

### Step 2: Write Frontmatter

```yaml
---
name: {skill-name}             # kebab-case, matches directory name
description: "WHEN: {exact trigger condition}. {What happens + what comes out}."
type: {skill-type}
# valid type values: rigid | flexible | reference
requires: [dependency-skill-1, dependency-skill-2]
---
```

**CSO (Claude Search Optimization) rules for description:**

| Bad | Good |
|---|---|
| `Manages eval results` | `WHEN all eval drivers have returned results and you need a final pass/fail verdict` |
| `Code review skill` | `WHEN implementation is complete and spec compliance needs verification before merge` |
| `Brain operations` | `WHEN a decision needs to be recorded with provenance in the brain` |

- Start every description with `WHEN:`
- Name the inputs (what triggers this)
- Name the outputs (what comes out)
- Use action verbs: locks, negotiates, scores, verifies, dispatches, extracts

---

### Step 3: Write Anti-Pattern Preamble

Format exactly as:

```markdown
## Anti-Pattern Preamble: Why [Agents/Reviewers/Teams] [Skip/Bypass/Rationalize] This

| Rationalization | The Truth |
|---|---|
| "First rationalization" | Counter-truth that cannot be disputed. |
| "Second rationalization" | Counter-truth. |
```

**Rules for preamble rows:**
- Rationalization is always in quotes (it's a thought someone might have)
- Counter-truth is always declarative, not a question
- Counter-truth cannot be disputed — if it can, strengthen it
- Cover all angles: speed pressure, confidence, scope reduction, past-success reasoning
- Minimum: 5 rows (rigid), 3 rows (flexible)
- Close with: `**If you are thinking any of the above, you are about to violate this skill.**`

---

### Step 4: Write Iron Law (Rigid Only)

```
## Iron Law

\`\`\`
{THE SINGLE MOST IMPORTANT RULE. If a human remembers nothing else from this skill, they remember this.
Write it in CAPITALS. Keep it to 1-2 sentences max.}
\`\`\`
```

**Rules:**
- One code block, no markup inside
- CAPS only — this is a command, not a suggestion
- If you can't distill to 1-2 sentences, you don't understand the skill yet

---

### Step 5: Write Red Flags (Rigid Only)

```markdown
## Red Flags — STOP

If you notice any of these, STOP and investigate before proceeding:

- **{Observable sign}** — {What it indicates + what to do}
- **{Observable sign}** — {What it indicates + what to do}
```

**Rules:**
- Each flag is an **observable behavior**, not a thought (you can see it, not just infer it)
- Each flag names the problem AND the action
- Minimum 5 flags (rigid)
- Flags should not duplicate anti-patterns — anti-patterns prevent, flags detect

---

### Step 6: Write Workflow

```markdown
## Detailed Workflow

### Phase 1: {Name}

**HARD-GATE: {What must be true before proceeding to Phase 2.}**

1. **{Action}** — {Why this action, what it produces}
2. **{Action}**

**Output:** {What leaves this phase}
```

**Rules:**
- Every non-skippable step has a HARD-GATE label
- Steps are numbered, not bulleted (order matters)
- Each step explains why, not just what
- Each phase has an explicit output (what enters the next phase)
- No "should", "may", "consider" in rigid skills — all steps are imperatives

---

### Step 7: Write Edge Cases

```markdown
## Edge Cases & Fallback Paths

### Case 1: {Descriptive scenario name}

- **Symptom:** Exact observable state
- **Do NOT:** The wrong thing (and why it's wrong)
- **Action:** Numbered steps for the correct response
```

**Rules:**
- Minimum 5 edge cases (rigid), 3 (flexible)
- Each case has symptom, "Do NOT", and action
- "Do NOT" is specific (not "don't be wrong")
- Action is numbered and concrete
- Include: infrastructure failures, upstream phase failures, policy conflicts, ambiguous inputs, resource exhaustion

---

### Step 8: Write Output Section + Checklist

**Output section:**
```markdown
Output: **{SUCCESS STATE}** ({conditions}) or **{FAILURE STATE}** ({conditions and action})
```

**Checklist (rigid skills):**
```markdown
## Checklist

Before claiming completion:

- [ ] {Item 1}
- [ ] {Item 2}
```

**Rules:**
- Output must be binary: exactly two states (success and failure)
- Each checklist item is independently verifiable (not "work is done")
- Checklist should be runnable by someone who didn't write the skill

---

### Step 9: Rigor Self-Review

Before shipping the skill, run the rigor checklist from `forge-skill-anatomy`:

- [ ] Frontmatter has CSO-optimized `description` starting with WHEN
- [ ] `type` is `rigid`, `flexible`, or `reference`
- [ ] `requires` lists all dependencies
- [ ] Anti-Pattern Preamble: 5+ rows (rigid), 3+ (flexible)
- [ ] Iron Law in code block (rigid)
- [ ] Red Flags — STOP section: 5+ flags (rigid)
- [ ] HARD-GATE tags on non-skippable steps (rigid)
- [ ] Edge Cases: 5+ (rigid), 3+ (flexible)
- [ ] Workflow: numbered steps, no ambiguity
- [ ] Output format specified (binary)
- [ ] Checklist at end (rigid)
- [ ] No placeholder text ("TBD", "TODO", "...")
- [ ] Cross-references to related skills present

If any item is unchecked: the skill is not ready to ship.

---

## Examples

### Example: Good vs. Bad Description

```yaml
# BAD — capability, not trigger
description: "Manages the cache contract negotiation process."

# GOOD — trigger + action + output
description: "WHEN: Two or more services share a Redis cache and you need to negotiate TTL, invalidation strategy, and key ownership. Produces locked cache contract."
```

### Example: Good vs. Bad Anti-Pattern Row

```markdown
# BAD — too vague, easily dismissed
| "Cache contracts aren't that important" | They are. |

# GOOD — specific rationalization, indisputable counter-truth
| "Cache TTL can be decided during implementation, not council" | TTL decisions affect invalidation strategy, which affects DB query patterns, which affects backend design. Deciding TTL during implementation means reopening negotiations that already closed. Decide at council. |
```

### Example: Good vs. Bad Edge Case

```markdown
# BAD — no action, no "Do NOT"
### Case 1: Infrastructure unavailable
Try to start the service.

# GOOD — symptom, wrong action, correct action
### Case 1: Redis unavailable during cache contract negotiation
- **Symptom:** `redis-cli ping` returns `Could not connect to Redis`
- **Do NOT:** Use estimated TTL values from last time and note "Redis was down"
- **Action:**
  1. Start Redis: `redis-server`
  2. Verify: `redis-cli ping` returns `PONG`
  3. If Redis cannot be started: escalate BLOCKED — cannot negotiate cache contract without target infrastructure
  4. Re-run negotiation with Redis running
```

---

## Edge Cases & Fallback Paths

### Case 1: Skill Pressure Test Reveals Fundamental Design Problem
- **Symptom:** "I've listed 8 rationalizations and I keep finding cases where skipping this skill is actually correct"
- **Do NOT:** Ship the skill with known bypass cases unaddressed
- **Action:**
  1. Document each bypass case in detail
  2. Determine: is this a skill design problem, or is the skill genuinely wrong?
  3. If design problem: restructure the skill (change type, add exceptions, clarify scope)
  4. If skill is wrong: abandon and reconsider the rule being enforced
  5. Never ship a skill you can't defend every rationalization for

### Case 2: Required Section Is Impossible for This Skill
- **Symptom:** "This is a rigid skill but I genuinely can't write 5 red flags — the skill is too simple"
- **Do NOT:** Downgrade to flexible just to avoid red flags
- **Action:**
  1. Pressure test harder — simple-seeming skills have subtle bypass patterns
  2. Look at the anti-patterns — each one implies a detectable warning sign
  3. If still stuck after 30 minutes: document why each red flag attempt failed
  4. Escalate: is this actually a rigid skill? Should it be reference?
  5. Decide type first, then requirements follow

### Case 3: Existing Skill Being Updated (Not New)
- **Symptom:** Updating `forge-tdd` to add a new edge case
- **Do NOT:** Add the edge case and ship without re-running rigor checklist
- **Action:**
  1. Make the change
  2. Re-run full rigor checklist on the updated skill
  3. Verify the change doesn't contradict existing workflow or edge cases
  4. If contradiction found: resolve it in the same commit
  5. Commit with: `skill: update {skill-name} — {what changed and why}`

### Case 4: Skill References a Non-Existent Dependency
- **Symptom:** `requires: [brain-persist-v2]` but `brain-persist-v2` doesn't exist
- **Do NOT:** Ship with a broken requires reference
- **Action:**
  1. Verify every entry in `requires:` maps to an existing skill directory
  2. If dependency doesn't exist: create it first, or remove the reference
  3. If dependency is planned: ship the dependency before the dependent skill

### Case 5: Two Skills Have Overlapping Scope
- **Symptom:** New skill `eval-driver-cache-v2` overlaps heavily with `eval-driver-cache-redis`
- **Do NOT:** Ship both and let confusion sort itself out
- **Action:**
  1. Determine: are these the same skill (consolidate) or genuinely different (clarify boundaries)?
  2. If same: update the existing skill, don't create a new one
  3. If different: update descriptions to clearly differentiate triggers
  4. Update cross-references in both skills

---

## Checklist

Before shipping any skill:

- [ ] Pressure test completed (rationalizations found and documented)
- [ ] Skill type decided (rigid, flexible, or reference)
- [ ] Frontmatter complete (name, description with WHEN:, type, requires)
- [ ] Anti-Pattern Preamble: 5+ rows with indisputable counter-truths (rigid/flexible)
- [ ] Iron Law: 1-2 sentences, CAPS, in code block (rigid)
- [ ] Red Flags — STOP: 5+ observable signs (rigid)
- [ ] Workflow: numbered, HARD-GATE on non-skippable steps, explicit outputs per phase (rigid/flexible)
- [ ] Edge Cases: 5+ with symptom + Do NOT + Action (rigid), 3+ (flexible)
- [ ] Output section: binary success/failure states
- [ ] Checklist present (rigid)
- [ ] Rigor self-review from forge-skill-anatomy passed
- [ ] No TBD, TODO, or placeholder text anywhere
- [ ] Cross-references to related skills included

Output: **SKILL READY** (all checklist items pass, rigor review passed) or **SKILL INCOMPLETE** (specific items failing — fix before shipping)

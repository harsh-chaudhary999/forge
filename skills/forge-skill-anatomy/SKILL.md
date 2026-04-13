---
name: forge-skill-anatomy
description: "Template, rigor checklist, and CSO guidelines for creating new Forge skills. Reference when writing or reviewing any skill."
type: reference
---
# Skill Anatomy

## Frontmatter (Required)

```yaml
---
name: {skill-name}
description: "WHEN: {trigger condition}. {What the skill does in one sentence}."
type: rigid | flexible | reference
requires: [other-skill-name]
---
```

### CSO (Claude Search Optimization) for Descriptions

The `description` field is how the AI decides whether to invoke a skill. Optimize it:

- **Start with WHEN** — Describe the trigger, not the capability. "WHEN eval drivers return results and you need a verdict" not "Judges eval results."
- **Include the action verb** — "locks", "negotiates", "scores", "verifies", "dispatches"
- **Name the inputs/outputs** — "shared-dev-spec", "eval verdict", "tech plan"
- **Avoid generic words** — "handles", "manages", "processes" tell the AI nothing

| Bad | Good |
|---|---|
| `Manages cache contracts` | `WHEN: Two or more services share a Redis cache and you need to negotiate TTL, invalidation, and key ownership` |
| `Code review skill` | `WHEN: Implementation is complete and you need spec-compliance verification before merge` |
| `Brain operations` | `WHEN: A decision needs to be recorded with provenance (who, when, why, evidence) in the brain` |

## Skill Types

| Type | Rule | When to Use |
|---|---|---|
| **rigid** | Follow exactly. No adaptation. Zero tolerance for shortcuts. | Discipline-enforcing skills: TDD, gates, eval, review |
| **flexible** | Adapt principles to context. Core intent preserved. | Technique skills: negotiation, planning, pattern extraction |
| **reference** | Explain concepts. No prescription. | Glossaries, templates, layout guides |

## Required Sections by Type

### Rigid Skills (Discipline)

1. **Anti-Pattern Preamble** (REQUIRED — D25)
   - Rationalization table: 5+ rows minimum
   - Format: `| Rationalization | Why It Fails |`
   - Close every loophole. If someone could talk themselves out of following the skill, add a row.
   - End with: `**If you are thinking any of the above, you are about to violate this skill.**`

2. **Iron Law** (one non-negotiable rule in a code block)
   ```
   IRON LAW: {The single most important rule. If you remember nothing else, remember this.}
   ```

3. **HARD-GATE** tags on every non-skippable step (D24)

4. **Red Flags — STOP** section
   - 5+ warning signs that indicate the skill is being bypassed
   - Format: bullet list of "If you notice X, STOP — Y is happening"

5. **Edge Cases** — At least 5, each with:
   - Scenario description
   - Specific action to take
   - Why the naive approach fails

6. **Workflow** — Step-by-step, numbered, no ambiguity

7. **Output** — What the skill produces, in what format

### Flexible Skills (Technique)

1. **Anti-Pattern Preamble** (REQUIRED — D25) — Same format as rigid
2. **Principles** — Core intent that must be preserved
3. **Workflow** — Adaptable steps with decision points
4. **Edge Cases** — At least 3
5. **Output** — Expected deliverables

### Reference Skills (Clarity)

1. **Structured tables** — Organize information for quick lookup
2. **Naming conventions** — How things are named and why
3. **Cross-references** — Links to related skills and concepts
4. **Examples** — Concrete usage

## Persuasion Principles (D14 — Cialdini)

Apply per skill type:

| Principle | Rigid Skills | Flexible Skills | Reference Skills |
|---|---|---|---|
| **Authority** | "This gate exists because X failure happened" | "Industry standard practice" | N/A |
| **Commitment** | "You committed to this process at intake" | "The team agreed on this approach" | N/A |
| **Social Proof** | "Every shipped product follows this" | "Teams that do this ship faster" | N/A |
| **Clarity** | Step numbers, checklists, zero ambiguity | Decision trees, clear criteria | Tables, structured formats |
| **Unity** | "We don't skip gates" | "We adapt, we don't abandon" | N/A |

---

# Deep Dive: Skill Anatomy by Type

## Understanding Skill Types: The Decision Tree

```
Is this a step-by-step workflow with a single correct path?
├─ YES → RIGID (TDD-based, zero tolerance, discipline enforcement)
│        Example: forge-tdd, eval-judge, spec-reviewer
│
└─ NO → Does this teach a pattern with valid variations?
        ├─ YES → FLEXIBLE (principle-based, context adaptation)
        │        Example: reasoning-as-infra, contract-negotiation
        │
        └─ NO → Is this lookup/reference only?
                ├─ YES → REFERENCE (glossaries, APIs, layouts)
                │        Example: forge-glossary, brain-read
                │
                └─ NO → You may need to split into multiple skills
```

### RIGID Skills: Discipline Enforcement

**When to write rigid:** Your skill enforces a non-negotiable process. Examples: test-driven development, security gates, code review checkpoints, eval verdicts.

**Key principle:** No adaptation. The skill says "do X", you do X. Users cannot rationalize shortcuts because the skill anticipates every rationalization.

**Structure for Rigid Skills:**

```
1. Anti-Pattern Preamble (5+ rationalizations with rebuttals)
2. Iron Law (one non-negotiable rule)
3. Red Flags — STOP section (5+ warning signs)
4. Numbered Workflow (HARD-GATE on critical steps)
5. Edge Cases (5-7 scenarios with escalations)
6. Output Specification (format, structure, validation)
```

**Example: forge-tdd**
- Anti-patterns: "We can write tests after", "TDD slows us down", "Our code is too simple for tests"
- Iron Law: Write test first. Failing test. Then implementation.
- Red Flags: If you see code without corresponding test, if implementation changed without test change, if green bar achieved by hacking test
- Workflow: (1) Read spec → (2) HARD-GATE: Write failing test → (3) Implement to pass test → (4) Refactor → (5) HARD-GATE: All tests green
- Edge Cases: What about legacy code? Integration tests? Performance tests?
- Output: Running test suite, 100% test coverage report

### FLEXIBLE Skills: Principle-Based Techniques

**When to write flexible:** Your skill teaches a pattern that varies by context. Examples: architecture negotiation, planning, code extraction, performance optimization.

**Key principle:** Core intent is preserved, but implementation adapts. Users understand the principles, then apply them to their codebase. Multiple valid approaches exist.

**Structure for Flexible Skills:**

```
1. Anti-Pattern Preamble (same format as rigid, but focuses on principle abandonment)
2. Core Principles (3-5 core rules that must hold)
3. Adaptive Workflow (decision points where context determines path)
4. Multiple Valid Approaches (show 2-3 different implementations)
5. Edge Cases (3-7 scenarios with context-dependent mitigation)
6. Output Specification (expected deliverables, not rigid format)
```

**Example: reasoning-as-infra**
- Principles: Async first, fail open vs fail closed trade-off documented, observability before performance
- Workflow: Read PRD → assess async/sync → DECISION: Can this timeout? → DECISION: Prefer fail-open? → Design patterns
- Approaches: Circuit breaker pattern, bulkhead pattern, saga pattern (pick based on consistency requirements)
- Edge Cases: Multiple failures in chain, observability gaps, cascading timeouts
- Output: Architecture diagram with trade-offs annotated

### REFERENCE Skills: Lookup and Query

**When to write reference:** Your skill is a glossary, API reference, directory structure guide, or lookup table.

**Key principle:** No prescription. Users consult when needed. Information should be organized for fast lookup.

**Structure for Reference Skills:**

```
1. Structured Tables (organized by category)
2. Naming Conventions (how things are named and why)
3. Cross-References (links to related skills and concepts)
4. Examples (concrete usage in context)
5. Search Keywords (for CSO optimization)
```

**Example: forge-glossary**
- Tables: Skill terms, product terms, eval terms
- Naming: Why are skills named `{verb}-{noun}`?
- Cross-references: "See forge-skill-anatomy for writing skills", "See brain-read for understanding brain structure"
- Examples: "PRD = Product Requirements Document. Used in /intake skill. Example: 'Feature PRD locked after 3 council iterations'"

---

# Anti-Patterns in Skill Authoring

The patterns below are rationalizations agents make when writing skills. Each rationalization leads to downstream failures. Close every loophole.

## Anti-Pattern 1: "Anti-pattern section is optional"

**Why This Fails:**
Users will find rationalizations to skip your skill. Without explicit anti-patterns, they succeed.
- "We'll just do the simplest version" → Misses edge cases
- "The test seems fine, let me ship it" → Fails in production
- "We already have a cache layer" → Doesn't validate new contract
- Silent failures compound (one wrong step leads to three downstream failures)
- You designed the skill but can't enforce it

**Enforcement:**
- **MUST** include 5+ rationalization patterns in any rigid skill
- **MUST** format as: `| Rationalization | Why It Fails |`
- **MUST** include a rebuttal explaining the real consequence
- **MUST** end with: `**If you are thinking any of the above, you are about to violate this skill.**`
- **MUST** validate anti-patterns during skill review (ask: "Can someone rationalize skipping this?")

---

## Anti-Pattern 2: "Edge cases can be thin"

**Why This Fails:**
- "5-7 edge cases" seems long, but if you miss one, your skill fails for 10% of users
- Thin edge cases (1-2 sentences) don't explain mitigation or escalation
- Users hit edge case, skill provides no guidance, they improvise (now inconsistent)
- Escalation keywords (BLOCKED, NEEDS_CONTEXT, NEEDS_COORDINATION, NEEDS_INFRA_CHANGE) are missing
- You can't tell if the issue is the skill's fault or the user's

**Enforcement:**
- **MUST** include 5-7 edge cases for rigid skills, 3-5 for flexible
- **MUST** follow format: Scenario → Specific Mitigation → Why Naive Fails → Escalation Keyword
- **MUST** include at least one BLOCKED scenario (where skill cannot be applied)
- **MUST** include at least one NEEDS_COORDINATION scenario (where multiple teams need alignment)
- **MUST** include at least one NEEDS_INFRA_CHANGE scenario (where underlying systems must change)

---

## Anti-Pattern 3: "HARD-GATE style is too harsh"

**Why This Fails:**
- HARD-GATE is binary (STOP or continue). Feels authoritarian.
- But without it, "critical steps" become optional in practice
- Users skip the HARD-GATE step, get wrong results, blame the skill
- You wanted to enforce discipline but used soft language instead
- Downstream failures are now your skill's reputation problem

**Enforcement:**
- **MUST** use HARD-GATE tags on steps that are non-negotiable
- **MUST** follow format: `HARD-GATE: [Step]. If [condition], you violate this skill.`
- **MUST** make every HARD-GATE testable (e.g., "verify test coverage >90%")
- **MUST** use enforcement keywords consistently (MUST, MUST NOT, HARD-GATE, Red Flag)
- **MUST** pair HARD-GATE with Red Flags section (what does violation look like?)

---

## Anti-Pattern 4: "Checklists duplicate workflow"

**Why This Fails:**
- Workflow is procedural ("Do A, then B, then C")
- Checklist is validation ("Did you do A? Did you do B?")
- These are NOT the same. A checklist catches issues even if you followed steps mechanically
- Example: Workflow says "run tests". Checklist asks "are tests meaningful?" (catches low-coverage tests)
- Without checklists, users follow steps but skip validation
- Duplication is acceptable when it catches different failures

**Enforcement:**
- **MUST** include pre-invocation checklist: "Do I have the right skill for this task?"
- **MUST** include pre-implementation checklist: "Am I ready to follow this skill?"
- **MUST** include post-implementation checklist: "Did I follow the skill correctly?"
- **MUST** make checklist items binary (can be YES/NO, checkmark/X)
- **MUST** link checklist items to workflow sections (traceable coverage)

---

## Anti-Pattern 5: "Cross-references aren't needed"

**Why This Fails:**
- A skill is useful in isolation. Adding cross-references is extra work.
- But without cross-references, skills become orphaned
- New users don't know "this skill connects to 3 others"
- Skills can't be combined in workflows (because connections aren't documented)
- You have 63 skills but users only use 5 because the other 58 are hidden
- Adoption compounds (if skill A references skill B, users discover B)

**Enforcement:**
- **MUST** link to 3+ related skills (prerequisite, follow-up, or sibling)
- **MUST** use format: `[skill-name]: {one sentence explaining connection}`
- **MUST** include prerequisite skills: "You should know X before reading this"
- **MUST** include follow-up skills: "After this skill, you'll be ready for Y"
- **MUST** create execution flow: Show how multiple skills chain together

---

# Edge Cases in Skill Authoring

These five scenarios are when skill anatomy breaks down. Know when to escalate.

## Edge Case 1: Skill Missing Required Sections

**Scenario:** You've written overview + examples but no anti-patterns or edge cases. Frontmatter is incomplete.

**Symptom:** When reviewing the skill, you notice:
- Anti-Pattern Preamble is missing (or has <5 entries)
- Edge Cases section is missing
- Frontmatter is missing `description` field or has generic description ("Code review skill")

**Mitigation:**
1. Validate against the template (read forge-skill-anatomy)
2. For each missing section, add it following the template format
3. For anti-patterns: Brain dump 10 rationalizations users might have, distill to 5 strongest
4. For edge cases: List 10 scenarios where the skill might fail, distill to 5-7 with clear escalations
5. Update frontmatter description to start with "WHEN:"

**Why Naive Approach Fails:**
- Skipping anti-patterns → Users rationalize away from skill
- Skipping edge cases → Skill fails silently (users blame skill, not their edge case)
- Incomplete frontmatter → Skill won't load or CSO can't find it

**Escalation:** BLOCKED if major sections missing (anti-patterns, edge cases, or HARD-GATE for rigid skills). Skill cannot ship until these are added.

---

## Edge Case 2: Skill Too Long (>2000 lines)

**Scenario:** You're adding examples, edge cases, and workflows, and the skill file balloons to 2500+ lines.

**Symptom:**
- Single skill file is hard to navigate
- Too many decision trees (more than 3)
- Examples section is >500 lines
- Skill feels like 3 skills merged together

**Mitigation:**
1. Identify natural section breaks (e.g., "Basic Workflow" vs "Advanced Patterns")
2. Split into sub-skills: primary skill + reference sub-skill
3. Move detailed examples to a separate `examples/` directory (reference from main skill)
4. Move decision trees to a separate decision-tree skill (if >3 trees)
5. Keep main skill to <1500 lines, reference files for deep dives

**Why Naive Approach Fails:**
- Users can't find what they need (2500 lines is overwhelming)
- Navigation by search becomes primary (defeats documentation structure)
- Long files are hard to review and maintain

**Escalation:** NEEDS_CONTEXT. Consult with tech lead before splitting. May need to refactor skill dependencies.

---

## Edge Case 3: Skill Overlaps with Existing Skill

**Scenario:** You're writing a new skill and realize it covers similar ground as an existing skill.

**Symptom:**
- Description is similar to another skill (CSO match >70%)
- Workflow solves the same problem with different steps
- Examples from both skills are nearly identical
- Users might be confused about which skill to use

**Mitigation:**
1. Read both skills top-to-bottom (understand their scopes)
2. Ask: "Are these the same skill with different names?" OR "Are these complementary?"
3. If same: Consider merging (new skill becomes variant section of existing skill)
4. If complementary: Create explicit cross-reference (A requires B or A leads to B)
5. Update descriptions to clarify when to use each (different WHEN clauses)

**Why Naive Approach Fails:**
- Duplicate effort (maintaining two similar skills)
- User confusion (which skill applies to my problem?)
- Inconsistent guidance (if they diverge over time)

**Escalation:** NEEDS_COORDINATION. This decision affects skill catalog. Flag for architecture review before merge.

---

## Edge Case 4: Skill Has No Clear Trigger

**Scenario:** Your skill description doesn't clearly explain when to invoke it. The "WHEN" clause is ambiguous.

**Symptom:**
- Description doesn't start with "WHEN"
- Description uses generic words ("Handles", "Manages", "Processes")
- You can't explain to a user: "Use this skill when X happens"
- Examples show skill being used, but the trigger isn't clear

**Mitigation:**
1. Write the WHEN clause first (before anything else)
2. Be specific: "WHEN you have X, and you need to do Y"
3. Add examples of WHEN the skill applies (and WHEN it doesn't)
4. Ask: "If a user says 'I need to X', would they find this skill?"
5. Optimize for CSO (search). Use action verbs and concrete nouns.

**Why Naive Approach Fails:**
- CSO can't find the skill (vague description doesn't match user queries)
- Users invoke skill at wrong time (wrong context, wrong stage)
- Skill seems pointless because you can't explain when to use it

**Escalation:** BLOCKED if CSO cannot infer trigger from description. Skill is unsearchable. Rewrite description.

---

## Edge Case 5: Skill Frontmatter Missing Required Fields

**Scenario:** Frontmatter has some fields but is missing critical ones (name, description, or type).

**Symptom:**
- `name` field is empty or missing
- `description` field is missing or placeholder text ("TODO: write description")
- `type` is missing or not one of: rigid, flexible, reference
- `requires` field references non-existent skills

**Mitigation:**
1. Validate against YAML schema (name, description, type are REQUIRED)
2. Populate `name` with skill directory name (kebab-case)
3. Write `description` starting with "WHEN:"
4. Set `type` explicitly to one of: rigid, flexible, reference
5. Verify each skill in `requires` exists and is spelled correctly
6. Test with: `grep -A 3 "^---$" skills/{skill-name}/SKILL.md`

**Why Naive Approach Fails:**
- Skill won't load (Forge plugin checks frontmatter at session start)
- CSO can't index it (missing description)
- Dependency chain breaks (if requires field is wrong)

**Escalation:** BLOCKED. Skill cannot be published without valid frontmatter. This is a hard gate.

---

# Worked Examples: Good vs Bad Skill Anatomy

## BAD Example: Incomplete Skill

```yaml
---
name: cache-negotiation
description: "Negotiate cache contracts"
type: flexible
---

# Cache Negotiation

## Overview

When multiple services share a cache (Redis, Memcached), you need to negotiate:
- TTL (time-to-live)
- Invalidation strategy
- Key ownership

## Workflow

1. Identify all services that touch the cache
2. List all keys and their TTLs
3. Define invalidation strategy (event-based vs TTL-based)
4. Document the contract

## Examples

Example 1: TTL-based cache
```
Service A: user-profile:{id}, TTL 5min
Service B: user-feed:{id}, TTL 10min
Invalidation: On profile update, invalidate both keys
```

Example 2: Event-based cache
```
Service A publishes user.updated event
Service B subscribes, invalidates cache
```

## Output

A cache contract document with keys, TTLs, and invalidation rules.
```

**What's Wrong:**

1. **Missing Anti-Pattern Preamble** — No rationalizations:
   - "We don't need to negotiate, just use Redis"
   - "TTL is enough, we don't need explicit invalidation"
   - "We can cache everything, it's safe"
   - Users will talk themselves out of following this skill

2. **Thin Edge Cases** — No edge cases section at all:
   - What if services have conflicting TTLs? (Service A wants 5min, Service B wants 1hr)
   - What if cache becomes inconsistent? (invalidation event lost)
   - What if key schema changes? (old keys not invalidated)
   - Skill provides no guidance for these scenarios

3. **No Decision Trees** — Just a linear workflow:
   - But the decision point "event-based vs TTL-based" is critical
   - Skill doesn't explain how to choose between them
   - Users have to guess

4. **Weak Checklists** — No pre/post validation:
   - Did the user actually negotiate, or just assume?
   - Are all services represented in the contract? (user might miss one)
   - Is the contract testable? (no verification step)

5. **No Cross-References** — Isolated from other skills:
   - This connects to contract-cache skill
   - Prerequisite: contract-api-rest (learn negotiation first)
   - Users don't know these connections

6. **Generic Workflow** — "Define invalidation strategy" is vague:
   - What does "define" mean? Write a document? Run a meeting?
   - How detailed should it be?
   - Who signs off?

---

## GOOD Example: Complete Skill

```yaml
---
name: contract-cache
description: "WHEN: Two or more services share a Redis/Memcached cache and you need to negotiate TTL, invalidation, and key ownership before implementation"
type: flexible
requires: [contract-api-rest, council-multi-repo-negotiate]
---

# Cache Contract Negotiation

## Anti-Pattern Preamble: Why Teams Skip Cache Contracts

| Rationalization | Why It Fails |
|---|---|
| "We don't need to negotiate, just use Redis" | Without negotiation, services overwrite each other's keys. Cache becomes inconsistent. Debugging production incidents becomes impossible. |
| "TTL is enough, we don't need explicit invalidation" | TTL is probabilistic (expires sometime). Invalidation is deterministic (expires now). One event-based invalidation beats waiting for 100 TTL expirations. |
| "We can cache everything, it's safe" | Over-caching creates stale data. Example: User profile cached for 1hr, profile updated, user sees old data for 1hr. Now you're breaking SLAs. |
| "Each service owns its own keys, no need to negotiate" | Keys collide (both services use `user:123`). Or keys have data dependencies (profile cache depends on session cache). Without negotiation, you'll deadlock. |
| "We'll document the cache contract later" | Later never comes. Six months later, service C joins and assumes different TTL. Cache breaks silently. No audit trail of why decisions were made. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
IRON LAW: Every service that reads or writes a shared cache key must sign the cache contract.
No exceptions. Unsigned services create cascading failures.
```

## Core Principles

1. **Explicit Ownership** — Each cache key has an owner (the service that writes it first)
2. **Fail-Open vs Fail-Closed** — Define what happens on cache miss (stale data OK? or must re-fetch?)
3. **Invalidation is Explicit** — Document WHEN and HOW each key invalidates
4. **Observability Before Performance** — Instrument cache hits/misses before optimizing

## Overview: When to Use This Skill

**Invoke this skill when:**
- You have 2+ services reading/writing the same cache layer
- Before any code is written (negotiation happens first)
- Multiple teams own the services (coordination needed)

**Do NOT invoke if:**
- Only one service uses the cache (no negotiation needed)
- Cache is ephemeral/non-critical (e.g., rate-limit buckets)
- You're within a single monolith (same team owns all code)

## Workflow: Step-by-Step

### Phase 1: Gather Stakeholders

**HARD-GATE: All services that touch the cache must have a representative in the room**

1. List all services that currently read/write the shared cache
2. Identify service owners (1 person per service)
3. Schedule negotiation meeting (async OK if written, synchronous preferred)
4. Send pre-read: existing cache schema (if any)

### Phase 2: Map Current Keys

**HARD-GATE: Every existing cache key must be documented**

1. For each key, record:
   - Key pattern (e.g., `user-profile:{user_id}`)
   - Owner service (who writes it)
   - Reader services (who reads it)
   - Current TTL (if any)
   - Size (bytes, to catch over-caching)

2. Create a matrix:
   ```
   Key Pattern          | Owner     | Readers            | TTL   | Size
   user-profile:{id}    | identity  | feed, recommendation | 5min | 2KB
   feed:{user_id}       | feed      | web, mobile         | 10s  | 50KB
   ```

3. Validate: Do any keys overlap? Do any readers exist without an owner?

### Phase 3: Decision Tree — Invalidation Strategy

**HARD-GATE: Choose an invalidation strategy for each key**

```
Does this key's data change frequently (multiple times per minute)?
├─ YES → Use EVENT-based invalidation
│        (service that owns the key publishes an event when it changes)
│        Readers subscribe to event, invalidate immediately
│        TTL is a safety net only (catches missed events)
│        Example: user-profile (changes on user action → publish event)
│
└─ NO → Use TTL-based invalidation
         (set a TTL, let it expire)
         Simpler to implement, acceptable staleness
         Example: feed data (ok to be 10s stale)
         Risk: TTL must be long enough to amortize invalidation cost
              but short enough to catch updates
```

For each key, document:
- Invalidation type (EVENT or TTL)
- If EVENT: which event triggers invalidation, who publishes
- If TTL: justify the TTL value (why this duration?)
- Fallback strategy (if primary invalidation fails)

### Phase 4: Fail-Open vs Fail-Closed

**HARD-GATE: For each key, define behavior on cache miss**

Ask: "If this key expires or is missing, what happens?"

| Scenario | Fail-Open (Stale Data OK) | Fail-Closed (Re-fetch) |
|---|---|---|
| User profile | Accept stale for 5min | Re-fetch from DB |
| Feed rankings | Return stale + async update | Re-rank (slow) |
| Session | Reject (stale session = security risk) | Re-fetch from session store |
| Rate limit | Accept stale (user gets burst) | Re-fetch counter (strict) |

Document for each key:
- Fail strategy (open or closed)
- Why this choice (business logic, SLA, security)
- Fallback if primary strategy fails

### Phase 5: Document the Contract

Create a `CACHE_CONTRACT.md` file in a shared location (e.g., `shared-dev-spec/CACHE_CONTRACT.md`):

```markdown
# Shared Cache Contract

**Signed Services:** identity, feed, recommendation, web

**Cache Backend:** Redis cluster at `cache.prod.internal:6379`

## Keys

| Key Pattern | Owner | Readers | TTL | Invalidation | Fail | Owner Contact |
|---|---|---|---|---|---|---|
| user-profile:{id} | identity | feed, web | 5min | event(user.updated) | open | @identity-team |
| feed:{id} | feed | web, mobile | 10s | TTL | closed | @feed-team |

## Escalation

If cache diverges from this contract:
1. Immediate: Page on-call (cache inconsistency = production incident)
2. Post-incident: Update contract and re-negotiate
3. Prevent: Monitoring alerts for keys not in contract
```

### Phase 6: Red Flags — STOP

If you notice any of these, STOP the negotiation. Cache contract is incomplete.

- **Service joins but isn't in the contract** — STOP. Re-negotiate. Add the service.
- **Key has both event AND TTL invalidation, but no trade-off documented** — STOP. Why both? Pick one.
- **Owner doesn't know their own keys' TTL** — STOP. Owner must know every key they write.
- **Readers list is "everyone"** — STOP. Be specific. Unknown readers = unknown dependencies.
- **Fail strategy is undefined** — STOP. Stale data vs re-fetch must be explicit.
- **Contract is unsigned** — STOP. Have each service owner sign the contract (commit message, or email trail).

## Edge Cases and Escalations

### Edge Case 1: Services Have Conflicting TTL Preferences

**Scenario:** Service A wants `user-profile` cached for 1 hour (reduce DB load). Service B wants 5 minutes (data freshness). Both read the key.

**Symptom:**
- Negotiation stalls (service owners can't agree)
- One service agrees but is unhappy (builds resentment, they'll ignore contract)
- You pick an arbitrary TTL (5min compromise, but satisfies neither)

**Mitigation:**
1. Reframe: "This isn't about who's right, it's about SLA"
2. Ask Service A: "How stale can the data be?" (1hr is business decision, not technical)
3. Ask Service B: "Why do you need fresh data?" (validate if 5min is truly required)
4. Trade: Service A gets 5min TTL, Service B adds caching layer (local cache + event-based invalidation)
5. Compromise: Event-based invalidation (immediate) + 30min TTL (safety net). Both happy.
6. Document the rationale (why 30min was chosen)

**Why Naive Approach Fails:**
- Picking arbitrary number (5min) → One service ignores contract later
- Majority vote (2 vs 1) → Minority service workarounds, creating shadow cache
- Escalating to manager → Loses technical context (why does each service need different TTL?)

**Escalation:** NEEDS_COORDINATION. Bring service owners + tech leads to negotiation. This requires cross-team alignment, not just cache engineers.

---

### Edge Case 2: Cache Becomes Inconsistent (Invalidation Event Lost)

**Scenario:** Service A publishes `user.updated` event. Service B doesn't receive it (event queue backlog, network partition). Cache is now stale. Service B serves stale data for hours.

**Symptom:**
- Users report seeing old data
- No error in logs (cache hit, nothing wrong from Service B's perspective)
- Inconsistency detected only when comparing two services' views

**Mitigation:**
1. Add monitoring: Track cache hit/miss ratio. If hit ratio jumps (abnormal), alert.
2. Add circuit breaker: If invalidation events are delayed >30min, purge cache (fail-closed)
3. Add audit log: Every cache key access logged with version number. Detects stale data in logs.
4. Add timestamp: Cache values include `last_updated_at`. Service B can detect staleness.
5. Test: Simulate event loss (kill event queue), verify cache strategy handles it.

**Why Naive Approach Fails:**
- Event-based invalidation only works if events are reliable. But systems fail.
- Without monitoring, stale cache is invisible (no alert)
- Users discover bug (bad UX, hard to debug)

**Escalation:** NEEDS_INFRA_CHANGE. Monitoring, circuit breakers, and audit logs are infrastructure requirements, not just cache strategy. May need dedicated cache observability tool.

---

### Edge Case 3: Cache Key Schema Changes

**Scenario:** Original contract: `user-profile:{user_id}`. Now Service A wants to change it to `user:profile:{user_id}:{version}` (versioning). Old cache keys are orphaned.

**Symptom:**
- Cache keys don't match the new schema
- Service B still looks for `user-profile:{id}` (miss, re-fetches)
- Service A writes to new schema, but no invalidation of old keys
- Memory bloat (orphaned keys accumulate)

**Mitigation:**
1. **Pre-change validation:** Before deploying new schema, HARD-GATE: "Have all readers agreed to new schema?"
2. **Dual-write period:** Service A writes to BOTH old and new keys for 1 week (both schemas valid)
3. **Async migration:** Background job migrates old keys to new keys (or deletes)
4. **Grace period:** After 1 week, Service A stops writing old keys. Readers switch to new keys.
5. **Verify:** Cache hit ratio stable → readers found new keys

**Why Naive Approach Fails:**
- Unilateral schema change (Service A changes without telling Service B) → Cache misses everywhere
- No migration period → Downtime while readers adapt
- No coordination → Readers don't know key schema changed

**Escalation:** NEEDS_COORDINATION + NEEDS_INFRA_CHANGE. Schema changes affect all readers. Requires synchronized rollout. Infrastructure must support dual-write.

---

### Edge Case 4: Cache Layer is Full (Eviction Policy Matters)

**Scenario:** Redis is 95% full. Eviction policy is LRU (least recently used). Your critical key (`user-session`) is evicted because it's accessed less often than another key.

**Symptom:**
- Session cache evicted unexpectedly
- Users logged out (cache miss, session lost)
- Fail-closed strategy (re-fetch from session store) kicks in, but session store is overloaded
- Cascade failure

**Mitigation:**
1. **Capacity planning:** Before negotiating contract, agree on cache size and eviction policy.
2. **Priority tiers:** Mark critical keys (session, auth) with higher priority than ephemeral keys (feed).
3. **Monitoring:** Alert when cache is >80% full. Reserve headroom.
4. **Escalation path:** If cache is full, de-prioritize non-critical keys (increase their TTL or delete).
5. **Fallback:** If cache is full and no de-prioritization available, fail-closed (re-fetch).

**Why Naive Approach Fails:**
- Assuming infinite cache space → Eviction surprises you
- Eviction policy not documented → Unexpected evictions
- No monitoring → Discover eviction in production incident

**Escalation:** NEEDS_INFRA_CHANGE. Cache sizing, eviction policy, and capacity planning are infrastructure requirements. May need to increase cache capacity or use tiered caching.

---

### Edge Case 5: Circular Invalidation (Cache Deadlock)

**Scenario:** Service A invalidates key `feed:{id}` on event `user.updated`. But computing `feed:{id}` requires reading `user-profile:{id}`. If profile cache is stale, feed recomputes infinitely.

**Symptom:**
- Invalidation cascades: Update user → invalidate feed → recompute feed → requires profile → profile is stale → ???
- CPU spike (recomputation loop)
- Or feed computation blocks waiting for profile cache to refresh

**Mitigation:**
1. **Dependency mapping:** Before finalizing contract, identify key dependencies (which keys depend on which others)
2. **Acyclic validation:** Check for cycles. If A depends on B and B depends on A, redesign contract.
3. **Timeout strategy:** Feed recomputation has timeout. If it takes too long, serve cached version and alert.
4. **Segregate concerns:** Cache infrastructure keys (profile) separately from derived keys (feed). Invalidate in order.

**Why Naive Approach Fails:**
- Treating cache keys independently (ignoring dependencies)
- Invalidation happens in unpredictable order (race conditions)
- Circular dependencies are invisible until production load hits

**Escalation:** BLOCKED. Circular dependencies must be resolved before contract can be signed. Requires redesign of cache strategy (separate caches, dependency injection, or compute pipeline).

---

## Decision Tree: When to Use This Skill

```
Do you have multiple services sharing a cache backend (Redis/Memcached)?
├─ NO → Skip this skill. Single-service caching is simpler (basic TTL sufficient).
│
└─ YES → Are all services under the same team's control?
         ├─ YES → You can use lightweight negotiation (1 meeting, async chat)
         │        Still use this skill, but compress phases (combine Phase 1-2)
         │
         └─ NO → Use full negotiation (all phases, all services present)
                 This skill is mandatory.
                 Services across team boundaries need explicit contracts.
```

## Checklists

### Pre-Invocation Checklist: Do I Need This Skill?

- [ ] Do I have 2+ services reading/writing the same cache backend?
- [ ] Is the cache layer shared infrastructure (not ephemeral)?
- [ ] Do service owners represent different teams (or different codebases)?
- [ ] Is this being designed before implementation (early enough to negotiate)?

If all YES: Use this skill now.
If any NO: You may not need this skill (cache negotiation is simpler or unnecessary).

### Pre-Implementation Checklist: Am I Ready?

- [ ] All stakeholders (service owners) are identified
- [ ] Existing cache keys are documented
- [ ] Invalidation strategy is chosen for every key (EVENT or TTL)
- [ ] Fail-open vs fail-closed is defined for every key
- [ ] Contract draft is written (CACHE_CONTRACT.md)
- [ ] All services have reviewed and agreed on contract
- [ ] Monitoring/observability is planned (before code is written)

If all YES: Ready to implement.
If any NO: Return to negotiation. Don't code until contract is signed.

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] Contract is signed (committed, in code, auditable)
- [ ] Every cache key in production matches contract
- [ ] Invalidation is event-based (if EVENT strategy) or TTL-based (if TTL)
- [ ] Monitoring alerts for stale cache, inconsistency, or eviction
- [ ] Services tested: What happens on cache miss? Does it match fail strategy?
- [ ] No unplanned cache keys (no shadow caching)

If all YES: Skill was followed correctly. Cache is safe.
If any NO: Contract was violated. Fix before accepting pull request.

## Cross-References

**Prerequisite Skills:**
- [contract-api-rest](/skills/contract-api-rest/SKILL.md) — Learn negotiation patterns first
- [council-multi-repo-negotiate](/skills/council-multi-repo-negotiate/SKILL.md) — Multi-team alignment framework

**Follow-Up Skills:**
- [eval-driver-cache-redis](/skills/eval-driver-cache-redis/SKILL.md) — Test cache behavior during eval
- [brain-write](/skills/brain-write/SKILL.md) — Record the contract decision in brain

**Related Skills:**
- [contract-event-bus](/skills/contract-event-bus/SKILL.md) — Event invalidation uses event bus contracts
- [contract-schema-db](/skills/contract-schema-db/SKILL.md) — Similar negotiation pattern for database schemas

## Output Specification

Deliverable: `CACHE_CONTRACT.md` (required file in shared-dev-spec)

Format:
```markdown
# Shared Cache Contract

**Signed Services:** [list of services, comma-separated]
**Cache Backend:** [host:port, cluster name, etc]
**Contract Signed:** [date, by whom]
**Last Updated:** [date]

## Key Directory

| Key Pattern | Owner | Readers | TTL | Invalidation Strategy | Fail Strategy | Owner Contact |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... |

## Trade-Offs Documented

[For each key with multiple services, document the decision made]

## Escalation Protocol

[If cache diverges: immediate action, post-incident action, prevention measures]

## Monitoring

[Alerts for inconsistency, eviction, misses, or keys not in contract]
```

Validation:
- [ ] Every service touching cache is listed
- [ ] Every key has owner, readers, TTL, and strategy
- [ ] All signatures present (commitment from each service)
- [ ] No placeholder text ("TODO", "TBD")
- [ ] Monitoring is specific (not generic)
```

**What's Good:**

1. **Anti-Pattern Preamble** — 5 rationalizations with rebuttals
2. **Iron Law** — One non-negotiable rule
3. **Decision Tree** — EVENT vs TTL invalidation
4. **Red Flags** — 5 specific warnings
5. **Edge Cases** — 5 scenarios with escalations (NEEDS_COORDINATION, NEEDS_INFRA_CHANGE)
6. **Checklists** — Pre/post validation
7. **Cross-References** — 5 related skills
8. **Clear Output** — Exact deliverable format specified

---

# Skill Authoring Anti-Patterns (for Skill Authors)

When you write a skill, avoid these meta-anti-patterns:

## Anti-Pattern: "I'll add examples later"

Examples are not optional. They're enforcement. Without examples, the skill is theoretical. Users can't tell if they're using it correctly.

**Fix:** Write 3-4 examples before finalizing. Each example should show a concrete scenario and how the skill applies.

## Anti-Pattern: "The workflow can be flexible"

If your skill is FLEXIBLE, the workflow has decision points (documented). If your skill is RIGID, the workflow is step-by-step (numbered, no branches).

You can't have a "flexible workflow" where users guess the order. Pick rigid or flexible. If you're undecided, your skill isn't ready.

**Fix:** Clarify: Is this a discipline skill (rigid) or a technique skill (flexible)? Rewrite workflow accordingly.

## Anti-Pattern: "Five edge cases is too many"

No. Five edge cases is the minimum. If you only have one edge case ("What if X?"), you're thinking too narrowly. Real users hit edge cases you haven't thought of.

**Fix:** Spend 30min brainstorming: "What could go wrong?" Write down 15 scenarios. Pick the 5-7 most important. Document mitigation + escalation for each.

---

# Pre-Publish Skill Validation Checklist

Complete this checklist before merging a skill:

**Frontmatter & Metadata**
- [ ] `name` field present and matches directory name (kebab-case)
- [ ] `description` field present and starts with "WHEN:"
- [ ] `type` field is one of: rigid, flexible, reference
- [ ] `requires` field lists all dependencies (and each skill exists)
- [ ] YAML syntax is valid (test with `yq` or similar)

**Anti-Patterns (Rigid & Flexible Skills Only)**
- [ ] Anti-Pattern Preamble section present
- [ ] 5+ rationalizations documented (with rebuttals)
- [ ] Ends with "If you are thinking any of the above, you are about to violate this skill."
- [ ] Each rationalization has a "Why It Fails" explanation

**Edge Cases**
- [ ] 5-7 edge cases documented (rigid) or 3-5 (flexible)
- [ ] Each edge case: Scenario → Mitigation → Why Naive Fails → Escalation
- [ ] At least one BLOCKED escalation (where skill can't apply)
- [ ] At least one NEEDS_COORDINATION escalation
- [ ] At least one NEEDS_INFRA_CHANGE escalation

**Workflow & Steps (Rigid Skills)**
- [ ] Workflow is step-by-step, numbered, no ambiguity
- [ ] HARD-GATE tags on 2-5 critical steps
- [ ] HARD-GATE format: "HARD-GATE: [step]. If [condition], violation occurs."
- [ ] HARD-GATE conditions are testable

**Red Flags (Rigid Skills)**
- [ ] "Red Flags — STOP" section present
- [ ] 5+ warning signs documented
- [ ] Format: "If you notice X, STOP — Y is happening"

**Iron Law (Rigid Skills)**
- [ ] Iron Law present in code block
- [ ] One non-negotiable rule, clear and enforceable

**Output Specification**
- [ ] Output format specified (document type, structure, validation)
- [ ] Examples of good vs bad output included
- [ ] Validation criteria listed

**Examples & Scenarios**
- [ ] 3-4 worked examples included
- [ ] Examples show concrete scenarios (not abstract)
- [ ] For FLEXIBLE skills: 2+ approaches shown
- [ ] No placeholder code (no "// implement this", "TODO")

**Decision Trees**
- [ ] Present if skill has >1 major choice point
- [ ] ASCII format for plaintext readability
- [ ] Each branch has clear action or next skill

**Cross-References**
- [ ] 3+ related skills linked (prerequisite, follow-up, or sibling)
- [ ] Format: `[skill-name]: one-sentence-explaining-connection`
- [ ] Prerequisite skills listed
- [ ] Follow-up skills listed

**Checklists (Rigid & Flexible Skills)**
- [ ] Pre-invocation checklist: "Do I have the right skill?"
- [ ] Pre-implementation checklist: "Am I ready?"
- [ ] Post-implementation checklist: "Did I follow correctly?"
- [ ] Each checklist has 5-10 items, binary (YES/NO)

**Text Quality**
- [ ] No placeholder text ("TBD", "TODO", "implement later", "...")
- [ ] No vague instructions ("do X", "handle Y") without examples
- [ ] No broken links (cross-references are valid)
- [ ] No orphaned sections or headers without content

**Line Count & Structure**
- [ ] Skill is 400-1500 lines (appropriate for type)
- [ ] Major sections use H2 headers (##)
- [ ] Sub-sections use H3 headers (###)
- [ ] Tables are readable (not >10 columns)

**Git & Publishing**
- [ ] File path is `skills/{skill-name}/SKILL.md`
- [ ] Commit message includes "[skill-name]" tag
- [ ] No other files in the skill directory (unless reference files like examples/)
- [ ] Skill is mentioned in forge-glossary (if it's discoverable)

---

# File Location

All skills live in `skills/{skill-name}/SKILL.md` at repo root. The `.claude/skills/` path is a symlink — never create skills there directly.

---

# Rigor Checklist (Concise Version)

Before a skill is considered complete, verify:

- [ ] Frontmatter has CSO-optimized `description` starting with WHEN
- [ ] `type` is explicitly `rigid`, `flexible`, or `reference`
- [ ] `requires` lists all skill dependencies
- [ ] Anti-Pattern Preamble has 5+ rationalizations (rigid/flexible)
- [ ] Edge Cases documented (5-7 for rigid, 3-5 for flexible) with escalation keywords
- [ ] HARD-GATE tags on non-skippable steps (rigid)
- [ ] Iron Law stated in code block (rigid)
- [ ] Red Flags — STOP section present (rigid)
- [ ] Output format specified
- [ ] No placeholder text ("TBD", "TODO", "...")
- [ ] Cross-references to 3+ related skills included
- [ ] Decision trees present (if >1 major choice point)
- [ ] Checklists: pre-invocation, pre-implementation, post-implementation
- [ ] 3-4 worked examples included (showing concrete scenarios)

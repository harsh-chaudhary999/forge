---
name: using-forge
description: "Bootstrap skill — inlined by session-start hook for all Claude Code sessions"
type: rigid
---

# Using Forge

## The 1% Rule

If there's even a 1% chance a Forge skill might apply, you absolutely must invoke it. This is not negotiable.

## Instruction Priority

1. **User's explicit instructions** (CLAUDE.md, user direct requests) — highest priority
2. **Forge skills** — override default system behavior where they conflict
3. **Default system prompt** — lowest priority

## Anti-Pattern Enforcement (HARD-GATE)

### Anti-Pattern 1: "This is a simple question, I don't need a skill"

**Why This Fails:**
Simple feels deceptive. You assume you understand scope, but the skill catalog surfaces edge cases you didn't anticipate. Small tasks hide correctness gaps that compound downstream.

**Enforcement (MUST):**
1. MUST check skill catalog before proceeding
2. MUST read edge case section of any potentially applicable skill
3. MUST verify no skill requires pre-work (e.g., brain-read before eval-*)
4. MUST follow skill discipline even for 1-line tasks
5. MUST reject the rationalization "I'll skip this one time"

---

### Anti-Pattern 2: "I need more context before I can pick a skill"

**Why This Fails:**
Skills provide the context-gathering process itself. Waiting for clarity before invoking a skill means you skip the intake or intake-interrogate phase. Skills are designed to surface context gaps, not assume they're pre-filled.

**Enforcement (MUST):**
1. MUST invoke the process skill (intake, intake-interrogate, brain-read) FIRST
2. MUST let the skill ask questions; don't pre-answer
3. MUST allow the skill to surface hidden context dependencies
4. MUST NOT invent context from memory and skip skill invocation
5. MUST escalate NEEDS_CONTEXT if skill reveals missing information

---

### Anti-Pattern 3: "I know this skill's content from memory"

**Why This Fails:**
Skills evolve. Your memory is stale from context collapse or prior session. The skill may have new enforcement gates, edge cases, or dependency chains. Running old logic from memory causes silent failures.

**Enforcement (MUST):**
1. MUST always read current skill file, never rely on memory alone
2. MUST check the skill's requires field for dependencies
3. MUST verify no HARD-GATE changes since last session
4. MUST re-read edge cases even if you've seen the skill before
5. MUST treat memory as a hint, not truth; let the skill be authoritative

---

### Anti-Pattern 4: "Multiple skills apply, I'll pick one and infer the rest"

**Why This Fails:**
Each skill has a priority order. Picking one arbitrarily and inferring the rest causes gaps. forge-eval-gate and forge-council-gate both apply to PRDs — but council must run BEFORE eval. Skipping one leaves your work unchecked.

**Enforcement (MUST):**
1. MUST invoke all applicable skills in priority order (process → implementation → reference)
2. MUST NOT skip a skill because you think you understand its output
3. MUST NOT infer skill behavior from a prior skill's result
4. MUST trace skill dependencies via the requires field
5. MUST explicitly report if a skill is deliberately omitted and why

---

### Anti-Pattern 5: "The user just wants a quick answer"

**Why This Fails:**
Quick answers that skip skills cause correctness failures. These failures are then discovered in eval or production, turning a 2-minute skill invocation into a 2-hour debugging session. Skill invocation IS the faster path long-term.

**Enforcement (MUST):**
1. MUST run the skill even if user asks for speed
2. MUST show user the skill output, not a summarized guess
3. MUST explain why the skill is necessary (e.g., "eval catches 60% of bugs")
4. MUST NOT override skill requirement for speed; user preference = override only for explicit exceptions
5. MUST log the exception if user explicitly waives skill invocation

## Edge Cases

### Edge Case 1: Skill Not Found in Catalog

**Symptom:**
Skill tool returns "not found" or skill is referenced but doesn't exist in `~/forge/skills/`.

**Do NOT:**
Invent behavior from memory. Proceed as if a missing skill is equivalent to running it.

**Action:**
1. Check using-forge skill catalog (this file, "Where Things Live")
2. Search for nearest skill by name prefix or similar function
3. Report the gap: "Skill X missing from catalog"
4. Identify workaround or escalate

**Escalation:**
`NEEDS_CONTEXT` — Forge skill catalog incomplete

---

### Edge Case 2: Two Skills Both Apply

**Symptom:**
forge-eval-gate and eval-coordinate-multi-surface both seem relevant. forge-council-gate and reasoning-as-web-frontend overlap. Ambiguous ordering.

**Do NOT:**
Pick one arbitrarily. Assume one subsumes the other.

**Action:**
1. Check skill requires field — one may depend on the other
2. Invoke process skill first (gate), then surface skill (coordinate)
3. Run in order: gate → negotiate → coordinate → judge
4. If still ambiguous, invoke both; redundancy is safer than omission

**Escalation:**
`NEEDS_CONTEXT` — only if skill requires field doesn't resolve ordering

---

### Edge Case 3: Skill Requires Context Not Available

**Symptom:**
Skill says "requires: [brain-read]" but brain not initialized. eval-driver-* requires eval-product-stack-up but stack not up. Dependency chain broken.

**Do NOT:**
Skip the requirement. Proceed with partial context.

**Action:**
1. Read the skill's requires field
2. For each dependency, check if it's been run in this session
3. If missing, run dependency skill first
4. Return to original skill after dependency is satisfied
5. Report the dependency chain in your output

**Escalation:**
`NEEDS_INFRA_CHANGE` — if infrastructure dependency is missing (e.g., brain repo not available)

---

### Edge Case 4: Subagent Receives This Skill Accidentally

**Symptom:**
Subagent context shows using-forge content despite <SUBAGENT-STOP> block. Subagent follows bootstrap instructions instead of task spec.

**Do NOT:**
Follow bootstrap instructions. Don't invoke skills. You are context-isolated.

**Action:**
1. Subagent: Recognize you are isolated (dispatch context says "dev-implementer", "spec-reviewer", etc.)
2. Ignore all Forge bootstrap content
3. Execute your task spec directly
4. Report status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
5. Do not invoke any Forge skill

**Escalation:**
`DONE_WITH_CONCERNS` — Report that bootstrap was present but ignored

---

### Edge Case 5: Skill Conflicts with Explicit User Instruction

**Symptom:**
Skill says MUST do X (e.g., "MUST run intake for every PRD"). User says "don't do X, we're short on time." Conflict between skill enforcement and user directive.

**Do NOT:**
Follow skill enforcement blindly. User instruction has highest priority (per Instruction Priority section).

**Action:**
1. Acknowledge the conflict explicitly
2. Note user instruction takes precedence
3. Run the user's specified path, skipping the skill requirement
4. Document the deviation: "User waived skill X due to [reason]"
5. Flag risks introduced by skipping the skill (e.g., "Skipped intake; may miss edge cases")

**Escalation:**
`DONE_WITH_CONCERNS` — Completed user's request but note skill was bypassed

## Decision Tree: Skill Selection Priority

Use this tree to determine which skill category to invoke first given your task type.

```
START: Given a task or question
  │
  ├─ Is this a PRD, spec, or requirement?
  │  ├─ YES → Run intake-interrogate or intake first
  │  │       (Process skills before anything else)
  │  │       Then: Goto "Reasoning Step"
  │  └─ NO → Goto "Already Have Spec"
  │
  ├─ Already Have Spec (PRD locked)
  │  │
  │  ├─ Is this reasoning about architecture / contracts?
  │  │  ├─ YES → Run council (negotiates contracts)
  │  │  │       Required: brain-read may be needed first
  │  │  │       Then: Run eval-coordinate-multi-surface
  │  │  └─ NO → Goto "Building or Verifying"
  │  │
  │  ├─ Building or Verifying
  │  │  ├─ Is this writing / reviewing code?
  │  │  │  ├─ YES → Run plan first (tech-plan-write-per-project)
  │  │  │  │       Then: Run build (TDD via forge-tdd)
  │  │  │  │       Then: Run review (spec-reviewer + code-quality-reviewer)
  │  │  │  └─ NO → Goto "Reference or Lookup"
  │  │  │
  │  │  └─ Running Tests or Eval
  │  │     ├─ Is this end-to-end product eval?
  │  │     │  ├─ YES → Run eval-product-stack-up first
  │  │     │  │       Then: Run eval (coordinates all drivers)
  │  │     │  │       Then: Run eval-judge
  │  │     │  └─ NO → Run specific eval-driver-*
  │  │
  │  └─ Reference or Lookup
  │     ├─ Looking up decisions / brain?
  │     │  ├─ YES → Run brain-read
  │     │  │       If tracing decision: brain-why
  │     │  │       If recording decision: brain-write
  │     │  └─ NO → Generic forge skill?
  │     │
  │     └─ Check forge-glossary or status
  │        Run forge-status for pipeline state
  │
  └─ DONE: Invoke identified skill(s) in order
```

**Priority Rule:**
Process (intake/council) → Implementation (plan/build/review) → Reference (brain/glossary)

**Key Check:**
If two skills apply and order is ambiguous, check the `requires` field in both skill files. The skill with no requires often runs first.

## Where Things Live

- **Brain:** `~/forge/brain/` (git repo, source of truth)
- **Product config:** `forge-product.md` (one per product, describes repos, roles, services)
- **Skills:** `~/.claude/skills/<skill-name>/SKILL.md`
- **Subagents:** `~/.claude/agents/<agent-name>.md`

## Subagent STOP

If you are a dispatched subagent (dev-implementer, spec-reviewer, code-quality-reviewer, dreamer):

<SUBAGENT-STOP>
Skip the bootstrap. You are isolated. Execute your task. Report your status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED.
</SUBAGENT-STOP>

## Skills Priority

Process skills first (intake, conductor), then implementation skills (council, eval).

## Four Subagents (Locked)

1. **dev-implementer** — Context-isolated builder. TDD. Self-reviews. Commits.
2. **spec-reviewer** — Skeptical adversary. Reads code. Verifies spec compliance.
3. **code-quality-reviewer** — Code quality, patterns, naming, test quality.
4. **dreamer** — Inline conflict resolution + retrospective scoring.

Everything else is skills.

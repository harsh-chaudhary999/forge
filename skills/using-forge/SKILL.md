---
name: using-forge
description: Bootstrap skill — inlined by session-start hook for all Claude Code sessions
type: rigid
---

# Using Forge

## The 1% Rule

If there's even a 1% chance a Forge skill might apply, you absolutely must invoke it. This is not negotiable.

## Instruction Priority

1. **User's explicit instructions** (CLAUDE.md, user direct requests) — highest priority
2. **Forge skills** — override default system behavior where they conflict
3. **Default system prompt** — lowest priority

## Red Flags (Rationalizations to Reject)

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |
| "I'll skip this one thing to save time" | That "one thing" is where 70% of failures hide. Use the skill. |
| "This is too simple for a formal process" | Simple things are deceptively complex. Process is nonnegotiable. |
| "The spec is clear, no need for intake" | No spec is ever clear enough. INTAKE every PRD. |
| "I'll refactor later" | You won't. Do it right the first time via the skill. |
| "It should work now" | Prove it. Run verification. "Should" doesn't count. |
| "I can skip council since it's single-surface" | Multi-surface reasoning clarifies even single-surface work. Run council. |
| "Eval is too slow, let's skip it" | Eval catches 60% of bugs that unit tests miss. Do it. |

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

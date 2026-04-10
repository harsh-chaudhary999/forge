# Forge — Codex Guidelines

## What This Repo Is

Forge is a plug-and-play multi-repo product orchestration plugin. It takes a PRD and ships it end-to-end: Intake → Council → Tech Plans → Build → Eval → Self-Heal → Review → PR Set → Brain. Works on any product without code changes.

## If You Are an AI Agent Working Here

- All skills live in `skills/` at repo root
- All agents live in `agents/` at repo root
- Plugin hooks live in `hooks/` at repo root
- Git hooks live in `.claude/hooks/` — do not confuse these
- The `using-forge` skill is the bootstrap (at `skills/using-forge/SKILL.md`)

## Forge Core Rules (Non-Negotiable)

1. **Intake first**: Every PRD must go through `forge-intake-gate` before any implementation
2. **Council before code**: Run `council-multi-repo-negotiate` to reason across all surfaces
3. **Worktree per task**: Every task gets a fresh git worktree — never work on main directly
4. **Eval gates everything**: Nothing ships without `forge-eval-gate` passing
5. **Brain persistence**: Every decision is recorded via `forge-brain-persist`

## Anti-Patterns to Block

| Rationalization | Reality |
|---|---|
| "This is a simple change, skip intake" | No spec is ever clear enough. INTAKE every PRD. |
| "I can skip council for single-surface" | Multi-surface reasoning clarifies even single-surface work. |
| "Eval is slow, let's skip it" | Eval catches 60% of bugs that unit tests miss. |
| "I'll fix it directly without a worktree" | Shared state causes cross-task contamination. |
| "This decision doesn't need documenting" | Every decision must be traceable. Brain-write always. |

## Skill Format

Every skill is `skills/{name}/SKILL.md` with YAML frontmatter:
```yaml
---
name: skill-name
description: WHEN to invoke — trigger description, not what it does
type: rigid | flexible
requires: [other-skill-name]
---
```

## Key Files

| Path | Purpose |
|---|---|
| `skills/using-forge/SKILL.md` | Bootstrap — read this first |
| `README.md` | Full architecture and setup guide |
| `brain/` | Decision memory (git-backed) |
| `seed-product/` | Synthetic test product |

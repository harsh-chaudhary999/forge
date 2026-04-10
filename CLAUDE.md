# Forge Plugin — AI Guidelines

## What This Repo Is

Forge is a plug-and-play multi-repo product orchestration plugin for Claude Code, Cursor, Gemini CLI, Project IDX, and JetBrains AI. It takes a PRD and ships it end-to-end across any product stack.

## If You Are an AI Working in This Repo

- All skills live in `skills/` at repo root (not `.claude/skills/` — that is a symlink)
- All agents live in `agents/` at repo root
- Plugin hooks (session injection) live in `hooks/` at repo root
- Git hooks (commit-msg, pre-commit, etc.) live in `.claude/hooks/` — do not confuse these
- The `using-forge` skill is the bootstrap. It is injected via the `hooks/session-start` hook

## Skill Format

Every skill is a `SKILL.md` file with YAML frontmatter:
```yaml
---
name: skill-name
description: WHEN to invoke — describes the trigger, not what the skill does
type: rigid | flexible
requires: [other-skill-name]
---
```

## Key Constraints

- D5: No third-party agent frameworks. No LangChain, Playwright, Puppeteer.
- D13: No runtime dependency on any external plugin at runtime.
- D15: Skills are TDD'd — developed via pressure scenarios against seed product.
- D24: HARD-GATE tags on every non-skippable step.
- D25: Anti-Pattern preambles on every discipline-enforcing skill.

## Where Things Live

| Thing | Location |
|---|---|
| Skills (63) | `skills/` |
| Agents (4) | `agents/` |
| Commands (15) | `commands/` |
| Plugin hooks | `hooks/` |
| Git hooks | `.claude/hooks/` |
| Brain (decisions) | `brain/` |
| Seed product | `seed-product/` |
| Platform docs | `docs/platforms/` |

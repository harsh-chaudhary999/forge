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

## Execution Rules (Non-Negotiable)

- **Never write scripts to `/tmp` and execute them.** Run all bash commands inline. Writing `/tmp/verify.sh`, `/tmp/check.sh`, `/tmp/final_check.sh` etc. and then running them is forbidden — it obscures what's being executed, creates untracked side effects, and requires extra permission approvals. If a command is complex, run it directly as a multi-line heredoc or chained pipeline.
- **`/tmp` is only for data files, never for scripts.** Intermediate data files (e.g. scan output, temp lists) are acceptable. Executable scripts written to `/tmp` are not.

## Key Constraints

- D5: No third-party agent frameworks. No LangChain, Playwright, Puppeteer.
- D13: No runtime dependency on any external plugin at runtime.
- D15: Skills are TDD'd — developed via pressure scenarios against seed product.
- D24: HARD-GATE tags on every non-skippable step.
- D25: Anti-Pattern preambles on every discipline-enforcing skill.

## Where Things Live

| Thing | Location |
|---|---|
| Skills (80) | `skills/` |
| Agents (4) | `agents/` |
| Commands (17) | `commands/` |
| Plugin hooks | `hooks/` |
| Git hooks | `.claude/hooks/` |
| Brain (decisions) | `brain/` |
| Seed product | `seed-product/` |
| Platform docs | `docs/platforms/` |

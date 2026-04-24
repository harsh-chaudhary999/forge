# Forge Plugin — AI Guidelines

## What This Repo Is

Forge is a plug-and-play multi-repo product orchestration plugin for Claude Code, Cursor, Gemini CLI, Project IDX, and JetBrains AI. It takes a PRD and ships it end-to-end across any product stack.

## If You Are an AI Working in This Repo

- All skills live in `skills/` at repo root (not `.claude/skills/` — that is a symlink)
- All agents live in `agents/` at repo root
- **`hooks/`** — IDE hook manifests (`hooks.json`, `hooks-cursor.json`) and the **`hooks/session-start`** shell shim (for configs that do not call `node` directly)
- **`.claude/hooks/`** — Claude Code hook implementations (`session-start.cjs`, `pre-tool-use.cjs`, …) plus git hook scripts installed for this repo — do not confuse the two directories
- The `using-forge` skill is the bootstrap; Claude Code loads it via **`hooks/hooks.json`** → **`session-start.cjs`**

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

- **D5 (agent frameworks vs eval hosts):** Do **not** ship **LangChain** (or similar agent orchestration frameworks) **inside Forge plugin code** (skills, bundled hooks, first-party tools) as a runtime dependency. **Playwright, Puppeteer, raw CDP clients, Appium, XCTest, or browser/device automation invoked via MCP** are **not** banned for **your product’s eval** on the **operator’s machine or CI**: they run **outside** Forge’s shipped plugin code. **Before choosing a web or mobile driver implementation**, ask the human **how they want to proceed** (e.g. existing **MCP** for browser/Appium vs local **CDP** / **ADB** / **XCTest** scripts). Document the choice in the task brain if it affects reproducibility.
- D13: No runtime dependency on any external plugin at runtime.
- D15: Skills are TDD'd — developed via pressure scenarios against seed product.
- D24: HARD-GATE tags on every non-skippable step.
- D25: Anti-Pattern preambles on every discipline-enforcing skill.

## Where Things Live

| Thing | Location |
|---|---|
| Skills (full catalog) | `skills/` — count: `bash scripts/count-skills.sh` from repo root |
| Agents (4) | `agents/` |
| Commands (17) | `commands/` |
| Hook manifests + `hooks/session-start` shim | `hooks/` |
| Claude / git hook scripts (`.cjs`) | `.claude/hooks/` |
| Brain (decisions) | `brain/` |
| Seed product | `seed-product/` |
| Platform docs | `docs/platforms/` |

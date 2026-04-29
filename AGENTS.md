# Forge — Codex Guidelines

## What This Repo Is

Forge is a plug-and-play multi-repo product orchestration plugin. It takes a PRD and ships it end-to-end: Intake → Council → Tech Plans → Build → Eval → Self-Heal → Review → PR Set → Brain. Works on any product without code changes.

## If You Are an AI Agent Working Here

- All skills live in `skills/` at repo root
- All agents live in `agents/` at repo root
- **`hooks/`** — hook manifests (`hooks.json`, `hooks-cursor.json`) and **`hooks/session-start`** shim
- **`.claude/hooks/`** — Claude Code + repo git hook scripts (`*.cjs`); do not confuse with `hooks/`
- The `using-forge` skill is the bootstrap (at `skills/using-forge/SKILL.md`)

## Forge Core Rules (Non-Negotiable)

1. **Intake first**: Every PRD must go through `forge-intake-gate` before any implementation
2. **Council before code**: Run `council-multi-repo-negotiate` to reason across all surfaces
3. **Worktree per task**: Every task gets a fresh git worktree — never work on main directly
4. **Eval gates everything**: Nothing ships without `forge-eval-gate` passing
5. **Brain persistence**: Every decision is recorded via `forge-brain-persist`
6. **Instruction completeness — size is not a skip lever**: Large files (e.g. multi‑thousand lines), long export lists, or bulky reads/writes **do not** authorize skipping steps, summarizing instead of executing, or “good enough” partials. **Do the full work** the skill or command requires (batch `Read` offsets, chunked writes, Shell streaming to disk under the brain). If something is **actually** impossible (hard tool limit, missing credentials), record **BLOCKED** with evidence — **never** silent truncation. **Skill-defined** hard stops (e.g. that skill’s own **HARD-GATE** or explicit fail condition) still apply **as written in that skill**; they are not the same as self-chosen “too much data.”

## Written artifacts — precision (plans, scans, QA, eval, code, tests)

- **Do not** substitute **scale** (counts, **"60+"**, **"many"**) for **substance** when the reader needs to act or verify. A number without **what / where / how** is still ambiguous.
- **Do** tie every material claim to **concrete evidence**:
  - **What** — named thing (path, symbol, endpoint, test id, `prd-locked.md` bullet, `SCAN.json` key).
  - **Where** — repo + file path, or `~/forge/brain/…` path, or doc heading / line range.
  - **How** — how you know (exact shell one-liner + cwd, `Read` / `rg` pattern, commit SHA, phase artifact). Another agent must be able to re-check without guessing.
- **Enumerated lists** beat aggregate-only summaries when the set is the deliverable (services touched, files changed, cases covered). If the set is huge, slice by **directory or role** and still give **paths + how** per slice — do not collapse to a headline count alone.
- If evidence does not exist yet: **UNKNOWN** + the **specific** files/commands you will run — not **N+** and not count-only hand-waving.

## Anti-Patterns to Block

| Rationalization | Reality |
|---|---|
| "This is a simple change, skip intake" | No spec is ever clear enough. INTAKE every PRD. |
| "I can skip council for single-surface" | Multi-surface reasoning clarifies even single-surface work. |
| "Eval is slow, let's skip it" | Eval catches whole classes of integration failures that isolated unit tests do not exercise. Skipping it ships blind. |
| "I'll fix it directly without a worktree" | Shared state causes cross-task contamination. |
| "This decision doesn't need documenting" | Every decision must be traceable. Brain-write always. |
| "~60+ services / files — close enough" | **Not close enough.** Need **what / where / how** per item or slice (paths, commands, commits) — not aggregate scale alone. |
| "This file / list is huge (5k–8k lines) — I'll extract a sample or skip the rest" | **BLOCKED** unless the **skill itself** explicitly allows sampling. Volume is **not** discretionary relief from instructions. Full export / full read / full write as required, or **BLOCKED** with what you tried. |
| "I'll narrate the full Forge pipeline in every chat turn so the user sees the big picture" | **Confuses humans upstream of those gates.** In **assistant dialogue**, follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** **Horizon narration** — **one-step horizon** (immediate next prerequisite only) unless the user asked what comes next or the current question **depends** on a downstream artifact. Full order stays in **README** / **commands/**. |
| "Bundled turns, command-tutorial prefaces, or trailing later-stage nags are fine while I'm eliciting one answer" | **Invalid.** One structured prompt must not smuggle other forks in prose; do not restate **`commands/`** or gate status unprompted; do not suffix *not ready for … yet* — **`docs/forge-one-step-horizon.md`**; **`using-forge`** **Multi-question elicitation** items **6–8**. |

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

## Repo constraints (Codex)

**`CLAUDE.md`** is authoritative for **D5** (no LangChain-style frameworks in **Forge plugin code**; **host eval** may use CDP, Playwright, Puppeteer, Appium, XCTest, or **MCP** — **ask the user** which path), **D13**, and execution rules (no `/tmp` scripts, etc.).

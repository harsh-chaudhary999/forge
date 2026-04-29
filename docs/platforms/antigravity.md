# Forge on Google Antigravity

## Prerequisites
- Google Antigravity IDE (public preview)
- Git

## Installation

**Auto:** Antigravity auto-discovers skills from `.agent/skills/` at workspace scope.

```bash
git clone https://github.com/<YOUR_GITHUB_ORG_OR_USERNAME>/forge ~/forge
# Open ~/forge in Antigravity
```

No install script needed. Antigravity reads:
- `.agent/skills/` — Full Forge skill catalog (symlinked from `skills/`; count: `bash scripts/count-skills.sh`)
- `AGENTS.md` — Project-level agent instructions
- `GEMINI.md` — Antigravity-specific context (takes precedence over AGENTS.md)

**Global install (available in all projects):**
```bash
bash scripts/install.sh --platform antigravity
# Symlinks skills to ~/.gemini/antigravity/skills/forge/
```

## Blocking interactive prompts

Use the host’s blocking UI if present; otherwise **numbered options in chat + stop** — same semantics as **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** (all Forge hosts).

## Verification

Open the Forge directory in Antigravity. Skills should be listed in the agent's available capabilities. Try invoking:
- "Use the forge-intake-gate skill to start intake"
- "What skills are available from Forge?"

## Keeping Forge updated

**Discovery:** same as all hosts — **[README Section 4](../../README.md#4-keeping-forge-updated-how-you-hear-about-changes)**.

**Apply:**

- If you work **inside the `~/forge` clone** (`.agent/skills/` symlinks in-repo): **`cd ~/forge && git pull`** then restart Antigravity / start a new session.
- If you used **`install.sh --platform antigravity`** (skills under **`~/.gemini/antigravity/skills/forge/`**): run **`cd ~/forge && git pull && bash scripts/install.sh --platform antigravity`** so symlinks refresh.

## Available Features

| Feature | Status |
|---|---|
| Skills (full tree) | Full native support via `.agent/skills/` |
| AGENTS.md | Auto-loaded as project context |
| GEMINI.md | Auto-loaded (takes precedence) |
| MCP integration | Compatible with Forge's tool-based approach |

## Forge phase session styles

Antigravity’s UI controls how aggressively the agent edits and runs tools. Map Forge phases to **planning-style** vs **execution-style** as in **[`session-modes-forge.md`](session-modes-forge.md)** — the same document used for Cursor, Claude Code, and CLI hosts.

## How It Works

### Three-Level Skill Loading
Antigravity uses efficient progressive loading:
1. **Level 1 — Frontmatter only:** YAML metadata from each SKILL.md (~20-50 tokens). Used for semantic matching.
2. **Level 2 — Full content:** Complete SKILL.md loaded when the agent determines the skill is relevant (~200-2000 tokens).

This prevents context saturation — only relevant skills consume tokens.

### Skill Format Compatibility
Forge skills use SKILL.md with YAML frontmatter — the exact format Antigravity expects:
```yaml
---
name: skill-name
description: WHEN to invoke — trigger condition
type: rigid | flexible
---
[Skill content]
```

### Context Files
- `AGENTS.md` — Cross-platform agent instructions (emerging standard)
- `GEMINI.md` — Points to `skills/using-forge/SKILL.md` for bootstrap context

## Limitations

- **No hook system:** Antigravity does not execute SessionStart hooks; context comes from AGENTS.md + GEMINI.md + skill loading
- **No slash commands:** Commands are not natively supported; invoke skills by name
- **No subagent dispatch:** Antigravity's agent model differs from Claude Code's Agent tool
- **Symlinks required:** `.agent/skills/` contains symlinks to `skills/`; if symlinks break, skills won't load

## Troubleshooting

**Skills not appearing:**
- Verify symlinks: `ls -la .agent/skills/` — each should point to `../../skills/<skill-name>`
- Counts should match canonical `skills/` (one symlink per skill dir): `test "$(ls -1 skills | wc -l)" -eq "$(ls -1 .agent/skills | wc -l)"`
- Find missing links: `comm -23 <(ls -1 skills | sort) <(ls -1 .agent/skills | sort)`
- Recreate all symlinks: `cd .agent/skills && for s in ../../skills/*/; do ln -sfn "$s" "$(basename "$s")"; done`

**AGENTS.md not loaded:**
- Verify file exists at repo root
- Check Antigravity version (AGENTS.md support added in v1.20.3+)

**GEMINI.md not taking precedence:**
- Verify GEMINI.md exists and is valid
- Update Antigravity to latest version

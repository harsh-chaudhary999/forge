# Forge on Claude Code

## Prerequisites
- Claude Code CLI or VS Code extension
- Node.js 16+
- Git

## Installation

**Auto (recommended):** Forge is detected as a plugin via `.claude-plugin/plugin.json`. Clone the repo and restart Claude Code.

```bash
git clone https://github.com/harsh-chaudhary999/forge ~/forge
```

**Fallback:**
```bash
cd ~/forge && bash scripts/install.sh --platform claude-code
```

## Verification

Start a new Claude Code session. You should see Forge context injected (the `using-forge` skill). Run:
```
/forge-status
```

## Available Features

| Feature | Status |
|---|---|
| Skills (68) | Full support via Skill tool |
| Agents (4) | Full support via Agent tool |
| Hooks | SessionStart injects `using-forge` bootstrap |
| Commands (17) | All slash commands available |
| Brain | Full read/write to `~/forge/brain/` |
| Worktrees | Full git worktree isolation |

## How It Works

1. **Session Start:** The `hooks/session-start` script runs on every session start, clear, or compact event
2. **Context Injection:** The `using-forge` skill content is injected as `additionalContext` via `hookSpecificOutput`
3. **Skill Loading:** All 68 skills in `skills/` are available via the `Skill` tool
4. **Agent Dispatch:** 4 subagents are available via the `Agent` tool with isolation via worktrees

## Forge phase session styles

Claude Code does not use Cursor’s **Plan/Agent** labels. Use the same **Forge-native** split everywhere: **planning-style** (intake, council, plan review) vs **execution-style** (build, eval, heal). Achieve it with **prompts**, **permission scope**, and **human checkpoints** — see **[`session-modes-forge.md`](session-modes-forge.md)**.

## Plugin skill layout (merged `skills/`)

Claude Code loads skills from the plugin cache (`~/.claude/plugins/cache/forge-plugin/forge/<version>/skills/`). Stale or nested `skills/skills/` trees cause the same “wrong intake” class of bugs as on Cursor. After install, run:

```bash
bash scripts/verify-forge-plugin-install.sh --platform claude-code
```

See **[`plugin-skill-layout.md`](plugin-skill-layout.md)**.

## Limitations
None — Claude Code is the primary platform. All features are fully supported.

## Troubleshooting

**Hook not firing:**
- Check `hooks/hooks.json` is valid JSON
- Verify `hooks/session-start` is executable: `chmod +x hooks/session-start`
- Check Claude Code plugin cache: `ls ~/.claude/plugins/cache/`

**Skills not loading:**
- Verify skill files exist: `ls skills/*/SKILL.md`
- Check YAML frontmatter is valid in each SKILL.md

**Commands not available:**
- Verify command files exist: `ls commands/*.md`
- Each command needs YAML frontmatter with a `description` field

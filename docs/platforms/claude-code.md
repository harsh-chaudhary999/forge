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
| Skills (63) | Full support via Skill tool |
| Agents (4) | Full support via Agent tool |
| Hooks | SessionStart injects `using-forge` bootstrap |
| Commands (15) | All slash commands available |
| Brain | Full read/write to `~/forge/brain/` |
| Worktrees | Full git worktree isolation |

## How It Works

1. **Session Start:** The `hooks/session-start` script runs on every session start, clear, or compact event
2. **Context Injection:** The `using-forge` skill content is injected as `additionalContext` via `hookSpecificOutput`
3. **Skill Loading:** All 63 skills in `skills/` are available via the `Skill` tool
4. **Agent Dispatch:** 4 subagents are available via the `Agent` tool with isolation via worktrees

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

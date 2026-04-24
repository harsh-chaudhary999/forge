# Forge on Claude Code

## Prerequisites
- Claude Code CLI or VS Code extension
- Node.js 16+
- Git

## Installation

**Auto (recommended):** Forge is detected as a plugin via `.claude-plugin/plugin.json`. Clone the repo and restart Claude Code.

```bash
git clone https://github.com/<YOUR_GITHUB_ORG_OR_USERNAME>/forge ~/forge
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

## Keeping Forge updated

There is **no** in-app auto-update for Forge. When your **`~/forge`** clone has new commits, refresh this host:

```bash
cd ~/forge && git pull && bash scripts/install.sh --platform claude-code
```

Start a **new Claude Code session** after skills or hooks change. **How to notice upstream changes** (GitHub Watch, Releases, team comms) is the same for every editor — see **[README Section 4 — Keeping Forge updated](../../README.md#4-keeping-forge-updated-how-you-hear-about-changes)**.

## Available Features

| Feature | Status |
|---|---|
| Skills (full `skills/` tree) | Full support via Skill tool — count: `bash scripts/count-skills.sh` |
| Codebase scan (`forge_scan.py`) | **`install.sh --platform claude-code`** copies **`tools/`** into the plugin cache — **`python3 ~/.claude/plugins/cache/forge-plugin/forge/<version>/tools/forge_scan.py`** when not using a Forge git checkout as cwd |
| Agents (4) | Full support via Agent tool |
| Hooks | SessionStart injects `using-forge` bootstrap |
| Commands (17) | All slash commands available |
| Brain | Full read/write to `~/forge/brain/` |
| Worktrees | Full git worktree isolation |

## How It Works

1. **Session Start:** `hooks/hooks.json` runs **`node …/.claude/hooks/session-start.cjs`** on every session start, clear, or compact event (repo also ships **`hooks/session-start`** as a shim for other configs)
2. **Context Injection:** The `using-forge` skill content is injected as `additionalContext` via `hookSpecificOutput`
3. **Skill Loading:** The full `skills/` catalog is available via the `Skill` tool (count: `bash scripts/count-skills.sh` from Forge root)
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

**`/plugin` shows forge-plugin "Failed to load" (often 1 error):**

- **Cause:** The user install cache must include **`.claude/hooks/*.cjs`** (Claude runs `node "${CLAUDE_PLUGIN_ROOT}/.claude/hooks/session-start.cjs"` per `hooks/hooks.json`). Older **`install.sh`** copies only the `hooks/` manifest folder and omitted those scripts.
- **Fix:** `git pull` in your Forge clone, then re-run **`bash scripts/install.sh --platform claude-code`**, fully quit Claude Code, reopen, and check **`/plugin` → Installed** again.
- **Verify on disk:** `ls ~/.claude/plugins/cache/forge-plugin/forge/*/.claude/hooks/session-start.cjs` — file must exist; **`…/forge/<version>/.claude/skills`** should be a symlink to **`../skills`**.

**Hook not firing:**
- Check `hooks/hooks.json` is valid JSON and **`SessionStart`** points at **`session-start.cjs`**
- If you use the **`hooks/session-start`** shim (e.g. some Cursor-style configs), run **`chmod +x hooks/session-start`**
- Check Claude Code plugin cache: `ls ~/.claude/plugins/cache/`

**Skills not loading:**
- Verify skill files exist: `ls skills/*/SKILL.md`
- Check YAML frontmatter is valid in each SKILL.md

**Commands not available:**
- Verify command files exist: `ls commands/*.md`
- Each command needs YAML frontmatter with a `description` field

# Forge on Cursor

## Prerequisites
- Cursor IDE
- Node.js 16+
- Git

## Installation

**Auto (recommended):** Forge is detected as a plugin via `.cursor-plugin/plugin.json`. Clone the repo and restart Cursor.

```bash
git clone https://github.com/harsh-chaudhary999/forge ~/forge
```

**Fallback:**
```bash
cd ~/forge && bash scripts/install.sh --platform cursor
```

## Verification

Open Cursor in the Forge directory. The `.cursorrules` file provides project-level AI context. The session-start hook injects the `using-forge` bootstrap.

## Available Features

| Feature | Status |
|---|---|
| Skills (68) | Full support |
| Agents (4) | Full support |
| Hooks | SessionStart via `hooks-cursor.json` |
| Commands (17) | All slash commands available |
| Brain | Full read/write |
| Worktrees | Full isolation |
| `.cursorrules` | Project-level AI context |

## How It Works

1. **Plugin Discovery:** Cursor reads `.cursor-plugin/plugin.json` to discover the plugin
2. **Project Context:** `.cursorrules` is loaded as project-level AI instructions
3. **Hook Format:** Cursor uses snake_case (`session_start` instead of `SessionStart`)
4. **Session Injection:** The `hooks/session-start` script detects Cursor via `CURSOR_PLUGIN_ROOT` env var and outputs the Cursor-specific JSON format

## Differences from Claude Code

- Hook config uses `hooks-cursor.json` (snake_case keys) instead of `hooks.json`
- Session-start output uses `additional_context` (snake_case) instead of `hookSpecificOutput.additionalContext`
- `.cursorrules` provides additional project context (Claude Code uses `CLAUDE.md`)

## Plan mode vs Agent mode (Cursor UI)

Cursor exposes **Plan** vs **Agent** in the UI. Map them to Forge’s portable **planning-style** vs **execution-style** phases — see **[`session-modes-forge.md`](session-modes-forge.md)** (same convention for every supported host).

**Quick map:** **`/intake`**, **`/council`**, **`/plan` review** → Plan. **`/build`**, **`/eval`**, **`/heal`** → Agent. Hooks cannot toggle this for you.

## Limitations
- Hook format differences require separate config file (`hooks-cursor.json`)
- Some advanced Claude Code features may not be available

## Troubleshooting

### Duplicate or nested `skills/` (agents read stale intake)

Same issue as other merged-tree installs — see **[`plugin-skill-layout.md`](plugin-skill-layout.md)**.

**Quick check (Cursor):**

```bash
bash scripts/verify-forge-plugin-install.sh --platform cursor
```

**`.cursorrules` not loading:**
- Verify the file exists at repo root: `ls -la .cursorrules`
- Restart Cursor after adding the file

**Hook not firing:**
- Check `hooks/hooks-cursor.json` is valid JSON
- Verify `CURSOR_PLUGIN_ROOT` env var is set during hook execution

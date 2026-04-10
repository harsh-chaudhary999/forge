---
description: "Show platform-specific Forge installation instructions"
---

Display Forge installation instructions for all supported platforms:

## Supported Platforms

### Claude Code (Auto)
Forge is auto-detected as a plugin. Restart Claude Code to activate.
- Plugin manifest: `.claude-plugin/plugin.json`
- Hook injection: `hooks/session-start` injects `using-forge` at session start

### Cursor (Auto)
Same plugin system as Claude Code. Restart Cursor to activate.
- Plugin manifest: `.cursor-plugin/plugin.json`
- Project context: `.cursorrules` provides project-level AI guidelines

### Google Antigravity (Auto)
Skills are auto-discovered from `.agent/skills/` directory.
- 58 skills available via native skill loading
- `AGENTS.md` and `GEMINI.md` provide project context

### Gemini CLI (Auto)
Extension auto-detected from `gemini-extension.json`.
- Context loaded from `GEMINI.md` → `skills/using-forge/SKILL.md`

### OpenAI Codex (Auto)
Codex reads `AGENTS.md` at session start automatically.

### GitHub Copilot CLI (Auto)
Session-start hook detects Copilot CLI and injects context.
- Tool mapping: `references/copilot-tools.md`

### JetBrains AI (Manual)
Copy the guidelines template to each project:
```bash
mkdir -p <your-project>/.junie
cp templates/junie-guidelines.md <your-project>/.junie/guidelines.md
```

## Fallback Install Script
```bash
bash scripts/install.sh                         # All platforms
bash scripts/install.sh --platform antigravity  # Single platform
bash scripts/install.sh --uninstall             # Remove
```

See `docs/platforms/` for detailed per-platform guides.

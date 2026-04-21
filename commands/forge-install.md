---
name: forge-install
description: "Show Forge plugin installation instructions for Cursor, Claude Code, Antigravity, CLIs, and JetBrains — paths and scripts in this repo only."
---

Display **Forge plugin** installation instructions for all supported platforms (this repository).

## Supported Platforms

### Claude Code (Auto)
Forge is auto-detected as a plugin. Restart Claude Code to activate.
- Plugin manifest: **`.claude-plugin/plugin.json`**
- Hook injection: **`hooks/session-start`** injects **`using-forge`** at session start

### Cursor (Auto)
Same plugin pattern. Restart Cursor to activate.
- Plugin manifest: **`.cursor-plugin/plugin.json`**
- Project context: **`.cursorrules`**

### Google Antigravity (Auto)
Skills from **`.agent/skills/`** (symlinks to **`skills/`**).
- **`AGENTS.md`**, **`GEMINI.md`**

### Gemini CLI (Auto)
**`gemini-extension.json`**; context from **`GEMINI.md`**

### OpenAI Codex (Auto)
**`AGENTS.md`** at session start

### GitHub Copilot CLI (Auto)
Session-start hook; see **`references/copilot-tools.md`** for tool mapping

### JetBrains AI (Manual)
```bash
mkdir -p <your-project>/.junie
cp templates/junie-guidelines.md <your-project>/.junie/guidelines.md
```
(**`templates/junie-guidelines.md`** lives in **this** Forge repo.)

## Fallback install script

```bash
bash scripts/install.sh                         # All platforms
bash scripts/install.sh --platform antigravity  # Single platform
bash scripts/install.sh --uninstall             # Remove
```

See **`docs/platforms/`** for per-platform guides.

**vs `/forge`:** This command only **documents install**; it does not run the delivery pipeline. Full E2E: **`commands/forge.md`**.

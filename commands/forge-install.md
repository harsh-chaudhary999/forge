---
name: forge-install
description: "Show Forge plugin installation instructions for Claude Code — paths and scripts in this repo only."
---

Display **Forge plugin** installation instructions for **Claude Code** (this repository is the Claude-only build; other IDEs live on dedicated branches).

## Install

```bash
bash scripts/install.sh              # install for Claude Code
bash scripts/install.sh --uninstall  # remove
```

This copies the plugin into the Claude Code plugin cache (`~/.claude/plugins/cache/forge-plugin/forge/<version>/`), registers the three Forge hooks in `~/.claude/settings.json`, symlinks the slash commands into `~/.claude/commands/forge`, and copies dynamic workflows into `~/.claude/workflows/`. Restart Claude Code to activate.

- Plugin manifest: **`.claude-plugin/plugin.json`** (+ **`.claude-plugin/marketplace.json`** for marketplace discovery)
- Hook manifest: **`hooks/hooks.json`** → **`.claude/hooks/session-start.cjs`** injects **`using-forge`** at session start
- Brain MCP server manifest: **`.mcp.json`** (register with `claude mcp add forge-brain -- python3 ~/forge/tools/forge_brain_mcp.py`)

Verify with **`/forge-status`** (and **`/doctor`** for install health). Full guide: **[`docs/platforms/claude-code.md`](../docs/platforms/claude-code.md)**.

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation; **one blocking affordance per unrelated fork**; **`AskUserQuestion`** = short title + options; **headline / first § = immediate next artifact**; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts** (see **`skills/_shared/human-input.md`**).

**vs `/forge`:** This command only **documents install**; it does not run the delivery pipeline. Full E2E: **`commands/forge.md`**.

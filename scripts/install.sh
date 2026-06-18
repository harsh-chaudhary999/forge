#!/usr/bin/env bash
# Forge Plugin Installer (Claude Code)
# Installs Forge as a native Claude Code plugin.
# Usage:
#   bash scripts/install.sh                         # Install for Claude Code
#   bash scripts/install.sh --uninstall             # Remove
#
# This branch ships a Claude-only build. Other-IDE builds live on their own branches.
# Must be run with **bash** (not `sh`): the script uses bash arrays and `[[`.

set -euo pipefail

if [ -z "${BASH_VERSION:-}" ]; then
  echo "ERROR: Run with bash, not sh. Example: bash scripts/install.sh" >&2
  exit 1
fi

FORGE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FORGE_VERSION=$(node -e "console.log(require('${FORGE_DIR}/package.json').version)" 2>/dev/null || echo "1.1.0")

# ── Argument Parsing ─────────────────────────────────────────────────────
TARGET_PLATFORM=""
UNINSTALL=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --platform)
      TARGET_PLATFORM="$2"
      shift 2
      ;;
    --uninstall)
      UNINSTALL=true
      shift
      ;;
    --help|-h)
      echo "Forge Plugin Installer v${FORGE_VERSION} (Claude Code)"
      echo ""
      echo "Usage:"
      echo "  bash scripts/install.sh                         # Install for Claude Code"
      echo "  bash scripts/install.sh --uninstall             # Remove"
      echo ""
      echo "Platform: claude-code (this branch is Claude-only)."
      exit 0
      ;;
    *)
      echo "Unknown option: $1. Use --help for usage." >&2
      exit 1
      ;;
  esac
done

# This branch only targets Claude Code. Accept --platform claude-code for compatibility; reject others.
if [[ -n "${TARGET_PLATFORM}" && "${TARGET_PLATFORM}" != "claude-code" ]]; then
  echo "ERROR: This is the Claude-only branch — '${TARGET_PLATFORM}' is not available here." >&2
  echo "       Use the dedicated branch for that IDE, or omit --platform." >&2
  exit 1
fi

echo "Forge Plugin Installer v${FORGE_VERSION} (Claude Code)"
echo "Source: ${FORGE_DIR}"
echo ""

# ── Claude Code ──────────────────────────────────────────────────────────
install_claude_code() {
  local plugin_dir="${HOME}/.claude/plugins/cache/forge-plugin/forge/${FORGE_VERSION}"
  echo "Installing for Claude Code..."
  mkdir -p "${plugin_dir}"

  # Always replace copied directories to avoid nested paths on re-install
  # (e.g. commands/commands, hooks/hooks, .claude-plugin/.claude-plugin).
  rm -rf "${plugin_dir}/skills" "${plugin_dir}/agents" "${plugin_dir}/hooks" "${plugin_dir}/commands" "${plugin_dir}/.claude-plugin"
  cp -r "${FORGE_DIR}/skills"                "${plugin_dir}/skills"
  cp -r "${FORGE_DIR}/agents"                "${plugin_dir}/agents"
  cp -r "${FORGE_DIR}/hooks"                 "${plugin_dir}/hooks"
  cp -r "${FORGE_DIR}/commands"              "${plugin_dir}/commands"
  # scan-codebase / /scan need forge_scan.py + scan_forge (phase4 → classes/, methods/, …)
  rm -rf "${plugin_dir}/tools"
  cp -r "${FORGE_DIR}/tools"                 "${plugin_dir}/tools"
  cp    "${FORGE_DIR}/package.json"          "${plugin_dir}/package.json"
  cp    "${FORGE_DIR}/CLAUDE.md"             "${plugin_dir}/CLAUDE.md"
  cp    "${FORGE_DIR}/AGENTS.md"             "${plugin_dir}/AGENTS.md"
  cp -r "${FORGE_DIR}/.claude-plugin"        "${plugin_dir}/.claude-plugin"
  # Brain MCP server manifest (Claude Code reads .mcp.json at the plugin root)
  cp    "${FORGE_DIR}/.mcp.json"             "${plugin_dir}/.mcp.json"

  # hooks/hooks.json runs node "${CLAUDE_PLUGIN_ROOT}/.claude/hooks/*.cjs" — the
  # runnable hook scripts live in repo .claude/hooks/ (not hooks/). Without this
  # copy, Claude Code shows forge-plugin "Failed to load".
  rm -rf "${plugin_dir}/.claude/hooks"
  mkdir -p "${plugin_dir}/.claude"
  cp -r "${FORGE_DIR}/.claude/hooks" "${plugin_dir}/.claude/hooks"

  # session-start.cjs resolves using-forge from .claude/skills/ (one dir up from
  # .claude/hooks); merged install keeps the tree at skills/ — symlink so hooks match repo layout.
  rm -f "${plugin_dir}/.claude/skills" 2>/dev/null || true
  ln -sfn "../skills" "${plugin_dir}/.claude/skills"

  # Make hook scripts executable (graceful — not all files may exist)
  find "${plugin_dir}/.claude-plugin" -name "*.cjs" -exec chmod +x {} \; 2>/dev/null || true
  find "${plugin_dir}/.claude/hooks" -type f -name "*.cjs" -exec chmod +x {} \; 2>/dev/null || true

  # Register forge hooks directly in ~/.claude/settings.json.
  # We do NOT use enabledPlugins — that key triggers marketplace validation which fails
  # for local installs because Claude Code tries to fetch from GitHub even when files
  # are already cached. Registering hooks with absolute paths bypasses marketplace
  # lookup entirely while keeping session-start, prompt-submit, and pre-tool-use active.
  local settings_file="${HOME}/.claude/settings.json"
  if [ ! -f "$settings_file" ]; then
    echo '{"permissions": {"allow": []}}' > "$settings_file"
  fi
  node -e "
    const fs = require('fs');
    const data = JSON.parse(fs.readFileSync('${settings_file}', 'utf-8'));

    // Remove stale enabledPlugins entry that triggers marketplace validation errors.
    if (data.enabledPlugins) {
      delete data.enabledPlugins['forge@forge-plugin'];
      if (Object.keys(data.enabledPlugins).length === 0) delete data.enabledPlugins;
    }

    // Register hooks with absolute paths — no \${CLAUDE_PLUGIN_ROOT} required.
    // Replace-in-place: remove prior Forge plugin hook entries for each event, then add
    // the current ones. Prevents duplicate SessionStart / UserPromptSubmit / PreToolUse
    // blocks when users upgrade Forge repeatedly (old logic only skipped identical command strings).
    if (!data.hooks) data.hooks = {};
    const hooksDir = '${plugin_dir}/.claude/hooks';

    const isForgePluginHookEntry = (entry) => {
      const hooks = entry.hooks || [];
      return hooks.some(
        (h) => h && typeof h.command === 'string' && h.command.includes('forge-plugin')
      );
    };

    const replaceForgeHook = (event, entry) => {
      if (!data.hooks[event]) data.hooks[event] = [];
      data.hooks[event] = data.hooks[event].filter((e) => !isForgePluginHookEntry(e));
      data.hooks[event].push(entry);
    };

    replaceForgeHook('SessionStart', {
      matcher: 'startup|clear|compact',
      hooks: [{type: 'command', command: 'node \"' + hooksDir + '/session-start.cjs\"', async: false}]
    });

    replaceForgeHook('UserPromptSubmit', {
      hooks: [{type: 'command', command: 'node \"' + hooksDir + '/prompt-submit.cjs\"', async: false}]
    });

    replaceForgeHook('PreToolUse', {
      matcher: 'Bash|Read|Write|Edit|StrReplace|Grep|Glob|SemanticSearch|CodebaseSearch|WebFetch|WebSearch|Task|Delete|ReadLints|EditNotebook|NotebookEdit|TodoWrite|Shell|GenerateImage|AskQuestion|AskUserQuestion|SwitchMode|AwaitShell|mcp__',
      hooks: [{type: 'command', command: 'node \"' + hooksDir + '/pre-tool-use.cjs\"', async: false}]
    });

    if (!data.permissions) data.permissions = {};
    if (!data.permissions.allow) data.permissions.allow = [];
    const forgePerms = [
      'Bash(git *)',
      'Bash(git worktree *)',
      'Bash(npm *)',
      'Bash(node *)',
      'Bash(mkdir *)',
      'Bash(cp *)',
      'Bash(mv *)',
      'Bash(rm *)',
      'Bash(chmod *)',
      'Bash(ls *)',
      'Bash(cat *)',
      'Bash(grep *)',
      'Bash(find *)',
      'Bash(echo *)',
      'Read(*)',
      'Write(*)',
      'Edit(*)'
    ];
    forgePerms.forEach(p => {
      if (!data.permissions.allow.includes(p)) data.permissions.allow.push(p);
    });
    fs.writeFileSync('${settings_file}', JSON.stringify(data, null, 2));
  " 2>/dev/null || echo "  Warning: Could not update settings.json (Node.js required)"

  if ! command -v node >/dev/null 2>&1; then
    echo "  Note: Node.js not found on PATH — plugin files were copied but ~/.claude/settings.json"
    echo "        was not updated. Install Node and re-run, or manually add hooks to settings.json."
    echo "        See docs/platforms/claude-code.md for the manual hook registration snippet."
  fi

  # Register slash commands globally via ~/.claude/commands/forge symlink.
  # Claude Code loads commands from ~/.claude/commands/ in every session regardless of project.
  # Symlinking to FORGE_DIR/commands means the commands stay current without re-running install.
  mkdir -p "${HOME}/.claude/commands"
  ln -sfn "${FORGE_DIR}/commands" "${HOME}/.claude/commands/forge"
  echo "  Commands: ~/.claude/commands/forge → ${FORGE_DIR}/commands"

  # Install dynamic workflows globally (Claude Code loads ~/.claude/workflows/*.js as /<name>).
  if compgen -G "${FORGE_DIR}/.claude/workflows/*.js" >/dev/null 2>&1; then
    mkdir -p "${HOME}/.claude/workflows"
    for wf in "${FORGE_DIR}"/.claude/workflows/*.js; do
      cp "$wf" "${HOME}/.claude/workflows/$(basename "$wf")"
    done
    echo "  Workflows: ~/.claude/workflows/ ← $(ls "${FORGE_DIR}"/.claude/workflows/*.js | wc -l | tr -d ' ') file(s)"
  fi

  echo "  Done: ${plugin_dir}"
  if [[ -x "${FORGE_DIR}/scripts/verify-forge-plugin-install.sh" ]]; then
    echo "  Verify merged skill trees: bash \"${FORGE_DIR}/scripts/verify-forge-plugin-install.sh\" --platform claude-code"
  fi
}

uninstall_claude_code() {
  local plugin_dir="${HOME}/.claude/plugins/cache/forge-plugin"
  if [ -d "$plugin_dir" ]; then
    rm -rf "$plugin_dir"
    echo "  Removed: ${plugin_dir}"
  fi
  # Remove from installed_plugins.json
  local installed_file="${HOME}/.claude/plugins/installed_plugins.json"
  if [ -f "$installed_file" ]; then
    node -e "
      const fs = require('fs');
      const data = JSON.parse(fs.readFileSync('${installed_file}', 'utf-8'));
      delete data.plugins['forge@forge-plugin'];
      fs.writeFileSync('${installed_file}', JSON.stringify(data, null, 2));
    " 2>/dev/null || true
    echo "  Deregistered from installed_plugins.json"
  fi
  # Remove forge hooks and enabledPlugins from settings.json
  local settings_file="${HOME}/.claude/settings.json"
  if [ -f "$settings_file" ]; then
    node -e "
      const fs = require('fs');
      const data = JSON.parse(fs.readFileSync('${settings_file}', 'utf-8'));
      // Remove enabledPlugins entry
      if (data.enabledPlugins) {
        delete data.enabledPlugins['forge@forge-plugin'];
        if (Object.keys(data.enabledPlugins).length === 0) delete data.enabledPlugins;
      }
      // Remove forge hook entries (any hook command referencing forge-plugin cache)
      const isForgeCmd = c => c && typeof c.command === 'string' && c.command.includes('forge-plugin');
      for (const event of Object.keys(data.hooks || {})) {
        data.hooks[event] = data.hooks[event].filter(entry =>
          !(entry.hooks || []).every(isForgeCmd)
        );
        if (data.hooks[event].length === 0) delete data.hooks[event];
      }
      if (data.hooks && Object.keys(data.hooks).length === 0) delete data.hooks;
      fs.writeFileSync('${settings_file}', JSON.stringify(data, null, 2));
    " 2>/dev/null || true
    echo "  Removed hooks from settings.json"
  fi
  # Remove global commands symlink
  if [ -L "${HOME}/.claude/commands/forge" ]; then
    rm "${HOME}/.claude/commands/forge"
    echo "  Removed: ~/.claude/commands/forge"
  fi
  # Remove dynamic workflows shipped by Forge
  if compgen -G "${FORGE_DIR}/.claude/workflows/*.js" >/dev/null 2>&1; then
    for wf in "${FORGE_DIR}"/.claude/workflows/*.js; do
      rm -f "${HOME}/.claude/workflows/$(basename "$wf")"
    done
    echo "  Removed Forge workflows from ~/.claude/workflows/"
  fi
  # The brain MCP server may have been registered manually (see docs/brain-mcp.md):
  #   claude mcp add forge-brain -- python3 ~/forge/tools/forge_brain_mcp.py
  # The bundled .mcp.json goes away with the plugin dir above, but a manual registration
  # would otherwise dangle, pointing at a deleted script. Best-effort removal (never fail uninstall).
  if command -v claude >/dev/null 2>&1; then
    if claude mcp remove forge-brain >/dev/null 2>&1; then
      echo "  Removed forge-brain MCP registration"
    fi
  fi
}

# ── Main ─────────────────────────────────────────────────────────────────
if $UNINSTALL; then
  echo "Uninstalling Forge from Claude Code..."
  uninstall_claude_code
  action="uninstall"
else
  install_claude_code
  action="install"
fi

echo ""
echo "Forge ${action} complete!"
echo ""
if [ "$action" = "install" ]; then
  echo "Next steps:"
  echo "  1. Restart Claude Code to activate hooks"
  echo "  2. Verify: Open a new session and run /forge-status"
  echo "  3. Claude Code guide: docs/platforms/claude-code.md"
fi

#!/usr/bin/env bash
# Forge Plugin Installer
# Installs Forge as a native plugin for all supported platforms
# Usage:
#   bash scripts/install.sh                         # Auto-detect and install all
#   bash scripts/install.sh --platform claude-code  # Single platform
#   bash scripts/install.sh --uninstall             # Remove from all platforms
#
# Must be run with **bash** (not `sh`): the script uses bash arrays and `[[`.

set -euo pipefail

if [ -z "${BASH_VERSION:-}" ]; then
  echo "ERROR: Run with bash, not sh. Example: bash scripts/install.sh" >&2
  exit 1
fi

FORGE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FORGE_VERSION=$(node -e "console.log(require('${FORGE_DIR}/package.json').version)" 2>/dev/null || echo "1.0.0")

# Copy optional repo files (forks or sparse checkouts may omit them; do not abort set -e).
copy_optional_file() {
  local src="$1" dest="$2"
  if [[ -f "$src" ]]; then
    cp "$src" "$dest"
  else
    echo "  (skip optional: ${src##*/} — not in repo)" >&2
  fi
}

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
      echo "Forge Plugin Installer v${FORGE_VERSION}"
      echo ""
      echo "Usage:"
      echo "  bash scripts/install.sh                         # Auto-detect, install all"
      echo "  bash scripts/install.sh --platform <name>       # Single platform"
      echo "  bash scripts/install.sh --uninstall             # Remove from all"
      echo "  bash scripts/install.sh --uninstall --platform <name>"
      echo ""
      echo "Platforms: claude-code, cursor, antigravity, codex, opencode, gemini-cli, jetbrains, copilot-cli"
      exit 0
      ;;
    *)
      echo "Unknown option: $1. Use --help for usage." >&2
      exit 1
      ;;
  esac
done

echo "Forge Plugin Installer v${FORGE_VERSION}"
echo "Source: ${FORGE_DIR}"
echo ""

# ── Platform Detection ───────────────────────────────────────────────────
# Cursor: many installs have no `cursor` on PATH until "Shell Command: Install" in the app.
# Still install if the user data dir exists (after first launch) or the app bundle is present (macOS).
detect_cursor() {
  command -v cursor >/dev/null 2>&1 && return 0
  [[ -d "${HOME}/.cursor" ]] && return 0
  [[ "$(uname -s)" == "Darwin" && -d "/Applications/Cursor.app" ]] && return 0
  [[ "$(uname -s)" == "Darwin" && -d "${HOME}/Applications/Cursor.app" ]] && return 0
  return 1
}

detect_platforms() {
  local detected=()
  command -v claude >/dev/null 2>&1 && detected+=("claude-code")
  detect_cursor && detected+=("cursor")
  [ -d "${HOME}/.gemini/antigravity" ] && detected+=("antigravity")
  command -v gemini >/dev/null 2>&1 && detected+=("gemini-cli")
  command -v codex >/dev/null 2>&1 && detected+=("codex")
  command -v copilot >/dev/null 2>&1 && detected+=("copilot-cli")
  command -v opencode >/dev/null 2>&1 && detected+=("opencode")
  # JetBrains always included (manual step)
  detected+=("jetbrains")
  echo "${detected[@]}"
}

# ── Claude Code / Cursor ─────────────────────────────────────────────────
install_claude_code() {
  local plugin_dir="${HOME}/.claude/plugins/cache/forge-plugin/forge/${FORGE_VERSION}"
  echo "Installing for Claude Code..."
  mkdir -p "${plugin_dir}"

  rm -rf "${plugin_dir}/skills"
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
  copy_optional_file "${FORGE_DIR}/GEMINI.md" "${plugin_dir}/GEMINI.md"
  copy_optional_file "${FORGE_DIR}/gemini-extension.json" "${plugin_dir}/gemini-extension.json"
  cp -r "${FORGE_DIR}/.claude-plugin"        "${plugin_dir}/.claude-plugin"

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
  find "${plugin_dir}/hooks" -type f \( -name "*.sh" -o -name "session-start" -o -name "run-hook.cmd" \) -exec chmod +x {} \; 2>/dev/null || true
  find "${plugin_dir}/.claude-plugin" -name "*.cjs" -exec chmod +x {} \; 2>/dev/null || true
  find "${plugin_dir}/.claude/hooks" -type f -name "*.cjs" -exec chmod +x {} \; 2>/dev/null || true

  local installed_file="${HOME}/.claude/plugins/installed_plugins.json"
  local entry="{
    \"scope\": \"user\",
    \"installPath\": \"${plugin_dir}\",
    \"version\": \"${FORGE_VERSION}\",
    \"installedAt\": \"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\",
    \"lastUpdated\": \"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\"
  }"

  if [ ! -f "$installed_file" ]; then
    mkdir -p "$(dirname "$installed_file")"
    echo '{"version": 2, "plugins": {}}' > "$installed_file"
  fi

  node -e "
    const fs = require('fs');
    const data = JSON.parse(fs.readFileSync('${installed_file}', 'utf-8'));
    data.plugins['forge@forge-plugin'] = [${entry}];
    fs.writeFileSync('${installed_file}', JSON.stringify(data, null, 2));
  " 2>/dev/null || echo "  Warning: Could not update installed_plugins.json (Node.js required)"

  # Enable plugin and grant minimum permissions in Claude Code settings.json
  local settings_file="${HOME}/.claude/settings.json"
  if [ ! -f "$settings_file" ]; then
    echo '{"enabledPlugins": {}, "permissions": {"allow": []}}' > "$settings_file"
  fi
  node -e "
    const fs = require('fs');
    const data = JSON.parse(fs.readFileSync('${settings_file}', 'utf-8'));
    if (!data.enabledPlugins) data.enabledPlugins = {};
    data.enabledPlugins['forge@forge-plugin'] = true;
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
      'Bash(gemini extensions *)',
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
    echo "  Note: Node.js not found on PATH — plugin files were copied, but installed_plugins.json"
    echo "        and ~/.claude/settings.json were not merged. Install Node and re-run this step, or"
    echo "        enable the plugin manually in Claude Code."
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
}

install_cursor() {
  local plugin_dir="${HOME}/.cursor/plugins/local/forge"
  echo "Installing for Cursor..."
  mkdir -p "${plugin_dir}"

  # Replace skills wholesale so stale layouts (e.g. accidental skills/skills/) cannot persist
  # after a merge-style cp.
  rm -rf "${plugin_dir}/skills"
  cp -r "${FORGE_DIR}/skills"             "${plugin_dir}/skills"
  cp -r "${FORGE_DIR}/agents"             "${plugin_dir}/agents"
  cp -r "${FORGE_DIR}/commands"           "${plugin_dir}/commands"
  cp -r "${FORGE_DIR}/hooks"              "${plugin_dir}/hooks"
  cp    "${FORGE_DIR}/CLAUDE.md"          "${plugin_dir}/CLAUDE.md"
  copy_optional_file "${FORGE_DIR}/AGENTS.md" "${plugin_dir}/AGENTS.md"
  cp -r "${FORGE_DIR}/.cursor-plugin"     "${plugin_dir}/.cursor-plugin"
  # Same as Claude install: full scanner so /scan works without a separate Forge clone on PATH
  rm -rf "${plugin_dir}/tools"
  cp -r "${FORGE_DIR}/tools"              "${plugin_dir}/tools"
  copy_optional_file "${FORGE_DIR}/package.json" "${plugin_dir}/package.json"

  # Make hook scripts executable (graceful — not all files may exist)
  find "${plugin_dir}/hooks" -type f \( -name "*.sh" -o -name "session-start" -o -name "run-hook.cmd" \) -exec chmod +x {} \; 2>/dev/null || true

  # Write global Cursor rules so Forge loads in ANY project opened in Cursor
  # Cursor reads ~/.cursor/rules/forge.mdc as a global always-on rule
  local global_rules_dir="${HOME}/.cursor/rules"
  mkdir -p "${global_rules_dir}"
  cat > "${global_rules_dir}/forge.mdc" << 'RULES'
---
description: Forge — multi-repo product orchestration plugin
alwaysApply: true
---

You have the Forge plugin installed. Forge skills, agents, and commands are available in every session.

The Forge plugin is installed at: ~/.cursor/plugins/local/forge

Key commands: /workspace /intake /council /plan /build /eval /heal /review /dream /forge-status

Scanner (class/method stubs, full scan pipeline): python3 ~/.cursor/plugins/local/forge/tools/forge_scan.py --help

Written artifacts (plans, scan notes, QA): every material claim needs **what / where / how** — paths, anchors, reproducible commands — not headline counts alone. See **AGENTS.md** / **CLAUDE.md** in this plugin directory (same folder as `skills/`). **Never** skip required steps because inputs are large — **AGENTS.md** Core rule **6** (batch reads/writes; **BLOCKED** only with evidence).

On every session start: read ~/.cursor/plugins/local/forge/skills/using-forge/SKILL.md and follow its bootstrap instructions.
RULES

  echo "  Done: ${plugin_dir}"
  echo "  Global Cursor rules: ${global_rules_dir}/forge.mdc (loads in every project)"
  echo "  Note: Restart Cursor to activate."
  if [[ -x "${FORGE_DIR}/scripts/verify-forge-plugin-install.sh" ]]; then
    echo "  Verify plugin skill layout: bash \"${FORGE_DIR}/scripts/verify-forge-plugin-install.sh\" --platform cursor"
    echo "  (all IDEs with merged skills/: --all)"
  fi
}

uninstall_cursor() {
  local plugin_dir="${HOME}/.cursor/plugins/local/forge"
  if [ -d "$plugin_dir" ]; then
    rm -rf "$plugin_dir"
    echo "  Removed: ${plugin_dir}"
  fi
}

# ── Antigravity (Google) ─────────────────────────────────────────────────
install_antigravity() {
  local skills_dir="${HOME}/.gemini/antigravity/skills/forge"
  echo "Installing for Antigravity (global)..."
  mkdir -p "${skills_dir}"

  # Symlink each skill directory
  for skill in "${FORGE_DIR}"/skills/*/; do
    local name
    name=$(basename "$skill")
    ln -sf "${skill}" "${skills_dir}/${name}" 2>/dev/null || cp -r "${skill}" "${skills_dir}/${name}"
  done

  echo "  Done: ${skills_dir} ($(ls "${skills_dir}" | wc -l | tr -d ' ') skills)"
}

uninstall_antigravity() {
  local skills_dir="${HOME}/.gemini/antigravity/skills/forge"
  if [ -d "$skills_dir" ]; then
    rm -rf "$skills_dir"
    echo "  Removed: ${skills_dir}"
  fi
}

# ── Codex (OpenAI) ───────────────────────────────────────────────────────
install_codex() {
  local marketplace_file="${HOME}/.agents/plugins/marketplace.json"
  echo "Installing for Codex..."
  mkdir -p "$(dirname "$marketplace_file")"

  # Create or update the personal marketplace file
  if [ ! -f "$marketplace_file" ]; then
    echo '{"plugins": []}' > "$marketplace_file"
  fi

  node -e "
    const fs = require('fs');
    const data = JSON.parse(fs.readFileSync('${marketplace_file}', 'utf-8'));
    if (!data.plugins) data.plugins = [];
    // Remove existing forge entry
    data.plugins = data.plugins.filter(p => p.name !== 'forge');
    data.plugins.push({
      name: 'forge',
      source: { source: 'local', path: '${FORGE_DIR}' },
      policy: { installation: 'AVAILABLE', authentication: 'ON_INSTALL' },
      category: 'Productivity'
    });
    fs.writeFileSync('${marketplace_file}', JSON.stringify(data, null, 2));
  " 2>/dev/null || echo "  Warning: Could not update marketplace.json (Node.js required)"

  echo "  Done: registered in ${marketplace_file}"
  echo "  Note: Run 'codex plugin install forge' to activate."
}

uninstall_codex() {
  local marketplace_file="${HOME}/.agents/plugins/marketplace.json"
  if [ -f "$marketplace_file" ]; then
    node -e "
      const fs = require('fs');
      const data = JSON.parse(fs.readFileSync('${marketplace_file}', 'utf-8'));
      if (data.plugins) data.plugins = data.plugins.filter(p => p.name !== 'forge');
      fs.writeFileSync('${marketplace_file}', JSON.stringify(data, null, 2));
    " 2>/dev/null || true
    echo "  Deregistered from ${marketplace_file}"
  fi
  # Also remove cached copy if present
  local cache_dir="${HOME}/.codex/plugins/cache"
  if [ -d "${cache_dir}" ]; then
    rm -rf "${cache_dir}"/*/forge 2>/dev/null || true
    echo "  Removed from Codex plugin cache"
  fi
}

# ── OpenCode ─────────────────────────────────────────────────────────────
install_opencode() {
  local plugin_dir="${HOME}/.opencode/plugins/forge"
  echo "Installing for OpenCode..."
  mkdir -p "${plugin_dir}"

  ln -sf "${FORGE_DIR}" "${plugin_dir}/forge" 2>/dev/null || {
    rm -rf "${plugin_dir}/skills"
    cp -r "${FORGE_DIR}/skills" "${plugin_dir}/skills"
    cp -r "${FORGE_DIR}/agents" "${plugin_dir}/agents"
    copy_optional_file "${FORGE_DIR}/.opencode/plugins/forge.js" "${plugin_dir}/forge.js"
  }

  echo "  Done: ${plugin_dir}"
  if [[ -x "${FORGE_DIR}/scripts/verify-forge-plugin-install.sh" ]]; then
    echo "  Verify: bash \"${FORGE_DIR}/scripts/verify-forge-plugin-install.sh\" --platform opencode"
  fi
}

uninstall_opencode() {
  local plugin_dir="${HOME}/.opencode/plugins/forge"
  if [ -d "$plugin_dir" ]; then
    rm -rf "$plugin_dir"
    echo "  Removed: ${plugin_dir}"
  fi
}

# ── Gemini CLI ───────────────────────────────────────────────────────────
install_gemini_cli() {
  echo "Installing for Gemini CLI..."
  if command -v gemini >/dev/null 2>&1; then
    gemini extensions link "${FORGE_DIR}" 2>/dev/null && \
      echo "  Done: linked via 'gemini extensions link'" || \
      echo "  Warning: 'gemini extensions link' failed — try manually: gemini extensions link ${FORGE_DIR}"
  else
    # Fallback: manually symlink into ~/.gemini/extensions/
    local ext_dir="${HOME}/.gemini/extensions/forge"
    mkdir -p "$(dirname "$ext_dir")"
    ln -sfn "${FORGE_DIR}" "${ext_dir}"
    echo "  Done: ${ext_dir} (symlinked)"
    echo "  Note: Run 'gemini extensions update forge' after gemini CLI is installed."
  fi
}

uninstall_gemini_cli() {
  if command -v gemini >/dev/null 2>&1; then
    gemini extensions uninstall forge 2>/dev/null || true
  fi
  local ext_dir="${HOME}/.gemini/extensions/forge"
  if [ -L "$ext_dir" ] || [ -d "$ext_dir" ]; then
    rm -rf "$ext_dir"
    echo "  Removed: ${ext_dir}"
  fi
}

# ── Copilot CLI ──────────────────────────────────────────────────────────
install_copilot_cli() {
  echo "Installing for Copilot CLI..."
  echo "  No install needed — session-start hook auto-detects COPILOT_CLI env var."
  echo "  Tool mapping reference: references/copilot-tools.md"
}

uninstall_copilot_cli() {
  echo "  No uninstall needed — Copilot CLI uses project-local hooks"
}

# ── JetBrains AI ─────────────────────────────────────────────────────────
install_jetbrains() {
  echo ""
  echo "JetBrains AI: Manual step required."
  echo "Copy the guidelines template to each project:"
  echo ""
  echo "  mkdir -p <your-project>/.junie"
  echo "  cp ${FORGE_DIR}/templates/junie-guidelines.md <your-project>/.junie/guidelines.md"
  echo ""
}

uninstall_jetbrains() {
  echo "  Manual: Remove .junie/guidelines.md from each project"
}

# ── Main ─────────────────────────────────────────────────────────────────
run_for_platform() {
  local platform="$1"
  local action="${2:-install}"

  case "$platform" in
    claude-code)  ${action}_claude_code ;;
    cursor)       ${action}_cursor ;;
    antigravity)  ${action}_antigravity ;;
    codex)        ${action}_codex ;;
    opencode)     ${action}_opencode ;;
    gemini-cli)   ${action}_gemini_cli ;;
    copilot-cli)  ${action}_copilot_cli ;;
    jetbrains)    ${action}_jetbrains ;;
    *)
      echo "Unknown platform: ${platform}" >&2
      echo "Valid: claude-code, cursor, antigravity, codex, opencode, gemini-cli, copilot-cli, jetbrains" >&2
      exit 1
      ;;
  esac
}

action="install"
$UNINSTALL && action="uninstall"

if [ -n "$TARGET_PLATFORM" ]; then
  # Single platform
  run_for_platform "$TARGET_PLATFORM" "$action"
else
  # Auto-detect and install all
  if $UNINSTALL; then
    echo "Uninstalling from all platforms..."
    for platform in claude-code cursor antigravity codex opencode gemini-cli copilot-cli jetbrains; do
      run_for_platform "$platform" "uninstall"
    done
  else
    echo "Detecting installed platforms..."
    detected=$(detect_platforms)
    echo "Detected: ${detected}"
    echo ""
    # If only JetBrains matched, auto-detect often missed Cursor / Claude (no CLI, never opened app).
    if [[ "${detected}" == "jetbrains" ]]; then
      echo "No Cursor / Claude / Codex / … binaries or marker dirs found."
      echo "If you use Cursor or Claude Code anyway, run explicitly (creates ~/.cursor or cache dirs):"
      echo "  bash scripts/install.sh --platform cursor"
      echo "  bash scripts/install.sh --platform claude-code"
      echo ""
    fi
    for platform in $detected; do
      run_for_platform "$platform" "install"
      echo ""
    done
  fi
fi

echo ""
echo "Forge ${action} complete!"
echo ""
if [ "$action" = "install" ]; then
  echo "Next steps:"
  echo "  1. Restart your IDE to activate hooks"
  echo "  2. Verify: Open a new session and run /forge-status"
  echo "  3. Per-platform guides: docs/platforms/"
fi

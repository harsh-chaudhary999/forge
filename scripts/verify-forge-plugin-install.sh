#!/usr/bin/env bash
# Verify the Forge **merged skills tree** (skills/<name>/SKILL.md) in the Claude Code
# plugin cache has no accidental nested skills/skills/ and that intake-interrogate
# includes design (Q9) markers, plus the .claude/hooks layout and scanner are present.
#
# This branch is Claude-only.
#
# Usage:
#   bash scripts/verify-forge-plugin-install.sh --platform claude-code
#   bash scripts/verify-forge-plugin-install.sh --root /path/to/plugin   # plugin root with skills/
#   bash scripts/verify-forge-plugin-install.sh --all
#
# Exit 0 = OK or skipped (no skills dir); 1 = error.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
FORGE_VERSION="$(node -e "console.log(require('${FORGE_DIR}/package.json').version)" 2>/dev/null || echo "1.1.0")"

verify_merged_skills_root() {
  local root="$1"
  local label="${2:-$root}"

  if [[ ! -d "${root}/skills" ]]; then
    echo "OK (skip ${label}): no ${root}/skills"
    return 0
  fi

  if [[ -d "${root}/skills/skills" ]]; then
    echo "ERROR [${label}]: nested ${root}/skills/skills exists — not shipped by Forge; remove it." >&2
    echo "  Example: rm -rf \"${root}/skills/skills\"" >&2
    return 1
  fi

  local intake="${root}/skills/intake-interrogate/SKILL.md"
  if [[ ! -f "${intake}" ]]; then
    echo "ERROR [${label}]: missing ${intake}" >&2
    return 1
  fi
  if ! grep -q 'design_intake_anchor' "${intake}"; then
    echo "ERROR [${label}]: ${intake} looks stale (no design_intake_anchor). Re-run install from Forge repo." >&2
    return 1
  fi
  if ! grep -q 'single design source of truth' "${intake}"; then
    echo "ERROR [${label}]: ${intake} looks stale (no design source-of-truth prompt)." >&2
    return 1
  fi

  echo "OK [${label}]: ${root}/skills — single tree, intake includes design markers."
  return 0
}

verify_no_nested_copy_dirs() {
  local root="$1"
  local label="${2:-$root}"
  local bad=0
  local dirs=(skills agents commands hooks .claude-plugin)

  for d in "${dirs[@]}"; do
    if [[ -d "${root}/${d}/${d}" ]]; then
      echo "ERROR [${label}]: nested ${root}/${d}/${d} exists — re-run install.sh (copy destination was not replaced cleanly)." >&2
      bad=1
    fi
  done

  [[ "${bad}" -eq 0 ]] && echo "OK [${label}]: no nested copied dirs (skills/skills, commands/commands, hooks/hooks, …)"
  return "${bad}"
}

# Claude Code hooks/hooks.json runs node "${CLAUDE_PLUGIN_ROOT}/.claude/hooks/*.cjs"
verify_claude_plugin_layout() {
  local root="$1"
  local hook="${root}/.claude/hooks/session-start.cjs"
  if [[ ! -f "${hook}" ]]; then
    echo "ERROR [claude-code]: missing ${hook} — install.sh must copy .claude/hooks into the plugin cache. Re-run: bash scripts/install.sh --platform claude-code" >&2
    return 1
  fi
  if [[ ! -L "${root}/.claude/skills" ]] && [[ ! -d "${root}/.claude/skills" ]]; then
    echo "ERROR [claude-code]: missing ${root}/.claude/skills (symlink to ../skills) — re-run install.sh --platform claude-code" >&2
    return 1
  fi
  echo "OK [claude-code]: .claude/hooks + .claude/skills layout present under ${root}"
  return 0
}

# /scan / scan-codebase need tools/forge_scan.py in the merged plugin tree
verify_plugin_tools_scanner() {
  local root="$1"
  local label="${2:-plugin}"
  if [[ ! -f "${root}/tools/forge_scan.py" ]]; then
    echo "ERROR [${label}]: missing ${root}/tools/forge_scan.py — re-run: bash scripts/install.sh --platform ${label}" >&2
    return 1
  fi
  echo "OK [${label}]: ${root}/tools/forge_scan.py present"
  return 0
}

ALL=0
PLATFORM=""
ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all) ALL=1; shift ;;
    --platform)
      PLATFORM="$2"
      shift 2
      ;;
    --root)
      ROOT="$2"
      shift 2
      ;;
    -h|--help)
      sed -n '1,18p' "$0" | tail -n +2
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

verify_claude_install() {
  local cc="$1"
  local ec=0
  verify_merged_skills_root "${cc}" "claude-code" || ec=1
  verify_no_nested_copy_dirs "${cc}" "claude-code" || ec=1
  if [[ -d "${cc}/skills" ]]; then
    verify_claude_plugin_layout "${cc}" || ec=1
    verify_plugin_tools_scanner "${cc}" "claude-code" || ec=1
  fi
  return "${ec}"
}

if [[ "$ALL" -eq 1 ]]; then
  verify_claude_install "${HOME}/.claude/plugins/cache/forge-plugin/forge/${FORGE_VERSION}"
  exit $?
fi

if [[ -n "${ROOT}" ]]; then
  verify_merged_skills_root "${ROOT}" "custom"
  exit $?
fi

case "${PLATFORM}" in
  claude-code)
    verify_claude_install "${HOME}/.claude/plugins/cache/forge-plugin/forge/${FORGE_VERSION}"
    exit $?
    ;;
  "")
    echo "Usage: $0 --platform claude-code | --root DIR | --all" >&2
    exit 1
    ;;
  *)
    echo "Unknown --platform ${PLATFORM} (this branch is Claude-only)" >&2
    exit 1
    ;;
esac

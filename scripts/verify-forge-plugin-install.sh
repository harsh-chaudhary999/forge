#!/usr/bin/env bash
# Verify a Forge **merged skills tree** (skills/<name>/SKILL.md) has no accidental
# nested skills/skills/ and that intake-interrogate includes design (Q9) markers.
#
# Use for any IDE that installs Forge this way: Cursor, Claude Code (plugin cache),
# OpenCode (fallback copy). Antigravity uses per-skill symlinks — see docs.
#
# Usage:
#   bash scripts/verify-forge-plugin-install.sh --platform cursor
#   bash scripts/verify-forge-plugin-install.sh --platform claude-code
#   bash scripts/verify-forge-plugin-install.sh --platform opencode
#   bash scripts/verify-forge-plugin-install.sh --root /path/to/plugin   # plugin root with skills/
#   bash scripts/verify-forge-plugin-install.sh --all
#
# Exit 0 = OK or skipped (no skills dir); 1 = error.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
FORGE_VERSION="$(node -e "console.log(require('${FORGE_DIR}/package.json').version)" 2>/dev/null || echo "1.0.0")"

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

opencode_skills_root() {
  local base="${HOME}/.opencode/plugins/forge"
  if [[ -d "${base}/skills" ]]; then
    echo "${base}"
    return 0
  fi
  if [[ -L "${base}/forge" ]] || [[ -d "${base}/forge" ]]; then
    local target
    target=$(readlink -f "${base}/forge" 2>/dev/null || echo "${base}/forge")
    if [[ -d "${target}/skills" ]]; then
      echo "${target}"
      return 0
    fi
  fi
  echo ""
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
      sed -n '1,20p' "$0" | tail -n +2
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

run_one() {
  local r="$1"
  local lbl="$2"
  verify_merged_skills_root "$r" "$lbl"
  if [[ "${lbl}" == "claude-code" ]] && [[ -d "${r}/skills" ]]; then
    verify_claude_plugin_layout "${r}" || return 1
  fi
  if [[ "${lbl}" == "cursor" || "${lbl}" == "claude-code" ]] && [[ -d "${r}/skills" ]]; then
    verify_plugin_tools_scanner "${r}" "${lbl}" || return 1
  fi
}

if [[ "$ALL" -eq 1 ]]; then
  ec=0
  run_one "${HOME}/.cursor/plugins/local/forge" "cursor" || ec=1
  run_one "${HOME}/.claude/plugins/cache/forge-plugin/forge/${FORGE_VERSION}" "claude-code" || ec=1
  oc=$(opencode_skills_root || true)
  if [[ -n "${oc}" ]]; then
    run_one "${oc}" "opencode" || ec=1
  else
    echo "OK (skip opencode): no merged skills dir under ~/.opencode/plugins/forge"
  fi
  exit "$ec"
fi

if [[ -n "${ROOT}" ]]; then
  verify_merged_skills_root "${ROOT}" "custom"
  exit $?
fi

case "${PLATFORM}" in
  cursor)
    cr="${HOME}/.cursor/plugins/local/forge"
    verify_merged_skills_root "${cr}" "cursor"
    if [[ -d "${cr}/skills" ]]; then
      verify_plugin_tools_scanner "${cr}" "cursor" || exit 1
    fi
    ;;
  claude-code)
    cc="${HOME}/.claude/plugins/cache/forge-plugin/forge/${FORGE_VERSION}"
    verify_merged_skills_root "${cc}" "claude-code"
    if [[ -d "${cc}/skills" ]]; then
      verify_claude_plugin_layout "${cc}" || exit 1
      verify_plugin_tools_scanner "${cc}" "claude-code" || exit 1
    fi
    ;;
  opencode)
    oc=$(opencode_skills_root)
    if [[ -z "${oc}" ]]; then
      echo "OK (skip opencode): no merged skills tree found (symlink-only layout is OK)."
      exit 0
    fi
    verify_merged_skills_root "${oc}" "opencode"
    ;;
  "")
    echo "Usage: $0 --platform cursor|claude-code|opencode | --root DIR | --all" >&2
    exit 1
    ;;
  *)
    echo "Unknown --platform ${PLATFORM}" >&2
    exit 1
    ;;
esac

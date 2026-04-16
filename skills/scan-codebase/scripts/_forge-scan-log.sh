#!/usr/bin/env bash
# Shared exclusive logging for scan-codebase scripts.
#
# Agents: filter agent/tool output with:
#   grep '^FORGE_SCAN|'   # all scan script diagnostics
#   grep '^FORGE_SCAN|.*|ERROR|'   # failures only
#
# Line format (pipe-separated, one line per event):
#   FORGE_SCAN|<script_id>|<utc_iso>|LEVEL|<message>
#
# Source from the same directory as the caller:
#   _fs_scripts=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
#   # shellcheck source=_forge-scan-log.sh
#   . "$_fs_scripts/_forge-scan-log.sh"

FORGE_SCAN_MAGIC='FORGE_SCAN'

_forge_scan_emit() {
  local level="$1"
  shift
  local ts
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf '%s' 'time-unavailable')
  printf '%s|%s|%s|%s|%s\n' "$FORGE_SCAN_MAGIC" "${FORGE_SCAN_SCRIPT_ID:-unknown}" "$ts" "$level" "$*"
}

# Sets FORGE_SCAN_SCRIPT_ID and logs run start (arguments / context).
forge_scan_log_start() {
  FORGE_SCAN_SCRIPT_ID="$1"
  shift
  _forge_scan_emit START "$*"
}

forge_scan_log_step() { _forge_scan_emit STEP "$*"; }
forge_scan_log_stat() { _forge_scan_emit STAT "$*"; }
forge_scan_log_warn() { _forge_scan_emit WARN "$*"; }
forge_scan_log_error() { _forge_scan_emit ERROR "$*"; }

forge_scan_log_done() {
  _forge_scan_emit DONE "$*"
}

forge_scan_log_die() {
  local msg="$1"
  local code="${2:-1}"
  _forge_scan_emit ERROR "$msg exit_code=$code"
  exit "$code"
}

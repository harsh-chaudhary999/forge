#!/usr/bin/env bash
# Forge scan-codebase: Cleanup — Remove all ${FORGE_SCAN_TMP}/forge_scan_* temp files
#
# Usage: bash /path/to/forge/skills/scan-codebase/scripts/cleanup.sh
#
# Run at end of every scan to prevent stale data from contaminating next run.
#
# Must run with bash: `bash cleanup.sh`

if [ -z "${BASH_VERSION:-}" ]; then
  printf '%s: requires bash. Use: bash "%s"\n' "${0##*/}" "$0" >&2
  exit 127
fi

set -euo pipefail

_fs_scripts=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC1091
. "$_fs_scripts/_forge-scan-log.sh"
# shellcheck disable=SC1091
. "$_fs_scripts/_forge-scan-paths.sh"

forge_scan_log_start cleanup "action=remove_glob pattern=${FORGE_SCAN_TMP}/forge_scan_*.txt"

BEFORE=$(ls "${FORGE_SCAN_TMP}"/forge_scan_*.txt 2>/dev/null | wc -l)
rm -f "${FORGE_SCAN_TMP}"/forge_scan_*.txt
echo "Cleanup: removed $BEFORE ${FORGE_SCAN_TMP}/forge_scan_*.txt files"
forge_scan_log_done "files_removed=$BEFORE"

#!/usr/bin/env bash
# Forge scan-codebase: Cleanup — Remove all /tmp/forge_scan_* temp files
#
# Usage: bash /path/to/forge/skills/scan-codebase/scripts/cleanup.sh
#
# Run at end of every scan to prevent stale data from contaminating next run.

set -euo pipefail

_fs_scripts=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC1091
. "$_fs_scripts/_forge-scan-log.sh"

forge_scan_log_start cleanup "action=remove_glob pattern=/tmp/forge_scan_*.txt"

BEFORE=$(ls /tmp/forge_scan_*.txt 2>/dev/null | wc -l)
rm -f /tmp/forge_scan_*.txt
echo "Cleanup: removed $BEFORE /tmp/forge_scan_*.txt files"
forge_scan_log_done "files_removed=$BEFORE"

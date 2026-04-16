#!/usr/bin/env bash
# Forge scan-codebase: Cleanup — Remove all /tmp/forge_scan_* temp files
#
# Usage: bash /path/to/forge/skills/scan-codebase/scripts/cleanup.sh
#
# Run at end of every scan to prevent stale data from contaminating next run.

set -euo pipefail

BEFORE=$(ls /tmp/forge_scan_*.txt 2>/dev/null | wc -l)
rm -f /tmp/forge_scan_*.txt
echo "Cleanup: removed $BEFORE /tmp/forge_scan_*.txt files"

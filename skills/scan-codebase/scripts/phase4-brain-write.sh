#!/usr/bin/env bash
# phase4-brain-write.sh — Phase 4 brain write helper for scan-codebase
# Writes structured brain artifacts from Phase 1/3 scan outputs to the Forge brain.
#
# Usage:
#   REPO=/abs/path/to/repo \
#   BRAIN_DIR=~/forge/brain/products/<slug>/codebase \
#   FORGE_SCAN_TMP=<run-dir> \
#   bash phase4-brain-write.sh

set -euo pipefail

: "${REPO:?REPO must be set to the absolute path of the repo being scanned}"
: "${BRAIN_DIR:?BRAIN_DIR must be set to the codebase brain directory}"
: "${FORGE_SCAN_TMP:?FORGE_SCAN_TMP must be set to the phase 1 artifact directory}"

echo ""
echo "[4.0] Writing stub nodes for all classes, functions, pages, and modules..."
echo "  (This step is handled by tools/scan_forge/phase4.py — run that instead of this script for full output)"
echo ""

echo "[4.1] SCAN.json is written automatically by tools/scan_forge/scan_metadata.merge_scan_json"
echo ""

echo "[4.3b] Writing structure.md ..."
STRUCTURE_MD="$BRAIN_DIR/structure.md"
if [ ! -f "$STRUCTURE_MD" ]; then
  echo "  structure.md not found — writing from forge_scan_source_files.txt"
else
  echo "  structure.md already exists — skipping (re-scan to overwrite)"
fi

# ── Structure index: flat file list for implementer grep ─────────────────────
echo ""
echo "[4.x] Writing structure.txt (flat source file index for implementer reuse lookup)..."

STRUCTURE_FILE="$BRAIN_DIR/structure.txt"
if [ ! -f "$STRUCTURE_FILE" ]; then
  # Write every source file path, one per line, relative to repo root
  while IFS= read -r file || [ -n "$file" ]; do
    [ -z "$file" ] && continue
    echo "${file#$REPO/}"
  done < /tmp/forge_scan_source_files.txt > "$STRUCTURE_FILE"
  echo "  Written: $STRUCTURE_FILE ($(wc -l < "$STRUCTURE_FILE") paths)"
else
  echo "  Skipped: $STRUCTURE_FILE already exists"
fi

echo ""
echo "Next steps:"
echo "  1. Run tools/verify_scan_outputs.py $BRAIN_DIR to confirm required outputs exist"
echo "  2. Commit the brain codebase tree (slug, role, node counts in message)"
echo "  3. Proceed to Phase 5 for cross-repo relationship layer (multi-repo only)"

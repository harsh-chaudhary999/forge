#!/usr/bin/env bash
# Forge scan-codebase: Phase 3.4-3.5 — Test name extraction + API route extraction
#
# Usage: bash /path/to/forge/skills/scan-codebase/scripts/phase35-extract.sh <REPO_PATH>
#
# Prerequisite: phase1-inventory.sh must have been run first (needs forge_scan_test_files.txt)
#
# Writes to /tmp:
#   forge_scan_test_names.txt   test name strings (describe/it/test/func Test/def test_)
#   forge_scan_api_routes.txt   API route decorators and router patterns

set -euo pipefail

REPO="${1:?Usage: $0 <repo-path>}"

echo "════════════════════════════════════════════════════════"
echo "FORGE SCAN — Phase 3.4-3.5: Test Names + API Routes"
echo "Repo: $REPO"
echo "════════════════════════════════════════════════════════"

# ── 3.4: Test name extraction ────────────────────────────────────────────────
echo ""
echo "[3.4] Extracting test names..."

if [ ! -f /tmp/forge_scan_test_files.txt ]; then
  echo "  ERROR: /tmp/forge_scan_test_files.txt not found. Run phase1-inventory.sh first."
  exit 1
fi

while IFS= read -r file; do
  echo "=== $file ==="
  grep -n \
    "it(\|test(\|describe(\|def test_\|func Test\|#\[test\]\|@Test\|should\b" \
    "$file" 2>/dev/null | head -30
done < /tmp/forge_scan_test_files.txt > /tmp/forge_scan_test_names.txt

echo "  Test names extracted from $(wc -l < /tmp/forge_scan_test_files.txt) test files"
echo "  Edge case strings found: $(grep -c "should\|error\|fail\|invalid\|missing\|expired\|exceed\|limit\|timeout" /tmp/forge_scan_test_names.txt 2>/dev/null || echo 0)"

# ── 3.5: API route extraction ────────────────────────────────────────────────
echo ""
echo "[3.5] Extracting API routes..."

grep -rn \
  "@Get\|@Post\|@Put\|@Delete\|@Patch\
\|@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping\|@PatchMapping\|@RequestMapping\
\|router\.get\|router\.post\|router\.put\|router\.delete\|router\.patch\
\|app\.get\|app\.post\|app\.put\|app\.delete\|app\.patch\
\|r\.GET\|r\.POST\|r\.PUT\|r\.DELETE\|r\.PATCH\
\|@app\.route\|@router\.\
\|mux\.HandleFunc\|http\.HandleFunc\|e\.GET\|e\.POST\|g\.GET\|g\.POST" \
  "$REPO" \
  --include="*.ts" --include="*.py" --include="*.go" \
  --include="*.java" --include="*.kt" \
  | grep -v node_modules | grep -v dist | grep -v test | grep -v spec \
  2>/dev/null > /tmp/forge_scan_api_routes.txt || true

echo "  API routes found: $(wc -l < /tmp/forge_scan_api_routes.txt)"
echo ""
echo "  Route breakdown by method:"
echo "    GET:    $(grep -c "@Get\b\|router\.get\|app\.get\|r\.GET\|e\.GET\|g\.GET\|@GetMapping" /tmp/forge_scan_api_routes.txt 2>/dev/null || echo 0)"
echo "    POST:   $(grep -c "@Post\b\|router\.post\|app\.post\|r\.POST\|e\.POST\|g\.POST\|@PostMapping" /tmp/forge_scan_api_routes.txt 2>/dev/null || echo 0)"
echo "    PUT:    $(grep -c "@Put\b\|router\.put\|app\.put\|r\.PUT\|@PutMapping" /tmp/forge_scan_api_routes.txt 2>/dev/null || echo 0)"
echo "    DELETE: $(grep -c "@Delete\b\|router\.delete\|app\.delete\|r\.DELETE\|@DeleteMapping" /tmp/forge_scan_api_routes.txt 2>/dev/null || echo 0)"
echo "    PATCH:  $(grep -c "@Patch\b\|router\.patch\|app\.patch\|r\.PATCH\|@PatchMapping" /tmp/forge_scan_api_routes.txt 2>/dev/null || echo 0)"

echo ""
echo "[3.5] Routes sample (first 20):"
head -20 /tmp/forge_scan_api_routes.txt | sed 's/^/  /'

echo ""
echo "Phase 3.4-3.5 complete."
echo "  /tmp/forge_scan_test_names.txt — use for gotchas.md"
echo "  /tmp/forge_scan_api_routes.txt — use for api-surface.md and Phase 5.5 correlation"

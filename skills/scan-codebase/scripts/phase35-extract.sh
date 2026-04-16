#!/usr/bin/env bash
# Forge scan-codebase: Phase 3.4-3.5 — Test name extraction + API route extraction
#
# Usage: bash .../phase35-extract.sh <REPO_PATH> [append]
#
# Multi-repo: run once per repo. First repo: no second arg (truncates API routes file).
# Later repos: pass "append" so routes accumulate in /tmp/forge_scan_api_routes.txt.
# If you always use "append" without truncating first, the file grows unbounded — start
# with a fresh run for the first repo, or run `: > /tmp/forge_scan_api_routes.txt` once.
#
# Prerequisite: phase1-inventory.sh must have been run first (needs forge_scan_test_files.txt)
#
# Writes to /tmp:
#   forge_scan_test_names.txt   test name strings (describe/it/test/func Test/def test_)
#   forge_scan_api_routes.txt   API route decorators and router patterns

set -euo pipefail

_fs_scripts=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC1091
. "$_fs_scripts/_forge-scan-log.sh"

REPO="${1:?Usage: $0 <repo-path> [append]}"
APPEND_ROUTES="${2:-}"
_repo_slug=$(basename "$REPO")
forge_scan_log_start phase35-extract "repo=$REPO append_routes=${APPEND_ROUTES:-no}"

echo "════════════════════════════════════════════════════════"
echo "FORGE SCAN — Phase 3.4-3.5: Test Names + API Routes"
echo "Repo: $REPO"
echo "════════════════════════════════════════════════════════"

# ── 3.4: Test name extraction ────────────────────────────────────────────────
echo ""
echo "[3.4] Extracting test names..."

if [ ! -f /tmp/forge_scan_test_files.txt ]; then
  echo "  ERROR: /tmp/forge_scan_test_files.txt not found. Run phase1-inventory.sh first."
  forge_scan_log_die "missing_prerequisite path=/tmp/forge_scan_test_files.txt hint=run_phase1-inventory.sh_first" 1
fi

while IFS= read -r file; do
  echo "=== $file ==="
  grep -n \
    "it(\|test(\|describe(\|def test_\|func Test\|#\[test\]\|@Test\|should\b" \
    "$file" 2>/dev/null | head -30 || true
done < /tmp/forge_scan_test_files.txt > /tmp/forge_scan_test_names.txt

echo "  Test names extracted from $(wc -l < /tmp/forge_scan_test_files.txt) test files"
_edge_case_hits=$(grep -c "should\|error\|fail\|invalid\|missing\|expired\|exceed\|limit\|timeout" /tmp/forge_scan_test_names.txt 2>/dev/null || true)
echo "  Edge case strings found: ${_edge_case_hits:-0}"
forge_scan_log_stat "phase=3.4 test_files=$(wc -l < /tmp/forge_scan_test_files.txt) edge_case_hits=${_edge_case_hits:-0}"

# ── 3.5: API route extraction ────────────────────────────────────────────────
echo ""
echo "[3.5] Extracting API routes..."

if [ "$APPEND_ROUTES" = "append" ]; then
  forge_scan_log_step "phase=3.5 appending_api_routes repo=$_repo_slug"
else
  : > /tmp/forge_scan_api_routes.txt
  forge_scan_log_step "phase=3.5 reset_api_routes_file repo=$_repo_slug"
fi

grep -rn \
  "@Get\|@Post\|@Put\|@Delete\|@Patch\
\|@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping\|@PatchMapping\|@RequestMapping\
\|@Controller\|@Route\
\|router\.get\|router\.post\|router\.put\|router\.delete\|router\.patch\
\|app\.get\|app\.post\|app\.put\|app\.delete\|app\.patch\
\|r\.GET\|r\.POST\|r\.PUT\|r\.DELETE\|r\.PATCH\
\|@app\.route\|@router\.\
\|mux\.HandleFunc\|http\.HandleFunc\|e\.GET\|e\.POST\|g\.GET\|g\.POST" \
  "$REPO" \
  --include="*.ts" --include="*.py" --include="*.go" \
  --include="*.java" --include="*.kt" --include="*.js" --include="*.jsx" \
  | grep -v node_modules | grep -v dist \
  | grep -Ev '/(test|tests|__tests__|e2e|spec)/|\.test\.|\.spec\.|/testing/' \
  2>/dev/null | sed "s|^|${_repo_slug}\t|" >> /tmp/forge_scan_api_routes.txt || true

echo "  API routes found: $(wc -l < /tmp/forge_scan_api_routes.txt)"
echo ""
echo "  Route breakdown by method:"
_get=$(grep -c "@Get\b\|router\.get\|app\.get\|r\.GET\|e\.GET\|g\.GET\|@GetMapping" /tmp/forge_scan_api_routes.txt 2>/dev/null || true)
_post=$(grep -c "@Post\b\|router\.post\|app\.post\|r\.POST\|e\.POST\|g\.POST\|@PostMapping" /tmp/forge_scan_api_routes.txt 2>/dev/null || true)
_put=$(grep -c "@Put\b\|router\.put\|app\.put\|r\.PUT\|@PutMapping" /tmp/forge_scan_api_routes.txt 2>/dev/null || true)
_delete=$(grep -c "@Delete\b\|router\.delete\|app\.delete\|r\.DELETE\|@DeleteMapping" /tmp/forge_scan_api_routes.txt 2>/dev/null || true)
_patch=$(grep -c "@Patch\b\|router\.patch\|app\.patch\|r\.PATCH\|@PatchMapping" /tmp/forge_scan_api_routes.txt 2>/dev/null || true)
echo "    GET:    ${_get:-0}"
echo "    POST:   ${_post:-0}"
echo "    PUT:    ${_put:-0}"
echo "    DELETE: ${_delete:-0}"
echo "    PATCH:  ${_patch:-0}"
forge_scan_log_stat "phase=3.5 api_routes=$(wc -l < /tmp/forge_scan_api_routes.txt) get=${_get:-0} post=${_post:-0} put=${_put:-0} delete=${_delete:-0} patch=${_patch:-0}"

echo ""
echo "[3.5] Routes sample (first 20):"
head -20 /tmp/forge_scan_api_routes.txt | sed 's/^/  /'

echo ""
echo "Phase 3.4-3.5 complete."
echo "  /tmp/forge_scan_test_names.txt — use for gotchas.md"
echo "  /tmp/forge_scan_api_routes.txt — use for api-surface.md and Phase 5.5 correlation"
forge_scan_log_done "test_names_bytes=$(wc -c < /tmp/forge_scan_test_names.txt 2>/dev/null || echo 0) api_routes=$(wc -l < /tmp/forge_scan_api_routes.txt)"

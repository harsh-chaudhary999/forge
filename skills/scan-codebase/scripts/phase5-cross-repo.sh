#!/usr/bin/env bash
# Forge scan-codebase: Phase 5.1-5.4 — Cross-repo relationship scanning
#
# Usage: bash /path/to/forge/skills/scan-codebase/scripts/phase5-cross-repo.sh <repo1> [repo2] [repo3] ...
#
# Prerequisite: phase35-extract.sh must have been run on the backend repo
#               (needs forge_scan_api_routes.txt for Phase 5.5 correlation)
#
# Writes to /tmp:
#   forge_scan_js_calls.txt         TS/JS HTTP call sites
#   forge_scan_java_calls.txt       Java HTTP call sites
#   forge_scan_kotlin_calls.txt     Kotlin HTTP call sites
#   forge_scan_python_calls.txt     Python HTTP call sites
#   forge_scan_go_calls.txt         Go HTTP call sites
#   forge_scan_dart_calls.txt       Dart HTTP call sites
#   forge_scan_all_callsites.txt    all call sites combined
#   forge_scan_url_strings.txt      extracted URL path strings
#   forge_scan_fe_urls.txt          unique sorted URL paths
#   forge_scan_dynamic_urls.txt     template literal / variable URLs (for manual review)
#   forge_scan_all_types.txt        all exported types from all repos (for shared type detection)
#   forge_scan_all_env_vars.txt     all env var references across repos

set -euo pipefail

_fs_scripts=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC1091
. "$_fs_scripts/_forge-scan-log.sh"

FORGE_SCAN_SCRIPT_ID=phase5-cross-repo
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <repo1> [repo2] [repo3] ..."
  forge_scan_log_error "bad_usage need_at_least_one_repo_path"
  exit 1
fi

REPOS=("$@")
forge_scan_log_start phase5-cross-repo "repo_count=${#REPOS[@]} repos=$(printf '%s;' "${REPOS[@]}")"

echo "════════════════════════════════════════════════════════"
echo "FORGE SCAN — Phase 5: Cross-Repo Relationship Scanning"
echo "Repos: ${REPOS[*]}"
echo "════════════════════════════════════════════════════════"

# Clear output files
> /tmp/forge_scan_js_calls.txt
> /tmp/forge_scan_java_calls.txt
> /tmp/forge_scan_kotlin_calls.txt
> /tmp/forge_scan_python_calls.txt
> /tmp/forge_scan_go_calls.txt
> /tmp/forge_scan_dart_calls.txt
> /tmp/forge_scan_all_types.txt
> /tmp/forge_scan_all_env_vars.txt
> /tmp/forge_scan_dynamic_urls.txt

# ── 5.1: API call detection ───────────────────────────────────────────────────
echo ""
echo "[5.1] Scanning API call sites across all repos..."

for repo in "${REPOS[@]}"; do
  repo_name=$(basename "$repo")
  echo "  Scanning: $repo_name"

  # TypeScript / JavaScript
  grep -rn \
    "fetch(\|axios\.\|got\.\|superagent\.\|ky\.\|needle\." \
    "$repo" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
    | grep -v node_modules | grep -v test | grep -v spec \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|" \
    2>/dev/null >> /tmp/forge_scan_js_calls.txt || true

  # Java (RestTemplate, WebClient, OkHttp, HttpClient, Feign)
  grep -rn \
    "restTemplate\.\|webClient\.\|HttpClient\.\|OkHttpClient\.\|\.exchange(\|\.getForObject(\|\.postForObject(\|@FeignClient" \
    "$repo" --include="*.java" \
    | grep -v test | grep -v Test \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|" \
    2>/dev/null >> /tmp/forge_scan_java_calls.txt || true

  # Feign client annotations
  grep -rn \
    "@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping\|@PatchMapping\|@RequestMapping" \
    "$repo" --include="*.java" \
    | grep -i "feign\|client\|Client" \
    | sed "s|$repo/||" | sed "s|^|$repo_name/feign\t|" \
    2>/dev/null >> /tmp/forge_scan_java_calls.txt || true

  # Kotlin (Ktor, Fuel, Retrofit)
  grep -rn \
    "client\.get(\|client\.post(\|client\.put(\|client\.delete(\|Fuel\.get(\|Fuel\.post(\|\.get<\|\.post<" \
    "$repo" --include="*.kt" \
    | grep -v test | grep -v Test \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|" \
    2>/dev/null >> /tmp/forge_scan_kotlin_calls.txt || true

  # Retrofit annotations on Kotlin interfaces
  grep -rn \
    "@GET(\|@POST(\|@PUT(\|@DELETE(\|@PATCH(" \
    "$repo" --include="*.kt" \
    | grep -v test \
    | sed "s|$repo/||" | sed "s|^|$repo_name/retrofit\t|" \
    2>/dev/null >> /tmp/forge_scan_kotlin_calls.txt || true

  # Python (requests, httpx, aiohttp)
  grep -rn \
    "requests\.get(\|requests\.post(\|requests\.put(\|requests\.delete(\|httpx\.get(\|httpx\.post(\|aiohttp\." \
    "$repo" --include="*.py" \
    | grep -v test | grep -v "_test" \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|" \
    2>/dev/null >> /tmp/forge_scan_python_calls.txt || true

  # Go (net/http, resty)
  grep -rn \
    "http\.Get(\|http\.Post(\|http\.NewRequest(\|resty\.\|client\.R()\.Get(" \
    "$repo" --include="*.go" \
    | grep -v "_test.go" \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|" \
    2>/dev/null >> /tmp/forge_scan_go_calls.txt || true

  # Dart / Flutter (Dio, http package)
  grep -rn \
    "dio\.get(\|dio\.post(\|dio\.put(\|dio\.delete(\|http\.get(\|http\.post(" \
    "$repo" --include="*.dart" \
    | grep -v test \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|" \
    2>/dev/null >> /tmp/forge_scan_dart_calls.txt || true
done

cat \
  /tmp/forge_scan_js_calls.txt \
  /tmp/forge_scan_java_calls.txt \
  /tmp/forge_scan_kotlin_calls.txt \
  /tmp/forge_scan_python_calls.txt \
  /tmp/forge_scan_go_calls.txt \
  /tmp/forge_scan_dart_calls.txt \
  > /tmp/forge_scan_all_callsites.txt

echo "  Total call sites: $(wc -l < /tmp/forge_scan_all_callsites.txt)"
echo "    TS/JS: $(wc -l < /tmp/forge_scan_js_calls.txt) | Java: $(wc -l < /tmp/forge_scan_java_calls.txt) | Kotlin: $(wc -l < /tmp/forge_scan_kotlin_calls.txt)"
echo "    Python: $(wc -l < /tmp/forge_scan_python_calls.txt) | Go: $(wc -l < /tmp/forge_scan_go_calls.txt) | Dart: $(wc -l < /tmp/forge_scan_dart_calls.txt)"
forge_scan_log_stat "phase=5.1 total_callsites=$(wc -l < /tmp/forge_scan_all_callsites.txt) js=$(wc -l < /tmp/forge_scan_js_calls.txt) java=$(wc -l < /tmp/forge_scan_java_calls.txt) kotlin=$(wc -l < /tmp/forge_scan_kotlin_calls.txt) python=$(wc -l < /tmp/forge_scan_python_calls.txt) go=$(wc -l < /tmp/forge_scan_go_calls.txt) dart=$(wc -l < /tmp/forge_scan_dart_calls.txt)"

# ── 5.2: Shared type detection ────────────────────────────────────────────────
echo ""
echo "[5.2] Scanning exported types for shared type detection..."

for repo in "${REPOS[@]}"; do
  grep -rhn \
    "^export interface \|^export type \|^export class \|^type \|^interface " \
    "$repo" --include="*.ts" \
    | sed 's/^[0-9]*://' \
    | grep -v node_modules \
    2>/dev/null >> /tmp/forge_scan_all_types.txt || true
done

echo "  Total type declarations: $(wc -l < /tmp/forge_scan_all_types.txt)"
echo "  Types appearing in 2+ repos (potential shared contracts):"
sort /tmp/forge_scan_all_types.txt | uniq -d | sed 's/^/    /'
_dup_type_lines=$(sort /tmp/forge_scan_all_types.txt | uniq -d | wc -l)
forge_scan_log_stat "phase=5.2 type_declarations=$(wc -l < /tmp/forge_scan_all_types.txt) duplicate_type_lines=${_dup_type_lines:-0}"

# ── 5.3: Environment variable cross-reference ─────────────────────────────────
echo ""
echo "[5.3] Scanning environment variable usage across repos..."

for repo in "${REPOS[@]}"; do
  repo_name=$(basename "$repo")
  grep -rn \
    "process\.env\.\|os\.environ\.\|os\.Getenv\|System\.getenv\|dotenv\|env\.\|Env\." \
    "$repo" \
    --include="*.ts" --include="*.js" --include="*.py" \
    --include="*.go" --include="*.java" --include="*.kt" \
    | grep -v node_modules | grep -v test \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|" \
    2>/dev/null >> /tmp/forge_scan_all_env_vars.txt || true
done

echo "  Env var references: $(wc -l < /tmp/forge_scan_all_env_vars.txt)"
echo "  Distinct variable names:"
{ grep -oE "process\.env\.[A-Z_]+" /tmp/forge_scan_all_env_vars.txt 2>/dev/null || true; } \
  | sed 's/process\.env\.//' | sort | uniq -c | sort -rn | sed 's/^/    /'
_process_env_names=$( { grep -oE "process\.env\.[A-Z_]+" /tmp/forge_scan_all_env_vars.txt 2>/dev/null || true; } | sort -u | wc -l)
forge_scan_log_stat "phase=5.3 env_var_lines=$(wc -l < /tmp/forge_scan_all_env_vars.txt) distinct_process_env_keys=${_process_env_names:-0}"

# ── 5.4: Event/message bus cross-reference ────────────────────────────────────
echo ""
echo "[5.4] Scanning event/message bus producers and consumers..."

echo "  Producers:"
for repo in "${REPOS[@]}"; do
  repo_name=$(basename "$repo")
  grep -rn \
    "publish(\|produce(\|emit(\|sendMessage\|kafkaProducer\|channel\.send\|rabbitMQ\.publish\|\.send(" \
    "$repo" \
    --include="*.ts" --include="*.py" --include="*.go" --include="*.java" --include="*.kt" \
    | grep -v node_modules | grep -v test \
    | sed "s|$repo/||" | sed "s|^|    $repo_name: |" \
    2>/dev/null || true
done

echo "  Consumers:"
for repo in "${REPOS[@]}"; do
  repo_name=$(basename "$repo")
  grep -rn \
    "subscribe(\|consume(\|\.on(\|kafkaConsumer\|channel\.receive\|rabbitMQ\.consume\|@KafkaListener\|\.listen(" \
    "$repo" \
    --include="*.ts" --include="*.py" --include="*.go" --include="*.java" --include="*.kt" \
    | grep -v node_modules | grep -v test \
    | sed "s|$repo/||" | sed "s|^|    $repo_name: |" \
    2>/dev/null || true
done

forge_scan_log_step "phase=5.4 producer_consumer_grep_complete (see_stdout_above_for_hits)"

# ── 5.5 prep: Extract URL strings from call sites ────────────────────────────
echo ""
echo "[5.5 prep] Extracting URL path strings from call sites..."

# TS/JS string literal URLs
grep -oE "(fetch|axios\.[a-z]+|got\.[a-z]+|ky\.[a-z]+)\(['\`]([/][^'\`\"?# ]+)" \
  /tmp/forge_scan_js_calls.txt \
  | grep -oE "['\`][/][^'\`\"?# ]+" | tr -d "'\`\"" \
  2>/dev/null > /tmp/forge_scan_url_strings.txt || true

# Java URL literals
grep -oE '"(/[^"?# ]+)"' /tmp/forge_scan_java_calls.txt \
  | tr -d '"' \
  2>/dev/null >> /tmp/forge_scan_url_strings.txt || true

# Feign/Retrofit mapping annotations
grep -oE '@[A-Z][a-z]+Mapping\("([^"]+)"' /tmp/forge_scan_kotlin_calls.txt \
  | grep -oE '"[^"]+"' | tr -d '"' \
  2>/dev/null >> /tmp/forge_scan_url_strings.txt || true

# Python requests string literals
grep -oE "(requests|httpx)\.[a-z]+\(['\"]([/][^'\"?# ]+)" \
  /tmp/forge_scan_python_calls.txt \
  | grep -oE "['\"][/][^'\"?# ]+" | tr -d "'\"" \
  2>/dev/null >> /tmp/forge_scan_url_strings.txt || true

sort -u /tmp/forge_scan_url_strings.txt > /tmp/forge_scan_fe_urls.txt
echo "  Unique URL paths extracted: $(wc -l < /tmp/forge_scan_fe_urls.txt)"

# Dynamic URLs (template literals / variable concatenation) — flag for manual review
for repo in "${REPOS[@]}"; do
  repo_name=$(basename "$repo")
  # Template literals: fetch(`${BASE_URL}/path`)
  grep -rn \
    "fetch(\`\${\\|axios\.[a-z]*(\`\${\|got\.[a-z]*(\`\${\|requests\.[a-z]*(f\"\|httpx\.[a-z]*(f\"" \
    "$repo" \
    --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" \
    | grep -v node_modules | grep -v test | grep -v spec \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|" \
    2>/dev/null >> /tmp/forge_scan_dynamic_urls.txt || true

  # Variable concatenation
  grep -rn \
    "baseURL\s*+\|API_BASE_URL\s*+\|API_URL\s*+\|BASE_URL\s*+" \
    "$repo" \
    --include="*.ts" --include="*.tsx" --include="*.js" \
    | grep -v node_modules | grep -v test \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|" \
    2>/dev/null >> /tmp/forge_scan_dynamic_urls.txt || true
done

if [ -s /tmp/forge_scan_dynamic_urls.txt ]; then
  echo ""
  echo "  ⚠  Dynamic URLs detected (template literals / variable concatenation):"
  echo "     $(wc -l < /tmp/forge_scan_dynamic_urls.txt) call sites — NOT extractable by grep"
  echo "     Document in cross-repo.md under '## Dynamic URL Call Sites (Manual Review Required)'"
  forge_scan_log_warn "phase=5.5-prep dynamic_url_lines=$(wc -l < /tmp/forge_scan_dynamic_urls.txt) manual_review_required=true"
fi

echo ""
echo "Phase 5.1-5.5 prep complete."
echo "  All call sites:  /tmp/forge_scan_all_callsites.txt"
echo "  URL strings:     /tmp/forge_scan_fe_urls.txt"
echo "  Dynamic URLs:    /tmp/forge_scan_dynamic_urls.txt  (manual review)"
echo "  Shared types:    /tmp/forge_scan_all_types.txt"
echo ""
echo "Next: Phase 5.5 Steps 3-6 — join URL strings against backend routes"
echo "      (model-side work: /tmp/forge_scan_fe_urls.txt × /tmp/forge_scan_api_routes.txt)"
forge_scan_log_done "callsites=$(wc -l < /tmp/forge_scan_all_callsites.txt) fe_urls=$(wc -l < /tmp/forge_scan_fe_urls.txt) dynamic_urls=$(wc -l < /tmp/forge_scan_dynamic_urls.txt) env_lines=$(wc -l < /tmp/forge_scan_all_env_vars.txt)"

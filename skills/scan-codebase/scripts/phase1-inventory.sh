#!/usr/bin/env bash
# Forge scan-codebase: Phase 1 — Full structural inventory (zero tokens)
#
# Usage: bash /path/to/forge/skills/scan-codebase/scripts/phase1-inventory.sh <REPO_PATH>
#
# Runs Phases 1.1 – 1.6: file inventory, monorepo detection, import graph,
# hub scoring, language fingerprinting, and full symbol/type/method/function/UI
# inventory across all supported languages.
#
# Writes to /tmp:
#   forge_scan_source_files.txt     all source files (excl. test/generated/vendor)
#   forge_scan_test_files.txt       test files
#   forge_scan_imports.txt          import lines per source file
#   forge_scan_hub_scores.txt       incoming-reference count per file
#   forge_scan_tier1.txt            files with 5+ incoming refs (Tier 1 hubs)
#   forge_scan_tier2.txt            files with 3-4 incoming refs (Tier 2 hubs)
#   forge_scan_types_{java,kotlin,go,ts,python,dart,rust}.txt  per-language types
#   forge_scan_methods_{java,kotlin,go,ts,python,dart,rust}.txt per-language methods
#   forge_scan_functions_{go,ts,python}.txt  per-language exported standalone funcs
#   forge_scan_annotations_{java,kotlin,python}.txt  per-language annotations/decorators
#   forge_scan_decorators_ts.txt    NestJS/TypeORM/class-validator decorators
#   forge_scan_html_files.txt       raw HTML files
#   forge_scan_vue_files.txt        Vue SFCs
#   forge_scan_svelte_files.txt     Svelte components
#   forge_scan_angular_templates.txt  Angular component templates
#   forge_scan_html_forms.txt       form elements across all template types
#   forge_scan_html_ids.txt         id= and data-* attributes
#   forge_scan_types_all.txt        master type inventory (→ classes/)
#   forge_scan_methods_all.txt      master method inventory (→ methods/)
#   forge_scan_functions_all.txt    master function inventory (→ functions/)
#   forge_scan_ui_all.txt           master UI file inventory (→ pages/)

set -euo pipefail

_fs_scripts=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC1091
. "$_fs_scripts/_forge-scan-log.sh"

REPO="${1:?Usage: $0 <repo-path>}"
forge_scan_log_start phase1-inventory "repo=$REPO"

echo "════════════════════════════════════════════════════════"
echo "FORGE SCAN — Phase 1: Structural Inventory"
echo "Repo: $REPO"
echo "════════════════════════════════════════════════════════"
echo ""

# ── 1.1: File inventory ─────────────────────────────────────────────────────

SUBMODULE_PATHS=$(git -C "$REPO" submodule --quiet foreach 'echo $displaypath' 2>/dev/null || true)
SUBMODULE_EXCLUDES=""
for sm in $SUBMODULE_PATHS; do
  SUBMODULE_EXCLUDES="$SUBMODULE_EXCLUDES | grep -v \"$sm/\""
done

find "$REPO" -type f \( \
  -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \
  -o -name "*.py" -o -name "*.go" -o -name "*.java" -o -name "*.kt" \
  -o -name "*.rs" -o -name "*.rb" -o -name "*.dart" -o -name "*.swift" \
  -o -name "*.cpp" -o -name "*.c" -o -name "*.h" \
\) \
| grep -v node_modules \
| grep -v "\.git/" \
| grep -v "__pycache__" \
| grep -v "/vendor/" \
| grep -v "/dist/" \
| grep -v "/build/" \
| grep -v "\.generated\." \
| grep -v "\.min\." \
| grep -v "\.spec\." \
| grep -v "\.test\." \
| eval "cat $SUBMODULE_EXCLUDES" \
| sort > /tmp/forge_scan_source_files.txt || true

find "$REPO" -type f \( \
  -name "*.spec.*" -o -name "*.test.*" -o -name "*_test.*" -o -name "test_*.py" \
\) \
| grep -v node_modules | grep -v "\.git/" | grep -v dist \
| sort > /tmp/forge_scan_test_files.txt || true

echo "[1.1] Source files: $(wc -l < /tmp/forge_scan_source_files.txt) | Test files: $(wc -l < /tmp/forge_scan_test_files.txt)"
forge_scan_log_stat "phase=1.1 source_files=$(wc -l < /tmp/forge_scan_source_files.txt) test_files=$(wc -l < /tmp/forge_scan_test_files.txt)"

# ── 1.2: Monorepo + entry point detection ───────────────────────────────────

echo ""
echo "[1.2] Repo structure:"

if [ -f "$REPO/turbo.json" ] || [ -f "$REPO/nx.json" ] || [ -f "$REPO/lerna.json" ]; then
  echo "  Monorepo detected (turbo/nx/lerna). Packages:"
  find "$REPO" -maxdepth 3 -name "package.json" \
    | grep -v node_modules | grep -v "^$REPO/package.json$" \
    | xargs dirname | sort | sed 's/^/    /' || true
else
  echo "  Single-repo"
fi

echo "  Entry points:"
find "$REPO" -maxdepth 3 \( \
  -name "main.py" -o -name "app.py" -o -name "server.py" \
  -o -name "index.ts" -o -name "main.ts" -o -name "app.ts" \
  -o -name "index.js" -o -name "main.js" -o -name "server.js" \
  -o -name "main.go" -o -name "main.kt" -o -name "Main.kt" \
  -o -name "main.rs" -o -name "Application.java" \
\) | grep -v node_modules | grep -v dist | sed 's/^/    /' || true

# ── 1.3: Import graph ────────────────────────────────────────────────────────

while IFS= read -r file; do
  echo "=== $file ==="
  head -50 "$file" | grep -E \
    "^import |^from |^require\(|^use |^extern crate|^#include|^using " \
    2>/dev/null || true
done < /tmp/forge_scan_source_files.txt > /tmp/forge_scan_imports.txt

_import_file_count=$(grep -c "^===" /tmp/forge_scan_imports.txt 2>/dev/null || true)
echo "[1.3] Import relationships extracted: ${_import_file_count:-0} files"
forge_scan_log_stat "phase=1.3 import_blocks=${_import_file_count:-0}"

# ── 1.4: Hub scoring — single-pass from import graph (O(n), no file count limit) ──
#
# Instead of grep-per-file (O(n²)), count how many times each filename stem
# appears in the already-extracted import lines. One grep pass over one file.

SOURCE_COUNT=$(wc -l < /tmp/forge_scan_source_files.txt)
echo "[1.4] Computing hub scores for $SOURCE_COUNT files (single-pass import analysis)..."

> /tmp/forge_scan_hub_scores.txt

set +o pipefail
while IFS= read -r file; do
  basename_no_ext=$(basename "$file" | sed 's/\.[^.]*$//')
  # Count import lines that reference this module name
  count=$(grep -c "$basename_no_ext" /tmp/forge_scan_imports.txt 2>/dev/null || true)
  count=${count:-0}
  echo "$count $file"
done < /tmp/forge_scan_source_files.txt \
| sort -rn > /tmp/forge_scan_hub_scores.txt
set -o pipefail

awk '$1 >= 5 {print $2}' /tmp/forge_scan_hub_scores.txt > /tmp/forge_scan_tier1.txt
awk '$1 >= 3 && $1 < 5 {print $2}' /tmp/forge_scan_hub_scores.txt > /tmp/forge_scan_tier2.txt

echo "[1.4] Tier 1 hubs (5+ refs): $(wc -l < /tmp/forge_scan_tier1.txt) | Tier 2 hubs (3-4 refs): $(wc -l < /tmp/forge_scan_tier2.txt)"
echo "[1.4] Top 10 hubs:"
head -10 /tmp/forge_scan_hub_scores.txt | sed 's/^/  /'
forge_scan_log_stat "phase=1.4 tier1=$(wc -l < /tmp/forge_scan_tier1.txt) tier2=$(wc -l < /tmp/forge_scan_tier2.txt) source_files_scored=$SOURCE_COUNT"

# ── 1.5: Language fingerprinting ─────────────────────────────────────────────

# grep -c prints 0 and exits 1 when there are no matches; never append `|| echo 0`
# or command substitution captures two lines and breaks $(( )) arithmetic.
TS_COUNT=$(grep -c "\.ts$\|\.tsx$" /tmp/forge_scan_source_files.txt 2>/dev/null || true)
JS_COUNT=$(grep -c "\.js$\|\.jsx$" /tmp/forge_scan_source_files.txt 2>/dev/null || true)
PY_COUNT=$(grep -c "\.py$"  /tmp/forge_scan_source_files.txt 2>/dev/null || true)
GO_COUNT=$(grep -c "\.go$"  /tmp/forge_scan_source_files.txt 2>/dev/null || true)
JAVA_COUNT=$(grep -c "\.java$" /tmp/forge_scan_source_files.txt 2>/dev/null || true)
KT_COUNT=$(grep -c "\.kt$"  /tmp/forge_scan_source_files.txt 2>/dev/null || true)
DART_COUNT=$(grep -c "\.dart$" /tmp/forge_scan_source_files.txt 2>/dev/null || true)
RS_COUNT=$(grep -c "\.rs$"  /tmp/forge_scan_source_files.txt 2>/dev/null || true)
TS_COUNT=${TS_COUNT:-0}
JS_COUNT=${JS_COUNT:-0}
PY_COUNT=${PY_COUNT:-0}
GO_COUNT=${GO_COUNT:-0}
JAVA_COUNT=${JAVA_COUNT:-0}
KT_COUNT=${KT_COUNT:-0}
DART_COUNT=${DART_COUNT:-0}
RS_COUNT=${RS_COUNT:-0}
TSJS_COUNT=$(( TS_COUNT + JS_COUNT ))

echo ""
echo "[1.5] Language breakdown:"
echo "  TypeScript/TSX: $TS_COUNT | JavaScript/JSX: $JS_COUNT | Python: $PY_COUNT | Go: $GO_COUNT"
echo "  Java: $JAVA_COUNT | Kotlin: $KT_COUNT | Dart: $DART_COUNT | Rust: $RS_COUNT"
forge_scan_log_stat "phase=1.5 ts=$TS_COUNT js=$JS_COUNT py=$PY_COUNT go=$GO_COUNT java=$JAVA_COUNT kt=$KT_COUNT dart=$DART_COUNT rs=$RS_COUNT tsjs=$TSJS_COUNT"

if [ -f "$REPO/package.json" ]; then
  FRAMEWORK_SIGNALS=$(grep -E '"next"|"express"|"fastify"|"nestjs"|"react-native"|"vue"|"nuxt"|"svelte"|"hono"|"koa"' "$REPO/package.json" 2>/dev/null || true)
  [ -n "$FRAMEWORK_SIGNALS" ] && echo "  Framework signals: $FRAMEWORK_SIGNALS"
fi
[ -f "$REPO/go.mod" ] && grep -E "gin|echo|fiber|chi|mux" "$REPO/go.mod" 2>/dev/null | sed 's/^/  /' || true
[ -f "$REPO/requirements.txt" ] && grep -iE "fastapi|django|flask|starlette|tornado" "$REPO/requirements.txt" 2>/dev/null | sed 's/^/  /' || true
[ -f "$REPO/pubspec.yaml" ] && head -5 "$REPO/pubspec.yaml" | sed 's/^/  /' || true

# ── 1.6: Type / method / function / UI inventory ─────────────────────────────

echo ""
echo "[1.6] Building symbol inventory..."

# ── Java ──────────────────────────────────────────────────────────────────────
if [ "$JAVA_COUNT" -gt 0 ]; then
  grep -rn \
    "^\s*\(public\|protected\|abstract\|final\)\{0,3\}\s*\(class\|interface\|enum\|@interface\)\s" \
    "$REPO" --include="*.java" \
    | grep -v "/test/\|Test\.java\b\|IT\.java\b\|Tests\.java\b" \
    2>/dev/null > /tmp/forge_scan_types_java.txt || true

  grep -rn \
    "^\s*@\(Service\|Repository\|Controller\|RestController\|Component\|Configuration\|Entity\|SpringBootApplication\|EventListener\|Scheduled\)" \
    "$REPO" --include="*.java" \
    | grep -v "/test/" \
    2>/dev/null > /tmp/forge_scan_annotations_java.txt || true

  grep -rn \
    "^\s\+\(public\|protected\)\s\+\(static\s\+\)\?\(final\s\+\)\?\(abstract\s\+\)\?\(synchronized\s\+\)\?\(void\|boolean\|int\|long\|double\|float\|String\|List\|Map\|Set\|Optional\|[A-Z]\)[a-zA-Z0-9<>\[\]?,\s]*\s\+[a-z_][a-zA-Z0-9_]*\s*(" \
    "$REPO" --include="*.java" \
    | grep -v "new \([A-Z]\|\")\|return \|if (\|while (\|for (\|switch (\|throw \|/test/\|Test\.java" \
    2>/dev/null > /tmp/forge_scan_methods_java.txt || true

  echo "  Java    — types: $(wc -l < /tmp/forge_scan_types_java.txt) | methods: $(wc -l < /tmp/forge_scan_methods_java.txt) | annotations: $(wc -l < /tmp/forge_scan_annotations_java.txt)"
else
  > /tmp/forge_scan_types_java.txt
  > /tmp/forge_scan_methods_java.txt
  > /tmp/forge_scan_annotations_java.txt
fi

# ── Kotlin ────────────────────────────────────────────────────────────────────
if [ "$KT_COUNT" -gt 0 ]; then
  grep -rn \
    "^\s*\(data \|sealed \|abstract \|open \|inner \|enum \|annotation \)\?\(class\|interface\|object\)\s\|^\s*typealias \|^\s*companion object" \
    "$REPO" --include="*.kt" \
    | grep -v "Test\.kt\b\|Spec\.kt\b\|/test/" \
    2>/dev/null > /tmp/forge_scan_types_kotlin.txt || true

  grep -rn \
    "^\s*@\(Service\|Repository\|Controller\|RestController\|Component\|Configuration\|Entity\|SpringBootApplication\)" \
    "$REPO" --include="*.kt" \
    | grep -v "/test/" \
    2>/dev/null > /tmp/forge_scan_annotations_kotlin.txt || true

  grep -rn \
    "^\s*\(override\s\+\)\?\(suspend\s\+\)\?\(inline\s\+\)\?\(private\s\+\|protected\s\+\|internal\s\+\|public\s\+\)\?\(open\s\+\)\?fun [a-zA-Z_]" \
    "$REPO" --include="*.kt" \
    | grep -v "Test\.kt\b\|Spec\.kt\b\|/test/" \
    2>/dev/null > /tmp/forge_scan_methods_kotlin.txt || true

  echo "  Kotlin  — types: $(wc -l < /tmp/forge_scan_types_kotlin.txt) | functions: $(wc -l < /tmp/forge_scan_methods_kotlin.txt)"
else
  > /tmp/forge_scan_types_kotlin.txt
  > /tmp/forge_scan_methods_kotlin.txt
  > /tmp/forge_scan_annotations_kotlin.txt
fi

# ── Go ────────────────────────────────────────────────────────────────────────
if [ "$GO_COUNT" -gt 0 ]; then
  grep -rn "^type [A-Z][a-zA-Z0-9]* \(struct\|interface\)\b" \
    "$REPO" --include="*.go" \
    | grep -v "_test\.go" \
    2>/dev/null > /tmp/forge_scan_types_go.txt || true

  grep -rn "^func ([a-zA-Z_][a-zA-Z0-9_]* \*\?[A-Z][a-zA-Z0-9]*) [A-Za-z]" \
    "$REPO" --include="*.go" \
    | grep -v "_test\.go" \
    2>/dev/null > /tmp/forge_scan_methods_go.txt || true

  grep -rn "^func [A-Z][a-zA-Z0-9]*(" \
    "$REPO" --include="*.go" \
    | grep -v "_test\.go" \
    2>/dev/null > /tmp/forge_scan_functions_go.txt || true

  echo "  Go      — types: $(wc -l < /tmp/forge_scan_types_go.txt) | receiver methods: $(wc -l < /tmp/forge_scan_methods_go.txt) | exported funcs: $(wc -l < /tmp/forge_scan_functions_go.txt)"
else
  > /tmp/forge_scan_types_go.txt
  > /tmp/forge_scan_methods_go.txt
  > /tmp/forge_scan_functions_go.txt
fi

# ── TypeScript / JavaScript ───────────────────────────────────────────────────
if [ "$TSJS_COUNT" -gt 0 ]; then
  grep -rn \
    "^export \(default \)\?\(abstract \)\?class \|^export interface \|^export abstract class \|^export type [A-Z]" \
    "$REPO" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
    | grep -v "node_modules\|\.d\.ts\|\.spec\.\|\.test\." \
    2>/dev/null > /tmp/forge_scan_types_ts.txt || true

  grep -rn \
    "^\s\+\(public\|private\|protected\|readonly\|static\|async\|override\)\s\+[a-zA-Z_][a-zA-Z0-9_]*\s*([^)]*)\s*[:{]" \
    "$REPO" --include="*.ts" --include="*.tsx" \
    | grep -v "node_modules\|\.spec\.\|\.test\.\|constructor" \
    2>/dev/null > /tmp/forge_scan_methods_ts.txt || true

  grep -rn \
    "^@\(Injectable\|Controller\|Service\|Repository\|Entity\|Module\|Guard\|Interceptor\|Pipe\|EventEmitter\|Resolver\|ObjectType\|InputType\|Get\|Post\|Put\|Delete\|Patch\)" \
    "$REPO" --include="*.ts" --include="*.tsx" \
    | grep -v "node_modules\|\.spec\.\|\.test\." \
    2>/dev/null > /tmp/forge_scan_decorators_ts.txt || true

  grep -rn "^export \(async \)\?function [a-zA-Z]" \
    "$REPO" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
    | grep -v "node_modules\|\.spec\.\|\.test\." \
    2>/dev/null > /tmp/forge_scan_functions_ts.txt || true

  grep -rn "^export default \(async \)\?function" \
    "$REPO" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
    | grep -v "node_modules\|\.spec\.\|\.test\." \
    2>/dev/null >> /tmp/forge_scan_functions_ts.txt || true

  grep -rn "^export const [a-zA-Z][a-zA-Z0-9]* = \(async \)\?(" \
    "$REPO" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
    | grep -v "node_modules\|\.spec\.\|\.test\." \
    2>/dev/null >> /tmp/forge_scan_functions_ts.txt || true

  echo "  TS/JS   — classes: $(wc -l < /tmp/forge_scan_types_ts.txt) | class methods: $(wc -l < /tmp/forge_scan_methods_ts.txt) | functions: $(wc -l < /tmp/forge_scan_functions_ts.txt) | decorators: $(wc -l < /tmp/forge_scan_decorators_ts.txt)"
else
  > /tmp/forge_scan_types_ts.txt
  > /tmp/forge_scan_methods_ts.txt
  > /tmp/forge_scan_functions_ts.txt
  > /tmp/forge_scan_decorators_ts.txt
fi

# ── Python ────────────────────────────────────────────────────────────────────
if [ "$PY_COUNT" -gt 0 ]; then
  grep -rn "^class [A-Za-z][a-zA-Z0-9]*\b" \
    "$REPO" --include="*.py" \
    | grep -v "test_[a-z]\|_test\.py\|Test[A-Z]" \
    2>/dev/null > /tmp/forge_scan_types_python.txt || true

  grep -rn \
    "^@\(dataclass\|dataclasses\.dataclass\|property\|staticmethod\|classmethod\|abstractmethod\|app\.route\|router\.\)" \
    "$REPO" --include="*.py" \
    | grep -v "test_\|_test\.py" \
    2>/dev/null > /tmp/forge_scan_annotations_python.txt || true

  grep -rn "^def [a-zA-Z][a-zA-Z0-9_]*\|^async def [a-zA-Z][a-zA-Z0-9_]*" \
    "$REPO" --include="*.py" \
    | grep -v "test_\|_test\.py\|__init__\|__main__\|__str__\|__repr__\|__eq__\|__hash__\|__len__\|__iter__" \
    2>/dev/null > /tmp/forge_scan_functions_python.txt || true

  grep -rn "^\s\+def [a-zA-Z][a-zA-Z0-9_]*\|^\s\+async def [a-zA-Z][a-zA-Z0-9_]*" \
    "$REPO" --include="*.py" \
    | grep -v "test_\|_test\.py\|__init__\|__str__\|__repr__\|__eq__\|__hash__\|__len__" \
    2>/dev/null > /tmp/forge_scan_methods_python.txt || true

  echo "  Python  — types: $(wc -l < /tmp/forge_scan_types_python.txt) | class methods: $(wc -l < /tmp/forge_scan_methods_python.txt) | module funcs: $(wc -l < /tmp/forge_scan_functions_python.txt)"
else
  > /tmp/forge_scan_types_python.txt
  > /tmp/forge_scan_methods_python.txt
  > /tmp/forge_scan_functions_python.txt
  > /tmp/forge_scan_annotations_python.txt
fi

# ── Dart / Flutter ────────────────────────────────────────────────────────────
if [ "$DART_COUNT" -gt 0 ]; then
  grep -rn "^\(abstract \)\?class [A-Z]\|^mixin [A-Z]\|^enum [A-Z]" \
    "$REPO" --include="*.dart" \
    | grep -v "_test\.dart\|test/" \
    2>/dev/null > /tmp/forge_scan_types_dart.txt || true

  grep -rn \
    "^\s*\(Future\|Stream\|void\|bool\|int\|double\|String\|Widget\|[A-Z][a-zA-Z0-9<>?]*\)\s\+[a-z_][a-zA-Z0-9_]*\s*(" \
    "$REPO" --include="*.dart" \
    | grep -v "_test\.dart\|test/" \
    2>/dev/null > /tmp/forge_scan_methods_dart.txt || true

  echo "  Dart    — types: $(wc -l < /tmp/forge_scan_types_dart.txt) | methods: $(wc -l < /tmp/forge_scan_methods_dart.txt)"
else
  > /tmp/forge_scan_types_dart.txt
  > /tmp/forge_scan_methods_dart.txt
fi

# ── Rust ──────────────────────────────────────────────────────────────────────
if [ "$RS_COUNT" -gt 0 ]; then
  grep -rn "^pub \(struct\|enum\|trait\) [A-Z]\|^pub(crate) \(struct\|enum\|trait\) [A-Z]" \
    "$REPO" --include="*.rs" \
    | grep -v "test\b\|#\[test\]" \
    2>/dev/null > /tmp/forge_scan_types_rust.txt || true

  grep -rn "^\s*pub fn [a-zA-Z_]\|^pub fn [a-zA-Z_]\|^pub async fn [a-zA-Z_]" \
    "$REPO" --include="*.rs" \
    | grep -v "#\[test\]\|mod tests" \
    2>/dev/null > /tmp/forge_scan_methods_rust.txt || true

  echo "  Rust    — types: $(wc -l < /tmp/forge_scan_types_rust.txt) | pub fns: $(wc -l < /tmp/forge_scan_methods_rust.txt)"
else
  > /tmp/forge_scan_types_rust.txt
  > /tmp/forge_scan_methods_rust.txt
fi

# ── Frontend / HTML / Templates ───────────────────────────────────────────────
find "$REPO" -type f \( -name "*.html" -o -name "*.htm" \) \
  | grep -v "node_modules\|dist\|build\|\.git\|coverage" \
  | sort > /tmp/forge_scan_html_files.txt || true

find "$REPO" -type f -name "*.vue" \
  | grep -v "node_modules\|dist" \
  | sort > /tmp/forge_scan_vue_files.txt || true

find "$REPO" -type f -name "*.svelte" \
  | grep -v "node_modules\|dist" \
  | sort > /tmp/forge_scan_svelte_files.txt || true

find "$REPO" -type f -name "*.component.html" \
  | grep -v "node_modules\|dist" \
  | sort > /tmp/forge_scan_angular_templates.txt || true

grep -rn "<form\s\+\|<form>" \
  "$REPO" --include="*.html" --include="*.vue" --include="*.svelte" \
  --include="*.tsx" --include="*.jsx" \
  | grep -v "node_modules\|dist" \
  2>/dev/null > /tmp/forge_scan_html_forms.txt || true

grep -rn "id=\"[a-zA-Z][a-zA-Z0-9_-]*\"\|data-[a-z][a-z0-9-]*=" \
  "$REPO" --include="*.html" --include="*.vue" --include="*.svelte" \
  | grep -v "node_modules\|dist" \
  2>/dev/null > /tmp/forge_scan_html_ids.txt || true

echo "  Frontend — HTML: $(wc -l < /tmp/forge_scan_html_files.txt) | Vue: $(wc -l < /tmp/forge_scan_vue_files.txt) | Svelte: $(wc -l < /tmp/forge_scan_svelte_files.txt) | Angular: $(wc -l < /tmp/forge_scan_angular_templates.txt) | Forms: $(wc -l < /tmp/forge_scan_html_forms.txt)"

# ── Master inventories ────────────────────────────────────────────────────────

cat \
  /tmp/forge_scan_types_java.txt \
  /tmp/forge_scan_types_kotlin.txt \
  /tmp/forge_scan_types_go.txt \
  /tmp/forge_scan_types_ts.txt \
  /tmp/forge_scan_types_python.txt \
  /tmp/forge_scan_types_dart.txt \
  /tmp/forge_scan_types_rust.txt \
  2>/dev/null > /tmp/forge_scan_types_all.txt

cat \
  /tmp/forge_scan_methods_java.txt \
  /tmp/forge_scan_methods_kotlin.txt \
  /tmp/forge_scan_methods_go.txt \
  /tmp/forge_scan_methods_ts.txt \
  /tmp/forge_scan_methods_python.txt \
  /tmp/forge_scan_methods_dart.txt \
  /tmp/forge_scan_methods_rust.txt \
  2>/dev/null > /tmp/forge_scan_methods_all.txt

cat \
  /tmp/forge_scan_functions_ts.txt \
  /tmp/forge_scan_functions_go.txt \
  /tmp/forge_scan_functions_python.txt \
  2>/dev/null > /tmp/forge_scan_functions_all.txt

cat \
  /tmp/forge_scan_html_files.txt \
  /tmp/forge_scan_vue_files.txt \
  /tmp/forge_scan_svelte_files.txt \
  /tmp/forge_scan_angular_templates.txt \
  2>/dev/null > /tmp/forge_scan_ui_all.txt

TYPES_COUNT=$(wc -l < /tmp/forge_scan_types_all.txt)
METHODS_COUNT=$(wc -l < /tmp/forge_scan_methods_all.txt)
FUNCS_COUNT=$(wc -l < /tmp/forge_scan_functions_all.txt)
UI_COUNT=$(wc -l < /tmp/forge_scan_ui_all.txt)
TOTAL=$(( TYPES_COUNT + METHODS_COUNT + FUNCS_COUNT + UI_COUNT ))

forge_scan_log_stat "phase=1.6 types=$TYPES_COUNT methods=$METHODS_COUNT functions=$FUNCS_COUNT ui=$UI_COUNT html_forms=$(wc -l < /tmp/forge_scan_html_forms.txt) total_potential_nodes=$TOTAL"

echo ""
echo "══════════════════════════════════════════════════════════"
echo "INVENTORY SUMMARY"
echo "══════════════════════════════════════════════════════════"
echo "  Types     (→ classes/):    $TYPES_COUNT"
echo "  Methods   (→ methods/):    $METHODS_COUNT"
echo "  Functions (→ functions/):  $FUNCS_COUNT"
echo "  UI files  (→ pages/):      $UI_COUNT"
echo "  HTML forms found:          $(wc -l < /tmp/forge_scan_html_forms.txt)"
echo "══════════════════════════════════════════════════════════"
echo "TOTAL POTENTIAL NODES: $TOTAL"
echo "══════════════════════════════════════════════════════════"
echo ""
echo "Tier 1 hubs (5+ refs): $(wc -l < /tmp/forge_scan_tier1.txt)"
echo "Tier 2 hubs (3-4 refs): $(wc -l < /tmp/forge_scan_tier2.txt)"
echo ""
echo "Phase 1 complete. All inventory files written to /tmp/forge_scan_*.txt"
echo "Next: Phase 2 (hub assignment already done above), Phase 3 (hub reads)"
forge_scan_log_done "tier1=$(wc -l < /tmp/forge_scan_tier1.txt) tier2=$(wc -l < /tmp/forge_scan_tier2.txt) types=$TYPES_COUNT methods=$METHODS_COUNT functions=$FUNCS_COUNT ui=$UI_COUNT total_potential_nodes=$TOTAL"

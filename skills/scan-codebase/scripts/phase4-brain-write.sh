#!/usr/bin/env bash
# Forge scan-codebase: Phase 4 — Brain node auto-generation
#
# Usage: bash /path/to/forge/scripts/phase4-brain-write.sh <REPO_PATH> <BRAIN_CODEBASE_DIR> <ROLE>
#
# Prerequisite: phase1-inventory.sh must have been run first.
# Needs: /tmp/forge_scan_types_all.txt, forge_scan_methods_all.txt,
#         forge_scan_functions_all.txt, forge_scan_ui_all.txt, forge_scan_source_files.txt
#
# What this does:
#   Generates stub .md brain nodes for EVERY class, function, page, and module
#   found by Phase 1 grep scans. The LLM no longer decides what to write —
#   the script writes everything. The LLM's only job in Phase 3 is to ENRICH
#   these stubs during hub reads (add purpose, parameters, relationships).
#
# Writes to <BRAIN_CODEBASE_DIR>:
#   classes/<role>-<ClassName>.md     one per class/interface/enum/struct/trait
#   methods/<role>-m-<cksum>.md      one per Phase 1.6 method line (full repo — not hub-gated)
#   functions/<role>-<FuncName>.md    one per exported standalone function
#   pages/<role>-<FileName>.md        one per HTML/Vue/Svelte/Angular/TSX/JSX file
#   modules/<role>-<PackageDir>.md    one per unique source directory (scaffold)
#
# Existing files are NEVER overwritten — safe to re-run after manual enrichment.

set -euo pipefail

_fs_scripts=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC1091
. "$_fs_scripts/_forge-scan-log.sh"
# shellcheck disable=SC1091
. "$_fs_scripts/_forge-mod-slug.sh"

REPO="${1:?Usage: $0 <repo-path> <brain-codebase-dir> <role>}"
BRAIN_DIR="${2:?Usage: $0 <repo-path> <brain-codebase-dir> <role>}"
ROLE="${3:?Usage: $0 <repo-path> <brain-codebase-dir> <role>}"

forge_scan_log_start phase4-brain-write "repo=$REPO brain_dir=$BRAIN_DIR role=$ROLE"

for _f in forge_scan_types_all.txt forge_scan_methods_all.txt forge_scan_functions_all.txt forge_scan_ui_all.txt forge_scan_source_files.txt; do
  if [ ! -s "/tmp/$_f" ]; then
    forge_scan_log_warn "input_missing_or_empty path=/tmp/$_f hint=run_phase1-inventory.sh_first"
  fi
done

mkdir -p "$BRAIN_DIR/classes" "$BRAIN_DIR/methods" "$BRAIN_DIR/functions" "$BRAIN_DIR/pages" "$BRAIN_DIR/modules"

CLASSES=0
METHODS=0
FUNCTIONS=0
PAGES=0
MODULES=0
SKIPPED=0

echo "════════════════════════════════════════════════════════"
echo "FORGE SCAN — Phase 4: Brain Node Auto-Generation"
echo "Repo:  $REPO"
echo "Role:  $ROLE"
echo "Brain: $BRAIN_DIR"
echo "════════════════════════════════════════════════════════"

# Helper: detect language from file extension
detect_lang() {
  case "$1" in
    *.java)  echo "Java" ;;
    *.kt)    echo "Kotlin" ;;
    *.go)    echo "Go" ;;
    *.ts)    echo "TypeScript" ;;
    *.tsx)   echo "TypeScript (TSX)" ;;
    *.js)    echo "JavaScript" ;;
    *.jsx)   echo "JavaScript (JSX)" ;;
    *.py)    echo "Python" ;;
    *.dart)  echo "Dart" ;;
    *.rs)    echo "Rust" ;;
    *.rb)    echo "Ruby" ;;
    *.swift) echo "Swift" ;;
    *)       echo "Unknown" ;;
  esac
}

# Helper: parse "filepath:linenum:content" grep output line
# Handles file paths that contain colons (rare but possible)
parse_grep_line() {
  local line="$1"
  # Line number is always a pure integer between two colons
  _LINENUM=$(echo "$line" | grep -oE ':[0-9]+:' | head -1 | tr -d ':')
  if [ -z "$_LINENUM" ]; then
    _FILE=""
    _CONTENT=""
    return
  fi
  _FILE=$(echo "$line" | sed "s/:${_LINENUM}:.*//")
  _CONTENT=$(echo "$line" | sed "s|^.*:${_LINENUM}:||")
}

# ── 4.3a: Classes ─────────────────────────────────────────────────────────────
echo ""
echo "[4.3a] Generating class nodes from forge_scan_types_all.txt..."
echo "  Input: $(wc -l < /tmp/forge_scan_types_all.txt 2>/dev/null || echo 0) lines"

set +o pipefail
while IFS= read -r line || [ -n "$line" ]; do
  [ -z "$line" ] && continue

  parse_grep_line "$line"
  [ -z "$_FILE" ] && continue

  # Extract type keyword and name
  TYPEINFO=$(echo "$_CONTENT" | grep -oE "\b(class|interface|enum|object|data class|sealed class|abstract class|annotation class|struct|trait|protocol|@interface)\b [A-Z][a-zA-Z0-9_]*" | head -1)
  [ -z "$TYPEINFO" ] && continue

  KIND=$(echo "$TYPEINFO" | awk '{print $1}')
  CLASS=$(echo "$TYPEINFO" | awk '{print $NF}')
  [ -z "$CLASS" ] && continue

  # Skip generated files
  echo "$_FILE" | grep -qE "(Generated\.|_pb2\.|DataBinding|ViewBinding|Binding\b|\.generated\.)" && continue

  REL_FILE="${_FILE#$REPO/}"
  LANG=$(detect_lang "$_FILE")
  MODULE=$(basename "$REL_FILE" | sed 's/\.[^.]*$//')
  DIR=$(dirname "$REL_FILE")
  [ "$DIR" = "." ] && DIR="root"

  NODE="$BRAIN_DIR/classes/$ROLE-$CLASS.md"
  if [ -f "$NODE" ]; then
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  cat > "$NODE" << NODEEOF
# $KIND: $CLASS

**Module:** [[modules/$ROLE-$MODULE]]
**File:** \`$REL_FILE:$_LINENUM\`
**Language:** $LANG
**Kind:** $KIND

## Purpose
_Auto-generated stub — enrich during Phase 3 hub read._

## Key Responsibilities
_What problem does this $KIND solve?_

## Key Methods
_See [[methods/]] — auto stubs use \`$ROLE-m-<cksum>\` (full inventory); optional hand nodes \`$ROLE-$CLASS-<method>\`._

## Extends / Implements
_Fill in during Phase 3 read._

## Used By
_Populated by phase56 / manual cross-repo notes after phase5 prep._

## Location in Structure
**Repo role:** $ROLE | **Package:** $DIR
NODEEOF
  CLASSES=$((CLASSES + 1))
done < /tmp/forge_scan_types_all.txt
set -o pipefail

echo "  Written: $CLASSES class nodes"
forge_scan_log_stat "phase=4.3a classes_written=$CLASSES input_lines=$(wc -l < /tmp/forge_scan_types_all.txt 2>/dev/null || echo 0)"

# ── 4.3c: Functions ──────────────────────────────────────────────────────────
echo ""
echo "[4.3c] Generating function nodes from forge_scan_functions_all.txt..."
echo "  Input: $(wc -l < /tmp/forge_scan_functions_all.txt 2>/dev/null || echo 0) lines"

set +o pipefail
while IFS= read -r line || [ -n "$line" ]; do
  [ -z "$line" ] && continue

  parse_grep_line "$line"
  [ -z "$_FILE" ] && continue

  FUNC=""
  # export function foo / export async function foo / export default function
  [ -z "$FUNC" ] && FUNC=$(echo "$_CONTENT" | grep -oE "\bfunction ([a-zA-Z][a-zA-Z0-9_]*)" | head -1 | awk '{print $2}')
  # Python: def foo / async def foo
  [ -z "$FUNC" ] && FUNC=$(echo "$_CONTENT" | grep -oE "\bdef ([a-zA-Z][a-zA-Z0-9_]*)" | head -1 | awk '{print $2}')
  # Go exported: func FooBar(
  [ -z "$FUNC" ] && FUNC=$(echo "$_CONTENT" | grep -oE "\bfunc ([A-Z][a-zA-Z0-9_]*)" | head -1 | awk '{print $2}')
  # Arrow: export const foo = (  / export const foo = async (
  [ -z "$FUNC" ] && FUNC=$(echo "$_CONTENT" | grep -oE "\bconst ([a-zA-Z][a-zA-Z0-9_]*)\s*=" | head -1 | awk '{print $2}')
  [ -z "$FUNC" ] && continue

  # Skip single-letter or too-generic names
  [ "${#FUNC}" -le 1 ] && continue
  echo "$FUNC" | grep -qE "^(get|set|is|has|to|of|by|on|do)$" && continue

  REL_FILE="${_FILE#$REPO/}"
  LANG=$(detect_lang "$_FILE")
  MODULE=$(basename "$REL_FILE" | sed 's/\.[^.]*$//')

  NODE="$BRAIN_DIR/functions/$ROLE-$FUNC.md"
  if [ -f "$NODE" ]; then
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  cat > "$NODE" << NODEEOF
# Function: $FUNC

**Module:** [[modules/$ROLE-$MODULE]]
**File:** \`$REL_FILE:$_LINENUM\`
**Language:** $LANG

## Purpose
_Auto-generated stub — enrich during Phase 3 hub read._

## Parameters
_Fill in: argument names and types._

## Returns
_Fill in: return type and what it represents._

## Called By
_Fill in during Phase 3 or manual cross-repo correlation (phase56 covers HTTP paths)._

## Calls
_Fill in during Phase 3 or manual cross-repo correlation (phase56 covers HTTP paths)._

## Location in Structure
**Repo role:** $ROLE
NODEEOF
  FUNCTIONS=$((FUNCTIONS + 1))
done < /tmp/forge_scan_functions_all.txt
set -o pipefail

echo "  Written: $FUNCTIONS function nodes"
forge_scan_log_stat "phase=4.3c functions_written=$FUNCTIONS input_lines=$(wc -l < /tmp/forge_scan_functions_all.txt 2>/dev/null || echo 0)"

# ── 4.3d: Method stubs (FULL inventory — not Tier 1/2 gated) ─────────────────
echo ""
if [ "${FORGE_PHASE4_SKIP_METHODS:-}" = "1" ]; then
  echo "[4.3d] Skipping method nodes (FORGE_PHASE4_SKIP_METHODS=1)"
else
  if [ ! -f /tmp/forge_scan_methods_all.txt ]; then
    echo "[4.3d] Skipping — /tmp/forge_scan_methods_all.txt missing (run phase1-inventory.sh)"
    forge_scan_log_warn "missing /tmp/forge_scan_methods_all.txt"
  else
  echo "[4.3d] Generating method nodes from forge_scan_methods_all.txt (every grep hit)..."
  echo "  Input: $(wc -l < /tmp/forge_scan_methods_all.txt 2>/dev/null || echo 0) lines"
  echo "  (Set FORGE_PHASE4_SKIP_METHODS=1 to skip on enormous repos.)"

  set +o pipefail
  while IFS= read -r line || [ -n "$line" ]; do
    [ -z "$line" ] && continue
    parse_grep_line "$line"
    [ -z "$_FILE" ] && continue

    REL_FILE="${_FILE#$REPO/}"
    LANG=$(detect_lang "$_FILE")
    DIR=$(dirname "$REL_FILE")
    [ "$DIR" = "." ] && DIR="root"

    _M_ID=$(printf '%s' "$line" | cksum | awk '{print $1}')
    NODE="$BRAIN_DIR/methods/$ROLE-m-$_M_ID.md"
    if [ -f "$NODE" ]; then
      SKIPPED=$((SKIPPED + 1))
      continue
    fi

    _SIG=$(printf '%s' "$_CONTENT" | head -c 400 | tr '\r\n' '  ')
    _MOD_SLUG=$(printf '%s' "$DIR" | tr '/' '-' | sed 's/^-//' | sed 's/-$//')
    [ -z "$_MOD_SLUG" ] && _MOD_SLUG=root

    {
      printf '%s\n\n' "# Method (inventory)"
      printf '%s\n' "**Module:** [[modules/$ROLE-$_MOD_SLUG]]"
      printf '%s\n' "**Class hub:** _See [[classes/]] for types in \`$REL_FILE\` — link the owning class during enrich._"
      printf '%s\n' "**File:** \`$REL_FILE:$_LINENUM\`"
      printf '%s\n' "**Language:** $LANG"
      printf '%s\n\n' "**Stable id:** \`$ROLE-m-$_M_ID\` (cksum of grep line — unique per grep hit)"
      printf '%s\n' "## Signature (Phase 1 grep)"
      printf '%s\n' '```text'
      printf '%s\n' "$_SIG"
      printf '%s\n\n' '```'
      printf '%s\n' "## Purpose"
      printf '%s\n\n' "_Auto-generated from Phase 1.6 — **not** limited to Tier 1 hubs. Enrich by reading this line in context._"
      printf '%s\n' "## Parameters / return"
      printf '%s\n\n' "_Fill in during read._"
      printf '%s\n' "## Calls / data flow"
      printf '%s\n\n' "_Fill in during read or manual cross-repo pass._"
      printf '%s\n' "## Location"
      printf '%s\n' "**Repo role:** $ROLE | **Directory:** $DIR"
    } > "$NODE"
    METHODS=$((METHODS + 1))
  done < /tmp/forge_scan_methods_all.txt
  set -o pipefail

  echo "  Written: $METHODS method nodes"
  forge_scan_log_stat "phase=4.3d methods_written=$METHODS input_lines=$(wc -l < /tmp/forge_scan_methods_all.txt 2>/dev/null || echo 0)"
  fi
fi

# ── 4.3e: Pages / UI ─────────────────────────────────────────────────────────
echo ""
echo "[4.3e] Generating page nodes from forge_scan_ui_all.txt..."
echo "  Input: $(wc -l < /tmp/forge_scan_ui_all.txt 2>/dev/null || echo 0) UI files"

set +o pipefail
while IFS= read -r file || [ -n "$file" ]; do
  [ -z "$file" ] && continue

  REL_FILE="${file#$REPO/}"
  NAME=$(basename "$REL_FILE" | sed 's/\.[^.]*$//')

  FORMAT="HTML"
  case "$file" in
    *.vue)            FORMAT="Vue SFC" ;;
    *.svelte)         FORMAT="Svelte" ;;
    *.component.html) FORMAT="Angular Template" ;;
    *.tsx)            FORMAT="TypeScript (TSX)" ;;
    *.jsx)            FORMAT="JavaScript (JSX)" ;;
    *.htm)            FORMAT="HTML" ;;
  esac

  KIND="component"
  echo "$REL_FILE" | grep -qiE "(pages?|screens?|views?)[/\\]" && KIND="page"
  echo "$REL_FILE" | grep -qiE "layouts?[/\\]"                  && KIND="layout"
  echo "$REL_FILE" | grep -qiE "(dialogs?|modals?)[/\\]"        && KIND="dialog"
  echo "$REL_FILE" | grep -qiE "(partials?|fragments?)[/\\]"    && KIND="partial"

  # Infer route from Next.js / Nuxt / SvelteKit convention
  ROUTE="unknown"
  ROUTE_PATH=$(echo "$REL_FILE" | grep -oE "(pages|app|routes)/.*" | sed 's/\.[^.]*$//' | sed 's|^pages/||' | sed 's|^app/||' | sed 's|^routes/||')
  [ -n "$ROUTE_PATH" ] && ROUTE="/$ROUTE_PATH"

  NODE="$BRAIN_DIR/pages/$ROLE-$NAME.md"
  if [ -f "$NODE" ]; then
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  cat > "$NODE" << NODEEOF
# Page: $NAME

**File:** \`$REL_FILE\`
**Language / Format:** $FORMAT
**Kind:** $KIND
**Route / URL:** \`$ROUTE\`

## Purpose
_Auto-generated stub — enrich during Phase 3 hub read._

## Key UI Elements
_Fill in: main components, data displayed, navigation._

## Forms
_Fill in: form names, fields, submit actions._

## Script / Component Dependencies
_Fill in: components imported, composables/hooks used._

## API Calls Made
_Populated by phase56 / manual cross-repo notes after phase5 prep._

## Location in Structure
**Repo role:** $ROLE
NODEEOF
  PAGES=$((PAGES + 1))
done < /tmp/forge_scan_ui_all.txt
set -o pipefail

echo "  Written: $PAGES page nodes"
forge_scan_log_stat "phase=4.3e pages_written=$PAGES input_lines=$(wc -l < /tmp/forge_scan_ui_all.txt 2>/dev/null || echo 0)"

# ── 4.3b: Module scaffolds from directory structure ───────────────────────────
echo ""
echo "[4.3b] Generating module scaffold nodes from source directory structure..."

# Build unique directory list without pipefail issue
> /tmp/forge_scan_dirs.txt
set +o pipefail
while IFS= read -r file; do
  [ -z "$file" ] && continue
  REL="${file#$REPO/}"
  dirname "$REL"
done < /tmp/forge_scan_source_files.txt | sort -u > /tmp/forge_scan_dirs.txt
set -o pipefail

while IFS= read -r dir || [ -n "$dir" ]; do
  [ -z "$dir" ] && continue
  [ "$dir" = "." ] && dir="root"

  MODULE_NAME=$(forge_mod_dirslug_from_dir "$dir")
  NODE="$BRAIN_DIR/modules/$ROLE-$MODULE_NAME.md"

  if [ -f "$NODE" ]; then
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  cat > "$NODE" << NODEEOF
# Module: $ROLE / $dir

**Directory:** \`$dir/\`
**Repo role:** $ROLE

## Purpose
_Auto-generated scaffold — enrich during Phase 3._

## Key Types Defined Here
_See [[classes/]] for individual class nodes with prefix \`$ROLE-\`_

## Exports
_Fill in: exported functions, types, constants._

## Internal Dependencies
_Fill in: other modules this one imports from._

## Calls (cross-repo)
_After `phase5-cross-repo.sh`, run `phase56-autolink-crossrepo.sh` (markers `FORGE:AUTO_CROSS_REPO_OUT`). Heuristic — verify. Optional: add `route-aliases.tsv` in the codebase brain parent for extra synthetic route lines. Further manual rows only if needed._

## Called By (cross-repo)
_Same: `phase56-autolink-crossrepo.sh` (`FORGE:AUTO_CROSS_REPO_IN`). Optional manual rows only if needed._
NODEEOF
  MODULES=$((MODULES + 1))
done < /tmp/forge_scan_dirs.txt

echo "  Written: $MODULES module scaffold nodes"
forge_scan_log_stat "phase=4.3b modules_written=$MODULES unique_dirs=$(wc -l < /tmp/forge_scan_dirs.txt 2>/dev/null || echo 0)"

# ── Summary ───────────────────────────────────────────────────────────────────
TOTAL=$((CLASSES + METHODS + FUNCTIONS + PAGES + MODULES))
echo ""
echo "════════════════════════════════════════════════════════"
echo "PHASE 4 AUTO-GENERATION COMPLETE"
echo "════════════════════════════════════════════════════════"
echo "  Classes     (classes/):   $CLASSES"
echo "  Methods     (methods/):   $METHODS  (full Phase 1.6 inventory — use FORGE_PHASE4_SKIP_METHODS=1 to skip)"
echo "  Functions   (functions/): $FUNCTIONS"
echo "  Pages       (pages/):     $PAGES"
echo "  Modules     (modules/):   $MODULES"
echo "  Skipped (already exist):  $SKIPPED"
echo "════════════════════════════════════════════════════════"
echo "TOTAL NEW NODES WRITTEN: $TOTAL"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Enrich: Tier 1/2 hub file reads (Phase 3) — OR batch-read all of forge_scan_source_files.txt for full prose"
echo "  2. Multi-repo: phase5-cross-repo.sh → phase56-autolink-crossrepo.sh → phase57-validate-brain-wikilinks.sh (optional --write-report) → cleanup.sh"
echo "  3. git -C ~/forge/brain add products/<slug>/codebase/"
echo "  4. git -C ~/forge/brain commit -m 'scan: <slug> codebase brain nodes ($TOTAL nodes)'"
forge_scan_log_done "classes=$CLASSES methods=$METHODS functions=$FUNCTIONS pages=$PAGES modules=$MODULES skipped_existing=$SKIPPED total_new=$TOTAL"

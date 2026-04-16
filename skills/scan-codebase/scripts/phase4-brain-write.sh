#!/usr/bin/env bash
# Forge scan-codebase: Phase 4 — Brain node auto-generation
#
# Usage: bash /path/to/forge/scripts/phase4-brain-write.sh <REPO_PATH> <BRAIN_CODEBASE_DIR> <ROLE>
#
# Prerequisite: phase1-inventory.sh must have been run first.
# Needs: /tmp/forge_scan_types_all.txt, forge_scan_functions_all.txt,
#         forge_scan_ui_all.txt, forge_scan_source_files.txt
#
# What this does:
#   Generates stub .md brain nodes for EVERY class, function, page, and module
#   found by Phase 1 grep scans. The LLM no longer decides what to write —
#   the script writes everything. The LLM's only job in Phase 3 is to ENRICH
#   these stubs during hub reads (add purpose, parameters, relationships).
#
# Writes to <BRAIN_CODEBASE_DIR>:
#   classes/<role>-<ClassName>.md     one per class/interface/enum/struct/trait
#   functions/<role>-<FuncName>.md    one per exported standalone function
#   pages/<role>-<FileName>.md        one per HTML/Vue/Svelte/Angular/TSX/JSX file
#   modules/<role>-<PackageDir>.md    one per unique source directory (scaffold)
#
# Existing files are NEVER overwritten — safe to re-run after manual enrichment.

set -euo pipefail

REPO="${1:?Usage: $0 <repo-path> <brain-codebase-dir> <role>}"
BRAIN_DIR="${2:?Usage: $0 <repo-path> <brain-codebase-dir> <role>}"
ROLE="${3:?Usage: $0 <repo-path> <brain-codebase-dir> <role>}"

mkdir -p "$BRAIN_DIR/classes" "$BRAIN_DIR/methods" "$BRAIN_DIR/functions" "$BRAIN_DIR/pages" "$BRAIN_DIR/modules"

CLASSES=0
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
_See [[methods/]] directory — nodes prefixed \`$ROLE-$CLASS-\`_

## Extends / Implements
_Fill in during Phase 3 read._

## Used By
_Populated during Phase 5.5 cross-repo correlation._

## Location in Structure
**Repo role:** $ROLE | **Package:** $DIR
NODEEOF
  CLASSES=$((CLASSES + 1))
done < /tmp/forge_scan_types_all.txt
set -o pipefail

echo "  Written: $CLASSES class nodes"

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
_Fill in during Phase 3 or Phase 5.5 cross-repo correlation._

## Calls
_Fill in during Phase 3 or Phase 5.5 cross-repo correlation._

## Location in Structure
**Repo role:** $ROLE
NODEEOF
  FUNCTIONS=$((FUNCTIONS + 1))
done < /tmp/forge_scan_functions_all.txt
set -o pipefail

echo "  Written: $FUNCTIONS function nodes"

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
_Populated during Phase 5.5 cross-repo correlation._

## Location in Structure
**Repo role:** $ROLE
NODEEOF
  PAGES=$((PAGES + 1))
done < /tmp/forge_scan_ui_all.txt
set -o pipefail

echo "  Written: $PAGES page nodes"

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

  # Sanitize: replace path separators with dashes for filename
  MODULE_NAME=$(echo "$dir" | tr '/' '-' | sed 's/^-//' | sed 's/-$//')
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
_Populated during Phase 5.5 cross-repo correlation._

## Called By (cross-repo)
_Populated during Phase 5.5 cross-repo correlation._
NODEEOF
  MODULES=$((MODULES + 1))
done < /tmp/forge_scan_dirs.txt

echo "  Written: $MODULES module scaffold nodes"

# ── Summary ───────────────────────────────────────────────────────────────────
TOTAL=$((CLASSES + FUNCTIONS + PAGES + MODULES))
echo ""
echo "════════════════════════════════════════════════════════"
echo "PHASE 4 AUTO-GENERATION COMPLETE"
echo "════════════════════════════════════════════════════════"
echo "  Classes     (classes/):   $CLASSES"
echo "  Functions   (functions/): $FUNCTIONS"
echo "  Pages       (pages/):     $PAGES"
echo "  Modules     (modules/):   $MODULES"
echo "  Skipped (already exist):  $SKIPPED"
echo "════════════════════════════════════════════════════════"
echo "TOTAL NEW NODES WRITTEN: $TOTAL"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Phase 3 hub reads — enrich stubs for Tier 1/2 hub files"
echo "  2. git -C ~/forge/brain add products/<slug>/codebase/"
echo "  3. git -C ~/forge/brain commit -m 'scan: <slug> codebase brain nodes ($TOTAL nodes)'"

#!/usr/bin/env bash
# List Obsidian-style [[wikilinks]] (and ![[embeds]]) under a codebase brain tree
# whose target does not resolve to any existing .md file. Optional: ambiguous basenames.
#
# Usage: bash .../phase57-validate-brain-wikilinks.sh <BRAIN_CODEBASE_PARENT> [--write-report]
#
# Example:
#   bash phase57-validate-brain-wikilinks.sh "$HOME/forge/brain/products/jh/codebase" --write-report
#
# Resolution rules (match common Obsidian + Forge scan output):
#   - [[name]] / ![[name]]  → any file named name.md anywhere under PARENT (excluding .obsidian)
#   - [[dir/sub]]          → PARENT/dir/sub.md first; if missing, same as basename-only search
#
# Must run with bash. Requires GNU grep with -o (BusyBox may fail).

if [ -z "${BASH_VERSION:-}" ]; then
  printf '%s: requires bash, not sh/dash. Use: bash "%s" <BRAIN_CODEBASE_PARENT> [--write-report]\n' "${0##*/}" "$0" >&2
  exit 127
fi

set -euo pipefail

USAGE() {
  printf 'Usage: %s <BRAIN_CODEBASE_PARENT> [--write-report]\n' "${0##*/}" >&2
  exit 1
}

PARENT="${1:-}"
[ -n "$PARENT" ] && [ -d "$PARENT" ] || USAGE
shift || true
WRITE=0
if [ "${1:-}" = "--write-report" ]; then
  WRITE=1
fi

_fs_scripts=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_forge-scan-log.sh
. "$_fs_scripts/_forge-scan-log.sh"
FORGE_SCAN_SCRIPT_ID=phase57-validate-brain-wikilinks
forge_scan_log_start "brain_parent=$PARENT write_report=$WRITE"

_idx=$(mktemp)
_links=$(mktemp)
_report=$(mktemp)
_cut_ambig=$(mktemp)
trap 'rm -f "$_idx" "$_links" "$_report" "$_cut_ambig"' EXIT

find "$PARENT" -type f -name '*.md' ! -path '*/.obsidian/*' -print 2>/dev/null \
  | while IFS= read -r f; do
    [ -z "$f" ] && continue
    b=$(basename "$f" .md)
    printf '%s\t%s\n' "$b" "$f"
  done | LC_ALL=C sort -t "$(printf '\t')" -k1,1 -k2,2 > "$_idx" || true

if [ ! -s "$_idx" ]; then
  forge_scan_log_warn "no_markdown_under_parent"
  printf 'No .md files found under %s (excluding .obsidian).\n' "$PARENT"
  forge_scan_log_done "orphans=0 ambiguous_basenames=0"
  exit 0
fi

# Collect wikilink occurrences: file<TAB>line<TAB>[[...]] (tabs — paths may contain ':')
> "$_links"
while IFS= read -r -d '' f; do
  # -o: one wikilink per line (same line number repeated if multiple on one line)
  grep -on '\[\[[^]]*\]\]' "$f" 2>/dev/null | while IFS= read -r gline; do
    [ -z "$gline" ] && continue
    lineno="${gline%%:*}"
    match="${gline#*:}"
    printf '%s\t%s\t%s\n' "$f" "$lineno" "$match"
  done >> "$_links" || true
  grep -on '!\[\[[^]]*\]\]' "$f" 2>/dev/null | while IFS= read -r gline; do
    [ -z "$gline" ] && continue
    lineno="${gline%%:*}"
    match="${gline#*:}"
    case "$match" in
      !\[\[*) match="${match/#!\[\[/[[}" ;;
    esac
    printf '%s\t%s\t%s\n' "$f" "$lineno" "$match"
  done >> "$_links" || true
done < <(find "$PARENT" -type f -name '*.md' ! -path '*/.obsidian/*' -print0 2>/dev/null) || true
LC_ALL=C sort -u -o "$_links" "$_links" 2>/dev/null || true

_count_for_basename() {
  local t="$1"
  awk -F '\t' -v t="$t" '$1 == t { c++ } END { print c+0 }' "$_idx"
}

_paths_for_basename() {
  local t="$1"
  awk -F '\t' -v t="$t" '$1 == t { print $2 }' "$_idx"
}

_resolve_target() {
  local raw="$1"
  local t="${raw%%|*}"
  t="${t%%#*}"
  t=$(printf '%s' "$t" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  [ -z "$t" ] && return 1

  if printf '%s' "$t" | grep -q /; then
    local rel="${t%.md}.md"
    [[ "$rel" == *.md ]] || rel="${t}.md"
    if [ -f "$PARENT/$rel" ]; then
      return 0
    fi
    if [ -f "$PARENT/${t}.md" ]; then
      return 0
    fi
    local base
    base=$(basename "$t" .md)
    local n
    n=$(_count_for_basename "$base")
    if [ "$n" -ge 1 ]; then
      return 0
    fi
    return 1
  fi

  local n
  n=$(_count_for_basename "$t")
  [ "$n" -ge 1 ] && return 0
  return 1
}

orphans=0
uniq_amb=0

{
  printf '# Wikilink validation (phase57)\n\n'
  printf '_Targets are checked against existing `.md` files under this tree (excluding `.obsidian/`)._\n\n'
  printf '**Brain root:** `%s`\n\n' "$PARENT"
  printf '## Orphan [[wikilinks]] (no matching note)\n\n'
} > "$_report"

while IFS=$'\t' read -r file line match || [ -n "${file:-}" ]; do
  [ -z "${file:-}" ] && continue
  inner="${match#[[}"
  inner="${inner%]]}"
  raw="$inner"
  target="${raw%%|*}"
  target="${target%%#*}"
  target=$(printf '%s' "$target" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  [ -z "$target" ] && continue

  if _resolve_target "$raw"; then
    :
  else
    orphans=$((orphans + 1))
    printf '%s\n' "- \`$file\` line $line — \`[[$inner]]\` — no matching \`$target.md\`" >> "$_report"
    forge_scan_log_warn "orphan_link file=$file line=$line target=$target"
  fi
done < "$_links"

if [ "$orphans" -eq 0 ]; then
  printf '_None found._\n\n' >> "$_report"
fi

{
  printf '\n## Ambiguous basenames (same note name in multiple folders)\n\n'
  printf '_Obsidian may pick an arbitrary match; prefer unique slugs (e.g. \`ROLE-dir-sub\`)._\n\n'
} >> "$_report"

awk -F '\t' '
  { c[$1]++ }
  END { for (b in c) if (c[b] > 1) print b "\t" c[b] }
' "$_idx" | LC_ALL=C sort > "$_cut_ambig" || true

if [ -s "$_cut_ambig" ]; then
  while IFS="$(printf '\t')" read -r b cnt || [ -n "${b:-}" ]; do
    [ -z "${b:-}" ] && continue
    printf '### `%s` (%s files)\n\n' "$b" "$cnt"
    _paths_for_basename "$b" | while IFS= read -r p; do
      [ -z "$p" ] && continue
      printf -- '- `%s`\n' "$p"
    done
    printf '\n'
  done < "$_cut_ambig" >> "$_report"
  uniq_amb=$(wc -l < "$_cut_ambig" | tr -d ' ')
  forge_scan_log_stat "phase=5.7 ambiguous_basename_groups=$uniq_amb"
else
  printf '_None._\n\n' >> "$_report"
fi

{
  printf '\n## How to fix orphans\n\n'
  printf '1. **Re-run scan** after slug fixes: `phase4` + `phase56` use the same directory slug; mismatched \`ROLE\` vs repo folder basename breaks module filenames.\n'
  printf '2. **Rename or add** the missing note so the basename matches the link text before \`|` or `#`.\n'
  printf '3. **Remove or replace** stale hand-written \`[[...]]\` in stubs after refactors.\n'
} >> "$_report"

if [ "$WRITE" -eq 1 ]; then
  cp "$_report" "$PARENT/wikilink-orphan-report.md"
  forge_scan_log_stat "phase=5.7 orphans=$orphans report=$PARENT/wikilink-orphan-report.md"
  printf 'Wrote %s\n' "$PARENT/wikilink-orphan-report.md"
else
  forge_scan_log_stat "phase=5.7 orphans=$orphans (stdout only; pass --write-report for markdown file)"
  cat "$_report"
fi

forge_scan_log_done "orphans=$orphans ambiguous_basename_groups=$uniq_amb"

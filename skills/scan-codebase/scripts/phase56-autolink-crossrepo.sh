#!/usr/bin/env bash
# Forge scan-codebase: Phase 5.6 — Auto-fill cross-repo Calls / Called By on module stubs
#
# Usage: bash .../phase56-autolink-crossrepo.sh <BRAIN_CODEBASE_PARENT>
#
# Example:
#   bash phase56-autolink-crossrepo.sh "$HOME/forge/brain/products/jh/codebase"
#
# Expects /tmp/forge_scan_all_callsites.txt and /tmp/forge_scan_api_routes.txt
# (phase5-cross-repo + phase35 with append for all route repos).
#
# Heuristic substring match on URL paths — no LLM. Re-run safe (idempotent blocks).

set -euo pipefail
shopt -s nullglob

_fs_scripts=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC1091
. "$_fs_scripts/_forge-scan-log.sh"

_raw_parent="${1:?Usage: $0 <brain_codebase_parent e.g. \$HOME/forge/brain/products/slug/codebase>}"
PARENT="${_raw_parent/#\~/$HOME}"

if [ ! -d "$PARENT" ]; then
  forge_scan_log_die "brain_parent_not_a_directory path=$PARENT" 1
fi

forge_scan_log_start phase56-autolink-crossrepo "brain_parent=$PARENT"

if [ ! -s /tmp/forge_scan_all_callsites.txt ]; then
  forge_scan_log_warn "skip empty_or_missing /tmp/forge_scan_all_callsites.txt"
  forge_scan_log_done "edges=0"
  exit 0
fi
if [ ! -s /tmp/forge_scan_api_routes.txt ]; then
  forge_scan_log_warn "skip empty_or_missing /tmp/forge_scan_api_routes.txt"
  forge_scan_log_done "edges=0"
  exit 0
fi

BEGIN_OUT='<!-- FORGE:AUTO_CROSS_REPO_OUT -->'
END_OUT='<!-- FORGE:AUTO_CROSS_REPO_OUT_END -->'
BEGIN_IN='<!-- FORGE:AUTO_CROSS_REPO_IN -->'
END_IN='<!-- FORGE:AUTO_CROSS_REPO_IN_END -->'

_key() {
  printf '%s' "$1" | cksum | awk '{print $1}'
}

_strip_auto() {
  local f="$1"
  sed -i \
    -e "\|${BEGIN_OUT}|,|${END_OUT}|d" \
    -e "\|${BEGIN_IN}|,|${END_IN}|d" \
    "$f" 2>/dev/null || true
}

while IFS= read -r -d '' modf; do
  _strip_auto "$modf"
done < <(find "$PARENT" -type f -path '*/modules/*.md' -print0 2>/dev/null)

_mod_slug_from_rel() {
  local repo="$1"
  local rel="$2"
  local d
  d=$(dirname "$rel")
  [ "$d" = "." ] && d="root"
  local slug
  slug=$(printf '%s' "$d" | tr '/' '-' | sed 's/^-//;s/-$//')
  printf '%s' "${repo}-${slug}"
}

_resolve_module_file() {
  local repo="$1"
  local rel="$2"
  local slug
  slug=$(_mod_slug_from_rel "$repo" "$rel")
  local f="$PARENT/$repo/modules/$slug.md"
  if [ -f "$f" ]; then
    printf '%s' "$f"
    return 0
  fi
  return 1
}

_work=$(mktemp -d)
trap 'rm -rf "$_work"' EXIT

_edges=0
: > "$_work/edges.tsv"

while IFS= read -r raw || [ -n "${raw:-}" ]; do
  [ -z "${raw:-}" ] && continue
  repo="${raw%%	*}"
  rest="${raw#*	}"
  [ "$rest" = "$raw" ] && continue
  caller_rel="${rest%%:*}"
  rem="${rest#*:}"
  caller_line="${rem%%:*}"
  content="${rem#*:}"
  [ -z "$repo" ] || [ -z "$caller_rel" ] && continue

  _urls=$(printf '%s' "$content" | grep -oE '/api[^"'\'')\`[:space:]]{1,220}|/v[0-9]+[^"'\'')\`[:space:]]{1,220}|/graphql[^"'\'')\`[:space:]]{1,220}|/rest[^"'\'')\`[:space:]]{1,220}' | sort -u || true)
  [ -z "$_urls" ] && continue

  while IFS= read -r url || [ -n "${url:-}" ]; do
    [ -z "${url:-}" ] && continue
    _u=$(printf '%s' "$url" | sed 's/[?#].*$//')
    hit=$(grep -F "$_u" /tmp/forge_scan_api_routes.txt 2>/dev/null | head -1 || true)
    [ -z "$hit" ] && continue

    be_repo="${hit%%	*}"
    be_rest="${hit#*	}"
    be_rel="${be_rest%%:*}"
    rem2="${be_rest#*:}"
    be_lineno="${rem2%%:*}"

    caller_mod=$(_resolve_module_file "$repo" "$caller_rel") || continue
    be_mod=$(_resolve_module_file "$be_repo" "$be_rel") || continue
    [ "$caller_mod" = "$be_mod" ] && continue

    caller_slug=$(basename "$caller_mod" .md)
    be_slug=$(basename "$be_mod" .md)

    b_call="- \`${_u}\` → [[${be_slug}]] (\`${be_repo}/${be_rel}:${be_lineno}\`)"
    b_by="- [[${caller_slug}]] (\`${repo}/${caller_rel}:${caller_line}\`) uses \`${_u}\`"

    ck=$(_key "$caller_mod")
    printf '%s\n' "$b_call" >> "$_work/calls-$ck"
    printf '%s\n' "$caller_mod" > "$_work/calls-$ck.path"

    bk=$(_key "$be_mod")
    printf '%s\n' "$b_by" >> "$_work/by-$bk"
    printf '%s\n' "$be_mod" > "$_work/by-$bk.path"

    printf '%s\t%s\t%s\t%s\n' "$repo" "$caller_rel" "$be_repo" "$_u" >> "$_work/edges.tsv"
    _edges=$((_edges + 1))
  done <<< "$_urls"
done < /tmp/forge_scan_all_callsites.txt

_merge_block() {
  local pathfile="$1"
  local title="$2"
  local datafile="$3"
  local bgn="$4"
  local edn="$5"
  [ ! -f "$pathfile" ] && return 0
  local target
  target=$(cat "$pathfile")
  [ ! -f "$target" ] && return 0
  [ ! -s "$datafile" ] && return 0
  {
    printf '%s\n' "$bgn"
    printf '%s\n\n' "### $title _(auto phase56 — verify)_"
    sort -u "$datafile"
    printf '\n%s\n' "$edn"
  } >> "$target"
}

for p in "$_work"/calls-*.path; do
  [ -f "$p" ] || continue
  h=${p%.path}
  [ -f "$h" ] || continue
  sort -u "$h" -o "$h.tmp" && mv "$h.tmp" "$h"
  _merge_block "$p" "Outgoing cross-repo (Calls)" "$h" "$BEGIN_OUT" "$END_OUT"
done

for p in "$_work"/by-*.path; do
  [ -f "$p" ] || continue
  h=${p%.path}
  [ -f "$h" ] || continue
  sort -u "$h" -o "$h.tmp" && mv "$h.tmp" "$h"
  _merge_block "$p" "Incoming cross-repo (Called by)" "$h" "$BEGIN_IN" "$END_IN"
done

if [ -s "$_work/edges.tsv" ]; then
  {
    printf '%s\n' "# Cross-repo automap (phase56)"
    printf '%s\n\n' "_Heuristic grep join — verify against contracts._"
    printf '%s\n' '```tsv'
    sort -u "$_work/edges.tsv"
    printf '%s\n' '```'
  } > "$PARENT/cross-repo-automap.md"
fi

_touched=$( { grep -rlF "$BEGIN_OUT" "$PARENT" 2>/dev/null; grep -rlF "$BEGIN_IN" "$PARENT" 2>/dev/null; } | sort -u | wc -l)
echo "Phase 5.6: auto-linked cross-repo blocks (OUT/IN markers). Edges=$_edges module_files≈$_touched"
forge_scan_log_stat "phase=5.6 edges=$_edges modules_with_out_block=$_touched"
forge_scan_log_done "edges=$_edges automap=$([ -f "$PARENT/cross-repo-automap.md" ] && echo yes || echo no)"

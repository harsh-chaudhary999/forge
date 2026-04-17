#!/usr/bin/env bash
# Warn when product.md "role:" does not match basename(repo path). Phase 4 / phase56
# use role for module filenames and basename "$repo" for call-site prefixes — they must align.
#
# Usage: bash .../validate-product-roles.sh <path/to/product.md>
# Exit: 0 always (warnings only). Set FORGE_VALIDATE_PRODUCT_STRICT=1 to exit 1 on mismatch.
#
set -euo pipefail

PRODUCT="${1:?Usage: $0 <path/to/product.md>}"
[ -f "$PRODUCT" ] || {
  echo "validate-product-roles: file not found: $PRODUCT" >&2
  exit 1
}

_fs_scripts=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_forge-scan-log.sh
. "$_fs_scripts/_forge-scan-log.sh"
FORGE_SCAN_SCRIPT_ID=validate-product-roles
forge_scan_log_start "product=$PRODUCT"

_mismatches=0
_incomplete=0
_pending_repo=""
_pending_role=""

_expand_repo_line() {
  local p="$1"
  p="${p#- repo:}"
  p="${p#- repo :}"
  p="${p#"${p%%[![:space:]]*}"}"
  p="${p%"${p##*[![:space:]]}"}"
  p="${p/#\~/$HOME}"
  printf '%s' "$p"
}

_expand_role_line() {
  local r="$1"
  r="${r#- role:}"
  r="${r#- role :}"
  r="${r#"${r%%[![:space:]]*}"}"
  r="${r%"${r##*[![:space:]]}"}"
  printf '%s' "$r"
}

_check_pair() {
  [ -z "$_pending_repo" ] && return 0
  [ -z "$_pending_role" ] && return 0
  local base
  base=$(basename "$_pending_repo")
  if [ "$base" != "$_pending_role" ]; then
    forge_scan_log_warn "role_repo_basename_mismatch role=$_pending_role repo_basename=$base path=$_pending_repo hint=rename_folder_or_set_role_to_match_basename_for_phase4_phase56"
    echo "validate-product-roles: WARN — role '$_pending_role' ≠ repo basename '$base' (repo: $_pending_repo)" >&2
    _mismatches=$((_mismatches + 1))
  fi
  _pending_repo=""
  _pending_role=""
}

_new_project_block() {
  if [ -n "$_pending_repo" ] && [ -z "$_pending_role" ]; then
    echo "validate-product-roles: WARN — project has repo but no role before next heading: $_pending_repo" >&2
    forge_scan_log_warn "incomplete_project_block repo=$_pending_repo missing_role_line"
    _incomplete=$((_incomplete + 1))
  fi
  _pending_repo=""
  _pending_role=""
}

_in_projects=0
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    '## Projects'|'## Projects '*)
      _new_project_block
      _in_projects=1
      continue
      ;;
    '## '*)
      if [ "$_in_projects" -eq 1 ]; then
        _new_project_block
        _in_projects=0
      fi
      continue
      ;;
  esac
  [ "$_in_projects" -eq 0 ] && continue

  case "$line" in
    '### '*)
      _new_project_block
      ;;
    '- repo:'*|'- repo :'*)
      _pending_repo="$(_expand_repo_line "$line")"
      ;;
    '- role:'*|'- role :'*)
      _pending_role="$(_expand_role_line "$line")"
      _check_pair
      ;;
  esac
done < "$PRODUCT"

_new_project_block

if [ "$_mismatches" -eq 0 ] && [ "$_incomplete" -eq 0 ]; then
  forge_scan_log_stat "phase=validate-product-roles mismatches=0 incomplete=0"
  forge_scan_log_done "ok"
else
  forge_scan_log_stat "phase=validate-product-roles mismatches=$_mismatches incomplete=$_incomplete"
  forge_scan_log_done "mismatches=$_mismatches incomplete=$_incomplete"
  if [ "${FORGE_VALIDATE_PRODUCT_STRICT:-0}" = 1 ] && [ "$_mismatches" -gt 0 ]; then
    exit 1
  fi
fi

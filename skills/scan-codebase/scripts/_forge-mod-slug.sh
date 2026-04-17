#!/usr/bin/env bash
# Shared module filename slug logic for phase4-brain-write and phase56-autolink-crossrepo.
# Source from the same directory as the caller:
#   _fs_scripts=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
#   # shellcheck source=_forge-mod-slug.sh
#   . "$_fs_scripts/_forge-mod-slug.sh"
#
# Contract: module node basename (no .md) = "<role>-<dirslug>"
#   <dirslug> = unique source directory relative to repo root, '/' → '-', '.' → 'root'

# Args: directory path relative to repo (e.g. src/api or .)
# Prints: dirslug (e.g. src-api or root)
forge_mod_dirslug_from_dir() {
  local d="$1"
  [ -z "$d" ] && return 1
  [ "$d" = "." ] && d="root"
  printf '%s' "$d" | tr '/' '-' | sed 's/^-//;s/-$//'
}

# Args: <repo_role> <path_relative_to_repo> (e.g. backend src/api/foo.ts)
# Prints: module node basename without .md (e.g. backend-src-api)
forge_mod_node_basename_from_rel() {
  local role="$1"
  local rel="$2"
  local d
  d=$(dirname "$rel")
  printf '%s-%s' "$role" "$(forge_mod_dirslug_from_dir "$d")"
}

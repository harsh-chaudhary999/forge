#!/usr/bin/env bash
# Print the number of skills (SKILL.md files under skills/). Run from any cwd.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
shopt -s nullglob
paths=("$ROOT"/skills/*/SKILL.md)
echo "${#paths[@]}"

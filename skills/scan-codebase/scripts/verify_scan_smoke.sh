#!/usr/bin/env bash
# Smoke-test scan-codebase scripts + tools/forge_scan_run.py on bundled fixtures.
set -euo pipefail

if [ -z "${BASH_VERSION:-}" ]; then
  echo "requires bash" >&2
  exit 127
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RUN_DIR="$(mktemp -d "${TMPDIR:-/tmp}/forge_scan_smoke.XXXXXX")"
BRAIN="$(mktemp -d "${TMPDIR:-/tmp}/forge_scan_smoke_brain.XXXXXX")"
trap 'rm -rf "$RUN_DIR" "$BRAIN"' EXIT

python3 "$ROOT/tools/forge_scan_run.py" \
  --run-dir "$RUN_DIR" \
  --brain-codebase "$BRAIN" \
  --skip-phase57 \
  --repos \
  "backend:$ROOT/skills/scan-codebase/fixtures/smoke/backend" \
  "web:$ROOT/skills/scan-codebase/fixtures/smoke/web"

python3 <<PY
import json, pathlib, sys
p = pathlib.Path(r"""$RUN_DIR""") / "run.json"
meta = json.loads(p.read_text(encoding="utf-8"))
assert meta.get("status") == "ok", meta
routes = p.parent / "forge_scan_api_routes.txt"
text = routes.read_text(encoding="utf-8", errors="replace")
assert "/api/hello" in text, routes
PY

echo "verify_scan_smoke: OK"

#!/usr/bin/env python3
"""
Append one phase-ledger.jsonl row (SHA256 attestation for listed artifacts).

Editor-agnostic — run from any shell after materializing files under prds/<task-id>/.

Example:
  python3 tools/append_phase_ledger.py \\
    --brain ~/forge/brain --task-id add-2fa \\
    --phase '[P4.0-EVAL-YAML]' \\
    --artifacts eval/smoke.yaml,eval/api.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from phase_ledger import append_entry, build_entry  # noqa: E402
from forge_paths import default_brain_root, sanitize_task_id  # noqa: E402

_PHASE_RE = re.compile(r"^\[P\d(?:\.\d+)?(?:-[^\]]+)?\]$")


def main() -> int:
    p = argparse.ArgumentParser(description="Append phase-ledger.jsonl entry with artifact SHA256.")
    p.add_argument(
        "--brain",
        default=None,
        help="Brain root (default $FORGE_BRAIN or $FORGE_BRAIN_PATH or ~/forge/brain)",
    )
    p.add_argument("--task-id", required=True)
    p.add_argument("--phase", required=True, help='Phase marker text, e.g. "[P4.0-EVAL-YAML]"')
    p.add_argument(
        "--artifacts",
        default="",
        help="Comma-separated paths relative to prds/<task-id>/ (e.g. eval/smoke.yaml)",
    )
    p.add_argument(
        "--artifact",
        action="append",
        default=[],
        help="Single artifact relpath; may be repeated. Preferred over comma-separated --artifacts.",
    )
    p.add_argument("--note", default=None)
    args = p.parse_args()

    brain = Path(args.brain).expanduser() if args.brain else default_brain_root()
    try:
        task_id = sanitize_task_id(args.task_id)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if not _PHASE_RE.match(args.phase.strip()):
        print(f"ERROR: --phase must look like [P4.0-EVAL-YAML], got {args.phase!r}", file=sys.stderr)
        return 1
    task_dir = brain / "prds" / task_id
    if not task_dir.is_dir():
        print(f"ERROR: task dir missing: {task_dir}", file=sys.stderr)
        return 1

    rels = [x.strip() for x in str(args.artifacts).split(",") if x.strip()]
    rels.extend([x.strip() for x in args.artifact if str(x).strip()])
    try:
        entry = build_entry(task_id, args.phase, rels, task_dir, note=args.note)
        out = append_entry(task_dir, entry)
    except (OSError, ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: appended to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

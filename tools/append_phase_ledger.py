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
import os
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from phase_ledger import append_entry, build_entry  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Append phase-ledger.jsonl entry with artifact SHA256.")
    p.add_argument("--brain", default=None, help="Brain root (default $FORGE_BRAIN or ~/forge/brain)")
    p.add_argument("--task-id", required=True)
    p.add_argument("--phase", required=True, help='Phase marker text, e.g. "[P4.0-EVAL-YAML]"')
    p.add_argument(
        "--artifacts",
        default="",
        help="Comma-separated paths relative to prds/<task-id>/ (e.g. eval/smoke.yaml)",
    )
    p.add_argument("--note", default=None)
    args = p.parse_args()

    home = Path.home()
    brain = (
        Path(args.brain).expanduser()
        if args.brain
        else Path(os.environ.get("FORGE_BRAIN", str(home / "forge" / "brain"))).expanduser()
    )
    task_dir = brain / "prds" / args.task_id
    if not task_dir.is_dir():
        print(f"ERROR: task dir missing: {task_dir}", file=sys.stderr)
        return 1

    rels = [x.strip() for x in str(args.artifacts).split(",") if x.strip()]
    try:
        entry = build_entry(args.task_id, args.phase, rels, task_dir, note=args.note)
        out = append_entry(task_dir, entry)
    except (OSError, ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: appended to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

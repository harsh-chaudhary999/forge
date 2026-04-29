#!/usr/bin/env python3
"""Pack a task directory from the Forge brain into a tar.gz + manifest (audit / handoff).

Usage:
  python3 tools/forge_evidence_bundle.py --task-id TASK --brain ~/forge/brain [--out PATH] [--full]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path as P


def git_rev(repo: P) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description="Forge brain task evidence bundle")
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--brain", type=P, default=P.home() / "forge" / "brain")
    ap.add_argument("--out", type=P, default=None)
    ap.add_argument(
        "--full",
        action="store_true",
        help="Include entire prds/<task-id>/ tree (default: key paths only)",
    )
    args = ap.parse_args()

    brain: P = args.brain.expanduser().resolve()
    task_dir = brain / "prds" / args.task_id
    if not task_dir.is_dir():
        print(f"ERROR: {task_dir} not found", file=sys.stderr)
        return 1

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    out_gz = args.out
    if out_gz is None:
        out_gz = P.cwd() / f"forge-evidence-{args.task_id}-{ts}.tar.gz"
    else:
        out_gz = out_gz.expanduser().resolve()

    if args.full:
        paths = sorted([p for p in task_dir.rglob("*") if p.is_file()])
    else:
        rels = [
            "prd-locked.md",
            "shared-dev-spec.md",
            "conductor.log",
            "qa-pipeline.log",
        ]
        paths = []
        for r in rels:
            p = task_dir / r
            if p.is_file():
                paths.append(p)
        for sub in ("tech-plans", "eval", "qa"):
            d = task_dir / sub
            if d.is_dir():
                paths.extend(sorted(f for f in d.rglob("*") if f.is_file()))
        qa = task_dir / "qa"
        if qa.is_dir():
            reports = sorted(qa.glob("qa-run-report-*.md"))
            if reports:
                paths.append(reports[-1])

    paths = sorted(set(paths), key=lambda p: str(p))
    manifest_files = []

    with tarfile.open(out_gz, "w:gz") as tf:
        for p in paths:
            try:
                arc = p.relative_to(brain)
            except ValueError:
                continue
            tf.add(p, arcname=str(arc), recursive=False)
            rel = str(arc)
            h = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else ""
            manifest_files.append({"path": rel, "sha256": h})

    manifest = {
        "task_id": args.task_id,
        "brain_git_rev": git_rev(brain),
        "created_utc": ts,
        "bundle": str(out_gz.name),
        "full_tree": args.full,
        "files": manifest_files,
    }
    base = (
        out_gz.name.removesuffix(".tar.gz")
        if out_gz.name.endswith(".tar.gz")
        else out_gz.stem
    )
    man_path = out_gz.parent / f"{base}.manifest.json"
    man_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {out_gz}")
    print(f"Wrote {man_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

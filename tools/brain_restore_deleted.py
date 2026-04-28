#!/usr/bin/env python3
"""
Restore tracked files that are missing from the working tree but still in the index.

Use when ``git status`` shows many `` D`` lines (deleted on disk, not staged as removal).
This runs ``git ls-files -d`` then ``git restore`` in batches — stdlib only.

Does **not** undo a committed deletion; use ``git checkout`` / ``git restore`` from a
revision for that. Does **not** drop staged changes to modified files.

Examples::

  python3 tools/brain_restore_deleted.py --brain ~/forge/brain
  python3 tools/brain_restore_deleted.py --brain ~/forge/brain --dry-run
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from forge_paths import default_brain_root


def _git_ls_files_deleted(repo: Path) -> list[str]:
    r = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-d", "-z"],
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"git ls-files failed (exit {r.returncode}): {r.stderr.strip() or r.stdout}"
        )
    if not r.stdout:
        return []
    return [p for p in r.stdout.split("\0") if p]


def _git_restore(repo: Path, paths: list[str], *, dry_run: bool) -> None:
    if not paths:
        return
    if dry_run:
        for p in paths:
            print(f"would restore: {p}")
        return
    # Avoid argv limits on huge trees
    batch = 400
    for i in range(0, len(paths), batch):
        chunk = paths[i : i + batch]
        subprocess.run(
            ["git", "-C", str(repo), "restore", "--", *chunk],
            check=True,
        )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Restore tracked files missing from disk (git ls-files -d)."
    )
    ap.add_argument(
        "--brain",
        default=None,
        help="Brain git root (default: $FORGE_BRAIN or $FORGE_BRAIN_PATH or ~/forge/brain)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print paths that would be restored; do not run git restore",
    )
    args = ap.parse_args()

    brain = (
        Path(args.brain).expanduser().resolve()
        if args.brain
        else default_brain_root().resolve()
    )
    if not (brain / ".git").is_dir() and not (brain / ".git").is_file():
        print(f"ERROR: not a git repository: {brain}", file=sys.stderr)
        return 1

    try:
        deleted = _git_ls_files_deleted(brain)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if not deleted:
        print(f"OK: no deleted tracked files under {brain}")
        return 0

    print(
        f"Restoring {len(deleted)} path(s) from index into working tree under {brain}"
        + (" (dry-run)" if args.dry_run else "")
        + "…",
        file=sys.stderr,
    )
    _git_restore(brain, deleted, dry_run=args.dry_run)
    if args.dry_run:
        print(f"OK: dry-run only; {len(deleted)} path(s) would be restored")
    else:
        print(f"OK: restored {len(deleted)} path(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

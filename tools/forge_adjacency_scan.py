#!/usr/bin/env python3
"""Append discovery-adjacency.md for a task — org-defined rg patterns only (see adjacency-seed-patterns.txt).

Implemented in Python to match other Forge utilities under tools/ (e.g. verify_scan_outputs.py).
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

_FOOTER = (
    "_End scan. Triage per `docs/adjacency-and-cohorts.md` "
    "(tables in `docs/templates/adjacency-cohort-and-signals.template.md`)._"
)


def load_patterns(path: Path) -> list[str]:
    if not path.is_file():
        return []
    out: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    return out


def run_rg(repo: Path, pattern: str, limit: int = 80) -> tuple[list[str], bool, str | None]:
    """Return (lines, truncated, error). error set on rg failure."""
    cmd = [
        "rg",
        "-n",
        "--hidden",
        "--glob",
        "!.git",
        "-e",
        pattern,
        str(repo),
    ]
    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return [], False, str(e)
    if p.returncode not in (0, 1):
        return [], False, (p.stderr or p.stdout or f"exit {p.returncode}")[:500]
    all_lines = (p.stdout or "").splitlines()
    lines = all_lines[:limit]
    return lines, len(all_lines) > limit, None


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Write discovery-adjacency.md for a Forge brain task.",
        epilog="Example: python3 tools/forge_adjacency_scan.py ~/forge/brain/prds/my-task ~/src/api ~/src/web",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("task_dir", type=Path, help="e.g. ~/forge/brain/prds/<task-id>")
    ap.add_argument("repos", nargs="+", type=Path, help="One or more product repo roots to search")
    ap.add_argument(
        "--patterns",
        type=Path,
        default=None,
        help="Newline-separated rg -e patterns (default: tools/adjacency-seed-patterns.txt)",
    )
    ap.add_argument(
        "--replace",
        action="store_true",
        help="Overwrite discovery-adjacency.md instead of appending.",
    )
    args = ap.parse_args()

    tools_dir = Path(__file__).resolve().parent
    patterns_path = (
        args.patterns.expanduser().resolve()
        if args.patterns
        else (tools_dir / "adjacency-seed-patterns.txt").resolve()
    )
    task_dir: Path = args.task_dir.expanduser().resolve()
    task_dir.mkdir(parents=True, exist_ok=True)
    out_path = task_dir / "discovery-adjacency.md"
    patterns = load_patterns(patterns_path)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    chunks: list[str] = [
        "## Adjacency seed scan",
        "",
        f"**Generated:** {ts} (`python3 tools/forge_adjacency_scan.py`)",
        "",
    ]

    if not patterns:
        chunks.append(
            "_No active patterns (all lines commented or empty in the patterns file)._"
        )
        chunks.append(_FOOTER)
        chunks.append("")
    elif not shutil.which("rg"):
        chunks.append(
            "_`rg` (ripgrep) not in PATH — install ripgrep or log `[ADJACENCY-SCAN] … SKIPPED reason=rg_absent` and run an agent-led search pass._"
        )
        chunks.append(_FOOTER)
        chunks.append("")
    else:
        for repo in args.repos:
            repo = repo.expanduser().resolve()
            chunks.append(f"### Repo: `{repo}`")
            chunks.append("")
            if not repo.is_dir():
                chunks.append("_Directory not found — skipped._")
                chunks.append("")
                continue
            for pat in patterns:
                safe = pat.replace("`", "")
                chunks.append(f"#### Pattern: `{safe}`")
                lines, truncated, err = run_rg(repo, pat)
                if err:
                    chunks.append(f"_rg error: {err}_")
                elif not lines:
                    chunks.append("_No matches._")
                else:
                    chunks.extend(f"- {line}" for line in lines)
                    if truncated:
                        chunks.append("- # TRUNCATED (limit=80)")
                chunks.append("")

        chunks.append(_FOOTER)
        chunks.append("")

    if args.replace or not out_path.is_file():
        out_path.write_text("\n".join(chunks), encoding="utf-8")
    else:
        existing = out_path.read_text(encoding="utf-8", errors="replace")
        out_path.write_text(existing + "\n" + "\n".join(chunks), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

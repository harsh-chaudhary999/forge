"""Consolidated brain `codebase/` integrity checks (used by CLI + ``verify_scan_outputs.py``)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "SCAN.json",
    "SCAN_SUMMARY.md",
    "graph.json",
    ".forge_scan_manifest.json",
    "index.md",
)


def _source_file_total(data: object) -> int:
    if not isinstance(data, dict):
        return 0
    n = data.get("source_files")
    if isinstance(n, int):
        return n
    repos = data.get("repos")
    if isinstance(repos, dict):
        t = 0
        for v in repos.values():
            if isinstance(v, dict) and isinstance(v.get("source_files"), int):
                t += int(v["source_files"])
        return t
    return 0


def verify_brain_codebase_once(root: Path) -> tuple[int, list[str]]:
    """
    Return (exit_code, lines).

    ``0`` = OK. ``1`` = integrity failure. ``2`` = bad args / not a directory.
    """
    msgs: list[str] = []
    root = root.resolve()
    if not root.is_dir():
        msgs.append(f"error: not a directory: {root}")
        return 2, msgs

    missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
    if missing:
        msgs.append(f"verify_brain_codebase: FAIL {root}")
        for m in missing:
            msgs.append(f"  missing file: {m}")
        return 1, msgs

    scan_path = root / "SCAN.json"
    try:
        data = json.loads(scan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        msgs.append(f"verify_brain_codebase: FAIL {root} SCAN.json unreadable: {e}")
        return 1, msgs

    src_total = _source_file_total(data)
    modules = root / "modules"
    md_count = 0
    if modules.is_dir():
        md_count = sum(1 for p in modules.iterdir() if p.suffix.lower() == ".md")
    if src_total > 0 and md_count == 0:
        msgs.append(f"verify_brain_codebase: FAIL {root}")
        msgs.append(f"  SCAN.json reports source_files≈{src_total} but modules/*.md count=0")
        return 1, msgs

    msgs.append(f"verify_brain_codebase: OK {root} (modules *.md: {md_count})")
    return 0, msgs


def verify_brain_codebase_with_retries(
    root: Path,
    *,
    attempts: int = 3,
    delay_s: float = 0.35,
) -> tuple[int, list[str]]:
    """
    Re-run verify after short delays (local FS / NFS eventual consistency).

    ``attempts`` must be >= 1. On first success, returns immediately.
    """
    attempts = max(1, int(attempts))
    last_code = 1
    all_msgs: list[str] = []
    for i in range(attempts):
        code, lines = verify_brain_codebase_once(root)
        all_msgs = lines
        last_code = code
        if code == 0:
            if i > 0:
                all_msgs = [f"verify_brain_codebase: OK after attempt {i + 1}/{attempts}"] + lines[1:]
            return 0, all_msgs
        if i + 1 < attempts:
            time.sleep(delay_s)
    return last_code, all_msgs


__all__ = [
    "REQUIRED_FILES",
    "verify_brain_codebase_once",
    "verify_brain_codebase_with_retries",
]

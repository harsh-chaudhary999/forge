"""Merge per-repo scan metadata into brain `codebase/SCAN.json`."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _line_count(path: Path) -> int:
    if not path.is_file():
        return 0
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    if not text.strip():
        return 0
    return len(text.splitlines())


def _git_short_sha(repo: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or "unknown"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _migrate_legacy(doc: dict[str, Any]) -> dict[str, Any]:
    """Old flat SCAN.json had role/source_files at top level."""
    if isinstance(doc.get("repos"), dict):
        return doc
    role = doc.get("role")
    if isinstance(role, str) and role.strip():
        nested = {k: v for k, v in doc.items() if k not in ("repos", "orchestrator")}
        return {"repos": {role: nested}}
    if not doc:
        return {"repos": {}}
    return {"repos": {}, **doc}


def merge_scan_json(brain_dir: Path, repo: Path, role: str, scan_tmp: Path) -> None:
    """Update ``brain_dir/SCAN.json`` with stats for this repo role."""
    brain_dir = brain_dir.resolve()
    repo = repo.resolve()
    scan_tmp = scan_tmp.resolve()
    path = brain_dir / "SCAN.json"

    doc: dict[str, Any] = {}
    if path.is_file():
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            doc = {}
    doc = _migrate_legacy(doc)
    repos = doc.get("repos")
    if not isinstance(repos, dict):
        repos = {}

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _read_int_file(path: Path) -> int:
        if not path.is_file():
            return 0
        try:
            return int(path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return 0

    filtered_methods = scan_tmp / "forge_scan_methods_filtered.txt"
    methods_in_inventory = (
        _line_count(filtered_methods) if filtered_methods.is_file() else _line_count(scan_tmp / "forge_scan_methods_all.txt")
    )
    methods_skipped = _read_int_file(scan_tmp / "forge_scan_methods_skipped.txt")

    entry = {
        "repo_path": str(repo),
        "role": role,
        "commit": _git_short_sha(repo),
        "scanned_at": now,
        "source_files": _line_count(scan_tmp / "forge_scan_source_files.txt"),
        "test_files": _line_count(scan_tmp / "forge_scan_test_files.txt"),
        "tier1_hubs": _line_count(scan_tmp / "forge_scan_tier1.txt"),
        "tier2_hubs": _line_count(scan_tmp / "forge_scan_tier2.txt"),
        "types_in_inventory": _line_count(scan_tmp / "forge_scan_types_all.txt"),
        "methods_in_inventory": methods_in_inventory,
        "methods_skipped_low_signal": methods_skipped,
        "functions_in_inventory": _line_count(scan_tmp / "forge_scan_functions_all.txt"),
        "ui_files_in_inventory": _line_count(scan_tmp / "forge_scan_ui_all.txt"),
    }
    repos[role] = entry

    def _sum_field(key: str) -> int:
        total = 0
        for v in repos.values():
            if isinstance(v, dict) and key in v:
                try:
                    total += int(v[key])
                except (TypeError, ValueError):
                    pass
        return total

    out: dict[str, Any] = {
        "scanned_at": now,
        "orchestrator": "scan_forge",
        "repos": repos,
    }
    # Flat compatibility: council / commands grep top-level scanned_at, totals
    out["commit"] = entry["commit"]
    out["source_files"] = _sum_field("source_files")
    out["test_files"] = _sum_field("test_files")
    out["tier1_hubs"] = _sum_field("tier1_hubs")
    out["tier2_hubs"] = _sum_field("tier2_hubs")
    out["types_in_inventory"] = _sum_field("types_in_inventory")
    out["methods_in_inventory"] = _sum_field("methods_in_inventory")
    out["methods_skipped_low_signal"] = _sum_field("methods_skipped_low_signal")
    out["functions_in_inventory"] = _sum_field("functions_in_inventory")
    out["ui_files_in_inventory"] = _sum_field("ui_files_in_inventory")
    out["role"] = role
    out["repo"] = str(repo)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

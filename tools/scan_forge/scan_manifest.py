"""Record last-scan repo fingerprints under ``brain_codebase``."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import log


def _git_tree_and_head(repo: Path) -> tuple[str, str]:
    try:
        tree = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        tree = "unknown"
    try:
        head = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        head = "unknown"
    return tree, head


def write_manifest(
    brain_codebase: Path,
    repos: list[tuple[str, Path]],
    *,
    incremental_enabled: bool = False,
    changed_by_role: dict[str, list[str]] | None = None,
) -> Path:
    os.environ["FORGE_SCAN_SCRIPT_ID"] = "scan_manifest"
    brain_codebase = brain_codebase.resolve()
    doc: dict[str, Any] = {
        "forge_scan_manifest_version": 2,
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "brain_codebase": str(brain_codebase),
        "incremental_enabled": bool(incremental_enabled),
        "repos": {},
    }
    changed_by_role = changed_by_role or {}
    for role, p in repos:
        p = p.resolve()
        tree, head = _git_tree_and_head(p)
        changed = sorted(set(changed_by_role.get(role, [])))
        doc["repos"][role] = {
            "path": str(p),
            "tree": tree,
            "head": head,
            "changed_paths_count": len(changed),
            "changed_paths_sample": changed[:50],
        }

    out = brain_codebase / ".forge_scan_manifest.json"
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", errors="replace")
    log.log_step(f"scan_manifest written path={out}")
    return out

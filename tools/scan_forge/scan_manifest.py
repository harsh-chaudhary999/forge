"""Record last-scan repo fingerprints under ``brain_codebase`` (tooling / future incremental)."""

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


def write_manifest(brain_codebase: Path, repos: list[tuple[str, Path]]) -> Path:
    os.environ["FORGE_SCAN_SCRIPT_ID"] = "scan_manifest"
    brain_codebase = brain_codebase.resolve()
    doc: dict[str, Any] = {
        "forge_scan_manifest_version": 1,
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "brain_codebase": str(brain_codebase),
        "repos": {},
    }
    for role, p in repos:
        p = p.resolve()
        tree, head = _git_tree_and_head(p)
        doc["repos"][role] = {"path": str(p), "tree": tree, "head": head}

    out = brain_codebase / ".forge_scan_manifest.json"
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", errors="replace")
    log.log_step(f"scan_manifest written path={out}")
    return out

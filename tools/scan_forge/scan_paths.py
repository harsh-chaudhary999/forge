"""Layout for multi-repo scan: per-role working dirs under a shared ``run_dir``."""

from __future__ import annotations

from pathlib import Path


def role_scan_dir(run_dir: Path, role: str) -> Path:
    """Directory for phase1 + phase35 (per-repo) artifacts — avoids last-repo-wins on inventory.

    Shared ``run_dir`` still holds merged ``forge_scan_api_routes.txt``, phase5 call files, etc.
    """
    d = (run_dir.resolve() / "_role" / role)
    d.mkdir(parents=True, exist_ok=True)
    return d

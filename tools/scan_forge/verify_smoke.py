#!/usr/bin/env python3
"""Smoke-test scan_forge on bundled fixtures (replaces verify_scan_smoke.sh)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    run_dir = Path(tempfile.mkdtemp(prefix="forge_scan_smoke."))
    brain = Path(tempfile.mkdtemp(prefix="forge_scan_smoke_brain."))
    try:
        cmd = [
            sys.executable,
            str(root / "tools" / "forge_scan_run.py"),
            "--run-dir",
            str(run_dir),
            "--brain-codebase",
            str(brain),
            "--skip-phase57",
            "--repos",
            f"backend:{root / 'skills/scan-codebase/fixtures/smoke/backend'}",
            f"web:{root / 'skills/scan-codebase/fixtures/smoke/web'}",
        ]
        subprocess.run(cmd, check=True, cwd=str(root))
        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        assert meta.get("status") == "ok", meta
        routes = run_dir / "forge_scan_api_routes.txt"
        text = routes.read_text(encoding="utf-8", errors="replace")
        assert "/api/hello" in text, routes
        scan_doc = json.loads((brain / "SCAN.json").read_text(encoding="utf-8"))
        repos = scan_doc.get("repos")
        assert isinstance(repos, dict) and "backend" in repos and "web" in repos, scan_doc
        assert scan_doc.get("source_files", 0) >= 2
    finally:
        import shutil

        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(brain, ignore_errors=True)
    print("verify_smoke: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

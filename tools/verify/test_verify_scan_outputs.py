#!/usr/bin/env python3
"""Tests for verify_scan_outputs.py CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
_SCRIPT = _TOOLS_DIR / "verify_scan_outputs.py"


class TestVerifyScanOutputsCli(unittest.TestCase):
    def _write_minimal_codebase(self, root: Path) -> None:
        root.mkdir(parents=True)
        (root / "SCAN.json").write_text(
            json.dumps({"source_files": 0}),
            encoding="utf-8",
        )
        (root / "SCAN_SUMMARY.md").write_text("# OK\n", encoding="utf-8")
        (root / "graph.json").write_text("{}", encoding="utf-8")
        (root / ".forge_scan_manifest.json").write_text("{}", encoding="utf-8")
        (root / "index.md").write_text("# Index\n", encoding="utf-8")
        (root / "modules").mkdir()

    def test_ok_minimal_scan_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "codebase"
            self._write_minimal_codebase(root)
            r = subprocess.run(
                [sys.executable, str(_SCRIPT), str(root)],
                capture_output=True,
                text=True,
                cwd=str(_TOOLS_DIR.parent.parent),
            )
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

    def test_missing_required_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "codebase"
            root.mkdir()
            (root / "SCAN.json").write_text("{}", encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(_SCRIPT), str(root)],
                capture_output=True,
                text=True,
                cwd=str(_TOOLS_DIR.parent.parent),
            )
            self.assertEqual(r.returncode, 1, r.stderr + r.stdout)


if __name__ == "__main__":
    unittest.main()

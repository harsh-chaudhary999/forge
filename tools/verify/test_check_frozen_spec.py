#!/usr/bin/env python3
"""CLI tests for check_frozen_spec.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
_SCRIPT = _TOOLS_DIR / "check_frozen_spec.py"


class TestCheckFrozenSpecCli(unittest.TestCase):
    def test_ok_when_no_tbd(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".md",
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write("# Spec\n\nAll done.\n")
            path = Path(f.name)
        try:
            r = subprocess.run(
                [sys.executable, str(_SCRIPT), str(path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        finally:
            path.unlink(missing_ok=True)

    def test_fail_on_todo(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".md",
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write("# Spec\n\nTODO: finish this\n")
            path = Path(f.name)
        try:
            r = subprocess.run(
                [sys.executable, str(_SCRIPT), str(path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 1, r.stderr + r.stdout)
            self.assertIn("TODO", r.stdout + r.stderr)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for phase_ledger (stdlib)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))

import phase_ledger as pl  # noqa: E402


class TestPhaseLedger(unittest.TestCase):
    def test_append_and_verify_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp) / "prds" / "t1"
            (td / "eval").mkdir(parents=True)
            f = td / "eval" / "x.yaml"
            f.write_text("scenario: a\nsteps:\n  - id: s\n    driver: d\n    action: a\n    expected:\n      k: 1\n", encoding="utf-8")
            e = pl.build_entry("t1", "[P4.0-EVAL-YAML]", ["eval/x.yaml"], td)
            pl.append_entry(td, e)
            self.assertEqual(pl.verify_ledger(td, verify_hashes=False, task_id_expected="t1"), [])
            self.assertEqual(pl.verify_ledger(td, verify_hashes=True, task_id_expected="t1"), [])
            f.write_text("changed", encoding="utf-8")
            errs = pl.verify_ledger(td, verify_hashes=True, task_id_expected="t1")
            self.assertTrue(any("sha256 mismatch" in x for x in errs))

    def test_ledger_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp) / "prds" / "t1"
            td.mkdir(parents=True)
            secret = Path(tmp) / "secret.txt"
            secret.write_text("x", encoding="utf-8")
            bad = {
                "schema_version": 1,
                "task_id": "t1",
                "phase_marker": "x",
                "recorded_at": "2026-01-01T00:00:00Z",
                "artifacts": [{"relpath": "../secret.txt", "sha256": "a" * 64}],
            }
            (td / pl.LEDGER_NAME).write_text(json.dumps(bad) + "\n", encoding="utf-8")
            errs = pl.verify_ledger(td, verify_hashes=True, task_id_expected="t1")
            self.assertTrue(any("unsafe" in e.lower() or "escape" in e.lower() for e in errs))

    def test_resolved_artifact_path_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp) / "task"
            td.mkdir()
            outside = Path(tmp) / "outside.txt"
            outside.write_text("data", encoding="utf-8")
            link = td / "eval"
            link.symlink_to(Path(tmp))
            fp, msg = pl._resolved_artifact_path(td, "eval/outside.txt")
            self.assertIsNone(fp)
            self.assertIsNotNone(msg)
            self.assertIn("escape", msg.lower())


if __name__ == "__main__":
    unittest.main()

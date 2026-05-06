#!/usr/bin/env python3
"""Tests for tdd_csv_trace (forge-tdd markers ↔ manual / semantic CSV ids)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import semantic_csv as sc  # noqa: E402
import tdd_csv_trace as tct  # noqa: E402


class TestManualRequiredColumn(unittest.TestCase):
    def test_required_column_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "manual-test-cases.csv"
            p.write_text(
                "Id,Title,Required\n"
                "TC-1,One,yes\n"
                "TC-2,Two,no\n",
                encoding="utf-8",
            )
            all_ids, req, errs = sc.parse_manual_test_cases_full(p)
            self.assertEqual(errs, [], errs)
            self.assertEqual(all_ids, {"TC-1", "TC-2"})
            self.assertEqual(req, {"TC-1"})


class TestCollectTddScanPyFiles(unittest.TestCase):
    def test_tdd_scan_paths_outside_task_dir_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp) / "prds" / "t1"
            qa = td / "qa"
            qa.mkdir(parents=True)
            outside = Path(tmp) / "outside_tests"
            outside.mkdir()
            (outside / "test_ext.py").write_text("# forge-tdd: TC-1\n", encoding="utf-8")
            rel = os.path.relpath(outside, td)
            (qa / "tdd-scan-paths.txt").write_text(f"{rel}\n", encoding="utf-8")
            files, errs = tct.collect_tdd_scan_py_files(td)
            self.assertEqual(files, [])
            self.assertTrue(any("escapes task dir" in e for e in errs), errs)


class TestVerifyTddCsvTrace(unittest.TestCase):
    def test_unknown_marker_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp) / "prds" / "t1"
            qa = td / "qa"
            qa.mkdir(parents=True)
            (qa / "manual-test-cases.csv").write_text(
                "Id,Title\nTC-1,x\n",
                encoding="utf-8",
            )
            (qa / "semantic-automation.csv").write_text(
                "Id,Surface,Intent\nstep-a,api,x\n",
                encoding="utf-8",
            )
            (qa / "test_foo.py").write_text(
                "def test_x():\n"
                '    # forge-tdd: TC-999\n'
                "    assert 1\n",
                encoding="utf-8",
            )
            errs = tct.verify_tdd_csv_trace(td)
            self.assertTrue(any("unknown forge-tdd id 'TC-999'" in e for e in errs), errs)

    def test_required_row_without_marker_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp) / "prds" / "t1"
            qa = td / "qa"
            qa.mkdir(parents=True)
            (qa / "manual-test-cases.csv").write_text(
                "Id,Title,Required\nTC-1,Login,yes\n",
                encoding="utf-8",
            )
            (qa / "semantic-automation.csv").write_text(
                "Id,Surface,Intent\ns1,api,x\n",
                encoding="utf-8",
            )
            (qa / "test_auth.py").write_text(
                "def test_other():\n"
                '    # forge-tdd: s1\n'
                "    assert 1\n",
                encoding="utf-8",
            )
            errs = tct.verify_tdd_csv_trace(td)
            self.assertTrue(
                any("TC-1" in e and "Required=yes" in e for e in errs),
                errs,
            )

    def test_required_satisfied_by_manual_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp) / "prds" / "t1"
            qa = td / "qa"
            qa.mkdir(parents=True)
            (qa / "manual-test-cases.csv").write_text(
                "Id,Title,Required\nTC-1,Login,yes\n",
                encoding="utf-8",
            )
            (qa / "semantic-automation.csv").write_text(
                "Id,Surface,Intent\ns1,api,x\n",
                encoding="utf-8",
            )
            (qa / "test_auth.py").write_text(
                "def test_login():\n"
                '    # forge-tdd: TC-1 (manual-test-cases.csv)\n'
                "    assert 1\n",
                encoding="utf-8",
            )
            self.assertEqual(tct.verify_tdd_csv_trace(td), [])


if __name__ == "__main__":
    unittest.main()

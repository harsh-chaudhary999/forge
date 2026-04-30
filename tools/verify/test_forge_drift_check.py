#!/usr/bin/env python3
"""Unit tests for forge_drift_check helpers.

Run from repo root:
  python3 -m unittest discover -s tools/verify -p 'test_forge_drift_check.py' -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import forge_drift_check as fdc


class TestCombinedSemanticAutomationText(unittest.TestCase):
    def test_empty_qa_dir_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            task_dir = Path(td)
            self.assertEqual(fdc._combined_semantic_automation_text(task_dir), "")

    def test_concatenates_csv_manifest_and_log(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            task_dir = Path(td)
            qa = task_dir / "qa"
            qa.mkdir(parents=True)
            (qa / "semantic-automation.csv").write_text("Id,Surface,Intent\na,api,ping\n", encoding="utf-8")
            (qa / "semantic-eval-manifest.json").write_text('{"schema_version":1}', encoding="utf-8")
            (qa / "semantic-eval-run.log").write_text('{"step":"a"}\n', encoding="utf-8")
            hay = fdc._combined_semantic_automation_text(task_dir)
            self.assertIn("ping", hay)
            self.assertIn("schema_version", hay)
            self.assertIn("step", hay)

    def test_does_not_include_prds_eval_directory(self) -> None:
        """Haystack is qa/semantic-* only — prds/<task>/eval/*.yaml is not read."""
        with tempfile.TemporaryDirectory() as td:
            task_dir = Path(td)
            ev = task_dir / "eval"
            ev.mkdir(parents=True)
            (ev / "smoke.yaml").write_text("scenario: legacy\n", encoding="utf-8")
            qa = task_dir / "qa"
            qa.mkdir(parents=True)
            (qa / "semantic-automation.csv").write_text(
                "Id,Surface,Intent\nx,api,check\n", encoding="utf-8"
            )
            hay = fdc._combined_semantic_automation_text(task_dir)
            self.assertIn("check", hay)
            self.assertNotIn("legacy", hay)


if __name__ == "__main__":
    unittest.main()

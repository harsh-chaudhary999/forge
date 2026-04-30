#!/usr/bin/env python3
"""Tests for forge_drift_check: helpers and main() CLI paths.

Run from repo root:
  python3 -m unittest discover -s tools/verify -p 'test_forge_drift_check.py' -v
"""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import forge_drift_check as fdc


class TestExtractSuccessCriteriaBullets(unittest.TestCase):
    def test_extracts_long_bullets_only(self) -> None:
        text = (
            "# PRD Locked\n\n"
            "**Success Criteria:**\n"
            "- Short\n"
            "- User can complete checkout with a saved payment method\n"
            "**Product:** X\n"
        )
        got = fdc._extract_success_criteria_bullets(text)
        self.assertEqual(
            got,
            ["User can complete checkout with a saved payment method"],
        )

    def test_missing_section_returns_empty(self) -> None:
        self.assertEqual(fdc._extract_success_criteria_bullets("# PRD Locked\n"), [])


class TestCombinedQaText(unittest.TestCase):
    def test_missing_manual_csv_returns_empty_without_warn(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "qa" / "manual-test-cases.csv"
            self.assertEqual(fdc._combined_qa_text(p), "")

    def test_reads_file_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "qa" / "manual-test-cases.csv"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("Id,Title\nTC-1,Hello World\n", encoding="utf-8")
            hay = fdc._combined_qa_text(p)
            self.assertIn("hello world", hay)


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


class TestMainCli(unittest.TestCase):
    def _brain_task(self, brain: Path, tid: str) -> Path:
        td = brain / "prds" / tid
        td.mkdir(parents=True)
        return td

    def test_missing_prd_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as b:
            brain = Path(b)
            self._brain_task(brain, "t1")
            stderr = io.StringIO()
            argv = ["forge_drift_check.py", "--task-id", "t1", "--brain", str(brain)]
            with patch.object(sys, "argv", argv):
                with patch.object(sys, "stderr", stderr):
                    rc = fdc.main()
            self.assertEqual(rc, 1)
            self.assertIn("ERROR", stderr.getvalue())

    def test_no_success_criteria_bullets_exits_0_with_info(self) -> None:
        with tempfile.TemporaryDirectory() as b:
            brain = Path(b)
            task = self._brain_task(brain, "t2")
            (task / "prd-locked.md").write_text(
                "# PRD Locked\n\n**Product:** X\n**Success Criteria:**\n- x\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            argv = ["forge_drift_check.py", "--task-id", "t2", "--brain", str(brain)]
            with patch.object(sys, "argv", argv):
                with patch.object(sys, "stdout", stdout):
                    rc = fdc.main()
            self.assertEqual(rc, 0)
            self.assertIn("INFO", stdout.getvalue())

    def test_bullet_found_in_semantic_haystack_exits_0(self) -> None:
        criterion = "User can verify order status after placing an order"
        with tempfile.TemporaryDirectory() as b:
            brain = Path(b)
            task = self._brain_task(brain, "t3")
            (task / "prd-locked.md").write_text(
                f"# PRD Locked\n\n**Success Criteria:**\n- {criterion}\n",
                encoding="utf-8",
            )
            qa = task / "qa"
            qa.mkdir(parents=True)
            (qa / "semantic-automation.csv").write_text(
                f"Id,Surface,Intent\na,api,{criterion}\n",
                encoding="utf-8",
            )
            argv = ["forge_drift_check.py", "--task-id", "t3", "--brain", str(brain)]
            stdout = io.StringIO()
            with patch.object(sys, "argv", argv):
                with patch.object(sys, "stdout", stdout):
                    rc = fdc.main()
            self.assertEqual(rc, 0)
            self.assertIn("OK:", stdout.getvalue())

    def test_bullet_missing_warns_non_strict_exits_0(self) -> None:
        with tempfile.TemporaryDirectory() as b:
            brain = Path(b)
            task = self._brain_task(brain, "t4")
            (task / "prd-locked.md").write_text(
                "# PRD Locked\n\n**Success Criteria:**\n"
                "- This criterion text is unique and not in any qa file\n",
                encoding="utf-8",
            )
            qa = task / "qa"
            qa.mkdir(parents=True)
            (qa / "semantic-automation.csv").write_text(
                "Id,Surface,Intent\na,api,unrelated text\n", encoding="utf-8"
            )
            stderr = io.StringIO()
            argv = ["forge_drift_check.py", "--task-id", "t4", "--brain", str(brain)]
            with patch.object(sys, "argv", argv):
                with patch.object(sys, "stderr", stderr):
                    rc = fdc.main()
            self.assertEqual(rc, 0)
            self.assertIn("WARN", stderr.getvalue())

    def test_strict_missing_bullet_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as b:
            brain = Path(b)
            task = self._brain_task(brain, "t5")
            (task / "prd-locked.md").write_text(
                "# PRD Locked\n\n**Success Criteria:**\n"
                "- Unique missing bullet xyzabc123notinhaystack\n",
                encoding="utf-8",
            )
            qa = task / "qa"
            qa.mkdir(parents=True)
            (qa / "semantic-automation.csv").write_text(
                "Id,Surface,Intent\na,api,nope\n", encoding="utf-8"
            )
            stderr = io.StringIO()
            argv = [
                "forge_drift_check.py",
                "--task-id",
                "t5",
                "--brain",
                str(brain),
                "--strict",
            ]
            with patch.object(sys, "argv", argv):
                with patch.object(sys, "stderr", stderr):
                    rc = fdc.main()
            self.assertEqual(rc, 1)
            self.assertIn("ERROR", stderr.getvalue())

    def test_absent_manual_csv_semantic_only_still_matches(self) -> None:
        """No qa/manual-test-cases.csv — haystack is semantic files only; still OK if criterion appears."""
        criterion = "End to end drift match without manual csv file present"
        with tempfile.TemporaryDirectory() as b:
            brain = Path(b)
            task = self._brain_task(brain, "t6")
            (task / "prd-locked.md").write_text(
                f"# PRD Locked\n\n**Success Criteria:**\n- {criterion}\n",
                encoding="utf-8",
            )
            qa = task / "qa"
            qa.mkdir(parents=True)
            (qa / "semantic-automation.csv").write_text(
                f"Id,Surface,Intent\nx,api,{criterion}\n",
                encoding="utf-8",
            )
            argv = ["forge_drift_check.py", "--task-id", "t6", "--brain", str(brain)]
            stdout = io.StringIO()
            with patch.object(sys, "argv", argv):
                with patch.object(sys, "stdout", stdout):
                    rc = fdc.main()
            self.assertEqual(rc, 0)
            self.assertIn("OK:", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()

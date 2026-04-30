#!/usr/bin/env python3
"""Tests for semantic_csv.py and coherence with verify_forge_task."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import semantic_csv as sc
import verify_forge_task as vft


class TestSemanticCsvParse(unittest.TestCase):
    def test_minimal_csv_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "semantic-automation.csv"
            p.write_text(
                "Id,Surface,Intent\n"
                "s1,api,GET /health returns 200\n"
                "s2,web,Open login page\n",
                encoding="utf-8",
            )
            steps, errs = sc.parse_semantic_automation_csv(p)
            self.assertEqual(errs, [], errs)
            self.assertEqual(len(steps), 2)
            self.assertEqual(steps[0].surface, "api")
            self.assertEqual(steps[1].surface, "web")

    def test_depends_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "semantic-automation.csv"
            p.write_text(
                "Id,Surface,Intent,DependsOn\n"
                "b,api,Setup token,\n"
                "a,web,Use token,b\n",
                encoding="utf-8",
            )
            steps, errs = sc.parse_semantic_automation_csv(p)
            self.assertEqual(errs, [], errs)
            ordered, c_err = sc.topological_order(steps)
            self.assertIsNone(c_err)
            assert ordered is not None
            self.assertEqual([x.id for x in ordered], ["b", "a"])

    def test_cycle_fails(self) -> None:
        steps = [
            sc.SemanticStep(id="a", surface="api", intent="x", depends_on=["b"]),
            sc.SemanticStep(id="b", surface="api", intent="y", depends_on=["a"]),
        ]
        _order, err = sc.topological_order(steps)
        self.assertIsNotNone(err)

    def test_unknown_dep(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "semantic-automation.csv"
            p.write_text(
                "Id,Surface,Intent,DependsOn\n"
                "a,api,x,missing\n",
                encoding="utf-8",
            )
            steps, errs = sc.parse_semantic_automation_csv(p)
            self.assertEqual(errs, [], errs)
            errs2 = sc.validate_depends_closure(steps)
            self.assertTrue(any("unknown Id" in e for e in errs2))


class TestVerifySemanticCoherence(unittest.TestCase):
    def test_semantic_csv_eval_requires_csv(self) -> None:
        with tempfile.TemporaryDirectory() as brain_s:
            brain = Path(brain_s)
            tid = "t1"
            task_dir = brain / "prds" / tid
            (task_dir / "qa").mkdir(parents=True)
            manifest = task_dir / "qa" / "semantic-eval-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "task_id": tid,
                        "recorded_at": "2026-04-29T00:00:00Z",
                        "kind": "semantic-csv-eval",
                        "outcome": "pass",
                    }
                ),
                encoding="utf-8",
            )
            (task_dir / "prd-locked.md").write_text("# PRD Locked\n", encoding="utf-8")

            errs, _ = vft.verify_detailed(
                brain=brain,
                task_id=tid,
                product_slug=None,
                strict_tdd=False,
                require_log=False,
            )
            self.assertTrue(any("semantic-automation.csv" in e for e in errs))

    def test_invalid_csv_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as brain_s:
            brain = Path(brain_s)
            tid = "t2"
            task_dir = brain / "prds" / tid
            (task_dir / "qa").mkdir(parents=True)
            csv_path = task_dir / "qa" / "semantic-automation.csv"
            csv_path.write_text(
                "Id,Surface,Intent\n"
                "a,not-a-real-surface,do something\n",
                encoding="utf-8",
            )
            (task_dir / "prd-locked.md").write_text("# PRD Locked\n", encoding="utf-8")

            errs, _ = vft.verify_detailed(
                brain=brain,
                task_id=tid,
                product_slug=None,
                strict_tdd=False,
                require_log=False,
            )
            self.assertTrue(any("unknown Surface" in e for e in errs), errs)


class TestRunSemanticCsvCli(unittest.TestCase):
    def test_cli_writes_manifest(self) -> None:
        script = _TOOLS_DIR / "run_semantic_csv_eval.py"
        with tempfile.TemporaryDirectory() as tmp:
            brain = Path(tmp)
            tid = "cli-task"
            qa = brain / "prds" / tid / "qa"
            qa.mkdir(parents=True)
            (qa / "semantic-automation.csv").write_text(
                "Id,Surface,Intent\n"
                "x,api,Call GET /health\n",
                encoding="utf-8",
            )
            r = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--task-id",
                    tid,
                    "--brain",
                    str(brain),
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                cwd=str(brain),
            )
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            man = qa / "semantic-eval-manifest.json"
            self.assertTrue(man.is_file())
            data = json.loads(man.read_text(encoding="utf-8"))
            self.assertEqual(data.get("kind"), "semantic-csv-eval")
            self.assertEqual(data.get("outcome"), "yellow")


if __name__ == "__main__":
    unittest.main()

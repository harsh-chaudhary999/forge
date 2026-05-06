#!/usr/bin/env python3
"""Tests for run_semantic_csv_eval.run_pipeline (ordering, manifest, log)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import run_semantic_csv_eval as rse  # noqa: E402


class TestRunSemanticCsvEvalPipeline(unittest.TestCase):
    def test_topological_order_reflected_in_run_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = Path(tmp)
            tid = "dag-task"
            td = brain / "prds" / tid
            qa = td / "qa"
            qa.mkdir(parents=True)
            csv_path = qa / "semantic-automation.csv"
            csv_path.write_text(
                "Id,Surface,Intent,DependsOn\n"
                "b,api,Setup,\n"
                "a,web,Follow,b\n",
                encoding="utf-8",
            )
            rc = rse.run_pipeline(
                task_dir=td,
                task_id=tid,
                csv_path=csv_path,
                dry_run=True,
                driver_name="noop",
                outcome_override=None,
            )
            self.assertEqual(rc, 0)
            log_path = qa / "semantic-eval-run.log"
            self.assertTrue(log_path.is_file())
            ids_in_order: list[str] = []
            for ln in log_path.read_text(encoding="utf-8").splitlines():
                ln = ln.strip()
                if not ln.startswith("{"):
                    continue
                obj = json.loads(ln)
                ids_in_order.append(obj["id"])
            self.assertEqual(ids_in_order, ["b", "a"])

            man_path = qa / "semantic-eval-manifest.json"
            data = json.loads(man_path.read_text(encoding="utf-8"))
            self.assertEqual(data.get("step_count"), 2)
            self.assertEqual(data.get("outcome"), "yellow")


if __name__ == "__main__":
    unittest.main()

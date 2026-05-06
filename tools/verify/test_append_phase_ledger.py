#!/usr/bin/env python3
"""Tests for append_phase_ledger.py CLI and phase-ledger append semantics."""

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

_SCRIPT = _TOOLS_DIR / "append_phase_ledger.py"

import phase_ledger as pl  # noqa: E402


def _run_append(
    *,
    brain: Path,
    task_id: str,
    phase: str,
    artifacts: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--brain",
            str(brain),
            "--task-id",
            task_id,
            "--phase",
            phase,
            "--artifacts",
            artifacts,
        ],
        capture_output=True,
        text=True,
        cwd=str(brain),
    )


class TestAppendPhaseLedgerCli(unittest.TestCase):
    def test_append_writes_jsonl_line_with_expected_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = Path(tmp)
            tid = "ledger-cli"
            td = brain / "prds" / tid
            (td / "qa").mkdir(parents=True)
            art = td / "qa" / "semantic-automation.csv"
            content = "Id,Surface,Intent\nx,api,y\n"
            art.write_text(content, encoding="utf-8")
            expected_sha = pl.file_sha256(art)

            r = _run_append(
                brain=brain,
                task_id=tid,
                phase="[P4.0-SEMANTIC-EVAL]",
                artifacts="qa/semantic-automation.csv",
            )
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

            ledger = td / pl.LEDGER_NAME
            self.assertTrue(ledger.is_file())
            line = ledger.read_text(encoding="utf-8").strip().splitlines()[-1]
            obj = json.loads(line)
            self.assertEqual(obj.get("schema_version"), pl.CURRENT_SCHEMA)
            self.assertEqual(obj.get("phase_marker"), "[P4.0-SEMANTIC-EVAL]")
            self.assertEqual(obj.get("task_id"), tid)
            self.assertIsInstance(obj.get("recorded_at"), str)
            self.assertTrue(obj.get("recorded_at"))
            arts = obj.get("artifacts")
            self.assertIsInstance(arts, list)
            self.assertEqual(len(arts), 1)
            self.assertEqual(arts[0].get("relpath"), "qa/semantic-automation.csv")
            self.assertEqual(arts[0].get("sha256"), expected_sha)

    def test_second_append_preserves_first_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = Path(tmp)
            tid = "ledger-append-twice"
            td = brain / "prds" / tid
            (td / "qa").mkdir(parents=True)
            a = td / "qa" / "semantic-automation.csv"
            b = td / "qa" / "semantic-eval-manifest.json"
            a.write_text("Id,Surface,Intent\nx,api,y\n", encoding="utf-8")
            b.write_text('{"schema_version":1}\n', encoding="utf-8")

            self.assertEqual(
                _run_append(
                    brain=brain,
                    task_id=tid,
                    phase="[P4.0-SEMANTIC-EVAL]",
                    artifacts="qa/semantic-automation.csv",
                ).returncode,
                0,
            )
            self.assertEqual(
                _run_append(
                    brain=brain,
                    task_id=tid,
                    phase="[P4.1-DISPATCH]",
                    artifacts="qa/semantic-eval-manifest.json",
                ).returncode,
                0,
            )

            ledger = td / pl.LEDGER_NAME
            lines = ledger.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 2)
            first = json.loads(lines[0])
            second = json.loads(lines[1])
            self.assertEqual(first.get("phase_marker"), "[P4.0-SEMANTIC-EVAL]")
            self.assertEqual(second.get("phase_marker"), "[P4.1-DISPATCH]")


if __name__ == "__main__":
    unittest.main()

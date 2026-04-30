#!/usr/bin/env python3
"""Unit tests for verify_forge_task helpers.

Run from repo root:
  python3 -m unittest discover -s tools -p 'test_verify_forge_task.py' -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import verify_forge_task as vft


class TestPrdLockedSections(unittest.TestCase):
    def test_minimal_prd_passes(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(
                "# PRD Locked\n\n"
                "**Product:** P\n**Goal:** G\n**Success Criteria:**\n- One criterion here\n"
                "**Repos Affected:**\n- backend-api\n"
                "**repo_registry_confidence:** high\n"
                "**repo_naming_mismatch_notes:** none\n**product_md_update_required:** no\n"
                "**Contracts Affected:** none\n**Timeline:** soon\n**Rollback:** safe\n"
                "**Success Metrics:** n/a\n"
                "**Design / UI (Q9):**\n**design_intake_anchor:** x\n"
            )
            path = Path(f.name)
        try:
            errs = vft._validate_prd_locked_sections(path)
            self.assertEqual(errs, [], errs)
        finally:
            path.unlink(missing_ok=True)


class TestVerifyDetailed(unittest.TestCase):
    def test_invalid_task_id_fails_fast(self) -> None:
        errs, warns = vft.verify_detailed(
            brain=Path("/tmp"),
            task_id="../bad",
            product_slug=None,
            strict_tdd=False,
            require_log=False,
        )
        self.assertTrue(errs)
        self.assertEqual(warns, [])


class TestSemanticEvalManifest(unittest.TestCase):
    def test_manifest_only_passes_eval_gate(self) -> None:
        with tempfile.TemporaryDirectory() as brain_s:
            brain = Path(brain_s)
            tid = "x-task"
            task_dir = brain / "prds" / tid
            (task_dir / "qa").mkdir(parents=True)
            manifest = task_dir / "qa" / "semantic-eval-manifest.json"
            manifest.write_text(
                """{"schema_version":1,"task_id":"x-task","recorded_at":"2026-04-29T00:00:00Z","kind":"semantic-eval-record","outcome":"pass"}
""",
                encoding="utf-8",
            )
            prd = task_dir / "prd-locked.md"
            prd.write_text("# PRD Locked\n", encoding="utf-8")

            errs, warns = vft.verify_detailed(
                brain=brain,
                task_id=tid,
                product_slug=None,
                strict_tdd=False,
                require_log=False,
            )
            need_manifest_msgs = [e for e in errs if "Need valid" in e and "semantic-eval-manifest" in e]
            self.assertEqual(need_manifest_msgs, [], errs)

    def test_bad_manifest_errors(self) -> None:
        with tempfile.TemporaryDirectory() as brain_s:
            brain = Path(brain_s)
            tid = "x-task"
            task_dir = brain / "prds" / tid
            (task_dir / "qa").mkdir(parents=True)
            manifest = task_dir / "qa" / "semantic-eval-manifest.json"
            manifest.write_text(
                '{"schema_version":1,"task_id":"wrong","recorded_at":"2026-04-29T00:00:00Z","kind":"k"}',
                encoding="utf-8",
            )
            prd = task_dir / "prd-locked.md"
            prd.write_text("# PRD Locked\n", encoding="utf-8")

            errs, warns = vft.verify_detailed(
                brain=brain,
                task_id=tid,
                product_slug=None,
                strict_tdd=False,
                require_log=False,
            )
            self.assertTrue(any("task_id must match" in e for e in errs))
            self.assertTrue(any("Need valid" in e and "semantic-eval-manifest" in e for e in errs))


class TestConductorLogOrdering(unittest.TestCase):
    def test_dispatch_before_semantic_eval_fails(self) -> None:
        with tempfile.TemporaryDirectory() as brain_s:
            brain = Path(brain_s)
            tid = "bad-order"
            task_dir = brain / "prds" / tid
            (task_dir / "qa").mkdir(parents=True)
            (task_dir / "qa" / "semantic-eval-manifest.json").write_text(
                '{"schema_version":1,"task_id":"bad-order",'
                '"recorded_at":"2026-04-29T00:00:00Z","kind":"k","outcome":"pass"}\n',
                encoding="utf-8",
            )
            (task_dir / "prd-locked.md").write_text("# PRD Locked\n", encoding="utf-8")
            (task_dir / "conductor.log").write_text(
                "2026-04-29T00:00:00Z [P4.1-DISPATCH]\n"
                "2026-04-29T00:01:00Z [P4.0-SEMANTIC-EVAL]\n",
                encoding="utf-8",
            )
            errs, _warns = vft.verify_detailed(
                brain=brain,
                task_id=tid,
                product_slug=None,
                strict_tdd=False,
                require_log=True,
            )
            self.assertTrue(
                any("[P4.1-DISPATCH]" in e and "[P4.0-SEMANTIC-EVAL]" in e for e in errs),
                errs,
            )


if __name__ == "__main__":
    unittest.main()

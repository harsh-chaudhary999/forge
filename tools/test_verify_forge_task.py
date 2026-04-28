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

_validate_single_eval_document = vft._validate_single_eval_document
_validate_eval_yaml_files = vft._validate_eval_yaml_files


class TestValidateSingleEvalDocument(unittest.TestCase):
    def test_minimal_ok(self) -> None:
        data = {
            "scenario": "smoke",
            "description": "d",
            "steps": [
                {
                    "id": "step_1",
                    "driver": "api-http",
                    "action": "call",
                    "expected": {"status": 200},
                }
            ],
        }
        self.assertEqual(_validate_single_eval_document(data, "x.yaml"), [])

    def test_missing_scenario(self) -> None:
        data = {"steps": [{"id": "a", "driver": "d", "action": "x", "expected": {"k": 1}}]}
        errs = _validate_single_eval_document(data, "f.yaml")
        self.assertTrue(any("scenario" in e for e in errs))

    def test_empty_expected(self) -> None:
        data = {
            "scenario": "s",
            "steps": [{"id": "step_1", "driver": "api-http", "action": "call", "expected": {}}],
        }
        errs = _validate_single_eval_document(data, "f.yaml")
        self.assertTrue(any("expected" in e and "empty" in e for e in errs))


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


class TestValidateEvalYamlFiles(unittest.TestCase):
    def test_parse_roundtrip(self) -> None:
        try:
            import yaml  # type: ignore  # noqa: F401
        except ImportError:
            self.skipTest("PyYAML not installed")

        y = """
scenario: stack-smoke
description: smoke
steps:
  - id: "step_1"
    driver: "api-http"
    action: "call"
    method: "GET"
    expected:
      status: 200
"""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "smoke.yaml"
            p.write_text(y, encoding="utf-8")
            self.assertEqual(_validate_eval_yaml_files(Path(tmp)), [])

    def test_invalid_yaml(self) -> None:
        try:
            import yaml  # type: ignore  # noqa: F401
        except ImportError:
            self.skipTest("PyYAML not installed")

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.yaml"
            p.write_text("scenario: [\n", encoding="utf-8")
            errs = _validate_eval_yaml_files(Path(tmp))
            self.assertTrue(any("parse" in e.lower() for e in errs))


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


if __name__ == "__main__":
    unittest.main()

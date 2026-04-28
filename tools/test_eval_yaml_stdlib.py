#!/usr/bin/env python3
"""Tests for eval_yaml_stdlib (python3 -m unittest discover -s tools -p 'test_eval*.py' -v)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import eval_yaml_stdlib as ey  # noqa: E402


class TestEvalYamlStdlib(unittest.TestCase):
    def test_smoke_passes(self) -> None:
        y = """
scenario: stack-smoke
description: d
steps:
  - id: "step_1"
    driver: "api-http"
    action: "call"
    expected:
      status: 200
"""
        self.assertEqual(ey.validate_eval_file_stdlib(y, "t.yaml"), [])

    def test_missing_scenario(self) -> None:
        y = "steps:\n  - id: a\n    driver: x\n    action: y\n    expected:\n      k: 1\n"
        errs = ey.validate_eval_file_stdlib(y, "t.yaml")
        self.assertTrue(any("scenario" in e for e in errs))

    def test_flow_style_steps_reported(self) -> None:
        y = (
            "scenario: s\n"
            "steps:\n"
            "  - {id: a, driver: api-http, action: call, expected: {status: 200}}\n"
        )
        errs = ey.validate_eval_file_stdlib(y, "t.yaml")
        self.assertTrue(any("flow-style" in e for e in errs), errs)

    def test_multi_document_supported(self) -> None:
        y = (
            "scenario: s1\nsteps:\n  - id: a\n    driver: x\n    action: y\n    expected:\n      k: 1\n"
            "---\n"
            "scenario: s2\nsteps:\n  - id: b\n    driver: x\n    action: y\n    expected:\n      k: 2\n"
        )
        self.assertEqual(ey.validate_eval_file_stdlib(y, "multi.yaml"), [])


if __name__ == "__main__":
    unittest.main()

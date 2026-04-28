#!/usr/bin/env python3
"""Tests for shared_spec_policy (stdlib)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))

import shared_spec_policy as ssp  # noqa: E402


class TestTbdViolations(unittest.TestCase):
    def test_tbd_inside_fence_ignored(self) -> None:
        text = "# Spec\n\n```\nTODO fix this in code sample\n```\n\nDone.\n"
        self.assertEqual(ssp.tbd_violations(text), [])

    def test_tbd_in_prose_reported(self) -> None:
        text = "# Spec\n\nWe will TODO later.\n"
        errs = ssp.tbd_violations(text)
        self.assertEqual(len(errs), 1)
        self.assertIn("TODO", errs[0])

    def test_todo_in_heading_ignored(self) -> None:
        text = "# TODO: follow-ups from council\n\nBody without markers.\n"
        self.assertEqual(ssp.tbd_violations(text), [])

    def test_tbd_inside_tilde_fence_ignored(self) -> None:
        text = "# Spec\n\n~~~\nTODO in code block\n~~~\n"
        self.assertEqual(ssp.tbd_violations(text), [])


class TestValidateSharedSpec(unittest.TestCase):
    def test_required_anchor_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = root / "shared-dev-spec.md"
            checklist = root / "checklist.json"
            spec.write_text("hello\n", encoding="utf-8")
            checklist.write_text('{"required_substrings": ["must-have"]}', encoding="utf-8")
            errs = ssp.validate_shared_spec(spec, checklist_path=checklist)
            self.assertTrue(any("must-have" in e for e in errs), errs)

    def test_malformed_checklist_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = root / "shared-dev-spec.md"
            checklist = root / "checklist.json"
            spec.write_text("content\n", encoding="utf-8")
            checklist.write_text("{bad json", encoding="utf-8")
            errs = ssp.validate_shared_spec(spec, checklist_path=checklist)
            self.assertTrue(any("invalid checklist JSON" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()

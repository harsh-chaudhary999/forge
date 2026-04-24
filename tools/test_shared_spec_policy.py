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


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for lint_skill_allowed_tools.collect_policy (stdlib)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))

import lint_skill_allowed_tools as lst  # noqa: E402


class TestCollectPolicySkillsRoot(unittest.TestCase):
    def test_collect_policy_custom_root_without_skills_segment(self) -> None:
        """Regression: policy must not skip all files when path has no 'skills' dirname."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "my-skills-clone"
            skill_dir = root / "autoplan"
            skill_dir.mkdir(parents=True)
            skill_dir.joinpath("SKILL.md").write_text(
                "---\n"
                "name: autoplan\n"
                "type: rigid\n"
                "allowed-tools:\n"
                "  - Read\n"
                "  - Grep\n"
                "---\n\n"
                "## Body\n",
                encoding="utf-8",
            )
            pol = lst.collect_policy(root)
            self.assertIn("autoplan", pol["skills"])
            self.assertEqual(pol["skills"]["autoplan"]["allowed_tools"], ["Read", "Grep"])

    def test_lint_rigid_without_allowed_tools_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "skill" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text(
                "---\nname: s\ntype: rigid\n---\n\nbody\n",
                encoding="utf-8",
            )
            errs, _warns = lst.lint_skill_file(skill)
            self.assertTrue(any("type rigid" in e for e in errs), errs)

    def test_collect_policy_parses_inline_allowed_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            skill = root / "s" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text(
                "---\nname: s\ntype: rigid\nallowed-tools: [Read, Grep]\n---\n",
                encoding="utf-8",
            )
            pol = lst.collect_policy(root)
            self.assertEqual(pol["skills"]["s"]["allowed_tools"], ["Read", "Grep"])


if __name__ == "__main__":
    unittest.main()

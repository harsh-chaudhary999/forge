#!/usr/bin/env python3
"""Tests for verify_tech_plans (structure + --strict-0c-inventory).

Run from repo root:
  python3 -m unittest discover -s tools -p 'test_verify_tech_plans.py' -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import verify_tech_plans as vtp


def _minimal_review_pass_skeleton(*, last_col: str = "PASS") -> str:
    """Minimal markdown satisfying structural REVIEW_PASS checks."""
    return f"""# Demo

Tech plan status: REVIEW_PASS

### 1b.0 x
### 1b.0b x
### 1b.2 x
### 1b.5 x
#### 1b.5b x
### 1b.2a x
### 1b.6 x

## Section 1c

<!-- FORGE-GATE:SECTION-0C-INVENTORY:v1 -->
| Source | Text | 1b.0 | Tasks | Evidence | Status |
| --- | --- | --- | --- | --- | --- |
| prd | scope | r1 | T1 | NONE | PASS |
| prd-source-confluence.md | body | r2 | T2 | NONE | {last_col} |

<!-- FORGE-GATE:CODE-RECROSS:v1 -->
- checked: none
"""


class TestStrict0cInventory(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.brain = self.root / "brain"
        self.task_id = "t-strict-0c"
        self.task_dir = self.brain / "prds" / self.task_id
        self.tp_dir = self.task_dir / "tech-plans"
        self.tp_dir.mkdir(parents=True)
        (self.task_dir / "prd-locked.md").write_text("# PRD\n", encoding="utf-8")
        (self.task_dir / "eval").mkdir()
        (self.task_dir / "eval" / "s.yaml").write_text(
            "scenario: s\ndescription: d\nsteps:\n"
            '  - id: a\n    driver: api-http\n    action: call\n    expected:\n      x: 1\n',
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_gap_row_fails_under_strict(self) -> None:
        (self.tp_dir / "svc.md").write_text(
            _minimal_review_pass_skeleton(last_col="GAP"), encoding="utf-8"
        )
        errs = vtp.verify_tech_plans(self.brain, self.task_id, strict_0c_inventory=True)
        self.assertTrue(any("GAP" in e for e in errs), errs)

    def test_passes_strict_when_inventory_cites_touchpoints(self) -> None:
        (self.task_dir / "touchpoints").mkdir()
        (self.task_dir / "touchpoints" / "COHORT-AND-ADJACENCY.md").write_text(
            "# c\n", encoding="utf-8"
        )
        body = _minimal_review_pass_skeleton(last_col="PASS")
        body = body.replace(
            "| prd-source-confluence.md | body | r2 | T2 | NONE | PASS |",
            "| touchpoints/COHORT-AND-ADJACENCY.md | cohort | r2 | T2 | NONE | PASS |",
        )
        (self.tp_dir / "svc.md").write_text(body, encoding="utf-8")
        errs = vtp.verify_tech_plans(self.brain, self.task_id, strict_0c_inventory=True)
        self.assertEqual(errs, [], errs)

    def test_touchpoints_present_but_inventory_omits_touchpoints_token(self) -> None:
        (self.task_dir / "touchpoints").mkdir()
        (self.task_dir / "touchpoints" / "x.md").write_text("# x\n", encoding="utf-8")
        (self.tp_dir / "svc.md").write_text(
            _minimal_review_pass_skeleton(last_col="PASS"), encoding="utf-8"
        )
        errs = vtp.verify_tech_plans(self.brain, self.task_id, strict_0c_inventory=True)
        self.assertTrue(any("touchpoints" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()

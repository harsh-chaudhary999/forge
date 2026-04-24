#!/usr/bin/env python3
"""
Structural machine checks for per-repo tech plans under a brain task.

Catches common "looks complete" slips:
  - Missing canonical headings (### 1b.0, 1b.0b, 1b.2, 1b.2a, 1b.6, Section 1c)
  - ### 1b.2a placed before wire-map headings (### 1b.5 / #### 1b.5b)
  - REVIEW_PASS without file-embedded self-review anchors (inventory + recross)

Stdlib only. Intended for CI via verify_forge_task.py --strict-tech-plans
or direct invocation:

  python3 tools/verify_tech_plans.py --task-id my-feature --brain ~/forge/brain
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RE_STATUS_PASS = re.compile(
    r"^\s*Tech plan status:\s*REVIEW_PASS\s*$", re.IGNORECASE | re.MULTILINE
)
RE_HEAD = re.compile(r"^(#{1,6})\s+(.+)$")

# Exact heading bodies after # strip (skill uses ### 1b.0 etc.)
REQUIRED_HEADINGS = (
    "1b.0",
    "1b.0b",
    "1b.2",
    "1b.2a",
    "1b.6",
)

MARKER_0C = "<!-- FORGE-GATE:SECTION-0C-INVENTORY:v1 -->"
MARKER_RECROSS = "<!-- FORGE-GATE:CODE-RECROSS:v1 -->"

SKIP_NAMES = frozenset(
    {
        "human_signoff.md",
        "readme.md",
    }
)


def _heading_body(line: str) -> str | None:
    m = RE_HEAD.match(line.rstrip())
    if not m:
        return None
    return m.group(2).strip()


def _heading_id(body: str) -> str:
    """First token of heading body (e.g. `1b.0 PRD↔scan` → `1b.0`)."""
    return body.split()[0] if body else ""


def _line_of_heading(lines: list[str], want: str) -> int | None:
    """First line (1-based) where the heading id equals `want` (exact token match)."""
    for i, ln in enumerate(lines, start=1):
        body = _heading_body(ln)
        if body is None:
            continue
        if _heading_id(body) == want:
            return i
    return None


def verify_tech_plans(brain: Path, task_id: str) -> list[str]:
    errors: list[str] = []
    tp_dir = brain / "prds" / task_id / "tech-plans"
    if not tp_dir.is_dir():
        return errors

    md_files = sorted(
        p
        for p in tp_dir.iterdir()
        if p.is_file() and p.suffix.lower() == ".md"
        and p.name.lower() not in SKIP_NAMES
    )
    if not md_files:
        return errors

    for plan in md_files:
        rel = plan.relative_to(brain)
        text = plan.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()

        if "Tech plan status:" not in text:
            errors.append(f"{rel}: missing 'Tech plan status:' line under title")

        for h in REQUIRED_HEADINGS:
            if _line_of_heading(lines, h) is None:
                errors.append(f"{rel}: missing heading for subsection {h!r} (e.g. '### {h} …')")

        ln_2a = _line_of_heading(lines, "1b.2a")
        ln_15 = _line_of_heading(lines, "1b.5")
        ln_15b = _line_of_heading(lines, "1b.5b")
        if ln_2a is not None:
            wire_lines = [x for x in (ln_15, ln_15b) if x is not None]
            if not wire_lines:
                errors.append(
                    f"{rel}: has '### 1b.2a' but no '### 1b.5' or '#### 1b.5b' heading — "
                    "wire maps must precede touchpoint inventory"
                )
            else:
                wire_end = max(wire_lines)
                if ln_2a < wire_end:
                    errors.append(
                        f"{rel}: '### 1b.2a' (line {ln_2a}) must appear after "
                        f"last wire heading (line {wire_end})"
                    )

        if not re.search(r"Section\s+1c", text, re.IGNORECASE):
            errors.append(f"{rel}: missing 'Section 1c' (plan lifecycle / revision log)")

        if RE_STATUS_PASS.search(text):
            if MARKER_0C not in text:
                errors.append(
                    f"{rel}: REVIEW_PASS requires literal {MARKER_0C!r} "
                    "immediately above Section 0c inventory table (tech-plan-self-review)"
                )
            if MARKER_RECROSS not in text:
                errors.append(
                    f"{rel}: REVIEW_PASS requires literal {MARKER_RECROSS!r} "
                    "immediately above code recross-check evidence (tech-plan-self-review)"
                )

    return errors


def main() -> int:
    p = argparse.ArgumentParser(description="Verify tech plan structure under a brain task.")
    p.add_argument("--task-id", required=True)
    p.add_argument("--brain", default=None)
    args = p.parse_args()
    home = Path.home()
    brain = (
        Path(args.brain).expanduser()
        if args.brain
        else Path(__import__("os").environ.get("FORGE_BRAIN", str(home / "forge" / "brain"))).expanduser()
    )
    task_dir = brain / "prds" / args.task_id
    if not task_dir.is_dir():
        print(f"Tech plan verification FAILED: missing task dir {task_dir}", file=sys.stderr)
        return 1
    errs = verify_tech_plans(brain, args.task_id)
    if errs:
        print("Tech plan verification FAILED:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"OK: tech-plans for task {args.task_id!r} under {brain}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

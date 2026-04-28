#!/usr/bin/env python3
"""
Structural machine checks for per-repo tech plans under a brain task.

Catches common "looks complete" slips:
  - Missing canonical headings (### 1b.0, 1b.0b, 1b.2, 1b.2a, 1b.6, Section 1c)
  - ### 1b.2a placed before wire-map headings (### 1b.5 / #### 1b.5b)
  - REVIEW_PASS without file-embedded self-review anchors (inventory + recross)

Optional ``--strict-0c-inventory`` (also wired from verify_forge_task.py) adds
semantic rails for **REVIEW_PASS** plans only: inventory rows whose last table
column is exactly **GAP**, and — when certain task-bound files exist under
``prds/<task-id>/`` — a requirement that the inventory block cite those sources
(so **prd-locked-only** inventories fail when Confluence mirror, touchpoints,
or QA CSV are present). This does not replace human self-review; it blocks a
subset of rubber-stamps CI can see.

Stdlib only. Intended for CI via verify_forge_task.py --strict-tech-plans
or direct invocation:

  python3 tools/verify_tech_plans.py --task-id my-feature --brain ~/forge/brain
  python3 tools/verify_tech_plans.py --task-id my-feature --brain ~/forge/brain --strict-0c-inventory
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from forge_paths import default_brain_root, sanitize_task_id

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
        # Meta-documents in tech-plans/ that are not per-repo plan files.
        "human_signoff.md",
        "readme.md",
    }
)

RE_TABLE_SEP = re.compile(r"^\s*\|?[\s\-:|]+\|\s*$")


def _heading_body(line: str) -> str | None:
    m = RE_HEAD.match(line.rstrip())
    if not m:
        return None
    return m.group(2).strip()


def _heading_id(body: str) -> str:
    """First token of heading body (e.g. `1b.0 PRD↔scan` → `1b.0`)."""
    if not body:
        return ""
    return body.split()[0].rstrip(":;")


def _line_of_heading(lines: list[str], want: str) -> int | None:
    """First line (1-based) where the heading id equals `want` (exact token match)."""
    for i, ln in enumerate(lines, start=1):
        body = _heading_body(ln)
        if body is None:
            continue
        if _heading_id(body) == want:
            return i
    return None


def _lines_between_exact_markers(lines: list[str], start: str, end: str) -> tuple[list[str] | None, str | None]:
    """Lines strictly between markers; returns (lines, reason_if_missing)."""
    start_i: int | None = None
    for i, ln in enumerate(lines):
        if ln.strip() == start:
            start_i = i + 1
            break
    if start_i is None:
        return None, "missing_start"
    for j in range(start_i, len(lines)):
        if lines[j].strip() == end:
            return lines[start_i:j], None
    return None, "missing_end"


def _markdown_table_row_cells(line: str) -> list[str] | None:
    """Split a ``| … |`` table row into cells; ``None`` for non-rows / separators."""
    if "|" not in line:
        return None
    if RE_TABLE_SEP.match(line):
        return None
    raw = [p.strip() for p in line.split("|")]
    if raw and raw[0] == "":
        raw = raw[1:]
    if raw and raw[-1] == "":
        raw = raw[:-1]
    if len(raw) < 2:
        return None
    return raw


def _inventory_block_has_gap_last_column(inv_lines: list[str]) -> list[int]:
    """Return 1-based line numbers (within ``inv_lines``) where last cell is exactly ``GAP``."""
    bad: list[int] = []
    for i, ln in enumerate(inv_lines, start=1):
        cells = _markdown_table_row_cells(ln)
        if not cells:
            continue
        last = cells[-1].strip()
        if last.casefold() == "gap":
            bad.append(i)
    return bad


def _csv_data_row_count(csv_path: Path) -> int:
    if not csv_path.is_file():
        return 0
    try:
        text = csv_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    rows = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not rows:
        return 0
    n = 0
    for ln in rows[1:]:
        if ln.startswith("#"):
            continue
        n += 1
    return n


def _strict_0c_semantic_errors(
    rel: Path, lines: list[str], task_dir: Path
) -> list[str]:
    """
    When ``strict_0c_inventory`` is enabled and plan is REVIEW_PASS: fail on
    open GAP rows and on missing citations for task-bound inputs that exist.
    """
    errs: list[str] = []
    inv, inv_reason = _lines_between_exact_markers(lines, MARKER_0C, MARKER_RECROSS)
    if inv is None:
        reason = (
            "missing opening marker"
            if inv_reason == "missing_start"
            else "missing closing marker"
        )
        errs.append(
            f"{rel}: --strict-0c-inventory requires {MARKER_0C!r} and later "
            f"{MARKER_RECROSS!r} each on their own line, with inventory table between them "
            f"({reason})"
        )
        return errs
    gap_lines = _inventory_block_has_gap_last_column(inv)
    if gap_lines:
        errs.append(
            f"{rel}: Section 0c inventory has GAP in last column (lines "
            f"{', '.join(str(x) for x in gap_lines)} relative to inventory start) — "
            "close gaps or use explicit WAIVER text in that cell per tech-plan-self-review"
        )
    inv_blob = "\n".join(inv).casefold()

    confluence_names = ("prd-source-confluence.md", "source-confluence.md")
    if any((task_dir / name).is_file() for name in confluence_names):
        tokens = ("confluence", "prd-source-confluence", "source-confluence")
        if not any(t in inv_blob for t in tokens):
            errs.append(
                f"{rel}: task has prd-source-confluence.md or source-confluence.md but "
                "Section 0c inventory does not cite it — 'prd-locked only' inventory is BLOCKED"
            )

    tp_dir = task_dir / "touchpoints"
    if tp_dir.is_dir() and any(p.suffix.lower() == ".md" for p in tp_dir.iterdir() if p.is_file()):
        if not re.search(r"\btouchpoints\b", inv_blob):
            errs.append(
                f"{rel}: task has touchpoints/*.md but Section 0c inventory never cites "
                "'touchpoints/' — add ≥1 inventory row per tech-plan-write-per-project"
            )

    qa_csv = task_dir / "qa" / "manual-test-cases.csv"
    if _csv_data_row_count(qa_csv) > 0:
        if "manual-test-cases" not in inv_blob and "qa/manual" not in inv_blob:
            errs.append(
                f"{rel}: task has data rows in qa/manual-test-cases.csv but Section 0c "
                "inventory does not cite that file — add a row or WAIVER with token "
                "'manual-test-cases' or 'qa/manual'"
            )

    return errs


def verify_tech_plans(brain: Path, task_id: str, *, strict_0c_inventory: bool = False) -> list[str]:
    errors: list[str] = []
    try:
        task_id = sanitize_task_id(task_id)
    except ValueError as exc:
        return [str(exc)]
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

    task_dir = brain / "prds" / task_id

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

            if strict_0c_inventory:
                errors.extend(_strict_0c_semantic_errors(rel, lines, task_dir))

    return errors


def main() -> int:
    p = argparse.ArgumentParser(description="Verify tech plan structure under a brain task.")
    p.add_argument("--task-id", required=True)
    p.add_argument("--brain", default=None)
    p.add_argument(
        "--strict-0c-inventory",
        action="store_true",
        help=(
            "For REVIEW_PASS plans: fail on Section 0c inventory rows with last column GAP; "
            "when prd-source-confluence.md / source-confluence.md, touchpoints/*.md, or "
            "qa/manual-test-cases.csv (with data rows) exist under the task, require those "
            "sources to appear in the inventory block (substring check)."
        ),
    )
    args = p.parse_args()
    brain = Path(args.brain).expanduser() if args.brain else default_brain_root()
    try:
        task_id = sanitize_task_id(args.task_id)
    except ValueError as exc:
        print(f"Tech plan verification FAILED: {exc}", file=sys.stderr)
        return 1
    task_dir = brain / "prds" / task_id
    if not task_dir.is_dir():
        print(f"Tech plan verification FAILED: missing task dir {task_dir}", file=sys.stderr)
        return 1
    errs = verify_tech_plans(brain, task_id, strict_0c_inventory=args.strict_0c_inventory)
    if errs:
        print("Tech plan verification FAILED:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"OK: tech-plans for task {task_id!r} under {brain}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Drift check: surface text in prd-locked.md that may be missing from eval / QA artifacts.

Heuristic only — not a substitute for human review. Helps catch renamed journeys,
stale PRD text, or eval scenarios that never referenced acceptance language.

Usage:
  python3 tools/forge_drift_check.py --task-id <id> --brain ~/forge/brain
  python3 tools/forge_drift_check.py --task-id <id> --brain . --strict

Exit 1 on drift when --strict; otherwise prints WARN and exits 0.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from forge_paths import default_brain_root, sanitize_task_id


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _extract_success_criteria_bullets(prd_text: str) -> list[str]:
    m = re.search(
        r"(?ms)\*\*Success Criteria:\*\*\s*\n(.*?)(?=\n\*\*[A-Za-z /()]+\*\*:|\n---|\Z)",
        prd_text,
    )
    if not m:
        return []
    block = m.group(1)
    out: list[str] = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("- ") or line.startswith("* "):
            t = line.lstrip("-* ").strip()
            if len(t) >= 12:
                out.append(t)
    return out


def _combined_eval_text(eval_dir: Path) -> str:
    if not eval_dir.is_dir():
        return ""
    parts: list[str] = []
    for p in sorted(eval_dir.iterdir()):
        if p.suffix.lower() in (".yaml", ".yml", ".json"):
            try:
                parts.append(_read(p))
            except OSError as exc:
                print(f"WARN: unable to read {p}: {exc}", file=sys.stderr)
    return "\n".join(parts).casefold()


def _combined_qa_text(qa_csv: Path) -> str:
    if not qa_csv.is_file():
        return ""
    try:
        return _read(qa_csv).casefold()
    except OSError:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Drift check: PRD success criteria vs eval/QA text.")
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--brain", default=None)
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when any success-criterion bullet is absent from eval+QA text",
    )
    args = ap.parse_args()
    brain = Path(args.brain).expanduser() if args.brain else default_brain_root()
    try:
        task_id = sanitize_task_id(args.task_id)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    task_dir = brain / "prds" / task_id
    prd = task_dir / "prd-locked.md"
    if not prd.is_file():
        print(f"ERROR: missing {prd}", file=sys.stderr)
        return 1
    prd_text = _read(prd)
    bullets = _extract_success_criteria_bullets(prd_text)
    if not bullets:
        print("INFO: No **Success Criteria:** bullets found (or section missing); nothing to drift-check.")
        return 0

    hay = _combined_eval_text(task_dir / "eval") + "\n" + _combined_qa_text(task_dir / "qa" / "manual-test-cases.csv")
    hay_cf = hay.casefold()
    missing: list[str] = []
    for b in bullets:
        key = b.casefold()
        if key not in hay_cf:
            missing.append(b)

    if not missing:
        print(f"OK: {len(bullets)} success-criteria bullet(s) have substring matches in eval/QA text.")
        return 0

    for m in missing:
        print(f"WARN: Success criterion not found in eval/*.yaml nor qa/manual-test-cases.csv:\n  - {m[:200]}", file=sys.stderr)
    if args.strict:
        print("ERROR: --strict drift check failed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

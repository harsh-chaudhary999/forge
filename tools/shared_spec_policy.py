"""
Validate shared-dev-spec.md against a portable JSON checklist + TBD scan.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

MARKERS = re.compile(r"\b(TBD|TODO)\b", re.IGNORECASE)
DEFAULT_CHECKLIST = Path(__file__).resolve().parent / "shared_spec_checklist.json"


def _load_checklist(path: Path | None) -> dict[str, Any]:
    p = path or DEFAULT_CHECKLIST
    if not p.is_file():
        return {"schema_version": 1, "required_substrings": []}
    return json.loads(p.read_text(encoding="utf-8"))


def tbd_violations(text: str) -> list[str]:
    """Same spirit as check_frozen_spec.py — skip fenced blocks."""
    errs: list[str] = []
    in_fence = False
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("#") and "TBD" in stripped.upper():
            continue
        if MARKERS.search(line):
            errs.append(f"shared-dev-spec.md line {i}: TBD/TODO in prose — {line.rstrip()[:160]!r}")
    return errs


def validate_shared_spec(
    spec_path: Path,
    *,
    checklist_path: Path | None = None,
) -> list[str]:
    errs: list[str] = []
    if not spec_path.is_file():
        errs.append(f"shared-dev-spec missing: {spec_path}")
        return errs
    text = spec_path.read_text(encoding="utf-8", errors="replace")
    data = _load_checklist(checklist_path)
    for s in data.get("required_substrings", []):
        if s not in text:
            errs.append(f"shared-dev-spec: missing required anchor {s!r}")
    errs.extend(tbd_violations(text))
    return errs


__all__ = ["validate_shared_spec", "tbd_violations", "DEFAULT_CHECKLIST"]

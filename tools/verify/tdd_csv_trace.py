"""
Machine checks for forge-tdd ↔ QA CSV traceability.

Tests under the task (see ``collect_tdd_scan_py_files``) should cite manual or semantic
step ids using::

    # forge-tdd: TC-001 (manual-test-cases.csv)
    # forge-tdd: step-login (semantic-automation.csv)

Optional **Required** column on ``qa/manual-test-cases.csv`` (yes/true/1/y) forces at
least one such marker per required Id.
"""

from __future__ import annotations

import re
from pathlib import Path

from semantic_csv import parse_manual_test_cases_full, parse_semantic_automation_csv

# Leading comment only; id token is first non-whitespace after the colon.
FORGE_TDD_MARKER_RE = re.compile(r"^\s*#\s*forge-tdd:\s*(\S+)", re.IGNORECASE | re.MULTILINE)


def collect_tdd_scan_py_files(task_dir: Path) -> tuple[list[Path], list[str]]:
    """
    Python files scanned for ``# forge-tdd:`` markers.

    If ``qa/tdd-scan-paths.txt`` exists and has non-comment lines, only those paths are
    used (no implicit fallback). Each line is relative to the task dir unless absolute:

    - Directory → all ``test_*.py`` and ``*_test.py`` under it (recursive).
    - Glob → resolved under ``task_dir`` (e.g. ``design/repo/tests/test_*.py``).
    - File → that ``.py`` path.

    Otherwise: all ``test_*.py`` / ``*_test.py`` under ``task_dir`` (recursive).
    """
    errs: list[str] = []
    paths_file = task_dir / "qa" / "tdd-scan-paths.txt"
    found: set[Path] = set()
    explicit = False

    if paths_file.is_file():
        raw_lines = paths_file.read_text(encoding="utf-8", errors="replace").splitlines()
        entries = [
            ln.strip()
            for ln in raw_lines
            if ln.strip() and not ln.strip().startswith("#")
        ]
        if entries:
            explicit = True
        td_resolved = task_dir.resolve()
        for line in entries:
            candidate = Path(line)
            p = candidate.resolve() if candidate.is_absolute() else (task_dir / line).resolve()
            try:
                p.relative_to(td_resolved)
            except ValueError:
                errs.append(f"tdd-scan-paths.txt: path escapes task dir: {line!r}")
                continue
            if p.is_dir():
                for pat in ("test_*.py", "*_test.py"):
                    found.update(p.rglob(pat))
            elif "*" in line or "?" in line:
                for match in task_dir.glob(line):
                    try:
                        match.resolve().relative_to(td_resolved)
                        found.add(match)
                    except ValueError:
                        errs.append(f"tdd-scan-paths.txt: glob match escapes task dir: {match}")
            elif p.is_file() and p.suffix.lower() == ".py":
                found.add(p)

    if not explicit:
        for pat in ("test_*.py", "*_test.py"):
            found.update(task_dir.rglob(pat))
    elif explicit and not found:
        errs.append(
            "qa/tdd-scan-paths.txt: no matching test_*.py or *_test.py files "
            "(fix globs or directories)"
        )

    files = sorted({x for x in found if x.is_file()}, key=lambda x: str(x))
    return files, errs


def extract_forge_tdd_markers(py_path: Path) -> list[tuple[str, int]]:
    """Return list of (referenced_id, 1-based line number)."""
    try:
        text = py_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    out: list[tuple[str, int]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        m = FORGE_TDD_MARKER_RE.match(line)
        if m:
            out.append((m.group(1).strip(), i))
    return out


def combined_forge_tdd_marker_haystack(task_dir: Path) -> str:
    """Concatenate ``# forge-tdd:`` lines from scanned files (for drift substring checks)."""
    files, _errs = collect_tdd_scan_py_files(task_dir)
    parts: list[str] = []
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if FORGE_TDD_MARKER_RE.match(line):
                parts.append(line.strip())
    return "\n".join(parts)


def verify_tdd_csv_trace(task_dir: Path) -> list[str]:
    """
    Validate ``# forge-tdd:`` markers in scanned tests vs manual + semantic-automation ids,
    and ensure every **Required** manual row has at least one marker.
    """
    errs: list[str] = []

    manual_csv = task_dir / "qa" / "manual-test-cases.csv"
    semantic_csv = task_dir / "qa" / "semantic-automation.csv"

    manual_ids, required_ids, m_errs = parse_manual_test_cases_full(manual_csv)
    errs.extend(m_errs)

    semantic_ids: set[str] = set()
    if semantic_csv.is_file():
        steps, s_errs = parse_semantic_automation_csv(semantic_csv)
        errs.extend(s_errs)
        semantic_ids = {s.id for s in steps}

    valid_ids = manual_ids | semantic_ids

    py_files, scan_errs = collect_tdd_scan_py_files(task_dir)
    errs.extend(scan_errs)

    refs_from_tests: dict[str, list[str]] = {}
    for py_path in py_files:
        rel = py_path
        try:
            rel = py_path.relative_to(task_dir.resolve())
        except ValueError:
            pass
        for token, ln in extract_forge_tdd_markers(py_path):
            if token not in valid_ids:
                errs.append(
                    f"TDD trace: unknown forge-tdd id {token!r} in {rel}:{ln} "
                    f"(not in manual-test-cases.csv Id set nor semantic-automation.csv Id)"
                )
            refs_from_tests.setdefault(token, []).append(f"{rel}:{ln}")

    if required_ids:
        if not py_files:
            errs.append(
                "TDD trace: manual-test-cases.csv has Required=yes rows but no Python "
                "test files were scanned — add qa/tdd-scan-paths.txt or place test_*.py "
                "under the task directory"
            )
        for rid in sorted(required_ids):
            if rid not in refs_from_tests:
                errs.append(
                    f"TDD trace: manual Id {rid!r} is Required=yes but no "
                    f"# forge-tdd: {rid} marker was found in scanned tests"
                )

    return errs

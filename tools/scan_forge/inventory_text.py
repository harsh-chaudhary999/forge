"""Reusable parsing of grep ``-rn`` inventory lines and language hints."""

from __future__ import annotations

import re
from pathlib import Path


def parse_grep_line(line: str) -> tuple[str, str, str]:
    """Split ``path:lineno:content`` from grep ``-rn`` output."""
    m = re.search(r":([0-9]+):", line)
    if not m:
        return "", "", ""
    lineno = m.group(1)
    start = m.start()
    file = line[:start]
    content = line[m.end() :]
    return file, lineno, content


def detect_language(path: str) -> str:
    """Rough language label from file extension (for brain stubs)."""
    p = path.lower()
    if p.endswith(".java"):
        return "Java"
    if p.endswith(".kt"):
        return "Kotlin"
    if p.endswith(".go"):
        return "Go"
    if p.endswith(".ts"):
        return "TypeScript"
    if p.endswith(".tsx"):
        return "TypeScript (TSX)"
    if p.endswith(".js"):
        return "JavaScript"
    if p.endswith(".jsx"):
        return "JavaScript (JSX)"
    if p.endswith(".py"):
        return "Python"
    if p.endswith(".dart"):
        return "Dart"
    if p.endswith(".rs"):
        return "Rust"
    if p.endswith(".rb"):
        return "Ruby"
    if p.endswith(".swift"):
        return "Swift"
    return "Unknown"


def repo_relative_posix(repo: Path, abs_path_s: str) -> str | None:
    """Return posix path relative to ``repo`` or ``None`` if outside."""
    try:
        return str(Path(abs_path_s).resolve().relative_to(repo.resolve()).as_posix())
    except ValueError:
        return None

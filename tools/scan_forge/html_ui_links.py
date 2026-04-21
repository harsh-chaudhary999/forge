"""Resolve <script src> / modulepreload href in HTML to repo-relative paths for brain wikilinks."""

from __future__ import annotations

import re
from pathlib import Path

SCRIPT_SRC_RE = re.compile(
    r"<script\b[^>]*\bsrc\s*=\s*[\"']([^\"']+)[\"']",
    re.IGNORECASE | re.DOTALL,
)
LINK_TAG_RE = re.compile(r"<link\b([^>]+)>", re.IGNORECASE)


def _resolve_href_to_repo_rel(
    href: str,
    html_dir: Path,
    repo: Path,
) -> str | None:
    href = href.strip()
    if not href or href.startswith(("http://", "https://", "//", "data:", "blob:")):
        return None
    repo_r = repo.resolve()
    if href.startswith("/"):
        target = (repo_r / href.lstrip("/")).resolve()
    else:
        target = (html_dir / href).resolve()
    try:
        rel = target.relative_to(repo_r).as_posix()
    except ValueError:
        return None
    if target.is_file():
        return rel
    return None


def html_linked_asset_paths(html_path: Path, repo: Path) -> list[str]:
    """Return sorted unique repo-relative paths for script/modulepreload targets that exist."""
    repo = repo.resolve()
    html_path = html_path.resolve()
    try:
        text = html_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    html_dir = html_path.parent
    out: list[str] = []
    seen: set[str] = set()
    for m in SCRIPT_SRC_RE.finditer(text):
        rel = _resolve_href_to_repo_rel(m.group(1), html_dir, repo)
        if rel and rel not in seen:
            seen.add(rel)
            out.append(rel)
    for m in LINK_TAG_RE.finditer(text):
        block = m.group(1)
        if not re.search(r'rel\s*=\s*["\']modulepreload["\']', block, re.I):
            continue
        hm = re.search(r'href\s*=\s*["\']([^"\']+)["\']', block, re.I)
        if not hm:
            continue
        rel = _resolve_href_to_repo_rel(hm.group(1), html_dir, repo)
        if rel and rel not in seen:
            seen.add(rel)
            out.append(rel)
    out.sort()
    return out

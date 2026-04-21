"""Resolve static ESM import / export-from specifiers to repo-relative paths for brain wikilinks."""

from __future__ import annotations

import re
from pathlib import Path

# `import ... from 'x'`, `export ... from 'x'`, `export * from 'x'` (single-line friendly)
_IMPORT_EXPORT_FROM = re.compile(
    r"""(?m)^\s*(?:export\s+(?:\*|\{[^}]*\}\s*|type\s+|default\s+)?(?:[\w*]+\s+)?from|import\s+(?:type\s+)?(?:[\w*{}\s,]+\s+from))\s*["']([^"']+)["']""",
)
# `import 'side-effect'`
_IMPORT_SIDE_EFFECT = re.compile(r'^\s*import\s+["\']([^"\']+)["\']', re.M)

_MODULE_EXTS = (".tsx", ".jsx", ".ts", ".js", ".mjs", ".cjs")


def _finalize_file_candidate(cand: Path, repo_r: Path) -> Path | None:
    cand = cand.resolve()
    try:
        cand.relative_to(repo_r)
    except ValueError:
        return None
    if cand.is_file():
        return cand
    low = cand.suffix.lower()
    if low in (".tsx", ".jsx", ".ts", ".js", ".mjs", ".cjs"):
        return None
    for ext in _MODULE_EXTS:
        p = cand.with_suffix(ext)
        if p.is_file():
            return p.resolve()
    if cand.is_dir():
        for n in ("index.tsx", "index.jsx", "index.ts", "index.js"):
            p = (cand / n).resolve()
            if p.is_file():
                return p
    return None


def _resolve_spec_to_repo_rel(spec: str, importer_dir: Path, repo: Path) -> str | None:
    s = spec.strip()
    if not s or s.startswith(("http://", "https://", "//", "data:", "node:", "blob:")):
        return None
    if "?" in s:
        s = s.split("?", 1)[0]
    if not (s.startswith(".") or s.startswith("/")):
        return None
    repo_r = repo.resolve()
    if s.startswith("/"):
        cand = (repo_r / s.lstrip("/")).resolve()
    else:
        cand = (importer_dir / s).resolve()
    fin = _finalize_file_candidate(cand, repo_r)
    if not fin:
        return None
    return fin.relative_to(repo_r).as_posix()


def static_import_targets(source_path: Path, repo: Path) -> list[str]:
    """Sorted unique repo-relative paths for local static imports/exports that resolve to files."""
    repo = repo.resolve()
    source_path = source_path.resolve()
    try:
        text = source_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    importer_dir = source_path.parent
    out: list[str] = []
    seen: set[str] = set()
    for rx in (_IMPORT_EXPORT_FROM, _IMPORT_SIDE_EFFECT):
        for m in rx.finditer(text):
            rel = _resolve_spec_to_repo_rel(m.group(1), importer_dir, repo)
            if rel and rel not in seen:
                seen.add(rel)
                out.append(rel)
    out.sort()
    return out

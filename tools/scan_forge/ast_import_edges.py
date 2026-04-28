"""Optional import/export edge extraction (TypeScript/JavaScript + Python)."""

from __future__ import annotations

import importlib
import os
import re
from pathlib import Path

from . import log

try:
    from tree_sitter import Language, Parser  # type: ignore[import-not-found]

    _HAS_TS_CORE = True
except ImportError:
    Language = None  # type: ignore[misc, assignment]
    Parser = None  # type: ignore[misc, assignment]
    _HAS_TS_CORE = False

_TSJS_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
_PY_EXT = {".py"}

_TS_IMPORT_RE = re.compile(
    r"""^\s*(?:import\s+(?:type\s+)?(?:[\w*{}\s,]+?\s+from\s+)?|export\s+(?:\*|{[^}]*}|type\s+[^=]+)\s+from\s+)["']([^"']+)["']""",
)
_PY_FROM_RE = re.compile(r"^\s*from\s+([A-Za-z0-9_\.]+)\s+import\s+")
_PY_IMPORT_RE = re.compile(r"^\s*import\s+([A-Za-z0-9_\.]+)")


def _load_lang(mod_name: str, attr: str) -> Language | None:
    if not _HAS_TS_CORE or Language is None:
        return None
    try:
        mod = importlib.import_module(mod_name)
        raw = getattr(mod, attr)
        ptr = raw() if callable(raw) else raw
        return Language(ptr)
    except Exception:
        return None


def _build_parsers() -> dict[str, Parser]:
    if not _HAS_TS_CORE or Parser is None:
        return {}
    out: dict[str, Parser] = {}
    ts_lang = _load_lang("tree_sitter_typescript", "language_typescript")
    tsx_lang = _load_lang("tree_sitter_typescript", "language_tsx")
    js_lang = _load_lang("tree_sitter_javascript", "language")
    py_lang = _load_lang("tree_sitter_python", "language")
    if ts_lang is not None:
        p = Parser(ts_lang)
        out[".ts"] = p
        out[".mts"] = p
        out[".cts"] = p
    if tsx_lang is not None:
        out[".tsx"] = Parser(tsx_lang)
    if js_lang is not None:
        p = Parser(js_lang)
        out[".js"] = p
        out[".jsx"] = p
        out[".mjs"] = p
        out[".cjs"] = p
    if py_lang is not None:
        out[".py"] = Parser(py_lang)
    return out


def _ast_import_lines(source: bytes, parser: Parser) -> set[int]:
    tree = parser.parse(source)
    lines: set[int] = set()
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        ntype = node.type.lower()
        if "import" in ntype or ntype in {"export_statement", "export_clause"}:
            lines.add(node.start_point[0] + 1)
        stack.extend(node.children)
    return lines


def _resolve_python_target(mod: str) -> str:
    return mod.replace(".", "/")


def append_import_edges(repos: list[Path], run_dir: Path) -> int:
    """Write `forge_scan_ast_import_edges.tsv` (repo, rel, line, kind, target, provenance)."""
    flag = os.environ.get("FORGE_SCAN_AST_IMPORTS", "").strip().lower()
    out_path = run_dir.resolve() / "forge_scan_ast_import_edges.tsv"
    if flag not in ("1", "true", "yes"):
        out_path.write_text("", encoding="utf-8")
        log.log_stat("phase=5.import_edges skipped=env_disabled")
        return 0

    parsers = _build_parsers()
    rows: list[str] = []
    for repo in repos:
        repo = repo.resolve()
        rname = repo.name
        for fp in repo.rglob("*"):
            if not fp.is_file():
                continue
            try:
                rel = fp.relative_to(repo).as_posix()
            except ValueError:
                continue
            low = rel.lower()
            if "node_modules/" in low or "/dist/" in low or "/build/" in low or "/.git/" in low:
                continue
            ext = fp.suffix.lower()
            if ext not in _TSJS_EXT and ext not in _PY_EXT:
                continue
            try:
                src = fp.read_bytes()
                lines = src.decode("utf-8", errors="replace").splitlines()
            except OSError:
                continue
            ast_lines: set[int] = set()
            parser = parsers.get(ext)
            if parser is not None:
                try:
                    ast_lines = _ast_import_lines(src, parser)
                except Exception:
                    ast_lines = set()

            for idx, line in enumerate(lines, start=1):
                target = ""
                kind = "IMPORT"
                m = _TS_IMPORT_RE.match(line)
                if m and ext in _TSJS_EXT:
                    target = m.group(1)
                    if line.lstrip().startswith("export"):
                        kind = "EXPORT_REF"
                elif ext in _PY_EXT:
                    fm = _PY_FROM_RE.match(line)
                    im = _PY_IMPORT_RE.match(line)
                    if fm:
                        target = _resolve_python_target(fm.group(1))
                        kind = "IMPORT"
                    elif im:
                        target = _resolve_python_target(im.group(1))
                        kind = "IMPORT"
                if not target:
                    continue
                prov = "AST" if idx in ast_lines else "HEURISTIC"
                rows.append(f"{rname}\t{rel}\t{idx}\t{kind}\t{target}\t{prov}")

    rows = sorted(set(rows))
    out_path.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    log.log_stat(f"phase=5.import_edges rows={len(rows)} output={out_path}")
    return len(rows)

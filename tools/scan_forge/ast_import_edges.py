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
_TS_REQUIRE_RE = re.compile(r"""^\s*(?:const|let|var)\s+[\w$]+\s*=\s*require\(["']([^"']+)["']\)""")
_PY_FROM_RE = re.compile(r"^\s*from\s+([A-Za-z0-9_\.]+)\s+import\s+")
_PY_IMPORT_RE = re.compile(r"^\s*import\s+([A-Za-z0-9_\.,\s]+)")


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


def _resolve_local_target_rel(source_rel: str, spec: str) -> str | None:
    """Resolve relative import specs to repo-relative-ish paths (without existence checks)."""
    s = (spec or "").strip()
    if not s:
        return None
    if s.startswith("/"):
        return s.lstrip("/")
    if not s.startswith("."):
        return None
    parent = Path(source_rel).parent.as_posix()
    raw = f"{parent}/{s}" if parent and parent != "." else s
    parts: list[str] = []
    for seg in raw.split("/"):
        if not seg or seg == ".":
            continue
        if seg == "..":
            if parts:
                parts.pop()
            continue
        parts.append(seg)
    return "/".join(parts) if parts else None


def _python_targets_from_import(line: str) -> list[str]:
    """Extract one or more python import targets from `import a, b as c`."""
    m = _PY_IMPORT_RE.match(line)
    if not m:
        return []
    raw = m.group(1)
    out: list[str] = []
    for part in raw.split(","):
        token = part.strip().split(" as ", 1)[0].strip()
        if token:
            out.append(_resolve_python_target(token))
    return out


def append_import_edges(repos: list[Path], run_dir: Path) -> int:
    """Write `forge_scan_ast_import_edges.tsv`.

    Columns:
    repo, rel, line, edge_kind, target_spec, provenance, resolved_target_rel
    """
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
                candidates: list[tuple[str, str]] = []
                m = _TS_IMPORT_RE.match(line)
                if m and ext in _TSJS_EXT:
                    kind = "EXPORT_REF" if line.lstrip().startswith("export") else "IMPORT"
                    candidates.append((kind, m.group(1)))
                rq = _TS_REQUIRE_RE.match(line)
                if rq and ext in _TSJS_EXT:
                    candidates.append(("IMPORT", rq.group(1)))
                if ext in _PY_EXT:
                    fm = _PY_FROM_RE.match(line)
                    if fm:
                        candidates.append(("IMPORT", _resolve_python_target(fm.group(1))))
                    for t in _python_targets_from_import(line):
                        candidates.append(("IMPORT", t))

                for kind, target in candidates:
                    if not target:
                        continue
                    resolved = _resolve_local_target_rel(rel, target) or ""
                    if idx in ast_lines:
                        prov = "AST_STRONG" if resolved else "AST_WEAK"
                    else:
                        prov = "HEURISTIC"
                    rows.append(
                        f"{rname}\t{rel}\t{idx}\t{kind}\t{target}\t{prov}\t{resolved}"
                    )

    rows = sorted(set(rows))
    out_path.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    log.log_stat(f"phase=5.import_edges rows={len(rows)} output={out_path}")
    return len(rows)

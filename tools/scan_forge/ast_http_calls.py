"""Optional Tree-sitter pass: HTTP-shaped calls across supported languages.

Parses source with the appropriate `tree-sitter-*` grammar, finds call-like nodes,
and appends lines to ``forge_scan_ast_http_calls.txt`` (same ``repo\\trel:lineno:content``
shape as phase 5.1 grep). Phase 5 merges that file into ``forge_scan_all_callsites.txt``
for phase56.

Disable with ``FORGE_SCAN_AST=0``. If the core ``tree_sitter`` package is missing, no-ops.
Individual grammars that fail to import are skipped; others still run.

Canonical upstream docs (parser model, bindings, grammar ecosystem):
https://tree-sitter.github.io/tree-sitter/
"""

from __future__ import annotations

import importlib
import os
import re
from pathlib import Path

from . import log

try:
    from tree_sitter import Language, Node, Parser  # type: ignore[import-not-found]

    _HAS_CORE = True
except ImportError:
    Language = None  # type: ignore[misc, assignment]
    Node = object  # type: ignore[misc, assignment]
    Parser = None  # type: ignore[misc, assignment]
    _HAS_CORE = False

# True when core bindings import (grammars may still be partially missing).
AST_HTTP_AVAILABLE = _HAS_CORE

_HTTP_MEMBER_VERBS = frozenset(
    {
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "head",
        "options",
        "request",
    },
)
_DIRECT_CALLEES = frozenset({"fetch", "$fetch", "ofetch", "useFetch"})
_TEST_PATH = re.compile(r"/(test|tests|__tests__|e2e|spec)/|\.test\.|\.spec\.|/testing/")
_MAX_FILE_BYTES = 900_000

# Node types that often represent a callable invocation (varies by grammar).
_CALL_NODE_TYPES = frozenset(
    {
        "call_expression",
        "call",
        "method_invocation",
        "invocation_expression",
        "function_call_expression",
        "function_call",
        "message_expression",
        "command",  # PowerShell
    },
)

# Line must suggest an HTTP client / route-ish call (reduces noise in C/Verilog/etc.).
_HTTP_LINE_HINT = re.compile(
    r"requests\.|httpx\.|aiohttp\.|urllib3\.|urllib\.|http\.Client|http\.Get|http\.Post|http\.Put|"
    r"http\.Patch|http\.Delete|RestTemplate|WebClient|OkHttp|@Feign|FeignClient|reqwest|ureq::|"
    r"surf::|hyper::|retrofit\.|@GET\b|@POST\b|@PUT\b|@DELETE\b|@PATCH\b|dio\.|"
    r"fetch\s*\(|axios|\$fetch|ofetch|useFetch|apiClient|HTTPoison\.|Tesla\.|"
    r"Invoke-RestMethod|Invoke-WebRequest|RestMethod\b|"
    r"URLSession|dataTask|http\.get|http\.post|http\.newRequest|Client\.|Session\.|"
    r"\.get\(|\.post\(|\.put\(|\.delete\(|\.patch\(|\.head\(|\.options\(|"
    r"file_get_contents|curl_exec|wp_remote_",
    re.I,
)

# (file extensions…), python_module, attribute_name on module returning Language pointer factory
_GRAMMAR_SPECS: list[tuple[tuple[str, ...], str, str]] = [
    ((".js", ".jsx", ".mjs", ".cjs"), "tree_sitter_javascript", "language"),
    ((".ts", ".mts", ".cts"), "tree_sitter_typescript", "language_typescript"),
    ((".tsx",), "tree_sitter_typescript", "language_tsx"),
    ((".py", ".pyi"), "tree_sitter_python", "language"),
    ((".go",), "tree_sitter_go", "language"),
    ((".rs",), "tree_sitter_rust", "language"),
    ((".java",), "tree_sitter_java", "language"),
    ((".c", ".h"), "tree_sitter_c", "language"),
    ((".cc", ".cpp", ".cxx", ".hpp", ".hh", ".hxx"), "tree_sitter_cpp", "language"),
    ((".rb", ".rake"), "tree_sitter_ruby", "language"),
    ((".cs",), "tree_sitter_c_sharp", "language"),
    ((".kt", ".kts"), "tree_sitter_kotlin", "language"),
    ((".scala", ".sc"), "tree_sitter_scala", "language"),
    ((".php", ".php3", ".phtml"), "tree_sitter_php", "language_php"),
    ((".swift",), "tree_sitter_swift", "language"),
    ((".lua",), "tree_sitter_lua", "language"),
    ((".zig",), "tree_sitter_zig", "language"),
    ((".ps1", ".psm1", ".psd1"), "tree_sitter_powershell", "language"),
    ((".ex", ".exs"), "tree_sitter_elixir", "language"),
    ((".m", ".mm"), "tree_sitter_objc", "language"),
    ((".jl",), "tree_sitter_julia", "language"),
    ((".v", ".sv", ".svh"), "tree_sitter_verilog", "language"),
]

_CALLSITE_SOURCES = (
    "forge_scan_js_calls.txt",
    "forge_scan_java_calls.txt",
    "forge_scan_kotlin_calls.txt",
    "forge_scan_python_calls.txt",
    "forge_scan_go_calls.txt",
    "forge_scan_dart_calls.txt",
    "forge_scan_ast_http_calls.txt",
)

_JS_LIKE_EXT = frozenset({".js", ".jsx", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".tsx"})


def _load_language(mod_name: str, attr: str) -> Language | None:
    if not _HAS_CORE or Language is None:
        return None
    try:
        mod = importlib.import_module(mod_name)
    except ImportError:
        return None
    fn = getattr(mod, attr, None)
    if fn is None:
        return None
    try:
        ptr = fn() if callable(fn) else fn
        return Language(ptr)
    except (ValueError, TypeError, AttributeError):
        return None


def _build_extension_parsers() -> tuple[dict[str, Parser], int]:
    """Map file suffix (``lower``, includes dot) → ``Parser``. Returns (map, grammars_loaded)."""
    if not _HAS_CORE or Parser is None or Language is None:
        return {}, 0
    ext_map: dict[str, Parser] = {}
    loaded = 0
    seen_lang: set[int] = set()
    for exts, mod_name, attr in _GRAMMAR_SPECS:
        lang = _load_language(mod_name, attr)
        if lang is None:
            continue
        lid = id(lang)
        if lid not in seen_lang:
            seen_lang.add(lid)
            loaded += 1
        parser = Parser(lang)
        for ext in exts:
            ext_map[ext.lower()] = parser
    return ext_map, loaded


def _parser_for_suffix(ext_map: dict[str, Parser], path: Path) -> Parser | None:
    suf = path.suffix.lower()
    if not suf:
        return None
    return ext_map.get(suf)


def _callee_node(call_node: Node) -> Node | None:
    fn = call_node.child_by_field_name("function")
    if fn is not None:
        return fn
    for c in call_node.children:
        if c.type in ("identifier", "member_expression"):
            return c
    return None


def _callee_matches_js_http(callee: Node | None, source: bytes) -> bool:
    if callee is None:
        return False
    if callee.type == "identifier":
        name = source[callee.start_byte : callee.end_byte].decode("utf-8", "replace")
        return name in _DIRECT_CALLEES
    if callee.type == "member_expression":
        prop = callee.child_by_field_name("property")
        if prop is None:
            return False
        raw = source[prop.start_byte : prop.end_byte].decode("utf-8", "replace")
        base = raw.lstrip("_").split(".")[-1]
        return base.lower() in _HTTP_MEMBER_VERBS
    return False


def _iter_callish_nodes(root: Node) -> list[Node]:
    out: list[Node] = []
    stack: list[Node] = [root]
    while stack:
        n = stack.pop()
        if n.type in _CALL_NODE_TYPES:
            out.append(n)
        for c in n.children:
            stack.append(c)
    return out


def _parse_existing_call_keys(scan_tmp: Path) -> set[tuple[str, str, int]]:
    keys: set[tuple[str, str, int]] = set()
    for fname in _CALLSITE_SOURCES:
        p = scan_tmp / fname
        if not p.is_file():
            continue
        for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if "\t" not in ln:
                continue
            repo, rest = ln.split("\t", 1)
            parts = rest.split(":", 2)
            if len(parts) < 3:
                continue
            rel, lineno_s = parts[0], parts[1]
            try:
                keys.add((repo, rel, int(lineno_s)))
            except ValueError:
                continue
    return keys


def _should_emit_line(
    *,
    path: Path,
    node: Node,
    source: bytes,
    lines: list[str],
) -> bool:
    row0 = node.start_point[0]
    if row0 < 0 or row0 >= len(lines):
        return False
    content = lines[row0].rstrip("\r\n")
    from .phase56 import _urls_in_content

    if not _urls_in_content(content):
        return False
    suf = path.suffix.lower()
    if suf in _JS_LIKE_EXT and node.type == "call_expression":
        callee = _callee_node(node)
        if _callee_matches_js_http(callee, source):
            return True
    return bool(_HTTP_LINE_HINT.search(content))


def append_ast_http_calls(repos: list[Path], scan_tmp: Path) -> int:
    """Walk repos with every loadable Tree-sitter grammar; append to ``forge_scan_ast_http_calls.txt``."""
    flag = os.environ.get("FORGE_SCAN_AST", "").strip().lower()
    if flag in ("0", "false", "no", "off"):
        log.log_stat("phase=5.1.ast_skipped reason=FORGE_SCAN_AST")
        return 0
    ext_map, grammars_loaded = _build_extension_parsers()
    if not ext_map:
        if not _HAS_CORE:
            log.log_stat("phase=5.1.ast_skipped reason=tree_sitter_core_missing")
        else:
            log.log_stat("phase=5.1.ast_skipped reason=no_grammars_imported")
        return 0

    out_path = scan_tmp / "forge_scan_ast_http_calls.txt"
    existing = _parse_existing_call_keys(scan_tmp)
    new_lines: list[str] = []

    for repo in repos:
        repo = repo.resolve()
        name = repo.name
        for p in repo.rglob("*"):
            if not p.is_file():
                continue
            try:
                rel = p.relative_to(repo).as_posix()
            except ValueError:
                continue
            if "node_modules" in rel or "/dist/" in rel or "/build/" in rel:
                continue
            if _TEST_PATH.search(rel):
                continue
            try:
                if p.stat().st_size > _MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            parser = _parser_for_suffix(ext_map, p)
            if parser is None:
                continue
            try:
                source = p.read_bytes()
            except OSError:
                continue
            tree = parser.parse(source)
            lines = source.decode("utf-8", errors="replace").splitlines()
            for node in _iter_callish_nodes(tree.root_node):
                if not _should_emit_line(path=p, node=node, source=source, lines=lines):
                    continue
                lineno = node.start_point[0] + 1
                key = (name, rel, lineno)
                if key in existing:
                    continue
                existing.add(key)
                content = lines[node.start_point[0]].rstrip("\r\n")
                new_lines.append(f"{name}\t{rel}:{lineno}:{content}")

    if not new_lines:
        log.log_stat(f"phase=5.1.ast_appended=0 grammars_loaded={grammars_loaded}")
        return 0
    with out_path.open("a", encoding="utf-8", errors="replace") as f:
        for ln in sorted(new_lines):
            f.write(ln + "\n")
    log.log_stat(f"phase=5.1.ast_appended={len(new_lines)} grammars_loaded={grammars_loaded}")
    return len(new_lines)


# Backwards-compatible name (older callers / docs).
def append_ast_js_http_calls(repos: list[Path], scan_tmp: Path) -> int:
    return append_ast_http_calls(repos, scan_tmp)

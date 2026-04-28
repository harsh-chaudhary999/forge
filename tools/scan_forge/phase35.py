from __future__ import annotations

import re
from pathlib import Path

from . import grep_util, log, openapi_routes


_JS_ROUTE_RE = re.compile(
    r"\b(?:app|router)\.(get|post|put|patch|delete|head|options|all|use)\s*\(\s*['\"`]([^'\"`]+)['\"`]",
    re.IGNORECASE,
)
_JS_ROUTE_CHAIN_RE = re.compile(
    r"\b(?:app|router)\.route\s*\(\s*['\"`]([^'\"`]+)['\"`]\s*\)\s*\.(get|post|put|patch|delete|head|options|all)\s*\(",
    re.IGNORECASE,
)
_SPRING_MAP_RE = re.compile(
    r"@(Get|Post|Put|Patch|Delete|Request)Mapping\s*\(([^)]*)\)",
    re.IGNORECASE,
)
_SPRING_SIMPLE_MAP_RE = re.compile(
    r"@(Get|Post|Put|Patch|Delete|Request)Mapping\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
    re.IGNORECASE,
)
_SPRING_ATTR_PATH_RE = re.compile(r"(?:value|path)\s*=\s*['\"]([^'\"]+)['\"]")
_SPRING_CLASS_MAP_RE = re.compile(
    r"@RequestMapping\s*\(([^)]*)\)\s*(?:public|private|protected|abstract|final|\s)*class\s+[A-Za-z_][A-Za-z0-9_]*",
    re.IGNORECASE | re.MULTILINE,
)
_NEST_CONTROLLER_RE = re.compile(r"@Controller\s*\(\s*['\"`]([^'\"`]*)['\"`]\s*\)", re.IGNORECASE)
_NEST_METHOD_RE = re.compile(r"@(Get|Post|Put|Patch|Delete)\s*\(\s*['\"`]([^'\"`]*)['\"`]\s*\)", re.IGNORECASE)
_REQ_ASSIGN_RE = re.compile(
    r"(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*require\(\s*['\"]([^'\"]+)['\"]\s*\)",
)
_USE_DIRECT_REQUIRE_RE = re.compile(
    r"\b(?:app|router)\.use\(\s*['\"`]([^'\"`]+)['\"`]\s*,\s*require\(\s*['\"]([^'\"]+)['\"]\s*\)",
    re.IGNORECASE,
)
_USE_VAR_RE = re.compile(
    r"\b(?:app|router)\.use\(\s*['\"`]([^'\"`]+)['\"`]\s*,\s*([A-Za-z_$][A-Za-z0-9_$]*)",
    re.IGNORECASE,
)
_JS_ROUTE_EXTS = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts")


def _norm_route(path: str) -> str:
    p = (path or "").strip()
    if not p:
        return ""
    if not p.startswith("/"):
        p = "/" + p
    p = re.sub(r"/{2,}", "/", p)
    if len(p) > 1 and p.endswith("/"):
        p = p[:-1]
    return p


def _join_route(prefix: str, path: str) -> str:
    a = _norm_route(prefix)
    b = _norm_route(path)
    if not a:
        return b
    if not b or b == "/":
        return a
    if a.endswith("/"):
        a = a[:-1]
    return _norm_route(a + b)


def _resolve_js_module_candidates(repo: Path, current_rel: str, spec: str) -> list[str]:
    """Resolve require() spec to repo-relative candidate source files."""
    spec = (spec or "").strip()
    if not spec:
        return []
    base_dir = (repo / current_rel).parent
    out: list[str] = []
    candidates: list[Path] = []
    if spec.startswith("./") or spec.startswith("../"):
        base = (base_dir / spec).resolve()
        candidates.append(base)
    elif spec.startswith("/"):
        candidates.append((repo / spec.lstrip("/")).resolve())
    else:
        # package imports are out of scope
        return []
    expanded: list[Path] = []
    for c in candidates:
        expanded.append(c)
        for ext in _JS_ROUTE_EXTS:
            expanded.append(Path(str(c) + ext))
            expanded.append(c / f"index{ext}")
    for c in expanded:
        try:
            rel = c.resolve().relative_to(repo.resolve()).as_posix()
        except Exception:
            continue
        if not c.is_file():
            continue
        if rel not in out:
            out.append(rel)
    return out


def _extract_js_mount_edges(repo: Path, rel: str, txt: str) -> list[tuple[str, str]]:
    """Extract (mount_prefix, child_rel_file) edges from app/router.use statements."""
    requires: dict[str, str] = {}
    for m in _REQ_ASSIGN_RE.finditer(txt):
        requires[m.group(1)] = m.group(2)
    edges: list[tuple[str, str]] = []
    for m in _USE_DIRECT_REQUIRE_RE.finditer(txt):
        mount = _norm_route(m.group(1))
        spec = m.group(2)
        for child in _resolve_js_module_candidates(repo, rel, spec):
            edges.append((mount, child))
    for m in _USE_VAR_RE.finditer(txt):
        mount = _norm_route(m.group(1))
        var = m.group(2)
        spec = requires.get(var)
        if not spec:
            continue
        for child in _resolve_js_module_candidates(repo, rel, spec):
            edges.append((mount, child))
    return edges


def _collect_js_routes_recursive(
    repo: Path,
    rel: str,
    prefix: str,
    file_cache: dict[str, str],
    visiting: set[tuple[str, str]],
) -> list[tuple[str, str]]:
    key = (rel, prefix)
    if key in visiting:
        return []
    visiting.add(key)
    txt = file_cache.get(rel)
    if txt is None:
        p = repo / rel
        if not p.is_file():
            visiting.discard(key)
            return []
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            visiting.discard(key)
            return []
        file_cache[rel] = txt
    out: list[tuple[str, str]] = []
    for meth, path in _extract_synthetic_routes(txt):
        joined = _join_route(prefix, path)
        if joined.startswith("/"):
            out.append((meth, joined))
    for mount, child_rel in _extract_js_mount_edges(repo, rel, txt):
        child_prefix = _join_route(prefix, mount)
        out.extend(_collect_js_routes_recursive(repo, child_rel, child_prefix, file_cache, visiting))
    visiting.discard(key)
    return out


def _extract_synthetic_routes(txt: str) -> list[tuple[str, str]]:
    """Return list of (methodish, path) from source text."""
    out: list[tuple[str, str]] = []
    for m in _JS_ROUTE_RE.finditer(txt):
        meth = m.group(1).upper()
        path = m.group(2).strip()
        if path.startswith("/"):
            out.append((meth, path))
    for m in _JS_ROUTE_CHAIN_RE.finditer(txt):
        path = m.group(1).strip()
        meth = m.group(2).upper()
        if path.startswith("/"):
            out.append((meth, path))
    for m in _SPRING_SIMPLE_MAP_RE.finditer(txt):
        meth = m.group(1).upper()
        path = m.group(2).strip()
        if path.startswith("/"):
            out.append((meth, path))
    for m in _SPRING_MAP_RE.finditer(txt):
        meth = m.group(1).upper()
        args = m.group(2)
        for pm in _SPRING_ATTR_PATH_RE.finditer(args):
            path = pm.group(1).strip()
            if path.startswith("/"):
                out.append((meth, path))
    # Spring class-level prefixes + method-level mappings.
    class_prefixes = [
        _norm_route(pm.group(1).strip())
        for cm in _SPRING_CLASS_MAP_RE.finditer(txt)
        for pm in _SPRING_ATTR_PATH_RE.finditer(cm.group(1))
        if _norm_route(pm.group(1).strip())
    ]
    if class_prefixes:
        for m in _SPRING_SIMPLE_MAP_RE.finditer(txt):
            meth = m.group(1).upper()
            path = _norm_route(m.group(2).strip())
            if not path:
                continue
            for cp in class_prefixes:
                out.append((meth, _join_route(cp, path)))
        for m in _SPRING_MAP_RE.finditer(txt):
            meth = m.group(1).upper()
            args = m.group(2)
            paths = [_norm_route(pm.group(1).strip()) for pm in _SPRING_ATTR_PATH_RE.finditer(args)]
            for p in [x for x in paths if x]:
                for cp in class_prefixes:
                    out.append((meth, _join_route(cp, p)))
    # NestJS controller prefixes + method decorators.
    ctrl_prefixes = [_norm_route(m.group(1).strip()) for m in _NEST_CONTROLLER_RE.finditer(txt)]
    if ctrl_prefixes:
        for m in _NEST_METHOD_RE.finditer(txt):
            meth = m.group(1).upper()
            rel = _norm_route(m.group(2).strip() or "/")
            for cp in ctrl_prefixes:
                out.append((meth, _join_route(cp, rel)))
    dedup: list[tuple[str, str]] = []
    for r in out:
        if r not in dedup:
            dedup.append(r)
    return dedup


def run_phase35(repo: Path, role_scan_tmp: Path, shared_run_dir: Path, append_routes: bool) -> None:
    """``role_scan_tmp`` holds per-role test inventory + test names; ``shared_run_dir`` holds merged API routes."""
    repo = repo.resolve()
    role_scan_tmp.mkdir(parents=True, exist_ok=True)
    shared_run_dir.mkdir(parents=True, exist_ok=True)
    slug = repo.name
    log.log_start("phase35", f"repo={repo} append_routes={'append' if append_routes else 'no'}")

    print("════════════════════════════════════════════════════════")
    print("FORGE SCAN — Phase 3.4-3.5: Test Names + API Routes")
    print(f"Repo: {repo}")
    print("════════════════════════════════════════════════════════")

    test_list = role_scan_tmp / "forge_scan_test_files.txt"
    if not test_list.is_file():
        print(f"  ERROR: {test_list} not found. Run phase1 first.")
        log.log_die(f"missing_prerequisite path={test_list} hint=run_phase1_first", 1)

    print()
    print("[3.4] Extracting test names...")
    names_lines: list[str] = []
    pat = re.compile(
        r"it\(|test\(|describe\(|def test_|func Test|#\[test\]|@Test|should\b",
    )
    for line in test_list.read_text(encoding="utf-8", errors="replace").splitlines():
        fp = Path(line.strip()).resolve()
        if not fp.is_file():
            continue
        names_lines.append(f"=== {fp} ===")
        try:
            txt = fp.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        shown = 0
        for i, ln in enumerate(txt, start=1):
            if pat.search(ln):
                names_lines.append(f"{i}:{ln}")
                shown += 1
                if shown >= 30:
                    break
    tn_path = role_scan_tmp / "forge_scan_test_names.txt"
    tn_path.write_text("\n".join(names_lines) + ("\n" if names_lines else ""), encoding="utf-8", errors="replace")
    n_tests = len([ln for ln in test_list.read_text().splitlines() if ln.strip()])
    edge_hits = sum(
        1
        for ln in names_lines
        if re.search(r"should|error|fail|invalid|missing|expired|exceed|limit|timeout", ln)
    )
    print(f"  Test names extracted from {n_tests} test files")
    print(f"  Edge case strings found: {edge_hits}")
    log.log_stat(f"phase=3.4 test_files={n_tests} edge_case_hits={edge_hits}")

    print()
    print("[3.5] Extracting API routes...")
    routes_path = shared_run_dir / "forge_scan_api_routes.txt"
    if append_routes:
        log.log_step(f"phase=3.5 appending_api_routes repo={slug}")
    else:
        routes_path.write_text("", encoding="utf-8")
        log.log_step(f"phase=3.5 reset_api_routes_file repo={slug}")

    pat_routes = (
        r"@Get\|@Post\|@Put\|@Delete\|@Patch"
        r"\|@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping\|@PatchMapping\|@RequestMapping"
        r"\|@Controller\|@Route"
        r"\|router\.get\|router\.post\|router\.put\|router\.delete\|router\.patch"
        r"\|router\.route\|app\.route"
        r"\|router\.use\|app\.use"
        r"\|app\.get\|app\.post\|app\.put\|app\.delete\|app\.patch"
        r"\|r\.GET\|r\.POST\|r\.PUT\|r\.DELETE\|r\.PATCH"
        r"\|@app\.route\|@router\."
        r"\|mux\.HandleFunc\|http\.HandleFunc\|e\.GET\|e\.POST\|g\.GET\|g\.POST"
    )
    raw = grep_util.run_grep_rn(
        repo,
        pat_routes,
        ["*.ts", "*.tsx", "*.mts", "*.cts", "*.py", "*.go", "*.java", "*.kt", "*.js", "*.jsx", "*.mjs", "*.cjs"],
    )
    test_path_re = re.compile(r"/(test|tests|__tests__|e2e|spec)/|\.test\.|\.spec\.|/testing/")
    fixed: list[str] = []
    for ln in raw.splitlines():
        if "node_modules" in ln or "/dist/" in ln or "dist/" in ln:
            continue
        parts = ln.split(":", 2)
        if len(parts) < 3:
            continue
        abs_path_s, lineno, content = parts[0], parts[1], parts[2]
        try:
            abs_path = Path(abs_path_s).resolve()
            rel = abs_path.relative_to(repo).as_posix()
        except (ValueError, OSError):
            continue
        # Match test paths on repo-relative path only — abs path may contain …/tests/… (e.g. fixtures).
        if test_path_re.search(rel):
            continue
        fixed.append(f"{slug}\t{rel}:{lineno}:{content}")

    with routes_path.open("a", encoding="utf-8", errors="replace") as f:
        for line in fixed:
            f.write(line + "\n")

    # Synthetic extractor pass to improve backend route recall (for chained routers, Spring attrs).
    synth_rows: list[str] = []
    file_cache: dict[str, str] = {}
    for p in repo.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts", ".java", ".kt"):
            continue
        try:
            rel = p.relative_to(repo).as_posix()
        except ValueError:
            continue
        if test_path_re.search(rel):
            continue
        if "/node_modules/" in f"/{rel}/" or "/dist/" in f"/{rel}/" or "/build/" in f"/{rel}/":
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        file_cache[rel] = txt
        for meth, path in _extract_synthetic_routes(txt):
            synth_rows.append(f"{slug}\t{rel}:0:{meth} {path} _forge_route_extract")
        # Recursive route-tree expansion for JS/TS routers mounted via app/router.use(...).
        if p.suffix.lower() in _JS_ROUTE_EXTS and ".use(" in txt:
            rec_routes = _collect_js_routes_recursive(
                repo,
                rel,
                "",
                file_cache=file_cache,
                visiting=set(),
            )
            for meth, path in rec_routes:
                synth_rows.append(f"{slug}\t{rel}:0:{meth} {path} _forge_route_tree")
    if synth_rows:
        with routes_path.open("a", encoding="utf-8", errors="replace") as f:
            for row in sorted(set(synth_rows)):
                f.write(row + "\n")

    openapi_n = openapi_routes.append_openapi_routes(repo, slug, routes_path)
    if openapi_n:
        print(f"  OpenAPI/Swagger operations appended: {openapi_n}")

    merged = routes_path.read_text(encoding="utf-8", errors="replace")
    n_routes = len([x for x in merged.splitlines() if x.strip()])
    _get = sum(1 for ln in merged.splitlines() if re.search(r"@Get\b|router\.get|app\.get|r\.GET|e\.GET|g\.GET|@GetMapping", ln))
    _post = sum(1 for ln in merged.splitlines() if re.search(r"@Post\b|router\.post|app\.post|r\.POST|e\.POST|g\.POST|@PostMapping", ln))
    _put = sum(1 for ln in merged.splitlines() if re.search(r"@Put\b|router\.put|app\.put|r\.PUT|@PutMapping", ln))
    _delete = sum(1 for ln in merged.splitlines() if re.search(r"@Delete\b|router\.delete|app\.delete|r\.DELETE|@DeleteMapping", ln))
    _patch = sum(1 for ln in merged.splitlines() if re.search(r"@Patch\b|router\.patch|app\.patch|r\.PATCH|@PatchMapping", ln))
    print(f"  API routes found: {n_routes}")
    print("  Route breakdown by method:")
    print(f"    GET:    {_get}")
    print(f"    POST:   {_post}")
    print(f"    PUT:    {_put}")
    print(f"    DELETE: {_delete}")
    print(f"    PATCH:  {_patch}")
    log.log_stat(
        f"phase=3.5 api_routes={n_routes} get={_get} post={_post} put={_put} delete={_delete} patch={_patch} "
        f"openapi_ops={openapi_n} synthetic_rows={len(synth_rows)}",
    )
    print()
    print("[3.5] Routes sample (first 20):")
    for ln in merged.splitlines()[:20]:
        print(f"  {ln}")
    print()
    print("Phase 3.4-3.5 complete.")
    log.log_done(
        f"test_names_bytes={tn_path.stat().st_size} api_routes={n_routes}",
    )

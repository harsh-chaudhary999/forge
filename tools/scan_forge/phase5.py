from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from . import ast_http_calls, ast_import_edges, grep_util, log

# Repo-relative paths only (never match parent dirs like ``.../my-test-workspace/...``).
_TEST_PATH_RE = re.compile(r"/(test|tests|__tests__|e2e|spec)/|\.test\.|\.spec\.|/testing/")
_LOW_SIGNAL_PATH_RE = re.compile(
    r"(?:^|/)(?:public|dist|build|coverage|target|tmp|temp|\.tmp|\.cache|generated|swagger-ui)(?:/|$)",
)
_LOW_SIGNAL_FILE_RE = re.compile(r"(?:^|/)(?:\d+|chunk-[^/]+)\.js$", re.IGNORECASE)


def _low_signal_relpath(rel: str) -> bool:
    r = rel.strip().replace("\\", "/")
    if _LOW_SIGNAL_PATH_RE.search(r):
        return True
    if _LOW_SIGNAL_FILE_RE.search(r):
        return True
    return False


_ENDPOINT_CONST_RE = re.compile(
    r"\b(?:const\s+val|val|const|public\s+static\s+final\s+String|static\s+final\s+String)\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*[A-Za-z0-9_<>,.? ]+)?=\s*['\"]([^'\"]{2,260})['\"]",
)


def _looks_like_endpoint_value(v: str) -> bool:
    low = (v or "").strip().lower()
    if not low:
        return False
    if low.startswith("http://") or low.startswith("https://"):
        return "/api" in low or "/v" in low or "/graphql" in low or "/internal" in low
    if low.startswith("/") or low.startswith("api/") or low.startswith("v"):
        return "api" in low or "graphql" in low or "internal" in low or re.match(r"^v[0-9]+", low) is not None
    return False


def _append_repo_lines(
    repo: Path,
    pattern: str,
    includes: list[str],
    out: Path,
    repo_name: str,
    extra_filter_rel=None,
) -> None:
    raw = grep_util.run_grep_rn(repo, pattern, includes)
    # Match phase35: apply test-path heuristics to **repo-relative** paths only. Matching the
    # full grep line false-positives on parent dirs (e.g. ``.../Music/test/web/...`` contains ``/test/``).
    with out.open("a", encoding="utf-8", errors="replace") as f:
        for ln in raw.splitlines():
            if "node_modules" in ln:
                continue
            parts = ln.split(":", 2)
            if len(parts) < 3:
                continue
            abs_p, lineno, content = parts[0], parts[1], parts[2]
            try:
                rel = Path(abs_p).resolve().relative_to(repo).as_posix()
            except ValueError:
                continue
            if _low_signal_relpath(rel):
                continue
            if extra_filter_rel and extra_filter_rel(rel, content):
                continue
            if _TEST_PATH_RE.search(rel):
                continue
            f.write(f"{repo_name}\t{rel}:{lineno}:{content}\n")


def run_phase5(repos: list[Path], scan_tmp: Path, topology=None) -> None:
    scan_tmp.mkdir(parents=True, exist_ok=True)
    log.log_start("phase5", f"repo_count={len(repos)} repos={';'.join(str(r) for r in repos)}")

    print("════════════════════════════════════════════════════════")
    print("FORGE SCAN — Phase 5: Cross-Repo Relationship Scanning")
    print(f"Repos: {' '.join(str(r) for r in repos)}")
    print("════════════════════════════════════════════════════════")

    for name in (
        "forge_scan_js_calls.txt",
        "forge_scan_java_calls.txt",
        "forge_scan_kotlin_calls.txt",
        "forge_scan_python_calls.txt",
        "forge_scan_go_calls.txt",
        "forge_scan_dart_calls.txt",
        "forge_scan_ast_http_calls.txt",
        "forge_scan_all_types.txt",
        "forge_scan_all_env_vars.txt",
        "forge_scan_dynamic_urls.txt",
        "forge_scan_api_constant_calls.txt",
        "forge_scan_endpoint_constants.tsv",
        "forge_scan_shared_types.tsv",
        "forge_scan_event_bus.tsv",
    ):
        (scan_tmp / name).write_text("", encoding="utf-8")

    print()
    print("[5.1] Scanning API call sites across all repos...")
    js_pat = r"fetch(\|\$fetch(\|useFetch(\|ofetch(\|axios\.\|got\.\|superagent\.\|ky\.\|needle\.\|http\.get(\|http\.post(\|http\.put(\|http\.delete(\|http\.patch(\|request(\|apiClient\.\|client\.get(\|client\.post(\|client\.put(\|client\.delete(\|createApi("
    java_pat = r"restTemplate\.\|webClient\.\|HttpClient\.\|OkHttpClient\.\|\.exchange(\|\.getForObject(\|\.postForObject(\|@FeignClient"
    java_map_pat = r"@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping\|@PatchMapping\|@RequestMapping"
    kt_pat = r"client\.get(\|client\.post(\|client\.put(\|client\.delete(\|Fuel\.get(\|Fuel\.post(\|\.get<\|\.post<"
    kt_retro = r"@GET(\|@POST(\|@PUT(\|@DELETE(\|@PATCH("
    py_pat = r"requests\.get(\|requests\.post(\|requests\.put(\|requests\.delete(\|httpx\.get(\|httpx\.post(\|aiohttp\."
    go_pat = r"http\.Get(\|http\.Post(\|http\.NewRequest(\|resty\.\|client\.R()\.Get("
    dart_pat = r"dio\.get(\|dio\.post(\|dio\.put(\|dio\.delete(\|http\.get(\|http\.post("

    for repo in repos:
        repo = repo.resolve()
        name = repo.name
        print(f"  Scanning: {name}")
        _append_repo_lines(repo, js_pat, ["*.ts", "*.tsx", "*.js", "*.jsx"], scan_tmp / "forge_scan_js_calls.txt", name)
        _append_repo_lines(
            repo,
            java_pat,
            ["*.java"],
            scan_tmp / "forge_scan_java_calls.txt",
            name,
            extra_filter_rel=lambda rel, c: bool(
                re.search(r"(?:^|/)(?:Test|IT|Tests)\.java$", rel)
            ),
        )
        raw = grep_util.run_grep_rn(repo, java_map_pat, ["*.java"])
        with (scan_tmp / "forge_scan_java_calls.txt").open("a", encoding="utf-8", errors="replace") as f:
            for ln in raw.splitlines():
                if not re.search(r"feign|client|Client", ln, re.I):
                    continue
                parts = ln.split(":", 2)
                if len(parts) < 3:
                    continue
                abs_p, lineno, content = parts[0], parts[1], parts[2]
                try:
                    rel = Path(abs_p).resolve().relative_to(repo).as_posix()
                except ValueError:
                    continue
                if _TEST_PATH_RE.search(rel):
                    continue
                f.write(f"{name}\t{rel}:{lineno}:{content}\n")
        _append_repo_lines(
            repo,
            kt_pat,
            ["*.kt"],
            scan_tmp / "forge_scan_kotlin_calls.txt",
            name,
            extra_filter_rel=lambda rel, c: bool(re.search(r"(?:^|/)(?:Test|Spec)\.kt$", rel)),
        )
        _append_repo_lines(repo, kt_retro, ["*.kt"], scan_tmp / "forge_scan_kotlin_calls.txt", name)
        _append_repo_lines(
            repo,
            py_pat,
            ["*.py"],
            scan_tmp / "forge_scan_python_calls.txt",
            name,
            extra_filter_rel=lambda rel, c: rel.endswith("_test.py")
            or rel.endswith("/conftest.py")
            or rel.rsplit("/", 1)[-1].startswith("test_"),
        )
        _append_repo_lines(
            repo,
            go_pat,
            ["*.go"],
            scan_tmp / "forge_scan_go_calls.txt",
            name,
            extra_filter_rel=lambda rel, c: rel.endswith("_test.go"),
        )
        _append_repo_lines(repo, dart_pat, ["*.dart"], scan_tmp / "forge_scan_dart_calls.txt", name)
        # Endpoint constants: mobile/web code often stores API paths in constants instead of direct HTTP callsites.
        const_files = []
        for p in repo.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in (".kt", ".java", ".ts", ".tsx", ".js", ".jsx"):
                continue
            try:
                rel = p.relative_to(repo).as_posix()
            except ValueError:
                continue
            if _TEST_PATH_RE.search(rel) or _low_signal_relpath(rel) or "node_modules" in rel:
                continue
            const_files.append((p, rel))
        with (scan_tmp / "forge_scan_endpoint_constants.tsv").open("a", encoding="utf-8", errors="replace") as tsv, (
            scan_tmp / "forge_scan_api_constant_calls.txt"
        ).open("a", encoding="utf-8", errors="replace") as calls_out:
            for abs_p, rel in const_files:
                try:
                    lines = abs_p.read_text(encoding="utf-8", errors="replace").splitlines()
                except OSError:
                    continue
                for i, ln in enumerate(lines, start=1):
                    m = _ENDPOINT_CONST_RE.search(ln)
                    if not m:
                        continue
                    symbol = m.group(1).strip()
                    value = m.group(2).strip()
                    if not _looks_like_endpoint_value(value):
                        continue
                    tsv.write(f"{name}\t{symbol}\t{rel}\t{i}\t{value}\n")
                    calls_out.write(f"{name}\t{rel}:{i}:{ln}\n")

    ast_n = ast_http_calls.append_ast_http_calls(repos, scan_tmp)
    if ast_n:
        print(f"  Tree-sitter AST: appended {ast_n} HTTP call line(s) to forge_scan_ast_http_calls.txt")

    def _cat(dst: str, *srcs: str) -> None:
        parts: list[str] = []
        for s in srcs:
            p = scan_tmp / s
            if p.is_file():
                parts.append(p.read_text(encoding="utf-8", errors="replace"))
        (scan_tmp / dst).write_text("".join(parts), encoding="utf-8", errors="replace")

    _cat(
        "forge_scan_all_callsites.txt",
        "forge_scan_js_calls.txt",
        "forge_scan_java_calls.txt",
        "forge_scan_kotlin_calls.txt",
        "forge_scan_python_calls.txt",
        "forge_scan_go_calls.txt",
        "forge_scan_dart_calls.txt",
        "forge_scan_api_constant_calls.txt",
        "forge_scan_ast_http_calls.txt",
    )

    js_n = len((scan_tmp / "forge_scan_js_calls.txt").read_text().splitlines())
    ja_n = len((scan_tmp / "forge_scan_java_calls.txt").read_text().splitlines())
    kt_n = len((scan_tmp / "forge_scan_kotlin_calls.txt").read_text().splitlines())
    py_n = len((scan_tmp / "forge_scan_python_calls.txt").read_text().splitlines())
    go_n = len((scan_tmp / "forge_scan_go_calls.txt").read_text().splitlines())
    da_n = len((scan_tmp / "forge_scan_dart_calls.txt").read_text().splitlines())
    all_n = len((scan_tmp / "forge_scan_all_callsites.txt").read_text().splitlines())
    const_n = len((scan_tmp / "forge_scan_api_constant_calls.txt").read_text().splitlines())
    const_sym_n = len((scan_tmp / "forge_scan_endpoint_constants.tsv").read_text().splitlines())
    print(f"  Total call sites: {all_n}")
    print(
        f"    TS/JS: {js_n} | Java: {ja_n} | Kotlin: {kt_n} | Python: {py_n} | Go: {go_n} | Dart: {da_n} | API constants: {const_n}"
    )
    log.log_stat(
        f"phase=5.1 total_callsites={all_n} js={js_n} java={ja_n} kotlin={kt_n} python={py_n} go={go_n} dart={da_n} "
        f"api_constants={const_n} endpoint_symbols={const_sym_n}",
    )

    # 5.2 types
    print()
    print("[5.2] Scanning exported types for shared type detection...")
    # repo_name -> list of (type_decl_line, rel_path)
    type_by_repo: dict[str, list[tuple[str, str]]] = {}
    for repo in repos:
        repo = repo.resolve()
        name = repo.name
        raw = grep_util.run_grep_rn(
            repo,
            r"^export interface \|^export type \|^export class \|^type \|^interface ",
            ["*.ts"],
        )
        type_by_repo[name] = []
        with (scan_tmp / "forge_scan_all_types.txt").open("a", encoding="utf-8", errors="replace") as f:
            for ln in raw.splitlines():
                if "node_modules" in ln:
                    continue
                parts = ln.split(":", 2)
                if len(parts) < 3:
                    continue
                abs_p, _lineno, content = parts[0], parts[1], parts[2]
                try:
                    rel = Path(abs_p).resolve().relative_to(repo).as_posix()
                except ValueError:
                    rel = abs_p
                f.write(content + "\n")
                type_by_repo[name].append((content.strip(), rel))

    type_text = (scan_tmp / "forge_scan_all_types.txt").read_text(encoding="utf-8", errors="replace")
    type_lines = [ln.strip() for ln in type_text.splitlines() if ln.strip()]
    total_decl = len(type_lines)
    ctr = Counter(type_lines)
    dup_distinct = sum(1 for n in ctr.values() if n > 1)
    print(f"  Total type declarations: {total_decl}")

    # Build shared-types TSV: type_name\trepo_a\trel_a\trepo_b\trel_b
    shared_tsv_rows: list[str] = []
    type_name_re = re.compile(
        r"\b(?:class|interface|type|enum)\s+([A-Z][a-zA-Z0-9_]*)"
    )
    if len(repos) >= 2:
        # Build lookup: normalized_decl -> [(repo_name, rel_path)]
        decl_map: dict[str, list[tuple[str, str]]] = {}
        for repo_name, entries in type_by_repo.items():
            for decl, rel in entries:
                decl_map.setdefault(decl, []).append((repo_name, rel))
        for decl, locs in decl_map.items():
            if len(locs) < 2:
                continue
            m = type_name_re.search(decl)
            type_name = m.group(1) if m else decl[:40]
            for i in range(len(locs)):
                for j in range(i + 1, len(locs)):
                    ra, pa = locs[i]
                    rb, pb = locs[j]
                    shared_tsv_rows.append(f"{type_name}\t{ra}\t{pa}\t{rb}\t{pb}")

    (scan_tmp / "forge_scan_shared_types.tsv").write_text(
        "\n".join(shared_tsv_rows) + ("\n" if shared_tsv_rows else ""),
        encoding="utf-8",
    )

    if dup_distinct:
        print("  Types appearing in 2+ repos (potential shared contracts):")
        dups = sorted(((ln, c) for ln, c in ctr.items() if c > 1), key=lambda x: -x[1])[:50]
        for line, n in dups:
            print(f"    ({n}x) {line[:120]}")
    print(f"  Shared type pairs written to forge_scan_shared_types.tsv: {len(shared_tsv_rows)}")
    log.log_stat(f"phase=5.2 type_declarations={total_decl} duplicate_type_lines={dup_distinct} shared_type_pairs={len(shared_tsv_rows)}")

    # 5.3 env
    print()
    print("[5.3] Scanning environment variable usage across repos...")
    env_pat = r"process\.env\.\|os\.environ\.\|os\.Getenv\|System\.getenv\|dotenv\|env\.\|Env\."
    for repo in repos:
        repo = repo.resolve()
        name = repo.name
        raw = grep_util.run_grep_rn(
            repo,
            env_pat,
            ["*.ts", "*.js", "*.py", "*.go", "*.java", "*.kt"],
        )
        with (scan_tmp / "forge_scan_all_env_vars.txt").open("a", encoding="utf-8", errors="replace") as f:
            for ln in raw.splitlines():
                if "node_modules" in ln or "test" in ln.lower():
                    continue
                parts = ln.split(":", 2)
                if len(parts) < 3:
                    continue
                abs_p, lineno, content = parts[0], parts[1], parts[2]
                try:
                    rel = Path(abs_p).resolve().relative_to(repo).as_posix()
                except ValueError:
                    continue
                f.write(f"{name}\t{rel}:{lineno}:{content}\n")

    env_lines = (scan_tmp / "forge_scan_all_env_vars.txt").read_text()
    proc_keys = sorted(set(re.findall(r"process\.env\.([A-Z_]+)", env_lines)))
    print(f"  Env var references: {len(env_lines.splitlines())}")
    log.log_stat(
        f"phase=5.3 env_var_lines={len(env_lines.splitlines())} distinct_process_env_keys={len(proc_keys)}",
    )

    # 5.4 producers/consumers → forge_scan_event_bus.tsv
    # columns: role\trel_path\tlineno\tkind\tpattern\ttopic
    print()
    print("[5.4] Scanning event/message bus producers and consumers...")
    prod_pat = r"publish(\|produce(\|emit(\|sendMessage\|kafkaProducer\|channel\.send\|rabbitMQ\.publish\|\.send("
    cons_pat = r"subscribe(\|consume(\|\.on(\|kafkaConsumer\|channel\.receive\|rabbitMQ\.consume\|@KafkaListener\|\.listen("

    _topic_arg_re = re.compile(r"""['"]([\w.\-/]+)['"]""")
    known_topics: set[str] = set()
    if topology is not None:
        known_topics = topology.all_topics()

    def _resolve_topic(content: str) -> str:
        """Best-effort: extract first quoted string that looks like a topic name."""
        for m in _topic_arg_re.finditer(content):
            candidate = m.group(1)
            if known_topics and candidate in known_topics:
                return candidate
            if re.search(r"[.\-]", candidate) or candidate.islower():
                return candidate
        return ""

    event_bus_rows: list[str] = []

    def _scan_bus_kind(kind: str, pattern: str) -> None:
        for repo in repos:
            repo = repo.resolve()
            role_name = repo.name
            raw = grep_util.run_grep_rn(repo, pattern, ["*.ts", "*.py", "*.go", "*.java", "*.kt"])
            for ln in raw.splitlines():
                if "node_modules" in ln or "test" in ln.lower():
                    continue
                parts = ln.split(":", 2)
                if len(parts) < 3:
                    continue
                abs_p, lineno, content = parts[0], parts[1], parts[2]
                try:
                    rel = Path(abs_p).resolve().relative_to(repo).as_posix()
                except ValueError:
                    continue
                topic = _resolve_topic(content)
                pat_matched = next(
                    (p for p in pattern.split(r"\|") if p.rstrip("(").replace("\\", "") in content),
                    pattern.split(r"\|")[0],
                )
                event_bus_rows.append(f"{role_name}\t{rel}\t{lineno}\t{kind}\t{pat_matched}\t{topic}")
                print(f"  [{kind}] {role_name}: {rel}:{lineno}:{content[:80]}")

    print("  Producers:")
    _scan_bus_kind("pub", prod_pat)
    print("  Consumers:")
    _scan_bus_kind("sub", cons_pat)

    (scan_tmp / "forge_scan_event_bus.tsv").write_text(
        "\n".join(event_bus_rows) + ("\n" if event_bus_rows else ""),
        encoding="utf-8",
    )
    print(f"  Event bus rows written to forge_scan_event_bus.tsv: {len(event_bus_rows)}")
    _pub = sum(1 for r in event_bus_rows if "\tpub\t" in r)
    _sub = sum(1 for r in event_bus_rows if "\tsub\t" in r)
    log.log_stat(f"phase=5.4 event_bus_rows={len(event_bus_rows)} pub={_pub} sub={_sub}")

    # 5.5 prep URLs (simplified: harvest from js_calls + broad /api patterns)
    print()
    print("[5.5 prep] Extracting URL path strings from call sites...")
    urls: set[str] = set()
    js_calls = (scan_tmp / "forge_scan_js_calls.txt").read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(
        r"(fetch|\$fetch|useFetch|ofetch|axios\.[a-zA-Z]+|got\.[a-zA-Z]+|ky\.[a-zA-Z]+)\(['\"`]([/][^'`\"?# ]+)",
        js_calls,
    ):
        urls.add(m.group(2))
    for m in re.finditer(
        r"(fetch|\$fetch|useFetch|ofetch|axios\.[a-zA-Z]+|got\.[a-zA-Z]+|ky\.[a-zA-Z]+)\(\"(/[^\"?# ]+)\"",
        js_calls,
    ):
        urls.add(m.group(2))
    api_re = re.compile(r'["\'](/api[^"\'#?]{1,240})["\']|`(/api[^`#?]{1,240})`')
    for repo in repos:
        repo = repo.resolve()
        for p in repo.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in (".ts", ".tsx", ".js", ".jsx"):
                continue
            rel = str(p.relative_to(repo))
            if "node_modules" in rel or "/dist/" in rel or "/build/" in rel:
                continue
            if _low_signal_relpath(rel):
                continue
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in api_re.finditer(txt):
                g1, g2 = m.group(1), m.group(2)
                u = g1 or g2
                if u:
                    urls.add(u)

    fe = scan_tmp / "forge_scan_fe_urls.txt"
    fe.parent.mkdir(parents=True, exist_ok=True)
    fe.write_text("\n".join(sorted(urls)) + ("\n" if urls else ""), encoding="utf-8")
    print(f"  Unique URL paths extracted: {len(urls)}")

    dyn_pat = r"fetch(\`\${\|axios\.[a-z]*(\`\${\|got\.[a-z]*(\`\${\|requests\.[a-z]*(f\"\|httpx\.[a-z]*(f\""
    concat_pat = r"baseURL\s*+\|API_BASE_URL\s*+\|API_URL\s*+\|BASE_URL\s*+"
    for repo in repos:
        repo = repo.resolve()
        name = repo.name
        raw = grep_util.run_grep_rn(repo, dyn_pat, ["*.ts", "*.tsx", "*.js", "*.py"])
        with (scan_tmp / "forge_scan_dynamic_urls.txt").open("a", encoding="utf-8", errors="replace") as f:
            for ln in raw.splitlines():
                if "node_modules" in ln:
                    continue
                if re.search(r"/(test|tests|__tests__|e2e|spec)/|\.test\.|\.spec\.|/testing/", ln):
                    continue
                parts = ln.split(":", 2)
                if len(parts) < 3:
                    continue
                try:
                    rel = Path(parts[0]).resolve().relative_to(repo).as_posix()
                except ValueError:
                    continue
                f.write(f"{name}\t{rel}:{parts[1]}:{parts[2]}\n")
        raw2 = grep_util.run_grep_rn(repo, concat_pat, ["*.ts", "*.tsx", "*.js"])
        with (scan_tmp / "forge_scan_dynamic_urls.txt").open("a", encoding="utf-8", errors="replace") as f:
            for ln in raw2.splitlines():
                if "node_modules" in ln:
                    continue
                if re.search(r"/(test|tests|__tests__|e2e|spec)/|\.test\.|\.spec\.|/testing/", ln):
                    continue
                parts = ln.split(":", 2)
                if len(parts) < 3:
                    continue
                try:
                    rel = Path(parts[0]).resolve().relative_to(repo).as_posix()
                except ValueError:
                    continue
                f.write(f"{name}\t{rel}:{parts[1]}:{parts[2]}\n")

    dyn_path = scan_tmp / "forge_scan_dynamic_urls.txt"
    if dyn_path.is_file() and dyn_path.stat().st_size > 0:
        log.log_warn(
            f"phase=5.5-prep dynamic_url_lines={len(dyn_path.read_text().splitlines())} manual_review_required=true",
        )

    (scan_tmp / "forge_scan_url_strings.txt").write_text("\n".join(sorted(urls)) + "\n", encoding="utf-8")

    # Optional import/export edge extraction for mapping quality.
    imp_rows = ast_import_edges.append_import_edges(repos, scan_tmp)

    api_routes_n = len((scan_tmp / "forge_scan_api_routes.txt").read_text().splitlines()) if (scan_tmp / "forge_scan_api_routes.txt").is_file() else 0
    log.log_stat(
        f"phase=5.x-prep api_routes={api_routes_n} callsites={all_n} fe_urls={len(urls)} "
        f"dynamic_urls={len(dyn_path.read_text().splitlines()) if dyn_path.is_file() else 0} "
        f"import_edges={imp_rows}",
    )
    log.log_done(
        f"callsites={all_n} fe_urls={len(urls)} dynamic_urls={len(dyn_path.read_text().splitlines()) if dyn_path.is_file() else 0} "
        f"env_lines={len(env_lines.splitlines())} api_routes={api_routes_n} import_edges={imp_rows}",
    )
    print()
    print("Phase 5.1-5.5 prep complete.")

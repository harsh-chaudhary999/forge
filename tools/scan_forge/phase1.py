from __future__ import annotations

import re
from pathlib import Path

from . import fs_util, grep_util, log


def _write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8", errors="replace")


def _append_text(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8", errors="replace") as f:
        f.write(text)


def _filter_lines(lines: list[str], drop_res: list[re.Pattern[str]]) -> list[str]:
    out: list[str] = []
    for ln in lines:
        if any(r.search(ln) for r in drop_res):
            continue
        out.append(ln)
    return out


def run_phase1(repo: Path, scan_tmp: Path) -> None:
    log.log_start("phase1-inventory", f"repo={repo}")
    repo = repo.resolve()
    scan_tmp.mkdir(parents=True, exist_ok=True)

    print("════════════════════════════════════════════════════════")
    print("FORGE SCAN — Phase 1: Structural Inventory")
    print(f"Repo: {repo}")
    print("════════════════════════════════════════════════════════")
    print()

    # 1.1 file inventory
    sources = fs_util.list_source_files(repo)
    tests = fs_util.list_test_files(repo)
    src_paths = [str(p.resolve()) for p in sources]
    tst_paths = [str(p.resolve()) for p in tests]
    _write_lines(scan_tmp / "forge_scan_source_files.txt", src_paths)
    _write_lines(scan_tmp / "forge_scan_test_files.txt", tst_paths)
    print(
        f"[1.1] Source files: {len(src_paths)} | Test files: {len(tst_paths)}",
    )
    log.log_stat(f"phase=1.1 source_files={len(src_paths)} test_files={len(tst_paths)}")
    print()

    # 1.2 monorepo + entry points
    print("[1.2] Repo structure:")
    mono = any((repo / f).is_file() for f in ("turbo.json", "nx.json", "lerna.json"))
    if mono:
        print("  Monorepo detected (turbo/nx/lerna). Packages:")
        for pj in sorted(repo.glob("**/package.json")):
            try:
                rel = pj.relative_to(repo)
            except ValueError:
                continue
            if len(rel.parts) > 4:
                continue
            if "node_modules" in rel.parts:
                continue
            if rel == Path("package.json"):
                continue
            print(f"    {pj.parent}")
    else:
        print("  Single-repo")
    print("  Entry points:")
    entry_names = {
        "main.py",
        "app.py",
        "server.py",
        "index.ts",
        "main.ts",
        "app.ts",
        "index.js",
        "main.js",
        "server.js",
        "main.go",
        "main.kt",
        "Main.kt",
        "main.rs",
        "Application.java",
    }
    for ep in sorted(repo.rglob("*")):
        if ep.name in entry_names and ep.is_file():
            try:
                rel = ep.relative_to(repo)
            except ValueError:
                continue
            if len(rel.parts) > 4 or "node_modules" in rel.parts or "dist" in rel.parts:
                continue
            print(f"    {ep}")
    print()

    # 1.3 import graph
    import_lines: list[str] = []
    import_header = re.compile(
        r"^import |^from |^require\(|^use |^extern crate|^#include|^using ",
    )
    for fp in sources:
        import_lines.append(f"=== {fp} ===")
        try:
            head = fp.read_text(encoding="utf-8", errors="replace").splitlines()[:50]
        except OSError:
            head = []
        for ln in head:
            if import_header.search(ln):
                import_lines.append(ln)
    imp_text = "\n".join(import_lines) + ("\n" if import_lines else "")
    (scan_tmp / "forge_scan_imports.txt").write_text(imp_text, encoding="utf-8", errors="replace")
    import_blocks = sum(1 for ln in import_lines if ln.startswith("=== "))
    print(f"[1.3] Import relationships extracted: {import_blocks} files")
    log.log_stat(f"phase=1.3 import_blocks={import_blocks}")

    # 1.4 hub scores
    hub_lines: list[str] = []
    for fp in sources:
        stem = fp.stem
        c = imp_text.count(stem)
        hub_lines.append(f"{c} {fp}")
    hub_lines.sort(key=lambda s: int(s.split(" ", 1)[0]), reverse=True)
    _write_lines(scan_tmp / "forge_scan_hub_scores.txt", hub_lines)
    tier1 = [ln.split(" ", 1)[1] for ln in hub_lines if ln.split(" ", 1)[0].isdigit() and int(ln.split(" ", 1)[0]) >= 5]
    tier2 = [
        ln.split(" ", 1)[1]
        for ln in hub_lines
        if ln.split(" ", 1)[0].isdigit() and 3 <= int(ln.split(" ", 1)[0]) < 5
    ]
    _write_lines(scan_tmp / "forge_scan_tier1.txt", tier1)
    _write_lines(scan_tmp / "forge_scan_tier2.txt", tier2)
    print(f"[1.4] Computing hub scores for {len(sources)} files (single-pass import analysis)...")
    print(f"[1.4] Tier 1 hubs (5+ refs): {len(tier1)} | Tier 2 hubs (3-4 refs): {len(tier2)}")
    print("[1.4] Top 10 hubs:")
    for ln in hub_lines[:10]:
        print(f"  {ln}")
    log.log_stat(
        f"phase=1.4 tier1={len(tier1)} tier2={len(tier2)} source_files_scored={len(sources)}",
    )
    print()

    # 1.5 language fingerprint
    def cnt(pat: str) -> int:
        r = re.compile(pat)
        return sum(1 for p in src_paths if r.search(p.replace("\\", "/")))

    ts_count = cnt(r"\.tsx?$")
    js_count = cnt(r"\.jsx?$")
    py_count = cnt(r"\.py$")
    go_count = cnt(r"\.go$")
    java_count = cnt(r"\.java$")
    kt_count = cnt(r"\.kt$")
    dart_count = cnt(r"\.dart$")
    rs_count = cnt(r"\.rs$")
    tsjs = ts_count + js_count
    print("[1.5] Language breakdown:")
    print(
        f"  TypeScript/TSX: {ts_count} | JavaScript/JSX: {js_count} | Python: {py_count} | Go: {go_count}",
    )
    print(f"  Java: {java_count} | Kotlin: {kt_count} | Dart: {dart_count} | Rust: {rs_count}")
    log.log_stat(
        f"phase=1.5 ts={ts_count} js={js_count} py={py_count} go={go_count} "
        f"java={java_count} kt={kt_count} dart={dart_count} rs={rs_count} tsjs={tsjs}",
    )
    if (repo / "package.json").is_file():
        try:
            pj = (repo / "package.json").read_text(encoding="utf-8", errors="replace")
            if re.search(r'"next"|"express"|"fastify"|"nestjs"|"react-native"|"vue"|"nuxt"|"svelte"|"hono"|"koa"', pj):
                print("  Framework signals: (matched package.json)")
        except OSError:
            pass
    if (repo / "go.mod").is_file():
        try:
            gm = (repo / "go.mod").read_text(encoding="utf-8", errors="replace")
            for ln in gm.splitlines():
                if re.search(r"gin|echo|fiber|chi|mux", ln):
                    print(f"  {ln}")
        except OSError:
            pass
    if (repo / "requirements.txt").is_file():
        try:
            rq = (repo / "requirements.txt").read_text(encoding="utf-8", errors="replace")
            for ln in rq.splitlines():
                if re.search(r"fastapi|django|flask|starlette|tornado", ln, re.I):
                    print(f"  {ln}")
        except OSError:
            pass
    if (repo / "pubspec.yaml").is_file():
        try:
            pub = (repo / "pubspec.yaml").read_text(encoding="utf-8", errors="replace").splitlines()[:5]
            for ln in pub:
                print(f"  {ln}")
        except OSError:
            pass
    print()

    # 1.6 symbol inventory — GNU grep patterns aligned with legacy inventory
    print("[1.6] Building symbol inventory...")

    def w(name: str, content: str) -> None:
        (scan_tmp / name).write_text(content, encoding="utf-8", errors="replace")

    def g(pat: str, includes: list[str]) -> str:
        return grep_util.run_grep_rn(repo, pat, includes)

    # Java
    if java_count > 0:
        s = g(
            r"^\s*\(public\|protected\|abstract\|final\)\{0,3\}\s*\(class\|interface\|enum\|@interface\)\s",
            ["*.java"],
        )
        s = "\n".join(
            _filter_lines(
                s.splitlines(),
                [re.compile(r"/test/|Test\.java\b|IT\.java\b|Tests\.java\b")],
            )
        ) + ("\n" if s else "")
        w("forge_scan_types_java.txt", s)
        s2 = g(
            r"^\s*@\(Service\|Repository\|Controller\|RestController\|Component\|Configuration\|Entity\|SpringBootApplication\|EventListener\|Scheduled\)",
            ["*.java"],
        )
        s2 = "\n".join(_filter_lines(s2.splitlines(), [re.compile(r"/test/")])) + ("\n" if s2 else "")
        w("forge_scan_annotations_java.txt", s2)
        s3 = g(
            r"^\s\+\(public\|protected\)\s\+\(static\s\+\)\?\(final\s\+\)\?\(abstract\s\+\)\?\(synchronized\s\+\)\?\(void\|boolean\|int\|long\|double\|float\|String\|List\|Map\|Set\|Optional\|[A-Z]\)[a-zA-Z0-9<>\[\]?,\s]*\s\+[a-z_][a-zA-Z0-9_]*\s*(",
            ["*.java"],
        )
        s3 = "\n".join(
            _filter_lines(
                s3.splitlines(),
                [re.compile(r"new \([A-Z]\|\"\)|return |if \(|while \(|for \(|switch \(|throw |/test/|Test\.java")],
            )
        ) + ("\n" if s3 else "")
        w("forge_scan_methods_java.txt", s3)
        print(
            f"  Java    — types: {len(s.splitlines())} | methods: {len(s3.splitlines())} | annotations: {len(s2.splitlines())}",
        )
    else:
        w("forge_scan_types_java.txt", "")
        w("forge_scan_methods_java.txt", "")
        w("forge_scan_annotations_java.txt", "")

    # Kotlin
    if kt_count > 0:
        s = g(
            r"^\s*\(data \|sealed \|abstract \|open \|inner \|enum \|annotation \)\?\(class\|interface\|object\)\s\|^\s*typealias \|^\s*companion object",
            ["*.kt"],
        )
        s = "\n".join(_filter_lines(s.splitlines(), [re.compile(r"Test\.kt\b|Spec\.kt\b|/test/")])) + ("\n" if s else "")
        w("forge_scan_types_kotlin.txt", s)
        s2 = g(
            r"^\s*@\(Service\|Repository\|Controller\|RestController\|Component\|Configuration\|Entity\|SpringBootApplication\)",
            ["*.kt"],
        )
        s2 = "\n".join(_filter_lines(s2.splitlines(), [re.compile(r"/test/")])) + ("\n" if s2 else "")
        w("forge_scan_annotations_kotlin.txt", s2)
        s3 = g(
            r"^\s*\(override\s\+\)\?\(suspend\s\+\)\?\(inline\s\+\)\?\(private\s\+\|protected\s\+\|internal\s\+\|public\s\+\)\?\(open\s\+\)\?fun [a-zA-Z_]",
            ["*.kt"],
        )
        s3 = "\n".join(_filter_lines(s3.splitlines(), [re.compile(r"Test\.kt\b|Spec\.kt\b|/test/")])) + ("\n" if s3 else "")
        w("forge_scan_methods_kotlin.txt", s3)
        print(f"  Kotlin  — types: {len(s.splitlines())} | functions: {len(s3.splitlines())}")
    else:
        w("forge_scan_types_kotlin.txt", "")
        w("forge_scan_methods_kotlin.txt", "")
        w("forge_scan_annotations_kotlin.txt", "")

    # Go
    if go_count > 0:
        s = g(r"^type [A-Z][a-zA-Z0-9]* \(struct\|interface\)\b", ["*.go"])
        s = "\n".join(_filter_lines(s.splitlines(), [re.compile(r"_test\.go")])) + ("\n" if s else "")
        w("forge_scan_types_go.txt", s)
        s2 = g(r"^func ([a-zA-Z_][a-zA-Z0-9_]* \*\?[A-Z][a-zA-Z0-9]*) [A-Za-z]", ["*.go"])
        s2 = "\n".join(_filter_lines(s2.splitlines(), [re.compile(r"_test\.go")])) + ("\n" if s2 else "")
        w("forge_scan_methods_go.txt", s2)
        s3 = g(r"^func [A-Z][a-zA-Z0-9]*\(", ["*.go"])
        s3 = "\n".join(_filter_lines(s3.splitlines(), [re.compile(r"_test\.go")])) + ("\n" if s3 else "")
        w("forge_scan_functions_go.txt", s3)
        print(
            f"  Go      — types: {len(s.splitlines())} | receiver methods: {len(s2.splitlines())} | exported funcs: {len(s3.splitlines())}",
        )
    else:
        w("forge_scan_types_go.txt", "")
        w("forge_scan_methods_go.txt", "")
        w("forge_scan_functions_go.txt", "")

    # TS/JS
    if tsjs > 0:
        inc = ["*.ts", "*.tsx", "*.js", "*.jsx"]
        s = g(
            r"^export \(default \)\?\(abstract \)\?class \|^export interface \|^export abstract class \|^export type [A-Z]",
            inc,
        )
        s = "\n".join(
            _filter_lines(s.splitlines(), [re.compile(r"node_modules|\.d\.ts|\.spec\.|\.test\.")]),
        ) + ("\n" if s else "")
        w("forge_scan_types_ts.txt", s)
        s2 = g(
            r"^\s\+\(public\|private\|protected\|readonly\|static\|async\|override\)\s\+[a-zA-Z_][a-zA-Z0-9_]*\s*([^)]*)\s*[:{]",
            ["*.ts", "*.tsx"],
        )
        s2 = "\n".join(
            _filter_lines(s2.splitlines(), [re.compile(r"node_modules|\.spec\.|\.test\.|constructor")]),
        ) + ("\n" if s2 else "")
        w("forge_scan_methods_ts.txt", s2)
        s3 = g(
            r"^@\(Injectable\|Controller\|Service\|Repository\|Entity\|Module\|Guard\|Interceptor\|Pipe\|EventEmitter\|Resolver\|ObjectType\|InputType\|Get\|Post\|Put\|Delete\|Patch\)",
            ["*.ts", "*.tsx"],
        )
        s3 = "\n".join(_filter_lines(s3.splitlines(), [re.compile(r"node_modules|\.spec\.|\.test\.")])) + ("\n" if s3 else "")
        w("forge_scan_decorators_ts.txt", s3)
        s4 = g(r"^export \(async \)\?function [a-zA-Z]", inc)
        s4 = "\n".join(_filter_lines(s4.splitlines(), [re.compile(r"node_modules|\.spec\.|\.test\.")])) + ("\n" if s4 else "")
        s5 = g(r"^export default \(async \)\?function", inc)
        s5 = "\n".join(_filter_lines(s5.splitlines(), [re.compile(r"node_modules|\.spec\.|\.test\.")])) + ("\n" if s5 else "")
        s6 = g(r"^export const [a-zA-Z][a-zA-Z0-9]* = \(async \)\?(", inc)
        s6 = "\n".join(_filter_lines(s6.splitlines(), [re.compile(r"node_modules|\.spec\.|\.test\.")])) + ("\n" if s6 else "")
        func_all = "\n".join((s4 + s5 + s6).splitlines()) + "\n"
        w("forge_scan_functions_ts.txt", func_all)
        print(
            f"  TS/JS   — classes: {len(s.splitlines())} | class methods: {len(s2.splitlines())} | functions: {len(func_all.splitlines())} | decorators: {len(s3.splitlines())}",
        )
    else:
        w("forge_scan_types_ts.txt", "")
        w("forge_scan_methods_ts.txt", "")
        w("forge_scan_functions_ts.txt", "")
        w("forge_scan_decorators_ts.txt", "")

    # Python
    if py_count > 0:
        s = g(r"^class [A-Za-z][a-zA-Z0-9]*\b", ["*.py"])
        s = "\n".join(
            _filter_lines(s.splitlines(), [re.compile(r"test_[a-z]|_test\.py|Test[A-Z]")]),
        ) + ("\n" if s else "")
        w("forge_scan_types_python.txt", s)
        s2 = g(
            r"^@\(dataclass\|dataclasses\.dataclass\|property\|staticmethod\|classmethod\|abstractmethod\|app\.route\|router\.\)",
            ["*.py"],
        )
        s2 = "\n".join(_filter_lines(s2.splitlines(), [re.compile(r"test_|_test\.py")])) + ("\n" if s2 else "")
        w("forge_scan_annotations_python.txt", s2)
        s3 = g(r"^def [a-zA-Z][a-zA-Z0-9_]*\|^async def [a-zA-Z][a-zA-Z0-9_]*", ["*.py"])
        s3 = "\n".join(
            _filter_lines(
                s3.splitlines(),
                [
                    re.compile(
                        r"test_|_test\.py|__init__|__main__|__str__|__repr__|__eq__|__hash__|__len__|__iter__",
                    ),
                ],
            ),
        ) + ("\n" if s3 else "")
        w("forge_scan_functions_python.txt", s3)
        s4 = g(r"^\s\+def [a-zA-Z][a-zA-Z0-9_]*\|^\s\+async def [a-zA-Z][a-zA-Z0-9_]*", ["*.py"])
        s4 = "\n".join(
            _filter_lines(
                s4.splitlines(),
                [re.compile(r"test_|_test\.py|__init__|__str__|__repr__|__eq__|__hash__|__len__")],
            ),
        ) + ("\n" if s4 else "")
        w("forge_scan_methods_python.txt", s4)
        print(
            f"  Python  — types: {len(s.splitlines())} | class methods: {len(s4.splitlines())} | module funcs: {len(s3.splitlines())}",
        )
    else:
        w("forge_scan_types_python.txt", "")
        w("forge_scan_methods_python.txt", "")
        w("forge_scan_functions_python.txt", "")
        w("forge_scan_annotations_python.txt", "")

    # Dart
    if dart_count > 0:
        s = g(r"^\(abstract \)\?class [A-Z]\|^mixin [A-Z]\|^enum [A-Z]", ["*.dart"])
        s = "\n".join(_filter_lines(s.splitlines(), [re.compile(r"_test\.dart|test/")])) + ("\n" if s else "")
        w("forge_scan_types_dart.txt", s)
        s2 = g(
            r"^\s*\(Future\|Stream\|void\|bool\|int\|double\|String\|Widget\|[A-Z][a-zA-Z0-9<>?]*\)\s\+[a-z_][a-zA-Z0-9_]*\s*(",
            ["*.dart"],
        )
        s2 = "\n".join(_filter_lines(s2.splitlines(), [re.compile(r"_test\.dart|test/")])) + ("\n" if s2 else "")
        w("forge_scan_methods_dart.txt", s2)
        print(f"  Dart    — types: {len(s.splitlines())} | methods: {len(s2.splitlines())}")
    else:
        w("forge_scan_types_dart.txt", "")
        w("forge_scan_methods_dart.txt", "")

    # Rust
    if rs_count > 0:
        s = g(r"^pub \(struct\|enum\|trait\) [A-Z]\|^pub(crate) \(struct\|enum\|trait\) [A-Z]", ["*.rs"])
        s = "\n".join(_filter_lines(s.splitlines(), [re.compile(r"test\b|#\[test\]")])) + ("\n" if s else "")
        w("forge_scan_types_rust.txt", s)
        s2 = g(r"^\s*pub fn [a-zA-Z_]\|^pub fn [a-zA-Z_]\|^pub async fn [a-zA-Z_]", ["*.rs"])
        s2 = "\n".join(_filter_lines(s2.splitlines(), [re.compile(r"#\[test\]|mod tests")])) + ("\n" if s2 else "")
        w("forge_scan_methods_rust.txt", s2)
        print(f"  Rust    — types: {len(s.splitlines())} | pub fns: {len(s2.splitlines())}")
    else:
        w("forge_scan_types_rust.txt", "")
        w("forge_scan_methods_rust.txt", "")

    # Frontend / HTML
    html_files: list[str] = []
    vue_files: list[str] = []
    svelte_files: list[str] = []
    angular_templates: list[str] = []
    for p in fs_util.iter_files_under(repo):
        n = p.name.lower()
        rel = str(p.relative_to(repo))
        if n.endswith((".html", ".htm")):
            html_files.append(str(p.resolve()))
        elif n.endswith(".vue"):
            vue_files.append(str(p.resolve()))
        elif n.endswith(".svelte"):
            svelte_files.append(str(p.resolve()))
        elif n.endswith(".component.html"):
            angular_templates.append(str(p.resolve()))
    html_files.sort()
    vue_files.sort()
    svelte_files.sort()
    angular_templates.sort()
    _write_lines(scan_tmp / "forge_scan_html_files.txt", html_files)
    _write_lines(scan_tmp / "forge_scan_vue_files.txt", vue_files)
    _write_lines(scan_tmp / "forge_scan_svelte_files.txt", svelte_files)
    _write_lines(scan_tmp / "forge_scan_angular_templates.txt", angular_templates)

    def gh(pat: str, includes: list[str]) -> str:
        raw = grep_util.run_grep_rn(repo, pat, includes)
        lines = [
            ln
            for ln in raw.splitlines()
            if "node_modules" not in ln and "dist" not in ln.split(":")[0].lower()
        ]
        return "\n".join(lines) + ("\n" if lines else "")

    w(
        "forge_scan_html_forms.txt",
        gh(
            r"<form\s\+\|<form>",
            ["*.html", "*.vue", "*.svelte", "*.tsx", "*.jsx"],
        ),
    )
    w(
        "forge_scan_html_ids.txt",
        gh(
            r'id="[a-zA-Z][a-zA-Z0-9_-]*"\|data-[a-z][a-z0-9-]*=',
            ["*.html", "*.vue", "*.svelte"],
        ),
    )

    def cat_files(keys: list[str]) -> str:
        parts: list[str] = []
        for k in keys:
            parts.append((scan_tmp / k).read_text(encoding="utf-8", errors="replace"))
        return "".join(parts)

    w(
        "forge_scan_types_all.txt",
        cat_files(
            [
                "forge_scan_types_java.txt",
                "forge_scan_types_kotlin.txt",
                "forge_scan_types_go.txt",
                "forge_scan_types_ts.txt",
                "forge_scan_types_python.txt",
                "forge_scan_types_dart.txt",
                "forge_scan_types_rust.txt",
            ],
        ),
    )
    w(
        "forge_scan_methods_all.txt",
        cat_files(
            [
                "forge_scan_methods_java.txt",
                "forge_scan_methods_kotlin.txt",
                "forge_scan_methods_go.txt",
                "forge_scan_methods_ts.txt",
                "forge_scan_methods_python.txt",
                "forge_scan_methods_dart.txt",
                "forge_scan_methods_rust.txt",
            ],
        ),
    )
    w(
        "forge_scan_functions_all.txt",
        cat_files(
            [
                "forge_scan_functions_ts.txt",
                "forge_scan_functions_go.txt",
                "forge_scan_functions_python.txt",
            ],
        ),
    )
    w(
        "forge_scan_ui_all.txt",
        "\n".join(html_files + vue_files + svelte_files + angular_templates) + "\n",
    )

    types_count = len((scan_tmp / "forge_scan_types_all.txt").read_text().splitlines())
    methods_count = len((scan_tmp / "forge_scan_methods_all.txt").read_text().splitlines())
    funcs_count = len((scan_tmp / "forge_scan_functions_all.txt").read_text().splitlines())
    ui_count = len((scan_tmp / "forge_scan_ui_all.txt").read_text().splitlines())
    forms_count = len((scan_tmp / "forge_scan_html_forms.txt").read_text().splitlines())
    total = types_count + methods_count + funcs_count + ui_count
    log.log_stat(
        f"phase=1.6 types={types_count} methods={methods_count} functions={funcs_count} ui={ui_count} "
        f"html_forms={forms_count} total_potential_nodes={total}",
    )
    print(
        f"  Frontend — HTML: {len(html_files)} | Vue: {len(vue_files)} | Svelte: {len(svelte_files)} | Angular: {len(angular_templates)} | Forms: {forms_count}",
    )
    print()
    print("══════════════════════════════════════════════════════════")
    print("INVENTORY SUMMARY")
    print("══════════════════════════════════════════════════════════")
    print(f"  Types     (→ classes/):    {types_count}")
    print(f"  Methods   (→ methods/):    {methods_count}")
    print(f"  Functions (→ functions/):  {funcs_count}")
    print(f"  UI files  (→ pages/):      {ui_count}")
    print(f"  HTML forms found:          {forms_count}")
    print("══════════════════════════════════════════════════════════")
    print(f"TOTAL POTENTIAL NODES: {total}")
    print("══════════════════════════════════════════════════════════")
    print()
    print(f"Tier 1 hubs (5+ refs): {len(tier1)}")
    print(f"Tier 2 hubs (3-4 refs): {len(tier2)}")
    print()
    print(f"Phase 1 complete. All inventory files written to {scan_tmp}/forge_scan_*.txt")
    log.log_done(
        f"tier1={len(tier1)} tier2={len(tier2)} types={types_count} methods={methods_count} "
        f"functions={funcs_count} ui={ui_count} total_potential_nodes={total}",
    )

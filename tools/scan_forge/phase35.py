from __future__ import annotations

import re
from pathlib import Path

from . import grep_util, log


def run_phase35(repo: Path, scan_tmp: Path, append_routes: bool) -> None:
    repo = repo.resolve()
    scan_tmp.mkdir(parents=True, exist_ok=True)
    slug = repo.name
    log.log_start("phase35", f"repo={repo} append_routes={'append' if append_routes else 'no'}")

    print("════════════════════════════════════════════════════════")
    print("FORGE SCAN — Phase 3.4-3.5: Test Names + API Routes")
    print(f"Repo: {repo}")
    print("════════════════════════════════════════════════════════")

    test_list = scan_tmp / "forge_scan_test_files.txt"
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
    tn_path = scan_tmp / "forge_scan_test_names.txt"
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
    routes_path = scan_tmp / "forge_scan_api_routes.txt"
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
        r"\|app\.get\|app\.post\|app\.put\|app\.delete\|app\.patch"
        r"\|r\.GET\|r\.POST\|r\.PUT\|r\.DELETE\|r\.PATCH"
        r"\|@app\.route\|@router\."
        r"\|mux\.HandleFunc\|http\.HandleFunc\|e\.GET\|e\.POST\|g\.GET\|g\.POST"
    )
    raw = grep_util.run_grep_rn(
        repo,
        pat_routes,
        ["*.ts", "*.py", "*.go", "*.java", "*.kt", "*.js", "*.jsx"],
    )
    test_path_re = re.compile(r"/(test|tests|__tests__|e2e|spec)/|\.test\.|\.spec\.|/testing/")
    fixed: list[str] = []
    for ln in raw.splitlines():
        if "node_modules" in ln or "/dist/" in ln or "dist/" in ln:
            continue
        if test_path_re.search(ln):
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
        fixed.append(f"{slug}\t{rel}:{lineno}:{content}")

    with routes_path.open("a", encoding="utf-8", errors="replace") as f:
        for line in fixed:
            f.write(line + "\n")

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
        f"phase=3.5 api_routes={n_routes} get={_get} post={_post} put={_put} delete={_delete} patch={_patch}",
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

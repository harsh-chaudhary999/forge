"""Phase 4: brain node auto-generation — orchestrates ``stub_writers`` + route enrich + SCAN.json."""

from __future__ import annotations

import os
from pathlib import Path

from . import log, route_module_enrich, scan_metadata, stub_writers


def run_phase4(
    repo: Path,
    brain_dir: Path,
    role: str,
    scan_tmp: Path,
    run_dir: Path | None = None,
) -> None:
    repo = repo.resolve()
    brain_dir = brain_dir.resolve()
    scan_tmp.mkdir(parents=True, exist_ok=True)
    log.log_start("phase4", f"repo={repo} brain_dir={brain_dir} role={role}")

    for name in (
        "forge_scan_types_all.txt",
        "forge_scan_methods_all.txt",
        "forge_scan_functions_all.txt",
        "forge_scan_ui_all.txt",
        "forge_scan_source_files.txt",
    ):
        p = scan_tmp / name
        if not p.is_file() or p.stat().st_size == 0:
            log.log_warn(f"input_missing_or_empty path={p} hint=run_phase1_first")

    for d in ("classes", "methods", "functions", "pages", "modules"):
        (brain_dir / d).mkdir(parents=True, exist_ok=True)

    skipped = 0

    print("════════════════════════════════════════════════════════")
    print("FORGE SCAN — Phase 4: Brain Node Auto-Generation")
    print(f"Repo:  {repo}")
    print(f"Role:  {role}")
    print(f"Brain: {brain_dir}")
    print("════════════════════════════════════════════════════════")

    types_path = scan_tmp / "forge_scan_types_all.txt"
    funcs_path = scan_tmp / "forge_scan_functions_all.txt"
    methods_path = scan_tmp / "forge_scan_methods_all.txt"
    ui_path = scan_tmp / "forge_scan_ui_all.txt"
    sources_path = scan_tmp / "forge_scan_source_files.txt"

    print()
    print("[4.3a] Generating class nodes from forge_scan_types_all.txt...")
    n_types = len(types_path.read_text(encoding="utf-8", errors="replace").splitlines()) if types_path.is_file() else 0
    print(f"  Input: {n_types} lines")
    classes, skipped = stub_writers.write_class_stubs(brain_dir, repo, role, types_path, skipped)
    print(f"  Written: {classes} class nodes")

    print()
    print("[4.3c] Generating function nodes from forge_scan_functions_all.txt...")
    n_fn = len(funcs_path.read_text(encoding="utf-8", errors="replace").splitlines()) if funcs_path.is_file() else 0
    print(f"  Input: {n_fn} lines")
    functions, skipped = stub_writers.write_function_stubs(brain_dir, repo, role, funcs_path, skipped)
    print(f"  Written: {functions} function nodes")

    print()
    if os.environ.get("FORGE_PHASE4_SKIP_METHODS") == "1":
        print("[4.3d] Skipping method nodes (FORGE_PHASE4_SKIP_METHODS=1)")
        methods = 0
    elif not methods_path.is_file():
        print(f"[4.3d] Skipping — {methods_path} missing (run phase1)")
        methods = 0
    else:
        print("[4.3d] Generating method nodes from forge_scan_methods_all.txt (every grep hit)...")
        n_m = len(methods_path.read_text(encoding="utf-8", errors="replace").splitlines())
        print(f"  Input: {n_m} lines")
        methods, skipped = stub_writers.write_method_stubs(brain_dir, repo, role, methods_path, skipped)
        print(f"  Written: {methods} method nodes")

    print()
    print("[4.3e] Generating page nodes from forge_scan_ui_all.txt...")
    n_ui = len(ui_path.read_text(encoding="utf-8", errors="replace").splitlines()) if ui_path.is_file() else 0
    print(f"  Input: {n_ui} UI files")
    pages, skipped = stub_writers.write_page_stubs(brain_dir, repo, role, ui_path, skipped)
    print(f"  Written: {pages} page nodes")

    print()
    print("[4.3b] Generating module scaffold nodes from source directory structure...")
    modules, skipped = stub_writers.write_module_scaffolds(brain_dir, repo, role, sources_path, skipped)
    print(f"  Written: {modules} module scaffold nodes")

    n_en = 0
    if run_dir is not None:
        rp = run_dir.resolve() / "forge_scan_api_routes.txt"
        n_en = route_module_enrich.enrich_modules_from_api_routes(brain_dir, role, rp)
        if n_en:
            print(f"[4.4] Enriched {n_en} module note(s) with HTTP routes from route inventory")
        log.log_stat(f"phase=4.4 route_module_enrich_updated={n_en}")

    total = classes + methods + functions + pages + modules
    print()
    print("════════════════════════════════════════════════════════")
    print("PHASE 4 AUTO-GENERATION COMPLETE")
    print("════════════════════════════════════════════════════════")
    print(f"  Classes     (classes/):   {classes}")
    print(f"  Methods     (methods/):     {methods}")
    print(f"  Functions   (functions/): {functions}")
    print(f"  Pages       (pages/):     {pages}")
    print(f"  Modules     (modules/):   {modules}")
    print(f"  Skipped (already exist):  {skipped}")
    print("════════════════════════════════════════════════════════")
    print(f"TOTAL NEW NODES WRITTEN: {total}")
    print("════════════════════════════════════════════════════════")
    scan_metadata.merge_scan_json(brain_dir, repo, role, scan_tmp)
    print(f"SCAN.json updated under {brain_dir}")
    log.log_done(
        f"classes={classes} methods={methods} functions={functions} pages={pages} modules={modules} "
        f"skipped_existing={skipped} total_new={total}",
    )

from __future__ import annotations

import os
import re
from pathlib import Path

from . import grep_util, log, modslug, scan_metadata


def _parse_grep_line(line: str) -> tuple[str, str, str]:
    m = re.search(r":([0-9]+):", line)
    if not m:
        return "", "", ""
    lineno = m.group(1)
    start = m.start()
    file = line[:start]
    content = line[m.end() :]
    return file, lineno, content


def _detect_lang(path: str) -> str:
    p = path.lower()
    if p.endswith(".java"):
        return "Java"
    if p.endswith(".kt"):
        return "Kotlin"
    if p.endswith(".go"):
        return "Go"
    if p.endswith(".ts"):
        return "TypeScript"
    if p.endswith(".tsx"):
        return "TypeScript (TSX)"
    if p.endswith(".js"):
        return "JavaScript"
    if p.endswith(".jsx"):
        return "JavaScript (JSX)"
    if p.endswith(".py"):
        return "Python"
    if p.endswith(".dart"):
        return "Dart"
    if p.endswith(".rs"):
        return "Rust"
    if p.endswith(".rb"):
        return "Ruby"
    if p.endswith(".swift"):
        return "Swift"
    return "Unknown"


def run_phase4(repo: Path, brain_dir: Path, role: str, scan_tmp: Path) -> None:
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

    classes = methods = functions = pages = modules = skipped = 0

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

    # 4.3a classes
    print()
    print("[4.3a] Generating class nodes from forge_scan_types_all.txt...")
    type_lines = types_path.read_text(encoding="utf-8", errors="replace").splitlines() if types_path.is_file() else []
    print(f"  Input: {len(type_lines)} lines")
    type_kw = re.compile(
        r"\b(class|interface|enum|object|data class|sealed class|abstract class|annotation class|struct|trait|protocol|@interface)\b ([A-Z][a-zA-Z0-9_]*)",
    )
    gen_re = re.compile(r"(Generated\.|_pb2\.|DataBinding|ViewBinding|Binding\b|\.generated\.)")
    for line in type_lines:
        if not line.strip():
            continue
        fpath, lineno, content = _parse_grep_line(line)
        if not fpath:
            continue
        m = type_kw.search(content)
        if not m:
            continue
        kind, cls = m.group(1), m.group(2)
        if gen_re.search(fpath):
            continue
        try:
            rel_file = str(Path(fpath).resolve().relative_to(repo).as_posix())
        except ValueError:
            continue
        lang = _detect_lang(fpath)
        module = Path(rel_file).stem
        dir_name = str(Path(rel_file).parent.as_posix())
        if dir_name == ".":
            dir_name = "root"
        node = brain_dir / "classes" / f"{role}-{cls}.md"
        if node.is_file():
            skipped += 1
            continue
        node.write_text(
            "\n".join(
                [
                    f"# {kind}: {cls}",
                    "",
                    f"**Module:** [[modules/{role}-{module}]]",
                    f"**File:** `{rel_file}:{lineno}`",
                    f"**Language:** {lang}",
                    f"**Kind:** {kind}",
                    "",
                    "## Purpose",
                    "_Auto-generated stub — enrich during Phase 3 hub read._",
                    "",
                    "## Key Responsibilities",
                    f"_What problem does this {kind} solve?_",
                    "",
                    "## Key Methods",
                    f"_See the `methods/` folder — auto stubs use `{role}-m-<cksum>` (full inventory); optional hand nodes `{role}-{cls}-<method>`._",
                    "",
                    "## Extends / Implements",
                    "_Fill in during Phase 3 read._",
                    "",
                    "## Used By",
                    "_Populated by phase56 / manual cross-repo notes after phase5 prep._",
                    "",
                    "## Location in Structure",
                    f"**Repo role:** {role} | **Package:** {dir_name}",
                    "",
                ],
            ),
            encoding="utf-8",
            errors="replace",
        )
        classes += 1
    print(f"  Written: {classes} class nodes")
    log.log_stat(f"phase=4.3a classes_written={classes} input_lines={len(type_lines)}")

    # 4.3c functions
    print()
    print("[4.3c] Generating function nodes from forge_scan_functions_all.txt...")
    flines = funcs_path.read_text(encoding="utf-8", errors="replace").splitlines() if funcs_path.is_file() else []
    print(f"  Input: {len(flines)} lines")
    generic = re.compile(r"^(get|set|is|has|to|of|by|on|do)$")
    for line in flines:
        if not line.strip():
            continue
        fpath, lineno, content = _parse_grep_line(line)
        if not fpath:
            continue
        func = ""
        m = re.search(r"\bfunction ([a-zA-Z][a-zA-Z0-9_]*)", content)
        if m:
            func = m.group(1)
        if not func:
            m = re.search(r"\bdef ([a-zA-Z][a-zA-Z0-9_]*)", content)
            if m:
                func = m.group(1)
        if not func:
            m = re.search(r"\bfunc ([A-Z][a-zA-Z0-9_]*)\(", content)
            if m:
                func = m.group(1)
        if not func:
            m = re.search(r"\bconst ([a-zA-Z][a-zA-Z0-9_]*)\s*=", content)
            if m:
                func = m.group(1)
        if not func or len(func) <= 1 or generic.match(func):
            continue
        try:
            rel_file = str(Path(fpath).resolve().relative_to(repo).as_posix())
        except ValueError:
            continue
        lang = _detect_lang(fpath)
        module = Path(rel_file).stem
        node = brain_dir / "functions" / f"{role}-{func}.md"
        if node.is_file():
            skipped += 1
            continue
        node.write_text(
            "\n".join(
                [
                    f"# Function: {func}",
                    "",
                    f"**Module:** [[modules/{role}-{module}]]",
                    f"**File:** `{rel_file}:{lineno}`",
                    f"**Language:** {lang}",
                    "",
                    "## Purpose",
                    "_Auto-generated stub — enrich during Phase 3 hub read._",
                    "",
                    "## Parameters",
                    "_Fill in: argument names and types._",
                    "",
                    "## Returns",
                    "_Fill in: return type and what it represents._",
                    "",
                    "## Called By",
                    "_Fill in during Phase 3 or manual cross-repo correlation (phase56 covers HTTP paths)._",
                    "",
                    "## Calls",
                    "_Fill in during Phase 3 or manual cross-repo correlation (phase56 covers HTTP paths)._",
                    "",
                    "## Location in Structure",
                    f"**Repo role:** {role}",
                    "",
                ],
            ),
            encoding="utf-8",
            errors="replace",
        )
        functions += 1
    print(f"  Written: {functions} function nodes")
    log.log_stat(f"phase=4.3c functions_written={functions} input_lines={len(flines)}")

    # 4.3d methods
    print()
    if os.environ.get("FORGE_PHASE4_SKIP_METHODS") == "1":
        print("[4.3d] Skipping method nodes (FORGE_PHASE4_SKIP_METHODS=1)")
    elif not methods_path.is_file():
        print(f"[4.3d] Skipping — {methods_path} missing (run phase1)")
        log.log_warn(f"missing {methods_path}")
    else:
        print("[4.3d] Generating method nodes from forge_scan_methods_all.txt (every grep hit)...")
        mlines = methods_path.read_text(encoding="utf-8", errors="replace").splitlines()
        print(f"  Input: {len(mlines)} lines")
        for line in mlines:
            if not line.strip():
                continue
            fpath, lineno, content = _parse_grep_line(line)
            if not fpath:
                continue
            try:
                rel_file = str(Path(fpath).resolve().relative_to(repo).as_posix())
            except ValueError:
                continue
            lang = _detect_lang(fpath)
            dir_name = str(Path(rel_file).parent.as_posix())
            if dir_name == ".":
                dir_name = "root"
            mid = grep_util.cksum_first_field(line)
            node = brain_dir / "methods" / f"{role}-m-{mid}.md"
            if node.is_file():
                skipped += 1
                continue
            sig = " ".join(content.splitlines()[:3])[:400]
            mod_slug = modslug.forge_mod_dirslug_from_dir(dir_name)
            node.write_text(
                "\n".join(
                    [
                        "# Method (inventory)",
                        "",
                        f"**Module:** [[modules/{role}-{mod_slug}]]",
                        f"**Class hub:** _See the `classes/` folder for types in `{rel_file}` — link the owning class during enrich._",
                        f"**File:** `{rel_file}:{lineno}`",
                        f"**Language:** {lang}",
                        f"**Stable id:** `{role}-m-{mid}` (cksum of grep line — unique per grep hit)",
                        "",
                        "## Signature (Phase 1 grep)",
                        "```text",
                        sig,
                        "```",
                        "",
                        "## Purpose",
                        "_Auto-generated from Phase 1.6 — **not** limited to Tier 1 hubs. Enrich by reading this line in context._",
                        "",
                        "## Parameters / return",
                        "_Fill in during read._",
                        "",
                        "## Calls / data flow",
                        "_Fill in during read or manual cross-repo pass._",
                        "",
                        "## Location",
                        f"**Repo role:** {role} | **Directory:** {dir_name}",
                        "",
                    ],
                ),
                encoding="utf-8",
                errors="replace",
            )
            methods += 1
        print(f"  Written: {methods} method nodes")
        log.log_stat(f"phase=4.3d methods_written={methods} input_lines={len(mlines)}")

    # 4.3e pages
    print()
    print("[4.3e] Generating page nodes from forge_scan_ui_all.txt...")
    uilines = ui_path.read_text(encoding="utf-8", errors="replace").splitlines() if ui_path.is_file() else []
    print(f"  Input: {len(uilines)} UI files")
    for file_s in uilines:
        if not file_s.strip():
            continue
        fp = Path(file_s.strip()).resolve()
        if not fp.is_file():
            continue
        try:
            rel_file = fp.relative_to(repo).as_posix()
        except ValueError:
            continue
        name = fp.stem
        suf = fp.suffix.lower()
        if suf in (".html", ".htm"):
            fmt = "HTML"
        elif suf == ".vue":
            fmt = "Vue SFC"
        elif suf == ".svelte":
            fmt = "Svelte"
        elif fp.name.endswith(".component.html"):
            fmt = "Angular Template"
        elif suf == ".tsx":
            fmt = "TypeScript (TSX)"
        elif suf == ".jsx":
            fmt = "JavaScript (JSX)"
        else:
            fmt = "HTML"
        kind = "component"
        rl = rel_file.lower()
        if re.search(r"(pages?|screens?|views?)[/\\]", rl):
            kind = "page"
        if re.search(r"layouts?[/\\]", rl):
            kind = "layout"
        if re.search(r"(dialogs?|modals?)[/\\]", rl):
            kind = "dialog"
        if re.search(r"(partials?|fragments?)[/\\]", rl):
            kind = "partial"
        route = "unknown"
        rm = re.search(r"(pages|app|routes)/.*", rel_file)
        if rm:
            route_path = re.sub(r"\.[^.]+$", "", rm.group(0))
            route_path = re.sub(r"^(pages|app|routes)/", "", route_path)
            route = f"/{route_path}"
        node = brain_dir / "pages" / f"{role}-{name}.md"
        if node.is_file():
            skipped += 1
            continue
        node.write_text(
            "\n".join(
                [
                    f"# Page: {name}",
                    "",
                    f"**File:** `{rel_file}`",
                    f"**Language / Format:** {fmt}",
                    f"**Kind:** {kind}",
                    f"**Route / URL:** `{route}`",
                    "",
                    "## Purpose",
                    "_Auto-generated stub — enrich during Phase 3 hub read._",
                    "",
                    "## Key UI Elements",
                    "_Fill in: main components, data displayed, navigation._",
                    "",
                    "## Forms",
                    "_Fill in: form names, fields, submit actions._",
                    "",
                    "## Script / Component Dependencies",
                    "_Fill in: components imported, composables/hooks used._",
                    "",
                    "## API Calls Made",
                    "_Populated by phase56 / manual cross-repo notes after phase5 prep._",
                    "",
                    "## Location in Structure",
                    f"**Repo role:** {role}",
                    "",
                ],
            ),
            encoding="utf-8",
            errors="replace",
        )
        pages += 1
    print(f"  Written: {pages} page nodes")
    log.log_stat(f"phase=4.3e pages_written={pages} input_lines={len(uilines)}")

    # 4.3b modules (after bash order: 4.3e then 4.3b in file - actually bash does 4.3e then 4.3b)
    print()
    print("[4.3b] Generating module scaffold nodes from source directory structure...")
    dirs: set[str] = set()
    if sources_path.is_file():
        for line in sources_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                rel = Path(line.strip()).resolve().relative_to(repo).as_posix()
            except ValueError:
                continue
            d = str(Path(rel).parent.as_posix())
            dirs.add(d if d != "." else "root")
    dirs.discard("")
    for dir_name in sorted(dirs):
        d = dir_name if dir_name != "root" else "."
        module_name = modslug.forge_mod_dirslug_from_dir(d)
        node = brain_dir / "modules" / f"{role}-{module_name}.md"
        if node.is_file():
            skipped += 1
            continue
        disp = "root" if dir_name == "root" else dir_name
        node.write_text(
            "\n".join(
                [
                    f"# Module: {role} / {disp}",
                    "",
                    f"**Directory:** `{disp}/`",
                    f"**Repo role:** {role}",
                    "",
                    "## Purpose",
                    "_Auto-generated scaffold — enrich during Phase 3._",
                    "",
                    "## Key Types Defined Here",
                    f"_See the `classes/` folder for individual class nodes with prefix `{role}-`_",
                    "",
                    "## Exports",
                    "_Fill in: exported functions, types, constants._",
                    "",
                    "## Internal Dependencies",
                    "_Fill in: other modules this one imports from._",
                    "",
                    "## Calls (cross-repo)",
                    "_After phase5 + phase56 (markers `FORGE:AUTO_CROSS_REPO_OUT`). Heuristic — verify._",
                    "",
                    "## Called By (cross-repo)",
                    "_Same: phase56 (`FORGE:AUTO_CROSS_REPO_IN`). Optional manual rows only if needed._",
                    "",
                ],
            ),
            encoding="utf-8",
            errors="replace",
        )
        modules += 1
    print(f"  Written: {modules} module scaffold nodes")
    log.log_stat(f"phase=4.3b modules_written={modules} unique_dirs={len(dirs)}")

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

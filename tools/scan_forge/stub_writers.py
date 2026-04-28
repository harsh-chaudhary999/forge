"""Write brain markdown stubs from Phase 1 inventories (reusable from ``phase4``)."""

from __future__ import annotations

import os
import re
from pathlib import Path

from . import grep_util, html_ui_links, inventory_text, js_ui_links, log, modslug

_LINKABLE_SCRIPT_FMTS = frozenset(
    {
        "JavaScript (JSX)",
        "TypeScript (TSX)",
        "TypeScript",
        "JavaScript",
    },
)


def write_class_stubs(
    brain_dir: Path,
    repo: Path,
    role: str,
    types_path: Path,
    skipped: int,
) -> tuple[int, int]:
    written = 0
    type_lines = types_path.read_text(encoding="utf-8", errors="replace").splitlines() if types_path.is_file() else []
    type_kw = re.compile(
        r"\b(class|interface|enum|object|data class|sealed class|abstract class|annotation class|struct|trait|protocol|@interface)\b ([A-Z][a-zA-Z0-9_]*)",
    )
    gen_re = re.compile(r"(Generated\.|_pb2\.|DataBinding|ViewBinding|Binding\b|\.generated\.)")
    for line in type_lines:
        if not line.strip():
            continue
        fpath, lineno, content = inventory_text.parse_grep_line(line)
        if not fpath:
            continue
        m = type_kw.search(content)
        if not m:
            continue
        kind, cls = m.group(1), m.group(2)
        if gen_re.search(fpath):
            continue
        rel_file = inventory_text.repo_relative_posix(repo, fpath)
        if rel_file is None:
            continue
        lang = inventory_text.detect_language(fpath)
        dir_name = str(Path(rel_file).parent.as_posix())
        if dir_name == ".":
            dir_name = "root"
        mod_basename = modslug.forge_mod_node_basename_from_rel(role, rel_file)
        node = brain_dir / "classes" / f"{role}-{cls}.md"
        if node.is_file():
            skipped += 1
            continue
        node.write_text(
            "\n".join(
                [
                    f"# {kind}: {cls}",
                    "",
                    f"**Module:** [[modules/{mod_basename}]]",
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
        written += 1
    log.log_stat(f"phase=4.3a classes_written={written} input_lines={len(type_lines)}")
    return written, skipped


def write_function_stubs(
    brain_dir: Path,
    repo: Path,
    role: str,
    funcs_path: Path,
    skipped: int,
) -> tuple[int, int]:
    written = 0
    flines = funcs_path.read_text(encoding="utf-8", errors="replace").splitlines() if funcs_path.is_file() else []
    generic = re.compile(r"^(get|set|is|has|to|of|by|on|do)$")
    for line in flines:
        if not line.strip():
            continue
        fpath, lineno, content = inventory_text.parse_grep_line(line)
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
        rel_file = inventory_text.repo_relative_posix(repo, fpath)
        if rel_file is None:
            continue
        lang = inventory_text.detect_language(fpath)
        mod_basename = modslug.forge_mod_node_basename_from_rel(role, rel_file)
        node = brain_dir / "functions" / f"{role}-{func}.md"
        if node.is_file():
            skipped += 1
            continue
        node.write_text(
            "\n".join(
                [
                    f"# Function: {func}",
                    "",
                    f"**Module:** [[modules/{mod_basename}]]",
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
        written += 1
    log.log_stat(f"phase=4.3c functions_written={written} input_lines={len(flines)}")
    return written, skipped


def write_method_stubs(
    brain_dir: Path,
    repo: Path,
    role: str,
    methods_path: Path,
    skipped: int,
) -> tuple[int, int]:
    written = 0
    if os.environ.get("FORGE_PHASE4_SKIP_METHODS") == "1":
        log.log_stat("phase=4.3d methods_written=0 skipped_env=FORGE_PHASE4_SKIP_METHODS")
        return 0, skipped
    if not methods_path.is_file():
        log.log_warn(f"missing {methods_path}")
        return 0, skipped
    mlines = methods_path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in mlines:
        if not line.strip():
            continue
        fpath, lineno, content = inventory_text.parse_grep_line(line)
        if not fpath:
            continue
        rel_file = inventory_text.repo_relative_posix(repo, fpath)
        if rel_file is None:
            continue
        lang = inventory_text.detect_language(fpath)
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
        written += 1
    log.log_stat(f"phase=4.3d methods_written={written} input_lines={len(mlines)}")
    return written, skipped


def write_page_stubs(
    brain_dir: Path,
    repo: Path,
    role: str,
    ui_path: Path,
    skipped: int,
) -> tuple[int, int]:
    written = 0
    uilines = ui_path.read_text(encoding="utf-8", errors="replace").splitlines() if ui_path.is_file() else []

    page_entries: list[tuple[Path, str, str, str, str, str, str]] = []
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
        elif suf == ".ts":
            fmt = "TypeScript"
        elif suf == ".js":
            fmt = "JavaScript"
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
        page_bn = modslug.forge_page_node_basename_from_rel(role, rel_file)
        page_entries.append((fp, rel_file, name, fmt, kind, route, page_bn))

    rel_to_page_bn = {e[1]: e[6] for e in page_entries}
    incoming_html: dict[str, list[str]] = {}
    incoming_js: dict[str, list[str]] = {}
    for fp, rel_file, _name, fmt, _k, _r, _bn in page_entries:
        if fmt == "HTML":
            for target_rel in html_ui_links.html_linked_asset_paths(fp, repo):
                if target_rel not in rel_to_page_bn:
                    continue
                incoming_html.setdefault(target_rel, []).append(rel_file)
        elif fmt in _LINKABLE_SCRIPT_FMTS:
            for target_rel in js_ui_links.static_import_targets(fp, repo):
                if target_rel not in rel_to_page_bn:
                    continue
                incoming_js.setdefault(target_rel, []).append(rel_file)

    for fp, rel_file, name, fmt, kind, route, page_bn in page_entries:
        node = brain_dir / "pages" / f"{page_bn}.md"
        if node.is_file():
            skipped += 1
            continue

        linked_lines: list[str] = []
        if fmt == "HTML":
            targets = html_ui_links.html_linked_asset_paths(fp, repo)
            wikis: list[str] = []
            for t in targets:
                tbn = rel_to_page_bn.get(t)
                if tbn:
                    wikis.append(f"- [[pages/{tbn}]] — `{t}`")
                else:
                    wikis.append(f"- `{t}` _(no page node — not in UI inventory or missing file)_")
            if wikis:
                linked_lines.extend(
                    [
                        "",
                        "## Linked assets (auto)",
                        "_From `<script src>` / `link rel=modulepreload` in this HTML._",
                        *wikis,
                    ],
                )

        if fmt in _LINKABLE_SCRIPT_FMTS:
            mod_targets = js_ui_links.static_import_targets(fp, repo)
            mw: list[str] = []
            for t in mod_targets:
                tbn = rel_to_page_bn.get(t)
                if tbn:
                    mw.append(f"- [[pages/{tbn}]] — `{t}`")
                else:
                    mw.append(f"- `{t}` _(no page node — extend UI inventory or bare package path)_")
            if mw:
                linked_lines.extend(
                    [
                        "",
                        "## Linked modules (auto)",
                        "_From static `import` / `export … from` in this file (local paths only)._",
                        *mw,
                    ],
                )

        incoming_lines: list[str] = []
        h_srcs = incoming_html.get(rel_file, [])
        if h_srcs:
            bullets = []
            for srel in sorted(set(h_srcs)):
                sbn = rel_to_page_bn.get(srel)
                if sbn:
                    bullets.append(f"- [[pages/{sbn}]] — `{srel}`")
                else:
                    bullets.append(f"- `{srel}`")
            incoming_lines.extend(
                [
                    "",
                    "## Referenced from HTML (auto)",
                    "_Other UI notes whose HTML entry points load this file._",
                    *bullets,
                ],
            )
        j_srcs = incoming_js.get(rel_file, [])
        if j_srcs:
            jbullets: list[str] = []
            for srel in sorted(set(j_srcs)):
                sbn = rel_to_page_bn.get(srel)
                if sbn:
                    jbullets.append(f"- [[pages/{sbn}]] — `{srel}`")
                else:
                    jbullets.append(f"- `{srel}`")
            incoming_lines.extend(
                [
                    "",
                    "## Imported by (auto)",
                    "_Other UI modules that statically import this file._",
                    *jbullets,
                ],
            )

        node.write_text(
            "\n".join(
                [
                    f"# Page: {name}",
                    "",
                    f"**File:** `{rel_file}`",
                    f"**Stable page id:** `{page_bn}`",
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
                    *linked_lines,
                    *incoming_lines,
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
        written += 1
    log.log_stat(f"phase=4.3e pages_written={written} input_lines={len(uilines)}")
    return written, skipped


def write_module_scaffolds(
    brain_dir: Path,
    repo: Path,
    role: str,
    sources_path: Path,
    extra_inventory_paths: list[Path] | None,
    skipped: int,
) -> tuple[int, int]:
    def _add_dir_from_path(path_s: str) -> None:
        rel = inventory_text.repo_relative_posix(repo, path_s)
        if rel is None:
            return
        d = str(Path(rel).parent.as_posix())
        dirs.add(d if d != "." else "root")

    written = 0
    dirs: set[str] = set()
    if sources_path.is_file():
        for line in sources_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            _add_dir_from_path(line.strip())

    for inv in extra_inventory_paths or []:
        if not inv.is_file():
            continue
        for line in inv.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            fpath, _lineno, _content = inventory_text.parse_grep_line(line)
            if not fpath:
                continue
            _add_dir_from_path(fpath)

    dirs.discard("")
    if any((repo / n).is_file() for n in ("openapi.json", "swagger.json", "openapi.yaml", "openapi.yml")):
        dirs.add("root")
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
        written += 1
    log.log_stat(f"phase=4.3b modules_written={written} unique_dirs={len(dirs)}")
    return written, skipped

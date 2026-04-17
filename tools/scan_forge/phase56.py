from __future__ import annotations

import re
from pathlib import Path

from . import grep_util, log, modslug, openapi_routes


BEGIN_OUT = "<!-- FORGE:AUTO_CROSS_REPO_OUT -->"
END_OUT = "<!-- FORGE:AUTO_CROSS_REPO_OUT_END -->"
BEGIN_IN = "<!-- FORGE:AUTO_CROSS_REPO_IN -->"
END_IN = "<!-- FORGE:AUTO_CROSS_REPO_IN_END -->"


def _urls_in_content(content: str) -> list[str]:
    """Harvest URL path strings from a grep call-site line (quoted, absolute, or /api…)."""
    out: set[str] = set()

    def _add(u: str) -> None:
        u = u.split("?", 1)[0].split("#", 1)[0].strip()
        if u.startswith("/") and len(u) > 1:
            out.add(u)

    for m in re.finditer(r"/api[^\s'\"`?#)]+", content):
        _add(m.group(0))
    for m in re.finditer(r"/v[0-9]+[^\s'\"`?#)]+", content):
        _add(m.group(0))
    for m in re.finditer(r"/graphql[^\s'\"`?#)]+", content):
        _add(m.group(0))
    for m in re.finditer(r"/rest[^\s'\"`?#)]+", content):
        _add(m.group(0))
    for m in re.finditer(r"['\"`](/[^'\"`]+)['\"`]", content):
        _add(m.group(1))
    for m in re.finditer(r"https?://[^/\s'\"]+(/[^\s'\"`?#)]+)", content):
        _add(m.group(1))
    return sorted(out)


def _strip_marker_blocks(text: str, begin: str, end: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == begin:
            i += 1
            while i < len(lines) and lines[i].strip() != end:
                i += 1
            if i < len(lines) and lines[i].strip() == end:
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out) + ("\n" if out else "")


def _resolve_module_file(parent: Path, repo: str, rel: str) -> Path | None:
    slug = modslug.forge_mod_node_basename_from_rel(repo, rel)
    for candidate in (parent / repo / "modules" / f"{slug}.md", parent / "modules" / f"{slug}.md"):
        if candidate.is_file():
            return candidate
    return None


def _parse_route_line(ln: str) -> tuple[str, str, str, str] | None:
    """Return (repo, rel, lineno, raw_line) for a forge_scan_api_routes line."""
    if "\t" not in ln:
        return None
    be_repo, rest = ln.split("\t", 1)
    parts = rest.split(":", 2)
    if len(parts) < 3:
        return None
    be_rel, be_lineno, _content = parts[0], parts[1], parts[2]
    return be_repo, be_rel, be_lineno, ln


def run_phase56(brain_parent: Path, scan_tmp: Path) -> None:
    brain_parent = brain_parent.resolve()
    scan_tmp.mkdir(parents=True, exist_ok=True)
    log.log_start("phase56", f"brain_parent={brain_parent}")

    calls = scan_tmp / "forge_scan_all_callsites.txt"
    routes = scan_tmp / "forge_scan_api_routes.txt"
    if not calls.is_file() or calls.stat().st_size == 0:
        log.log_warn(f"skip empty_or_missing {calls}")
        log.log_done("edges=0")
        return
    if not routes.is_file() or routes.stat().st_size == 0:
        log.log_warn(f"skip empty_or_missing {routes}")
        log.log_done("edges=0")
        return

    for modf in brain_parent.rglob("*.md"):
        rel_posix = str(modf).replace("\\", "/")
        if "/modules/" not in rel_posix:
            continue
        txt = modf.read_text(encoding="utf-8", errors="replace")
        new_txt = txt
        new_txt = _strip_marker_blocks(new_txt, BEGIN_OUT, END_OUT)
        new_txt = _strip_marker_blocks(new_txt, BEGIN_IN, END_IN)
        if new_txt != txt:
            modf.write_text(new_txt, encoding="utf-8", errors="replace")

    routes_body = routes.read_text(encoding="utf-8", errors="replace")
    routes_merged_lines = [ln for ln in routes_body.splitlines() if ln.strip()]
    n_routes_before_alias = len(routes_merged_lines)
    alias_file = brain_parent / "route-aliases.tsv"
    if alias_file.is_file():
        extra = [
            ln
            for ln in alias_file.read_text(encoding="utf-8", errors="replace").splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")
        ]
        routes_merged_lines.extend(extra)
        log.log_stat(f"phase=5.6 route_aliases_tsv=appended non_comment_lines={len(extra)}")
    else:
        log.log_stat("phase=5.6 route_aliases_tsv=absent")

    def _provenance_for_line(idx: int, ln: str, matched_by: str) -> str:
        """How this route line was matched — for brain honesty (not runtime proof)."""
        if idx >= n_routes_before_alias:
            return "MANUAL_ALIAS"
        if "_forge_openapi" in ln:
            return "OPENAPI"
        if matched_by == "substring":
            return "GREP_SUBSTRING"
        return "GREP_TEMPLATE"

    def hit_route(url: str) -> tuple[str, str, str, str] | None:
        u = url.split("?", 1)[0].split("#", 1)[0]
        for idx, ln in enumerate(routes_merged_lines):
            parsed = _parse_route_line(ln)
            if not parsed:
                continue
            be_repo, be_rel, be_lineno, _raw = parsed
            if u in ln:
                prov = _provenance_for_line(idx, ln, "substring")
                return be_repo, be_rel, be_lineno, prov
            for tmpl in openapi_routes.path_templates_in_route_line(ln):
                if openapi_routes.path_template_matches(u, tmpl):
                    prov = _provenance_for_line(idx, ln, "template")
                    return be_repo, be_rel, be_lineno, prov
        return None

    calls_by_mod: dict[str, list[str]] = {}
    bys_by_mod: dict[str, list[str]] = {}
    mod_paths: dict[str, Path] = {}
    edges: list[str] = []
    edges_n = 0

    for raw in calls.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.strip() or "\t" not in raw:
            continue
        repo, rest = raw.split("\t", 1)
        if ":" not in rest:
            continue
        caller_rel, rem = rest.split(":", 1)
        if ":" not in rem:
            continue
        caller_line, content = rem.split(":", 1)
        for url in _urls_in_content(content):
            hit = hit_route(url)
            if not hit:
                continue
            be_repo, be_rel, be_lineno, provenance = hit
            caller_mod = _resolve_module_file(brain_parent, repo, caller_rel)
            be_mod = _resolve_module_file(brain_parent, be_repo, be_rel)
            if not caller_mod or not be_mod or caller_mod == be_mod:
                continue
            caller_slug = caller_mod.stem
            be_slug = be_mod.stem
            tag = f"`[{provenance}]`"
            b_call = f"- {tag} `{url}` → [[{be_slug}]] (`{be_repo}/{be_rel}:{be_lineno}`)"
            b_by = f"- {tag} [[{caller_slug}]] (`{repo}/{caller_rel}:{caller_line}`) uses `{url}`"
            ck_c = grep_util.cksum_first_field(str(caller_mod))
            ck_b = grep_util.cksum_first_field(str(be_mod))
            calls_by_mod.setdefault(ck_c, []).append(b_call)
            mod_paths[ck_c] = caller_mod
            bys_by_mod.setdefault(ck_b, []).append(b_by)
            mod_paths[ck_b] = be_mod
            edges.append(f"{repo}\t{caller_rel}\t{be_repo}\t{be_rel}\t{url}\t{provenance}")
            edges_n += 1

    def _append_block(target: Path, begin: str, end: str, title: str, bullets: list[str]) -> None:
        if not bullets:
            return
        body = (
            f"{begin}\n\n### {title} _(auto phase56 — verify)_\n\n"
            + "\n".join(sorted(set(bullets)))
            + f"\n\n{end}\n\n"
        )
        cur = target.read_text(encoding="utf-8", errors="replace").rstrip()
        target.write_text(cur + "\n\n" + body, encoding="utf-8", errors="replace")

    for ck, lines in calls_by_mod.items():
        target = mod_paths.get(ck)
        if target and lines:
            _append_block(target, BEGIN_OUT, END_OUT, "Outgoing cross-repo (Calls)", lines)
    for ck, lines in bys_by_mod.items():
        target = mod_paths.get(ck)
        if target and lines:
            _append_block(target, BEGIN_IN, END_IN, "Incoming cross-repo (Called by)", lines)

    if edges:
        out_md = brain_parent / "cross-repo-automap.md"
        out_md.write_text(
            "# Cross-repo automap (phase56)\n\n"
            "_Heuristic join (grep routes + OpenAPI paths + call sites) — verify against runtime behavior._\n\n"
            "TSV columns: `caller_repo`, `caller_rel_path`, `route_repo`, `route_rel_path`, "
            "`url_path`, `provenance` (`OPENAPI` | `GREP_SUBSTRING` | `GREP_TEMPLATE` | `MANUAL_ALIAS`).\n\n"
            "```tsv\n"
            + "\n".join(sorted(set(edges)))
            + "\n```\n",
            encoding="utf-8",
            errors="replace",
        )

    uniq: set[str] = set()
    for modf in brain_parent.rglob("*.md"):
        try:
            t = modf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if BEGIN_OUT in t or BEGIN_IN in t:
            uniq.add(str(modf.resolve()))
    touched = len(uniq)

    print(f"Phase 5.6: auto-linked cross-repo blocks (OUT/IN markers). Edges={edges_n} module_files≈{touched}")
    log.log_stat(f"phase=5.6 edges={edges_n} modules_with_out_block={touched}")
    log.log_done(f"edges={edges_n} automap={'yes' if edges else 'no'}")

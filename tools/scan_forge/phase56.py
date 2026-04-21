from __future__ import annotations

import re
from pathlib import Path

from . import grep_util, log, modslug, openapi_routes


BEGIN_OUT = "<!-- FORGE:AUTO_CROSS_REPO_OUT -->"
END_OUT = "<!-- FORGE:AUTO_CROSS_REPO_OUT_END -->"
BEGIN_IN = "<!-- FORGE:AUTO_CROSS_REPO_IN -->"
END_IN = "<!-- FORGE:AUTO_CROSS_REPO_IN_END -->"

# Extract explicit HTTP method from a call-site line
_METHOD_RE = re.compile(
    r"method\s*[:=]\s*['\"]?(GET|POST|PUT|PATCH|DELETE|HEAD)['\"]?"
    r"|\.(?P<dot>get|post|put|patch|delete|head)\s*\(",
    re.IGNORECASE,
)

# Extract method from a route declaration line (decorator / annotation style)
_ROUTE_METHOD_RE = re.compile(
    r"@(?:Get|Post|Put|Patch|Delete|Head)Mapping"
    r"|@(?:GET|POST|PUT|PATCH|DELETE|HEAD)\("
    r"|\b(?:router|app|router)\.(get|post|put|patch|delete|head)\s*\(",
    re.IGNORECASE,
)


def _http_method_from_callsite(content: str) -> str | None:
    """Return uppercase HTTP method if unambiguously detectable, else None."""
    m = _METHOD_RE.search(content)
    if not m:
        return None
    if m.group("dot"):
        return m.group("dot").upper()
    # Extract from method: 'POST' pattern
    raw = content[m.start():m.end()]
    for method in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"):
        if method in raw.upper():
            return method
    return None


def _http_method_from_route(route_line: str) -> str | None:
    """Extract HTTP method declared in a route definition line."""
    m = _ROUTE_METHOD_RE.search(route_line)
    if not m:
        return None
    raw = m.group(0).upper()
    for method in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"):
        if method in raw:
            return method
    return None


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


def run_phase56(brain_parent: Path, scan_tmp: Path, topology=None) -> None:
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

    def hit_route(url: str, caller_method: str | None = None) -> tuple[str, str, str, str] | None:
        u = url.split("?", 1)[0].split("#", 1)[0]
        for idx, ln in enumerate(routes_merged_lines):
            parsed = _parse_route_line(ln)
            if not parsed:
                continue
            be_repo, be_rel, be_lineno, _raw = parsed
            # HTTP method filter (4a): if both sides have a declared method, they must match
            if caller_method:
                route_method = _http_method_from_route(ln)
                if route_method and route_method != caller_method:
                    continue
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
    edges_http = 0
    edges_topology = 0
    unresolved: list[tuple[str, str]] = []  # (caller_repo/caller_rel, url)

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
        caller_method = _http_method_from_callsite(content)

        for url in _urls_in_content(content):
            hit = hit_route(url, caller_method)
            if hit:
                be_repo, be_rel, be_lineno, provenance = hit
                caller_mod = _resolve_module_file(brain_parent, repo, caller_rel)
                be_mod = _resolve_module_file(brain_parent, be_repo, be_rel)
                if not caller_mod or not be_mod or caller_mod == be_mod:
                    if not caller_mod or not be_mod:
                        unresolved.append((f"{repo}/{caller_rel}", url))
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
                edges_http += 1
            elif topology is not None:
                # 4b: topology-assisted fallback for unresolved URLs
                caller_role = repo  # repo name used as role key
                callees = topology.callees_of(caller_role)
                for callee_role in callees:
                    caller_mod = _resolve_module_file(brain_parent, repo, caller_rel)
                    # resolve callee brain dir: look for any module under callee role
                    be_mod_candidate = None
                    for candidate in brain_parent.rglob(f"modules/{callee_role}-*.md"):
                        be_mod_candidate = candidate
                        break
                    if not be_mod_candidate:
                        # try repo-named subdir
                        for candidate in (brain_parent / callee_role / "modules").glob("*.md") if (brain_parent / callee_role / "modules").is_dir() else []:
                            be_mod_candidate = candidate
                            break
                    if not caller_mod or not be_mod_candidate:
                        unresolved.append((f"{repo}/{caller_rel}", url))
                        continue
                    caller_slug = caller_mod.stem
                    be_slug = be_mod_candidate.stem
                    tag = "`[TOPOLOGY_DECLARED]`"
                    b_call = f"- {tag} `{url}` → [[{be_slug}]] (topology-declared; verify endpoint)"
                    b_by = f"- {tag} [[{caller_slug}]] (`{repo}/{caller_rel}:{caller_line}`) uses `{url}` (topology-declared)"
                    ck_c = grep_util.cksum_first_field(str(caller_mod))
                    ck_b = grep_util.cksum_first_field(str(be_mod_candidate))
                    calls_by_mod.setdefault(ck_c, []).append(b_call)
                    mod_paths[ck_c] = caller_mod
                    bys_by_mod.setdefault(ck_b, []).append(b_by)
                    mod_paths[ck_b] = be_mod_candidate
                    edges.append(f"{repo}\t{caller_rel}\t{callee_role}\t(topology)\t{url}\tTOPOLOGY_DECLARED")
                    edges_n += 1
                    edges_topology += 1
                if not callees:
                    unresolved.append((f"{repo}/{caller_rel}", url))
            else:
                unresolved.append((f"{repo}/{caller_rel}", url))

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

    # 4c — Shared type edges from forge_scan_shared_types.tsv
    edges_type = 0
    shared_types_tsv = scan_tmp / "forge_scan_shared_types.tsv"
    if shared_types_tsv.is_file() and shared_types_tsv.stat().st_size > 0:
        for row in shared_types_tsv.read_text(encoding="utf-8", errors="replace").splitlines():
            parts = row.split("\t")
            if len(parts) < 5:
                continue
            type_name, repo_a, rel_a, repo_b, rel_b = parts[0], parts[1], parts[2], parts[3], parts[4]
            mod_a = _resolve_module_file(brain_parent, repo_a, rel_a)
            mod_b = _resolve_module_file(brain_parent, repo_b, rel_b)
            # Also try class files: classes/{role}-{TypeName}.md
            if not mod_a:
                for cand in (brain_parent / repo_a / "classes" / f"{repo_a}-{type_name}.md",
                             brain_parent / "classes" / f"{repo_a}-{type_name}.md"):
                    if cand.is_file():
                        mod_a = cand
                        break
            if not mod_b:
                for cand in (brain_parent / repo_b / "classes" / f"{repo_b}-{type_name}.md",
                             brain_parent / "classes" / f"{repo_b}-{type_name}.md"):
                    if cand.is_file():
                        mod_b = cand
                        break
            if not mod_a or not mod_b or mod_a == mod_b:
                continue
            slug_a, slug_b = mod_a.stem, mod_b.stem
            tag = "`[SHARED_TYPE]`"
            _append_block(
                mod_a, BEGIN_OUT, END_OUT, "Shared types (cross-repo)",
                [f"- {tag} `{type_name}` shared with [[{slug_b}]] (`{repo_b}/{rel_b}`)"],
            )
            _append_block(
                mod_b, BEGIN_IN, END_IN, "Shared types (cross-repo)",
                [f"- {tag} `{type_name}` shared with [[{slug_a}]] (`{repo_a}/{rel_a}`)"],
            )
            edges.append(f"{repo_a}\t{rel_a}\t{repo_b}\t{rel_b}\t{type_name}\tSHARED_TYPE")
            edges_n += 1
            edges_type += 1

    # 4d — Event bus edges from forge_scan_event_bus.tsv + topology
    edges_event = 0
    event_bus_tsv = scan_tmp / "forge_scan_event_bus.tsv"
    if event_bus_tsv.is_file() and event_bus_tsv.stat().st_size > 0:
        pub_rows: list[tuple[str, str, str, str]] = []   # (role, rel, lineno, topic)
        sub_rows: list[tuple[str, str, str, str]] = []
        for row in event_bus_tsv.read_text(encoding="utf-8", errors="replace").splitlines():
            parts = row.split("\t")
            if len(parts) < 5:
                continue
            role, rel, lineno, kind = parts[0], parts[1], parts[2], parts[3]
            topic = parts[5] if len(parts) > 5 else ""
            if kind == "pub":
                pub_rows.append((role, rel, lineno, topic))
            elif kind == "sub":
                sub_rows.append((role, rel, lineno, topic))

        for pub_role, pub_rel, pub_lineno, pub_topic in pub_rows:
            # Find subscribers for the same topic
            matched_subs = [
                (sr, sr_rel, sr_lineno)
                for sr, sr_rel, sr_lineno, st in sub_rows
                if pub_topic and st == pub_topic
            ]
            # If topology available, also use topic_edges
            if topology and pub_topic:
                for sub_role in topology.subscribers_of(pub_topic):
                    if not any(r == sub_role for r, _, _ in matched_subs):
                        # Add topology-derived subscriber (no specific file known)
                        matched_subs.append((sub_role, "(topology)", ""))
            if not matched_subs:
                continue
            pub_mod = _resolve_module_file(brain_parent, pub_role, pub_rel)
            for sub_role, sub_rel, _sub_lineno in matched_subs:
                sub_mod = _resolve_module_file(brain_parent, sub_role, sub_rel) if sub_rel != "(topology)" else None
                if not pub_mod:
                    continue
                tag = "`[EVENT_BUS]`"
                topic_label = pub_topic or "(unknown)"
                if sub_mod and sub_mod != pub_mod:
                    sub_slug = sub_mod.stem
                    pub_slug = pub_mod.stem
                    _append_block(
                        pub_mod, BEGIN_OUT, END_OUT, "Event bus (publishes)",
                        [f"- {tag} `{topic_label}` consumed by [[{sub_slug}]] (`{sub_role}/{sub_rel}`)"],
                    )
                    _append_block(
                        sub_mod, BEGIN_IN, END_IN, "Event bus (subscribes)",
                        [f"- {tag} `{topic_label}` published by [[{pub_slug}]] (`{pub_role}/{pub_rel}:{pub_lineno}`)"],
                    )
                    edges.append(f"{pub_role}\t{pub_rel}\t{sub_role}\t{sub_rel}\t{topic_label}\tEVENT_BUS")
                    edges_n += 1
                    edges_event += 1
                elif not sub_mod:
                    # Topology-declared subscriber, no resolved file
                    pub_slug = pub_mod.stem
                    _append_block(
                        pub_mod, BEGIN_OUT, END_OUT, "Event bus (publishes)",
                        [f"- {tag} `{topic_label}` → {sub_role} (topology-declared; no module resolved)"],
                    )
                    edges.append(f"{pub_role}\t{pub_rel}\t{sub_role}\t(topology)\t{topic_label}\tEVENT_BUS_TOPOLOGY")
                    edges_n += 1
                    edges_event += 1

    out_md = brain_parent / "cross-repo-automap.md"
    if edges:
        automap_lines = sorted(set(edges))
        # Split by provenance for the header description
        prov_set = {e.split("\t")[-1] for e in automap_lines}
        out_md.write_text(
            "# Cross-repo automap (phase56)\n\n"
            "_Heuristic join (grep routes + OpenAPI paths + call sites + topology + shared types + event bus) "
            "— verify against runtime behavior._\n\n"
            "TSV columns: `caller_repo`, `caller_rel_path`, `route_repo`, `route_rel_path`, "
            "`url_or_type_or_topic`, `provenance`.\n\n"
            f"Provenance types present: {', '.join(sorted(prov_set))}\n\n"
            "```tsv\n"
            + "\n".join(automap_lines)
            + "\n```\n",
            encoding="utf-8",
            errors="replace",
        )

    # 4e — Unresolved edge report
    unresolved_unique = sorted(set(f"{loc}\t{url}" for loc, url in unresolved))
    if unresolved_unique:
        unresolved_section = (
            "\n\n## Unresolved Edges\n\n"
            "_Call sites where no matching route, type, or topology entry was found. "
            "Likely dynamic URLs, environment-variable base URLs, or cross-product calls not in product.md._\n\n"
            "```tsv\n"
            + "\n".join(unresolved_unique[:200])
            + ("\n... (truncated)" if len(unresolved_unique) > 200 else "")
            + "\n```\n"
        )
        cur = out_md.read_text(encoding="utf-8", errors="replace") if out_md.is_file() else "# Cross-repo automap (phase56)\n"
        out_md.write_text(cur.rstrip() + unresolved_section, encoding="utf-8", errors="replace")

    uniq: set[str] = set()
    for modf in brain_parent.rglob("*.md"):
        try:
            t = modf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if BEGIN_OUT in t or BEGIN_IN in t:
            uniq.add(str(modf.resolve()))
    touched = len(uniq)

    print(
        f"Phase 5.6: cross-repo edges={edges_n} "
        f"(http={edges_http} topology={edges_topology} type={edges_type} event={edges_event}) "
        f"unresolved={len(unresolved_unique)} module_files≈{touched}"
    )
    log.log_stat(
        f"phase=5.6 edges={edges_n} edges_http={edges_http} edges_topology={edges_topology} "
        f"edges_type={edges_type} edges_event={edges_event} "
        f"unresolved={len(unresolved_unique)} modules_with_out_block={touched}"
    )
    log.log_done(f"edges={edges_n} automap={'yes' if edges else 'no'} unresolved={len(unresolved_unique)}")

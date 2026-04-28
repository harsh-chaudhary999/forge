from __future__ import annotations

from collections import defaultdict
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
_LOW_SIGNAL_URL_PREFIXES = (
    "/dev",
    "/proc",
    "/tmp",
    "/home",
    "/dist",
    "/debug",
    "/validator",
)
_MOUNT_PREFIX_RE = re.compile(r"\b(?:app|router)\.use\(\s*['\"`](/[^'\"`]+)['\"`]")
_HTTP_METHOD_TOKENS = ("get(", "post(", "put(", "patch(", "delete(", "head(", "@get", "@post", "@put", "@patch", "@delete", "@head")
_ANN_ENDPOINT_REF_RE = re.compile(
    r"@(?:GET|POST|PUT|PATCH|DELETE|HTTP)\s*\(\s*([A-Za-z_][A-Za-z0-9_\.]{2,200})",
    re.IGNORECASE,
)
_URL_DYNAMIC_TOKEN_RE = re.compile(r"\$\{|{[^}]+}|:[A-Za-z_][A-Za-z0-9_]*")


def _is_candidate_api_path(url: str) -> bool:
    u = (url or "").strip()
    if not u.startswith("/") or len(u) < 3:
        return False
    if "${" in u or "{" in u and "}" in u:
        return False
    if any(u == p or u.startswith(p + "/") for p in _LOW_SIGNAL_URL_PREFIXES):
        return False
    if u.startswith("/api/") or u.startswith("/internal/") or u.startswith("/graphql"):
        return True
    if re.match(r"^/v[0-9]+(?:[./]|$)", u):
        return True
    return False


def _norm_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _tokenize_key(s: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", (s or "").lower()) if len(t) > 1}


def _best_alias_match(name: str, choices: list[str]) -> str | None:
    if not choices:
        return None
    n = _norm_key(name)
    t = _tokenize_key(name)
    # 1) exact normalized match
    for c in choices:
        if n and n == _norm_key(c):
            return c
    # 2) substring normalized match
    for c in choices:
        cn = _norm_key(c)
        if n and cn and (n in cn or cn in n):
            return c
    # 3) token overlap match
    best: tuple[int, int, str] | None = None
    for c in choices:
        tc = _tokenize_key(c)
        overlap = len(t & tc)
        if overlap <= 0:
            continue
        cand = (overlap, -len(c), c)
        if best is None or cand > best:
            best = cand
    return best[2] if best else None


def _join_route_path(prefix: str, path: str) -> str:
    pfx = (prefix or "").strip()
    p = (path or "").strip()
    if not pfx:
        return p
    if not p:
        return pfx
    if not pfx.startswith("/"):
        pfx = "/" + pfx
    if not p.startswith("/"):
        p = "/" + p
    if p == "/":
        return pfx
    if pfx.endswith("/"):
        pfx = pfx[:-1]
    return pfx + p


def _is_mount_only_route_line(raw_line: str) -> bool:
    low = raw_line.lower()
    if ".use(" not in low:
        return False
    return not any(tok in low for tok in _HTTP_METHOD_TOKENS)


def _load_product_roles(brain_parent: Path) -> dict[str, str]:
    """Best-effort parse of ../product.md project roles."""
    product_md = brain_parent.parent / "product.md"
    if not product_md.is_file():
        return {}
    try:
        lines = product_md.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    out: dict[str, str] = {}
    cur: str | None = None
    for ln in lines:
        m = re.match(r"^###\s+(.+?)\s*$", ln)
        if m:
            cur = m.group(1).strip()
            continue
        if cur is None:
            continue
        rm = re.match(r"^-+\s*role:\s*([A-Za-z0-9_-]+)\s*$", ln.strip(), re.IGNORECASE)
        if rm:
            out[cur] = rm.group(1).strip().lower()
            cur = None
    return out


def _extract_endpoint_symbol_refs(content: str) -> list[str]:
    refs: list[str] = []
    for m in _ANN_ENDPOINT_REF_RE.finditer(content):
        tok = (m.group(1) or "").strip()
        if tok:
            refs.append(tok)
    for m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){1,6})\b", content):
        tok = m.group(1)
        if any(k in tok.upper() for k in ("ENDPOINT", "API", "ROUTE", "PATH")):
            refs.append(tok)
    # de-dup preserve order
    out: list[str] = []
    for r in refs:
        if r not in out:
            out.append(r)
    return out


def _normalize_endpoint_value(v: str) -> str | None:
    s = (v or "").strip().strip('"').strip("'")
    if not s:
        return None
    if s.startswith("http://") or s.startswith("https://"):
        m = re.search(r"https?://[^/\s]+(/[^?#\s]+)", s)
        s = m.group(1) if m else ""
    if not s:
        return None
    if not s.startswith("/"):
        s = "/" + s
    s = s.split("?", 1)[0].split("#", 1)[0]
    return s if _is_candidate_api_path(s) else None


def _url_aliases(u: str) -> list[str]:
    """Generate conservative URL variants for gateway/base-path alias matching."""
    base = (u or "").split("?", 1)[0].split("#", 1)[0].strip()
    if not base.startswith("/"):
        return []
    out = [base]
    # /v2/x <-> /api/v2/x
    if base.startswith("/v"):
        out.append("/api" + base)
    if base.startswith("/api/"):
        tail = base[len("/api") :]
        if tail.startswith("/v"):
            out.append(tail)
    # normalize duplicate slashes
    dedup: list[str] = []
    for x in out:
        y = re.sub(r"/{2,}", "/", x)
        if y not in dedup:
            dedup.append(y)
        cy = _canonical_api_path(y)
        if cy not in dedup:
            dedup.append(cy)
    return dedup


def _canonical_api_path(path: str) -> str:
    """Project-level canonical path for connection joins/reporting."""
    p = (path or "").split("?", 1)[0].split("#", 1)[0].strip()
    if not p.startswith("/"):
        p = "/" + p
    p = re.sub(r"/{2,}", "/", p)
    if len(p) > 1 and p.endswith("/"):
        p = p[:-1]
    # Common gateway normalization: /api/vN/... and /vN/... represent same functional route.
    if p.startswith("/api/v"):
        p = p[len("/api") :]
    return p


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
        if _is_candidate_api_path(u):
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
    # Retrofit/relative API fragments often omit the leading slash: "v2/foo", "api/foo"
    for m in re.finditer(r"['\"`]((?:api|internal|graphql|v[0-9]+)[^'\"`?#)\s]*)['\"`]", content):
        frag = m.group(1).strip()
        if frag:
            _add("/" + frag.lstrip("/"))
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
        if matched_by == "mounted":
            return "GREP_MOUNTED"
        if matched_by == "substring":
            return "GREP_SUBSTRING"
        return "GREP_TEMPLATE"

    route_records: list[dict[str, object]] = []
    mount_prefixes_by_repo: dict[str, set[str]] = defaultdict(set)
    observed_route_repos: set[str] = set()
    for idx, ln in enumerate(routes_merged_lines):
        parsed = _parse_route_line(ln)
        if not parsed:
            continue
        be_repo, be_rel, be_lineno, raw_line = parsed
        observed_route_repos.add(be_repo)
        templates = openapi_routes.path_templates_in_route_line(raw_line)
        for m in _MOUNT_PREFIX_RE.finditer(raw_line):
            mount = m.group(1).strip()
            if mount and mount.startswith("/") and _is_candidate_api_path(mount):
                mount_prefixes_by_repo[be_repo].add(mount.rstrip("/") or "/")
        route_records.append(
            {
                "idx": idx,
                "repo": be_repo,
                "rel": be_rel,
                "lineno": be_lineno,
                "raw": raw_line,
                "templates": templates,
                "mount_only": _is_mount_only_route_line(raw_line),
            }
        )

    repo_to_topology: dict[str, str] = {}
    topology_to_repo: dict[str, str] = {}
    if topology is not None and getattr(topology, "services", None):
        service_names = list(topology.services.keys())
        for repo_name in sorted(observed_route_repos):
            m = _best_alias_match(repo_name, service_names)
            if m:
                repo_to_topology[repo_name] = m
        for svc in service_names:
            m = _best_alias_match(svc, sorted(observed_route_repos))
            if m:
                topology_to_repo[svc] = m

    endpoint_consts = scan_tmp / "forge_scan_endpoint_constants.tsv"
    endpoint_by_repo_symbol: dict[tuple[str, str], str] = {}
    endpoint_by_repo_leaf: dict[tuple[str, str], set[str]] = defaultdict(set)
    if endpoint_consts.is_file() and endpoint_consts.stat().st_size > 0:
        for row in endpoint_consts.read_text(encoding="utf-8", errors="replace").splitlines():
            parts = row.split("\t")
            if len(parts) < 5:
                continue
            repo_name, symbol, _rel, _lineno, value = parts[0], parts[1], parts[2], parts[3], parts[4]
            norm = _normalize_endpoint_value(value)
            if not norm:
                continue
            endpoint_by_repo_symbol[(repo_name, symbol)] = norm
            endpoint_by_repo_leaf[(repo_name, symbol.split(".")[-1])].add(norm)

    # Product role heuristics for URLs that do not resolve to concrete routes.
    product_roles = _load_product_roles(brain_parent)
    observed_all_repos = sorted({str(rec["repo"]) for rec in route_records})
    repo_role_kind: dict[str, str] = {}
    for repo_name in observed_all_repos:
        m = _best_alias_match(repo_name, list(product_roles.keys()))
        if m and m in product_roles:
            repo_role_kind[repo_name] = product_roles[m]
    backend_repos = [r for r, k in repo_role_kind.items() if k == "backend"]
    route_count_by_repo: dict[str, int] = defaultdict(int)
    for rec in route_records:
        route_count_by_repo[str(rec["repo"])] += 1
    route_templates_by_repo: dict[str, set[str]] = defaultdict(set)
    for rec in route_records:
        repo_n = str(rec["repo"])
        tpls = rec.get("templates")
        if isinstance(tpls, list):
            for t in tpls:
                if isinstance(t, str) and t.startswith("/"):
                    route_templates_by_repo[repo_n].add(t)

    def _pick_backend_repo_for_url(url: str) -> str | None:
        if not backend_repos:
            return None
        if len(backend_repos) == 1:
            return backend_repos[0]
        u = (url or "").strip()
        aliases = _url_aliases(u)
        major = "/" + u.strip("/").split("/", 1)[0] if u.startswith("/") else ""
        scores: list[tuple[int, int, str]] = []
        for r in backend_repos:
            s = 0
            if major and any(major in str(rec["raw"]) for rec in route_records if str(rec["repo"]) == r):
                s += 3
            if u.startswith("/api") and any("/api" in str(rec["raw"]) for rec in route_records if str(rec["repo"]) == r):
                s += 1
            if aliases:
                for a in aliases:
                    if any(a in tmpl or openapi_routes.path_template_matches(a, tmpl) for tmpl in route_templates_by_repo.get(r, set())):
                        s += 5
                        break
            s += min(route_count_by_repo.get(r, 0), 50) // 10
            scores.append((s, route_count_by_repo.get(r, 0), r))
        scores.sort(reverse=True)
        if not scores:
            return None
        if scores[0][0] > 0:
            return scores[0][2]
        # Last-resort: dominant backend by route inventory size.
        return scores[0][2]

    def hit_route(url: str, caller_repo: str, caller_method: str | None = None) -> tuple[str, str, str, str] | None:
        u = url.split("?", 1)[0].split("#", 1)[0]
        aliases = _url_aliases(u) or [u]
        tails = [a.lstrip("/") for a in aliases]
        same_repo_hit: tuple[str, str, str, str] | None = None
        for rec in route_records:
            idx = int(rec["idx"])
            ln = str(rec["raw"])
            be_repo = str(rec["repo"])
            be_rel = str(rec["rel"])
            be_lineno = str(rec["lineno"])
            # HTTP method filter (4a): if both sides have a declared method, they must match
            if caller_method:
                route_method = _http_method_from_route(ln)
                if route_method and route_method != caller_method:
                    continue
            matched_prov: str | None = None
            if any(a in ln for a in aliases):
                matched_prov = _provenance_for_line(idx, ln, "substring")
            elif any(t and ("/" + t) in ln for t in tails):
                matched_prov = _provenance_for_line(idx, ln, "substring")
            else:
                templates = rec.get("templates")
                if not isinstance(templates, list):
                    templates = []
                for tmpl in templates:
                    if any(openapi_routes.path_template_matches(a, tmpl) for a in aliases):
                        matched_prov = _provenance_for_line(idx, ln, "template")
                        break
                    if any(t and openapi_routes.path_template_matches("/" + t, tmpl) for t in tails):
                        matched_prov = _provenance_for_line(idx, ln, "template")
                        break
                # Mounted router fallback: combine app.use('/api/x') + router.get('/y') routes.
                if not matched_prov and not bool(rec.get("mount_only")) and templates and be_repo in mount_prefixes_by_repo:
                    for mount in mount_prefixes_by_repo[be_repo]:
                        for tmpl in templates:
                            merged = _join_route_path(mount, tmpl)
                            if not _is_candidate_api_path(merged):
                                continue
                            if any(a == merged for a in aliases) or any(t and ("/" + t) == merged for t in tails):
                                matched_prov = _provenance_for_line(idx, ln, "mounted")
                                break
                            if any(openapi_routes.path_template_matches(a, merged) for a in aliases):
                                matched_prov = _provenance_for_line(idx, ln, "mounted")
                                break
                        if matched_prov:
                            break
            if not matched_prov:
                continue
            cand = (be_repo, be_rel, be_lineno, matched_prov)
            if be_repo != caller_repo:
                return cand
            if same_repo_hit is None:
                same_repo_hit = cand
        return same_repo_hit

    calls_by_mod: dict[str, list[str]] = {}
    bys_by_mod: dict[str, list[str]] = {}
    mod_paths: dict[str, Path] = {}
    edges: list[str] = []
    api_rows: list[tuple[str, str, str, str, str, str, str]] = []
    route_usage_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    route_usage_callers: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    edges_n = 0
    edges_http = 0
    edges_topology = 0
    unresolved: list[tuple[str, str]] = []  # (caller_repo/caller_rel, url)
    unresolved_reason: dict[str, int] = defaultdict(int)
    linked_backend_routes: set[tuple[str, str, str]] = set()  # repo, rel, lineno

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
        candidate_urls = set(_urls_in_content(content))
        for ref in _extract_endpoint_symbol_refs(content):
            if (repo, ref) in endpoint_by_repo_symbol:
                candidate_urls.add(endpoint_by_repo_symbol[(repo, ref)])
            leaf = ref.split(".")[-1]
            vals = endpoint_by_repo_leaf.get((repo, leaf), set())
            if len(vals) == 1:
                candidate_urls.update(vals)

        for url in sorted(candidate_urls):
            hit = hit_route(url, repo, caller_method)
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
                api_rows.append(
                    (
                        repo,
                        caller_rel,
                        be_repo,
                        be_rel,
                        caller_method or "",
                        url,
                        provenance,
                    )
                )
                edges_n += 1
                edges_http += 1
                linked_backend_routes.add((be_repo, be_rel, be_lineno))
                rk = (be_repo, be_rel, be_lineno)
                route_usage_counts[rk] += 1
                route_usage_callers[rk].add(repo)
            elif topology is not None:
                # 4b: topology-assisted fallback for unresolved URLs
                caller_role = repo_to_topology.get(repo, repo)
                callees = topology.callees_of(caller_role)
                for callee_svc in callees:
                    callee_role = topology_to_repo.get(callee_svc, callee_svc)
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
                    api_rows.append(
                        (
                            repo,
                            caller_rel,
                            callee_role,
                            "(topology)",
                            caller_method or "",
                            url,
                            "TOPOLOGY_DECLARED",
                        )
                    )
                    edges_n += 1
                    edges_topology += 1
                if not callees:
                    unresolved.append((f"{repo}/{caller_rel}", url))
                    unresolved_reason["topology_no_callee"] += 1
            elif repo_role_kind.get(repo) in ("web", "mobile"):
                guessed_backend = _pick_backend_repo_for_url(url)
                if guessed_backend:
                    caller_mod = _resolve_module_file(brain_parent, repo, caller_rel)
                    be_mod_candidate = None
                    for candidate in brain_parent.rglob(f"modules/{guessed_backend}-*.md"):
                        be_mod_candidate = candidate
                        break
                    if not be_mod_candidate and (brain_parent / guessed_backend / "modules").is_dir():
                        for candidate in (brain_parent / guessed_backend / "modules").glob("*.md"):
                            be_mod_candidate = candidate
                            break
                    if caller_mod and be_mod_candidate and caller_mod != be_mod_candidate:
                        caller_slug = caller_mod.stem
                        be_slug = be_mod_candidate.stem
                        tag = "`[ROLE_HEURISTIC]`"
                        b_call = f"- {tag} `{url}` → [[{be_slug}]] (product-role heuristic; verify endpoint)"
                        b_by = f"- {tag} [[{caller_slug}]] (`{repo}/{caller_rel}:{caller_line}`) uses `{url}` (product-role heuristic)"
                        ck_c = grep_util.cksum_first_field(str(caller_mod))
                        ck_b = grep_util.cksum_first_field(str(be_mod_candidate))
                        calls_by_mod.setdefault(ck_c, []).append(b_call)
                        mod_paths[ck_c] = caller_mod
                        bys_by_mod.setdefault(ck_b, []).append(b_by)
                        mod_paths[ck_b] = be_mod_candidate
                        edges.append(f"{repo}\t{caller_rel}\t{guessed_backend}\t(topology)\t{url}\tROLE_HEURISTIC")
                        api_rows.append(
                            (
                                repo,
                                caller_rel,
                                guessed_backend,
                                "(topology)",
                                caller_method or "",
                                url,
                                "ROLE_HEURISTIC",
                            )
                        )
                        edges_n += 1
                        edges_topology += 1
                        continue
                unresolved.append((f"{repo}/{caller_rel}", url))
                unresolved_reason["heuristic_no_backend_target"] += 1
            else:
                unresolved.append((f"{repo}/{caller_rel}", url))
                if _URL_DYNAMIC_TOKEN_RE.search(url):
                    unresolved_reason["dynamic_or_templated_url"] += 1
                else:
                    unresolved_reason["no_route_match"] += 1

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
    api_md = brain_parent / "cross-repo-api-map.md"
    if edges:
        automap_lines = sorted(set(edges))
        # Split by provenance for the header description
        prov_set = {e.split("\t")[-1] for e in automap_lines}
        base_automap = (
            "# Cross-repo automap (phase56)\n\n"
            "_Heuristic join (grep routes + OpenAPI paths + call sites + topology + shared types + event bus) "
            "— verify against runtime behavior._\n\n"
            "TSV columns: `caller_repo`, `caller_rel_path`, `route_repo`, `route_rel_path`, "
            "`url_or_type_or_topic`, `provenance`.\n\n"
            f"Provenance types present: {', '.join(sorted(prov_set))}\n\n"
            "```tsv\n"
            + "\n".join(automap_lines)
            + "\n```\n"
        )
    else:
        base_automap = (
            "# Cross-repo automap (phase56)\n\n"
            "_No joined edges in this run._ Typical causes: empty `forge_scan_all_callsites.txt` "
            "(phase 5.1 grep/AST found no HTTP-shaped calls), empty `forge_scan_api_routes.txt` "
            "(phase 3.5 / OpenAPI), call paths that do not match any route line (dynamic URLs, "
            "different `/api` prefix), or HTTP method mismatch between caller and route.\n\n"
            "TSV columns: `caller_repo`, `caller_rel_path`, `route_repo`, `route_rel_path`, "
            "`url_or_type_or_topic`, `provenance`.\n\n"
            "```tsv\n```\n"
        )
    out_md.write_text(base_automap, encoding="utf-8", errors="replace")

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
        cur = out_md.read_text(encoding="utf-8", errors="replace")
        out_md.write_text(cur.rstrip() + unresolved_section, encoding="utf-8", errors="replace")

    # API-focused map: only HTTP URL matches where caller repo != route repo.
    api_cross = sorted(
        set(r for r in api_rows if r[0] != r[2]),
        key=lambda r: (r[0], r[2], r[5], r[1], r[3]),
    )
    api_lines = [
        "# Cross-repo API map (phase56)",
        "",
        "_HTTP API-level edges only (`/api`, `/internal`, `/graphql`, `/vN...`) where caller and route repos differ. "
        "Paths are matched with project-aware normalization aliases._",
        "",
        "TSV columns: `caller_repo`, `caller_rel_path`, `route_repo`, `route_rel_path`, `caller_method`, `url`, `provenance`.",
        "",
        f"Total API cross-repo edges: {len(api_cross)}",
        "",
        "```tsv",
    ]
    for row in api_cross:
        api_lines.append("\t".join(row))
    api_lines.extend(["```", ""])
    api_md.write_text("\n".join(api_lines), encoding="utf-8", errors="replace")

    # API coverage report (denominator + linked + gaps).
    cov_md = brain_parent / "cross-repo-api-coverage.md"
    catalog_md = brain_parent / "cross-repo-api-route-catalog.md"
    backend_route_keys: set[tuple[str, str, str]] = set()
    backend_route_counts: dict[str, int] = defaultdict(int)
    backend_route_catalog_rows: list[tuple[str, str, str, str, str, str, str, str]] = []
    for rec in route_records:
        rrepo = str(rec["repo"])
        if repo_role_kind.get(rrepo) != "backend":
            continue
        tpls = rec.get("templates")
        if not isinstance(tpls, list) or not tpls:
            continue
        key = (rrepo, str(rec["rel"]), str(rec["lineno"]))
        backend_route_keys.add(key)
        backend_route_counts[rrepo] += 1
        norm_tpls = sorted({_canonical_api_path(str(t)) for t in tpls if isinstance(t, str)})
        meth = _http_method_from_route(str(rec.get("raw", ""))) or "UNKNOWN"
        callers = sorted(route_usage_callers.get(key, set()))
        backend_route_catalog_rows.append(
            (
                rrepo,
                str(rec["rel"]),
                str(rec["lineno"]),
                meth,
                ",".join(str(t) for t in tpls),
                ",".join(norm_tpls),
                str(route_usage_counts.get(key, 0)),
                ",".join(callers),
            )
        )
    linked_backend = len([k for k in linked_backend_routes if k in backend_route_keys])
    total_backend = len(backend_route_keys)
    cov_pct = (100.0 * linked_backend / total_backend) if total_backend else 0.0
    cov_lines = [
        "# Cross-repo API coverage (phase56)",
        "",
        "## Totals",
        f"- Backend routes discovered: {total_backend}",
        f"- Backend routes linked by cross-repo API map: {linked_backend}",
        f"- Coverage: {cov_pct:.2f}%",
        "",
        "## Backend route inventory by repo",
    ]
    for repo_name, n in sorted(backend_route_counts.items(), key=lambda x: (-x[1], x[0])):
        cov_lines.append(f"- {repo_name}: {n}")
    cov_lines.extend(
        [
            "",
            "## Unresolved reasons (caller-side)",
        ]
    )
    if unresolved_reason:
        for reason, n in sorted(unresolved_reason.items(), key=lambda x: (-x[1], x[0])):
            cov_lines.append(f"- {reason}: {n}")
    else:
        cov_lines.append("- none")
    cov_lines.extend(
        [
            "",
            "## Notes",
            "- Coverage counts backend route records with path templates extracted from route inventory.",
            "- ROLE_HEURISTIC edges are caller-side mappings and are not treated as direct route-backed links.",
            "- For full backend route inventory and per-route usage counts, see `cross-repo-api-route-catalog.md`.",
            "",
        ]
    )
    cov_md.write_text("\n".join(cov_lines), encoding="utf-8", errors="replace")

    cat_lines = [
        "# Cross-repo API route catalog (phase56)",
        "",
        "_Route inventory (backend) with project-normalized paths and direct cross-repo usage counts._",
        "",
        "TSV columns: `route_repo`, `route_rel_path`, `route_lineno`, `route_method`, "
        "`raw_templates`, `normalized_templates`, `direct_usage_edges`, `caller_repos`.",
        "",
        f"Total backend routes in catalog: {len(backend_route_catalog_rows)}",
        "",
        "```tsv",
    ]
    for row in sorted(backend_route_catalog_rows, key=lambda r: (r[0], r[1], r[2])):
        cat_lines.append("\t".join(row))
    cat_lines.extend(["```", ""])
    catalog_md.write_text("\n".join(cat_lines), encoding="utf-8", errors="replace")

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

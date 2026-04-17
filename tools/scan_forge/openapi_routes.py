"""Discover OpenAPI / Swagger specs and emit ``forge_scan_api_routes``-compatible lines.

Phase 3.5 appends these **after** grep-based route extraction so phase56 can match
call-site URL paths to **documented** paths (including ``{param}`` templates).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import fs_util, log

MAX_OPENAPI_FILES = 40
MAX_BYTES = 4 * 1024 * 1024

# Filenames (case-insensitive) we treat as specs.
_OPENAPI_NAMES = frozenset(
    {
        "openapi.json",
        "openapi.yaml",
        "openapi.yml",
        "swagger.json",
        "swagger.yaml",
    },
)


def _should_skip_rel(rel: str) -> bool:
    if fs_util._rel_has_excluded_dir(rel):
        return True
    if "/node_modules/" in f"/{rel}/":
        return True
    if ".git/" in rel:
        return True
    return False


def discover_openapi_files(repo: Path) -> list[Path]:
    """Return sorted candidate spec paths (bounded).

    Matches common names plus filenames containing ``openapi`` or ``swagger`` with
    ``.json`` / ``.yaml`` / ``.yml`` extensions (deduplicated by resolved path).
    """
    repo = repo.resolve()
    submods = fs_util.git_submodule_displaypaths(repo)
    found_set: set[Path] = set()
    for p in repo.rglob("*"):
        if not p.is_file():
            continue
        try:
            rel = p.relative_to(repo).as_posix()
        except ValueError:
            continue
        if _should_skip_rel(rel):
            continue
        if fs_util.path_under_submodule(rel, submods):
            continue
        low = p.name.lower()
        if low in _OPENAPI_NAMES:
            found_set.add(p.resolve())
            continue
        if low.endswith((".openapi.json", ".openapi.yaml", ".openapi.yml")):
            found_set.add(p.resolve())
            continue
        if ("openapi" in low or "swagger" in low) and low.endswith((".json", ".yaml", ".yml")):
            found_set.add(p.resolve())
            continue
    out = sorted(found_set, key=lambda x: str(x))
    return out[:MAX_OPENAPI_FILES]


def _iter_operations_from_paths_obj(paths_obj: object) -> list[tuple[str, str]]:
    """OpenAPI 2/3: paths -> path -> method -> operation."""
    out: list[tuple[str, str]] = []
    if not isinstance(paths_obj, dict):
        return out
    for path_key, path_item in paths_obj.items():
        if not isinstance(path_key, str) or not path_key.startswith("/"):
            continue
        if not isinstance(path_item, dict):
            continue
        for method, _op in path_item.items():
            m = method.lower()
            if m not in ("get", "post", "put", "delete", "patch", "options", "head"):
                continue
            out.append((method.upper(), path_key))
    return out


def _parse_json_spec(text: str) -> list[tuple[str, str]]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, dict):
        return []
    # Swagger 2: may nest differently; still has top-level "paths"
    paths = data.get("paths")
    return _iter_operations_from_paths_obj(paths)


def _try_yaml_spec(text: str) -> list[tuple[str, str]]:
    try:
        import yaml  # type: ignore[import-untyped]

        data = yaml.safe_load(text)
    except Exception:
        return []
    if not isinstance(data, dict):
        return []
    return _iter_operations_from_paths_obj(data.get("paths"))


def _loose_yaml_paths(text: str) -> list[tuple[str, str]]:
    """If PyYAML fails, walk a ``paths:`` block: ``/path:`` then ``get:`` / ``post:`` …"""
    lines = text.splitlines()
    try:
        start = next(i for i, ln in enumerate(lines) if re.match(r"^\s*paths:\s*(#.*)?$", ln))
    except StopIteration:
        return []
    out: list[tuple[str, str]] = []
    i = start + 1
    paths_indent = len(lines[start]) - len(lines[start].lstrip())
    current_path: str | None = None
    while i < len(lines):
        ln = lines[i]
        if not ln.strip() or ln.lstrip().startswith("#"):
            i += 1
            continue
        ind = len(ln) - len(ln.lstrip())
        if ind <= paths_indent and ln.strip() and not ln.lstrip().startswith("/"):
            break
        pm = re.match(r"^\s*(/\S+):\s*$", ln)
        if pm:
            p = pm.group(1).strip()
            if p.startswith("/"):
                current_path = p
            i += 1
            continue
        mm = re.match(r"^\s*(get|post|put|delete|patch|options|head):\s", ln, re.I)
        if mm and current_path:
            out.append((mm.group(1).upper(), current_path))
        i += 1
    return out


def parse_openapi_file(path: Path) -> list[tuple[str, str]]:
    """Return list of (METHOD, path) from a JSON or YAML OpenAPI/Swagger file."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    if len(raw) > MAX_BYTES:
        log.log_warn(f"openapi_skip_too_large path={path} bytes={len(raw)}")
        return []
    low = path.name.lower()
    if raw.strip().startswith("{"):
        ops = _parse_json_spec(raw)
        if ops:
            return ops
    if low.endswith(".json"):
        ops = _parse_json_spec(raw)
        if ops:
            return ops
    ops = _try_yaml_spec(raw)
    if ops:
        return ops
    if low.endswith((".yaml", ".yml")):
        return _loose_yaml_paths(raw)
    return []


def path_template_matches(call_path: str, template: str) -> bool:
    """True if a concrete URL matches an OpenAPI path template (``{id}`` segments)."""
    call_path = call_path.split("?", 1)[0].split("#", 1)[0].strip()
    template = template.split("?", 1)[0].split("#", 1)[0].strip()
    if not call_path.startswith("/"):
        call_path = "/" + call_path
    if not template.startswith("/"):
        template = "/" + template
    c_parts = [p for p in call_path.split("/") if p != ""]
    t_parts = [p for p in template.split("/") if p != ""]
    if len(c_parts) < len(t_parts):
        return False
    for i, tp in enumerate(t_parts):
        if i >= len(c_parts):
            return False
        if tp.startswith("{") and tp.endswith("}"):
            continue
        if tp != c_parts[i]:
            return False
    return len(c_parts) == len(t_parts)


def path_templates_in_route_line(ln: str) -> list[str]:
    """Extract path strings from a route line (grep or OpenAPI synthetic)."""
    seen: list[str] = []
    for m in re.finditer(r"\b(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\s+(/[^\s]+)", ln, re.I):
        seen.append(m.group(2).split("?")[0])
    for m in re.finditer(r"['\"`](/[^'\"]+)['\"`]", ln):
        seen.append(m.group(1).split("?")[0])
    for m in re.finditer(r"/api[^\s'\"`?#)]+", ln):
        seen.append(m.group(0).split("?")[0])
    for m in re.finditer(r"/v[0-9]+[^\s'\"`?#)]+", ln):
        seen.append(m.group(0).split("?")[0])
    for m in re.finditer(r"https?://[^/\s'\"]+(/[^\s'\"`?#)]+)", ln):
        seen.append(m.group(1).split("?")[0])
    # de-dupe preserving order
    out: list[str] = []
    for s in seen:
        if s not in out:
            out.append(s)
    return out


def append_openapi_routes(repo: Path, slug: str, routes_path: Path) -> int:
    """Append synthetic route lines for every discovered OpenAPI operation. Returns count."""
    n = 0
    for spec in discover_openapi_files(repo):
        ops = parse_openapi_file(spec)
        if not ops:
            continue
        try:
            rel = spec.resolve().relative_to(repo.resolve()).as_posix()
        except ValueError:
            continue
        with routes_path.open("a", encoding="utf-8", errors="replace") as f:
            for method, pth in ops:
                # Line must contain METHOD and path so phase56 can match templates and display.
                content = f"{method} {pth} _forge_openapi"
                f.write(f"{slug}\t{rel}:0:{content}\n")
                n += 1
        log.log_stat(f"openapi_ops file={rel} count={len(ops)}")
    if n:
        log.log_step(f"phase=3.5 openapi_total_lines_appended={n}")
    return n

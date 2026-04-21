"""Append discovered HTTP paths from merged API route lines onto module scaffolds."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from . import modslug, openapi_routes

_MARKER = "## HTTP routes (auto)"


def enrich_modules_from_api_routes(
    brain_dir: Path,
    role: str,
    routes_path: Path,
) -> int:
    """Append route bullets to ``modules/{role}-*.md`` for this role. Returns modules updated."""
    if not routes_path.is_file():
        return 0
    brain_dir = brain_dir.resolve()
    mod_lines: dict[str, set[str]] = defaultdict(set)
    for line in routes_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or "\t" not in line:
            continue
        slug, rest = line.split("\t", 1)
        if slug != role:
            continue
        m = re.match(r"([^:]+):(\d+):(.*)", rest)
        if not m:
            continue
        rel, lineno, content = m.group(1), m.group(2), m.group(3)
        paths = openapi_routes.path_templates_in_route_line(content)
        if not paths:
            continue
        mod_bn = modslug.forge_mod_node_basename_from_rel(role, rel)
        for p in paths:
            mod_lines[mod_bn].add(f"- `{rel}:{lineno}` → `{p}`")

    touched = 0
    for mod_bn, bullets in sorted(mod_lines.items()):
        node = brain_dir / "modules" / f"{mod_bn}.md"
        if not node.is_file():
            continue
        body = node.read_text(encoding="utf-8", errors="replace")
        if _MARKER in body:
            continue
        block = "\n".join(
            [
                "",
                _MARKER,
                f"_From merged `forge_scan_api_routes.txt` for role `{role}` (grep + OpenAPI)._",
                *sorted(bullets),
                "",
            ],
        )
        node.write_text(body.rstrip() + block, encoding="utf-8", errors="replace")
        touched += 1
    return touched

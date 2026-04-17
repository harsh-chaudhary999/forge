"""Write ``graph.json`` — derived, regeneratable graph for agents (not canonical over markdown)."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import log, modslug


GRAPH_VERSION = 1


def _resolve_module_stem(brain: Path, repo: str, rel: str) -> str | None:
    slug = modslug.forge_mod_node_basename_from_rel(repo, rel)
    for candidate in (brain / repo / "modules" / f"{slug}.md", brain / "modules" / f"{slug}.md"):
        if candidate.is_file():
            return candidate.stem
    return None


def _module_nodes(brain: Path) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for md in sorted(brain.rglob("*.md")):
        rel = str(md).replace("\\", "/")
        if "/.forge_scan_" in rel or "/.obsidian/" in rel:
            continue
        if "/modules/" not in rel:
            continue
        stem = md.stem
        if stem in seen:
            continue
        seen.add(stem)
        try:
            rel_posix = md.relative_to(brain).as_posix()
        except ValueError:
            rel_posix = str(md)
        nodes.append({"id": stem, "type": "module", "path": rel_posix})
    return nodes


def _edges_from_automap(brain: Path) -> list[dict[str, Any]]:
    auto = brain / "cross-repo-automap.md"
    if not auto.is_file():
        return []
    text = auto.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"```tsv\n(.*?)```", text, re.S)
    if not m:
        return []
    edges: list[dict[str, Any]] = []
    for ln in m.group(1).strip().splitlines():
        if not ln.strip():
            continue
        parts = ln.split("\t")
        if len(parts) < 6:
            # Legacy rows without route_rel_path — skip (cannot resolve callee module)
            continue
        caller_repo, caller_rel, route_repo, route_rel, url, provenance = (
            parts[0],
            parts[1],
            parts[2],
            parts[3],
            parts[4],
            parts[5],
        )
        src = _resolve_module_stem(brain, caller_repo, caller_rel)
        tgt = _resolve_module_stem(brain, route_repo, route_rel)
        if not src or not tgt:
            continue
        edges.append(
            {
                "source": src,
                "target": tgt,
                "kind": "cross_repo_http",
                "url": url,
                "provenance": provenance,
                "caller_repo": caller_repo,
                "route_repo": route_repo,
            },
        )
    return edges


def write_graph_json(brain_codebase: Path) -> Path | None:
    """Merge module nodes + automap edges into ``graph.json`` under ``brain_codebase``."""
    os.environ["FORGE_SCAN_SCRIPT_ID"] = "graph_export"
    brain_codebase = brain_codebase.resolve()
    scan = brain_codebase / "SCAN.json"
    scan_meta: dict[str, Any] = {}
    if scan.is_file():
        try:
            scan_meta = json.loads(scan.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            scan_meta = {}

    nodes = _module_nodes(brain_codebase)
    edges = _edges_from_automap(brain_codebase)
    doc: dict[str, Any] = {
        "forge_scan_graph_version": GRAPH_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "brain_codebase": str(brain_codebase),
        "scan": {
            "scanned_at": scan_meta.get("scanned_at"),
            "repos": scan_meta.get("repos"),
        },
        "nodes": nodes,
        "edges": edges,
    }
    out = brain_codebase / "graph.json"
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", errors="replace")
    log.log_step(f"scan_graph_export written path={out} nodes={len(nodes)} edges={len(edges)}")
    return out

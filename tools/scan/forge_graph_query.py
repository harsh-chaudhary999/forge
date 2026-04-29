#!/usr/bin/env python3
"""Query ``graph.json`` produced by forge_scan (stdlib only).

Usage:
  python3 tools/forge_graph_query.py --graph brain/products/<slug>/codebase/graph.json summary
  python3 tools/forge_graph_query.py --graph <path> neighbors <node_id>
  python3 tools/forge_graph_query.py --graph <path> search <substring>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_WARNINGS_LIMIT = 20


def _load(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        raise RuntimeError(f"forge_graph_query: cannot read {path}: {e}") from e
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"forge_graph_query: invalid JSON in {path}: {e}") from e
    if not isinstance(doc, dict):
        raise RuntimeError("forge_graph_query: root must be a JSON object")
    return doc


def cmd_summary(doc: dict[str, Any], *, warnings_all: bool = False) -> int:
    ver = doc.get("forge_scan_graph_version", "?")
    nodes = doc.get("nodes") or []
    edges = doc.get("edges") or []
    warns = doc.get("warnings") or []
    if not isinstance(nodes, list):
        print("forge_graph_query: nodes must be a list", file=sys.stderr)
        return 2
    if not isinstance(edges, list):
        print("forge_graph_query: edges must be a list", file=sys.stderr)
        return 2
    if not isinstance(warns, list):
        print("forge_graph_query: warnings must be a list", file=sys.stderr)
        return 2
    print(f"forge_scan_graph_version={ver}")
    print(f"nodes={len(nodes)} edges={len(edges)} warnings={len(warns)}")
    if warns:
        shown = warns if warnings_all else warns[:_WARNINGS_LIMIT]
        for w in shown:
            print(f"  warning: {w}")
        if not warnings_all and len(warns) > _WARNINGS_LIMIT:
            print(f"  ... and {len(warns) - _WARNINGS_LIMIT} more warnings")
    return 0


def cmd_neighbors(doc: dict[str, Any], node_id: str, *, limit: int = 200) -> int:
    edges = doc.get("edges") or []
    if not isinstance(edges, list):
        print("forge_graph_query: edges must be a list", file=sys.stderr)
        return 2
    hits = 0
    max_hits = max(1, int(limit))
    for e in edges:
        if not isinstance(e, dict):
            continue
        src, tgt = e.get("source"), e.get("target")
        if src != node_id and tgt != node_id:
            continue
        hits += 1
        kind = e.get("kind", "")
        url = e.get("url", "")
        prov = e.get("provenance", "")
        print(f"{src} -> {tgt}  kind={kind}  url={url!r}  provenance={prov!r}")
        if hits >= max_hits:
            print(f"(output truncated at limit={max_hits})")
            break
    if hits == 0:
        print(f"(no edges touch node_id={node_id!r})")
    return 0


def cmd_search(
    doc: dict[str, Any], needle: str, *, limit: int = 200, ignore_case: bool = False
) -> int:
    nodes = doc.get("nodes") or []
    if not isinstance(nodes, list):
        print("forge_graph_query: nodes must be a list", file=sys.stderr)
        return 2
    hits = 0
    max_hits = max(1, int(limit))
    query = needle.casefold() if ignore_case else needle
    for n in nodes:
        if not isinstance(n, dict):
            continue
        path = str(n.get("path", ""))
        hay = path.casefold() if ignore_case else path
        if query not in hay:
            continue
        hits += 1
        print(f"{n.get('id')}\t{path}")
        if hits >= max_hits:
            print(f"(output truncated at limit={max_hits})")
            break
    if hits == 0:
        print(f"(no node path contains {needle!r})")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Query Forge scan graph.json (nodes + cross_repo_http edges).",
    )
    p.add_argument(
        "--graph",
        type=Path,
        required=True,
        help="Path to graph.json (e.g. brain/products/<slug>/codebase/graph.json)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    psu = sub.add_parser("summary", help="Print counts and warnings")
    psu.add_argument(
        "--warnings-all",
        action="store_true",
        help="Print all warnings instead of the default capped list.",
    )
    pn = sub.add_parser("neighbors", help="List edges where source or target matches node id")
    pn.add_argument("node_id", help="Module node id (same as graph node id / module stem)")
    pn.add_argument("--limit", type=int, default=200, help="Max edge rows to print (default: 200)")
    ps = sub.add_parser("search", help="List nodes whose path contains substring")
    ps.add_argument("needle", help="Substring to match in node path (case-sensitive)")
    ps.add_argument("--ignore-case", action="store_true", help="Case-insensitive match.")
    ps.add_argument("--limit", type=int, default=200, help="Max node rows to print (default: 200)")
    args = p.parse_args()
    try:
        doc = _load(args.graph.resolve())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.cmd == "summary":
        return cmd_summary(doc, warnings_all=bool(args.warnings_all))
    if args.cmd == "neighbors":
        return cmd_neighbors(doc, args.node_id, limit=args.limit)
    if args.cmd == "search":
        return cmd_search(doc, args.needle, limit=args.limit, ignore_case=bool(args.ignore_case))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

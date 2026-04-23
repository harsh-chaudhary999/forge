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


def _load(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"forge_graph_query: cannot read {path}: {e}", file=sys.stderr)
        sys.exit(2)
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"forge_graph_query: invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(doc, dict):
        print("forge_graph_query: root must be a JSON object", file=sys.stderr)
        sys.exit(2)
    return doc


def cmd_summary(doc: dict[str, Any]) -> int:
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
        for w in warns[:20]:
            print(f"  warning: {w}")
        if len(warns) > 20:
            print(f"  ... and {len(warns) - 20} more warnings")
    return 0


def cmd_neighbors(doc: dict[str, Any], node_id: str) -> int:
    edges = doc.get("edges") or []
    if not isinstance(edges, list):
        print("forge_graph_query: edges must be a list", file=sys.stderr)
        return 2
    hits = 0
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
    if hits == 0:
        print(f"(no edges touch node_id={node_id!r})")
    return 0


def cmd_search(doc: dict[str, Any], needle: str) -> int:
    nodes = doc.get("nodes") or []
    if not isinstance(nodes, list):
        print("forge_graph_query: nodes must be a list", file=sys.stderr)
        return 2
    hits = 0
    for n in nodes:
        if not isinstance(n, dict):
            continue
        path = str(n.get("path", ""))
        if needle not in path:
            continue
        hits += 1
        print(f"{n.get('id')}\t{path}")
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
    sub.add_parser("summary", help="Print counts and warnings")
    pn = sub.add_parser("neighbors", help="List edges where source or target matches node id")
    pn.add_argument("node_id", help="Module node id (same as graph node id / module stem)")
    ps = sub.add_parser("search", help="List nodes whose path contains substring")
    ps.add_argument("needle", help="Substring to match in node path (case-sensitive)")
    args = p.parse_args()
    doc = _load(args.graph.resolve())

    if args.cmd == "summary":
        return cmd_summary(doc)
    if args.cmd == "neighbors":
        return cmd_neighbors(doc, args.node_id)
    if args.cmd == "search":
        return cmd_search(doc, args.needle)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

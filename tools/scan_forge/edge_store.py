"""Materialize a queryable SQLite edge store from `graph.json`."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from . import log


def write_edge_store(brain_codebase: Path) -> Path | None:
    os.environ["FORGE_SCAN_SCRIPT_ID"] = "edge_store"
    brain = brain_codebase.resolve()
    graph = brain / "graph.json"
    if not graph.is_file():
        log.log_warn("edge_store skipped graph_json_missing")
        return None
    try:
        doc = json.loads(graph.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        log.log_warn("edge_store skipped graph_json_unreadable")
        return None
    nodes = doc.get("nodes") if isinstance(doc.get("nodes"), list) else []
    edges = doc.get("edges") if isinstance(doc.get("edges"), list) else []

    db = brain / "forge_scan_edges.sqlite"
    conn = sqlite3.connect(str(db))
    try:
        conn.executescript(
            """
            DROP TABLE IF EXISTS nodes;
            DROP TABLE IF EXISTS edges;
            CREATE TABLE nodes (
              id TEXT PRIMARY KEY,
              type TEXT,
              path TEXT
            );
            CREATE TABLE edges (
              source TEXT NOT NULL,
              target TEXT NOT NULL,
              kind TEXT,
              provenance TEXT,
              url TEXT,
              edge_kind TEXT,
              repo TEXT,
              line INTEGER,
              target_spec TEXT,
              payload_json TEXT
            );
            CREATE INDEX idx_edges_source ON edges(source);
            CREATE INDEX idx_edges_target ON edges(target);
            CREATE INDEX idx_edges_kind ON edges(kind);
            """
        )
        node_rows: list[tuple[str, str, str]] = []
        for n in nodes:
            if not isinstance(n, dict):
                continue
            nid = str(n.get("id", "")).strip()
            if not nid:
                continue
            node_rows.append((nid, str(n.get("type", "")), str(n.get("path", ""))))
        conn.executemany("INSERT OR REPLACE INTO nodes(id, type, path) VALUES (?, ?, ?)", node_rows)

        edge_rows: list[tuple[Any, ...]] = []
        for e in edges:
            if not isinstance(e, dict):
                continue
            src = str(e.get("source", "")).strip()
            tgt = str(e.get("target", "")).strip()
            if not src or not tgt:
                continue
            edge_rows.append(
                (
                    src,
                    tgt,
                    str(e.get("kind", "")),
                    str(e.get("provenance", "")),
                    str(e.get("url", "")),
                    str(e.get("edge_kind", "")),
                    str(e.get("repo", "")),
                    int(e.get("line", 0) or 0),
                    str(e.get("target_spec", "")),
                    json.dumps(e, sort_keys=True),
                )
            )
        conn.executemany(
            "INSERT INTO edges(source,target,kind,provenance,url,edge_kind,repo,line,target_spec,payload_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            edge_rows,
        )
        conn.commit()
    finally:
        conn.close()
    log.log_step(f"edge_store written path={db} nodes={len(node_rows)} edges={len(edge_rows)}")
    return db

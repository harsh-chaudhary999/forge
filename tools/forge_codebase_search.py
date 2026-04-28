#!/usr/bin/env python3
"""Local full-text search over scan artifacts (BM25 via SQLite FTS5)."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path


def _iter_docs(brain: Path) -> list[tuple[str, str]]:
    docs: list[tuple[str, str]] = []
    for rel in (
        "index.md",
        "SCAN_SUMMARY.md",
        "cross-repo-automap.md",
        "openapi-schema-digest.md",
    ):
        p = brain / rel
        if p.is_file():
            docs.append((rel, p.read_text(encoding="utf-8", errors="replace")))
    for p in sorted((brain / "modules").glob("*.md")) if (brain / "modules").is_dir() else []:
        rel = p.relative_to(brain).as_posix()
        docs.append((rel, p.read_text(encoding="utf-8", errors="replace")))
    sid = brain / "repo-docs" / "SEARCH_INDEX.md"
    if sid.is_file():
        docs.append((sid.relative_to(brain).as_posix(), sid.read_text(encoding="utf-8", errors="replace")))
    return docs


def _build_fts(docs: list[tuple[str, str]]) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE VIRTUAL TABLE docs USING fts5(path, content)")
    except sqlite3.OperationalError as exc:
        raise RuntimeError(
            "SQLite FTS5 is unavailable in this Python build (no such module: fts5)."
        ) from exc
    conn.executemany("INSERT INTO docs(path, content) VALUES (?, ?)", docs)
    return conn


def _search(conn: sqlite3.Connection, q: str, limit: int) -> list[dict[str, object]]:
    try:
        cur = conn.execute(
            "SELECT path, snippet(docs, 1, '[', ']', ' … ', 8) AS snippet, bm25(docs) AS score "
            "FROM docs WHERE docs MATCH ? ORDER BY score LIMIT ?",
            (q, max(1, int(limit))),
        )
    except sqlite3.OperationalError as exc:
        raise RuntimeError(
            f"Invalid FTS query {q!r} (or FTS5 unavailable): {exc}"
        ) from exc
    out: list[dict[str, object]] = []
    for path, snippet, score in cur.fetchall():
        out.append({"path": path, "score": score, "snippet": snippet})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Search Forge codebase artifacts with local BM25.")
    ap.add_argument("--brain-codebase", type=Path, required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument(
        "--json",
        action="store_true",
        help="Print JSON output (default: plain text).",
    )
    args = ap.parse_args(argv)

    brain = args.brain_codebase.expanduser().resolve()
    if not brain.is_dir():
        print(f"forge_codebase_search: not a directory: {brain}", file=sys.stderr)
        return 2

    docs = _iter_docs(brain)
    if not docs:
        print("forge_codebase_search: no searchable docs found", file=sys.stderr)
        return 1
    try:
        conn = _build_fts(docs)
        rows = _search(conn, args.query, args.limit)
    except RuntimeError as exc:
        print(f"forge_codebase_search: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"query": args.query, "hits": rows}, indent=2))
        return 0
    print(f"query={args.query!r} hits={len(rows)}")
    for r in rows:
        print(f"- {r['path']} score={r['score']}")
        print(f"  {r['snippet']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

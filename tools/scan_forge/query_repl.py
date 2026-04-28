"""Query `forge_scan_edges.sqlite` with SQL (read-only helper)."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run SQL queries against forge_scan_edges.sqlite.")
    ap.add_argument("--brain-codebase", type=Path, required=True)
    ap.add_argument(
        "--sql",
        default="SELECT kind, COUNT(*) AS n FROM edges GROUP BY kind ORDER BY n DESC",
        help="SQL query to execute (read-only expected).",
    )
    ap.add_argument("--limit", type=int, default=200, help="Max rows to print.")
    args = ap.parse_args(argv)

    brain = args.brain_codebase.expanduser().resolve()
    db = brain / "forge_scan_edges.sqlite"
    if not db.is_file():
        print(f"query_repl: sqlite file not found: {db}", file=sys.stderr)
        return 2
    conn = sqlite3.connect(str(db))
    try:
        cur = conn.execute(args.sql)
        cols = [d[0] for d in cur.description or []]
        print("\t".join(cols))
        shown = 0
        for row in cur:
            print("\t".join("" if v is None else str(v) for v in row))
            shown += 1
            if shown >= max(1, int(args.limit)):
                break
        if shown == 0:
            print("(no rows)")
    except sqlite3.Error as exc:
        print(f"query_repl: sqlite error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

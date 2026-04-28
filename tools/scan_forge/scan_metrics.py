"""Print scan coverage hints (artifact counts, SCAN.json, automap edges). Empirical only."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    root = _repo_root()
    ap = argparse.ArgumentParser(description="Forge scan metrics (optional run-dir + brain).")
    ap.add_argument("--brain-codebase", type=Path, required=True, help="e.g. ~/forge/brain/products/x/codebase")
    ap.add_argument("--run-dir", type=Path, default=None, help="If set, count forge_scan_*.txt (skip if --cleanup removed)")
    args = ap.parse_args(argv)

    brain = args.brain_codebase.expanduser()
    if not brain.is_absolute():
        brain = (root / brain).resolve()
    else:
        brain = brain.resolve()

    scan = brain / "SCAN.json"
    if scan.is_file():
        doc = json.loads(scan.read_text(encoding="utf-8"))
        print("SCAN.json")
        print(f"  scanned_at: {doc.get('scanned_at')}")
        print(f"  top-level source_files (aggregate): {doc.get('source_files')}")
        repos = doc.get("repos")
        if isinstance(repos, dict):
            print(f"  repos: {len(repos)} roles — {', '.join(sorted(repos.keys()))}")
            for r, ent in sorted(repos.items()):
                if isinstance(ent, dict):
                    print(f"    {r}: source_files={ent.get('source_files')} commit={ent.get('commit')}")
    else:
        print("SCAN.json: not found")

    auto = brain / "cross-repo-automap.md"
    if auto.is_file():
        t = auto.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"```tsv\n(.*?)```", t, re.S)
        if m:
            rows = [ln for ln in m.group(1).strip().splitlines() if ln.strip()]
            print(f"cross-repo-automap.md: {len(rows)} edge rows")
        else:
            print("cross-repo-automap.md: present (no tsv block parsed)")
    else:
        print("cross-repo-automap.md: not found")

    digest = brain / "openapi-schema-digest.md"
    print(f"openapi-schema-digest.md: {'present' if digest.is_file() else 'not found'}")

    summary = brain / "SCAN_SUMMARY.md"
    print(f"SCAN_SUMMARY.md: {'present' if summary.is_file() else 'not found'}")

    graph = brain / "graph.json"
    if graph.is_file():
        try:
            gdoc = json.loads(graph.read_text(encoding="utf-8"))
            nn = len(gdoc.get("nodes", []))
            ne = len(gdoc.get("edges", []))
            print(f"graph.json: present (nodes={nn} edges={ne})")
        except (OSError, json.JSONDecodeError):
            print("graph.json: present (unparseable)")
    else:
        print("graph.json: not found")
    es = brain / "forge_scan_edges.sqlite"
    print(f"forge_scan_edges.sqlite: {'present' if es.is_file() else 'not found'}")
    state = brain / ".forge_scan_file_state.json"
    print(f".forge_scan_file_state.json: {'present' if state.is_file() else 'not found'}")

    manifest = brain / ".forge_scan_manifest.json"
    print(f".forge_scan_manifest.json: {'present' if manifest.is_file() else 'not found'}")

    if args.run_dir is not None:
        rd = args.run_dir.expanduser()
        if not rd.is_absolute():
            rd = (root / rd).resolve()
        else:
            rd = rd.resolve()
        calls = rd / "forge_scan_all_callsites.txt"
        routes = rd / "forge_scan_api_routes.txt"
        if calls.is_file():
            n = len([x for x in calls.read_text().splitlines() if x.strip()])
            print(f"run_dir callsites: {n}")
        else:
            print("run_dir callsites: missing (use a kept run-dir)")
        if routes.is_file():
            n = len([x for x in routes.read_text().splitlines() if x.strip()])
            print(f"run_dir api_routes lines: {n}")
        else:
            print("run_dir api_routes: missing")
        run_json = rd / "run.json"
        if run_json.is_file():
            try:
                rj = json.loads(run_json.read_text(encoding="utf-8"))
                pt = rj.get("phase_timings_ms")
                if isinstance(pt, dict) and pt:
                    print("run.json phase_timings_ms (wall, last run):")
                    for k in sorted(pt.keys()):
                        print(f"  {k}: {pt[k]} ms")
                te = rj.get("total_elapsed_ms")
                if te is not None:
                    print(f"  total_elapsed_ms: {te} ms")
            except (OSError, json.JSONDecodeError):
                print("run.json: present (unparseable)")

    print("\nNote: Pass --run-dir from the scan CLI output before --cleanup, or use --keep-run-dir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

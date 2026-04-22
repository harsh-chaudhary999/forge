"""Write ``codebase/index.md`` after scan consolidation (orientation + wikilink hub)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import log


def write_codebase_index_md(brain_codebase: Path, repos: list[tuple[str, Path]]) -> Path:
    """
    Minimal but complete ``index.md`` so verify + skills have a stable entry note.

    Rich tables in the skill doc are aspirational; this file is **machine-written**
    and points humans/agents at ``SCAN_SUMMARY.md`` and ``modules/``.
    """
    os.environ["FORGE_SCAN_SCRIPT_ID"] = "codebase_index"
    brain_codebase = brain_codebase.resolve()
    scan_path = brain_codebase / "SCAN.json"
    scan: dict[str, Any] = {}
    if scan_path.is_file():
        try:
            scan = json.loads(scan_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            scan = {}

    scanned_at = scan.get("scanned_at", "unknown")
    src = scan.get("source_files", "n/a")
    tst = scan.get("test_files", "n/a")
    t1 = scan.get("tier1_hubs", "n/a")

    role_lines: list[str] = []
    rmap = scan.get("repos")
    if isinstance(rmap, dict):
        for role in sorted(rmap.keys()):
            ent = rmap[role]
            if isinstance(ent, dict):
                c = ent.get("commit", "?")
                sf = ent.get("source_files", "?")
                role_lines.append(f"- **`{role}`** — commit `{c}`, source_files={sf}")

    mod_dir = brain_codebase / "modules"
    mod_names: list[str] = []
    if mod_dir.is_dir():
        mod_names = sorted(p.stem for p in mod_dir.iterdir() if p.suffix.lower() == ".md")

    mod_table_rows: list[str] = []
    cap = 60
    for stem in mod_names[:cap]:
        mod_table_rows.append(f"| [[modules/{stem}]] | scaffold | _see note_ |")
    more = ""
    if len(mod_names) > cap:
        more = f"\n\n> _{len(mod_names) - cap} additional module notes omitted; list ``modules/``._\n"

    title = "Codebase (multi-repo)" if len(repos) > 1 else f"Codebase ({repos[0][0]})"

    lines = [
        f"# {title}",
        "",
        f"last-scanned: {scanned_at}",
        f"files: {src} source, {tst} test (aggregate from SCAN.json)",
        f"tier1_hubs (line count signal): {t1}",
        "",
        "## Repos in this run",
        "",
        "| Role | Path |",
        "|------|------|",
    ]
    for role, p in repos:
        lines.append(f"| `{role}` | `{p.resolve()}` |")
    if role_lines:
        lines.extend(["", "### Per-role commits (SCAN.json)", "", *role_lines])

    lines.extend(
        [
            "",
            "## Architecture style",
            "",
            "_Heuristic only — infer from repo layout and ``SCAN_SUMMARY.md``. Re-scan after major refactors._",
            "",
            "## Orientation (read next)",
            "",
            "- **[[SCAN_SUMMARY]]** — limitations, artifact map, diagnostics.",
            "- **`graph.json`** — module nodes + cross-repo HTTP edges (machine).",
            "- **`cross-repo-automap.md`** — when present, URL ↔ route joins.",
            "",
            "## Module map (first notes)",
            "",
            "| Module | Layer | Notes |",
            "|--------|-------|-------|",
            *mod_table_rows,
            more,
            "## Related",
            "",
            "- `SCAN.json` — counts and per-role metadata",
            "- `repo-docs/INDEX.md` — mirrored markdown from repos (if mirror ran)",
            "",
            f"_Auto-generated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}._",
            "",
        ],
    )

    out = brain_codebase / "index.md"
    out.write_text("\n".join(lines), encoding="utf-8", errors="replace")
    log.log_step(f"codebase_index written path={out} module_rows={len(mod_table_rows)}")
    return out

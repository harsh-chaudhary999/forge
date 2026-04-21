"""Write ``SCAN_SUMMARY.md`` — one-page orientation for humans and agents."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import log


def write_scan_summary(brain_codebase: Path, repos: list[tuple[str, Path]]) -> Path:
    os.environ["FORGE_SCAN_SCRIPT_ID"] = "scan_summary"
    brain_codebase = brain_codebase.resolve()
    scan_path = brain_codebase / "SCAN.json"
    scan: dict[str, Any] = {}
    if scan_path.is_file():
        try:
            scan = json.loads(scan_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            scan = {}

    mod_count = sum(1 for _ in brain_codebase.rglob("*.md") if "/modules/" in str(_).replace("\\", "/"))

    lines = [
        "# Scan summary",
        "",
        f"_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}. Read this before deep-diving the tree._",
        "",
        "## Freshness",
        "",
        f"- **SCAN.json `scanned_at`:** `{scan.get('scanned_at', 'n/a')}`",
        f"- **Module markdown files (approx):** {mod_count}",
        "",
        "## Repos in this run",
        "",
        "| Role | Path |",
        "|------|------|",
    ]
    for role, p in repos:
        lines.append(f"| `{role}` | `{p.resolve()}` |")
    lines.extend(
        [
            "",
            "## Aggregates (SCAN.json top-level)",
            "",
            f"- **source_files:** {scan.get('source_files', 'n/a')}",
            f"- **tier1_hubs:** {scan.get('tier1_hubs', 'n/a')}",
            f"- **tier2_hubs:** {scan.get('tier2_hubs', 'n/a')}",
            "",
            "### Per-role",
            "",
        ],
    )
    rmap = scan.get("repos")
    if isinstance(rmap, dict):
        for role in sorted(rmap.keys()):
            ent = rmap[role]
            if isinstance(ent, dict):
                lines.append(
                    f"- **`{role}`:** source_files={ent.get('source_files')} "
                    f"tier1={ent.get('tier1_hubs')} commit=`{ent.get('commit')}`",
                )
    else:
        lines.append("_No `repos` map in SCAN.json._")

    lines.extend(
        [
            "",
            "## Run directory layout (multi-repo)",
            "",
            "- Per-role phase1/3.5/4 inputs live under **`<run_dir>/_role/<role>/`** so inventories are not overwritten by the next repo.",
            "- Merged **`forge_scan_api_routes.txt`**, phase5 call-site files, and **`run.json`** stay at **`<run_dir>/`** root.",
            "",
            "## Machine-readable graph",
            "",
            "- **`graph.json`** — module nodes + `cross_repo_http` edges with `provenance` "
            "(regeneratable; markdown modules remain human source of truth). "
            "Check **`warnings`** for skipped legacy automap rows or unresolved module paths.",
            "",
            "## Cross-repo",
            "",
            "- **`cross-repo-automap.md`** — URL ↔ route joins with provenance tags "
            "(`OPENAPI`, `GREP_SUBSTRING`, `GREP_TEMPLATE`, `MANUAL_ALIAS`, `TOPOLOGY_DECLARED`, `SHARED_TYPE`, `EVENT_BUS`).",
            "- **`repo-docs/`** — verbatim Markdown + OpenAPI spec snapshots from scanned repos (`docs/`, ADRs, READMEs…). "
            "See `repo-docs/INDEX.md` (human table) and `repo-docs/index.json` (`content_sha256`, per-repo policy). "
            "Disable: `FORGE_REPO_DOCS_MIRROR=0`.",
            "",
            "## API / schema hints",
            "",
            "- **`openapi-schema-digest.md`** — shallow `components.schemas` names when OpenAPI exists.",
            "",
            "## Known limitations (honest)",
            "",
            "- Call sites and routes are **grep/heuristic**; dynamic URLs and unconventional frameworks may be missing.",
            "- OpenAPI discovery is **filename/pattern-based**; odd layouts need `route-aliases.tsv` or more patterns.",
            "- **Obsidian** resolves `[[modules/...]]` relative to the vault root — open `codebase/` as vault or use path links if links look broken from a higher root.",
            "- `graph.json` edges require **current** automap TSV (includes `route_rel_path` column).",
            "",
            "## Diagnostics",
            "",
            "- **`python3 -m scan_forge.scan_metrics --brain-codebase <this-dir>`** — quick artifact presence and SCAN.json summary.",
            "- **`--phase57-write-report`** on scan — `wikilink-orphan-report.md` for broken `[[...]]` targets.",
            "",
        ],
    )

    out = brain_codebase / "SCAN_SUMMARY.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", errors="replace")
    log.log_step(f"scan_summary written path={out}")
    return out

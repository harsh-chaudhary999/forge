# scan_forge

Python package implementing the Forge codebase scan pipeline. Invoked via `python3 tools/forge_scan.py` (or `PYTHONPATH=tools python3 -m scan_forge`). Do not import directly from outside `tools/`.

## Pipeline phases

| Phase | Module | What it does |
|-------|--------|--------------|
| 1 | `phase1.py` | File inventory — walks repo tree, classifies files by role, writes `forge_scan_inventory.txt` |
| 3.5 | `phase35.py` | Method/symbol extraction — stable IDs via `cksum` for diffing across runs |
| 4 | `phase4.py` | Brain stub writer — emits `index.md`, `modules/*.md`, `api-surface.md` under `--brain-codebase` |
| 5 | `phase5.py` | Call-site grep — HTTP-shaped calls across all supported languages |
| 5.1 | `ast_http_calls.py` | AST-level HTTP call extraction via Tree-sitter (optional; falls back to grep when wheels absent) |
| 56 | `phase56.py` | Route→module enrichment — merges OpenAPI / route-table hits into `forge_scan_all_callsites.txt` |
| 57 | `phase57.py` | Graph export — writes `graph.json` for `forge_graph_query.py` |

## Key modules

| Module | Role |
|--------|------|
| `cli.py` | Argparse entry point; orchestrates phase order and retries |
| `scan_paths.py` | All path constants (`run_dir`, `_role/`, brain output dirs) |
| `verify_brain_codebase.py` | Post-scan validation (required files, non-empty `modules/` when `source_files > 0`) |
| `verify_smoke.py` | Smoke test — generates fixture data at runtime and runs full CLI |
| `scan_graph_export.py` | Builds `graph.json` from inventory + call-site data |
| `openapi_routes.py` | Parses OpenAPI/Swagger specs to extract route table |
| `stub_writers.py` | Writes brain stub files (`index.md`, `modules/*.md`, `api-surface.md`) |

## Environment variables

| Variable | Effect |
|----------|--------|
| `FORGE_SCAN_SKIP_VERIFY=1` | Skip post-scan verify step (emergency triage only) |
| `FORGE_SCAN_AST=0` | Disable Tree-sitter AST pass even when wheels are installed |

## Adding a language to AST extraction

1. Add a grammar entry in `ast_http_calls.py` (`LANG_CONFIGS`).
2. Add the `tree-sitter-<lang>` wheel to `requirements.txt`.
3. Run `PYTHONPATH=tools python3 tools/scan_forge/verify_smoke.py` to confirm no regressions.

## Running the smoke test

```bash
PYTHONPATH=tools python3 tools/scan_forge/verify_smoke.py
```

A clean run prints `SMOKE OK` and exits 0. If it exits non-zero, check the temp run dir printed to stderr — `forge_scan_*.txt` files show which phase failed.

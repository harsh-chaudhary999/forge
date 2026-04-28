# Scan hardening gates

This document defines ship gates for the hardening tracks.

## Precision track gate

- A no-change incremental run reports `incremental.skipped_scan_phases=true`.
- `total_elapsed_ms` for no-change incremental is lower than a full run on the same fixture.
- `run.json` includes `incremental.phase5_56_mode` and `incremental.phase5_56_reason`.

## Tests track gate

- Smoke coverage includes:
  - non-git fallback,
  - rename/delete-heavy diff,
  - mixed staged + unstaged + untracked changes.
- `verify_smoke.py` validates `graph.json` and `forge_scan_edges.sqlite` are generated.

## Import-depth gate

- Import TSV provenance uses `AST_STRONG`, `AST_WEAK`, `HEURISTIC`.
- `graph.json` imports include only confidence-qualified import edges.
- Local relative imports include resolved target path in TSV output.

## Benchmark track gate

- `tools/scan_bench.py` emits JSON and markdown artifacts.
- Benchmark step runs in CI as non-blocking.
- Gate booleans are explicit in benchmark JSON under `gates`.

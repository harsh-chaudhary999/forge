# Forge tools

Small, repo-local utilities shipped with Forge. The main maintained package here is **`scan_forge/`** — the scan-codebase pipeline (inventory → brain stubs → cross-repo heuristics).

## Layout

| Path | Purpose |
|------|---------|
| [`scan_forge/`](scan_forge/) | Python package: phases 1, 3.5, 4, 5, 56, 57, CLI, smoke fixtures |
| [`forge_scan.py`](forge_scan.py) | CLI entry: prepends `tools/` on `sys.path` and runs `scan_forge.cli` |

There is **no** separate throwaway “temp” tree under `tools/`; scan run artifacts are always created in a directory you pass as **`--run-dir`** (or a process temp dir), not committed here.

## Running the scan pipeline

From the **Forge repo root** (parent of `tools/`):

```bash
python3 tools/forge_scan.py --help
```

Equivalent manual invocation:

```bash
PYTHONPATH=tools python3 -m scan_forge --help
```

Smoke test (fixtures + full CLI):

```bash
PYTHONPATH=tools python3 tools/scan_forge/verify_smoke.py
```

Install optional scan deps (PyYAML + **Tree-sitter grammars** for phase 5.1 AST: HTTP-shaped calls across JS/TS, Python, Go, Rust, Java, Kotlin, Ruby, C#, PHP, Swift, Lua, Zig, PowerShell, Elixir, ObjC, Julia, Verilog, C/C++, Scala — written to `forge_scan_ast_http_calls.txt` and merged into `forge_scan_all_callsites.txt` for phase56):

```bash
pip install -r tools/scan_forge/requirements.txt
```

Without those wheels, phase 5.1 stays grep-only. Set `FORGE_SCAN_AST=0` to force-disable the AST pass when installed.

Background on Tree-sitter (incremental parsing, language bindings, upstream parsers): [tree-sitter.github.io](https://tree-sitter.github.io/tree-sitter/).

## Requirements

- Python 3.9+
- GNU **grep** and **cksum** on `PATH` (inventory and stable method ids)

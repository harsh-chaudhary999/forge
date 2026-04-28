# Forge tools

Small, repo-local utilities shipped with Forge. The main maintained package here is **`scan_forge/`** — the scan-codebase pipeline (inventory → brain stubs → cross-repo heuristics).

## Layout

| Path | Purpose |
|------|---------|
| [`scan_forge/`](scan_forge/) | Python package: phases 1, 3.5, 4, 5, 56, 57, CLI; smoke data is generated at runtime by `verify_smoke.py` — see **[`scan_forge/README.md`](scan_forge/README.md)** for phase map and module guide |
| [`verify_scan_outputs.py`](verify_scan_outputs.py) | Standalone check: same rules as `scan_forge.verify_brain_codebase` (required files + non-empty `modules/` when `source_files` > 0). **`forge_scan.py` runs verify automatically** (3 retries) after writing `index.md`; set **`FORGE_SCAN_SKIP_VERIFY=1`** only for emergency triage |
| [`forge_scan.py`](forge_scan.py) | CLI entry: prepends `tools/` on `sys.path` and runs `scan_forge.cli` |
| `scan_forge/scan_state.py` | Incremental scan state (changed-path report + `.forge_scan_file_state.json` with per-role heads and tracked blob SHAs) |
| [`verify_forge_task.py`](verify_forge_task.py) | **Machine gate:** eval YAML (**`--validate-eval-yaml`** — PyYAML if installed else [`eval_yaml_stdlib.py`](eval_yaml_stdlib.py)), `conductor.log` order, QA/design gates, optional **`--check-prd-sections`**, **`--require-conductor-timestamps`**, **`--strict-single-task-brain`**, **`--strict-tech-plans`**, **`--strict-0c-inventory`**, shared-spec + phase-ledger flags, gates dir auto-fallback ([doc](../docs/forge-task-verification.md)) |
| [`verify_tech_plans.py`](verify_tech_plans.py) | **Tech plan structure:** canonical Section **1b** headings, **`### 1b.2a` after** wire maps, **`REVIEW_PASS`** requires FORGE-GATE HTML comments — standalone or via **`verify_forge_task.py --strict-tech-plans`**; add **`--strict-0c-inventory`** for GAP + multi-source citation rails |
| [`forge_drift_check.py`](forge_drift_check.py) | **Drift:** `prd-locked.md` **Success Criteria** bullets vs `eval/*` + QA CSV text (**stdlib**; optional **`--strict`**) |
| [`eval_yaml_stdlib.py`](eval_yaml_stdlib.py) | Best-effort eval scenario shape without PyYAML (imported by verify script) |
| [`phase_ledger.py`](phase_ledger.py) / [`append_phase_ledger.py`](append_phase_ledger.py) | Append-only **`phase-ledger.jsonl`** with per-file **SHA256** (editor-agnostic) |
| [`shared_spec_policy.py`](shared_spec_policy.py) + [`shared_spec_checklist.json`](shared_spec_checklist.json) | **`verify_forge_task.py --check-shared-spec`** |
| [`lint_skill_allowed_tools.py`](lint_skill_allowed_tools.py) | CI: rigid **`allowed-tools`**; **`--write-policy`** → [`skill-tool-policy.json`](skill-tool-policy.json) for hosts that can consume it |
| [`forge_graph_query.py`](forge_graph_query.py) | **Ad-hoc queries** on **`graph.json`** from a completed scan: `summary`, `neighbors <node_id>`, `search <substring>` — stdlib only |
| [`forge_codebase_search.py`](forge_codebase_search.py) | Local BM25 search (SQLite FTS5) across scan artifacts (`modules/`, `index.md`, `SCAN_SUMMARY.md`, automap, doc index) |
| `scan_forge/query_repl.py` | SQL helper for `forge_scan_edges.sqlite` (generated from `graph.json`) |
| [`forge_adjacency_scan.py`](forge_adjacency_scan.py) | **Optional** pre-Council scan — **`docs/adjacency-and-cohorts.md`**. Appends `discovery-adjacency.md` using **`rg`** + org patterns (`adjacency-seed-patterns.txt` or `--patterns`). |
| [`check_frozen_spec.py`](check_frozen_spec.py) | **Pre-freeze lint:** fails if `TBD` or `TODO` appears outside code fences in `shared-dev-spec.md` |
| [`brain_restore_deleted.py`](brain_restore_deleted.py) | **Recovery utility:** restores brain files deleted from git history (`--help` for usage) |

There is **no** separate throwaway “temp” tree under `tools/`; scan run artifacts are always created in a directory you pass as **`--run-dir`** (or a process temp dir), not committed here.

## Verifying a brain task (CI / pre-merge)

From the **Forge repo root**:

```bash
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain
# stricter (PyYAML): pip install -r tools/requirements-verify.txt
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain --require-log --validate-eval-yaml
```

See **[`docs/forge-task-verification.md`](../docs/forge-task-verification.md)** and **[`.github/workflows/forge-brain-guard.yml`](../.github/workflows/forge-brain-guard.yml)** (template for your brain repo).

## Verifying tech plan structure (standalone)

```bash
python3 tools/verify_tech_plans.py --help

# Check all tech plans for a task (pass the tech-plans/ directory):
python3 tools/verify_tech_plans.py ~/forge/brain/prds/<task-id>/tech-plans/

# Or via verify_forge_task.py (combines eval + tech-plan checks in one pass):
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain --strict-tech-plans
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain --strict-0c-inventory
```

Checks performed: canonical Section 1b headings present, `### 1b.2a` placed **after** wire-map sections (Section 1b.5 / `#### 1b.5b`), and any `Tech plan status: REVIEW_PASS` file contains both `<!-- FORGE-GATE:… -->` HTML comment markers in Section 1c. With **`--strict-0c-inventory`**, **`REVIEW_PASS`** plans also fail on inventory rows whose last column is **`GAP`**, and on **prd-locked-only** inventories when Confluence mirror, **touchpoints/*.md**, or populated **QA CSV** exist (substring rules — see [doc](../docs/forge-task-verification.md)).

## Verifying merged plugin `skills/` layout (all IDEs that copy the tree)

After any install that copies `skills/<name>/SKILL.md` into a plugin root (Cursor, Claude Code cache, OpenCode fallback copy), run:

```bash
bash scripts/verify-forge-plugin-install.sh --all
# or one platform:
bash scripts/verify-forge-plugin-install.sh --platform cursor
```

Fails on nested `skills/skills/` or stale `intake-interrogate` (missing **Q9 / design** markers) — see **[`docs/platforms/plugin-skill-layout.md`](../docs/platforms/plugin-skill-layout.md)** and **[`docs/platforms/cursor.md`](../docs/platforms/cursor.md)** (Troubleshooting).

## Running the scan pipeline

From the **Forge repo root** (parent of `tools/`):

```bash
python3 tools/forge_scan.py --help
```

Incremental mode (same behavior via `FORGE_SCAN_INCREMENTAL=1`):

```bash
python3 tools/forge_scan.py --incremental --brain-codebase ... --repos role:/abs/path ...
```

Equivalent manual invocation:

```bash
PYTHONPATH=tools python3 -m scan_forge --help
```

Smoke test (fixtures + full CLI):

```bash
PYTHONPATH=tools python3 tools/scan_forge/verify_smoke.py
```

After a successful CLI run, `run.json` should show **`"status": "ok"`** and **`verify_scan_outputs.exit_code": 0`**. If **`status`** is **`verify_failed`**, the brain tree is incomplete — fix and re-scan; **`--cleanup` was skipped** so **`run_dir`** still has `forge_scan_*.txt` for debugging.

Install optional scan deps (PyYAML + **Tree-sitter grammars** for phase 5.1 AST: HTTP-shaped calls across JS/TS, Python, Go, Rust, Java, Kotlin, Ruby, C#, PHP, Swift, Lua, Zig, PowerShell, Elixir, ObjC, Julia, Verilog, C/C++, Scala — written to `forge_scan_ast_http_calls.txt` and merged into `forge_scan_all_callsites.txt` for phase56):

```bash
pip install -r tools/scan_forge/requirements.txt
```

Without those wheels, phase 5.1 stays grep-only. Set `FORGE_SCAN_AST=0` to force-disable the AST pass when installed.

Background on Tree-sitter (incremental parsing, language bindings, upstream parsers): [tree-sitter.github.io](https://tree-sitter.github.io/tree-sitter/).

## Requirements

- Python 3.9+
- GNU **grep** and **cksum** on `PATH` (inventory and stable method ids)

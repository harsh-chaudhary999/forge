# Forge tools

Small, repo-local utilities shipped with Forge. The main maintained package here is **`scan_forge/`** — the scan-codebase pipeline (inventory → brain stubs → cross-repo heuristics).

## Directory layout

| Directory | Purpose |
|-----------|---------|
| **[`scan_forge/`](scan_forge/)** | Python package: phases 1, 3.5, 4, 5, 56, 57, CLI; smoke data is generated at runtime by `verify_smoke.py` — see **[`scan_forge/README.md`](scan_forge/README.md)** for phase map and module guide. |
| **[`verify/`](verify/)** | Machine verification: task/brain gates (`verify_forge_task.py`, `verify_tech_plans.py`, `verify_scan_outputs.py`, eval YAML helpers, drift, shared-spec, phase ledger, `requirements-verify.txt`, unit tests). |
| **[`scan/`](scan/)** | Scan **CLI and helpers** (not the `scan_forge` package): `forge_scan.py`, `forge_codebase_search.py`, `forge_graph_query.py`, `forge_adjacency_scan.py`, `scan_bench.py`, `adjacency-seed-patterns.txt`. |
| **[`dev/`](dev/)** | Maintainer tooling: `lint_skill_allowed_tools.py`, `skill-tool-policy.json`, tests. |
| **[`ops/`](ops/)** | Operator utilities: `forge_evidence_bundle.py`, `brain_restore_deleted.py`. |
| **[`js/`](js/)** | Node regression tests (e.g. `test-prompt-submit-gates.cjs`). |

**Stable CLI paths:** Thin **`tools/<name>.py`** shims at the repo `tools/` root forward to the grouped implementation (so **`python3 tools/verify_forge_task.py`** and docs stay unchanged). Prefer shims for everyday use; open **`verify/`**, **`scan/`**, etc. when editing source.

## Tool reference

| Entry (shim → impl) | Purpose |
|----------------------|---------|
| [`forge_scan.py`](forge_scan.py) → [`scan/forge_scan.py`](scan/forge_scan.py) | CLI entry: prepends `tools/` on `sys.path` and runs `scan_forge.cli` |
| [`verify_scan_outputs.py`](verify_scan_outputs.py) → [`verify/verify_scan_outputs.py`](verify/verify_scan_outputs.py) | Standalone check: same rules as `scan_forge.verify_brain_codebase`. **`forge_scan.py` runs verify automatically** (3 retries) after writing `index.md`; set **`FORGE_SCAN_SKIP_VERIFY=1`** only for emergency triage |
| [`verify_forge_task.py`](verify_forge_task.py) → [`verify/verify_forge_task.py`](verify/verify_forge_task.py) | **Machine gate:** eval YAML (`--validate-eval-yaml`), `qa/semantic-automation.csv` coherence, `conductor.log` order, QA/design gates, optional tech-plan / shared-spec / phase-ledger flags — see **[`docs/forge-task-verification.md`](../docs/forge-task-verification.md)** |
| [`run_semantic_csv_eval.py`](run_semantic_csv_eval.py) → [`verify/run_semantic_csv_eval.py`](verify/run_semantic_csv_eval.py) | Validates **`qa/semantic-automation.csv`**, writes **`semantic-eval-manifest.json`** — **[`docs/semantic-eval-csv.md`](../docs/semantic-eval-csv.md)** |
| [`verify_tech_plans.py`](verify_tech_plans.py) → [`verify/verify_tech_plans.py`](verify/verify_tech_plans.py) | **Tech plan structure:** canonical Section **1b** headings, **`### 1b.2a` after** wire maps, **`REVIEW_PASS`** FORGE-GATE comments |
| [`forge_drift_check.py`](forge_drift_check.py) → [`verify/forge_drift_check.py`](verify/forge_drift_check.py) | **Drift:** `prd-locked.md` **Success Criteria** vs `eval/*` + QA CSV (**stdlib**; optional **`--strict`**) |
| [`verify/eval_yaml_stdlib.py`](verify/eval_yaml_stdlib.py) | Best-effort eval scenario shape without PyYAML (imported by `verify_forge_task`; no top-level shim) |
| [`append_phase_ledger.py`](append_phase_ledger.py) → [`verify/append_phase_ledger.py`](verify/append_phase_ledger.py), [`verify/phase_ledger.py`](verify/phase_ledger.py) | Append-only **`phase-ledger.jsonl`** with per-file **SHA256** |
| [`verify/shared_spec_policy.py`](verify/shared_spec_policy.py) + [`verify/shared_spec_checklist.json`](verify/shared_spec_checklist.json) | **`verify_forge_task.py --check-shared-spec`** |
| [`lint_skill_allowed_tools.py`](lint_skill_allowed_tools.py) → [`dev/lint_skill_allowed_tools.py`](dev/lint_skill_allowed_tools.py) | CI: rigid **`allowed-tools`**; **`--write-policy`** → [`dev/skill-tool-policy.json`](dev/skill-tool-policy.json) (**`pre-tool-use.cjs`** loads `tools/dev/skill-tool-policy.json`, with legacy fallback `tools/skill-tool-policy.json`) |
| [`forge_graph_query.py`](forge_graph_query.py) → [`scan/forge_graph_query.py`](scan/forge_graph_query.py) | **Ad-hoc queries** on **`graph.json`**: `summary`, `neighbors`, `search` — stdlib only |
| [`forge_codebase_search.py`](forge_codebase_search.py) → [`scan/forge_codebase_search.py`](scan/forge_codebase_search.py) | Local BM25 search (SQLite FTS5) across scan artifacts |
| `scan_forge/query_repl.py` | SQL helper for `forge_scan_edges.sqlite` (generated from `graph.json`) |
| [`scan_bench.py`](scan_bench.py) → [`scan/scan_bench.py`](scan/scan_bench.py) | Synthetic benchmark harness (full vs incremental, gate booleans) |
| `scan_forge/HARDENING_GATES.md` | Ship gates for precision, smoke coverage, import-depth confidence, and benchmark reporting |
| [`forge_adjacency_scan.py`](forge_adjacency_scan.py) → [`scan/forge_adjacency_scan.py`](scan/forge_adjacency_scan.py) | **Optional** pre-Council — **`docs/adjacency-and-cohorts.md`**. **`adjacency-seed-patterns.txt`** lives next to the script under **`scan/`**. |
| [`check_frozen_spec.py`](check_frozen_spec.py) → [`verify/check_frozen_spec.py`](verify/check_frozen_spec.py) | **Pre-freeze lint:** `TBD` / `TODO` outside fences in `shared-dev-spec.md` |
| [`brain_restore_deleted.py`](brain_restore_deleted.py) → [`ops/brain_restore_deleted.py`](ops/brain_restore_deleted.py) | **Recovery:** restore brain files deleted from disk but still in the git index |

There is **no** separate throwaway “temp” tree under `tools/`; scan run artifacts are always created in a directory you pass as **`--run-dir`** (or a process temp dir), not committed here.

## Verifying a brain task (CI / pre-merge)

From the **Forge repo root**:

```bash
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain
# stricter (PyYAML): pip install -r tools/verify/requirements-verify.txt
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain --require-log --validate-eval-yaml
```

See **[`docs/forge-task-verification.md`](../docs/forge-task-verification.md)** and **[`.github/workflows/forge-brain-guard.yml`](../.github/workflows/forge-brain-guard.yml)** (template for your brain repo).

## Verifying tech plan structure (standalone)

```bash
python3 tools/verify_tech_plans.py --help

python3 tools/verify_tech_plans.py ~/forge/brain/prds/<task-id>/tech-plans/

python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain --strict-tech-plans
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain --strict-0c-inventory
```

Checks performed: canonical Section 1b headings present, `### 1b.2a` placed **after** wire-map sections, and any `Tech plan status: REVIEW_PASS` file contains both `<!-- FORGE-GATE:… -->` HTML comment markers in Section 1c. With **`--strict-0c-inventory`**, **`REVIEW_PASS`** plans also fail on inventory **GAP** rows and **prd-locked-only** inventories when Confluence mirror, **touchpoints/**, or populated **QA CSV** exist (substring rules — see [doc](../docs/forge-task-verification.md)).

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

Benchmark report:

```bash
python3 tools/scan_bench.py --output-json tools/scan_bench.ci.json --output-md tools/scan_bench.ci.md
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

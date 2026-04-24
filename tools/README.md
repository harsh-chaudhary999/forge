# Forge tools

Small, repo-local utilities shipped with Forge. The main maintained package here is **`scan_forge/`** — the scan-codebase pipeline (inventory → brain stubs → cross-repo heuristics).

## Layout

| Path | Purpose |
|------|---------|
| [`scan_forge/`](scan_forge/) | Python package: phases 1, 3.5, 4, 5, 56, 57, CLI; smoke data is generated at runtime by `verify_smoke.py` |
| [`verify_scan_outputs.py`](verify_scan_outputs.py) | Standalone check: same rules as `scan_forge.verify_brain_codebase` (required files + non-empty `modules/` when `source_files` > 0). **`forge_scan.py` runs verify automatically** (3 retries) after writing `index.md`; set **`FORGE_SCAN_SKIP_VERIFY=1`** only for emergency triage |
| [`forge_scan.py`](forge_scan.py) | CLI entry: prepends `tools/` on `sys.path` and runs `scan_forge.cli` |
| [`verify_forge_task.py`](verify_forge_task.py) | **Machine gate:** eval YAML ( **`--validate-eval-yaml`** — PyYAML if installed else [`eval_yaml_stdlib.py`](eval_yaml_stdlib.py)), `conductor.log` order, optional **`--check-prd-sections`**, **`--require-conductor-timestamps`**, **`--strict-single-task-brain`**, gates dir auto-fallback ([doc](../docs/forge-task-verification.md)) |
| [`forge_drift_check.py`](forge_drift_check.py) | **Drift:** `prd-locked.md` **Success Criteria** bullets vs `eval/*` + QA CSV text (**stdlib**; optional **`--strict`**) |
| [`eval_yaml_stdlib.py`](eval_yaml_stdlib.py) | Best-effort eval scenario shape without PyYAML (imported by verify script) |
| [`phase_ledger.py`](phase_ledger.py) / [`append_phase_ledger.py`](append_phase_ledger.py) | Append-only **`phase-ledger.jsonl`** with per-file **SHA256** (editor-agnostic) |
| [`shared_spec_policy.py`](shared_spec_policy.py) + [`shared_spec_checklist.json`](shared_spec_checklist.json) | **`verify_forge_task.py --check-shared-spec`** |
| [`lint_skill_allowed_tools.py`](lint_skill_allowed_tools.py) | CI: rigid **`allowed-tools`**; **`--write-policy`** → [`skill-tool-policy.json`](skill-tool-policy.json) for hosts that can consume it |

There is **no** separate throwaway “temp” tree under `tools/`; scan run artifacts are always created in a directory you pass as **`--run-dir`** (or a process temp dir), not committed here.

## Verifying a brain task (CI / pre-merge)

From the **Forge repo root**:

```bash
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain
# stricter (PyYAML): pip install -r tools/requirements-verify.txt
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain --require-log --validate-eval-yaml
```

See **[`docs/forge-task-verification.md`](../docs/forge-task-verification.md)** and **[`.github/workflows/forge-brain-guard.yml`](../.github/workflows/forge-brain-guard.yml)** (template for your brain repo).

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

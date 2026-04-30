# Semantic automation CSV (NL-first eval)

## CSV execution results

The machine-eval deliverable is **`qa/semantic-automation.csv`** executed through **`tools/run_semantic_csv_eval.py`** (or host automation), producing **`qa/semantic-eval-manifest.json`** + **`qa/semantic-eval-run.log`** — results that CI, **`[P4.0-SEMANTIC-EVAL]`**, and **`eval-judge`** consume.

## Why NL-first

Concrete **URLs, selectors, and payloads** often only become known **after** running against a real stack. **`qa/semantic-automation.csv`** records **Intent** per step and **DependsOn** ordering; the host layer (MCP, CDP, ADB, HTTP, SQL — per **CLAUDE.md** D5) maps **Surface** to tools. **`qa/manual-test-cases.csv`** remains the human acceptance inventory that **`forge-tdd`** traces for RED/GREEN tests.

**Intended order:**

1. **`qa/manual-test-cases.csv`** where policy requires it (acceptance inventory).
2. **`qa/semantic-automation.csv`** + host drivers → **`semantic-eval-manifest.json`** + **`semantic-eval-run.log`**.
3. Log **`[P4.0-SEMANTIC-EVAL]`** in **`conductor.log`** after manifest + run log are written.

`verify_forge_task.py` requires a **valid** `qa/semantic-eval-manifest.json` (and CSV coherence when **`kind: semantic-csv-eval`**).

---

| Path | Artifact |
|------|-----------|
| **Semantic** | `qa/semantic-automation.csv` + `qa/semantic-eval-manifest.json` + `qa/semantic-eval-run.log` |

## File layout

| Path | Role |
|------|------|
| `qa/semantic-automation.csv` | Step definitions (this document) |
| `qa/semantic-eval-manifest.json` | Written by **`tools/verify/run_semantic_csv_eval.py`** — outcome + metadata |
| `qa/semantic-eval-run.log` | JSON lines per step (runner output) |

## CSV columns

**Required**

| Column | Description |
|--------|-------------|
| **Id** | Stable step id (unique). Referenced by **DependsOn**. |
| **Surface** | One of: `web`, `api`, `mysql`, `redis`, `es`, `kafka`, `ios`, `android` (aliases like `web-cdp` → `web`, `api-http` → `api` — see **`tools/verify/semantic_csv.py`** `SURFACE_ALIASES`). |
| **Intent** | Natural-language instruction for the host automation layer. |

**Optional**

| Column | Description |
|--------|-------------|
| **DependsOn** | Comma-separated **Id** values. Steps with unmet or failed dependencies are **SKIPPED** at run time. Order is validated as a **DAG** (no cycles). |
| **TraceToCsvId** | Optional **`Id`** from **`qa/manual-test-cases.csv`** for traceability. |
| **ExpectedHint** | Optional substring or short hint for assertions / screenshots — interpreted by the host driver. |

## Host drivers (operator machine)

Forge plugin code does **not** ship LangChain-style orchestrators (**CLAUDE.md** D5). Semantic execution uses **host-local** drivers documented in **`eval-driver-*`** skills:

- **Web:** CDP / Playwright / **browser MCP** — ask the operator which path.
- **Android:** **ADB** vs **Appium MCP** — ask before committing.
- **iOS:** **XCTest** / simulator — macOS host.

Default CLI driver is **`noop`**: validates CSV, writes manifest + log, **does not** drive a browser or device. Use **`python3 tools/verify/run_semantic_csv_eval.py --dry-run`** for structure-only (**`outcome`**: **`yellow`** in manifest).

## CLI

From Forge repo root:

```bash
python3 tools/verify/run_semantic_csv_eval.py --task-id MY-TASK --brain ~/forge/brain
python3 tools/verify/run_semantic_csv_eval.py --task-id MY-TASK --brain ~/forge/brain --dry-run
```

Log **`[P4.0-SEMANTIC-EVAL]`** in **`conductor.log`** after manifest + **`semantic-eval-run.log`** are written.

## Skill

**`qa-semantic-csv-orchestrate`** — brain read → validate CSV → run CLI or dispatch host automation → append conductor marker.

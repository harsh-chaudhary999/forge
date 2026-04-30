# Semantic automation CSV (NL-first eval)

## Why this path exists (exploration before frozen YAML)

**Driver YAML** (`eval-scenario-format`) is **declarative**: it names concrete **actions, targets, URLs, selectors, payloads** your stack can resolve. That information often **does not exist** until after **exploratory execution** — you have run against a real stack, a real build, or a real device and discovered what is actually on screen and on the wire.

If process **requires** `eval/*.yaml` **before** the environment is knowable, teams produce **placeholder or fiction YAML** to satisfy a gate. That is the failure mode the semantic path fixes.

**Intended order of operations:**

1. **Acceptance inventory** where policy requires it — **`qa/manual-test-cases.csv`** (what must be true), not pre-encoded automation.
2. **Exploratory / NL-driven runs** — **`qa/semantic-automation.csv`** + host drivers (MCP, CDP, ADB, …) so execution can **discover** real behavior and **DependsOn** order without committing fake locators.
3. **Optional hardening** — once routes, health endpoints, and UI structure are **known**, add or replace with **`eval/*.yaml`** for **deterministic regression** and CI-shaped runs.

`verify_forge_task.py` treats a **valid** `qa/semantic-eval-manifest.json` (and CSV when `kind: semantic-csv-eval`) as **first-class** machine-eval evidence — not a waiver of “real” eval, but an honest record when YAML would be fiction.

---

Machine-eval paths in Forge:

| Path | Artifact | When |
|------|-----------|------|
| Declarative | `prds/<task-id>/eval/*.yaml` | Drivers with explicit locators — **`eval-scenario-format`** |
| Semantic | `prds/<task-id>/qa/semantic-automation.csv` + `qa/semantic-eval-manifest.json` | NL **`Intent`** per step, **`DependsOn`** ordering, optional trace to **`manual-test-cases.csv`** **`Id`** |

`tools/verify/verify_forge_task.py` accepts **either** YAML scenarios **or** a valid **`qa/semantic-eval-manifest.json`** (see **`docs/forge-task-verification.md`**). If manifest **`kind`** is **`semantic-csv-eval`**, the semantic CSV file **must** exist and parse cleanly.

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
| **Intent** | Natural-language instruction for the host automation layer (MCP browser, ADB, HTTP client, SQL — **not** pre-encoded selectors in this file). |

**Optional**

| Column | Description |
|--------|-------------|
| **DependsOn** | Comma-separated **Id** values. Steps with unmet or failed dependencies are **SKIPPED** at run time (runner responsibility). Order is validated as a **DAG** (no cycles); execution order is topological. |
| **TraceToCsvId** | Optional **`Id`** from **`qa/manual-test-cases.csv`** for traceability (same task). |
| **ExpectedHint** | Optional substring or short hint for assertions / screenshots — interpreted by the host driver. |

## Host drivers (operator machine)

Forge plugin code does **not** ship LangChain-style orchestrators (**CLAUDE.md** D5). Semantic execution uses **host-local** drivers:

- **Web:** Chrome DevTools / Playwright / Puppeteer / **browser MCP** — ask the operator which path before locking tooling.
- **Android:** **ADB** vs **Appium MCP** — ask before committing.
- **iOS:** **XCTest** / simulator — macOS host.

Default CLI driver is **`noop`**: validates CSV, writes manifest + log, **does not** drive a browser or device. Use **`python3 tools/verify/run_semantic_csv_eval.py --dry-run`** for structure-only (**`outcome`**: **`yellow`** in manifest).

## CLI

From Forge repo root:

```bash
python3 tools/verify/run_semantic_csv_eval.py --task-id MY-TASK --brain ~/forge/brain
python3 tools/verify/run_semantic_csv_eval.py --task-id MY-TASK --brain ~/forge/brain --dry-run
```

Log **`[P4.0-SEMANTIC-EVAL]`** in **`conductor.log`** after a successful run (same ordering role as **`[P4.0-EVAL-YAML]`**).

## Skill

**`qa-semantic-csv-orchestrate`** — brain read → validate CSV → run CLI or dispatch host automation → append conductor marker.

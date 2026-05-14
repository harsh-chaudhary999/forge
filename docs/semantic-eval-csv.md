# Semantic automation CSV (NL-first eval)

## Authoring vs execution

**Authoring:** **`qa-semantic-csv-orchestrate`** (skill) produces or updates **`qa/semantic-automation.csv`** from the brain/PRD context.

**Execution:** That CSV is then run through **`tools/run_semantic_csv_eval.py`** (or host automation), producing **`qa/semantic-eval-manifest.json`** + **`qa/semantic-eval-run.log`** — the artifacts CI, **`[P4.0-SEMANTIC-EVAL]`**, and **`eval-judge`** consume.

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

**Worked example:** [`docs/examples/semantic-automation.csv`](examples/semantic-automation.csv) — **api** health → **api** write → **mysql** verify (DAG depends on API before DB read) → **web** UI; **DependsOn** + **TraceToCsvId**.

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

### Result Interpolation: Passing Data Between Steps

When step B depends on step A (`DependsOn: step-A`), step B can reference step A's result values directly in its `Intent` or payload fields using this syntax:

```
${stepId.result.fieldName}
```

**Example:** Step `api-create-user` returns:
```json
{ "stepId": "api-create-user", "outcome": "PASS", "result": { "userId": "u_abc123", "email": "test@example.com" } }
```

A downstream step can reference:
- `${api-create-user.result.userId}` → resolves to `u_abc123`
- `${api-create-user.result.email}` → resolves to `test@example.com`

**Intent field example:**
```
Log in as the user created above: POST /auth/login with email=${api-create-user.result.email}
```

**Outcome when dependency fails:**
- Dependency `FAIL` → this step classified `BLOCKED_DEPENDENCY` (not executed)
- Dependency `PASS` but `result: {}` → this step classified `CONTEXT_GAP` (attempted without interpolation)
- Reference to unknown field → treat as `CONTEXT_GAP`

**Driver responsibility:** The eval driver (web-cdp, api-http, etc.) resolves `${...}` references by reading `semantic-eval-run.log` before executing the step. If resolution fails, the step is marked `CONTEXT_GAP`, not `FAIL`.

| **TraceToCsvId** | Optional **`Id`** from **`qa/manual-test-cases.csv`** for traceability (validated against that CSV). RED tests can cite the same ids via **`# forge-tdd: …`** — see **`skills/forge-tdd`** and **`verify_forge_task.py --verify-tdd-csv-trace`**. |
| **ExpectedHint** | Optional substring or short hint for assertions / screenshots — interpreted by the host driver. |

## Surface → Driver Mapping

The `Surface` column in `semantic-automation.csv` maps to a specific eval driver skill:

| CSV Surface value | Aliases | Eval Driver Skill | Notes |
|---|---|---|---|
| `web` | `web-cdp` | `eval-driver-web-cdp` | CDP / Playwright / browser MCP — ask operator which path |
| `api` | `api-http` | `eval-driver-api-http` | HTTP/REST calls |
| `mysql` | `db`, `db-mysql` | `eval-driver-db-mysql` | MySQL direct queries |
| `redis` | `cache`, `cache-redis` | `eval-driver-cache-redis` | Redis cache state |
| `es` | `search`, `search-es` | `eval-driver-search-es` | Elasticsearch |
| `kafka` | `bus`, `bus-kafka` | `eval-driver-bus-kafka` | Event bus |
| `android` | `android-adb` | `eval-driver-android-adb` | ADB vs Appium MCP — ask operator |
| `ios` | `ios-xctest` | `eval-driver-ios-xctest` | XCTest / simulator — macOS host only |

Aliases are resolved by `tools/verify/semantic_csv.py` `SURFACE_ALIASES` before validation.

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

## Related Documentation

| Doc | Purpose |
|---|---|
| [`docs/semantic-eval-schema.md`](semantic-eval-schema.md) | Full JSON schema for `semantic-eval-manifest.json` and `semantic-eval-run.log`, verdict logic table, RED_INFRA escalation |
| [`docs/forge-task-verification.md`](forge-task-verification.md) | CI integration, `verify_forge_task.py` flags, GitHub Actions workflow template |
| [`docs/conductor-log-format.md`](conductor-log-format.md) | Marker registry — `[P4.0-SEMANTIC-EVAL]` format and ordering constraints |

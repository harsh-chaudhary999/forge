---
name: scan-codebase
description: "WHEN: You need to map an existing codebase into the Forge brain — building an Obsidian-format knowledge graph of module relationships, architecture patterns, API surface, and documented edge cases. Invoked automatically after /workspace init and manually via /scan."
type: rigid
requires: [brain-write]
version: 1.0.0
preamble-tier: 2
triggers:
  - "scan the codebase"
  - "map the codebase"
  - "index repo for planning"
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# Scan Codebase

Map an existing repository into the Forge brain as an interconnected Obsidian knowledge graph.
Produces `~/forge/brain/products/<slug>/codebase/` — readable by humans, queryable by agents.

### Downstream handoff (E2E, novice-friendly)

This graph exists so **operators who do not know the repo** can still ship safely. **`tech-plan-write-per-project`** must cite **`codebase/`** paths when planning **reuse**; **intake-locked design** (Figma nodes, exports under `~/forge/brain/prds/<task-id>/design/`, Lovable GitHub sync) answers **what** net-new UI should look like — the tech plan’s **Section 1b.4** connects design anchors to components. Scan + design together prevent “Figma was in intake but planning ignored it” and reduce integration bugs. Prefer a **fresh `/scan <slug>`** before major tech planning if **`SCAN.json`** is stale.

---

## Anti-Pattern Preamble

**Stop. Read this before touching any file.**

### Anti-Pattern 1: "Just read all the source files — that's how you understand a codebase"

**Why This Fails:** Reading every file burns 50-200K tokens on boilerplate, tests, generated code, and third-party vendored files. 30-40% of what you read will be noise. The structural relationships you need (who imports whom, what the entry points are, which files are hubs) are available from import lines and filenames alone — zero tokens required.

**Enforcement:**
- MUST run Phase 1 (grep/find) before reading any source file
- MUST identify hub files via incoming-reference count before selecting what to read
- MUST exclude: `node_modules/`, `vendor/`, `dist/`, `build/`, `__pycache__/`, `.git/`, `*.generated.*`, `*.min.js`, `*.lock`
- MUST extract class/type/struct inventory via grep in Phase 1.6 BEFORE reading any hub file
- MUST NOT read test files unless they are the only documentation for an API

### Anti-Pattern 2: "I'll scan the entire codebase at once and produce a single summary"

**Why This Fails:** Monolithic summaries are high-token, low-recall. When an agent later needs to know "what does the auth module export?", searching a 5000-word summary is slower and less reliable than reading `brain/products/<slug>/codebase/modules/auth.md`. The output must be navigable files, not a wall of text.

**Enforcement:**
- MUST produce separate `.md` files per module — not a single summary document
- MUST use `[[wikilinks]]` to cross-reference between brain files

### Anti-Pattern 3: "I'll headline inventory with ~60+ files / many services — sounds credible"

**Why This Fails:** **"60+"**, **"many"**, or even **"exactly 62"** without **which paths / what role / how listed** does not let the next agent open the right files. Brain output exists so people can **navigate** — summaries must point to **named nodes** (modules, routes, dirs), not scale alone.

**Enforcement:**
- MUST ground inventory in **what / where / how**: path or `[[wikilink]]`, repo + role, and the Phase artifact or command that produced the row (e.g. line in `forge_scan_source_files.txt`, key in **`SCAN.json`**).
- MUST NOT use **N+** / vague quantifiers; MUST NOT use **count-only** bullets when a **path list or table** is practical for the slice you are describing.
- If not yet written: **UNKNOWN** + the **specific** Phase 1 file or command you will use — never a guessed floor.
- MUST write each file to `~/forge/brain/products/<slug>/codebase/` individually
- MUST git-commit after each project role is scanned (backend, web, app) — not after all

### Anti-Pattern 3: "I'll infer architecture patterns without checking the actual dependency graph"

**Why This Fails:** Pattern detection from file names alone is wrong 40% of the time. A file named `UserService.ts` in a monolith does not imply service architecture. The actual import graph — which files import which — is the ground truth for pattern detection.

**Enforcement:**
- MUST build import adjacency before classifying patterns
- MUST confirm pattern with at least 3 structural signals (not just naming conventions)
- MUST label uncertain patterns as `likely-<pattern> (unconfirmed)` in output
- MUST NOT write patterns.md until after the import graph is built

### Anti-Pattern 4: "Tests are noise — skip them"

**Why This Fails:** Test files are often the only documentation for edge cases and expected failure modes. A `test_login_with_expired_token.py` tells you more about auth edge cases than any docstring. Test file names and their `describe`/`test` strings are high-signal, zero-token gotcha sources.

**Enforcement:**
- MUST scan test file names and top-level describe/test strings
- MUST extract `it("should fail when...")` and `test("edge case:...")` strings into `gotchas.md`
- MAY skip test file bodies — names and test strings only
- MUST NOT skip entire test directories

### Anti-Pattern 5: "I've scanned this before — I'll use my memory instead of re-running"

**Why This Fails:** Codebases change. A brain scan is a snapshot. Using stale scan data leads agents to reference deleted modules, outdated APIs, or patterns that were refactored out. Every scan must produce a new timestamped snapshot.

### Anti-Pattern 6: "The scan command finished — I won't verify outputs"

**Why This Fails:** Partial runs, wrong `--brain-codebase`, or aborted phase56 leave **`SCAN_SUMMARY.md` / `graph.json` / `modules/`** missing or empty while **`SCAN.json` looks fine**. Downstream consolidations never happened; the pipeline “escapes” silently. **MUST** run **`tools/verify_scan_outputs.py`** after each scan (see **Post-run integrity gate**).

**Enforcement:**
- MUST write `SCAN.json` with timestamp, commit SHA, and file count on every run
- MUST include `last-scanned:` field in `index.md` header
- MUST NOT reuse a scan older than 7 days without re-running Phase 1 to check for new files
- MUST overwrite existing codebase brain files on re-scan (not append)

---

## Overview

Scan produces a structured knowledge graph of a codebase, stored in the Forge brain as navigable Obsidian markdown. It runs in 4 phases, ordered by token cost (cheapest first):

```
Phase 1 — Structural map     (Python + grep, 0 LLM tokens)
Phase 2 — Hub detection      (derived from phase 1 artifacts, 0 LLM tokens)
Phase 3 — Semantic enrichment (targeted reads, low tokens)
Phase 4 — Brain write        (structured output, low tokens)
```

Output goes to: `~/forge/brain/products/<slug>/codebase/`

---

## Deployment / runbook gate (eval & stack-up)

**Problem:** `eval-product-stack-up` and deploy drivers read **`~/forge/brain/products/<slug>/product.md`**. If every project lacks **`deploy_doc`** (path to run/deploy doc, relative to that repo) **and** lacks a usable **`start`** + **`health`**, agents guess — services fail to spawn and eval wastes cycles.

**HARD-GATE (workspace path):** When scan follows **`/workspace`** init, **`product.md` must already satisfy `/workspace` Step 3b** (each project has `deploy_source` + `deploy_doc`, or `start`+`health`). Do not treat workspace-complete until Step 3b is done.

**When `/scan` runs later:** If `product.md` is missing deploy fields, follow **`commands/scan.md` Step 1** — rediscover README/compose, ask once for paths or commands, update `product.md`, then run `forge_scan.py`. **Blocking is allowed** until deploy fields exist — eval and stack-up are not optional for a “ready” product workspace.

**Optional brain artifact:** After a successful gate, you may add `codebase/DEPLOYMENT.md` summarizing per-role `deploy_doc` paths and health URLs for humans — keep **`product.md`** the machine source of truth for stack-up.

---

```
codebase/
  index.md              # Overview: entry points, architecture style, stats, last scanned
  SCAN.json             # Metadata: timestamp, commit SHA, file count, language breakdown
  SCAN_SUMMARY.md       # One-page orientation + limitations (after each scan)
  graph.json            # Derived module graph + cross-repo edges (regeneratable)
  .forge_scan_manifest.json  # Per-role git tree/head fingerprints (tooling)
  modules/
    <module-name>.md    # Per-module: purpose, exports, dependencies, dependents
  patterns.md           # Detected architecture patterns with evidence
  api-surface.md        # Public API endpoints, exported symbols, event schemas
  gotchas.md            # Documented edge cases, TODOs, FIXMEs, test-case-named edge cases
```

**Consumer contract:** Phases that pick *where* to work (council, tech plans, eval YAML, design notes) should read **`index.md`**, **`modules/*.md`**, **`api-surface.md`**, and **`SCAN.json` here first**, then open paths under the product clones. Do not use ad-hoc repo tree exploration as a substitute when this tree exists and is fresh; refresh with **`/scan <slug>`** if stale or absent.

---

## Scan runner (`tools/scan_forge`)

> **Do not re-implement Phase 1–5 pipelines by hand.** The committed Python package is the source of truth; one invocation runs the full scan. Layout and CI commands: **`tools/README.md`**.

| Entry | Purpose |
|-------|---------|
| `python3 tools/forge_scan.py …` | Prepends `tools/` on `sys.path` and runs **`scan_forge.cli`** (implementation: **`tools/scan/forge_scan.py`**; root file is a shim) |
| `PYTHONPATH=tools python3 -m scan_forge …` | Same CLI when `tools/` is already on `PYTHONPATH` |

**Requirements:** Python 3.9+, **GNU grep** and **cksum** on `PATH` (pattern inventory and stable method IDs). Optional: `pip install -r tools/scan_forge/requirements.txt` (adds **PyYAML**) for reliable YAML OpenAPI parsing and full `openapi-schema-digest` coverage.

**Package layout:** `tools/scan_forge/` — `cli.run_scan` invokes `phase1` → `phase35` → `phase4` (writes `SCAN.json` via `scan_metadata`) per repo, then **`openapi_schema_digest.write_digest`** (writes `openapi-schema-digest.md`), then `phase5` → `phase56`, then **`codebase_index.write_codebase_index_md`** (writes **`index.md`**), optional `phase57`, **`repo_docs_mirror`**, then **`verify_brain_codebase_with_retries`** (3 attempts, short delay) unless **`FORGE_SCAN_SKIP_VERIFY=1`**; then optional `cleanup`; optional `validate_roles` when `--product-md` is set. **Per-repo inventory** is written under **`<run_dir>/_role/<role>/`** (`scan_paths.role_scan_dir`) so phase1 outputs are not overwritten across repos; merged routes and phase5 artifacts stay at **`run_dir/`** root. **`run.json`** records **`phase_timings_ms`**, **`verify_scan_outputs`**, and **`total_elapsed_ms`**. If verify fails, **`status`** is **`verify_failed`**, **`run.json`** is still written, **`--cleanup` is skipped** (keeps `forge_scan_*.txt` for triage), and the CLI exits **non-zero**.

**OpenAPI / Swagger (phase 3.5):** Each repo is scanned for spec files (`openapi.json`, `openapi.yaml`, `openapi.yml`, `swagger.json`, `*.openapi.json`, filenames containing `openapi` or `swagger` with json/yaml/yml — see `openapi_routes.discover_openapi_files`). Operations are **appended** to `forge_scan_api_routes.txt` after grep-based route lines. **Phase 56** matches frontend call paths to those operations using substring match **or** `{param}` template matching (so `/api/users/123` can match `/api/users/{id}`). Without PyYAML, YAML specs may be skipped or partially parsed; install from `tools/scan_forge/requirements.txt` when possible.

**Schema digest (not prop↔DTO proof):** `openapi-schema-digest.md` lists shallow `components.schemas` property names per role for LLM/recall — it does **not** certify React props ↔ backend fields. **Empirical coverage:** re-scan your stack, then use `python3 -m scan_forge.scan_metrics --brain-codebase <codebase> [--run-dir <kept>]` to print SCAN.json / automap / digest hints (numbers are observational, not a guarantee of N% accuracy).

**Derived artifacts (after phase56, always regenerated):**

| File | Purpose |
|------|---------|
| `index.md` | **Auto-written** orientation: `last-scanned`, repo table, module map (first N wikilinks), pointers to `SCAN_SUMMARY.md` / `graph.json` — satisfies verify + gives agents a single entry note |
| `SCAN_SUMMARY.md` | One-page orientation: freshness, per-role stats, links to automap / digest / graph, known limitations |
| `graph.json` | Machine graph: `nodes` (module stems + paths) + `edges` (`cross_repo_http` with `url` + `provenance`) — **derived** from markdown + automap; markdown modules remain the human source of truth |
| `.forge_scan_manifest.json` | Per-role `git` `HEAD` + `HEAD^{tree}` after each successful scan — for tooling and future incremental strategies |
| `.forge_scan_file_state.json` | Per-role `head` / `tree`, tracked source blob SHAs, and changed-path counts used by `--incremental` mode |
| `forge_scan_edges.sqlite` | Regenerated query store from `graph.json` (ad-hoc SQL; non-canonical, disposable) |

**Cross-repo provenance (phase56):** Injected module bullets and `cross-repo-automap.md` TSV use tags: **`OPENAPI`** (route line from OpenAPI append), **`GREP_SUBSTRING`** / **`GREP_TEMPLATE`** (grep route inventory; template = `{param}` match), **`MANUAL_ALIAS`** (rows from `route-aliases.tsv`). These label **how the join was made**, not runtime correctness.

**MCP:** Not part of the default pipeline. Full scans are driven by **`/scan`** and **`python3 tools/forge_scan.py`** (or `PYTHONPATH=tools python3 -m scan_forge`) plus workspace init. For ad-hoc queries without loading all markdown, use **`python3 tools/forge_graph_query.py --graph <path-to-graph.json> summary|neighbors|search`** (stdlib CLI on the same `graph.json` this scan writes).

**Token policy:** The scanner does **not** impose artificial context/token budgets on outputs — summaries and graphs include available signal; agents and skills choose what to read.

**Known limitations (honest):** Grep-based call/route inventory misses dynamic URLs and some frameworks; OpenAPI discovery is heuristic; Obsidian resolves `[[modules/…]]` from the **vault root** (often open `codebase/` as vault or expect some wikilinks to need path adjustment); `graph.json` edges require current automap TSV columns (includes `route_rel_path`). Re-scan after major refactors.

**Diagnostics:** Modules emit `FORGE_SCAN|<id>|<utc>|LEVEL|…` (see `tools/scan_forge/log.py`).

### Post-run integrity gate (HARD-GATE — prevents “scan escaped”)

**Problem:** The CLI can be interrupted, pointed at the wrong `--brain-codebase`, or leave a half-written tree. Downstream then treats **missing** `SCAN_SUMMARY.md` / `graph.json` / empty `modules/` as “no data” and silently **invents paths** — the same class of failure as skipping parity.

**Built-in (Python CLI):** `scan_forge.cli.run_scan` ends with **`verify_brain_codebase_with_retries`** (default **3** attempts, **~0.35s** between attempts for local FS), after **`codebase_index.write_codebase_index_md`** (so **`index.md`** always exists on a full run). **`run.json`** includes **`verify_scan_outputs`** with exit code and messages. **Emergency bypass only:** set **`FORGE_SCAN_SKIP_VERIFY=1`** (documents intentional risk — never default in automation).

**Agent / shell belt-and-suspenders:** After any **`forge_scan.py`** / **`python3 -m scan_forge`** that exits **0**, still run (or re-run until OK, max **3** tries with **1s** backoff):

```bash
python3 tools/verify_scan_outputs.py ~/forge/brain/products/<slug>/codebase
```

- **Exit 0:** Required consolidated artifacts exist (`SCAN.json`, `SCAN_SUMMARY.md`, `graph.json`, `.forge_scan_manifest.json`, `index.md`) and `modules/` is non-empty when the scan reports source files.
- **Exit non-zero:** **Do not** claim `/scan` complete; **do not** proceed to council or tech-planning that depends on file-level brain paths until re-run passes. Log **`[SCAN-VERIFY] slug=<slug> status=FAIL`** with the script stdout. If the **CLI already exited non-zero** with **`verify_failed`**, treat that the same — **full re-scan** with a **fresh `--run-dir`**, correct **`--brain-codebase`**, then verify again.

**If you hand-ran phases or patched brain files:** You **must** run **`verify_scan_outputs.py`** before claiming parity with a full scan.

**Determinism / “irrational” behaviour (reduce surprises):**

| Pitfall | Mitigation |
|---------|------------|
| **Reusing a stale `--run-dir`** after partial failure | Use a **fresh** run directory per attempt; with **`--cleanup`**, do not assume artifacts survived. |
| **Single-repo `--repos`** when phase56 needs route owners | For FE↔BE linking, include **every route-defining repo** in one invocation (backend first). |
| **Missing PyYAML** | YAML OpenAPI may be skipped → weaker api inventory; install `tools/scan_forge/requirements.txt` when possible. |
| **`--brain-codebase` not the workspace `codebase/`** | Verify path matches **`~/forge/brain/products/<slug>/codebase`** exactly. |
| **Skipping phase57** | Wikilink/orphan issues stay hidden — use **`--phase57-write-report`** after large `modules/` edits. |

**Log (optional):** `[SCAN-VERIFY] slug=<slug> status=OK run_dir=<path>` for conductor / audit trails.

### CLI flags (common)

| Flag | Meaning |
|------|---------|
| `--brain-codebase <dir>` | Brain codebase parent (the tree containing `modules/`, `classes/`, …) |
| `--repos role:/abs/path …` | One or more repos; **`role` must equal `basename(path)`** |
| `--run-dir <dir>` | Artifact dir for `forge_scan_*.txt` and `run.json` |
| `--product-md <file>` | Optional — validates `role:` vs repo basename pairs in `product.md` |
| `--skip-phase57` | Skip wikilink validation |
| `--phase57-write-report` | Write `wikilink-orphan-report.md` under the brain codebase parent |
| `--cleanup` | Remove `forge_scan_*.txt` in the run dir after success |
| `--incremental` | Use previous heads to compute changed paths and skip per-role phase1/3.5/4 when no scan-relevant files changed |

**Related environment flags (operator controls):**

- `FORGE_SCAN_INCREMENTAL=1` — same as passing `--incremental`
- `FORGE_SCAN_AST_IMPORTS=1` — emit `forge_scan_ast_import_edges.tsv` and include import-ref edges in `graph.json`

**Incremental confidence/fallback inspection:**

- Check `run.json` keys `incremental.phase5_56_mode` and `incremental.phase5_56_reason`.
- `run_full_fallback` means conservative full recompute due to low confidence in prior state.
- `skipped_by_profile` means cross-repo recompute was skipped only after heuristic change profiling found no phase5 inputs.

**Import-edge confidence guidance:**

- TSV provenance tiers: `AST_STRONG`, `AST_WEAK`, `HEURISTIC`.
- `graph.json` includes only confidence-qualified import edges (`AST_STRONG` / `AST_WEAK`).
- Use `HEURISTIC` rows for diagnostics, not trusted dependency claims.

### Canonical command (multi-repo)

```text
python3 tools/forge_scan.py \
  --brain-codebase ~/forge/brain/products/<slug>/codebase \
  --repos backend:~/projects/backend web:~/projects/web app:~/projects/app \
  [--product-md ~/forge/brain/products/<slug>/product.md] \
  [--phase57-write-report] [--cleanup]
```

**Order inside the runner:** phase **1** → **3.5** (first repo truncates `forge_scan_api_routes.txt`; later repos **append**) → **4** per repo → **5** once → **56** → optional **57** → optional **cleanup**. List route-defining repos with **backend first** when possible so API routes accumulate correctly for phase 56.

### Tier 1 / Tier 2 hubs vs a full file graph

**Hub tiers are not a ceiling on brain size.** They only prioritize which files to read first in Phase 3. Phase 1 lists every scanned source file; Phase 4 writes stubs from full inventories; Phase 4.3d emits one method stub per `forge_scan_methods_all.txt` line (not hub-filtered). Cross-repo edges come from routes × call sites in Phase 5–56, not hub scores.

| You want… | What to do |
|---|---|
| Maximum **nodes** | Run the full runner through phase 4 |
| Maximum **prose** | Batch-read all paths in `forge_scan_source_files.txt` |
| Maximum **FE↔BE links** | Ensure multi-repo `--repos` includes every route-defining repo; use `--phase57-write-report` after edits |

### FAQ: Tier 1 count vs git file count

Tier 1 is **incoming reference score ≥5** from a cheap import-line scan, not “every file in git.” Many files stay at 0–2 incoming hits. Node counts come from Phase 4 and are orthogonal.

### Fixing orphan `[[wikilinks]]`

1. Re-run with **`--phase57-write-report`**.
2. Align **`role`** in `product.md` with **`basename(repo path)`** for each project.
3. Re-run scan after slug fixes; remove stale links the report flags.

### Optional operator utilities (post-scan)

- Search artifacts with local BM25:
  - `python3 tools/forge_codebase_search.py --brain-codebase <codebase> --query "<terms>"`
- Query edge store:
  - `python3 -m scan_forge.query_repl --brain-codebase <codebase> --sql "select kind,count(*) from edges group by kind"`
- Run benchmark harness:
  - `python3 tools/scan_bench.py --output-json tools/scan_bench.ci.json --output-md tools/scan_bench.ci.md`

These are convenience analysis tools; they do not replace scan verification or required outputs.

---

## Phase 1: Structural Map (Zero Tokens)

**Implementation:** `tools/scan_forge/phase1.py`. The runner sets **`FORGE_SCAN_TMP`** (and `FORGE_SCAN_RUN_DIR`) to your artifact directory — prefer `--run-dir` instead of littering `/tmp`.

**Artifacts** (under `$FORGE_SCAN_TMP`): `forge_scan_source_files.txt`, `forge_scan_test_files.txt`, `forge_scan_imports.txt`, `forge_scan_hub_scores.txt`, `forge_scan_tier1.txt`, `forge_scan_tier2.txt`, per-language inventories, aggregated `forge_scan_types_all.txt`, `forge_scan_methods_all.txt`, `forge_scan_functions_all.txt`, `forge_scan_ui_all.txt`.

Read the **INVENTORY SUMMARY** printed at the end of phase 1 (or inspect those files). Do not re-run ad-hoc `find`/`grep` blocks; `phase1.py` already produces the full inventory.

---

## Phase 2: Hub Identification (Zero Tokens)

From `forge_scan_hub_scores.txt`, identify:

**Tier 1 Hubs** (referenced by 5+ files) — read in full in Phase 3
**Tier 2 Hubs** (referenced by 3-4 files) — read in full in Phase 3
**Leaf files** (referenced by 0-2 files) — stubs auto-generated; enrich in batches during Phase 3 if full coverage is needed

Tier lists are already in **`forge_scan_tier1.txt`** and **`forge_scan_tier2.txt`** under `$FORGE_SCAN_TMP` (produced during phase 1).

---

## Phase 3: Semantic Enrichment (Full Reads)

Read files in this priority order. Read each file in full. **No file is off limits and no hard token cap applies** — if there are too many files to fit in one pass, process in batches (commit after each batch) and continue until all files are enriched. Never skip a file permanently.

### 3.1 — Always read

These are documentation files, not code. Read fully when present: `README.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`, `docs/architecture.md`, `docs/design.md`, `ADR*.md`, `adr/*.md`, `docs/decisions/*.md`.

### 3.2 — Tier 1 hub reads (full file)

Read each absolute path listed in **`forge_scan_tier1.txt`** (under `$FORGE_SCAN_TMP`) in full.

Extract from each hub:
- Exported classes, functions, interfaces (look for `export`, `public`, `pub fn`, `func`, `def`)
- Constructor signatures and key method signatures
- JSDoc/docstrings on exported items
- `// TODO`, `// FIXME`, `// HACK`, `// NOTE` comments

### 3.3 — Tier 2 hub reads (full file)

Read each path in **`forge_scan_tier2.txt`** in full.

### 3.3a — Class/method/attribute enrichment from hub reads

Phase 1.6 already extracted the **names and locations** of all types from disk via grep. The job here is to **enrich** those known types with methods, properties, doc comments, and inheritance — by reading the hub files in full.

For each hub file, cross-reference `$FORGE_SCAN_TMP/forge_scan_types_all.txt` to know which classes live there, then extract the following. **Each language has fundamentally different syntax:**

---

**Java** (`*.java`)

*Types*: `public class Foo`, `abstract class Foo`, `interface Foo`, `enum Foo`, `@interface Foo`
*Inheritance*: `extends BarClass`, `implements BazInterface` — critical for graph edges
*Annotations*: `@Service`, `@Repository`, `@RestController`, `@Entity` — determines layer
*Fields (properties)*: `private String name;`, `protected final List<X> items;`
*Methods*: `public ReturnType methodName(Type param)` — include full signature
*Constructor*: `public ClassName(Type param, Type param2)`
*Key gotcha*: Inner classes and anonymous classes — record them as nested, not top-level

**Kotlin** (`*.kt`)

*Types*: `data class Foo(val a: A, val b: B)` — constructor params ARE the properties
*Sealed class*: `sealed class Result` with subclasses `data class Success(...)` and `data class Error(...)` — these are variants, not independent classes
*Object*: `object Singleton` — no constructor, static singleton
*Companion object*: nested `companion object { ... }` — factory methods live here
*Coroutines*: `suspend fun fetchData(): Result<T>` — mark `suspend` in method notes
*Properties*: `val name: String`, `var count: Int = 0`, `lateinit var db: DB`
*Key gotcha*: Extension functions (`fun String.toUser(): User`) are NOT class members — they belong to the module, not the class

**Go** (`*.go`)

*Types*: `type UserService struct { ... }` — fields are inside the struct body
*Struct fields*: Lines inside `type X struct { ... }` block — `FieldName Type \`json:"..."\`` 
*Interfaces*: `type UserRepository interface { ... }` — method signatures inside the block
*Methods*: **NOT inside the struct.** Look in `$FORGE_SCAN_TMP/forge_scan_methods_go.txt` for lines matching `(* TypeName)` or `( TypeName)`. Pattern: `func (u *UserService) GetUser(ctx context.Context, id int64) (*User, error)`
*Constructor*: `func NewUserService(db *DB) *UserService` — named constructors, not `new`
*Key gotcha*: Go has no inheritance. Embedding (`type Admin struct { User }`) is composition, not inheritance. Note it as "embeds [[classes/<role>-User]]" not "extends".

**TypeScript / Node.js** (`*.ts`, `*.tsx`)

*Types*: `export class UserController`, `export interface IUser`, `export abstract class BaseService`
*Decorators*: `@Injectable()`, `@Controller('/users')`, `@Entity()` — the decorator tells you the layer before you read a single method
*Constructor injection*: `constructor(private readonly userService: UserService)` — injected deps = class dependencies for graph edges
*Methods*: `async getUser(id: string): Promise<User>`, `private validate(data: unknown): boolean`
*Properties*: `readonly name: string`, `private count = 0`, `@Column() email: string`
*Type aliases*: `export type UserId = string` — if used widely, it's a domain concept worth noting
*Key gotcha*: Arrow function class properties (`private handleClick = () => {}`) are methods defined as properties — include them

**Python** (`*.py`)

*Types*: `class UserService(BaseService):` — base class in parens = inheritance
*Dataclasses*: `@dataclass class User:` — fields defined as `name: str`, `age: int = 0`
*Abstract*: `class IRepository(ABC):` with `@abstractmethod def find_by_id(self, id: int)`
*Methods*: `def get_user(self, user_id: int) -> User:`, `async def fetch(self) -> List[T]:`
*Class variables*: `MAX_RETRIES: int = 3` (outside `__init__`)
*Instance variables*: set in `__init__`: `self.name = name`
*Key gotcha*: `__init__` params are the constructor signature — list them as "Constructor" not as a method

**Dart / Flutter** (`*.dart`)

*Types*: `class UserBloc extends Bloc<UserEvent, UserState>`, `abstract class IUserRepository`, `mixin LoggerMixin`
*Widgets*: `class UserWidget extends StatelessWidget` / `StatefulWidget` — note as "widget", not "service"
*Fields*: `final String name;`, `late UserRepository _repo;`
*Methods*: `@override Widget build(BuildContext context)`, `Future<User> getUser(String id)`

---

**Record per class as you read** (used in Phase 4.3a):

```
Language: Go
File: internal/user/service.go
Type: UserService (struct)
Annotation/Decorator: none
Fields: db *gorm.DB, logger *zap.Logger
Methods (from forge_scan_methods_go.txt): GetUser(ctx, id int64) (*User, error), CreateUser(ctx, req CreateUserRequest) (*User, error), DeleteUser(ctx, id int64) error
Implements: UserRepository (interface)
Constructor: NewUserService(db *gorm.DB, logger *zap.Logger) *UserService
```

```
Language: Kotlin
File: src/main/kotlin/com/app/user/UserService.kt
Type: UserService (class)
Annotation: @Service
Properties: userRepository: UserRepository (injected), emailSender: EmailSender (injected)
Methods: findById(id: Long): User?, createUser(req: CreateUserRequest): User, suspend sendWelcomeEmail(userId: Long)
Extends: none
Implements: IUserService
```

**Stub nodes for ALL classes** are already auto-generated by the Phase 4 step in `tools/scan_forge` (`phase4.py`) (Step 4.0) — from the full `forge_scan_types_all.txt` inventory, not just hubs.

**Enrichment in Phase 3** (filling in Purpose, Methods, Properties, Relationships from reading the actual file) is **prioritized** for **Tier 1 and Tier 2 hub files** to save tokens — but **stubs** (classes, **methods/**, functions, pages, modules) already exist for the **whole** grep inventory. To enrich every file anyway, walk `forge_scan_source_files.txt` in batches and ignore the tier lists.

---

### 3.4 — Test name extraction + 3.5 — API route extraction

Handled automatically by **`tools/scan_forge`** (`phase35.py`) for each repo in `--repos` order: the first repo resets `forge_scan_api_routes.txt`; later repos **append**.

**HARD-GATE (multi-repo):** `$FORGE_SCAN_TMP/forge_scan_api_routes.txt` must list routes from **every** repo that defines HTTP APIs (typically backend + any BFF). If the backend is not included or order is wrong, phase 56 will miss FE↔BE links.

Recommended `--repos` order: **backend first**, then web, mobile, BFFs.

Artifacts:
- `forge_scan_test_names.txt` — test name strings (for `gotchas.md`)
- `forge_scan_api_routes.txt` — route lines with `<repo-basename>\\trel:line:content` (for `api-surface.md` and phase 56)

Read the phase 3.5 console output for the HTTP method breakdown before manual enrichment.

---

## Phase 4: Brain Write (Obsidian Format)

Create all output files in `~/forge/brain/products/<slug>/codebase/`. Use `[[wikilinks]]` throughout.

### 4.0 — Auto-generate all stub nodes (REQUIRED, run before any manual enrichment)

**HARD-GATE:** The runner’s **Phase 4** (`tools/scan_forge/phase4.py`) generates EVERY class, function, page, and module stub from the Phase 1 inventories. Do NOT hand-author stub files at scale — enrich them after. Phase 4 reads `forge_scan_types_all.txt`, `forge_scan_functions_all.txt`, `forge_scan_ui_all.txt`, and `forge_scan_source_files.txt` under **`$FORGE_SCAN_TMP`**. It writes under `classes/`, `functions/`, `pages/`, and `modules/` beneath `--brain-codebase`. Existing files are **never overwritten**.

**Multi-repo:** Prefer **one** `python3 tools/forge_scan.py` (or `PYTHONPATH=tools python3 -m scan_forge`) invocation with all `--repos` so phase 1 → 3.5 → 4 run in the correct order for every role. If you must split work, run the full runner per repo with the same `--run-dir` only when you know what you are doing — the default is one coherent pipeline.

Check the Phase 4 summary for node counts. If a count is 0 unexpectedly, confirm Phase 1 artifacts exist for that repo in `FORGE_SCAN_TMP`.

### 4.1 — SCAN.json (metadata, always first)

**Written automatically** at the end of each repo’s Phase 4 by **`tools/scan_forge/scan_metadata.merge_scan_json`**: `~/forge/brain/products/<slug>/codebase/SCAN.json`.

- **`repos.<role>`** holds per-repo path, commit SHA, scan time, and inventory line counts (sources, tests, tier hubs, types, methods, functions, UI).
- **Top-level** `scanned_at`, `source_files`, `test_files`, etc. are **aggregated** across roles for backward compatibility with skills that grep a flat `SCAN.json`.
- Legacy single-repo flat `SCAN.json` files are merged into **`repos`** on the next run.

### 4.2 — index.md format

```markdown
# Codebase: <repo-name> (<role>)

last-scanned: <ISO timestamp>
commit: <SHA>
files: <count> source, <count> test

## Architecture Style

<Detected pattern: monolith | service-per-feature | layered | modular-monolith | microservice slice>
Evidence:
- <Signal 1 from import graph>
- <Signal 2 from file structure>
- <Signal 3 from framework detection>

## Entry Points

- [[modules/<module>]] — `<path/to/entry>` (<what it boots>)

## Module Map

| Module | Role | Incoming Refs | Key Exports |
|---|---|---|---|
| [[modules/<name>]] | <layer: controller/service/repo/util/config> | <count> | `<ClassA>`, `<fnB>` |

## Architectural Hubs (Tier 1)

Files referenced by 5+ other modules — these are the load-bearing structures:

- [[modules/<name>]] (`<path>`) — <one-line purpose>

## Key Dependencies

External dependencies that shape the architecture:
- `<package>` — <what it's used for>

## Related Brain Files

- [[structure]] — Directory tree with wikilinks to every module
- [[patterns]] — Architecture patterns detected
- [[api-surface]] — Public API endpoints
- [[gotchas]] — Documented edge cases

## Key Classes

> Top classes across this repo — each is a graph node in `classes/`.

- [[classes/<role>-<ClassName>]] — `<one-line purpose>`
- [[classes/<role>-<ClassName2>]] — `<one-line purpose>`
```

### 4.3 — modules/<name>.md format

**Naming convention:** Files are named `<role>-<module>.md` — e.g. `backend-users.md`, `web-useUser.md`, `consumer-service-UserClient.md`. The role prefix is mandatory. It makes cross-repo wikilinks unambiguous in the Obsidian graph — `[[backend-users]]` is a different node from `[[web-users]]`.

Create one file per top-level module directory + one for each Tier 1 hub.

```markdown
# Module: <name>

**Repo:** <role> (`<repo-path>`)
**Path:** `<relative/path/from/repo/root>`
**Layer:** <controller | service | repository | domain | infrastructure | util | config>
**Language:** <language>

## Purpose

<One-paragraph description synthesized from: docstrings, README mentions, hub file top comments>

## Classes

> Significant classes defined in this module. Each is a node in the Obsidian graph.

| Class | Type | Description |
|---|---|---|
| [[classes/<role>-<ClassName>]] | class / interface / struct | <one-line purpose> |

## Exports

| Symbol | Type | Used by |
|---|---|---|
| `<ClassName>` | class | [[<role>-<consumer>]], [[<role>-<consumer2>]] |
| `<functionName>` | function | [[<role>-<consumer>]] |

## Imports (within repo)

- [[<role>-<dep>]] — `<what it uses from dep>`
- `<external-package>` — <what it's used for>

## Imported by (within repo)

- [[<role>-<dep>]] — `<why it needs this module>`

## Calls (cross-repo)

> Routes this module calls in other repos — auto-filled by **phase56** after `scan_forge.phase5` (markers `FORGE:AUTO_*`). Manual rows optional.
> On first pass stubs may be prose-only until phase56 runs.

- `<METHOD> <path>` → [[<other-role>-<module>]] (`<other-repo>/src/routes/file.ts:<line>`)

## Called By (cross-repo)

> Callers in other repos — **phase56** fills `FORGE:AUTO_CROSS_REPO_IN`. Manual rows optional.

- [[<caller-role>-<module>]] (`<caller-repo>/src/hooks/file.ts:<line>`) → `<METHOD> <path>`

## Documented Edge Cases

> From test file: `<test name that describes edge case>`

- `<test string describing edge case 1>`
- `<test string describing edge case 2>`

## TODO / FIXME

> Extracted from source comments

- `<file:line>` — `<comment text>`
```

**Important:** Phase 4 writes scaffold text for `## Calls (cross-repo)` / `## Called By (cross-repo)`. **phase56** appends auto-blocks once `$FORGE_SCAN_TMP/forge_scan_all_callsites.txt` and merged routes exist. Do not hand-fill large edge lists during Phase 4 — correlation data is not ready until phase5 prep completes.

### 4.3a — classes/<role>-<ClassName>.md format

> **Stubs are auto-generated by the Phase 4 step in `tools/scan_forge` (`phase4.py`) (Step 4.0).** The script writes a stub for EVERY class in `forge_scan_types_all.txt`. Your job here is to ENRICH stubs for Tier 1 and Tier 2 hub classes during hub reads — add Purpose, Methods, Properties, Relationships by reading the actual source file. Do not recreate stubs that already exist.

**Driven by `$FORGE_SCAN_TMP/forge_scan_types_all.txt`.** For every type in that file whose source file is in `$FORGE_SCAN_TMP/forge_scan_tier1.txt` or `$FORGE_SCAN_TMP/forge_scan_tier2.txt`, enrich the existing stub. Do NOT rely solely on in-context memory — the grep inventory is ground truth.

File path: `~/forge/brain/products/<slug>/codebase/classes/<role>-<ClassName>.md`

The `classes/` directory is what makes the Obsidian graph show class-level nodes connected to modules, to each other (via extends/implements), and to the directory structure. Without these files, the graph is a flat list of module nodes.

```markdown
# <TypeKind>: <ClassName>

> TypeKind: Class | Interface | Struct | Data Class | Sealed Class | Object | Enum | Trait | Protocol | Abstract Class

**Module:** [[modules/<role>-<module>]]
**File:** `<relative/path/from/repo/root>`
**Language:** <Java | Kotlin | Go | TypeScript | Python | Dart | Rust | ...>
**Layer:** <controller | service | repository | domain | entity | util | config | widget | bloc>
**Annotation / Decorator:** `@Service` / `@Injectable()` / `@Entity` / none

## Purpose

<One-sentence description — from the class docstring, comment block above the class, or synthesized from constructor params and method names>

## Constructor / Initialization

| Language | What to write |
|---|---|
| Java / Kotlin | `ClassName(Type param1, Type param2)` |
| Kotlin data class | `ClassName(val param1: Type, var param2: Type)` — constructor IS the property list |
| Go | `NewTypeName(dep1 *Dep1, dep2 *Dep2) *TypeName` (the `NewX` function, not a constructor keyword) |
| TypeScript | `constructor(private svc: ServiceType, readonly config: Config)` |
| Python | `__init__(self, param1: Type, param2: Type = default)` |

`<constructor signature for this class>`

## Methods

> For **Go**: methods come from `$FORGE_SCAN_TMP/forge_scan_methods_go.txt` — grep for `(* <TypeName>)` or `( <TypeName>)` receiver. They are NOT inside the struct definition.
> For all others: list public/exported methods only.

| Method | Signature | Notes |
|---|---|---|
| `<methodName>` | `<methodName>(<params>): <ReturnType>` | async / suspend / override |

## Properties / Fields

> For **Kotlin data class**: constructor params are the properties — copy from constructor.
> For **Go struct**: list fields from inside `type X struct { ... }` block.
> For **Java**: `private`/`protected` fields from class body.

| Property | Type | Notes |
|---|---|---|
| `<propName>` | `<type>` | readonly / lateinit / inject / json:"..." |

## Relationships

- **Extends:** [[classes/<role>-<ParentClass>]] *(omit line if none)*
- **Implements:** [[classes/<role>-<InterfaceName>]], [[classes/<role>-<InterfaceName2>]] *(omit if none)*
- **Embeds (Go):** [[classes/<role>-<EmbeddedStruct>]] *(Go composition — not inheritance)*
- **Sealed variants (Kotlin):** [[classes/<role>-<Subclass1>]], [[classes/<role>-<Subclass2>]] *(omit if not sealed)*
- **Used by:** [[modules/<role>-<consumer>]], [[modules/<role>-<consumer2>]]
- **Depends on:** [[classes/<role>-<Dependency>]] *(classes injected or composed)*

## Location in Structure

[[structure]] → `<directory/path>/` → [[modules/<role>-<module>]] → `<ClassName>`
```

**Skip a class if** it is a pure generated file (e.g. `*Generated.java`, `*_pb2.py`, Kotlin `*Binding` from Android View Binding) or a test-only class. Everything else gets a file — even simple data classes, because they are still graph nodes that other classes reference.

### 4.3d — Method nodes (script + optional rich layout)

**Auto (Phase 4 script):** the Phase 4 step in `tools/scan_forge` (`phase4.py`) writes **one** `methods/<role>-m-<cksum>.md` stub per line in `$FORGE_SCAN_TMP/forge_scan_methods_all.txt` — that is the **entire** Phase 1.6 method grep inventory, **not** filtered by Tier 1/2 hubs. Each stub links to `[[modules/...]]` by directory slug. Set `FORGE_PHASE4_SKIP_METHODS=1` to skip on huge repos.

**Manual enrich (optional):** For a hand-authored layout `methods/<role>-<ClassName>-<methodName>.md` (nicer titles), use the template below — you can replace or supplement `m-<cksum>` stubs after scan.

> **Why individual method files?** Method-level nodes enable relationship tracing that class-level nodes cannot: "which methods call this repository?", "what does `GetUser` delegate to?", "which handlers use this validation method?". Without method nodes, the graph stops at the class boundary and cross-cutting concerns are invisible.

File path: `~/forge/brain/products/<slug>/codebase/methods/<role>-<ClassName>-<methodName>.md`

**Naming convention:** `<role>-<ClassName>-<methodName>.md` — preserve class name casing, lowercase the method name only when the language convention requires it.
Examples: `backend-UserService-getUser.md`, `app-OrderBloc-fetchOrders.md`, `api-UserController-create.md`, `go-UserService-GetUser.md`

```markdown
# Method: <ClassName>.<methodName>

**Class:** [[classes/<role>-<ClassName>]]
**Module:** [[modules/<role>-<module>]]
**File:** `<relative/path/from/repo/root>:<line>`
**Language:** <Java | Kotlin | Go | TypeScript | Python | Dart | Rust>
**Visibility:** <public | protected | private | package-private | internal>
**Modifiers:** <static | async | suspend | override | abstract | final | inline> *(omit line if none)*

## Signature

> Write the signature for the language of this method. Use the language-specific block below:

```java
// Java
public ReturnType methodName(Type1 param1, Type2 param2) throws ExceptionType
```

```kotlin
// Kotlin
suspend fun methodName(param1: Type1, param2: Type2 = default): ReturnType
```

```go
// Go receiver method — NOT inside the struct, defined separately
func (u *ClassName) MethodName(ctx context.Context, param1 Type1) (ReturnType, error)
```

```ts
// TypeScript
async methodName(param1: Type1, param2?: Type2): Promise<ReturnType>
```

```python
# Python
async def method_name(self, param1: Type1, param2: Type2 = None) -> ReturnType:
```

## Parameters

| Parameter | Type | Notes |
|---|---|---|
| `<param>` | `<type>` | required / optional / default=X / nullable |

## Returns

`<ReturnType>` — <what it returns and under what conditions; "void" if none>

## Purpose

<One-sentence description from Javadoc/KDoc/TSDoc/docstring, or synthesized from name + params + return type>

## Called By

- [[methods/<role>-<CallerClass>-<callerMethod>]] — `<why it calls this>`
- [[functions/<role>-<callerFunction>]] — `<context>`
- [[modules/<role>-<module>]] — `<entry point if applicable>`

## Calls

- [[methods/<role>-<DependencyClass>-<dependencyMethod>]] — `<what it delegates to>`
- [[classes/<role>-<Dependency>]] — `<how it uses this class>`

## Location in Structure

[[structure]] → `<directory/path>/` → [[classes/<role>-<ClassName>]] → `<methodName>`
```

**When to create a method file:**
- Methods on **Tier 1 hub classes**: create for ALL public/exported methods — no exceptions
- Methods on **Tier 2 hub classes**: create for public methods with non-trivial bodies (skip trivial getters/setters that are one-liners)
- **Go receiver methods**: always create — they are the primary behavior of Go types and are NOT visible inside the struct definition. Use `$FORGE_SCAN_TMP/forge_scan_methods_go.txt` as the authoritative list
- **Kotlin `suspend fun`**: always create — async boundary is architecturally significant
- **Override methods implementing an interface**: always create — they are the fulfillment of a contract node
- **Private/internal methods**: skip unless clearly the core algorithm (named `execute`, `process`, `run`, `handle`, `validate`, `transform`)

**Language-specific skip rules:**
- **Java**: skip `getX()` / `setX()` unless they have side effects beyond field access
- **Kotlin data class**: skip `copy()`, `equals()`, `hashCode()`, `toString()` — auto-generated, no architectural value
- **Go**: skip `String()` (Stringer) and `Error()` (error interface) unless custom logic present; skip `init()`
- **Python**: skip `@property` accessors unless they have significant computation; skip `__init__` (covered by class Constructor section); skip `__str__`, `__repr__`, `__eq__`, `__hash__`
- **All languages**: skip auto-generated CRUD scaffolding methods when a code generator is detected (Hibernate-generated, GRPC stubs, Android ViewBinding)

### 4.3c — functions/<role>-<FunctionName>.md format

> **Stubs are auto-generated by the Phase 4 step in `tools/scan_forge` (`phase4.py`) (Step 4.0).** Your job here is to ENRICH stubs for Tier 1 and Tier 2 hub functions during hub reads.

**Driven by `$FORGE_SCAN_TMP/forge_scan_functions_all.txt`.** For every exported function in that file whose source file is in `$FORGE_SCAN_TMP/forge_scan_tier1.txt` or `$FORGE_SCAN_TMP/forge_scan_tier2.txt`, enrich the existing stub.

> This is the JS/TS/Python equivalent of `classes/`. In React, Next.js, Express, and most modern TS/JS codebases, the primary abstraction is the exported function — not the class. Without this directory, a React or Node codebase produces almost no graph nodes.

File path: `~/forge/brain/products/<slug>/codebase/functions/<role>-<functionName>.md`

```markdown
# Function: <functionName>

**Module:** [[modules/<role>-<module>]]
**File:** `<relative/path/from/repo/root>`
**Language:** TypeScript | JavaScript | Python
**Kind:** <React component | Custom hook | API handler | Service function | Utility | Next.js page | Middleware>
**Async:** yes | no

## Purpose

<One-sentence description from JSDoc/docstring, or synthesized from params and return type>

## Signature

```ts
// TypeScript / JavaScript
export function functionName(param1: Type1, param2: Type2): ReturnType
export const functionName = async (param: Type): Promise<ReturnType> => {}
export default function PageName({ prop }: Props): JSX.Element
```

```python
# Python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
async def function_name(param: Type) -> ReturnType:
```

## Parameters

| Parameter | Type | Notes |
|---|---|---|
| `<param>` | `<type>` | required / optional / default=X |

## Returns

`<ReturnType>` — <what it returns and when>

## Side Effects / Dependencies

> For React components: what hooks it uses, what context it reads
> For API handlers: what services/repos it calls
> For utility functions: none / describe if present

- Uses: [[functions/<role>-<usedHook>]], [[classes/<role>-<ServiceClass>]]
- Calls: [[modules/<role>-<dep>]]

## Used by

- [[modules/<role>-<consumer>]] — `<how it uses this function>`
- [[functions/<role>-<callerFn>]] — `<how it uses this function>`

## Location in Structure

[[structure]] → `<directory/path>/` → [[modules/<role>-<module>]] → `<functionName>`
```

**What counts as "significant" enough for its own file:**
- Any function that is the primary/only export of its file (React component files, hooks, page files)
- Any function called by 3+ other modules (visible in the import graph)
- Any function from a Tier 1 hub file
- Do NOT create a file for: internal helpers with no export, test utility functions, one-liner utils that have no parameters worth documenting

**For utility files with many small exports** (e.g. `utils/format.ts` with `formatDate`, `formatPrice`, `formatName`): list all exports in the module file's `## Exports` section instead. Only create individual function files for the ones referenced by 3+ other modules.

### 4.3e — pages/<role>-<PageName>.md format

> **Stubs are auto-generated by the Phase 4 step in `tools/scan_forge` (`phase4.py`) (Step 4.0).** Your job here is to ENRICH stubs for key UI pages during hub reads.

**Driven by `$FORGE_SCAN_TMP/forge_scan_ui_all.txt`.** For every HTML, Vue SFC, Svelte, and Angular template file found in Phase 1.6, the script has already created a stub. Enrich the ones for Tier 1 hub files. This gives every screen, form, and template its own navigable node in the Obsidian graph — enabling the full traversal: UI surface → JS/TS handler → API call → backend route.

> **Why page nodes?** Without page files, the frontend is invisible in the graph. Page nodes connect what the user sees to the functions that power it. The `pages/` → `functions/` → `modules/` edge chain is the most readable path through a full-stack system.

File path: `~/forge/brain/products/<slug>/codebase/pages/<role>-<PageName>.md`

**Naming:** Use the file stem (without extension), preserving original casing. For route-based directories (Next.js `pages/`, SvelteKit `routes/`), include the parent path segment to disambiguate same-named files.
Examples: `web-LoginPage.md`, `web-UserProfile.md`, `app-HomeScreen.md`, `web-checkout-index.md`, `web-auth-login.md`

```markdown
# Page: <PageName>

**File:** `<relative/path/from/repo/root>`
**Language / Format:** <HTML | Vue SFC | Svelte | Angular Template | JSX | TSX>
**Kind:** <page | component | layout | partial | template | screen | dialog>
**Route / URL:** `<path>` *(derive from filename for Next.js / SvelteKit / React Router)* | unknown

## Purpose

<One-sentence description of what this page/component renders and its role in the product>

## Key UI Elements

> Extracted from `$FORGE_SCAN_TMP/forge_scan_html_forms.txt` and `$FORGE_SCAN_TMP/forge_scan_html_ids.txt`.
> Do NOT read the full template file to populate this section — grep output is sufficient.

| Element | Type | ID / Selector | Notes |
|---|---|---|---|
| `<element description>` | form / button / input / nav / section / modal | `#<id>` or `[data-<attr>]` | <what user action this enables> |

## Forms

> From `$FORGE_SCAN_TMP/forge_scan_html_forms.txt`

| Form | Action / Handler | Method | Purpose |
|---|---|---|---|
| `<form context>` | `<action URL or @submit handler>` | GET / POST / onSubmit | <what this form does> |

## Script / Component Dependencies

> Functions and components this page uses — these wikilinks create graph edges into the `functions/` layer

- [[functions/<role>-<ComponentName>]] — `<how it's rendered on this page>`
- [[functions/<role>-<hookName>]] — `<what data/state it manages>`
- [[classes/<role>-<ServiceClass>]] — `<if page directly instantiates a class>`

## API Calls Made

> Cross-reference with [[api-surface]] — backend routes this page triggers (via its script dependencies)

- `GET /api/<path>` → [[modules/<backend-role>-<module>]] *(via [[functions/<role>-<hook>]])*
- `POST /api/<path>` → [[modules/<backend-role>-<module>]] *(via form submit / mutation)*

## Location in Structure

[[structure]] → `<directory/path>/` → `<PageName>.<html|vue|svelte|tsx>`
```

**What to write without reading the template file:**
- **File path, language, kind, route**: derivable from the path alone — no read needed
- **Key UI elements**: from `$FORGE_SCAN_TMP/forge_scan_html_forms.txt` (forms) and `$FORGE_SCAN_TMP/forge_scan_html_ids.txt` (IDs/data attributes)
- **Script / Component Dependencies**: cross-reference filenames in `$FORGE_SCAN_TMP/forge_scan_functions_all.txt` whose stem matches the page name or lives in the same directory
- **API Calls Made**: derive from the function nodes linked above — their `## Side Effects` sections contain the call info

**For HTML/Vue/Svelte templates:** stubs are already written by the script. Read the full template when enriching a page node — grep inventory gives you forms and IDs, but a full read reveals the component hierarchy, slot usage, and conditional rendering logic. If there are many template files, process in batches: enrich a set, commit, continue.

**For React `.tsx` / `.jsx` page files** (Next.js, Remix, CRA): The same file is captured as BOTH a `functions/` node (for the exported component function) AND a `pages/` node (for the UI surface). The two nodes are complementary — link them explicitly:
`**Component Function:** [[functions/<role>-<PageName>]]`

**For Vue SFCs** (`.vue`): The `<script>` block exports are captured in `functions/` or `classes/`. The `<template>` block is the UI surface captured here. Link: `**Vue Component Logic:** [[functions/<role>-<ComponentName>]]` or `[[classes/<role>-<ComponentName>]]`

### 4.3b — structure.md format

`structure.md` is the directory-tree backbone of the Obsidian graph. Every module and class node links back to it, giving the mindmap its hierarchy. Without this file the graph is a flat soup of nodes with no spatial structure.

File path: `~/forge/brain/products/<slug>/codebase/structure.md`

```markdown
# File Structure: <repo-name> (<role>)

> Directory hierarchy with links to module files. This is the map — navigate from here to any module or class.

## Repository Tree

> Written as a nested list — NOT a code block. Obsidian does not parse `[[wikilinks]]` inside fenced code blocks, so a code block tree produces zero graph edges.

- `<repo-name>/`
  - `<dir1>/` → [[modules/<role>-<dir1>]]
    - `<subdir1>/` → [[modules/<role>-<subdir1>]]
      - `<UserService>.java` → [[classes/<role>-<UserService>]]     *(class-based: Java/Kotlin/Go)*
      - `<UserCard>.tsx` → [[functions/<role>-<UserCard>]]           *(function-based: JS/TS component)*
      - `<useAuth>.ts` → [[functions/<role>-<useAuth>]]              *(hook)*
    - `<file>.ts` → [[modules/<role>-<stem>]]
  - `<dir2>/` → [[modules/<role>-<dir2>]]
    - `<file>.go` → [[modules/<role>-<stem>]]
  - `package.json` / `go.mod` / `pom.xml`
  - `README.md`

> Omit: `node_modules/`, `dist/`, `build/`, `__pycache__/`, `.git/`, test fixtures

## Directory Index

| Directory | Purpose | Modules |
|---|---|---|
| `<dir1>/` | <what this layer contains — e.g. "HTTP controllers"> | [[modules/<role>-<m1>]], [[modules/<role>-<m2>]] |
| `<dir2>/` | <e.g. "Business logic services"> | [[modules/<role>-<m3>]] |
| `<dir3>/` | <e.g. "Database access layer"> | [[modules/<role>-<m4>]] |

## Entry Points

| File | Module | Boots |
|---|---|---|
| `<path/to/main.ts>` | [[modules/<role>-<stem>]] | HTTP server on port <N> |
| `<path/to/worker.ts>` | [[modules/<role>-<stem>]] | Background job runner |

## Related

- [[index]] — Module map overview
- [[patterns]] — Architecture patterns
```

**How to write the tree:** Use the file inventory from Phase 1 (`$FORGE_SCAN_TMP/forge_scan_source_files.txt`) grouped by directory. Do not read additional files. Reconstruct the directory structure from the paths alone — you already have them.

### 4.4 — patterns.md format

```markdown
# Architecture Patterns

> Detected from import graph + framework signals. Unconfirmed patterns marked ⚠️.

## Confirmed Patterns

### <Pattern Name>
**Evidence:**
1. <Import graph signal>
2. <File structure signal>
3. <Framework/library signal>

**Implications for development:**
- <What this means for how to add a feature>
- <What this means for where to put new files>
- <What this means for testing strategy>

## Likely Patterns ⚠️

### <Pattern Name> (unconfirmed)
**Signals:** <why it might be this pattern>
**Counter-signals:** <why it might not be>
**Recommendation:** Confirm before planning new features — run `/scan` after reading 3-5 hub files fully.

## Anti-Patterns Detected

> These are problems, not features.

- **<Anti-pattern>** at `<location>` — <what makes it an anti-pattern>

## Related

- [[index]] — Module map
- [[modules/<relevant-hub>]] — Core structural file
```

### 4.5 — api-surface.md format

```markdown
# API Surface: <repo-name>

> Auto-extracted from route decorators and router patterns. Verify against actual implementation.

## REST Endpoints

| Method | Path | File | Handler |
|---|---|---|---|
| `GET` | `/api/users` | `<file:line>` | `<HandlerName>` |

## Event Schemas (if applicable)

| Event | Producer | Consumer | Schema |
|---|---|---|---|
| `<event.name>` | [[modules/<producer>]] | [[modules/<consumer>]] | `<type/shape>` |

## Exported SDK / Library Surface (if applicable)

| Symbol | Type | Description |
|---|---|---|
| `<name>` | function/class | <one-line description> |

## Related

- [[patterns]] — Architecture context
- [[modules/<main-router>]] — Main routing hub
```

### 4.6 — gotchas.md format

```markdown
# Codebase Gotchas

> Extracted from: test names, TODO/FIXME comments, HACK comments, documented edge cases.
> These are things that will bite you if you don't know about them.

## Edge Cases (from test names)

- `<test string>` — [[modules/<module>]]
- `<test string>` — [[modules/<module>]]

## Known Issues (from TODO/FIXME)

| Location | Severity | Note |
|---|---|---|
| `<file:line>` | TODO | `<comment>` |
| `<file:line>` | FIXME | `<comment>` |
| `<file:line>` | HACK | `<comment>` |

## Architectural Warnings

> Patterns that will cause bugs if misunderstood:

- **<Warning>** — `<where>` — <why it matters>

## Related

- [[patterns]] — Architecture patterns
- [[index]] — Module map
```

### 4.7 — Diff against prior scan (re-scan only)

When a `SCAN.json` already existed before this run (re-scan), compare **prior** `repos.<role>` (or legacy flat fields) with the new entry: `scanned_at`, `commit`, `source_files`, and module directory counts under `codebase/modules/`. Use `git log` between prior and current commit for the repo when helpful.

Write diff summary into `index.md` under a `## Changes Since Last Scan` section:

```markdown
## Changes Since Last Scan

> Prior scan: <prior-date> (commit <prior-sha>)
> This scan: <current-date> (commit <current-sha>)

- File count: <prior> → <current> (<delta>)
- Commits included: <N commits since prior scan>

### New Modules (files with 0 prior refs now appearing as hubs)
- `<new-module>` — first seen in this scan

### Removed Hubs (files that dropped below threshold)
- `<removed-module>` — no longer referenced by 3+ files

### API Surface Changes
- <N> new endpoints detected
- <N> endpoints no longer found (may have been removed or renamed)
```

This section is overwritten on every re-scan. First scans do not include this section.

### 4.8 — Commit after each project role

After the runner finishes (or after each logical batch), verify under `~/forge/brain/products/<slug>/codebase/`: `SCAN.json`, counts in `modules/`, `classes/`, `methods/`, `functions/`, `pages/`, plus `structure.md` and `api-surface.md` when expected. Commit the tree with a message that includes slug, role, and approximate node counts.

**If `classes/` has 0 files** and hub reads included class-bearing code: do NOT skip. Go back and extract at least the top 3-5 classes from the Tier 1 hubs. The `classes/` directory is mandatory for a meaningful Obsidian graph — flat module-only output does not produce a navigable mindmap.

**If `methods/` has 0 files** and the codebase has Java/Kotlin/Go/TypeScript classes: do NOT skip. Extract method nodes from at least the top 3 Tier 1 hub classes. Without method nodes, class-level graph traversal is a dead end.

**If `pages/` has 0 files** and the repo contains `.html`/`.vue`/`.svelte` files: do NOT skip. Write page nodes from `forge_scan_ui_all.txt` in `$FORGE_SCAN_TMP` — no additional file reads required.

**If `structure.md` is missing:** do NOT proceed to Phase 5 or commit. Write it now using the file paths already in `forge_scan_source_files.txt` under `$FORGE_SCAN_TMP` — no additional reads needed.

---

## Phase 5: Cross-Repo Relationship Layer (Multi-Repo Workspaces Only)

**Skip if workspace has only one repo.** Run after all individual repo scans are complete.

This phase identifies the architectural seams between repos — the contracts, shared types, and communication patterns that cross repo boundaries. This is the most valuable architectural data for multi-repo planning and the data most likely to be missing without an explicit scan phase.

**Correlation quality:** If `cross-repo.md` shows almost no `MATCHED` rows while the backend has hundreds of routes, verify (1) phase 3.5 (`scan_forge.phase35`) was run with **`append`** for every route-defining repo so **`forge_scan_api_routes.txt`** in `$FORGE_SCAN_TMP` is complete, and (2) **`forge_scan_fe_urls.txt`** is non-trivial after phase 5 (many SPAs use `$fetch`, `api.`, or quoted `/api/...` paths — phase 5 harvests those; dynamic template URLs still need manual rows).

### 5.1 – 5.5 prep — Cross-repo scan

**Already included** when you pass every repo on **`--repos`** in one `python3 tools/forge_scan.py` (or `PYTHONPATH=tools python3 -m scan_forge`) run. Phase 5 runs **once** after all per-repo phases. Read the console output for:
- Total call sites per language
- Shared type names appearing in 2+ repos
- Env variable names used across repos
- Event producers and consumers
- Count of unique URL paths extracted vs. dynamic URLs that need manual review

### 5.6 — Auto-patch module stubs (HARD-GATE for first-pass workspace/scan)

**No LLM, no “come back in Phase 5.5”.** Phase **56** (`tools/scan_forge/phase56.py`) runs automatically after phase 5 in the same `python3 tools/forge_scan.py` (or `PYTHONPATH=tools python3 -m scan_forge`) invocation.

**Prerequisites:** Phase 4 has created `*/modules/<role>-<dirslug>.md` files; `$FORGE_SCAN_TMP/forge_scan_api_routes.txt` lists **all** route-defining repos (correct `--repos` order); `$FORGE_SCAN_TMP/forge_scan_all_callsites.txt` comes from phase 5.

**What it does:** For each HTTP call line, extracts `/api…`, `/vN…`, `/graphql…`, `/rest…` fragments, finds a substring hit in a merged routes file (copy of `forge_scan_api_routes.txt` **plus** optional **`route-aliases.tsv`** in the brain parent — lines appended as extra `repo<TAB>path:line:…` rows, `#` comments and blank lines ignored), then **appends** idempotent blocks to caller and callee module files:

- Outgoing: markers `FORGE:AUTO_CROSS_REPO_OUT`
- Incoming: markers `FORGE:AUTO_CROSS_REPO_IN`

Also writes `cross-repo-automap.md` (TSV) at the codebase parent. **Re-run safe** — old auto blocks are stripped first.

**Limitations:** Heuristic substring match only (no OpenAPI diff). Dynamic/template URLs still need manual rows. Module layout must be `codebase/<role>/modules/` as produced by Phase 4.

### 5.7 — Validate `[[wikilinks]]` (optional, after Phase 4 / 5.6)

Pass **`--phase57-write-report`** to `python3 tools/forge_scan.py` (or `PYTHONPATH=tools python3 -m scan_forge`) (or omit **`--skip-phase57`**). Phase 57 (`tools/scan_forge/phase57.py`) writes **`wikilink-orphan-report.md`** at the codebase root when requested: orphan links plus **ambiguous basenames**. Without `--write-report`, the report is printed to stdout only.

### 5.1 – 5.5 — Reference (implementation)

Phases **5.1–5.5** are implemented in **`tools/scan_forge/phase5.py`**: per-language HTTP client call sites (grep-first), exported TypeScript types (with duplicate-line stats), environment-variable references, producer/consumer heuristics, URL literal harvest, and dynamic-URL flags. After the grep pass, **`tools/scan_forge/ast_http_calls.py`** optionally runs **Tree-sitter** across **many grammars** (Python, Go, Rust, Java, Kotlin, Ruby, C#, PHP, Swift, Lua, Zig, PowerShell, Elixir, ObjC, Julia, Verilog, C/C++, Scala, JS/TS — see `requirements.txt`) and appends extra lines to **`forge_scan_ast_http_calls.txt`** (merged into **`forge_scan_all_callsites.txt`** with the grep outputs) for HTTP-shaped calls grep often misses (e.g. **`api.get('/api/…')`**, **`session.get('/api/…')`**). Phase56 consumes the merged callsites file unchanged. Disable with **`FORGE_SCAN_AST=0`**. Extend **`phase5.py`** / **`ast_http_calls.py`** if you need new callee shapes or line heuristics.

**tRPC / gRPC:** Plain URL heuristics may not apply; document procedure/stub names in `cross-repo.md` manually when needed.

---
### 5.6 — Write cross-repo map

Write to `~/forge/brain/products/<slug>/codebase/cross-repo.md` using data from all prior Phase 5 steps. Include the route correlation table from 5.5.

```markdown
# Cross-Repo Relationships: <slug>

> Automatically extracted — verify against actual API contracts in brain/products/<slug>/contracts/

## Route Correlation Map (Caller Module → Backend Module)

> Built by joining Phase 3.5 (backend routes) with Phase 5.1 (call sites across all repos).
> Wikilinks here create the actual Obsidian graph edges — each `[[module]]` reference is a navigable node.
> `MATCHED` = confirmed route exists. `UNMATCHED` = broken contract. `ORPHAN` = backend route with no known caller.

| Status | Caller Module | Caller File:Line | Method + URL | Backend Module | Backend File:Line |
|---|---|---|---|---|---|
| ✅ MATCHED | [[web-useUser]] | `web/src/hooks/useUser.ts:34` | `GET /api/users/profile` | [[backend-users]] | `backend/src/routes/users.ts:18` |
| ✅ MATCHED | [[web-OrdersPage]] | `web/src/pages/orders.tsx:67` | `GET /api/orders/:id` | [[backend-orders]] | `backend/src/routes/orders.ts:42` |
| ✅ MATCHED | [[app-authClient]] | `app/lib/api/auth.dart:12` | `POST /api/auth/login` | [[backend-auth]] | `backend/src/routes/auth.ts:9` |
| ✅ MATCHED | [[consumer-service-UserClient]] | `consumer-service/src/client/UserClient.java:55` | `GET /api/users/:id` | [[core-backend-users]] | `core-backend/src/routes/users.ts:18` |
| ❌ UNMATCHED | [[web-legacy]] | `web/src/utils/legacy.ts:88` | `GET /api/v1/feed` | — | — |
| 🔍 ORPHAN | — | — | `GET /api/admin/metrics` | [[backend-admin]] | `backend/src/routes/admin.ts:7` |

### Broken Contracts (UNMATCHED — action required)

> These frontend calls have no matching backend route. Likely causes: route was renamed, removed, or never implemented.

- `web/src/utils/legacy.ts:88` → `GET /api/v1/feed` — no backend route matches. Check if renamed to `/api/v2/feed`.

### Orphan Routes (no known frontend caller)

> These backend routes have no detected frontend call site. May be internal, webhook-only, or dead code.

- `backend/src/routes/admin.ts:7` → `GET /api/admin/metrics` — no caller found in web or app repos.

---

## API Calls (Consumer → Provider)

> Covers ALL repos — microservice-to-microservice calls included.

| From | Language/Client | To | Pattern | Matched Routes | Unmatched |
|---|---|---|---|---|---|
| [[web]] | TypeScript / axios | [[backend]] | REST HTTP | 22/23 matched | 1 broken (`/api/v1/feed`) |
| [[app]] | Dart / Dio | [[backend]] | REST HTTP | 18/18 matched | 0 broken |
| [[consumer-service]] | Java / RestTemplate | [[core-backend]] | REST HTTP | 14/15 matched | 1 broken (`/api/v1/legacy`) |
| [[consumer-service]] | Java / Feign | [[core-backend]] | REST HTTP | 6/6 matched | 0 broken |
| [[order-service]] | Go / http.Get | [[inventory-service]] | REST HTTP | 4/4 matched | 0 broken |

## Shared Types

Types that appear in 2+ repos — these are implicit contracts. Each wikilink is a navigable module node.

| Type Name | Defined In | Used By |
|---|---|---|
| `User` | [[backend-types]] | [[web-useUser]], [[web-UserProfile]], [[app-authClient]] |
| `OrderStatus` | [[shared-types]] | [[backend-orders]], [[web-OrdersPage]], [[app-orderList]] |

> ⚠️ Shared types not in a shared package are a fragility risk — consider extracting to shared/

## Environment Variable Contracts

Variables that cross repo boundaries:

| Variable | Set By | Read By | Purpose |
|---|---|---|---|
| `API_BASE_URL` | infra/env | [[web]], [[app]] | Backend API root |
| `JWT_SECRET` | infra/env | [[backend]] | Auth token signing |

## Event Bus (Producer → Consumer)

| Event | Produced By | Consumed By | Channel |
|---|---|---|---|
| `order.created` | [[backend]] | [[backend]]/notifications | Kafka |

## Integration Risk Areas

> Patterns that are likely to cause cross-repo bugs:

- **Broken contracts** — `<N>` frontend call sites have no matching backend route. See "Broken Contracts" above.
- **Implicit type sharing** — `<type>` in [[repo-a]] and [[repo-b]] are different structs named the same. Risk: silent deserialization failure.
- **Direct URL hardcoding** — `<N>` call sites use hardcoded backend URL instead of `API_BASE_URL`. Risk: breaks on env change.
- **Missing consumer** — Event `<event>` is produced but no consumer found in any repo. Risk: silent data loss.
- **Orphan routes** — `<N>` backend routes have no frontend caller. Risk: dead code or undocumented internal API.

## Summary Stats

> Quick health check for cross-repo integration:

- Frontend call sites: <N total>
- Matched routes: <N> (<pct>%)
- Broken contracts (UNMATCHED): <N> ⚠️
- Orphan backend routes: <N>
- Shared types (implicit contracts): <N>
- Event producers: <N> | consumers: <N>

## Related

- [[index]] — Per-repo module maps
- [[patterns]] — Architecture patterns detected per repo
- [[api-surface]] — Full backend API surface
```

Commit after cross-repo layer: stage `cross-repo.md` (and related updates) under `~/forge/brain/products/<slug>/codebase/` with a message summarizing route correlation and contract health.

---

## Decision Trees

### Decision Tree 1: What to read for a given file

```
Is the file a README / ARCHITECTURE / CONTRIBUTING / ADR?
  → YES: Read fully (always)
  → NO:
      Is reference count ≥ 5?
        → YES (Tier 1 hub): Read in full (cat — no line limit)
        → NO:
            Is reference count 3-4?
              → YES (Tier 2 hub): Read in full (cat — no line limit)
              → NO (leaf file):
                  Is it a test file?
                    → YES: Extract test name strings only (grep, no Read)
                    → NO: Stub already exists from Phase 4 (`scan_forge.phase4`).
                          Read in batches to enrich — no file is skipped,
                          just prioritize hubs first. If doing full coverage,
                          read all leaf files in groups of 20-30, writing
                          enriched brain nodes after each group.
```

### Decision Tree 2: Pattern classification

```
Does import graph show ≥3 services importing a central "container" or "di" module?
  → YES: Dependency Injection / IoC pattern

Does every feature directory contain (controller + service + repository)?
  → YES: Layered architecture (controller → service → repository)

Does import graph show no cross-feature imports (features only import shared/)?
  → YES: Modular monolith / vertical slice

Do all routes live in one file and call functions from many modules?
  → YES: Centralized routing (common in Go, Flask)

Does the file structure have one directory per domain entity?
  → YES (and DI found): Domain-Driven Design signal

None of the above match cleanly?
  → Label as: "unclassified — recommend manual architecture review"
```

### Decision Tree 3: When a scan is stale

```
Does codebase/SCAN.json exist?
  → NO: Run full scan

Does SCAN.json exist?
  → YES: Read last-scanned timestamp
    Is it older than 7 days?
      → YES: Re-run Phase 1 (file inventory) to check for new files
        Are there new files (diff from SCAN.json file count)?
          → YES: Run full scan
          → NO: Scan is usable, note staleness in response

    Is it older than 30 days?
      → Always run full scan regardless of file count change
```

---

## Edge Cases

### Edge Case 1: Monorepo with 500+ files

**Symptom:** Phase 1 produces thousands of source files; hub scoring takes a moment on very large repos.

**Do NOT:** Cap or sample the file inventory — all stubs are generated by the Phase 4 step in `tools/scan_forge` (`phase4.py`) from the full inventory regardless of repo size. Never skip files.

**Mitigation:**
1. Phase 1 hub scoring is O(n) — it counts references per file from the already-extracted import graph, not by re-grepping the entire repo per file. Runs fast at any scale.
2. Phase 4: run the Phase 4 step in `tools/scan_forge` (`phase4.py`) as normal — it handles any number of files
3. For Phase 3 enrichment on very large repos (1000+ hub candidates): process in batches — read the first batch of hub files, write their brain nodes, then continue with the next batch. No file is skipped, just done in multiple passes.
4. Add `"monorepo": true` flag to SCAN.json

**Escalation:** NEEDS_CONTEXT — ask which subdirectory to focus on if repo has >3000 files and user wants deep enrichment on a specific area

---

### Edge Case 2: No test files found

**Symptom:** `$FORGE_SCAN_TMP/forge_scan_test_files.txt` is empty; gotchas.md has no test-derived content.

**Do NOT:** Fabricate edge cases or infer them from production code alone.

**Mitigation:**
1. Check for alternative test locations: `__tests__/`, `test/`, `spec/`, `integration/`
2. Try alternative naming patterns: `*_spec.rb`, `*IT.java`, `*Integration.java`
3. Check `package.json` test script for test directory config
4. If truly no tests: write `gotchas.md` with only TODO/FIXME content and a note: `> No test files found — edge cases may be undocumented.`

**Escalation:** DONE_WITH_CONCERNS — flag in index.md: "⚠️ No test files found"

---

### Edge Case 3: Private/generated import paths

**Symptom:** Import graph shows paths like `@app/`, `~/utils/`, `@/components/` that don't map to real directories.

**Do NOT:** Skip these imports or mark them as external dependencies.

**Mitigation:**
1. Check `tsconfig.json` paths aliases: `cat $REPO/tsconfig.json | grep -A5 '"paths"'`
2. Check `vite.config.*` or `webpack.config.*` aliases
3. Check `pyproject.toml` or `setup.py` for src-layout: `grep -E "src_dirs|packages|where" $REPO/pyproject.toml`
4. Resolve aliases before building module map — otherwise module relationships will be wrong

**Escalation:** NEEDS_CONTEXT if aliases cannot be resolved from config files

---

### Edge Case 4: Polyglot repo (multiple languages)

**Symptom:** Source file inventory finds both `.ts` and `.py` files, or `.go` and `.dart` files in the same repo.

**Do NOT:** Pick one language and ignore the other.

**Mitigation:**
1. Scan each language's import lines separately (language-specific grep patterns)
2. Create separate module maps per language layer in `modules/`
3. Look for cross-language communication points: REST calls, gRPC, shared JSON schemas
4. Document the boundary in `patterns.md` as "polyglot boundary"

**Escalation:** NEEDS_CONTEXT if cross-language calls cannot be identified from code alone

---

### Edge Case 5: No git repo in project directory

**Symptom:** `git -C $REPO rev-parse` fails; SCAN.json cannot get commit SHA.

**Do NOT:** Abort the scan.

**Mitigation:**
1. Set `"commit": "no-git"` in SCAN.json
2. Use file modification timestamps as scan version: `date -r <newest-file>`
3. Warn user in index.md: `> ⚠️ No git repository found — cannot track codebase version`

**Escalation:** DONE_WITH_CONCERNS

---

### Edge Case 6: Hub file is auto-generated

**Symptom:** Tier 1 hub file has a header like `// This file is auto-generated. Do not edit.` or `// Code generated by protoc`.

**Do NOT:** Read it as human-authored architecture. Generated files inflate hub scores.

**Mitigation:**
1. Detect generation markers: `grep -m1 "auto-generated\|DO NOT EDIT\|Code generated\|@generated" <file>`
2. Remove from hub lists: add to exclusion list
3. Note the generator in patterns.md: "API types generated by protoc from `<proto-file>`"

**Escalation:** None — handle silently, note in patterns.md

---

### Edge Case 7: Scan runs during /workspace init on a very new repo (few files)

**Symptom:** File inventory returns <10 files. Hub detection has no meaningful signal.

**Do NOT:** Produce an empty or near-empty brain scan.

**Mitigation:**
1. If <10 source files: skip Phases 1-2, read all files fully (they fit in one context window)
2. Write a `codebase/index.md` with note: `> Early-stage codebase — <10 source files. Full scan not needed.`
3. List all files in index.md as a flat inventory with one-line purpose per file
4. Set a reminder in index.md: `> Re-run /scan when codebase grows past 20 files.`

**Escalation:** None

---

## Common Pitfalls

1. **Scanning `node_modules/`** — always results in thousands of files and hub scores dominated by `index.js` files from npm packages. Exclusion pattern MUST be in every `find` command.

2. **Not resolving TypeScript path aliases** — `@/services/auth` looks like an external package but is `src/services/auth.ts`. Check `tsconfig.json` first.

3. **Treating test doubles/mocks as real modules** — `UserRepositoryMock.ts` will score high on incoming references in test files. Exclude `*.mock.*`, `*.stub.*`, `*.fake.*` from hub scoring.

4. **Writing module files for every file instead of every module** — A repo with 200 files does not need 200 module files. Group by directory/feature, not by file.

5. **Not committing SCAN.json before other brain files** — If the write fails mid-way, an incomplete scan with no metadata is worse than no scan. Commit SCAN.json first.

6. **Forgetting to clean up `forge_scan_*.txt` in the run directory** — Pass **`--cleanup`** to `python3 tools/forge_scan.py` (or `PYTHONPATH=tools python3 -m scan_forge`) to remove them after a successful run, or delete the temp run dir printed on stdout when you no longer need it.

---

## Quick Reference Card

| Phase | What | Implementation |
|---|---|---|
| 1.x | Inventory, hubs, tiers | `tools/scan_forge/phase1.py` (GNU `grep` where needed) |
| 3.4–3.5 | Test names + API routes | `tools/scan_forge/phase35.py` |
| 4 | Brain stubs + `SCAN.json` | `tools/scan_forge/phase4.py`, `scan_metadata.py` |
| 5–57 | Cross-repo, autolink, wikilinks | `phase5.py`, `phase56.py`, `phase57.py` |
| Cleanup | Remove `forge_scan_*.txt` in run dir | `tools/scan_forge/cleanup.py` via **`--cleanup`** |

**Token guidance:** No hard budget cap — read hub files fully. Phase 1 inventory is automated (no manual `find`/`awk` in the skill path). The token investment is in Phase 3 reads and Phase 4 writes, both of which produce permanent brain files that prevent future re-reads.

---

## Cross-References

- **Triggers:** Automatically after [[workspace]] init; manually via `/scan <slug> <repo-path>`
- **Produces:** Brain files consumed by [[brain-read]], [[brain-recall]], [[council-multi-repo-negotiate]]
- **Required before:** [[forge-eval-gate]] on an existing codebase (agent needs module map)
- **Related skills:** [[brain-write]], [[brain-read]], [[forge-brain-layout]]

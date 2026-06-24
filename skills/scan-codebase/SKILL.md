---
name: scan-codebase
description: "WHEN: You need to map an existing codebase into the Forge brain — building an Obsidian-format knowledge graph of module relationships, architecture patterns, API surface, and documented edge cases. Invoked automatically after /workspace init and manually via /scan."
type: rigid
requires: [brain-write]
version: 1.0.2
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

## Human input

This skill lists **`AskUserQuestion`** in **`allowed-tools`** — canonical for Claude Code and skill lint. Blocking prompts follow **[`skills/_shared/human-input.md`](../_shared/human-input.md)**. See **`using-forge`** **Interactive human input**.

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

## Iron Law

```
SCAN OUTPUT MUST BE VALIDATED BEFORE ANY TECH PLAN PROCEEDS.
structure.txt MUST BE WRITTEN AND COUNT-VERIFIED BEFORE EXITING PHASE 4.
INCREMENTAL SKIP (FORGE_SCAN_INCREMENTAL=1) APPLIES ONLY TO UNCHANGED ROLES — NEVER TO FIRST-TIME SCANS.
code-style.md ABSENCE IS NOT SILENT — FLAG AS UNKNOWN AND LOG TO CONDUCTOR.
```

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

**Problem:** `eval-product-stack-up` and deploy drivers read **`~/forge/brain/products/<slug>/forge-product.md`**. If every project lacks **`deploy_doc`** (path to run/deploy doc, relative to that repo) **and** lacks a usable **`start`** + **`health`**, agents guess — services fail to spawn and eval wastes cycles.

**HARD-GATE (workspace path):** When scan follows **`/workspace`** init, **`forge-product.md` must already satisfy `/workspace` Step 3b** (each project has `deploy_source` + `deploy_doc`, or `start`+`health`). Do not treat workspace-complete until Step 3b is done.

**When `/scan` runs later:** If `forge-product.md` is missing deploy fields, follow **`commands/scan.md` Step 1** — rediscover README/compose, ask once for paths or commands, update `forge-product.md`, then run `forge_scan.py`. **Blocking is allowed** until deploy fields exist — eval and stack-up are not optional for a “ready” product workspace.

**Optional brain artifact:** After a successful gate, you may add `codebase/DEPLOYMENT.md` summarizing per-role `deploy_doc` paths and health URLs for humans — keep **`forge-product.md`** the machine source of truth for stack-up.

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

**Consumer contract:** Phases that pick *where* to work (council, tech plans, semantic machine-eval targets, design notes) should read **`index.md`**, **`modules/*.md`**, **`api-surface.md`**, and **`SCAN.json` here first**, then open paths under the product clones. Do not use ad-hoc repo tree exploration as a substitute when this tree exists and is fresh; refresh with **`/scan <slug>`** if stale or absent.

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
| `--product-md <file>` | Optional — validates `role:` vs repo basename pairs in `forge-product.md` |
| `--skip-phase57` | Skip wikilink validation |
| `--phase57-write-report` | Write `wikilink-orphan-report.md` under the brain codebase parent |
| `--cleanup` | Remove `forge_scan_*.txt` in the run dir after success |
| `--incremental` | Use previous heads to compute changed paths and skip per-role phase1/3.5/4 when no scan-relevant files changed |

**Related environment flags (operator controls):**

- `FORGE_SCAN_INCREMENTAL=1` — same as passing `--incremental`
- `FORGE_SCAN_AST_IMPORTS=1` — emit `forge_scan_ast_import_edges.tsv` and include import-ref edges in `graph.json`

**When to use incremental vs full scan:**
- **Full scan** (`FORGE_SCAN_INCREMENTAL` unset or 0): first scan of a repo; after a major refactor (>20 files moved/renamed); after switching branches; after adding/removing dependencies.
- **Incremental scan** (`FORGE_SCAN_INCREMENTAL=1`): re-scan after small changes (1-5 files modified); adding a new function to an existing module; fixing a bug in an existing class. Incremental skips unchanged roles in phase1/3.5/4.
- **When in doubt, run full.** Incremental saves ~60% of scan time but may miss cross-role edge updates if interface files changed.

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
  [--product-md ~/forge/brain/products/<slug>/forge-product.md] \
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
2. Align **`role`** in `forge-product.md` with **`basename(repo path)`** for each project.
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

## Reference (load on demand)

Deep detail — worked examples, detailed section breakdowns, edge-case deep-dives, templates,
and decision trees — lives in **`reference/scan-formats-and-phases.md`** (Agent Skills progressive disclosure). This
SKILL.md is the operational contract: discipline, core workflow/decision logic, and checklists.

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

## Post-Implementation Checklist

- [ ] `codebase/<role>/structure.txt` written and line count matches `forge_scan_source_files.txt` line count (±0, not truncated).
- [ ] Hub score computed for all files with ≥ 20 source files (Edge Case 8 skip rule applied correctly).
- [ ] `code-style.md` written to brain for each scanned repo role (or absence flagged as UNKNOWN).
- [ ] `FORGE_SCAN_INCREMENTAL=1` used only for re-scans of unchanged roles (not first-time scans).
- [ ] Phase 4 integrity check passed: no source file from `forge_scan_source_files.txt` missing from structure.txt.

## Cross-References

- **Triggers:** Automatically after [[workspace]] init; manually via `/scan <slug> <repo-path>`
- **Produces:** Brain files consumed by [[brain-read]], [[brain-recall]], [[council-multi-repo-negotiate]]
- **Required before:** [[forge-eval-gate]] on an existing codebase (agent needs module map)
- **Related skills:** [[brain-write]], [[brain-read]], [[forge-brain-layout]]

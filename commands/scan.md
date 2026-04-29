---
name: scan
description: Map an existing codebase into the Forge brain. Produces an Obsidian-format knowledge graph — module relationships, architecture patterns, API surface, and documented edge cases. Zero-token structural phase first, targeted reads only for architectural hubs.
---

# /scan

**Forge plugin:** Invokes **`scan-codebase`** / **`forge_scan.py`**; outputs go under **`~/forge/brain/products/<slug>/codebase/`** (per skill). Not a substitute for **`/forge`** delivery. **`scripts/install.sh`** (Cursor + Claude Code) copies the full **`tools/`** tree into the plugin dir so **`classes/`**, **`methods/`**, and the rest of the pipeline run from an installed plugin — not module-only stubs from a missing scanner.

Build a codebase knowledge graph for the Forge brain. Works on any existing repo — no prior Forge setup needed. Produces navigable Obsidian markdown files that agents can query without re-reading source code.

## Usage

```
/scan                              # scan all repos in current workspace
/scan <slug>                       # scan all repos in workspace <slug>
/scan <slug> <role>                # scan one project role (backend | web | mobile | shared)
/scan <slug> <path>                # scan a specific repo path (overrides product.md)
/scan --refresh                    # force re-scan even if scan is <7 days old
```

---

## What You Must Do When Invoked

### Step 0 — Resolve target

**If no slug given:**
- Check if a workspace is open (look for `~/forge/brain/products/*/product.md`)
- If exactly one workspace exists → use it
- If multiple exist → list them and use a **blocking interactive prompt** per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** (**`AskQuestion`** / **numbered slugs + stop**)
- If none exist → use a **blocking interactive prompt** to choose: e.g. run **`/workspace`** now vs provide path — not only prose *Run `/workspace` first* with no same-turn choices

**If slug given:**
- Read `~/forge/brain/products/<slug>/product.md`
- Collect all `repo:` paths from the Projects section
- Verify each path exists: `ls <repo-path>` — warn if any are missing, skip them

**If a specific path is given (no slug match):**
- Treat as ad-hoc scan: use dirname as slug, don't require product.md
- Warn: "No product.md found — scanning as standalone repo. Brain output will be at `~/forge/brain/products/<dirname>/codebase/`"

---

### Step 1 — Deployment / runbook readiness (from `product.md`)

When `~/forge/brain/products/<slug>/product.md` exists, **read it before** invoking `scan-codebase` / `forge_scan.py`:

- For each `### <project>` block, check for **`deploy_doc`** (path relative to that project’s `repo:`) **or** a usable **`start`** + **`health`** pair.
- If **missing**: run the same README / `docker-compose` discovery as **`/workspace` Step 3b**. If still insufficient, **pause** the scan once, require a doc path or `start`/`health`, update `product.md`, then continue. **Do not** complete `/scan` for that slug while deploy fields are empty (same bar as workspace).

This keeps the first workspace pass authoritative while allowing `/scan --refresh` without repeating the whole wizard if `product.md` is already complete.

---

### Step 2 — Check for existing scan

```bash
cat ~/forge/brain/products/<slug>/codebase/SCAN.json 2>/dev/null
```

If scan exists and is <7 days old AND `--refresh` not passed:

```
Found existing scan for <slug>:
  Scanned: <date> (<N days ago>)
  Commit: <SHA>
  Files: <count> source, <count> test

Scan is recent. Use it? (yes / re-scan / scan only <role>)
```

If scan is >7 days old → proceed automatically with re-scan, note: "Scan is <N> days old — refreshing."

---

### Step 3 — Invoke scan-codebase skill

**REQUIRED SKILL:** Use `scan-codebase` skill for all phases.

Announce before starting:

```
Scanning <slug> codebase...

  Repos:
  → backend   ~/jh/backend
  → web        ~/jh/web
  → app        ~/jh/app

  Phase 1: Structural mapping (grep/find — no token cost)
  Phase 2: Hub detection
  Phase 3: Semantic enrichment (targeted reads only)
  Phase 4: Writing brain files
  Phase 5–5.7: Cross-repo prep + **phase56** auto-wikilinks on `modules/*.md` (multi-repo) + optional **phase57** wikilink audit (`wikilink-orphan-report.md`)

This will take 1-3 minutes per repo. Token budget: <15K per repo.
```

Run the scan-codebase skill for each project role. Process roles in this order:
1. `backend` first (most architecturally dense)
2. `shared` / `lib` (often imported by everything)
3. `web` / `mobile` (consumer layers)

**Runner (multi-repo — see `scan-codebase` SKILL):** one invocation with **`forge_scan.py`** and `--brain-codebase`, `--repos role:path …`, optional `--product-md`, optional `--phase57-write-report`, optional **`--cleanup`**, optional **`--incremental`** (or `FORGE_SCAN_INCREMENTAL=1`). Phases 1 → 3.5 → 4 → 5 → 56 → 57 run in order inside `tools/scan_forge/`; in incremental mode, unchanged roles may skip phase 1/3.5/4 and still regenerate summaries/manifest/state. See `tools/README.md`.

**Which `forge_scan.py`:** Prefer **`python3 tools/forge_scan.py`** when the workspace is a Forge git checkout and **`tools/forge_scan.py`** exists. Otherwise call the scanner from the merged plugin **`tools/`** tree (copied by **`install.sh`**):
- **Cursor:** `python3 "$HOME/.cursor/plugins/local/forge/tools/forge_scan.py"`
- **Claude Code:** under **`$HOME/.claude/plugins/cache/forge-plugin/forge/<version>/tools/forge_scan.py`** where **`<version>`** matches **`package.json`** in that directory (run **`ls ~/.claude/plugins/cache/forge-plugin/forge/`** if unsure).

Optional equivalent: **`PYTHONPATH=$HOME/.cursor/plugins/local/forge/tools python3 -m scan_forge`** (adjust **`PYTHONPATH`** to the same **`tools`** directory you used for **`forge_scan.py`**).

Hand verification uses the same prefix: **`python3 …/tools/verify_scan_outputs.py ~/forge/brain/products/<slug>/codebase`**.

---

### Step 3b — Verify consolidated outputs (HARD-GATE)

**Built-in:** `python3 tools/forge_scan.py` / `python3 -m scan_forge` already runs **`verify_brain_codebase`** with **3 retries** after writing **`index.md`** (unless `FORGE_SCAN_SKIP_VERIFY=1`). Inspect **`run.json`** in the printed **`run_dir`**: expect **`"status": "ok"`** and **`verify_scan_outputs.exit_code": 0`**. If **`status": "verify_failed"`**, the CLI exited **non-zero** — **do not** announce completion; triage `run_dir` (cleanup was skipped so `forge_scan_*.txt` remain).

**Agent belt-and-suspenders (max 3 shell attempts, 1s sleep between):** Until `verify_scan_outputs.py` exits **0**:

```bash
python3 tools/verify_scan_outputs.py ~/forge/brain/products/<slug>/codebase
```

- **If this fails after 3 tries:** Do **not** print “scan complete.” Full re-scan: **fresh `--run-dir`**, correct **`--brain-codebase`**, **`backend` first** in `--repos`, install scan deps if needed, then Step 3b again. Log `[SCAN-VERIFY] status=FAIL` with the last script stdout.
- **If OK:** Log `[SCAN-VERIFY] status=OK` and continue to Step 4.

**Incremental artifacts to inspect when `--incremental` is used:**

- `<run_dir>/changed_paths.txt` — role-scoped changed paths selected for this run.
- `<brain-codebase>/.forge_scan_file_state.json` — per-role `head`, `tree`, tracked blob SHAs, untracked relevant files.
- `<brain-codebase>/.forge_scan_manifest.json` — includes incremental metadata and changed-path sample.
- `<run_dir>/run.json` (`incremental.phase5_56_mode`, `incremental.phase5_56_reason`) — explains why cross-repo recompute ran or was skipped.

**Incremental fallback guidance (conservative by default):**

- If any role is `full_fallback`, treat the run as low-confidence and expect full phase5/56 recompute.
- If `phase5_56_mode=skipped_by_profile`, verify `graph.json` and `cross-repo-automap.md` still exist from prior full runs.
- If `phase5_56_mode=run_full_fallback`, it indicates state uncertainty (for example, missing previous head) and is expected.

---

### Step 4 — Show results

After scan completes:

```
Scan complete: <slug>

  brain/products/<slug>/codebase/
  ├── index.md            (architecture: <detected-style>, <N> modules)
  ├── SCAN.json           (committed <ISO timestamp>)
  ├── modules/
  │   ├── auth.md         (Tier 1 hub — referenced by 12 files)
  │   ├── database.md     (Tier 1 hub — referenced by 8 files)
  │   └── ...             (<N> total modules)
  ├── patterns.md         (<N> patterns detected)
  ├── api-surface.md      (<N> endpoints)
  ├── gotchas.md          (<N> edge cases, <N> TODOs)
  └── cross-repo.md       (<N> routes correlated, <N> broken contracts, <N> shared types)  ← multi-repo only

Token usage: ~<N>K tokens (<well-within budget> / over budget — see concerns below)

Ready to plan? Run: /intake
```

**Optional post-scan analysis tools (no change to HARD-GATE):**

- Local search over brain artifacts: `python3 tools/forge_codebase_search.py --brain-codebase <codebase> --query "auth middleware"`
- SQL on regenerated edge store: `python3 -m scan_forge.query_repl --brain-codebase <codebase> --sql "select kind,count(*) from edges group by kind"`
- Import edge extraction (opt-in at scan time): `FORGE_SCAN_AST_IMPORTS=1 python3 tools/forge_scan.py ...`
  - Provenance tiers in `forge_scan_ast_import_edges.tsv`: `AST_STRONG`, `AST_WEAK`, `HEURISTIC`
  - `graph.json` import edges include confidence-qualified rows only (`AST_STRONG`/`AST_WEAK`)
- Benchmark gates/report: `python3 tools/scan_bench.py --output-json tools/scan_bench.ci.json --output-md tools/scan_bench.ci.md`

**On re-scan, also show a diff summary:**

```
Changes since last scan (<N> days ago, commit <prior-sha> → <current-sha>):
  → File count: 184 → 201 (+17 new source files)
  → New hubs:   notification-service (6 refs)
  → Dropped:    legacy-auth (2 refs — below threshold)
  → API changes: +3 endpoints, -1 endpoint
  → Commits:    8 commits since prior scan
```

If no changes detected (same file count, same commit SHA):
```
  No structural changes detected since last scan.
  SCAN.json timestamp updated.
```

If over token budget (>15K):
```
⚠️  Token budget exceeded (<N>K tokens used)
    Likely cause: repo has >300 source files or path aliases were not resolved
    Recommendation: run /scan <slug> <role> to scan one role at a time
```

---

### Step 5 — Auto-trigger context (from /workspace)

When `/scan` is invoked automatically at the end of `/workspace` init:

- Do NOT show the usage prompt
- DO show a minimal status line: "Scanning codebase... (run /scan --refresh to redo)"
- Run all phases silently
- After completion, append to the workspace-complete confirmation:

```
  Codebase scan: ✅ complete
  → brain/products/<slug>/codebase/ (use /recall to query)
```

---

## Principles

- **Evidence is what / where / how** — when you report scan outcomes in chat or docs, cite **paths**, **`SCAN.json` / `index.md` anchors**, and **how** each fact was produced (phase artifact, command + cwd). Do not substitute headline counts or **"N+"** for that detail (see **AGENTS.md** — *Written artifacts — precision*).
- **Grep first, read second.** Structural relationships are free. File bodies are expensive.
- **Hubs only.** Read top-N lines of files referenced by 3+ other modules. Nothing else.
- **Obsidian format.** Every output file uses `[[wikilinks]]`. The brain is navigable by humans and agents alike.
- **Per-role commits.** Commit brain files after each role completes — never batch all roles into one commit.
- **Token budget is a hard limit.** If you exceed 15K tokens per repo, the scan is broken. Stop and report why.
- **Stale is honest.** Always show `last-scanned:` in index.md. Never present a stale scan as current.

---
name: scan
description: Map an existing codebase into the Forge brain. Produces an Obsidian-format knowledge graph — module relationships, architecture patterns, API surface, and documented edge cases. Zero-token structural phase first, targeted reads only for architectural hubs.
trigger: /scan
---

# /scan

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
- If multiple exist → list them and ask which
- If none exist → ask: "No workspace found. Run `/workspace` first to set one up."

**If slug given:**
- Read `~/forge/brain/products/<slug>/product.md`
- Collect all `repo:` paths from the Projects section
- Verify each path exists: `ls <repo-path>` — warn if any are missing, skip them

**If a specific path is given (no slug match):**
- Treat as ad-hoc scan: use dirname as slug, don't require product.md
- Warn: "No product.md found — scanning as standalone repo. Brain output will be at `~/forge/brain/products/<dirname>/codebase/`"

---

### Step 1 — Check for existing scan

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

### Step 2 — Invoke scan-codebase skill

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

**Script order (multi-repo — see `scan-codebase` SKILL):** optional `validate-product-roles.sh` on `product.md` → per repo `phase1-inventory.sh` → `phase35-extract.sh` (first routes run **without** `append`, later repos **with** `append`) → per repo `phase4-brain-write.sh` (pass `ROLE` = basename of that repo path) → once `phase5-cross-repo.sh` → once `phase56-autolink-crossrepo.sh` → optional `phase57-validate-brain-wikilinks.sh --write-report` → **`cleanup.sh`** to clear `/tmp/forge_scan_*.txt`.

---

### Step 3 — Show results

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

### Step 4 — Auto-trigger context (from /workspace)

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

- **Grep first, read second.** Structural relationships are free. File bodies are expensive.
- **Hubs only.** Read top-N lines of files referenced by 3+ other modules. Nothing else.
- **Obsidian format.** Every output file uses `[[wikilinks]]`. The brain is navigable by humans and agents alike.
- **Per-role commits.** Commit brain files after each role completes — never batch all roles into one commit.
- **Token budget is a hard limit.** If you exceed 15K tokens per repo, the scan is broken. Stop and report why.
- **Stale is honest.** Always show `last-scanned:` in index.md. Never present a stale scan as current.

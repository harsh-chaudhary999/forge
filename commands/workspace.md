---
name: workspace
description: Initialize or open a Forge workspace. Point it at any folder — it scans for git repos, infers roles from folder names, detects languages, and builds product.md automatically. No manual config needed.
trigger: /workspace
---

# /workspace

Set up a Forge workspace by scanning an existing folder structure. Works with any layout — Forge detects git repos, infers roles, and auto-detects languages. Only asks what it cannot figure out itself.

## Usage

```
/workspace                          # scan current directory
/workspace <path>                   # scan a specific folder (e.g. /workspace ~/jh)
/workspace open <slug>              # open an existing workspace
/workspace list                     # list all workspaces in brain
/workspace add-repo <slug>          # add a repo to an existing workspace
/workspace add-infra <slug>         # fill in DB/cache/ports when ready for eval
```

---

## What You Must Do When Invoked

### Step 0 — Check if a path or subcommand was given

- If subcommand (`open`, `list`, `add-repo`, `add-infra`) → jump to the relevant step
- If a path was given → use that path as the scan root
- If no path → use current directory (`.`) as scan root
- Before scanning, check if workspaces already exist:

```bash
ls ~/forge/brain/products/ 2>/dev/null
```

If workspaces exist, show them and ask: **"Set up a new workspace or open an existing one?"**

---

### Step 1 — Scan the folder for git repos

```bash
# Find all git repos within the given path (up to 3 levels deep)
find <path> -maxdepth 3 -name ".git" -type d 2>/dev/null | sed 's|/.git||'
```

For each repo found, collect:

```bash
# Get remote URL
git -C <repo-path> remote get-url origin 2>/dev/null || echo "(no remote)"

# Get current branch
git -C <repo-path> branch --show-current 2>/dev/null || echo "main"

# Detect language and framework (run all, use what matches)
ls <repo-path>/package.json        && echo "node"
ls <repo-path>/requirements.txt    && echo "python"
ls <repo-path>/go.mod              && echo "go"
ls <repo-path>/Cargo.toml          && echo "rust"
ls <repo-path>/pubspec.yaml        && echo "dart/flutter"
ls <repo-path>/pom.xml             && echo "java"
ls <repo-path>/build.gradle        && echo "kotlin/java"
ls <repo-path>/Gemfile             && echo "ruby"

# Detect framework from package.json if present
cat <repo-path>/package.json 2>/dev/null | grep -E '"next"|"react-native"|"express"|"fastify"|"nestjs"|"vue"|"nuxt"|"svelte"'
```

---

### Step 2 — Infer role from folder name

Apply this mapping automatically — no need to ask if the name is unambiguous:

| Folder name contains | Inferred role |
|---|---|
| `backend`, `api`, `server`, `service`, `core` | `backend` |
| `web`, `frontend`, `dashboard`, `portal`, `admin` | `web` |
| `app`, `mobile`, `android`, `ios`, `native` | `mobile` |
| `shared`, `common`, `lib`, `packages`, `sdk` | `shared` |
| `infra`, `devops`, `deploy`, `k8s`, `terraform` | `infra` |

If the folder name is ambiguous (e.g. `src`, `code`, `main`), ask once:
**"What role does `<folder-name>` play — backend, web, mobile, shared, or infra?"**

---

### Step 3 — Show what was detected and confirm

Present a summary before creating anything:

```
Detected the following repos in ~/jh:

  backend/    → role: backend  | node + express  | branch: main  | github.com/org/jh-backend
  web/        → role: web      | typescript + next | branch: main | github.com/org/jh-web
  app/        → role: mobile   | dart + flutter  | branch: main  | github.com/org/jh-app

Does this look right? (yes / correct something)
```

If the user corrects something, apply it before continuing. Do not re-scan — just update the specific field they corrected.

---

### Step 4 — Ask only what cannot be detected

After scan, ask **only** what is missing and cannot be inferred:

1. **Product name** — if not obvious from folder name or repo names
   - e.g. `jh` → ask "Is this JobHai? What should we call it?"
   - e.g. `my-startup-backend` → infer "my-startup", confirm

2. **Role clarification** — only for ambiguous folder names (see Step 2)

That's it. Do NOT ask about ports, DB credentials, frameworks, or merge order.

---

### Step 5 — Create product.md

Generate `~/forge/brain/products/<slug>/product.md` from the scan results:

```markdown
# Product: <Detected or Confirmed Name>

## Identity
- slug: <slug>
- description: (add a one-line description — or run /intake to define it)
- primary owner: (your team)

## Projects

### backend
- repo: ~/jh/backend
- remote: https://github.com/org/jh-backend
- role: backend
- language: node
- framework: express
- branch: main

### web
- repo: ~/jh/web
- remote: https://github.com/org/jh-web
- role: web
- language: typescript
- framework: next
- branch: main

### app
- repo: ~/jh/app
- remote: https://github.com/org/jh-app
- role: mobile
- language: dart
- framework: flutter
- branch: main

## Infrastructure
# ── Optional — only needed for DB/cache/queue-dependent eval scenarios ──
# Run: /workspace add-infra <slug>
#
# Forge will ask about DB, cache, message bus, and ports at that point.
# You do not need this to run /intake, /council, /plan, or even /eval.
# Eval scenarios requiring unconfigured infra are marked N/A, not failed.

## Merge Order
# Determined during /council — leave blank for now
```

Then confirm and auto-trigger codebase scan:

```
✅ Workspace created: ~/forge/brain/products/<slug>/product.md

   3 repos registered:
   → backend  (~/jh/backend)
   → web      (~/jh/web)
   → app      (~/jh/app)

   Infrastructure: not configured (optional — add with /workspace add-infra <slug>)
```

### Step 5a — Bootstrap brain as Obsidian vault (first time only)

Obsidian expects a **complete** `.obsidian/` folder, not only `app.json` + `graph.json`. Missing `workspace.json`, `core-plugins.json`, or `appearance.json` often makes “Open folder as vault” fail, show a blank window, or refuse to treat the folder as a vault. The Forge `brain-template/.obsidian/` ships all five files; **Sync is off** in `core-plugins.json` so the brain is not mistaken for a Sync-linked vault.

Check whether the vault skeleton is already present (all required files):

```bash
for f in app.json graph.json workspace.json core-plugins.json appearance.json; do
  [ -f "$HOME/forge/brain/.obsidian/$f" ] || echo "missing: $f"
done
```

If **any** of those files is missing, run the full bootstrap below (copy the whole template set). This upgrades older brains that only had `app.json` + `graph.json`.

**Step 5a.1 — Ensure brain is a git repo:**

```bash
git -C ~/forge/brain status 2>/dev/null || (
  git -C ~/forge/brain init
  cat > ~/forge/brain/.gitignore << 'EOF'
.DS_Store
*.tmp
EOF
  git -C ~/forge/brain add .gitignore
  git -C ~/forge/brain commit -m "chore: initialize brain git repo"
)
```

**Step 5a.2 — Copy Obsidian config from Forge template:**

```bash
FORGE_DIR=$(find ~/.claude/plugins ~/.cursor/plugins ~/.cursor/plugins/local ~/.config/gemini/plugins \
  -path "*/forge/brain-template" -type d 2>/dev/null | head -1 | sed 's|/brain-template||')
# Fallback: common direct clone locations (covers a forge git clone without plugin layout)
[ -z "$FORGE_DIR" ] && FORGE_DIR=$(find ~/forge ~/Videos/forge -maxdepth 1 -name "brain-template" -type d 2>/dev/null | head -1 | sed 's|/brain-template||')

mkdir -p ~/forge/brain/.obsidian
OBS_TPL="$FORGE_DIR/brain-template/.obsidian"
cp "$OBS_TPL/app.json"            ~/forge/brain/.obsidian/app.json
cp "$OBS_TPL/graph.json"         ~/forge/brain/.obsidian/graph.json
cp "$OBS_TPL/workspace.json"     ~/forge/brain/.obsidian/workspace.json
cp "$OBS_TPL/core-plugins.json"  ~/forge/brain/.obsidian/core-plugins.json
cp "$OBS_TPL/appearance.json"    ~/forge/brain/.obsidian/appearance.json
```

**Step 5a.3 — Write README.md with wikilinks (hub for graph):**

Write `~/forge/brain/README.md` with `[[wikilink]]` references to the key subdirectories. This creates graph edges so the vault opens with a connected structure, not isolated nodes. Use links pointing to files that actually exist in the brain.

**Step 5a.4 — Commit:**

```bash
git -C ~/forge/brain add .obsidian/ README.md
git -C ~/forge/brain commit -m "chore: initialize brain as Obsidian vault"
```

**Output:**
```
✅ Brain initialized as Obsidian vault
   Open in Obsidian: File → Open vault → ~/forge/brain
```

If **all** of `app.json`, `graph.json`, `workspace.json`, `core-plugins.json`, and `appearance.json` already exist under `~/forge/brain/.obsidian/`, skip Step 5a.2 silently (still run 5a.1 / 5a.3 / 5a.4 as needed for git and README).

**Troubleshooting (vault still won’t open):** Fully quit Obsidian and open **exactly** `~/forge/brain` (the folder containing `README.md`, `products/`, and `.obsidian/` — not `products/<slug>`). Flatpak/Snap sandboxes may block paths under `~/forge/`; grant filesystem access (Flatseal) or use AppImage/deb, or on Windows + WSL use `\\wsl$\…\forge\brain`.

**Obsidian URIs / `xdg-open` “unable to find vault or the path”:**

- `obsidian://open?path=…` — `path` must be an **absolute path to a markdown file inside** the vault (Obsidian resolves the vault as an ancestor of that file). Using `path=` for the vault directory alone is invalid.
- Prefer `obsidian://open?vault=<vaultId>&file=<relative/note.md>` where `vaultId` is listed in `~/.config/obsidian/obsidian.json`. Per-vault UI state lives in `~/.config/obsidian/<vaultId>.json`; if that file is missing you can see ENOENT until you open the vault once in Obsidian or seed a minimal JSON like another vault’s sibling file.
- That config lives under **the user’s home directory**, not in `~/forge/brain/` — the Forge plugin does not ship or modify it.

**Repair an existing brain that only has partial `.obsidian/` (one-liner):**

```bash
FORGE_DIR="$(find ~/.cursor/plugins ~/.cursor/plugins/local ~/.claude/plugins ~/.config/gemini/plugins \
  -path '*/forge/brain-template' -type d 2>/dev/null | head -1 | sed 's|/brain-template||')"
BT="$FORGE_DIR/brain-template/.obsidian"
mkdir -p ~/forge/brain/.obsidian
cp "$BT/"{app.json,graph.json,workspace.json,core-plugins.json,appearance.json} ~/forge/brain/.obsidian/
```

(Adjust `FORGE_DIR` if your canonical Forge checkout lives outside plugin caches.)

---

### Step 5b — Auto-scan all repos (REQUIRED after product.md is created)

**REQUIRED SKILL:** Invoke `scan-codebase` skill for each registered repo automatically.
Do NOT wait for the user to ask — the codebase map is needed for planning.

**Multi-repo HARD-GATE (first pass):** Use **`python3 tools/forge_scan_run.py`** with **every** `--repos` entry so phase 5 and **phase56** (`tools/scan_forge/phase56.py`) run against `~/forge/brain/products/<slug>/codebase` and fill module `## Calls (cross-repo)` / `## Called By` from the run-dir artifacts — no deferred “Phase 5.5 manual patch” unless the user wants refinements.

**Optional (recommended after first brain write):** Pass **`--phase57-write-report`** so phase57 emits `wikilink-orphan-report.md` — orphan `[[wikilinks]]` and ambiguous basenames.

**Optional before Phase 4:** Pass **`--product-md ~/forge/brain/products/<slug>/product.md`** so built-in role validation ensures each project’s `- role:` matches the basename of its `- repo:` path (phase4 / phase56 assume they are equal).

**After the run:** Pass **`--cleanup`** or delete the temp run directory printed on stdout so `forge_scan_*.txt` files in that directory are not reused accidentally.

Run silently (no verbose output), announce progress briefly:

```
Scanning codebase... (grep/find phase — no token cost)
  → backend: 184 source files, 6 hubs detected
  → web: 312 source files, 9 hubs detected
  → app: 89 source files, 4 hubs detected

Writing brain files...
```

After scan completes, show final confirmation:

```
✅ Workspace ready: <slug>

   3 repos registered and scanned:
   → backend  (~/jh/backend)  → brain/products/<slug>/codebase/
   → web      (~/jh/web)      → brain/products/<slug>/codebase/
   → app      (~/jh/app)      → brain/products/<slug>/codebase/

   Infrastructure: not configured (optional — add with /workspace add-infra <slug>)
   Codebase scan: ✅ done (re-run any time: /scan <slug>)
   Cross-repo module links: ✅ phase56 (if multi-repo)
   Wikilink audit: optional `--phase57-write-report` → `wikilink-orphan-report.md`
   Run-dir cleanup: optional `--cleanup` on `forge_scan_run.py`

   Ready to start planning? Run: /intake
```

---

### Step 6 — Open existing workspace (`/workspace open <slug>`)

```bash
cat ~/forge/brain/products/<slug>/product.md
```

Read `SCAN.json` to get scan age:

```bash
cat ~/forge/brain/products/<slug>/codebase/SCAN.json 2>/dev/null
```

Show a summary:

```
📁 Workspace: <name> (<slug>)

   Repos:
   → backend   ~/jh/backend    (node + express)
   → web       ~/jh/web        (typescript + next)
   → app       ~/jh/app        (dart + flutter)

   Infrastructure: not configured (optional) — add with /workspace add-infra <slug> for DB/cache eval

   Codebase scan:
   → Last scanned: 3 days ago (commit a1b2c3d)    ← if scan exists and fresh
   → ⚠️  12 days old — refresh before next council: /scan <slug>   ← if stale (7-30 days)
   → ❌  No scan found — run /scan <slug> to map codebase         ← if no scan

   Brain activity:
   → PRDs: 2 locked
   → Last decision: D004 (3 days ago)
```

Then ask: **"What would you like to do?"**
- Start a new feature → `/intake`
- Look up past decisions → `/recall`
- Configure optional DB/cache infra → `/workspace add-infra <slug>`
- Check full status → `/forge-status`

---

### Step 7 — add-infra (`/workspace add-infra <slug>`)

Only triggered when the user explicitly wants to configure DB/cache/queue for eval. Infra is optional — eval runs without it (infra-dependent scenarios are marked N/A, not failed). Ask one at a time:

1. **"What database?"** — MySQL / PostgreSQL / MongoDB / SQLite / none
2. **"What cache?"** — Redis / Memcached / none
3. **"What message bus?"** — Kafka / RabbitMQ / none
4. **"Port for each service?"** — ask per repo, suggest common defaults (3000, 3001, 8080)
5. **"How do you start each service?"** — suggest `npm start`, `python -m uvicorn`, `go run .`, etc. based on detected language

Update `product.md` Infrastructure section in-place. Never rewrite the whole file.

---

### Step 8 — add-repo (`/workspace add-repo <slug>`)

1. Ask: **"Path or GitHub URL of the new repo?"**
2. Auto-detect language, framework, branch
3. Ask role only if ambiguous
4. Append to `product.md` Projects section
5. Ask: **"Does the merge order need updating?"**

---

## Auto-Detection Reference

| File found | Language | Framework |
|---|---|---|
| `package.json` + `"next"` | TypeScript/JS | Next.js |
| `package.json` + `"react-native"` | TypeScript/JS | React Native |
| `package.json` + `"express"` | Node.js | Express |
| `package.json` + `"nestjs"` | Node.js | NestJS |
| `package.json` + `"fastify"` | Node.js | Fastify |
| `pubspec.yaml` | Dart | Flutter |
| `requirements.txt` + `fastapi` | Python | FastAPI |
| `requirements.txt` + `django` | Python | Django |
| `requirements.txt` + `flask` | Python | Flask |
| `go.mod` | Go | (check for gin, echo, fiber) |
| `Cargo.toml` | Rust | (check for actix, axum) |
| `pom.xml` | Java | Spring |
| `build.gradle` | Kotlin/Java | Spring / Android |
| `Gemfile` + `rails` | Ruby | Rails |

---

## Principles

- **Scan first, ask second.** Never ask for something Forge can detect from the filesystem or git.
- **One question at a time.** No forms. No YAML to fill in.
- **Any folder structure works.** `jh/backend`, `projects/myapp/api`, `~/code/backend` — all the same.
- **Infra is eval-time only.** Intake, council, and plan work without a single infra detail.
- **Never overwrite existing product.md without confirmation.** If one already exists for the slug, show diff and ask.

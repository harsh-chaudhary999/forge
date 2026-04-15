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
# ── Add when ready for eval ──────────────────────────────────────────
# Run: /workspace add-infra <slug>
#
# Forge will ask about DB, cache, message bus, and ports at that point.
# You do not need this to run /intake, /council, or /plan.

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

   Infrastructure: not configured yet (add before /eval)
```

### Step 5b — Auto-scan all repos (REQUIRED after product.md is created)

**REQUIRED SKILL:** Invoke `scan-codebase` skill for each registered repo automatically.
Do NOT wait for the user to ask — the codebase map is needed for planning.

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

   Infrastructure: not configured yet (add before /eval)
   Codebase scan: ✅ done (re-run any time: /scan <slug>)

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

   Infrastructure: ⚠️  not configured — run /workspace add-infra <slug> before /eval

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
- Configure infra for eval → `/workspace add-infra <slug>`
- Check full status → `/forge-status`

---

### Step 7 — add-infra (`/workspace add-infra <slug>`)

Only triggered when the user is ready to run `/eval`. Ask one at a time:

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

---
name: workspace
description: Initialize or open a Forge workspace from existing repos. Minimal setup — just repos and roles. Infrastructure details added later when needed for eval.
trigger: /workspace
---

# /workspace

Set up a Forge workspace from your existing repos. Only asks what's needed to start planning. Infrastructure (DB, cache, ports) is added later when you run `/eval`.

## Usage

```
/workspace                        # create new workspace interactively
/workspace open <slug>            # open existing workspace
/workspace list                   # list all workspaces
/workspace add-repo <slug>        # add a repo to existing workspace
/workspace add-infra <slug>       # add DB/cache/ports when ready for eval
```

## What You Must Do When Invoked

### Step 1 — Check for existing workspaces

```bash
ls ~/forge/brain/products/ 2>/dev/null || echo "none"
```

If workspaces exist, ask: **"Open an existing workspace or create a new one?"**
- If open → skip to Step 4
- If new → continue to Step 2

---

### Step 2 — Ask only the minimum

Ask these questions **one at a time** (do not dump a form):

1. **"What's the product name?"** (e.g. "JobHai Recruiter")
   - Auto-generate slug from name (lowercase, hyphens)

2. **"What repos are you working with? Paste GitHub URLs or local paths, one per line."**
   - Accept GitHub URLs, local paths, or just repo names
   - If GitHub URL: clone automatically
   - If local path: use as-is
   - If just a name: ask where it lives

3. **"What role does each repo play?"** (for each repo)
   - Options: `backend` / `web` / `mobile` / `shared` / `infra`
   - If only one repo: skip this question, infer from name

That's it. Do NOT ask about ports, frameworks, DB credentials, or merge order at this stage.

---

### Step 3 — Create the workspace

Generate `~/forge/brain/products/<slug>/product.md` with only what was provided:

```markdown
# Product: <Name>

## Identity
- slug: <slug>
- description: (add a one-line description)
- primary owner: (add your team name)

## Projects

### <repo-name>
- repo: <path-or-url>
- role: <backend|web|mobile|shared|infra>
- branch: main
- language: (detected or TBD)
- framework: (detected or TBD)

### <repo-name-2>
- repo: <path-or-url>
- role: <role>
- branch: main

## Infrastructure
# Not configured yet — run /workspace add-infra <slug> before /eval

## Merge Order
# Will be determined during /council
```

Then confirm:
```
✅ Workspace created: ~/forge/brain/products/<slug>/product.md
   Repos: <list>
   Next: run /intake to start planning
```

---

### Step 4 — Open existing workspace

```bash
cat ~/forge/brain/products/<slug>/product.md
```

Show a summary:
```
📁 Workspace: <name>
   Repos: backend (~/code/...), web (~/code/...), app (~/code/...)
   Infra: ⚠️  Not configured (run /workspace add-infra before /eval)
   PRDs: <count> in brain
   Last activity: <date of last brain commit>
```

Then ask: **"What would you like to do?"**
- `/intake` — start a new feature
- `/recall` — look up past decisions
- `/workspace add-infra` — configure infrastructure for eval
- `/forge-status` — check full status

---

### Step 5 — add-infra (when user is ready for eval)

Only triggered by `/workspace add-infra <slug>`. Ask:

1. **"What database are you using?"** (MySQL / PostgreSQL / MongoDB / none)
2. **"What cache?"** (Redis / none)
3. **"What message bus?"** (Kafka / RabbitMQ / none)
4. **"What ports does each service run on?"** (per repo)
5. **"How do you start each service?"** (per repo)

Update `product.md` in-place with the infra section filled in.

---

### Step 6 — add-repo

Adds a new repo to an existing workspace:

1. Ask for repo URL or path
2. Ask for role
3. Append to `product.md` Projects section
4. Ask if merge order needs updating

---

## Principles

- **Never block planning with infra questions.** Intake and council work without ports or DB credentials.
- **One question at a time.** No forms, no YAML to fill in manually.
- **Auto-detect what you can.** Language from file extensions, framework from package.json / requirements.txt / go.mod, branch from git.
- **Infra is eval-time, not planning-time.** The only time you need DB credentials is when `/eval` runs.

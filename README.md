# Forge

> Plug-and-play multi-repo product orchestration plugin. Takes a PRD and ships it end-to-end across any product stack.

Forge takes a single PRD (Product Requirements Document) and ships the entire feature across multiple repos: it locks scope through intake, negotiates contracts between services, generates bite-sized tech plans, builds with TDD in isolated worktrees, runs end-to-end eval across your whole stack, auto-heals failures, reviews code, raises coordinated PRs in dependency order, and writes every decision to a searchable brain. 64 skills, 4 subagents, 15 slash commands.

---

## Table of Contents

- [Quick Start](#quick-start)
- [How Forge Works](#how-forge-works)
- [Platform Setup](#platform-setup)
- [Describing Your Product](#describing-your-product)
- [Example: Shipping a Feature with Forge](#example-shipping-a-feature-with-forge)
- [Commands Reference](#commands-reference)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/harsh-chaudhary999/forge ~/forge
cd ~/forge
```

### 2. Install

```bash
bash scripts/install.sh
```

This auto-detects your IDE(s) and installs for all of them. To install for a single platform:

```bash
bash scripts/install.sh --platform claude-code
```

### 3. Restart your IDE

Forge loads on session start. After restart, verify:

```
/forge-status
```

You should see Forge context injected with all 64 skills available.

---

## How Forge Works

Forge runs a 10-stage pipeline on every PRD:

```
PRD → Intake → Council → Spec Freeze → Tech Plans → Build → Eval → Self-Heal → Review → PR Set → Brain
```

### The Pipeline

| Stage | What Happens | Gate |
|---|---|---|
| **Intake** | 8-question interrogation locks scope, success criteria, constraints. No ambiguity survives. | HARD-GATE |
| **Council** | 4 surfaces (backend, web, app, infra) + 5 contracts (REST, events, cache, DB, search) negotiate to produce a shared-dev-spec. | HARD-GATE |
| **Spec Freeze** | Shared-dev-spec is immutably locked. No changes without full re-negotiation. | HARD-GATE |
| **Tech Plans** | Per-repo bite-sized tasks (2-5 min each, exact files, exact code, exact commands). One plan per repo. | Human approval |
| **Build** | TDD implementation in isolated worktrees. dev-implementer subagent executes each task: write test, watch fail, write code, watch pass. | HARD-GATE (TDD) |
| **Eval** | End-to-end product test across all services. Drivers: API, DB, cache, search, events, web browser, mobile. | HARD-GATE |
| **Self-Heal** | If eval fails: locate fault, triage (flaky/bad-test/real-bug/environment), fix, re-eval. Max 3 retries. | Auto |
| **Review** | Two-stage: spec-reviewer verifies implementation matches spec, code-quality-reviewer checks quality/perf/security. | HARD-GATE |
| **PR Set** | Coordinated PRs across repos, merged in strict dependency order. | HARD-GATE |
| **Brain** | Dreamer scores every decision, extracts patterns, writes learnings to `~/forge/brain/`. | Auto |

### What Makes It Different

- **No code changes to your product.** Describe your product once in a `forge-product.md` file. Forge does the rest.
- **No third-party agent frameworks.** No LangChain, no Playwright, no Puppeteer. Just native AI tool calls and markdown.
- **No runtime plugin dependencies.** Forge skills are self-contained markdown. They work offline.
- **Every decision is auditable.** The brain is a git repo. Every decision has provenance: who, when, why, evidence, alternatives.
- **Anti-pattern preambles on every skill.** Each skill starts with a rationalization table that closes loopholes before they open.
- **350+ edge cases with escalation paths.** Every skill documents failure scenarios with Symptom, Do NOT, Mitigation, and escalation keywords (BLOCKED / NEEDS_CONTEXT / NEEDS_COORDINATION / NEEDS_INFRA_CHANGE).
- **Decision trees for complex judgment calls.** 29+ skills include ASCII decision trees for choosing between strategies (e.g. cache isolation approach, transaction isolation level, PR merge strategy).
- **Iron Law enforcement on every rigid skill.** Non-negotiable MUST rules in ALL CAPS. If the rule says write the test first, there is no exception.

---

## Platform Setup

| Platform | Status | Install |
|---|---|---|
| Claude Code | Full support | Auto-detected via `.claude-plugin/plugin.json` |
| Cursor | Full support | Auto-detected via `.cursor-plugin/plugin.json` + `.cursorrules` |
| Google Antigravity | Full support | Auto-detected via `.agent/skills/` + `AGENTS.md` + `GEMINI.md` |
| Gemini CLI | Full support | Auto-detected via `gemini-extension.json` |
| Project IDX | Full support | Same as Gemini CLI |
| OpenAI Codex | Full support | Auto-detected via `AGENTS.md` |
| GitHub Copilot CLI | Full support | SessionStart hook detects `COPILOT_CLI` env var |
| OpenCode | Full support | Auto-detected via `.opencode/plugins/forge.js` |
| JetBrains AI | Manual setup | Copy `templates/junie-guidelines.md` to `.junie/guidelines.md` |

Per-platform guides with prerequisites, verification steps, and troubleshooting: [`docs/platforms/`](docs/platforms/)

---

## Describing Your Product

Before Forge can orchestrate your product, you need one file: `forge-product.md`. This tells Forge what repos exist, what role each plays, how to start/stop them, and what infrastructure they use.

### forge-product.md Template

```markdown
# Product: {Your Product Name}

## Identity
- slug: my-product
- description: One sentence about what this product does
- primary owner: your-team

## Projects

### backend-api
- repo: ~/code/my-product-backend
- role: backend
- language: node
- framework: express
- branch: main
- port: 3001
- start: npm install && npm start
- stop: (process kill)
- health: GET http://localhost:3001/health
- depends_on: (none)
- deploy_strategy: local-process

### web-app
- repo: ~/code/my-product-web
- role: web-frontend
- language: typescript
- framework: next
- branch: main
- port: 3000
- start: npm install && npm run dev
- stop: (process kill)
- health: GET http://localhost:3000
- depends_on: backend-api
- deploy_strategy: local-process

## Infrastructure (for eval)

### mysql
- driver: mysql-native
- host: localhost
- port: 3306
- reset_command: mysql -u root -e "DROP DATABASE IF EXISTS myproduct; CREATE DATABASE myproduct;"
- migration: cd ~/code/my-product-backend && npm run migrate

### redis
- driver: redis-resp
- host: localhost
- port: 6379
- reset_command: redis-cli FLUSHALL

## Contracts
- contracts/api-rest.md
- contracts/schema-mysql.md
- contracts/cache-redis.md

## Merge Order
1. backend-api
2. web-app
```

Place this file in `~/forge/brain/products/{your-slug}/product.md` or in your product's root directory.

---

## Example: Shipping a Feature with Forge

This walkthrough uses the included seed product (SeedShop) to show the full pipeline. The feature: **Item Favorites with Cross-Surface Sync** — users can favorite items on web and mobile, with real-time sync between surfaces.

### Step 1: Write the PRD

Write a PRD describing what you want to build. It should cover: problem statement, goals, success metrics, technical scope, and acceptance criteria. See [`seed/prds/01-favorites-cross-surface-sync.md`](seed/prds/01-favorites-cross-surface-sync.md) for a complete example.

### Step 2: Run the full pipeline

```
/forge
```

Paste or reference your PRD. Forge takes over from here. Or run each stage manually:

### Step 2a: Intake (locks scope)

```
/intake
```

Forge asks 8 questions to eliminate ambiguity:

1. What is the exact scope? (which repos, which services)
2. What are the success criteria? (measurable, testable)
3. What are the constraints? (performance, compatibility, timeline)
4. What's out of scope? (prevents scope creep)
5. Who are the stakeholders?
6. What are the known risks?
7. What are the dependencies?
8. What does "done" look like?

After all 8 are answered, the PRD is **locked** in the brain. No changes without re-intake.

### Step 2b: Council (negotiates contracts)

```
/council
```

Four surfaces reason about the PRD independently:

- **Backend**: "I need a `favorites` table, REST endpoints, WebSocket events"
- **Web Frontend**: "I need optimistic updates, a favorites page, real-time sync"
- **App Frontend**: "I need offline SQLite storage, background sync, conflict resolution"
- **Infrastructure**: "I need Redis cache keys, Kafka topics for sync events, MySQL migration"

Then 5 contracts are negotiated:
- **REST API**: endpoints, request/response schemas, status codes
- **Events**: Kafka topics, message schemas, ordering guarantees
- **Cache**: Redis key patterns, TTLs, invalidation rules
- **Database**: schema migrations, indexes, constraints
- **Search**: (if applicable) index mappings, analyzers

Conflicts are resolved during council, not during build. The output is a **shared-dev-spec** — a single document that all surfaces agree on.

### Step 2c: Spec Freeze

The shared-dev-spec is frozen. From this point, no changes without full re-negotiation. This prevents mid-build scope drift.

### Step 2d: Tech Plans

```
/plan
```

Forge generates one plan per repo. Each task is 2-5 minutes of work with:
- Exact file paths
- Complete code (no pseudocode, no placeholders)
- Exact bash commands
- Test code that must be written first (TDD)

Example task from the backend plan:
```
Task 3: Add POST /api/favorites endpoint
File: src/routes/favorites.ts
Test: tests/routes/favorites.test.ts

Write test first:
  - POST /api/favorites with valid {itemId} → 201, body has {id, userId, itemId, createdAt}
  - POST /api/favorites with duplicate → 409
  - POST /api/favorites without auth → 401

Then implement:
  [complete code provided]
```

You review and approve the plans before build starts.

### Step 2e: Build

```
/build
```

The dev-implementer subagent executes each task in an isolated git worktree:
1. Creates fresh worktree (no shared state between tasks)
2. Writes the test
3. Runs it — watches it fail (red)
4. Writes the implementation
5. Runs it — watches it pass (green)
6. Commits

### Step 2f: Eval

```
/eval
```

Forge brings up the entire product stack and drives it end-to-end:

1. Start MySQL, Redis, backend, web, app
2. Run migration
3. Execute eval scenarios:
   - `POST /api/favorites` → verify 201
   - Check MySQL row exists
   - Check Redis cache populated
   - Open web browser → verify favorite button state
   - Favorite on web → verify app sees it within 2s
   - Go offline on app → favorite → come back online → verify sync

Each driver (API, DB, cache, browser, mobile) reports pass/fail with evidence.

### Step 2g: Self-Heal (if eval fails)

```
/heal
```

If any scenario fails:
1. **Locate**: Which service failed? Parse error, check logs, find the first failure in the chain.
2. **Triage**: Is it flaky (timing), bad test (wrong assertion), real bug (code broken), or environment (service down)?
3. **Fix**: Apply minimal fix. One thing at a time. No refactoring.
4. **Verify**: Re-run the failing scenario.

Max 3 retries. If still failing after 3, escalates to you with full diagnostic context.

### Step 2h: Review

```
/review
```

Two-stage:
1. **Spec reviewer**: Reads actual code (not reports). Does the implementation match the shared-dev-spec?
2. **Code quality reviewer**: 8-point quality framework + performance + security + observability.

### Step 2i: PR Set

PRs are raised in dependency order:
1. `shared-schemas` (if any schema changes)
2. `backend-api`
3. `web-dashboard`
4. `android-app`

Each PR links to the others with `depends-on` references. Forge waits for each to merge before raising the next.

### Step 2j: Dream (retrospective)

```
/dream
```

The dreamer scores every decision across 5 categories (1-5 each):
- Intake Quality
- Council Negotiation
- Tech Plan Accuracy
- Build Execution
- Eval Coverage

Extracts patterns (what worked), gotchas (what failed), and opportunities (what was missed). Writes learnings to `~/forge/brain/` for future recall.

---

## Commands Reference

| Command | What It Does |
|---|---|
| `/forge` | Run full pipeline: PRD to shipped PRs |
| `/intake` | Start PRD intake (8 questions, lock scope) |
| `/council` | Multi-surface contract negotiation |
| `/plan` | Generate per-project tech plans |
| `/build` | Build in isolated worktrees with TDD |
| `/eval` | Run end-to-end product eval |
| `/heal` | Diagnose and fix eval failures |
| `/review` | Two-stage code review (spec + quality) |
| `/dream` | Dreamer retrospective (score decisions, extract learnings) |
| `/why` | Trace provenance of any decision ("Why did we choose WebSocket over polling?") |
| `/recall` | Search brain for past decisions and patterns |
| `/remember` | Record a new decision to the brain |
| `/forge-status` | Show current Forge state and configuration |
| `/forge-test` | Run end-to-end self-test on the seed product |
| `/forge-install` | Show platform-specific install instructions |

---

## Architecture

```
forge/
├── skills/             # 64 Forge skills (SKILL.md with YAML frontmatter)
│   ├── conductor-orchestrate/    # Master state machine
│   ├── intake-interrogate/       # PRD intake (8 questions)
│   ├── council-multi-repo-negotiate/  # Multi-surface negotiation
│   ├── forge-tdd/                # TDD discipline (Iron Law)
│   ├── eval-judge/               # Final eval verdict
│   ├── self-heal-locate-fault/   # Fault diagnosis
│   └── ...                       # 58 more skills
├── agents/             # 4 subagents
│   ├── dev-implementer/          # Builds code with TDD
│   ├── spec-reviewer/            # Verifies code matches spec
│   ├── code-quality-reviewer/    # 8-point quality review
│   └── dreamer/                  # Retrospective scoring
├── commands/           # 15 slash commands
├── hooks/              # Plugin hooks (session-start injection)
├── .claude-plugin/     # Claude Code plugin manifest
├── .cursor-plugin/     # Cursor plugin manifest
├── .agent/skills/      # Antigravity symlinks → skills/
├── .opencode/plugins/  # OpenCode plugin entry
├── references/         # Tool mapping (Copilot CLI)
├── templates/          # IDE templates (JetBrains)
├── docs/platforms/     # Per-platform setup guides
├── seed/               # Seed product (SeedShop) for testing
├── CLAUDE.md           # Claude Code project context
├── AGENTS.md           # Codex / Antigravity context
├── GEMINI.md           # Gemini CLI / Antigravity context
└── .cursorrules        # Cursor project context
```

### Skills

Every skill is a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: skill-name
description: "WHEN: trigger condition. What it does."
type: rigid | flexible | reference
requires: [other-skill]
---
```

- **rigid**: Follow exactly. No adaptation. Discipline skills (TDD, gates, eval).
- **flexible**: Adapt principles to context. Technique skills (negotiation, planning).
- **reference**: Explain concepts. No prescription. Glossaries, templates.

All rigid and flexible skills follow a standardised format:

| Section | Purpose |
|---|---|
| **Anti-Pattern Preamble** | Table of 5+ rationalizations agents use to skip the skill, with rebuttals. Closes loopholes before they open. |
| **Iron Law** | Non-negotiable MUST rules in ALL CAPS. No exceptions permitted. |
| **Red Flags — STOP** | 5+ observable signals that mean stop immediately and do not proceed. |
| **Edge Cases** | 3–7 failure scenarios per skill: Symptom, Do NOT, Mitigation steps, Escalation keyword. |
| **Decision Trees** | ASCII flowcharts for the primary judgment calls (present in 29+ skills). |
| **Checklist** | End-of-skill verification checklist before marking step complete. |

Escalation keywords used across skills: `BLOCKED` · `NEEDS_CONTEXT` · `NEEDS_COORDINATION` · `NEEDS_INFRA_CHANGE` · `DONE_WITH_CONCERNS`

### Subagents

| Agent | Role | Reports |
|---|---|---|
| dev-implementer | TDD build in isolated worktree | DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED |
| spec-reviewer | Verify code matches shared-dev-spec | DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED |
| code-quality-reviewer | 8-point quality + perf/security/observability | DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED |
| dreamer | Inline conflict resolution + post-merge retrospective | DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED |

### Brain

The brain at `~/forge/brain/` is a git repo of markdown files. Every decision, spec, eval result, and retrospective is committed with structured messages. The brain grows sharper with every shipped feature.

```
~/forge/brain/
├── products/{slug}/
│   ├── product.md              # Product topology
│   └── prd/{prd-id}/
│       ├── PRD.md              # Locked PRD
│       ├── shared-dev-spec.md  # Frozen spec
│       ├── tech-plans/         # Per-repo plans
│       ├── evals/              # Eval run results
│       └── learnings/          # Retrospective
└── decisions/
    ├── D001.md                 # Decision records
    └── ...
```

---

## Troubleshooting

### Forge not loading on session start

1. Check the hook is executable: `chmod +x ~/forge/hooks/session-start`
2. Verify `hooks/hooks.json` is valid JSON
3. Restart your IDE
4. Run `/forge-status` to check

### Skills not found

1. Verify skill files exist: `ls ~/forge/skills/*/SKILL.md | wc -l` (should be 64)
2. Check YAML frontmatter is valid in each SKILL.md
3. For Antigravity: verify symlinks exist: `ls ~/forge/.agent/skills/ | wc -l`

### Commands not working

1. Verify command files: `ls ~/forge/commands/*.md`
2. Each command needs YAML frontmatter with a `description` field

### Eval failures

1. Check infrastructure is running (MySQL, Redis, etc.)
2. Run `/heal` to enter the self-heal loop
3. Check `~/forge/brain/products/{slug}/prd/{id}/evals/` for detailed results

### Uninstall

```bash
cd ~/forge && bash scripts/install.sh --uninstall
```

---

## Requirements

- **One of:** Claude Code, Cursor, Antigravity, Gemini CLI, Codex, Copilot CLI, OpenCode, or JetBrains AI
- **Git** (for brain, worktrees, and version control)
- **Bash** (for hooks and install script)
- **Node.js 16+** (for install script)

## License

MIT

# Forge

> Plug-and-play multi-repo product orchestration for AI-assisted delivery. Takes a PRD and drives it through locked scope, negotiated contracts, tech plans, TDD implementation, multi-surface eval, review, and coordinated PRs — with a **git-backed brain** as the system of record.

Forge ships a feature across **multiple repos** without embedding a runtime framework in your product code: **skills** (markdown + YAML), **subagents**, **hooks**, and **commands** encode process. **68 skills**, **4 subagents**, **17 slash commands**. Works with **Claude Code, Cursor, Codex, Gemini CLI, Antigravity, Copilot CLI, OpenCode, JetBrains AI** (see [Platform Setup](#platform-setup)).

**`/forge`** (`commands/forge.md`) is the **full end-to-end** entrypoint: same phases as **`conductor-orchestrate`**, including **mandatory** State 4b **manual QA CSV** (`qa-prd-analysis` → `qa-manual-test-cases-from-prd` → approved `qa/manual-test-cases.csv` → `[P4.0-QA-CSV]`) **before** `[P4.0-EVAL-YAML]`, then eval YAML, TDD RED, design ingest when applicable, dispatch, reviews, **P4.4 eval**, self-heal, PR set, dream/brain. Other slash commands are **partial slices** — see [Commands reference](#commands-reference) and [Orchestration model](#orchestration-model-automation-vs-approvals).

---

## Table of contents

- [Quick start](#quick-start)
- [What Forge is (and is not)](#what-forge-is-and-is-not)
- [How Forge works](#how-forge-works)
- [Delivery gates (Phase 4)](#delivery-gates-phase-4)
- [Design & UI](#design--ui)
- [QA & test artifacts](#qa--test-artifacts)
- [Codebase knowledge & file targeting](#codebase-knowledge--file-targeting)
- [Service topology](#service-topology)
- [What makes it different](#what-makes-it-different)
- [Platform setup](#platform-setup)
- [Getting started with an existing project](#getting-started-with-an-existing-project)
- [Describing your product](#describing-your-product)
- [Example: shipping a feature](#example-shipping-a-feature-with-forge)
- [Commands reference](#commands-reference)
- [Repository layout](#repository-layout)
- [Brain layout](#brain-layout)
- [Machine verification (optional CI)](#machine-verification-optional-ci)
- [Orchestration model (automation vs approvals)](#orchestration-model-automation-vs-approvals)
- [Troubleshooting](#troubleshooting)
- [Requirements & license](#requirements--license)

---

## Quick start

### 1. Clone

```bash
git clone https://github.com/harsh-chaudhary999/forge ~/forge
cd ~/forge
```

### 2. Install

Use **bash** (not `sh` / dash). If auto-detect skips your IDE (e.g. Cursor without the shell command on PATH), pass **`--platform`** explicitly — see [Cursor troubleshooting](docs/platforms/cursor.md#installsh-did-not-install-forge-for-cursor-auto-detect-skipped-cursor).

```bash
bash scripts/install.sh
```

Installs for all detected IDEs. For one platform:

```bash
bash scripts/install.sh --platform cursor
```

### 3. Restart your IDE

Forge injects context on session start. Verify:

```
/forge-status
```

You should see **using-forge** and the skill catalog (**68 skills** when installed from this repo).

---

## What Forge is (and is not)

| Forge **is** | Forge **is not** |
|---|---|
| A **process plugin**: rules, gates, and workflows your agent is expected to follow | A replacement for your language/framework or CI provider |
| **Markdown skills** + optional **Python** (`tools/scan_forge/`) for codebase inventory | LangChain, Playwright, or Puppeteer in your product (explicitly out of scope for plugin code) |
| A **brain** (`~/forge/brain/`) for PRDs, specs, scans, QA CSV, eval YAML, and decisions | **IDE enforcement is procedural** — pair with optional **[machine verification](#machine-verification-optional-ci)** (`tools/verify_forge_task.py` + CI) so bad ordering or missing `eval/` fails the build, not just the chat |
| **Parallel subagents** (e.g. four council surfaces, per-repo **`dev-implementer`**) for independent work | **Not a background daemon** — phases do not auto-advance when files appear on disk; the **agent** must invoke the next skill/phase (or you say “continue”). **`/forge`** documents full sequencing; it does not replace host session limits or human gates where skills require approval |

---

## How Forge works

### End-to-end narrative

```
PRD → Intake → Council → Spec freeze → Tech plans
         → Phase 4 gates (QA CSV†, eval YAML, TDD RED, design ingest‡)
         → Build (GREEN) → Review → Eval (execute) → Self-heal → PR set → Brain / dream
```

† **Manual QA CSV (`qa/manual-test-cases.csv`):**  
- **`/forge` (full pipeline):** **Always mandatory** in State 4b before `[P4.0-EVAL-YAML]` — do **not** log `[P4.0-QA-CSV] skipped=not_required`. Orchestrator should pass **`entrypoint = full pipeline (/forge)`** into **`conductor-orchestrate`**. If `forge_qa_csv_before_eval` is missing or `false` in **`product.md`**, a **`/forge`** run **sets it to `true`** when CSV is produced so CI and later runs stay aligned.  
- **Partial commands** (`/intake`, `/council`, `/plan`, …): **Mandatory** when **`forge_qa_csv_before_eval: true`** in **`~/forge/brain/products/<slug>/product.md`** or the task charter requires a CSV; otherwise **recommended** — may log `[P4.0-QA-CSV] skipped=not_required` when intentionally omitted for that partial run only.  
- **CSV rows** are **acceptance / TMS-style** atomic cases (8 columns + **Source**), **not** a catalog of unit tests — see [QA & test artifacts](#qa--test-artifacts).

‡ *When web/app work has **net-new UI**, intake must lock **design** in `prd-locked.md` (see **`intake-interrogate`**) — not a fixed “question count.”*

### Pipeline stages (conceptual)

| Stage | What happens | Gate |
|---|---|---|
| **Intake** | Mandatory **`prd-locked.md`** **sections** (not a fixed number of user questions): product, goal, success criteria, **repos + registry** (`repo_registry_confidence`, mismatch notes, `product_md_update_required`), contracts, timeline, rollback, metrics — plus **design / UI** (`design_intake_anchor`, implementable design or waiver) when web, app, or user-visible UI is in scope. **Confidence-first:** pre-fill from PRD + `product.md`, ask **low-confidence / high-stakes** doubts only; **variable** user turns — **stop** when every required section is concrete. Skill **`intake-interrogate`** uses **Q1–Q9** only as an **internal checklist** name for those sections. | HARD-GATE |
| **Council** | Four surfaces (backend, web, app, infra) + five contracts (REST, events, cache, DB, search) negotiate → **`shared-dev-spec.md`**. | HARD-GATE |
| **Spec freeze** | Spec is immutable until re-council. | HARD-GATE |
| **Tech plans** | Per-repo plans: **exact files**, complete code snippets, exact commands (`tech-plan-write-per-project`). Informed by **codebase scan** when present. | Human approval typical |
| **Phase 4** | See [Delivery gates](#delivery-gates-phase-4) — **eval YAML + TDD RED** + **QA CSV when required** (`forge_qa_csv_before_eval: true` **or** full **`/forge`**) + **design ingest** when applicable — **all before** P4.1 feature dispatch. | HARD-GATE |
| **Build** | **`dev-implementer`**: TDD GREEN in **isolated worktrees**. | HARD-GATE (TDD) |
| **Review** | Spec + code-quality reviewers; optional **design parity** reviewers when net-new UI and harness supports them. | HARD-GATE |
| **Eval (execute)** | **`eval-product-stack-up`** + multi-surface drivers; scenarios from **`eval/*.yaml`**. | HARD-GATE |
| **Self-heal** | Locate → triage → fix → re-eval; max **3** attempts. | Auto then escalate |
| **PR set** | Merge order with dependency links (`pr-set-merge-order` / `pr-set-coordinate`). | HARD-GATE |
| **Brain / dream** | Retrospectives, learnings, links (`dream-retrospect-post-pr`, brain skills). | Auto |

### Brain as transport

**Council and subagents do not read your live chat.** They read what is written under **`~/forge/brain/`** (e.g. **`prd-locked.md`**, **`shared-dev-spec.md`**, **`design/`**, **`qa/`**, **`eval/`**, **`council/`** / **`reasoning/`** for surface artifacts). If design or acceptance lives only in a wiki URL, downstream phases have nothing durable to implement or test against.

---

## Delivery gates (Phase 4)

**`conductor-orchestrate`** defines **State 4b** before **State 5 (dispatch)**. Rules are spelled out in **`skills/conductor-orchestrate/SKILL.md`**; **`commands/forge.md`** pins the stricter **full-pipeline** CSV path for **`/forge`**.

| Order | Artifact / log | Purpose |
|---:|---|---|
| **0** | **`[P4.0-QA-CSV]`** | **Approved** **`~/forge/brain/prds/<task-id>/qa/manual-test-cases.csv`** (≥1 row after **`qa-prd-analysis`** + **`qa-manual-test-cases-from-prd`** Step 7). **Required** when **`forge_qa_csv_before_eval: true`** in **`product.md`** **or** the run is **full `/forge`** (then also persist **`forge_qa_csv_before_eval: true`** if it was unset/false). **Partial** run + flag false/unset: may log **`skipped=not_required`** only if CSV is intentionally omitted. |
| **1** | **`[P4.0-EVAL-YAML]`** + `eval/*.yaml` (≥1 file) | Executable scenarios for **`eval-coordinate-multi-surface`** / **P4.4** (**YAML** drivers — not a substitute for repo **BDD** files; see [QA & test artifacts](#qa--test-artifacts)). **No standard waive** for shippable work; only logged **`ABORT_TASK`**. |
| **2** | **`[P4.0-TDD-RED]`** per repo (or logged **`WAIVE_TDD`**) | **Automated** tests in product repos: **RED before GREEN** (**`forge-tdd`**). May be **unit, service, or BDD-style** — team choice; must encode tech plan + trace **CSV `Id`s** when CSV exists. |
| **3** | **`[DESIGN-INGEST]`** when **net-new UI** | Materialized design under **`design/`** or locked Figma key + node IDs + ingest notes — unless **`design_waiver: prd_only`**. |
| **4** | **P4.1 dispatch** | Feature implementation only after the above per policy. |

**`dev-implementer`** returns **`BLOCKED_ORCHESTRATION`** if dispatch skips **`eval/`**, **`[P4.0-EVAL-YAML]`**, or (when **`forge_qa_csv_before_eval: true`** — including after a **`/forge`** run set it) skips approved QA CSV — see **`agents/dev-implementer.md`**.

---

## Design & UI

- **Intake — design / UI** (mandatory for web/app / user-visible scope): the user must see the **verbatim** design source-of-truth question from **`intake-interrogate`** in chat (not only text in `prd-locked.md`); then **`design_intake_anchor`**, implementable paths or **`figma_file_key` + `figma_root_node_ids`**, or a documented waiver — not wiki-only links.
- **Surface skills** (`reasoning-as-web-frontend`, `reasoning-as-app-frontend`): **Lovable → GitHub** when `lovable_github_repo` is locked (**[`docs/platforms/lovable.md`](docs/platforms/lovable.md)**); **Figma MCP first** when the host provides it; then REST; human export as fallback.
- **Council / spec-freeze** copy design fields into **`shared-dev-spec.md`**; thin design blocks **block** freeze when net-new UI lacks implementable inputs.

---

## QA & test artifacts

Forge uses **three** linked layers. None replaces the others:

| Layer | Where it lives | What it is |
|---|---|---|
| **1. Manual QA CSV** | **`~/forge/brain/prds/<task-id>/qa/manual-test-cases.csv`** | **Acceptance inventory**: atomic rows for humans / TMS (**8 columns** + optional **`Source`** per **`qa-manual-test-cases-from-prd`**). **Not** a list of unit-test methods — rows are verifiable **user/API-visible** outcomes (**`Web`**, **`Android`**, **`API`**, etc.). |
| **2. Eval YAML** | **`~/forge/brain/prds/<task-id>/eval/*.yaml`** | **Machine-runnable** scenarios for **P4.4** (**`eval-scenario-format`**, **`eval-translate-english`**, drivers: web CDP, API HTTP, DB, cache, search, mobile, …). This is Forge’s **E2E / multi-surface execution** spec. **Does not** require Gherkin in your product repo. |
| **3. Repo automated tests** | Your repos (worktrees) | **`forge-tdd`**: **RED → GREEN → refactor**. Can be **unit**, **integration**, or **BDD** (Cucumber, etc.) — whatever the repo runs in CI. **First** failing tests that encode the **tech plan** (and **CSV `Id`s`** when CSV exists), **then** production code. |

**Rigid skills for CSV path:**

| Skill | Role |
|---|---|
| **`qa-prd-analysis`** | Structured PRD analysis → **`~/forge/brain/prds/<task-id>/qa/PRD_ANALYSIS.md`** before bulk CSV work. |
| **`qa-manual-test-cases-from-prd`** | Atomic **CSV**, Step 3 + Step 7 approvals, estimation, reuse/deprecation, final report. **HARD-GATE:** no production CSV rows before sample approval; no final report before count approval. |

**Product policy** — edit **`~/forge/brain/products/<slug>/product.md`** (create with **`/workspace`**; there is **no** bundled `forge-product.md` template in-repo):

```yaml
# When true: conductor requires [P4.0-QA-CSV] before [P4.0-EVAL-YAML] on partial runs too.
# /forge always mandates CSV in State 4b and may set this to true if it was false/missing.
forge_qa_csv_before_eval: true   # set false only if you intentionally skip CSV on partial runs
```

**Traceability:** **`eval-translate-english`** should carry **CSV `Id`s** into YAML **names/comments** when both exist so **P4.4** and **RED** stay aligned with the **signed** acceptance set.

**Commands:** **`/eval`** **runs** existing YAML against the stack — it does **not** author CSV or YAML (that is **State 4b**). **`/forge`** drives **full** State 4b including CSV when you want end-to-end automation in one entrypoint.

---

## Codebase knowledge & file targeting

1. **`/scan`** runs **`tools/scan_forge/`** → **`~/forge/brain/products/<slug>/codebase/`** — producing:
   - **Module + class stubs** (`modules/`, `classes/`, `pages/`) — wikilinked Obsidian-format knowledge graph
   - **`graph.json`** — full dependency graph with cross-repo edges
   - **`SCAN.json`** — timestamp, commit SHA, file counts, method inventory stats, cross-repo edge counts
   - **`SCAN_SUMMARY.md`** — human-readable narrative of what was found
   - **`repo-docs/`** — enriched snapshots of curated docs from each repo (see below)
   - **`cross-repo-automap.md`** — all detected cross-repo links with provenance labels
2. **`product-context-load`** surfaces scan metadata and **warns** if scan is missing or **>7 days** old.
3. **`tech-plan-write-per-project`** must list **exact file paths** (plans are what **`dev-implementer`** relies on in isolation).
4. **Implementer** reads the paths and contracts named in the plan — it does not re-derive the repo map from scratch if the plan is complete.

### Repo-docs mirror (`brain/codebase/repo-docs/`)

`/scan` automatically mirrors curated documentation from each scanned repo into the brain so council, tech-plan, and eval phases can read actual docs — not just code structure.

**What gets mirrored:** `docs/**`, `doc/**`, `guides/**`, `adr/**`, `rfc/**`, root `*.md` files (README, CONTRIBUTING, CHANGELOG, SECURITY, ARCHITECTURE…), `openapi*.yaml/json`, `swagger*.yaml/json`.

**Enrichment applied to every `.md` file:**
- YAML frontmatter — `source_repo`, `source_file`, `commit`, `doc_type`, `scanned_at`
- Heading outline — extracted `##`/`###` hierarchy appended for navigation
- ADR structured fields — `Status`, `Context`, `Decision`, `Consequences` parsed from ADR files
- Brain node wikilinks — auto-detected links to matching `modules/` and `classes/` nodes

**Index files written under `repo-docs/`:**
- **`SEARCH_INDEX.md`** — one row per section across all docs; use this to find relevant documentation before reading full files
- **`INDEX.md`** — file inventory table with role, type, HEAD, and byte count
- **`index.json`** — machine-readable metadata with `source_sha256`, `doc_type`, `extract_version`, policy results

**Incremental:** source SHA + extract version tracked — files are only re-enriched when the source changes or the enrichment logic is bumped.

**Per-repo policy** (`forge-scan-docs.policy.yaml` in the repo root):

```yaml
version: 1
deny_path_contains:
  - "DO_NOT_MIRROR"        # never copy or index
index_only_path_contains:
  - "CHANGELOG"            # appear in index.json but no file copy
allow_extra_path_contains:
  - "extras/"              # include beyond the default set
max_files: 80              # per-repo cap (default: 120)
max_bytes_per_file: 102400 # per-repo size cap (default: 512 KB)
```

Disable entirely: `FORGE_REPO_DOCS_MIRROR=0`.

### Cross-repo edge types

`/scan` detects and labels relationships between repos in `cross-repo-automap.md`:

| Edge type | Source | Meaning |
|---|---|---|
| `GREP_SUBSTRING` | URL string in source matches route in another repo | Direct HTTP call detected by static analysis |
| `OPENAPI` | Call-site URL matched against OpenAPI spec path | Verified against the consuming service's spec |
| `TOPOLOGY_DECLARED` | `product.md` topology says A calls B but URL is dynamic | Declared dependency (env var / template literal) — verify manually |
| `SHARED_TYPE` | Same type name found in `classes/` of two repos | Shared data contract across services |
| `EVENT_BUS` | Producer keyword in one repo + consumer keyword in another | Kafka/event-bus publish→subscribe link |

Unresolved edges (call-sites with no matched route) are listed in an **`## Unresolved Edges`** section at the bottom of `cross-repo-automap.md` — visible, not silently dropped.

---

## Service topology

Add a `## Service Topology` section to **`~/forge/brain/products/<slug>/product.md`** to unlock cross-repo edge inference in `/scan`. This is optional but recommended for multi-service products — without it, scan can only detect routes via literal URL strings in source code.

```markdown
## Service Topology

### backend-api
calls: [auth-service, notification-service]
publishes: [user.created, order.placed]
db-owner: [users_db, orders_db]
config: [DATABASE_URL, JWT_SECRET]

### frontend
calls: [backend-api]
subscribes: []
config: [NEXT_PUBLIC_API_URL]

### auth-service
calls: []
subscribes: [user.created]
db-owner: [auth_db]
config: [JWT_SECRET, REDIS_URL]
```

**How scan uses this:**
- `calls` — when a call-site URL is dynamic (env var, template literal, constant), scan writes a `TOPOLOGY_DECLARED` edge instead of silently dropping it
- `publishes` / `subscribes` — matched against grep hits for producer/consumer keywords to produce `EVENT_BUS` edges
- Unknown keys are ignored — the format is forward-compatible

Role names (`backend-api`, `frontend`, …) must match the `--repos <role>:<path>` labels used during `/scan`.

---

## What makes it different

- **No product code changes required** to adopt Forge — you describe topology in **`product.md`** / workspace flow.
- **No third-party agent frameworks** in the plugin’s own rules (D5).
- **Auditable brain** — git-backed markdown for decisions, specs, scans, QA, eval.
- **Anti-pattern preambles** on discipline skills — rationalization tables before workflows.
- **Iron laws** on rigid skills — explicit non-negotiables (TDD, eval gate, intake, etc.).
- **Documented edge cases & escalation** — `BLOCKED`, `NEEDS_CONTEXT`, `NEEDS_COORDINATION`, `NEEDS_INFRA_CHANGE`, `DONE_WITH_CONCERNS` across skills.
- **Decision trees** in many skills for repeated judgment calls (contracts, merge order, triage).
- **Optional machine-adjacent hooks** — install per IDE; see `docs/platforms/`.
- **Slash commands** (`commands/*.md`) — each documents **partial** vs **`/forge`** full E2E, **`name:`** / **`description:`**, and **`<HARD-GATE>`** where phases must not blur.

---

## Platform setup

| Platform | Status | Install |
|---|---|---|
| Claude Code | Supported | `.claude-plugin/plugin.json` |
| Cursor | Supported | `.cursor-plugin/plugin.json` + `.cursorrules` |
| Google Antigravity | Supported | `.agent/skills/` + `AGENTS.md` + `GEMINI.md` |
| Gemini CLI / Project IDX | Supported | `gemini-extension.json` |
| OpenAI Codex | Supported | `AGENTS.md` |
| GitHub Copilot CLI | Supported | Session hook + `COPILOT_CLI` |
| OpenCode | Supported | `.opencode/plugins/forge.js` |
| JetBrains AI | Manual | `templates/junie-guidelines.md` → `.junie/guidelines.md` |
| Lovable (UI) | Design + export path | No plugin — lock **GitHub-synced repo** or brain exports per **[`docs/platforms/lovable.md`](docs/platforms/lovable.md)** |

**Guides:** [`docs/platforms/`](docs/platforms/) — **Planning vs execution sessions (all hosts):** [`docs/platforms/session-modes-forge.md`](docs/platforms/session-modes-forge.md) — **Merged `skills/` installs (Cursor, Claude Code, OpenCode copy):** [`docs/platforms/plugin-skill-layout.md`](docs/platforms/plugin-skill-layout.md)

---

## Getting started with an existing project

```
/workspace
```

Forge will guide: product name, repos (URLs or paths), **roles**, and **deploy / run gate** (README or doc path + **`start`** / **`health`** for `product.md` — required for reliable **`eval-product-stack-up`**).

Add infra later:

```
/workspace add-infra <your-slug>
```

Then **`/scan <slug>`** so council and tech plans have **codebase context**.

---

## Describing your product

The **only** file drivers and the conductor read is **`~/forge/brain/products/<slug>/product.md`**. Create or extend it with **`/workspace`** (repos, deploy gate, services) and **`product-context-load`**. There is no bundled copy-template step — edit **`product.md`** directly so flags like **`forge_qa_csv_before_eval`** match how you actually run delivery.

---

## Example: shipping a feature with Forge

Example narrative: **Item favorites with cross-surface sync** (see **[`docs/examples/sample-prd.md`](docs/examples/sample-prd.md)** for shape).

### 1. PRD

Problem, goals, metrics, scope, acceptance criteria.

### 2. Intake (`/intake`)

- **Intake** — all **required `prd-locked.md` sections** elicited **doubt-first**; **any number of user turns**; stop when concrete (scope, success, repos + registry, contracts, timeline, rollback, metrics, and **design** when UI applies).
- **Design / UI** when web/app / user-visible — **design source of truth**, implementable assets or waiver, **`design_intake_anchor`**.

Output: **`~/forge/brain/prds/<task-id>/prd-locked.md`**.

### 3. Council (`/council`)

Four surfaces + five contracts → **`shared-dev-spec.md`**.

### 4. Spec freeze

Immutable until re-negotiation.

### 5. Tech plans (`/plan`)

One plan per repo; **exact paths**, code, commands; TDD ordering inside plans. Use **scan** + contracts as inputs.

### 6. Phase 4 prep (before `/build`)

Per **`conductor-orchestrate`** State 4b (order matters):

1. **`qa-prd-analysis`** → **`qa-manual-test-cases-from-prd`** through approvals → **`manual-test-cases.csv`** + **`[P4.0-QA-CSV]`** — **always** on **`/forge`**; on **partial** runs per **`forge_qa_csv_before_eval`** / charter (else log `skipped=not_required` if intentionally skipped).  
2. **`eval/*.yaml`** + **`[P4.0-EVAL-YAML]`** — at least one scenario (**`eval-scenario-format`**, **`eval-translate-english`**).  
3. **`forge-tdd` RED** + **`[P4.0-TDD-RED]`** per in-scope repo — failing **automated** tests (unit/service/BDD per team) **before** production feature code.  
4. **`[DESIGN-INGEST]`** when net-new UI applies.  
5. Then **P4.1** dispatch (**`/build`** or conductor dispatch).

Using **`/forge`** is intended to **not stop** after tech plans: same sequence through PR set / dream unless **`[ABORT_TASK]`** or **BLOCKED** escalation.

### 7. Build (`/build`)

**`dev-implementer`** in worktrees: RED → GREEN per task.

### 8. Review (`/review`)

Spec + quality; design parity subagents when configured and in scope.

### 9. Eval (`/eval`)

Stack up + drivers; YAML scenarios.

### 10. Self-heal (`/heal`)

If eval fails — up to three repair cycles.

### 11. PR set

Ordered merges with dependency metadata.

### 12. Dream (`/dream`)

Retrospective scoring and brain learnings.

---

## Commands reference

Each file under **`commands/`** has YAML **`name:`** + **`description:`**, optional **`<HARD-GATE>`** blocks, **Forge plugin scope**, and **`vs /forge`** where relevant — so agents know **partial** vs **full** behavior.

| Command | Purpose |
|---|---|
| **`/forge`** | **Full E2E** — invoke **`conductor-orchestrate`** with **`entrypoint = full pipeline (/forge)`**: intake → context → council → tech plans → **State 4b (mandatory QA CSV + eval YAML + TDD RED + design gate)** → dispatch → reviews → **P4.4 eval** → heal → **PR set / merges** → dream/brain. Does **not** stop at planning. |
| **`/workspace`** | Register product **`product.md`**, repos, roles, deploy/runbook (`scan` / eval prerequisites). |
| **`/scan`** | Codebase → brain graph (**`scan-codebase`**); not a substitute for **`/forge`**. |
| **`/intake`** | **Partial** — PRD lock only (**`forge-intake-gate`**, **`intake-interrogate`**). |
| **`/council`** | **Partial** — multi-surface council only; needs locked PRD. |
| **`/plan`** | **Partial** — per-repo tech plans; needs locked **`shared-dev-spec.md`**. |
| **`/build`** | **Partial** — worktrees + **TDD GREEN**; **must not** bypass State 4b gates (**`dev-implementer`**). |
| **`/eval`** | **Partial** — **`forge-eval-gate`**: stack-up + run **`eval/*.yaml`**; does **not** create CSV/YAML. |
| **`/heal`** | **Partial** — self-heal after eval failure (max **3** loops). |
| **`/review`** | **Partial** — **`forge-trust-code`** two-stage review. |
| **`/dream`** | Dreamer retrospective or inline conflict resolution (**`dream-*`**). |
| **`/why`** | **`brain-why`** — decision provenance. |
| **`/recall`** | **`brain-recall`** — search brain. |
| **`/remember`** | **`brain-write`** — record decision / learning. |
| **`/forge-status`** | Read-only brain / plugin snapshot. |
| **`/forge-test`** | **Meta** — **`forge-self-test`** on **bundled seed** product (validates **this** repo), **not** your product’s **`/forge`**. |
| **`/forge-install`** | Show install paths for supported IDEs. |

---

## Repository layout

```
forge/
├── skills/                 # 68 SKILL.md trees (YAML frontmatter)
│   ├── using-forge/        # Bootstrap (session hook injects)
│   ├── conductor-orchestrate/
│   ├── intake-interrogate/
│   ├── council-multi-repo-negotiate/
│   ├── qa-prd-analysis/
│   ├── qa-manual-test-cases-from-prd/
│   ├── forge-tdd/
│   ├── forge-eval-gate/
│   ├── eval-scenario-format/
│   └── …
├── agents/                 # 4 subagent definitions (*.md)
├── commands/               # 17 slash-command docs (*.md)
├── hooks/                  # Hook scripts + IDE-specific hook JSON
├── tools/                  # scan_forge + verify_forge_task.py — see tools/README.md
├── docs/
│   ├── platforms/          # Cursor, Claude Code, …
│   └── examples/
├── templates/              # e.g. JetBrains junie-guidelines (no bundled forge-product; product = brain product.md)
├── .claude-plugin/
├── .cursor-plugin/         # Cursor manifest (plugin.json)
├── .agent/skills/          # Antigravity symlinks → skills/
├── .opencode/plugins/
├── CLAUDE.md / AGENTS.md / GEMINI.md / .cursorrules
├── package.json
└── README.md
```

### Skill types

| `type` | Meaning |
|---|---|
| **rigid** | Follow exactly — gates, TDD, eval, intake |
| **flexible** | Principles with adaptation |
| **reference** | Lookup / layout / glossary |

Rigid skills typically include: **Anti-Pattern Preamble**, **Iron Law**, **Red Flags — STOP**, **Workflow**, **Edge cases**, **Checklist**.

---

## Brain layout

Two common layouts coexist:

1. **`~/forge/brain/products/<slug>/`** — `product.md`, **`codebase/`** (from `/scan`), patterns, optional nested PRD material.

   **`codebase/`** contains:

   | Path | Contents |
   |---|---|
   | `modules/` | One `.md` stub per module — imports, exports, API routes, wikilinks |
   | `classes/` | One `.md` stub per class/type — signatures, cross-repo `SHARED_TYPE` links |
   | `pages/` | One `.md` per source file — static import wikilinks, imported-by back-links |
   | `graph.json` | Full dependency graph (nodes + edges, versioned) |
   | `SCAN.json` | Timestamp, commit SHA, file counts, method inventory, cross-repo edge counts |
   | `SCAN_SUMMARY.md` | Human-readable scan narrative |
   | `cross-repo-automap.md` | All cross-repo edges with provenance labels + unresolved section |
   | `repo-docs/` | Enriched Markdown + OpenAPI snapshots; `SEARCH_INDEX.md`, `INDEX.md`, `index.json` |

2. **`~/forge/brain/prds/<task-id>/`** — **task** artifacts: **`prd-locked.md`**, **`shared-dev-spec.md`**, **`tech-plans/`**, **`eval/`**, **`qa/`** (`PRD_ANALYSIS.md`, **`manual-test-cases.csv`**, reports), **`design/`** (exports, MCP ingest notes), **`council/`** (or team-specific **`reasoning/`** for surface write-ups), eval verdicts, **`conductor.log`** (recommended), etc.

The brain should be a **git repo** so history and provenance are preserved.

---

## Machine verification (optional CI)

Forge does not run inside your compiler. To move Phase 4 checks from **“please follow the skill”** to **“merge is blocked”**, run the stdlib Python verifier against your brain:

```bash
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain
```

It enforces **at least one** `eval/*.yaml`, optional **`conductor.log`** ordering (`[P4.0-EVAL-YAML]` before `[P4.1-DISPATCH]`, **QA CSV + `[P4.0-QA-CSV]`** when **`forge_qa_csv_before_eval: true`**, net-new **design/** or `[DESIGN-INGEST]`), and optional **`--strict-tdd`**.

After a successful **`/forge`** run, **`product.md`** should carry **`forge_qa_csv_before_eval: true`** so this verifier matches **full-pipeline** semantics.

Full reference: **[`docs/forge-task-verification.md`](docs/forge-task-verification.md)**. GitHub Actions template: **[`.github/workflows/forge-brain-guard.yml`](.github/workflows/forge-brain-guard.yml)** (usually copied or invoked from the **brain** repo, not only from Forge).

---

## Orchestration model (automation vs approvals)

- **Skills and subagents** encode **procedure**, **artifacts**, **gates**, and **safe parallelism** (e.g. four council surfaces, multiple **`dev-implementer`** worktrees). They do **not** replace **human** judgment at lock points (intake design, QA CSV sample/count approvals per **`qa-manual-test-cases-from-prd`**, merge rights, secrets).
- **Nothing auto-chains** when a folder updates under **`~/forge/brain/`** — the **next** phase runs when **you** or the **agent** continues (same session or a new one). Say **“execute State 4b next”** or use **`/forge`** for the documented full sequence.
- **Approvals** are concentrated where mistakes are expensive; **bulk work** (reads, drafts, parallel implementation) still benefits from subagents.

---

## Troubleshooting

### Forge not loading

1. See **[`docs/platforms/`](docs/platforms/)** for your IDE.
2. Validate hook JSON under **`hooks/`** (and IDE-specific variants, e.g. **`hooks-cursor.json`**).
3. Restart the IDE; run **`/forge-status`**.

### Skills not discovered

```bash
ls ~/forge/skills/*/SKILL.md | wc -l    # expect 68 from this repository
```

Check YAML frontmatter on any skill that fails to load.

### Eval or stack-up fails

1. Confirm **`product.md`** has **`start`** + **`health`** (or **`deploy_doc`**) per service.
2. Run **`/heal`** with logs from **`~/forge/brain/prds/<task-id>/`** (or product’s eval paths).
3. Re-run **`/scan`** if the codebase map is stale.

### Uninstall

```bash
cd ~/forge && bash scripts/install.sh --uninstall
```

---

## Requirements & license

- **One of:** Claude Code, Cursor, Antigravity, Gemini CLI, Codex, Copilot CLI, OpenCode, JetBrains AI  
- **Git**, **Bash**  
- **Node.js 16+** (install script)

**License:** MIT

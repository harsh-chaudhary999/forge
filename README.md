# Forge

> Plug-and-play multi-repo product orchestration for AI-assisted delivery. Takes a PRD and drives it through locked scope, negotiated contracts, tech plans, TDD implementation, multi-surface eval, review, and coordinated PRs — with a **git-backed brain** as the system of record.

Forge ships a feature across **multiple repos** without embedding a runtime framework in your product code: **skills** (markdown + YAML), **subagents**, **hooks**, and **commands** encode process. **68 skills**, **4 subagents**, **17 slash commands**. Works with **Claude Code, Cursor, Codex, Gemini CLI, Antigravity, Copilot CLI, OpenCode, JetBrains AI** (see [Platform Setup](#platform-setup)).

---

## Table of contents

- [Quick start](#quick-start)
- [What Forge is (and is not)](#what-forge-is-and-is-not)
- [How Forge works](#how-forge-works)
- [Delivery gates (Phase 4)](#delivery-gates-phase-4)
- [Design & UI](#design--ui)
- [QA & test artifacts](#qa--test-artifacts)
- [Codebase knowledge & file targeting](#codebase-knowledge--file-targeting)
- [What makes it different](#what-makes-it-different)
- [Platform setup](#platform-setup)
- [Getting started with an existing project](#getting-started-with-an-existing-project)
- [Describing your product](#describing-your-product)
- [Example: shipping a feature](#example-shipping-a-feature-with-forge)
- [Commands reference](#commands-reference)
- [Repository layout](#repository-layout)
- [Brain layout](#brain-layout)
- [Machine verification (optional CI)](#machine-verification-optional-ci)
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

---

## How Forge works

### End-to-end narrative

```
PRD → Intake → Council → Spec freeze → Tech plans
         → Phase 4 gates (QA CSV†, eval YAML, TDD RED, design ingest‡)
         → Build (GREEN) → Review → Eval (execute) → Self-heal → PR set → Brain / dream
```

† *Optional but recommended; **mandatory** when `forge_qa_csv_before_eval: true` in `product.md`.*  
‡ *When web/app work has **net-new UI** per intake Q9.*

### Pipeline stages (conceptual)

| Stage | What happens | Gate |
|---|---|---|
| **Intake** | **Q1–Q8** always; **Q9 (design / UI)** when web, app, or user-visible UI is in scope. Locks `prd-locked.md` in the brain — including **design source of truth** (`design_intake_anchor`) and implementable design fields when applicable. | HARD-GATE |
| **Council** | Four surfaces (backend, web, app, infra) + five contracts (REST, events, cache, DB, search) negotiate → **`shared-dev-spec.md`**. | HARD-GATE |
| **Spec freeze** | Spec is immutable until re-council. | HARD-GATE |
| **Tech plans** | Per-repo plans: **exact files**, complete code snippets, exact commands (`tech-plan-write-per-project`). Informed by **codebase scan** when present. | Human approval typical |
| **Phase 4** | See [Delivery gates](#delivery-gates-phase-4) — **eval YAML + TDD RED** (and optional QA CSV / design ingest) **before** feature dispatch. | HARD-GATE |
| **Build** | **`dev-implementer`**: TDD GREEN in **isolated worktrees**. | HARD-GATE (TDD) |
| **Review** | Spec + code-quality reviewers; optional **design parity** reviewers when net-new UI and harness supports them. | HARD-GATE |
| **Eval (execute)** | **`eval-product-stack-up`** + multi-surface drivers; scenarios from **`eval/*.yaml`**. | HARD-GATE |
| **Self-heal** | Locate → triage → fix → re-eval; max **3** attempts. | Auto then escalate |
| **PR set** | Merge order with dependency links (`pr-set-merge-order` / `pr-set-coordinate`). | HARD-GATE |
| **Brain / dream** | Retrospectives, learnings, links (`dream-retrospect-post-pr`, brain skills). | Auto |

### Brain as transport

**Council and subagents do not read your live chat.** They read what is written under **`~/forge/brain/`** (e.g. `prd-locked.md`, `shared-dev-spec.md`, `design/`, `qa/`, `eval/`). If design or acceptance lives only in a wiki URL, downstream phases have nothing durable to implement or test against.

---

## Delivery gates (Phase 4)

**`conductor-orchestrate`** defines **State 4b** before **State 5 (dispatch)**:

| Order | Artifact / log | Purpose |
|---:|---|---|
| **0** | **`[P4.0-QA-CSV]`** (when `forge_qa_csv_before_eval: true`) | Approved **`~/forge/brain/prds/<task-id>/qa/manual-test-cases.csv`** — same acceptance inventory TDD and eval should trace to. |
| **1** | **`[P4.0-EVAL-YAML]`** + `eval/*.yaml` (≥1 file) | Executable scenarios for **`eval-coordinate-multi-surface`** / **P4.4**. **No standard waive** for shippable work; only logged **`ABORT_TASK`**. |
| **2** | **`[P4.0-TDD-RED]`** per repo (or logged **`WAIVE_TDD`**) | Failing tests before production feature code (**`forge-tdd`**). |
| **3** | **`[DESIGN-INGEST]`** when **net-new UI** | Materialized design under **`design/`** or locked Figma key + node IDs + ingest notes — unless **`design_waiver: prd_only`**. |
| **4** | **P4.1 dispatch** | Feature implementation only after the above per policy. |

**`dev-implementer`** is instructed to return **`BLOCKED_ORCHESTRATION`** if dispatch skips **`eval/`** or (when the product flag is set) skips approved QA CSV — see `agents/dev-implementer.md`.

---

## Design & UI

- **Intake Q9** (mandatory for web/app / user-visible scope): **`design_intake_anchor`** records the explicit answer to **“single design source of truth”**; implementable paths or **`figma_file_key` + `figma_root_node_ids`**, or a documented waiver — not wiki-only links.
- **Surface skills** (`reasoning-as-web-frontend`, `reasoning-as-app-frontend`): **Figma MCP first** when the host provides it; then REST; human export as fallback.
- **Council / spec-freeze** copy design fields into **`shared-dev-spec.md`**; thin design blocks **block** freeze when net-new UI lacks implementable inputs.

---

## QA & test artifacts

Two **rigid** skills support **manual / TMS-style** acceptance **before** implementation and eval authoring (when you opt in):

| Skill | Role |
|---|---|
| **`qa-prd-analysis`** | Structured PRD analysis → **`~/forge/brain/prds/<task-id>/qa/PRD_ANALYSIS.md`** before bulk CSV work. |
| **`qa-manual-test-cases-from-prd`** | Atomic **CSV** (8 columns + **Source**), estimation, reuse/deprecation tracking, approvals, final report. |

Set in **`templates/forge-product.md`** (copy to your real **`product.md`**):

```yaml
forge_qa_csv_before_eval: false   # true = conductor requires [P4.0-QA-CSV] before [P4.0-EVAL-YAML]
```

**`eval-translate-english`** should reference **CSV `Id`s** in YAML when both exist so **P4.4** exercises the signed inventory.

**Distinction:** **`eval-scenario-format`** = **YAML** for **automated** eval drivers. **`qa-manual-test-cases-from-prd`** = **CSV** for humans / Xray / TestRail style workflows. Both can run; they are not duplicates.

---

## Codebase knowledge & file targeting

1. **`/scan`** runs **`tools/scan_forge/`** → **`~/forge/brain/products/<slug>/codebase/`** (modules, hubs, `SCAN.json`, graphs).
2. **`product-context-load`** surfaces scan metadata and **warns** if scan is missing or **>7 days** old.
3. **`tech-plan-write-per-project`** must list **exact file paths** (plans are what **`dev-implementer`** relies on in isolation).
4. **Implementer** reads the paths and contracts named in the plan — it does not re-derive the repo map from scratch if the plan is complete.

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

**Guides:** [`docs/platforms/`](docs/platforms/)

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

Canonical template: **[`templates/forge-product.md`](templates/forge-product.md)** — copy to **`~/forge/brain/products/<slug>/product.md`**. It includes **services**, **infrastructure**, optional **`forge_qa_csv_before_eval`**, and repo metadata the conductor and eval drivers read.

---

## Example: shipping a feature with Forge

Example narrative: **Item favorites with cross-surface sync** (see **[`docs/examples/sample-prd.md`](docs/examples/sample-prd.md)** for shape).

### 1. PRD

Problem, goals, metrics, scope, acceptance criteria.

### 2. Intake (`/intake`)

- **Q1–Q8** — scope, success, contracts, timeline, rollback, metrics, registry confidence, etc.
- **Q9** when web/app / UI — **design source of truth**, implementable assets or waiver, **`design_intake_anchor`**.

Output: **`~/forge/brain/prds/<task-id>/prd-locked.md`**.

### 3. Council (`/council`)

Four surfaces + five contracts → **`shared-dev-spec.md`**.

### 4. Spec freeze

Immutable until re-negotiation.

### 5. Tech plans (`/plan`)

One plan per repo; **exact paths**, code, commands; TDD ordering inside plans. Use **scan** + contracts as inputs.

### 6. Phase 4 prep (before `/build`)

Per conductor: **QA CSV** (if product flag) → **`eval/*.yaml`** + **`[P4.0-EVAL-YAML]`** → **TDD RED** + **`[P4.0-TDD-RED]`** → **design ingest** if net-new UI → then dispatch.

Skills: **`eval-scenario-format`**, **`eval-translate-english`**, **`forge-tdd`**, **`qa-*`** as needed.

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

| Command | Purpose |
|---|---|
| `/workspace` | Register product repos, roles, deploy/runbook fields |
| `/scan` | Codebase → brain graph (`scan-codebase`) |
| `/forge` | Full pipeline driver |
| `/intake` | PRD lock (Q1–Q8 + Q9 when UI) |
| `/council` | Multi-surface negotiation |
| `/plan` | Per-repo tech plans |
| `/build` | TDD implementation in worktrees |
| `/eval` | Multi-surface eval |
| `/heal` | Self-heal loop |
| `/review` | Two-stage review |
| `/dream` | Dreamer / retrospective |
| `/why` | Decision provenance |
| `/recall` | Search brain |
| `/remember` | Record decision |
| `/forge-status` | Forge / plugin status |
| `/forge-test` | Self-test on seed product |
| `/forge-install` | Install instructions |

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
├── templates/              # forge-product.md, JetBrains, …
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
2. **`~/forge/brain/prds/<task-id>/`** — **task** artifacts: `prd-locked.md`, `shared-dev-spec.md`, **`tech-plans/`**, **`eval/`**, **`qa/`** (PRD analysis, manual CSV, reports), **`design/`** (exports, MCP ingest notes), eval verdicts, etc.

The brain should be a **git repo** so history and provenance are preserved.

---

## Machine verification (optional CI)

Forge does not run inside your compiler. To move Phase 4 checks from **“please follow the skill”** to **“merge is blocked”**, run the stdlib Python verifier against your brain:

```bash
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain
```

It enforces **at least one** `eval/*.yaml`, optional **`conductor.log`** ordering (`[P4.0-EVAL-YAML]` before `[P4.1-DISPATCH]`, QA CSV gate when `forge_qa_csv_before_eval: true`, net-new **design/** or `[DESIGN-INGEST]`), and optional **`--strict-tdd`**.

Full reference: **[`docs/forge-task-verification.md`](docs/forge-task-verification.md)**. GitHub Actions template: **[`.github/workflows/forge-brain-guard.yml`](.github/workflows/forge-brain-guard.yml)** (usually copied or invoked from the **brain** repo, not only from Forge).

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

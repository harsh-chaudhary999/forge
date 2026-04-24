# Forge task verification (machine checks)

Forge’s **skills** and **agents** enforce Phase 4 ordering **procedurally**. This document describes an **optional machine layer**: small **Python** tools that fail CI (or pre-push) when the **brain** is missing required artifacts, `conductor.log` ordering is wrong, or text has **drifted** between PRD and eval/QA files.

## Tools

| Script | Purpose |
|--------|---------|
| [`tools/verify_forge_task.py`](../tools/verify_forge_task.py) | Gates: eval files, log order, QA CSV, design evidence, optional PRD headings, timestamps, single-task brain, optional tech-plan structure |
| [`tools/eval_yaml_stdlib.py`](../tools/eval_yaml_stdlib.py) | Used internally when PyYAML is absent — best-effort eval YAML shape checks |
| [`tools/forge_drift_check.py`](../tools/forge_drift_check.py) | Heuristic: **Success Criteria** bullets from `prd-locked.md` appear as substrings in `eval/*` + `qa/manual-test-cases.csv` (stdlib only) |
| [`tools/verify_tech_plans.py`](../tools/verify_tech_plans.py) | Tech plan headings / `### 1b.2a` placement / `REVIEW_PASS` gate markers — used by **`--strict-tech-plans`** |
| [`tools/append_phase_ledger.py`](../tools/append_phase_ledger.py) | Append one **`phase-ledger.jsonl`** row with **SHA256** for listed task-relative files |
| [`tools/phase_ledger.py`](../tools/phase_ledger.py) | Ledger schema + validation (used by verify and append CLI) |
| [`tools/shared_spec_policy.py`](../tools/shared_spec_policy.py) + [`shared_spec_checklist.json`](../tools/shared_spec_checklist.json) | **`--check-shared-spec`** anchors + TBD/TODO scan |
| [`tools/lint_skill_allowed_tools.py`](../tools/lint_skill_allowed_tools.py) | CI: rigid skills must declare **`allowed-tools`**; optional **`--write-policy`** → [`skill-tool-policy.json`](../tools/skill-tool-policy.json) |

**PyYAML** (optional, recommended in CI): [`tools/requirements-verify.txt`](../tools/requirements-verify.txt). When installed, `--validate-eval-yaml` uses full YAML parse + the same shape rules; otherwise the stdlib helper runs.

**Brain root:** Python CLIs accept **`--brain`**, else **`FORGE_BRAIN`** or **`FORGE_BRAIN_PATH`** (either works), then default **`~/forge/brain`**. Hooks (`session-start.cjs`, `prompt-submit.cjs`) honor the same two env vars.

## What `verify_forge_task.py` checks

| Check | When it fails |
|--------|----------------|
| **Task directory** | `prds/<task-id>/` missing under `--brain` |
| **Eval YAML** | No `*.yaml` / `*.yml` files under `prds/<task-id>/eval/` |
| **`--validate-eval-yaml`** | Each eval file: root `scenario`, non-empty `steps`, each step `id` / `driver` / `action` / non-empty `expected` (PyYAML if available, else `eval_yaml_stdlib`) |
| **`--check-prd-sections`** | `prd-locked.md` missing `# PRD Locked`, mandatory `**…**` lock blocks from intake, or UI-ish **Repos Affected** without **Design / UI** / `design_ui_scope: not applicable` |
| **`--require-conductor-timestamps`** | Any non-comment line containing a `[P…]` phase token lacks a leading ISO-8601 timestamp (see `conductor-orchestrate` **Log Format**) |
| **`--strict-single-task-brain`** | More than one `prds/*/conductor.log` exists (combine with **`--allow-multi-task-brain`** to opt out) |
| **Gate ledger path** | **`--gates-dir`** optional: defaults to `prds/<task-id>/gates/` when that directory exists; if an explicit `--gates-dir` path is missing, the task-local `gates/` is used instead (**INFO** on stderr) |
| **`forge_qa_csv_before_eval: true`** | Resolved `products/<slug>/product.md` (via `--product` or `prd-locked.md` **Product:** matching `name:`) — requires data rows in `qa/manual-test-cases.csv` |
| **Log order** | If `conductor.log` exists: first `[P4.1-DISPATCH]` must not appear before `[P4.0-EVAL-YAML]`; with QA flag, `[P4.0-QA-CSV]` … `approved=yes` must precede `[P4.0-EVAL-YAML]` |
| **Net-new design** | If `prd-locked.md` indicates **design_new_work: yes** and no `design_waiver` … `prd_only`: requires files under `design/` and/or `[DESIGN-INGEST]` before first `[P4.1-DISPATCH]` when a log exists; if the log is missing, **design/** must be non-empty |
| **`--strict-tdd`** | `[P4.0-TDD-RED]` must appear before the first `[P4.1-DISPATCH]` |
| **`--strict-tech-plans`** | When `prds/<task-id>/tech-plans/*.md` exist (excluding `HUMAN_SIGNOFF.md` / `README.md`): each plan must include canonical headings (`### 1b.0`, `### 1b.0b`, `### 1b.2`, `### 1b.2a`, `### 1b.6`), **`### 1b.2a` after** `### 1b.5` / `#### 1b.5b`, a **`Section 1c`** marker, and — if **`Tech plan status: REVIEW_PASS`** — the literals **`<!-- FORGE-GATE:SECTION-0C-INVENTORY:v1 -->`** and **`<!-- FORGE-GATE:CODE-RECROSS:v1 -->`** (see **`skills/tech-plan-self-review/SKILL.md`** Section 0c and **`skills/tech-plan-write-per-project/SKILL.md`** Section 1c). Implemented by [`tools/verify_tech_plans.py`](../tools/verify_tech_plans.py). |
| **`--check-shared-spec`** | `shared-dev-spec.md` (override with **`--shared-spec-path`**) must include anchors from **`shared_spec_checklist.json`** (override with **`--shared-spec-checklist`**) and must not contain **TBD/TODO** outside fenced blocks |
| **`--validate-phase-ledger`** | If **`phase-ledger.jsonl`** exists, every line is valid JSON with **`schema_version`**, **`task_id`**, **`phase_marker`**, **`recorded_at`**, **`artifacts`** |
| **`--require-phase-ledger`** | **`phase-ledger.jsonl`** must exist |
| **`--phase-ledger-verify-hashes`** | Re-hash each **`artifacts[].relpath`** under the task dir and compare to **`sha256`** |

If **`conductor.log`** is absent, **log ordering** checks are skipped by default (warning only). Use **`--require-log`** to fail when the log is missing.

## Usage

```bash
python3 tools/verify_forge_task.py --task-id <task-id> --brain ~/forge/brain
```

```bash
export FORGE_BRAIN=~/forge/brain
# equivalent: export FORGE_BRAIN_PATH=~/forge/brain
python3 tools/verify_forge_task.py --task-id add-2fa --brain ~/forge/brain --product shopapp --strict-tdd
```

**Recommended CI bundle** (after `pip install -r tools/requirements-verify.txt`):

```bash
python3 tools/verify_forge_task.py \
  --task-id add-2fa \
  --brain ~/forge/brain \
  --require-log \
  --validate-eval-yaml
```

**Optional stricter flags** (enable per team; see `forge-brain-guard` env vars):

- `--check-prd-sections`
- `--require-conductor-timestamps`
- `--strict-single-task-brain` (use `--allow-multi-task-brain` if the brain legitimately tracks several tasks)
- `--strict-tech-plans`
- `--check-shared-spec`
- `--validate-phase-ledger` / `--require-phase-ledger` / `--phase-ledger-verify-hashes`

When more than one task has `conductor.log` and strict mode is off, the tool prints a **stderr WARN** — set **`FORGE_TASK_ID`** in hooks and CI (see `using-forge`).

## Phase ledger (`phase-ledger.jsonl`)

Append-only JSONL at **`prds/<task-id>/phase-ledger.jsonl`**. Each line is one object: **`schema_version`**, **`task_id`**, **`phase_marker`**, **`recorded_at`**, **`artifacts`** (array of **`{ "relpath", "sha256" }`** relative to the task directory), optional **`note`**.

Record after you commit eval files (or any artifacts you want attested):

```bash
python3 tools/append_phase_ledger.py --brain ~/forge/brain --task-id add-2fa \
  --phase '[P4.0-EVAL-YAML]' --artifacts eval/smoke.yaml,eval/api.yaml
```

## Drift check (`forge_drift_check.py`)

Brain-repo CI: copy or adapt [`.github/workflows/forge-brain-guard.yml`](../.github/workflows/forge-brain-guard.yml). Set **`FORGE_TASK_ID`** and **`FORGE_TOOLS_REPO`** (`owner/repo` for the sparse checkout of Forge `tools/`).

Extracts bullet lines under **`**Success Criteria:**`** in `prd-locked.md` and checks each (length ≥ 12) appears as a **substring** (case-insensitive) in concatenated `eval/*.yaml|yml|json` and `qa/manual-test-cases.csv`. Without **`--strict`**, missing matches are **WARN** only and exit **0**. With **`--strict`**, exit **1**.

```bash
python3 tools/forge_drift_check.py --task-id add-2fa --brain ~/forge/brain
python3 tools/forge_drift_check.py --task-id add-2fa --brain ~/forge/brain --strict
```

## CI (brain repository)

See [`.github/workflows/forge-brain-guard.yml`](../.github/workflows/forge-brain-guard.yml). Variables: **`FORGE_TASK_ID`** (required), **`FORGE_TOOLS_REPO`** (required — Forge GitHub repo for sparse checkout), plus optional **`FORGE_STRICT_TDD`**, **`FORGE_STRICT_TECH_PLANS`**, **`FORGE_CHECK_PRD_SECTIONS`**, **`FORGE_STRICT_SINGLE_TASK`**, **`FORGE_REQUIRE_CONDUCTOR_TIMESTAMPS`**, **`FORGE_DRIFT_STRICT`**, **`FORGE_CHECK_SHARED_SPEC`**, **`FORGE_VALIDATE_PHASE_LEDGER`**, **`FORGE_REQUIRE_PHASE_LEDGER`**, **`FORGE_PHASE_LEDGER_VERIFY_HASHES`** (wire to matching `verify_forge_task.py` flags).

Sparse checkout should include at least:

```text
tools/verify_forge_task.py
tools/eval_yaml_stdlib.py
tools/phase_ledger.py
tools/shared_spec_policy.py
tools/shared_spec_checklist.json
tools/requirements-verify.txt
tools/forge_drift_check.py
tools/verify_tech_plans.py
```

## Limits

- **`--validate-eval-yaml`** / stdlib helper: validates **shape**, not that URLs, selectors, or drivers match your stack.
- **`--check-prd-sections`**: template-oriented; unusual PRD layouts may need follow-up in intake, not silent loosening of checks.
- **`forge_drift_check`**: substring heuristic — short or generic bullets may false-pass; long nuanced bullets may false-fail.
- **`shared_spec_checklist.json`**: must stay aligned with council template edits; loosen or extend the list when the normative spec outline changes.
- **`phase-ledger.jsonl`**: rows are only as trustworthy as the process that appends them; **`--phase-ledger-verify-hashes`** catches post-append file edits, not malicious ledger edits (git history is the backstop).
- **`--strict-tech-plans`** checks **structure + anchors**, not whether inventory rows are *correct* — humans still judge content; the tool blocks the common slip of **REVIEW_PASS** with no file-backed Section 0c / recross.
- Does **not** validate adjacency/cohort artifacts — see **`docs/adjacency-and-cohorts.md`**; optional: grep **`conductor.log`** for **`[ADJACENCY-SCAN]`**. Tool: **`tools/forge_adjacency_scan.py`** (**`tools/README.md`**).
- These tools do **not** prove eval is **GREEN** or that **stack-up** works — only **committed** artifacts and ordering.
- They do **not** stop a misbehaving LLM in the IDE; they stop **bad commits** and **broken merge candidates** when wired into CI or hooks.

## Portable skill tool policy (any editor)

1. Run **`python3 tools/lint_skill_allowed_tools.py`** in Forge CI (see **`.github/workflows/forge-hooks.yml`**) — fails if any **`type: rigid`** skill lacks **`allowed-tools`**.
2. Regenerate the committed manifest when skills change:  
   **`python3 tools/lint_skill_allowed_tools.py --write-policy tools/skill-tool-policy.json`**
3. **Claude Code** (`pre-tool-use.cjs`): when **`~/.forge/.active-skill`** is set, **`hooks/hooks.json`** should register **PreToolUse** for every tool name your host emits (see matcher in that file — alternation of tool names). Then the hook can enforce **`allowed_tools`** from **`tools/skill-tool-policy.json`** or **`skills/<name>/SKILL.md`**. **`FORGE_ROOT`** may point at a non-default Forge checkout. **HARD-GATE** entries **deny** disallowed tools; others **ask**. Canary and destructive-pattern checks remain **Bash-only**. Other IDEs need their own wiring if you want the same behavior.

## Hooks

- **`session-start.cjs`**: warns when multiple `conductor.log` files exist and **`FORGE_TASK_ID`** is unset or points at a missing log. When a **`conductor.log`** is resolved, it also prepends a short **resume / re-anchor** block (path, last `[P…]` marker, read-this-first hints) before stage stub or full bootstrap — see **`skills/using-forge/SKILL.md`** (*Agent reliability*). Repo also ships **`hooks/session-start`** (shell shim) for **`hooks-cursor.json`** and similar configs.
- **`pre-tool-use.cjs`**: **`/freeze`** scope for Edit/Write/NotebookEdit/StrReplace; skill **`allowed_tools`** when PreToolUse is wired for that tool; Bash-only canary + destructive patterns. When your host adds new tool names, extend **`hooks/hooks.json`** PreToolUse **`matcher`** and **`tools/lint_skill_allowed_tools.py`** **`KNOWN_TOOLS`** so CI and the hook stay aligned.

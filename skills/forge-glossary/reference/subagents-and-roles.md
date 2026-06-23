# Glossary — Subagents, Status Codes & Preamble-Tier

The four Forge subagents (dev-implementer, spec-reviewer, code-quality-reviewer, dreamer), the dev-implementer status-code vocabulary, and the preamble-tier / design_new_work frontmatter fields.

---

## Subagents

### dev-implementer

**Definition:** Subagent that executes tech plan tasks sequentially. Writes tests first (TDD), implements code, and reports status (DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED). Each task runs in an isolated worktree with no shared state (D30).

**Usage Context:** Dispatched once per task from the tech plan. Receives task description, context (PRD, spec, codebase), and success criteria. Reports status at completion. If BLOCKED, escalates to conductor.

**Cross-References:** Related to `worktree-per-project-per-task`, `forge-tdd`. Part of Build stage.

---

### spec-reviewer

**Definition:** Subagent that reads actual code line-by-line and verifies it matches `shared-dev-spec` exactly. Enforces D14: "trust code, not reports." Not allowed to skim or trust summaries. Runs a 9-phase verification scope: (1) API contract compliance, (2) DB schema compliance, (3) event bus contracts, (4) cache contracts, (5) search contracts, (6) cross-service integration wiring, (7) performance guard rails, (8) security requirements, (9) operational readiness (health endpoints, logging, metrics). Also checks for over-building (code not in spec) and under-building (spec requirements not implemented).

**Usage Context:** Invoked during Review stage. Must read full implementation (not diffs or summaries) and cross-reference against spec. Reports APPROVED or CHANGE_REQUESTED with findings per phase.

**Cross-References:** Enforced by `forge-trust-code` (HARD-GATE). Part of Review stage, first stage. Agent definition: `agents/spec-reviewer.md`.

---

### code-quality-reviewer

**Definition:** Subagent that checks 8-point quality framework: (1) Naming Conventions & Clarity, (2) File Size & Organization, (3) Code Complexity & Readability, (4) Error Handling & Resilience, (5) Test Coverage & Quality, (6) Performance & Scalability, (7) Security Practices, (8) Observability & Debuggability. Plus Phase 4 cross-service quality checks (consistent error codes, cache key patterns, event schema field names, class/function naming conventions across services).

**Usage Context:** Invoked during Review stage after spec-reviewer approves. Must read code and apply all 8 checks. Reports APPROVED or CHANGE_REQUESTED with issues categorized as Critical, Important, or Minor.

**Cross-References:** Part of Review stage, second stage. Agent definition: `agents/code-quality-reviewer.md`.

---

### dreamer

**Definition:** Subagent that runs two functions: inline conflict resolution (when eval surfaces incompatibilities between services) and post-merge retrospective (scoring decisions, extracting patterns, writing to brain). Dual role during and after the pipeline.

**Usage Context:** Invoked during eval (if conflicts surface) and after PR set merge. Produces brain artifacts (decisions, learnings, patterns).

**Cross-References:** Uses `dream-resolve-inline`, `dream-retrospect-post-pr`. Related to brain skills.

---

## Subagent Status Codes

| Status | Meaning |
|---|---|
| **DONE** | Task completed successfully, all success criteria met. Proceed to review. |
| **DONE_WITH_CONCERNS** | Task completed but code quality or correctness issues exist. Must be addressed before review. |
| **NEEDS_CONTEXT** | Missing information to complete task (spec ambiguity, missing API docs, unclear requirement). Provide context and re-dispatch. |
| **BLOCKED** | Cannot proceed. Escalate to conductor or human. (Example: required service not available, contract conflict, infrastructure unavailable.) |

---

## Preamble-Tier System

### preamble-tier

**Definition:** Integer (1–4) in a skill's YAML frontmatter that controls how much of the skill's context is inlined into session-start by `session-start.cjs`. Tier 1 = minimal (name + one-line description only); Tier 4 = full content inlined. Higher tiers burn more context budget; use sparingly for skills that must be available before any tool invocation.

**How it works:** On session start, `session-start.cjs` reads the active skill's `preamble-tier` from `~/.forge/.active-skill-tier`. The cache file is **per-active-skill** (global path, tracks whichever skill is currently active). Format: line 1 = tier digit `1`–`4`; line 2 = `# sha256=<hex>` (optional, new format). If line 2 is present and the SHA-256 of the current `SKILL.md` differs, the cache is invalidated and re-parsed. If line 2 is absent (older single-line format written by `echo N > ~/.forge/.active-skill-tier`), hash validation is skipped — the tier is used as-is. The tier determines how many sections are serialized into the IDE's system prompt injection.

**Usage Context:** Set `preamble-tier: 1` for most skills (name + description sufficient). Set `preamble-tier: 3` or `preamble-tier: 4` only for foundational skills (`using-forge`, `forge-glossary`) that must deliver orientation context on every session. Never set `preamble-tier: 4` on a skill that has 500+ lines — it will saturate context.

**Cross-References:** `using-forge` § **`~/.forge/.active-skill-tier`** (cache format). `session-start.cjs` implements the read/write logic.

---

### design_new_work

**Definition:** Boolean field in `prd-locked.md` (from `intake-interrogate` Q9) indicating whether the PRD requires net-new UI design artifacts. When `design_new_work: yes`, the pipeline MUST run State 4b-design (`conductor-orchestrate`) before P4.1 dispatch — materializing design to `~/forge/brain/prds/<task-id>/design/` (Figma MCP ingest, Lovable sync, or manual exports) and logging `[DESIGN-INGEST] status=PASS` to `conductor.log`. When `design_new_work: no` or `design_waiver: prd_only`, State 4b-design is skipped.

**How to set:** During `intake-interrogate` Q9, the agent asks whether new UI design artifacts are required. If yes, write `design_new_work: yes` in the YAML frontmatter of `prd-locked.md`. If no new design, write `design_new_work: no` (or `design_waiver: prd_only` with owner + risk justification).

**Artifact Traceability:** `intake-interrogate Q9` → `prd-locked.md design_new_work: yes` → `State 4b-design` → `~/forge/brain/prds/<task-id>/design/MCP_INGEST.md` (or `LOVABLE_SYNC.md`) → `[DESIGN-INGEST] status=PASS` in `conductor.log` → P4.1 dispatch unlocked for web/app repos.

**Cross-References:** `conductor-orchestrate` § State 4b-design; `intake-interrogate` Q9; `docs/conductor-log-format.md` `[DESIGN-INGEST]`.

# Glossary — Pipeline Stages

The sequential phases of the Forge delivery pipeline, in order: Intake → Council → Spec Freeze → Tech Plan → Build → Eval → Self-Heal → Review → PR Set → Dream.

---

### Intake

**Definition:** The first non-skippable phase where a PRD is interrogated, confidence-first, until every mandatory `prd-locked.md` lock field (Q1–Q9, plus a conditional Q10 when the implementation-closure gate applies) is concrete — not a fixed count of questions; see `intake-interrogate`. Produces a locked PRD artifact.

**Usage Context:** Triggered at the start of every Forge run. The conductor invokes `forge-intake-gate` to execute intake. Output is immutable — no scope changes after intake without restarting the pipeline.

**What It's NOT:** Not a casual discussion or brainstorm. Not optional. Not a place to add features mid-interview. Not informal — every answer is logged in the brain with provenance (who answered, when, why that interpretation).

**Cross-References:** Enforced by `forge-intake-gate` (HARD-GATE). Output feeds into `Council`. Related to PRD lock.

---

### Council

**Definition:** Multi-surface contract negotiation where 4 domain surfaces (backend, web frontend, app frontend, infrastructure) reason about the locked PRD and agree on 5 contracts (REST APIs, event bus, cache, database schema, search). Produces the `shared-dev-spec`.

**Usage Context:** Runs after intake. Each surface reasons independently from its domain perspective, then surfaces negotiate compatibility. Results in a single canonical spec that all repos follow. Cannot proceed to build until council produces a frozen spec.

**What It's NOT:** Not a debate where one surface "wins." Not technical design — it's contract negotiation (interfaces, not implementation). Not optional; all 4 surfaces must participate. Not quick — requires disciplined negotiation across multiple services.

**Cross-References:** Enforced by `forge-council-gate` (HARD-GATE). Uses `reasoning-as-backend`, `reasoning-as-web-frontend`, `reasoning-as-app-frontend`, `reasoning-as-infra`. Output is the `shared-dev-spec`. Involves contract skills: `contract-api-rest`, `contract-event-bus`, `contract-cache`, `contract-schema-db`, `contract-search`.

---

### Spec Freeze

**Definition:** Immutable lock on `shared-dev-spec` after council completes. Changes are not allowed without full re-negotiation through council. Signals transition from design to implementation.

**Usage Context:** Invoked via `spec-freeze` skill after council concludes. Once frozen, the spec becomes the single source of truth for all tasks in `Tech Plan`. Any surface discovering a conflict during build must escalate (not proceed).

**What It's NOT:** Not a soft freeze. Not a guideline. Not flexible to "quick fixes." Once frozen, the spec cannot be modified by individual repos or developers — it requires re-opening council.

**Cross-References:** Output of `Council`. Input to `Tech Plan`. Related to D24 (HARD-GATE discipline).

---

### Tech Plan

**Definition:** Per-project breakdown of the `shared-dev-spec` into bite-sized implementation tasks (2–5 minutes each), with exact code snippets and exact commands. One tech plan per repository.

**Usage Context:** Generated after spec freeze via `tech-plan-write-per-project`. Each task is atomic, measurable, and follows a standard format: description, code, commands, success criteria. Dev-implementer consumes these tasks sequentially in isolated worktrees.

**What It's NOT:** Not a high-level roadmap. Not aspirational. Not flexibility for developers to improvise. Each task has exact code and commands — deviation is a red flag requiring escalation.

**Cross-References:** Generated from `shared-dev-spec`. Consumed by `Build`. Related to D15 (TDD pressure scenarios).

---

### Build

**Definition:** TDD implementation phase where `dev-implementer` subagent executes each task from the tech plan in an isolated worktree, writing tests first, then code. Produces code ready for review.

**Usage Context:** Triggered after tech plan is complete. Dev-implementer is dispatched once per task. Each task runs in a fresh git worktree (D30) with no shared state. Reports status (DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED) at task completion.

**What It's NOT:** Not exploratory development. Not "let's see what works." Not a place to refactor specs. Not allowed to skip TDD — `forge-tdd` is a HARD-GATE.

**Cross-References:** Implements tasks from `Tech Plan`. Enforced by `forge-tdd` (HARD-GATE). Output goes to `Review`. Related to `worktree-per-project-per-task` (D30).

---

### Eval

**Definition:** End-to-end product test that brings up the full stack (all services), executes evaluation scenarios (user journeys, cross-service flows), and verifies critical success criteria. Produces a verdict (GREEN, YELLOW, RED).

**Usage Context:** Runs after code is merged. Multiple eval drivers coordinate: API (HTTP), database (MySQL), cache (Redis), event bus (Kafka), search (Elasticsearch), web UI (Chrome DevTools Protocol), mobile (XCTest, ADB). All drivers report results to `eval-judge` which renders a verdict.

**What It's NOT:** Not unit testing — it's integration testing at scale. Not optional; all critical scenarios must pass. Not local — assumes full multi-service stack is running. Not quick fixes during eval — failures require escalation to `self-heal` loop.

**Cross-References:** Enforced by `forge-eval-gate` (HARD-GATE). Uses eval drivers: `eval-driver-api-http`, `eval-driver-db-mysql`, `eval-driver-cache-redis`, `eval-driver-bus-kafka`, `eval-driver-search-es`, `eval-driver-web-cdp`, `eval-driver-ios-xctest`, `eval-driver-android-adb`. Output feeds into `Self-Heal` (RED verdict) or `Review` (GREEN/YELLOW verdict).

---

### Self-Heal

**Definition:** Automated fault-finding and repair loop triggered by a RED eval verdict. Sequences: locate fault → triage → fix → verify. Max 3 retries before escalation to human.

**Usage Context:** When eval returns RED, self-heal is invoked. `self-heal-locate-fault` identifies which service failed, `self-heal-triage` classifies the failure, `self-heal-systematic-debug` repairs, then eval re-runs. If 3 retries fail, escalates (BLOCKED).

**What It's NOT:** Not a blanket retry mechanism. Not allowed to modify the spec. Not permitted to work around failures — must find root cause. Not infinite retries — capped at 3 by `self-heal-loop-cap`.

**Cross-References:** Triggered by RED eval verdict. Uses `self-heal-locate-fault`, `self-heal-triage`, `self-heal-systematic-debug`, `self-heal-loop-cap`. Can escalate to `Review` after 3 retries fail.

---

### Review

**Definition:** Two-stage code quality gate. First stage: `spec-reviewer` verifies implementation matches `shared-dev-spec` line-by-line in actual code. Second stage: `code-quality-reviewer` checks 8-point quality framework, performance, security, and observability.

**Usage Context:** Runs after eval passes (GREEN or YELLOW). Both reviewers read actual code (D14: trust code), not reports. Produces APPROVED or CHANGE_REQUESTED. Required before PR merge.

**What It's NOT:** Not a formality. Not allowed to approve without reading code. Not a place to nitpick style — only substantial quality and spec compliance. Not optional; all PRs must pass both stages.

**Cross-References:** Triggered by passing eval. Enforced by `forge-trust-code` (HARD-GATE). Uses spec-reviewer and code-quality-reviewer subagents. Output feeds into `PR Set` merge coordination.

---

### Dream

**Definition:** Post-merge retrospective where the `dreamer` subagent scores decisions, extracts patterns, and writes learnings to the `brain`. Captures what worked, what failed, and why.

**Usage Context:** Runs after all PRs in the `PR Set` are merged and feature is live. Dreamer reviews eval results, conflict resolutions, code review feedback, and produces structured learnings. These learnings inform future PRD interpretations and skill enhancements.

**What It's NOT:** Not a blame session. Not informal chat. Not optional — every shipped feature produces brain artifacts. Not skipped even for "small" features.

**Cross-References:** Triggered after `PR Set` merge. Uses `dream-retrospect-post-pr` skill. Outputs to `brain` via `brain-write`. Related to `brain-recall` for future pattern matching.

---

### PR Set

**Definition:** Coordinated set of pull requests across multiple repositories that must be merged in dependency order (services that others depend on merge first). Ensures cross-service compatibility during merge.

**Usage Context:** After review passes, all PRs are staged as a `PR Set`. `pr-set-coordinate` creates all PRs simultaneously, then `pr-set-merge-order` determines merge sequence. Merges proceed in order; downstream repos can only merge after dependencies are live.

**What It's NOT:** Not independent per-repo PRs. Not "merge whenever." Not allowed to reorder without service team sign-off. Not skipped for "simple" features.

**Cross-References:** Output of `Review`. Uses `pr-set-coordinate` and `pr-set-merge-order`. Related to `council` (which negotiates service boundaries).

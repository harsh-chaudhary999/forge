---
name: forge-glossary
description: "Forge glossary. Terms and definitions in Forge context. Look up when encountering unfamiliar Forge terminology."
type: reference
---
# Forge Glossary

## Pipeline Stages

### Intake

**Definition:** The first non-skippable phase where a PRD is interrogated through 8 structured questions that lock scope, success criteria, constraints, and cross-service boundaries. Produces a locked PRD artifact.

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

---

## Core Concepts

### Skill

**Definition:** A reusable, discipline-enforcing capability packaged as a `SKILL.md` file with YAML frontmatter (name, description, type, requires). Skills can be rigid (must follow exactly) or flexible (principles-based). Each skill has optional red flags (STOP conditions), anti-patterns (common excuses), and edge cases (unusual scenarios).

**Usage Context:** Invoked via the `invoke` command or through skill dependencies. A skill can require other skills, forming a dependency tree. Skills are discovered in `skills/` directory (repo root) and symlinked from `.claude/skills/`. When you invoke a skill, the harness renders the markdown and passes context (PRD, spec, codebase) as needed.

**What It's NOT:** Not a tool (tools are CLI utilities). Not a hook (hooks are session-level plugins). Not an agent (agents are independent processes). Not a prompt — skills are reusable references that adapt to your context.

**Cross-References:** Related to `superpowers` (discipline-enforcing skills from Anthropic). Similar format to `agent` but lightweight. Enforced by `forge-skill-anatomy` (format checklist).

---

### Rigid Skill

**Definition:** A skill that must be followed exactly as written, with no adaptation or shortcutting. Enforced by HARD-GATE markers and TDD pressure tests. Examples: `forge-tdd`, `forge-intake-gate`, `forge-eval-gate`.

**Usage Context:** When you invoke a rigid skill, you are agreeing to follow every step. Deviations are red flags. Rigid skills typically have anti-pattern preambles (D25) that rationalize common excuses and rebut them.

**What It's NOT:** Not flexible. Not subject to interpretation. Not "follow the spirit but skip steps." Not negotiable with schedule pressure.

**Cross-References:** Contrast with `flexible-skill`. Enforced by D24 (HARD-GATE tags on non-skippable steps). Related to D15 (TDD pressure).

---

### Flexible Skill

**Definition:** A skill that establishes principles and constraints but allows adaptation to context. Example: contract negotiation skills use a framework but adapt to service-specific boundaries. Developers can skip optional sections if justified.

**Usage Context:** Invoke a flexible skill and apply its principles to your specific scenario. Document deviations. Flexible skills typically have edge cases (unusual conditions) that guide when to adapt vs. when to escalate.

**What It's NOT:** Not a free pass to ignore it. Not "do whatever you want." Not permission to skip mandatory sections. Flexible skills still enforce core discipline — just with more context-sensitivity.

**Cross-References:** Contrast with `rigid-skill`. Examples: reasoning skills (`reasoning-as-backend`, `reasoning-as-web-frontend`), contract skills.

---

### Red Flag

**Definition:** An explicit STOP condition embedded in a skill that signals the skill cannot proceed as written. Red flags are safety valves — they prevent silent failures and force escalation. Each red flag is a single condition that, if true, halts execution.

**Usage Context:** When executing a skill, check red flags before each major step. If a red flag condition is met, stop and escalate (do not rationalize or work around). Examples: "if service is not responding, RED FLAG: BLOCKED"; "if more than 3 retries fail, RED FLAG: escalate."

**What It's NOT:** Not a warning. Not a hint to be careful. Not optional. Not a place for judgment — if condition is true, you must escalate.

**Cross-References:** Often paired with anti-patterns (common excuses NOT to apply red flags). Enforced by D24. Related to `escalation` (next step after RED FLAG).

---

### Anti-Pattern

**Definition:** A rationalization table (D25) that lists common excuses for skipping a discipline and rebuts each one. Embedded at the top of every discipline-enforcing skill. Example: forge-tdd lists "We're running late" → rebuttal: "TDD saves time because fewer bugs slip through."

**Usage Context:** Before skipping any required step, consult the anti-pattern preamble. If your excuse is listed, read the rebuttal. If your excuse is NOT listed, escalate (do not improvise). Anti-patterns are git-backed and immutable — they evolve through dreamer retrospectives but never disappear.

**What It's NOT:** Not permission to skip steps if your excuse isn't listed. Not a menu of excuses — it's a rebuttal table. Not formal policy; it's discipline enforcement via language.

**Cross-References:** Required by D25. Paired with red flags. Related to HARD-GATE skills. Examples in `forge-tdd`, `forge-intake-gate`, `forge-eval-gate`.

---

### HARD-GATE

**Definition:** A non-negotiable process gate marked with a HARD-GATE label. Enforced by 5+ MUST bullets that cannot be skipped or rationalized away. Examples: intake (MUST interrogate 8 questions), council (MUST negotiate all contracts), eval (MUST pass critical scenarios), TDD (MUST write test first).

**Usage Context:** When you encounter a HARD-GATE, you have no choice but to execute it fully. It cannot be shortcut due to schedule pressure, complexity, or other factors. Red flags within HARD-GATE steps are not advisory — they are mandatory stop conditions.

**What It's NOT:** Not advisory. Not "try to do this if possible." Not flexible to context. Not negotiable with stakeholders or schedule.

**Cross-References:** Enforced by D24. Every HARD-GATE has associated skill. Examples: `forge-intake-gate`, `forge-council-gate`, `forge-eval-gate`, `forge-tdd`, `forge-worktree-gate`, `forge-trust-code`, `forge-verification`, `forge-letter-spirit`.

---

### Superpowers

**Definition:** Collection of 10 discipline-enforcing skills from Anthropic (not Forge-specific) that cover planning, testing, debugging, code review, and development workflows. Superpowers are universal; Forge skills are product-specific. Superpowers include: writing-plans, brainstorming, executing-plans, dispatching-parallel-agents, test-driven-development, systematic-debugging, requesting-code-review, receiving-code-review, verification-before-completion, finishing-a-development-branch.

**Usage Context:** Use superpowers when facing any task that matches their domain. Example: before implementation, invoke `superpowers:writing-plans`. During test-driven development, invoke `superpowers:test-driven-development`. Superpowers often parallel Forge skills but provide deeper guidance.

**What It's NOT:** Not Forge-specific. Not baked into Forge pipeline — they are parallel resources you invoke as needed. Not required (though highly recommended). Not limited to Forge work — applicable to any Claude project.

**Cross-References:** Related to Forge skills but orthogonal. Invoked alongside rigid/flexible skills. Examples: `superpowers:test-driven-development` parallels `forge-tdd`, `superpowers:writing-plans` parallels `tech-plan-write-per-project`.

---

### Phase

**Definition:** Sequential batch of skill enhancements organized in the Forge roadmap. Each phase adds anti-patterns, edge cases, and decision trees to existing skills. Phases: P0 (foundation, complete), P1 (critical eval drivers, complete), P2 (surface reasoning + brain + deployment, complete), P3 (remaining skills, in progress).

**Usage Context:** Phases guide skill maturity. P0 skills are foundational (always required). P1 skills enable multi-service eval. P2 skills add depth to reasoning and operations. P3 skills expand coverage to remaining domains. When invoking a skill, check which phase it's in — earlier phases are more stable.

**What It's NOT:** Not arbitrary groupings. Not a "nice to have" roadmap. Not flexible timelines — phases complete in order before moving forward. Not skippable — all phases are required for full Forge capability.

**Cross-References:** Related to `batch` (finer-grained grouping within a phase). Examples: P0 (intake, council, build), P1 (eval drivers: API, DB, cache, search, events), P2 (reasoning skills + brain skills + deploy drivers), P3 (remaining skills).

---

### Batch

**Definition:** Finer-grained grouping of related skills within a phase. Example: P1 has 3 eval driver batches (HTTP/DB, cache/search, events/mobile) and 1 coordination batch (eval-judge, dream-resolve). P2 has 3 batches (reasoning, brain, deployment).

**Usage Context:** Batches allow parallel work within a phase. If phase P2 Batch 1 (reasoning skills) is complete, you can start using those skills while Batch 2 (brain skills) is still in development. Batches ship together but are tracked separately.

**What It's NOT:** Not independent from phases — batches are subdivisions of phases. Not arbitrary — batches group skills with strong dependencies.

**Cross-References:** Subdivides `phase`. Examples: P2 Batch 1 (reasoning-as-backend, reasoning-as-web-frontend, reasoning-as-app-frontend), P2 Batch 2 (brain-read, brain-write, brain-recall, brain-why, brain-forget), P2 Batch 3 (deploy-driver-pm2-ssh, deploy-driver-docker-compose, deploy-driver-local-process, deploy-driver-systemd).

---

### P0/P1/P2/P3

**Definition:** Phase numbering for the Forge skill enhancement roadmap. P0: foundation skills (intake, council, spec-freeze, tech-plan, build, eval, review, dream). P1: critical eval drivers (API, DB, cache, search, events, web, mobile). P2: surface reasoning + brain operations + deployment drivers. P3: remaining skills (in progress).

**Usage Context:** Check phase number to understand skill maturity and feature completeness. P0 skills are required and stable. P1 skills enable multi-service product testing. P2 skills add reasoning depth and decision tracking. P3 skills expand to specialized domains.

**What It's NOT:** Not marketing phases. Not "versions." Not flexible — phase order is locked.

**Cross-References:** Each phase contains multiple `batch`es. Progress tracked in memory file at `/home/lordvoldemort/.claude/projects/-home-lordvoldemort-Videos-forge/memory/MEMORY.md`.

---

### Seed Product

**Definition:** ShopApp — a test e-commerce product used to pressure-test all Forge skills via realistic scenarios. Includes backend (Node.js), web frontend (React), mobile app (React Native or native), and infrastructure (Docker, Kubernetes). Lives in `seed-product/` directory.

**Usage Context:** Every skill is validated against ShopApp before shipping. D15 requires all skills be TDD'd against seed product pressure scenarios. When developing a new skill, build a scenario on ShopApp first, then write the skill to handle it.

**What It's NOT:** Not the only product Forge can work on — ShopApp is the validation vehicle. Not a finished product — it's intentionally simple to isolate skill behavior. Not source of truth for Forge patterns; it's a test bed.

**Cross-References:** Related to D15 (TDD pressure scenarios). Used by skill tests. Part of `forge-self-test`.

---

### Surface

**Definition:** A domain perspective in council and evaluation: backend (database, APIs, business logic), web frontend (browser UI, React), app frontend (mobile, native), infrastructure (deployment, operations). Each surface reasons about the PRD from its specialized viewpoint.

**Usage Context:** During council, 4 surfaces negotiate contracts from their perspectives. During eval, surface-specific eval drivers test the surface (web-cdp for web, xctest for iOS, adb for Android, API for backend, DB for schema). When reasoning about a PRD, switch surfaces to see blind spots in your design.

**What It's NOT:** Not vertical layers (frontend/backend split). Not silos — surfaces must negotiate with each other. Not optional — all 4 surfaces must participate in council.

**Cross-References:** Used by council via `reasoning-as-backend`, `reasoning-as-web-frontend`, `reasoning-as-app-frontend`, `reasoning-as-infra`. Tested by surface-specific eval drivers.

---

### Discipline

**Definition:** Non-negotiable practice embedded in Forge skills (TDD, HARD-GATE, two-stage review, isolation). Disciplines are enforced by anti-patterns (D25) and red flags (D24). Examples: test-driven-development (discipline), HARD-GATE enforcement (discipline), two-stage review (discipline), worktree isolation (discipline).

**Usage Context:** When a skill enforces discipline, follow it exactly. Disciplines prevent the most common sources of bugs: untested code, unreviewed changes, shared state, incomplete specifications. If schedule pressure tempts you to skip a discipline, consult the skill's anti-pattern preamble.

**What It's NOT:** Not bureaucracy. Not optional. Not "suggestions for quality." Not flexible to urgency or context.

**Cross-References:** Enforced by D24 (HARD-GATE tags) and D25 (anti-pattern preambles). Examples: `forge-tdd`, `forge-trust-code`, `forge-worktree-gate`, `spec-freeze`.

---

### Contract

**Definition:** Explicit negotiated specification for the interface between services. Covers: REST APIs (methods, endpoints, payloads), event bus (topic names, message schema), cache (keys, TTL, invalidation), database (table names, schema, migrations), search (document structure, analyzers). Contracts are part of `shared-dev-spec`.

**Usage Context:** During council, services negotiate contracts. Each contract defines what data flows where, when, and in what format. Implementation must match contracts exactly (enforced by spec-reviewer). Changes to contracts require re-opening council.

**What It's NOT:** Not internal API design. Not documentation of what you built — it's the agreement before you build. Not flexible post-lock. Not micro-optimization territory.

**Cross-References:** Negotiated by `council-multi-repo-negotiate`. Skills: `contract-api-rest`, `contract-event-bus`, `contract-cache`, `contract-schema-db`, `contract-search`. Part of `shared-dev-spec`. Verified by `spec-reviewer` in review stage.

---

### Driver

**Definition:** Implementation skill that "drives" a system by connecting to it, running operations, and verifying state. Two types: eval drivers (connect, run scenarios, verify results) and deploy drivers (start/stop services, check health). Examples: `eval-driver-api-http` (connect via HTTP, run API calls), `deploy-driver-docker-compose` (start containers, verify running).

**Usage Context:** Eval drivers are invoked during eval stage to test each service. Deploy drivers are invoked to bring up the stack for eval or production. Each driver exposes functions (connect, disconnect, run, verify) that skills use to automate integration tests.

**What It's NOT:** Not unit tests. Not mocks. Not local-only — drivers assume services are running. Not hardcoded to one service — drivers are reusable across products.

**Cross-References:** Eval drivers: `eval-driver-api-http`, `eval-driver-db-mysql`, `eval-driver-cache-redis`, `eval-driver-bus-kafka`, `eval-driver-search-es`, `eval-driver-web-cdp`, `eval-driver-ios-xctest`, `eval-driver-android-adb`. Deploy drivers: `deploy-driver-pm2-ssh`, `deploy-driver-docker-compose`, `deploy-driver-local-process`, `deploy-driver-systemd`. Coordinated by `eval-coordinate-multi-surface`, `eval-product-stack-up`.

---

### Escalation

**Definition:** Signal that human judgment, context, or coordination is needed. Triggered by red flags, unrecovered failures, or scope ambiguity. Keywords: BLOCKED, NEEDS_CONTEXT, NEEDS_COORDINATION, NEEDS_INFRA_CHANGE. Escalation is not failure — it's the correct response when automation cannot proceed.

**Usage Context:** When a skill hits a red flag, escalate immediately (do not work around). When dev-implementer reports BLOCKED, escalate to conductor. When eval fails 3 times, escalate. When contracts conflict, escalate. Escalation triggers human review, context addition, or re-negotiation.

**What It's NOT:** Not a rare event. Not a sign of incompetence. Not shameful. Not the same as failure. Not permitting continued work around the issue.

**Cross-References:** Related to red flags, self-heal retry cap, dev-implementer status codes. Handled by conductor or human team.

---

## Subagents

### dev-implementer

**Definition:** Subagent that executes tech plan tasks sequentially. Writes tests first (TDD), implements code, and reports status (DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED). Each task runs in an isolated worktree with no shared state (D30).

**Usage Context:** Dispatched once per task from the tech plan. Receives task description, context (PRD, spec, codebase), and success criteria. Reports status at completion. If BLOCKED, escalates to conductor.

**Cross-References:** Related to `worktree-per-project-per-task`, `forge-tdd`. Part of Build stage.

---

### spec-reviewer

**Definition:** Subagent that reads actual code line-by-line and verifies it matches `shared-dev-spec` exactly. Enforces D14: "trust code, not reports." Not allowed to skim or trust summaries.

**Usage Context:** Invoked during Review stage. Must read full implementation (not diffs or summaries) and cross-reference against spec. Reports APPROVED or CHANGE_REQUESTED.

**Cross-References:** Enforced by `forge-trust-code` (HARD-GATE). Part of Review stage, first stage.

---

### code-quality-reviewer

**Definition:** Subagent that checks 8-point quality framework (readability, maintainability, testability, error handling, consistency, performance, security, observability) plus cross-cutting concerns (race conditions, deadlocks, injection attacks).

**Usage Context:** Invoked during Review stage after spec-reviewer approves. Must read code and apply framework. Reports APPROVED or CHANGE_REQUESTED.

**Cross-References:** Part of Review stage, second stage.

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

## Decision References (D1-D30)

Key locked decisions:

| Decision | Summary |
|---|---|
| D5 | No third-party agent frameworks (no LangChain, Playwright, Puppeteer) |
| D13 | No runtime dependency on any external plugin at runtime |
| D14 | Trust code: spec-reviewer reads actual code, not reports or summaries |
| D15 | Skills are TDD'd against seed product pressure scenarios |
| D24 | HARD-GATE tags on every non-skippable step; red flags enforce them |
| D25 | Anti-Pattern preambles on every discipline-enforcing skill |
| D30 | Fresh worktree per project per task. No shared state. |

---

## Eval Verdicts

| Verdict | Meaning | Next Step |
|---|---|---|
| **GREEN** | All critical scenarios passed. Ready to merge. | Proceed to Review stage. |
| **YELLOW** | All critical passed, some non-critical failed. Decide: fix or accept trade-off. | Review or return to Self-Heal. |
| **RED** | Critical scenario failed. Cannot merge. | Enter Self-Heal loop (max 3 retries). |

---

## Quick Reference: Pipeline Flow

1. **Intake** (HARD-GATE) → lock PRD
2. **Council** (HARD-GATE) → negotiate contracts, produce shared-dev-spec
3. **Spec Freeze** → lock shared-dev-spec
4. **Tech Plan** → break spec into per-project tasks
5. **Build** (HARD-GATE: TDD) → dev-implementer executes tasks
6. **Review** (two-stage: spec + quality) → spec-reviewer, code-quality-reviewer
7. **PR Set** → coordinate PRs across repos in merge order
8. **Eval** (HARD-GATE) → multi-driver product test
9. **Self-Heal** (if RED) → locate fault, triage, fix, re-test (max 3 retries)
10. **Dream** → retrospective, learnings to brain

---

## Quick Reference: Key Skills by Category

**HARD-GATE Skills:**
`forge-intake-gate`, `forge-council-gate`, `forge-eval-gate`, `forge-tdd`, `forge-worktree-gate`, `forge-trust-code`, `forge-verification`, `forge-letter-spirit`

**Reasoning Skills (Council):**
`reasoning-as-backend`, `reasoning-as-web-frontend`, `reasoning-as-app-frontend`, `reasoning-as-infra`

**Contract Skills (Council):**
`contract-api-rest`, `contract-event-bus`, `contract-cache`, `contract-schema-db`, `contract-search`

**Eval Drivers:**
`eval-driver-api-http`, `eval-driver-db-mysql`, `eval-driver-cache-redis`, `eval-driver-bus-kafka`, `eval-driver-search-es`, `eval-driver-web-cdp`, `eval-driver-ios-xctest`, `eval-driver-android-adb`

**Deploy Drivers:**
`deploy-driver-pm2-ssh`, `deploy-driver-docker-compose`, `deploy-driver-local-process`, `deploy-driver-systemd`

**Brain Skills:**
`brain-read`, `brain-write`, `brain-recall`, `brain-why`, `brain-forget`, `brain-link`

**Self-Heal Skills:**
`self-heal-locate-fault`, `self-heal-triage`, `self-heal-systematic-debug`, `self-heal-loop-cap`

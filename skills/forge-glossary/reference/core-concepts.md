# Glossary — Core Concepts

Canonical artifacts (shared-dev-spec, product.md, prd-locked.md, terminology.md, brain layout), the skill/discipline vocabulary (Skill, Rigid/Flexible Skill, Red Flag, Anti-Pattern, HARD-GATE, Discipline), roadmap terms (Phase, Batch, P0/P1/P2/P3), and the cross-cutting nouns (Surface, Contract, Driver, Escalation, Superpowers, Seed Product, worktree-per-project-per-task).

---

### shared-dev-spec.md

**Definition:** The canonical contract document produced by `Council` and locked by `spec-freeze`. Lives at `~/forge/brain/prds/<task-id>/shared-dev-spec.md`. Contains all 5 service contracts negotiated by the 4 surfaces: REST API (endpoints, payloads, status codes), event bus (topics, schemas), cache (keys, TTL, invalidation), database (tables, schema, migrations), search (document structure, analyzers). Immutable after `[P2-SPEC-FROZEN]` — changes require full SPEC-AMENDMENT Protocol (council re-vote + new `[P2-SPEC-AMENDED]` marker).

**Usage Context:** All downstream phases read from this file. `tech-plan-write-per-project` breaks it into per-repo tasks. `spec-reviewer` verifies implementation matches it line-by-line. `forge-drift-check` detects divergence. Do not modify post-freeze without re-opening council.

**What It's NOT:** Not a living document. Not per-repo. Not aspirational. Not a "first draft" — it is the signed contract.

**Cross-References:** Written by `council-multi-repo-negotiate`; locked by `spec-freeze`; read by `tech-plan-write-per-project`, `spec-reviewer`, `forge-drift-check`; amended via `spec-freeze` § SPEC-AMENDMENT Protocol.

---

### product.md

**Definition:** Per-product workspace config file at `~/forge/brain/products/<slug>/product.md`. Contains: product slug, repo paths (role → absolute path), start/health commands per service, `deploy_doc` for services with complex startup, and flags. The most important flag is `forge_qa_csv_before_eval` (boolean) — when `true` or when the entrypoint is `/forge`, `qa-manual-test-cases-from-prd` is mandatory before `[P4.0-SEMANTIC-EVAL]`.

**Key fields:**
- `forge_qa_csv_before_eval: true|false` — gates manual QA CSV requirement
- `repos:` — role-to-path map (e.g., `backend: /abs/path/to/backend`)
- `start:` — how to start each service for eval
- `health:` — health check command per service

**Cross-References:** Read by `conductor-orchestrate`, `eval-product-stack-up`, `deploy-driver-*`; `forge_qa_csv_before_eval` enforced by `conductor-orchestrate` State 4b.

---

### worktree-per-project-per-task (D30)

**Definition:** D30 discipline enforced by the `worktree-per-project-per-task` skill. Every `dev-implementer` task must execute in a **fresh isolated git worktree** — never on the main working tree or a shared branch. One worktree per repo per task. The branch follows naming convention `task/<task-id>[-<repo-role>]`. Worktrees are created before `[P4.1-DISPATCH]` and confirmed by `forge-tdd` Step 0.

**Why isolated:** Prevents state leakage between parallel tasks, ensures the RED test only sees the current task's code, and makes rollback clean (delete worktree, branch is gone).

**Red flag:** If `git worktree list` shows the current directory on `main`/`master` or `HEAD` without a task branch — STOP. Invoke `worktree-per-project-per-task` first.

**Cross-References:** Enforced by `forge-tdd` Step 0 HARD-GATE; `conductor-orchestrate` State 5 HARD-GATE; skill `worktree-per-project-per-task`.

---

### Brain Directory Structure

**Definition:** The Forge brain is the append-only, git-backed evidence store at `~/forge/brain/`. Two subtrees:

- `~/forge/brain/products/<slug>/` — persistent per-product config (`product.md`, `codebase/`, `terminology.md`, scan outputs)
- `~/forge/brain/prds/<task-id>/` — per-task artifacts (all phases of a single pipeline run)

**Per-task layout (`~/forge/brain/prds/<task-id>/`):**

| Path | Contents |
|---|---|
| `prd-locked.md` | Intake output — immutable PRD with all 9 Q answers |
| `terminology.md` | Canonical product term sheet |
| `shared-dev-spec.md` | Council output — 5 contracts, frozen |
| `tech-plans/<repo>.md` | Per-repo task breakdown |
| `qa/manual-test-cases.csv` | Approved acceptance test cases |
| `qa/semantic-automation.csv` | Machine-eval step DAG |
| `qa/semantic-eval-manifest.json` | Eval run outcome |
| `qa/semantic-eval-run.log` | Per-step JSON lines |
| `design/` | Figma MCP ingest or Lovable sync artifacts |
| `conductor.log` | Append-only phase marker log |
| `decisions/` | Brain decisions (DREAM-*, SPECCHG-*) |
| `blockers/` | Escalation files when BLOCKED |

**Cross-References:** `brain-read`, `brain-write`, `brain-recall`, `forge-brain-layout`.

---

### prd-locked.md

**Definition:** Immutable PRD artifact written to `~/forge/brain/prds/<task-id>/prd-locked.md` at the end of intake. Contains all 9 `intake-interrogate` question answers as structured sections. Key frontmatter fields: `product`, `goal`, `success_criteria`, `repos` (role list), `contracts` (which of 5 apply), `timeline`, `rollback_plan`, `metrics`, `design_new_work`, `design_intake_anchor`. Once written and `[P1-PRD-LOCKED]` is logged, this file is read-only — reopen intake if it must change.

**Cross-References:** Written by `intake-interrogate`; read by all downstream skills; consumed by `council-multi-repo-negotiate`, `tech-plan-write-per-project`, `qa-prd-analysis`.

---

### terminology.md

**Definition:** Per-task canonical term sheet at `~/forge/brain/prds/<task-id>/terminology.md`. Table of canonical product names, disallowed variants, and `open_doubts` in frontmatter. Authored in intake, aligned at council. Consumed by QA authoring (for `Intent`/`ExpectedHint` wording), tech plans (UI copy), and assertion text so human-facing copy matches contracts.

**What It's NOT:** Not the `forge-glossary` (which covers Forge process terms). Not global — it is task-scoped. Not optional for UI-facing work.

**Cross-References:** `intake-interrogate`; `council-multi-repo-negotiate`; `docs/terminology-review.md`; `forge-glossary` § Product terminology.

---

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

**Definition:** A non-negotiable process gate marked with a HARD-GATE label. Enforced by 5+ MUST bullets that cannot be skipped or rationalized away. Examples: intake (MUST satisfy mandatory **prd-locked.md** fields via **`intake-interrogate`**, confidence-first), council (MUST negotiate all contracts), eval (MUST pass critical scenarios), TDD (MUST write test first).

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

**Cross-References:** Eval drivers: `eval-driver-api-http`, `eval-driver-db-mysql`, `eval-driver-cache-redis`, `eval-driver-bus-kafka`, `eval-driver-search-es`, `eval-driver-web-cdp`, `eval-driver-ios-xctest`, `eval-driver-android-adb`. Deploy drivers: `deploy-driver-pm2-ssh`, `deploy-driver-docker-compose`, `deploy-driver-local-process`, `deploy-driver-systemd`. Stack-up: `eval-product-stack-up`. Semantic execution: `qa-semantic-csv-orchestrate`.

---

### Escalation

**Definition:** Signal that human judgment, context, or coordination is needed. Triggered by red flags, unrecovered failures, or scope ambiguity. Keywords: BLOCKED, NEEDS_CONTEXT, NEEDS_COORDINATION, NEEDS_INFRA_CHANGE. Escalation is not failure — it's the correct response when automation cannot proceed.

**Usage Context:** When a skill hits a red flag, escalate immediately (do not work around). When dev-implementer reports BLOCKED, escalate to conductor. When eval fails 3 times, escalate. When contracts conflict, escalate. Escalation triggers human review, context addition, or re-negotiation.

**What It's NOT:** Not a rare event. Not a sign of incompetence. Not shameful. Not the same as failure. Not permitting continued work around the issue.

**Cross-References:** Related to red flags, self-heal retry cap, dev-implementer status codes. Handled by conductor or human team.

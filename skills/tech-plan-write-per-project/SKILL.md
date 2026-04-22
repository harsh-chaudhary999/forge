---
name: tech-plan-write-per-project
description: "WHEN: Shared-dev-spec is frozen and per-project tech plans must be written before dev-implementer dispatch. Output: 1 plan per repo — Section 0 doubt log (unlimited Q&A until confident), elaborative §1b–§1c, then bite-sized tasks; no vendor-specific assumptions; scan-grounded; review/XALIGN before dispatch."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers: []
allowed-tools:
  - Bash
  - Write
---

# tech-plan-write-per-project

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "The implementer will figure out the details" | Vague tasks cause divergence. "Add the endpoint" is not a task — "Add POST /api/v1/orders to routes/orders.ts returning 201 with OrderResponse schema" is a task. |
| "I'll use pseudocode to keep the plan concise" | Pseudocode forces the implementer to make design decisions that should have been made in planning. Write complete code. |
| "This task is too small to write out" | If it takes 2 minutes to execute, it takes 30 seconds to write. Small tasks that are written out get done correctly. Small tasks left vague get done wrong. |
| "I'll group related changes into one big task" | Tasks over 5 minutes need splitting. Big tasks hide complexity and make progress tracking impossible. |
| "The bash commands are obvious" | "Obviously" wrong commands waste a self-heal loop iteration. Write the exact command including flags, paths, and environment variables. |
| "I'll reference the spec instead of repeating details" | The implementer (dev-implementer subagent) works in an isolated worktree with only the plan. Self-contained tasks prevent NEEDS_CONTEXT status. |
| "I'll discover file paths by exploring the repo" | Duplicates work the scan already did and burns tokens. **Default:** read `~/forge/brain/products/<slug>/codebase/` first; put paths from `index.md` / `modules/*.md` / `api-surface.md` into tasks, then open sources when writing full file bodies. **Exception:** **Section 1b.6** lists an **UNKNOWN** — you **must** deepen discovery (targeted `rg`/glob, read hub files, route tables, OpenAPI, client wrappers, test names) until resolved or **BLOCKED** — do not ship “mystery meat” tasks. |
| "Elaboration is optional — bite-sized tasks are enough" | Tasks without **§1b.5 API map**, **§1b.6 unknown closure**, and **§1c review rounds** hide integration risk. STOP. Elaboration is **mandatory** for E2E; micro-tasks execute the elaboration, they do not replace it. |
| "I've hit my question quota — ship the plan with lingering doubts" | **There is no maximum question count** during planning. Doubt left unasked becomes a gap in Section 2. STOP. Ask until **confidence is high** (see **Section 0**), then write the elaborative plan. |
| "Concise plan = professional" | **Professional** here means **complete**: the plan is the **only** input to sub-tasks. Concision that omits wiring, edge cases, or evidence is negligence. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
EVERY TASK IN A TECH PLAN IS SELF-CONTAINED, COMPLETE, AND EXECUTABLE IN ISOLATION. NO PLACEHOLDERS. NO PSEUDOCODE. NO "SEE SPEC" REFERENCES. THE PLAN IS THE ONLY THING THE DEV-IMPLEMENTER READS.
```

**Normative claims (companion rule):** Every **interface** claim in a task (path, field name, status code, topic name, column) must be **copied from** the **frozen** `shared-dev-spec.md` or the task-local inlined excerpt of **`contracts/*`** — **not invented** in the tech plan. If `shared-dev-spec` was thinner than reality, **fix the spec** (change request / re-council) — do not “paper over” in tasks. **Program / rollout / sequencing** lives in **`~/forge/brain/prds/<task-id>/delivery-plan.md`** (non-frozen); tech plans may **reference** it by heading but **must not** rely on it for interface truth.

**Optional PM traceability (inside each `tech-plans/<repo>.md`):** You may group Section 2 tasks under IDs like **`REVERIF-<AREA>-<nn>`** with columns **Est / Deps / Acceptance / Spec refs** (link to `shared-dev-spec` § or `contracts/` heading). This does **not** replace one-file-per-repo or self-contained task bodies.

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Task contains "add the endpoint" or other vague verbs without file paths** — Vague tasks produce vague implementations. STOP. Rewrite with exact file path, function name, and complete code.
- **A task exceeds 5 minutes of execution** — Tasks over 5 minutes hide complexity and block progress tracking. STOP. Split into smaller tasks, each 2-5 minutes.
- **Plan has no Section 0 / 1b / 1c** — Missing **doubt log**, **§1b.1–1b.6** (per applicability), or **§1c**. Micro-tasks without inventory and without cleared doubts hide gaps. STOP. Add **Section 0** then the full preamble before Task 1.
- **Migration or DDL tasks exist but the data model delta table is empty or claims “none”** — Contradiction with locked DB contract. STOP. Align the table and tasks.
- **Plan references the shared-dev-spec with "see spec" instead of repeating the details** — Dev-implementer works in isolation without spec access. STOP. Make every task fully self-contained with all needed details inline.
- **Bash commands lack flags, paths, or environment variables** — Incomplete commands produce incorrect results or fail silently. STOP. Write the exact, complete command.
- **Tech plan is written before shared-dev-spec is frozen** — Plans written against an unlocked spec will drift. STOP. Confirm spec-freeze before writing any tech plan.
- **Multiple repos share a single tech plan** — One plan per repo. Cross-repo plans create cross-task dependencies that block independent dispatch. STOP. Write one plan per repo.
- **Test task is listed after implementation task** — TDD requires test first. STOP. Reorder: test task always precedes the implementation task it covers.
- **Web or app tech plan skips Section 1b.4 or omits design anchors while intake locked Figma / `design_brain_paths` / Lovable repo** — Figma captured in Q9 is **not** decorative; it must drive the component/screen plan. STOP. Add the design→UI table and align tasks to nodes or brain paths.
- **UI tasks cite neither a design anchor nor `design_waiver: prd_only` + scan reuse** — Implementers cannot verify pixels or reuse. STOP.
- **HTTP-consuming web/app plan has no Section 1b.5 consumer map** — No way to verify which component calls which API. STOP.
- **HTTP-serving backend plan has no Section 1b.5 rows for new/changed endpoints** — Consumers cannot be aligned. STOP.
- **Section 1b.6 lists UNRESOLVED unknowns but Section 2 still has executable tasks depending on them** — Discovery incomplete. STOP. Resolve, escalate **BLOCKED**, or remove tasks until evidence exists.
- **`Tech plan status: REVIEW_PASS` with no `tech-plan-self-review` round logged in §1c revision log** — Rubber-stamp. STOP.
- **State 4b or implementation started without `tech-plans/HUMAN_SIGNOFF.md` + `[TECH-PLAN-HUMAN]`** — Human feedback phase skipped. STOP.
- **Section 0 doubt log has open items** (unanswered questions, `UNCONFIRMED` rows) but Section 2 tasks are already written — Planning was short-circuited. STOP. Resolve or **BLOCK** before tasks.

## Overview

This skill converts a locked shared-dev-spec into bite-sized, executable technical implementation plans per project. Each task is 2-5 minutes of execution with exact file paths, complete code (no placeholders), and exact bash commands.

**Primary audience:** A human or agent who **does not** already know the product repos. The plan must stand alone: **brain scan** supplies *where things live today*; **locked intake design** (`prd-locked.md` and the **Design source (from intake)** section in **shared-dev-spec**) supplies *what net-new UI should match* (Figma nodes, `design_brain_paths`, Lovable GitHub tree, or an explicit waiver). **Taking Figma in intake but omitting it from the tech plan** is the same class of failure as skipping migrations — implementers will invent components and ship visual bugs.

**Order of operations for paths:** Before naming files in tasks, load **`~/forge/brain/products/<slug>/codebase/`** (at least `index.md`, `SCAN.json`, and the `modules/*.md` files that match the spec’s surfaces). **Failsafe:** if `SCAN.json` exists, run **`python3 tools/verify_scan_outputs.py <that/codebase>`** (up to **3** tries, **1s** backoff). On persistent failure, prefix the plan with **`SCAN_INCOMPLETE`** and **do not** treat brain paths as authoritative until `/scan` passes verify — deepen with targeted `rg`/reads or **BLOCKED** per Section 1b.6. Derive **exact repo-relative paths** from verified brain material, then read the product repo only to pull current file contents for “complete code” blocks. If scan is missing or >7 days old, note it and align with `product-context-load` / user on **`/scan <slug>`** before finalizing paths.

**Order of operations for UI:** When this repo is **web** or **app**, read **Design source (from intake)** in the locked spec **and** any **`~/forge/brain/prds/<task-id>/design/`** ingest notes (`MCP_INGEST.md`, `README.md`, …). Complete **Section 1b.4** before writing UI tasks so every screen/component change is tied to **design anchors** and/or **scan-backed** reuse paths — not to memory of a Figma URL from chat.

**Elaboration bar:** The plan should be **as elaborative as practical** — it is what **defines** Section 2 sub-tasks. If a fact would change a task boundary, it belongs in **§1b** or the task body, not in a planner’s head.

---

## Section 0: Planning doubt clearance (before §1b and Section 2)

**Purpose:** Sub-tasks inherit every gap you skip while “planning.” This section **forces** questions until doubt is low — **no artificial cap** on how many you ask.

### 0.1 Rules

1. **Ask freely:** Raise **every** ambiguity (ownership, edge case, failure mode, idempotency, auth, rollout, test data, environment flag, naming, which repo owns what). Prefer **over-asking** to under-asking. There is **no** “max questions per task” in Forge.
2. **Answer channels:** Product owner, tech lead, **`delivery-plan.md`**, **`parity/`** material, brain scan, another repo’s plan draft, or **explicit `BLOCKED`** with who must answer — all valid. Chat history alone is **not** durable; **write outcomes** into this plan or `~/forge/brain/prds/<task-id>/planning-doubts.md` (optional file) and **summarize** in **§1b.6** when they affect code paths.
3. **Start the elaborative plan only when:** You would stake implementation on it — i.e. no remaining **high-impact** unknowns without an owner, or they are recorded as **BLOCKED** / **WAIVER** with risk.
4. **Trace questions to coverage:** Each resolved doubt should visibly affect **§1b** tables or a specific Section 2 task — or be explicitly **out of scope** with spec citation.

### 0.2 Artifact (required in each `tech-plans/<repo>.md` or linked file)

Include **before** `## Section 1b`:

```markdown
## Section 0: Planning doubt log
| Q# | Question | Answer / resolution | Confidence (H/M/L) | Affects (§1b.x / Task ids) |
|----|----------|---------------------|--------------------|----------------------------|
| Q1 | …        | …                   | H                  | 1b.5, Task 3–5             |
```

- Add rows until **high-impact** doubts are **H** or **M** with an owner, or **BLOCKED** / **WAIVER**.
- If zero open questions: one row stating **`No material doubts — ready to elaborate.`**

---

## Section 1: Parse shared-dev-spec

### Input
- Locked spec location: `/home/lordvoldemort/Videos/forge/brain/prds/<task-id>/spec.md`
- Status: LOCKED (spec is immutable at this stage)

### Process
1. **Read the spec file** to understand:
   - Feature requirements (functional + non-functional)
   - Success criteria and acceptance tests
   - Affected projects (which repos need changes)
   - Contracts and interfaces (API shapes, schema changes, event formats)

2. **Extract per-project work items** by identifying:
   - Database migrations (schema changes)
   - API endpoints (routes, handlers, validation)
   - Data models and business logic
   - Frontend components and views
   - Integration points and dependencies

3. **Map to repositories** (standard Forge topology):
   - `shared-schemas/` — Shared TypeScript types, validation schemas, contracts
   - `backend-api/` — Node/Express REST API, database migrations, business logic
   - `web-dashboard/` — React SPA, UI components, state management
   - `app-mobile/` — React Native app, mobile UI, offline-first patterns

### Output
- Structured list of per-project tasks (raw)
- Dependency graph (which project depends on which)
- Identified contracts (API, schema, events)

---

## Section 1b: Elaborative preamble (mandatory per tech-plan file)

**Authoring order in the saved `tech-plans/<repo>.md` file:** (1) `#` title line, then **`Tech plan status: DRAFT`** (or `REVIEW_CHANGES` / `REVIEW_PASS` per **§Section 1c**); (2) **`## Section 0: Planning doubt log`** (see **Section 0** of this skill); (3) this **Section 1b** (`### 1b.1` … `### 1b.6`); (4) **§Section 1c** body (revision log table + cross-repo notes); (5) **Section 2** tasks.

Bite-sized tasks exist so a **dev-implementer in isolation** can execute without guessing. They **do not** replace **§Section 0** (cleared doubts), nor a short, explicit narrative of **what changes in the world** (data, reuse, design, **HTTP wiring**, unknowns, review trail). **Subsection 1b.4** follows web/app rules; **1b.5** follows HTTP rules; **1b.6** is always required (may be a single “no unknowns” line). **§Section 1c** is always required. All of the above **before Section 2**.

Skipping them because “the tasks are obvious” or “only micro-steps matter” is **BLOCKED** — that is how schema drift, duplicate tables, wrong screens, **wrong API wiring**, and silent greenfield work slip through.

### 1b.1 Data model delta (persistence)

Ground this in the **locked shared-dev-spec** and any **`db-contract` / `contract-schema-db`** material — do not invent tables here that the spec did not lock.

| Table / collection / index | Change type | Rationale (one line) | Rollback or backward-compat note |
|-----------------------------|---------------|----------------------|----------------------------------|
| *(row per CREATE, ALTER, DROP, new index, or materialized view)* | CREATE \| ALTER \| DROP \| INDEX | *why* | *e.g. nullable-first, dual-write, irreversible — link to contract if long* |

- If this repo has **no** persistence ownership for this task (e.g. pure UI repo), state exactly: **`No database or durable storage schema changes in this repo.`**
- If persistence lives in another repo, say **which repo owns DDL** and keep this table empty with that cross-reference — do not imply this repo runs migrations it does not own.

Every later **migration / DDL task** in this file MUST correspond to a row above (same table + change type). Orphans either way are a planning defect.

### 1b.2 Implementation reuse vs net-new

Summarize so **reuse is not taken for granted** from task ordering alone. **Prefer evidence from `~/forge/brain/products/<slug>/codebase/`** (`index.md`, `modules/*.md`, `api-surface.md`): reuse bullets should cite paths that **appear in the scan** when the repo was scanned. If the scan is missing or stale, state **`SCAN_MISSING_OR_STALE`** and trigger **`/scan <slug>`** (or equivalent) before claiming paths.

- **Reuse (extend, call, wrap, configure):** bullets with **repo-relative paths** and symbol/module names (existing services, models, components, shared validators).
- **Net-new:** bullets — new files, new tables, new public routes/events — also with paths or names.
- **Unknown / scan gap:** if brain scan or spec does not prove a reuse target, say **`DISCOVERY_REQUIRED`** or **`HUMAN_CONFIRM`** — do not silently pick a module.

### 1b.3 Trace to locked spec

Bullets mapping **shared-dev-spec** requirement headings, contract IDs, or acceptance criteria **to task numbers** in this file (e.g. “Requirement **FR-3 auth** → Tasks 1–4”). If a requirement has no task, **STOP** — fix coverage before dispatch.

### 1b.4 Design source → UI / component plan (web & app repos)

**Purpose:** Intake may lock **`figma_file_key` + `figma_root_node_ids`**, **`design_brain_paths`**, **`lovable_github_repo`**, or **`design_waiver: prd_only`**. Council may copy that into **Design source (from intake)** in `shared-dev-spec.md`. None of that helps E2E delivery if the **tech plan** never maps design to **concrete components, routes, or files**. This subsection is the handoff from **design transport** to **implementation tasks**.

**When to fill the table vs one-line N/A**

| Situation | Required content |
|-----------|-------------------|
| This file is for a **backend**, **worker**, **shared-schema**, or other **non-UI** repo | One line: **`1b.4 not applicable — not a web/app repo.`** |
| **`design_ui_scope: not applicable`** in lock (no user-visible UI for this slice) | One line: **`1b.4 not applicable — no user-visible UI in this repo for this task.`** |
| **`design_new_work: yes`** OR implementable design paths/keys exist (Figma, `design_brain_paths`, Lovable repo) | **Full table** (below) + ensure **each UI task** later references a **row id** (e.g. `D1`) in its title or header |
| **`design_new_work: no`** but UI still changes | Table or bullet list: **which existing components** (from **scan**) are extended; if any **new** file is unavoidable, say why PRD/engineering-only still requires it |

**Design → implementation mapping table** (add rows until every net-new or changed screen in scope is covered):

| Id | Design anchor (Figma node id / frame name / path under `.../design/` / Lovable route) | UI deliverable (screen, component, layout region) | Existing code (path from **brain scan**) **or** `NET_NEW` | parity / notes |
|----|----------------------------------------------------------------------------------------|---------------------------------------------------|-------------------------------------------------------------|----------------|
| D1 | *(e.g. `123:456` or `design/wireframes/checkout.png`)* | *(e.g. Checkout summary card)* | *(e.g. `src/features/cart/Summary.tsx` or `NET_NEW`)* | *(states, tokens, a11y)* |

**Rules**

- Do **not** write “see Figma” without **node id(s)** or **brain path** that appear in the **locked** PRD/spec — chat URLs are not a transport layer.
- If **`design_waiver: prd_only`** is locked, the table still lists **screens/components** and maps them to **scan-backed** files or `NET_NEW`, with **one line** citing the waiver for pixel latitude.
- **Every** UI implementation task in Section 2 should reference **`D<n>`** or explicitly say **waiver + PRD section** so reviewers can trace intake → plan → code.

### 1b.5 API ↔ consumer map (HTTP / REST integration)

**Purpose:** E2E delivery requires a **written** answer to: *which component (or service) calls which endpoint*, and *where the handler lives*. Do not assume the reader has opened the backend and frontend repos.

**When N/A:** This repo has **no** HTTP server and **no** HTTP client changes for this task — one line: **`1b.5 not applicable — no HTTP API surface in this repo for this task.`**

**When this repo implements or changes HTTP APIs** (backend, BFF, API gateway): build a table from the **locked** `shared-dev-spec` REST section (verbatim paths and methods — no invention):

| Endpoint (METHOD `path`) | Handler (repo-relative path : symbol or class#method) | Auth / versioning / idempotency | Consumers — component path **or** `tech-plans/<other>.md` §1b.5 row id (e.g. `web: C3`) |

**When this repo consumes HTTP APIs** (web, app, worker with outbound REST): build a table tying **UI or job code** to **contract**:

| Consumer (path : component or hook) | When it runs (mount, click, job tick, …) | METHOD + `path` | Client module (path) | Success + error handling (status codes) |

If the owning API plan lives in another repo file, **cross-reference** exact rows (same METHOD+path string) so **`tech-plan-self-review` cross-plan checks** can diff them.

### 1b.6 Unknowns & deep discovery closure

**Purpose:** Scans and specs leave **gaps**. **Elaborative** planning means **closing** gaps with repo evidence, not leaving them for implementers.

1. Start a table (zero rows = fine only if you genuinely have **no** unknowns — then write **`No material unknowns — scan + spec sufficient for every Section 2 path.`**):

| U# | Unknown | Why it matters if wrong |
|----|---------|-------------------------|

2. For **each** row, append columns (same table or continuation):

| … | Deep discovery performed (tools: e.g. `rg`, `Read`, hub file) | Resolution (`RESOLVED: …` \| `BLOCKED: …`) |

**Rules**

- **RESOLVED** must cite **concrete evidence** (file paths, line ranges, grep pattern hit counts, test file name) — not “I checked.”  
- **BLOCKED** must state the **exact** decision needed from a human or from **`/scan`** refresh — and **Section 2 must not** contain tasks that depend on that unknown until resolved.  
- **Deep exploration is required** when scan/`api-surface.md` does not show registration, client wrapper, middleware chain, or feature flag gate: open those files in the product repo until the unknown is mapped or escalated.

## Section 1c: Plan lifecycle, cross-repo alignment, and feedback

Tech plans are **not one-shot** documents. They go through **review → revise → re-align** until integration is legible on paper.

1. **Status line** — Placed immediately under the `#` title (see **Section 1b** authoring order). Values: **`DRAFT`** | **`REVIEW_CHANGES`** | **`REVIEW_PASS`**. Start at **`DRAFT`**. After **`tech-plan-self-review`**: all PASS → **`REVIEW_PASS`**; any CHANGES or BLOCKER → **`REVIEW_CHANGES`**, fix plans, set **`DRAFT`**, re-run review.

2. **Revision log** (append one row per meaningful edit):

   | Rev | When (ISO8601 approx) | Who | Trigger (e.g. self-review §1b.5 FAIL, XALIGN drift) | What changed |

3. **Minimum feedback loop**

   - Run **`tech-plan-self-review`** on this file **before** treating the plan as final for dispatch.  
   - Record in the log: **`self-review round=<n> result=PASS|CHANGES|BLOCKED`** (short note).  
   - Default **max 3** review rounds per repo per task; then **ESCALATE** with consolidated blockers.

4. **Cross-repo alignment** (when this product task has **≥2** of `{API-owning repo, HTTP-consuming repo}`):

   - After **all** sibling `tech-plans/*.md` are in **`DRAFT`** with **§1b.5** filled, perform one **cross-walk**: every consumer **METHOD+path** matches an owner row; version/prefix matches; auth assumptions consistent.  
   - Append to **each** affected plan’s revision log: **`XALIGN PASS`** or **`XALIGN FAIL: <drift>`** and fix drift before setting **`REVIEW_PASS`**.

5. **Conductor logging** (when orchestrated): emit **`[TECH-PLAN-REVIEW]`** and **`[TECH-PLAN-XALIGN]`** lines as specified in **`conductor-orchestrate`** State 4.

6. **Human go-ahead (pipeline phase — after agent loops, before State 4b)**  
   Automated **`tech-plan-self-review` PASS** + **`XALIGN` PASS** are **not** the same as stakeholder acceptance. **Before** eval YAML / RED (State 4b), a **human** must record one of:
   - **`~/forge/brain/prds/<task-id>/tech-plans/HUMAN_SIGNOFF.md`** from **`docs/tech-plan-human-signoff.template.md`** with **`status: approved`** (or **`changes_requested`** → revise plans → re-run steps 3–5 → new signoff), **or**
   - **`status: waived`** with actor + reason (solo / unattended policy only).  
   Append the same decision as a **revision-log row** in each affected `tech-plans/<repo>.md` for traceability.  
   **Conductor** logs **`[TECH-PLAN-HUMAN] task_id=<id> status=APPROVED|CHANGES_REQUESTED|WAIVED`**. **No State 4b** until **`APPROVED`** or documented **`WAIVED`**.

**Interconnection (no gaps):** `intake` → `parity` (spec-freeze Step 0) → **frozen** `shared-dev-spec` → **Section 0** doubt log → **§1b** (data, reuse, design, API map, unknowns) → **§1c** (agent review + XALIGN) → **`HUMAN_SIGNOFF.md`** → **State 4b** (QA CSV / eval YAML / RED) → implementation. Skipping a box forwards **hidden** gaps backward into cheaper phases — forbidden.

---

## Section 2: Bite-Sized Task Breakdown

### Definition
Each task must satisfy:
- **Duration**: 2-5 minutes of focused execution
- **Scope**: Single feature increment (add one endpoint, one component, one migration)
- **Completeness**: Every file shown in full, no abbreviations, no "..."
- **Specificity**: Exact file paths, exact bash commands, exact test assertions

### Non-Examples (What NOT to do)
```markdown
## ❌ Task: Add validation
- Files: backend-api/routes/auth.js
- Code: "Add validation logic here"
- Test: "Run npm test"

## ❌ Task: Create user model
- Files: backend-api/models/user.js
- Code: 
  ```js
  class User {
    ...
    validateEmail() { /* validation */ }
  }
  ```
```

### Correct Example
```markdown
## ✓ Task: Add email validation to User model
- Files: backend-api/models/user.js
- Code: (complete class with method)
  ```js
  class User {
    constructor(data) {
      this.id = data.id;
      this.email = data.email;
    }
    
    validateEmail() {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(this.email)) {
        throw new Error('Invalid email format');
      }
      return true;
    }
  }
  
  module.exports = User;
  ```
- Test: `npm test -- models/user.test.js` (expect: email validation throws on invalid)
- Commit: "feat: add email validation to User model"
```

### Task Template
```markdown
## Task N: [Specific action] in [file/module]

**Files affected:**
- /path/to/file1.js
- /path/to/file2.ts
- etc.

**Complete code for each file:**
(Show every line, no abbreviations)

**Exact bash command to test:**
```bash
npm test -- specific-test-file.test.js
```

**Expected output:** (What success looks like)

**Git commit message:**
```
feat: [action description]
```
```

---

## Section 3: Task Ordering

### Dependency-First Approach
Tasks must respect this order:

1. **Layer 0: Shared Schemas** (no dependencies)
   - TypeScript types
   - Validation schemas (zod/joi)
   - Contract definitions
   - Shared constants and enums

2. **Layer 1: Backend Infrastructure** (depends on schemas)
   - Database migrations
   - Models and DAOs
   - Business logic services
   - Error handling and middleware

3. **Layer 2: Backend APIs** (depends on models)
   - REST endpoints
   - Request/response handlers
   - Authentication and authorization

4. **Layer 3: Web Frontend** (depends on API contracts)
   - API client (generated or manual)
   - State management (Redux, Zustand)
   - Components and views
   - Forms and validation

5. **Layer 4: Mobile App** (depends on API contracts)
   - API client
   - Navigation structure
   - Screens and components
   - Offline-first setup

### Within-Project Ordering
Order by dependency:
- Shared types → Constants → Validation → Models → Services → Routes → Middleware → Integration

### Dependency Markers
Mark explicit dependencies:
```markdown
## Task 3: Create user repository
**Depends on:** Task 1 (User schema), Task 2 (database connection)

## Task 5: Add POST /users endpoint
**Depends on:** Task 3 (user repository), Task 4 (authentication middleware)
```

---

## Section 4: Code Completeness

### Every file must be 100% complete
No:
- `import { Todo } from '../types'` without defining Todo in this plan
- `function validateUser() { /* validation logic */ }`
- `// Add error handling here`
- `...rest of the file...`

### Every import must be resolvable
If a file imports from another file, ensure that file is created earlier in the plan or it already exists in the repo.

### Example: Bad Plan
```markdown
## Task 2: Create user service
- Files: backend-api/services/userService.js
- Code:
  ```js
  const { UserRepository } = require('../models/user');
  
  class UserService {
    async createUser(userData) {
      return UserRepository.create(userData); // Not implemented yet!
    }
  }
  ```
```

### Example: Good Plan
```markdown
## Task 1: Create user repository
- Files: backend-api/models/userRepository.js
- Code:
  ```js
  class UserRepository {
    static async create(userData) {
      const db = require('../db');
      const query = 'INSERT INTO users (email, name) VALUES (?, ?)';
      const result = await db.run(query, [userData.email, userData.name]);
      return { id: result.lastID, ...userData };
    }
  }
  module.exports = { UserRepository };
  ```

## Task 2: Create user service
- Files: backend-api/services/userService.js
- Code:
  ```js
  const { UserRepository } = require('../models/userRepository');
  
  class UserService {
    async createUser(userData) {
      return UserRepository.create(userData);
    }
  }
  module.exports = { UserService };
  ```
```

### Complete Code Checklist
- ✓ All imports are defined or pre-existing
- ✓ All functions have complete bodies (no // TODO or // TODO: implement)
- ✓ All class methods are implemented
- ✓ All error cases are handled
- ✓ No placeholder strings or fake data

---

## Section 5: Verification Checklist

Every task must include:

### 1. Test Command
An exact, runnable bash command:
```bash
npm test -- users.test.js
npm run migrate:test
npm run build && npm run test:integration
jest --testPathPattern=userService.test.js
```

### 2. Expected Output
What the developer sees on success:
```
PASS  tests/userService.test.js
  UserService
    ✓ creates user with valid email (2ms)
    ✓ throws error on invalid email (1ms)
    ✓ returns user with id (3ms)

Test Suites: 1 passed, 1 total
Tests: 3 passed, 3 total
```

### 3. Commit Message
Standard format:
```
feat: [action] [what changed]
fix: [bug] [how it's fixed]
refactor: [what] [why simplified]
test: [what] [coverage added]
docs: [what] [clarity improved]
```

Example:
```
feat: add email validation to User model
```

### 4. Integration Checkpoint
After each task, verify:
- [ ] Code compiles/lints (no syntax errors)
- [ ] Test passes (assert expected output)
- [ ] No new import errors
- [ ] No breaking changes to previous tasks

### Task Verification Template
```markdown
## Task 7: Add POST /users endpoint

**Files affected:**
- backend-api/routes/auth.js

**Complete code:**
(Full route handler, no abbreviations)

**Test command:**
```bash
npm test -- routes/auth.test.js -- --testNamePattern="POST /users"
```

**Expected output:**
```
✓ POST /users creates new user (10ms)
✓ POST /users returns 400 on invalid email (5ms)
✓ POST /users returns 409 on duplicate email (8ms)
```

**Commit message:**
```
feat: add POST /users endpoint with validation
```

**Breaking changes:** None
**Backward compatible:** Yes (new endpoint, no changes to existing)
```

---

## Usage

### When Called
1. `brain-read` has provided locked spec from `/home/lordvoldemort/Videos/forge/brain/prds/<task-id>/spec.md`
2. Phase 2.10 (shared-dev-spec) is complete and immutable

### How to Use
```bash
# As a subagent in conductor-orchestrate flow:
skill tech-plan-write-per-project <task-id>

# Or manually:
cd /home/lordvoldemort/Videos/forge
# 1. Read the spec
# 2. Break into bite-sized tasks
# 3. Order by dependency
# 4. Write complete code (no placeholders)
# 5. Add test + commit message
# 6. Output to: brain/prds/<task-id>/tech-plans/
```

### Output Structure
```
brain/prds/<task-id>/tech-plans/
├── shared-schemas.md      (layer 0 tasks)
├── backend-api.md         (layers 1-2 tasks)
├── web-dashboard.md       (layer 3 tasks)
└── app-mobile.md          (layer 4 tasks)
```

Each file:
- **Section 0** doubt log present; no **high-impact** `L` confidence rows without **BLOCKED** / **WAIVER** / follow-up owner
- **Section 1b + 1c** preamble is present (1b.1–1b.6 per rules; **1c** status + revision log)
- Task ordering respects dependencies
- Every task is 2-5 min executable
- Every code block is complete
- Every test is exact and runnable
- Every commit message is standard

---

## Quality Gates

A tech plan passes if:
1. **Completeness**: No "...", no "TODO", no placeholders
2. **Preamble**: **Section 0** cleared for planning; Sections **1b + 1c** present; data model delta matches DDL tasks; reuse + spec trace; **1b.4** for web/app; **1b.5** when HTTP applies (consumer↔provider rows align across repos); **1b.6** has no silent UNRESOLVED; **1c** shows review rounds + XALIGN when multi-repo HTTP
3. **Specificity**: Every file path is absolute, every command is exact
4. **Testability**: Every task has a runnable test command and expected output
5. **Ordering**: No task depends on later tasks (DAG)
6. **Atomicity**: Each task is independent-executable (dev can run task N without running 1-N-1, given task setup is complete)

---

## Example: Complete Tech Plan Entry

```markdown
# Tech Plan: backend-api

## Task 1: Create user_profiles table migration
**Depends on:** None (schema layer 0)

**Files affected:**
- backend-api/migrations/001_create_user_profiles.sql

**Complete SQL migration:**
```sql
CREATE TABLE IF NOT EXISTS user_profiles (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  first_name VARCHAR(255),
  last_name VARCHAR(255),
  bio TEXT,
  avatar_url VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_user_id (user_id)
);
```

**Test command:**
```bash
npm run migrate:test
npm test -- migrations/001_create_user_profiles.test.js
```

**Expected output:**
```
PASS  migrations/001_create_user_profiles.test.js
  ✓ creates user_profiles table (15ms)
  ✓ enforces user_id uniqueness (8ms)
  ✓ cascades delete on user deletion (12ms)

Test Suites: 1 passed, 1 total
Tests: 3 passed, 3 total
```

**Git commit message:**
```
feat: add user_profiles table migration
```

---

## Task 2: Create UserProfile model
**Depends on:** Task 1 (migration)

**Files affected:**
- backend-api/models/UserProfile.js
- backend-api/models/UserProfile.test.js

**Complete UserProfile.js:**
```js
const db = require('../db');

class UserProfile {
  constructor(data) {
    this.id = data.id;
    this.userId = data.user_id;
    this.firstName = data.first_name;
    this.lastName = data.last_name;
    this.bio = data.bio;
    this.avatarUrl = data.avatar_url;
    this.createdAt = data.created_at;
    this.updatedAt = data.updated_at;
  }

  static async findByUserId(userId) {
    const query = 'SELECT * FROM user_profiles WHERE user_id = ?';
    const row = await db.get(query, [userId]);
    return row ? new UserProfile(row) : null;
  }

  static async create(userId, profileData) {
    const { firstName, lastName, bio, avatarUrl } = profileData;
    const query = `
      INSERT INTO user_profiles (user_id, first_name, last_name, bio, avatar_url)
      VALUES (?, ?, ?, ?, ?)
    `;
    const result = await db.run(
      query,
      [userId, firstName, lastName, bio, avatarUrl]
    );
    return {
      id: result.lastID,
      userId,
      firstName,
      lastName,
      bio,
      avatarUrl,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
  }

  async update(updateData) {
    const { firstName, lastName, bio, avatarUrl } = updateData;
    const query = `
      UPDATE user_profiles
      SET first_name = ?, last_name = ?, bio = ?, avatar_url = ?
      WHERE id = ?
    `;
    await db.run(
      query,
      [firstName, lastName, bio, avatarUrl, this.id]
    );
    this.firstName = firstName;
    this.lastName = lastName;
    this.bio = bio;
    this.avatarUrl = avatarUrl;
    this.updatedAt = new Date().toISOString();
    return this;
  }

  async delete() {
    const query = 'DELETE FROM user_profiles WHERE id = ?';
    await db.run(query, [this.id]);
  }

  toJSON() {
    return {
      id: this.id,
      userId: this.userId,
      firstName: this.firstName,
      lastName: this.lastName,
      bio: this.bio,
      avatarUrl: this.avatarUrl,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt
    };
  }
}

module.exports = UserProfile;
```

**Complete UserProfile.test.js:**
```js
const UserProfile = require('./UserProfile');
const db = require('../db');

jest.mock('../db');

describe('UserProfile', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('findByUserId', () => {
    test('returns user profile when found', async () => {
      const mockProfile = {
        id: 1,
        user_id: 10,
        first_name: 'John',
        last_name: 'Doe',
        bio: 'Developer',
        avatar_url: 'https://example.com/avatar.jpg',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };
      db.get.mockResolvedValue(mockProfile);

      const result = await UserProfile.findByUserId(10);

      expect(result).toBeInstanceOf(UserProfile);
      expect(result.firstName).toBe('John');
      expect(db.get).toHaveBeenCalledWith(
        expect.stringContaining('SELECT * FROM user_profiles WHERE user_id = ?'),
        [10]
      );
    });

    test('returns null when profile not found', async () => {
      db.get.mockResolvedValue(null);

      const result = await UserProfile.findByUserId(999);

      expect(result).toBeNull();
    });
  });

  describe('create', () => {
    test('creates a new user profile', async () => {
      db.run.mockResolvedValue({ lastID: 5 });

      const result = await UserProfile.create(10, {
        firstName: 'Jane',
        lastName: 'Smith',
        bio: 'Designer',
        avatarUrl: 'https://example.com/jane.jpg'
      });

      expect(result.id).toBe(5);
      expect(result.userId).toBe(10);
      expect(result.firstName).toBe('Jane');
      expect(db.run).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO user_profiles'),
        expect.arrayContaining([10, 'Jane', 'Smith', 'Designer'])
      );
    });
  });

  describe('update', () => {
    test('updates user profile', async () => {
      const profile = new UserProfile({
        id: 1,
        user_id: 10,
        first_name: 'John',
        last_name: 'Doe',
        bio: 'Developer',
        avatar_url: 'https://example.com/avatar.jpg',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      });

      db.run.mockResolvedValue({ changes: 1 });

      const updated = await profile.update({
        firstName: 'John',
        lastName: 'Doe Updated',
        bio: 'Senior Developer',
        avatarUrl: 'https://example.com/avatar-new.jpg'
      });

      expect(updated.lastName).toBe('Doe Updated');
      expect(db.run).toHaveBeenCalledWith(
        expect.stringContaining('UPDATE user_profiles'),
        expect.arrayContaining(['Doe Updated'])
      );
    });
  });

  describe('toJSON', () => {
    test('returns serializable object', () => {
      const profile = new UserProfile({
        id: 1,
        user_id: 10,
        first_name: 'John',
        last_name: 'Doe',
        bio: 'Developer',
        avatar_url: 'https://example.com/avatar.jpg',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      });

      const json = profile.toJSON();

      expect(json).toEqual({
        id: 1,
        userId: 10,
        firstName: 'John',
        lastName: 'Doe',
        bio: 'Developer',
        avatarUrl: 'https://example.com/avatar.jpg',
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z'
      });
    });
  });
});
```

**Test command:**
```bash
npm test -- models/UserProfile.test.js
```

**Expected output:**
```
PASS  models/UserProfile.test.js
  UserProfile
    findByUserId
      ✓ returns user profile when found (5ms)
      ✓ returns null when profile not found (3ms)
    create
      ✓ creates a new user profile (4ms)
    update
      ✓ updates user profile (6ms)
    toJSON
      ✓ returns serializable object (2ms)

Test Suites: 1 passed, 1 total
Tests: 5 passed, 5 total
Snapshots: 0 total
Time: 0.847 s
```

**Git commit message:**
```
feat: add UserProfile model with CRUD operations
```

---

## Task 3: Add GET /users/:userId/profile endpoint
**Depends on:** Task 2 (UserProfile model)

**Files affected:**
- backend-api/routes/profile.js
- backend-api/routes/profile.test.js

**Complete profile.js:**
```js
const express = require('express');
const router = express.Router();
const UserProfile = require('../models/UserProfile');
const { authenticateToken } = require('../middleware/auth');

// GET /users/:userId/profile
router.get('/:userId/profile', authenticateToken, async (req, res) => {
  try {
    const { userId } = req.params;

    // Validate userId is a number
    if (!Number.isInteger(parseInt(userId))) {
      return res.status(400).json({
        error: 'Invalid user ID format',
        code: 'INVALID_USER_ID'
      });
    }

    const profile = await UserProfile.findByUserId(parseInt(userId));

    if (!profile) {
      return res.status(404).json({
        error: 'User profile not found',
        code: 'PROFILE_NOT_FOUND'
      });
    }

    res.json(profile.toJSON());
  } catch (error) {
    console.error('Error fetching user profile:', error);
    res.status(500).json({
      error: 'Internal server error',
      code: 'INTERNAL_ERROR'
    });
  }
});

module.exports = router;
```

**Complete profile.test.js:**
```js
const request = require('supertest');
const express = require('express');
const profileRouter = require('./profile');
const UserProfile = require('../models/UserProfile');

// Mock UserProfile
jest.mock('../models/UserProfile');

// Mock auth middleware
jest.mock('../middleware/auth', () => ({
  authenticateToken: (req, res, next) => {
    req.user = { id: 1 };
    next();
  }
}));

const app = express();
app.use(express.json());
app.use('/users', profileRouter);

describe('Profile Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('GET /users/:userId/profile', () => {
    test('returns user profile for valid userId', async () => {
      const mockProfile = {
        id: 1,
        userId: 10,
        firstName: 'John',
        lastName: 'Doe',
        bio: 'Developer',
        avatarUrl: 'https://example.com/avatar.jpg',
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
        toJSON: () => ({
          id: 1,
          userId: 10,
          firstName: 'John',
          lastName: 'Doe',
          bio: 'Developer',
          avatarUrl: 'https://example.com/avatar.jpg',
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z'
        })
      };

      UserProfile.findByUserId.mockResolvedValue(mockProfile);

      const response = await request(app).get('/users/10/profile');

      expect(response.status).toBe(200);
      expect(response.body).toEqual(mockProfile.toJSON());
      expect(UserProfile.findByUserId).toHaveBeenCalledWith(10);
    });

    test('returns 404 when profile not found', async () => {
      UserProfile.findByUserId.mockResolvedValue(null);

      const response = await request(app).get('/users/999/profile');

      expect(response.status).toBe(404);
      expect(response.body.code).toBe('PROFILE_NOT_FOUND');
    });

    test('returns 400 for invalid userId format', async () => {
      const response = await request(app).get('/users/invalid/profile');

      expect(response.status).toBe(400);
      expect(response.body.code).toBe('INVALID_USER_ID');
    });

    test('returns 500 on database error', async () => {
      UserProfile.findByUserId.mockRejectedValue(
        new Error('Database connection failed')
      );

      const response = await request(app).get('/users/10/profile');

      expect(response.status).toBe(500);
      expect(response.body.code).toBe('INTERNAL_ERROR');
    });
  });
});
```

**Test command:**
```bash
npm test -- routes/profile.test.js
```

**Expected output:**
```
PASS  routes/profile.test.js
  Profile Routes
    GET /users/:userId/profile
      ✓ returns user profile for valid userId (12ms)
      ✓ returns 404 when profile not found (8ms)
      ✓ returns 400 for invalid userId format (6ms)
      ✓ returns 500 on database error (5ms)

Test Suites: 1 passed, 1 total
Tests: 4 passed, 4 total
Snapshots: 0 total
Time: 1.204 s
```

**Git commit message:**
```
feat: add GET /users/:userId/profile endpoint
```

---

## Task 4: Register profile routes in main app
**Depends on:** Task 3 (profile routes)

**Files affected:**
- backend-api/index.js

**Complete index.js (update section):**
```js
const express = require('express');
const cors = require('cors');
const authRoutes = require('./routes/auth');
const profileRoutes = require('./routes/profile');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', profileRoutes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({
    error: 'Internal server error',
    code: 'INTERNAL_ERROR'
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;
```

**Test command:**
```bash
npm test -- integration/routes.test.js
```

**Expected output:**
```
PASS  integration/routes.test.js
  App Routes
    ✓ GET /health returns 200 (4ms)
    ✓ GET /api/users/:userId/profile is registered (8ms)
    ✓ POST /api/auth/login is registered (6ms)

Test Suites: 1 passed, 1 total
Tests: 3 passed, 3 total
Snapshots: 0 total
Time: 0.923 s
```

**Git commit message:**
```
feat: register profile routes in main app
```

---
```

---

## Edge Cases & Fallback Paths

### Edge Case 1: Spec has holes in one project (missing implementation details)

**Diagnosis**: Shared spec says "add user authentication" but doesn't specify: which auth mechanism (OAuth, JWT, API key)? Web project has no guidance.

**Response**:
- **Escalate for spec clarification**: "Spec missing detail: authentication mechanism for web project. Options: OAuth2, JWT, API key. Which applies here?"
- **Default not allowed**: Do NOT fill in missing details without confirming with spec owner.
- **Lock clarification**: Once confirmed, document in tech plan: "Authentication: [chosen mechanism] per spec clarification [date]."

**Escalation**: NEEDS_CONTEXT - Cannot write tech plan without clarity. Ask spec owner for missing detail.

---

### Edge Case 2: Tasks cannot be 2-5 minutes (some tasks are inherently larger)

**Diagnosis**: Tech plan says "Task: implement OAuth2 flow: 3 minutes". Realistically, this takes 30+ minutes (API calls, token management, error handling).

**Response**:
- **Break down into smaller tasks**:
  1. "Set up OAuth2 library and dependencies" (2-3 min)
  2. "Implement token request flow" (3-4 min)
  3. "Implement token refresh logic" (3-4 min)
  4. "Add error handling and edge cases" (2-3 min)
- **If task cannot be broken down further**: Escalate to tech-plan-self-review, which will flag it as too large.
- **Justification**: Each task should be completable and reviewable in isolation.

**Escalation**: If a task cannot be broken below 5 minutes without becoming trivial, escalate: "Task is too large. Recommend: split into subtasks or adjust scope."

---

### Edge Case 3: Placeholder cannot be avoided (external dependency, research needed)

**Diagnosis**: Tech plan says "Task: integrate with [Third-Party API]". But API docs are not yet available. Placeholder: "Wait for API docs".

**Response**:
- **Document the blocker**: "Task blocked by: [Third-Party API docs]. Cannot proceed until [condition]."
- **Plan around it**: If possible, write tests/stubs for the API before it's available.
- **Track risk**: Flag in tech plan: "Critical path blocker: [API]. Delay risk: if not available by [date], project at risk."
- **Escalation to tech-plan-self-review**: Self-review will flag this as a risk and escalate if needed.

**Escalation**: BLOCKED - Task has unresolvable external dependency. Flag in tech plan and escalate to conductor if it impacts timeline.

---

### Edge Case 4: Tech Plan Has Cross-Repo Task Ordering Conflict

**Diagnosis**: Project A's task 3 requires a type from Project B's task 5. But the merge order puts Project A first. The tech plan as written cannot execute without breaking the dependency.

**Do NOT:** Silently reorder tasks across repos without flagging the cycle.

**Action:**
1. Identify the cross-repo dependency: which task in which project depends on output from another project?
2. Check if the dependency is a compile-time type, a runtime API call, or a shared contract
3. For compile-time types: require shared/common package task to complete first — update merge order
4. For runtime API: the dependency is satisfied at runtime, not compile-time — no task reordering needed, just document
5. For shared contracts: extract the shared type to a `shared/` or `lib/` project task that runs before both dependent tasks
6. Escalation: NEEDS_COORDINATION — cross-repo task ordering must be approved by both project leads

---

### Edge Case 5: Spec Has No Clear Test Boundary (Integration vs Unit)

**Diagnosis**: The shared-dev-spec defines a feature that spans multiple services (e.g., "user creates order, inventory decrements, notification sent"). The tech plan needs tests, but it's unclear which service owns which assertion.

**Do NOT:** Duplicate assertions across all services, or skip cross-service assertions entirely.

**Action:**
1. Each service owns assertions for its own state changes only (inventory service asserts decrement, not the notification)
2. The eval scenario (not the unit test) owns end-to-end assertions across services
3. Unit tests: pure function behavior, mocked external calls
4. Integration tests (within a service): real DB/cache, mocked external service clients
5. Eval scenarios: real services, real infrastructure, no mocks
6. Escalation: NEEDS_CONTEXT if a service boundary is ambiguous — ask the conductor which service owns the shared state

---

## End of Example

This example shows how each task:
1. Has complete, runnable code (not placeholders)
2. Specifies exact file paths
3. Includes a test command and expected output
4. Has a standard commit message
5. Respects dependencies (Task 2 depends on Task 1)

## Checklist

Before handing plans to tech-plan-self-review:

- [ ] One plan file written per affected repo (not one shared plan)
- [ ] Shared-dev-spec frozen (spec-freeze) before writing began
- [ ] Every spec requirement has at least one task that implements it
- [ ] All code in task blocks is complete and runnable (no `TODO`, no pseudocode)
- [ ] Each task has exact file paths (relative to project root)
- [ ] Test task precedes implementation task for each feature (TDD order)
- [ ] External dependencies identified and flagged if unresolvable

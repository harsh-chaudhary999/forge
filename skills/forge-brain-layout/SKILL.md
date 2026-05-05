---
name: forge-brain-layout
description: "WHEN: You need to look up brain directory structure, naming conventions, or query patterns before writing to or reading from the brain."
type: reference
version: 1.0.5
preamble-tier: 2
triggers:
  - "brain directory layout"
  - "how is brain structured"
  - "brain folder structure"
allowed-tools:
  - Bash
  - Read
---
# Brain Layout

## Introduction: Why Brain Structure Matters

The brain is the **immutable decision record** for your entire product. Every choice made during intake, negotiation, evaluation, and deployment is locked into the brain as auditable truth. The brain structure enables three critical capabilities:

1. **Rapid Navigation** — Consistent naming conventions and directory organization mean you can find any decision without searching
2. **Pattern Discovery** — File naming enables automated pattern matching (decisions by category, date, status)
3. **Decision Lifecycle Tracking** — Status tracking from draft → review → locked → archived shows the complete evolution of each choice

The brain is **not** a task tracker, issue system, or temporary notes file. It is the permanent record of architecture, product, and engineering decisions that shaped the product.

**Product terminology (`terminology.md`):** Per-task **domain** vocabulary (entities, roles, flags) lives in **`~/forge/brain/prds/<task-id>/terminology.md`**. It is **not** the same as **[forge-glossary](../forge-glossary/SKILL.md)** (Forge process terms). Optional **process checklists** for planning should prefer **`tech-plans/<repo>.md` Section 2** and **`planning-doubts.md`** over a separate “task tracker” file; see [docs/terminology-review.md](../../docs/terminology-review.md).

### Phase 2 prep (embeddings / hybrid index — optional today)

Before any vector or FTS index ships, prefer **YAML frontmatter** on new decision files: stable `id`, `updated` (ISO-8601 date), `product` / `project` where applicable, and optional `supersedes: <prior-id>` for knowledge updates. Use predictable `##` section boundaries in long notes so a later indexer can chunk without splitting mid-thought. Codebase scans already emit `SCAN.json` under `products/<slug>/codebase/`; optional **`route-aliases.tsv`** there augments phase56 route matching. Each scan run also writes **`graph.json`**, **`SCAN_SUMMARY.md`**, and **`.forge_scan_manifest.json`**; the runner keeps per-role temp inputs under **`<run_dir>/_role/<role>/`** (see `tools/scan_forge/scan_paths.py`) so multi-repo inventories are not overwritten.

## Directory Tree

```
~/forge/brain/
├── prds/                                  # Per-task PRD delivery (conductor path; parallel to product slug dirs)
│   └── <task-id>/
│       ├── prd-locked.md
│       ├── terminology.md                 # Product/domain terms for this task (not Forge glossary); see docs/terminology-review.md + docs/templates/terminology.md
│       ├── shared-dev-spec.md
│       ├── parity/                        # HARD-GATE before spec-freeze (see spec-freeze Step 0): external-plan.md OR completed checklist.md OR waiver.md
│       ├── planning-doubts.md             # Optional overflow for long Q&A during tech planning (summary still belongs in each tech-plans/*.md Section 0)
│       ├── delivery-plan.md               # Optional: program / rollout meta — NOT frozen for implementer isolation; may evolve until GA
│       ├── design/                        # REQUIRED for net-new UI: exports, MCP_INGEST.md, README (see intake Q9 + conductor P4.0b)
│       ├── qa/                            # Optional per-task QA / machine-eval artifacts
│       │   ├── manual-test-cases.csv      # Human acceptance inventory (qa-manual-test-cases-from-prd)
│       │   ├── semantic-automation.csv   # NL-first / semantic eval steps (docs/semantic-eval-csv.md)
│       │   ├── semantic-eval-manifest.json  # Coherence + machine gate (docs/forge-task-verification.md)
│       │   ├── semantic-eval-run.log     # Transcript for semantic / CSV-anchored runs
│       │   ├── qa-analysis.md
│       │   ├── scenarios-manifest.md
│       │   ├── branch-env-manifest.md
│       │   ├── TEST_SUITE_REPORT.md
│       │   └── logs/                      # eval host preflight / driver probe logs (eval-driver-*, QA-P5)
│       ├── tech-plans/
│       │   ├── HUMAN_SIGNOFF.md            # After agent self-review + XALIGN: human approval / feedback / waiver before State 4b (see docs/tech-plan-human-signoff.template.md)
│       │   └── <repo-name>.md
│       ├── checkpoints/                    # Session checkpoints from context-save/context-restore
│       └── eval/
│
├── products/                              # All product, PRD, and delivery context
│   └── {product-slug}/
│       ├── prd/
│       │   └── {prd-id}/
│       │       ├── PRD.md                    # Locked after intake gate
│       │       ├── council/                  # Surface team reasonings
│       │       │   ├── backend.md            # Backend surface perspective
│       │       │   ├── web.md                # Web frontend perspective
│       │       │   ├── app.md                # App frontend perspective
│       │       │   └── infra.md              # Infrastructure perspective
│       │       ├── contracts/                # Service boundaries and contracts
│       │       │   ├── api-rest.md           # REST API contract
│       │       │   ├── events-kafka.md       # Kafka event contract
│       │       │   ├── cache-redis.md        # Redis cache contract
│       │       │   ├── schema-db.md          # MySQL schema contract
│       │       │   └── search-es.md          # Elasticsearch contract
│       │       ├── shared-dev-spec.md        # Locked after spec-freeze
│       │       ├── tech-plans/               # Per-repo implementation plans
│       │       │   ├── {repo-name}.md        # One plan per repo
│       │       │   └── ...
│       │       ├── evals/                    # Evaluation results and verdicts
│       │       │   ├── scenarios.md          # Eval scenario definitions
│       │       │   ├── run-{timestamp}.md    # Individual eval run results
│       │       │   └── verdict.md            # Final eval-judge verdict
│       │       ├── dreaming/                 # Conflict resolution notes
│       │       │   ├── inline-{timestamp}.md # Inline conflict resolutions
│       │       │   └── ...
│       │       └── learnings/                # Retrospective analysis
│       │           └── {prd-id}-retrospective.md  # Post-PR dreamer retrospective
│       ├── codebase/                       # Codebase knowledge graph (from /scan)
│       │   ├── route-aliases.tsv           # Optional — extra synthetic API route lines for phase56 (same columns as phase35 routes)
│       │   ├── SCAN.json                     # Scan metadata: `repos.<role>` per repo + aggregated top-level fields (see scan-codebase)
│       │   ├── SCAN_SUMMARY.md               # One-page scan orientation + limitations (regenerated each scan)
│       │   ├── graph.json                    # Derived module + cross-repo edge graph (regenerated)
│       │   ├── .forge_scan_manifest.json     # Per-role git tree/head fingerprints (tooling)
│       │   ├── index.md                      # Architecture style, module map, entry points
│       │   ├── patterns.md                   # Detected architecture patterns with evidence
│       │   ├── api-surface.md                # REST endpoints, exported symbols, event schemas
│       │   ├── gotchas.md                    # TODOs, FIXMEs, test-case-derived edge cases
│       │   ├── cross-repo.md                 # Cross-repo API calls, shared types, env contracts
│       │   ├── repo-docs/                    # Verbatim curated Markdown + OpenAPI spec mirrors from scanned repos (docs/, ADRs, READMEs…); INDEX.md + index.json (content_sha256)
│       │   └── modules/                      # One .md per module/feature directory
│       │       ├── <module-name>.md          # Exports, imports, dependents, edge cases
│       │       └── ...
│       └── patterns/                       # Identified reusable patterns
│           ├── warm/                         # Seen 1 time
│           ├── active/                       # Seen 2+ times (same product)
│           └── candidates/                   # Seen 3+ times (cross-product) → skill candidate
│
├── decisions/                              # Global architectural decisions (LOCKED)
│   ├── architecture/                        # System design decisions (D001-D099)
│   │   ├── D001_microservice_vs_monolith.md
│   │   ├── D002_async_event_bus.md
│   │   └── ...
│   ├── product/                             # Product feature decisions (D100-D199)
│   │   ├── D102_session_timeout_strategy.md
│   │   ├── D150_multi_tenant_isolation.md
│   │   └── ...
│   ├── engineering/                         # Implementation decisions (D200-D299)
│   │   ├── D201_orm_vs_raw_sql.md
│   │   ├── D250_caching_layer.md
│   │   └── ...
│   └── ops/                                 # Operations and infrastructure (D300+)
│       ├── D301_deployment_strategy.md
│       ├── D350_monitoring_stack.md
│       └── ...
│
├── drafts/                                 # Proposals under review (not yet locked)
│   ├── pending/                             # Awaiting council review
│   │   ├── draft-{author}-{topic}.md
│   │   └── ...
│   └── resolved/                            # Reviewed, decision made (ready to lock)
│       ├── {decision-topic}.md
│       └── ...
│
├── archived/                               # Superseded or deprecated decisions
│   ├── reasons.txt                          # Index of why decisions were archived
│   ├── D095_deprecated_auth_flow.md         # Reason: replaced by D102
│   └── ...
│
└── README.md                                # Brain overview and navigation guide
```

### Directory Annotations

**qa/semantic-automation.csv** — NL-first or structured semantic eval steps; schema and orchestration: **`docs/semantic-eval-csv.md`**, skill **`qa-semantic-csv-orchestrate`**.

**qa/semantic-eval-manifest.json** — Records machine-eval outcome and paths for **`verify_forge_task.py`**. See **`docs/forge-task-verification.md`**.

**qa/semantic-eval-run.log** — Append-only transcript for semantic / CSV-anchored execution (complements driver preflight logs under **`qa/logs/`**).

**qa/logs/** — Under **`~/forge/brain/prds/<task-id>/qa/logs/`**, optional **eval host preflight** and driver probe transcripts (ADB, CDP, API reachability). Create with **`mkdir -p`** before append. **Naming:** **`eval-preflight-<ISO8601>.log`**; use **append-only** sections per surface with markers such as **`--- android ---`**, **`--- web ---`**, **`--- ios ---`**, **`--- api ---`**. **Redact** tokens and secrets. Canonical references: **`eval-driver-android-adb`**, **`eval-driver-web-cdp`**, **`eval-driver-ios-xctest`**, **`eval-driver-api-http`**, **`qa-pipeline-orchestrate`** (QA-P5).

**prds/** — Task-scoped conductor path (`<task-id>/`) aligned with `intake-interrogate`, `conductor-orchestrate`, and `~/forge/brain/prds/<task-id>/prd-locked.md`. Holds **`design/`** for net-new UI (exports, `MCP_INGEST.md`, `README.md`). Distinct from **`products/{slug}/prd/{prd-id}/`** layout; teams may use one or both — do not assume artifacts exist in both without checking.

**products/** — Contains all PRD-specific context and delivery artifacts
- **`forge_qa_csv_before_eval`** in **`~/forge/brain/products/<slug>/product.md`** is a **product-level switch** (omit or `false` = no CSV hard gate; **`true` = hard gate**): when **`true`**, **`conductor-orchestrate`** **must not** log **`[P4.0-SEMANTIC-EVAL]`** until approved **`~/forge/brain/prds/<task-id>/qa/manual-test-cases.csv`** exists and **`[P4.0-QA-CSV]`** is logged — so TDD and eval trace to the same acceptance inventory. Calling the switch “optional” only means **teams choose** whether CSV is mandatory for that product; the gate is **not** optional once the flag is on.
- Optional **`qa_track`**: **`delivery`** (default mental model — **`/forge`** + State 4b CSV) vs **`standalone`** (team leans on **`/qa`** / **`qa-run`** without full conductor). **Documentation only** — does not reroute automation by itself.
- Optional **machine gate** on the brain repo: run **`python3 <forge>/tools/verify_forge_task.py --task-id <id> --brain ~/forge/brain`** in CI — see Forge **`docs/forge-task-verification.md`** (checks valid **`qa/semantic-eval-manifest.json`** + **`qa/semantic-automation.csv`** coherence when applicable, `conductor.log` ordering, QA CSV when the flag is true, net-new **design/** evidence). For **tech plan discipline**, add **`--strict-tech-plans`** so **`REVIEW_PASS`** cannot ship without FORGE-GATE Section 0c / recross markers and canonical **1b** headings (**`tools/verify_tech_plans.py`**).
- Each product gets its own slug (e.g., `auth-service`, `web-ui`)
- Each PRD gets a unique ID (e.g., `PRD-20260410-001`)
- Council, contracts, evals, and learnings are nested under PRD ID
- Patterns track reusable solutions identified during delivery

**decisions/** — Contains global architectural and engineering decisions
- Decisions are immutable once locked
- Numbered sequentially with category ranges (D001-D099 architecture, D100-D199 product, etc.)
- Each file is a complete record: problem, solution, rationale, alternatives
- Links to related decisions track dependencies

**drafts/** — Workspace for decisions under review
- `pending/` holds proposals awaiting council or stakeholder review
- `resolved/` holds reviewed proposals ready to lock as decisions
- Same format as locked decisions, but with status=draft

**archived/** — Historical record of superseded decisions
- `reasons.txt` documents why each decision was archived
- Links to replacement decision (if superseded) are included in archived file
- Timestamp of archival is recorded

**links/** — Cross-reference edges between decisions
- Enables navigation of related decisions
- Format: `{source}-to-{target}.md` (e.g., `D001-to-D050.md`)

## File Naming Conventions

| Location | Pattern | Example |
|---|---|---|
| Product slug | lowercase, hyphenated | `my-saas-app` |
| PRD ID | `PRD-YYYYMMDD-NNN` | `PRD-20260410-001` |
| Tech plan | `{repo-name}.md` | `backend-api.md` |
| Eval run | `run-{ISO-timestamp}.md` | `run-2026-04-10T14-30-00.md` |
| Decision | `D{NNN}.md` (zero-padded) | `D005.md` |
| Retrospective | `{prd-id}-retrospective.md` | `PRD-20260410-001-retrospective.md` |
| Inline dream | `inline-{ISO-timestamp}.md` | `inline-2026-04-10T15-00-00.md` |

## File Format Specifications

### Decision File Format

**Location:** `brain/decisions/{category}/D{NNN}_{topic}.md`

**Example:** `brain/decisions/product/D102_session_timeout_strategy.md`

**Format:**

```markdown
---
title: Session Timeout Strategy
date_locked: 2026-04-10T14:30:00Z
status: LOCKED
author: backend-team
tags: [authentication, session-management, security]
category: product
decision_number: D102
relates_to: [D001, D050, D085]
---

## Problem

[2-3 paragraphs describing the business or technical problem this decision addresses]
- What pain points or constraints did we face?
- Why couldn't existing approaches work?

## Solution

[Clear statement of the chosen solution]
- [Key decision]
- [Key decision]
- [Rationale for this specific choice]

## Rationale

[Detailed explanation of why this solution was chosen]
- Trade-offs made
- Risks accepted or mitigated
- Impact on system architecture

## Alternatives Considered

### Alternative 1: [Name]
- Pros: ...
- Cons: ...
- Why not chosen: ...

### Alternative 2: [Name]
- Pros: ...
- Cons: ...
- Why not chosen: ...

## Implementation Notes

- Language/stack specifics
- Configuration defaults
- Expected performance characteristics

## Links

- Related decisions: D001, D050, D085
- Related PRD: PRD-20260410-001
- Affected repos: backend-api, auth-service
```

### Draft File Format

**Location:** `brain/drafts/pending/{topic}.md` or `brain/drafts/resolved/{topic}.md`

**Format:** Same as decision file, but with these differences:

```markdown
---
title: [Proposed Decision Topic]
date_proposed: 2026-04-08T10:00:00Z
status: DRAFT  # or AWAITING_REVIEW
author: submitter-name
tags: [...]
---

[Same sections as decision file]

## Council Review

### Backend Review
- Status: APPROVED / PENDING / REJECTED
- Reviewer: backend-lead
- Comment: [Feedback]

### Web Review
- Status: APPROVED / PENDING / REJECTED
- Reviewer: web-lead
- Comment: [Feedback]

### App Review
- Status: APPROVED / PENDING / REJECTED
- Reviewer: app-lead
- Comment: [Feedback]

### Infra Review
- Status: APPROVED / PENDING / REJECTED
- Reviewer: infra-lead
- Comment: [Feedback]
```

### Archived Decision Format

**Location:** `brain/archived/D{NNN}_{topic}.md`

**Format:** Decision file with addition of archival metadata:

```markdown
---
title: [Original Title]
date_locked: 2026-02-01T10:00:00Z
date_archived: 2026-04-10T14:30:00Z
status: ARCHIVED
archive_reason: SUPERSEDED  # or DEPRECATED, OBSOLETE, INCORRECT
replaced_by: D200  # If superseded
---

## Archival Note

Reason for archival: [Explanation of why this decision is no longer valid]

Replacement decision: [Link to replacement, if superseded]

Date archived: 2026-04-10

[Original decision content follows...]
```

### PRD File Format (Product Context)

**Location:** `brain/products/{product-slug}/prd/{prd-id}/PRD.md`

**Status:** LOCKED after intake gate completes

**Contains:**
- Problem statement
- Acceptance criteria
- User journeys
- Success metrics
- Scope and constraints

**Related files in same PRD directory:**
- `council/*.md` — Surface team perspectives (locked after council-gate)
- `contracts/*.md` — Service boundaries (locked after spec-freeze)
- `shared-dev-spec.md` — Implementation spec (locked after spec-freeze)
- `tech-plans/{repo}.md` — Per-repo implementation plans
- `evals/scenarios.md` — Eval test cases
- `evals/run-*.md` — Individual eval run results
- `evals/verdict.md` — Final eval judge verdict

## Immutability Rules

| File | Locked After | Can Be Changed By |
|---|---|---|
| `PRD.md` | Intake gate passes | Full re-intake only |
| `shared-dev-spec.md` | `spec-freeze` skill runs | Full council re-negotiation only |
| `D{NNN}.md` | Decision is recorded | Never — append a new decision instead |
| Council surface files | Council gate passes | Re-negotiation only |
| Contract files | Spec freeze | Re-negotiation only |

## Anti-Patterns: How NOT to Use the Brain

### Anti-Pattern 1: Store Non-Decisions in Brain

**What it looks like:**
```
brain/decisions/D500_user_complained_about_feature.md
brain/decisions/D501_bug_in_production.md
brain/decisions/D502_performance_regression.md
```

**Why it's wrong:**
- Brain is for locked architectural and product decisions
- Issues, bugs, and complaints are temporary events
- Task tracker (Jira, GitHub Issues) is the right place for temporary work
- Brain gets polluted with noise; decision queries become unreliable

**How to fix it:**
- Store issues in project tracking system
- Link to decisions from issues (e.g., "This bug violates D102")
- Only write to brain via `brain-write` skill
- Enforce `type=decision` in decision frontmatter

**Enforcement:**
```
brain-write rejects any record that isn't a deliberate decision
Only LOCKED, DRAFT, and ARCHIVED status are valid
```

### Anti-Pattern 2: Use Brain as Task Tracker

**What it looks like:**
```
brain/products/auth-service/prd/PRD-20260410-001/
├── implementation-status.md          # WRONG: task state
├── jira-tickets.txt                  # WRONG: task list
└── developer-notes.md                # WRONG: temporary notes
```

**Why it's wrong:**
- Brain is immutable; task state changes constantly
- Task progress belongs in project management tool
- Brain entries require commits; task updates don't
- Decision lockdown gets confused with task completion

**How to fix it:**
- Store task state in Jira/GitHub Projects
- Reference decisions from task (e.g., "Implement decision D102")
- Brain contains decisions; tasks implement decisions
- Use `learnings/` only for post-delivery retrospectives

**Enforcement:**
```
Reject PRD mutations after intake-gate
Reject PRD mutations after spec-freeze
Use brain-forget to archive, never bulk-delete
```

### Anti-Pattern 3: Modify Brain Files Directly

**What it looks like:**
```bash
# User directly edits a decision file
vi brain/decisions/D042.md
git add brain/decisions/D042.md
git commit -m "fix typo in D042"
```

**Why it's wrong:**
- Direct edits bypass lock/unlock/archive workflows
- Audit trail is lost; no provenance tracking
- Can't distinguish typo fixes from decision changes
- brain-why skill can't trace the change

**How to fix it:**
- Always use `brain-write` skill to lock decisions
- Use `brain-forget` skill to archive decisions
- Direct edits are only for bootstrapping (empty brain)
- All mutations logged in git with structured commit messages

**Enforcement:**
```
brain-persist: detects direct edits, raises alert
Pre-commit hook: warns on direct brain file modifications
brain-why: traces all changes back to skill invocations
```

## Edge Cases: How to Handle Unusual Situations

### Edge Case 1: Brain Not Initialized

**Symptom:** `brain/` directory doesn't exist or is not in git

**Root cause:**
- First-time setup on a repo
- User cloned without initializing brain
- Shallow clone that excluded brain/

**Action Plan:**

1. Check if brain directory exists:
   ```bash
   ls -la brain/
   ```

2. If not found, initialize:
   ```bash
   mkdir -p brain/decisions/{architecture,product,engineering,ops}
   mkdir -p brain/drafts/{pending,resolved}
   mkdir -p brain/archived
   mkdir -p brain/products
   mkdir -p brain/links
   touch brain/README.md
   git add brain/
   git commit -m "brain: initialize structure"
   ```

3. Seed with empty README

**Escalation:** NEEDS_INFRA_CHANGE
- Document in project setup guide
- Add to git post-clone hook
- Include in forge-init script

### Edge Case 2: Brain Corrupted or Lost

**Symptom:** 
- Brain directory exists but not tracked in git
- File permissions wrong (not readable)
- Brain structure partially missing (some categories empty)

**Root cause:**
- User force-pushed, lost history
- Brain copied manually without .git
- Incomplete migration from old system

**Action Plan:**

1. Check git status:
   ```bash
   cd brain/
   git status
   git log --oneline | head -5
   ```

2. If not tracked, restore from backup:
   ```bash
   git reset --hard origin/main
   ```

3. If partially missing, check what's gone:
   ```bash
   find brain/ -type d | sort
   ```

4. Recreate missing structure:
   ```bash
   mkdir -p brain/decisions/{architecture,product,engineering,ops}
   mkdir -p brain/drafts/{pending,resolved}
   ```

5. Verify integrity:
   ```bash
   brain-read: verify structure
   ```

**Escalation:** NEEDS_COORDINATION
- Notify team of brain state
- Restore from backup if necessary
- Document what was lost

### Edge Case 3: Brain in Wrong Directory

**Symptom:**
- User cloned a different branch
- Brain exists but in unexpected path
- Multiple brain directories (confusion)

**Root cause:**
- User cloned wrong repository
- Symlink points to wrong location
- Team forked codebase and split brain structure

**Action Plan:**

1. Verify current directory:
   ```bash
   pwd
   ls -la .git/
   ```

2. Check where brain actually is:
   ```bash
   find . -name "brain" -type d
   ```

3. If it's a symlink, check target:
   ```bash
   ls -la brain/
   # Shows: brain -> /path/to/real/brain
   ```

4. Ensure the correct repository:
   ```bash
   git remote -v
   git branch
   ```

5. Guide to correct location:
   ```bash
   # If in wrong repo, clone correct one:
   git clone https://correct-repo.git
   cd correct-repo
   ```

**Escalation:** NEEDS_CONTEXT
- Document team's brain organization
- Clarify which repos share brain
- Update onboarding guide

## Quick Reference Card

| Path Pattern | What It Contains | File Count | Query Tool |
|---|---|---|---|
| `decisions/architecture/` | System design (D001-D099) | 50-100 | by design category |
| `decisions/product/` | Feature decisions (D100-D199) | 100-200 | by feature area |
| `decisions/engineering/` | Implementation (D200-D299) | 50-100 | by service |
| `decisions/ops/` | Infrastructure (D300+) | 20-50 | by deployment/ops area |
| `drafts/pending/` | Awaiting review | <10 | by topic or reviewer |
| `drafts/resolved/` | Approved, ready to lock | <10 | by topic |
| `archived/` | Superseded decisions | varies | by archive reason |
| `products/{slug}/prd/{id}/` | All PRD context | ~50 files | by product + PRD |
| `products/{slug}/codebase/` | Module map, patterns, API surface, cross-repo | 10-50 | by module or topic |
| `products/{slug}/patterns/` | Reusable patterns | 5-20 | by frequency |
| `links/` | Decision relationships | varies | by source → target |

**Common Queries:**

| Question | Query |
|---|---|
| How do I record a new decision? | Use `brain-write` skill |
| How do I find related decisions? | Check `relates_to` field or use `brain-recall` |
| Why was this decision made? | Use `brain-why` skill |
| Is this decision still valid? | Check if it's in `archived/` or `decisions/` |
| What's the next available decision number? | Count files in `decisions/{category}/` |
| Can I change a locked decision? | No; create a new decision or archive the old one |
| How do I archive a decision? | Use `brain-forget` skill |

## Status Lifecycle: Decision States

```
DRAFT
  ↓
AWAITING_REVIEW (in brain/drafts/pending/)
  ↓ (council approval or rejection)
  ├→ REJECTED
  │   └→ Discard (never locked)
  │
  └→ APPROVED (in brain/drafts/resolved/)
      ↓
      LOCKED (in brain/decisions/{category}/)
        ↓ (over time, becomes obsolete or replaced)
        ├→ SUPERSEDED (in brain/archived/)
        │   └→ Links to replacement decision
        │
        ├→ DEPRECATED (in brain/archived/)
        │   └→ No longer recommended
        │
        └→ OBSOLETE (in brain/archived/)
            └→ No longer applicable
```

**Timestamps:**
- `date_proposed`: When draft was created
- `date_locked`: When decision transitioned to LOCKED
- `date_archived`: When decision was superseded/deprecated/obsolete

## Cross-References: Related Skills

The forge-brain-layout documents structure. These skills work with the brain:

| Skill | Purpose |
|---|---|
| `brain-write` | Create and lock decisions; create drafts for review |
| `brain-read` | Look up decisions; verify PRD structure |
| `brain-recall` | Search brain by keyword; find related decisions |
| `brain-why` | Trace provenance; see who made decision when |
| `brain-forget` | Archive decisions; mark as superseded/deprecated |
| `brain-link` | Create edges between related decisions |
| `scan-codebase` | Populate `codebase/` directory with module maps, patterns, API surface |

**When to use each:**

- **Writing a decision?** → `brain-write`
- **Need context for a PRD?** → `brain-read`
- **Searching for decisions?** → `brain-recall`
- **Curious why a decision was made?** → `brain-why`
- **Decision is obsolete?** → `brain-forget`
- **Two decisions are related?** → `brain-link`

## Navigation Patterns

### Navigate by Product Area

To find all decisions and context for a specific product:

```
brain/products/{product-slug}/prd/{prd-id}/
├── PRD.md                          # Problem and acceptance criteria
├── council/                         # How each surface team sees it
├── contracts/                       # Service boundaries
├── shared-dev-spec.md              # Implementation specification
├── tech-plans/                      # Per-repo implementation
├── evals/                           # Test results
└── learnings/                       # Retrospective analysis
```

**Example:** To understand all decisions for auth-service PRD-20260410-001:
```bash
ls -la brain/products/auth-service/prd/PRD-20260410-001/
```

### Navigate by Decision Category

Architecture decisions (foundational system design):
```
brain/decisions/architecture/D001.md through D099.md
```

Product decisions (feature and UX choices):
```
brain/decisions/product/D100.md through D199.md
```

Engineering decisions (implementation approach):
```
brain/decisions/engineering/D200.md through D299.md
```

Operations decisions (deployment, infrastructure, observability):
```
brain/decisions/ops/D300.md and above
```

### Navigate by Decision Status

**LOCKED decisions** (auditable, immutable):
```
brain/decisions/{category}/D{NNN}.md
```

**Drafts awaiting review** (not yet decided):
```
brain/drafts/pending/{topic}.md
```

**Drafts ready to lock** (approved by council):
```
brain/drafts/resolved/{topic}.md
```

**Archived decisions** (superseded or deprecated):
```
brain/archived/D{NNN}_{topic}.md
```

### Navigate by Keyword/Relationship

To find related decisions, check the `relates_to` field in decision files:

```markdown
---
relates_to: [D001, D050, D085]
---
```

Use brain-recall skill to search by keyword:
```
brain-recall: "session timeout"
```

Use brain-why skill to trace provenance of a decision:
```
brain-why: D102
```

### Query Patterns (Specific Examples)

**Find all decisions for a product:**
```
~/forge/brain/products/{product-slug}/prd/{prd-id}/
```

**Find all eval results for a PRD:**
```
~/forge/brain/products/{product-slug}/prd/{prd-id}/evals/
```

**Find patterns promoted to skill candidates:**
```
~/forge/brain/products/{product-slug}/patterns/candidates/
```

**Find cross-references between decisions:**
```
~/forge/brain/links/{source}-to-{target}.md
```

**Find retrospective learnings:**
```
~/forge/brain/products/{product-slug}/prd/{prd-id}/learnings/
```

**Find all architecture decisions:**
```
~/forge/brain/decisions/architecture/
```

**Find the latest decisions:**
```
ls -lt ~/forge/brain/decisions/**/*.md | head -20
```

**Find all decisions about authentication:**
```
grep -r "authentication" ~/forge/brain/decisions/ --include="*.md"
```

**Find decisions archived in last 30 days:**
```
find ~/forge/brain/archived/ -mtime -30 -name "*.md"
```

## Commit Conventions

All brain writes are committed with structured messages:

| Action | Commit message format |
|---|---|
| Lock PRD | `brain: lock PRD {prd-id}` |
| Lock spec | `brain: freeze shared-dev-spec for {prd-id}` |
| Record decision | `brain: decision D{NNN} — {one-line summary}` |
| Eval result | `brain: eval run for {prd-id} — {GREEN/YELLOW/RED}` |
| Retrospective | `brain: retrospective for {prd-id} (score: X/25)` |
| Link decisions | `brain: link {source} → {target}` |

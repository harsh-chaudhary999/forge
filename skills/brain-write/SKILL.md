---
name: brain-write
description: "WHEN: You need to record a decision, lock a spec, log an eval run, or document learnings in the brain."
type: flexible
version: 1.0.2
preamble-tier: 2
triggers:
  - "record a decision"
  - "write to brain"
  - "log to brain"
  - "lock a spec"
  - "document in brain"
allowed-tools:
  - Bash
  - Edit
  - Read
  - Write
  - AskUserQuestion
---

# Brain Write

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I'll commit the decision later" | Uncommitted decisions are invisible decisions. If it's not in git, it didn't happen. |
| "The commit message can be brief" | Commit messages are the primary search surface for brain-recall. Vague messages make past decisions unfindable. |
| "I don't need to reference task-id or decision-id in the commit" | Without at least one of {task-id, decision-id, contract-id}, `git log --grep` returns noise. Every brain commit must anchor to one identifier. |
| "I'll update the existing decision file" | Brain decisions are append-only. Editing a locked decision destroys provenance. Create a new decision that supersedes the old one. |
| "This doesn't need a full decision record" | Every decision needs who, when, why, evidence. "Quick notes" become orphaned context that no one can trace. |
| "I'll write it to a scratch file first" | Scratch files bypass the brain's git-backed audit trail. Write directly to the correct brain path. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
EVERY BRAIN WRITE IS A GIT COMMIT — NOT JUST A FILE WRITE.
EVERY BRAIN COMMIT MESSAGE MUST INCLUDE task_id:, decision_id:, OR contract_id: ANCHOR.
COMMITS WITHOUT ANCHORS ARE NOISE — THEY CANNOT BE FOUND, RESUMED, OR AUDITED.
A DECISION THAT EXISTS ONLY IN CHAT IS LOST AT CONTEXT COMPACTION.
```

Every write is a git commit. Pattern:

## 1. Write the file
```bash
cat > ~/forge/brain/prds/<task-id>/shared-dev-spec.md <<'EOF'
# Shared Dev Spec

[content]
EOF
```

## 1b. Update the scope's OKF index.md + log.md (required, not optional)
The brain is an [OKF](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/) +
Memory-tool directory (see `forge-brain-layout`). Before committing, in the **same
scope directory** you just wrote into:
```bash
SCOPE=~/forge/brain/prds/<task-id>
# 1) add/refresh the file's row in the scope index (create index.md if absent)
#    "| shared-dev-spec.md | spec | locked contracts for <task-id> |"
# 2) append a dated, newest-first entry to the scope changelog (create log.md if absent)
printf '## %s\n- wrote shared-dev-spec.md — locked contracts for <task-id>\n\n' \
  "$(date -u +%Y-%m-%d)" | cat - "$SCOPE/log.md" 2>/dev/null > "$SCOPE/log.md.tmp" && mv "$SCOPE/log.md.tmp" "$SCOPE/log.md"
```

## 2. Commit with context (include index.md + log.md)
```bash
git -C ~/forge/brain add prds/<task-id>/shared-dev-spec.md prds/<task-id>/index.md prds/<task-id>/log.md
git -C ~/forge/brain commit -m "spec: lock shared dev spec for <task-id>

Converged across: backend, web, app, infra
Contracts locked: API v2, MySQL schema changes, Redis invalidation
Next: tech-plan-write-per-project"
```

## Key Guidelines

- **Product terminology (`terminology.md`)** — **Path:** `~/forge/brain/prds/<task-id>/terminology.md`. **Format:** YAML frontmatter per [docs/templates/terminology.md](../../docs/templates/terminology.md) (`task_id`, `status`, `updated`, `open_doubts`, `terminology_risk`). **When to use this skill:** creating or **committing** the file after a review turn (not ad hoc edits without `git commit` in the brain). **HARD-GATE content:** use [docs/terminology-review.md](../../docs/terminology-review.md) for review protocol; prefer **append** to the **Revision** table over silent edits to locked rows. For machine DRIFT logs by convention, see `qa/terminology-drift-log.md` in the template [docs/templates/terminology-drift-log.md](../../docs/templates/terminology-drift-log.md) (optional).
- **One file per decision** (prd-locked.md, shared-dev-spec.md, retrospective.md, etc.)
- **Descriptive commit messages** — why this decision, what it depends on, next step

**Commit message searchability (HARD-GATE):** Every brain commit message MUST include at least one of:
- `task_id: <id>` — ties commit to the PRD task
- `decision_id: D<NNN>` — ties commit to a specific decision record
- `contract_id: <name>` — ties commit to a locked contract (api-rest, schema-db, event-bus, etc.)

Without one of these anchors, `brain-recall` grep and `git log --grep` produce too much noise. The anchor can appear in the subject line or body — not only in the commit footer.

### Anchor-Type Matrix

Every brain commit message **must** include the appropriate anchor. Use this table to pick the right one:

| File written | Required anchor | Example |
|---|---|---|
| `prd-locked.md` | `task_id:` | `task_id: post-jml-recruiter-verification-nudges` |
| `shared-dev-spec.md` | `task_id:` | `task_id: post-jml-recruiter-verification-nudges` |
| `tech-plans/*.md` | `task_id:` | `task_id: post-jml-recruiter-verification-nudges` |
| `decisions/*.md` | `decision_id:` | `decision_id: auth-strategy-v2` |
| `blockers/*.md` | `task_id:` | `task_id: post-jml-recruiter-verification-nudges` |
| `contracts/*.md` | `contract_id:` | `contract_id: api-rest-v1` |
| `qa/*.md` / `qa/*.csv` | `task_id:` | `task_id: post-jml-recruiter-verification-nudges` |
| `context/*.md` | `task_id:` | `task_id: post-jml-recruiter-verification-nudges` |

**Rule:** `decision_id:` is for architectural decisions that outlive a single task. `contract_id:` is for cross-team API/schema contracts. Everything else uses `task_id:`.

- **Markup:** Markdown always
- **Paths:** Follow `~/forge/brain/` structure exactly
- **No binary files**

## Provenance Tracking Checklist

When writing a decision, capture the 11 provenance elements (decision ID, title, problem statement, date/phase, decision-maker/stakeholders, the decision itself, alternatives, impact/rollback, linked decisions, status, review/approval). See [reference/provenance-checklist.md](reference/provenance-checklist.md) for the full per-element checklist (why capture, how to document, examples, production patterns).

---

## Commit Message Patterns

Every write to brain is a git commit. There are 5 canonical commit-message patterns — spec lock, decision record, contract negotiation, retrospective/learning, and migration plan. See [reference/commit-message-patterns.md](reference/commit-message-patterns.md) for each pattern's template, worked example, and key-sections breakdown.

---

## Metadata Frontmatter Template

Use this YAML frontmatter in decision records, specs, and contracts. Standardize field names to enable brain-recall, brain-link, and brain-why.

> **OKF + Memory-tool (see `forge-brain-layout` → OKF alignment).** `type` is also the [Open Knowledge Format](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/) required field — keep it concrete so OKF consumers and a future indexer can filter by kind. When you write into a brain **scope** (`prds/<task-id>/`, `decisions/<category>/`, …): (1) add or update that scope's **`index.md`** row for the new file, and (2) append a dated, newest-first entry to that scope's **`log.md`** describing what changed and why (append-only). The brain is the agent's durable Memory-tool store — persist the decision here, not only in chat.

Valid decision `type` values:

| type | Use for |
|---|---|
| architecture | System structure, service boundaries, component topology |
| api | External/internal interface contracts and versioning choices |
| database | Schema, migration, indexing, and data-model decisions |
| infra | Deployment/runtime/platform choices (compute, network, ops) |
| process | Workflow/governance/pipeline decisions |
| decision | General decision record when none of the above is a precise fit |

```yaml
---
decision_id: D087
title: Adopt gRPC for Service-to-Service Communication
type: architecture
status: active  # active, warm, cold, archived
date: 2025-11-15
phase: scaling  # optional; omit if decision is evergreen
owner: platform-infra
decision_maker: Alice Chen (Principal Architect)
stakeholders: [backend-team, web-team, app-team, devops]
approved_by:
  - name: VP Engineering
    date: 2025-11-16
  - name: Principal Database Architect
    date: 2025-11-16
  - name: Security Review Board
    date: 2025-11-18
related_decisions:
  parent: D042  # "Adopt service mesh architecture"
  children: [D088, D089, D090]  # "gRPC auth", "service discovery", "tracing"
  related: [D023, D055]  # "API versioning", "Observability stack"
tags: [#api, #performance, #architecture, #scaling]
evidence:
  - type: load-test
    link: https://metrics.internal/reports/grpc-vs-rest-2025-11
    finding: gRPC 10x RPS improvement, p99 latency 50x reduction
  - type: incident
    link: "incident-2025-11-14"  # Link to learning in brain
    finding: REST polling exhausted connection pools; gRPC uses multiplexed streams
  - type: contract
    link: "contracts/grpc-service-definitions.proto"
    finding: All 47 services can express APIs in gRPC
review_date: <~90 days out, e.g. 2026-09-30>  # Quarterly review of adoption metrics
deprecation_planned: 2027-01-01  # REST API fully sunset
---
```

**Field definitions:**

| Field | Purpose | Example |
|-------|---------|---------|
| `decision_id` | Unique identifier for linking | D087 |
| `title` | One-line summary | "Adopt gRPC for Service-to-Service Communication" |
| `type` | Category for filtering | architecture, api, database, infra, process |
| `status` | Current state of decision | active, warm, cold, archived |
| `date` | ISO date when decided | 2025-11-15 |
| `phase` | Optional project/roadmap phase | scaling, launch, stability |
| `owner` | Team responsible for execution | platform-infra |
| `decision_maker` | Person/role who made final call | Alice Chen (Principal Architect) |
| `stakeholders` | Teams/people impacted | [backend-team, web-team, app-team] |
| `approved_by` | Formal sign-offs with dates | [{name: VP Eng, date: 2025-11-16}] |
| `related_decisions` | Links to parent/child/related | parent: D042, children: [D088, ...] |
| `tags` | Searchable tags for brain-recall | #api, #performance, #scaling |
| `evidence` | Links to proof (tests, metrics, incidents) | load-test: URL, incident: link |
| `review_date` | When to revisit this decision | a future date ~1 quarter out (quarterly) |
| `deprecation_planned` | When to sunset if applicable | 2027-01-01 |

**Link conventions for decision graphs:**
```yaml
related_decisions:
  parent: D042                    # Single parent (this decision is a child of D042)
  children: [D088, D089, D090]    # Multiple children (D088, D089, D090 are children of this)
  related: [D023, D055]           # Sibling/peer decisions (influence but don't depend)
  supersedes: D040                # This decision replaces D040
  superseded_by: D100             # This decision was replaced by D100
```

**Tag structure** (use consistently):
- Infrastructure: `#infra`, `#kubernetes`, `#database`, `#cache`, `#messaging`
- API & Services: `#api`, `#grpc`, `#rest`, `#graphql`, `#service-mesh`
- Data & Scaling: `#performance`, `#scaling`, `#sharding`, `#replication`, `#caching`
- Process: `#process`, `#tooling`, `#testing`, `#deployment`, `#incident-response`
- Architecture: `#architecture`, `#design-pattern`, `#refactoring`, `#migration`

---

## Common Pitfalls

Five recurring failure modes when writing to the brain: incomplete commit messages, missing alternatives section, no evidence links, decisions without IDs, and stale decisions never marked for archival. See [reference/common-pitfalls.md](reference/common-pitfalls.md) for each pitfall's BAD/GOOD examples and how-to-avoid guidance.

---

## Coordination with Other Brain Skills

### brain-write → brain-read
**What you write, others read.** brain-read queries the brain and returns decision records. Your job: write with clarity, using metadata and prose that brain-read can find and present.

- **Implication:** Structure every decision with consistent YAML frontmatter so brain-read can filter by `status:`, `type:`, `tags:`, `owner:`
- **Example:** brain-read query "show me all active infrastructure decisions" only works if you tagged your decisions with `type: infra` or similar
- **Best practice:** Include one-line description in every decision title; brain-read surfaces this for quick scanning

### brain-write → brain-recall
**What you write, others recall.** brain-recall uses hybrid search (grep + semantic) to find relevant past decisions.

- **Implication:** Write prose using concrete language, not jargon. Use consistent terminology across decisions
- **Example:** If you call it "gRPC" in D087 but "microservice RPC" in D089, brain-recall won't find the semantic link. Use consistent naming
- **Best practice:** In prose, explain technical terms on first use. Use `tags:` to cluster related decisions. Link related decisions using `related_decisions:` field

### brain-write → brain-why
**What you write, why walks it backward.** brain-why invokes `/why <commit-hash>` to return the full provenance tree (who, when, why, what decision).

- **Implication:** Write commit messages that answer "why did we do this?" Not just "what changed"
- **Example:** Commit message "spec: lock shared dev spec" is not enough. Use: "spec: lock shared dev spec for PRD-2025-11-streaming — converged on gRPC (resolves D087)"
- **Best practice:** Every commit message should include the decision ID or problem it solves. Link to parent decisions in frontmatter (`parent_decision:` field)

### brain-write → brain-link
**What you write, link connects semantically.** brain-link creates edges between decisions based on shared tags, parent/child, and cross-references.

- **Implication:** Use consistent `tags:` and explicit `related_decisions:` so brain-link has good signals
- **Example:** If you tag D087 (gRPC) with `#api` and `#performance`, brain-link can find other decisions tagged the same way and suggest connections
- **Best practice:** Every decision should have 3-5 tags from the standard set. Always fill in `related_decisions:` field (even if it's just `related: []`). Update links whenever you reference a related decision

### brain-write → brain-forget
**What you write, forget archivizes.** brain-forget scans for decisions with `status: cold` or `deprecation_planned:` in the past and moves them to archive.

- **Implication:** Set `status:` and `deprecation_planned:` on every decision; brain-forget can't act without these signals
- **Example:** If D040 (old API versioning strategy) was superseded by D087, set `status: cold` and `deprecation_planned: 2026-12-31`. brain-forget will surface D040 for archival when the date passes
- **Best practice:** Proactively mark decisions as `warm` or `cold` when you know they're being phased out. Include `superseded_by:` field. Make brain-forget's job easy by giving it clear signals

---

## Edge Cases

### Edge Case 1: File already exists (D001_feature.md exists)

**Symptom:** Decision file exists at target path; write would overwrite it.

**Do NOT:** Overwrite existing decision. Do NOT edit a locked decision directly.

**Mitigation:**
1. Check if decision is locked: `grep "status:" <existing-file.md> | grep "active\|warm"`
2. If locked, create NEW decision that supersedes it (set `superseded_by:` in new decision, `superseded_by:` in old)
3. If file is draft (status: draft), OK to update — but still prefer new decision for clear lineage
4. Use semantic ID pattern: D001 (original), D001_v2 (revision), or D002 (next decision)

**Escalation:** NEEDS_CONTEXT — Verify whether to overwrite (draft status) or supersede (active/locked status). Consult decision author if unsure.

---

### Edge Case 2: Brain not in git (lost version control)

**Symptom:** `git -C ~/forge/brain status` returns "not a git repository" or fails.

**Do NOT:** Write decision anyway (loses audit trail). Do NOT bypass git.

**Mitigation:**
1. Check git state: `cd ~/forge/brain && git status`
2. Verify remote: `git remote -v`
3. If .git missing, relink: `git clone <remote-url> ~/forge/brain`
4. If uncommitted changes exist: `git add . && git commit -m "WIP"`

**Escalation:** BLOCKED — Cannot write decision without git backing. Brain must be in git repository. Contact platform team to restore/reinitialize brain repo.

---

### Edge Case 3: Invalid frontmatter (missing required fields)

**Symptom:** Decision file lacks required YAML fields (decision_id, title, status, date, owner).

**Do NOT:** Write incomplete frontmatter. Do NOT assume defaults.

**Mitigation:**
1. Use template with all required fields (see "Metadata Frontmatter Template" above)
2. Validate frontmatter before commit: `head -30 <file> | grep -E "^decision_id:|^title:|^status:|^date:|^owner:"`
3. Use linter if available: `yamllint <file>` (checks YAML syntax)

**Escalation:** NEEDS_CONTEXT — Frontmatter incomplete. Verify all required fields before committing. Use provided template to ensure consistency.

---

### Edge Case 4: Concurrent write conflict (two people writing same decision)

**Symptom:** Git merge conflict on same decision file (both people edited D042.md).

**Do NOT:** Merge conflicted versions. Do NOT lose either person's changes.

**Mitigation:**
1. Resolve conflict manually: `git status` shows which files have conflicts
2. Review both versions: `git show :<version-number> <file>` to see both sides
3. Merge intelligently: Keep both versions' metadata, append one to "supersedes" or "related" field
4. If both added alternatives/evidence: Consolidate under single decision (not duplicate)
5. After merge: `git add <file> && git commit -m "resolve: merge concurrent edits to D042"`

**Escalation:** NEEDS_COORDINATION — Concurrent writes to same decision. Coordinate with other author to understand intent. Decide: merge into single decision or split into two related decisions (parent/child).

---

### Edge Case 5: Decision locked too early (stakeholders not consulted)

**Symptom:** Decision marked `status: active` but stakeholders report lack of input or alternative not considered.

**Do NOT:** Lock decision with hidden dissent. Do NOT ignore stakeholder objections.

**Mitigation:**
1. Check stakeholders field: `grep "stakeholders:" <file>`
2. If stakeholders missing or incomplete, set `status: draft` and re-circulate
3. Add approval_status field: confirm all stakeholders reviewed
4. Use decision review process: circulate to stakeholders before locking
5. If already locked: downgrade to `status: warm` with note "awaiting stakeholder review"

**Escalation:** NEEDS_COORDINATION — Decision locked without consensus. Downgrade status and re-circulate for review. Document any dissent in decision file (add dissent field with names/concerns).

---

## Decision Tree: Lock vs Draft Strategy

```
About to write a decision, should you lock it immediately?
    ↓
Are all stakeholders present and consulted?
├─ NO → Set `status: draft`; circulate for review before locking
└─ YES → Continue below

Have alternatives been evaluated and documented?
├─ NO → Set `status: draft`; return to evaluate alternatives
└─ YES → Continue below

Is this decision blocking downstream work?
├─ YES → Lock immediately (`status: active`); note deadline
└─ NO → Continue below

Is this a major architectural or API decision?
├─ YES → Lock only after council review (`status: active`); include council approval in frontmatter
└─ NO → Continue below

Is this a time-sensitive decision (hot fix, incident response)?
├─ YES → Lock immediately (`status: active`); document urgency and any shortcuts taken
└─ NO → Continue below

Is this a standard operational decision (deployment strategy, naming convention)?
├─ YES → Lock after team alignment (`status: active`)
└─ NO → Continue below

Result:
- If any answer suggests incompleteness: `status: draft` + circulate for input
- If all checks pass and stakeholders aligned: `status: active` + commit with context
- Milestone-based: lock when blocker is cleared, not when written
- Default: When in doubt, start as `status: draft` and upgrade after review
```

---

## Cross-References

- `brain-read`: Low-level file reader; brain-write calls it before overwriting to detect conflicts.
- `brain-recall`: Queries the brain before making a new decision — pair with brain-write to record what was found.
- `brain-why`: Traces provenance of an existing decision; use after brain-write to verify the record is complete.
- `brain-forget`: Archives a decision when it is superseded; complement to brain-write for lifecycle management.
- `brain-link`: Creates semantic edges between decisions written via brain-write.
- `forge-brain-persist`: Handles commit and push of brain files after brain-write creates them.
- `docs/conductor-log-format.md`: Format for conductor.log entries; brain-write records log markers as decision evidence.

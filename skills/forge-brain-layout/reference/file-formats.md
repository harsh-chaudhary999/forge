# File Format Specifications

> Moved verbatim from `SKILL.md` for progressive disclosure (forge-skill-anatomy v2.1.0). This is the full catalog of brain file format specs; the operational contract lives in `../SKILL.md`.

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

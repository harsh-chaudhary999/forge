---
name: contract-schema-db
description: "WHEN: Council has identified database schema conflicts across services and needs a locked contract. Defines migrations, backward compatibility, indexing, constraints, and safe change procedures."
type: rigid
effort: high
requires: [brain-read]
version: 1.0.1
preamble-tier: 3
triggers:
  - "design database schema"
  - "define DB schema"
  - "database contract"
allowed-tools:
  - Write
  - AskUserQuestion
---

# Database Schema Contract Negotiation

## Human input

Resolve every human-decision fork (NEEDS_CONTEXT / NEEDS_COORDINATION / NEEDS_INFRA_CHANGE / BLOCKED) through **`AskUserQuestion`** (in `allowed-tools`) — never a prose-only "escalate to user". Canonical convention: [`skills/_shared/human-input.md`](../_shared/human-input.md).

## Step 0 — Recall prior schema decisions (before negotiating)

This skill declares `requires: [brain-read]` — exercise it. Before proposing schema changes: `brain_recall`/grep the affected tables + prior `contract-schema-db` decisions and the product topology, so the migration supersedes rather than re-litigates prior locks. Record the resulting `contract_id` (brain decision id / commit SHA) in the Post-Implementation Checklist.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "It's just adding a column, no contract needed" | ALTER TABLE on a large table can lock writes for minutes. Even "simple" changes need migration safety review. |
| "We'll add the index later when it's slow" | Missing indexes in production cause cascading failures under load. Index decisions are contract decisions — make them at council. |
| "Both services can read/write the same table" | Shared table ownership without contracts creates schema conflicts, migration races, and implicit coupling. One owner per table. |
| "Rollback is just DROP COLUMN" | DROP COLUMN is destructive and irreversible. Safe rollback requires a plan before the migration runs, not after it fails. |
| "The ORM handles schema compatibility" | ORMs hide but don't solve backward compatibility. A NOT NULL column added without a default breaks every existing row. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
NO SCHEMA MIGRATION SHIPS WITHOUT A VERIFIED BACKWARD-COMPATIBLE ROLLBACK PLAN. A MIGRATION WITH NO ROLLBACK IS A MIGRATION THAT WILL CAUSE AN INCIDENT.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Migration adds a NOT NULL column without a DEFAULT or backfill** — This will fail on any row that existed before the migration. STOP. Add a DEFAULT or perform a 3-step migration (add nullable → backfill → add NOT NULL constraint).
- **Migration plan has no rollback procedure** — Irreversible migrations with no rollback = production incident with no recovery. STOP. Write rollback steps before any migration runs.
- **Two services are documented as owning the same table** — Shared table ownership causes schema conflicts and migration races. STOP. Establish single ownership per table before locking the contract.
- **Index is not specified for a column used in WHERE clauses** — Missing indexes cause full table scans under load. STOP. Define indexes for all query patterns at contract time.
- **Breaking schema change is introduced without a deprecation window** — Clients using the old schema will break on deploy. STOP. Plan a backward-compatible migration (add new columns, deprecate old ones, remove after transition).
- **Migration locks the table without a lock timeout** — Long locks block all reads/writes. STOP. Set explicit lock wait timeouts and use online DDL strategies for large tables.

This skill teaches teams to safely negotiate and implement MySQL database schema changes using contracts. It covers safe migration patterns, backward compatibility strategies, indexing best practices, constraint handling, and comprehensive rollback procedures.

---

## Minimum depth for each NEW or materially changed table

**Purpose:** Match the rigor of a full implementation plan: every table row in the locked contract should answer “what ships in MVP.”

For **each** new or materially changed table, include in the locked DB contract / `shared-dev-spec`:

| Column group | Requirement |
|--------------|-------------|
| **Core columns** | Names, types, nullability, PK/FK |
| **Audit / lineage** | `created_at`, `updated_at`, actor/user ref — **or** explicit **`DEFERRED`** row with risk + owner |
| **Indexes** | For every **WHERE** / **JOIN** in new queries — or **`DEFERRED`** with reason |
| **Backfill / rollout** | Nullable-first + backfill job, or dual-write window — reference migration task class |
| **Vendor / third-party / verifier logs** (when PRD implies) | Store hash vs raw secret, retention, encryption boundary — **or** **`DEFERRED out of MVP`** row |

Silent omission = **not locked**. Use **`DEFERRED`** + risk when intentionally slimming MVP.

---

## Migration, Indexing & Constraint Depth

The numbered sections below carry the operational spine; full DDL samples, worked
templates, and rule catalogs live in `reference/`:

1. **Safe Migrations** (ADD/DROP/RENAME COLUMN, ALTER CONSTRAINTS), **Backward
   Compatibility** (dual-write, dual-read, migration timeline), and **Rollback
   Procedures** (script templates + verification queries) — full DDL and timelines
   in [reference/migrations.md](reference/migrations.md).
2. **Indexing Strategy** (primary-key design, foreign-key indexes, query-pattern
   indexes, bloat monitoring) — full DDL and rules in
   [reference/indexing.md](reference/indexing.md).
3. **Constraints & Triggers** (NOT NULL, UNIQUE, CHECK, FOREIGN KEY) — full DDL,
   verification queries, and rollback per constraint in
   [reference/constraints.md](reference/constraints.md).

Each migration still obeys the Iron Law: additive-before-destructive, every
destructive step paired with a verified rollback, every WHERE/JOIN column indexed.

## Worked Example, Key Principles & Common Mistakes

Full 2FA-feature schema contract (current schema → safe changes → rollback plan →
timeline), the 7 Key Principles, and the Common Mistakes to Avoid list are in
[reference/examples.md](reference/examples.md).

---

## Edge Cases, Fallback Paths & Decision Trees

Five fully worked edge cases — (1) non-reversible one-way migration, (2) existing
data violates new constraints, (3) multiple services touch the same table, (4)
large-table (>100M rows) migration, (5) hidden-constraint breakage of dependent
services — each with diagnosis, response, and escalation, plus **Decision Tree 1
(Schema Migration Strategy: Expand-Only / Expand-Contract / Coordinated Cutover)**
and **Decision Tree 2 (Constraint Enforcement Layer: DB / App / Dual)** with their
decision flows and contract-commitment templates, are in
[reference/edge-cases.md](reference/edge-cases.md).

Each escalation fork (BLOCKED / NEEDS_COORDINATION / escalate-to-user) is resolved
through **`AskUserQuestion`** per [`skills/_shared/human-input.md`](../_shared/human-input.md) — never a prose-only escalation.

---

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] Migration files match the agreed schema: every column name, type, and nullability in the migration matches the contract row-for-row
- [ ] Column types and nullability are explicitly locked in `shared-dev-spec.md` — no column is listed as `TBD` or left with a vague type like `string`
- [ ] `contract_schema_status: negotiated` is set in the `shared-dev-spec.md` frontmatter — not `draft` or `open`
- [ ] No `TBD` column names or constraint definitions remain in the contract — every table, column, index, and foreign key is named and typed
- [ ] Every destructive migration step (DROP COLUMN, rename, type change) has a verified down migration (rollback script) written and tested alongside the up migration

## Checklist

Before locking a database schema contract:

- [ ] All new columns have explicit NOT NULL/NULL declared with rationale
- [ ] All foreign key constraints reference the correct table and column
- [ ] All indexes specified with type and rationale (covering, partial, composite)
- [ ] Migration plan included for every schema change (additive before destructive)
- [ ] Rollback procedure defined for every destructive migration step
- [ ] Constraint level chosen (DB-enforced vs app-enforced vs dual-layer) with rationale
- [ ] No schema change marked TBD or "to be decided later"

## Cross-References

- `council-multi-repo-negotiate`: Drives contract negotiation that produces the DB schema contract this skill governs.
- `spec-freeze`: Locks all 5 contracts (including DB schema) after council — immutable after `[P2-SPEC-FROZEN]`.
- `forge-council-gate`: Gate that enforces all 5 contracts are `negotiated` before freezing.
- `contract-api-rest`: REST API contract that depends on DB schema; foreign keys and indexes must align.
- `contract-cache`: Cache contract for denormalization and cache-warming; coordinates with DB schema.
- `eval-driver-db-mysql`: Executes `mysql` surface steps in `semantic-automation.csv` — validates schema compliance at eval time.
- `spec-reviewer`: Verifies implementation matches the locked DB schema contract (migration safety, index rationale).
- `tech-plan-write-per-project`: References the DB schema contract when generating per-repo implementation plans.

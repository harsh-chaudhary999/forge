---
name: contract-search
description: "WHEN: Council has identified search contract conflicts across services and needs a locked contract. Defines index mapping, analyzer, consistency, update semantics, refresh policy, and reindex procedures."
type: rigid
effort: high
requires: [brain-read]
version: 1.0.1
preamble-tier: 3
triggers:
  - "design search contract"
  - "define search index"
  - "search schema"
allowed-tools:
  - Write
  - AskUserQuestion
---

# Contract-Search Skill

## Human input

Resolve every human-decision fork (NEEDS_CONTEXT / NEEDS_COORDINATION / NEEDS_INFRA_CHANGE / BLOCKED) through **`AskUserQuestion`** (in `allowed-tools`) — never a prose-only "reply if…". Canonical convention: [`skills/_shared/human-input.md`](../_shared/human-input.md).

## Step 0 — Recall prior search contracts (before negotiating)

This skill declares `requires: [brain-read]` — exercise it. Before proposing the search contract: `brain_recall`/grep the product topology and any existing `search-contract.md` + prior index/reindex/mapping decisions for the entity, so this contract supersedes rather than duplicates prior locks. Record the resulting `contract_id` (brain decision id / commit SHA) in the LOCK checklist.

Teaches teams to negotiate Elasticsearch contracts with explicit specifications for index design, analyzer strategy, consistency model, and update semantics. Bridges requirements to operational search contracts.

## Anti-Pattern Preamble: Search Contract Failures

| Rationalization | The Truth |
|---|---|
| "We'll use dynamic mapping, ES handles types automatically" | Dynamic mapping creates type conflicts the moment two documents disagree on a field type. First document sets the type forever. Explicit mapping in the contract prevents silent data loss and query failures. |
| "Search is eventually consistent, the UI will just retry" | Users don't retry. They see stale results and report bugs. The contract must specify refresh policy (immediate for critical writes, interval for bulk) and the UI must show freshness indicators. |
| "Reindexing is just a background job" | Reindexing without a contract means index name collisions, mapping conflicts, and query routing failures during the migration. The contract must specify: alias strategy, zero-downtime reindex procedure, and rollback plan. |
| "We don't need analyzers, default is fine" | Default analyzer splits on whitespace and lowercases. "New York" becomes ["new", "york"]. "iPhone" becomes ["iphone"]. If your search contract doesn't specify analyzer behavior, users will get wrong results. |
| "Index versioning is overkill" | Without index versioning, schema changes require destructive reindexing. With versioning (`products_v1`, `products_v2` behind alias), you can reindex in the background and swap atomically. Contract must include version strategy. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
NO INDEX IS CREATED BEFORE ITS MAPPING, ANALYZER, AND ALIAS STRATEGY ARE LOCKED IN THE CONTRACT. DYNAMIC MAPPING IS NEVER ACCEPTABLE.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Contract has `dynamic: true` or no explicit mappings** — Dynamic mapping will silently corrupt data the moment field types disagree. STOP. Define explicit mappings for every field before the contract is accepted.
- **Refresh policy is not specified in the contract** — Search consistency expectations are undefined. Different surfaces will make different assumptions. STOP. Agree on refresh policy (immediate vs. interval) before locking.
- **Index alias strategy is absent from the contract** — Reindexing will require downtime or cause routing failures. STOP. Define index versioning and alias strategy before any index is created.
- **Analyzer strategy is listed as "TBD" or "default"** — Default analyzers produce wrong search results for many languages, proper nouns, and compound words. STOP. Define analyzers explicitly before locking.
- **No reindex rollback plan is documented** — Reindex failures without a rollback plan mean data unavailability. STOP. Define the rollback procedure (swap alias back, restore from snapshot) before the contract is accepted.
- **Multiple teams interpret "search freshness" differently** — One team expects read-after-write, another expects eventual consistency. STOP. Align on a single freshness SLO and write it into the contract.

---

## When to Use

Use this skill when:
- Designing a new Elasticsearch index for a feature or domain entity
- Negotiating search behavior between client teams (read-after-write, eventual consistency)
- Establishing index mapping and analyzer strategy before implementation
- Planning reindex procedures and data migration strategies
- Defining update patterns (event-sourced, dual-write, bulk indexing)

## Core Sections

A locked search contract specifies five sections — index mapping (field types, mapping template, dynamic policy), analyzer strategy (standard/custom analyzers, synonyms), consistency model (read-after-write vs. eventual, refresh intervals), update semantics (event-sourced / dual-write / bulk), and reindex & backfill (alias swap, `_reindex`/ILM/data streams, rollback, Kafka replay). Full depth — templates, JSON samples, option tables — in [reference/index-design.md](reference/index-design.md).

A complete worked search contract (Users) is in [reference/patterns.md](reference/patterns.md).

---

## Contract Checklist

Before finalizing a search contract, verify:

- [ ] **Index Mapping**: All required fields defined with correct types; dynamic mapping policy set
- [ ] **Analyzer Strategy**: Each text field assigned analyzer; synonyms defined if applicable
- [ ] **Consistency Model**: Read-after-write guarantee specified; refresh interval chosen
- [ ] **Update Pattern**: Event source identified; consumer/indexer approach described; latency SLA defined
- [ ] **Reindex Plan**: Procedure documented; backfill time estimated; rollback strategy tested
- [ ] **Monitoring**: Reindex lag, document count, query latency metrics identified
- [ ] **Validation**: Count reconciliation, sample queries, timestamp distribution checks

---

## Edge Cases & Escalation Keywords

Six search-contract failure modes — each with symptom, anti-pattern, mitigation, and escalation keyword (BLOCKED / NEEDS_CONTEXT / NEEDS_INFRA_CHANGE / NEEDS_COORDINATION) — drive the human-decision forks. Resolve every fork via `AskUserQuestion`.

1. **Index field type mismatch breaks queries** → BLOCKED if dynamic mapping enabled; lock `dynamic: false`.
2. **Relevance scoring disagreement** → NEEDS_CONTEXT: lock ranking priority (BM25 / recency / popularity).
3. **Query DSL variant incompatibility** → NEEDS_INFRA_CHANGE if backend changes (ES→Solr/Algolia).
4. **Full-text analyzer conflict (stemming/stopwords/language)** → NEEDS_COORDINATION on a single analyzer standard.
5. **Index refresh lag causes stale read-after-write** → NEEDS_CONTEXT on read-after-write requirement.
6. **Index size grows unbounded** → NEEDS_INFRA_CHANGE: lock a retention policy.

Full symptoms, mitigations, and example queries/mappings in [reference/edge-cases.md](reference/edge-cases.md).

## Decision Tree: Search Index Strategy

Pick the ownership model by counting writers: **one service** → Dedicated Index (Search Service owns); **one writer, many readers** → Shared Read Index (define update-lag SLA, coordinate reindex); **many writers** → Shared Mutable Index (avoid; if unavoidable, route all writes through a central indexing API with a single analyzer). Full decision flow plus the per-model "Search Index Ownership" commitment templates to paste into the contract in [reference/patterns.md](reference/patterns.md).

---

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] Index mapping is explicitly agreed (every field name, type, and analyzer) and written into `shared-dev-spec.md` — `dynamic: true` is never used; the mapping is formal, not prose
- [ ] Query interface is documented: which fields are searchable, which are filterable, which are sortable — no implicit "it should work" assumptions
- [ ] `contract_search_status: negotiated` is set in the `shared-dev-spec.md` frontmatter — not `draft` or `open`
- [ ] No unresolved ranking or relevance questions remain: scoring model (BM25, boosting, decay), freshness priority, and synonym rules are locked and agreed by all consumer teams
- [ ] Index alias strategy and zero-downtime reindex procedure are documented, including rollback steps and the agreed refresh interval

## Related Skills

- **brain-read**: Retrieve product topology and contracts from the brain
- **reasoning-as-infra**: Full discussion of Elasticsearch scaling, sharding, cluster topology
- **code-quality-reviewer** (agent, not a skill): dispatched after implementation to review indexing code (consumer, dual-write, bulk API)

## Checklist

Before claiming search contract locked:

- [ ] Explicit field mappings defined for every indexed field (no `dynamic: true`)
- [ ] Analyzer strategy specified for all text fields
- [ ] Refresh policy agreed upon and documented for each write surface
- [ ] Index versioning strategy defined (e.g., `index_v1` behind alias)
- [ ] Zero-downtime reindex procedure documented with rollback steps
- [ ] Contract locked and written to brain


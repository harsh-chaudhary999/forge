---
name: contract-search
description: Negotiate search contracts (Elasticsearch). Defines index mapping, analyzer, consistency, update semantics, refresh policy, and reindex procedures.
type: rigid
requires: [brain-read]
---

# Contract-Search Skill

Teaches teams to negotiate Elasticsearch contracts with explicit specifications for index design, analyzer strategy, consistency model, and update semantics. Bridges requirements to operational search contracts.

## Anti-Pattern Preamble: Search Contract Failures

| Rationalization | The Truth |
|---|---|
| "We'll use dynamic mapping, ES handles types automatically" | Dynamic mapping creates type conflicts the moment two documents disagree on a field type. First document sets the type forever. Explicit mapping in the contract prevents silent data loss and query failures. |
| "Search is eventually consistent, the UI will just retry" | Users don't retry. They see stale results and report bugs. The contract must specify refresh policy (immediate for critical writes, interval for bulk) and the UI must show freshness indicators. |
| "Reindexing is just a background job" | Reindexing without a contract means index name collisions, mapping conflicts, and query routing failures during the migration. The contract must specify: alias strategy, zero-downtime reindex procedure, and rollback plan. |
| "We don't need analyzers, default is fine" | Default analyzer splits on whitespace and lowercases. "New York" becomes ["new", "york"]. "iPhone" becomes ["iphone"]. If your search contract doesn't specify analyzer behavior, users will get wrong results. |
| "Index versioning is overkill" | Without index versioning, schema changes require destructive reindexing. With versioning (`products_v1`, `products_v2` behind alias), you can reindex in the background and swap atomically. Contract must include version strategy. |

---

## When to Use

Use this skill when:
- Designing a new Elasticsearch index for a feature or domain entity
- Negotiating search behavior between client teams (read-after-write, eventual consistency)
- Establishing index mapping and analyzer strategy before implementation
- Planning reindex procedures and data migration strategies
- Defining update patterns (event-sourced, dual-write, bulk indexing)

## Core Sections

### 1. Index Mapping

Define the structure of your Elasticsearch index with explicit field types and analysis rules.

**Field Types:**
- `keyword`: Exact match, aggregations, sorting (low cardinality identifiers, status, tags)
- `text`: Full-text search, analyzer applied (titles, descriptions, bios, content)
- `number`: Numeric range queries, sorting (counts, scores, IDs for range)
- `date`: Temporal queries, sorting (timestamps, scheduled events)
- `boolean`: Binary flags (feature flags, enabled states)
- `geo_point`: Geospatial queries (latitude/longitude)
- `nested`: Relationships with sub-objects (comments within articles, line items in orders)
- `object`: Denormalized relationships (shallow nesting)

**Mapping Template:**
```json
{
  "index": "<index_name>",
  "mappings": {
    "properties": {
      "id": {"type": "keyword"},
      "name": {"type": "text", "analyzer": "standard"},
      "email": {"type": "keyword"},
      "status": {"type": "keyword"},
      "score": {"type": "float"},
      "created_at": {"type": "date"},
      "metadata": {
        "type": "object",
        "properties": {
          "version": {"type": "keyword"},
          "tier": {"type": "keyword"}
        }
      }
    }
  }
}
```

**Dynamic Mapping Policy:**
- `true`: Accept unmapped fields (risky, can cause mapping explosion)
- `false`: Reject unmapped fields (safe, requires schema discipline)
- `strict`: Throw error on unmapped fields (strict mode, debugging)

### 2. Analyzer Strategy

Choose tokenization, stemming, and synonym handling to match search semantics.

**Standard Analyzers:**
- `standard`: Tokenizer (whitespace/punctuation), lowercase, stop-word filter (common for general text)
- `english`: standard tokenizer + porter_stem (English stemming) + stop-word filter (product descriptions, content)
- `whitespace`: Split on whitespace only, lowercase (when stemming is unwanted)
- `keyword`: No tokenization (for exact match fields, if text type is misused)

**Custom Analyzer Pattern:**
```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "bio_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop", "porter_stem", "my_synonym_filter"]
        }
      },
      "filter": {
        "my_synonym_filter": {
          "type": "synonym",
          "synonyms": ["fast,quick,rapid", "slow,sluggish,lagging"]
        }
      }
    }
  }
}
```

**Analyzer Decisions:**
- Use `english` for human-readable text (titles, bios, product names)
- Use `standard` for mixed-language or technical content
- Use `whitespace` for code, IDs, exact-match text
- Use custom analyzers for domain terminology (medical terms, product jargon)
- Always include synonyms if search behavior depends on term equivalence

### 3. Consistency Model

Define read-after-write guarantees and acceptable staleness.

**Strongly Consistent (Immediate reads):**
- Every write immediately visible to reads
- Requires `refresh_interval: "0"` or explicit refresh call
- Use when: user profile updates, permission changes, critical account data
- Cost: higher write latency, lower indexing throughput

**Eventual Consistency (Stale reads acceptable):**
- Reads lag writes by refresh interval (typically 1–30 seconds)
- Requires `refresh_interval: "30s"` or on-demand refresh
- Use when: search, analytics, non-critical reads, feed ranking
- Cost: lower write latency, higher indexing throughput

**Refresh Interval Options:**
- `1s`: Near real-time (5–10ms latency increase per write)
- `5s`: Balanced (10–30ms per write)
- `30s`: Eventual (seconds of staleness, high throughput)
- `-1`: Manual refresh only (bulk indexing, offline updates)

**Read-After-Write Guarantee:**
```json
{
  "settings": {
    "index.refresh_interval": "30s",
    "index.max_result_window": 10000
  }
}
```

### 4. Update Semantics

Choose how your application feeds updates into Elasticsearch.

**Event-Sourced Pattern:**
- Application publishes domain events (user.created, user.email_updated)
- Event stream (Kafka, Pub/Sub) acts as source of truth
- Elasticsearch consumer subscribes, indexes changes
- Pros: idempotent, replayable, decoupled, audit trail
- Cons: eventual consistency, consumer lag visibility required
- Latency: 100ms–30s depending on refresh interval

```
User Service → Kafka topic (user.events) → ES Consumer → Elasticsearch Index
```

**Dual-Write Pattern:**
- Application writes to primary database AND Elasticsearch in same transaction/RPC
- Pros: immediate consistency, simple logic
- Cons: distributed transaction complexity, harder rollback, dual failures
- Use when: strong consistency required AND low update volume

**Bulk Indexing Pattern:**
- Batch updates collected (1000s per hour, nightly reindex)
- Periodic bulk index operation (scroll/scan, bulk API)
- Pros: highest throughput, lowest latency variance
- Cons: high staleness (hours), not for real-time features

### 5. Reindex & Backfill

Plan major index changes and recovery from corruption or schema evolution.

**Reindex via Alias Swapping:**

Procedure:
1. Create new index with updated mapping: `index_v2`
2. Populate from source (Kafka replay, scan + bulk, or app writes dual-write)
3. Validate data (count, sample queries)
4. Create alias pointing to current index
5. Update alias to point to `index_v2` (atomic operation)
6. Delete old index after validation

```json
POST _aliases
{
  "actions": [
    {"remove": {"index": "users_v1", "alias": "users"}},
    {"add": {"index": "users_v2", "alias": "users"}}
  ]
}
```

**Backfill Strategy:**

- **Full backfill**: Replay entire event history or scan source table
  - Use when: schema change is incompatible (new analyzer, new fields)
  - Time: hours for large datasets
  - Validation: count matches source, sample queries match expectations
- **Incremental backfill**: Only index events after cutover
  - Use when: adding new index for new features (no old data needed)
  - Time: minutes

**Rollback via Alias:**
```json
POST _aliases
{
  "actions": [
    {"remove": {"index": "users_v2", "alias": "users"}},
    {"add": {"index": "users_v1", "alias": "users"}}
  ]
}
```

**Event Replay (Kafka 7-day retention):**
- Reset consumer offset to 7 days ago
- Consume events, re-index into new index
- Replay must be idempotent (document ID based)
- Validate count, sample queries, timestamp distribution

---

## Example: Users Search Contract

```markdown
# Search Contract — Users

## Index Mapping

**Index:** `users` (aliased)

```json
{
  "index": "users",
  "mappings": {
    "properties": {
      "id": {"type": "keyword"},
      "email": {"type": "keyword"},
      "name": {"type": "text", "analyzer": "standard"},
      "bio": {"type": "text", "analyzer": "english"},
      "company": {"type": "keyword"},
      "tier": {"type": "keyword"},
      "2fa_enabled": {"type": "boolean"},
      "verification_status": {"type": "keyword"},
      "created_at": {"type": "date"},
      "last_login_at": {"type": "date"},
      "score": {"type": "float"}
    }
  }
}
```

## Analyzer Strategy

- **name**: standard analyzer (whitespace + lowercase + stop words)
- **bio**: english analyzer (whitespace + lowercase + porter_stem + stop words + synonyms: "engineer↔developer", "fast↔quick")
- **email, company, tier**: keyword (no analysis)

## Consistency Model

- **Model**: Eventual consistency (stale reads acceptable)
- **Refresh interval**: 30 seconds
- **Read-after-write**: For user-visible updates, client waits 1 second before searching (UI optimistic update)
- **Acceptable staleness**: 30 seconds (user profile updates visible within 30s in search results)

## Update Pattern

- **Source of truth**: User Service (PostgreSQL)
- **Event stream**: Kafka topic `user.events` (7-day retention)
- **Events**: user.created, user.updated, user.deleted
- **Consumer**: ES indexer service (subscribed, idempotent by user ID)
- **Latency**: 100ms–5s (P99 within 30s refresh)
- **Failure recovery**: Replay from Kafka, rebuild index if corrupted

## Reindex & Backfill

- **Procedure**: 
  1. Create `users_v2` with new mapping
  2. Replay Kafka events (user.* starting from 7 days ago)
  3. Validate count matches staging PostgreSQL
  4. Swap alias: `users` → `users_v2`
  5. Delete `users_v1` after 24h monitoring
  
- **Rollback**: Swap alias back to `users_v1` (< 1 second)
- **Backfill time**: ~2 hours for 10M users (Kafka replay + indexing)
- **Monitoring**: Reindex lag, document count drift, query latency

---
Ready for: Shared-dev-spec lock
```

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

## Related Skills

- **brain-read**: Retrieve product topology and contracts from the brain
- **reasoning-as-infra**: Full discussion of Elasticsearch scaling, sharding, cluster topology
- **code-quality-reviewer**: Review indexing code (consumer, dual-write, bulk API)


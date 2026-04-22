---
name: contract-search
description: "WHEN: Council has identified search contract conflicts across services and needs a locked contract. Defines index mapping, analyzer, consistency, update semantics, refresh policy, and reindex procedures."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers: []
allowed-tools:
  - Write
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

## Edge Cases & Escalation Keywords

### Edge Case 1: Index field type mismatch breaks queries

**Symptom:** Contract specifies `score` as `float` in mapping. One indexer publishes score as string "9.5". Another publishes as number 9.5. Elasticsearch accepts both (mapping is flexible). Queries `GET products?min_score=8.0` return inconsistent results: sometimes string "8.5" is excluded, sometimes included (comparison mismatch).

**Do NOT:** Assume dynamic mapping handles type variance.

**Mitigation:**
- Lock `dynamic: false` in mapping: Reject unmapped fields, enforce schema strictly
- Document field types: "score is float (never string). Indexers must convert before publishing."
- Pre-index validation: Consumer validates type before indexing, rejects type mismatches to DLQ
- Example valid mapping:
  ```json
  {
    "properties": {
      "score": {"type": "float"},
      "user_id": {"type": "keyword"}
    },
    "dynamic": false
  }
  ```
- Validation code: "If score is string, convert to float or reject"

**Escalation:** BLOCKED if dynamic mapping enabled. Must use strict `dynamic: false` before contract lock.

---

### Edge Case 2: Relevance scoring disagreement causes user frustration

**Symptom:** Search contract specifies BM25 relevance scoring. Product team expects "newest first" by default. Search team implements BM25 (term frequency). Users search "iPhone", get 2015 articles ranking higher than 2026 articles (because 2015 article mentions "iPhone" 100x, new article 5x). Team A spent 2 weeks tuning BM25, Team B expects chronological. Conflict.

**Do NOT:** Leave relevance expectations undefined.

**Mitigation:**
- Lock relevance model in contract: "Scoring uses BM25 (term frequency + document length norm)"
- Document scoring factors: "Score = BM25(term_frequency) + boost(recency) + boost(popularity)"
- Define boost values: "Recent docs (< 30 days) get +2.0 boost. Popular docs (10k views) get +1.5 boost."
- Example query:
  ```json
  {
    "query": {
      "bool": {
        "must": [{"match": {"title": "iPhone"}}],
        "should": [
          {"range": {"created_at": {"gte": "now-30d", "boost": 2}}},
          {"term": {"popular": true, "boost": 1.5}}
        ]
      }
    }
  }
  ```
- Testing: "Search 'iPhone', verify recent articles in top 5"

**Escalation:** NEEDS_CONTEXT — What's the ranking priority? Relevance (BM25), recency, popularity, or custom? Lock before implementation.

---

### Edge Case 3: Query DSL variant incompatibility

**Symptom:** Contract specifies Elasticsearch. Later, team wants to integrate Solr search (different DSL syntax). Query `query_string:"iPhone AND -broken"` valid in Elasticsearch, invalid in Solr syntax. Clients wrote custom query logic for ES DSL, cannot reuse.

**Do NOT:** Assume DSL is standardized.

**Mitigation:**
- Commit to search backend in contract: "Elasticsearch 7.x only. DSL: Lucene query syntax."
- Document query format: "Queries use Elasticsearch query_string syntax: `(title:iPhone OR description:iPhone) AND -broken`"
- Example query layer: "API accepts simple filters (name, status, date_range). API translates to ES DSL internally. Clients never write raw DSL."
- If backend changes: New contract required, API layer absorbs DSL differences

**Escalation:** NEEDS_INFRA_CHANGE — If backend will change (ES→Solr, ES→Algolia), must renegotiate contract. Clients must not write backend-specific DSL.

---

### Edge Case 4: Full-text analyzer conflict (stemming, stopwords, language)

**Symptom:** Search contract specifies `english` analyzer (porter stemmer). Business user searches "engineers" expecting to find "engineer" docs (stemming). But stemmer + stopwords combo also removes "ing" suffix from some words. Inconsistent results. Another team added custom stemmer rules that differ from porter. Results diverge.

**Do NOT:** Assume analyzer behavior is universal.

**Mitigation:**
- Lock analyzer in contract: "All text fields use 'english' analyzer: standard tokenizer + lowercase + porter_stem + english stop-words"
- Document what analyzer does:
  ```
  "engineers" → ["engin"] (porter stem to root form)
  "fast running" → ["fast", "run"] (stop-words removed, stemmed)
  "New York" → ["new", "york"] (lowercased, whitespace split)
  ```
- Define custom analyzer if needed:
  ```json
  {
    "analyzer": {
      "product_name": {
        "type": "custom",
        "tokenizer": "standard",
        "filter": ["lowercase", "my_synonyms"]
      }
    }
  }
  ```
- Lock synonyms: "engineers ↔ engineer" (prevent stemmer incompleteness)
- Testing: "Search 'engineers', verify 'engineer' docs in results"

**Escalation:** NEEDS_COORDINATION — If multiple teams add analyzers/stemming rules, must agree on single standard before lock.

---

### Edge Case 5: Index refresh lag causes stale read-after-write

**Symptom:** Contract specifies `refresh_interval: 30s` (eventual consistency). Product service updates user profile to `verified=true`, writes to Elasticsearch. User immediately searches for "verified: true" profiles. Search doesn't return user for 30 seconds. User refreshes page, still not there. Confused.

**Do NOT:** Assume clients understand eventual consistency.

**Mitigation:**
- Document refresh semantics in contract: "Updates indexed within 30 seconds. Acceptable staleness: 30 seconds."
- Client-side workaround: "After write, wait 1 second before searching (UI optimistic update)" OR "Use short refresh_interval for critical searches"
- Alternative: "For read-after-write guarantee, use explicit refresh: `POST /{index}/_refresh` after write (costs throughput)"
- SLA: "95% of updates indexed within 10 seconds, 99% within 30 seconds"
- Monitoring: "Track indexing lag per shard, alert if > 60 seconds"

**Escalation:** NEEDS_CONTEXT — Does client require read-after-write guarantee? If yes, need shorter refresh_interval (higher cost). If no, 30s acceptable.

---

### Edge Case 6: Index size grows unbounded

**Symptom:** Search contract doesn't specify index retention. Index grows from 10GB → 100GB → 1TB over 2 years. Queries slow down. Disk full. Old documents from 2024 irrelevant to current searches.

**Do NOT:** Assume index size is managed automatically.

**Mitigation:**
- Lock retention policy in contract: "Index retains documents for 90 days only. Older documents deleted."
- Implementation: Use index aliases with time-based rotation: `products_2026-01`, `products_2026-02`, etc.
- Deletion strategy: "Monthly: delete `products_2025-*` indices (>12 months old)"
- Capacity planning: "Assume 1GB per 10M documents. Plan storage for 3x index size (redundancy + reindex space)"
- Monitoring: "Alert if index size > 100GB or growth rate > 1GB/day"

**Escalation:** NEEDS_INFRA_CHANGE — If no retention policy, index will grow unbounded. Must define retention before lock.

---

## Decision Tree: Search Index Strategy

**Q: How many services need to read this search index?**

→ **Single service owns index (Search Service)**
  - Model: **Dedicated Index**
  - Ownership: Search Service owns index, updates, analyzer rules
  - Data source: Event stream (Kafka) or dual-write from app
  - Reindex: Search Service controls process
  - Consistency: Search Service defines acceptable staleness
  - Pros: Simple, dedicated infra, easy to deprecate
  - Cons: Additional data pipeline, eventual consistency

→ **Multiple services read, one writes (Product Service writes, Catalog/Search/Analytics read)**
  - Model: **Shared Read Index**
  - Ownership: Product Service owns source, Search Service owns index
  - Data source: Product Service publishes events (product.created, product.updated)
  - Consistency: Update lag documented (typically 1-30s)
  - Read semantics: All services read same index
  - Coordination: Product Service changes require Search Service reindex
  - Pros: Decoupled, all services have consistent search results
  - Cons: Coordination overhead, eventual consistency

→ **Multiple services read AND write (Distributed full-text search, multi-tenant)**
  - Model: **Shared Mutable Index**
  - Ownership: Unclear (conflict risk) OR explicitly partitioned by tenant
  - Partitioning: Index by service scope (one index per service, no shared writes)
  - Alternative: Central indexing service (all writes go through API)
  - Consistency: Strong consistency required (read-after-write)
  - Cost: Coordination overhead, reindex complexity
  - Risk: Multiple services breaking analyzer assumptions
  - Mitigation: Use central indexing service with single analyzer, all services submit to API

**Decision Flow:**
```
How many services will write to this index?
├─ One service only
│  └─ Dedicated Index
│     Search Service owns
│     Simple reindex, deprecation, updates
│
├─ One writer, multiple readers
│  └─ Shared Read Index
│     Product Service writes, Search Service indexes
│     Define update lag SLA (< 30 seconds)
│     Reindex: Product Service + Search Service coordinate
│
└─ Multiple writers
   └─ Shared Mutable Index (avoid if possible)
      If unavoidable: Use central indexing service
      Single API endpoint, single analyzer, all writes validated
      Cannot allow writers to bypass API
```

**Key Commitment in Contract:**
```markdown
# Search Index Ownership

## Dedicated Index (e.g., Products Search)
- Owner: Search Service (sole indexer)
- Data source: Kafka product.events stream
- Analyzer: English analyzer (standard + porter_stem)
- Refresh interval: 30 seconds
- Retention: 90 days (rolling deletion)
- Read-after-write SLA: < 30 seconds

## Shared Read Index (e.g., Users Search)
- Owner: User Service (data source), Search Service (indexing)
- Readers: User Service, Admin Service, Analytics Service
- Update lag: < 10 seconds (95%), < 30 seconds (99%)
- Reindex procedure: User Service publishes all events, Search Service consumes
- Consistency: Eventual (acceptable stale reads up to refresh_interval)

## Shared Mutable Index (Minimize)
- Access: Only through central Indexing API
- No direct index writes (all services use API)
- Single analyzer, validated at API layer
- Conflict resolution: Last-write-wins per document ID
- Monitoring: Track write conflicts, log to DLQ
```

---

## Related Skills

- **brain-read**: Retrieve product topology and contracts from the brain
- **reasoning-as-infra**: Full discussion of Elasticsearch scaling, sharding, cluster topology
- **code-quality-reviewer**: Review indexing code (consumer, dual-write, bulk API)

## Checklist

Before claiming search contract locked:

- [ ] Explicit field mappings defined for every indexed field (no `dynamic: true`)
- [ ] Analyzer strategy specified for all text fields
- [ ] Refresh policy agreed upon and documented for each write surface
- [ ] Index versioning strategy defined (e.g., `index_v1` behind alias)
- [ ] Zero-downtime reindex procedure documented with rollback steps
- [ ] Contract locked and written to brain


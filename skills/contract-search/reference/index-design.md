# Search Contract Core Sections — Index Design Depth

The five core sections a locked search contract must specify: index mapping, analyzer strategy, consistency model, update semantics, and reindex/backfill procedures.

## 1. Index Mapping

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

## 2. Analyzer Strategy

Choose tokenization, stemming, and synonym handling to match search semantics.

**Standard Analyzers:**
- `standard`: Unicode-aware tokenizer + lowercase, **no stop-word removal by default** (default stopwords are `_none_`; only the `english` analyzer removes stop words by default)
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

## 3. Consistency Model

Define read-after-write guarantees and acceptable staleness.

**Strongly Consistent (Immediate reads):**
- Every write immediately visible to reads
- Requires `refresh=wait_for` (or `refresh=true`) on the write, or an explicit `POST /{index}/_refresh` after writing (ES has no `refresh_interval: "0"`; `-1` only disables auto-refresh)
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

## 4. Update Semantics

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

## 5. Reindex & Backfill

Plan major index changes and recovery from corruption or schema evolution.

**Prefer ES-native mechanisms; specify which one the contract uses:**
- **`_reindex` API** — server-side copy from old → new index (no app round-trips); pair with alias swap for zero downtime.
- **ILM (Index Lifecycle Management)** — hot/warm/cold + delete phases and rollover for time-series indices, instead of ad-hoc periodic index deletion.
- **Data streams** — append-only time-series backing indices with automatic rollover.
- Hand-rolled scan+bulk / Kafka replay / dual-write is the **manual fallback** when `_reindex` can't express the transform.

**Reindex via Alias Swapping (zero-downtime cutover):**

Procedure:
1. Create new index with updated mapping: `index_v2`
2. Populate from source — prefer the `_reindex` API (server-side); else Kafka replay, scan + bulk, or dual-write
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

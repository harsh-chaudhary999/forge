# Search Contract Patterns — Worked Example, Decision Tree, Ownership Templates

A complete worked search contract, the index-strategy decision tree, and the per-model ownership commitment templates to paste into `shared-dev-spec.md`.

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

- **name**: standard analyzer (Unicode tokenizer + lowercase; no stop-word removal by default)
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

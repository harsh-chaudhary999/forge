# Search Contract Edge Cases & Escalation Keywords

Extended failure modes a search contract must pre-empt, each with symptom, anti-pattern, mitigation, and the escalation keyword that routes the human-decision fork.

## Edge Case 1: Index field type mismatch breaks queries

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

## Edge Case 2: Relevance scoring disagreement causes user frustration

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

## Edge Case 3: Query DSL variant incompatibility

**Symptom:** Contract specifies Elasticsearch. Later, team wants to integrate Solr search (different DSL syntax). Query `query_string:"iPhone AND -broken"` valid in Elasticsearch, invalid in Solr syntax. Clients wrote custom query logic for ES DSL, cannot reuse.

**Do NOT:** Assume DSL is standardized.

**Mitigation:**
- Commit to search backend in contract: "Elasticsearch 8.x (or OpenSearch 2.x). DSL: Lucene query syntax." (7.x is EOL — align with `eval-driver-search-es`)
- Document query format: "Queries use Elasticsearch query_string syntax: `(title:iPhone OR description:iPhone) AND -broken`"
- Example query layer: "API accepts simple filters (name, status, date_range). API translates to ES DSL internally. Clients never write raw DSL."
- If backend changes: New contract required, API layer absorbs DSL differences

**Escalation:** NEEDS_INFRA_CHANGE — If backend will change (ES→Solr, ES→Algolia), must renegotiate contract. Clients must not write backend-specific DSL.

---

## Edge Case 4: Full-text analyzer conflict (stemming, stopwords, language)

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

## Edge Case 5: Index refresh lag causes stale read-after-write

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

## Edge Case 6: Index size grows unbounded

**Symptom:** Search contract doesn't specify index retention. Index grows from 10GB → 100GB → 1TB over 2 years. Queries slow down. Disk full. Old documents from 2024 irrelevant to current searches.

**Do NOT:** Assume index size is managed automatically.

**Mitigation:**
- Lock retention policy in contract: "Index retains documents for 90 days only. Older documents deleted."
- Implementation: Use index aliases with time-based rotation: `products_2026-01`, `products_2026-02`, etc.
- Deletion strategy: "Monthly: delete `products_2025-*` indices (>12 months old)"
- Capacity planning: "Assume 1GB per 10M documents. Plan storage for 3x index size (redundancy + reindex space)"
- Monitoring: "Alert if index size > 100GB or growth rate > 1GB/day"

**Escalation:** NEEDS_INFRA_CHANGE — If no retention policy, index will grow unbounded. Must define retention before lock.

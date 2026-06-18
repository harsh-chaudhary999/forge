# Elasticsearch driver — reference for `eval-driver-search-es`

> Progressive-disclosure Level 3 (loaded on demand). Full API, examples, protocol/wire details, edge-case code, and deep guidance. SKILL.md is the operational contract.

## Edge Cases with Mitigation

### Edge Case 1: Refresh Not Applied Before Assert

**Scenario:** Document is indexed successfully, but search runs before refresh interval, returning 0 hits.

**Symptom:** `index(es, indexName, 'doc1', {...})` returns success. `search(es, indexName, {query: {term: {id: 'doc1'}}})` returns `total: 0` immediately after. Then 1 second later, the same search returns `total: 1`.

**Do NOT:** Assume the index() call failed. The document is in the index buffer, not yet in the refreshed segment.

**Mitigation:**
1. Call `POST /_refresh` explicitly after index() and before any search assertion
2. Use `?refresh=wait_for` in index API call to block until refresh completes
3. Verify refresh completed by checking `GET /_cat/indices?h=refresh.interval` for your index
4. If using bulk operations: explicitly POST `/{index}/_refresh` after bulk, not just within bulk
5. Add sleep/poll loop: keep searching with 100ms backoff until hits > 0 or timeout

**Escalation:** `BLOCKED` if cluster is yellow or red — refresh may not complete if shards are unavailable.

---

### Edge Case 2: Shard Unavailable (Index Yellow/Red)

**Scenario:** Index has unassigned primary or replica shards; search returns incomplete or stale results.

**Symptom:** `GET /_cluster/health/{index}` returns `status: yellow` or `status: red`. Search assertions pass but with fewer hits than expected. Bulk indexing says "failures" in response.

**Do NOT:** Proceed with eval while cluster is yellow/red. Results are partial and unreliable.

**Mitigation:**
1. Before eval, call `GET /_cluster/health` and verify `status: green` (all replicas active)
2. If yellow: check `GET /_cat/shards?h=index,shard,state` and verify only replica shards are unassigned (primaries must be active)
3. If red: primary shard is missing — investigate `GET /_cluster/allocation/explain` to find cause
4. Wait for allocation: `POST /_cluster/reroute?retry_failed=true` and poll until green
5. If recovery timeout: may need to delete problematic index and recreate

**Escalation:** `NEEDS_INFRA_CHANGE` if cluster cannot reach green health — indicates missing nodes or disk issues.

---

### Edge Case 3: Query DSL Clause Limit Exceeded

**Scenario:** Boolean query with many `must`, `should`, or `filter` clauses hits the clause limit (default 1024).

**Symptom:** `too_many_clauses` exception during search. Error message: `[bool] query can't have more than 1024 clauses`.

**Do NOT:** Increase the clause limit globally; this is a symptom of inefficient query design.

**Mitigation:**
1. Break complex bool query into smaller sub-queries (e.g., two separate searches combined in app logic)
2. Use `terms` query instead of multiple `term` clauses: `{terms: {status: ['active', 'pending']}}` instead of 100 OR'd `term` clauses
3. Use `range` query instead of many equality checks: `{range: {age: {gte: 18, lte: 65}}}`
4. For `match` queries with many terms: use `match_bool_prefix` or `simple_query_string` (more forgiving)
5. If must exceed: use `indices_boost` to split by index and run multiple queries

**Escalation:** `NEEDS_COORDINATION` — queries that need 1024+ clauses indicate schema design issue; coordinate with data team on query simplification.

---

### Edge Case 4: Field Mapping Conflict

**Scenario:** First document indexes with `age: 30` (integer), second document has `age: "30+"` (string). Mapping conflict on `age` field.

**Symptom:** `mapper_parsing_exception` when indexing second document. Error: `failed to parse field [age] of type [long] in document`.

**Do NOT:** Delete the first document and retry. The mapping is already locked to the first type.

**Mitigation:**
1. Define explicit mapping before indexing: `PUT /{index}/_mapping {properties: {age: {type: 'integer'}}}`
2. Use `dynamic: false` in mapping to reject unmapped fields instead of auto-creating mismatched types
3. For schema flexibility: use `keyword` type for mixed-type fields (stores as string, no parsing)
4. Before indexing test data: validate all field types match mapping (schema validation in eval harness)
5. If schema must change: re-index with new mapping (using `_reindex` API), don't modify existing mapping

**Escalation:** `NEEDS_INFRA_CHANGE` if data shape is inconsistent — producer team should normalize field types.

---

### Edge Case 5: Scroll Context Expired

**Scenario:** Eval uses scroll API for large result sets. Scroll context expires before all results are fetched.

**Symptom:** `search_context_missing_exception` when calling scroll with expired scroll_id. Partial results fetched (e.g., 2/5 pages of 1000-doc result set).

**Do NOT:** Use scroll for eval; prefer search-after or point-in-time (PIT) search.

**Mitigation:**
1. Use `search_after` with sort for pagination: `GET /{index}/_search {sort: [{_id: asc}], size: 100}` then `search_after: [last_id_from_page_1]`
2. If scroll required: increase scroll timeout: `GET /{index}/_search?scroll=5m` instead of default 1m
3. Use point-in-time search (8.x+): `POST /{index}/_pit?keep_alive=5m`, then fetch with `pit: {id, keep_alive}`
4. Keep scroll context alive by calling scroll frequently (at least once per 30s)
5. Always close unused scroll contexts: `DELETE /_search/scroll/{scroll_id}`

**Escalation:** `BLOCKED` if scroll context expires repeatedly — indicates timeout too short or network latency too high.

---

### Edge Case 6: Aggregation Precision Loss (Cardinality)

**Scenario:** Eval counts unique values using cardinality aggregation. Actual count is 10,000 but cardinality returns 9,500 (5% error).

**Symptom:** Cardinality aggregation returns approximate count (via HyperLogLog). Assertion fails because actual != expected. Error: `expected: 10000, actual: 9500`.

**Do NOT:** Assume cardinality is exact. It's probabilistic sampling.

**Mitigation:**
1. Use `precision_threshold` parameter to trade memory for accuracy: `{cardinality: {field: 'id', precision_threshold: 40000}}` (default 3000)
2. For exact counts: use `value_count` (slower but accurate) or `terms` aggregation with `min_doc_count: 1` and `size: <actual_cardinality>`
3. Assert with tolerance: `actual >= expected * 0.95` instead of exact equality
4. Document cardinality error tolerance in eval scenario (e.g., "±5% acceptable")
5. Verify precision_threshold is set appropriately for dataset size before assertion

**Escalation:** `NEEDS_CONTEXT` — clarify if count must be exact or approximate; use `value_count` if exact is required.

---

## Overview

This driver provides a complete testing harness for Elasticsearch indexes, supporting document indexing, search queries, result verification, and test cleanup. Uses the native Elasticsearch REST API with refresh semantics and comprehensive error handling.

## Connection

### `connect(url)`

Establish connection to Elasticsearch cluster via HTTP REST endpoint.

**Parameters:**
- `url` (string): Elasticsearch REST endpoint. Default: `http://localhost:9200`

**Returns:**
- `elasticsearch` (object): Connection handle with `url` and `client` properties

**Example:**
```javascript
const es = await connect('http://localhost:9200')
// or custom endpoint
const es = await connect('https://es-cluster.example.com:9200')
```

**Implementation notes:**
- Validates connectivity via GET / (cluster health check)
- Throws error if cluster unreachable
- Connection handle is reusable across multiple operations
- Supports HTTP Basic Auth in URL: `http://user:pass@localhost:9200`

---

## Index Operations

### `index(es, index_name, doc_id, doc)`

Upsert document into Elasticsearch index. Creates index if not exists. Refreshes index to make document immediately searchable.

**Parameters:**
- `es` (elasticsearch): Connection handle from `connect()`
- `index_name` (string): Index name (created if missing)
- `doc_id` (string): Document ID (UUID format recommended)
- `doc` (object): Document body. Fields should match index mapping.

**Returns:**
- `{acknowledged: boolean, id: string, index: string, version: number}`: Operation result

**Example:**
```javascript
const result = await index(es, 'users', '123', {
  user_id: '123',
  name: 'Alice',
  email: 'alice@example.com',
  age: 32,
  is_premium: true,
  registered_at: '2024-01-15T10:30:00Z',
  tags: ['admin', 'verified'],
  profile: {
    country: 'US',
    phone: '+1234567890'
  }
})
```

**Implementation notes:**
- Uses PUT `/index_name/_doc/doc_id` with auto_generate_ips=false
- Automatically creates index with default settings if not present
- Performs refresh=true on PUT to make doc immediately searchable
- Handles nested objects and arrays natively
- Returns HTTP 201 on create, 200 on update
- Throws error on mapping conflicts or validation failures

---

### `search(es, index_name, query)`

Execute search query against index. Returns matched documents and metadata.

**Parameters:**
- `es` (elasticsearch): Connection handle
- `index_name` (string): Index name to search
- `query` (object): Elasticsearch Query DSL object

**Returns:**
- `{hits: array, total: number, aggregations: object}`: Query results
  - `hits[].{_id, _score, _source}`: Matched documents
  - `total`: Total hit count
  - `aggregations`: Any agg results from query

**Query Examples:**

**Term query (exact match):**
```javascript
const results = await search(es, 'users', {
  query: {
    term: { is_premium: true }
  }
})
```

**Match query (full-text):**
```javascript
const results = await search(es, 'users', {
  query: {
    match: { email: 'alice@example.com' }
  }
})
```

**Bool query (complex):**
```javascript
const results = await search(es, 'users', {
  query: {
    bool: {
      must: [
        { term: { is_premium: true } },
        { range: { age: { gte: 30 } } }
      ],
      filter: [
        { term: { status: 'active' } }
      ]
    }
  }
})
```

**Aggregation query:**
```javascript
const results = await search(es, 'users', {
  query: { match_all: {} },
  aggs: {
    premium_count: {
      filter: { term: { is_premium: true } }
    },
    age_ranges: {
      range: {
        field: 'age',
        ranges: [
          { to: 30 }, { from: 30, to: 50 }, { from: 50 }
        ]
      }
    }
  }
})
```

**Implementation notes:**
- Uses POST `/index_name/_search` with DSL in request body
- Defaults to 10 results, configurable via `size` parameter
- Preserves full query structure (filters, must, should, aggs, etc.)
- Returns `_score` for relevance ranking
- Aggregations in response mirror request structure
- Throws error if query syntax invalid
- Empty result set returns `{hits: [], total: 0}`

---

## Verification & Assertions

### `verify(es, index_name, assertion)`

Assert that search results match expected criteria. Executes search and validates against assertions.

**Parameters:**
- `es` (elasticsearch): Connection handle
- `index_name` (string): Index name
- `assertion` (object): Assertion spec with properties:
  - `search_query` (object, required): Elasticsearch Query DSL
  - `expected_count` (number, optional): Expected number of hits
  - `contains_id` (string, optional): Assert document ID is in results
  - `contains_source` (object, optional): Assert _source fields match
  - `aggregation_path` (string, optional): Dot-path to agg value (e.g., `premium_count.value`)
  - `aggregation_value` (any, optional): Expected agg value
  - `min_score` (number, optional): All hits must score >= min_score
  - `description` (string, optional): Assertion description

**Returns:**
- `{passed: boolean, expected: any, actual: any, results: array, error: string}`: Assertion result

**Examples:**

**Count assertion:**
```javascript
const verified = await verify(es, 'users', {
  search_query: { query: { term: { is_premium: true } } },
  expected_count: 5,
  description: 'Should have exactly 5 premium users'
})
// Returns: {passed: true, expected: 5, actual: 5, results: [...]}
```

**Document ID assertion:**
```javascript
const verified = await verify(es, 'users', {
  search_query: { query: { match: { name: 'Alice' } } },
  contains_id: '123',
  description: 'Alice doc should appear in name search'
})
// Returns: {passed: true, results: [{_id: '123', _source: {...}}]}
```

**Source field assertion:**
```javascript
const verified = await verify(es, 'users', {
  search_query: { query: { term: { user_id: '123' } } },
  contains_source: { email: 'alice@example.com', age: 32 },
  description: 'User 123 should have correct email and age'
})
// Returns: {passed: true, results: [...]}
```

**Aggregation assertion:**
```javascript
const verified = await verify(es, 'users', {
  search_query: {
    query: { match_all: {} },
    aggs: {
      premium_count: {
        filter: { term: { is_premium: true } }
      }
    }
  },
  aggregation_path: 'premium_count.doc_count',
  aggregation_value: 5,
  description: 'Premium user count should be 5'
})
// Returns: {passed: true, expected: 5, actual: 5}
```

**Implementation notes:**
- Executes search_query internally
- Checks assertions in order: count, contains_id, contains_source, agg_path, min_score
- Returns first failed assertion with details
- On failure, includes actual vs expected + document excerpt
- Empty results pass count=0 assertion, fail contains_id
- Returns `passed: false` with error message on assertion failure

---

## Teardown

### `teardown(es, index_name)`

Delete test index and clean up resources.

**Parameters:**
- `es` (elasticsearch): Connection handle
- `index_name` (string): Index name to delete

**Returns:**
- `{acknowledged: boolean}`: Deletion result

**Example:**
```javascript
await teardown(es, 'users')
// Index deleted, mappings and data removed
```

**Implementation notes:**
- Uses DELETE `/index_name`
- Returns `acknowledged: true` on success
- Safe to call even if index doesn't exist (no error)
- Synchronous operation waits for full index deletion
- Removes all shards and replicas

---

## Complete Usage Example

```javascript
// Setup
const es = await connect('http://localhost:9200')
const indexName = 'test_users_' + Date.now()

// Index documents
await index(es, indexName, 'user_1', {
  user_id: '1',
  name: 'Alice',
  email: 'alice@example.com',
  is_premium: true,
  age: 32,
  tags: ['admin']
})

await index(es, indexName, 'user_2', {
  user_id: '2',
  name: 'Bob',
  email: 'bob@example.com',
  is_premium: false,
  age: 28,
  tags: []
})

// Query
const allUsers = await search(es, indexName, {
  query: { match_all: {} }
})
console.log(`Total users: ${allUsers.total}`) // 2

// Search premium users
const premiumUsers = await search(es, indexName, {
  query: { term: { is_premium: true } }
})
console.log(`Premium users: ${premiumUsers.total}`) // 1

// Verify assertions
const verify1 = await verify(es, indexName, {
  search_query: { query: { term: { is_premium: true } } },
  expected_count: 1,
  description: 'Should find 1 premium user'
})
console.log(verify1.passed) // true

const verify2 = await verify(es, indexName, {
  search_query: { query: { match: { name: 'Alice' } } },
  contains_id: 'user_1',
  contains_source: { email: 'alice@example.com' },
  description: 'Alice should be searchable by name with correct email'
})
console.log(verify2.passed) // true

// Cleanup
await teardown(es, indexName)
```

---

## Error Handling

### Connection Errors
- `ConnectError`: Cluster unreachable or invalid URL
- `AuthError`: Invalid credentials

### Query Errors
- `QueryParseError`: Invalid Elasticsearch DSL syntax
- `MappingConflictError`: Document doesn't match index mapping

### Assertion Errors
- `AssertionFailedError`: One or more assertions failed
  - Includes expected vs actual values
  - Includes document snippet for debugging

### Index Errors
- `IndexNotFoundError`: Index doesn't exist (verify, search operations)
- `IndexAlreadyExistsError`: Index creation conflict (rare with auto-create)

---

## Refresh Semantics

Elasticsearch indexes are eventually consistent by default. This driver:

1. **Explicit refresh on index()**: Each document upsert includes `?refresh=true` to make it immediately searchable
2. **No artificial delays**: Verification queries execute immediately after indexing
3. **Test isolation**: Each test uses unique index name to avoid cross-test interference
4. **Cleanup**: `teardown()` completely removes test indexes

---

## Decision Trees and Patterns

### Decision Tree 1: When to Use ?refresh=wait_for vs Explicit _refresh vs Polling

```
AFTER INDEXING A DOCUMENT, WHEN SHOULD EVAL PROCEED TO SEARCH?
│
├── IMMEDIATE SEARCH (next line of code)
│   ├── Use ?refresh=wait_for in index API call
│   │   └── STRATEGY: PUT /{index}/_doc/{id}?refresh=wait_for
│   │       TRADE-OFF: slower index (blocks until refresh), but guarantees searchability
│   │
│   └── Or use explicit refresh after index
│       └── STRATEGY: index(), then POST /_refresh, then search()
│           TRADE-OFF: two API calls, but index() returns quickly
│
├── BULK INDEXING (many documents)
│   ├── Refresh only AFTER bulk completes
│   │   └── STRATEGY: PUT /_bulk (many docs), then POST _refresh, then search
│   │       TRADE-OFF: bulk is fast, refresh is single call after
│   │
│   └── Do NOT refresh per-document in bulk
│       └── ANTI-PATTERN: refresh=wait_for in bulk request (defeats bulk efficiency)
│
├── ASYNC WORKFLOW (index happens in background, search much later)
│   ├── Polling strategy: search with exponential backoff
│   │   └── STRATEGY: search(), if 0 hits wait 100ms, retry; max 5 attempts
│   │       TRADE-OFF: eventual consistency model, flexible timeout
│   │
│   └── Verify explicit refresh was called
│       └── STRATEGY: monitor _refresh call count via cluster stats before assertion
│
└── UNKNOWN INDEX STATE (debugging)
    └── STRATEGY: Always call POST _refresh before any search assertion
        SAFEST: explicit refresh costs minimal overhead, prevents most refresh-related failures
```

---

### Decision Tree 2: Index Isolation Strategy (Dedicated Test Index vs Alias-Routed)

```
HOW SHOULD THIS EVAL ISOLATE TEST DATA?
│
├── DEDICATED TEST INDEX (simplest, most common)
│   ├── Single eval at a time
│   │   └── STRATEGY: create unique index per eval run (e.g., `test_users_${timestamp}`)
│   │       CLEANUP: DELETE /test_users_${timestamp} at teardown
│   │       PROS: complete isolation, easy cleanup
│   │       CONS: extra index creation overhead
│   │
│   └── Concurrent evals (parallel test runs)
│       └── STRATEGY: use unique index per test (UUIDs to avoid collision)
│           CLEANUP: use bulk delete or concurrent teardown
│
├── ALIAS-ROUTED INDEX (advanced, multiple versions)
│   ├── Rolling index with time-based rotation
│   │   └── STRATEGY: alias points to current index; rotate daily via ILM
│   │       PRECAUTION: verify DELETE targets correct backing index, not alias
│   │       VERIFY: GET /_aliases, confirm alias → index mapping before delete
│   │
│   └── Blue-green index swap
│       └── STRATEGY: maintain two indices, alias switches between them
│           PRECAUTION: never DELETE the alias, only DELETE the old backing index
│
├── SHARED PRODUCTION INDEX (NOT recommended for eval)
│   ├── Eval on isolated shard (shard_routing)
│   │   └── STRATEGY: use eval-specific routing value in all documents
│   │       SEARCH: specify same routing in queries (returns docs only from that shard)
│   │       CLEANUP: delete only docs with eval routing value
│   │
│   └── Eval-prefixed document IDs (filtering)
│       └── STRATEGY: prefix all eval docs with `eval_${uuid}_`
│           CLEANUP: query all eval docs, delete in bulk
│           RISK: pollutes production data, not recommended unless forced
│
└── NO ISOLATION (worst case)
    └── STRATEGY: accept data contamination risk
        CLEANUP: hope teardown works; verify count decreased
        RISK: eval failures from prior runs' leftover data
```

---

## Common Pitfalls

### Pitfall 1: Missing Refresh Before Assertion (Most Common Elasticsearch Eval Failure)

**Mistake:** Indexing a document and immediately asserting it's searchable without refresh.

```javascript
// WRONG
await index(es, 'users', '123', { name: 'Alice' });
const results = await search(es, 'users', { query: { term: { _id: '123' } } });
assert.equal(results.total, 1);  // FAILS: document not yet in searchable segment
```

**Fix:** Explicitly refresh before searching.

```javascript
// CORRECT
await index(es, 'users', '123', { name: 'Alice' });
await fetch(`http://localhost:9200/users/_refresh`, { method: 'POST' });
const results = await search(es, 'users', { query: { term: { _id: '123' } } });
assert.equal(results.total, 1);  // PASSES: document is now searchable
```

**Or use refresh=wait_for:**

```javascript
// CORRECT (alternative)
await fetch(`http://localhost:9200/users/_doc/123?refresh=wait_for`, {
  method: 'PUT',
  body: JSON.stringify({ name: 'Alice' })
});
const results = await search(es, 'users', { query: { term: { _id: '123' } } });
assert.equal(results.total, 1);  // PASSES
```

---

### Pitfall 2: Asserting _score Without Controlling Source Documents

**Mistake:** Searching for multiple documents and asserting on _score, without accounting for corpus-dependent scoring.

```javascript
// WRONG
await index(es, 'products', 'a', { name: 'Apple', category: 'fruit' });
await fetch(`http://localhost:9200/products/_refresh`, { method: 'POST' });
const results1 = await search(es, 'products', { query: { match: { name: 'Apple' } } });
assert.equal(results1.hits[0]._score, 1.25);  // FAILS: score is corpus-dependent

// Now index a second document
await index(es, 'products', 'b', { name: 'Apple Pie', category: 'dessert' });
await fetch(`http://localhost:9200/products/_refresh`, { method: 'POST' });
const results2 = await search(es, 'products', { query: { match: { name: 'Apple' } } });
// results2.hits[0]._score is now different!  Score changed due to new corpus
```

**Fix:** Assert on relative score ranking, not absolute values, or use controlled scoring.

```javascript
// CORRECT
await index(es, 'products', 'a', { name: 'Apple', category: 'fruit' });
await index(es, 'products', 'b', { name: 'Apple Pie', category: 'dessert' });
await fetch(`http://localhost:9200/products/_refresh`, { method: 'POST' });

const results = await search(es, 'products', {
  query: {
    bool: {
      must: [{ match: { name: 'Apple' } }],
      filter: [{ term: { category: 'fruit' } }]  // Filter to control document set
    }
  }
});

// Assert on position and presence, not exact _score
assert.ok(results.total >= 1);
assert.equal(results.hits[0]._source.category, 'fruit');
assert.ok(results.hits[0]._score > 0);
```

---

### Pitfall 3: Not Handling Multi-Value Field Arrays in Assertions

**Mistake:** Asserting on array fields as if they were single values.

```javascript
// WRONG
await index(es, 'users', '123', { 
  name: 'Alice',
  tags: ['admin', 'verified', 'moderator']
});
await fetch(`http://localhost:9200/users/_refresh`, { method: 'POST' });

const results = await search(es, 'users', { query: { term: { tags: 'admin' } } });
assert.deepEqual(results.hits[0]._source.tags, ['admin']);  // FAILS: array has 3 elements
```

**Fix:** Assert on array presence, not exact equality.

```javascript
// CORRECT
const results = await search(es, 'users', { query: { term: { tags: 'admin' } } });
assert.ok(Array.isArray(results.hits[0]._source.tags));
assert.ok(results.hits[0]._source.tags.includes('admin'));
assert.equal(results.hits[0]._source.tags.length, 3);
```

---

### Pitfall 4: Forgetting to Close Scroll Context (Resource Leak)

**Mistake:** Using scroll API without closing the context.

```javascript
// WRONG
const scroll1 = await fetch(`http://localhost:9200/users/_search?scroll=1m`, {
  method: 'POST',
  body: JSON.stringify({ size: 100, query: { match_all: {} } })
}).then(r => r.json());
const scrollId = scroll1._scroll_id;

// Fetch more pages...
const scroll2 = await fetch(`http://localhost:9200/_search/scroll`, {
  method: 'POST',
  body: JSON.stringify({ scroll: '1m', scroll_id: scrollId })
}).then(r => r.json());

// Never close the scroll context!
// Resource leak: scroll context persists in ES memory, accumulates across test runs
```

**Fix:** Always close scroll contexts.

```javascript
// CORRECT
let scrollId = null;
try {
  const scroll1 = await fetch(`http://localhost:9200/users/_search?scroll=1m`, {
    method: 'POST',
    body: JSON.stringify({ size: 100, query: { match_all: {} } })
  }).then(r => r.json());
  scrollId = scroll1._scroll_id;

  // Fetch pages...
  const scroll2 = await fetch(`http://localhost:9200/_search/scroll`, {
    method: 'POST',
    body: JSON.stringify({ scroll: '1m', scroll_id: scrollId })
  }).then(r => r.json());

} finally {
  // Always close scroll context
  if (scrollId) {
    await fetch(`http://localhost:9200/_search/scroll`, {
      method: 'DELETE',
      body: JSON.stringify({ scroll_id: scrollId })
    });
  }
}

// Or better: use search_after instead of scroll for eval
```

---


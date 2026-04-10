---
name: eval-driver-search-es
description: Eval driver for Elasticsearch via REST. Functions: connect(), index(doc), search(query), verify(assertion), teardown().
type: rigid
requires: [brain-read]
---

# Elasticsearch Eval Driver

REST-based evaluation driver for Elasticsearch search index testing. Verifies search state, query results, and data consistency.

## Anti-Pattern Preamble: Search Eval Failures You Will Hit

| Rationalization | The Truth |
|---|---|
| "Index the doc, then search immediately" | Elasticsearch is eventually consistent. Without `refresh=true` or an explicit refresh call, your search will return stale results. ALWAYS refresh before asserting search state. |
| "If the document was indexed, search will find it" | Indexing success means the write was acknowledged. Search visibility depends on refresh interval (default: 1s). In eval, always force refresh after indexing and before searching. |
| "Mapping conflicts won't happen in tests" | Dynamic mapping creates fields based on first-seen type. If test A indexes `price: 10` (integer) and test B indexes `price: "10.50"` (string), you get a mapping conflict. Always define explicit mappings before indexing. |
| "Analyzer settings don't affect eval" | Analyzers determine tokenization. If you search for "New York" but the analyzer tokenizes as ["new", "york"], your exact match fails. Verify analyzer behavior matches your search queries. |
| "We can skip cleanup, ES handles it" | Leftover indices from failed tests cause index name collisions, disk exhaustion, and shard count limits. Always teardown indices in eval cleanup, even on failure. |

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

## Limitations & Notes

- Supports Elasticsearch 7.x+ and 8.x (REST API compatible)
- Single document operations (bulk operations via separate tool)
- No custom analyzer definition (uses index defaults)
- No explicit mapping control (uses dynamic mapping by default)
- Verification is point-in-time (no time-range assertions)
- Errors are synchronous; no async retry logic

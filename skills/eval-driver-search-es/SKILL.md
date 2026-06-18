---
name: eval-driver-search-es
description: "WHEN: qa-semantic-csv-orchestrate or run_semantic_csv_eval dispatches an automation step that requires Elasticsearch index state verification via REST. Functions: connect(), index(doc), search(query), verify(assertion), teardown()."
type: rigid
requires: [brain-read]
version: 1.0.1
preamble-tier: 3
triggers:
  - "eval Elasticsearch"
  - "run search eval"
  - "ES eval driver"
allowed-tools:
  - Bash
---

# Elasticsearch Eval Driver

**Runner dispatch:** **`qa-semantic-csv-orchestrate`** / **`run_semantic_csv_eval.py`** routes **`Surface: es`** rows in **`qa/semantic-automation.csv`** to this driver. Do not invoke this skill directly unless you are implementing or debugging the runner.

REST-based evaluation driver for Elasticsearch search index testing. Verifies search state, query results, and data consistency.

## HARD-GATE: Anti-Pattern Preambles

### 1. "Just index and search — if hits > 0, eval passes"
**Why This Fails:**
- Relevance ranking means position matters; hit count says nothing about result quality
- Score threshold varies by document corpus size and analyzer; exact same query scores differently on different data
- Multi-field searches with different analyzers cause unexpected ranking inversions
- Phrase queries fail if tokenization doesn't match intent (e.g., "New York" tokenized as separate terms)
- Boolean query clause weighting is non-obvious; OR clauses boost scores in ways that change hit order

**Enforcement:**
- MUST assert on result position (hits[0] for top-ranked result, not just presence in results)
- MUST set min_score threshold and verify all results exceed it
- MUST assert exact match on at least one field (e.g., _id or unique identifier)
- MUST verify ranking order if multiple docs match (use _score comparison)
- MUST verify _source content, not just existence of hit count

### 2. "Elasticsearch refresh is automatic, no need to wait"
**Why This Fails:**
- Default refresh interval is 1 second; indexed documents are NOT immediately searchable
- `refresh=true` on index() call makes doc searchable, but if index() doesn't use it, doc is in buffer
- Rapid index-search sequences hit the stale buffer between refresh cycles
- Bulk operations don't auto-refresh; bulk-indexed docs remain invisible for up to 1s after bulk completes
- Force refresh after index() is idempotent and safe; skipping it causes intermittent failures

**Enforcement:**
- MUST use `?refresh=wait_for` or explicit POST _refresh before ANY search assertion
- MUST verify refresh was called by checking cluster task list or monitoring
- MUST document refresh_interval tuning if eval uses custom settings (e.g., `refresh_interval=500ms`)
- MUST call POST `/_refresh` explicitly if using bulk operations before assertions
- MUST never assume indexing success = searchability; test with explicit refresh-then-search pattern

### 3. "Delete test index with DELETE /index at teardown"
**Why This Fails:**
- Shared ES cluster with alias-routed indices loses data on wrong delete (deletes current alias target)
- Index names are case-sensitive; deleting `Test_Index` when you created `test_index` leaves orphan
- ILM (Index Lifecycle Management) policies auto-create rolled-over indices; DELETE deletes active index only
- Backup or snapshot containing index may reference deleted index by name, causing restore failure
- Replication in-flight to followers may not see delete; followers retain the index

**Enforcement:**
- MUST verify index name exactly matches (no case mismatches, no dynamic suffixes)
- MUST check for active aliases before delete (GET `/_aliases`)
- MUST verify ILM policy is disabled or understood (GET `/_ilm/status`)
- MUST snapshot or verify no in-flight replication before deleting
- MUST verify correct index deleted (GET index count before/after, verify delta)

### 4. "Aggregation results are deterministic"
**Why This Fails:**
- Cardinality aggregations use HyperLogLog sampling; results are approximate (±5% error)
- Terms aggregations order non-deterministically when counts are equal (no stable sort across shards)
- Result ordering depends on shard distribution; same query returns results in different order if shard count changes
- Collection ordering (e.g., top_hits within terms) is not guaranteed unless size explicitly bounds it
- Nested aggregations inherit parent shard assignment; different shards = different local results

**Enforcement:**
- MUST acknowledge cardinality is approximate; use precision_threshold parameter
- MUST set explicit `size` on terms aggregations to deterministically bound result count
- MUST use `order` clause to sort results explicitly (e.g., `"order": {"_count": "desc"}`)
- MUST not assert exact equality on cardinality; use range tolerance instead
- MUST document sampling semantics in eval scenario description

### 5. "Mapping changes take effect immediately"
**Why This Fails:**
- Dynamic mapping adds new fields but does NOT re-index existing documents
- Existing docs continue to use old mapping; only new docs get new mapping
- Changing field type (e.g., string → keyword) requires re-index; old docs stay in old type
- Mapping updates can fail if new mapping conflicts with existing mappings (e.g., changing analyzer)
- Rollover indices with ILM create new indices with updated mapping; old indices retain old mapping

**Enforcement:**
- MUST define explicit mapping before indexing ANY documents
- MUST call POST `/{index}/_reindex` after mapping change and before assertions on changed fields
- MUST track mapping version in eval scenario and verify version before searching
- MUST implement rollback plan if re-index fails (delete index, re-index from source)
- MUST verify mapping change via GET `/{index}/_mapping` before asserting on new fields

## Iron Law

```
EVERY ELASTICSEARCH EVAL SCENARIO REFRESHES THE INDEX BEFORE ANY SEARCH ASSERTION. EVERY SEARCH ASSERTION VERIFIES SPECIFIC FIELD VALUES, RESULT POSITION, AND SCORE — NOT JUST HIT COUNT. teardown() IS CALLED IN ALL PATHS.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Search assertion runs immediately after index() without a refresh call** — You are asserting against stale state. STOP. Add explicit refresh before any search assertion.
- **Index is created without explicit mappings** — Dynamic mapping will corrupt field types when multiple document shapes are indexed. STOP. Define explicit mappings before any indexing.
- **Teardown is not present in the test cleanup block** — Index artifacts will accumulate across runs causing shard limits and index name collisions. STOP. Add teardown() to every test's cleanup path, including failure paths.
- **Elasticsearch cluster returns HTTP 503 or yellow health** — The cluster is degraded. Assertions may pass against missing replicas. STOP. Restore cluster health (green or yellow-acceptable) before running eval.
- **Test searches for exact phrase but analyzer was not verified** — Tokenization may split the phrase in unexpected ways. STOP. Verify analyzer behavior with the `_analyze` API before asserting exact matches.
- **Index from a previous test run is still present at test start** — State contamination from prior run. STOP. Call teardown/recreate at the start of each eval run.

---

## Reference (load on demand)

The full API, examples, protocol details, edge-case code, and deep guidance live in
**`reference/es-reference.md`** (Agent Skills progressive disclosure). This SKILL.md is the operational
contract: runner dispatch, discipline (anti-pattern / iron law / red flags), and decision logic.

## Eval Checklist: Elasticsearch Driver

Before marking eval pass for any Elasticsearch-backed feature:

- [ ] Cluster health verified (GET /_cluster/health returns status: green or yellow)
- [ ] Index name is unique (timestamp or UUID suffix to prevent collisions)
- [ ] Explicit mapping defined before indexing ANY documents
- [ ] Dynamic mapping is OFF (dynamic: false) or well-understood
- [ ] Analyzer behavior verified with _analyze API before assertion
- [ ] Each index() call includes refresh=wait_for OR explicit POST _refresh before search
- [ ] Bulk operations followed by explicit POST _refresh before assertions
- [ ] Search assertion verifies result position (not just hit count)
- [ ] Score assertions account for corpus-dependent scoring (use relative, not absolute)
- [ ] Aggregation precision tolerance documented (cardinality, terms ordering acknowledged)
- [ ] Array field assertions use includes/contains, not exact equality
- [ ] Scroll contexts properly closed (or use search_after/PIT instead)
- [ ] Teardown deletes correct index (verify index count decreased)
- [ ] Mapping updates followed by re-index before asserting on new fields

### Post-Implementation Checklist: Did I Follow the Skill?

- [ ] Every scenario step has an entry in `qa/semantic-eval-run.log` (no silent skips).
- [ ] Each step outcome is one of: `PASS`, `FAIL`, `BLOCKED_DEPENDENCY`, `SKIPPED` (with reason), `CONTEXT_GAP` — no unclassified results.
- [ ] `qa/semantic-eval-manifest.json` written with `kind: semantic-csv-eval` and a non-placeholder `outcome`.
- [ ] Elasticsearch cluster health is `green` or `yellow` (not `red`) before eval; index mapping matches expected fields.
- [ ] `python3 tools/verify/verify_forge_task.py --task-id <id> --brain <brain>` exits 0.

## Cross-References

- **eval-driver-api-http** — HTTP trigger for search-indexing endpoints
- **eval-product-stack-up** — Bring up Elasticsearch cluster before eval
- **qa-semantic-csv-orchestrate** — Coordinate Elasticsearch eval with API/DB assertions in **`qa/semantic-automation.csv`**
- **deploy-driver-docker-compose** — Elasticsearch service definition
- **reasoning-as-infra** — Search architecture patterns, sharding strategy, analyzer tuning
- **contract-search** — Negotiate search contracts (field names, query DSL semantics)

---

## Limitations & Notes

- Supports Elasticsearch 7.x+ and 8.x (REST API compatible)
- Single document operations (bulk operations via separate tool)
- No custom analyzer definition (uses index defaults)
- No explicit mapping control (uses dynamic mapping by default)
- Verification is point-in-time (no time-range assertions)
- Errors are synchronous; no async retry logic

## Checklist

Before running an Elasticsearch eval scenario:

- [ ] Index refreshed (`?refresh=wait_for` or `POST _refresh`) before every search assertion
- [ ] Assertions verify specific field values and result position — not just hit count > 0
- [ ] `min_score` threshold set and verified in search results
- [ ] `teardown()` called in all paths (success, failure, timeout)
- [ ] Cluster health verified as `green` or `yellow` before scenario begins
- [ ] Mapping verified via `GET /{index}/_mapping` before assertions on new fields

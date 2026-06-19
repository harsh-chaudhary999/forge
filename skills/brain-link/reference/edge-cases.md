# brain-link — Edge Cases

> Extracted from `SKILL.md` §11 (Edge Cases). Five edge cases with symptom,
> Do-NOT, action steps, and escalation path. The inline SKILL.md keeps a summary
> table; this is the full detail.

### Edge Case 1: Circular Link Graph

**Symptom**: D001 complements D002, D002 replaces D001, creating a cycle.

**Do NOT**: Silently accept the cycle. Circular dependencies in a decision graph indicate unresolved conflicts or miscategorized relationships.

**Action**:
1. Detect cycle before write (graph validation during link creation)
2. Reject with error message listing the cycle: "Cannot create link D002 replaces D001: would create cycle D001 → D002 → D001"
3. Prompt user: "Did you mean variant relationship instead of replaces? Or does this indicate two conflicting decisions that should both be marked?"

**Escalation**: NEEDS_CONTEXT
- User must clarify: Is this variant instantiation? Bidirectional conflict? Misclassified relationship?
- If true circular dependency exists, both decisions need status review (cannot both be active)

---

### Edge Case 2: Decision Superseded by Multiple Heirs

**Symptom**: D003 replaces D001 AND D007 replaces D001 (parallel supersession).

**Do NOT**: Treat as invalid — this is valid in parallel supersession scenarios (e.g., different products adopt different successors).

**Action**:
1. Accept link creation (this is valid)
2. Mark D001 status = `superseded` (not `deprecated`)
3. Reference both successors in D001's metadata: `succeeded_by: [D003, D007]`
4. Ensure each heir has `replaces: D001` link explicitly
5. Document why parallel supersession occurred (product divergence, feature split, etc.)

**Escalation**: NEEDS_COORDINATION
- When multiple heirs exist, council should document the split point
- Each heir must have clear domain/product scope so they don't create false conflicts

---

### Edge Case 3: Link Target Not Found

**Symptom**: `brain-link create D042 replaces D099` but D099.md doesn't exist in the brain.

**Do NOT**: Create dangling link pointing to non-existent decision.

**Action**:
1. Search brain for near-match (similar ID range, similar creation date, similar tags)
2. Return candidates: "Did you mean D098 (similar era) or D109 (similar domain)?"
3. If no match found, reject with error: "D099 not found in brain. Create decision first, then link."
4. Store as tombstone link if D099 is confirmed deleted: `replaces: D099 [ARCHIVED]`

**Escalation**: NEEDS_CONTEXT
- If target is confirmed deleted (in brain archive), document as superseded by archive
- If target never existed, return error: user must verify ID before linking

---

### Edge Case 4: Conflicting Links Between Active Decisions

**Symptom**: D010 conflicts D015, both status=active, both in production across multiple products.

**Do NOT**: Silently coexist. Active conflicting decisions indicate unresolved architectural choice.

**Action**:
1. Detect conflict during link creation
2. Query both decisions: confirm both are status=active
3. Escalate with warning: "Creating conflict between two active decisions. One must be deprecated."
4. Force user to: mark one as deprecated OR verify they serve different products
5. If product-divergent, update link metadata: `applies_to: {D010: [product_a, product_b], D015: [product_c, product_d]}`

**Escalation**: NEEDS_COORDINATION
- Active conflicts require council decision to resolve
- Document resolution in both decisions: "Conflict resolved Q3-2024: D010 for product_a, D015 for product_c"
- Set timeline for convergence (if applicable)

---

### Edge Case 5: Graph Traversal Timeout on Large Brain

**Symptom**: `brain-link query tag=#api-versioning depth=all` returns partial results after 5-second timeout on brain with >500 decisions.

**Do NOT**: Use partial results for analysis. Partial graph closure gives false negatives.

**Action**:
1. Detect timeout during query execution
2. Return partial results with warning: "Query incomplete (timeout). 287 of ~400 decisions returned."
3. Suggest narrowing: "Add filter: `tag=#api-versioning AND product=shopapp` (returns in <1s)"
4. Suggest depth limit: "Use `depth=2` instead of `depth=all` (returns immediate neighbors)"
5. Recommend indexing: "For >500 decisions, enable tag index via brain-read config"

**Escalation**: NEEDS_CONTEXT
- User should narrow query using product/tag filters
- If full graph traversal required, may need to optimize brain structure (split by domain)
- For production brains >1000 decisions, graph indexing becomes mandatory

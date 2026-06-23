# brain-why — Edge Cases

## Edge Cases

### Edge Case 1: Circular dependency in decision links (A→B→A)

**Symptom:** Provenance trace loops back on itself (parent → child → parent creates cycle).

**Do NOT:** Follow cycle infinitely. Do NOT treat circular dependency as acceptable.

**Mitigation:**
1. Detect cycle: Track visited decision IDs during traverse
2. Report when found: "Circular dependency detected: D42 → D43 → D42"
3. Break cycle by reporting at cycle detection point (not following back edge)
4. Escalate: This indicates decision graph corruption

**Escalation:** BLOCKED — Circular dependency in decision graph. Indicates data corruption or modeling error. One decision references the other incorrectly. Contact decision owners to remove circular reference and restore linear provenance chain.

---

### Edge Case 2: Decision has no parent (orphaned decision)

**Symptom:** Decision lacks `parent_decision:` field, showing no upstream context or justification.

**Do NOT:** Assume decision stands alone. Do NOT treat missing parent as authoritative.

**Mitigation:**
1. Check for `parent_decision:` field in frontmatter
2. If empty or missing, search for implicit parent: `grep -r "related.*D<id>" ~/forge/brain --include="*.md"`
3. If truly orphaned, document: "Decision D### has no recorded parent (orphan or root decision)"
4. For orphan: Review decision title and problem statement — may be foundational decision (no parent needed)

**Escalation:** NEEDS_CONTEXT — Orphaned decision may be root decision (acceptable) or indicate incomplete decision graph. Verify with decision author whether parent is missing or decision is intentionally foundational.

---

### Edge Case 3: Provenance chain broken (linked decision deleted)

**Symptom:** Decision references parent/child that no longer exists (file was archived or moved).

**Do NOT:** Ignore broken reference. Do NOT proceed with incomplete provenance.

**Mitigation:**
1. Verify referenced decision exists: `grep -r "^decision_id: D<parent-id>" ~/forge/brain --include="*.md"`
2. If not found, check archive: `grep -r "^decision_id: D<parent-id>" ~/forge/brain/archived --include="*.md"`
3. If archived: Note in provenance that parent was archived; flag for investigation
4. If truly deleted: Flag as data integrity issue — decisions should never be deleted

**Escalation:** BLOCKED — Broken provenance chain. Parent/child decision missing or archived. Cannot trace complete lineage. Contact brain maintainers to restore reference or document why parent was removed.

---

### Edge Case 4: Too many hops to root (provenance path > 5 levels)

**Symptom:** Provenance trace requires traversing > 5 parent decisions (D1 → D2 → D3 → D4 → D5 → D6 → ...).

**Do NOT:** Treat excessively deep chains as normal. Deep chains indicate poor decision granularity.

**Mitigation:**
1. Count hops while tracing parent chain
2. If > 5 hops, warn: "Long provenance chain detected (6+ decisions)"
3. Report intermediate decisions at each level (help readers understand path)
4. Recommend decision consolidation: consider merging some decisions

**Escalation:** NEEDS_COORDINATION — Very deep provenance chain suggests decision graph could be simplified. Consult decision owners about consolidating related decisions or creating summary decision at intermediate level.

---

### Edge Case 5: (EXISTING) Partially documented decisions missing sections

**Symptom:** Decision file lacks expected sections (Why, When, By Whom, Alternatives, Evidence).

**Do NOT:** Ignore gaps. Do NOT guess missing information.

**Mitigation:**
1. Check for required sections: grep for "^##" (heading level 2) in decision file
2. List missing sections: "Decision D### missing: Evidence, Alternatives Considered"
3. Flag as incomplete: "Provenance incomplete — cannot fully trace reasoning"
4. Point to original author: "Contact <decision_author> to document missing sections"

**Escalation:** NEEDS_CONTEXT — Decision partially documented. Cannot trace full provenance without missing sections. Notify decision author to complete documentation.

---

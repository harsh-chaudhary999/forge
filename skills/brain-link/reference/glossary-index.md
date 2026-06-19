# brain-link — Glossary & Index

> Extracted from `SKILL.md` §15 (Glossary) and §16 (Index). Section numbers in
> the Index refer to the section structure of `SKILL.md` as authored; after the
> progressive-disclosure split, the named topics now live either inline in
> `SKILL.md` or in the sibling `reference/*.md` files noted below.

## Glossary

**Bidirectional Link**: A link that travels in both directions. Used for CONFLICTS, COMPLEMENTS, RELATED. Query "What conflicts with D30?" finds D31 and vice versa.

**Circular Dependency**: A cycle in the link graph (D1 → D2 → D1). Invalid in decision graphs; indicates unresolved conflicts or miscategorization.

**Closure** (graph closure): The set of all reachable decisions from a starting decision, following all link types up to a specified depth.

**Decision Node**: A single decision (D42) with metadata: ID, title, creation date, product, domain, tags, status, summary.

**Directional Link**: A link with a source and target that are not interchangeable. Used for REPLACES and VARIANT. "D42 replaces D89" ≠ "D89 replaces D42".

**Provenance**: The history of when and why a link was created. Essential for understanding decision rationale.

**Supersession**: When one decision replaces another. Created with `replaces` link. Old decision marked `status=superseded`.

**Variant**: An instance of a pattern applied in a different product or context. Created with `variant` link. Used for cross-product queries.

---

## Index

- **Link Types**: Related, Replaces, Conflicts, Complements, Variant (Section 1, inline in SKILL.md)
- **Semantic Tags**: Concept, Pattern, Domain, Architectural, Metadata (Section 2 → `reference/tags.md`)
- **Cross-Product Linking**: Strategy for global → instance links (Section 3, inline in SKILL.md)
- **Cross-Time Linking**: Evolution chains and change rationale (Section 4, inline in SKILL.md)
- **Query Interface**: Basic and advanced query syntax (Section 5, inline in SKILL.md)
- **Data Model**: Decision nodes, link edges, tag indexes (Section 6, inline in SKILL.md)
- **Example Graph**: Complete decision graph with all relationship types (Section 7 → `reference/example-graph.md`)
- **Usage Examples**: Four detailed example queries (Section 8 → `reference/examples.md`)
- **Integration with brain-read**: Complementary skills and workflow (Section 9, inline in SKILL.md)
- **Best Practices**: When to link, link hygiene, tag strategy, query strategy (Section 10, inline in SKILL.md)
- **Edge Cases**: 5 edge cases with escalation paths (Section 11, inline in SKILL.md)
- **Decision Trees**: Link type selection and directionality (Section 12 → `reference/decision-trees.md`)
- **Related Skills**: brain-write, brain-why, brain-recall, brain-forget (Section 14, inline in SKILL.md)

---

## Extending brain-link (Section 13)

Future enhancements:

- **Impact analysis**: "Which decisions would be affected if we change D42?"
- **Change impact**: "Which products would be affected by deprecating D89?"
- **Pattern suggestions**: "You're considering a saga pattern — here are similar decisions"
- **Cross-linking**: Link to code (commit SHAs, file paths, class definitions)
- **Timeline visualization**: Calendar view of decision evolution
- **Collaboration**: Decision committee tracking, approval chains

# Troubleshooting

> Deep reference for brain-recall. The operational contract lives in
> [`../SKILL.md`](../SKILL.md).

**Q: No results found for my query**
- A: Try broader keywords or check available tags with `grep -r "^tags:" ~/forge/brain/`
- A: Search in a specific section (decisions/ vs patterns/ vs learnings/)
- A: Check if the brain file exists for your product/project

**Q: Too many results returned**
- A: Add product/project filter to narrow scope
- A: Add tag filter (e.g., `#resolved` to exclude open issues)
- A: Add date filter (e.g., "last 6 months")

**Q: Result seems outdated**
- A: Check the decision date and #resolved status
- A: Look for superseding decisions (often linked in "Related" section)
- A: Ask brain-read for the latest version of that file

**Q: Can't find the exact pattern I'm looking for**
- A: Try searching with different keywords (synonyms)
- A: Check brain/contracts/ if you're looking for API/schema patterns
- A: Create a new pattern in brain-write if this is a novel solution

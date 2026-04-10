---
description: "Search brain for past decisions, patterns, and gotchas"
---

Invoke the `brain-recall` skill.

The user's argument is a search query (e.g., "cache invalidation", "auth middleware", "seed product").
If no query was provided, ask the user what they want to search for.

Brain-recall uses hybrid search: grep patterns + tag filtering + recency weighting to find relevant decisions, patterns, and gotchas from `~/forge/brain/`.

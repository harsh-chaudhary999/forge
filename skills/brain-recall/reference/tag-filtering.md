# Tag-Based Filtering

## 2. Tag-Based Filtering

Filter decisions by structured tags. **Tags are a YAML array of bare words** in the
decision's frontmatter — `tags: [api, versioning, breaking-change]` — **not**
`#hashtags`. Lifecycle is a separate `status:` field (`active | warm | cold |
archived` per brain-write/brain-forget), **not** a tag like `#resolved`/`#open`.

**Common tag values** (bare words, domain/category): `api`, `database`, `cache`,
`frontend`, `mobile`, `events`, `search`, `infra`, `scaling`, `migration`,
`versioning`, `backward-compat`, `performance`, `observability`, `security`.

**Tag filtering strategies** (match inside the YAML `tags:` array):

### Single tag query
```bash
# Find all active API decisions
grep -rlE "^tags:.*\bapi\b" ~/forge/brain/decisions/ --include="*.md" \
  | xargs grep -l "^status: active"
```

### Multi-tag AND query
```bash
# Find database decisions tagged both 'migration' and 'performance'
grep -rlE "^tags:.*\bdatabase\b" ~/forge/brain/decisions/ --include="*.md" \
  | xargs grep -lE "^tags:.*\bmigration\b" | xargs grep -lE "^tags:.*\bperformance\b"
```

### Tag + status extraction from frontmatter
```bash
# Show the tags and status of each decision
grep -A 25 "^---" ~/forge/brain/decisions/**/*.md | grep -E "^(tags|status):"
```

**Example tag-based queries:**

- "Show me all database decisions"
  ```bash
  grep -rlE "^tags:.*\bdatabase\b" ~/forge/brain/decisions/ --include="*.md"
  ```

- "Which decisions are tagged both 'cache' and 'eventual-consistency'?"
  ```bash
  grep -rlE "^tags:.*\bcache\b" ~/forge/brain/decisions/ --include="*.md" \
    | xargs grep -lE "^tags:.*\beventual-consistency\b"
  ```

- "Show active decisions tagged 'security' (exclude archived)"
  ```bash
  grep -rlE "^tags:.*\bsecurity\b" ~/forge/brain/decisions/ --include="*.md" \
    | xargs grep -l "^status: active"
  ```

> The shipped read-only **brain MCP** `brain_recall` tool does this scan for you
> (case-insensitive substring over the brain) and computes the brain root itself —
> prefer it when configured; the greps above are the live fallback. See
> [`docs/brain-mcp.md`](../../../docs/brain-mcp.md).

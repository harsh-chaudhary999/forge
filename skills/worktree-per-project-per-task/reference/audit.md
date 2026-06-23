# Audit & Observability

How worktree lifecycle state is tracked, persisted, and queried.

## Metadata File (.worktree-meta)

Created inside each worktree, tracked through lifecycle:

```
task_id: feature-xyz-abc123
created_at: 2026-04-08T14:32:15Z
status: in_flight|merged|eval_failed_escalate|rolled_back
eval_pass: true|false
eval_timestamp: 2026-04-08T14:45:22Z
self_heal_attempts: 0|1|2|3
branch_name: task/feature-xyz-abc123
```

## Archive Directory (.worktree-archive/)

Persists metadata and cleanup logs after worktree removal:

```
.worktree-archive/
  feature-xyz-abc123-1712596335.meta     ← Metadata snapshot
  cleanup.log                             ← Cleanup audit trail
```

## Query Pattern

Find all eval failures for a task:

```bash
grep -r "eval_pass: false" .worktree-archive/ | wc -l
```

Find worktrees older than 48 hours:

```bash
find .worktrees -name ".worktree-meta" -exec \
  grep -l "created_at:" {} \; | while read f; do
    created=$(grep "created_at:" "$f" | cut -d' ' -f2-)
    created_ts=$(date -d "$created" +%s)
    if (( $(date +%s) - created_ts > 172800 )); then
      echo "$(dirname $f)"
    fi
  done
```

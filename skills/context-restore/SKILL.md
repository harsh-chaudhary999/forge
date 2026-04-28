---
name: context-restore
description: "WHEN: You need to resume work from a previous session — after context compaction, after picking up a stalled task, or when asked 'where were we', 'resume', 'restore context', 'pick up where I left off'."
type: flexible
version: 1.0.0
preamble-tier: 2
triggers:
  - "resume"
  - "restore context"
  - "where were we"
  - "pick up where I left off"
  - "context restore"
allowed-tools:
  - Bash
  - Read
---

# context-restore

Finds and displays the most recent checkpoint for the current repo. Read-only — never modifies files or codebase.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I can reconstruct context from git log" | Git log shows commits, not in-flight decisions or remaining work. |
| "I'll just ask the user what we were doing" | Wastes human attention. The checkpoint exists for exactly this moment. |
| "The brain files have everything" | Brain files store finalized decisions. Checkpoints store in-progress state. |

**Read the checkpoint. Then orient. Then proceed.**

## Invocation Modes

- `/context-restore` — most recent checkpoint
- `/context-restore list` — all checkpoints newest-first
- `/context-restore <title-fragment>` — find checkpoint matching the fragment

## Workflow

### Step 1 — Detect repo slug

```bash
SLUG=$(git remote get-url origin 2>/dev/null \
  | sed 's/.*[:/]\([^/]*\)\.git$/\1/' \
  | sed 's/.*[:/]\([^/]*\)$/\1/')
[ -z "$SLUG" ] && SLUG=$(basename "$(git rev-parse --show-toplevel)")
TASK_ID="${FORGE_TASK_ID:-${FORGE_PRD_TASK_ID:-}}"
if [ -z "$TASK_ID" ]; then
  echo "No FORGE_TASK_ID set. Set FORGE_TASK_ID (or FORGE_PRD_TASK_ID) before restoring checkpoints."
  exit 1
fi
CHECKPOINT_DIR="$HOME/forge/brain/prds/$TASK_ID/checkpoints"
echo "Checkpoint dir: $CHECKPOINT_DIR"
```

### Step 2 — Check for checkpoints

```bash
if [ ! -d "$CHECKPOINT_DIR" ] || [ -z "$(ls -A "$CHECKPOINT_DIR" 2>/dev/null)" ]; then
  echo "No checkpoints found for $SLUG. Run /context-save first."
  exit 0
fi
```

If no checkpoints found, output the message above and stop.

### Step 3 — For `/context-restore list`

```bash
ls -1 "$CHECKPOINT_DIR"/*.md 2>/dev/null | sort -r | while read f; do
  echo "$(basename "$f")"
done
```

Display the list and stop.

### Step 4 — For `/context-restore` or `/context-restore <title-fragment>`

**Find the target file:**

Default (no fragment) — most recent:
```bash
TARGET=$(ls -1 "$CHECKPOINT_DIR"/*.md 2>/dev/null | sort -r | head -1)
```

With fragment — first match descending:
```bash
TARGET=$(ls -1 "$CHECKPOINT_DIR"/*.md 2>/dev/null | sort -r | grep "<fragment>" | head -1)
```

Replace `<fragment>` with the user-provided title fragment.

**Read and display the checkpoint:**

```bash
cat "$TARGET"
```

Then synthesize a structured summary from the checkpoint content:

```
CONTEXT RESTORED
Title:      <filename without YYYYMMDD-HHMMSS prefix and hex suffix>
Branch:     <branch from frontmatter>
Commit:     <commit from frontmatter>
Saved:      <timestamp from frontmatter>
Modified:   <files_modified from frontmatter> files at save time

Summary:    <Summary section content>

Remaining Work:
  - <each item from Remaining Work section>
```

**After displaying, offer:**

> Continue from here / View full checkpoint / List all checkpoints

---
name: context-save
description: "WHEN: You need to save working context — decisions made, git state, remaining work — so any future session can resume without losing state. Invoke when asked to 'save progress', 'save state', 'checkpoint', or before ending a long session."
type: flexible
version: 1.0.0
preamble-tier: 2
triggers:
  - "save progress"
  - "save state"
  - "checkpoint"
  - "save context"
allowed-tools:
  - Bash
  - Write
---

# context-save

Captures current working state to a structured checkpoint file. Read-only to the codebase — only writes to `~/.forge/`.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I'll remember where we were" | Context windows compact. Sessions end. Memory is not state. |
| "The git log shows enough" | Git log shows commits, not decisions-in-flight or remaining work. |
| "I'll just leave a note in the chat" | Chat is ephemeral. Checkpoints are persistent and structured. |

**If you are thinking any of the above, save now.**

## Invocation Modes

- `/context-save` — auto-title from branch + timestamp
- `/context-save <title>` — user-provided title
- `/context-save list` — list all checkpoints for this repo

## Workflow

### For `/context-save list`

```bash
SLUG=$(git remote get-url origin 2>/dev/null \
  | sed 's/.*[:/]\([^/]*\)\.git$/\1/' \
  | sed 's/.*[:/]\([^/]*\)$/\1/')
[ -z "$SLUG" ] && SLUG=$(basename "$(git rev-parse --show-toplevel)")

DIR="$HOME/.forge/projects/$SLUG/checkpoints"
if [ ! -d "$DIR" ] || [ -z "$(ls -A "$DIR" 2>/dev/null)" ]; then
  echo "No checkpoints found for $SLUG. Run /context-save first."
else
  ls -1 "$DIR"/*.md 2>/dev/null | sort -r | while read f; do
    echo "$(basename "$f")"
  done
fi
```

Display results to user. Stop.

### For `/context-save` and `/context-save <title>`

**Step 1 — Detect repo slug:**

```bash
SLUG=$(git remote get-url origin 2>/dev/null \
  | sed 's/.*[:/]\([^/]*\)\.git$/\1/' \
  | sed 's/.*[:/]\([^/]*\)$/\1/')
[ -z "$SLUG" ] && SLUG=$(basename "$(git rev-parse --show-toplevel)")
echo "Slug: $SLUG"
```

**Step 2 — Capture git state:**

```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)
COMMIT=$(git rev-parse HEAD)
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
FILETIMESTAMP=$(date -u +"%Y%m%d-%H%M%S")
MODIFIED=$(git status --short | wc -l | tr -d ' ')
GIT_LOG=$(git log --oneline -5)
echo "Branch: $BRANCH | Commit: $COMMIT | Modified: $MODIFIED files"
```

**Step 3 — Build title and filename:**

If the user provided a `<title>` argument, set `USER_TITLE` to it. If invoked as bare `/context-save`, leave `USER_TITLE` unset. Then run:

```bash
RAW_TITLE="${USER_TITLE:-$BRANCH}"
CLEAN_TITLE=$(echo "$RAW_TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g' | sed 's/--*/-/g' | cut -c1-40)
SUFFIX=$(openssl rand -hex 2)
FILENAME="${FILETIMESTAMP}-${CLEAN_TITLE}-${SUFFIX}.md"
```

**Step 4 — Create checkpoint directory:**

```bash
CHECKPOINT_DIR="$HOME/.forge/projects/$SLUG/checkpoints"
mkdir -p "$CHECKPOINT_DIR"
```

**Step 5 — Write checkpoint file:**

Synthesize the checkpoint from this session's context: what is being worked on, decisions made, remaining work, and any notes that would help a future session resume. Then write the file with this structure:

```
---
status: in-progress
branch: <BRANCH>
commit: <COMMIT>
timestamp: <TIMESTAMP>
files_modified: <MODIFIED>
---

## Summary

<1-2 sentences: what is being worked on>

## Decisions Made

- <decision 1>
- <decision 2>

## Remaining Work

- <item 1>
- <item 2>

## Notes

<any context that would help a future session resume>
```

Replace `<BRANCH>`, `<COMMIT>`, `<TIMESTAMP>`, `<MODIFIED>` with actual values. Fill all sections from session context — do not write placeholder text.

**Step 6 — Output confirmation:**

```
CONTEXT SAVED
Title:    <CLEAN_TITLE>
Branch:   <BRANCH>
Commit:   <COMMIT (first 8 chars)>
Path:     ~/.forge/projects/<SLUG>/checkpoints/<FILENAME>
Modified: <MODIFIED> files
```

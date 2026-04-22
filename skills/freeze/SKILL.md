---
name: freeze
description: "WHEN: You need to restrict Edit/Write/Bash operations to a single service directory during a debug or fix session — prevents accidental changes outside scope. Use before starting targeted self-heal."
type: flexible
version: 1.0.0
preamble-tier: 3
triggers:
  - "lock to directory"
  - "freeze scope"
  - "restrict to service"
  - "scope this fix"
allowed-tools:
  - Bash
  - Write
---

# freeze

Restricts file-write scope to one directory by writing a state file that `pre-tool-use.cjs` can read. Useful during `self-heal-systematic-debug` to prevent accidental edits outside the broken service.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I'll be careful not to edit other services" | Careful intent ≠ guaranteed scope. One mistyped path touches shared code. freeze enforces it. |
| "This is too much overhead for a quick fix" | Quick fixes that escape their intended scope create new bugs. freeze takes 5 seconds. |

**Freeze the scope. Fix the bug. Unfreeze.**

## Invocation Modes

- `/freeze <directory>` — restrict writes to this directory
- `/freeze status` — show current freeze state
- `/freeze off` — remove freeze

## Workflow

### For `/freeze status`

```bash
FREEZE_FILE="$HOME/.forge/.freeze"
if [ -f "$FREEZE_FILE" ]; then
  echo "FROZEN: $(cat "$FREEZE_FILE")"
else
  echo "No freeze active."
fi
```

### For `/freeze <directory>`

```bash
TARGET="<user-provided directory>"
FREEZE_FILE="$HOME/.forge/.freeze"
mkdir -p "$HOME/.forge"

# Resolve to absolute path
ABS_TARGET=$(cd "$TARGET" 2>/dev/null && pwd || echo "$TARGET")

echo "$ABS_TARGET" > "$FREEZE_FILE"
echo "SCOPE FROZEN"
echo "Directory: $ABS_TARGET"
echo "Effect:    Edit/Write/Bash commands outside this path will be flagged by pre-tool-use"
echo "Remove:    Run /freeze off when done"
```

### For `/freeze off`

```bash
FREEZE_FILE="$HOME/.forge/.freeze"
if [ -f "$FREEZE_FILE" ]; then
  PREV=$(cat "$FREEZE_FILE")
  rm "$FREEZE_FILE"
  echo "FREEZE REMOVED — scope was: $PREV"
else
  echo "No freeze was active."
fi
```

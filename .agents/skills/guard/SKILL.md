---
name: guard
description: "WHEN: You are about to run a potentially destructive command (rm, drop, truncate, force-push, reset) and want a warning gate before execution. Wraps freeze scope + destructive-command warnings."
type: flexible
version: 1.0.0
preamble-tier: 3
triggers:
  - "guard this command"
  - "dangerous command"
  - "destructive operation"
  - "confirm before running"
allowed-tools:
  - Bash
hooks:
  PreToolUse:
    - destructive-command-check
    - freeze-scope-check
---

# guard

Warning gate for destructive commands. Combines freeze scope enforcement with explicit confirmation for high-risk operations. A lightweight safety layer before any irreversible action.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I know what this command does" | Knowing what a command does is not the same as knowing what it will affect in context. |
| "I'll undo it if something goes wrong" | Some operations are irreversible: dropped tables, force-pushed commits, deleted branches. |

**Ask guard. Then act.**

## What guard warns on

| Command pattern | Risk |
|----------------|------|
| `rm -rf` | Irreversible file deletion |
| `git push --force` | Overwrites remote history |
| `git reset --hard` | Discards uncommitted work |
| `DROP TABLE` / `TRUNCATE` | Irreversible data loss |
| `git branch -D` | Deletes branch (may lose commits) |
| Any command touching outside freeze scope | Scope violation |

## Workflow

### For `/guard <command>`

**Step 1 — Check against destructive patterns:**

```bash
CMD="<user-provided command>"
FREEZE_FILE="$HOME/.forge/.freeze"
FROZEN_DIR=$(cat "$FREEZE_FILE" 2>/dev/null || echo "")

RISK=""
echo "$CMD" | grep -q "rm -rf" && RISK="IRREVERSIBLE FILE DELETION"
echo "$CMD" | grep -q "push --force\|push -f" && RISK="OVERWRITES REMOTE HISTORY"
echo "$CMD" | grep -q "reset --hard" && RISK="DISCARDS UNCOMMITTED WORK"
echo "$CMD" | grep -iq "DROP TABLE\|TRUNCATE" && RISK="IRREVERSIBLE DATA LOSS"
echo "$CMD" | grep -q "branch -D" && RISK="DELETES BRANCH"
```

**Step 2 — Check freeze scope violation:**

```bash
if [ -n "$FROZEN_DIR" ]; then
  # Check if command touches paths outside the frozen directory
  if echo "$CMD" | grep -qE "[./~][^ ]+" ; then
    PATHS=$(echo "$CMD" | grep -oE "[./~][^ ]+" | head -5)
    for p in $PATHS; do
      abs=$(cd "$(dirname "$p" 2>/dev/null)" 2>/dev/null && pwd || echo "$p")
      if ! echo "$abs" | grep -q "^$FROZEN_DIR"; then
        RISK="${RISK:+$RISK | }SCOPE VIOLATION (outside $FROZEN_DIR)"
        break
      fi
    done
  fi
fi
```

**Step 3 — Display warning and require confirmation:**

If any risk was detected:
```
GUARD WARNING
Command:  <CMD>
Risk:     <RISK>

Type 'confirm' to proceed, or press Ctrl+C to cancel.
```

Wait for user to type `confirm`. Only then output: `Guard cleared — proceed with: <CMD>`

If no risk detected: `Guard: no risks detected — safe to proceed with: <CMD>`

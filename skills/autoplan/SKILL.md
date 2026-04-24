---
name: autoplan
description: "WHEN: You are about to start a planning session and need to pre-load all brain context for the current task. Invoke before running tech-plan-write-per-project to have spec, QA CSV, and conductor stage ready."
type: flexible
version: 1.0.0
preamble-tier: 2
triggers:
  - "prepare to plan"
  - "load planning context"
  - "autoplan"
  - "start planning"
allowed-tools:
  - Bash
  - Read
---

# autoplan

Pre-loads planning context from the current brain task so `/tech-plan-write-per-project` can start immediately. Detects the current task, reads spec and QA CSV, identifies conductor stage. Read-only.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I'll find the files as I go" | Manual file hunting repeats every session. autoplan automates it once. |
| "I know where everything is" | Brain paths vary by task ID and product slug. Wrong paths cause incorrect plans. |

**Run autoplan. Then plan. Context first.**

## Workflow

### Step 1 — Locate brain and task

```bash
BRAIN_DIR="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}"
PRDS_DIR="$BRAIN_DIR/prds"

# Find most recent task dir by modification time
TASK_DIR=$(ls -td "$PRDS_DIR"/*/ 2>/dev/null | head -1)
TASK_ID=$(basename "$TASK_DIR")

echo "Brain: $BRAIN_DIR"
echo "Task:  $TASK_ID"
```

If no task dir found: output "No tasks found under $PRDS_DIR. Create a task first." and stop.

### Step 2 — Read conductor stage

```bash
CONDUCTOR_LOG="$TASK_DIR/conductor.log"
if [ -f "$CONDUCTOR_LOG" ]; then
  LAST_MARKER=$(grep -oE '\[P[0-9][^]]*\]' "$CONDUCTOR_LOG" | tail -1)
  echo "Stage: $LAST_MARKER"
else
  LAST_MARKER="[no log]"
  echo "Stage: not yet started"
fi
```

### Step 3 — Read spec path

```bash
SPEC="$TASK_DIR/shared-dev-spec.md"
if [ -f "$SPEC" ]; then
  echo "Spec:  $SPEC — found"
  # Extract first non-empty line after "## Overview" or first 3 lines of content
  SPEC_SUMMARY=$(grep -A 3 "^## Overview" "$SPEC" 2>/dev/null | grep -v "^##" | grep -v "^$" | head -2)
else
  echo "Spec:  NOT FOUND — spec must be written before planning"
fi
```

### Step 4 — Check QA CSV

```bash
QA_CSV=$(find "$TASK_DIR" -name "*.csv" 2>/dev/null | head -1)
if [ -n "$QA_CSV" ]; then
  QA_COUNT=$(grep -c "approved" "$QA_CSV" 2>/dev/null || echo "0")
  echo "QA CSV: $QA_CSV ($QA_COUNT approved rows)"
else
  echo "QA CSV: not found"
fi
```

### Step 5 — Read product context

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
PRODUCT_YAML="$REPO_ROOT/forge-product.yaml"
if [ -f "$PRODUCT_YAML" ]; then
  REPOS=$(grep "^  - " "$PRODUCT_YAML" 2>/dev/null | head -5 | sed 's/^  - //')
  echo "Repos: $REPOS"
else
  echo "Repos: forge-product.yaml not found"
fi
```

### Step 6 — Output context block

Display a structured summary:

```
AUTOPLAN CONTEXT
================
Task ID:  <TASK_ID>
Stage:    <LAST_MARKER>
Spec:     <SPEC path or "NOT FOUND">
QA CSV:   <QA_CSV path or "not found">
Repos:    <REPOS>

Spec summary:
<SPEC_SUMMARY>
```

Then output:

> Context loaded. Run `/tech-plan-write-per-project` to begin planning with the above context pre-loaded.

---
name: review-readiness
description: "WHEN: You are about to raise a PR and need to verify all gates have passed. Checks spec frozen, eval GREEN, QA CSV covered, brain committed, no WIP commits."
type: flexible
version: 1.0.0
preamble-tier: 2
triggers:
  - "ready to raise PR"
  - "pre-PR check"
  - "review readiness"
  - "is this ready to merge"
  - "check before PR"
allowed-tools:
  - Bash
---

# review-readiness

Pre-PR checklist that verifies all forge gates have passed before a PR is raised. Read-only — never modifies files.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I know eval passed" | "I know" is not a GREEN log entry. Check the brain file. |
| "The PR can be fixed after review" | Post-merge fixes are incidents. Gates exist to prevent them. |
| "Quick check is enough" | Missed gates are found in production. Run readiness. It takes 30 seconds. |

**Five checks. One verdict. Then raise the PR.**

## Workflow

Run all 5 checks. Collect pass/fail. Display at end.

### Check 1 — Spec frozen

```bash
BRAIN_DIR="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}"
TASK_DIR=$(ls -td "$BRAIN_DIR/prds"/*/ 2>/dev/null | head -1)
SPEC="$TASK_DIR/shared-dev-spec.md"

if [ -f "$SPEC" ] && grep -q "status: frozen" "$SPEC" 2>/dev/null; then
  echo "✓ Spec frozen"
else
  echo "✗ Spec frozen     — $SPEC missing or not frozen"
  echo "  Fix: ensure shared-dev-spec.md has 'status: frozen' in frontmatter"
fi
```

### Check 2 — Eval GREEN

```bash
EVAL_DIR="$TASK_DIR/eval"
CUTOFF=$(date -u -v-24H +"%Y%m%d%H%M%S" 2>/dev/null || date -u -d '24 hours ago' +"%Y%m%d%H%M%S" 2>/dev/null || echo "00000000000000")

GREEN_FILE=$(find "$EVAL_DIR" -name "*.md" -newer "$SPEC" 2>/dev/null | xargs grep -l "verdict: GREEN" 2>/dev/null | head -1)
if [ -n "$GREEN_FILE" ]; then
  echo "✓ Eval GREEN      — $GREEN_FILE"
else
  echo "✗ Eval GREEN      — no GREEN verdict found in $EVAL_DIR"
  echo "  Fix: run /forge-eval-gate and ensure eval passes"
fi
```

### Check 3 — QA CSV covered

```bash
QA_CSV=$(find "$TASK_DIR" -name "*.csv" 2>/dev/null | head -1)
if [ -z "$QA_CSV" ]; then
  echo "✓ QA CSV          — no CSV found (skip)"
else
  APPROVED=$(grep -c "approved" "$QA_CSV" 2>/dev/null || echo "0")
  if [ "$APPROVED" -eq 0 ]; then
    echo "✓ QA CSV          — no approved rows"
  else
    # Check if eval dir has files referencing journey IDs
    EVAL_SCENARIOS=$(find "$EVAL_DIR" -name "*.yaml" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$EVAL_SCENARIOS" -gt 0 ]; then
      echo "✓ QA CSV          — $APPROVED approved rows, $EVAL_SCENARIOS eval scenarios present"
    else
      echo "✗ QA CSV          — $APPROVED approved rows but no eval scenarios found"
      echo "  Fix: run /forge-eval-gate QA CSV traceability check"
    fi
  fi
fi
```

### Check 4 — Brain decisions committed

```bash
cd "$(git rev-parse --show-toplevel)" 2>/dev/null
BRAIN_UNTRACKED=$(git status --short "$BRAIN_DIR" 2>/dev/null | grep -v "^$" | wc -l | tr -d ' ')
if [ "$BRAIN_UNTRACKED" -eq 0 ]; then
  echo "✓ Brain committed  — no untracked brain files"
else
  echo "✗ Brain committed  — $BRAIN_UNTRACKED brain file(s) not committed"
  echo "  Fix: git add $BRAIN_DIR && git commit -m 'brain: commit decisions'"
fi
```

### Check 5 — No WIP commits

```bash
WIP_COUNT=$(git log --oneline -10 2>/dev/null | grep -ci "^[a-f0-9]* wip" || echo "0")
if [ "$WIP_COUNT" -eq 0 ]; then
  echo "✓ No WIP commits"
else
  echo "✗ WIP commits      — $WIP_COUNT WIP commit(s) in last 10"
  echo "  Fix: squash or amend WIP commits before raising PR"
fi
```

### Final verdict

Count passes and failures. Output:

```
================
```

If all 5 pass: `READY — All gates passed. Safe to raise PR.`
If any fail: `NOT READY — Fix N issue(s) above before raising PR.`

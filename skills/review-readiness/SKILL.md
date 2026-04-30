---
name: review-readiness
description: "WHEN: You are about to raise a PR and need to verify all gates have passed. Checks spec frozen, eval GREEN, QA CSV covered, brain committed, no WIP commits."
type: flexible
version: 1.0.8
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

**Six required checks (check 6 can fail the run for user-visible terminology risk). One verdict. Then raise the PR.**

**Shell:** Every check block re-initializes `BRAIN_DIR` / `TASK_DIR` where needed so a single block can be run **standalone** (not only after a prior check in the same shell).

## Workflow

Run all 6 checks in order (same `TASK_DIR` as below). Count **failures** (lines starting with `✗`). Check 6 uses **`terminology_risk`** in `terminology.md` frontmatter: `internal` + `open_doubts: pending` → **advisory only**; `user_visible` (default) + `open_doubts: pending` → **NOT READY** (user-visible copy must not ship with unresolved doubts). See [docs/terminology-review.md](../../docs/terminology-review.md) and [docs/templates/terminology.md](../../docs/templates/terminology.md).

### Check 1 — Spec frozen

```bash
BRAIN_DIR="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}"
TASK_DIR="${TASK_DIR:-$(ls -td "$BRAIN_DIR/prds"/*/ 2>/dev/null | head -1)}"
SPEC="${TASK_DIR%/}/shared-dev-spec.md"

if [ -f "$SPEC" ] && grep -q "status: frozen" "$SPEC" 2>/dev/null; then
  echo "✓ Spec frozen"
else
  echo "✗ Spec frozen     — $SPEC missing or not frozen"
  echo "  Fix: ensure shared-dev-spec.md has 'status: frozen' in frontmatter"
fi
```

### Check 2 — Eval GREEN

```bash
BRAIN_DIR="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}"
TASK_DIR="${TASK_DIR:-$(ls -td "$BRAIN_DIR/prds"/*/ 2>/dev/null | head -1)}"
SPEC="${TASK_DIR%/}/shared-dev-spec.md"
EVAL_DIR="${TASK_DIR%/}/eval"
# Newer than frozen spec mtime: eval run must post-date the locked spec, not a calendar window.
if [ ! -d "$EVAL_DIR" ] || [ ! -f "$SPEC" ]; then
  echo "✗ Eval GREEN      — EVAL_DIR or spec missing (check TASK_DIR / run Check 1)"
  echo "  Fix: ensure $EVAL_DIR and frozen $SPEC exist"
else
GREEN_FILE=$(find "$EVAL_DIR" -name "*.md" -newer "$SPEC" 2>/dev/null | xargs grep -l "verdict: GREEN" 2>/dev/null | head -1)
  if [ -n "$GREEN_FILE" ]; then
    echo "✓ Eval GREEN      — $GREEN_FILE"
  else
    echo "✗ Eval GREEN      — no GREEN verdict found in $EVAL_DIR"
    echo "  Fix: run /forge-eval-gate and ensure eval passes"
  fi
fi
```

### Check 3 — QA CSV + State 4b + eval

Authoritative **human CSV approval** is logged in **`conductor.log`**, not a substring in the CSV body (`[P4.0-QA-CSV]` … `approved=yes`, same as `GATE_PATTERNS.QA_CSV` in `prompt-submit-gates.cjs`).

```bash
BRAIN_DIR="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}"
TASK_DIR="${TASK_DIR:-$(ls -td "$BRAIN_DIR/prds"/*/ 2>/dev/null | head -1)}"
EVAL_DIR="${TASK_DIR%/}/eval"
CONDUCTOR_LOG="${TASK_DIR%/}/conductor.log"
QA_CSV=$(find "$TASK_DIR" -name "*.csv" 2>/dev/null | head -1)
if [ -z "$QA_CSV" ] || [ ! -f "$QA_CSV" ]; then
  echo "✓ QA CSV          — no manual CSV in task (skip)"
else
  P40=0
  if [ -f "$CONDUCTOR_LOG" ] && grep -aE '\[P4\.0-QA-CSV\].*approved=yes' "$CONDUCTOR_LOG" >/dev/null 2>&1; then
    P40=1
  fi
  if [ "$P40" -eq 0 ]; then
    echo "✗ QA CSV          — manual CSV at $QA_CSV but $CONDUCTOR_LOG has no [P4.0-QA-CSV] … approved=yes (State 4b)"
    echo "  Fix: complete qa-manual approval and log, or use documented waiver; see skills/qa-manual-test-cases-from-prd"
  else
    EVAL_SCENARIOS=$(find "$EVAL_DIR" -name "*.yaml" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$EVAL_SCENARIOS" -gt 0 ]; then
      echo "✓ QA CSV          — P4.0 approved=yes in conductor.log, $EVAL_SCENARIOS eval scenario(s) under $EVAL_DIR"
    else
      echo "✗ QA CSV          — P4.0 passed but no eval scenarios under $EVAL_DIR"
      echo "  Fix: run /forge-eval-gate; align eval YAML to CSV ids per qa-write-scenarios"
    fi
  fi
fi
```

### Check 4 — Brain decisions committed

```bash
BRAIN_DIR="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}"
# Brain may be its own git repo. Use -e: linked worktrees use a .git *file* (gitdir: …), not always a .git directory.
if [ -e "$BRAIN_DIR/.git" ]; then
  BRAIN_UNTRACKED=$(git -C "$BRAIN_DIR" status --short 2>/dev/null | grep -v "^$" | wc -l | tr -d ' ')
else
  cd "$(git rev-parse --show-toplevel)" 2>/dev/null
  BRAIN_UNTRACKED=$(git status --short "$BRAIN_DIR" 2>/dev/null | grep -v "^$" | wc -l | tr -d ' ')
fi
if [ "$BRAIN_UNTRACKED" -eq 0 ]; then
  echo "✓ Brain committed  — no uncommitted changes under brain (short status empty)"
else
  echo "✗ Brain committed  — $BRAIN_UNTRACKED brain path(s) not clean"
  echo "  Fix: git -C \"$BRAIN_DIR\" add <paths-from-status-above> && git -C \"$BRAIN_DIR\" commit -m 'brain: commit decisions' (stage only what you intend; never blind add -A in a sensitive tree)"
fi
```

### Check 5 — No WIP commits

WIP is read from **the repo for your current `pwd`** (or run `cd` to the product repo you are about to PR before this block). If your PR is in a worktree, `cd` there first.

```bash
WIP_COUNT=$(git log --oneline -10 2>/dev/null | grep -ci "^[a-f0-9]* wip" || echo "0")
if [ "$WIP_COUNT" -eq 0 ]; then
  echo "✓ No WIP commits"
else
  echo "✗ WIP commits      — $WIP_COUNT WIP commit(s) in last 10"
  echo "  Fix: squash or amend WIP commits before raising PR"
fi
```

### Check 6 — Product terminology (blocking when user-visible + pending)

```bash
BRAIN_DIR="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}"
TASK_DIR="${TASK_DIR:-$(ls -td "$BRAIN_DIR/prds"/*/ 2>/dev/null | head -1)}"
# Normalize: works when TASK_DIR is exported without a trailing slash (e.g. /path/to/task).
TERM="${TASK_DIR%/}/terminology.md"

if [ ! -f "$TERM" ]; then
  echo "✓ Terminology   — no terminology.md (skip)"
else
  # Strip optional YAML double/single quotes from scalar values
  OPEN=$(awk '/^open_doubts:/{v=$0; sub(/^open_doubts:[ \t]*/,"",v); gsub(/^\047|\047$|^\042|\042$|^[ \t]+|[ \t]+$/,"",v); print tolower(v); exit}' "$TERM" 2>/dev/null || true)
  RISK=$(awk '/^terminology_risk:/{v=$0; sub(/^terminology_risk:[ \t]*/,"",v); gsub(/^\047|\047$|^\042|\042$|^[ \t]+|[ \t]+$/,"",v); print tolower(v); exit}' "$TERM" 2>/dev/null || true)
  if [ "$OPEN" = "none" ] || [ -z "$OPEN" ]; then
    echo "✓ Terminology   — open_doubts none (or empty)"
  elif [ "$OPEN" = "pending" ]; then
    if echo "$RISK" | grep -q 'internal'; then
      echo "△ Terminology  — open_doubts pending, terminology_risk: internal (advisory — confirm acceptable)"
    else
      echo "✗ Terminology   — open_doubts pending (defaults to user_visible risk) — NOT READY"
      echo "  Fix: lock terminology.md, set open_doubts: none, or set terminology_risk: internal if doubts are implementation-only; see docs/terminology-review.md"
    fi
  else
    echo "△ Terminology  — open_doubts=$OPEN (review)"
  fi
fi
```

If **`open_doubts: pending`** and frontmatter has **`terminology_risk: internal`**, the line starts with `△` — count as **pass with warning** (do not add to **failure** count). If line starts with `✗`, that is a **failure**.

### Final verdict

Count `✗` lines (excluding advisory `△` only if your policy counts warnings separately). Output:

```
================
```

If checks **1–6** pass (no `✗` in checks 1–5; check 6 no `✗` line, `△` OK): `READY — All gates passed. Safe to raise PR.`
If any check shows **`✗`**: `NOT READY — Fix N issue(s) above before raising PR.`

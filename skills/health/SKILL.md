---
name: health
description: "WHEN: You need to verify the forge environment is correctly set up — hooks wired, skills symlinked, brain accessible, canary set. Invoke when setup seems broken or as a first-run check."
type: flexible
version: 1.0.0
preamble-tier: 2
triggers:
  - "check forge health"
  - "is forge set up"
  - "diagnose forge"
  - "health check"
allowed-tools:
  - Bash
---

# health

Diagnoses whether the local forge environment is functional. Read-only — never modifies any file.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I'll just check manually as I go" | Manual checks miss interactions. A single health run catches all config issues at once. |
| "It was working before, skip the check" | Environment state changes: hooks can be unregistered, symlinks can break, canary can expire. |

**Run health first. Debug second.**

## Invocation Modes

- `/health` — full check (all 7 env items)
- `/health quick` — fast subset: canary + hooks only
- `/health quality` — weighted 0-10 code quality score (type safety + lint + tests + dead code + shell)

## Workflow

### For `/health quick`

Run only checks 2, 4, and 5 below. Report a 3-item result.

### For `/health` (full check)

Run each check in order. Collect pass/fail per item. Display all at once at the end.

**Check 1 — Brain directory:**

```bash
BRAIN_DIR="${FORGE_BRAIN_PATH:-$HOME/forge/brain}"
if [ -d "$BRAIN_DIR" ] && [ "$(ls -A "$BRAIN_DIR" 2>/dev/null)" ]; then
  echo "✓ Brain directory     $BRAIN_DIR — accessible"
else
  echo "✗ Brain directory     $BRAIN_DIR — NOT FOUND or empty"
  echo "  Fix: mkdir -p $BRAIN_DIR"
fi
```

**Check 2 — Canary file:**

```bash
CANARY="$HOME/.forge/.canary"
if [ -f "$CANARY" ] && [ -s "$CANARY" ]; then
  echo "✓ Canary file         $CANARY — set"
else
  echo "✗ Canary file         $CANARY — missing or empty"
  echo "  Fix: restart your Claude Code session to regenerate the canary"
fi
```

**Check 3 — Skills symlink:**

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -L "$REPO_ROOT/.claude/skills" ]; then
  TARGET=$(readlink "$REPO_ROOT/.claude/skills")
  echo "✓ Skills symlink      .claude/skills → $TARGET"
else
  echo "✗ Skills symlink      .claude/skills — not a symlink"
  echo "  Fix: ln -s ../../skills $REPO_ROOT/.claude/skills"
fi
```

**Check 4 — Session-start hook:**

```bash
HOOK="$REPO_ROOT/.claude/hooks/session-start.cjs"
if [ -f "$HOOK" ]; then
  echo "✓ Session-start hook  .claude/hooks/session-start.cjs — present"
else
  echo "✗ Session-start hook  .claude/hooks/session-start.cjs — NOT FOUND"
  echo "  Fix: verify .claude/hooks/ directory contains session-start.cjs"
fi
```

**Check 5 — Pre-tool-use hook:**

```bash
HOOK2="$REPO_ROOT/.claude/hooks/pre-tool-use.cjs"
if [ -f "$HOOK2" ]; then
  echo "✓ Pre-tool-use hook   .claude/hooks/pre-tool-use.cjs — present"
else
  echo "✗ Pre-tool-use hook   .claude/hooks/pre-tool-use.cjs — NOT FOUND"
  echo "  Fix: verify .claude/hooks/ directory contains pre-tool-use.cjs"
fi
```

**Check 6 — using-forge skill:**

```bash
SKILL="$REPO_ROOT/skills/using-forge/SKILL.md"
if [ -f "$SKILL" ]; then
  echo "✓ using-forge skill   skills/using-forge/SKILL.md — present"
else
  echo "✗ using-forge skill   skills/using-forge/SKILL.md — NOT FOUND"
  echo "  Fix: verify skills/ directory is intact"
fi
```

**Check 7 — Forge product config:**

```bash
CONFIG="$REPO_ROOT/forge-product.yaml"
if [ -f "$CONFIG" ]; then
  echo "✓ Forge product cfg   forge-product.yaml — present"
else
  echo "✗ Forge product cfg   forge-product.yaml — NOT FOUND"
  echo "  Fix: copy from seed-product/ or create from template"
fi
```

**Final summary:**

Count passes and failures across all 7 checks. Output:

```
==================
Status: X/7 checks passed.
```

If all pass: append `All checks passed. Forge environment is healthy.`
If any fail: append `Fix N issue(s) above before proceeding.`

---

## For `/health quality`

Compute a weighted 0-10 code quality score. Auto-detects which tools are installed; skips missing tools gracefully (excluded weight redistributed proportionally). Read-only — never modifies files.

### Weights

| Check | Weight | Tool (auto-detected in order) |
|---|---|---|
| Type safety | 25% | `tsc --noEmit`, `mypy`, `cargo check`, `go build ./...` |
| Lint | 20% | `biome check`, `eslint`, `ruff check`, `golangci-lint` |
| Tests | 30% | `npm test`, `pytest`, `cargo test`, `go test ./...` |
| Dead code | 15% | `knip`, `ts-prune`, `vulture` |
| Shell | 10% | `shellcheck` on `*.sh` files |

### Scoring formula

Each check returns a raw score 0-10 based on error count from the tool's exit/output:

| Error count | Score |
|---|---|
| 0 | 10.0 |
| 1–2 | 8.0 |
| 3–5 | 6.0 |
| 6–10 | 4.0 |
| 11–20 | 2.0 |
| > 20 | 0.0 |
| tool not found / skipped | excluded from weighted average |

**Tests** use pass rate instead: `(passed / total) * 10`. Parse the summary line from the test runner output (e.g. `47 passed, 5 failed` → `47/52 * 10 = 9.0`). If the runner exits 0 with no summary, score = 10; if it exits non-zero with no count, score = 0.

**Shell** uses shellcheck issue count via the same error-count table above.

```
final_score = sum(raw_score[i] * weight[i]  for each detected tool)
            / sum(weight[i]                  for each detected tool)
```

All weights are renormalized across detected tools so the score is always out of 10, even when some tools are absent.

### Workflow

**Step 1 — Detect available tools:**

```bash
# Type safety
command -v tsc   >/dev/null 2>&1 && echo "tsc"
command -v mypy  >/dev/null 2>&1 && echo "mypy"
command -v cargo >/dev/null 2>&1 && [ -f Cargo.toml ] && echo "cargo"
command -v go    >/dev/null 2>&1 && [ -f go.mod ]    && echo "go"

# Lint
command -v biome         >/dev/null 2>&1 && echo "biome"
command -v eslint        >/dev/null 2>&1 && echo "eslint"
command -v ruff          >/dev/null 2>&1 && echo "ruff"

# Tests
[ -f package.json ] && command -v npm  >/dev/null 2>&1 && echo "npm-test"
command -v pytest        >/dev/null 2>&1 && echo "pytest"
command -v cargo         >/dev/null 2>&1 && [ -f Cargo.toml ] && echo "cargo-test"
command -v go            >/dev/null 2>&1 && [ -f go.mod ]    && echo "go-test"

# Dead code
command -v knip    >/dev/null 2>&1 && echo "knip"
command -v ts-prune >/dev/null 2>&1 && echo "ts-prune"
command -v vulture >/dev/null 2>&1 && echo "vulture"

# Shell
command -v shellcheck >/dev/null 2>&1 && echo "shellcheck"
```

**Step 2 — Run each detected tool, capture exit code + error count**

Run each detected tool and extract the error/issue count from its output. Do not print full tool output unless the final score is below 6.0.

```bash
# Type safety examples (pick first that matches your stack)
tsc --noEmit 2>&1 | tail -1              # "Found 3 errors."  → count = 3
mypy . --ignore-missing-imports 2>&1 | grep "^Found"   # "Found 2 errors" → count = 2
cargo check 2>&1 | grep "^error" | wc -l
go build ./... 2>&1 | grep "^.*\.go:" | wc -l

# Lint examples
biome check . 2>&1 | grep "Found" | grep -oP '\d+ error'
eslint . --format=compact 2>&1 | tail -1  # "2 problems (2 errors, 0 warnings)"
ruff check . 2>&1 | tail -1              # "Found 4 errors."

# Test examples — capture passed/total
npm test -- --reporter=json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('numPassedTests',0), d.get('numTotalTests',0))"
pytest --tb=no -q 2>&1 | tail -2         # "42 passed, 3 failed"
cargo test 2>&1 | grep "test result"     # "test result: ok. 42 passed; 0 failed"

# Dead code examples
knip 2>&1 | grep -c "Unused"
ts-prune 2>&1 | wc -l

# Shell
shellcheck **/*.sh 2>&1 | grep -c "^In "  # count of files with issues
```

Map each result to a score using the lookup table in the Scoring section above.

**Step 3 — Compute and display score**

```
===========================
Code Quality Score: 7.4/10
===========================
  Type safety (25%)   9.0  tsc: 2 errors
  Lint        (20%)   8.5  eslint: 3 warnings (0 errors)
  Tests       (30%)   6.8  42/62 passed
  Dead code   (15%)   7.0  knip: 4 unused exports
  Shell       (10%)  10.0  shellcheck: no issues
  ─────────────────────
  Weighted:           7.4  ← YELLOW (below 8.0)
```

Tiers: **GREEN ≥ 8.0** | **YELLOW 6.0-7.9** | **RED < 6.0**

**Step 4 — Persist to JSONL history**

Fill in each field with the computed values from Step 3, then append:

```bash
LEARN_DIR="${FORGE_BRAIN_PATH:-$HOME/forge/brain}/quality-history"
mkdir -p "$LEARN_DIR"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
# Replace SCORE_*, TIER with the actual computed values before running
printf '{"timestamp":"%s","commit":"%s","score":SCORE_FINAL,"tier":"TIER","type_safety":SCORE_TS,"lint":SCORE_LINT,"tests":SCORE_TESTS,"dead_code":SCORE_DC,"shell":SCORE_SH}\n' \
  "$TIMESTAMP" "$COMMIT" >> "$LEARN_DIR/quality-scores.jsonl"
```

**Step 5 — Show trend (last 5 runs)**

```bash
LEARN_DIR="${FORGE_BRAIN_PATH:-$HOME/forge/brain}/quality-history"
tail -5 "$LEARN_DIR/quality-scores.jsonl" 2>/dev/null \
  | python3 -c "import sys,json; [print(f\"{r['timestamp'][:10]}  {r['commit']}  {r['score']:.1f}/10  {r['tier']}\") for r in (json.loads(l) for l in sys.stdin)]"
```

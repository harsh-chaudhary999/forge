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

- `/health` — full check (all 7 items)
- `/health quick` — fast subset: canary + hooks only

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

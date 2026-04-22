---
name: learn
description: "WHEN: You've discovered something worth capturing — a pattern, a gotcha, a process improvement — and want to preserve it so future sessions can benefit. Invoke at end of session or when asked to 'save this insight', 'capture learning', 'log lesson'."
type: flexible
version: 1.0.0
preamble-tier: 2
triggers:
  - "what did we learn"
  - "capture learning"
  - "save this insight"
  - "log lesson"
  - "remember this for next time"
allowed-tools:
  - Bash
  - Write
---

# learn

Writes session learnings to brain so future sessions benefit. Unlike `brain-write` (formal decisions), `learn` captures soft knowledge: patterns, gotchas, process improvements.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I'll remember this next time" | Context windows reset. Sessions end. Knowledge not written is knowledge lost. |
| "The git commit message has this" | Commit messages describe what changed, not what you learned about the system. |
| "brain-write is for this" | brain-write is for decisions. learn is for insights. Different audiences, different formats. |

**Write it now. The next session won't have this context.**

## Invocation Modes

- `/learn` — interactive: asks for category and insight
- `/learn "pattern: always check X before Y on this service"` — inline, no prompts

## Categories

| Category | When to use |
|----------|------------|
| `pattern` | A reusable approach discovered (e.g., "always flush cache before running eval") |
| `gotcha` | A non-obvious trap (e.g., "Kafka consumer group IDs must be unique per eval run") |
| `process` | A workflow improvement (e.g., "run eval with --verbose when diagnosing YELLOW") |

## Workflow

### Step 1 — Determine category and insight

If invoked as bare `/learn`, ask the user:
> "What's the category? (pattern / gotcha / process) And what's the insight in one sentence?"

If invoked as `/learn "<category>: <insight>"`, parse directly — no prompting.

### Step 2 — Detect session context

```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
FILEDATE=$(date -u +"%Y%m%d")
```

### Step 3 — Generate slug from insight

```bash
RAW="${INSIGHT}"
SLUG=$(echo "$RAW" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g' | sed 's/--*/-/g' | cut -c1-40)
```

### Step 4 — Write learning to brain

```bash
BRAIN_DIR="${FORGE_BRAIN_PATH:-$HOME/forge/brain}/learnings"
mkdir -p "$BRAIN_DIR"
FILENAME="${FILEDATE}-${SLUG}.md"
```

Write `$BRAIN_DIR/$FILENAME` with this structure:

```markdown
---
category: <pattern|gotcha|process>
date: <ISO8601>
session: <BRANCH>
---

# <Insight as a short title>

<The learning in 1-3 sentences. Concrete and specific — not "be careful" but exactly what to do or avoid.>

## Context

<What situation surfaced this learning — 1-2 sentences.>

## Apply When

<When a future session should recall this: what scenario triggers it.>
```

Fill all sections with actual content. Do not write placeholder text.

### Step 5 — Commit to git

```bash
cd "$(git rev-parse --show-toplevel)"
git add "$BRAIN_DIR/$FILENAME"
git commit -m "learn($CATEGORY): $SLUG"
```

### Step 6 — Output confirmation

```
LEARNING SAVED
Category: <category>
File:     ~/forge/brain/learnings/<filename>
Branch:   <branch>
```

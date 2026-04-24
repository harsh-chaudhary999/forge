---
name: retro
description: "WHEN: You need a weekly engineering retrospective — git log analysis, features shipped, contributors, test ratio, trend comparison vs. prior period. Invoke when asked for 'retro', 'weekly summary', 'what did we ship this week'."
type: flexible
version: 1.0.0
preamble-tier: 2
triggers:
  - "retro"
  - "weekly summary"
  - "what did we ship this week"
  - "engineering retrospective"
allowed-tools:
  - Bash
  - Write
---

# retro

Weekly engineering retrospective from git log. Analyzes commits, contributors, test ratio, and trends. Saves to brain.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I can summarize this from memory" | Memory is selective. git log is not. Anchor every claim in actual commits. |
| "Skip the trend comparison" | A retro without trend is a snapshot. Trend reveals whether velocity is improving or declining. |

**Every claim must cite an actual commit hash.**

## Invocation Modes

- `/retro` — current week (last 7 days)
- `/retro <N>` — last N days
- `/retro --compare` — current week vs. prior week

## Workflow

### Step 1 — Collect commits

```bash
DAYS="${RETRO_DAYS:-7}"
SINCE=$(date -u -v-${DAYS}d +"%Y-%m-%d" 2>/dev/null || date -u -d "${DAYS} days ago" +"%Y-%m-%d" 2>/dev/null || echo "7 days ago")
REPO_ROOT=$(git rev-parse --show-toplevel)
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# All commits in period
COMMITS=$(git log --oneline --since="$SINCE" 2>/dev/null)
COMMIT_COUNT=$(echo "$COMMITS" | grep -c "." 2>/dev/null || echo 0)

# Commits by author
AUTHORS=$(git log --format="%an" --since="$SINCE" 2>/dev/null | sort | uniq -c | sort -rn)

# Test-related commits (commits touching test files)
TEST_COMMITS=$(git log --oneline --since="$SINCE" -- "*.test.*" "*.spec.*" "tests/" "test/" 2>/dev/null | wc -l | tr -d ' ')

# Feature/fix/chore breakdown
FEAT_COUNT=$(echo "$COMMITS" | grep -c "^[a-f0-9]* feat" || echo 0)
FIX_COUNT=$(echo "$COMMITS" | grep -c "^[a-f0-9]* fix" || echo 0)
CHORE_COUNT=$(echo "$COMMITS" | grep -c "^[a-f0-9]* chore\|^[a-f0-9]* docs\|^[a-f0-9]* refactor" || echo 0)

echo "Period: last $DAYS days (since $SINCE)"
echo "Total commits: $COMMIT_COUNT"
echo "Features: $FEAT_COUNT | Fixes: $FIX_COUNT | Other: $CHORE_COUNT"
echo "Test commits: $TEST_COMMITS"
echo "Authors:"
echo "$AUTHORS"
```

### Step 2 — Session detection (45-min gap heuristic)

```bash
# Count distinct work sessions (gaps > 45 min between commits = new session)
git log --format="%at" --since="$SINCE" 2>/dev/null | sort -n | awk '
  BEGIN { sessions=1; prev=0 }
  { if (prev > 0 && ($1 - prev) > 2700) sessions++; prev=$1 }
  END { print sessions " sessions" }
'
```

### Step 3 — Prior period comparison (if --compare)

```bash
PRIOR_SINCE=$(date -u -v-$((DAYS*2))d +"%Y-%m-%d" 2>/dev/null || date -u -d "$((DAYS*2)) days ago" +"%Y-%m-%d" 2>/dev/null)
PRIOR_UNTIL=$(date -u -v-${DAYS}d +"%Y-%m-%d" 2>/dev/null || date -u -d "${DAYS} days ago" +"%Y-%m-%d" 2>/dev/null)
PRIOR_COUNT=$(git log --oneline --since="$PRIOR_SINCE" --until="$PRIOR_UNTIL" 2>/dev/null | wc -l | tr -d ' ')
DELTA=$((COMMIT_COUNT - PRIOR_COUNT))
TREND=""
if [ "$DELTA" -gt 0 ]; then TREND="↑ +$DELTA vs prior period"
elif [ "$DELTA" -lt 0 ]; then TREND="↓ $DELTA vs prior period"
else TREND="→ same as prior period"
fi
echo "Prior period commits: $PRIOR_COUNT | Trend: $TREND"
```

### Step 4 — Write to brain

```bash
BRAIN_DIR="${FORGE_BRAIN:-${FORGE_BRAIN_PATH:-$HOME/forge/brain}}/retros"
mkdir -p "$BRAIN_DIR"
FILEDATE=$(date -u +"%Y%m%d")
RESULT_FILE="$BRAIN_DIR/${FILEDATE}-retro.md"
```

Write the retro to `$RESULT_FILE` with this structure:

```markdown
---
period_days: <DAYS>
since: <SINCE>
branch: <BRANCH>
total_commits: <COMMIT_COUNT>
features: <FEAT_COUNT>
fixes: <FIX_COUNT>
test_commits: <TEST_COMMITS>
---

# Weekly Retro — <SINCE> to today

## Commits

<COMMITS — each line as bullet with hash and message>

## Contributors

<AUTHORS table>

## Breakdown

- Features: <FEAT_COUNT>
- Fixes: <FIX_COUNT>
- Other: <CHORE_COUNT>
- Test commits: <TEST_COMMITS>
- Work sessions: <session count>

## Trend

<TREND line — only if --compare was used>
```

### Step 5 — Commit and output summary

```bash
cd "$REPO_ROOT"
git add "$RESULT_FILE"
git commit -m "retro: weekly summary $(date -u +%Y-%m-%d)"
```

Output:
```
RETRO
Period:  last <DAYS> days
Commits: <COMMIT_COUNT> (<FEAT_COUNT> feat, <FIX_COUNT> fix)
Tests:   <TEST_COMMITS> test commits
Authors: <count> contributor(s)
File:    ~/forge/brain/retros/<filename>
```

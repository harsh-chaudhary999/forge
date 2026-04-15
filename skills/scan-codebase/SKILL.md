---
name: scan-codebase
description: "WHEN: You need to map an existing codebase into the Forge brain — building an Obsidian-format knowledge graph of module relationships, architecture patterns, API surface, and documented edge cases. Invoked automatically after /workspace init and manually via /scan."
type: rigid
requires: [brain-write]
---

# Scan Codebase

Map an existing repository into the Forge brain as an interconnected Obsidian knowledge graph.
Produces `~/forge/brain/products/<slug>/codebase/` — readable by humans, queryable by agents.

---

## Anti-Pattern Preamble

**Stop. Read this before touching any file.**

### Anti-Pattern 1: "Just read all the source files — that's how you understand a codebase"

**Why This Fails:** Reading every file burns 50-200K tokens on boilerplate, tests, generated code, and third-party vendored files. 30-40% of what you read will be noise. The structural relationships you need (who imports whom, what the entry points are, which files are hubs) are available from import lines and filenames alone — zero tokens required.

**Enforcement:**
- MUST run Phase 1 (grep/find) before reading any source file
- MUST identify hub files via incoming-reference count before selecting what to read
- MUST exclude: `node_modules/`, `vendor/`, `dist/`, `build/`, `__pycache__/`, `.git/`, `*.generated.*`, `*.min.js`, `*.lock`
- MUST NOT read more than 100 lines from any single non-README file
- MUST NOT read test files unless they are the only documentation for an API

### Anti-Pattern 2: "I'll scan the entire codebase at once and produce a single summary"

**Why This Fails:** Monolithic summaries are high-token, low-recall. When an agent later needs to know "what does the auth module export?", searching a 5000-word summary is slower and less reliable than reading `brain/products/<slug>/codebase/modules/auth.md`. The output must be navigable files, not a wall of text.

**Enforcement:**
- MUST produce separate `.md` files per module — not a single summary document
- MUST use `[[wikilinks]]` to cross-reference between brain files
- MUST write each file to `~/forge/brain/products/<slug>/codebase/` individually
- MUST git-commit after each project role is scanned (backend, web, app) — not after all

### Anti-Pattern 3: "I'll infer architecture patterns without checking the actual dependency graph"

**Why This Fails:** Pattern detection from file names alone is wrong 40% of the time. A file named `UserService.ts` in a monolith does not imply service architecture. The actual import graph — which files import which — is the ground truth for pattern detection.

**Enforcement:**
- MUST build import adjacency before classifying patterns
- MUST confirm pattern with at least 3 structural signals (not just naming conventions)
- MUST label uncertain patterns as `likely-<pattern> (unconfirmed)` in output
- MUST NOT write patterns.md until after the import graph is built

### Anti-Pattern 4: "Tests are noise — skip them"

**Why This Fails:** Test files are often the only documentation for edge cases and expected failure modes. A `test_login_with_expired_token.py` tells you more about auth edge cases than any docstring. Test file names and their `describe`/`test` strings are high-signal, zero-token gotcha sources.

**Enforcement:**
- MUST scan test file names and top-level describe/test strings
- MUST extract `it("should fail when...")` and `test("edge case:...")` strings into `gotchas.md`
- MAY skip test file bodies — names and test strings only
- MUST NOT skip entire test directories

### Anti-Pattern 5: "I've scanned this before — I'll use my memory instead of re-running"

**Why This Fails:** Codebases change. A brain scan is a snapshot. Using stale scan data leads agents to reference deleted modules, outdated APIs, or patterns that were refactored out. Every scan must produce a new timestamped snapshot.

**Enforcement:**
- MUST write `SCAN.json` with timestamp, commit SHA, and file count on every run
- MUST include `last-scanned:` field in `index.md` header
- MUST NOT reuse a scan older than 7 days without re-running Phase 1 to check for new files
- MUST overwrite existing codebase brain files on re-scan (not append)

---

## Overview

Scan produces a structured knowledge graph of a codebase, stored in the Forge brain as navigable Obsidian markdown. It runs in 4 phases, ordered by token cost (cheapest first):

```
Phase 1 — Structural map     (bash only, 0 tokens)
Phase 2 — Hub detection      (bash only, 0 tokens)
Phase 3 — Semantic enrichment (targeted reads, low tokens)
Phase 4 — Brain write        (structured output, low tokens)
```

Output goes to: `~/forge/brain/products/<slug>/codebase/`

```
codebase/
  index.md              # Overview: entry points, architecture style, stats, last scanned
  SCAN.json             # Metadata: timestamp, commit SHA, file count, language breakdown
  modules/
    <module-name>.md    # Per-module: purpose, exports, dependencies, dependents
  patterns.md           # Detected architecture patterns with evidence
  api-surface.md        # Public API endpoints, exported symbols, event schemas
  gotchas.md            # Documented edge cases, TODOs, FIXMEs, test-case-named edge cases
```

---

## Phase 1: Structural Map (Zero Tokens)

Run these bash commands for **each repo** in the workspace. Collect all output before reading any files.

### 1.1 — File inventory

```bash
REPO=<repo-path>

# All source files, excluding noise
find "$REPO" -type f \( \
  -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \
  -o -name "*.py" -o -name "*.go" -o -name "*.java" -o -name "*.kt" \
  -o -name "*.rs" -o -name "*.rb" -o -name "*.dart" -o -name "*.swift" \
  -o -name "*.cpp" -o -name "*.c" -o -name "*.h" \
) \
| grep -v node_modules \
| grep -v "\.git/" \
| grep -v "__pycache__" \
| grep -v "/vendor/" \
| grep -v "/dist/" \
| grep -v "/build/" \
| grep -v "\.generated\." \
| grep -v "\.min\." \
| grep -v "\.spec\." \
| grep -v "\.test\." \
| sort > /tmp/forge_scan_source_files.txt

# Test files — separately (for gotchas extraction)
find "$REPO" -type f \( -name "*.spec.*" -o -name "*.test.*" -o -name "*_test.*" -o -name "test_*.py" \) \
| grep -v node_modules | grep -v "\.git/" | grep -v dist \
| sort > /tmp/forge_scan_test_files.txt

echo "Source files: $(wc -l < /tmp/forge_scan_source_files.txt)"
echo "Test files: $(wc -l < /tmp/forge_scan_test_files.txt)"
```

### 1.2 — Module boundary detection

```bash
# Top-level directories (excluding config/infra noise)
find "$REPO" -maxdepth 2 -type d \
  | grep -v node_modules | grep -v "\.git" | grep -v __pycache__ \
  | grep -v "dist\b" | grep -v "\bbuild\b" \
  | awk -F/ 'NF<=4' \
  | sort

# Entry point detection
find "$REPO" -maxdepth 3 \( \
  -name "main.py" -o -name "app.py" -o -name "server.py" \
  -o -name "index.ts" -o -name "main.ts" -o -name "app.ts" \
  -o -name "index.js" -o -name "main.js" -o -name "server.js" \
  -o -name "main.go" -o -name "main.kt" -o -name "Main.kt" \
  -o -name "main.rs" -o -name "Application.java" \
\) | grep -v node_modules | grep -v dist
```

### 1.3 — Import graph extraction

```bash
# Extract import lines only (first 50 lines per file — imports are always at the top)
while IFS= read -r file; do
  echo "=== $file ==="
  head -50 "$file" | grep -E \
    "^import |^from |^require\(|^use |^extern crate|^#include|^using " \
    2>/dev/null
done < /tmp/forge_scan_source_files.txt > /tmp/forge_scan_imports.txt

echo "Import relationships extracted: $(grep -c "^===" /tmp/forge_scan_imports.txt) files"
```

### 1.4 — Incoming reference count (hub detection)

```bash
# Count how many files reference each module/file
# This identifies architectural hubs without reading any file content

while IFS= read -r file; do
  basename_no_ext=$(basename "$file" | sed 's/\.[^.]*$//')
  count=$(grep -rl "$basename_no_ext" "$REPO" \
    --include="*.ts" --include="*.py" --include="*.go" --include="*.java" --include="*.kt" \
    2>/dev/null | grep -v node_modules | grep -v "\.git" | grep -v dist | wc -l)
  echo "$count $file"
done < /tmp/forge_scan_source_files.txt \
| sort -rn > /tmp/forge_scan_hub_scores.txt

echo "Top 10 hubs:"
head -10 /tmp/forge_scan_hub_scores.txt
```

### 1.5 — Language and framework fingerprinting

```bash
# Language breakdown
echo "Language breakdown:"
grep -c "\.ts$\|\.tsx$" /tmp/forge_scan_source_files.txt && echo "TypeScript/TSX files"
grep -c "\.py$" /tmp/forge_scan_source_files.txt && echo "Python files"
grep -c "\.go$" /tmp/forge_scan_source_files.txt && echo "Go files"
grep -c "\.java$" /tmp/forge_scan_source_files.txt && echo "Java files"
grep -c "\.kt$" /tmp/forge_scan_source_files.txt && echo "Kotlin files"
grep -c "\.dart$" /tmp/forge_scan_source_files.txt && echo "Dart files"

# Framework signals (package.json, go.mod, requirements.txt, etc.)
[ -f "$REPO/package.json" ] && cat "$REPO/package.json" | grep -E '"next"|"express"|"fastify"|"nestjs"|"react-native"|"vue"|"nuxt"|"svelte"|"hono"|"koa"'
[ -f "$REPO/go.mod" ] && grep -E "gin|echo|fiber|chi|mux" "$REPO/go.mod"
[ -f "$REPO/requirements.txt" ] && grep -iE "fastapi|django|flask|starlette|tornado" "$REPO/requirements.txt"
[ -f "$REPO/pubspec.yaml" ] && head -5 "$REPO/pubspec.yaml"
```

---

## Phase 2: Hub Identification (Zero Tokens)

From `forge_scan_hub_scores.txt`, identify:

**Tier 1 Hubs** (referenced by 5+ files) — read top 150 lines in Phase 3
**Tier 2 Hubs** (referenced by 3-4 files) — read top 80 lines in Phase 3
**Leaf files** (referenced by 0-2 files) — extract only from import graph, do NOT read body

```bash
# Tier 1 hubs
awk '$1 >= 5 {print $2}' /tmp/forge_scan_hub_scores.txt > /tmp/forge_scan_tier1.txt
echo "Tier 1 hubs: $(wc -l < /tmp/forge_scan_tier1.txt)"

# Tier 2 hubs
awk '$1 >= 3 && $1 < 5 {print $2}' /tmp/forge_scan_hub_scores.txt > /tmp/forge_scan_tier2.txt
echo "Tier 2 hubs: $(wc -l < /tmp/forge_scan_tier2.txt)"
```

**Cap enforcement:**
- Maximum 20 Tier 1 hub reads per repo
- Maximum 30 Tier 2 hub reads per repo
- If more than 20 Tier 1 hubs exist, read only the top 20 by reference count

---

## Phase 3: Semantic Enrichment (Targeted Reads)

Read files in this priority order. Read only the specified line ranges.

### 3.1 — Always read (zero token restriction)

These are documentation files, not code. Read fully:

```bash
for doc in README.md CONTRIBUTING.md ARCHITECTURE.md docs/architecture.md docs/design.md \
           ADR*.md adr/*.md docs/decisions/*.md; do
  [ -f "$REPO/$doc" ] && echo "=== $REPO/$doc ===" && cat "$REPO/$doc"
done
```

### 3.2 — Tier 1 hub reads (top 150 lines only)

```bash
while IFS= read -r file; do
  echo "=== $file ==="
  head -150 "$file"
  echo ""
done < /tmp/forge_scan_tier1.txt
```

Extract from each hub:
- Exported classes, functions, interfaces (look for `export`, `public`, `pub fn`, `func`, `def`)
- Constructor signatures and key method signatures
- JSDoc/docstrings on exported items
- `// TODO`, `// FIXME`, `// HACK`, `// NOTE` comments

### 3.3 — Tier 2 hub reads (top 80 lines only)

```bash
while IFS= read -r file; do
  echo "=== $file ==="
  head -80 "$file"
  echo ""
done < /tmp/forge_scan_tier2.txt
```

### 3.4 — Test name extraction (zero token body reads)

```bash
# Extract test names only — no file body reads needed
while IFS= read -r file; do
  echo "=== $file ==="
  grep -n \
    "it\(.\|test\(.\|describe\(.\|def test_\|func Test\|#\[test\]\|@Test" \
    "$file" 2>/dev/null | head -30
done < /tmp/forge_scan_test_files.txt > /tmp/forge_scan_test_names.txt
```

### 3.5 — API surface extraction

```bash
# REST endpoints (look for route decorators and router patterns)
grep -rn \
  "@Get\|@Post\|@Put\|@Delete\|@Patch\|router\.get\|router\.post\|app\.get\|app\.post\|r\.GET\|r\.POST\|@app\.route\|@router\." \
  "$REPO" --include="*.ts" --include="*.py" --include="*.go" --include="*.java" --include="*.kt" \
  | grep -v node_modules | grep -v dist | grep -v test | grep -v spec \
  > /tmp/forge_scan_api_routes.txt

echo "API routes found: $(wc -l < /tmp/forge_scan_api_routes.txt)"
cat /tmp/forge_scan_api_routes.txt
```

---

## Phase 4: Brain Write (Obsidian Format)

Create all output files in `~/forge/brain/products/<slug>/codebase/`. Use `[[wikilinks]]` throughout.

### 4.1 — SCAN.json (metadata, always first)

```bash
SCAN_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
COMMIT_SHA=$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo "unknown")
FILE_COUNT=$(wc -l < /tmp/forge_scan_source_files.txt)
TEST_COUNT=$(wc -l < /tmp/forge_scan_test_files.txt)

cat > ~/forge/brain/products/<slug>/codebase/SCAN.json << EOF
{
  "scanned_at": "$SCAN_DATE",
  "repo": "$REPO",
  "commit": "$COMMIT_SHA",
  "source_files": $FILE_COUNT,
  "test_files": $TEST_COUNT,
  "tier1_hubs": $(wc -l < /tmp/forge_scan_tier1.txt),
  "tier2_hubs": $(wc -l < /tmp/forge_scan_tier2.txt),
  "role": "<backend|web|mobile|shared>"
}
EOF
```

### 4.2 — index.md format

```markdown
# Codebase: <repo-name> (<role>)

last-scanned: <ISO timestamp>
commit: <SHA>
files: <count> source, <count> test

## Architecture Style

<Detected pattern: monolith | service-per-feature | layered | modular-monolith | microservice slice>
Evidence:
- <Signal 1 from import graph>
- <Signal 2 from file structure>
- <Signal 3 from framework detection>

## Entry Points

- [[modules/<module>]] — `<path/to/entry>` (<what it boots>)

## Module Map

| Module | Role | Incoming Refs | Key Exports |
|---|---|---|---|
| [[modules/<name>]] | <layer: controller/service/repo/util/config> | <count> | `<ClassA>`, `<fnB>` |

## Architectural Hubs (Tier 1)

Files referenced by 5+ other modules — these are the load-bearing structures:

- [[modules/<name>]] (`<path>`) — <one-line purpose>

## Key Dependencies

External dependencies that shape the architecture:
- `<package>` — <what it's used for>

## Related Brain Files

- [[patterns]] — Architecture patterns detected
- [[api-surface]] — Public API endpoints
- [[gotchas]] — Documented edge cases
```

### 4.3 — modules/<name>.md format

Create one file per top-level module directory + one for each Tier 1 hub.

```markdown
# Module: <name>

**Path:** `<relative/path/from/repo/root>`
**Layer:** <controller | service | repository | domain | infrastructure | util | config>
**Language:** <language>

## Purpose

<One-paragraph description synthesized from: docstrings, README mentions, hub file top comments>

## Exports

| Symbol | Type | Used by |
|---|---|---|
| `<ClassName>` | class | [[modules/<consumer>]], [[modules/<consumer2>]] |
| `<functionName>` | function | [[modules/<consumer>]] |

## Imports (dependencies)

- [[modules/<dep>]] — `<what it uses from dep>`
- `<external-package>` — <what it's used for>

## Imported by (dependents)

- [[modules/<dep>]] — `<why it needs this module>`

## Documented Edge Cases

> From test file: `<test name that describes edge case>`

- `<test string describing edge case 1>`
- `<test string describing edge case 2>`

## TODO / FIXME

> Extracted from source comments

- `<file:line>` — `<comment text>`
```

### 4.4 — patterns.md format

```markdown
# Architecture Patterns

> Detected from import graph + framework signals. Unconfirmed patterns marked ⚠️.

## Confirmed Patterns

### <Pattern Name>
**Evidence:**
1. <Import graph signal>
2. <File structure signal>
3. <Framework/library signal>

**Implications for development:**
- <What this means for how to add a feature>
- <What this means for where to put new files>
- <What this means for testing strategy>

## Likely Patterns ⚠️

### <Pattern Name> (unconfirmed)
**Signals:** <why it might be this pattern>
**Counter-signals:** <why it might not be>
**Recommendation:** Confirm before planning new features — run `/scan` after reading 3-5 hub files fully.

## Anti-Patterns Detected

> These are problems, not features.

- **<Anti-pattern>** at `<location>` — <what makes it an anti-pattern>

## Related

- [[index]] — Module map
- [[modules/<relevant-hub>]] — Core structural file
```

### 4.5 — api-surface.md format

```markdown
# API Surface: <repo-name>

> Auto-extracted from route decorators and router patterns. Verify against actual implementation.

## REST Endpoints

| Method | Path | File | Handler |
|---|---|---|---|
| `GET` | `/api/users` | `<file:line>` | `<HandlerName>` |

## Event Schemas (if applicable)

| Event | Producer | Consumer | Schema |
|---|---|---|---|
| `<event.name>` | [[modules/<producer>]] | [[modules/<consumer>]] | `<type/shape>` |

## Exported SDK / Library Surface (if applicable)

| Symbol | Type | Description |
|---|---|---|
| `<name>` | function/class | <one-line description> |

## Related

- [[patterns]] — Architecture context
- [[modules/<main-router>]] — Main routing hub
```

### 4.6 — gotchas.md format

```markdown
# Codebase Gotchas

> Extracted from: test names, TODO/FIXME comments, HACK comments, documented edge cases.
> These are things that will bite you if you don't know about them.

## Edge Cases (from test names)

- `<test string>` — [[modules/<module>]]
- `<test string>` — [[modules/<module>]]

## Known Issues (from TODO/FIXME)

| Location | Severity | Note |
|---|---|---|
| `<file:line>` | TODO | `<comment>` |
| `<file:line>` | FIXME | `<comment>` |
| `<file:line>` | HACK | `<comment>` |

## Architectural Warnings

> Patterns that will cause bugs if misunderstood:

- **<Warning>** — `<where>` — <why it matters>

## Related

- [[patterns]] — Architecture patterns
- [[index]] — Module map
```

### 4.7 — Diff against prior scan (re-scan only)

When a `SCAN.json` already existed before this run (i.e. this is a re-scan, not first scan), produce a diff summary before overwriting:

```bash
# Read prior scan metadata
PRIOR_FILES=$(cat ~/forge/brain/products/<slug>/codebase/SCAN.json 2>/dev/null | grep '"source_files"' | grep -o '[0-9]*')
PRIOR_COMMIT=$(cat ~/forge/brain/products/<slug>/codebase/SCAN.json 2>/dev/null | grep '"commit"' | grep -o '"[a-f0-9]*"' | tr -d '"')
PRIOR_DATE=$(cat ~/forge/brain/products/<slug>/codebase/SCAN.json 2>/dev/null | grep '"scanned_at"' | grep -o '"[^"]*"' | tail -1 | tr -d '"')

CURRENT_FILES=$(wc -l < /tmp/forge_scan_source_files.txt)
CURRENT_COMMIT=$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Compare module counts
PRIOR_MODULES=$(ls ~/forge/brain/products/<slug>/codebase/modules/ 2>/dev/null | wc -l)

echo "=== Scan Diff ==="
echo "Prior scan: $PRIOR_DATE (commit $PRIOR_COMMIT, $PRIOR_FILES files)"
echo "This scan:  $(date -u +"%Y-%m-%dT%H:%M:%SZ") (commit $CURRENT_COMMIT, $CURRENT_FILES files)"
echo ""
echo "File count change: $((CURRENT_FILES - PRIOR_FILES)) files ($([ $((CURRENT_FILES - PRIOR_FILES)) -gt 0 ] && echo '+')$((CURRENT_FILES - PRIOR_FILES)))"

# Git log between prior and current commit for change summary
if [ "$PRIOR_COMMIT" != "unknown" ] && [ "$PRIOR_COMMIT" != "$CURRENT_COMMIT" ]; then
  echo ""
  echo "Commits since prior scan:"
  git -C "$REPO" log --oneline "$PRIOR_COMMIT".."$CURRENT_COMMIT" 2>/dev/null | head -10
fi
```

Write diff summary into `index.md` under a `## Changes Since Last Scan` section:

```markdown
## Changes Since Last Scan

> Prior scan: <prior-date> (commit <prior-sha>)
> This scan: <current-date> (commit <current-sha>)

- File count: <prior> → <current> (<delta>)
- Commits included: <N commits since prior scan>

### New Modules (files with 0 prior refs now appearing as hubs)
- `<new-module>` — first seen in this scan

### Removed Hubs (files that dropped below threshold)
- `<removed-module>` — no longer referenced by 3+ files

### API Surface Changes
- <N> new endpoints detected
- <N> endpoints no longer found (may have been removed or renamed)
```

This section is overwritten on every re-scan. First scans do not include this section.

### 4.8 — Commit after each project role

```bash
cd ~/forge/brain
git add products/<slug>/codebase/
git commit -m "scan: map <slug>/<role> codebase — <file-count> files, <hub-count> hubs"
```

---

## Phase 5: Cross-Repo Relationship Layer (Multi-Repo Workspaces Only)

**Skip if workspace has only one repo.** Run after all individual repo scans are complete.

This phase identifies the architectural seams between repos — the contracts, shared types, and communication patterns that cross repo boundaries. This is the most valuable architectural data for multi-repo planning and the data most likely to be missing without an explicit scan phase.

### 5.1 — API call detection (consumer → provider)

Find where one repo calls another's HTTP API:

```bash
# In web and mobile repos, find backend API base URLs and fetch patterns
for repo in <web-repo> <mobile-repo>; do
  echo "=== API calls from: $repo ==="
  grep -rn \
    "fetch(\|axios\.\|http\.get\|http\.post\|requests\.get\|requests\.post\|http\.NewRequest\|retrofit\|Dio\(\)" \
    "$repo" \
    --include="*.ts" --include="*.js" --include="*.py" --include="*.go" --include="*.dart" --include="*.kt" \
    | grep -v node_modules | grep -v test | grep -v spec \
    | grep -v "localhost\|127\.0\.0\.1\|example\.com" \
    | head -50
done
```

### 5.2 — Shared type / schema detection

Find types, interfaces, or schemas that appear in multiple repos (shared contracts):

```bash
# Extract exported interface/type names from each repo
for repo in <all-repos>; do
  echo "=== Types from: $repo ==="
  grep -rhn \
    "^export interface \|^export type \|^export class \|^type \|^interface " \
    "$repo" \
    --include="*.ts" \
    | sed 's/^[0-9]*://' \
    | grep -v node_modules
done > /tmp/forge_scan_all_types.txt

# Find type names that appear in 2+ repos (shared types)
sort /tmp/forge_scan_all_types.txt | uniq -d | head -30
```

### 5.3 — Environment variable cross-reference

Environment variables are often the contract between repos (service URLs, API keys, feature flags):

```bash
for repo in <all-repos>; do
  echo "=== Env vars from: $repo ==="
  grep -rhn \
    "process\.env\.\|os\.environ\.\|os\.Getenv\|System\.getenv\|dotenv" \
    "$repo" \
    --include="*.ts" --include="*.js" --include="*.py" --include="*.go" --include="*.java" --include="*.kt" \
    | grep -v node_modules | grep -v test \
    | sed 's/.*process\.env\.\([A-Z_]*\).*/\1/' \
    | sort | uniq
done
```

### 5.4 — Event/message bus cross-reference

Find event producers and consumers across repos:

```bash
# Producer patterns
for repo in <all-repos>; do
  echo "=== Events produced by: $repo ==="
  grep -rhn \
    "publish(\|produce(\|emit(\|sendMessage\|kafkaProducer\|channel\.send\|rabbitMQ\.publish" \
    "$repo" \
    --include="*.ts" --include="*.py" --include="*.go" --include="*.java" --include="*.kt" \
    | grep -v node_modules | grep -v test | head -20
done

# Consumer patterns
for repo in <all-repos>; do
  echo "=== Events consumed by: $repo ==="
  grep -rhn \
    "subscribe(\|consume(\|\.on(\|kafkaConsumer\|channel\.receive\|rabbitMQ\.consume\|@KafkaListener" \
    "$repo" \
    --include="*.ts" --include="*.py" --include="*.go" --include="*.java" --include="*.kt" \
    | grep -v node_modules | grep -v test | head -20
done
```

### 5.5 — Write cross-repo map

Write to `~/forge/brain/products/<slug>/codebase/cross-repo.md`:

```markdown
# Cross-Repo Relationships: <slug>

> Automatically extracted — verify against actual API contracts in brain/products/<slug>/contracts/

## API Calls (Consumer → Provider)

| From | To | Pattern | Notes |
|---|---|---|---|
| [[web]] | [[backend]] | REST HTTP | `fetch('/api/...')` — 23 call sites |
| [[app]] | [[backend]] | REST HTTP | Retrofit client — 18 call sites |

## Shared Types

Types that appear in 2+ repos — these are implicit contracts:

| Type Name | Defined In | Used By |
|---|---|---|
| `User` | [[backend]]/src/types | [[web]], [[app]] |
| `OrderStatus` | [[shared]] | [[backend]], [[web]], [[app]] |

> ⚠️ Shared types not in a shared package are a fragility risk — consider extracting to shared/

## Environment Variable Contracts

Variables that cross repo boundaries:

| Variable | Set By | Read By | Purpose |
|---|---|---|---|
| `API_BASE_URL` | infra/env | [[web]], [[app]] | Backend API root |
| `JWT_SECRET` | infra/env | [[backend]] | Auth token signing |

## Event Bus (Producer → Consumer)

| Event | Produced By | Consumed By | Channel |
|---|---|---|---|
| `order.created` | [[backend]] | [[backend]]/notifications | Kafka |

## Integration Risk Areas

> Patterns that are likely to cause cross-repo bugs:

- **Implicit type sharing** — `<type>` in [[repo-a]] and [[repo-b]] are different structs named the same. Risk: silent deserialization failure.
- **Direct URL hardcoding** — `<N>` call sites use hardcoded backend URL instead of `API_BASE_URL`. Risk: breaks on env change.
- **Missing consumer** — Event `<event>` is produced but no consumer found in any repo. Risk: silent data loss.

## Related

- [[index]] — Per-repo module maps
- [[patterns]] — Architecture patterns detected per repo
```

Commit after cross-repo layer:
```bash
cd ~/forge/brain
git add products/<slug>/codebase/cross-repo.md
git commit -m "scan: cross-repo relationships for <slug> — <N> API call patterns, <N> shared types"
```

---

## Decision Trees

### Decision Tree 1: What to read for a given file

```
Is the file a README / ARCHITECTURE / CONTRIBUTING / ADR?
  → YES: Read fully (always)
  → NO:
      Is reference count ≥ 5?
        → YES (Tier 1 hub): Read top 150 lines
        → NO:
            Is reference count 3-4?
              → YES (Tier 2 hub): Read top 80 lines
              → NO (leaf file):
                  Is it a test file?
                    → YES: Extract test name strings only (grep, no Read)
                    → NO: DO NOT READ — derive from import graph only
```

### Decision Tree 2: Pattern classification

```
Does import graph show ≥3 services importing a central "container" or "di" module?
  → YES: Dependency Injection / IoC pattern

Does every feature directory contain (controller + service + repository)?
  → YES: Layered architecture (controller → service → repository)

Does import graph show no cross-feature imports (features only import shared/)?
  → YES: Modular monolith / vertical slice

Do all routes live in one file and call functions from many modules?
  → YES: Centralized routing (common in Go, Flask)

Does the file structure have one directory per domain entity?
  → YES (and DI found): Domain-Driven Design signal

None of the above match cleanly?
  → Label as: "unclassified — recommend manual architecture review"
```

### Decision Tree 3: When a scan is stale

```
Does codebase/SCAN.json exist?
  → NO: Run full scan

Does SCAN.json exist?
  → YES: Read last-scanned timestamp
    Is it older than 7 days?
      → YES: Re-run Phase 1 (file inventory) to check for new files
        Are there new files (diff from SCAN.json file count)?
          → YES: Run full scan
          → NO: Scan is usable, note staleness in response

    Is it older than 30 days?
      → Always run full scan regardless of file count change
```

---

## Edge Cases

### Edge Case 1: Monorepo with 500+ files

**Symptom:** Phase 1 produces thousands of source files; hub detection takes minutes; token budget exceeded.

**Do NOT:** Read any file body during Phase 3 unless it has 10+ incoming references.

**Mitigation:**
1. Raise hub thresholds: Tier 1 = 10+ refs (not 5+), Tier 2 = 6-9 refs (not 3-4)
2. Cap file inventory at 300 files per role (take the highest-referenced files)
3. Create one module file per top-level directory only (not per subdirectory)
4. Add `"monorepo": true` flag to SCAN.json

**Escalation:** NEEDS_CONTEXT — ask which subdirectory to focus on if repo has >1000 files

---

### Edge Case 2: No test files found

**Symptom:** `/tmp/forge_scan_test_files.txt` is empty; gotchas.md has no test-derived content.

**Do NOT:** Fabricate edge cases or infer them from production code alone.

**Mitigation:**
1. Check for alternative test locations: `__tests__/`, `test/`, `spec/`, `integration/`
2. Try alternative naming patterns: `*_spec.rb`, `*IT.java`, `*Integration.java`
3. Check `package.json` test script for test directory config
4. If truly no tests: write `gotchas.md` with only TODO/FIXME content and a note: `> No test files found — edge cases may be undocumented.`

**Escalation:** DONE_WITH_CONCERNS — flag in index.md: "⚠️ No test files found"

---

### Edge Case 3: Private/generated import paths

**Symptom:** Import graph shows paths like `@app/`, `~/utils/`, `@/components/` that don't map to real directories.

**Do NOT:** Skip these imports or mark them as external dependencies.

**Mitigation:**
1. Check `tsconfig.json` paths aliases: `cat $REPO/tsconfig.json | grep -A5 '"paths"'`
2. Check `vite.config.*` or `webpack.config.*` aliases
3. Check `pyproject.toml` or `setup.py` for src-layout: `grep -E "src_dirs|packages|where" $REPO/pyproject.toml`
4. Resolve aliases before building module map — otherwise module relationships will be wrong

**Escalation:** NEEDS_CONTEXT if aliases cannot be resolved from config files

---

### Edge Case 4: Polyglot repo (multiple languages)

**Symptom:** Source file inventory finds both `.ts` and `.py` files, or `.go` and `.dart` files in the same repo.

**Do NOT:** Pick one language and ignore the other.

**Mitigation:**
1. Scan each language's import lines separately (language-specific grep patterns)
2. Create separate module maps per language layer in `modules/`
3. Look for cross-language communication points: REST calls, gRPC, shared JSON schemas
4. Document the boundary in `patterns.md` as "polyglot boundary"

**Escalation:** NEEDS_CONTEXT if cross-language calls cannot be identified from code alone

---

### Edge Case 5: No git repo in project directory

**Symptom:** `git -C $REPO rev-parse` fails; SCAN.json cannot get commit SHA.

**Do NOT:** Abort the scan.

**Mitigation:**
1. Set `"commit": "no-git"` in SCAN.json
2. Use file modification timestamps as scan version: `date -r <newest-file>`
3. Warn user in index.md: `> ⚠️ No git repository found — cannot track codebase version`

**Escalation:** DONE_WITH_CONCERNS

---

### Edge Case 6: Hub file is auto-generated

**Symptom:** Tier 1 hub file has a header like `// This file is auto-generated. Do not edit.` or `// Code generated by protoc`.

**Do NOT:** Read it as human-authored architecture. Generated files inflate hub scores.

**Mitigation:**
1. Detect generation markers: `grep -m1 "auto-generated\|DO NOT EDIT\|Code generated\|@generated" <file>`
2. Remove from hub lists: add to exclusion list
3. Note the generator in patterns.md: "API types generated by protoc from `<proto-file>`"

**Escalation:** None — handle silently, note in patterns.md

---

### Edge Case 7: Scan runs during /workspace init on a very new repo (few files)

**Symptom:** File inventory returns <10 files. Hub detection has no meaningful signal.

**Do NOT:** Produce an empty or near-empty brain scan.

**Mitigation:**
1. If <10 source files: skip Phases 1-2, read all files fully (they fit in one context window)
2. Write a `codebase/index.md` with note: `> Early-stage codebase — <10 source files. Full scan not needed.`
3. List all files in index.md as a flat inventory with one-line purpose per file
4. Set a reminder in index.md: `> Re-run /scan when codebase grows past 20 files.`

**Escalation:** None

---

## Common Pitfalls

1. **Scanning `node_modules/`** — always results in thousands of files and hub scores dominated by `index.js` files from npm packages. Exclusion pattern MUST be in every `find` command.

2. **Not resolving TypeScript path aliases** — `@/services/auth` looks like an external package but is `src/services/auth.ts`. Check `tsconfig.json` first.

3. **Treating test doubles/mocks as real modules** — `UserRepositoryMock.ts` will score high on incoming references in test files. Exclude `*.mock.*`, `*.stub.*`, `*.fake.*` from hub scoring.

4. **Writing module files for every file instead of every module** — A repo with 200 files does not need 200 module files. Group by directory/feature, not by file.

5. **Not committing SCAN.json before other brain files** — If the write fails mid-way, an incomplete scan with no metadata is worse than no scan. Commit SCAN.json first.

6. **Forgetting to clean up `/tmp/forge_scan_*.txt` temp files** — These accumulate and may cause stale data if a second scan runs in the same session without cleanup.

```bash
# Always run at end of scan
rm -f /tmp/forge_scan_*.txt
```

---

## Quick Reference Card

| Phase | What | Tools | Tokens |
|---|---|---|---|
| 1.1 | File inventory | `find`, `grep` | 0 |
| 1.2 | Module boundaries | `find`, `awk` | 0 |
| 1.3 | Import graph | `head`, `grep` | 0 |
| 1.4 | Hub scoring | `grep -rl`, `awk`, `sort` | 0 |
| 1.5 | Language fingerprint | `grep`, `cat` (package.json) | 0 |
| 2 | Hub tier assignment | `awk` | 0 |
| 3.1 | README / docs | Read (full) | Low |
| 3.2 | Tier 1 hub reads | Read (top 150 lines) | Medium |
| 3.3 | Tier 2 hub reads | Read (top 80 lines) | Low |
| 3.4 | Test name extraction | `grep` | 0 |
| 3.5 | API route extraction | `grep -rn` | 0 |
| 4 | Brain write | Write per file | Low |
| 5 | Cross-repo layer | `grep` across all repos | 0 (grep) + Low (write) |

**Token budget target:** <15K tokens per repo + <5K for cross-repo layer. If you exceed this, you skipped the exclusions.

---

## Cross-References

- **Triggers:** Automatically after [[workspace]] init; manually via `/scan <slug> <repo-path>`
- **Produces:** Brain files consumed by [[brain-read]], [[brain-recall]], [[council-multi-repo-negotiate]]
- **Required before:** [[forge-eval-gate]] on an existing codebase (agent needs module map)
- **Related skills:** [[brain-write]], [[brain-read]], [[forge-brain-layout]]

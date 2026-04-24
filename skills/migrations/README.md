# Skill Migrations

This directory is the global migration registry for cross-cutting or multi-skill breaking changes. Per-skill migrations live under `skills/<name>/migrations/` (see `forge-skill-anatomy` for the per-skill pattern).

Use this directory when a breaking change affects multiple skills, the hook system, or operator brain layouts.

## Format

Each migration is a shell script named `v<version>-<slug>.sh`:

```
skills/migrations/
  v2.0.0-freeze-scope-enforcement.sh
  v2.1.0-learnings-jsonl-format.sh
```

## Script Template

```bash
#!/usr/bin/env bash
# Migration: <skill-name or "global"> v<from> → v<to>
# Date: YYYY-MM-DD
# What changed: <one-line summary of breaking change>
# Required if: <condition — e.g. "you use the freeze skill" or "always">

set -euo pipefail

echo "Running migration: <slug>..."

# --- migration steps ---


echo "Done. If something went wrong, restore from: git stash or git checkout HEAD~1 -- skills/"
```

## Running Migrations

Migrations are run manually when upgrading between major versions. There is no auto-runner — each script is idempotent (safe to run twice).

```bash
# List available migrations
ls skills/migrations/

# Run one
bash skills/migrations/v2.0.0-freeze-scope-enforcement.sh
```

## Migration Log

| Version | Slug | Date | Affects | Notes |
|---------|------|------|---------|-------|
| (none yet) | — | — | — | First migrations will appear here when a skill hits v2.0.0 |

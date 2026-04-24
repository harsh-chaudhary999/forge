# Brain template (Obsidian vault)

This directory is an **Obsidian vault template** for the Forge brain — the persistent decision record that lives at `~/forge/brain/` on the operator's machine.

## What it is

The brain stores everything Forge writes during a pipeline run: PRD artifacts, shared dev specs, conductor logs, tech plans, eval results, and architectural decisions. The `.obsidian/` config here sets sensible defaults (Markdown links, shortest relative paths, assets folder) so the vault is immediately usable without manual configuration.

## How to use it

Copy this directory to `~/forge/brain/` before running Forge for the first time:

```bash
cp -r brain-template ~/forge/brain
```

Then open `~/forge/brain/` in Obsidian. Forge will populate subdirectories (`prds/`, `products/`) as you run commands.

**Do not commit the populated brain to this repo.** The brain contains product-specific decisions and is kept in a separate private repository (or local-only). Only the empty template ships here.

## Directory structure written by Forge

See **[`skills/forge-brain-layout/SKILL.md`](../skills/forge-brain-layout/SKILL.md)** for the full annotated directory tree that Forge creates under `~/forge/brain/`.

## Obsidian config

The `.obsidian/` config enables:
- Markdown-style links (not Wikilinks) for git-diffability
- Shortest relative link format for portability across machines
- `assets/` as the default attachment folder

These settings are intentionally minimal. Add plugins or themes to your local brain vault without committing them here.

## Reliability for agents and CI (recommended)

When this vault is the **git-backed brain** you use with Forge:

1. **Set `FORGE_TASK_ID`** in your shell or CI whenever **multiple** tasks under `prds/` have a `conductor.log` — otherwise hooks and verifiers may use the **wrong** task (mtime heuristic). Same for **`FORGE_BRAIN`** / **`FORGE_BRAIN_PATH`** if the brain is not at `~/forge/brain`.
2. **Copy CI from Forge** — Use **[`.github/workflows/forge-brain-guard.yml`](../.github/workflows/forge-brain-guard.yml)** as a template: set **`FORGE_TOOLS_REPO`**, **`FORGE_TASK_ID`**, and optional strict flags so **empty eval, bad log order, or drift** fail the merge, not the agent’s memory.
3. **Human checkpoints in `conductor.log`** — After major transitions, log one **timestamped** `HUMAN_INTENT` line (see **`skills/conductor-orchestrate/SKILL.md`** → *Human intent checkpoint*) so post-compact sessions still see **what mattered**.
4. **Operational docs** — **`docs/forge-task-verification.md`** and **`skills/using-forge/SKILL.md`** (*Agent reliability*) describe diversion and collapse mitigations.

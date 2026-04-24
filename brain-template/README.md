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

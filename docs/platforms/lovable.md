# Forge with Lovable (UI)

[Lovable](https://lovable.dev) is an **AI-assisted web UI builder**. It is **not** a Forge host like Cursor or Claude Code — there is no Lovable-specific plugin install. Forge treats Lovable as a **design and implementation surface** whose output must land where agents can read it (usually **GitHub**).

## Stack assumptions

Exported Lovable projects are typically **React + TypeScript + Vite + Tailwind** with **shadcn/ui**. Council and **`reasoning-as-web-frontend`** should assume that stack when the PRD names Lovable, unless `prd-locked.md` says otherwise.

## Implementable design (Q9)

A **Lovable-only browser URL** is **not** enough for autonomous phases — same rule as a bare Figma link: agents cannot reliably scrape the live builder.

You **must** lock at least one of:

1. **`lovable_github_repo`** (`owner/repo`) plus optional **`lovable_path_prefix`** (e.g. `apps/marketing-site/`) when the synced code lives inside a monorepo, **and** a pinned **branch, tag, or commit SHA** in `prd-locked.md` or `design/LOVABLE_SYNC.md` under the task brain folder — so implementers and scan skills read **real files**; **or**
2. **`design_brain_paths`** — exports under `~/forge/brain/prds/<task-id>/design/` (screenshots, `README.md`, `LOVABLE_EXPORT.md` with repo + SHA + “canonical side” notes); **or**
3. **`design_waiver: prd_only`** when UI is explicitly engineering-only / no pixel gate.

Optional human pointers: **`design_assets`** may still list the Lovable project URL for people; that does **not** satisfy implementability alone.

## Bi-directional sync and ownership

Lovable can **push to GitHub** and continue editing. Record in **`design/LOVABLE_SYNC.md`** (or `shared-dev-spec.md`):

- Which repo/folder is the **source of truth** for a given slice (Lovable export vs product monorepo).
- How you resolve **merge conflicts** when both Lovable and Forge-driven worktrees touch the same files.
- That **secrets are not exported** from Lovable — wire env and API keys in the product repo per your security model.

## Session modes

- **Plan / iterate UI** in Lovable (layout, copy, flows).
- **Execute** Forge phases (`/intake`, `/council`, `/build`, eval) in the **git repos** listed in `product.md` — typically the same GitHub repo Lovable syncs to, plus any backend services.

See **[`session-modes-forge.md`](session-modes-forge.md)** for Plan vs Agent mapping in the IDE.

## Forge install on your machine

Lovable is not a Forge host. Still **refresh your `~/forge` clone** the same way as other editors (**`git pull`** + **`install.sh`** for Cursor / Claude Code / etc.) so skills you invoke from the IDE stay current — **[README §4](../../README.md#4-keeping-forge-updated-how-you-hear-about-changes)**.

## Related skills

- **`intake-interrogate`** — Q9 design lock; add **`lovable_github_repo`** when Lovable is authoritative.
- **`reasoning-as-web-frontend`** — Design input order includes Lovable + GitHub before Figma-only fallbacks.
- **`conductor-orchestrate`** — `[DESIGN-INGEST]` should cite the synced repo path or brain exports the same way as Figma ingest.

## Verification

There is no Lovable CLI in Forge. Verify by:

1. Clone the locked **`lovable_github_repo`** at the pinned ref and confirm **`lovable_path_prefix`** matches components referenced in `shared-dev-spec.md`.
2. Run **`/scan`** (or your CI **`scan_forge`**) on the repo that contains the Lovable export so council and tech plans see routes and UI coupling.

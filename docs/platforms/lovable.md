# Lovable as a design source (→ GitHub → brain)

[Lovable](https://lovable.dev) is a **design / UI-generation tool**, not an IDE or
agent host — so it lives here as a *design source of truth*, not as a Forge
runtime. Forge (on this Claude-only branch) consumes Lovable output the same way
it consumes any other design source: through files an agent can actually read.

## The rule: lock a readable source, never a bare URL

A bare `lovable.dev` URL is **not** an acceptable design source for intake Q9 —
agents cannot open it. Lock one of these instead, in `prd-locked.md` under
`design_intake_anchor`:

1. **Lovable → GitHub repo (preferred).** Lovable syncs the generated project to a
   GitHub repo. Lock `lovable_github_repo` (+ optional `lovable_path_prefix` and a
   pinned branch/tag/SHA). Forge reads the synced components/pages as code — the
   most implementable form.
2. **Brain design export.** Materialized design under
   `~/forge/brain/prds/<task-id>/design/` (exports + `MCP_INGEST.md` + `README.md`),
   produced during intake / `[DESIGN-INGEST]`.
3. **Figma** (`figma_file_key` + `figma_root_node_ids`) when the design lives there
   instead — read via the host's Figma MCP when available, REST otherwise.

## How the council chain uses this

- **`intake-interrogate`** (Q9) — requires one of the above when there is net-new
  UI; a bare Lovable URL is rejected.
- **`reasoning-as-web-frontend` / `reasoning-as-app-frontend`** — read the locked
  Lovable repo (or brain export) to reason about real components, not a screenshot.
- **`council-multi-repo-negotiate` / `spec-freeze`** — copy the design anchor into
  `shared-dev-spec.md`; a thin design block (net-new UI with no implementable
  source) **blocks** freeze.

## Pinning

Pin the Lovable→GitHub repo to a **branch, tag, or SHA** so downstream phases
implement against a stable snapshot — Lovable can regenerate and move the design
under you otherwise. Record the pin in `design_intake_anchor`.

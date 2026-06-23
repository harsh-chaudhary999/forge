# Design Input Processing (Lovable / Figma / Screenshots / MCP)

**Before running the Analysis Framework**, check if design assets were provided. Design assets are optional but change what you can produce — with them, you move from spec-derived reasoning to spec-validated reasoning.

## Priority order (best → fallback)

1. **Readable files on disk** — Paths under `~/forge/brain/prds/<task-id>/design/` or repo-relative exports listed in `prd-locked.md` / `shared-dev-spec.md`. **Read them first** with the Read tool (images + `README.md` / ingest notes).
2. **Lovable + GitHub (AI-built UI)** — When `prd-locked.md` locks **`lovable_github_repo`** (`owner/repo`) and optional **`lovable_path_prefix`** (e.g. subfolder inside a monorepo), treat that **synced** tree as the live UI source: inventory `src/` routes, layouts, and shadcn/Tailwind usage from **files**, not from a bare `lovable.dev` link. Persist **`~/forge/brain/prds/<task-id>/design/LOVABLE_SYNC.md`** when you ingest (repo, branch or SHA, who resolves Lovable ↔ product-repo conflicts). If only a Lovable **browser URL** is given with **no** GitHub repo + ref and **no** brain exports, **STOP** — same implementability bar as a bare Figma URL (see **`docs/platforms/lovable.md`**).
3. **Figma MCP (when the host exposes it — Claude Code ships `mcp__claude_ai_Figma__*`)** — If `prd-locked.md` contains **`figma_file_key`** + **`figma_root_node_ids`**, use the **Figma MCP** tools to fetch file metadata, nodes, variables, and dev-mode context **before** asking a human for PNGs. Persist a short summary under `~/forge/brain/prds/<task-id>/design/MCP_INGEST.md` (timestamp, nodes pulled, tool used) so council threads and subagents do not depend on chat.
4. **Figma REST API** — If MCP is unavailable but the user provides a **personal access token** and **file key**, use `GET https://api.figma.com/v1/files/{file_key}` (and nodes endpoint as needed). Same persistence rule: capture enough structured detail in the brain so downstream phases are not chat-scoped.
5. **Human export** — Only when MCP and API are unavailable or unauthorized: request PNG/SVG exports into `~/forge/brain/prds/<task-id>/design/` and re-lock paths in intake if necessary.

## If only a bare Figma or wiki URL exists

Figma share links (`figma.com/file/...` or `figma.com/design/...`) are **not** directly readable as pixels in plain markdown. **Do not** invent layouts from the URL alone.

- If **`figma_file_key` + `figma_root_node_ids`** are present → use **Priority order** Figma steps (MCP, then REST).
- If **`lovable_github_repo`** is present → read the GitHub-synced tree per step 2 above.
- If none of the above and no sufficient disk exports → **STOP** and return to intake: require implementable assets per **`intake-interrogate` Q9** (brain `design/` paths, **Lovable GitHub repo + ref**, figma keys + nodes, or explicit `design_waiver: prd_only`).

Wiki-only links (Confluence, Notion, etc.) **without** files in brain or repo and **without** figma key+nodes are **not** authoritative for autonomous UI — treat as a blocker until materialized.

## If screenshots or exported PNGs are provided

Read each image using the Read tool. Extract:

1. **Component inventory** — What UI elements are visible? (buttons, forms, modals, cards, tables, navigation bars, sidebars)
2. **Layout structure** — Grid layout, sidebar + main, full-width, tabbed? Responsive breakpoints visible?
3. **Interaction states shown** — Empty state, loading state, error state, success state, hover/active states?
4. **Navigation flow** — What routes are implied? Breadcrumbs, back buttons, step indicators?
5. **Typography & spacing** — Heading hierarchy (H1/H2/H3), font sizes, spacing density (compact vs comfortable)
6. **Color tokens** — Primary/secondary/destructive action colors, background variants, border colors
7. **Data density** — How many items per page? Pagination or infinite scroll? Table or card grid?
8. **Form complexity** — Number of fields, field types (text, select, file upload, date picker), validation feedback shown

## Design → Contract Implications

After extracting the above, flag design decisions that force backend contract requirements:

| Design Observation | Contract Implication |
|---|---|
| Search box with real-time results | `GET /search?q=...` needs ≤100ms response or debounce + loading state |
| File upload button visible | Backend must define `max_file_size`, `accepted_types`, upload endpoint |
| Pagination with page numbers | API must return `total_count` + `page` + `per_page` |
| Infinite scroll | API must support cursor-based pagination (`cursor`, `has_next`) |
| Avatar/image for every list item | Backend must return `avatar_url` per item; broken images need fallback |
| "Last updated N minutes ago" timestamps | API must return ISO timestamps; client does relative formatting |
| Multi-step form (wizard) | State must survive page refresh — needs either session storage or draft API |
| Bulk select + action | API must support batch operations endpoint |

## Design Gap Analysis

After reading the design assets, compare what's shown against the PRD text:

- **In design but not in PRD** — Flag as scope clarification needed (UI implies a feature the PRD didn't specify)
- **In PRD but not in design** — Flag as design gap (feature is specified but UI flow is unclear)
- **Design contradicts PRD** — Flag as conflict (e.g., PRD says "no file upload", design shows upload button)

Include a `## Design Gap Analysis` section in your output when design assets are provided.

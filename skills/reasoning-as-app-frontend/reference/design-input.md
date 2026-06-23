# Design Input Processing (intake lock → Lovable / Figma / Screenshots)

The SKILL.md spine points here for the full design-ingestion procedure used before the
Screens & Navigation analysis. It covers transport priority, screenshot extraction, the
Design → Mobile Contract implications table, screen-inventory validation, and gap analysis.

**Before running the Screens & Navigation analysis**, read the **Design / UI** block from **locked `prd-locked.md`** (and **`shared-dev-spec.md` → Design source (from intake)** when council has run). That block must include **`design_intake_anchor`** when Q9 applied — proof the **single design source of truth** was asked and answered. That block is the **only** reliable channel for “new design files exist” when humans are no longer in the loop — subagents do not share your chat history.

- If **`design_new_work: yes`**: implementable inputs are **mandatory** — paths under `~/forge/brain/prds/<task-id>/design/` or repo exports, **or** **`lovable_github_repo`** (+ optional **`lovable_path_prefix`**) with a pinned ref for **Lovable → GitHub** UI (see **`docs/platforms/lovable.md`**), **or** **`figma_file_key` + `figma_root_node_ids`** for MCP/REST fetch (see Design Input Processing). If the lock says yes but only wiki/Figma/Lovable **browser** URLs without keys, repo, nodes, or files, **STOP** and send the task back to intake.
- If **`design_new_work: no`** or **`design_assets: none`**: proceed from PRD + existing patterns; still document that decision in `app.md`.
- **`design_ui_scope: not applicable`**: skip file-based design reads.

Bare Figma/wiki URLs without **file key + node ids** or **on-disk exports** are not a transport layer — intake must materialize design per **`intake-interrogate` Q9** before council. Do not invent screens from a bare URL.

## Priority order (best → fallback)

1. **Readable files on disk** — `~/forge/brain/prds/<task-id>/design/` or repo paths from `prd-locked.md` / `shared-dev-spec.md`. Read with the Read tool.
2. **Lovable + GitHub** — When **`lovable_github_repo`** is locked, read the synced **React/TS** tree (and optional **`lovable_path_prefix`**) the same way as web **`reasoning-as-web-frontend`**: routes, layouts, shared components. Persist **`design/LOVABLE_SYNC.md`** on ingest when helpful. Web-first Lovable exports still inform **native shell** flows (navigation, forms) when the PRD ties them together.
3. **Figma MCP (when the host exposes it — Claude Code ships `mcp__claude_ai_Figma__*`)** — When `figma_file_key` + `figma_root_node_ids` are locked, use **Figma MCP** to fetch nodes, variables, and dev-mode constraints before asking for PNGs. Write `~/forge/brain/prds/<task-id>/design/MCP_INGEST.md` (timestamp, nodes, summary) for downstream agents.
4. **Figma REST** — If MCP unavailable and user provides token + file key, use `GET https://api.figma.com/v1/files/{file_key}`; persist structured notes under `design/`.
5. **Human export** — Request PNG exports into `~/forge/brain/prds/<task-id>/design/` only when 2–4 are not available.

## If only a share URL or wiki link exists

**STOP** — require implementable design (brain paths, **Lovable GitHub repo + ref**, figma key+nodes, or `design_waiver: prd_only`). Do not proceed with screen inventory from prose alone when `design_new_work: yes`.

## If screenshots or exported PNGs are provided

Read each image using the Read tool. For mobile, extract:

1. **Screen inventory** — List every distinct screen visible (onboarding, home, detail, settings, modals, bottom sheets)
2. **Navigation pattern** — Bottom tab bar? Side drawer? Stack navigation? Tab + stack hybrid?
3. **Platform signals** — iOS design language (SF Symbols, native pickers, swipe-to-delete)? Material Design (FAB, chips, snackbars)?
4. **Gesture interactions visible** — Swipe left/right, pull-to-refresh, pinch-to-zoom, long press menu?
5. **States shown** — Empty state, loading skeleton, error screen, offline banner, permission prompt?
6. **Form inputs** — Native date pickers? Custom keyboard types? Camera/gallery access implied?
7. **Content density** — List rows, card grids, media-heavy (image/video previews)?
8. **Notification entry points** — Deep links implied by notification tap-to-open patterns?

## Design → Mobile Contract Implications

| Design Observation | Mobile Contract Implication |
|---|---|
| Bottom tab bar with 4+ items | Tab state must persist across sessions (last active tab) |
| Pull-to-refresh on list | API must support `If-None-Match` / ETags or cursor-based pagination for diff |
| "Last seen online" / presence | WebSocket or polling contract — define interval and fallback |
| Photo upload from camera/gallery | Permission model: iOS `NSCameraUsageDescription`, Android `READ_MEDIA_IMAGES` |
| Video playback inline | Bandwidth budget: streaming vs download; background audio session needed? |
| Map with pins | Location permission: always vs when-in-use; clustering at zoom levels |
| Biometric login button | iOS FaceID/TouchID + Android BiometricPrompt — platform-specific APIs |
| Push notification icon in UI | Notification permission prompt — iOS requires explicit prompt timing decision |
| Deep link from notification | URL scheme or Universal Link / App Link must be defined |
| Offline-capable list | Sync strategy must be defined before locking (last-write-wins, server-auth, CRDT) |

## Design → Screen Inventory

After reading the design assets, produce a validated screen list that replaces the spec-derived list in Section 1:

```
Screens confirmed from design assets:
  ✅ OnboardingScreen       — 3-step wizard, skip button on step 1-2, no skip on step 3
  ✅ HomeScreen             — Bottom tab, feed list, FAB for new post
  ✅ DetailScreen           — Hero image, comment section, like/share actions
  ⚠️  SettingsScreen        — Visible in design but NOT in PRD — flag for scope confirmation
  ❌  ProfileEditScreen     — In PRD but NOT in design — design gap, request mockup
```

## Design Gap Analysis

Flag every discrepancy between design and PRD as a blocker or advisory:

- **In design but not in PRD** → scope clarification required before Council can lock
- **In PRD but not in design** → design gap; mobile surface cannot commit to implementation without visual spec
- **Design contradicts PRD** → explicit conflict, must resolve before spec freeze

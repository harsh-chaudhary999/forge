# Changelog

All notable changes to Forge are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-06-18

The **Claude-only** line. This branch is specialized for Claude Code and aligns
Forge with the 2026 platform standards (Agent Skills standard, native subagent
frontmatter, dynamic workflows, MCP, OpenTelemetry GenAI). Builds for other IDEs
move to dedicated branches.

> Foundation work for 1.1.0 lands incrementally on the `claude` branch and is
> reviewed commit by commit. This entry is updated as stages merge.

### Added
- **Brain MCP server** (`tools/mcp/forge_brain_mcp.py`, shim `tools/forge_brain_mcp.py`):
  a dependency-free, **read-only** Model Context Protocol server (JSON-RPC/stdio)
  exposing the brain to any MCP client — tools `brain_read`, `brain_list`,
  `brain_recall`, `brain_why`, `brain_conductor_status`. Confined to the brain
  root (path traversal refused). Bundled `.mcp.json` at the plugin root; register
  on any install with `claude mcp add forge-brain -- python3 tools/forge_brain_mcp.py`.
  See [`docs/brain-mcp.md`](docs/brain-mcp.md).
  - **MCP resources + prompts** (server `v1.2.0`): every brain text file is also an
    MCP **resource** (`brain:///<path>`, paginated, with a `brain:///{path}`
    template) and three **prompts** (`task_brief`, `decision_provenance`,
    `recall_brain`) embed the relevant brain content inline. `initialize` now
    advertises `capabilities: { tools, resources, prompts }`. Still read-only,
    still brain-confined.
- **Agent Skills standard conformance check** (`tools/check_skill_standard.py`),
  run in CI; OKF + Memory-tool brain conventions (`index.md`/`log.md`/`type:`).
- **Trajectory eval + OpenTelemetry export** (`tools/eval/`):
  - `forge_trajectory_eval.py` — scores the *delivery trajectory* from
    `conductor.log` (gate adherence, phase ordering, eval outcome, self-heal
    efficiency → GREEN/YELLOW/RED). The second eval axis alongside `eval-judge`'s
    product verdict; `--strict` exits 1 on RED.
  - `forge_otel_export.py` — exports the trajectory as OTLP/JSON (eval spans carry
    OTel GenAI `gen_ai.*` attributes) for Langfuse / Braintrust / Phoenix.
  - `dream-retrospect-post-pr` (v1.0.0→1.1.0) now runs the analyzer before
    qualitative scoring; `eval-judge` (v2.0.0→2.1.0) cross-references it. Stdlib
    only. See [`docs/eval-trajectory.md`](docs/eval-trajectory.md).
- **`/forge-council` dynamic workflow** (`.claude/workflows/forge-council.js`):
  the council span as a [Dynamic Workflow](https://code.claude.com/docs/en/workflows)
  — fans out 4 surfaces × 5 contracts over a locked PRD, adversarially cross-checks
  them, and writes a `shared-dev-spec.DRAFT.md` to the brain (spec-freeze stays a
  human gate). `install.sh` copies workflows to `~/.claude/workflows/`. Mapping of
  conductor phases to workflows: [`docs/workflows.md`](docs/workflows.md).
- **Agent Teams mapping** ([`docs/agent-teams.md`](docs/agent-teams.md)): documents
  which conductor spans suit Claude Code [agent teams](https://code.claude.com/docs/en/agent-teams)
  (the human-in-the-loop counterpart to workflows — live adversarial council, parallel
  review, competing-hypothesis self-heal), how Forge's `agents/` subagents serve as
  teammate roles, and how the `TeammateIdle`/`TaskCreated`/`TaskCompleted` hooks map
  onto Forge's HARD-GATEs. No team config is shipped (team config is auto-generated and
  must not be pre-authored).
  - **`forge-team-gates.cjs`** (registered in `hooks/hooks.json` for all three team
    events): an **audit** layer (append-only team-events log in the brain — never
    blocks) plus an **opt-in** strict layer (`FORGE_TEAM_GATES=strict`) that blocks a
    `TaskCompleted` claiming a merge/ship with no `[P5…]` brain marker, and a
    `TeammateIdle` on a `[P4.4-EVAL-FAIL]`. Inert outside an experimental agent team.
- **`effort: high` frontmatter** on the 14 reasoning-heavy skills (council surfaces
  ×4, contracts ×5, `council-multi-repo-negotiate`, `tech-plan-write-per-project`,
  `intake-interrogate`, `dream-retrospect-post-pr`, `dream-resolve-inline`) — uses the
  2026 skill `effort` field to raise reasoning depth where it pays off; patch-bumped.

### Fixed
- **`/forge-council` portability**: subagents now invoke the `reasoning-as-*` /
  `contract-*` / `spec-freeze` skills **by name** (Skill tool) instead of by relative
  `skills/<x>/SKILL.md` path (which doesn't exist in a user's project), and every
  file-touching prompt now expands `~` to an absolute path before Read/Write.
- **Workflow CI coverage**: `.github/workflows/forge-hooks.yml` now syntax-checks
  `.claude/workflows/*.js` by mirroring the runtime's async wrapper (raw `node --check`
  is unreliable for the `export` + top-level-`await`/`return` form).
- **Uninstall**: best-effort `claude mcp remove forge-brain` so a manually-registered
  brain MCP server doesn't dangle at a deleted script.
- **OTel export**: eval spans now emit `kind: CLIENT` (GenAI convention) instead of
  INTERNAL. Trajectory analyzer drops an unreachable scoring branch and gains an
  explicit "audits the log, not the run" caveat.

### Changed
- **Progressive-disclosure refactor (begun).** `forge-skill-anatomy` (v2.0.4→2.1.0)
  now mandates the Agent Skills three-level model: SKILL.md ≤ ~400 lines (operational
  contract), catalogs/depth relocated to a skill's `reference/*.md` (loaded on demand),
  shared boilerplate under `skills/_shared/`, ritual-by-type, and a `triggers`/
  `allowed-tools` status note. New shared source of truth:
  `skills/_shared/human-input.md` (replaces the multi-host human-input block repeated
  across 21 skills). First skill refactored to the new standard:
  **`eval-driver-android-adb`** (v1.0.3→1.1.0) — SKILL.md **1826→219 lines** with the
  API catalog, edge-case code, and UIAutomator guide moved verbatim into
  `reference/{adb-driver-api,edge-cases-and-lifecycle,uiautomator-guide}.md`
  (line-accounted, zero content loss) and multi-host prose removed.
- **Claude-only build.** `scripts/install.sh`, `scripts/verify-forge-plugin-install.sh`,
  and `scripts/forge-doctor.sh` now target Claude Code only. `install.sh` rejects
  `--platform` values other than `claude-code`.
- **README + CLAUDE.md** rewritten for a Claude Code-only plugin (platform table,
  quick start, repository layout, troubleshooting, requirements).
- `package.json`: removed `main` (pointed at the deleted OpenCode entry) and `type`.
- Version bumped `1.0.0 → 1.1.0` across `package.json`, `.claude-plugin/plugin.json`,
  and `.claude-plugin/marketplace.json`.

### Removed
- All non-Claude host artifacts: `.cursor/`, `.cursor-plugin/`, `.cursorrules`,
  `.codex-plugin/`, `.codex/`, `.opencode/`, `.agent/`, `.agents/` (a stale duplicate
  skill tree), `gemini-extension.json`, `GEMINI.md`, `references/copilot-tools.md`,
  `templates/junie-guidelines.md`, the Cursor hook manifest, the `hooks/session-start`
  shell shim, and the non-Claude platform docs under `docs/platforms/`. `.gitignore`
  now blocks `.codex/`, `.agents/`, `.cursor/`, `.opencode/` from being recommitted by
  other-IDE tooling.

### Notes
- `AGENTS.md` is retained — it is now a vendor-neutral standard (Linux Foundation)
  and is referenced by many skills for the "written artifacts — precision" rules.

[1.1.0]: https://github.com/harsh-chaudhary999/forge/releases/tag/v1.1.0

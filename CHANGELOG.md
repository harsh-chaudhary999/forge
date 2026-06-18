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

### Changed
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
  `.codex-plugin/`, `.opencode/`, `.agent/`, `gemini-extension.json`, `GEMINI.md`,
  `references/copilot-tools.md`, `templates/junie-guidelines.md`, the Cursor hook
  manifest, the `hooks/session-start` shell shim, and the non-Claude platform docs
  under `docs/platforms/`.

### Notes
- `AGENTS.md` is retained — it is now a vendor-neutral standard (Linux Foundation)
  and is referenced by many skills for the "written artifacts — precision" rules.

[1.1.0]: https://github.com/harsh-chaudhary999/forge/releases/tag/v1.1.0

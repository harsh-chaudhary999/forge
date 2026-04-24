# Forge on OpenAI Codex

## Prerequisites
- OpenAI Codex CLI
- Git

## Installation

**Auto:** Codex reads `AGENTS.md` at session start automatically.

```bash
git clone https://github.com/<YOUR_GITHUB_ORG_OR_USERNAME>/forge ~/forge
cd ~/forge
codex  # Start Codex in the Forge directory
```

No install script needed.

## Verification

Start a Codex session in the Forge directory. The `AGENTS.md` content should be displayed as context. Verify by asking Codex about Forge rules.

## Keeping Forge updated

**Discovery:** **[README Section 4](../../README.md#4-keeping-forge-updated-how-you-hear-about-changes)**.

**Context-only mode** (open `~/forge` in Codex): **`git pull`** the clone; new sessions load updated `AGENTS.md` / `skills/`.

**Marketplace / cached plugin** (after **`install.sh --platform codex`**): **`cd ~/forge && git pull && bash scripts/install.sh --platform codex`**, then **`codex plugin install forge`** again if Codex kept a stale cache (see `install.sh` notes).

## Available Features

| Feature | Status |
|---|---|
| AGENTS.md context | Auto-loaded at session start |
| Core rules | Non-negotiable rules enforced via AGENTS.md |
| Anti-pattern table | Rationalization blocking from AGENTS.md |
| Skill format docs | Skill directory structure documented |

## How It Works

1. **Context Loading:** Codex reads `AGENTS.md` from the project root at session start
2. **Rule Enforcement:** AGENTS.md contains Forge's core rules (intake first, council before code, worktree per task, eval gates everything, brain persistence)
3. **Anti-Pattern Blocking:** The rationalization table in AGENTS.md prevents common shortcuts

## Forge phase session styles

Codex is **context-only** (no Forge slash commands or hooks). Session style is entirely **prompt discipline**: **planning-style** for locking scope and contracts in prose before asking for file edits; **execution-style** for implementation and running tests. See **[`session-modes-forge.md`](session-modes-forge.md)**.

## Limitations

- **No skills system:** Codex does not have a Skill tool; skills cannot be invoked directly
- **No hooks:** No SessionStart hook injection
- **No slash commands:** Commands are not available
- **No subagent dispatch:** No Agent tool for parallel subagent work
- **Context only:** Codex gets Forge's rules but not its full skill orchestration

## Workarounds

- **Instead of skills:** Reference the skill content manually — read `skills/{name}/SKILL.md` and follow its instructions
- **Instead of hooks:** AGENTS.md provides equivalent rule context
- **Instead of commands:** Ask Codex to follow the workflow described in AGENTS.md

## Troubleshooting

**AGENTS.md not loaded:**
- Verify file exists at repo root: `ls AGENTS.md`
- Ensure you started Codex from the Forge directory (not a parent/child)

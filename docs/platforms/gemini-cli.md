# Forge on Gemini CLI

## Prerequisites
- Gemini CLI installed
- Git

## Installation

**Auto:** Gemini CLI auto-discovers extensions from `gemini-extension.json` in the project root.

```bash
git clone https://github.com/<YOUR_GITHUB_ORG_OR_USERNAME>/forge ~/forge
cd ~/forge
gemini  # Start Gemini CLI in the Forge directory
```

Opening the clone as the project is enough for discovery mode. For **`gemini extensions link` / `update forge`**, run **`bash scripts/install.sh --platform gemini-cli`** once from the clone so the CLI knows where Forge lives.

## Verification

Start Gemini CLI in the Forge directory. The extension loads `GEMINI.md` which points to `skills/using-forge/SKILL.md`.

## Keeping Forge updated

**Discovery** of new Forge commits is the same for every host — **[README §4](../../README.md#4-keeping-forge-updated-how-you-hear-about-changes)** (GitHub Watch / Releases, team comms).

**Apply updates:**

1. **`git pull`** in `~/forge` (or your clone).
2. If you use **`gemini extensions link`** / the linked extension workflow, run **`gemini extensions update forge`** (or re-link) so the CLI picks up new files — see **`bash scripts/install.sh --platform gemini-cli`** for the supported layout.
3. If you only ever open the **Forge repo as the project root**, pulling the repo is usually enough; still restart the CLI session after large skill changes.

## Available Features

| Feature | Status |
|---|---|
| Skills (full tree) | Available via Gemini's tool system |
| GEMINI.md context | Auto-loaded as project context |
| AGENTS.md context | Auto-loaded (Gemini reads both) |

## How It Works

1. **Extension Discovery:** Gemini CLI reads `gemini-extension.json` at project root
2. **Context Loading:** The `contextFileName` field points to `GEMINI.md`
3. **GEMINI.md:** Contains `@./skills/using-forge/SKILL.md` which loads the bootstrap skill
4. **Skill Access:** Skills can be invoked via Gemini's native tool calls

## Forge phase session styles

Gemini CLI has no Forge slash-command layer unless you add one; invoke skills by name. Use **planning-style** vs **execution-style** prompts per Forge phase — see **[`session-modes-forge.md`](session-modes-forge.md)**.

## Limitations

- **No hooks:** Gemini CLI does not have a SessionStart hook system; context is loaded via extension config
- **No subagent dispatch:** Gemini does not support the Agent tool for spawning subagents
- **No slash commands:** Commands are not available; invoke skills directly
- **No brain persistence hooks:** Post-commit and pre-merge hooks are Claude Code specific

## Workarounds

- **Instead of hooks:** GEMINI.md + extension config provides equivalent session context
- **Instead of subagents:** Run skills inline (the AI handles task execution directly)
- **Instead of commands:** Reference skill names directly in conversation

## Troubleshooting

**Extension not loading:**
- Verify `gemini-extension.json` exists at repo root
- Check JSON is valid: `cat gemini-extension.json | python3 -m json.tool`
- Restart Gemini CLI

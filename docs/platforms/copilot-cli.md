# Forge on GitHub Copilot CLI

## Prerequisites
- GitHub Copilot CLI
- Git
- Bash

## Installation

**Auto:** The session-start hook detects Copilot CLI via the `COPILOT_CLI` environment variable.

```bash
git clone https://github.com/harsh-chaudhary999/forge ~/forge
```

**Fallback:**
```bash
cd ~/forge && bash scripts/install.sh --platform copilot-cli
```

## Verification

Start a Copilot CLI session in the Forge directory. The `using-forge` bootstrap should be injected as context.

## Available Features

| Feature | Status |
|---|---|
| Skills (68) | Available via skill invocation |
| Session bootstrap | Auto via hook detection |
| Tool mapping | `references/copilot-tools.md` |

## How It Works

1. **Platform Detection:** The `hooks/session-start` script checks for `COPILOT_CLI` env var
2. **Context Injection:** Outputs `using-forge` content in the standard `additionalContext` JSON format
3. **Tool Mapping:** Skills reference Claude Code tool names; see `references/copilot-tools.md` for Copilot equivalents

## Forge phase session styles

Copilot CLI is prompt- and permission-driven. Apply **planning-style** vs **execution-style** phases as in **[`session-modes-forge.md`](session-modes-forge.md)**.

## Tool Name Mapping

Forge skills use Claude Code tool names. On Copilot CLI:

| Claude Code | Copilot CLI |
|---|---|
| `Skill` | `@skill` mention |
| `Agent` | Subagent dispatch |
| `Read` | File read |
| `Edit` | File edit |
| `Bash` | Shell execution |
| `Grep` | Content search |
| `Glob` | File search |

Full mapping: `references/copilot-tools.md`

## Limitations

- **Tool names differ:** Skills reference Claude Code tools; Copilot CLI uses different names
- **Limited subagent support:** Copilot CLI's agent model may differ from Claude Code's
- **No slash commands:** Commands are not available as slash commands

## Troubleshooting

**Hook not detecting Copilot CLI:**
- Verify `COPILOT_CLI` env var is set during session
- Check hook output format matches Copilot's expected JSON structure
- Run manually: `COPILOT_CLI=1 bash hooks/session-start`

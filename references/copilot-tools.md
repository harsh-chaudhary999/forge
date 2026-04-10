# Copilot CLI Tool Mapping

Forge skills reference Claude Code tool names. When running on GitHub Copilot CLI, use these equivalents.

## Tool Name Mapping

| Claude Code Tool | Copilot CLI Equivalent | Notes |
|---|---|---|
| `Skill` | `@skill` mention | Copilot uses @mentions for skill invocation |
| `Agent` | Subagent dispatch | Use `spawn` for parallel agent work |
| `TodoWrite` | Task tracking | Copilot tracks tasks internally |
| `Read` | File read | Native file reading capability |
| `Edit` | File edit | Native file editing capability |
| `Write` | File write | Native file creation capability |
| `Bash` | Shell execution | Direct terminal access |
| `Grep` | Content search | Regex-based file content search |
| `Glob` | File search | Pattern-based file discovery |
| `WebFetch` | HTTP fetch | URL content retrieval |
| `WebSearch` | Web search | Internet search capability |

## Behavioral Differences

- **Session Start:** Copilot CLI detects `COPILOT_CLI` env var; the session-start hook outputs the standard `additionalContext` JSON format
- **Skill Discovery:** Skills are discovered from the plugin's `skills/` directory; each `SKILL.md` frontmatter is indexed
- **Subagents:** Copilot CLI supports spawning subagents; pass full task context inline (per Forge D22)
- **Commands:** Slash commands in `commands/` are available as `/command-name`

## Platform Detection

The `hooks/session-start` script detects Copilot CLI via:
```bash
if [ -n "${COPILOT_CLI:-}" ]; then
  # Copilot CLI format
  printf '{"additionalContext": "%s"}\n' "$session_context"
fi
```

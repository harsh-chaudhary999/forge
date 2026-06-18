# Forge Brain MCP server

`tools/mcp/forge_brain_mcp.py` is a **read-only** [Model Context Protocol](https://modelcontextprotocol.io)
server that exposes the git-backed Forge brain to any MCP client. It lets Claude
Code (or any agent) query PRDs, specs, decisions, and conductor phase state
**without a Forge session loaded** — turning the brain from "a thing you must be
inside Forge to read" into a memory layer any agent can consult.

It is **dependency-free** (Python stdlib only, JSON-RPC 2.0 over stdio) and ships
no agent framework, so it does not violate D5/D13.

## Tools

| Tool | What it returns |
|---|---|
| `brain_read` | The text of a brain file, or a directory listing if the path is a folder. |
| `brain_list` | One-level listing of a brain directory — discover what exists before reading. |
| `brain_recall` | Case-insensitive substring search across brain `.md/.csv/.log/.json/.txt/.tsv`; returns `file:line` snippets. |
| `brain_why` | Provenance for a decision/file: YAML frontmatter + `git log` history (who/when/why). Accepts a brain-relative path or a decision id (e.g. `D102`). |
| `brain_conductor_status` | Latest `conductor.log` phase markers for a task (`task_id`), or a summary across all tasks under `prds/`. |

All tools are confined to the brain root — a path that escapes it (e.g. `../../etc/passwd`) is refused.

## Resources & Prompts

Beyond tools, the server exposes the brain over the two other MCP primitives (both
read-only, both confined to the brain root):

**Resources** — every brain text file (`.md/.csv/.log/.json/.txt/.tsv`) is listed as an
MCP resource with the URI `brain:///<relative-path>`, so a client can browse and read
the brain as resources, not only by calling tools. `resources/list` paginates (200 per
page via an offset `cursor`); `resources/templates/list` advertises the
`brain:///{path}` template; `resources/read` returns a file's text (a URI that escapes
the brain root yields a `-32002` resource-not-found, same guard as the tools).

**Prompts** — ready-made questions that embed the relevant brain content inline, so a
one-shot query needs no tool round-trips:

| Prompt | Argument | What it embeds |
|---|---|---|
| `task_brief` | `task_id` | The task's locked PRD + `shared-dev-spec` (frozen, else `.DRAFT`) + conductor status, then asks for a scope/contracts/status summary. |
| `decision_provenance` | `target` | A decision's frontmatter + git history (`brain_why`), then asks why it was made and what it superseded. |
| `recall_brain` | `query` | Matching brain lines (`brain_recall`), then asks for a synthesis of prior art. |

`initialize` advertises `capabilities: { tools, resources, prompts }`.

## Brain root resolution

First match wins: `$FORGE_BRAIN` → `$FORGE_BRAIN_PATH` → `~/forge/brain`.

## Registering it with Claude Code

**Any install (recommended):** register the server from your Forge clone — always current, independent of the plugin cache version:

```bash
claude mcp add forge-brain -- python3 ~/forge/tools/forge_brain_mcp.py
```

To point it at a non-default brain, add the env:

```bash
claude mcp add forge-brain --env FORGE_BRAIN=/path/to/brain -- python3 ~/forge/tools/forge_brain_mcp.py
```

**Bundled mechanism:** the plugin also ships a `.mcp.json` at its root (copied
into the plugin cache by `install.sh`), which Claude Code auto-discovers when the
plugin is enabled as a marketplace plugin. It runs
`python3 ${CLAUDE_PLUGIN_ROOT}/tools/mcp/forge_brain_mcp.py`.

> **In-repo caveat:** `${CLAUDE_PLUGIN_ROOT}` is defined **only** when Claude Code
> loads this `.mcp.json` as a *plugin* manifest. If you open the Forge repo
> directly, the same file is read as a *project-scoped* MCP config, the variable is
> undefined, and the server won't start. For in-repo development, register it
> manually with the `claude mcp add` command above (pointing at your clone).

## Verify it works

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | python3 tools/forge_brain_mcp.py
```

You should see an `initialize` result with `serverInfo.name = "forge-brain"`, then
a `tools/list` result naming the five tools above. Diagnostics go to **stderr**;
**stdout carries only JSON-RPC** (required by the stdio transport).

## Design notes

- **Read-only by construction.** There are no write/edit/delete tools. Brain
  mutation stays with the `brain-write` / `brain-forget` skills (audited, committed).
- **No SDK dependency.** The JSON-RPC loop (`initialize`, `tools/list`,
  `tools/call`, `ping`, `notifications/initialized`) is implemented directly so the
  plugin adds no runtime package.
- **Pairs with the brain's OKF layout.** `brain_list` + `index.md` give cheap
  progressive disclosure; `brain_why` reads the git history that `log.md` narrates.
- **`brain_recall` here is plain substring search, not the skill.** This tool does a
  case-insensitive line scan over the brain; it is intentionally simpler than the
  [`brain-recall`](../skills/brain-recall/SKILL.md) skill's hybrid retrieval
  (grep + tags + product/project filtering). Use it to locate files cheaply, then
  `brain_read` them — don't assume ranked-relevance parity with the skill.

# Forge on Cursor

## Prerequisites
- Cursor IDE
- Node.js 16+
- Git

## Installation

**Auto (recommended):** Forge is detected as a plugin via `.cursor-plugin/plugin.json`. Clone the repo and restart Cursor.

```bash
git clone https://github.com/<YOUR_GITHUB_ORG_OR_USERNAME>/forge ~/forge
```

**Fallback:**
```bash
cd ~/forge && bash scripts/install.sh --platform cursor
```

## Verification

Open Cursor in the Forge directory. The `.cursorrules` file provides project-level AI context. The session-start hook injects the `using-forge` bootstrap.

## Keeping Forge updated

After **`git pull`** in your Forge clone, re-run:

```bash
cd ~/forge && git pull && bash scripts/install.sh --platform cursor
```

Restart **Cursor** when skills or hooks change. **Discovery** of new Forge versions (Watch, Releases, etc.) is editor-agnostic — see **[README Section 4](../../README.md#4-keeping-forge-updated-how-you-hear-about-changes)**.

## Available Features

| Feature | Status |
|---|---|
| Skills (full `skills/` tree) | Full support — count: `bash scripts/count-skills.sh` from Forge root |
| Codebase scan (`forge_scan.py`) | **`install.sh --platform cursor`** copies **`tools/`** into **`~/.cursor/plugins/local/forge/tools/`** — run **`python3 ~/.cursor/plugins/local/forge/tools/forge_scan.py`** when the workspace is not the Forge repo |
| Agents (4) | Full support |
| Hooks | SessionStart via `hooks-cursor.json` |
| Commands (17) | All slash commands available |
| Brain | Full read/write |
| Worktrees | Full isolation |
| `.cursorrules` | Project-level AI context |

## How It Works

1. **Plugin Discovery:** Cursor reads `.cursor-plugin/plugin.json` to discover the plugin
2. **Project Context:** `.cursorrules` is loaded as project-level AI instructions
3. **Hook Format:** Cursor uses snake_case (`session_start` instead of `SessionStart`)
4. **Session Injection:** **`hooks-cursor.json`** runs **`./hooks/session-start`**, which execs **`.claude/hooks/session-start.cjs`** (same bootstrap as Claude Code; ensure the shim is executable: **`chmod +x hooks/session-start`**)

## Differences from Claude Code

- Hook config uses `hooks-cursor.json` (snake_case keys) instead of `hooks.json`
- Session-start output uses `additional_context` (snake_case) instead of `hookSpecificOutput.additionalContext`
- `.cursorrules` provides additional project context (Claude Code uses `CLAUDE.md`)

## Plan mode vs Agent mode (Cursor UI)

Cursor exposes **Plan** vs **Agent** in the UI. Map them to Forge’s portable **planning-style** vs **execution-style** phases — see **[`session-modes-forge.md`](session-modes-forge.md)** (same convention for every supported host).

**Quick map:** **`/intake`**, **`/council`**, **`/plan` review** → Plan. **`/build`**, **`/eval`**, **`/heal`** → Agent. Hooks cannot toggle this for you.

## Limitations
- Hook format differences require separate config file (`hooks-cursor.json`)
- Some advanced Claude Code features may not be available

## Troubleshooting

### `install.sh` did not install Forge for Cursor (auto-detect skipped Cursor)

Auto-detect looks for the **`cursor`** shell command, a **`~/.cursor`** directory (after you have opened Cursor at least once), or **Cursor.app** under `/Applications` or `~/Applications` (macOS). On a brand-new machine with none of those, run an explicit install:

```bash
cd ~/forge && bash scripts/install.sh --platform cursor
```

That creates `~/.cursor/plugins/local/forge` and `~/.cursor/rules/forge.mdc` even before first launch. In Cursor, use **Command Palette → “Shell Command: Install 'cursor' command in PATH”** so future auto-detect works.

### Duplicate or nested `skills/` (agents read stale intake)

Same issue as other merged-tree installs — see **[`plugin-skill-layout.md`](plugin-skill-layout.md)**.

**Quick check (Cursor):**

```bash
bash scripts/verify-forge-plugin-install.sh --platform cursor
```

**`.cursorrules` not loading:**
- Verify the file exists at repo root: `ls -la .cursorrules`
- Restart Cursor after adding the file

**Hook not firing:**
- Check `hooks/hooks-cursor.json` is valid JSON
- Verify `CURSOR_PLUGIN_ROOT` env var is set during hook execution

### `git commit` fails with `unknown option 'trailer'` (Cursor + old Git)

Cursor can invoke **`git commit --trailer 'Made-with: Cursor' …`**. That needs a **recent Git** (roughly **2.32+**). On older distros (e.g. **2.25**), the commit aborts before hooks run.

**Fix (pick one or combine):**

1. **Turn off commit attribution in Cursor** — **Cursor Settings** (not VS Code) → **Agents** → **Attribution** → disable **Commit Attribution** (and **PR Attribution** if you want). Restart Cursor. See also [Cursor forum: trailer / attribution](https://forum.cursor.com/t/trailer-in-git-commit-messages-cant-be-stopped/150552).
2. **CLI / agent** — In **`~/.cursor/cli-config.json`**, set **`"attribution": { "attributeCommitsToAgent": false, "attributePRsToAgent": false }`** (field names match [Cursor CLI config](https://cursor.com/docs/cli/reference/configuration)); run **`cursor /update-cli-config`** if the IDE should sync into the CLI.
3. **Upgrade Git** on the machine so **`git commit --trailer`** is supported even if attribution stays on.
4. **Commit outside the agent** — run **`/usr/bin/git commit`** from a plain terminal with a normal **`-m`** message (no Cursor wrapper), or upgrade Git first.

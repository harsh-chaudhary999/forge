# Plugin skill layout (all IDEs that copy `skills/`)

Some Forge installs ship a **merged** tree:

```text
<plugin-root>/skills/<skill-name>/SKILL.md
```

That layout is used by **Cursor** (`~/.cursor/plugins/local/forge`), **Claude Code** (`~/.claude/plugins/cache/forge-plugin/forge/<version>/`), and **OpenCode** when it falls back to a file copy under `~/.opencode/plugins/forge/` (when not symlinked to the full repo).

After **`git pull`** in your Forge repo, **re-run `install.sh` for each IDE** you use so merged `skills/` trees are replaced — see **[README Section 4 — Keeping Forge updated](../../README.md#4-keeping-forge-updated-how-you-hear-about-changes)** and the other pages under **`docs/platforms/`**.

## What goes wrong

If a **nested** directory appears:

```text
<plugin-root>/skills/skills/...
```

it is **not** produced by current Forge `scripts/install.sh`. It usually comes from a **bad manual copy**, an **old installer**, or a **merge-style `cp`**. Tools or humans may then open a **stale** `intake-interrogate` (e.g. missing **Q9 / design**).

## Fix

1. Re-install from a current Forge clone so `install.sh` can **replace** the `skills/` tree (see `scripts/install.sh` — Cursor, Claude Code, and OpenCode fallback paths **remove** `skills/` before copy).

2. Run the verifier:

```bash
cd /path/to/forge
bash scripts/verify-forge-plugin-install.sh --all
# or one platform:
bash scripts/verify-forge-plugin-install.sh --platform cursor
bash scripts/verify-forge-plugin-install.sh --platform claude-code
bash scripts/verify-forge-plugin-install.sh --platform opencode
# or custom root:
bash scripts/verify-forge-plugin-install.sh --root /path/to/plugin-with-skills
```

Exit **1** if `skills/skills/` exists or `intake-interrogate/SKILL.md` is missing **Q9** markers (`design_intake_anchor`, design source-of-truth text).

## Antigravity / Gemini link installs

**Antigravity** installs per-skill symlinks under `~/.gemini/antigravity/skills/forge/<skill>/` — there is **no** single merged `skills/` parent in that mode, so this verifier’s **`--platform`** checks may **skip** Antigravity. The canonical files still live in the **Forge repo** `skills/`; symlinks should point there.

## Why `verify-forge-plugin-install.sh` does not cover every README editor

The script checks **one layout**: a plugin (or home) directory whose **`skills/`** subtree is a **full merged copy** of Forge’s canonical `skills/<name>/SKILL.md` tree. Only hosts that install that way get `--platform` entries today.

| Editor / host | Typical Forge material on disk | Merged `skills/` tree to scan? |
|---|---|---|
| **Cursor** | `~/.cursor/plugins/local/forge/skills/` (copy) | Yes → `--platform cursor` |
| **Claude Code** | `~/.claude/plugins/cache/forge-plugin/forge/<ver>/skills/` (copy) | Yes → `--platform claude-code` |
| **OpenCode** | `~/.opencode/plugins/forge/` may symlink the repo **or** copy `skills/` | Yes when a real `skills/` dir exists → `--platform opencode` |
| **Antigravity (global)** | Per-skill links under `~/.gemini/antigravity/skills/forge/<skill>/` | No single merged parent; verifier skips |
| **Antigravity (repo)** | `.agent/skills/*` → `../../skills/<skill>` (symlinks in this repo) | Different shape; keep symlinks in sync with `skills/` (see `docs/platforms/antigravity.md`) |
| **Gemini CLI / IDX** | Extension / project wiring via `gemini-extension.json` | No standard merged Forge plugin `skills/` path |
| **Codex** | Root `AGENTS.md` (+ optional rules); no bundled `skills/` tree | No |
| **Copilot CLI** | Session hooks + env; skills live in Forge clone or elsewhere | No |
| **JetBrains** | Manual `templates/junie-guidelines.md` → user guidelines | No |

Adding `--platform` for those hosts would mean **guessing or standardizing paths that do not exist yet** in Forge’s installer, or duplicating checks that belong in other docs (e.g. “AGENTS.md present”, “hook JSON valid”). When a host later ships a **single** `skills/` directory we can document and detect, extend `verify-forge-plugin-install.sh` and `--all` in one place.

## Codex / Copilot CLI / JetBrains

These paths often **do not** use a merged Forge `skills/` directory in the home plugin layout the same way; use this doc when your platform **does** copy `skills/<name>/` into a plugin root.

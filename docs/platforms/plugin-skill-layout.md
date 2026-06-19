# Plugin skill layout (Claude Code)

`install.sh` ships a **merged** skill tree into the Claude Code plugin cache:

```text
~/.claude/plugins/cache/forge-plugin/forge/<version>/skills/<skill-name>/SKILL.md
```

After **`git pull`** in your Forge clone, **re-run `install.sh`** so the merged
`skills/` tree is replaced (it removes `skills/` before copying) — see
**[README Section 4 — Keeping Forge updated](../../README.md#4-keeping-forge-updated-how-you-hear-about-changes)**.

## What goes wrong

If a **nested** directory appears:

```text
.../forge/<version>/skills/skills/...
```

it is **not** produced by current `scripts/install.sh`. It usually comes from a
**bad manual copy**, an **old installer**, or a **merge-style `cp`**. Tools or humans
may then open a **stale** `intake-interrogate` (e.g. missing **Q9 / design**).

## Fix

1. Re-install from a current Forge clone so `install.sh` can **replace** the
   `skills/` tree.
2. Run the verifier:

```bash
cd /path/to/forge
bash scripts/verify-forge-plugin-install.sh --platform claude-code
# or: --all  |  --root /path/to/plugin-with-skills
```

Exit **1** if `skills/skills/` exists, the `.claude/hooks` + `.claude/skills`
layout is missing, the scanner (`tools/forge_scan.py`) is absent, or
`intake-interrogate/SKILL.md` is missing its **Q9** markers
(`design_intake_anchor`, design source-of-truth text).

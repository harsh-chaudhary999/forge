# Contributing to Forge

## Forks and remotes

- **Clone URL:** Use **`https://github.com/<YOUR_GITHUB_ORG_OR_USERNAME>/forge`** (replace with your fork or the upstream you trust). Platform docs and `README.md` use the same placeholder.
- **Brain CI sparse-checkout** (when copying [**forge-brain-guard.yml**](../.github/workflows/forge-brain-guard.yml) into a brain repo): set GitHub Actions variable **`FORGE_TOOLS_REPO`** to **`owner/repo`** of the Forge clone that hosts `tools/verify_forge_task.py`. If unset, the workflow defaults to **`harsh-chaudhary999/forge`** so out-of-the-box copies keep working.
- **Publishing a plugin fork:** Update **`package.json`**, **`gemini-extension.json`**, and **`.*-plugin/plugin.json`** `homepage` / `repository` fields if you want npm / marketplace metadata to point at your fork.

## Skill catalog count

From the Forge repo root:

```bash
bash scripts/count-skills.sh
```

Use this instead of hardcoding a number in docs or runbooks.

## Git history

- **Avoid squashing unrelated work into a single commit on `main`.** Large squashes make **`git bisect`**, code review, and revert archaeology painful.
- Prefer **merge commits** or **stacked branches** with one theme per PR so history stays navigable.
- **Do not rewrite published `main`** (force-push to “unsquash”) without explicit team agreement — it breaks clones and open branches.

## Hooks and scripts

- After changing **`.claude/hooks/session-start.cjs`**, **`pre-tool-use.cjs`**, **`post-commit.cjs`**, or **`forge-stage-detect.cjs`**, run **`node .claude/hooks/test-forge-stage-detect.cjs`** when stage detection changed, and **`node --check .claude/hooks/<file>.cjs`** for syntax (CI runs **`node --check`** on session-start, pre-tool-use, and post-commit when those files change).
- Set **`FORGE_HOOKS_DEBUG=1`** when validating which **`conductor.log`** path and stage were selected.

### Manual checklist (session-start)

1. Export **`FORGE_HOOKS_DEBUG=1`** (and optionally **`FORGE_TASK_ID=<task-id>`**).
2. Start a Claude Code session from the Forge repo (hook runs).
3. Confirm stderr shows **`conductor.log selection:`** (task-scoped vs mtime) and **`→ stage:`** matching the **last** `[P…]` line in that log.
4. With a log that ends in **`[P4.4-EVAL-RED]`**, expect stage **`eval`**; with **`[P4.4-EVAL-GREEN]`**, expect **`pr`**.
5. CI runs **`node .claude/hooks/test-forge-stage-detect.cjs`** via **`.github/workflows/forge-hooks.yml`** on hook changes.

## Skills

- New skills must follow **`forge-skill-anatomy`** and **`skills/forge-writing-skills/SKILL.md`** (frontmatter, HARD-GATE text where applicable).
- Optional / experimental skills should be listed in **`docs/adjunct-skills.md`** so they do not compete silently with **`conductor-orchestrate`**.

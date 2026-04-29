---
name: doctor
description: "Host install health — plugin trees, Claude hooks symlink, settings.json forge hook counts, Cursor global rules freshness. Read-only."
---

Run **`bash ~/forge/scripts/forge-doctor.sh`** from your Forge clone (or **`bash scripts/forge-doctor.sh`** when cwd is the repo).

Interprets output: **`OK`** lines pass; **`WARN`** means re-run **`bash scripts/install.sh`** for your IDE (`--platform cursor` / `--platform claude-code`); **`ERROR`** from the nested verifier means broken plugin layout.

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** (**`using-forge`** **Horizon narration**) — in dialogue, only the **immediate** next prerequisite unless the user asks what comes later or the current step truly depends on a downstream artifact.

**Forge plugin scope:** local machine paths only; does not read product code.

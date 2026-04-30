---
name: doctor
description: "Host install health — plugin trees, Claude hooks symlink, settings.json forge hook counts, Cursor global rules freshness. Read-only."
---

Run **`bash ~/forge/scripts/forge-doctor.sh`** from your Forge clone (or **`bash scripts/forge-doctor.sh`** when cwd is the repo).

Interprets output: **`OK`** lines pass; **`WARN`** means re-run **`bash scripts/install.sh`** for your IDE (`--platform cursor` / `--platform claude-code`); **`ERROR`** from the nested verifier means broken plugin layout.

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns, **no defensive downstream-gate narration** mid-elicitation — **`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration (repo-wide)**); **one blocking affordance per unrelated fork** (no bundled prose obligations); **no dual prompts** — **never** **`AskQuestion`** / **Questions** widget on **one** topic **and** a **long markdown question** on **another** in the **same** message; **no chat–widget duplicate** — long lists / same question body **once** in **chat**; **`AskQuestion`** = **short** title + **options** only (**`docs/forge-one-step-horizon.md`** **Chat vs `AskQuestion` / Questions widget**); **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

**Forge plugin scope:** local machine paths only; does not read product code.

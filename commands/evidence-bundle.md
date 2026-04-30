---
name: evidence-bundle
description: "Pack brain task artifacts into a tar.gz + manifest (SHA256 + brain git rev) for audit or handoff."
---

Invoke:

```bash
python3 ~/forge/tools/forge_evidence_bundle.py --task-id <task-id> --brain ~/forge/brain
```

Optional: **`--out /path/to/out.tar.gz`**, **`--full`** to include the entire **`prds/<task-id>/`** tree (default packs key paths: PRD, spec, logs, tech-plans, eval, qa, latest qa-run-report).

Writes **`forge-evidence-<task>-<ts>.tar.gz`** and a sidecar **`.manifest.json`** in the current directory unless **`--out`** is set.

**Assistant chat:** Follow **`docs/forge-one-step-horizon.md`** and **`skills/using-forge/SKILL.md`** — **one-step horizon**; **question-forward** elicitation (no unsolicited command/skill-reference **preface**, no **later-stage** status **suffix** on single-answer turns, **no defensive downstream-gate narration** mid-elicitation — **`docs/forge-one-step-horizon.md`** **No defensive downstream-gate narration (repo-wide)**); **one blocking affordance per unrelated fork** (no bundled prose obligations); **no dual prompts** — **never** **`AskQuestion`** / **Questions** widget on **one** topic **and** a **long markdown question** on **another** in the **same** message; **no chat–widget duplicate** — long lists / same question body **once** in **chat**; **`AskQuestion`** = **short** title + **options** only (**`docs/forge-one-step-horizon.md`** **Chat vs `AskQuestion` / Questions widget**); **phase-specific** waivers/ordering **only** where this doc and the active skill say; **Multi-question elicitation** (items **4–8**) & **Blocking interactive prompts**.

**Forge plugin scope:** brain paths only; never packs product repo `.env` files.

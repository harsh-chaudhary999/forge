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

**Forge plugin scope:** brain paths only; never packs product repo `.env` files.

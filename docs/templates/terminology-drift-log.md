# terminology-drift-log (optional per task)

**Path:** `~/forge/brain/prds/<task-id>/qa/terminology-drift-log.md` (optional; **not** a substitute for the **Revision** table in `terminology.md`).

Use when eval/QA work discovers a **mismatch** between expected text in **`qa/semantic-automation.csv`** (or driver traces), the running app, and `terminology.md` **before** you are ready to edit the canonical term sheet. Each row: **date**, **source** (file + id), **observed vs canonical**, **resolution** (link to `terminology.md` revision or pending).

**Preferred default:** add a **Revision** row in **`terminology.md`** and fix YAML; open this file only if the team wants driver-output audit separate from the term table.

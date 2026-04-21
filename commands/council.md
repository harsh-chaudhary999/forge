---
description: "Run multi-surface council — negotiate contracts across backend, web, app, and infra"
---

Invoke the `forge-council-gate` skill to run the multi-surface council.

This requires a locked PRD from intake. If no locked PRD exists for the current task, direct the user to run `/intake` first.

The council invokes 4 surface reasoning skills (backend, web, app, infra) and negotiates cross-service contracts (REST APIs, DB schemas, events, cache, search). Unresolvable conflicts are escalated to the dreamer for inline resolution.

**Session style:** Prefer **planning-style** for `/council`. See **`docs/platforms/session-modes-forge.md`**.

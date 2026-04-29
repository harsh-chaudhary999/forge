---
name: product-context-load
description: "WHEN: You have a locked PRD and need to validate the target product exists, load its topology, and list affected projects."
type: rigid
requires: [brain-read]
version: 1.0.2
preamble-tier: 2
triggers:
  - "load product context"
  - "read forge-product.yaml"
  - "load product config"
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# Product Context Load

## Human input (all hosts)

This skill lists **`AskUserQuestion`** in **`allowed-tools`** — canonical for Claude Code and skill lint. Map to the host’s **blocking interactive prompt** per **`skills/using-forge/SKILL.md`** **Blocking interactive prompts** (Cursor **`AskQuestion`**; hosts without the tool: **numbered options + stop**). See **`using-forge`** **Interactive human input**.

**Cross-cutting assistant dialogue:** **`docs/forge-one-step-horizon.md`** — **`using-forge`** **Multi-question elicitation** items **4–8**.

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "I already know this product's repos" | Products change between PRDs — repos get added, services get decomposed, stacks get migrated. Always reload from brain. |
| "The PRD mentions the repos, I don't need product.md" | PRDs describe features, not topology. product.md is the canonical source for repos, services, stacks, and deployment strategies. |
| "I'll skip validation, the product definitely exists" | Typos in product slugs and stale PRD references cause silent failures downstream. Validate existence before proceeding. |
| "I only need the backend repo for this change" | Even single-repo changes may affect other services through contracts. Load the full topology to see the impact radius. |
| "Product context is just metadata, not critical" | Every downstream phase (council, tech plans, eval) uses product context. Wrong context means wrong contracts, wrong plans, wrong eval. |

**If you are thinking any of the above, you are about to violate this skill.**

## Iron Law

```
PRODUCT CONTEXT IS LOADED FROM THE BRAIN FILE ON EVERY INVOCATION — NEVER FROM MEMORY OR CHAT HISTORY. WRONG TOPOLOGY MEANS WRONG CONTRACTS, WRONG PLANS, AND WRONG EVAL.
```

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Product slug from PRD doesn't match any directory in `~/forge/brain/products/`** — Unregistered product will cause all downstream phases to fail. STOP. Ask user to create forge-product.md or fix the PRD slug before proceeding.
- **Product context is loaded from memory or chat history instead of reading the brain file** — Memory is stale. Brain files are authoritative. STOP. Read `~/forge/brain/products/<slug>/product.md` fresh on every load.
- **Product topology lists repos that no longer exist in git** — Stale product.md causes tech plan tasks to fail. STOP. Validate each repo path exists before returning context.
- **PRD mentions a repo not in product.md** — Either the repo should be added to product.md or the PRD has a typo. STOP. Reconcile before proceeding to council.
- **Product context is loaded after council has already started** — Council needs topology to identify affected surfaces. STOP. Always load product context before invoking any surface reasoning.
- **Service start/stop commands in product.md are not verified** — Wrong startup commands make eval-product-stack-up fail. STOP. Verify commands are executable before surfacing to downstream phases.
- **A project has neither `deploy_doc` nor (`start` and `health`)** — Stack-up has no runbook. STOP. Send the user back to `/workspace` Step 3b or `/scan` Step 1 to record deploy truth before council or eval that needs a live stack.
- **Git discovery (step 7) skipped when Q10 applies or multi-repo ambiguity exists** — Implementers will optimize for brain-only artifacts and miss in-repo reference branches. STOP. Append branch listing for each in-scope repo before marking context load complete (see **`intake-interrogate` Q10** for when closure / discovery matter).

Given a product slug (from the locked PRD), load and validate:

1. **Find the product.md**
   ```bash
   cd ~/forge/brain
   cat products/<slug>/product.md
   ```
   If not found, stop. User must write and commit forge-product.md first.

2. **Parse the projects**
   The product.md lists projects: backend-api, web-dashboard, app-mobile, etc.
   Each project has: repo path, role (backend/web/app/infra), language, framework, deploy_strategy.

3. **Validate repos exist**
   ```bash
   for project in $(grep -A 2 "^### " product.md | grep -v "^--" | awk '{print $2}'); do
     if [ ! -d $(grep -A 1 "^### $project" product.md | grep "repo:" | awk '{print $2}') ]; then
       echo "ERROR: Repo for $project not found"
     fi
   done
   ```

4. **Check circular dependencies**
   Read `depends_on` for each project. If A depends on B and B depends on A, stop.

5. **Load contracts**
   ```bash
   cat products/<slug>/contracts/api-rest.md
   cat products/<slug>/contracts/schema-mysql.md
   # ... etc
   ```

6. **Load codebase scan if present**

   After loading contracts, check for a codebase scan:
   ```bash
   ls ~/forge/brain/products/<slug>/codebase/SCAN.json 2>/dev/null
   ```

   If found, **verify integrity first** (catches half-written scans / missing markdown consolidation). Run **`python3 tools/verify_scan_outputs.py …`** up to **3** times with **1s** pause between attempts (same check the CLI runs after `forge_scan`; retries cover slow disks). If **all attempts fail**, write to `context-loaded.md`: **`SCAN_INCOMPLETE: re-run /scan <slug>`** and treat the scan as **not usable** for file-level tech planning until fixed — do not silently fall back to ad-hoc repo walks without stating the gap.

   If verification passes, read and surface key scan data into context:
   ```bash
   cat ~/forge/brain/products/<slug>/codebase/SCAN.json
   cat ~/forge/brain/products/<slug>/codebase/index.md
   ```

   `SCAN.json` may list each repo under **`repos.<role>`** (with top-level fields aggregated across roles). Use those entries when you need per-role `scanned_at`, `commit`, or file counts.

   Extract and record:
   - **Last-scanned timestamp** — warn if older than 7 days: `⚠️ Codebase scan is N days old — run /scan to refresh before planning`
   - **Architecture style** — include in context-loaded.md so council surfaces get it
   - **Tier 1 hubs** — files referenced by 5+ modules (architectural load-bearing structures)
   - **Module count** — scope indicator for tech plan complexity

   If codebase scan is absent:
   - Add a note to context-loaded.md: `⚠️ No codebase scan found — run /scan <slug> before council to give surface agents architecture context`
   - Do NOT block or fail — scan is advisory, not required for first-time setup

   **Downstream routing (pass this forward in context):** Any phase that must name **concrete files** in product repos (council, tech-plan, eval YAML, design notes) should **take filenames and module boundaries from this scan output first** (`index.md`, `modules/*.md`, `api-surface.md`, hub lists in `SCAN.json`). Repo tree exploration is a **fallback** when scan is absent, stale, or a path is provably wrong after checking brain.

7. **Git / branch discovery (feeds conductor State 2.5)**

   For **each** repo path validated in step 3, record read-only git facts into `context-loaded.md` (or `discovery.md` if the orchestrator prefers a split file):

   ```bash
   cd <repo-path> && git rev-parse --show-toplevel && git status -sb && git rev-parse --short HEAD
   git branch -a 2>/dev/null | head -80
   ```

   Optional: `git branch -a | grep -iE '<slug-from-PRD-or-feature-keywords>'` when **`implementation_reference`** in `prd-locked.md` is unknown or `none`.

   **Purpose:** Surfaces existing topic / release / integration branches (including common naming patterns per team) so council and tech plans do not assume greenfield when a canonical implementation already exists. **Do not** checkout or merge — discovery only.

   **Adjacency (State 2.6):** When the orchestrator reaches **State 2.6**, follow **`docs/adjacency-and-cohorts.md`** (CLI + log line). If the scan cannot run, note **`ADJACENCY_SCAN_SKIPPED: <reason>`** in `context-loaded.md` so **`[ADJACENCY-SCAN] … SKIPPED`** can be logged.

8. **Output**
   Write to `~/forge/brain/prds/<task-id>/context-loaded.md`:
   ```markdown
   # Product Context Loaded

   **Product:** ShopApp  
   **Repos:**
   - backend-api (Node/Express, depends: shared-schemas)
   - web-dashboard (TypeScript/Next.js, depends: backend-api)
   - app-mobile (Kotlin, depends: backend-api)
   - shared-schemas (Protobuf, depends: none)

   **Contracts:**
   - api-rest.md — REST versioning, v1 active, v2 in development
   - schema-mysql.md — 5 tables, migrations backward-compat
   - cache-redis.md — session keys, 24h TTL

   **Deployment:** pm2-ssh to shopapp-prod-1

   **Codebase Scan:** last-scanned 2026-04-15 (0 days ago)
   - Architecture: layered (controller → service → repository)
   - Modules: 14 (6 Tier 1 hubs: auth, database, user-service, payment, order, notification)
   - ⚠️ Recommend refreshing before next council: `/scan shopapp`
   <!-- OR if scan absent: -->
   - ⚠️ No scan found — run `/scan shopapp` before council

   Validation: ✅ All repos exist, ✅ no circular deps, ✅ contracts coherent
   ```

9. **Commit**
   ```bash
   git -C ~/forge/brain add prds/<task-id>/context-loaded.md
   git -C ~/forge/brain commit -m "context: load product topology for <task-id>"
   ```

---

## Edge Cases & Fallback Paths

### Edge Case 1: Product config doesn't exist

**Diagnosis**: Product slug from PRD (e.g., "shopapp") maps to `~/forge/brain/products/shopapp/product.md`, but the file doesn't exist.

**Response**:
- **Escalate to user**: "Product 'shopapp' configuration not found. Do you have a `product.md` file for this product?"
- **Options**:
  1. User provides the file: Import it, validate, proceed.
  2. User asks to create it: Escalate with template: "We need: product name, repos list, contracts, deployment strategy."
  3. User says "use a different product": Update PRD slug, try again.

**Escalation**: BLOCKED - Cannot load context without product config. Ask user to provide or create product.md.

---

### Edge Case 2: Repos in config are missing (path doesn't exist)

**Diagnosis**: Product config lists `repo: /home/user/shopapp/backend-api`, but that directory doesn't exist.

**Response**:
- **Detect**: Run validation loop. Log each missing repo.
- **Report**: "Repos missing: [list]. Reasons could be: paths are wrong, repos need to be cloned, product config is outdated."
- **Recovery options**:
  1. **Update paths**: If repos exist but paths are wrong, fix the config.
  2. **Clone repos**: If repos exist remotely but not locally, run `git clone` for each.
  3. **Update config**: If repos have been renamed/moved, update product config.
- **Escalate**: If repos don't exist anywhere, escalate to user: "Repos listed in config don't exist. Should we create them or update the config?"

**Escalation**: BLOCKED - Cannot validate topology without accessible repos. Ask user to clone or update config.

---

### Edge Case 3: Circular dependencies detected (A → B → C → A)

**Diagnosis**: Product config shows: backend-api depends on web-dashboard, web-dashboard depends on shared-schemas, shared-schemas depends on backend-api.

**Response**:
- **Detect**: Topological sort of dependencies. If cycle found, flag it.
- **Report**: "Circular dependency detected: [A → B → C → A]. This will cause issues during deployment/planning."
- **Escalation**: Cannot proceed with circular deps. Ask user: "Should we break the cycle? Options: 1) Remove one dependency, 2) Extract shared code to separate module, 3) Update config to reflect actual dependencies."

**Escalation**: BLOCKED - Circular dependencies must be resolved before proceeding. User must decide which dependency to remove.

---

### Edge Case 4: Versions are incompatible (schema v2 requires API v3, but API is only v2)

**Diagnosis**: Product has schema version 2.0 contract and API version 2.0 contract, but reading the contracts reveals: schema v2.0 depends on API v3.0 features not yet available.

**Response**:
- **Detect**: Load all contracts. Check version requirements/constraints.
- **Report**: "Version incompatibility: Schema v2.0 requires API ≥v3.0, but API is v2.0. Options: 1) Downgrade schema to v1.0, 2) Upgrade API to v3.0, 3) Defer this feature until API is upgraded."
- **Decision**: User chooses. Update config to lock chosen versions.

**Escalation**: BLOCKED - Incompatible versions must be resolved. If decision requires external coordination (API team owns upgrade), escalate to user: "Incompatibility requires coordination with API team. Should we defer this PRD or plan cross-team upgrade?"

---

### Edge Case 5: Contracts are incoherent or missing critical info

**Diagnosis**: Contracts are loaded but some are incomplete (e.g., REST contract missing versioning strategy, DB contract missing migration instructions).

**Response**:
- **Detect**: Validate each contract against a checklist (e.g., REST contracts must have version, deprecation policy).
- **Report**: "Incomplete contracts: [list issues]. Examples: API contract missing version field, cache contract missing TTL strategy."
- **Recovery**:
  1. **Fill in missing info**: If it's a known fact, add it to the contract.
  2. **Escalate for clarification**: If it's unknown, escalate to domain expert.
  3. **Defer contract**: If not critical for current PRD, mark as "to be negotiated during council phase".

**Escalation**: NEEDS_CONTEXT - Ask domain experts (backend, infra, web) to provide missing contract details, or proceed with incomplete contracts if they're not on the critical path for this PRD.

---

## Commit
   ```bash
   git -C ~/forge/brain add prds/<task-id>/context-loaded.md
   git -C ~/forge/brain commit -m "context: load product topology for <task-id>"
   ```

Next: Council reasoning.

## Checklist

Before advancing to council:

- [ ] Product slug validated — `~/forge/brain/products/<slug>/product.md` exists
- [ ] All listed repos validated — each path exists on disk
- [ ] Circular dependencies checked — topological sort passes without cycles
- [ ] All contracts loaded — api-rest, schema-mysql, cache, event, search as applicable
- [ ] Incompatible version constraints identified and escalated if found
- [ ] Codebase scan checked — either **`verify_scan_outputs.py` PASS** + loaded (with staleness warning if >7 days), **`SCAN_INCOMPLETE`** noted if verify fails, or absence flagged in context-loaded.md
- [ ] context-loaded.md written and committed to `~/forge/brain/prds/<task-id>/`

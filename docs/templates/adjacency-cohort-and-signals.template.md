# Adjacency, cohort, signal, and risk tables (split into brain paths below)

**Install**

- `mkdir -p ~/forge/brain/prds/<task-id>/touchpoints`
- `mkdir -p ~/forge/brain/prds/<task-id>/parity` (only if using Part C)

Copy each **Part** into the named file, or keep one working doc and split at lock time. Canonical workflow: **`docs/adjacency-and-cohorts.md`**.

---

## Part A — save as `touchpoints/COHORT-AND-ADJACENCY.md`

**Purpose:** Lock **who** is in scope per **segment** and how UX/API/jobs differ. Pair with **`discovery-adjacency.md`** (tool or agent-led `rg`) so each hit is a touchpoint row or **waiver**.

### A.1 Cohort matrix (USER / PO — not SPEC_INFERENCE)

| Segment / cohort | In scope? | UX / API difference? | Batch / cron touches? | Owner confirmed |
|------------------|-----------|----------------------|------------------------|-----------------|
| | | | | |

**Rule:** Product-visible segmentation rows need **`USER:`** / **`PO:`** / **`TL:`** or **`WAIVER:`** — not **`SPEC_INFERENCE`** only.

### A.2 Adjacent pipelines & collisions

| Adjacent domain | Overlapping flags / tables / topics | R/W | Exclusion / ordering | Evidence |
|-----------------|-------------------------------------|-----|----------------------|----------|
| | | | | |

### A.3 Cron collision table (when applicable)

| Job / schedule | Touches | Same artifacts as this PRD? | Ordering / mutex | Waiver |
|----------------|---------|-------------------------------|------------------|--------|
| | | | | |

### A.4 Waivers

- Owner + ticket for waived segments or adjacency.

---

## Part B — save as `touchpoints/PRD-SIGNAL-REGISTRY.md`

**Purpose:** Map PRD **trust / persistence** lines to **table.column**, **topic+schema**, **cache key**, **index field**, or **eval fixture id**.

### B.1 Registry

| PRD section / line id | Signal type | Anchor | Owner repo | Verified by |
|-----------------|-------------|--------|------------|-------------|
| | | | | |

### B.2 Gaps

- **`GAP:`** / **`WAIVER:`** rows Council must close before spec-freeze.

---

## Part C — save as `parity/risk-register.md` (optional)

**Purpose:** “What we might break” — complements **`spec-freeze`** Step 0 parity artifacts.

### C.1 Risks

| Risk area | What could break | Mitigation / test | Owner | Status |
|-----------|------------------|-------------------|-------|--------|
| | | | | |

### C.2 DB / store ownership (when persistence is in scope)

| Catalog / pool | ORM / access layer | Notes | Confirmed by |
|----------------|-------------------|-------|--------------|
| | | | |

### C.3 FK / value matrix (cross-store)

| FK / reference | Allowed values | Source of truth | Confirmed by |
|----------------|----------------|-----------------|--------------|
| | | | |

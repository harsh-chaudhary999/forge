---
name: pr-set-merge-order
description: "WHEN coordinated PRs exist across multiple repos and you need to determine the safe merge sequence before pr-set-coordinate executes merges."
type: rigid
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers:
  - "PR merge order"
  - "which PR merges first"
  - "sequence PR merges"
allowed-tools:
  - Bash
  - Write
---

# PR Set Merge Order — Dependency-Aware Merge Sequencing

## Purpose

Given N coordinated PRs across multiple repos, this skill builds a dependency graph from shared-dev-spec contracts and outputs a strict, validated merge order. The output feeds directly into pr-set-coordinate for execution.

**Input:** Shared-dev-spec with affected projects, contract definitions (schema, API, event, cache)
**Output:** Ordered merge list with wait gates, validated for cycles and completeness

---

## Anti-Pattern Preamble: Why Agents Get Merge Order Wrong

| Rationalization | The Truth |
|---|---|
| "These two repos don't really depend on each other, I can merge them in parallel" | If they share any contract (schema, API, event), one MUST merge first. Hidden dependencies cause post-merge breakage that is expensive to unwind. |
| "The backend change is backward-compatible, so merge order doesn't matter" | Backward compatibility is a claim until proven by CI on the merged result. Merge order enforces proof before proceeding. |
| "Schema changes are trivial, I'll merge them alongside the backend" | Schema changes are the foundation. Every other layer reads from schema. Merge schema first, verify, then proceed. Trivial changes cause non-trivial cascading failures. |
| "CI passed on the feature branch, so it will pass after merge too" | Feature branch CI runs against the branch base, not against the state after upstream merges. Post-merge CI is the only valid signal. |
| "I'll merge everything at once and fix failures after" | Simultaneous merges make failure attribution impossible. If 3 repos break after 3 merges, you cannot tell which merge caused which failure. Serial merge with gates isolates blame. |
| "The frontend doesn't touch the database, so it has no dependency on schema" | Frontend depends on API. API depends on schema. Transitive dependencies are real dependencies. The full graph must be resolved. |
| "We merged out of order last time and it was fine" | Empirical luck is not a merge strategy. The next out-of-order merge may corrupt production data. Follow the graph every time. |

---

## Iron Law

```
THE MERGE ORDER IS DETERMINED BY THE DEPENDENCY GRAPH, NOT INTUITION. NO PARALLEL MERGES. NO SKIPPED WAIT GATES. EVERY MERGE WAITS FOR THE PREVIOUS MERGE'S CI TO PASS.
```

## HARD-GATE: NO PARALLEL MERGES — STRICT DEPENDENCY ORDER ONLY

Every merge in the chain MUST wait for the previous merge to complete AND its post-merge CI to pass before the next merge begins. No exceptions. No "they're independent enough." If the dependency graph says A before B, A merges first. Period.

**Violation of this gate requires escalation to dreamer. No agent may override.**

---

## Step 1: Build Dependency Graph from Contracts

Read shared-dev-spec and all contract definitions to build the project dependency DAG.

```bash
# Read affected projects from brain
AFFECTED=$(brain-read --key "shared-dev-spec.affected_projects")
# Example: "shared-schemas,backend-api,web-dashboard,app-mobile"

# For each project, identify what it PRODUCES and what it CONSUMES
# Sources: contract-schema-db, contract-api-rest, contract-event-bus, contract-cache

# Build adjacency list: edge A -> B means "A must merge before B"
declare -A DEPENDS_ON
# Example edges derived from contracts:
# shared-schemas produces: DB schema, domain types
# backend-api consumes: DB schema, domain types -> depends on shared-schemas
# backend-api produces: REST API endpoints
# web-dashboard consumes: REST API endpoints -> depends on backend-api
# app-mobile consumes: REST API endpoints -> depends on backend-api

DEPENDS_ON["backend-api"]="shared-schemas"
DEPENDS_ON["web-dashboard"]="backend-api"
DEPENDS_ON["app-mobile"]="backend-api"
# shared-schemas has no dependencies (root node)
```

### Contract Sources for Dependency Edges

| Contract Type | Skill | Produces | Consumed By |
|---|---|---|---|
| DB Schema | contract-schema-db | Tables, columns, migrations | Backend services |
| REST API | contract-api-rest | Endpoints, request/response shapes | Frontends, other backends |
| Event Bus | contract-event-bus | Topics, event schemas | Any subscriber service |
| Cache | contract-cache | Key patterns, TTL, invalidation | Any cache consumer |

**Rule:** If project B's contract references any artifact produced by project A's contract, then A -> B is a dependency edge.

---

## Step 2: Topological Sort (Merge Order Algorithm)

Apply Kahn's algorithm to produce a linear merge order from the DAG.

```bash
topological_sort() {
  local -A in_degree
  local -a queue=()
  local -a sorted=()

  # Initialize in-degree for all affected projects
  for project in $(echo "$AFFECTED" | tr ',' ' '); do
    in_degree[$project]=0
  done

  # Count incoming edges
  for project in "${!DEPENDS_ON[@]}"; do
    for dep in $(echo "${DEPENDS_ON[$project]}" | tr ',' ' '); do
      in_degree[$project]=$(( ${in_degree[$project]} + 1 ))
    done
  done

  # Enqueue projects with in-degree 0 (no dependencies — roots)
  for project in "${!in_degree[@]}"; do
    if [[ ${in_degree[$project]} -eq 0 ]]; then
      queue+=("$project")
    fi
  done

  # Process queue
  while [[ ${#queue[@]} -gt 0 ]]; do
    local current="${queue[0]}"
    queue=("${queue[@]:1}")
    sorted+=("$current")

    # For each project that depends on current, decrement in-degree
    for project in "${!DEPENDS_ON[@]}"; do
      if [[ "${DEPENDS_ON[$project]}" == *"$current"* ]]; then
        in_degree[$project]=$(( ${in_degree[$project]} - 1 ))
        if [[ ${in_degree[$project]} -eq 0 ]]; then
          queue+=("$project")
        fi
      fi
    done
  done

  # Cycle detection: if sorted list is shorter than project count, cycle exists
  if [[ ${#sorted[@]} -ne $(echo "$AFFECTED" | tr ',' ' ' | wc -w) ]]; then
    echo "ERROR: CYCLE DETECTED — cannot determine merge order"
    return 1
  fi

  echo "${sorted[@]}"
}

MERGE_ORDER=$(topological_sort)
# Expected output: shared-schemas backend-api web-dashboard app-mobile
```

**Canonical layer ordering (when topological sort has ties):**
1. Schema / shared-types projects (foundation)
2. Backend / API services (business logic)
3. Web frontends (UI consumers)
4. Mobile / native apps (UI consumers)
5. Infrastructure / config repos (if affected)

---

## Step 3: Validate the Merge Order

Three mandatory validations before the merge order is accepted.

### Validation 1: No Cycles

```bash
if [[ $? -ne 0 ]]; then
  echo "FATAL: Dependency cycle detected. Cannot merge."
  echo "ACTION: Review contracts — circular dependency must be broken."
  echo "ESCALATE: dreamer must decide which dependency to remove."
  exit 1
fi
```

### Validation 2: No Orphan PRs

Every affected project must appear exactly once in the merge order.

```bash
for project in $(echo "$AFFECTED" | tr ',' ' '); do
  if [[ ! " ${MERGE_ORDER[*]} " =~ " $project " ]]; then
    echo "ERROR: Orphan PR — $project is affected but not in merge order"
    echo "ACTION: Check contracts — $project may have undeclared dependencies"
    exit 1
  fi
done
```

### Validation 3: All Dependencies Present

Every dependency target must itself be in the affected set.

```bash
for project in "${!DEPENDS_ON[@]}"; do
  for dep in $(echo "${DEPENDS_ON[$project]}" | tr ',' ' '); do
    if [[ ! " $(echo $AFFECTED | tr ',' ' ') " =~ " $dep " ]]; then
      echo "ERROR: Missing dependency — $project depends on $dep but $dep has no PR"
      echo "ACTION: Either add $dep to affected projects or remove the dependency"
      exit 1
    fi
  done
done
```

---

## Step 4: Output Merge Order with Wait Gates

```bash
echo "=== MERGE ORDER ==="
POSITION=1
TOTAL=$(echo "$MERGE_ORDER" | wc -w)

for project in $MERGE_ORDER; do
  PR_NUM=$(brain-read --key "prs.${project}.number")
  DEPS="${DEPENDS_ON[$project]:-none}"

  echo "[$POSITION/$TOTAL] $project (PR #$PR_NUM)"
  echo "  Depends on: $DEPS"

  if [[ $POSITION -lt $TOTAL ]]; then
    echo "  --- WAIT GATE: merge + CI green before proceeding ---"
  else
    echo "  --- FINAL: merge completes the chain ---"
  fi

  POSITION=$((POSITION + 1))
done

# Record merge order in brain
brain-write \
  --key "merge_order.sequence" \
  --value "$MERGE_ORDER"

brain-write \
  --key "merge_order.validated_at" \
  --value "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

**Example output:**

```
=== MERGE ORDER ===
[1/4] shared-schemas (PR #42)
  Depends on: none
  --- WAIT GATE: merge + CI green before proceeding ---
[2/4] backend-api (PR #123)
  Depends on: shared-schemas
  --- WAIT GATE: merge + CI green before proceeding ---
[3/4] web-dashboard (PR #124)
  Depends on: backend-api
  --- WAIT GATE: merge + CI green before proceeding ---
[4/4] app-mobile (PR #125)
  Depends on: backend-api
  --- FINAL: merge completes the chain ---
```

---

## Conflict Detection

Before locking merge order, check for conflicts that would block the chain.

```bash
detect_merge_conflicts() {
  for project in $MERGE_ORDER; do
    PR_NUM=$(brain-read --key "prs.${project}.number")
    MERGEABLE=$(gh pr view "$PR_NUM" --repo "org/$project" \
      --json mergeable --jq .mergeable)

    if [[ "$MERGEABLE" != "MERGEABLE" ]]; then
      echo "WARNING: $project PR#$PR_NUM has merge conflicts"
      echo "ACTION: Resolve conflicts BEFORE starting merge chain"
      CONFLICTS_FOUND=true
    fi
  done

  if [[ "$CONFLICTS_FOUND" == "true" ]]; then
    echo "BLOCKED: Resolve all conflicts before proceeding"
    return 1
  fi
}
```

---

## Edge Cases & Fallback Paths

### Edge Case 1: Circular Dependency Detected

- **Symptom:** Topological sort produces fewer nodes than affected projects.
- **Example:** backend-api depends on shared-schemas, shared-schemas depends on backend-api (circular).
- **Action:** Identify the cycle by tracing dependency edges. Report exact cycle path (A -> B -> C -> A).
- **Fallback:** Escalate to dreamer. The cycle must be broken by refactoring one dependency direction (extract shared interface, introduce adapter layer, or split the circular contract into two phases).
- **Never:** Merge in arbitrary order hoping it works.

### Edge Case 2: Merge Conflict in Middle of Chain

- **Symptom:** PR #2 in a 4-PR chain develops a merge conflict after PR #1 merges (main moved).
- **Action:** HALT the chain. Do not proceed to PR #3 or #4.
- **Fallback:** Rebase PR #2 against updated main. Re-run CI. Once green, resume chain from PR #2 onward. Re-validate remaining PRs for conflicts before continuing.
- **Never:** Skip the conflicted PR and merge downstream PRs.

### Edge Case 3: CI Fails on Dependent PR After Upstream Merged

- **Symptom:** shared-schemas merges successfully. backend-api CI fails post-merge (contract mismatch revealed only after schemas landed in main).
- **Action:** HALT the chain immediately. Do not merge web-dashboard or app-mobile.
- **Fallback:** Fix the backend-api branch against the now-merged schema. Push fix, re-run CI. If fix is non-trivial, escalate — the schema PR may need a follow-up patch. Resume chain only after backend-api CI is green.
- **Never:** Revert the upstream (schema) merge to "unblock" downstream. Forward-fix only.

### Edge Case 4: Shared Schema PR Blocks All Others

- **Symptom:** The root schema PR has failing CI, review delays, or is contested. All downstream PRs are blocked indefinitely.
- **Action:** Prioritize unblocking the root. Assign reviewers, fix CI failures, resolve contested changes.
- **Fallback:** If the schema PR cannot be unblocked within the agreed SLA, escalate to dreamer for a decision: (a) split the schema change into a smaller safe-to-merge subset, (b) decouple downstream PRs to work with old schema temporarily, or (c) abort the coordinated merge and refile.
- **Never:** Merge downstream PRs against the old schema while expecting the new schema to land later.

### Edge Case 5: Hot-Fix Needed During Merge Chain

- **Symptom:** Production incident requires a hot-fix to a repo that is mid-chain (e.g., backend-api needs a hot-fix while web-dashboard merge is pending).
- **Action:** PAUSE the merge chain. Land the hot-fix on main first (hot-fix takes absolute priority over feature merges).
- **Fallback:** After hot-fix lands, rebase ALL remaining PRs in the chain against updated main. Re-validate merge order (hot-fix may have changed dependency landscape). Re-run conflict detection. Resume chain from the next unmerged PR.
- **Never:** Merge the feature PR and the hot-fix simultaneously. Never delay a production hot-fix for a feature merge chain.

---

## Red Flags — STOP

Stop and escalate if any of these are true:

- **Merge order was determined "by feel" without building the dependency graph.** Rebuild from contracts.
- **Two PRs were merged simultaneously** (parallel merge). Roll back the second and re-merge in order.
- **A PR was merged before its dependency's CI turned green.** Halt chain, verify integrity.
- **An affected project has no PR but other projects depend on it.** Missing PR means broken chain.
- **Dependency graph has a cycle and someone "resolved" it by picking an arbitrary order.** Cycles must be broken structurally, not ignored.
- **Someone skipped a wait gate because "CI is slow."** CI speed is not a reason to skip verification.
- **Merge order differs from topological sort output with no documented justification.** The algorithm decides, not intuition.

---

## Merge Order Checklist

Before handing off to pr-set-coordinate, verify:

- [ ] Dependency graph built from contract definitions (not guessed)
- [ ] Topological sort executed (Kahn's algorithm or equivalent)
- [ ] No cycles detected (sort output count matches project count)
- [ ] No orphan PRs (every affected project appears in order)
- [ ] All dependency targets are in the affected set (no missing PRs)
- [ ] Conflict detection passed (all PRs mergeable against current main)
- [ ] Wait gates defined between every consecutive merge
- [ ] Merge order recorded in brain (merge_order.sequence)
- [ ] Merge order validated timestamp recorded (merge_order.validated_at)
- [ ] Order reviewed: schemas first, then backends, then frontends

Output: **MERGE ORDER LOCKED** (sequence validated, ready for pr-set-coordinate) or **BLOCKED** (issue identified, must resolve before proceeding)

## Checklist

Before handing off to pr-set-coordinate:

- [ ] Dependency graph built from contract definitions (schema, API, event, cache) — not guessed
- [ ] Topological sort executed; output count matches affected project count (no cycles)
- [ ] No orphan PRs — every affected project appears exactly once in the order
- [ ] All dependency targets present in the affected set (no missing PRs)
- [ ] Conflict detection passed — all PRs mergeable against current main
- [ ] Wait gates defined between every consecutive merge step
- [ ] Merge order recorded in brain (`merge_order.sequence` and `merge_order.validated_at`)

---

## Cross-References

- **pr-set-coordinate** — Executes the merge order produced by this skill (creation, linking, merging)
- **contract-schema-db** — Schema contracts that define foundation-layer dependencies
- **contract-api-rest** — REST API contracts that define backend-to-frontend dependencies
- **contract-event-bus** — Event contracts that define async inter-service dependencies
- **brain-read** — Reads shared-dev-spec, affected projects, and contract definitions

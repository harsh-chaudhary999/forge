# Integration with Other Brain Skills

`brain-why` works with other brain skills to form a complete decision knowledge system.

## brain-why ← brain-read (How to Fetch a Decision)

When you invoke `/brain-why D42`, internally it calls `/brain-read` to:
1. Query the decision index (where is D42?)
2. Load the decision file from `~/forge/brain/decisions/architecture/D042_api-versioning.md`
3. Fetch linked context (parent decisions, child decisions)
4. Validate decision exists and is accessible

**What you invoke:** `brain-why D42`
**What happens under the hood:** brain-why calls brain-read to load D42 from disk

**Example:**
```
/brain-why D42
→ brain-why queries brain-read: "Load D42 and its context"
→ brain-read searches ~/forge/brain/decisions/ index
→ brain-read finds ~/forge/brain/decisions/architecture/D042_api-versioning.md
→ brain-read loads all linked decisions (D41, D43, D44, D45)
→ brain-why formats the output and returns it
```

## brain-why ← brain-write (Provenance Info Written by brain-write)

When you create a decision via `/brain-write`, it prompts you for:
1. Why? (Problem, goal, motivation, evidence)
2. When? (Date, phase, deadline)
3. By whom? (Decision maker, champion, stakeholders)
4. Alternatives considered (rejected options with rationale)
5. Impact map (what decisions depend on this?)

**brain-why depends on brain-write to record provenance.** The Why/When/By Whom/Evidence structure is created by brain-write, then navigated by brain-why.

**Example:**
```
/brain-write D42 "API Versioning Strategy"
→ brain-write prompts for all 5 provenance layers
→ Saves to ~/forge/brain/decisions/architecture/D042_api-versioning.md
→ Later: /brain-why D42
→ brain-why reads what brain-write created
```

## brain-why → brain-recall (Recall Uses Why for Ranking)

When you search for a decision via `/brain-recall`, it looks for:
1. Decisions with similar "Why" (problem statements)
2. Similar "Evidence" (shared metrics, sources)
3. Related "Alternatives" (same design patterns)

**brain-recall uses brain-why structure to find relevant decisions.** The richness of your Why/Evidence sections makes search more useful.

**Example:**
```
/brain-recall "API versioning strategy"
→ brain-recall searches decision index
→ Finds D42, D45, D102 (all about versioning)
→ Ranks by relevance (Why matches your query)
→ Returns: "D42 has the most relevant Why"
→ You then call /brain-why D42 to read full provenance
```

## brain-why ← brain-link (Semantic Edges Show Relationships)

`brain-link` creates semantic edges between decisions:
1. "D42 enables D43" (dependency edge)
2. "D42 supersedes D88" (replacement edge)
3. "D42 similar to D102" (pattern edge)
4. "D42 conflicts with D33" (tradeoff edge)

**These links augment the Why structure.** When you call `/brain-why D42`, it shows:
- Parent decisions (what D42 depends on)
- Child decisions (what depends on D42)
- Related decisions (similar patterns)
- Superseded decisions (old versions)

**Example:**
```
/brain-link D42 --depends-on D41
/brain-link D42 --enables D43
/brain-link D42 --supersedes D88

Later: /brain-why D42
→ Shows D41 as parent, D43 as child, D88 as replaced version
→ These links are created by brain-link, navigated by brain-why
```

## brain-why → brain-forget (Understand Why Decision Was Archived)

When you archive a decision via `/brain-forget D88`, it:
1. Marks decision as Archived (status change)
2. Links it to the replacement decision (supersedes edge)
3. Records why it was archived (brief reason)
4. Keeps it in read-only status (for history)

**brain-why helps you understand the archive decision.** You can still read `/brain-why D88` to see:
- Why was this decision made? (original Why section)
- When was it archived? (archive date)
- What replaced it? (superseded-by link)
- What did we learn? (Lessons section)

**Example:**
```
Original: /brain-why D88 "MongoDB for cache"
→ Shows original decision, why we chose MongoDB

Later: Switched to Redis
/brain-forget D88 "Replaced by D150"
→ Marks D88 as Archived
→ Links D88 → D150 (superseded-by)

Later: /brain-why D88 (on archive)
→ Shows original decision + archive metadata
→ Shows why we switched: "Redis more reliable for cache"
```

## Full Integration Example: Tracing a Decision Across All Skills

```
Scenario: We want to understand why we use gRPC for service communication

Step 1: Find the decision
  /brain-read D89
  → brain-read returns: "D89 Switch to gRPC"

Step 2: Understand the provenance
  /brain-why D89
  → brain-why returns: full 5-layer walk (Why/When/By Whom/Evidence/Alternatives)
  → Shows problem: "REST latency bottleneck (250ms)"
  → Shows evidence: "Load test 50ms vs 250ms"

Step 3: Find related decisions
  /brain-recall "gRPC performance latency"
  → brain-recall returns: D89 (primary), D91 (gRPC monitoring), D85 (service arch)

Step 4: Understand relationships
  /brain-link D89
  → brain-link shows: D85 (parent), D90/D91/D92 (children)

Step 5: See current status
  /brain-why D89 (check status, gotchas, lessons)
  → Status: Active (partial rollout)
  → Gotchas: Protobuf versioning fragile
  → Future: Need better tooling

Step 6: If decision was archived
  /brain-forget D89 (hypothetically, once replaced)
  → Shows what replaced it and why
```

# Common Decision Walk Pitfalls

Avoid these mistakes when navigating decision history.

## Pitfall 1: Following Stale Decisions (Archived Decision Treated as Active)

**What happens:** You find decision D88 "Use MongoDB for cache" from 2024. It's in the brain. You implement based on it. But D88 was archived in 2025 and replaced by D150 "Use Redis for cache."

**How to detect:**
- Check decision's "Status" field (should be Active, not Archived)
- Look for "supersedes:" link (brain-link shows D150 supersedes D88)
- Check brain-forget archive status
- If decision is 6+ months old, verify it's still in use

**How to fix:**
- When reading a decision, check its status first
- If status is Archived, don't use it
- Search for superseding decision (use brain-link or brain-recall)
- If you can't find a replacement, ask the team (decision might be orphaned)

**Real example:**
```
You find: D88 "Use MongoDB for cache" (locked 2025-01-15)
Status: Archived (June 2025)
Superseded by: D150 "Use Redis for cache"
Mistake: Implementing MongoDB based on D88
Correct: Read D150 instead, understand why we switched
```

## Pitfall 2: Missing Superseded Links (Old Decision Not Marked as Replaced)

**What happens:** Two decisions exist: D42 "6-month deprecation" and D42b "3-month deprecation" (made later). You don't know which one is active. You implement using old D42, but team expected D42b.

**How to detect:**
- Search brain for similar decisions (use brain-recall)
- Multiple decisions with same topic?
- Check dates (newer decision might be override)
- Ask: Does this decision have a superseding decision?

**How to fix:**
- When adding a new decision, use brain-link to mark old decision as superseded
- Create a chain: D42 --superseded-by--> D42b
- Both decisions must link to each other (D42b --supersedes--> D42)
- Archive the old decision (use brain-forget)

**Prevention:**
- Use brain-write to create decision, it will prompt for superseding links
- brain-link tool should enforce bidirectional links

**Real example:**
```
D42 (6-month deprecation window) — locked 2026-03-15
Later: Team realizes 6 months too generous
D42-revised (3-month deprecation window) — locked 2026-04-10

Mistake: Someone implements D42 (old), not D42-revised
Fix: D42-revised should have link: "supersedes: D42"
       D42 should have link: "superseded-by: D42-revised"
       D42 should be archived
```

## Pitfall 3: Evidence Links Broken (Original Incident Report Deleted)

**What happens:** Decision D89 cites "our 2024 incident report" as evidence. But 2 years later, the incident report was deleted (storage cleanup). You can't verify the evidence anymore. Should you trust D89?

**How to detect:**
- Check if evidence links are resolvable (can you find the document?)
- Look for "Evidence" section with broken links
- Try to load incident report, test results, or benchmark
- If link is missing/deleted, mark as unverifiable

**How to fix:**
- Evidence should have stable links (e.g., to archived incident reports)
- Use version control for evidence (keep old reports in /archives)
- When referencing evidence, include enough detail to re-create it
- Don't rely on links alone; summarize findings in decision

**Prevention:**
- Store evidence in permanent locations (brain/evidence, not temp files)
- Use brain-write tool, it will enforce evidence storage
- Require at least one summary of evidence in decision (not just link)

**Real example from D42:**
```
Evidence: "2024 incident report shows 32 outages"
Link: /incidents/2024-deprecation-incident.md
Problem: File was deleted during storage cleanup

Better evidence:
  "2024 incident report (archived): 32 outages from rapid deprecation
   Root cause: Clients not notified before endpoint removal
   See: ~/forge/brain/archived/2024-deprecation-incident.md (permanent archive)"
```

## Pitfall 4: Single-Source Evidence (Only Internal Opinion, No External Reference)

**What happens:** Decision D156 "Reject Kubernetes" is based only on "Infra team agrees it's overkill." No external reference. No similar companies cited. Pure opinion.

**How to detect:**
- Read "Evidence" section
- Ask: Where did this come from? Data or opinion?
- Is there external validation? (Competitors, case studies, best practices?)
- Is there internal data? (Test, metrics, incident reports?)
- If answer is "just our opinion," it's weak

**How to fix:**
- Add external reference (Google, AWS, similar startup)
- Add internal data (timeline comparison, team size analysis)
- Show methodology (why is 5-engineer threshold chosen?)
- Cite multiple sources

**Prevention:**
- brain-write should prompt for evidence sources
- Require at least 2 of: {internal data, external reference, test results}

**Real example from D156:**
```
Weak evidence:
  "Kubernetes is overkill for our team"
  (pure opinion, no data)

Better evidence:
  "Kubernetes setup: 3 weeks (measured)
   Docker Compose setup: 1 day (measured)
   Team size: 5 engineers (fact)
   Similar startups (Stripe, GitHub) used Compose at early stage (reference)"
```

## Pitfall 5: Circular Decision Graphs (D42 Depends on D89 Depends on D42)

**What happens:** D42 says "use graduated deprecation because gRPC is fast" (depends on D89). D89 says "use gRPC because API versioning is stable" (depends on D42). Reading one requires reading the other, which requires reading the first. Infinite loop.

**How to detect:**
- Walk dependency chain (D42 → D89 → D42)
- If you end up where you started, you have a cycle
- Tools should detect and warn (brain-write, brain-link validation)

**How to fix:**
- One decision must be independent (doesn't depend on other)
- Re-order: D89 doesn't depend on D42, it depends on performance needs
- D42 depends on D41 (REST principles), not D89
- Break the cycle by clarifying what each decision actually depends on

**Prevention:**
- brain-write should validate dependency graph (reject cycles)
- Use brain-link to audit graphs before committing

**Real example:**
```
Circular dependency (WRONG):
  D42 (API versioning) depends on D89 (gRPC for performance)
  D89 (gRPC) depends on D42 (versioning for stability)
  Reading D42 requires D89, reading D89 requires D42

Correct dependency:
  D89 (gRPC for performance) — independent, depends on D85 (service architecture)
  D42 (API versioning) — depends on D41 (REST principles), not D89
  They are related but not dependent
```

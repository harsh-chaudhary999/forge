# Decision Walk Patterns

When you need to trace a decision, use these 5 patterns. Each pattern answers a specific question and shows how to walk the decision graph.

## Pattern 1: Root Cause Walk (Current Problem → Which Decision Caused It?)

**Question:** "We're seeing API timeouts. Which decision led to this?"

**Graph traversal:**
1. Start with current problem (API timeouts in production)
2. Check recent decisions in affected service (D42, D89, D91)
3. Walk children of those decisions (D43 → D44, D89 → D90)
4. Check "Did It Work?" and "Gotchas Discovered" sections
5. Look for "Incidents" that match current problem

**Real example query:**
```
Problem: API timeouts (250ms p99) in user service
→ Recent decision D89 (gRPC migration)?
   - Check D89 incidents: Yes, Week 2 had Protobuf versioning issue
   - Check D89 impact: user-svc latency 50ms (not timing out)
   - Not this one
→ Recent decision D91 (gRPC monitoring)?
   - Check D91 changes to observability
   - Might be contributing (monitoring overhead?)
   - Unlikely root cause
→ Parent decision D85 (Service architecture)?
   - Check if service topology changed
   - Maybe added synchronous calls that weren't async before?
→ Walk unrelated decisions: D42 (API versioning)?
   - Check if deprecation logic added latency
   - Found it! D42 added deprecation header parsing (5ms overhead per request)
   - With 50 internal API calls per user request = 250ms added

Root cause: D42 deprecation logic, not D89 gRPC (red herring)
```

## Pattern 2: Precedent Walk (Similar Problem in Past → Which Decision Addressed It?)

**Question:** "We need to deprecate a service. How did we handle this before?"

**Graph traversal:**
1. Search brain for similar decisions (use brain-recall pattern search)
2. Find decisions with similar problem statement
3. Check "Why" and "Evidence" sections
4. Look at "Did It Work?" and lessons learned
5. Check if decision was superseded (use brain-forget status)

**Real example query:**
```
Problem: Need to deprecate legacy auth service
→ Search brain for "deprecation" decisions
   - D42 (API versioning → 6-month deprecation window) ✓
   - D45 (Client library SLA → SDK updates) ✓
   - D88 (Old payment service → replaced by D89) ✓
→ D42 most relevant (we deprecated endpoint, they deprecated API)
   - Evidence: Graduated approach works
   - Timeline: 6 months for clients to migrate
   - Lessons: Automated notifications important
   → Apply same pattern: 6-month deprecation for legacy-auth-svc
→ D88 also relevant (service deprecation, not just API endpoint)
   - How long for teams to switch? 4 weeks
   - Did we notify teams? Ad-hoc (mistake)
   - Should have been automated
   → Add notification system this time

Precedent solution: Combine D42 (timeline) + D88 (service communication)
```

## Pattern 3: Cascading Impact Walk (This Decision Affects Which Downstream Decisions?)

**Question:** "We just changed API versioning strategy. What else breaks?"

**Graph traversal:**
1. Start with decision (D42)
2. Walk all child decisions (D43, D44, D45)
3. For each child, walk their children
4. Check "Status" fields (active, archived, planned)
5. Find decisions with "depends on" links to your decision
6. Trace impact to products/services (use brain-read for topology)

**Real example query:**
```
Decision: D42 (API versioning) changed from 12-month to 6-month window
→ Immediate children: D43, D44, D45
   - D43 (Sunset header strategy): Uses D42 timeline, needs update
   - D44 (Error code taxonomy): Independent, no change
   - D45 (Client library SLA): Directly tied to deprecation timeline, needs update
→ Grandchildren:
   - D46 (SDK release cadence): Depends on D45, may need faster cadence
   - D47 (Docs versioning): Depends on D45, must document new timeline
→ Check impacted products:
   - shopapp: D42 in production, clients assume 12-month window
   - vendorapp: D42 baseline, using same 12-month approach
   - partner-api: D42 published to external docs, clients depending on it
→ Impact assessment:
   - D43 must change (header strategy tied to timeline)
   - D45 must change (SLA timeline)
   - D46 optional (can work with existing cadence)
   - D47 must update (docs show new timeline)
   - External docs must update (partner-api clients reading)

Cascading decisions to update: D43, D45, D47 (+ docs/api-versioning.md)
Requires: Communication plan to partner-api clients
```

## Pattern 4: Alternative Evaluation Walk (We Rejected Option X in D42, Why?)

**Question:** "Should we use URL versioning instead of header versioning?"

**Graph traversal:**
1. Find decision that evaluated alternatives (D42)
2. Go to "Alternatives Considered" section
3. Read "Why rejected" for each option
4. Check "Trade-offs" (what would we gain/lose?)
5. Look for similar decisions on other products
6. Check if rejected alternative is used elsewhere (brain-recall)

**Real example query:**
```
Option: URL versioning (/v1/users vs /v2/users)

In D42 alternatives:
  - Why rejected: "High cognitive load on clients, duplicated routes in server"
  - Trade-off: "Simpler for server, harder for clients"
  - Vote: Rejected (3-2 vote, showed dissent)

Why this matters:
  - We had to maintain both /v1 and /v2 routes (duplication)
  - Clients must hardcode version in URL (coupling)
  - Harder to deprecate (can't just remove route, breaks clients)

Check other decisions:
  - D35 (older API versioning): Used URL versioning, had to support 5 versions
  - D102 (new service API): Chose header versioning after learning from D35

Pattern across org: Moved away from URL versioning → header/graduated deprecation

Conclusion: Reject URL versioning (we tried it, learned it's costly)
```

## Pattern 5: Timeline Walk (Decision Lifecycle → When Superseded, Archived, Evergreen?)

**Question:** "Is this decision still valid, or has it been superseded?"

**Graph traversal:**
1. Check decision's "Status" field (Active, Archived, Superseded)
2. Look for "Locked" date vs current date
3. Search for "supersedes:" link (using brain-link)
4. Check "Did It Work?" section for ongoing applicability
5. Look for "Future Cautions" (when to revisit)
6. Use brain-forget to check archive status

**Real example query:**
```
Decision: D156 (Docker Compose for local dev)
  - Locked: 2026-01-10
  - Current date: 2026-04-10 (3 months later)
  - Status: Active
  - Check future cautions: "Revisit at 10+ engineers, probably Q3 2026"

Timeline:
  - Jan 2026: 5 engineers → Docker Compose chosen ✓
  - Feb 2026: 6 engineers → still fine
  - Mar 2026: 8 engineers → starting to show strain (manual deploys slow)
  - Apr 2026: 10 engineers → threshold reached
  - Decision point: Migrate to Kubernetes or find middle ground?

Check related decision:
  - D200 (Kubernetes adoption) → planned for Q3 2026
  - D200 supersedes D156? → Not yet, D156 still active
  - Timeline alignment: D200 planned for July 2026 (Q3)

Current decision: D156 still active, but evaluate Kubernetes migration now
Next step: Create D200 (Kubernetes decision) for Q3 launch
```

# Evidence Quality Guidelines

Not all evidence is equal. When reading a decision, evaluate the evidence strength. When writing a decision, ensure you have strong evidence.

## Types of Evidence

### 1. Data Evidence (Strongest)
- Load test results with methodology documented
- Metrics from production (latency, error rates, throughput)
- Customer feedback (surveys, support tickets)
- Incident reports with root cause analysis
- Benchmark comparisons (apples-to-apples)

**Examples from D42:**
- Customer survey: 6/8 want 6+ months notice (60% of sample)
- Our incident report: 32 outages from rapid deprecation (hard data)
- Competitor timelines: AWS 12mo, Stripe 18mo, GitHub 12mo (verifiable facts)

**Examples from D89:**
- Load test: gRPC 50ms vs REST 250ms (5x improvement, methodology shown)
- Benchmark: 1000 calls/sec test (specific numbers, reproducible)

### 2. Authority Evidence (Medium-Strong)
- Industry-standard practices (Google, AWS, Stripe public docs)
- Published case studies (Uber latency improvements)
- Open-source precedent (popular libraries using same pattern)
- Expert recommendations from known experts
- Academic papers on specific problem

**Examples from D42:**
- AWS API versioning guide (authoritative source)
- Stripe API lifecycle documentation (competitor precedent)
- GitHub API deprecation schedule (industry leader example)

**Examples from D156:**
- Kubernetes adoption patterns (ecosystem evidence)
- Similar startups early decisions (implicit precedent)

### 3. Experience Evidence (Medium)
- Internal incident reports (our past failures)
- Team's previous success with similar decisions
- Customer support feedback (anecdotal but from users)
- War stories from team members (pattern recognition)

**Examples from D42:**
- Our 2024 incident report (internal experience)
- Partner feedback (customer experience)

**Examples from D89:**
- Google/Uber case studies (their experience, published)

## Weak Evidence (Be Suspicious)

- **Assumptions without data:** "I think latency is the bottleneck" (test it)
- **Expert opinion alone:** "Jamie says gRPC is better" (where's the data?)
- **Anecdotal feedback:** "One customer complained" (10% vs 10 customers?)
- **Outdated comparisons:** "Node.js was slow in 2015" (it's 2026 now)
- **Missing methodology:** "Load tests showed improvement" (how many requests? traffic pattern?)
- **Single source:** Only internal opinion, no external reference

## How to Evaluate Evidence Quality When Reading a Decision

**Checklist:**
- [ ] Is this data or assumption? (Look for numbers, logs, reports)
- [ ] Is it from a reliable source? (Named company, published docs, our incident report)
- [ ] Is methodology described? (If test, how many samples? What traffic pattern?)
- [ ] Is it current? (Decision made 2026, evidence from 2024? Still relevant?)
- [ ] Are there multiple sources? (One data point or three?)
- [ ] Does it answer the right question? (Load test proves latency, but is latency the bottleneck?)

**Red flags:**
- "Everyone uses gRPC" (no data)
- "I'm pretty sure this will work" (no evidence)
- "Competitors do this" (which competitors? how do you know?)
- "Best practice" (best for what team size? context?)

## When to Challenge Evidence (Evidence Outdated or Context Changed)

**Question:** "Is this evidence still valid?"

**Challenge checklist:**
- [ ] **Timeline:** Decision 2024, evidence 2023. Is 1-year-old data still accurate?
- [ ] **Context shift:** Decision assumes REST. We now use gRPC. Does evidence still apply?
- [ ] **Scale change:** Evidence from 100 requests/sec. We now do 10k requests/sec. Bottleneck still same?
- [ ] **Technology update:** Evidence from Python 2.7. We now use Python 3.11. Still relevant?
- [ ] **Team size change:** Evidence from 20-person team. We now have 5. Same constraints?
- [ ] **Broken link:** Original incident report deleted. Can't verify root cause anymore.

**Real example challenge:**

Original D42 evidence: "AWS uses 12-month deprecation"
Question: Is AWS evidence still valid in 2026?
- AWS likely updated their strategy (check current docs)
- Our context: 5-engineer team (vs enterprise at AWS)
- Challenge: Maybe 6 months is right for us, even if AWS uses 12?
- Resolution: Re-read current AWS docs, compare with our team size

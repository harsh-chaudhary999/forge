## Evergreen Classification

Evergreen decisions are foundational principles or patterns that stand the test of time and should never be archived. They represent organizational wisdom, core architecture principles, stable contracts, and validated lessons that transcend individual projects or time periods.

### Evergreen Decision Patterns

#### 1. Evergreen Pattern
**Definition:** "This approach works for ALL projects and ALL contexts"

**Characteristics:**
- Applies universally across product, technical platform, and team boundaries
- No known edge cases or exclusions
- Proven over multiple major product cycles (2+ years minimum)
- Reduces to a simple, repeatable process

**How to identify:**
- Ask: "Could any team on any project ignore this and be okay?" Answer should be "No"
- Check: Multiple independent teams have adopted and found value
- Validate: Pattern has been stress-tested in diverse contexts
- Test: Decision applies to projects 5+ years in the future

**How to mark:**
```yaml
status: Active
evergreen: true
evergreen_type: pattern
evergreen_since: 2024-01-15
pattern_scope: "All projects, all teams, all contexts"
```

**Search and maintenance:**
```
# Find all evergreen patterns
brain-read tag:* evergreen:true evergreen_type:pattern

# Periodic validation (annually)
Review all evergreen patterns to ensure still universal
Check for any new edge cases discovered
Update timestamp if revalidated
```

**Examples:**
- "Code review approval required before merge" (universal quality gate)
- "API versioning deprecation period: 12 months" (cross-team consistency)
- "Security: never commit credentials, use secret manager" (non-negotiable)

---

#### 2. Evergreen Decision (Architecture Principle)
**Definition:** "Core tenet of our architecture that defines who we are"

**Characteristics:**
- Expresses fundamental principle about system design
- Typically immutable or changes only when company pivots
- Defines constraints on all systems built within organization
- Often appears in multiple decisions as parent/reference

**How to identify:**
- Ask: "Would changing this require fundamentally restructuring the company?"
- Check: Decision appears in many other decisions as a prerequisite
- Validate: Principle has been maintained across major product rewrites
- Test: New decisions regularly reference this one positively

**How to mark:**
```yaml
status: Active
evergreen: true
evergreen_type: architecture
evergreen_since: 2022-06-01
architectural_principle: "Always prioritize customer data privacy over feature velocity"
enforcement: "All systems must implement end-to-end encryption by default"
```

**Search and maintenance:**
```
# Find all architecture principles
brain-read tag:* evergreen:true evergreen_type:architecture

# Annual architecture review
Review all architectural principles
Assess if new product directions require updates
Solicit feedback from senior engineers
Update guidance based on lessons from past year
```

**Examples:**
- "Always use CI/CD for all production deployments" (non-negotiable operational principle)
- "Database-agnostic abstractions for core business logic" (flexibility principle)
- "Customer data never leaves data residency region" (compliance principle)

---

#### 3. Evergreen Contract
**Definition:** "Stable, long-lived interface that won't change"

**Characteristics:**
- Defines stable contracts (APIs, event schemas, database interfaces)
- Multiple systems depend on stability of this contract
- Changes would require coordinated migration of dependent systems
- Rarely updated but when changed, requires major coordination

**How to identify:**
- Ask: "How many systems would break if this contract changed?"
- Check: Contract is referenced in multiple dependent decisions
- Validate: Contract has been stable for multiple major releases
- Test: New dependent systems can adopt this contract without version pinning

**How to mark:**
```yaml
status: Active
evergreen: true
evergreen_type: contract
evergreen_since: 2023-03-15
contract_stability: "Breaking changes require 6-month deprecation period and council approval"
dependent_systems: [PaymentService, InventoryService, NotificationService]
versioning_strategy: "Additive changes only; removals require deprecation cycle"
```

**Search and maintenance:**
```
# Find all stable contracts
brain-read tag:api evergreen:true evergreen_type:contract

# Quarterly contract review
Audit all evergreen contracts for backward compatibility
Check for any dependent system failures or incompatibilities
Plan deprecation cycles for any necessary breaking changes
Communicate timeline to all dependent teams
```

**Examples:**
- "REST API contract for order service: v3 stable, v2 deprecated, v1 sunset" (API contract)
- "Kafka event schema for payment events: must be backward compatible" (event contract)
- "Database schema for customer table: primary keys never change, only additive columns" (schema contract)

---

#### 4. Evergreen Lesson (Validated Learning)
**Definition:** "Hard-won insight that shaped how we build systems; worth remembering forever"

**Characteristics:**
- Documents a significant problem we solved and why the solution matters
- Captures reasoning that explains current decisions
- Prevents reinventing the wheel or repeating past mistakes
- Valuable even if specific technical decision becomes outdated

**How to identify:**
- Ask: "If we lost this knowledge, what expensive mistake would we repeat?"
- Check: Lesson is referenced as justification in multiple other decisions
- Validate: Lesson has been consistently applied over multiple product cycles
- Test: Lesson remains valuable even if we rebuild the system differently

**How to mark:**
```yaml
status: Active
evergreen: true
evergreen_type: lesson
evergreen_since: 2021-09-10
lesson_category: "Database selection rationale"
lesson_title: "Why we chose MySQL for financial transactions"
lesson_value: "Prevents pressure to switch databases in pursuit of cool tech"
```

**Search and maintenance:**
```
# Find all evergreen lessons
brain-read tag:* evergreen:true evergreen_type:lesson

# Lessons review (biannually)
Review all evergreen lessons for continued validity
Update context if new information discovered
Add new lessons from major learnings or incidents
Ensure lessons are accessible and discoverable
```

**Examples:**

**Evergreen Lesson Example 1: Database Selection**
```yaml
id: D15
title: "Why MySQL for Financial Transactions"
status: Active
evergreen: true
evergreen_type: lesson
evergreen_since: 2021-09-10

## The Problem
Early on, we explored NoSQL for transaction logs. Benchmarks looked good. 
Pressure from engineering to use trendy tech was high.

## What We Chose and Why
MySQL with InnoDB: Full ACID compliance, proven at scale, simple operations.

## The Lesson
Never optimize for engineering trendsiness when data integrity is on the line.
ACID guarantees prevented 47 data inconsistency bugs that would have been 
invisible in eventual-consistency systems. Cost of fixing one incident: $300K+.

## Why This Remains Evergreen
The reasoning—data integrity > cool technology—transcends database choices.
Even if we eventually use different database, this principle remains.
Prevents repeating "why did we choose the cool tech" mistakes in future.

## When This Lesson Is Relevant
- Any discussion of changing financial transaction storage
- Tech selection for any critical business data
- Evaluating new databases or frameworks
- When pressure mounts to adopt trendy technology

## What NOT to Infer
This is NOT "never use NoSQL" (we use it for logs, caching, analytics).
This IS "think carefully about data integrity requirements first".
```

**Evergreen Lesson Example 2: Team Scaling**
```yaml
id: D28
title: "Why Microservices Didn't Scale Our Org"
status: Active
evergreen: true
evergreen_type: lesson
evergreen_since: 2020-06-15

## The Problem
With 15 engineers, we split into microservices to "scale better".
Expected: independent team deployment, faster iteration.
Reality: coordination overhead, cross-service debugging nightmare, 12 months to stable.

## What We Learned
Microservices scale teams, not monoliths. We had one team with unclear boundaries.
Should have scaled team structure first, then services to match org structure.

## The Lesson
Organization structure determines system architecture, not vice versa.
Conway's Law: System design mirrors communication structure of org that built it.
Reverse-engineering architecture to make teams autonomous doesn't work.

## Why This Remains Evergreen
True regardless of tech stack or company size.
Valid at 5 people and 500 people.
Prevents repeating expensive architecture mistakes.

## When This Lesson Is Relevant
- Any architectural redesign proposal
- Decisions about microservices, modular monolith, or monolith
- Team restructuring discussions
- When teams request architectural changes to improve independence
```

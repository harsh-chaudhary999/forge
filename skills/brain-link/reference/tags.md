# brain-link — Semantic Tag Catalog

> Extracted from `SKILL.md` §2 (Semantic Tags). Tags enable cross-cutting
> queries and pattern discovery across the decision graph. Tags are stored as a
> YAML array in each decision's frontmatter (`tags: [...]`, no `#` on disk); the
> `#` prefix here is the query/display convention.

Tags enable cross-cutting queries and pattern discovery.

### Concept Tags
Abstract ideas and principles:
- `#api-versioning` — API evolution strategy
- `#eventual-consistency` — Consistency model
- `#cache-invalidation` — Cache freshness
- `#rate-limiting` — Traffic control
- `#observability` — Monitoring and tracing
- `#resilience` — Fault tolerance
- `#idempotency` — Repeated operation safety

### Pattern Tags
Proven design patterns:
- `#circuit-breaker` — Fault isolation
- `#bulkhead` — Resource isolation
- `#saga` — Distributed transaction
- `#bloom-filter` — Set membership
- `#backpressure` — Flow control
- `#exponential-backoff` — Retry strategy
- `#gossip` — Peer-to-peer sync

### Domain Tags
Business/feature areas:
- `#auth` — Authentication & authorization
- `#payments` — Payment processing
- `#search` — Search functionality
- `#notifications` — Messaging system
- `#inventory` — Stock management
- `#catalog` — Product data
- `#recommendations` — ML-based suggestions

### Architectural Tags
System design dimensions:
- `#async` — Asynchronous pattern
- `#sync` — Synchronous pattern
- `#hybrid` — Mixed sync/async
- `#event-driven` — Event-based architecture
- `#request-reply` — RPC-style communication
- `#publish-subscribe` — Pub/sub messaging
- `#database` — Data persistence
- `#cache` — In-memory storage

### Metadata Tags
Decision properties:
- `#breaking-change` — Client-incompatible
- `#deprecation` — Phased retirement
- `#rollback-plan` — Can unwind if needed
- `#tech-debt` — Known limitation
- `#performance-critical` — SLO-impacting
- `#security-critical` — Security-relevant

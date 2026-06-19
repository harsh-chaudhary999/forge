# Search Strategies by Use Case

Decision tree: For each use case, which grep pattern and brain skill combination to use.

### Use Case 1: Finding Past Decisions on Topic X

**Example:** "We've handled database migrations before. What did we decide?"

**Recommended grep pattern:**
```bash
grep -r "database.*migration\|schema.*change" products/*/decisions/ --include="*.md" -i
```

**Also use:**
- `brain-recall`: For ranked keyword + tag/status search across the brain ("How have we upgraded databases?")
- `brain-why`: To trace why old approaches were deprecated

**Workflow:**
1. Start with grep pattern above
2. If results are sparse, use brain-recall for semantic matching
3. If decision exists, use brain-why to understand rationale

### Use Case 2: Locating Contract for Specific Service

**Example:** "What's the API contract for the payment service?"

**Recommended grep pattern:**
```bash
cat products/payment/contracts/api-rest.md
# OR search if unsure:
grep -r "payment" products/*/contracts/ --include="*.md"
```

**Also use:**
- `brain-link`: To find dependent contracts (payment API → auth API)
- `brain-read`: Direct file access (contracts are well-organized)

**Workflow:**
1. Use direct file access if you know the service name
2. Use grep only if service name is ambiguous
3. Use brain-link to validate contract dependencies

### Use Case 3: Identifying Patterns Used Across Products

**Example:** "How do multiple products handle API versioning? Are we consistent?"

**Recommended grep pattern:**
```bash
grep -r "versioning\|version.*strategy" products/*/decisions/ --include="*.md" -i
```

**Also use:**
- `brain-recall`: For semantic clustering ("version management approaches")
- `brain-link`: To show pattern relationships across products

**Workflow:**
1. Use grep to find all versioning decisions
2. Use brain-recall to cluster similar approaches
3. Use brain-link to show cross-product edges

### Use Case 4: Tracing Decision History (When Changed, Why)

**Example:** "We moved to a new payment gateway. When was that decided? What was the old approach?"

**Recommended grep pattern:**
```bash
grep -r "payment.*gateway\|deprecated.*gateway" products/*/decisions/ --include="*.md" -i
```

**Also use:**
- `brain-why`: To trace decision provenance (who decided, when, rationale)
- `brain-link`: To find related decisions (new gateway depends on auth changes)

**Workflow:**
1. Use grep to find decision(s)
2. Use brain-why for full audit trail (when, who, rationale)
3. Use brain-link to show decision dependencies

### Use Case 5: Validating Against Contract Before Implementation

**Example:** "Before coding, verify: what's the API schema we promised?"

**Recommended path:**
```bash
cat products/payment/contracts/api-rest.md
```

**Also use:**
- `brain-read`: Direct file access (contracts are versioned)
- No grep needed (exact path is known)

**Workflow:**
1. Read contract directly
2. Cross-reference against related decisions (grep)
3. Use brain-link to confirm dependencies haven't changed

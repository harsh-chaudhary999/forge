# Anti-Patterns: How NOT to Use the Brain

## Anti-Patterns: How NOT to Use the Brain

### Anti-Pattern 1: Store Non-Decisions in Brain

**What it looks like:**
```
brain/decisions/D500_user_complained_about_feature.md
brain/decisions/D501_bug_in_production.md
brain/decisions/D502_performance_regression.md
```

**Why it's wrong:**
- Brain is for locked architectural and product decisions
- Issues, bugs, and complaints are temporary events
- Task tracker (Jira, GitHub Issues) is the right place for temporary work
- Brain gets polluted with noise; decision queries become unreliable

**How to fix it:**
- Store issues in project tracking system
- Link to decisions from issues (e.g., "This bug violates D102")
- Only write to brain via `brain-write` skill
- Enforce `type=decision` in decision frontmatter

**Enforcement:**
```
brain-write rejects any record that isn't a deliberate decision
Only LOCKED, DRAFT, and ARCHIVED status are valid
```

### Anti-Pattern 2: Use Brain as Task Tracker

**What it looks like:**
```
brain/products/auth-service/prd/PRD-20260410-001/
├── implementation-status.md          # WRONG: task state
├── jira-tickets.txt                  # WRONG: task list
└── developer-notes.md                # WRONG: temporary notes
```

**Why it's wrong:**
- Brain is immutable; task state changes constantly
- Task progress belongs in project management tool
- Brain entries require commits; task updates don't
- Decision lockdown gets confused with task completion

**How to fix it:**
- Store task state in Jira/GitHub Projects
- Reference decisions from task (e.g., "Implement decision D102")
- Brain contains decisions; tasks implement decisions
- Use `learnings/` only for post-delivery retrospectives

**Enforcement:**
```
Reject PRD mutations after intake-gate
Reject PRD mutations after spec-freeze
Use brain-forget to archive, never bulk-delete
```

### Anti-Pattern 3: Modify Brain Files Directly

**What it looks like:**
```bash
# User directly edits a decision file
vi brain/decisions/D042.md
git add brain/decisions/D042.md
git commit -m "fix typo in D042"
```

**Why it's wrong:**
- Direct edits bypass lock/unlock/archive workflows
- Audit trail is lost; no provenance tracking
- Can't distinguish typo fixes from decision changes
- brain-why skill can't trace the change

**How to fix it:**
- Always use `brain-write` skill to lock decisions
- Use `brain-forget` skill to archive decisions
- Direct edits are only for bootstrapping (empty brain)
- All mutations logged in git with structured commit messages

**Enforcement (convention, not tooling):**
```
forge-brain-persist: commit-discipline gate — every decision is a committed brain file
brain-why: traces changes via git history (git log on the decision file)
```

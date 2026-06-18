---
name: forge-subagent-anatomy
description: "WHEN: You are creating or reviewing a Forge subagent and need the canonical template, state machine, or dispatch rules."
type: reference
version: 1.0.2
preamble-tier: 1
triggers:
  - "subagent template"
  - "how to write an agent"
  - "subagent format"
allowed-tools:
  - Read
---

# Subagent Anatomy: Complete Authoring Guide

## Anti-Pattern Preamble: Why Subagents Break Down

| Rationalization | Why It Fails |
|---|---|
| "The parent session has context — the subagent will inherit it" | Subagents get only what you explicitly pass in the prompt. They start with zero session history. Anything not written in the dispatch prompt is invisible to them. |
| "A vague role description is fine — the subagent is smart enough to figure it out" | Ambiguous role + no scope boundary = subagent doing half the work or the wrong work. The conductor gets back an output it cannot use and must redispatch. |
| "I'll pass the full conversation history as context" | Context pollution is the failure mode subagents exist to prevent. Pass only the task-specific inputs: the plan file, the relevant brain slice, and the explicit output contract. |
| "The subagent will decide what format to return results in" | If the parent doesn't specify the output format (status enum, file path, JSON fields), the subagent will invent one. The conductor's parse step breaks on first divergence. |
| "Subagents are optional — the conductor can just do all the work" | Parallel subagent dispatch is how Forge compresses wall-clock time. Skipping subagents forces serial execution and caps throughput at single-session token rate. |
| "I'll define the edge cases and error paths later" | Subagents hit edge cases during execution, not planning. Without explicit error-path instructions (what to return on BLOCKED, how to report partial results), the subagent silently drops work or returns NEEDS_CONTEXT. |

## Introduction: Why Specialized Subagents Matter

Subagents are isolated agents that solve a **single, well-defined task** in a fresh context. They are not smaller versions of the main conductor — they are specialists with focused roles, clear boundaries, and zero context pollution.

**Why subagents matter:**

1. **Isolation prevents context pollution** — Subagent gets only the task it needs to solve. No conversation history, no parent session state, no baggage. Clean mental model.

2. **Fresh context per task means subagent stays focused** — With no historical context, subagent doesn't have to parse "which of my prior work applies here?" It focuses entirely on the current task.

3. **Parallel execution with independent reasoning** — Multiple subagents can reason independently on different tasks simultaneously. Each gets its own fresh Haiku context. Parent (conductor) can dispatch 3 code reviewers in parallel, each working in isolation, then collect results.

4. **Clear input/output contracts prevent miscommunication** — A subagent's role, inputs, and outputs are explicit contracts. Parent session knows exactly what to give and what to expect back.

This guide teaches you to write subagents that are **focused, unambiguous, and reliably executable**.

## Product language (brain)

When the parent passes a **`task_id`**, if **`~/forge/brain/prds/<task-id>/terminology.md`** exists, subagents that author **user-facing** text, **API error** copy, or **eval/QA** assertions must **read** that file from the brain path (or ask the parent to pass the path in the dispatch prompt) and use **canonical** product terms — not [forge-glossary](../forge-glossary/SKILL.md) alone. The **conductor does not** auto-inject term excerpts; the subagent’s allowed tools must include **Read** for that path. See [docs/terminology-review.md](../../docs/terminology-review.md).

## Part 1: Required Sections

Every subagent definition MUST include these sections. They form an explicit contract between the parent conductor and the specialized subagent.

```markdown
# {Subagent Name}

## Role
[Specific 1-line role description]

## When to Invoke
[Explicit trigger conditions]

## Inputs
[Complete list of required inputs with formatting specs]

## Workflow
[Step-by-step process the subagent follows]

## Output
[Status codes and structured output format]

## Edge Cases
[At least 3 documented edge cases with explicit actions]

## Examples
[Concrete usage examples with realistic inputs and outputs]
```

Each section is described in detail below.

## Part 2: Detailed Section Breakdown

### Role Section

The **Role** defines what specialized persona this subagent embodies, its expertise boundary, and its scope.

A good role statement:
- Names the **specific role** (not "code reviewer" but "spec compliance reviewer for implementation tasks")
- Defines **scope boundaries** — what is in scope, what is explicitly out
- States **expertise level assumptions** — what does this subagent know? What is it expert at?
- Is **unambiguous** — reading the role, a parent conductor knows exactly what to expect

**Anti-pattern**: "Code Reviewer"
**Why it's bad**: Too vague. Does it review API contracts? Performance? Security? Readability? All of the above?

**Good pattern**: "Spec Compliance Reviewer — Verifies that implementation matches the shared-dev-spec requirements, line-by-line, requirement-by-requirement."

**Examples by role:**

- `spec-reviewer`: Verify implementation matches shared-dev-spec requirements (requirement-by-requirement, in scope for correctness only)
- `code-quality-reviewer`: Audit code against 8-point quality framework (performance, security, observability, readability, maintainability, testability, modularity, performance) — out of scope: architecture review
- `architecture-reviewer`: Evaluate high-level design decisions (module boundaries, API contracts, dependency directions) — out of scope: code-level style or implementation details
- `test-writer`: Write unit tests for given code (100% coverage of public API) — out of scope: integration/e2e tests
- `performance-profiler`: Identify bottlenecks and generate optimization proposals (profiling data, measurement methodology) — out of scope: implementation

### When to Invoke Section

**When to Invoke** specifies the trigger conditions. When should a parent conductor dispatch this subagent? Under what circumstances is it the right choice?

A good "When to Invoke" includes:
- **Clear trigger conditions** — "When implementation is DONE, dispatch spec-reviewer"
- **Task characteristics** that warrant this subagent — "When code file is under 500 lines and is a single concern"
- **NOT when to invoke** — boundary cases where this is the wrong subagent
- **Examples with good and bad cases** — "Good case: single endpoint review. Bad case: refactoring entire auth system."

**Anti-pattern**: No explicit conditions ("invoke whenever needed")
**Why it's bad**: Parent doesn't know when. Leads to duplicate dispatches or missed reviews.

**Good pattern**: 
```
Invoke when:
- Implementation is complete (DONE status)
- Code is readable (no WIP markers)
- You have the shared-dev-spec and prior review feedback (if any)

Do NOT invoke:
- During WIP (incomplete implementation)
- If shared-dev-spec is missing or locked
- If prior spec-reviewer feedback has not been addressed
- On architecture-level decisions (use architecture-reviewer instead)
```

**Examples:**

- `spec-reviewer`: "Invoke after dev-implementer returns DONE. Do NOT invoke on architecture proposals or design docs."
- `code-quality-reviewer`: "Invoke after spec-reviewer returns DONE. Do NOT invoke on incomplete code or before spec compliance is verified."
- `test-writer`: "Invoke when implementation is feature-complete and code is stable. Do NOT invoke on refactoring PRs or incomplete endpoints."

### Inputs Section

**Inputs** are everything the subagent needs to do its job. Crucial: Subagent gets isolated context, so "obvious" context is NOT obvious without explicit specification.

A good Inputs section:
- **Documents all required inputs** — every piece of information needed to complete the task
- **Provides full text, not file references** — Subagent is in isolation. "See `/src/auth.ts`" is useless. Provide full file text.
- **Specifies format** — "YAML, 50 lines max" or "Markdown with code blocks"
- **Includes scene-setting context** — why is this task needed? What is the business context?
- **Marks required vs optional** — which inputs block task completion, which are nice-to-have?

**Anti-pattern**: 
```
Inputs:
- Implementation file
- Spec reference
- Prior feedback
```

**Why it's bad**: 
- "Implementation file" — which file? Full path? Relative path? Is it in the worktree?
- "Spec reference" — link? Is the link accessible in isolation?
- "Prior feedback" — which feedback? Which format? Is it expected to influence the decision?

**Good pattern**:
```
Inputs (Required):
1. Full implementation code (YAML block, complete)
   - Example: "```yaml\nclass AuthService: ...```"
   - Constraint: Single file under 2000 lines
   
2. Specification text (Markdown, verbatim)
   - Example: "# Auth Spec\n## Requirements\n..."
   - Constraint: Include all numbered requirements
   - Format: Markdown with explicit requirement IDs

3. Scene-setting context (Markdown prose)
   - Explain: What is this task for? Why now? What's the business goal?
   - Example: "We're hardening the auth layer for GDPR compliance. This PR adds password rotation enforcement."
   - Format: 2-3 sentences, max 200 words

Inputs (Optional):
1. Prior review feedback (Markdown list)
   - If available, include prior spec-reviewer notes
   - May influence depth of re-verification
```

### Workflow Section

**Workflow** is the step-by-step process the subagent follows. It is not a high-level goal (that's the Role). It is the granular decision tree and sequence.

A good Workflow:
- **Step-by-step process** — numbered steps, each specific
- **Questions the subagent may ask** — "Does this match requirement #5?" "Is error handling complete?"
- **Checkpoints and validation** — "After step 3, verify X before moving to step 4"
- **Failure modes and recovery** — "If requirement #2 is missing, flag as DONE_WITH_CONCERNS, not DONE"

**Anti-pattern**:
```
Workflow:
1. Read the spec
2. Review the code
3. Compare them
4. Report findings
```

**Why it's bad**: Too abstract. Subagent doesn't know what "compare" means. What granularity? What are the comparison criteria?

**Good pattern**:
```
Workflow:

1. **Parse spec requirements** (step 1)
   - Read spec top-to-bottom
   - Extract all numbered requirements into a checklist
   - Verify checklist is complete (no missing #s)
   - Checkpoint: Confirm spec is well-formed before proceeding

2. **Read implementation code** (step 2)
   - Scan code structure (classes, functions, error handlers)
   - Note: Look for requirement references in comments
   - Flag: Any code not referenced in spec (out-of-scope code)

3. **Line-by-line requirement verification** (step 3)
   - For each requirement in checklist:
     a. Find corresponding code implementation
     b. Verify implementation matches requirement text exactly
     c. Check error handling matches requirement
     d. Verify types/formats match requirement
     e. Mark as VERIFIED or MISSING
   - Checkpoint: If any requirement is MISSING, transition to "NEEDS_CONTEXT" (ask parent for clarification)

4. **Cross-validation** (step 4)
   - Any code found in step 2 not covered by spec? Flag as DONE_WITH_CONCERNS
   - Any requirement not implemented? Flag as DONE_WITH_CONCERNS

5. **Report** (step 5)
   - If all requirements VERIFIED and no extra code: Status = DONE
   - If all requirements VERIFIED but some concerns exist: Status = DONE_WITH_CONCERNS
   - If requirements are unclear or spec is malformed: Status = NEEDS_CONTEXT
```

### Output Section

**Output** defines the exact format of what the subagent returns. Parent session uses this structure to route results.

A good Output section:
- **Status codes** — which status is this subagent returning? (DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED)
- **Structured output** — not prose, but clear sections (findings, recommendations, next steps)
- **Reasoning section** — why this status? What led to this conclusion?
- **Actionable format** — parent can parse this and act on it

**Anti-pattern**:
```
Output:
- Status
- A summary of findings
```

**Why it's bad**: "Summary of findings" is prose. How does parent session parse it? How does it route results for action?

**Good pattern**:
```
Output:

Status: [DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED]

Structured Findings:
- Requirement coverage: X/Y implemented
- Specification coverage: Z% complete
- Issues found: [list with severity]
- Recommendations: [actionable list]

Reasoning:
- Why this status?
- What was the deciding factor?
- What should parent conductor do next?

Examples by status:

DONE:
```
Status: DONE
Findings:
  - All 12 requirements implemented
  - Code structure matches spec sections
  - Error handling complete for all paths
Reasoning: Full compliance, no gaps, no extra code.
Next: Proceed to code-quality-reviewer.
```

DONE_WITH_CONCERNS:
```
Status: DONE_WITH_CONCERNS
Findings:
  - 11/12 requirements implemented
  - Requirement #7 (audit logging) not found in code
  - Extra validation added in getUser() not in spec
Concerns:
  - Audit logging may be in infrastructure layer (outside scope)
  - Extra validation is good for security but not spec-required
Reasoning: Implementation is functionally complete but has spec drift.
Next: Parent should clarify if audit logging is expected in this file, and whether extra validation is acceptable.
```

NEEDS_CONTEXT:
```
Status: NEEDS_CONTEXT
Findings:
  - Specification is ambiguous on requirement #5
  - "Secure token storage" is not defined (where? how?)
  - Code implements bcrypt but spec doesn't mention bcrypt
Reasoning: Cannot verify compliance without clarity on requirement #5.
Parent should: Clarify requirement #5, re-dispatch.
```

BLOCKED:
```
Status: BLOCKED
Issue: Specification is locked and unmodifiable. Requirement #8 contradicts requirement #11. Cannot verify compliance without resolving contradiction.
Next: Escalate to conductor for spec clarification or unlock.
```
```

### Edge Cases Section

**Edge Cases** document scenarios where the "happy path" doesn't apply. Each edge case should include:
- **Symptom** — what situation triggers this edge case?
- **Subagent action** — what does the subagent do when this happens?
- **Escalation path** — what status does it report, and what should parent do?

A good Edge Cases section includes **at least 3** documented cases.

**Anti-pattern**:
```
Edge cases:
- "Spec is incomplete" — ask parent for clarification
- "Code is unreadable" — ask parent to clean it up
```

**Why it's bad**: Too vague. "Ask parent" is not a status. How does parent know to ask?

**Good pattern**:
```
Edge Case #1: Specification is ambiguous or incomplete

Symptom: Subagent reads spec and cannot extract clear requirements (requirements are conditional, use vague language like "should", lack specific acceptance criteria)

Subagent action: 
1. Document specific ambiguities (note the line/section)
2. List assumptions subagent is making to proceed
3. Report as NEEDS_CONTEXT

Parent action: Clarify spec, re-dispatch with clearer requirements

Example: Spec says "provide secure authentication" but doesn't specify:
- What cipher?
- What key length?
- What protocol version?
→ Subagent cannot verify implementation matches spec without knowing these
→ Report NEEDS_CONTEXT: "Requirement #3 uses 'secure' but doesn't specify cipher, key length, or protocol version. Clarify before re-dispatch."

---

Edge Case #2: Code and spec mismatch (intentional divergence)

Symptom: Implementation intentionally differs from spec. Code includes extra features not in spec, or implements spec requirements differently than described.

Subagent action:
1. Identify each divergence (requirement #X implemented as Y instead of Z)
2. Assess severity (is this a breaking change? Is it incompatible?)
3. Report as DONE_WITH_CONCERNS (not BLOCKED — the code works, it's just different)

Parent action: Decide whether divergence is acceptable, update spec if needed, or re-implement

Example: Spec says "use RSA-2048 for encryption" but code implements AES-256. Both are secure, but they're different.
→ Subagent reports DONE_WITH_CONCERNS: "Requirement #5 specifies RSA-2048, but implementation uses AES-256. Both are cryptographically sound, but they diverge. Clarify if this is intentional."

---

Edge Case #3: Spec references external documents subagent cannot access

Symptom: Spec says "Implement according to OWASP guidelines" but OWASP doc is not provided in inputs

Subagent action:
1. Identify the reference (Spec requires "conformance to X")
2. Note: Subagent is in isolation and cannot fetch external resources
3. Report as NEEDS_CONTEXT: "Spec references OWASP CWE-352 (CSRF) but document not provided. Please provide or clarify requirements."

Parent action: Provide referenced document, or quote the relevant requirement, then re-dispatch

Example: Spec says "Follow JWT RFC 7519 section 3.2" but RFC text not provided
→ Subagent reports NEEDS_CONTEXT: "Spec references RFC 7519 section 3.2, which is not provided in inputs. Cannot verify implementation without this. Please quote the relevant RFC section or clarify the requirements."
```

### Examples Section

**Examples** are concrete, realistic walkthroughs. Not templates — actual example inputs, expected workflow, and expected output.

A good Examples section includes:
- **Realistic example inputs** (not toy examples, actual-size code/specs)
- **Expected workflow and questions** (show subagent's reasoning)
- **Expected output** (show actual status, structured findings, reasoning)
- **What success looks like** (define the win condition)

**Anti-pattern**:
```
Example:
Input: Some spec and code
Workflow: Read both
Output: Status and findings
```

**Why it's bad**: Too abstract. Doesn't show actual scale, actual reasoning, or what good output looks like.

**Good pattern**:

See **Part 6: Worked Example — Good vs Bad Subagent Anatomy** below for a full example.

## Part 3: Anti-Patterns for Subagent Authoring

These are 5 common mistakes when writing subagents. Each includes enforcement bullets to prevent the mistake.

### Anti-Pattern #1: "Role can be vague"

**Why this is bad**: A vague role means the subagent doesn't know its expertise boundary. It will try to solve problems outside its scope, or miss critical aspects because it's unclear what "critical" means.

**Example**: Role = "Code Reviewer"
- Does this review API contracts? (maybe, maybe not)
- Does this review performance? (unclear)
- Does this review security? (unclear)
- Does this review documentation? (unclear)

Result: Subagent guesses. Parent gets inconsistent results.

**Enforcement (MUST have all 5):**
1. Role must name a specific expertise or perspective (not "reviewer" but "performance reviewer" or "spec compliance reviewer")
2. Scope boundaries must be explicitly stated (in scope: ..., out of scope: ...)
3. Expertise level must be defined (e.g., "expert in cryptography" or "knowledgeable in REST API design")
4. Role must be 1-2 sentences max (longer suggests it's doing too much)
5. Role must answer: "What is this subagent's unique perspective on the problem?"

**Audit checklist**:
- [ ] Does the role have a specific, unambiguous name?
- [ ] Are scope boundaries explicitly stated?
- [ ] Is expertise level defined?
- [ ] Could two different engineers write the same role and get the same interpretation?

---

### Anti-Pattern #2: "Inputs are obvious"

**Why this is bad**: Subagent is in isolation. What's "obvious" in your head is not obvious without explicit specification. Subagent will either guess (and guess wrong) or report NEEDS_CONTEXT every time.

**Example**: Input = "Full implementation code"
- Which implementation? (multiple files? single file? which directory?)
- In what format? (can subagent assume it's a single file, or could it be 10 files?)
- What about imports and dependencies? (should subagent understand them? are they provided?)
- What about context from other parts of the codebase? (should subagent know about other modules?)

Result: Subagent either wastes time asking for clarification, or makes wrong assumptions.

**Enforcement (MUST have all 5):**
1. Every input must be explicitly named and described (not "code" but "implementation code: getUser() function in TypeScript")
2. Provide full text, never file paths (subagent is in isolation, file paths are useless)
3. For complex inputs, include format specification (YAML, JSON, Markdown, line count, section structure)
4. For each input, state whether it's required or optional (and what happens if optional input is missing)
5. Include a "scene-setting" input that explains why this task matters (business context)

**Audit checklist**:
- [ ] Is every input explicitly named?
- [ ] Is full text provided (not file references)?
- [ ] Are formats specified?
- [ ] Are required/optional marked?
- [ ] Is there a scene-setting context explaining why?
- [ ] Could another engineer read the inputs and provide exactly what's needed?

---

### Anti-Pattern #3: "Workflow section is optional"

**Why this is bad**: Without a workflow, subagent guesses at the process. What does "review the code" mean? Line by line? Section by section? Does it check everything or just critical paths? Result: inconsistent reviews, missed findings.

**Example**: Workflow = "Read code and compare to spec"
- What order? (top to bottom? requirements first? error handling first?)
- What granularity? (line-by-line? function-by-function? conceptual?)
- What's the decision tree? (if requirement is missing, what then? if code has extra, what then?)
- What are the checkpoints? (after reading spec, verify it's well-formed before reading code?)

Result: Subagent follows a random process. Parent gets inconsistent findings.

**Enforcement (MUST have all 5):**
1. Workflow must be step-by-step numbered (not prose, not high-level)
2. Each step must be specific and actionable (subagent can follow it without interpretation)
3. Each step must have a decision point or checkpoint (e.g., "After step 3, verify X before step 4")
4. Workflow must include questions subagent should ask (e.g., "Does this match requirement #5?")
5. Workflow must include failure modes (e.g., "If requirement missing, report DONE_WITH_CONCERNS")

**Audit checklist**:
- [ ] Is workflow numbered and sequential?
- [ ] Is each step specific enough that another engineer could follow it?
- [ ] Are checkpoints and decision points explicit?
- [ ] Are subagent questions documented?
- [ ] Are failure modes and recovery paths documented?

---

### Anti-Pattern #4: "Output format doesn't matter"

**Why this is bad**: Parent session needs to parse output and route results. If output format is unstructured or varies, parent cannot automate processing. Results pile up in an inbox instead of being actioned.

**Example**: Output = "Report findings and status"
- What findings? (prose paragraphs? bullet list? table?)
- What's the structure? (findings first, then status? status first?)
- How does parent parse "report findings"? (regex? keyword search? ask for clarification?)
- What if there are multiple findings of different types? (how are they grouped?)

Result: Parent can't automate. Each result requires manual parsing.

**Enforcement (MUST have all 5):**
1. Status codes must be explicit (DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED) — no variants
2. Output must be structured, not prose (sections with headers, bullet lists, tables — not paragraphs)
3. Each status must have a different output format (parent knows what to expect based on status)
4. Reasoning section must explicitly state "why this status" (parent doesn't have to guess)
5. Actionable next steps must be included (parent knows what to do with each status)

**Audit checklist**:
- [ ] Are status codes only the 4 standard ones?
- [ ] Is output structured (not prose)?
- [ ] Is there a different output format for each status?
- [ ] Does reasoning section explain why?
- [ ] Are next steps actionable?
- [ ] Could a non-human parser (regex, JSON extraction) reliably extract the structure?

---

### Anti-Pattern #5: "Examples can be minimal"

**Why this is bad**: Minimal examples don't show realistic scenarios. "Example: Review this function" doesn't show what happens when code is 10,000 lines, or when spec is ambiguous, or when there are edge cases. Subagent doesn't know how to behave at scale.

**Example**: Example = 50 lines of code, 10 requirements, happy path only
- What if code is 5,000 lines? (does workflow scale? do checkpoints still work?)
- What if spec is ambiguous? (example doesn't show this scenario)
- What if code has edge cases? (example doesn't cover this)
- What if requirements conflict? (example doesn't show resolution)

Result: Subagent works fine on examples but fails on real scenarios.

**Enforcement (MUST have all 5):**
1. Examples must be realistic in scale (not toy examples, actual-size code/specs)
2. Examples must show multiple scenarios (happy path, edge cases, ambiguous specs)
3. Examples must include workflow walkthrough (show subagent's reasoning step by step)
4. Examples must show output for each status (what does DONE look like? DONE_WITH_CONCERNS? NEEDS_CONTEXT?)
5. Examples must define success criteria (how does subagent know it did the job right?)

**Audit checklist**:
- [ ] Are examples realistic in scale?
- [ ] Do examples cover happy path AND edge cases?
- [ ] Is subagent reasoning shown?
- [ ] Are output examples provided for each status?
- [ ] Are success criteria defined?
- [ ] Could a new engineer read the examples and write the same subagent?

---

## Part 4: Edge Cases for Subagent Usage

These are 5 scenarios that commonly occur when deploying subagents. Each includes the symptom, action, and escalation path.

### Edge Case #1: Subagent Gets Wrong Context

**Symptom**: Parent session provides incomplete or misdirected context. Subagent receives partial code, incomplete spec, or context for a different task.

**Action**: Subagent should NOT guess or proceed with incomplete context. Instead, declare NEEDS_CONTEXT.
- Document what's missing (e.g., "Received getUser() function but inputs say 'full auth module' — missing 5 other functions")
- List what's needed to proceed (e.g., "Need full auth.ts file, not just getUser()")
- Report NEEDS_CONTEXT with specific requirements

**Escalation**: Parent session reviews NEEDS_CONTEXT output, provides correct context, re-dispatches.

If parent keeps sending wrong context after 2 re-dispatches → Escalate to BLOCKED. "Repeated context mismatch. Requires human review of task definition."

**Example**: Subagent spec-reviewer receives getUser() function but spec describes entire Auth module (login, logout, session, token refresh). 
- Subagent: "Context mismatch. Received 1 function but spec describes 5 functions. Cannot verify partial implementation. Report NEEDS_CONTEXT: Provide full auth.ts with all 5 functions."
- Parent: Re-reads task, realizes it asked for getUser() but provided wrong spec. Corrects and re-dispatches.

---

### Edge Case #2: Subagent Is Too Broad

**Symptom**: Subagent trying to handle multiple distinct concerns. Example: "Review code quality AND security AND performance" — that's 3 subagents, not 1.

**Action**: Subagent should recognize scope creep and split itself.
- Document what's bundled (e.g., "This role covers code quality (readability, maintainability) AND security (input validation, OWASP) AND performance (runtime, memory)")
- List what should be split (e.g., "Security should be a separate subagent with cryptography expertise")
- Report NEEDS_CONTEXT: "Role is too broad. Split into: code-quality-reviewer, security-reviewer, performance-reviewer"

**Escalation**: Parent conductor notes the feedback, creates separate subagents for each concern, dispatches all three in parallel.

**Example**: "Code Review Subagent" has a role like "Review code for quality, security, performance, and documentation"
- Subagent: "Role bundles 4 concerns: quality, security, performance, docs. Each deserves specialized review. Recommend splitting into 4 subagents with separate expertise. Report NEEDS_CONTEXT."
- Parent: Creates code-quality-reviewer, security-reviewer, performance-reviewer, docs-reviewer. Dispatches all 4 in parallel.

---

### Edge Case #3: Subagent Overlaps With Existing Agent

**Symptom**: New subagent duplicates role of existing agent. Example: Creating a "code-reviewer" when code-quality-reviewer already exists.

**Action**: Check the **Existing Subagents** table (see below) before creating new subagents.
1. Search existing agents in `agents/` directory
2. If role already exists, reuse (don't create duplicate)
3. If role is similar but distinct, clarify the distinction (update both roles to avoid confusion)

**Escalation**: If overlap is discovered, conductor consolidates: either merge the two subagents or clarify role distinction and add to Existing Subagents table.

**Example**: "Implement a new 'quality-reviewer' subagent"
- Check: code-quality-reviewer already exists in `agents/code-quality-reviewer/`
- Action: Reuse code-quality-reviewer, don't create quality-reviewer
- If distinction is needed: Document the difference and add both to Existing Subagents table

---

### Edge Case #4: Subagent Needs Blocking Tool Access

**Symptom**: Subagent cannot complete task without write/deploy/execute tools. Example: "Test-writer subagent needs to run tests" — but running tests is a blocking operation.

**Action**: Clarify if this is really a subagent task or if it belongs in parent session.
- Subagents should output (code, analysis, decisions) not execute/deploy
- If task requires execution (run tests, deploy code, validate in prod), it's a parent session responsibility
- Subagents can check code for testability, but cannot run tests

**Escalation**: NEEDS_CONTEXT (architecture review). "This task requires execution. Clarify: Is this a subagent task (output test code) or parent session task (output + run tests)?"

**Example**: "Test-Writer Subagent" asked to "write tests and verify they pass"
- Writing tests → Subagent output
- Verifying tests pass → Parent session action (requires test runner)
- Subagent: "Role bundled writing tests (output) with verifying tests (execution). Subagents output; parent session executes. Clarify scope: output only, or output + execute?"

---

### Edge Case #5: Subagent Receives Too Much Prior Context

**Symptom**: Subagent context includes full conversation history, prior decisions, past attempts, all notes. Subagent is polluted with historical context.

**Action**: Subagent should flag context pollution and reject.
1. Identify what's extra (conversation history, prior attempts, notes not relevant to current task)
2. List what should be removed
3. Report NEEDS_CONTEXT: "Context includes unrelated history (prior attempts #1-3, conversation artifacts). Provide only current task context."

**Escalation**: Parent session cleans context, provides only task-specific information, re-dispatches.

**Example**: Subagent receives 10,000 tokens of prior conversation, 5 failed attempts, notes from other engineers, plus the actual task (100 tokens).
- Subagent: "Context includes 90% unrelated history and 10% current task. Cannot focus. Report NEEDS_CONTEXT: Provide only current task context (implementation code + spec + prior review feedback, if any). Remove conversation history and prior attempts."
- Parent: Extracts only current task context, re-dispatches.

---

## Part 5: Decision Tree — When to Create a Subagent

Use this decision tree to determine: **Should I create a subagent, reuse an existing agent, or inline the task?**

```
START: Do I have a specialized task?
│
├─ YES → Does it fit an existing subagent role?
│        │
│        ├─ YES → Reuse existing subagent (check Existing Subagents table)
│        │
│        └─ NO → Is it a specialized, isolated concern?
│                │
│                ├─ YES → Is it independent from parent session context?
│                │        │
│                │        ├─ YES → Create subagent
│                │        │        (specialized role, fresh context, parallel capable)
│                │        │
│                │        └─ NO → Inline in parent session
│                │                (needs conversation history or parent state)
│                │
│                └─ NO → Inline in parent session
│                        (not specialized enough to warrant isolation)
│
└─ NO → Inline in parent session
        (not a distinct task)

---

DECISION EXAMPLES:

1. "Review code for spec compliance"
   → Specialized? YES → Existing subagent? YES (spec-reviewer) → Reuse spec-reviewer

2. "Review code for cryptography correctness"
   → Specialized? YES → Existing subagent? NO → Independent? YES → Create security-reviewer

3. "Implement feature X"
   → Specialized? YES (implementation) → Existing subagent? YES (dev-implementer) → Reuse dev-implementer

4. "Implement feature X, but context depends on 5 prior decisions"
   → Specialized? YES → Existing subagent? YES (dev-implementer) → Independent? NO → Inline in parent session
   → Reason: dev-implementer needs context from prior work; use parent session so context is available

5. "Decide which database technology to use"
   → Specialized? NO (decision-making, not specialized execution) → Inline in parent session
   → Reason: Needs broad context and prior decisions; not a specialized task

```

## Part 6: Worked Example — Good vs Bad Subagent Anatomy

### BAD Example: Vague Code Reviewer

```yaml
---
name: code-reviewer
---

# Code Reviewer

## Role
Review code.

## When to Invoke
When you need code reviewed.

## Inputs
- Code file
- Any additional context

## Workflow
1. Read code
2. Find issues
3. Report findings

## Output
Status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
Findings: [issues found]
Recommendations: [what to fix]

## Edge Cases
- Code is unreadable: Ask parent for cleaner code
- No context: Ask parent for context
- Code is incomplete: Ask parent to complete it

## Examples
Input: Some code
Output: Findings and status
```

**Why it's bad:**
- Role is vague ("Review code" — what aspect? quality? spec compliance? security?)
- Inputs don't specify format or scope (which code file? how big? what language?)
- Workflow is too abstract (what's the process? What questions should subagent ask?)
- Output format is unstructured (what does "findings" look like? How does parent parse it?)
- Edge cases are reactive ("ask parent" — not actionable)
- Examples are templates, not realistic (not show actual code, actual findings, actual reasoning)

---

### GOOD Example: Spec Compliance Reviewer

```yaml
---
name: spec-compliance-reviewer
---

# Spec Compliance Reviewer

## Role
Verify that implementation code matches the shared-dev-spec requirements, line-by-line, requirement-by-requirement. Expertise: requirement analysis, implementation tracing. Scope: correctness only (not performance, security, style — see code-quality-reviewer for that). Out of scope: architecture review, API contract negotiation.

## When to Invoke
- Invoke when: Implementation is marked DONE by dev-implementer, you have the shared-dev-spec and implementation code
- Do NOT invoke: During WIP, if shared-dev-spec is locked/unmodifiable, if prior feedback has not been addressed, on architecture-level proposals
- Trigger: After dev-implementer returns DONE status
- Precondition: shared-dev-spec is unlocked and readable

## Inputs (Required)

1. **Specification text** (Markdown, complete)
   - Full text of shared-dev-spec
   - All numbered requirements (#1, #2, #3...)
   - Format: Markdown with explicit requirement IDs
   - Example:
     ```
     # Auth Module Specification
     
     ## Requirements
     #1 Login endpoint accepts username/password
     #2 On success, return JWT token
     #3 Token includes user ID and expiration
     ...
     ```
   - Constraint: All requirements must have explicit IDs

2. **Implementation code** (Single language file, complete)
   - Full implementation code (not excerpts, not references)
   - Single file under 3000 lines (if larger, split into multiple reviews)
   - Format: Code block with language marker
   - Example:
     ```typescript
     class AuthService {
       async login(username: string, password: string) {
         // implementation
       }
     }
     ```
   - Constraint: Include all imports, types, and logic

3. **Scene-setting context** (Markdown prose, 2-3 sentences)
   - Why is this review happening?
   - What's the business context?
   - Example: "We're implementing the Auth module for GDPR compliance. This PR implements login and session management."

Inputs (Optional)

1. **Prior review feedback** (Markdown list, if available)
   - Any previous spec-reviewer notes or corrections
   - Format: Bullet list with requirement ID and feedback
   - Example:
     ```
     - #1: Prior feedback said "username should accept email or username"
     - #3: Prior feedback said "token expiration should be configurable"
     ```
   - Purpose: Flags areas already reviewed; helps avoid repeat findings

## Workflow

**Step 1: Parse Specification** (Checkpoint: Verify spec is well-formed)
1. Read spec top-to-bottom
2. Extract all numbered requirements (#1, #2, #3...) into a checklist
3. For each requirement, identify:
   - What is being tested? (e.g., "endpoint accepts username/password")
   - What is the acceptance criterion? (e.g., "returns JWT token on success")
   - Are there edge cases? (e.g., "invalid password returns 401")
4. Verify checklist is complete (no skipped numbers, no duplicates)
5. **Checkpoint**: If spec is malformed (missing requirements, unclear IDs, ambiguous language), STOP and report NEEDS_CONTEXT

**Step 2: Read Implementation Code** (Checkpoint: Understand code structure before verification)
1. Scan code top-to-bottom
2. Identify:
   - Class/function names and signatures
   - Error handling paths (throw, return error, retry)
   - Dependencies (what does this code depend on?)
   - Side effects (database writes, logging, external calls)
3. Note any code comments that reference requirements (e.g., "// Implements #2: return JWT")
4. Flag any code NOT referenced in spec (extra code, out-of-scope logic)
5. **Checkpoint**: If code structure is unclear (missing functions, unreadable, no comments), note but continue (flag as DONE_WITH_CONCERNS)

**Step 3: Line-by-Line Requirement Verification** (Core of review)
1. For EACH requirement in checklist:
   a. Find the code that implements this requirement
   b. Read that code closely
   c. Verify code matches requirement text exactly
   d. Check error handling (does code handle all error cases in requirement?)
   e. Check types/formats (does code use correct types? String, int, JWT format?)
   f. Check side effects (does code do what requirement says, no more, no less?)
   g. Mark as:
      - ✓ VERIFIED (code matches requirement exactly)
      - ✗ MISSING (requirement not found in code)
      - ⚠ PARTIAL (some but not all of requirement implemented)
      - ? UNCLEAR (code implementation matches requirement ambiguously)

2. **Checkpoint**: If any requirement is MISSING or PARTIAL:
   - Subagent MUST report NEEDS_CONTEXT
   - Explain which requirement is missing and why
   - Ask parent: "Is this intentional? Should implementation be completed?"

**Step 4: Cross-Validation** (Check for gaps and extra code)
1. Any code found in Step 2 NOT covered by requirements? (Extra code)
   - List it
   - Assess: Is it infrastructure (logging, error handling, validation that's not in spec but is good engineering)? Or is it out-of-scope?
   - Flag as observation (not an error, but something parent should know)

2. Any requirement in checklist without corresponding code? (Gap)
   - Mark as MISSING
   - Flag for parent action

**Step 5: Determine Status**
- If all requirements are VERIFIED and no extra code → Status: DONE
- If all requirements VERIFIED but some extra code or concerns → Status: DONE_WITH_CONCERNS
- If any requirement is MISSING, PARTIAL, or spec is unclear → Status: NEEDS_CONTEXT
- If implementation is blocked (cannot proceed, requires redesign) → Status: BLOCKED

**Step 6: Report**
- Output structured findings (see Output section below)
- Explain status decision
- List next steps for parent

## Output

**Status: DONE**

```
Status: DONE
Requirements Coverage: 12/12 verified
Extra Code: None beyond spec
Summary: Implementation matches specification 100%. All requirements implemented, error handling complete, no gaps.

Findings:
- #1 Login endpoint: ✓ Verified (accepts username and password as strings)
- #2 JWT response: ✓ Verified (returns JWT on success)
- #3 Token contents: ✓ Verified (includes user_id and exp fields)
- ... (all requirements listed)

Concerns: None

Reasoning:
All 12 requirements are implemented correctly. Code structure matches spec sections. Error handling is complete. No deviations from spec.

Next Step: Proceed to code-quality-reviewer for 8-point quality review.
```

**Status: DONE_WITH_CONCERNS**

```
Status: DONE_WITH_CONCERNS
Requirements Coverage: 11/12 verified, 1 extra
Summary: Implementation covers all numbered requirements but includes extra validation not in spec. Ready for code-quality review, but parent should clarify scope of extra validation.

Findings:
- #1 Login endpoint: ✓ Verified
- #2 JWT response: ✓ Verified
- #3 Token contents: ✓ Verified
- #4-#11: ✓ Verified
- Extra: Code includes rate limiting on login (not in spec)

Concerns:
- Extra rate limiting: Implementation adds rate limiting not required by spec. Is this intentional? Is it acceptable?

Reasoning:
All required functionality is present. The extra rate limiting is good security practice, but it's scope creep if not intentional.

Next Step: Parent should clarify: Is rate limiting out-of-scope, or should spec be updated to include it? If rate limiting is intentional, update spec. Otherwise, remove from implementation.
```

**Status: NEEDS_CONTEXT**

```
Status: NEEDS_CONTEXT
Requirements Coverage: 9/12 verified, 3 missing
Summary: Implementation is incomplete. Three requirements (#5, #8, #11) are not found in code.

Findings:
- #1-#4: ✓ Verified
- #5 Token refresh: ✗ Missing (spec requires refresh endpoint, but no code found)
- #6-#7: ✓ Verified
- #8 Logout: ✗ Missing (spec requires logout endpoint, not found)
- #9-#10: ✓ Verified
- #11 Session cleanup: ✗ Missing (spec requires cleanup after logout, not found)

Concerns:
- Missing requirements: #5, #8, #11 are not implemented

Reasoning:
Implementation is incomplete. Three critical requirements (token refresh, logout, session cleanup) are missing from the code. Cannot declare compliance without these.

Next Step: Complete implementation of #5, #8, #11, then re-dispatch for verification.
```

**Status: BLOCKED**

```
Status: BLOCKED
Blocker: Specification is ambiguous and locked (cannot modify)
Issue: Requirement #3 says "Token includes expiration" but doesn't specify format (JWT standard exp field? Unix timestamp? ISO8601 string?). Implementation uses JWT standard exp (Unix timestamp), but spec doesn't confirm this is correct.

Cannot verify correctness without clarity on requirement #3.

Reasoning:
Spec is ambiguous. Implementation made a reasonable choice, but without spec confirmation, cannot declare compliance.

Next Step: Escalate to conductor. Spec is locked and unmodifiable. Either unlock spec for clarification, or provide explicit written confirmation that implementation's choice (Unix timestamp in exp field) is accepted.
```

## Edge Cases Examples

**Edge Case #1: Incomplete context**

Parent provides: Only the login() function
Spec describes: Full Auth module (login, logout, refresh, session, etc.)

Subagent reasoning:
"Spec describes 5 functions; received 1. Cannot verify full spec compliance with partial code. Report NEEDS_CONTEXT: Provide full auth.ts with all 5 functions (login, logout, refreshToken, getSession, clearSession)."

**Edge Case #2: Spec is ambiguous**

Spec says: "Password must be secure"
Code implements: 12-character minimum

Subagent reasoning:
"Requirement 'secure password' is ambiguous. Does it mean 12-char minimum? 8-char? Uppercase required? Spec doesn't say. Implementation chose 12-char, but without spec confirmation, this is a guess. Report NEEDS_CONTEXT: Define 'secure password' with explicit rules (minimum length, required character types)."

**Edge Case #3: Code has extra logic**

Spec requires: Login returns JWT
Code implements: Login returns JWT, plus increments login counter, plus logs event, plus rate-limits

Subagent reasoning:
"Code implements spec requirement (JWT) plus 3 extras (counter, logging, rate-limit). Extras are good engineering practice. Report DONE_WITH_CONCERNS: All required functionality present. Extra logic (logging, rate-limit) is not in spec but is good practice. Clarify if extras are acceptable or should be spec'd."

## Examples

**Example 1: Happy Path**

Input:
```
Specification (markdown):
# Login Module Spec
## Requirements
#1 Endpoint: POST /auth/login
#2 Request: {username: string, password: string}
#3 Success response: {token: string, expires_in: number}
#4 Token format: JWT with user_id and exp claims
#5 Error: invalid password returns 401 Unauthorized
#6 Error: user not found returns 404 Not Found

Implementation Code (TypeScript):
export async function login(username: string, password: string) {
  const user = await findUser(username);
  if (!user) return { error: 'User not found', status: 404 };
  
  const valid = await validatePassword(password, user.passwordHash);
  if (!valid) return { error: 'Invalid password', status: 401 };
  
  const token = jwt.sign({ user_id: user.id }, secret, { expiresIn: '1h' });
  return { token, expires_in: 3600, status: 200 };
}

Scene-setting: "Implementing auth module for user login. This PR covers login endpoint only."
```

Expected workflow:
1. Parse spec: Extract requirements #1-#6. Verify spec is well-formed. ✓
2. Read code: Identify login function, error handling (404, 401), JWT generation. ✓
3. Verify each requirement:
   - #1: Endpoint POST /auth/login → not in code (but code is function, not full endpoint routing)
   - #2: Request username/password → ✓ Function parameters match
   - #3: Success response {token, expires_in} → ✓ Returned on success
   - #4: Token format JWT with user_id, exp → ✓ jwt.sign() creates JWT, includes user_id and expiresIn
   - #5: Invalid password returns 401 → ✓ Code checks password and returns 401
   - #6: User not found returns 404 → ✓ Code checks user and returns 404
4. Cross-validate: No extra code. ✓
5. Status: DONE (all requirements verified)

Expected output:
```
Status: DONE
Requirements Coverage: 6/6 verified
Summary: Implementation matches specification completely. All requirements present, error handling correct.

Findings:
- #1 Endpoint: Note: Code is function, not endpoint routing (endpoint layer above this)
- #2 Request format: ✓ Username and password parameters
- #3 Response format: ✓ token and expires_in returned
- #4 Token format: ✓ JWT with user_id and exp
- #5 Error 401: ✓ Invalid password returns 401
- #6 Error 404: ✓ User not found returns 404

Reasoning: All requirements implemented correctly. Error handling is complete.

Next Step: Proceed to code-quality-reviewer.
```

---

**Example 2: Ambiguous Spec**

Input:
```
Specification (markdown):
# Auth Module Spec
#1 Password must be secure
#2 Return token on success
#3 Handle errors gracefully

Implementation Code (TypeScript):
export function login(username: string, password: string) {
  // Check password strength (12+ chars, numbers, symbols)
  if (password.length < 12) return { error: 'Password too weak' };
  
  // ... rest of implementation
}
```

Expected workflow:
1. Parse spec: Requirements are vague. "Secure" is undefined. "Gracefully" is undefined. ⚠
2. Checkpoint: Spec is ambiguous. Stop and report NEEDS_CONTEXT.

Expected output:
```
Status: NEEDS_CONTEXT
Blocker: Specification is ambiguous
Issues:
- #1 "Password must be secure": What is 'secure'? Min length? Char types? Strength meter?
- #3 "Handle errors gracefully": What does 'graceful' mean? Retry? Log? Return specific error codes?

Implementation assumes:
- "Secure" = 12+ chars with numbers and symbols (good practice, but not spec'd)

Reasoning: Cannot verify compliance without clarity on #1 and #3.

Next Step: Clarify requirements:
- #1: Define 'secure password' with explicit rules (e.g., "minimum 12 characters, must contain at least one number and one symbol")
- #3: Define 'handle errors gracefully' with specific actions (e.g., "return structured error codes: 401 for invalid password, 404 for user not found")
Then re-dispatch for verification.
```

---

**Example 3: Missing Requirements**

Input:
```
Specification (markdown):
#1 Login endpoint accepts username/password
#2 Return JWT token on success
#3 Token includes user ID and expiration
#4 Logout endpoint clears session
#5 Logout returns 200 OK

Implementation Code (TypeScript):
export function login(username: string, password: string) {
  // ... authenticate ...
  const token = jwt.sign({ user_id }, secret);
  return { token };
}
// No logout function
```

Expected workflow:
1. Parse spec: 5 requirements. ✓
2. Read code: login() found, but no logout(). ⚠
3. Verify:
   - #1-#3: ✓ Verified in login()
   - #4 Logout: ✗ Missing (no logout function)
   - #5 Logout 200 OK: ✗ Missing (no logout function)
4. Checkpoint: Missing #4, #5. Report NEEDS_CONTEXT.

Expected output:
```
Status: NEEDS_CONTEXT
Requirements Coverage: 3/5 verified, 2 missing
Issues:
- #1-#3: ✓ Verified (login endpoint and token implementation correct)
- #4 Logout endpoint: ✗ Missing (no logout function in code)
- #5 Logout 200 OK: ✗ Missing (depends on #4)

Reasoning: Implementation is incomplete. Logout endpoint is required by spec but not found in code.

Next Step: Implement logout() function, then re-dispatch for verification.
```
```

---

## Part 7: Subagent Status Codes — Clear Definitions and Handling

| Status | Definition | When to Use | Parent Action |
|---|---|---|---|
| **DONE** | Task completed successfully. All requirements met, no gaps, no concerns. Output is final and ready for next stage. | - All criteria met - No ambiguities or gaps - No extra scope to clarify | Proceed to next stage (review, merge, deploy) |
| **DONE_WITH_CONCERNS** | Task completed but flags observations, doubts, or scope clarifications needed before proceeding. Work is done, but parent should be aware of caveats. | - All core requirements done - Extra code present (good practice, but not spec'd) - Minor ambiguities resolved with assumptions - Recommendations for follow-up | Review concerns, decide: acceptable or needs rework? If acceptable, proceed. If not, send back for fixes. |
| **NEEDS_CONTEXT** | Task cannot proceed. Missing information, ambiguous requirements, or unclear inputs. Subagent has identified what's needed. | - Required input is missing - Specification is ambiguous - Context is incomplete - Parent must clarify before subagent can work | Provide clarification, send corrected inputs, re-dispatch. Do NOT assume or fill gaps yourself. |
| **BLOCKED** | Task cannot be completed. Requires intervention, redesign, or escalation. No workaround available. | - Specification contradicts itself - Infrastructure is missing - Requirements are impossible to meet - Subagent needs higher-level decision | Escalate to conductor or human. May require spec redesign, architecture review, or external decision. |

---

## Part 8: Pre-Dispatch Checklist (15 Items)

Before dispatching a subagent, verify all 15 items:

1. **[ ] Role is specific and bounded**
   - Subagent role is not vague (not "code reviewer" but "spec compliance reviewer")
   - Scope boundaries are explicit (in scope: X, out of scope: Y)
   - Expertise level is stated

2. **[ ] Inputs are complete and explicit**
   - Every input is named and described
   - No file paths; full text provided
   - Format specifications included (YAML, JSON, Markdown, line count)

3. **[ ] Scene-setting context explains task purpose**
   - Business context is clear (why is this task needed?)
   - Task has been introduced to subagent (not just "review this" but "we're implementing Auth for GDPR compliance")

4. **[ ] Workflow is step-by-step**
   - Not high-level (not "review code") but granular ("read spec, extract requirements, compare to code line-by-line")
   - Checkpoints are marked

5. **[ ] Output format is specified**
   - Status codes are explicit (only DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED)
   - Output structure is defined (findings, reasoning, next steps)
   - Examples show what DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT output looks like

6. **[ ] Status codes are clear**
   - All 4 status codes have definitions
   - Subagent knows when to use each

7. **[ ] Examples are complete and realistic**
   - Examples are actual-scale, not toy examples
   - Examples show happy path AND edge cases
   - Subagent reasoning is visible in examples

8. **[ ] Subagent knows what questions to ask**
   - Workflow includes questions subagent should ask before proceeding
   - Subagent knows what "done" means (acceptance criteria)

9. **[ ] No conversation history pollution**
   - Inputs are task-specific only
   - No conversation history, prior attempts, or unrelated context
   - Subagent gets fresh context for this task only

10. **[ ] Tool access is appropriate**
    - Subagent has tools to complete task (read, analyze, output)
    - Subagent does NOT have write/deploy/execute tools (those belong in parent session)

11. **[ ] Escalation paths are clear**
    - If subagent hits BLOCKED, what happens? (Escalate to conductor, human review?)
    - If subagent hits NEEDS_CONTEXT repeatedly, what's the escalation?

12. **[ ] Overlap with existing agents checked**
    - New subagent doesn't duplicate existing role
    - Check Existing Subagents table before creating new subagent

13. **[ ] Role distinction from parent session is clear**
    - Subagent's role is different from parent conductor's role
    - Subagent is NOT the parent session, it's a specialist

14. **[ ] Error handling is specified**
    - What if input is malformed?
    - What if specification is locked/read-only?
    - What if code is unreadable?
    - For each error scenario, what status does subagent return?

15. **[ ] Success criteria are defined**
    - How does subagent know it succeeded?
    - What does DONE output look like?
    - Can parent session tell success from failure by reading status code and output?

---

## Existing Subagents Reference

| Subagent | Role | Location | Status Code | Best For |
|---|---|---|---|---|
| **dev-implementer** | TDD implementation in isolated worktree. Writes code from spec. | `agents/dev-implementer/` | DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED | Building features from shared-dev-spec |
| **spec-reviewer** | Verify implementation matches shared-dev-spec requirements line-by-line. | `agents/spec-reviewer/` | DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED | Verifying spec compliance after dev-implementer |
| **code-quality-reviewer** | Audit code against 8-point quality framework (performance, security, observability, readability, maintainability, testability, modularity, robustness). | `agents/code-quality-reviewer/` | DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED | Reviewing code quality after spec compliance |
| **dreamer** | Inline conflict resolution and post-merge retrospective. Scores decisions, surfaces anti-patterns, recommends improvements. | `agents/dreamer/` | Summary + recommendations | Post-PR retrospective and decision review |

---

## Review Integration

Subagents that produce code go through a two-stage review:

1. **Spec compliance** (spec-reviewer) — Does the code match the shared-dev-spec?
2. **Code quality** (code-quality-reviewer) — Does the code meet the 8-point quality framework?

The conductor dispatches reviewers after a `DONE` or `DONE_WITH_CONCERNS` status from dev-implementer. Both reviewers are themselves subagents and follow the same status protocol.

**Dispatch sequence:**
1. Conductor dispatches dev-implementer → returns DONE / DONE_WITH_CONCERNS
2. If DONE or DONE_WITH_CONCERNS, conductor dispatches spec-reviewer in parallel
3. If spec-reviewer returns DONE, conductor dispatches code-quality-reviewer
4. If all return DONE, code is ready to merge
5. If any returns DONE_WITH_CONCERNS, parent reviews concerns and decides: merge or rework
6. If any returns NEEDS_CONTEXT or BLOCKED, escalate to conductor or human

---

## Creating a New Subagent

1. **Check for overlap**: Review Existing Subagents table. Does this role already exist?
2. **Create directory**: `agents/{subagent-name}/`
3. **Create AGENT.md**: Follow this template with all 8 sections (Role, When to Invoke, Inputs, Workflow, Output, Edge Cases, Examples, Status Codes)
4. **Include anti-patterns**: Ensure your subagent anatomy doesn't fall into the 5 anti-patterns listed in Part 3
5. **Document edge cases**: Include at least 3 edge cases with explicit actions
6. **Write realistic examples**: Include example inputs, workflow reasoning, and expected outputs for each status
7. **Add to glossary**: Update `forge-glossary` subagents table with entry for new subagent
8. **Review for readability**: Another engineer should be able to dispatch this subagent from AGENT.md alone, without asking questions
9. **If platform uses Antigravity**: Create symlink in `.agent/skills/`

---

## Cross-Reference: Superpowers

This skill pairs with **superpowers:subagent-driven-development** for executing complex tasks with specialized subagents. Use when:
- You have a complex multi-stage task (implementation → review → integration)
- Different stages need different expertise
- You want parallel execution and independent reasoning
- Parent session needs to route results and make decisions

**Related skills:**
- `superpowers:dispatching-parallel-agents` — Dispatch multiple subagents in parallel
- `superpowers:receiving-code-review` — Handle DONE_WITH_CONCERNS status and address feedback
- `forge-skill-anatomy` — Write new skills (similar to subagents but different scope)

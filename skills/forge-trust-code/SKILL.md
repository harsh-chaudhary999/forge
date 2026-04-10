---
name: forge-trust-code
description: HARD-GATE: Spec-reviewer reads actual code, doesn't trust implementer report. Verify every claim.
type: rigid
---
# Do Not Trust The Report

**Rule:** Spec-reviewer must read actual code (diffs, files). Never trust implementer's self-review.

## Anti-Pattern Preamble: Why Reviewers Trust Reports Over Code

| Rationalization | The Truth |
|---|---|
| "The commit message says it implements X, I'll trust that" | Commit messages are claims, not evidence. Read code to verify claims. |
| "Tests pass, so the requirements must be met" | Tests verify what was tested, not what was required. Spec may require Y; tests may only verify X. |
| "The implementer is experienced, I trust their judgment on spec compliance" | Trust is not verification. Experienced developers miss requirements all the time (spec ambiguity, forgotten edge cases). Verify anyway. |
| "The code looks clean and well-structured, the implementation must be correct" | Code quality is orthogonal to spec compliance. Beautiful code can violate requirements. Verify both. |
| "The PR review is already done, the code must be correct" | PR review verifies code quality, not spec compliance. Spec review is a separate gate. Do it. |
| "I understand the spec from the discussion, I don't need to read the code" | Understanding is not verification. Read actual code to see what was actually built. |
| "The staging environment works, the spec must be met" | Staging behavior is point-in-time. Verify code to ensure behavior is persistent, not accidental. |
| "No one filed a bug, so the implementation must be correct" | Absence of bug reports is not proof of correctness. You're testing early. Don't assume production feedback replaces review. |
| "I did a spot-check of key functions, that's sufficient" | Spot-checks miss edge cases, error handling, and integration points. Read all relevant code. |
| "The implementer said they checked the spec, so I don't need to" | Self-review is the weakest form of review. Verify independently. Always. |

## Detailed Workflow

### Prepare for Review
- **Input:** PR with implementation, spec (from council), and acceptance criteria
- **Action:** Gather review materials
  1. Read the locked spec (from council gate) — know what was promised
  2. Read acceptance criteria — understand "done"
  3. Identify spec surfaces touched (API, DB, cache, events, UI, mobile)
  4. List files changed in PR (diffs)
- **Output:** Review context prepared

### Spec-to-Code Mapping
- **For each requirement in spec:**
  1. Identify which file(s) implement it
  2. Open those files and read the code
  3. **Do NOT rely on:**
     - Commit messages ("implements X")
     - PR description ("adds Y")
     - Function names ("configureX" doesn't prove it's actually configured)
     - Test names ("testX passes" doesn't prove X is fully implemented)
  4. **Do rely on:**
     - Actual code execution (what does the code actually do?)
     - Data flow (where does data come from, where does it go?)
     - Error handling (what happens if something fails?)

### Deep Code Review (Line-by-Line)
For each requirement:

1. **Read the implementation code** (not tests, not comments)
   ```
   Example: Spec says "API must reject requests without auth header"
   Code review: Find the auth middleware. Read it. Does it actually
   check for the header? Does it reject if missing? Does it reject
   with correct HTTP status? Verify each detail.
   ```

2. **Verify data flow**
   ```
   Example: Spec says "User data is encrypted in DB"
   Code review: Find the DB write code. Is encryption applied
   before write? Find the read code. Is decryption applied after read?
   Verify both directions.
   ```

3. **Check error handling**
   ```
   Example: Spec says "If external API fails, retry with exponential backoff"
   Code review: Find the API call. Is there a try-catch? What's the
   catch block doing? Is it retrying? Is backoff implemented?
   Is retry count bounded? Verify all parts.
   ```

4. **Verify edge cases**
   ```
   Example: Spec says "Support users with 0, 1, or 100 groups"
   Code review: Find the group-handling code. Does it work with 0 groups?
   With 1? With 100? Are there array index assumptions? Off-by-one errors?
   Verify each edge case mentioned in spec.
   ```

5. **Check integration points**
   ```
   Example: Spec says "Cache is invalidated when data changes"
   Code review: Find all places data can change. Is cache invalidated
   in every path? Or just one? Verify complete coverage.
   ```

### Verify Against Acceptance Criteria
- **Input:** Acceptance criteria from spec + code
- **For each acceptance criterion:**
  1. Find the code that implements it
  2. Read that code
  3. Verify it actually does what the criterion says
  4. Identify test cases that verify it
  5. Read test code (do tests cover the criterion completely?)

- **Example:**
  - Criterion: "Users can export data in CSV format"
  - Code check: Find export function, verify CSV generation, verify file download
  - Test check: Find test that calls export, verify test assertions

### Document Gaps
**If code does NOT match spec:**

- **For each gap, document:**
  1. Spec requirement (exact quote)
  2. What code actually does (exact quote + line numbers)
  3. Why gap exists (misunderstanding? Known limitation? Bug?)
  4. Impact (does it break acceptance criteria?)

- **Output options:**
  - If gap is critical: REQUEST CHANGES (implementer must fix)
  - If gap is minor: COMMENT (request clarification or improvement)
  - If gap is acceptable (spec ambiguity): APPROVE with notes

### Verify Test Coverage
**Do NOT assume tests are correct. Verify test code.**

- **For each critical requirement:**
  1. Find corresponding test
  2. Read test code (what does it actually assert?)
  3. Verify assertion is correct (not a false positive)
  4. Verify test would fail if code was wrong

- **Red flag tests:**
  - Test always passes (no assertion, or assertion is always true)
  - Test only checks happy path (no error cases)
  - Test mocks or stubs the implementation (doesn't test real behavior)

### Final Verification
Before approving, complete checklist:

- [ ] All spec requirements mapped to code
- [ ] Code actually implements each requirement (verified by reading)
- [ ] All acceptance criteria met (verified by reading code + tests)
- [ ] Error handling present (and tested)
- [ ] Edge cases handled (per spec)
- [ ] Integration points complete (no missing calls)
- [ ] Data flow correct (input → processing → output)
- [ ] No assumptions or shortcuts taken
- [ ] Gaps documented (if any, implementer must address)
- [ ] Tests are real (not just passing by luck)

### Edge Cases & Fallback Paths

#### Case 1: Code Is Hard to Understand (Complex Logic, Unclear)
- **Symptom:** "I read the function 3 times and still don't understand what it does"
- **Do NOT:** Assume it's correct, ask implementer
- **Action:**
  1. Trace through code with a concrete example (input → step 1 → step 2 → output)
  2. If still unclear: add comment requests (code must be reviewable)
  3. Request: "Add comments explaining algorithm" or "Simplify this logic"
  4. Don't approve until you understand it

#### Case 2: Code Doesn't Match PR Description
- **Symptom:** PR says "adds feature X" but code does feature Y or has no feature at all
- **Do NOT:** Trust the description, verify the code
- **Action:**
  1. Read code (what does it actually do?)
  2. If code implements something different: request changes
  3. If code is incomplete: request changes
  4. Sync PR description with code, or revert

#### Case 3: Requirement Touches Multiple Files (Complex Implementation)
- **Symptom:** "Auth requirement is implemented across 5 files (middleware, handler, util, test, config)"
- **Do NOT:** Spot-check one or two files
- **Action:**
  1. Map requirement to all files it touches
  2. Read code in all 5 files
  3. Verify they work together correctly
  4. Test integration (not just individual file correctness)

#### Case 4: Spec Requirement Is Ambiguous
- **Symptom:** Spec says "validate user input" but doesn't say exactly what validation
- **Do NOT:** Assume implementer guessed correctly
- **Action:**
  1. Identify the ambiguity
  2. Read code (what validation was chosen?)
  3. Ask: "Is this validation sufficient?" (escalate if unsure)
  4. Or: "Spec should clarify this, please update"
  5. Document assumption in code review

#### Case 5: Test Passes but Code Looks Wrong
- **Symptom:** Function to add numbers: "function add(a, b) { return a + 1 }" — test passes
- **Do NOT:** Trust the test, investigate
- **Action:**
  1. Read test code (what is it actually testing?)
  2. If test is wrong: request test fix
  3. If code is wrong: request code fix
  4. Verify test actually exercises the code path you're reviewing

#### Case 6: Code Implements More Than Required (Gold-Plating)
- **Symptom:** Spec says "add basic search", code implements full-featured search with analytics
- **Do NOT:** Approve just because it's better
- **Action:**
  1. Verify required functionality is correct (basic search works)
  2. Flag extra code: "Out of scope, remove or file separate task"
  3. Extra scope can hide bugs (more code = more risk)
  4. Enforce scope boundaries

### Code Review Checklist

Before approving PR, verify:

- [ ] All spec requirements identified
- [ ] All requirements found in code (actual implementation, not comments)
- [ ] Code actually does what spec says (not what PR description says)
- [ ] Edge cases handled (per spec or acceptance criteria)
- [ ] Error handling present and correct
- [ ] Integration complete (no missing pieces)
- [ ] Data flow verified (input → output)
- [ ] Tests are real (not false positives)
- [ ] No assumptions or shortcuts
- [ ] Code is understandable (not opaque)
- [ ] No scope creep (only required features)
- [ ] Gaps documented (if any exist)

Output: **CODE VERIFIED** (spec met, implementation correct) or **SPEC GAPS FOUND** (implementer must fix before merge)

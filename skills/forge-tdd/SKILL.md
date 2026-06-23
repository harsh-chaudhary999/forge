---
name: forge-tdd
description: "WHEN: About to write any production code. HARD-GATE: Iron law - write test first, watch fail, write minimal code, watch pass. No exceptions."
type: rigid
version: 1.1.1
preamble-tier: 3
requires:
  - worktree-per-project-per-task
triggers:
  - "write test first"
  - "TDD"
  - "test-driven development"
  - "RED test before code"
allowed-tools:
  - Bash
  - Write
---

# Test-Driven Development (Iron Law)

**Prerequisite (HARD-GATE):** You must be executing inside an isolated git worktree created by `worktree-per-project-per-task`. Step 0 enforces this. No test is written before worktree existence is confirmed.

**HARD-GATE: Non-negotiable. No production code without failing test first.**

---

## Anti-Pattern Preamble: Why You Think TDD Is Optional (It Isn't)

| Rationalization | The Truth |
|---|---|
| "This is a simple feature, TDD feels slow" | Simplicity hides the hardest bugs. TDD catches them. Slow startup, faster debugging. Net win. |
| "I'll write tests after to save time" | You won't. Post-hoc tests miss 40% of edge cases TDD would have caught. Write first. |
| "The spec is clear enough, I don't need tests to clarify it" | No spec is ever clear enough. Test is the spec. Test forces you to think through edge cases. |
| "I can skip the test-run-fail step, I know it will fail" | NO. You MUST run it and see the failure. Seeing the failure teaches you what you're fixing. |
| "Our codebase doesn't do TDD, I'll follow convention" | YOU are disciplined. Convention doesn't override discipline. Do it. |
| "I'll test as I code (test-parallel) instead of test-first" | Wrong order. Test FIRST, then code. The order matters. Test-first catches what test-parallel misses. |
| "This code is internal/hidden, no one will use it, I'll skip TDD" | Internal code is harder to test and debug. TDD is MORE important, not less. |
| "I already know what tests to write, I'll code first" | You don't. Writing code first blinds you to edge cases. Test first clarifies. |
| "The test infrastructure is broken, I'll work around it" | STOP. Report BLOCKED. Don't workaround. Fix or escalate. |
| "I wrote a test that passes but it doesn't actually test anything" | Weak tests are worse than no tests. Test must verify behavior, not just syntax. |
| "RED tests only mirror the tech plan, not approved QA cases" | When **`qa/manual-test-cases.csv`** exists for the task, RED should **map to those atomic rows** (or explicitly document gaps). Otherwise TDD and **P4.4 semantic machine eval** drift from the acceptance inventory the team signed. |

---

## Step 0 — Worktree Pre-Check (HARD-GATE)

**Before writing a single test line, verify you are executing inside an isolated git worktree.**

```bash
# Verify current directory is a worktree (not main working tree)
git rev-parse --show-toplevel && git worktree list | grep "$(git rev-parse --show-toplevel)"
```

Expected output: the current path appears in `git worktree list` with a branch name matching the task (e.g., `task/<task-id>`).

**If the check fails (current dir is main, or no task branch exists):**

1. STOP — do not write any test.
2. Invoke `worktree-per-project-per-task` to create a fresh isolated worktree for this task.
3. `cd` into the new worktree path.
4. Re-start forge-tdd from Step 0 inside the worktree.

**HARD-GATE: No test file is created, no `git add` is run, and no RED phase begins until `git worktree list` shows the current path on a task-specific branch.**

---

## Step 1: Read Code Style Before Writing Any Test

Before writing the first test, read the project's coding conventions:

```bash
cat ~/forge/brain/products/<slug>/codebase/code-style.md
```

Match test code to these conventions: import style, async pattern (`async/await` vs `.then()`), assertion library (`expect` vs `assert`), test block naming (`describe/it` vs `test()`), error handling shape, and file naming.

**Fallback if `code-style.md` is absent (scan not yet run):** Open the 3 most recently modified source files in the repo and infer conventions from them:
```bash
git -C <repo-path> log --diff-filter=M --name-only -3 -- '*.ts' '*.py' '*.kt' '*.go' '*.java' | grep '\.'
```
Log: `[WARN] code-style.md absent — test style inferred from recent files`.

**HARD-GATE:** Do not write a single test line before completing this step. Mismatched test style causes P2 reviewer findings that delay merge.

## Iron Law

```
NO PRODUCTION CODE EXISTS BEFORE THE TEST.
```

If you write 1 line of code without a test first, you have failed.

---

## Red Flags — STOP

If you notice any of these, STOP and do not proceed:

- **Implementation code is written before a test file exists** — The Iron Law is violated. STOP. Delete the implementation, write the test first, watch it fail, then reimplement.
- **Test passes on first run without ever seeing it fail (RED step skipped)** — A test that never fails is a test that doesn't test anything. STOP. Verify the test actually fails when the implementation is removed.
- **Multiple tests are written at once before any implementation** — Multiple tests at once hide which test drives which implementation. STOP. Write one test, see it fail, implement, see it pass, then write the next.
- **RED only asserts registry / enum / opaque “id exists” for user-visible UI** — That passes while alternate delivery paths, stacks, and layout remain unsettled. STOP. Rewrite RED to assert **one observable behavior** under test doubles (e.g. when input X, rendered count / bound data / visible state), aligned with **`delivery_mechanism`** + **`implementation_stack`** (or legacy **`ui_implementation_stack`**) from `prd-locked.md` Q10 and approved QA rows when present.
- **Agent says "I'll write tests after" or "tests follow the implementation"** — Post-hoc tests cannot drive design. STOP. Tests must be written first, always.
- **Refactoring adds new behavior** — Refactor is for clarity, not features. STOP. If the refactor adds functionality, extract that as a new RED-GREEN cycle.
- **Test infrastructure is broken and agent proceeds without tests** — Working without tests is not a valid workaround. STOP. Report BLOCKED. Do not write production code in a broken test environment.

---

## The RED-GREEN-REFACTOR Cycle

### RED — Write Test, Watch It Fail

1. **Write a test** that describes the desired behavior
   - Test is minimal and focused on the specific task
   - Test should fail with current code
   - Use existing test patterns in the project
   
2. **Run the test**
   - MUST run and MUST see it fail
   - Failure message should be clear and sensible
   - If test doesn't fail → test is useless (rewrite it)
   - If test runs at all but crashes → infrastructure issue (escalate BLOCKED)

**Success Criterion:** Red test fails with clear, meaningful error.

### Test Matrix — Required Before Any GREEN Phase

Before writing any production code, you must have failing tests covering ALL four scenario types for every public function/method/endpoint being implemented. One test total is not acceptable.

| Scenario Type | Required count | What it tests |
|---|---|---|
| **Happy path** | 1+ per public function | Normal input → expected output |
| **Edge case** | 2+ per public function | At minimum: one null/empty/zero input AND one boundary value (max length, min int, overflow, off-by-one). Also consider: concurrent call, permission denied (if access-controlled), malformed input, missing required field |
| **Error / failure** | 1+ per public function | Invalid input, dependency down, timeout, permission denied |
| **Integration** | 1+ per API endpoint or cross-service call | Full request → handler → DB/cache/queue → response round trip |

**HARD-GATE:** If your test file has fewer than 4 tests per public function (or fewer than 5 for any API endpoint), you have not completed the RED phase. Do not proceed to GREEN.

**Anti-patterns that trigger STOP:**
- `it('should work')` — not a scenario, not a test
- One happy-path test and nothing else — edge cases and errors ARE requirements
- "I'll add more tests after the feature works" — test matrix must be RED before any production code
- Integration tests as optional — if the function touches a DB, cache, queue, or external API, an integration test is mandatory
- Tests use `assert result is not None` / `expect(fn).toHaveBeenCalled()` as the primary assertion — existence and call-only checks are hollow. Assert the specific output contract.
- Test name is a single word or function name (`test_login`, `test_user`, `test_api`) — rewrite with behavior + condition pattern.

**Recommended test authoring order within RED:**
1. Happy path first — validates the API contract and makes the function's contract visible
2. Error / failure next — validates robustness before edge cases distract you
3. Edge cases last — validates completeness once happy path and errors are solid
4. Integration test — write after unit tests confirm the function's contract; integration confirms wiring

Writing edge cases first is a trap: you'll design the API around edge cases and miss the obvious happy path.

---

## Test Anatomy: Arrange-Act-Assert (MANDATORY STRUCTURE)

Every test MUST use Arrange-Act-Assert. Label each section with a comment. No exceptions.

```python
# Python example
def test_login_with_valid_credentials_returns_jwt_token():
    # --- Arrange ---
    mock_user_repo = Mock()
    mock_user_repo.find_by_email.return_value = User(
        id="user_1", email="test@example.com",
        password_hash=hash_password("correct_pass"), active=True
    )
    service = LoginService(user_repo=mock_user_repo, token_ttl=3600)

    # --- Act ---
    result = service.authenticate("test@example.com", "correct_pass")

    # --- Assert ---
    assert result.token is not None, "Valid credentials must yield a token"
    assert result.expires_in == 3600, f"Expected ttl=3600, got {result.expires_in}"
    assert result.user_id == "user_1", "Token must identify the authenticated user"
```

```typescript
// TypeScript example
it('should return 200 with JWT when credentials are valid', async () => {
    // --- Arrange ---
    jest.spyOn(userRepo, 'findByEmail').mockResolvedValue(
        mockUser({ email: 'test@example.com', passwordHash: hash('correct_pass') })
    );

    // --- Act ---
    const response = await request(app)
        .post('/api/auth/login')
        .send({ email: 'test@example.com', password: 'correct_pass' });

    // --- Assert ---
    expect(response.status).toBe(200);
    expect(response.body.token).toMatch(/^eyJ/);       // JWT format
    expect(response.body.expiresIn).toBe(3600);
    expect(response.body).not.toHaveProperty('passwordHash'); // no secret leak
});
```

**Rules:**
- Arrange: build ALL inputs, mocks, and fixtures BEFORE the act line. Zero setup after Act.
- Act: ONE line only. If you need two act lines, split into two tests.
- Assert: assert SPECIFIC values, NOT just existence. Every assert gets a failure message.

---

## Test Naming Convention (MANDATORY)

Test names must describe **behavior** and **condition**, not the function name.

| ❌ BAD (describes code) | ✅ GOOD (describes behavior) |
|---|---|
| `test_login()` | `test_login_with_valid_credentials_returns_jwt_token()` |
| `test_user_service()` | `test_create_user_when_email_already_exists_raises_duplicate_error()` |
| `test_api()` | `test_get_orders_when_user_has_no_orders_returns_empty_list()` |
| `it('works')` | `it('should display validation error when email field is empty on submit')` |
| `test_edge_case()` | `test_validate_email_rejects_string_without_at_symbol()` |

**Pattern:**
- Python/Go/Java: `test_<subject>_<condition>_<expected_outcome>`
- TypeScript/JS: `it('should <expected_outcome> when <condition>')`
- Kotlin: `` `when <condition>, <expected_outcome>` `` (backtick syntax)

**HARD-GATE:** A test named `test_login`, `test_user`, `test_api`, `test_edge`, or any single-word name is **NOT a valid test name** — rewrite it before committing.

---

## Assertion Quality Rules (MANDATORY)

Assertions must verify **specific observable behavior**, not just existence or invocation.

**Assertion quality ladder — only ✅ tiers are acceptable:**

| Tier | Example | Verdict |
|---|---|---|
| ❌ Existence | `assert result` / `assert result is not None` | Useless — passes for any truthy value |
| ❌ Call-only | `expect(fn).toHaveBeenCalled()` | Useless — doesn't verify arguments or outcome |
| ❌ Status only | `expect(response.status).toBe(200)` alone | Incomplete — body might be wrong |
| ✅ Specific value | `assert result.token.startswith('eyJ')` | Good — verifies content |
| ✅ Full contract | `assert result.token`, `assert result.expires_in == 3600`, `assert result.user_id == user.id` | Best — covers the full output contract |

**Rules:**
1. **Assert the output contract, not the code path.** Never assert that a private method was called — assert what the caller observes.
2. **Every assert gets a failure message.** `assert x == y, f"Expected {y}, got {x}"` / `expect(x).toBe(y)` (Jest messages are built in).
3. **Error tests must assert the error code/message**, not just that an exception was raised. `pytest.raises(AuthError) as exc; assert exc.value.code == 'INVALID_CREDENTIALS'`
4. **State-change tests must assert the new state**, not just that a method was called. If `update_user` is called, assert `user.updated_at` changed and `user.name == new_name`.
5. **Negative assertions are required for security.** If login fails, assert the response body does NOT contain a token. If user is unauthorized, assert the response does NOT contain the resource.

---

## Reference (load on demand)

Deep detail — worked examples, detailed section breakdowns, edge-case deep-dives, templates,
and decision trees — lives in **`reference/tdd-reference.md`** (Agent Skills progressive disclosure). This
SKILL.md is the operational contract: discipline, core workflow/decision logic, and checklists.

## Iron Law Enforcement

This skill is RIGID: type=rigid. Do not bend it.

- If you're tempted to skip the test → invoke this skill
- If you're tempted to code first → invoke this skill
- If you're tempted to skip seeing the test fail → invoke this skill
- If you're tempted to refactor outside your task → invoke this skill

TDD is the foundation. Every other discipline depends on it.

---

Note: This version includes edge cases and decision tree for complex testing scenarios (slow tests, flaky tests, infrastructure dependencies, legacy code, integration vs. unit testing).

## Post-Implementation Checklist

- [ ] Every test was run and confirmed FAIL before any implementation code was written.
- [ ] Test names follow `test_<subject>_<condition>_<expected_outcome>` pattern (no single-word names).
- [ ] Each test has labeled AAA sections (# Arrange / # Act / # Assert).
- [ ] Assertions are specific-value or full-contract (not existence-only or call-only mock).
- [ ] No hollow test anti-patterns present: no 2+2=4, no tautology, no missing negative path.

### Next Step After TDD

After all tests pass (GREEN phase complete and REFACTOR done):

1. Run the full test suite one final time to confirm no regressions.
2. **Invoke `forge-verification`** — TDD proves unit/integration correctness; `forge-verification` confirms the integrated system behaves correctly end-to-end before the task is marked ready for review.
3. Do not raise a PR or mark the task complete without `forge-verification` passing.

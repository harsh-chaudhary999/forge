# Surface-specific test patterns, edge-case escalation & decision tree — reference for `forge-tdd`

> Progressive-disclosure Level 3 (loaded on demand). Deep detail relocated from the SKILL.md: worked examples, detailed breakdowns, edge-case deep-dives, decision trees, templates.

## Surface-Specific Test Patterns

### Backend Service / Business Logic (Python)

```python
class TestOrderService:
    def test_place_order_with_valid_items_creates_order_and_returns_order_id(self):
        # --- Arrange ---
        mock_inventory = Mock()
        mock_inventory.check_availability.return_value = True
        mock_order_repo = Mock()
        mock_order_repo.save.return_value = Order(id="ord_123", status="PENDING")
        service = OrderService(inventory=mock_inventory, order_repo=mock_order_repo)

        # --- Act ---
        result = service.place_order(user_id="u1", items=[{"sku": "A1", "qty": 2}])

        # --- Assert ---
        assert result.order_id == "ord_123", f"Expected ord_123, got {result.order_id}"
        assert result.status == "PENDING", f"New order must be PENDING, got {result.status}"
        mock_order_repo.save.assert_called_once()  # side effect verified AFTER output

    def test_place_order_when_item_out_of_stock_raises_out_of_stock_error(self):
        # --- Arrange ---
        mock_inventory = Mock()
        mock_inventory.check_availability.return_value = False
        service = OrderService(inventory=mock_inventory, order_repo=Mock())

        # --- Act / Assert ---
        with pytest.raises(OutOfStockError) as exc:
            service.place_order(user_id="u1", items=[{"sku": "A1", "qty": 2}])
        assert exc.value.sku == "A1", f"Error must name the out-of-stock SKU"
        assert exc.value.code == "OUT_OF_STOCK"
```

### REST API Endpoint (Node.js / Express + Supertest)

```typescript
describe('POST /api/orders', () => {
    it('should return 201 with order id when items are in stock', async () => {
        // --- Arrange ---
        jest.spyOn(inventoryService, 'checkAvailability').mockResolvedValue(true);
        jest.spyOn(orderRepo, 'save').mockResolvedValue({ id: 'ord_123', status: 'PENDING' });

        // --- Act ---
        const response = await request(app)
            .post('/api/orders')
            .set('Authorization', `Bearer ${validToken}`)
            .send({ items: [{ sku: 'A1', qty: 2 }] });

        // --- Assert ---
        expect(response.status).toBe(201);
        expect(response.body.orderId).toBe('ord_123');
        expect(response.body.status).toBe('PENDING');
        expect(response.headers['location']).toContain('/api/orders/ord_123');
    });

    it('should return 409 with OUT_OF_STOCK when item unavailable', async () => {
        // --- Arrange ---
        jest.spyOn(inventoryService, 'checkAvailability').mockResolvedValue(false);

        // --- Act ---
        const response = await request(app)
            .post('/api/orders')
            .set('Authorization', `Bearer ${validToken}`)
            .send({ items: [{ sku: 'A1', qty: 2 }] });

        // --- Assert ---
        expect(response.status).toBe(409);
        expect(response.body.error).toBe('OUT_OF_STOCK');
        expect(response.body.sku).toBe('A1');
        expect(response.body).not.toHaveProperty('orderId'); // no partial order on failure
    });

    it('should return 401 when Authorization header is missing', async () => {
        const response = await request(app).post('/api/orders').send({ items: [] });
        expect(response.status).toBe(401);
        expect(response.body.error).toBe('UNAUTHORIZED');
    });
});
```

### React Component (RTL + userEvent)

```typescript
describe('OrderForm', () => {
    it('should show quantity error when qty exceeds max stock', async () => {
        // --- Arrange ---
        render(<OrderForm maxStock={5} onSubmit={jest.fn()} />);

        // --- Act ---
        await userEvent.type(screen.getByLabelText(/quantity/i), '10');
        await userEvent.click(screen.getByRole('button', { name: /place order/i }));

        // --- Assert ---
        expect(screen.getByRole('alert')).toHaveTextContent('Maximum quantity is 5');
        expect(screen.queryByText(/order placed/i)).not.toBeInTheDocument();
    });

    it('should call onSubmit with sku and qty when form is valid', async () => {
        // --- Arrange ---
        const onSubmit = jest.fn().mockResolvedValue({ orderId: 'ord_123' });
        render(<OrderForm maxStock={10} onSubmit={onSubmit} />);

        // --- Act ---
        await userEvent.type(screen.getByLabelText(/sku/i), 'A1');
        await userEvent.type(screen.getByLabelText(/quantity/i), '3');
        await userEvent.click(screen.getByRole('button', { name: /place order/i }));

        // --- Assert ---
        expect(onSubmit).toHaveBeenCalledWith({ sku: 'A1', qty: 3 });
        await screen.findByText(/order placed/i); // async confirmation visible
    });
});
```

### Android / Kotlin (JUnit + MockK + ViewModel)

```kotlin
class OrderViewModelTest {
    @Test
    fun `when valid items submitted, emits Success state with order id`() {
        // --- Arrange ---
        val orderRepo = mockk<OrderRepository>()
        coEvery { orderRepo.placeOrder(any()) } returns Result.Success(Order(id = "ord_123", status = "PENDING"))
        val viewModel = OrderViewModel(orderRepo)

        // --- Act ---
        viewModel.placeOrder(items = listOf(OrderItem(sku = "A1", qty = 2)))

        // --- Assert ---
        val state = viewModel.uiState.value
        assertIs<OrderUiState.Success>(state)
        assertEquals("ord_123", state.orderId)
        assertEquals("PENDING", state.status)
    }

    @Test
    fun `when item is out of stock, emits Error state with OUT_OF_STOCK code`() {
        // --- Arrange ---
        val orderRepo = mockk<OrderRepository>()
        coEvery { orderRepo.placeOrder(any()) } returns Result.Error(OutOfStockException("A1"))
        val viewModel = OrderViewModel(orderRepo)

        // --- Act ---
        viewModel.placeOrder(items = listOf(OrderItem(sku = "A1", qty = 2)))

        // --- Assert ---
        val state = viewModel.uiState.value
        assertIs<OrderUiState.Error>(state)
        assertEquals("OUT_OF_STOCK", state.code)
        assertEquals("A1", state.sku)
    }
}
```

---

## Mocking Contract

**Mock at system boundaries only. Do NOT mock your own business logic.**

| ✅ Mock these (system boundaries) | ❌ Never mock these (your own code) |
|---|---|
| Database / ORM queries | Service classes you wrote |
| HTTP clients (external APIs) | Value objects / DTOs |
| File system reads/writes | Pure functions |
| Message queue producers/consumers | Enum lookups |
| Clock / `datetime.now()` / `Date.now()` | In-memory data structures |
| Third-party SDKs (payment, auth, SMS) | Constants |
| Email / push notification services | Business rule validators |

**Mocking strategy by test type:**
- **Unit test**: mock ALL system boundaries; test one class/function in isolation
- **Integration test**: use real DB (test DB / in-memory), mock only external HTTP and third-party SDKs
- **E2E / eval test**: no mocks — real services, real DB, real network

**Mock verification rule:** Always verify mock calls WITH arguments, not just that they were called:
```python
# ❌ Wrong — verifies nothing
mock_email.send.assert_called()

# ✅ Right — verifies the contract
mock_email.send.assert_called_once_with(
    to="user@example.com",
    subject="Order Confirmation",
    template="order-confirm",
    context={"order_id": "ord_123"}
)
```

---

## Hollow Test Anti-Patterns — HARD-GATE STOP

These tests technically pass the matrix count but provide zero coverage. **Any test matching these patterns must be rewritten before committing.**

| Pattern | Example | Why it fails | Rewrite target |
|---|---|---|---|
| **Trivial equality** | `assert add(2, 2) == 4` | Only tests the obvious; catches nothing real | Test boundary: `add(MAX_INT, 1)` → overflow behavior |
| **Existence only** | `assert result is not None` | Passes for any truthy output | Assert specific fields: `assert result.order_id.startswith('ord_')` |
| **Call-only mock** | `expect(fn).toHaveBeenCalled()` | Doesn't verify arguments or return value | `expect(fn).toHaveBeenCalledWith(expectedArgs)` |
| **Status-only HTTP** | `expect(res.status).toBe(200)` alone | Body could be empty or wrong | Add body assertions: `expect(res.body.data).toEqual(expectedData)` |
| **Tautology** | `assert user.name == user.name` | Always true | `assert user.name == 'Alice'` (fixed expected value) |
| **No negative path** | Only happy path tests for auth | Auth bugs live in the failure paths | Add: wrong password → 401, missing token → 401, expired token → 401 |
| **Stub behavior only** | Test only verifies mock was set up correctly | Tests the mock, not the real code | Remove mock setup for the function under test; verify the actual output |

### CSV / semantic trace markers (machine verification)

When **`qa/manual-test-cases.csv`** exists for the task, tie each RED test to an acceptance **Id** and/or a **`qa/semantic-automation.csv`** step **Id** using a comment the verifier scans:

```python
def test_valid_login_succeeds(self):
    # forge-tdd: TC-001 (manual-test-cases.csv)
    # forge-tdd: step-login (semantic-automation.csv)
    ...
```

- Use the exact **Id** values from those CSVs (first token after `# forge-tdd:`). Parenthetical hints are optional.
- Optional **`Required`** column on the manual CSV (`yes` / `true` / `1` / `y`) means **at least one** scanned test must include `# forge-tdd: <that Id>`.
- Tests are discovered under **`~/forge/brain/prds/<task-id>/`**: all **`test_*.py`** and **`*_test.py`**, or only paths/globs listed in **`qa/tdd-scan-paths.txt`** (one entry per line, relative to the task dir).
- **`python3 tools/verify/verify_forge_task.py --verify-tdd-csv-trace`** fails the build when markers reference unknown ids or required rows lack markers.
- **`forge_drift_check.py`** adds these `# forge-tdd:` lines to the success-criteria haystack by default (use **`--skip-tdd-marker-hay`** to omit them).

### GREEN — Write Minimal Code, Watch It Pass

1. **Write minimal code** to make test pass
   - Minimal means: no extra features, no "future-proofing", no refactoring yet
   - YAGNI: You Aren't Gonna Need It
   - If you wrote code thinking "this might be useful later", DELETE it
   
2. **Run the test**
   - MUST run and MUST see it pass
   - If test still fails → adjust code (iterate)
   - If different test fails now → investigate (you may have broken something)

**Success Criterion:** Test passes. Only minimal code added.

### REFACTOR — Improve Code While Tests Still Pass

1. **Refactor the implementation** (not the test)
   - Extract duplicated logic
   - Rename for clarity
   - Restructure for maintainability
   - Clean up comments and formatting
   
2. **Run tests again**
   - All tests must still pass
   - If any test fails → undo refactor (your refactor broke something)
   - Never refactor beyond the task scope

3. **Stop refactoring**
   - Refactor is NOT an excuse to redesign the whole system
   - Refactor is NOT an excuse to optimize prematurely
   - Refactor ONLY if: it makes code clearer/simpler (YAGNI still applies)

**Success Criterion:** Tests still pass, code is cleaner, scope unchanged.

---

## Detailed Workflow

### Step 1: Understand the Task
- Read the task text completely
- If unclear → ask questions (don't guess)
- Understand: what behavior should exist? What does "done" look like?

### Step 2: Find or Write the Test
- Look for existing test files
- Identify the test pattern used in the project
- Write ONE test for this task
- Test should be small enough to understand in 30 seconds
- Test should verify exactly the behavior you're implementing

**Example:**
```python
# TASK: Add method to validate email format
# BAD TEST: Tests that function exists and returns something
def test_validate_email():
    assert email_validator.validate_email("test@example.com") is not None

# GOOD TEST: Tests the specific behavior
def test_validate_email_accepts_valid_address():
    assert email_validator.validate_email("test@example.com") == True
    
def test_validate_email_rejects_invalid_address():
    assert email_validator.validate_email("invalid") == False
    
def test_validate_email_rejects_missing_at_symbol():
    assert email_validator.validate_email("testexample.com") == False
```

### Step 3: Run the Test (RED phase)
```bash
# Run your new test
$ npm test -- test_email_validator.js
# MUST see: Test FAILED / Red
```

Do not proceed until you see the test fail.

### Step 4: Write Code to Pass the Test (GREEN phase)
- Write only what's needed
- Follow existing code style
- No extra features
- No premature optimization

```python
# MINIMAL implementation
def validate_email(email: str) -> bool:
    return "@" in email and "." in email.split("@")[1]
```

### Step 5: Run the Test Again (verify GREEN)
```bash
$ npm test -- test_email_validator.js
# MUST see: Test PASSED / Green
```

Do not proceed until the test passes.

### Step 6: Run All Tests
```bash
$ npm test  # All tests, not just the new one
# MUST see: All tests still pass
```

If existing tests now fail, you broke something. Fix it before proceeding.

### Step 7: Refactor (if needed)
Only after tests pass:
- Is the code clear?
- Are there duplicated patterns?
- Can variable names be better?
- Can the logic be simpler?

If yes → refactor. Then re-run all tests to verify.

### Step 8: Done
- New test passes ✅
- All existing tests pass ✅
- Code is minimal ✅
- Code is clear ✅

---

## Edge Cases & Escalation

### What if I'm not sure how to write a test?
Read existing tests in the project. Copy the pattern. Ask for clarification if needed.

### What if the test infrastructure is broken?
Report `BLOCKED: Test infrastructure broken [details]`. Do not attempt workarounds. Escalate.

### What if the task is "add logging" or "update documentation"?
These are typically not TDD-able. But: if possible, write a test that verifies the logging/docs exist and are correct. If not possible, report `NEEDS_CONTEXT: Task not TDD-compatible [reason]`.

### What if the test takes longer than the code?
That's normal and correct. Complex behavior requires complex tests. Tests are not overhead; they're part of the implementation.

### What if I don't know what the behavior should be?
Stop. Report `NEEDS_CONTEXT: Unclear acceptance criteria [details]`. Don't guess.

### What if multiple tests fail now?
You probably wrote too much code. Roll back. Write LESS code. Make the first test pass. Then write the next test.

### What if I finish the task but want to refactor the whole file?
Don't. Refactor ONLY the code you touched. Out-of-scope refactoring is not part of the task.

### What if the project doesn't have tests?
Create a test file. Use standard test framework for the language. Start with one test. But: if test infrastructure is fundamentally broken, report `BLOCKED`.

---

## Success Criteria

✅ **PASS:**
- Test written before any code
- Test fails when run (RED phase observed)
- Test matrix complete: happy path + edge case + error + integration (where applicable) all RED before any production code
- Minimal code written to pass test
- Test passes when run (GREEN phase observed)
- All existing tests still pass
- Code is refactored for clarity (if needed)
- Task behavior is correct

❌ **BLOCKED:**
- Test infrastructure broken/missing
- Task is not TDD-compatible
- Acceptance criteria unclear

---

## Verification

Before claiming task is done, verify:

```bash
# 1. New test exists
$ grep -r "def test_" <test_file>  # New test present?

# 2. Test passes
$ npm test -- <test_file>  # All tests in file pass?

# 3. All tests pass
$ npm test  # No regressions?

# 4. Code is minimal
$ git diff <file>  # Only necessary changes? No extra features?

# 5. Code is clear
# Read the code. Is it obvious what it does?
```

If all 5 pass → done. Otherwise → iterate.

---

## Edge Cases & Escalation Paths

### Edge Case 1: Test Is Too Slow (10+ Seconds Per Run, Blocks Development)
**Situation:** Test is valid and correct, but takes 15+ seconds to run. Each RED-GREEN cycle takes minutes instead of seconds.

**Example:** Database integration test that creates 1000 records and validates queries. Valid test, but too slow for fast feedback loop.

**Do NOT:** Skip the test or reduce test scope because it's slow. Slow tests catch real issues.

**Action:**
1. Run test once to verify it works (see GREEN)
2. Identify bottleneck (where does time go?)
   - Database setup/teardown?
   - Large data set creation?
   - Network calls?
3. Options:
   - **Option A (Preferred):** Refactor test to be faster without losing coverage
     - Use fixtures instead of creating data
     - Mock external services
     - Reduce data set size (still tests behavior)
   - **Option B:** Split into two tests
     - Unit test (fast, < 100ms)
     - Integration test (slow, but run less frequently)
4. If cannot optimize: escalate as **NEEDS_CONTEXT** (test infrastructure too slow)
5. Do NOT reduce verification rigor to gain speed

---

### Edge Case 2: Test Is Flaky (Fails 20% of Time Unpredictably)
**Situation:** Test passes sometimes, fails sometimes. No clear pattern (timing, state, environment).

**Example:** Test that polls for eventual consistency; sometimes data appears in 10ms, sometimes 500ms. Test has hard-coded 50ms wait.

**Do NOT:** Accept flakiness or increase timeouts. Flakiness is a real bug in code or test.

**Action:**
1. Run test 10 times in succession; note pass/fail pattern
2. Classify flakiness type:
   - **Timing-dependent:** Add explicit waits, remove hard-coded delays
   - **Order-dependent:** Tests run in different order; state leaks between tests
   - **Concurrency:** Race condition in code or test
   - **Environment:** Infrastructure variability (network, database)
3. Fix root cause (not the test, the code):
   - Code: add synchronization, remove race condition
   - Test: add proper setup/teardown, isolate tests
4. Re-run test 10 times again; must pass all 10
5. If cannot stabilize: escalate as **BLOCKED** (flaky infrastructure or untestable code)

---

### Edge Case 3: Test Requires Infrastructure Not Available (Database, API Service)
**Situation:** Test is valid, but requires external service that's not running or accessible.

**Example:** Test for payment gateway integration requires live API connection. API service is down.

**Do NOT:** Skip the test or mock the service permanently. Integration tests must eventually test real integration.

**Action:**
1. Determine: is the service _always_ required or only for this test?
   - Always: you need the infrastructure restored before proceeding
   - Only this test: can you mock it temporarily?
2. If service can be restored (local database, stub server):
   - Restore/start the service
   - Re-run test
3. If service cannot be restored (external API, vendor service):
   - **Option A:** Mock the service for now, add comment "TODO: verify with real API"
   - **Option B:** Escalate as **NEEDS_CONTEXT** (cannot run full integration test)
   - **Option C:** Split test into unit (mocked) + integration (real API, run later)
4. Document the dependency in code comments
5. If mocking: create follow-up task to remove mock and verify against real service

---

### Edge Case 4: Legacy Code Path Has No Way to Unit Test (Tightly Coupled)
**Situation:** Code to test is tightly coupled to global state, static calls, or framework internals. Cannot unit test without refactoring code itself.

**Example:** Class that calls `Database.getInstance().query()` globally; Database is a singleton with no way to inject a test double.

**Do NOT:** Skip TDD or write test after code. Tight coupling is the problem.

**Action:**
1. Acknowledge: this code cannot be unit tested in current form
2. Refactor first (extract dependency, inject it):
   ```
   // BEFORE: tightly coupled
   class UserRepository {
       def getUser(id) { Database.getInstance().query(...) }
   }
   
   // AFTER: injectable
   class UserRepository {
       constructor(database) { this.db = database }
       def getUser(id) { this.db.query(...) }
   }
   ```
3. Then follow normal TDD: test first, code second
4. If refactoring is not possible (framework limitation):
   - Escalate as **NEEDS_CONTEXT** (code untestable, needs architecture change)
   - Mark code as "legacy, cannot unit test"
   - Use integration tests instead
5. Going forward: enforce testable design (dependency injection, loose coupling)

---

### Edge Case 5: Integration Test Required > Unit Test (Distributed System Testing)
**Situation:** Behavior cannot be verified with unit test alone. Service boundary requires integration test (multiple services, eventual consistency, network behavior).

**Example:** Feature: "Cache invalidated when user data changes". Requires backend write → cache invalidation → frontend read. One service cannot test alone.

**Do NOT:** Force a unit test for inherently distributed behavior. Integration tests are valid TDD.

**Action:**
1. Recognize: this is an integration test, not a unit test
2. Follow TDD at integration level:
   - RED: write integration test (bring up services, exercise end-to-end flow, verify cache behavior)
   - GREEN: implement feature
   - REFACTOR: optimize services without breaking integration test
3. May be slower than unit test (that's expected)
4. Integration test still drives design (discover contracts, dependencies)
5. Run integration tests less frequently (as gate, not per-commit), but still TDD
6. Do NOT skip the test because "it's just integration"

---

## Decision Tree: When to Unit Test vs. Integration Test

**Use this tree to decide which test to write first:**

```
START: I need to test behavior X

Q1: Does X require multiple services/processes?
├─ YES → Q2
└─ NO → UNIT TEST (test single component in isolation)

Q2: Does X depend on eventual consistency, timing, or network?
├─ YES → INTEGRATION TEST (test end-to-end, multiple services)
└─ NO → Could be unit test with mocks (see Q3)

Q3: Is the external service/boundary testable in isolation?
├─ NO → INTEGRATION TEST (no way around it)
├─ YES, easy to mock → UNIT TEST (mock the boundary)
└─ YES, but mocking loses important behavior → INTEGRATION TEST (test real behavior)

Q4: Is the integration test too slow (>5 sec)?
├─ YES → Split: UNIT TEST (fast path) + INTEGRATION TEST (slow path, run separately)
└─ NO → Single INTEGRATION TEST suffices

DECISION RULE:
- Unit test for single component logic (validation, calculation, formatting)
- Integration test for multi-component behavior (contracts, APIs, eventual consistency)
- Always write test first (RED), regardless of type
- Fast feedback: prefer unit tests for development
- Final verification: integration tests before merge
```

---

Output: **TDD PASS** (test first, minimal code, all tests pass — log `[P4.0-TDD-RED] task_id=<id> repo=<repo> test_files=<list> red_confirmed=yes` to `conductor.log` after RED phase is confirmed) or **BLOCKED** (test infrastructure broken, untestable legacy code, infrastructure unavailable after attempts to restore)

TDD is not about writing tests. It's about:
1. **Clarifying requirements** — Test forces you to think through edge cases before coding
2. **Preventing bugs** — Test catches bugs at write time, not debug time
3. **Enabling refactoring** — Tests let you refactor safely
4. **Documenting behavior** — Test is the executable spec
5. **Reducing rework** — Upfront clarity saves debugging time later

TDD feels slow at first. After the RED phase (writing the test), you're 60% done. The code is the easy 40%.

---


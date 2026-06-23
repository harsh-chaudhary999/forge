# Code-Quality Review Criteria (Sections 2–5)

Reference-grade FAIL/PASS catalogs for the four code-quality review dimensions. The SKILL.md spine names the dimension and its top-level checks; the full per-item FAIL/PASS examples live here. Mark each item ✅ (pass) or ❌ (fail) with evidence per `## Review Process` → Step 2.

## 2. Code Completeness

**Checklist:**
- [ ] **No "..." or "elided" code**
  - All code blocks are complete implementations
  - No "// ... rest of code" or "// ... other fields"
  - Example FAIL: `const obj = { foo: 1, ... };`
  - Example PASS: `const obj = { foo: 1, bar: 2, baz: 3 };`

- [ ] **No TODO or TODO(future) markers**
  - All code is ready to execute now
  - No "// TODO: implement validation" in code samples
  - Example FAIL: `// TODO: add error handling`
  - Example PASS: `if (!value) throw new Error("value required");`

- [ ] **No unresolved imports**
  - Every `import { X } from "module"` has X defined before use
  - No imports of functions that don't exist in the module
  - Example FAIL: `import { validateEmail } from "./helpers";` (if helpers.js doesn't export validateEmail)
  - Example PASS: `import { validateEmail } from "./helpers";` (helpers.js exports validateEmail)

- [ ] **All variables declared before use**
  - No forward references in code
  - All dependencies are defined in scope
  - Example FAIL: `return calculateTotal(items);` (calculateTotal not defined above)
  - Example PASS: `function calculateTotal(items) { ... } return calculateTotal(items);`

## 3. No Placeholder Code

**Checklist:**
- [ ] **Validation logic is complete, not stubbed**
  - Not: "add validation logic"
  - Is: Complete validation code with specific checks
  - Example FAIL: `// validate email address`
  - Example PASS: `const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/; if (!emailRegex.test(email)) throw new Error("Invalid email");`

- [ ] **Database queries are exact, not sketchy**
  - Not: "fetch from DB"
  - Is: Complete SQL query with table name, columns, WHERE clause
  - Example FAIL: `// query the user table`
  - Example PASS: `SELECT id, email, created_at FROM users WHERE status = 'active' AND deleted_at IS NULL;`

- [ ] **API calls are concrete, not abstract**
  - Not: "call the payment service"
  - Is: Exact endpoint, method, headers, payload
  - Example FAIL: `// contact payment API to charge card`
  - Example PASS: `POST /v1/charges { amount: 5000, currency: "usd", source: token }`

- [ ] **Configuration values are explicit, not variables**
  - Not: "set timeout to appropriate value"
  - Is: Exact timeout in seconds/ms
  - Example FAIL: `setTimeout(() => { ... }, TIMEOUT);`
  - Example PASS: `setTimeout(() => { ... }, 5000);` (5 seconds explicit)

- [ ] **Error messages are specific, not generic**
  - Not: "handle errors gracefully"
  - Is: Specific error message and recovery strategy
  - Example FAIL: `catch (e) { console.log("error"); }`
  - Example PASS: `catch (e) { logger.error("Failed to fetch user details", { userId, error: e.message }); res.status(500).json({ error: "Internal server error" }); }`

## 4. Test & Commit

**Checklist:**
- [ ] **Each task has a runnable test command**
  - Test is executable in the environment (npm test, python -m pytest, etc.)
  - Test actually validates the requirement
  - Example FAIL: `Test: "verify it works"`
  - Example PASS: `Test: npm test -- --testNamePattern="validateEmail rejects invalid formats"`

- [ ] **Each task has a commit message**
  - Follows conventional commits (feat:, fix:, test:, etc.)
  - References the requirement or task description
  - Is actionable and specific
  - Example FAIL: `git commit -m "update code"`
  - Example PASS: `git commit -m "feat: add email validation with regex pattern"`

- [ ] **Commit messages follow your project convention**
  - Check recent commits for style (git log --oneline)
  - Example: If repo uses "feat(auth): ...", replicate that format
  - Example FAIL: `chore: misc updates`
  - Example PASS: `feat(auth): add 2FA token caching with 300s TTL`

## 5. Output Format

**Checklist:**
- [ ] **Expected output is described for each test**
  - Exit code (0 = success, non-zero = failure)
  - stdout content (exact text or pattern)
  - File changes (which files created/modified, content)
  - Example:
    ```
    Test passes with:
    - Exit code: 0
    - stdout: "All tests passed: 12 passed, 0 failed"
    - Files created: src/validators/email.test.js
    ```

- [ ] **Failure modes are documented**
  - If test fails, what's the likely cause?
  - How does the error message guide troubleshooting?
  - Example:
    ```
    If test fails:
    - "validateEmail is not defined" → Function not exported from helpers.js
    - "regex pattern mismatch" → Email pattern needs update
    ```

- [ ] **Performance expectations are explicit**
  - If there's a performance requirement, test must measure it
  - Not: "ensure it's fast"
  - Is: "response time < 100ms" (measured in test)
  - Example:
    ```
    Test validates performance:
    - Query execution: < 50ms
    - API response: < 200ms p95
    ```

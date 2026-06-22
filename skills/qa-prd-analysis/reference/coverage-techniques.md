# qa-prd-analysis — Coverage techniques & maps

## Step 4 — Test design techniques (completeness)

Build a full matrix: `Feature Areas × Test Types × Surfaces × User Roles × States × Input Partitions`.

| Technique | When to apply |
|---|---|
| **Equivalence Partitioning** | Any input field — group valid and invalid classes |
| **Boundary Value Analysis** | Any numeric, string-length, or date input — test min, max, min−1, max+1 |
| **Decision Table** | Business rules with multiple conditions (e.g. role=admin AND status=active) |
| **State Transition** | Any entity with a state machine (order status, user status, payment state) |
| **Pairwise / Combinatorial** | Multiple independent inputs — use pairwise to cover interactions without factorial explosion |
| **Error Guessing** | Known failure patterns from production, similar features, OWASP |
| **Use Case Testing** | All alternate and exception flows in every use case, not just main flow |

**Minimum scenario expectations per feature area (enforce, do not reduce — these are floors):**

| Feature complexity | Minimum scenarios |
|---|---|
| Simple CRUD (1 entity, 2-3 fields) | 25–40 |
| Medium (multi-field form, validation, roles) | 50–80 |
| Complex (multi-step flow, payment, auth) | 100–150 |
| Cross-surface end-to-end | +20–30 per surface added |

## Step 6 — Coverage map by test type (example)

For each confirmed test type from Q1, write an explicit coverage plan (complete this
for every feature area before calling the skill done):

```markdown
### Smoke Coverage
- SC-AUTH-SMOKE-001: Login success → dashboard loads
- SC-PAYMENT-SMOKE-001: Add to cart → checkout → order created

### Positive Coverage
- SC-AUTH-POS-001: Login with valid email + password
- SC-AUTH-POS-002: Login via Google OAuth
- SC-AUTH-POS-003: Login with "remember me" checked → session persists 30d
...

### Negative Coverage
- SC-AUTH-NEG-001: Login with wrong password → error message shown
- SC-AUTH-NEG-002: Login with unregistered email → error message shown
- SC-AUTH-NEG-003: Login with empty email → field validation
- SC-AUTH-NEG-004: Login with empty password → field validation
- SC-AUTH-NEG-005: Login with SQL injection in email field → rejected
...

### Boundary Coverage
- SC-AUTH-BVA-001: Password at minimum length (8 chars) → accepted
- SC-AUTH-BVA-002: Password at min−1 (7 chars) → rejected
- SC-AUTH-BVA-003: Password at maximum length (128 chars) → accepted
- SC-AUTH-BVA-004: Password at max+1 (129 chars) → truncated or rejected
- SC-AUTH-BVA-005: Email at maximum length (254 chars) → accepted
...

### Security Coverage
- SC-AUTH-SEC-001: SQL injection in email field
- SC-AUTH-SEC-002: XSS payload in email field
- SC-AUTH-SEC-003: Brute force 10 attempts → account locked
- SC-AUTH-SEC-004: Session token in URL → rejected
- SC-AUTH-SEC-005: Expired JWT → 401 returned
...

### Accessibility Coverage
- SC-AUTH-A11Y-001: Tab through login form → all fields reachable
- SC-AUTH-A11Y-002: Error message announced by screen reader
- SC-AUTH-A11Y-003: Submit button accessible via keyboard Enter
...
```

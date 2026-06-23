# Fault Diagnosis Output Template + Worked Examples

## Output Fault Diagnosis

Format the diagnosis clearly with these sections:

```yaml
fault_diagnosis:
  service: "<service-name>:<port>"
  status: "failed"
  
  error:
    type: "<exception-type or http-status>"
    message: "<error-message>"
    step: "<scenario-step-that-failed>"
    
  evidence:
    logs:
      - timestamp: "2026-04-10T14:32:15Z"
        level: "ERROR"
        message: "<log-line>"
        file: "<source-file>:<line>"
      
    stack_trace:
      - function: "<function-name>"
        file: "<filename>"
        line: <line-number>
        context: "<code-context>"
    
    request:
      method: "POST"
      url: "/endpoint"
      headers: { ... }
      body: { ... }
    
    response:
      status: 500
      headers: { ... }
      body: { ... }
    
    db_state:
      query: "<failed-query>"
      error: "<constraint-or-syntax-error>"
      affected_rows: <count>
      transaction_state: "rolled_back"
    
    cache_state:
      key: "<cache-key>"
      expected_value: "..."
      actual_value: "..."
      ttl_remaining: <seconds>
      was_hit: false
  
  actionable:
    root_cause: "<what-actually-broke>"
    immediate_fix: "<how-to-fix-now>"
    prevention: "<how-to-prevent-next-time>"
    affected_flows: ["<flow-1>", "<flow-2>"]
```

## Example Diagnoses

### Example 1: Backend API Fault
```yaml
fault_diagnosis:
  service: "backend-api:3000"
  status: "failed"
  
  error:
    type: "InternalServerError"
    message: "POST /auth/2fa/enable returned 500"
    step: "Enable 2FA on user account"
  
  evidence:
    logs:
      - timestamp: "2026-04-10T14:32:15Z"
        level: "ERROR"
        message: "Error: 2FA secret generation failed"
        file: "auth.js:123"
      - timestamp: "2026-04-10T14:32:15Z"
        level: "ERROR"
        message: "Cannot read property 'base32' of undefined"
        file: "auth.js:125"
    
    stack_trace:
      - function: "generateSecret"
        file: "auth.js"
        line: 123
        context: "const encoded = speakeasy.totp.base32Encode(secret)"
      - function: "enableTwoFactor"
        file: "auth.js"
        line: 156
    
    request:
      method: "POST"
      url: "/auth/2fa/enable"
      body: { phone: "+1234567890", method: "sms" }
    
    response:
      status: 500
      body: { error: "Internal Server Error" }
  
  actionable:
    root_cause: "speakeasy library not imported or undefined"
    immediate_fix: "Add: const speakeasy = require('speakeasy')"
    prevention: "Add unit tests for auth.js, check imports in CI"
    affected_flows: ["2FA setup", "login with 2FA"]
```

### Example 2: Database Fault
```yaml
fault_diagnosis:
  service: "mysql:3306"
  status: "failed"
  
  error:
    type: "ConstraintViolation"
    message: "Duplicate entry for user_id in profile table"
    step: "Update user profile after registration"
  
  evidence:
    logs:
      - timestamp: "2026-04-10T14:32:16Z"
        level: "ERROR"
        message: "Duplicate entry '12345' for key 'uk_user_id'"
    
    db_state:
      query: "INSERT INTO user_profile (user_id, name) VALUES (?, ?)"
      error: "ER_DUP_ENTRY: Duplicate entry '12345' for key 'uk_user_id'"
      affected_rows: 0
      transaction_state: "rolled_back"
  
  actionable:
    root_cause: "Unique constraint violation—profile already exists for user"
    immediate_fix: "Check if profile exists before INSERT, use UPSERT instead"
    prevention: "Add integration tests for duplicate profile scenarios"
    affected_flows: ["User registration", "Profile updates"]
```

### Example 3: Cache Fault
```yaml
fault_diagnosis:
  service: "redis:6379"
  status: "failed"
  
  error:
    type: "StaleDataError"
    message: "Cache verification failed—expected '{role:admin}' but got '{role:user}'"
    step: "Verify admin cache after role upgrade"
  
  evidence:
    cache_state:
      key: "user:12345:roles"
      expected_value: { role: "admin" }
      actual_value: { role: "user" }
      ttl_remaining: 3599
      was_hit: true
  
  actionable:
    root_cause: "Cache not invalidated when user role was updated"
    immediate_fix: "Add cache.delete('user:12345:roles') to role update handler"
    prevention: "Implement cache invalidation triggers on role changes"
    affected_flows: ["Permission checks", "Authorization"]
```

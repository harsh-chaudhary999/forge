# Common Debugging Patterns & Command Catalog

## Common Debugging Patterns

### Pattern 1: Missing Import/Export
```
Symptom: ReferenceError: X is not defined
Investigation: X exists in another file but not imported
Fix: Add import statement
```

### Pattern 2: Wrong Function Call
```
Symptom: TypeError: X.method is not a function
Investigation: X is wrong object or doesn't have method
Fix: Change X to correct object or method name
```

### Pattern 3: Missing Environment Variable
```
Symptom: TypeError: Cannot read property 'X' of undefined
Investigation: Config.X is undefined because env var not set
Fix: Add env var to .env or set in deployment
```

### Pattern 4: Broken Dependency
```
Symptom: Error during require/import
Investigation: Dependency version changed or module not installed
Fix: npm install or lock to correct version
```

### Pattern 5: Wrong Data Format
```
Symptom: Error in validation or processing
Investigation: Input data doesn't match expected schema
Fix: Transform data before processing or fix source
```

### Pattern 6: Service Not Running
```
Symptom: ECONNREFUSED on port X
Investigation: Database/cache/queue service not started
Fix: Start service or fix connection string
```

---

## Commands

### Investigate
```bash
# Read recent errors
tail -100 app.log | grep ERROR

# Get full stack trace
app.log | jq '.[] | select(.level=="error")' | jq '.stack' | head -50

# Find where function is defined
grep -r "function generateSecret" src/

# Check imports in failing file
grep "^import\|^require" src/routes/auth.ts
```

### Hypothesize
```bash
# Check git blame for recent changes
git blame src/routes/auth.ts | grep -A5 -B5 "line 145"

# See what was there before
git show HEAD~1:src/routes/auth.ts | sed -n '140,150p'

# Check if function exists elsewhere
grep -r "export.*generateSecret" src/
```

### Fix
```bash
# Make minimal change
# Verify syntax
npm run lint src/routes/auth.ts

# Don't commit yet
```

### Verify
```bash
# Run specific test
npm test -- auth.test.ts -t "POST /auth/2fa/enable"

# Run full test suite
npm test

# Check logs after running
tail -50 app.log
```

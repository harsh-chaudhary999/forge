---
name: tech-plan-write-per-project
description: Convert shared-dev-spec into per-project tech plans. Output: 1 plan per repo with bite-sized tasks (exact files, complete code, exact bash commands).
type: rigid
requires: [brain-read]
---

# tech-plan-write-per-project

## Anti-Pattern Preamble

| Rationalization | Why It Fails |
|---|---|
| "The implementer will figure out the details" | Vague tasks cause divergence. "Add the endpoint" is not a task — "Add POST /api/v1/orders to routes/orders.ts returning 201 with OrderResponse schema" is a task. |
| "I'll use pseudocode to keep the plan concise" | Pseudocode forces the implementer to make design decisions that should have been made in planning. Write complete code. |
| "This task is too small to write out" | If it takes 2 minutes to execute, it takes 30 seconds to write. Small tasks that are written out get done correctly. Small tasks left vague get done wrong. |
| "I'll group related changes into one big task" | Tasks over 5 minutes need splitting. Big tasks hide complexity and make progress tracking impossible. |
| "The bash commands are obvious" | "Obviously" wrong commands waste a self-heal loop iteration. Write the exact command including flags, paths, and environment variables. |
| "I'll reference the spec instead of repeating details" | The implementer (dev-implementer subagent) works in an isolated worktree with only the plan. Self-contained tasks prevent NEEDS_CONTEXT status. |

**If you are thinking any of the above, you are about to violate this skill.**

## Overview

This skill converts a locked shared-dev-spec into bite-sized, executable technical implementation plans per project. Each task is 2-5 minutes of execution with exact file paths, complete code (no placeholders), and exact bash commands.

---

## Section 1: Parse shared-dev-spec

### Input
- Locked spec location: `/home/lordvoldemort/Videos/forge/brain/prds/<task-id>/spec.md`
- Status: LOCKED (spec is immutable at this stage)

### Process
1. **Read the spec file** to understand:
   - Feature requirements (functional + non-functional)
   - Success criteria and acceptance tests
   - Affected projects (which repos need changes)
   - Contracts and interfaces (API shapes, schema changes, event formats)

2. **Extract per-project work items** by identifying:
   - Database migrations (schema changes)
   - API endpoints (routes, handlers, validation)
   - Data models and business logic
   - Frontend components and views
   - Integration points and dependencies

3. **Map to repositories** (standard Forge topology):
   - `shared-schemas/` — Shared TypeScript types, validation schemas, contracts
   - `backend-api/` — Node/Express REST API, database migrations, business logic
   - `web-dashboard/` — React SPA, UI components, state management
   - `app-mobile/` — React Native app, mobile UI, offline-first patterns

### Output
- Structured list of per-project tasks (raw)
- Dependency graph (which project depends on which)
- Identified contracts (API, schema, events)

---

## Section 2: Bite-Sized Task Breakdown

### Definition
Each task must satisfy:
- **Duration**: 2-5 minutes of focused execution
- **Scope**: Single feature increment (add one endpoint, one component, one migration)
- **Completeness**: Every file shown in full, no abbreviations, no "..."
- **Specificity**: Exact file paths, exact bash commands, exact test assertions

### Non-Examples (What NOT to do)
```markdown
## ❌ Task: Add validation
- Files: backend-api/routes/auth.js
- Code: "Add validation logic here"
- Test: "Run npm test"

## ❌ Task: Create user model
- Files: backend-api/models/user.js
- Code: 
  ```js
  class User {
    ...
    validateEmail() { /* validation */ }
  }
  ```
```

### Correct Example
```markdown
## ✓ Task: Add email validation to User model
- Files: backend-api/models/user.js
- Code: (complete class with method)
  ```js
  class User {
    constructor(data) {
      this.id = data.id;
      this.email = data.email;
    }
    
    validateEmail() {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(this.email)) {
        throw new Error('Invalid email format');
      }
      return true;
    }
  }
  
  module.exports = User;
  ```
- Test: `npm test -- models/user.test.js` (expect: email validation throws on invalid)
- Commit: "feat: add email validation to User model"
```

### Task Template
```markdown
## Task N: [Specific action] in [file/module]

**Files affected:**
- /path/to/file1.js
- /path/to/file2.ts
- etc.

**Complete code for each file:**
(Show every line, no abbreviations)

**Exact bash command to test:**
```bash
npm test -- specific-test-file.test.js
```

**Expected output:** (What success looks like)

**Git commit message:**
```
feat: [action description]
```
```

---

## Section 3: Task Ordering

### Dependency-First Approach
Tasks must respect this order:

1. **Layer 0: Shared Schemas** (no dependencies)
   - TypeScript types
   - Validation schemas (zod/joi)
   - Contract definitions
   - Shared constants and enums

2. **Layer 1: Backend Infrastructure** (depends on schemas)
   - Database migrations
   - Models and DAOs
   - Business logic services
   - Error handling and middleware

3. **Layer 2: Backend APIs** (depends on models)
   - REST endpoints
   - Request/response handlers
   - Authentication and authorization

4. **Layer 3: Web Frontend** (depends on API contracts)
   - API client (generated or manual)
   - State management (Redux, Zustand)
   - Components and views
   - Forms and validation

5. **Layer 4: Mobile App** (depends on API contracts)
   - API client
   - Navigation structure
   - Screens and components
   - Offline-first setup

### Within-Project Ordering
Order by dependency:
- Shared types → Constants → Validation → Models → Services → Routes → Middleware → Integration

### Dependency Markers
Mark explicit dependencies:
```markdown
## Task 3: Create user repository
**Depends on:** Task 1 (User schema), Task 2 (database connection)

## Task 5: Add POST /users endpoint
**Depends on:** Task 3 (user repository), Task 4 (authentication middleware)
```

---

## Section 4: Code Completeness

### Every file must be 100% complete
No:
- `import { Todo } from '../types'` without defining Todo in this plan
- `function validateUser() { /* validation logic */ }`
- `// Add error handling here`
- `...rest of the file...`

### Every import must be resolvable
If a file imports from another file, ensure that file is created earlier in the plan or it already exists in the repo.

### Example: Bad Plan
```markdown
## Task 2: Create user service
- Files: backend-api/services/userService.js
- Code:
  ```js
  const { UserRepository } = require('../models/user');
  
  class UserService {
    async createUser(userData) {
      return UserRepository.create(userData); // Not implemented yet!
    }
  }
  ```
```

### Example: Good Plan
```markdown
## Task 1: Create user repository
- Files: backend-api/models/userRepository.js
- Code:
  ```js
  class UserRepository {
    static async create(userData) {
      const db = require('../db');
      const query = 'INSERT INTO users (email, name) VALUES (?, ?)';
      const result = await db.run(query, [userData.email, userData.name]);
      return { id: result.lastID, ...userData };
    }
  }
  module.exports = { UserRepository };
  ```

## Task 2: Create user service
- Files: backend-api/services/userService.js
- Code:
  ```js
  const { UserRepository } = require('../models/userRepository');
  
  class UserService {
    async createUser(userData) {
      return UserRepository.create(userData);
    }
  }
  module.exports = { UserService };
  ```
```

### Complete Code Checklist
- ✓ All imports are defined or pre-existing
- ✓ All functions have complete bodies (no // TODO or // TODO: implement)
- ✓ All class methods are implemented
- ✓ All error cases are handled
- ✓ No placeholder strings or fake data

---

## Section 5: Verification Checklist

Every task must include:

### 1. Test Command
An exact, runnable bash command:
```bash
npm test -- users.test.js
npm run migrate:test
npm run build && npm run test:integration
jest --testPathPattern=userService.test.js
```

### 2. Expected Output
What the developer sees on success:
```
PASS  tests/userService.test.js
  UserService
    ✓ creates user with valid email (2ms)
    ✓ throws error on invalid email (1ms)
    ✓ returns user with id (3ms)

Test Suites: 1 passed, 1 total
Tests: 3 passed, 3 total
```

### 3. Commit Message
Standard format:
```
feat: [action] [what changed]
fix: [bug] [how it's fixed]
refactor: [what] [why simplified]
test: [what] [coverage added]
docs: [what] [clarity improved]
```

Example:
```
feat: add email validation to User model
```

### 4. Integration Checkpoint
After each task, verify:
- [ ] Code compiles/lints (no syntax errors)
- [ ] Test passes (assert expected output)
- [ ] No new import errors
- [ ] No breaking changes to previous tasks

### Task Verification Template
```markdown
## Task 7: Add POST /users endpoint

**Files affected:**
- backend-api/routes/auth.js

**Complete code:**
(Full route handler, no abbreviations)

**Test command:**
```bash
npm test -- routes/auth.test.js -- --testNamePattern="POST /users"
```

**Expected output:**
```
✓ POST /users creates new user (10ms)
✓ POST /users returns 400 on invalid email (5ms)
✓ POST /users returns 409 on duplicate email (8ms)
```

**Commit message:**
```
feat: add POST /users endpoint with validation
```

**Breaking changes:** None
**Backward compatible:** Yes (new endpoint, no changes to existing)
```

---

## Usage

### When Called
1. `brain-read` has provided locked spec from `/home/lordvoldemort/Videos/forge/brain/prds/<task-id>/spec.md`
2. Phase 2.10 (shared-dev-spec) is complete and immutable

### How to Use
```bash
# As a subagent in conductor-orchestrate flow:
skill tech-plan-write-per-project <task-id>

# Or manually:
cd /home/lordvoldemort/Videos/forge
# 1. Read the spec
# 2. Break into bite-sized tasks
# 3. Order by dependency
# 4. Write complete code (no placeholders)
# 5. Add test + commit message
# 6. Output to: brain/prds/<task-id>/tech-plans/
```

### Output Structure
```
brain/prds/<task-id>/tech-plans/
├── shared-schemas.md      (layer 0 tasks)
├── backend-api.md         (layers 1-2 tasks)
├── web-dashboard.md       (layer 3 tasks)
└── app-mobile.md          (layer 4 tasks)
```

Each file:
- Task ordering respects dependencies
- Every task is 2-5 min executable
- Every code block is complete
- Every test is exact and runnable
- Every commit message is standard

---

## Quality Gates

A tech plan passes if:
1. **Completeness**: No "...", no "TODO", no placeholders
2. **Specificity**: Every file path is absolute, every command is exact
3. **Testability**: Every task has a runnable test command and expected output
4. **Ordering**: No task depends on later tasks (DAG)
5. **Atomicity**: Each task is independent-executable (dev can run task N without running 1-N-1, given task setup is complete)

---

## Example: Complete Tech Plan Entry

```markdown
# Tech Plan: backend-api

## Task 1: Create user_profiles table migration
**Depends on:** None (schema layer 0)

**Files affected:**
- backend-api/migrations/001_create_user_profiles.sql

**Complete SQL migration:**
```sql
CREATE TABLE IF NOT EXISTS user_profiles (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  first_name VARCHAR(255),
  last_name VARCHAR(255),
  bio TEXT,
  avatar_url VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_user_id (user_id)
);
```

**Test command:**
```bash
npm run migrate:test
npm test -- migrations/001_create_user_profiles.test.js
```

**Expected output:**
```
PASS  migrations/001_create_user_profiles.test.js
  ✓ creates user_profiles table (15ms)
  ✓ enforces user_id uniqueness (8ms)
  ✓ cascades delete on user deletion (12ms)

Test Suites: 1 passed, 1 total
Tests: 3 passed, 3 total
```

**Git commit message:**
```
feat: add user_profiles table migration
```

---

## Task 2: Create UserProfile model
**Depends on:** Task 1 (migration)

**Files affected:**
- backend-api/models/UserProfile.js
- backend-api/models/UserProfile.test.js

**Complete UserProfile.js:**
```js
const db = require('../db');

class UserProfile {
  constructor(data) {
    this.id = data.id;
    this.userId = data.user_id;
    this.firstName = data.first_name;
    this.lastName = data.last_name;
    this.bio = data.bio;
    this.avatarUrl = data.avatar_url;
    this.createdAt = data.created_at;
    this.updatedAt = data.updated_at;
  }

  static async findByUserId(userId) {
    const query = 'SELECT * FROM user_profiles WHERE user_id = ?';
    const row = await db.get(query, [userId]);
    return row ? new UserProfile(row) : null;
  }

  static async create(userId, profileData) {
    const { firstName, lastName, bio, avatarUrl } = profileData;
    const query = `
      INSERT INTO user_profiles (user_id, first_name, last_name, bio, avatar_url)
      VALUES (?, ?, ?, ?, ?)
    `;
    const result = await db.run(
      query,
      [userId, firstName, lastName, bio, avatarUrl]
    );
    return {
      id: result.lastID,
      userId,
      firstName,
      lastName,
      bio,
      avatarUrl,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
  }

  async update(updateData) {
    const { firstName, lastName, bio, avatarUrl } = updateData;
    const query = `
      UPDATE user_profiles
      SET first_name = ?, last_name = ?, bio = ?, avatar_url = ?
      WHERE id = ?
    `;
    await db.run(
      query,
      [firstName, lastName, bio, avatarUrl, this.id]
    );
    this.firstName = firstName;
    this.lastName = lastName;
    this.bio = bio;
    this.avatarUrl = avatarUrl;
    this.updatedAt = new Date().toISOString();
    return this;
  }

  async delete() {
    const query = 'DELETE FROM user_profiles WHERE id = ?';
    await db.run(query, [this.id]);
  }

  toJSON() {
    return {
      id: this.id,
      userId: this.userId,
      firstName: this.firstName,
      lastName: this.lastName,
      bio: this.bio,
      avatarUrl: this.avatarUrl,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt
    };
  }
}

module.exports = UserProfile;
```

**Complete UserProfile.test.js:**
```js
const UserProfile = require('./UserProfile');
const db = require('../db');

jest.mock('../db');

describe('UserProfile', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('findByUserId', () => {
    test('returns user profile when found', async () => {
      const mockProfile = {
        id: 1,
        user_id: 10,
        first_name: 'John',
        last_name: 'Doe',
        bio: 'Developer',
        avatar_url: 'https://example.com/avatar.jpg',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };
      db.get.mockResolvedValue(mockProfile);

      const result = await UserProfile.findByUserId(10);

      expect(result).toBeInstanceOf(UserProfile);
      expect(result.firstName).toBe('John');
      expect(db.get).toHaveBeenCalledWith(
        expect.stringContaining('SELECT * FROM user_profiles WHERE user_id = ?'),
        [10]
      );
    });

    test('returns null when profile not found', async () => {
      db.get.mockResolvedValue(null);

      const result = await UserProfile.findByUserId(999);

      expect(result).toBeNull();
    });
  });

  describe('create', () => {
    test('creates a new user profile', async () => {
      db.run.mockResolvedValue({ lastID: 5 });

      const result = await UserProfile.create(10, {
        firstName: 'Jane',
        lastName: 'Smith',
        bio: 'Designer',
        avatarUrl: 'https://example.com/jane.jpg'
      });

      expect(result.id).toBe(5);
      expect(result.userId).toBe(10);
      expect(result.firstName).toBe('Jane');
      expect(db.run).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO user_profiles'),
        expect.arrayContaining([10, 'Jane', 'Smith', 'Designer'])
      );
    });
  });

  describe('update', () => {
    test('updates user profile', async () => {
      const profile = new UserProfile({
        id: 1,
        user_id: 10,
        first_name: 'John',
        last_name: 'Doe',
        bio: 'Developer',
        avatar_url: 'https://example.com/avatar.jpg',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      });

      db.run.mockResolvedValue({ changes: 1 });

      const updated = await profile.update({
        firstName: 'John',
        lastName: 'Doe Updated',
        bio: 'Senior Developer',
        avatarUrl: 'https://example.com/avatar-new.jpg'
      });

      expect(updated.lastName).toBe('Doe Updated');
      expect(db.run).toHaveBeenCalledWith(
        expect.stringContaining('UPDATE user_profiles'),
        expect.arrayContaining(['Doe Updated'])
      );
    });
  });

  describe('toJSON', () => {
    test('returns serializable object', () => {
      const profile = new UserProfile({
        id: 1,
        user_id: 10,
        first_name: 'John',
        last_name: 'Doe',
        bio: 'Developer',
        avatar_url: 'https://example.com/avatar.jpg',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      });

      const json = profile.toJSON();

      expect(json).toEqual({
        id: 1,
        userId: 10,
        firstName: 'John',
        lastName: 'Doe',
        bio: 'Developer',
        avatarUrl: 'https://example.com/avatar.jpg',
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z'
      });
    });
  });
});
```

**Test command:**
```bash
npm test -- models/UserProfile.test.js
```

**Expected output:**
```
PASS  models/UserProfile.test.js
  UserProfile
    findByUserId
      ✓ returns user profile when found (5ms)
      ✓ returns null when profile not found (3ms)
    create
      ✓ creates a new user profile (4ms)
    update
      ✓ updates user profile (6ms)
    toJSON
      ✓ returns serializable object (2ms)

Test Suites: 1 passed, 1 total
Tests: 5 passed, 5 total
Snapshots: 0 total
Time: 0.847 s
```

**Git commit message:**
```
feat: add UserProfile model with CRUD operations
```

---

## Task 3: Add GET /users/:userId/profile endpoint
**Depends on:** Task 2 (UserProfile model)

**Files affected:**
- backend-api/routes/profile.js
- backend-api/routes/profile.test.js

**Complete profile.js:**
```js
const express = require('express');
const router = express.Router();
const UserProfile = require('../models/UserProfile');
const { authenticateToken } = require('../middleware/auth');

// GET /users/:userId/profile
router.get('/:userId/profile', authenticateToken, async (req, res) => {
  try {
    const { userId } = req.params;

    // Validate userId is a number
    if (!Number.isInteger(parseInt(userId))) {
      return res.status(400).json({
        error: 'Invalid user ID format',
        code: 'INVALID_USER_ID'
      });
    }

    const profile = await UserProfile.findByUserId(parseInt(userId));

    if (!profile) {
      return res.status(404).json({
        error: 'User profile not found',
        code: 'PROFILE_NOT_FOUND'
      });
    }

    res.json(profile.toJSON());
  } catch (error) {
    console.error('Error fetching user profile:', error);
    res.status(500).json({
      error: 'Internal server error',
      code: 'INTERNAL_ERROR'
    });
  }
});

module.exports = router;
```

**Complete profile.test.js:**
```js
const request = require('supertest');
const express = require('express');
const profileRouter = require('./profile');
const UserProfile = require('../models/UserProfile');

// Mock UserProfile
jest.mock('../models/UserProfile');

// Mock auth middleware
jest.mock('../middleware/auth', () => ({
  authenticateToken: (req, res, next) => {
    req.user = { id: 1 };
    next();
  }
}));

const app = express();
app.use(express.json());
app.use('/users', profileRouter);

describe('Profile Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('GET /users/:userId/profile', () => {
    test('returns user profile for valid userId', async () => {
      const mockProfile = {
        id: 1,
        userId: 10,
        firstName: 'John',
        lastName: 'Doe',
        bio: 'Developer',
        avatarUrl: 'https://example.com/avatar.jpg',
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
        toJSON: () => ({
          id: 1,
          userId: 10,
          firstName: 'John',
          lastName: 'Doe',
          bio: 'Developer',
          avatarUrl: 'https://example.com/avatar.jpg',
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z'
        })
      };

      UserProfile.findByUserId.mockResolvedValue(mockProfile);

      const response = await request(app).get('/users/10/profile');

      expect(response.status).toBe(200);
      expect(response.body).toEqual(mockProfile.toJSON());
      expect(UserProfile.findByUserId).toHaveBeenCalledWith(10);
    });

    test('returns 404 when profile not found', async () => {
      UserProfile.findByUserId.mockResolvedValue(null);

      const response = await request(app).get('/users/999/profile');

      expect(response.status).toBe(404);
      expect(response.body.code).toBe('PROFILE_NOT_FOUND');
    });

    test('returns 400 for invalid userId format', async () => {
      const response = await request(app).get('/users/invalid/profile');

      expect(response.status).toBe(400);
      expect(response.body.code).toBe('INVALID_USER_ID');
    });

    test('returns 500 on database error', async () => {
      UserProfile.findByUserId.mockRejectedValue(
        new Error('Database connection failed')
      );

      const response = await request(app).get('/users/10/profile');

      expect(response.status).toBe(500);
      expect(response.body.code).toBe('INTERNAL_ERROR');
    });
  });
});
```

**Test command:**
```bash
npm test -- routes/profile.test.js
```

**Expected output:**
```
PASS  routes/profile.test.js
  Profile Routes
    GET /users/:userId/profile
      ✓ returns user profile for valid userId (12ms)
      ✓ returns 404 when profile not found (8ms)
      ✓ returns 400 for invalid userId format (6ms)
      ✓ returns 500 on database error (5ms)

Test Suites: 1 passed, 1 total
Tests: 4 passed, 4 total
Snapshots: 0 total
Time: 1.204 s
```

**Git commit message:**
```
feat: add GET /users/:userId/profile endpoint
```

---

## Task 4: Register profile routes in main app
**Depends on:** Task 3 (profile routes)

**Files affected:**
- backend-api/index.js

**Complete index.js (update section):**
```js
const express = require('express');
const cors = require('cors');
const authRoutes = require('./routes/auth');
const profileRoutes = require('./routes/profile');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', profileRoutes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({
    error: 'Internal server error',
    code: 'INTERNAL_ERROR'
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;
```

**Test command:**
```bash
npm test -- integration/routes.test.js
```

**Expected output:**
```
PASS  integration/routes.test.js
  App Routes
    ✓ GET /health returns 200 (4ms)
    ✓ GET /api/users/:userId/profile is registered (8ms)
    ✓ POST /api/auth/login is registered (6ms)

Test Suites: 1 passed, 1 total
Tests: 3 passed, 3 total
Snapshots: 0 total
Time: 0.923 s
```

**Git commit message:**
```
feat: register profile routes in main app
```

---
```

---

## Edge Cases & Fallback Paths

### Edge Case 1: Spec has holes in one project (missing implementation details)

**Diagnosis**: Shared spec says "add user authentication" but doesn't specify: which auth mechanism (OAuth, JWT, API key)? Web project has no guidance.

**Response**:
- **Escalate for spec clarification**: "Spec missing detail: authentication mechanism for web project. Options: OAuth2, JWT, API key. Which applies here?"
- **Default not allowed**: Do NOT fill in missing details without confirming with spec owner.
- **Lock clarification**: Once confirmed, document in tech plan: "Authentication: [chosen mechanism] per spec clarification [date]."

**Escalation**: NEEDS_CONTEXT - Cannot write tech plan without clarity. Ask spec owner for missing detail.

---

### Edge Case 2: Tasks cannot be 2-5 minutes (some tasks are inherently larger)

**Diagnosis**: Tech plan says "Task: implement OAuth2 flow: 3 minutes". Realistically, this takes 30+ minutes (API calls, token management, error handling).

**Response**:
- **Break down into smaller tasks**:
  1. "Set up OAuth2 library and dependencies" (2-3 min)
  2. "Implement token request flow" (3-4 min)
  3. "Implement token refresh logic" (3-4 min)
  4. "Add error handling and edge cases" (2-3 min)
- **If task cannot be broken down further**: Escalate to tech-plan-self-review, which will flag it as too large.
- **Justification**: Each task should be completable and reviewable in isolation.

**Escalation**: If a task cannot be broken below 5 minutes without becoming trivial, escalate: "Task is too large. Recommend: split into subtasks or adjust scope."

---

### Edge Case 3: Placeholder cannot be avoided (external dependency, research needed)

**Diagnosis**: Tech plan says "Task: integrate with [Third-Party API]". But API docs are not yet available. Placeholder: "Wait for API docs".

**Response**:
- **Document the blocker**: "Task blocked by: [Third-Party API docs]. Cannot proceed until [condition]."
- **Plan around it**: If possible, write tests/stubs for the API before it's available.
- **Track risk**: Flag in tech plan: "Critical path blocker: [API]. Delay risk: if not available by [date], project at risk."
- **Escalation to tech-plan-self-review**: Self-review will flag this as a risk and escalate if needed.

**Escalation**: BLOCKED - Task has unresolvable external dependency. Flag in tech plan and escalate to conductor if it impacts timeline.

---

## End of Example

This example shows how each task:
1. Has complete, runnable code (not placeholders)
2. Specifies exact file paths
3. Includes a test command and expected output
4. Has a standard commit message
5. Respects dependencies (Task 2 depends on Task 1)

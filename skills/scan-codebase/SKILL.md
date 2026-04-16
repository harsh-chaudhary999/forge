---
name: scan-codebase
description: "WHEN: You need to map an existing codebase into the Forge brain — building an Obsidian-format knowledge graph of module relationships, architecture patterns, API surface, and documented edge cases. Invoked automatically after /workspace init and manually via /scan."
type: rigid
requires: [brain-write]
---

# Scan Codebase

Map an existing repository into the Forge brain as an interconnected Obsidian knowledge graph.
Produces `~/forge/brain/products/<slug>/codebase/` — readable by humans, queryable by agents.

---

## Anti-Pattern Preamble

**Stop. Read this before touching any file.**

### Anti-Pattern 1: "Just read all the source files — that's how you understand a codebase"

**Why This Fails:** Reading every file burns 50-200K tokens on boilerplate, tests, generated code, and third-party vendored files. 30-40% of what you read will be noise. The structural relationships you need (who imports whom, what the entry points are, which files are hubs) are available from import lines and filenames alone — zero tokens required.

**Enforcement:**
- MUST run Phase 1 (grep/find) before reading any source file
- MUST identify hub files via incoming-reference count before selecting what to read
- MUST exclude: `node_modules/`, `vendor/`, `dist/`, `build/`, `__pycache__/`, `.git/`, `*.generated.*`, `*.min.js`, `*.lock`
- MUST extract class/type/struct inventory via grep in Phase 1.6 BEFORE reading any hub file
- MUST NOT read test files unless they are the only documentation for an API

### Anti-Pattern 2: "I'll scan the entire codebase at once and produce a single summary"

**Why This Fails:** Monolithic summaries are high-token, low-recall. When an agent later needs to know "what does the auth module export?", searching a 5000-word summary is slower and less reliable than reading `brain/products/<slug>/codebase/modules/auth.md`. The output must be navigable files, not a wall of text.

**Enforcement:**
- MUST produce separate `.md` files per module — not a single summary document
- MUST use `[[wikilinks]]` to cross-reference between brain files
- MUST write each file to `~/forge/brain/products/<slug>/codebase/` individually
- MUST git-commit after each project role is scanned (backend, web, app) — not after all

### Anti-Pattern 3: "I'll infer architecture patterns without checking the actual dependency graph"

**Why This Fails:** Pattern detection from file names alone is wrong 40% of the time. A file named `UserService.ts` in a monolith does not imply service architecture. The actual import graph — which files import which — is the ground truth for pattern detection.

**Enforcement:**
- MUST build import adjacency before classifying patterns
- MUST confirm pattern with at least 3 structural signals (not just naming conventions)
- MUST label uncertain patterns as `likely-<pattern> (unconfirmed)` in output
- MUST NOT write patterns.md until after the import graph is built

### Anti-Pattern 4: "Tests are noise — skip them"

**Why This Fails:** Test files are often the only documentation for edge cases and expected failure modes. A `test_login_with_expired_token.py` tells you more about auth edge cases than any docstring. Test file names and their `describe`/`test` strings are high-signal, zero-token gotcha sources.

**Enforcement:**
- MUST scan test file names and top-level describe/test strings
- MUST extract `it("should fail when...")` and `test("edge case:...")` strings into `gotchas.md`
- MAY skip test file bodies — names and test strings only
- MUST NOT skip entire test directories

### Anti-Pattern 5: "I've scanned this before — I'll use my memory instead of re-running"

**Why This Fails:** Codebases change. A brain scan is a snapshot. Using stale scan data leads agents to reference deleted modules, outdated APIs, or patterns that were refactored out. Every scan must produce a new timestamped snapshot.

**Enforcement:**
- MUST write `SCAN.json` with timestamp, commit SHA, and file count on every run
- MUST include `last-scanned:` field in `index.md` header
- MUST NOT reuse a scan older than 7 days without re-running Phase 1 to check for new files
- MUST overwrite existing codebase brain files on re-scan (not append)

---

## Overview

Scan produces a structured knowledge graph of a codebase, stored in the Forge brain as navigable Obsidian markdown. It runs in 4 phases, ordered by token cost (cheapest first):

```
Phase 1 — Structural map     (bash only, 0 tokens)
Phase 2 — Hub detection      (bash only, 0 tokens)
Phase 3 — Semantic enrichment (targeted reads, low tokens)
Phase 4 — Brain write        (structured output, low tokens)
```

Output goes to: `~/forge/brain/products/<slug>/codebase/`

```
codebase/
  index.md              # Overview: entry points, architecture style, stats, last scanned
  SCAN.json             # Metadata: timestamp, commit SHA, file count, language breakdown
  modules/
    <module-name>.md    # Per-module: purpose, exports, dependencies, dependents
  patterns.md           # Detected architecture patterns with evidence
  api-surface.md        # Public API endpoints, exported symbols, event schemas
  gotchas.md            # Documented edge cases, TODOs, FIXMEs, test-case-named edge cases
```

---

## Phase 1: Structural Map (Zero Tokens)

Run these bash commands for **each repo** in the workspace. Collect all output before reading any files.

### 1.1 — File inventory

```bash
REPO=<repo-path>

# Detect git submodule paths to exclude from scan
SUBMODULE_PATHS=$(git -C "$REPO" submodule --quiet foreach 'echo $displaypath' 2>/dev/null)

# Build exclusion pattern for submodule directories
SUBMODULE_EXCLUDES=""
for sm in $SUBMODULE_PATHS; do
  SUBMODULE_EXCLUDES="$SUBMODULE_EXCLUDES | grep -v \"$sm/\""
done

# All source files, excluding noise
find "$REPO" -type f \( \
  -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \
  -o -name "*.py" -o -name "*.go" -o -name "*.java" -o -name "*.kt" \
  -o -name "*.rs" -o -name "*.rb" -o -name "*.dart" -o -name "*.swift" \
  -o -name "*.cpp" -o -name "*.c" -o -name "*.h" \
) \
| grep -v node_modules \
| grep -v "\.git/" \
| grep -v "__pycache__" \
| grep -v "/vendor/" \
| grep -v "/dist/" \
| grep -v "/build/" \
| grep -v "\.generated\." \
| grep -v "\.min\." \
| grep -v "\.spec\." \
| grep -v "\.test\." \
| eval "grep -v node_modules $SUBMODULE_EXCLUDES" \
| sort > /tmp/forge_scan_source_files.txt

# Test files — separately (for gotchas extraction)
find "$REPO" -type f \( -name "*.spec.*" -o -name "*.test.*" -o -name "*_test.*" -o -name "test_*.py" \) \
| grep -v node_modules | grep -v "\.git/" | grep -v dist \
| sort > /tmp/forge_scan_test_files.txt

echo "Source files: $(wc -l < /tmp/forge_scan_source_files.txt)"
echo "Test files: $(wc -l < /tmp/forge_scan_test_files.txt)"
```

### 1.2 — Module boundary detection

> **Monorepo detection:** Before scanning, check if the repo is a Turborepo/Nx/Lerna/pnpm workspace monorepo. If it is, treat each package as a separate logical repo for the purposes of module naming and brain file organization.

```bash
# Detect monorepo structure
IS_MONOREPO=false
MONOREPO_PACKAGES=""

if [ -f "$REPO/turbo.json" ] || [ -f "$REPO/nx.json" ] || [ -f "$REPO/lerna.json" ]; then
  IS_MONOREPO=true
  # Find package directories (packages/, apps/, libs/ are common roots)
  MONOREPO_PACKAGES=$(find "$REPO" -maxdepth 3 -name "package.json" \
    | grep -v node_modules | grep -v "^$REPO/package.json" \
    | xargs dirname | sort)
  echo "Monorepo detected. Packages:"
  echo "$MONOREPO_PACKAGES"
  echo ""
  echo "Scan each package as a separate logical repo. Use package directory name as role prefix."
  echo "Example: packages/api/src/users.ts → api-users.md"
fi

# Top-level directories (excluding config/infra noise)
find "$REPO" -maxdepth 2 -type d \
  | grep -v node_modules | grep -v "\.git" | grep -v __pycache__ \
  | grep -v "dist\b" | grep -v "\bbuild\b" \
  | awk -F/ 'NF<=4' \
  | sort

# Entry point detection
find "$REPO" -maxdepth 3 \( \
  -name "main.py" -o -name "app.py" -o -name "server.py" \
  -o -name "index.ts" -o -name "main.ts" -o -name "app.ts" \
  -o -name "index.js" -o -name "main.js" -o -name "server.js" \
  -o -name "main.go" -o -name "main.kt" -o -name "Main.kt" \
  -o -name "main.rs" -o -name "Application.java" \
\) | grep -v node_modules | grep -v dist
```

### 1.3 — Import graph extraction

```bash
# Extract import lines only (first 50 lines per file — imports are always at the top)
while IFS= read -r file; do
  echo "=== $file ==="
  head -50 "$file" | grep -E \
    "^import |^from |^require\(|^use |^extern crate|^#include|^using " \
    2>/dev/null
done < /tmp/forge_scan_source_files.txt > /tmp/forge_scan_imports.txt

echo "Import relationships extracted: $(grep -c "^===" /tmp/forge_scan_imports.txt) files"
```

### 1.4 — Incoming reference count (hub detection)

```bash
# Count how many files reference each module/file
# This identifies architectural hubs without reading any file content

while IFS= read -r file; do
  basename_no_ext=$(basename "$file" | sed 's/\.[^.]*$//')
  count=$(grep -rl "$basename_no_ext" "$REPO" \
    --include="*.ts" --include="*.py" --include="*.go" --include="*.java" --include="*.kt" \
    2>/dev/null | grep -v node_modules | grep -v "\.git" | grep -v dist | wc -l)
  echo "$count $file"
done < /tmp/forge_scan_source_files.txt \
| sort -rn > /tmp/forge_scan_hub_scores.txt

echo "Top 10 hubs:"
head -10 /tmp/forge_scan_hub_scores.txt
```

### 1.5 — Language and framework fingerprinting

```bash
# Language breakdown
echo "Language breakdown:"
grep -c "\.ts$\|\.tsx$" /tmp/forge_scan_source_files.txt && echo "TypeScript/TSX files"
grep -c "\.py$" /tmp/forge_scan_source_files.txt && echo "Python files"
grep -c "\.go$" /tmp/forge_scan_source_files.txt && echo "Go files"
grep -c "\.java$" /tmp/forge_scan_source_files.txt && echo "Java files"
grep -c "\.kt$" /tmp/forge_scan_source_files.txt && echo "Kotlin files"
grep -c "\.dart$" /tmp/forge_scan_source_files.txt && echo "Dart files"

# Framework signals (package.json, go.mod, requirements.txt, etc.)
[ -f "$REPO/package.json" ] && cat "$REPO/package.json" | grep -E '"next"|"express"|"fastify"|"nestjs"|"react-native"|"vue"|"nuxt"|"svelte"|"hono"|"koa"'
[ -f "$REPO/go.mod" ] && grep -E "gin|echo|fiber|chi|mux" "$REPO/go.mod"
[ -f "$REPO/requirements.txt" ] && grep -iE "fastapi|django|flask|starlette|tornado" "$REPO/requirements.txt"
[ -f "$REPO/pubspec.yaml" ] && head -5 "$REPO/pubspec.yaml"
```

### 1.6 — Type/class inventory (zero tokens, all languages)

> **This step is mandatory.** Class file generation in Phase 4.3a is driven from this inventory — not from in-context memory. Run this before any hub reads.

Each language has fundamentally different syntax. Grep patterns below are language-specific.

```bash
# ── Java ──────────────────────────────────────────────────────────────────────
# Capture: class, abstract class, interface, enum, annotation type (@interface)
# Include Spring annotations line above (@Service, @Repository, @Controller, etc.)
grep -rn \
  "^\s*\(public\|protected\|private\|abstract\|final\|static\)\{0,3\}\s*\(class\|interface\|enum\|@interface\)\s" \
  "$REPO" --include="*.java" \
  | grep -v "/test/\|Test\.java\b\|IT\.java\b\|Tests\.java\b" \
  > /tmp/forge_scan_types_java.txt

# Spring/Jakarta stereotype annotations (these mark the important classes)
grep -rn "^\s*@\(Service\|Repository\|Controller\|RestController\|Component\|Configuration\|Entity\|SpringBootApplication\)" \
  "$REPO" --include="*.java" \
  | grep -v "/test/" \
  > /tmp/forge_scan_annotations_java.txt

echo "Java types: $(wc -l < /tmp/forge_scan_types_java.txt) | Annotations: $(wc -l < /tmp/forge_scan_annotations_java.txt)"

# ── Kotlin ────────────────────────────────────────────────────────────────────
# Capture: class, data class, sealed class, abstract class, open class,
#          inner class, interface, object, companion object, typealias, enum class
grep -rn \
  "^\s*\(data \|sealed \|abstract \|open \|inner \|enum \|annotation \)\?\(class\|interface\|object\)\s\|^\s*typealias \|^\s*companion object" \
  "$REPO" --include="*.kt" \
  | grep -v "Test\.kt\b\|Spec\.kt\b\|/test/" \
  > /tmp/forge_scan_types_kotlin.txt

# Kotlin/Spring annotations
grep -rn "^\s*@\(Service\|Repository\|Controller\|RestController\|Component\|Configuration\|Entity\|SpringBootApplication\)" \
  "$REPO" --include="*.kt" \
  | grep -v "/test/" \
  > /tmp/forge_scan_annotations_kotlin.txt

echo "Kotlin types: $(wc -l < /tmp/forge_scan_types_kotlin.txt)"

# ── Go ────────────────────────────────────────────────────────────────────────
# Go has NO classes. Types are: struct, interface (both defined with `type`)
# Methods are defined SEPARATELY via receiver functions — not inside the type.
# These MUST be extracted independently.

# Exported structs and interfaces (uppercase first letter = exported in Go)
grep -rn "^type [A-Z][a-zA-Z0-9]* \(struct\|interface\)\b" \
  "$REPO" --include="*.go" \
  | grep -v "_test\.go" \
  > /tmp/forge_scan_types_go.txt

# Go receiver methods — CRITICAL: these are Go's equivalent of class methods
# Pattern: func (receiverVar *TypeName) MethodName( OR func (receiverVar TypeName) MethodName(
grep -rn "^func ([a-zA-Z_][a-zA-Z0-9_]* \*\?[A-Z][a-zA-Z0-9]*) [A-Z]" \
  "$REPO" --include="*.go" \
  | grep -v "_test\.go" \
  > /tmp/forge_scan_methods_go.txt

echo "Go types: $(wc -l < /tmp/forge_scan_types_go.txt) | Go exported methods: $(wc -l < /tmp/forge_scan_methods_go.txt)"

# ── TypeScript / JavaScript ───────────────────────────────────────────────────
# Capture: exported class, abstract class, interface, type alias (uppercase = domain type)
grep -rn \
  "^export \(default \)\?\(abstract \)\?class \|^export interface \|^export abstract class \|^export type [A-Z]" \
  "$REPO" --include="*.ts" --include="*.tsx" \
  | grep -v "node_modules\|\.d\.ts\|\.spec\.\|\.test\." \
  > /tmp/forge_scan_types_ts.txt

# NestJS / TypeORM / class-validator decorators (these mark the architecturally important classes)
grep -rn "^@\(Injectable\|Controller\|Service\|Repository\|Entity\|Module\|Guard\|Interceptor\|Pipe\|EventEmitter\|Resolver\|ObjectType\|InputType\)" \
  "$REPO" --include="*.ts" \
  | grep -v "node_modules\|\.spec\.\|\.test\." \
  > /tmp/forge_scan_decorators_ts.txt

echo "TypeScript types: $(wc -l < /tmp/forge_scan_types_ts.txt) | Decorators: $(wc -l < /tmp/forge_scan_decorators_ts.txt)"

# ── Python ────────────────────────────────────────────────────────────────────
# Capture: class definitions starting with uppercase (PEP8 class naming convention)
grep -rn "^class [A-Za-z][a-zA-Z0-9]*\(.*\)\?:" \
  "$REPO" --include="*.py" \
  | grep -v "test_[a-z]\|_test\.py\|Test[A-Z]" \
  > /tmp/forge_scan_types_python.txt

# Python dataclasses and ABCs
grep -rn "^@\(dataclass\|dataclasses\.dataclass\|abstractmethod\|abc\.ABC\)" \
  "$REPO" --include="*.py" \
  | grep -v "test_\|_test\.py" \
  > /tmp/forge_scan_annotations_python.txt

echo "Python types: $(wc -l < /tmp/forge_scan_types_python.txt)"

# ── Dart / Flutter ────────────────────────────────────────────────────────────
grep -rn "^\(abstract \)\?class [A-Z]\|^mixin [A-Z]\|^enum [A-Z]" \
  "$REPO" --include="*.dart" \
  | grep -v "_test\.dart\|test/" \
  > /tmp/forge_scan_types_dart.txt

echo "Dart types: $(wc -l < /tmp/forge_scan_types_dart.txt)"

# ── Rust ──────────────────────────────────────────────────────────────────────
grep -rn "^pub \(struct\|enum\|trait\|impl\) [A-Z]\|^pub(crate) \(struct\|enum\|trait\) [A-Z]" \
  "$REPO" --include="*.rs" \
  | grep -v "test\b" \
  > /tmp/forge_scan_types_rust.txt

echo "Rust types: $(wc -l < /tmp/forge_scan_types_rust.txt)"

# ── Master inventory ──────────────────────────────────────────────────────────
cat /tmp/forge_scan_types_java.txt \
    /tmp/forge_scan_types_kotlin.txt \
    /tmp/forge_scan_types_go.txt \
    /tmp/forge_scan_types_ts.txt \
    /tmp/forge_scan_types_python.txt \
    /tmp/forge_scan_types_dart.txt \
    /tmp/forge_scan_types_rust.txt \
    2>/dev/null > /tmp/forge_scan_types_all.txt

echo "══════════════════════════════════════════"
echo "Total types in inventory: $(wc -l < /tmp/forge_scan_types_all.txt)"
echo "Go methods: $(wc -l < /tmp/forge_scan_methods_go.txt)"
echo "══════════════════════════════════════════"
```

> **Go note:** Go methods (`/tmp/forge_scan_methods_go.txt`) are NOT in the type inventory because they are standalone functions with a receiver — they have no syntactic nesting. When writing a class file for a Go struct, look up matching entries in `forge_scan_methods_go.txt` where the receiver type matches the struct name.
>
> **Decorator note:** For Java/Kotlin/TypeScript, cross-reference `forge_scan_annotations_*.txt` with the type inventory. A class annotated `@Service` is an application service. `@Repository` is a data layer. `@Controller` / `@RestController` is a request handler. Use these to populate the **Layer** field in class files.

---

## Phase 2: Hub Identification (Zero Tokens)

From `forge_scan_hub_scores.txt`, identify:

**Tier 1 Hubs** (referenced by 5+ files) — read in full in Phase 3
**Tier 2 Hubs** (referenced by 3-4 files) — read in full in Phase 3
**Leaf files** (referenced by 0-2 files) — extract only from import graph, do NOT read body

```bash
# Tier 1 hubs
awk '$1 >= 5 {print $2}' /tmp/forge_scan_hub_scores.txt > /tmp/forge_scan_tier1.txt
echo "Tier 1 hubs: $(wc -l < /tmp/forge_scan_tier1.txt)"

# Tier 2 hubs
awk '$1 >= 3 && $1 < 5 {print $2}' /tmp/forge_scan_hub_scores.txt > /tmp/forge_scan_tier2.txt
echo "Tier 2 hubs: $(wc -l < /tmp/forge_scan_tier2.txt)"
```

---

## Phase 3: Semantic Enrichment (Full Reads)

Read files in this priority order. Read each file in full.

### 3.1 — Always read

These are documentation files, not code. Read fully:

```bash
for doc in README.md CONTRIBUTING.md ARCHITECTURE.md docs/architecture.md docs/design.md \
           ADR*.md adr/*.md docs/decisions/*.md; do
  [ -f "$REPO/$doc" ] && echo "=== $REPO/$doc ===" && cat "$REPO/$doc"
done
```

### 3.2 — Tier 1 hub reads (full file)

```bash
while IFS= read -r file; do
  echo "=== $file ==="
  cat "$file"
  echo ""
done < /tmp/forge_scan_tier1.txt
```

Extract from each hub:
- Exported classes, functions, interfaces (look for `export`, `public`, `pub fn`, `func`, `def`)
- Constructor signatures and key method signatures
- JSDoc/docstrings on exported items
- `// TODO`, `// FIXME`, `// HACK`, `// NOTE` comments

### 3.3 — Tier 2 hub reads (full file)

```bash
while IFS= read -r file; do
  echo "=== $file ==="
  cat "$file"
  echo ""
done < /tmp/forge_scan_tier2.txt
```

### 3.3a — Class/method/attribute enrichment from hub reads

Phase 1.6 already extracted the **names and locations** of all types from disk via grep. The job here is to **enrich** those known types with methods, properties, doc comments, and inheritance — by reading the hub files in full.

For each hub file, cross-reference `/tmp/forge_scan_types_all.txt` to know which classes live there, then extract the following. **Each language has fundamentally different syntax:**

---

**Java** (`*.java`)

*Types*: `public class Foo`, `abstract class Foo`, `interface Foo`, `enum Foo`, `@interface Foo`
*Inheritance*: `extends BarClass`, `implements BazInterface` — critical for graph edges
*Annotations*: `@Service`, `@Repository`, `@RestController`, `@Entity` — determines layer
*Fields (properties)*: `private String name;`, `protected final List<X> items;`
*Methods*: `public ReturnType methodName(Type param)` — include full signature
*Constructor*: `public ClassName(Type param, Type param2)`
*Key gotcha*: Inner classes and anonymous classes — record them as nested, not top-level

**Kotlin** (`*.kt`)

*Types*: `data class Foo(val a: A, val b: B)` — constructor params ARE the properties
*Sealed class*: `sealed class Result` with subclasses `data class Success(...)` and `data class Error(...)` — these are variants, not independent classes
*Object*: `object Singleton` — no constructor, static singleton
*Companion object*: nested `companion object { ... }` — factory methods live here
*Coroutines*: `suspend fun fetchData(): Result<T>` — mark `suspend` in method notes
*Properties*: `val name: String`, `var count: Int = 0`, `lateinit var db: DB`
*Key gotcha*: Extension functions (`fun String.toUser(): User`) are NOT class members — they belong to the module, not the class

**Go** (`*.go`)

*Types*: `type UserService struct { ... }` — fields are inside the struct body
*Struct fields*: Lines inside `type X struct { ... }` block — `FieldName Type \`json:"..."\`` 
*Interfaces*: `type UserRepository interface { ... }` — method signatures inside the block
*Methods*: **NOT inside the struct.** Look in `/tmp/forge_scan_methods_go.txt` for lines matching `(* TypeName)` or `( TypeName)`. Pattern: `func (u *UserService) GetUser(ctx context.Context, id int64) (*User, error)`
*Constructor*: `func NewUserService(db *DB) *UserService` — named constructors, not `new`
*Key gotcha*: Go has no inheritance. Embedding (`type Admin struct { User }`) is composition, not inheritance. Note it as "embeds [[classes/<role>-User]]" not "extends".

**TypeScript / Node.js** (`*.ts`, `*.tsx`)

*Types*: `export class UserController`, `export interface IUser`, `export abstract class BaseService`
*Decorators*: `@Injectable()`, `@Controller('/users')`, `@Entity()` — the decorator tells you the layer before you read a single method
*Constructor injection*: `constructor(private readonly userService: UserService)` — injected deps = class dependencies for graph edges
*Methods*: `async getUser(id: string): Promise<User>`, `private validate(data: unknown): boolean`
*Properties*: `readonly name: string`, `private count = 0`, `@Column() email: string`
*Type aliases*: `export type UserId = string` — if used widely, it's a domain concept worth noting
*Key gotcha*: Arrow function class properties (`private handleClick = () => {}`) are methods defined as properties — include them

**Python** (`*.py`)

*Types*: `class UserService(BaseService):` — base class in parens = inheritance
*Dataclasses*: `@dataclass class User:` — fields defined as `name: str`, `age: int = 0`
*Abstract*: `class IRepository(ABC):` with `@abstractmethod def find_by_id(self, id: int)`
*Methods*: `def get_user(self, user_id: int) -> User:`, `async def fetch(self) -> List[T]:`
*Class variables*: `MAX_RETRIES: int = 3` (outside `__init__`)
*Instance variables*: set in `__init__`: `self.name = name`
*Key gotcha*: `__init__` params are the constructor signature — list them as "Constructor" not as a method

**Dart / Flutter** (`*.dart`)

*Types*: `class UserBloc extends Bloc<UserEvent, UserState>`, `abstract class IUserRepository`, `mixin LoggerMixin`
*Widgets*: `class UserWidget extends StatelessWidget` / `StatefulWidget` — note as "widget", not "service"
*Fields*: `final String name;`, `late UserRepository _repo;`
*Methods*: `@override Widget build(BuildContext context)`, `Future<User> getUser(String id)`

---

**Record per class as you read** (used in Phase 4.3a):

```
Language: Go
File: internal/user/service.go
Type: UserService (struct)
Annotation/Decorator: none
Fields: db *gorm.DB, logger *zap.Logger
Methods (from forge_scan_methods_go.txt): GetUser(ctx, id int64) (*User, error), CreateUser(ctx, req CreateUserRequest) (*User, error), DeleteUser(ctx, id int64) error
Implements: UserRepository (interface)
Constructor: NewUserService(db *gorm.DB, logger *zap.Logger) *UserService
```

```
Language: Kotlin
File: src/main/kotlin/com/app/user/UserService.kt
Type: UserService (class)
Annotation: @Service
Properties: userRepository: UserRepository (injected), emailSender: EmailSender (injected)
Methods: findById(id: Long): User?, createUser(req: CreateUserRequest): User, suspend sendWelcomeEmail(userId: Long)
Extends: none
Implements: IUserService
```

Only record classes from Tier 1 and Tier 2 hub files. Leaf files contribute to the import graph only.

---

### 3.4 — Test name extraction (zero token body reads)

```bash
# Extract test names only — no file body reads needed
while IFS= read -r file; do
  echo "=== $file ==="
  grep -n \
    "it\(.\|test\(.\|describe\(.\|def test_\|func Test\|#\[test\]\|@Test" \
    "$file" 2>/dev/null | head -30
done < /tmp/forge_scan_test_files.txt > /tmp/forge_scan_test_names.txt
```

### 3.5 — API surface extraction

```bash
# REST endpoints (look for route decorators and router patterns)
grep -rn \
  "@Get\|@Post\|@Put\|@Delete\|@Patch\|router\.get\|router\.post\|app\.get\|app\.post\|r\.GET\|r\.POST\|@app\.route\|@router\." \
  "$REPO" --include="*.ts" --include="*.py" --include="*.go" --include="*.java" --include="*.kt" \
  | grep -v node_modules | grep -v dist | grep -v test | grep -v spec \
  > /tmp/forge_scan_api_routes.txt

echo "API routes found: $(wc -l < /tmp/forge_scan_api_routes.txt)"
cat /tmp/forge_scan_api_routes.txt
```

---

## Phase 4: Brain Write (Obsidian Format)

Create all output files in `~/forge/brain/products/<slug>/codebase/`. Use `[[wikilinks]]` throughout.

### 4.1 — SCAN.json (metadata, always first)

```bash
SCAN_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
COMMIT_SHA=$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo "unknown")
FILE_COUNT=$(wc -l < /tmp/forge_scan_source_files.txt)
TEST_COUNT=$(wc -l < /tmp/forge_scan_test_files.txt)

cat > ~/forge/brain/products/<slug>/codebase/SCAN.json << EOF
{
  "scanned_at": "$SCAN_DATE",
  "repo": "$REPO",
  "commit": "$COMMIT_SHA",
  "source_files": $FILE_COUNT,
  "test_files": $TEST_COUNT,
  "tier1_hubs": $(wc -l < /tmp/forge_scan_tier1.txt),
  "tier2_hubs": $(wc -l < /tmp/forge_scan_tier2.txt),
  "types_in_inventory": $(wc -l < /tmp/forge_scan_types_all.txt 2>/dev/null || echo 0),
  "go_methods_in_inventory": $(wc -l < /tmp/forge_scan_methods_go.txt 2>/dev/null || echo 0),
  "role": "<backend|web|mobile|shared>"
}
EOF
```

### 4.2 — index.md format

```markdown
# Codebase: <repo-name> (<role>)

last-scanned: <ISO timestamp>
commit: <SHA>
files: <count> source, <count> test

## Architecture Style

<Detected pattern: monolith | service-per-feature | layered | modular-monolith | microservice slice>
Evidence:
- <Signal 1 from import graph>
- <Signal 2 from file structure>
- <Signal 3 from framework detection>

## Entry Points

- [[modules/<module>]] — `<path/to/entry>` (<what it boots>)

## Module Map

| Module | Role | Incoming Refs | Key Exports |
|---|---|---|---|
| [[modules/<name>]] | <layer: controller/service/repo/util/config> | <count> | `<ClassA>`, `<fnB>` |

## Architectural Hubs (Tier 1)

Files referenced by 5+ other modules — these are the load-bearing structures:

- [[modules/<name>]] (`<path>`) — <one-line purpose>

## Key Dependencies

External dependencies that shape the architecture:
- `<package>` — <what it's used for>

## Related Brain Files

- [[structure]] — Directory tree with wikilinks to every module
- [[patterns]] — Architecture patterns detected
- [[api-surface]] — Public API endpoints
- [[gotchas]] — Documented edge cases

## Key Classes

> Top classes across this repo — each is a graph node in `classes/`.

- [[classes/<role>-<ClassName>]] — `<one-line purpose>`
- [[classes/<role>-<ClassName2>]] — `<one-line purpose>`
```

### 4.3 — modules/<name>.md format

**Naming convention:** Files are named `<role>-<module>.md` — e.g. `backend-users.md`, `web-useUser.md`, `consumer-service-UserClient.md`. The role prefix is mandatory. It makes cross-repo wikilinks unambiguous in the Obsidian graph — `[[backend-users]]` is a different node from `[[web-users]]`.

Create one file per top-level module directory + one for each Tier 1 hub.

```markdown
# Module: <name>

**Repo:** <role> (`<repo-path>`)
**Path:** `<relative/path/from/repo/root>`
**Layer:** <controller | service | repository | domain | infrastructure | util | config>
**Language:** <language>

## Purpose

<One-paragraph description synthesized from: docstrings, README mentions, hub file top comments>

## Classes

> Significant classes defined in this module. Each is a node in the Obsidian graph.

| Class | Type | Description |
|---|---|---|
| [[classes/<role>-<ClassName>]] | class / interface / struct | <one-line purpose> |

## Exports

| Symbol | Type | Used by |
|---|---|---|
| `<ClassName>` | class | [[<role>-<consumer>]], [[<role>-<consumer2>]] |
| `<functionName>` | function | [[<role>-<consumer>]] |

## Imports (within repo)

- [[<role>-<dep>]] — `<what it uses from dep>`
- `<external-package>` — <what it's used for>

## Imported by (within repo)

- [[<role>-<dep>]] — `<why it needs this module>`

## Calls (cross-repo)

> Routes this module calls in other repos — backfilled by Phase 5.5 after correlation runs.
> Leave blank on first pass. Phase 5.5 will patch this section.

- `<METHOD> <path>` → [[<other-role>-<module>]] (`<other-repo>/src/routes/file.ts:<line>`)

## Called By (cross-repo)

> Modules in other repos that call routes defined here — backfilled by Phase 5.5.
> Leave blank on first pass. Phase 5.5 will patch this section.

- [[<caller-role>-<module>]] (`<caller-repo>/src/hooks/file.ts:<line>`) → `<METHOD> <path>`

## Documented Edge Cases

> From test file: `<test name that describes edge case>`

- `<test string describing edge case 1>`
- `<test string describing edge case 2>`

## TODO / FIXME

> Extracted from source comments

- `<file:line>` — `<comment text>`
```

**Important:** The `## Calls (cross-repo)` and `## Called By (cross-repo)` sections are written as empty stubs during Phase 4. Phase 5.5 Step 6 fills them in after correlation is complete. Do NOT attempt to fill them during Phase 4 — the correlation data doesn't exist yet.

### 4.3a — classes/<role>-<ClassName>.md format

**Driven by `/tmp/forge_scan_types_all.txt`.** For every type in that file whose source file is in `/tmp/forge_scan_tier1.txt` or `/tmp/forge_scan_tier2.txt`, create one class file. Do NOT rely solely on in-context memory — the grep inventory is ground truth.

File path: `~/forge/brain/products/<slug>/codebase/classes/<role>-<ClassName>.md`

The `classes/` directory is what makes the Obsidian graph show class-level nodes connected to modules, to each other (via extends/implements), and to the directory structure. Without these files, the graph is a flat list of module nodes.

```markdown
# <TypeKind>: <ClassName>

> TypeKind: Class | Interface | Struct | Data Class | Sealed Class | Object | Enum | Trait | Protocol | Abstract Class

**Module:** [[modules/<role>-<module>]]
**File:** `<relative/path/from/repo/root>`
**Language:** <Java | Kotlin | Go | TypeScript | Python | Dart | Rust | ...>
**Layer:** <controller | service | repository | domain | entity | util | config | widget | bloc>
**Annotation / Decorator:** `@Service` / `@Injectable()` / `@Entity` / none

## Purpose

<One-sentence description — from the class docstring, comment block above the class, or synthesized from constructor params and method names>

## Constructor / Initialization

| Language | What to write |
|---|---|
| Java / Kotlin | `ClassName(Type param1, Type param2)` |
| Kotlin data class | `ClassName(val param1: Type, var param2: Type)` — constructor IS the property list |
| Go | `NewTypeName(dep1 *Dep1, dep2 *Dep2) *TypeName` (the `NewX` function, not a constructor keyword) |
| TypeScript | `constructor(private svc: ServiceType, readonly config: Config)` |
| Python | `__init__(self, param1: Type, param2: Type = default)` |

`<constructor signature for this class>`

## Methods

> For **Go**: methods come from `/tmp/forge_scan_methods_go.txt` — grep for `(* <TypeName>)` or `( <TypeName>)` receiver. They are NOT inside the struct definition.
> For all others: list public/exported methods only.

| Method | Signature | Notes |
|---|---|---|
| `<methodName>` | `<methodName>(<params>): <ReturnType>` | async / suspend / override |

## Properties / Fields

> For **Kotlin data class**: constructor params are the properties — copy from constructor.
> For **Go struct**: list fields from inside `type X struct { ... }` block.
> For **Java**: `private`/`protected` fields from class body.

| Property | Type | Notes |
|---|---|---|
| `<propName>` | `<type>` | readonly / lateinit / inject / json:"..." |

## Relationships

- **Extends:** [[classes/<role>-<ParentClass>]] *(omit line if none)*
- **Implements:** [[classes/<role>-<InterfaceName>]], [[classes/<role>-<InterfaceName2>]] *(omit if none)*
- **Embeds (Go):** [[classes/<role>-<EmbeddedStruct>]] *(Go composition — not inheritance)*
- **Sealed variants (Kotlin):** [[classes/<role>-<Subclass1>]], [[classes/<role>-<Subclass2>]] *(omit if not sealed)*
- **Used by:** [[modules/<role>-<consumer>]], [[modules/<role>-<consumer2>]]
- **Depends on:** [[classes/<role>-<Dependency>]] *(classes injected or composed)*

## Location in Structure

[[structure]] → `<directory/path>/` → [[modules/<role>-<module>]] → `<ClassName>`
```

**Skip a class if** it is a pure generated file (e.g. `*Generated.java`, `*_pb2.py`, Kotlin `*Binding` from Android View Binding) or a test-only class. Everything else gets a file — even simple data classes, because they are still graph nodes that other classes reference.

### 4.3b — structure.md format

`structure.md` is the directory-tree backbone of the Obsidian graph. Every module and class node links back to it, giving the mindmap its hierarchy. Without this file the graph is a flat soup of nodes with no spatial structure.

File path: `~/forge/brain/products/<slug>/codebase/structure.md`

```markdown
# File Structure: <repo-name> (<role>)

> Directory hierarchy with links to module files. This is the map — navigate from here to any module or class.

## Repository Tree

> Written as a nested list — NOT a code block. Obsidian does not parse `[[wikilinks]]` inside fenced code blocks, so a code block tree produces zero graph edges.

- `<repo-name>/`
  - `<dir1>/` → [[modules/<role>-<dir1>]]
    - `<subdir1>/` → [[modules/<role>-<subdir1>]]
      - `<ClassA>.ts` → [[classes/<role>-<ClassA>]]
      - `<ClassB>.ts` → [[classes/<role>-<ClassB>]]
    - `<file>.ts` → [[modules/<role>-<stem>]]
  - `<dir2>/` → [[modules/<role>-<dir2>]]
    - `<file>.ts` → [[modules/<role>-<stem>]]
  - `package.json` / `go.mod` / `pom.xml`
  - `README.md`

> Omit: `node_modules/`, `dist/`, `build/`, `__pycache__/`, `.git/`, test fixtures

## Directory Index

| Directory | Purpose | Modules |
|---|---|---|
| `<dir1>/` | <what this layer contains — e.g. "HTTP controllers"> | [[modules/<role>-<m1>]], [[modules/<role>-<m2>]] |
| `<dir2>/` | <e.g. "Business logic services"> | [[modules/<role>-<m3>]] |
| `<dir3>/` | <e.g. "Database access layer"> | [[modules/<role>-<m4>]] |

## Entry Points

| File | Module | Boots |
|---|---|---|
| `<path/to/main.ts>` | [[modules/<role>-<stem>]] | HTTP server on port <N> |
| `<path/to/worker.ts>` | [[modules/<role>-<stem>]] | Background job runner |

## Related

- [[index]] — Module map overview
- [[patterns]] — Architecture patterns
```

**How to write the tree:** Use the file inventory from Phase 1 (`/tmp/forge_scan_source_files.txt`) grouped by directory. Do not read additional files. Reconstruct the directory structure from the paths alone — you already have them.

### 4.4 — patterns.md format

```markdown
# Architecture Patterns

> Detected from import graph + framework signals. Unconfirmed patterns marked ⚠️.

## Confirmed Patterns

### <Pattern Name>
**Evidence:**
1. <Import graph signal>
2. <File structure signal>
3. <Framework/library signal>

**Implications for development:**
- <What this means for how to add a feature>
- <What this means for where to put new files>
- <What this means for testing strategy>

## Likely Patterns ⚠️

### <Pattern Name> (unconfirmed)
**Signals:** <why it might be this pattern>
**Counter-signals:** <why it might not be>
**Recommendation:** Confirm before planning new features — run `/scan` after reading 3-5 hub files fully.

## Anti-Patterns Detected

> These are problems, not features.

- **<Anti-pattern>** at `<location>` — <what makes it an anti-pattern>

## Related

- [[index]] — Module map
- [[modules/<relevant-hub>]] — Core structural file
```

### 4.5 — api-surface.md format

```markdown
# API Surface: <repo-name>

> Auto-extracted from route decorators and router patterns. Verify against actual implementation.

## REST Endpoints

| Method | Path | File | Handler |
|---|---|---|---|
| `GET` | `/api/users` | `<file:line>` | `<HandlerName>` |

## Event Schemas (if applicable)

| Event | Producer | Consumer | Schema |
|---|---|---|---|
| `<event.name>` | [[modules/<producer>]] | [[modules/<consumer>]] | `<type/shape>` |

## Exported SDK / Library Surface (if applicable)

| Symbol | Type | Description |
|---|---|---|
| `<name>` | function/class | <one-line description> |

## Related

- [[patterns]] — Architecture context
- [[modules/<main-router>]] — Main routing hub
```

### 4.6 — gotchas.md format

```markdown
# Codebase Gotchas

> Extracted from: test names, TODO/FIXME comments, HACK comments, documented edge cases.
> These are things that will bite you if you don't know about them.

## Edge Cases (from test names)

- `<test string>` — [[modules/<module>]]
- `<test string>` — [[modules/<module>]]

## Known Issues (from TODO/FIXME)

| Location | Severity | Note |
|---|---|---|
| `<file:line>` | TODO | `<comment>` |
| `<file:line>` | FIXME | `<comment>` |
| `<file:line>` | HACK | `<comment>` |

## Architectural Warnings

> Patterns that will cause bugs if misunderstood:

- **<Warning>** — `<where>` — <why it matters>

## Related

- [[patterns]] — Architecture patterns
- [[index]] — Module map
```

### 4.7 — Diff against prior scan (re-scan only)

When a `SCAN.json` already existed before this run (i.e. this is a re-scan, not first scan), produce a diff summary before overwriting:

```bash
# Read prior scan metadata
PRIOR_FILES=$(cat ~/forge/brain/products/<slug>/codebase/SCAN.json 2>/dev/null | grep '"source_files"' | grep -o '[0-9]*')
PRIOR_COMMIT=$(cat ~/forge/brain/products/<slug>/codebase/SCAN.json 2>/dev/null | grep '"commit"' | grep -o '"[a-f0-9]*"' | tr -d '"')
PRIOR_DATE=$(cat ~/forge/brain/products/<slug>/codebase/SCAN.json 2>/dev/null | grep '"scanned_at"' | grep -o '"[^"]*"' | tail -1 | tr -d '"')

CURRENT_FILES=$(wc -l < /tmp/forge_scan_source_files.txt)
CURRENT_COMMIT=$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Compare module counts
PRIOR_MODULES=$(ls ~/forge/brain/products/<slug>/codebase/modules/ 2>/dev/null | wc -l)

echo "=== Scan Diff ==="
echo "Prior scan: $PRIOR_DATE (commit $PRIOR_COMMIT, $PRIOR_FILES files)"
echo "This scan:  $(date -u +"%Y-%m-%dT%H:%M:%SZ") (commit $CURRENT_COMMIT, $CURRENT_FILES files)"
echo ""
echo "File count change: $((CURRENT_FILES - PRIOR_FILES)) files ($([ $((CURRENT_FILES - PRIOR_FILES)) -gt 0 ] && echo '+')$((CURRENT_FILES - PRIOR_FILES)))"

# Git log between prior and current commit for change summary
if [ "$PRIOR_COMMIT" != "unknown" ] && [ "$PRIOR_COMMIT" != "$CURRENT_COMMIT" ]; then
  echo ""
  echo "Commits since prior scan:"
  git -C "$REPO" log --oneline "$PRIOR_COMMIT".."$CURRENT_COMMIT" 2>/dev/null | head -10
fi
```

Write diff summary into `index.md` under a `## Changes Since Last Scan` section:

```markdown
## Changes Since Last Scan

> Prior scan: <prior-date> (commit <prior-sha>)
> This scan: <current-date> (commit <current-sha>)

- File count: <prior> → <current> (<delta>)
- Commits included: <N commits since prior scan>

### New Modules (files with 0 prior refs now appearing as hubs)
- `<new-module>` — first seen in this scan

### Removed Hubs (files that dropped below threshold)
- `<removed-module>` — no longer referenced by 3+ files

### API Surface Changes
- <N> new endpoints detected
- <N> endpoints no longer found (may have been removed or renamed)
```

This section is overwritten on every re-scan. First scans do not include this section.

### 4.8 — Commit after each project role

```bash
cd ~/forge/brain
# Verify expected output files were created
echo "=== Output summary ==="
echo "Modules: $(ls products/<slug>/codebase/modules/ 2>/dev/null | wc -l) files"
echo "Classes: $(ls products/<slug>/codebase/classes/ 2>/dev/null | wc -l) files"
echo "Structure: $([ -f products/<slug>/codebase/structure.md ] && echo 'present' || echo 'MISSING')"
echo "API surface: $([ -f products/<slug>/codebase/api-surface.md ] && echo 'present' || echo 'MISSING')"

git add products/<slug>/codebase/
git commit -m "scan: map <slug>/<role> codebase — <file-count> files, <hub-count> hubs, <class-count> classes"
```

**If `classes/` has 0 files** and hub reads included class-bearing code: do NOT skip. Go back and extract at least the top 3-5 classes from the Tier 1 hubs. The `classes/` directory is mandatory for a meaningful Obsidian graph — flat module-only output does not produce a navigable mindmap.

**If `structure.md` is missing:** do NOT proceed to Phase 5 or commit. Write it now using the file paths already in `/tmp/forge_scan_source_files.txt` — no additional reads needed.

---

## Phase 5: Cross-Repo Relationship Layer (Multi-Repo Workspaces Only)

**Skip if workspace has only one repo.** Run after all individual repo scans are complete.

This phase identifies the architectural seams between repos — the contracts, shared types, and communication patterns that cross repo boundaries. This is the most valuable architectural data for multi-repo planning and the data most likely to be missing without an explicit scan phase.

### 5.1 — API call detection (any repo → any repo)

Find where any repo calls another service's HTTP API. **Scan ALL repos** — not just web/mobile. Microservices call other microservices. A Java consumer service calls a Node backend. A Go service calls another Go service.

```bash
# Scan ALL repos for outbound HTTP calls — every language, every client library
for repo in <all-repos>; do
  echo "=== API calls from: $(basename $repo) ==="

  # TypeScript / JavaScript (fetch, axios, got, superagent, ky, needle)
  grep -rn \
    "fetch(\|axios\.\|got\.\|superagent\.\|ky\.\|needle\." \
    "$repo" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
    | grep -v node_modules | grep -v test | grep -v spec | head -30

  # Java (RestTemplate, WebClient, OkHttp, HttpClient, Feign interfaces)
  grep -rn \
    "restTemplate\.\|webClient\.\|HttpClient\.\|OkHttpClient\.\|\.exchange(\|\.getForObject(\|\.postForObject(\|@FeignClient" \
    "$repo" --include="*.java" \
    | grep -v test | grep -v Test | head -20

  # Kotlin (Ktor client, Fuel, Retrofit annotations on consumer interfaces)
  grep -rn \
    "client\.get\|client\.post\|Fuel\.get\|Fuel\.post\|@GET(\|@POST(\|@PUT(\|@DELETE(" \
    "$repo" --include="*.kt" \
    | grep -v test | head -20

  # Python (requests, httpx, aiohttp)
  grep -rn \
    "requests\.get\|requests\.post\|requests\.put\|requests\.delete\|httpx\.get\|httpx\.post\|aiohttp\." \
    "$repo" --include="*.py" \
    | grep -v test | grep -v _test | head -20

  # Go (net/http, resty, go-resty)
  grep -rn \
    "http\.Get(\|http\.Post(\|http\.NewRequest(\|resty\.\|client\.R()" \
    "$repo" --include="*.go" \
    | grep -v _test.go | head -20

  # Dart / Flutter (Dio, http package)
  grep -rn \
    "dio\.get\|dio\.post\|dio\.put\|dio\.delete\|http\.get\|http\.post" \
    "$repo" --include="*.dart" \
    | grep -v test | head -20

  # Ruby (Net::HTTP, HTTParty, Faraday, RestClient)
  grep -rn \
    "Net::HTTP\.\|HTTParty\.\|Faraday\.new\|RestClient\.\|\.get(\|\.post(\|\.put(\|\.delete(" \
    "$repo" --include="*.rb" \
    | grep -v test | grep -v spec | head -20

  # Swift (URLSession, Alamofire)
  grep -rn \
    "URLSession\.\|AF\.\|Alamofire\.\|dataTask(with\|URLRequest(" \
    "$repo" --include="*.swift" \
    | grep -v test | grep -v Test | head -20

  # tRPC (client.procedure.query / client.procedure.mutate patterns)
  grep -rn \
    "trpc\.\|createTRPCClient\|\.query(\|\.mutate(\|\.useQuery(\|\.useMutation(" \
    "$repo" --include="*.ts" --include="*.tsx" \
    | grep -v node_modules | grep -v test | grep -v spec | head -20

  # gRPC stub calls (generated client method calls)
  grep -rn \
    "Stub(\|\.stub\.\|grpc\.unary\|grpc\.invoke\|ServicePromiseClient\|\.call(" \
    "$repo" --include="*.ts" --include="*.js" --include="*.java" --include="*.kt" --include="*.go" \
    | grep -v node_modules | grep -v test | grep -v Test | head -20
done
```

> **tRPC / gRPC note:** These protocols don't emit plain HTTP path strings. tRPC call sites reference procedure names (e.g. `trpc.user.getById.query()`), not URLs. gRPC call sites reference stub method names. For these, the route correlation in Phase 5.5 cannot use URL matching — instead, note the call sites in `cross-repo.md` under a separate section `## tRPC / gRPC Call Sites` with the procedure/method names. Match them manually against the router/proto definition files.

### 5.2 — Shared type / schema detection

Find types, interfaces, or schemas that appear in multiple repos (shared contracts):

```bash
# Extract exported interface/type names from each repo
for repo in <all-repos>; do
  echo "=== Types from: $repo ==="
  grep -rhn \
    "^export interface \|^export type \|^export class \|^type \|^interface " \
    "$repo" \
    --include="*.ts" \
    | sed 's/^[0-9]*://' \
    | grep -v node_modules
done > /tmp/forge_scan_all_types.txt

# Find type names that appear in 2+ repos (shared types)
sort /tmp/forge_scan_all_types.txt | uniq -d | head -30
```

### 5.3 — Environment variable cross-reference

Environment variables are often the contract between repos (service URLs, API keys, feature flags):

```bash
for repo in <all-repos>; do
  echo "=== Env vars from: $repo ==="
  grep -rhn \
    "process\.env\.\|os\.environ\.\|os\.Getenv\|System\.getenv\|dotenv" \
    "$repo" \
    --include="*.ts" --include="*.js" --include="*.py" --include="*.go" --include="*.java" --include="*.kt" \
    | grep -v node_modules | grep -v test \
    | sed 's/.*process\.env\.\([A-Z_]*\).*/\1/' \
    | sort | uniq
done
```

### 5.4 — Event/message bus cross-reference

Find event producers and consumers across repos:

```bash
# Producer patterns
for repo in <all-repos>; do
  echo "=== Events produced by: $repo ==="
  grep -rhn \
    "publish(\|produce(\|emit(\|sendMessage\|kafkaProducer\|channel\.send\|rabbitMQ\.publish" \
    "$repo" \
    --include="*.ts" --include="*.py" --include="*.go" --include="*.java" --include="*.kt" \
    | grep -v node_modules | grep -v test | head -20
done

# Consumer patterns
for repo in <all-repos>; do
  echo "=== Events consumed by: $repo ==="
  grep -rhn \
    "subscribe(\|consume(\|\.on(\|kafkaConsumer\|channel\.receive\|rabbitMQ\.consume\|@KafkaListener" \
    "$repo" \
    --include="*.ts" --include="*.py" --include="*.go" --include="*.java" --include="*.kt" \
    | grep -v node_modules | grep -v test | head -20
done
```

### 5.5 — Route-to-callsite correlation (backend route ↔ any-repo call)

This is the join between Phase 3.5 (backend route table) and Phase 5.1 (call sites across ALL repos). It produces the most actionable cross-repo data: which call site maps to which backend route, and which calls have no matching route (broken contracts).

**Scope: ALL repos, not just web/mobile.** Microservices call other services. A Java consumer may call a Node backend. A backend service may call another backend microservice. Every repo is a potential API consumer.

**Step 1 — Extract URL strings from ALL repo call sites (language-aware):**

```bash
# ── TypeScript / JavaScript / Node (fetch, axios, got, superagent) ──────────
for repo in <all-repos>; do
  repo_name=$(basename "$repo")
  grep -rn \
    "fetch(\|axios\.\|got\.\|superagent\.\|request\.\|needle\.\|ky\." \
    "$repo" \
    --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
    | grep -v node_modules | grep -v test | grep -v spec \
    | grep -E "['\`\"]/" \
    | sed "s|$repo/||" \
    | sed "s|^|$repo_name\t|"
done > /tmp/forge_scan_js_calls.txt

# ── Java (RestTemplate, WebClient, OkHttp, HttpClient, Feign annotations) ───
for repo in <all-repos>; do
  repo_name=$(basename "$repo")
  # RestTemplate / WebClient URL string literals
  grep -rn \
    "restTemplate\.\|webClient\.\|HttpClient\.\|OkHttpClient\.\|\.exchange(\|\.getForObject(\|\.postForObject(" \
    "$repo" --include="*.java" \
    | grep -v test | grep -v Test \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|"

  # Feign client interface @GetMapping/@PostMapping etc. (these ARE the route definitions)
  grep -rn \
    "@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping\|@PatchMapping\|@RequestMapping" \
    "$repo" --include="*.java" \
    | grep -i "feign\|client\|Client" \
    | sed "s|$repo/||" | sed "s|^|$repo_name/feign\t|"
done >> /tmp/forge_scan_java_calls.txt

# ── Kotlin (Ktor, Fuel, Retrofit annotations) ────────────────────────────────
for repo in <all-repos>; do
  repo_name=$(basename "$repo")
  grep -rn \
    "client\.get(\|client\.post(\|client\.put(\|client\.delete(\|Fuel\.get(\|Fuel\.post(\|\.get<\|\.post<" \
    "$repo" --include="*.kt" \
    | grep -v test | grep -v Test \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|"

  # Retrofit annotations on interfaces
  grep -rn \
    "@GET(\|@POST(\|@PUT(\|@DELETE(\|@PATCH(" \
    "$repo" --include="*.kt" \
    | grep -v test \
    | sed "s|$repo/||" | sed "s|^|$repo_name/retrofit\t|"
done >> /tmp/forge_scan_kotlin_calls.txt

# ── Python (requests, httpx, aiohttp) ────────────────────────────────────────
for repo in <all-repos>; do
  repo_name=$(basename "$repo")
  grep -rn \
    "requests\.get(\|requests\.post(\|requests\.put(\|requests\.delete(\|httpx\.get(\|httpx\.post(\|aiohttp\." \
    "$repo" --include="*.py" \
    | grep -v test | grep -v "_test" \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|"
done >> /tmp/forge_scan_python_calls.txt

# ── Go (http.Get, http.Post, http.NewRequest, resty, go-resty) ───────────────
for repo in <all-repos>; do
  repo_name=$(basename "$repo")
  grep -rn \
    "http\.Get(\|http\.Post(\|http\.NewRequest(\|resty\.\|client\.R()\.Get(" \
    "$repo" --include="*.go" \
    | grep -v "_test.go" \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|"
done >> /tmp/forge_scan_go_calls.txt

# ── Dart/Flutter (Dio, http package) ─────────────────────────────────────────
for repo in <all-repos>; do
  repo_name=$(basename "$repo")
  grep -rn \
    "dio\.get(\|dio\.post(\|dio\.put(\|dio\.delete(\|http\.get(\|http\.post(" \
    "$repo" --include="*.dart" \
    | grep -v test \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|"
done >> /tmp/forge_scan_dart_calls.txt

cat /tmp/forge_scan_js_calls.txt /tmp/forge_scan_java_calls.txt \
    /tmp/forge_scan_kotlin_calls.txt /tmp/forge_scan_python_calls.txt \
    /tmp/forge_scan_go_calls.txt /tmp/forge_scan_dart_calls.txt \
    > /tmp/forge_scan_all_callsites.txt

echo "Total call sites across all repos and languages: $(wc -l < /tmp/forge_scan_all_callsites.txt)"
```

**Step 2 — Extract literal URL strings with file:line context:**

```bash
# For each language, extract the actual URL path string from the call
# TS/JS: look for string arguments starting with '/' or config constants
grep -oE "(fetch|axios\.[a-z]+|got\.[a-z]+)\(['\`\"]([/][^'\`\"?# ]+)" \
  /tmp/forge_scan_js_calls.txt \
  | grep -oE "['\`\"][/][^'\`\"?# ]+" | tr -d "'\`\"" > /tmp/forge_scan_url_strings.txt

# Java: RestTemplate URL strings, Feign @*Mapping values
grep -oE '"(/[^"?# ]+)"' /tmp/forge_scan_java_calls.txt \
  | tr -d '"' >> /tmp/forge_scan_url_strings.txt

# Feign @GetMapping("...") annotations — these are consumer-side route declarations
grep -oE '@[A-Z][a-z]+Mapping\("([^"]+)"' /tmp/forge_scan_kotlin_calls.txt \
  | grep -oE '"[^"]+"' | tr -d '"' >> /tmp/forge_scan_url_strings.txt

# Python requests.get("..."), requests.post("...")
grep -oE "(requests|httpx)\.[a-z]+\(['\"]([/][^'\"?# ]+)" \
  /tmp/forge_scan_python_calls.txt \
  | grep -oE "['\"][/][^'\"?# ]+" | tr -d "'\"" >> /tmp/forge_scan_url_strings.txt

sort -u /tmp/forge_scan_url_strings.txt > /tmp/forge_scan_fe_urls.txt
echo "Unique URL paths extracted: $(wc -l < /tmp/forge_scan_fe_urls.txt)"
cat /tmp/forge_scan_fe_urls.txt

# ── Dynamic URLs (template literals / variable concatenation) — flag for manual review ──
# These cannot be statically extracted — the path is built at runtime from env vars or state
for repo in <all-repos>; do
  repo_name=$(basename "$repo")
  # Template literals: fetch(`${BASE_URL}/path`) or axios.get(`${API_URL}/users`)
  grep -rn \
    "fetch(\`\${\\|axios\.[a-z]*(\`\${\|got\.[a-z]*(\`\${\|requests\.[a-z]*(f\"\|httpx\.[a-z]*(f\"" \
    "$repo" \
    --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" \
    | grep -v node_modules | grep -v test | grep -v spec \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|"
  # Concatenation: baseURL + '/path' or API_BASE_URL + endpoint
  grep -rn \
    "baseURL\s*+\|API_BASE_URL\s*+\|API_URL\s*+\|BASE_URL\s*+" \
    "$repo" \
    --include="*.ts" --include="*.tsx" --include="*.js" \
    | grep -v node_modules | grep -v test \
    | sed "s|$repo/||" | sed "s|^|$repo_name\t|"
done > /tmp/forge_scan_dynamic_urls.txt

if [ -s /tmp/forge_scan_dynamic_urls.txt ]; then
  echo ""
  echo "⚠️  Dynamic URLs detected — path not extractable by grep (template literals / variable concatenation):"
  wc -l < /tmp/forge_scan_dynamic_urls.txt
  echo "These call sites will NOT appear in URL correlation. Document in cross-repo.md under '## Dynamic URL Call Sites (Manual Review Required)'"
fi
```

**Step 3 — Normalize backend route table for matching:**

```bash
# /tmp/forge_scan_api_routes.txt was built in Phase 3.5
# Normalize :param placeholders to a regex-friendly pattern for matching
# Format each line: METHOD  /route/path  file:line  handler
grep -E "@Get|@Post|@Put|@Delete|@Patch|router\.(get|post|put|delete|patch)|app\.(get|post|put|delete|patch)|r\.(GET|POST|PUT|DELETE)" \
  /tmp/forge_scan_api_routes.txt \
  | sed \
    -e "s/.*@Get('\([^']*\)').*/GET\t\1/" \
    -e "s/.*@Post('\([^']*\)').*/POST\t\1/" \
    -e "s/.*@Put('\([^']*\)').*/PUT\t\1/" \
    -e "s/.*@Delete('\([^']*\)').*/DELETE\t\1/" \
    -e "s/.*@Patch('\([^']*\)').*/PATCH\t\1/" \
    -e "s/.*router\.get('\([^']*\)'.*/GET\t\1/" \
    -e "s/.*router\.post('\([^']*\)'.*/POST\t\1/" \
    -e "s/.*app\.get('\([^']*\)'.*/GET\t\1/" \
    -e "s/.*app\.post('\([^']*\)'.*/POST\t\1/" \
    -e "s/.*@GetMapping(\"\([^\"]*\)\").*/GET\t\1/" \
    -e "s/.*@PostMapping(\"\([^\"]*\)\").*/POST\t\1/" \
    -e "s/.*@RequestMapping.*\"\([^\"]*\)\".*/MULTI\t\1/" \
  > /tmp/forge_scan_be_routes_normalized.txt

echo "Backend routes normalized: $(wc -l < /tmp/forge_scan_be_routes_normalized.txt)"
cat /tmp/forge_scan_be_routes_normalized.txt
```

**Step 4 — Join: match each frontend URL against backend route table:**

This step is done by the model (not bash) — bash regex matching for `:param` normalization is brittle. Read both files and produce the correlation:

For each URL in `/tmp/forge_scan_fe_urls.txt`:
1. Strip query strings (`?key=val`) and hash fragments
2. Try exact match against backend routes
3. If no exact match, try pattern match — replace `:param`, `{param}`, `[param]` with `*` wildcard and match
4. Record: `MATCHED` (exact or pattern), `UNMATCHED` (no backend route found), or `AMBIGUOUS` (matches 2+ routes)

Flag these specifically:
- **UNMATCHED** frontend URLs → broken contract (frontend calls a route that doesn't exist in backend)
- Routes in backend with zero frontend call sites → orphan routes (may be internal, may be dead code)

**Step 5 — Output correlation results to temp file:**

Write `/tmp/forge_scan_route_correlation.txt` with this structure (tab-separated):
```
STATUS  CALLER_REPO  CALLER_FILE  CALLER_LINE  CALLER_MODULE  URL  MATCH_TYPE  BE_REPO  BE_FILE  BE_LINE  BE_MODULE  BE_ROUTE  BE_METHOD
MATCHED  web  src/hooks/useUser.ts  34  web-useUser  /api/users/profile  exact  backend  src/routes/users.ts  18  backend-users  /api/users/profile  GET
MATCHED  app  lib/api/auth.dart  12  app-authClient  /api/auth/login  exact  backend  src/routes/auth.ts  9  backend-auth  /api/auth/login  POST
MATCHED  consumer-service  src/client/UserClient.java  55  consumer-service-UserClient  /api/users/profile  pattern  core-backend  src/routes/users.ts  18  core-backend-users  /api/users/:id  GET
UNMATCHED  web  src/utils/legacy.ts  88  web-legacy  /api/v1/feed  -  -  -  -  -  -  -
ORPHAN  -  -  -  -  -  -  backend  src/routes/admin.ts  7  backend-admin  /api/admin/metrics  GET
```

**Module name derivation rule:** `<role>-<stem>` where stem = filename without extension, lowercased.

**Collision rule:** Common filenames (`index`, `main`, `app`, `server`, `utils`, `helpers`, `types`, `config`, `client`, `handler`, `middleware`) appear in many directories within the same repo and will collide. For these names, prefix with the immediate parent directory: `<role>-<parent>-<stem>`.

Examples:
- `web/src/hooks/useUser.ts` → `web-useUser` (unique name, no prefix needed)
- `backend/src/routes/users.ts` → `backend-users` (unique name, no prefix needed)
- `backend/src/auth/index.ts` → `backend-auth-index` (collision-prone name, parent included)
- `backend/src/middleware/index.ts` → `backend-middleware-index` (collision-prone, different parent)
- `consumer-service/src/client/UserClient.java` → `consumer-service-UserClient` (unique name)

**Detection:** Before writing a module file, check if the name already exists in `modules/`. If it does, apply the parent-directory prefix to both the existing and new file to disambiguate.

---

**Step 6 — Patch module files with cross-repo wikilinks (CRITICAL — this creates the Obsidian graph edges):**

For every `MATCHED` row in `/tmp/forge_scan_route_correlation.txt`, patch two brain files:

**6a — Patch the CALLER module file** (`~/forge/brain/products/<slug>/codebase/modules/<CALLER_MODULE>.md`):

Find the `## Calls (cross-repo)` section (written as empty stub in Phase 4.3) and append:
```markdown
- `<BE_METHOD> <BE_ROUTE>` → [[<BE_MODULE>]] (`<BE_REPO>/<BE_FILE>:<BE_LINE>`)
```

Example — patching `modules/web-useUser.md`:
```markdown
## Calls (cross-repo)

- `GET /api/users/profile` → [[backend-users]] (`backend/src/routes/users.ts:18`)
- `PUT /api/users/profile` → [[backend-users]] (`backend/src/routes/users.ts:31`)
```

**6b — Patch the PROVIDER module file** (`~/forge/brain/products/<slug>/codebase/modules/<BE_MODULE>.md`):

Find the `## Called By (cross-repo)` section and append:
```markdown
- [[<CALLER_MODULE>]] (`<CALLER_REPO>/<CALLER_FILE>:<CALLER_LINE>`) → `<BE_METHOD> <BE_ROUTE>`
```

Example — patching `modules/backend-users.md`:
```markdown
## Called By (cross-repo)

- [[web-useUser]] (`web/src/hooks/useUser.ts:34`) → `GET /api/users/profile`
- [[app-authClient]] (`app/lib/api/auth.dart:89`) → `GET /api/users/profile`
- [[consumer-service-UserClient]] (`consumer-service/src/client/UserClient.java:55`) → `GET /api/users/:id`
```

**6c — Handle UNMATCHED rows** — patch only the caller file, note the broken contract:

In `modules/<CALLER_MODULE>.md` → `## Calls (cross-repo)`:
```markdown
- `GET /api/v1/feed` → ❌ NO MATCHING BACKEND ROUTE FOUND — broken contract
```

**6d — Handle ORPHAN rows** — patch the provider file with a note:

In `modules/<BE_MODULE>.md` → `## Called By (cross-repo)`:
```markdown
> ⚠️ No callers found in any repo scan. May be: internal/webhook-only, dead code, or called via dynamic URL construction not detectable by grep.
```

**Why this step matters:** These wikilinks create the actual graph edges in Obsidian. Without them, cross-repo.md is a flat table no one navigates. With them, clicking any module node in the graph immediately shows every cross-repo dependency — you can trace a call from a Java consumer interface to a Node route to its DB query in three clicks.

---

### 5.6 — Write cross-repo map

Write to `~/forge/brain/products/<slug>/codebase/cross-repo.md` using data from all prior Phase 5 steps. Include the route correlation table from 5.5.

```markdown
# Cross-Repo Relationships: <slug>

> Automatically extracted — verify against actual API contracts in brain/products/<slug>/contracts/

## Route Correlation Map (Caller Module → Backend Module)

> Built by joining Phase 3.5 (backend routes) with Phase 5.1 (call sites across all repos).
> Wikilinks here create the actual Obsidian graph edges — each `[[module]]` reference is a navigable node.
> `MATCHED` = confirmed route exists. `UNMATCHED` = broken contract. `ORPHAN` = backend route with no known caller.

| Status | Caller Module | Caller File:Line | Method + URL | Backend Module | Backend File:Line |
|---|---|---|---|---|---|
| ✅ MATCHED | [[web-useUser]] | `web/src/hooks/useUser.ts:34` | `GET /api/users/profile` | [[backend-users]] | `backend/src/routes/users.ts:18` |
| ✅ MATCHED | [[web-OrdersPage]] | `web/src/pages/orders.tsx:67` | `GET /api/orders/:id` | [[backend-orders]] | `backend/src/routes/orders.ts:42` |
| ✅ MATCHED | [[app-authClient]] | `app/lib/api/auth.dart:12` | `POST /api/auth/login` | [[backend-auth]] | `backend/src/routes/auth.ts:9` |
| ✅ MATCHED | [[consumer-service-UserClient]] | `consumer-service/src/client/UserClient.java:55` | `GET /api/users/:id` | [[core-backend-users]] | `core-backend/src/routes/users.ts:18` |
| ❌ UNMATCHED | [[web-legacy]] | `web/src/utils/legacy.ts:88` | `GET /api/v1/feed` | — | — |
| 🔍 ORPHAN | — | — | `GET /api/admin/metrics` | [[backend-admin]] | `backend/src/routes/admin.ts:7` |

### Broken Contracts (UNMATCHED — action required)

> These frontend calls have no matching backend route. Likely causes: route was renamed, removed, or never implemented.

- `web/src/utils/legacy.ts:88` → `GET /api/v1/feed` — no backend route matches. Check if renamed to `/api/v2/feed`.

### Orphan Routes (no known frontend caller)

> These backend routes have no detected frontend call site. May be internal, webhook-only, or dead code.

- `backend/src/routes/admin.ts:7` → `GET /api/admin/metrics` — no caller found in web or app repos.

---

## API Calls (Consumer → Provider)

> Covers ALL repos — microservice-to-microservice calls included.

| From | Language/Client | To | Pattern | Matched Routes | Unmatched |
|---|---|---|---|---|---|
| [[web]] | TypeScript / axios | [[backend]] | REST HTTP | 22/23 matched | 1 broken (`/api/v1/feed`) |
| [[app]] | Dart / Dio | [[backend]] | REST HTTP | 18/18 matched | 0 broken |
| [[consumer-service]] | Java / RestTemplate | [[core-backend]] | REST HTTP | 14/15 matched | 1 broken (`/api/v1/legacy`) |
| [[consumer-service]] | Java / Feign | [[core-backend]] | REST HTTP | 6/6 matched | 0 broken |
| [[order-service]] | Go / http.Get | [[inventory-service]] | REST HTTP | 4/4 matched | 0 broken |

## Shared Types

Types that appear in 2+ repos — these are implicit contracts. Each wikilink is a navigable module node.

| Type Name | Defined In | Used By |
|---|---|---|
| `User` | [[backend-types]] | [[web-useUser]], [[web-UserProfile]], [[app-authClient]] |
| `OrderStatus` | [[shared-types]] | [[backend-orders]], [[web-OrdersPage]], [[app-orderList]] |

> ⚠️ Shared types not in a shared package are a fragility risk — consider extracting to shared/

## Environment Variable Contracts

Variables that cross repo boundaries:

| Variable | Set By | Read By | Purpose |
|---|---|---|---|
| `API_BASE_URL` | infra/env | [[web]], [[app]] | Backend API root |
| `JWT_SECRET` | infra/env | [[backend]] | Auth token signing |

## Event Bus (Producer → Consumer)

| Event | Produced By | Consumed By | Channel |
|---|---|---|---|
| `order.created` | [[backend]] | [[backend]]/notifications | Kafka |

## Integration Risk Areas

> Patterns that are likely to cause cross-repo bugs:

- **Broken contracts** — `<N>` frontend call sites have no matching backend route. See "Broken Contracts" above.
- **Implicit type sharing** — `<type>` in [[repo-a]] and [[repo-b]] are different structs named the same. Risk: silent deserialization failure.
- **Direct URL hardcoding** — `<N>` call sites use hardcoded backend URL instead of `API_BASE_URL`. Risk: breaks on env change.
- **Missing consumer** — Event `<event>` is produced but no consumer found in any repo. Risk: silent data loss.
- **Orphan routes** — `<N>` backend routes have no frontend caller. Risk: dead code or undocumented internal API.

## Summary Stats

> Quick health check for cross-repo integration:

- Frontend call sites: <N total>
- Matched routes: <N> (<pct>%)
- Broken contracts (UNMATCHED): <N> ⚠️
- Orphan backend routes: <N>
- Shared types (implicit contracts): <N>
- Event producers: <N> | consumers: <N>

## Related

- [[index]] — Per-repo module maps
- [[patterns]] — Architecture patterns detected per repo
- [[api-surface]] — Full backend API surface
```

Commit after cross-repo layer:
```bash
cd ~/forge/brain
git add products/<slug>/codebase/cross-repo.md
git commit -m "scan: cross-repo relationships for <slug> — <N> routes correlated, <N> broken contracts, <N> shared types"
```

---

## Decision Trees

### Decision Tree 1: What to read for a given file

```
Is the file a README / ARCHITECTURE / CONTRIBUTING / ADR?
  → YES: Read fully (always)
  → NO:
      Is reference count ≥ 5?
        → YES (Tier 1 hub): Read top 150 lines
        → NO:
            Is reference count 3-4?
              → YES (Tier 2 hub): Read top 80 lines
              → NO (leaf file):
                  Is it a test file?
                    → YES: Extract test name strings only (grep, no Read)
                    → NO: DO NOT READ — derive from import graph only
```

### Decision Tree 2: Pattern classification

```
Does import graph show ≥3 services importing a central "container" or "di" module?
  → YES: Dependency Injection / IoC pattern

Does every feature directory contain (controller + service + repository)?
  → YES: Layered architecture (controller → service → repository)

Does import graph show no cross-feature imports (features only import shared/)?
  → YES: Modular monolith / vertical slice

Do all routes live in one file and call functions from many modules?
  → YES: Centralized routing (common in Go, Flask)

Does the file structure have one directory per domain entity?
  → YES (and DI found): Domain-Driven Design signal

None of the above match cleanly?
  → Label as: "unclassified — recommend manual architecture review"
```

### Decision Tree 3: When a scan is stale

```
Does codebase/SCAN.json exist?
  → NO: Run full scan

Does SCAN.json exist?
  → YES: Read last-scanned timestamp
    Is it older than 7 days?
      → YES: Re-run Phase 1 (file inventory) to check for new files
        Are there new files (diff from SCAN.json file count)?
          → YES: Run full scan
          → NO: Scan is usable, note staleness in response

    Is it older than 30 days?
      → Always run full scan regardless of file count change
```

---

## Edge Cases

### Edge Case 1: Monorepo with 500+ files

**Symptom:** Phase 1 produces thousands of source files; hub detection takes minutes; token budget exceeded.

**Do NOT:** Read any file body during Phase 3 unless it has 10+ incoming references.

**Mitigation:**
1. Raise hub thresholds: Tier 1 = 10+ refs (not 5+), Tier 2 = 6-9 refs (not 3-4)
2. Cap file inventory at 300 files per role (take the highest-referenced files)
3. Create one module file per top-level directory only (not per subdirectory)
4. Add `"monorepo": true` flag to SCAN.json

**Escalation:** NEEDS_CONTEXT — ask which subdirectory to focus on if repo has >1000 files

---

### Edge Case 2: No test files found

**Symptom:** `/tmp/forge_scan_test_files.txt` is empty; gotchas.md has no test-derived content.

**Do NOT:** Fabricate edge cases or infer them from production code alone.

**Mitigation:**
1. Check for alternative test locations: `__tests__/`, `test/`, `spec/`, `integration/`
2. Try alternative naming patterns: `*_spec.rb`, `*IT.java`, `*Integration.java`
3. Check `package.json` test script for test directory config
4. If truly no tests: write `gotchas.md` with only TODO/FIXME content and a note: `> No test files found — edge cases may be undocumented.`

**Escalation:** DONE_WITH_CONCERNS — flag in index.md: "⚠️ No test files found"

---

### Edge Case 3: Private/generated import paths

**Symptom:** Import graph shows paths like `@app/`, `~/utils/`, `@/components/` that don't map to real directories.

**Do NOT:** Skip these imports or mark them as external dependencies.

**Mitigation:**
1. Check `tsconfig.json` paths aliases: `cat $REPO/tsconfig.json | grep -A5 '"paths"'`
2. Check `vite.config.*` or `webpack.config.*` aliases
3. Check `pyproject.toml` or `setup.py` for src-layout: `grep -E "src_dirs|packages|where" $REPO/pyproject.toml`
4. Resolve aliases before building module map — otherwise module relationships will be wrong

**Escalation:** NEEDS_CONTEXT if aliases cannot be resolved from config files

---

### Edge Case 4: Polyglot repo (multiple languages)

**Symptom:** Source file inventory finds both `.ts` and `.py` files, or `.go` and `.dart` files in the same repo.

**Do NOT:** Pick one language and ignore the other.

**Mitigation:**
1. Scan each language's import lines separately (language-specific grep patterns)
2. Create separate module maps per language layer in `modules/`
3. Look for cross-language communication points: REST calls, gRPC, shared JSON schemas
4. Document the boundary in `patterns.md` as "polyglot boundary"

**Escalation:** NEEDS_CONTEXT if cross-language calls cannot be identified from code alone

---

### Edge Case 5: No git repo in project directory

**Symptom:** `git -C $REPO rev-parse` fails; SCAN.json cannot get commit SHA.

**Do NOT:** Abort the scan.

**Mitigation:**
1. Set `"commit": "no-git"` in SCAN.json
2. Use file modification timestamps as scan version: `date -r <newest-file>`
3. Warn user in index.md: `> ⚠️ No git repository found — cannot track codebase version`

**Escalation:** DONE_WITH_CONCERNS

---

### Edge Case 6: Hub file is auto-generated

**Symptom:** Tier 1 hub file has a header like `// This file is auto-generated. Do not edit.` or `// Code generated by protoc`.

**Do NOT:** Read it as human-authored architecture. Generated files inflate hub scores.

**Mitigation:**
1. Detect generation markers: `grep -m1 "auto-generated\|DO NOT EDIT\|Code generated\|@generated" <file>`
2. Remove from hub lists: add to exclusion list
3. Note the generator in patterns.md: "API types generated by protoc from `<proto-file>`"

**Escalation:** None — handle silently, note in patterns.md

---

### Edge Case 7: Scan runs during /workspace init on a very new repo (few files)

**Symptom:** File inventory returns <10 files. Hub detection has no meaningful signal.

**Do NOT:** Produce an empty or near-empty brain scan.

**Mitigation:**
1. If <10 source files: skip Phases 1-2, read all files fully (they fit in one context window)
2. Write a `codebase/index.md` with note: `> Early-stage codebase — <10 source files. Full scan not needed.`
3. List all files in index.md as a flat inventory with one-line purpose per file
4. Set a reminder in index.md: `> Re-run /scan when codebase grows past 20 files.`

**Escalation:** None

---

## Common Pitfalls

1. **Scanning `node_modules/`** — always results in thousands of files and hub scores dominated by `index.js` files from npm packages. Exclusion pattern MUST be in every `find` command.

2. **Not resolving TypeScript path aliases** — `@/services/auth` looks like an external package but is `src/services/auth.ts`. Check `tsconfig.json` first.

3. **Treating test doubles/mocks as real modules** — `UserRepositoryMock.ts` will score high on incoming references in test files. Exclude `*.mock.*`, `*.stub.*`, `*.fake.*` from hub scoring.

4. **Writing module files for every file instead of every module** — A repo with 200 files does not need 200 module files. Group by directory/feature, not by file.

5. **Not committing SCAN.json before other brain files** — If the write fails mid-way, an incomplete scan with no metadata is worse than no scan. Commit SCAN.json first.

6. **Forgetting to clean up `/tmp/forge_scan_*.txt` temp files** — These accumulate and may cause stale data if a second scan runs in the same session without cleanup.

```bash
# Always run at end of scan
rm -f /tmp/forge_scan_*.txt
```

---

## Quick Reference Card

| Phase | What | Tools | Tokens |
|---|---|---|---|
| 1.1 | File inventory | `find`, `grep` | 0 |
| 1.2 | Module boundaries | `find`, `awk` | 0 |
| 1.3 | Import graph | `head`, `grep` | 0 |
| 1.4 | Hub scoring | `grep -rl`, `awk`, `sort` | 0 |
| 1.5 | Language fingerprint | `grep`, `cat` (package.json) | 0 |
| 2 | Hub tier assignment | `awk` | 0 |
| 3.1 | README / docs | Read (full) | Low |
| 3.2 | Tier 1 hub reads | Read (top 150 lines) | Medium |
| 3.3 | Tier 2 hub reads | Read (top 80 lines) | Low |
| 3.4 | Test name extraction | `grep` | 0 |
| 3.5 | API route extraction | `grep -rn` | 0 |
| 4 | Brain write | Write per file | Low |
| 5 | Cross-repo layer | `grep` across all repos | 0 (grep) + Low (write) |

**Token budget target:** <15K tokens per repo + <5K for cross-repo layer. If you exceed this, you skipped the exclusions.

---

## Cross-References

- **Triggers:** Automatically after [[workspace]] init; manually via `/scan <slug> <repo-path>`
- **Produces:** Brain files consumed by [[brain-read]], [[brain-recall]], [[council-multi-repo-negotiate]]
- **Required before:** [[forge-eval-gate]] on an existing codebase (agent needs module map)
- **Related skills:** [[brain-write]], [[brain-read]], [[forge-brain-layout]]

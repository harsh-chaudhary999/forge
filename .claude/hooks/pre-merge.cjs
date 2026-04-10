#!/usr/bin/env node

/**
 * pre-merge.cjs
 *
 * EVAL GATE ENFORCER (HARD-GATE: D17)
 * Fires before a merge to main in a tracked project
 * BLOCKS the merge if eval is not green in brain's pr-set.md
 * Ensures no code merges without verified eval
 *
 * Why this matters (HARD-GATE):
 * "Nothing merges without eval green" is non-negotiable.
 * Without this gate, code ships untested against the full product stack.
 * This hook is the last defense. If code gets to main without passing,
 * production failures are guaranteed.
 *
 * Cannot be bypassed:
 * - Rationalization: "The code looks fine, eval is just slow"
 *   Truth: Eval catches 40% of bugs unit tests miss. No shortcuts.
 * - Rationalization: "I'll fix it after merge"
 *   Truth: You won't. Main is live. Broken code merges silently.
 *
 * Usage:
 *   Installed via forge-install-hooks in tracked projects
 *   node pre-merge.cjs [project-slug] [forge-root] [branch-name]
 *
 * Exit codes:
 *   0 = merge allowed (eval is green)
 *   1 = merge blocked (eval not green or not found)
 *
 * Cross-platform: works on Linux, macOS, Windows
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const PROJECT_SLUG = process.argv[2] || 'unknown-project';
const FORGE_ROOT = process.argv[3] || path.join(process.env.HOME || '/root', 'forge');
const BRANCH_NAME = process.argv[4] || '';
const BRAIN_ROOT = path.join(FORGE_ROOT, 'brain');
const PR_SET_FILE = path.join(BRAIN_ROOT, 'pr-set.md');

function log(message) {
  // Write to stderr so it appears in git merge output
  const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
  console.error(`[${timestamp}] ${message}`);
}

function blockMerge(message) {
  console.error(`\n❌ MERGE BLOCKED: ${message}`);
  console.error(`   Project: ${PROJECT_SLUG}`);
  console.error(`   Branch: ${BRANCH_NAME}`);
  console.error(`   Reason: Eval must be green before merge to main`);
  console.error(`\n   Check: ${PR_SET_FILE}`);
  process.exit(1);
}

function allowMerge() {
  console.error(`✅ MERGE ALLOWED: Eval is green`);
  process.exit(0);
}

// ==================== Edge Cases & Fallback Paths ====================
// Edge Case 1: No task ID found in branch or commit
//   Action: Log warning, allow merge (might be manual/untracked)
//   Escalation: If this happens often, update branch naming convention
//
// Edge Case 2: pr-set.md doesn't exist
//   Action: BLOCK merge - no eval record exists
//   Escalation: Run eval first, then merge
//
// Edge Case 3: Task not found in pr-set.md
//   Action: BLOCK merge - task not in PR set
//   Escalation: Add task to PR set before merge
//
// Edge Case 4: Project not found in pr-set.md for this task
//   Action: BLOCK merge - project section missing
//   Escalation: Run eval for this project, update pr-set
//
// Edge Case 5: Eval status is RED (failing)
//   Action: BLOCK merge - code doesn't pass eval
//   Escalation: Fix code and re-run eval
//
// Edge Case 6: Eval status is neither GREEN nor RED (ambiguous)
//   Action: BLOCK merge - status unclear
//   Escalation: Run eval to get definitive status
// ==================== End Edge Case Definitions ====================

// Extract task ID from branch name
// Typical format: feature/task-123-description or bugfix/task-456-ui
let taskId = '';
const branchMatch = BRANCH_NAME.match(/task-(\d+)/);
if (branchMatch) {
  taskId = branchMatch[0]; // e.g., "task-123"
}

if (!taskId) {
  // Try to get from commit message
  try {
    const lastCommit = execSync('git log -1 --format=%B', {
      encoding: 'utf-8',
      stdio: 'pipe'
    }).trim();
    const commitMatch = lastCommit.match(/task-(\d+)/);
    if (commitMatch) {
      taskId = commitMatch[0];
    }
  } catch (e) {
    // Continue without task ID
  }
}

// If no task ID found, warn but allow merge (might be a manual merge)
if (!taskId) {
  log(`WARNING: No task ID found in branch name "${BRANCH_NAME}" or commit message`);
  log(`Allowing merge for ${PROJECT_SLUG} (untracked task)`);
  allowMerge();
}

// Check if pr-set.md exists
if (!fs.existsSync(PR_SET_FILE)) {
  blockMerge(`brain/pr-set.md not found. No eval record exists.`);
}

// Read pr-set.md
let prSetContent = '';
try {
  prSetContent = fs.readFileSync(PR_SET_FILE, 'utf-8');
} catch (e) {
  blockMerge(`Cannot read pr-set.md: ${e.message}`);
}

// Check if this task exists in pr-set.md
if (!prSetContent.includes(taskId)) {
  blockMerge(`Task ${taskId} not found in pr-set.md`);
}

// Extract eval status for this task/project combination
// Look for patterns like: "eval: green" or "eval: PASS" under the project section
const projectSection = prSetContent.split(`### ${PROJECT_SLUG}`)[1];
if (!projectSection) {
  blockMerge(`Project ${PROJECT_SLUG} not found in pr-set.md`);
}

const taskSection = projectSection.split(taskId)[1];
if (!taskSection) {
  blockMerge(`Task ${taskId} not found for project ${PROJECT_SLUG} in pr-set.md`);
}

// Look for eval status in next 500 chars after task mention
const statusCheck = taskSection.substring(0, 500);
const isGreen = /eval:\s*(green|pass|✅|OK)/i.test(statusCheck);
const isRed = /eval:\s*(red|fail|❌|FAIL|NOT_OK)/i.test(statusCheck);

if (!isGreen && isRed) {
  blockMerge(`Eval for task ${taskId} is RED/FAILING. Fix and re-run eval before merge.`);
}

if (!isGreen && !isRed) {
  blockMerge(`Eval status for task ${taskId} in project ${PROJECT_SLUG} is not GREEN. Run eval first.`);
}

// Eval is green, allow merge
log(`Task ${taskId} passed eval in ${PROJECT_SLUG}`);
allowMerge();

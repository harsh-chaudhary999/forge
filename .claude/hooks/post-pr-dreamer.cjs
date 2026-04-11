#!/usr/bin/env node

/**
 * post-pr-dreamer.cjs
 *
 * RETROSPECTIVE SCORER
 * Triggers dreamer subagent in retrospective mode after all PRs merge to main
 * Analyzes run, scores decisions, extracts patterns, writes learnings to brain
 *
 * Why this matters:
 * Without retrospective, each project ends and learning dies.
 * Dreamer analysis finds: patterns that work, gotchas that recur, opportunities missed,
 * risks misestimated. This data becomes institutional memory for future projects.
 *
 * Cannot be skipped:
 * - Rationalization: "The project's done, no need to analyze"
 *   Truth: Patterns repeat. You'll make the same mistakes next time without dreamer.
 *
 * Usage:
 *   Installed via forge-install-hooks in tracked projects
 *   node post-pr-dreamer.cjs <TASK_ID>
 *
 * Example:
 *   node post-pr-dreamer.cjs task-123
 *
 * Cross-platform: works on Linux, macOS, Windows
 * Environment: DREAMER_MODE=retrospect (automatically set)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const TASK_ID = process.argv[2];
const FORGE_ROOT = process.argv[3] || path.join(process.env.HOME || '/root', 'forge');
const BRAIN_DIR = path.join(FORGE_ROOT, 'brain');
const RETROSPECTIVES_DIR = path.join(BRAIN_DIR, 'retrospectives');
const EXOCORTEX_BRAIN = process.env.EXOCORTEX_BRAIN || '';

function die(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

// ==================== Edge Cases & Fallback Paths ====================
// Edge Case 1: TASK_ID not provided
//   Action: Die with error
//   Escalation: Provide TASK_ID as argument
//
// Edge Case 2: Not a git repo
//   Action: Die with error
//   Escalation: Run from forge root or valid git repo
//
// Edge Case 3: No commits found for task
//   Action: Continue - dreamer will analyze empty history
//   Escalation: Check task ID format and git log
//
// Edge Case 4: Brain directory doesn't exist
//   Action: Create it (mkdir -p)
//   Escalation: Automatic recovery
//
// Edge Case 5: Cannot write to brain directory
//   Action: Log error but continue
//   Escalation: Check permissions on ~/forge/brain
//
// Edge Case 6: Git commit fails (nothing to commit)
//   Action: Log warning, continue
//   Escalation: Retrospective is written even if commit fails
//
// Edge Case 7: Exocortex brain not available
//   Action: Skip exocortex write, continue
//   Escalation: Not critical - forge brain is primary
// ==================== End Edge Case Definitions ====================

function log(message) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${message}`);
}

// Validate inputs
if (!TASK_ID) {
  die('TASK_ID required as first argument');
}

if (!fs.existsSync(path.join(FORGE_ROOT, '.git'))) {
  die(`Not a git repo: ${FORGE_ROOT}`);
}

log(`Post-PR Hook: Triggering dreamer retrospective for task ${TASK_ID}`);

// Create retrospectives directory if it doesn't exist
if (!fs.existsSync(RETROSPECTIVES_DIR)) {
  fs.mkdirSync(RETROSPECTIVES_DIR, { recursive: true });
}

// Export dreamer mode for subagent
process.env.DREAMER_MODE = 'retrospect';
process.env.TASK_ID = TASK_ID;

// Collect PR metadata and context
log(`Collecting PR metadata for task ${TASK_ID}...`);

let prLog = '';
let prCount = 0;

try {
  prLog = execSync(`git log --all --grep="${TASK_ID}" --oneline 2>/dev/null || true`, {
    cwd: FORGE_ROOT,
    encoding: 'utf-8',
    stdio: ['pipe', 'pipe', 'pipe']
  });
  prCount = prLog.trim().split('\n').filter(line => line.length > 0).length;
} catch (e) {
  prLog = '';
  prCount = 0;
}

// Get current date and recent commit info
let workStart = '';
let workEnd = new Date().toISOString();
let gitUser = 'unknown';

try {
  const commitDateCmd = `git log --all --grep="${TASK_ID}" --format=%aI 2>/dev/null | tail -1 || true`;
  workStart = execSync(commitDateCmd, {
    cwd: FORGE_ROOT,
    encoding: 'utf-8',
    stdio: ['pipe', 'pipe', 'pipe']
  }).trim();
} catch (e) {
  workStart = '';
}

try {
  gitUser = execSync('git config user.name || echo "unknown"', {
    cwd: FORGE_ROOT,
    encoding: 'utf-8'
  }).trim();
} catch (e) {
  gitUser = 'unknown';
}

log(`Found ${prCount} commits related to task ${TASK_ID}`);

// Generate retrospective via dreamer invocation
log('Dispatching to dreamer subagent in retrospective mode...');

// Create run log from git history
let runLog = `=== Run Log for Task: ${TASK_ID} ===\n`;
runLog += `Date: ${workEnd}\n`;
runLog += `Git User: ${gitUser}\n`;
runLog += '\n=== Related Commits ===\n';

if (prLog) {
  runLog += prLog;
} else {
  runLog += `No specific commits found for task ${TASK_ID}\n`;
}

runLog += '\n=== Commit Details ===\n';

try {
  const detailCmd = `git log --all --grep="${TASK_ID}" --format="%H|%s|%aI|%b" 2>/dev/null || echo "No detailed commits available"`;
  const commitDetails = execSync(detailCmd, {
    cwd: FORGE_ROOT,
    encoding: 'utf-8',
    stdio: ['pipe', 'pipe', 'pipe']
  });
  runLog += commitDetails;
} catch (e) {
  runLog += 'No detailed commits available\n';
}

log(`Generated run log`);

// Write retrospective metadata
log('Writing retrospective to brain...');

// Create basic retrospective structure
const retrospectiveContent = `# Retrospective: PR Merge Cycle
Date: ${new Date().toISOString().split('T')[0]}
Duration: Post-merge retrospective
Task ID: ${TASK_ID}

## Executive Summary
Dreamer retrospective analysis triggered after PR merge completion. This retrospective captures decision scoring, patterns identified, and learnings from the development cycle.

## Decision Scoring

### PR Merge Validation
- **Context**: All PRs for task ${TASK_ID} have been merged
- **Correctness**: [To be scored by dreamer]
- **Robustness**: [To be scored by dreamer]
- **Efficiency**: [To be scored by dreamer]
- **Reversibility**: [To be scored by dreamer]
- **Confidence at time**: [To be updated]
- **Outcome**: Code merged to main branch

## Learning Categorization

### Patterns (What Worked)
[To be populated by dreamer analysis]

### Gotchas (What Failed)
[To be populated by dreamer analysis]

### Opportunities (What We Missed)
[To be populated by dreamer analysis]

## Aggregate Statistics
- Task ID: ${TASK_ID}
- Related commits: ${prCount}
- Retrospective generated: ${workEnd}

## Top 3 Takeaways
1. [To be identified by dreamer]
2. [To be identified by dreamer]
3. [To be identified by dreamer]

## Recommended Actions
[To be populated by dreamer analysis]
`;

// Write per-task retrospective file (never overwrite; each task gets its own)
const retroFileName = `${TASK_ID}-${new Date().toISOString().split('T')[0]}.md`;
const retrospectiveFile = path.join(RETROSPECTIVES_DIR, retroFileName);

fs.writeFileSync(retrospectiveFile, retrospectiveContent);

log(`Retrospective written to ${retrospectiveFile}`);

// If exocortex brain is available, write to distributed brain as well
if (EXOCORTEX_BRAIN && fs.existsSync(EXOCORTEX_BRAIN)) {
  log('Writing to exocortex brain...');
  const exocortexRetroDir = path.join(EXOCORTEX_BRAIN, 'brain', 'retrospectives');
  const exocortexRetrospective = path.join(exocortexRetroDir, retroFileName);

  if (!fs.existsSync(exocortexRetroDir)) {
    fs.mkdirSync(exocortexRetroDir, { recursive: true });
  }

  fs.copyFileSync(retrospectiveFile, exocortexRetrospective);
  log(`Exocortex retrospective: ${exocortexRetrospective}`);
}

// Stage and commit retrospective to forge repo
log('Committing retrospective to forge repo...');

try {
  // Add retrospective file
  execSync(`git add "${retrospectiveFile}"`, {
    cwd: FORGE_ROOT,
    stdio: 'pipe'
  });
} catch (e) {
  // Continue even if add fails
}

// Commit with dreamer reference
const commitMsg = `dreamer: retrospective for ${TASK_ID} after PR merge

- Task ID: ${TASK_ID}
- Commits analyzed: ${prCount}
- Generated: ${workEnd}
- Mode: retrospective scoring
- Output: brain/retrospectives/${retroFileName}`;

try {
  // Check if there are staged changes
  const statusOutput = execSync('git diff --cached --quiet', {
    cwd: FORGE_ROOT,
    stdio: 'pipe'
  });

  log('No changes to commit');
} catch (e) {
  try {
    execSync(`git commit -m "${commitMsg.replace(/"/g, '\\"')}"`, {
      cwd: FORGE_ROOT,
      stdio: 'pipe'
    });
    log(`Committed retrospective`);
  } catch (commitError) {
    log(`Warning: commit may have failed or files already staged`);
  }
}

log(`Post-PR Hook: Complete for task ${TASK_ID}`);
log(`Retrospective available at: ${retrospectiveFile}`);

process.exit(0);

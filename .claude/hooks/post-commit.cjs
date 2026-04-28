#!/usr/bin/env node

/**
 * post-commit.cjs
 *
 * BRAIN INBOX WRITER + GATE ARTIFACT WRITER
 * Fires after a commit in a tracked project repo (or brain repo)
 * Drops commit metadata (repo, sha, message, files) into brain inbox.
 *
 * Gate artifact writer (Improvement 3):
 * If the commit modifies conductor.log, scans the updated log for gate markers
 * and writes a JSON sidecar per gate to brain/prds/<task-id>/gates/<gate-id>.json.
 * This produces a machine-readable gate ledger for verify_forge_task.py,
 * dream-retrospect-post-pr, and CI tools without requiring regex on conductor.log.
 *
 * Gate JSON schema:
 * {
 *   "gate_id":      "P4.0-EVAL-YAML",
 *   "task_id":      "task-2025-04-21",
 *   "satisfied_at": "2025-04-21T10:30:00Z",
 *   "commit_sha":   "abc123...",
 *   "evidence": {
 *     "log_line":   "[P4.0-EVAL-YAML] task_id=... scenarios=3",
 *     "conductor_log": "prds/task-id/conductor.log"
 *   },
 *   "status": "satisfied"
 * }
 *
 * Why this matters:
 * Without commit tracking, brain can't see what code was written when.
 * Gate artifacts give verify_forge_task.py structured input instead of text regex,
 * and give dreamer a timestamped record of when each phase completed.
 *
 * Cannot be disabled:
 * - Rationalization: "I'll remember my commits without the brain"
 *   Truth: You won't. Retrospective needs artifacts. Brain inbox is provenance.
 *
 * Usage:
 *   Installed via forge-install-hooks in tracked projects
 *   node post-commit.cjs [project-slug] [forge-root]
 *
 * Examples:
 *   node post-commit.cjs backend-api /home/user/forge
 *   node post-commit.cjs web-dashboard /home/user/forge
 *
 * Cross-platform: works on Linux, macOS, Windows
 * Environment: GIT_COMMIT (set by git hook)
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync, spawnSync } = require('child_process');

// Configuration
const PROJECT_SLUG = process.argv[2] || 'unknown-project';
const FORGE_ROOT = process.argv[3] || path.join(os.homedir(), 'forge');
const BRAIN_ROOT = path.join(FORGE_ROOT, 'brain');
const INBOX_DIR = path.join(BRAIN_ROOT, 'inbox');

function log(message) {
  // Silent by default; set FORGE_HOOKS_DEBUG=1 to see output
  if (process.env.FORGE_HOOKS_DEBUG === '1') {
    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
    console.error(`[${timestamp}] ${message}`);
  }
}

function die(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

// ==================== Edge Cases & Fallback Paths ====================
// What if git command fails? → Log and exit gracefully (don't block commit)
// What if inbox dir doesn't exist? → Create it (mkdir recursive)
// What if commit has no message? → Use empty string, still record it
// What if files list is empty? → That's fine, just record empty list
// What if brain is inaccessible? → Log warning, don't block commit
// What if gate JSON write fails? → Log warning, don't block commit
// ==================== End Edge Case Definitions ====================

// Create inbox directory if needed
if (!fs.existsSync(INBOX_DIR)) {
  try {
    fs.mkdirSync(INBOX_DIR, { recursive: true });
  } catch (e) {
    log(`Failed to create inbox directory: ${INBOX_DIR}`);
  }
}

// Extract commit info
let commitSha = '';
let commitMessage = '';
let commitAuthor = '';
let commitDate = '';
let filesChanged = [];

function runGit(args) {
  return spawnSync('git', args, {
    encoding: 'utf-8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
}

try {
  // Get HEAD commit info
  commitSha = execSync('git rev-parse HEAD', {
    encoding: 'utf-8',
    stdio: 'pipe'
  }).trim();

  if (!commitSha) {
    log('No commit sha found');
    process.exit(0);
  }

  // Get commit message
  const msgRes = runGit(['log', '-1', '--format=%B', 'HEAD']);
  if (msgRes.status !== 0) {
    throw new Error((msgRes.stderr || '').trim() || 'failed to read commit message');
  }
  commitMessage = (msgRes.stdout || '').trim();

  // Get author
  const authorRes = runGit(['log', '-1', '--format=%an', commitSha]);
  if (authorRes.status !== 0) {
    throw new Error((authorRes.stderr || '').trim() || 'failed to read commit author');
  }
  commitAuthor = (authorRes.stdout || '').trim();

  // Get commit date
  const dateRes = runGit(['log', '-1', '--format=%aI', commitSha]);
  if (dateRes.status !== 0) {
    throw new Error((dateRes.stderr || '').trim() || 'failed to read commit date');
  }
  commitDate = (dateRes.stdout || '').trim();

  // Get list of changed files
  const filesRes = runGit(['diff-tree', '--no-commit-id', '--name-only', '-r', commitSha]);
  if (filesRes.status !== 0) {
    throw new Error((filesRes.stderr || '').trim() || 'failed to list changed files');
  }
  const fileList = (filesRes.stdout || '').trim();

  filesChanged = fileList ? fileList.split('\n').filter(f => f.length > 0) : [];
} catch (e) {
  log(`Failed to extract commit info: ${e.message}`);
  process.exit(0);
}

// Generate inbox entry
const shortSha = commitSha.substring(0, 7);
const timestamp = new Date().toISOString();
const inboxFile = path.join(
  INBOX_DIR,
  `${timestamp.split('T')[0]}-${PROJECT_SLUG}-${shortSha}.md`
);

const inboxEntry = `# Commit Drop: ${PROJECT_SLUG}

**Timestamp:** ${timestamp}
**Commit SHA:** ${commitSha}
**Short SHA:** ${shortSha}
**Project:** ${PROJECT_SLUG}
**Author:** ${commitAuthor}
**Date:** ${commitDate}

## Message
\`\`\`
${commitMessage}
\`\`\`

## Files Changed (${filesChanged.length})
${filesChanged.map(f => `- ${f}`).join('\n')}

## Raw Metadata
\`\`\`json
${JSON.stringify({
  repo: PROJECT_SLUG,
  sha: commitSha,
  short_sha: shortSha,
  author: commitAuthor,
  date: commitDate,
  message_first_line: commitMessage.split('\n')[0] || '',
  files_count: filesChanged.length,
}, null, 2)}
\`\`\`
`;

// Write to inbox
try {
  fs.writeFileSync(inboxFile, inboxEntry, 'utf-8');
  log(`Commit drop written: ${inboxFile}`);
} catch (e) {
  log(`Failed to write inbox entry: ${e.message}`);
  process.exit(1);
}

// ==================== Gate Artifact Writer ====================

/**
 * Gate marker patterns and their canonical gate IDs.
 * Each entry: [regex to detect in conductor.log, gate_id for JSON filename]
 */
const GATE_MARKERS = [
  { pattern: /\[P4\.0-QA-CSV\].*approved=yes/,   id: 'P4.0-QA-CSV' },
  { pattern: /\[P4\.0-EVAL-YAML\]/,              id: 'P4.0-EVAL-YAML' },
  { pattern: /\[P4\.0-TDD-RED\]/,                id: 'P4.0-TDD-RED' },
  { pattern: /\[P4\.1-DISPATCH\]/,               id: 'P4.1-DISPATCH' },
  { pattern: /\[P4\.4-EVAL-GREEN\]/,             id: 'P4.4-EVAL-GREEN' },
  { pattern: /\[P5[.-]/,                         id: 'P5-PR-SET' },
  { pattern: /\[P3-SPEC-FROZEN\]/,               id: 'P3-SPEC-FROZEN' },
  { pattern: /\[P1-PRD-LOCKED\]/,                id: 'P1-PRD-LOCKED' },
];

/**
 * Extracts the task_id from a conductor.log line.
 * Looks for task_id=<value> pattern.
 */
function extractTaskId(logLine) {
  const match = logLine.match(/task_id=([^\s]+)/);
  return match ? match[1] : null;
}

/**
 * Writes a gate JSON sidecar for a given gate and conductor.log line.
 */
function writeGateArtifact(gateId, taskId, logLine, conductorLogRelPath) {
  if (!taskId) {
    log(`Gate ${gateId} found but no task_id in log line — skipping artifact`);
    return;
  }
  if (!/^[\w.-]+$/.test(taskId)) {
    log(`Gate ${gateId} has invalid task_id '${taskId}' — skipping artifact`);
    return;
  }

  const gatesDir = path.join(BRAIN_ROOT, 'prds', taskId, 'gates');
  try {
    fs.mkdirSync(gatesDir, { recursive: true });
  } catch (e) {
    log(`Failed to create gates dir ${gatesDir}: ${e.message}`);
    return;
  }

  const artifactPath = path.join(gatesDir, `${gateId}.json`);

  // Don't overwrite an existing gate artifact (gates are immutable once satisfied)
  if (fs.existsSync(artifactPath)) {
    log(`Gate artifact already exists: ${artifactPath} — skipping`);
    return;
  }

  const artifact = {
    gate_id: gateId,
    task_id: taskId,
    satisfied_at: new Date().toISOString(),
    commit_sha: commitSha,
    evidence: {
      log_line: logLine.trim(),
      conductor_log: conductorLogRelPath,
    },
    status: 'satisfied',
  };

  try {
    fs.writeFileSync(artifactPath, JSON.stringify(artifact, null, 2) + '\n', 'utf-8');
    log(`Gate artifact written: ${artifactPath}`);
  } catch (e) {
    log(`Failed to write gate artifact ${artifactPath}: ${e.message}`);
  }
}

/**
 * Scans conductor.log files touched in this commit and writes gate artifacts.
 */
function processGateArtifacts() {
  // Only scan conductor.log files that were changed in this commit
  const conductorLogs = filesChanged.filter(f => f.endsWith('conductor.log'));
  if (conductorLogs.length === 0) {
    log('No conductor.log in changed files — skipping gate artifact scan');
    return;
  }

  for (const relLogPath of conductorLogs) {
    // conductor.log may be in the current repo (brain repo) or a relative path
    let absLogPath = null;

    // Try as absolute from CWD (most likely when installed in brain repo)
    const cwdLog = path.join(process.cwd(), relLogPath);
    if (fs.existsSync(cwdLog)) {
      absLogPath = cwdLog;
    }
    // Try as path relative to BRAIN_ROOT
    else {
      const brainLog = path.join(BRAIN_ROOT, relLogPath);
      if (fs.existsSync(brainLog)) {
        absLogPath = brainLog;
      }
    }

    if (!absLogPath) {
      log(`Cannot find conductor.log at ${relLogPath} — skipping`);
      continue;
    }

    let logContent = '';
    try {
      logContent = fs.readFileSync(absLogPath, 'utf-8');
    } catch (e) {
      log(`Failed to read ${absLogPath}: ${e.message}`);
      continue;
    }

    const lines = logContent.split('\n');
    for (const line of lines) {
      for (const { pattern, id } of GATE_MARKERS) {
        if (pattern.test(line)) {
          const taskId = extractTaskId(line);
          writeGateArtifact(id, taskId, line, relLogPath);
        }
      }
    }
  }
}

// Run gate artifact processing — non-blocking, errors are logged not thrown
try {
  processGateArtifacts();
} catch (e) {
  log(`Gate artifact processing error (non-fatal): ${e.message}`);
}

process.exit(0);

#!/usr/bin/env node

/**
 * post-commit.cjs
 *
 * BRAIN INBOX WRITER
 * Fires after a commit in a tracked project repo
 * Drops commit metadata (repo, sha, message, files) into brain inbox
 * Enables brain to track commit activity across projects
 *
 * Why this matters:
 * Without commit tracking, brain can't see what code was written when.
 * This data enables: decision history, pattern detection, retrospective scoring,
 * and cross-project coordination. Commits without inbox records are invisible.
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
const { execSync } = require('child_process');

// Configuration
const PROJECT_SLUG = process.argv[2] || 'unknown-project';
const FORGE_ROOT = process.argv[3] || path.join(process.env.HOME || '/root', 'forge');
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
  if (process.env.FORGE_HOOKS_DEBUG === '1') {
    console.error(`ERROR: ${message}`);
  }
  process.exit(1);
}

// ==================== Edge Cases & Fallback Paths ====================
// What if git command fails? → Log and exit gracefully (don't block commit)
// What if inbox dir doesn't exist? → Create it (mkdir recursive)
// What if commit has no message? → Use empty string, still record it
// What if files list is empty? → That's fine, just record empty list
// What if brain is inaccessible? → Log warning, don't block commit
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
  commitMessage = execSync(`git log -1 --format=%B "${commitSha}"`, {
    encoding: 'utf-8',
    stdio: 'pipe'
  }).trim();

  // Get author
  commitAuthor = execSync(`git log -1 --format=%an "${commitSha}"`, {
    encoding: 'utf-8',
    stdio: 'pipe'
  }).trim();

  // Get commit date
  commitDate = execSync(`git log -1 --format=%aI "${commitSha}"`, {
    encoding: 'utf-8',
    stdio: 'pipe'
  }).trim();

  // Get list of changed files
  const fileList = execSync(`git diff-tree --no-commit-id --name-only -r "${commitSha}"`, {
    encoding: 'utf-8',
    stdio: 'pipe'
  }).trim();

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
{
  "repo": "${PROJECT_SLUG}",
  "sha": "${commitSha}",
  "short_sha": "${shortSha}",
  "author": "${commitAuthor}",
  "date": "${commitDate}",
  "message_first_line": "${commitMessage.split('\n')[0].replace(/"/g, '\\"')}",
  "files_count": ${filesChanged.length}
}
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

process.exit(0);

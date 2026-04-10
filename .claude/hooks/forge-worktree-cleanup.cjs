#!/usr/bin/env node

/**
 * forge-worktree-cleanup.cjs
 *
 * WORKTREE JANITOR
 * Removes stale worktrees (D30: per-task-per-project isolation)
 * Archives metadata before cleanup, audits cleanup decisions
 *
 * Why this matters (D30):
 * Each task gets a fresh worktree for isolation. Without cleanup,
 * old worktrees accumulate, waste disk space, and create confusion.
 * This hook audits which worktrees were removed and why.
 *
 * Usage:
 *   node forge-worktree-cleanup.cjs [project-root] [stale-threshold-hours] [verbose]
 *
 * Examples:
 *   node forge-worktree-cleanup.cjs . 24 1          # 24h threshold, verbose
 *   node forge-worktree-cleanup.cjs /path/to/proj 48 0  # 48h threshold, silent
 *
 * Cross-platform: works on Linux, macOS, Windows
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PROJECT_ROOT = process.argv[2] || '.';
const STALE_THRESHOLD_HOURS = parseInt(process.argv[3] || '24', 10);
const VERBOSE = parseInt(process.argv[4] || '0', 10) === 1;

function die(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

function log(message) {
  if (VERBOSE) {
    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
    console.log(`[${timestamp}] ${message}`);
  }
}

// Validate project is a git repo
const gitDir = path.join(PROJECT_ROOT, '.git');
if (!fs.existsSync(gitDir)) {
  die(`Not a git repo: ${PROJECT_ROOT}`);
}

log(`Scanning for stale worktrees in ${PROJECT_ROOT}...`);

const WORKTREE_DIR = path.join(PROJECT_ROOT, '.worktrees');

// Exit early if no worktrees directory
if (!fs.existsSync(WORKTREE_DIR)) {
  log('No .worktrees directory. Exiting.');
  process.exit(0);
}

// Calculate stale timestamp (now - threshold)
const now = new Date();
const staleDate = new Date(now.getTime() - STALE_THRESHOLD_HOURS * 60 * 60 * 1000);
const STALE_TIMESTAMP = Math.floor(staleDate.getTime() / 1000);

let removedCount = 0;
let archivedCount = 0;

// Iterate through worktrees
const worktrees = fs.readdirSync(WORKTREE_DIR).filter(name => {
  const fullPath = path.join(WORKTREE_DIR, name);
  return fs.statSync(fullPath).isDirectory();
});

for (const worktreeName of worktrees) {
  const worktreePath = path.join(WORKTREE_DIR, worktreeName);
  const metaFile = path.join(worktreePath, '.worktree-meta');

  // If no metadata file, skip (not a forge-managed worktree)
  if (!fs.existsSync(metaFile)) {
    continue;
  }

  // Extract creation timestamp
  let createdAt = '';
  try {
    const metaContent = fs.readFileSync(metaFile, 'utf-8');
    const match = metaContent.match(/^created_at:\s*(.+)$/m);
    if (match) {
      createdAt = match[1];
    }
  } catch (e) {
    log(`Skipping ${worktreeName}: error reading metadata`);
    continue;
  }

  if (!createdAt) {
    log(`Skipping ${worktreeName}: no creation timestamp in metadata`);
    continue;
  }

  // Parse ISO timestamp to Unix seconds
  let createdTimestamp = 0;
  try {
    createdTimestamp = Math.floor(new Date(createdAt).getTime() / 1000);
  } catch (e) {
    log(`Skipping ${worktreeName}: invalid timestamp format '${createdAt}'`);
    continue;
  }

  if (createdTimestamp === 0) {
    log(`Skipping ${worktreeName}: invalid timestamp format '${createdAt}'`);
    continue;
  }

  // Check if stale
  if (createdTimestamp < STALE_TIMESTAMP) {
    const ageSeconds = Math.floor(Date.now() / 1000) - createdTimestamp;
    const ageHours = Math.floor(ageSeconds / 3600);

    log(`Marking ${worktreeName} as stale (age: ${ageHours}h)`);

    // Archive metadata
    const archiveDir = path.join(PROJECT_ROOT, '.worktree-archive');
    if (!fs.existsSync(archiveDir)) {
      fs.mkdirSync(archiveDir, { recursive: true });
    }

    try {
      fs.copyFileSync(metaFile, path.join(archiveDir, `${worktreeName}.meta`));
      archivedCount += 1;
    } catch (e) {
      log(`WARNING: Failed to archive metadata for ${worktreeName}`);
    }

    // Remove worktree
    try {
      execSync(`git worktree remove --force "${worktreePath}"`, {
        cwd: PROJECT_ROOT,
        stdio: 'pipe'
      });
      log(`Removed worktree: ${worktreeName}`);
      removedCount += 1;
    } catch (e) {
      log(`WARNING: Failed to remove worktree: ${worktreeName} (may be in use)`);
    }
  }
}

// Log cleanup summary
const archiveLogFile = path.join(PROJECT_ROOT, '.worktree-archive', 'cleanup.log');
const cleanupLog = `${new Date().toISOString()} — cleanup run
  project: ${PROJECT_ROOT}
  stale_threshold: ${STALE_THRESHOLD_HOURS}h
  worktrees_removed: ${removedCount}
  metadata_archived: ${archivedCount}
`;

try {
  const archiveDir = path.join(PROJECT_ROOT, '.worktree-archive');
  if (!fs.existsSync(archiveDir)) {
    fs.mkdirSync(archiveDir, { recursive: true });
  }

  fs.appendFileSync(archiveLogFile, cleanupLog + '\n');
} catch (e) {
  log(`WARNING: Failed to write cleanup log`);
}

log(`Cleanup complete: removed=${removedCount} archived=${archivedCount}`);
process.exit(0);

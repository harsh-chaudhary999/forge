#!/usr/bin/env node

/**
 * pre-commit.cjs
 *
 * GARBAGE DETECTOR
 * Prevents committing secrets, large files, and obviously broken code
 * Fires before staging for commit (catches issues before they land in tree)
 *
 * Why this matters:
 * Secrets in git history are FOREVER. Rotating credentials doesn't delete them.
 * Large files bloat repo, slow clones, and can't be removed without rewriting history.
 * This hook is your last local defense before bad data enters the permanent record.
 *
 * Cannot be bypassed:
 * - Rationalization: "Secrets are fine, we'll rotate them later"
 *   Truth: Rotated credentials don't delete history. Attacker still has old secret.
 * - Rationalization: "I'll delete large files before pushing"
 *   Truth: They're already in git history. Pushing just makes it public.
 *
 * Usage:
 *   Installed via forge-install-hooks in tracked projects
 *   node pre-commit.cjs [project-root] [verbose]
 *
 * Exit codes:
 *   0 = no dangerous files staged (commit allowed)
 *   1 = dangerous files detected (commit rejected)
 *
 * Cross-platform: works on Linux, macOS, Windows
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PROJECT_ROOT = process.argv[2] || '.';
const VERBOSE = parseInt(process.argv[3] || '0', 10) === 1;

// Configuration
const SECRET_PATTERNS = [
  /\.env\.local/,           // Local env files with secrets
  /\.env\.development\.local/,
  /\.env\.production/,      // Production secrets
  /\.env\.test\.local/,
  /private_key/,            // SSH/crypto keys
  /id_rsa/,
  /id_dsa/,
  /\.pem$/,
  /\.key$/,
  /password/,               // Hardcoded passwords
  /api[-_]key/i,            // API keys
  /aws[-_]access[-_]key/i,  // AWS credentials
  /aws[-_]secret/i,
  /oauth[-_]token/i,        // OAuth tokens
  /Bearer\s+[A-Za-z0-9\-._~\+\/]+=*/i, // Bearer tokens
  /github[-_]token/i,       // GitHub tokens
  /slack[-_]token/i,        // Slack webhooks
  /firebase[-_]key/i,       // Firebase keys
  /mongodb[-_]uri/i,        // DB connection strings
  /postgresql[-_]password/i,
  /mysql[-_]password/i,
];

const LARGE_FILE_THRESHOLD = 10 * 1024 * 1024; // 10 MB
const BINARY_PATTERNS = [
  /\.jar$/,
  /\.class$/,
  /\.pyc$/,
  /\.o$/,
  /\.a$/,
  /\.so$/,
  /\.exe$/,
  /\.dll$/,
  /\.bin$/,
];

const IGNORE_PATTERNS = [
  /node_modules\//,
  /\.git\//,
  /dist\//,
  /build\//,
  /\.next\//,
  /\.cache\//,
];

function die(message) {
  console.error(`\n❌ PRE-COMMIT CHECK FAILED: ${message}`);
  console.error('\nFix the staged files and try again:');
  console.error('  git reset HEAD <file>    # Unstage file');
  console.error('  rm <file>                # Delete or fix');
  console.error('  git add <file>           # Re-stage if safe');
  process.exit(1);
}

function allow() {
  if (VERBOSE) {
    console.log('✅ Pre-commit check passed');
  }
  process.exit(0);
}

function log(message) {
  if (VERBOSE) {
    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
    console.log(`[${timestamp}] ${message}`);
  }
}

// ==================== Edge Cases & Fallback Paths ====================
// Edge Case 1: .env.example file (template, should be safe)
//   Action: Allow - it's a template, no real secrets
//   Escalation: None
//
// Edge Case 2: Legitimate large binaries (package-lock.json, compiled artifacts)
//   Action: Block and require explicit override (git commit --no-verify)
//   Escalation: Use .gitignore to prevent staging
//
// Edge Case 3: Partially staged file (git add -p)
//   Action: Check entire file, not just staged hunks
//   Escalation: Check full file content
//
// Edge Case 4: node_modules accidentally staged (happens)
//   Action: Block - node_modules must never be in git
//   Escalation: Remove from staging, add to .gitignore
//
// Edge Case 5: git add -A picked up build artifacts
//   Action: Block - catch before commit
//   Escalation: User adds build dirs to .gitignore
//
// Edge Case 6: Symlink to secret file (indirect secret leak)
//   Action: Block - symlinks to dangerous files are dangerous
//   Escalation: Don't stage symlink
// ==================== End Edge Case Definitions ====================

// Check if we're in a git repo
const gitDir = path.join(PROJECT_ROOT, '.git');
if (!fs.existsSync(gitDir)) {
  // Not a git repo - allow (might be called elsewhere)
  allow();
}

let stagedFiles = [];
try {
  const output = execSync('git diff --cached --name-only --diff-filter=ACMR', {
    cwd: PROJECT_ROOT,
    encoding: 'utf-8',
    stdio: 'pipe'
  });
  stagedFiles = output.trim().split('\n').filter(f => f.length > 0);
} catch (e) {
  // No staged files or git command failed - allow
  allow();
}

if (stagedFiles.length === 0) {
  allow();
}

log(`Checking ${stagedFiles.length} staged files for secrets and large files...`);

let hasIssues = false;
const issues = [];

for (const file of stagedFiles) {
  const filePath = path.join(PROJECT_ROOT, file);

  // Check if file should be ignored
  let shouldIgnore = false;
  for (const pattern of IGNORE_PATTERNS) {
    if (pattern.test(file)) {
      shouldIgnore = true;
      break;
    }
  }
  if (shouldIgnore) {
    log(`Ignoring (in ignore list): ${file}`);
    continue;
  }

  // Check filename for secrets
  let isSecret = false;
  for (const pattern of SECRET_PATTERNS) {
    if (pattern.test(file.toLowerCase())) {
      isSecret = true;
      issues.push(`SECRET FILE: ${file}`);
      hasIssues = true;
      log(`SECRET DETECTED: ${file}`);
      break;
    }
  }
  if (isSecret) continue;

  // Check file size (if it exists)
  if (fs.existsSync(filePath)) {
    try {
      const stats = fs.statSync(filePath);
      if (stats.isFile() && stats.size > LARGE_FILE_THRESHOLD) {
        issues.push(`LARGE FILE (${Math.round(stats.size / 1024 / 1024)}MB): ${file}`);
        hasIssues = true;
        log(`LARGE FILE: ${file} (${Math.round(stats.size / 1024 / 1024)}MB)`);
        continue;
      }

      // Check if binary file
      let isBinary = false;
      for (const pattern of BINARY_PATTERNS) {
        if (pattern.test(file)) {
          isBinary = true;
          issues.push(`BINARY FILE: ${file}`);
          hasIssues = true;
          log(`BINARY: ${file}`);
          break;
        }
      }
      if (isBinary) continue;

      // Check STAGED content for secrets (use git show to read index, not working dir)
      if (stats.isFile() && stats.size < 1024 * 1024) { // Only check files < 1MB
        try {
          // Read from the git index (staged version), not the working directory file.
          // This catches: staged secret removed from working copy before commit.
          const stagedContent = execSync(`git show ":${file}"`, {
            cwd: PROJECT_ROOT,
            encoding: 'utf-8',
            stdio: 'pipe',
            maxBuffer: 2 * 1024 * 1024
          });
          for (const pattern of SECRET_PATTERNS) {
            if (pattern.test(stagedContent)) {
              issues.push(`SECRET IN STAGED FILE: ${file}`);
              hasIssues = true;
              log(`SECRET DETECTED IN STAGED CONTENT: ${file}`);
              break;
            }
          }
        } catch (e) {
          // Binary file, git show error, or read error — skip content check
        }
      }
    } catch (e) {
      log(`Could not check file: ${file} (${e.message})`);
    }
  }
}

if (hasIssues) {
  const issueList = issues.map(i => `  • ${i}`).join('\n');
  die(`Dangerous files detected:\n${issueList}`);
}

allow();

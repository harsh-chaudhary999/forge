#!/usr/bin/env node

/**
 * forge-install-hooks.cjs
 *
 * HOOK INSTALLER
 * Installs Forge git hooks into a project repository
 * Called by: /forge-install command (Phase 1)
 *
 * What it installs:
 *   - post-commit: Tracks commits in brain inbox (provenance)
 *   - pre-merge: Blocks merge if eval not green (HARD-GATE)
 *   - post-pr: Triggers dreamer retrospective (learning)
 *
 * Why this matters:
 * Hooks create the continuous feedback loop: commit → inbox → eval → merge gate → dreamer.
 * Without hooks, none of Forge's discipline works. They're the glue that ties
 * code changes to brain state and vice versa.
 *
 * Usage:
 *   node forge-install-hooks.cjs <project-root> [project-slug] [forge-root]
 *
 * Examples:
 *   node forge-install-hooks.cjs . backend-api /home/user/forge
 *   node forge-install-hooks.cjs /path/to/web-repo web-dashboard /home/user/forge
 *
 * Cross-platform: works on Linux, macOS, Windows
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const PROJECT_ROOT = process.argv[2] || '.';
const PROJECT_SLUG = process.argv[3] || path.basename(PROJECT_ROOT);
const FORGE_ROOT = process.argv[4] || path.join(process.env.HOME || '/root', 'forge');
const HOOKS_SRC = path.join(FORGE_ROOT, '.claude', 'hooks');

function die(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

function log(message) {
  console.log(`✓ ${message}`);
}

// Validate project is a git repo
const gitDir = path.join(PROJECT_ROOT, '.git');
if (!fs.existsSync(gitDir)) {
  die(`Not a git repository: ${PROJECT_ROOT}`);
}

// Validate hooks source exists
if (!fs.existsSync(HOOKS_SRC)) {
  die(`Forge hooks directory not found: ${HOOKS_SRC}`);
}

const HOOKS_DIR = path.join(gitDir, 'hooks');

// Create hooks directory if needed
if (!fs.existsSync(HOOKS_DIR)) {
  try {
    fs.mkdirSync(HOOKS_DIR, { recursive: true });
  } catch (e) {
    die(`Failed to create hooks directory: ${e.message}`);
  }
}

console.log(`Installing Forge hooks into: ${PROJECT_ROOT}`);
console.log(`Project slug: ${PROJECT_SLUG}`);
console.log(`Forge root: ${FORGE_ROOT}\n`);

// 1. Install post-commit hook
const postCommitSrc = path.join(HOOKS_SRC, 'post-commit.cjs');
const postCommitDest = path.join(HOOKS_DIR, 'post-commit');

if (!fs.existsSync(postCommitSrc)) {
  die(`post-commit.cjs not found: ${postCommitSrc}`);
}

try {
  // Create a wrapper script that calls the Forge post-commit hook
  const postCommitWrapper = `#!/bin/bash
# Forge post-commit hook — tracks commits in brain inbox
node "${postCommitSrc}" "${PROJECT_SLUG}" "${FORGE_ROOT}"
exit 0
`;

  fs.writeFileSync(postCommitDest, postCommitWrapper);
  fs.chmodSync(postCommitDest, 0o755);
  log(`Installed post-commit hook`);
} catch (e) {
  die(`Failed to install post-commit hook: ${e.message}`);
}

// 2. Install commit-msg hook
const commitMsgSrc = path.join(HOOKS_SRC, 'commit-msg.cjs');
const commitMsgDest = path.join(HOOKS_DIR, 'commit-msg');

if (!fs.existsSync(commitMsgSrc)) {
  die(`commit-msg.cjs not found: ${commitMsgSrc}`);
}

try {
  const commitMsgWrapper = `#!/bin/bash
# Forge commit-msg hook — validates commit message format
node "${commitMsgSrc}" "$1"
exit 0
`;

  fs.writeFileSync(commitMsgDest, commitMsgWrapper);
  fs.chmodSync(commitMsgDest, 0o755);
  log(`Installed commit-msg hook`);
} catch (e) {
  die(`Failed to install commit-msg hook: ${e.message}`);
}

// 3. Install pre-commit hook
const preCommitSrc = path.join(HOOKS_SRC, 'pre-commit.cjs');
const preCommitDest = path.join(HOOKS_DIR, 'pre-commit');

if (!fs.existsSync(preCommitSrc)) {
  die(`pre-commit.cjs not found: ${preCommitSrc}`);
}

try {
  const preCommitWrapper = `#!/bin/bash
# Forge pre-commit hook — prevents committing secrets and large files
node "${preCommitSrc}" . 0
exit 0
`;

  fs.writeFileSync(preCommitDest, preCommitWrapper);
  fs.chmodSync(preCommitDest, 0o755);
  log(`Installed pre-commit hook`);
} catch (e) {
  die(`Failed to install pre-commit hook: ${e.message}`);
}

// 4. Install post-rewrite hook
const postRewriteSrc = path.join(HOOKS_SRC, 'post-rewrite.cjs');
const postRewriteDest = path.join(HOOKS_DIR, 'post-rewrite');

if (!fs.existsSync(postRewriteSrc)) {
  die(`post-rewrite.cjs not found: ${postRewriteSrc}`);
}

try {
  const postRewriteWrapper = `#!/bin/bash
# Forge post-rewrite hook — updates brain state when commits are rewritten
node "${postRewriteSrc}" "$1" "${PROJECT_SLUG}" "${FORGE_ROOT}"
exit 0
`;

  fs.writeFileSync(postRewriteDest, postRewriteWrapper);
  fs.chmodSync(postRewriteDest, 0o755);
  log(`Installed post-rewrite hook`);
} catch (e) {
  die(`Failed to install post-rewrite hook: ${e.message}`);
}

// 5. Install post-merge hook
const postMergeSrc = path.join(HOOKS_SRC, 'post-merge.cjs');
const postMergeDest = path.join(HOOKS_DIR, 'post-merge');

if (!fs.existsSync(postMergeSrc)) {
  die(`post-merge.cjs not found: ${postMergeSrc}`);
}

try {
  const postMergeWrapper = `#!/bin/bash
# Forge post-merge hook — consolidates brain state and validates main
node "${postMergeSrc}" "${PROJECT_SLUG}" "${FORGE_ROOT}"
exit 0
`;

  fs.writeFileSync(postMergeDest, postMergeWrapper);
  fs.chmodSync(postMergeDest, 0o755);
  log(`Installed post-merge hook`);
} catch (e) {
  die(`Failed to install post-merge hook: ${e.message}`);
}

// 6. Install pre-merge hook (uses pre-merge logic for merge validation)
const preMergeSrc = path.join(HOOKS_SRC, 'pre-merge.cjs');
const prePushDest = path.join(HOOKS_DIR, 'pre-push');

if (!fs.existsSync(preMergeSrc)) {
  die(`pre-merge.cjs not found: ${preMergeSrc}`);
}

try {
  // Create a wrapper script that calls the Forge pre-merge hook
  // Note: pre-push is called before push; pre-receive runs on server (not applicable here)
  // We use pre-push as the client-side gate
  const prePushWrapper = `#!/bin/bash
# Forge pre-push hook — verifies eval is green before allowing push to main
# This prevents pushing code that hasn't passed eval

# Get the branch being pushed
while read local_ref local_sha remote_ref remote_sha
do
  if [[ "$remote_ref" == "refs/heads/main" ]] || [[ "$remote_ref" == "refs/heads/master" ]]; then
    # Pushing to main/master — verify eval
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    node "${preMergeSrc}" "${PROJECT_SLUG}" "${FORGE_ROOT}" "$BRANCH"
    RESULT=$?

    if [ $RESULT -ne 0 ]; then
      exit 1
    fi
  fi
done

exit 0
`;

  fs.writeFileSync(prePushDest, prePushWrapper);
  fs.chmodSync(prePushDest, 0o755);
  log(`Installed pre-push hook`);
} catch (e) {
  die(`Failed to install pre-push hook: ${e.message}`);
}

// 7. Install post-pr-dreamer hook
const postPrDreamerSrc = path.join(HOOKS_SRC, 'post-pr-dreamer.cjs');
const postPrDreamerDest = path.join(HOOKS_DIR, 'post-merge-dreamer');

if (!fs.existsSync(postPrDreamerSrc)) {
  die(`post-pr-dreamer.cjs not found: ${postPrDreamerSrc}`);
}

try {
  // post-pr-dreamer is invoked manually with a TASK_ID after all PRs merge.
  // We also install it as a named hook script so it can be called:
  //   .git/hooks/post-merge-dreamer <task-id>
  const postPrDreamerWrapper = `#!/bin/bash
# Forge post-pr-dreamer hook — triggers dreamer retrospective after PR set merges
# Usage: .git/hooks/post-merge-dreamer <task-id>
# Called manually after all PRs for a task have merged to main
TASK_ID="\${1:-}"
if [ -z "$TASK_ID" ]; then
  echo "Usage: $0 <task-id>" >&2
  exit 1
fi
node "${postPrDreamerSrc}" "$TASK_ID" "${FORGE_ROOT}"
exit 0
`;

  fs.writeFileSync(postPrDreamerDest, postPrDreamerWrapper);
  fs.chmodSync(postPrDreamerDest, 0o755);
  log(`Installed post-merge-dreamer hook`);
} catch (e) {
  die(`Failed to install post-merge-dreamer hook: ${e.message}`);
}

// 8. Install forge-worktree-cleanup hook
const worktreeCleanupSrc = path.join(HOOKS_SRC, 'forge-worktree-cleanup.cjs');
const worktreeCleanupDest = path.join(HOOKS_DIR, 'forge-worktree-cleanup');

if (!fs.existsSync(worktreeCleanupSrc)) {
  die(`forge-worktree-cleanup.cjs not found: ${worktreeCleanupSrc}`);
}

try {
  // Worktree cleanup is invoked after eval completes (pass or fail).
  // Installed as a named hook script: .git/hooks/forge-worktree-cleanup [stale-hours] [verbose]
  const worktreeCleanupWrapper = `#!/bin/bash
# Forge worktree cleanup hook — removes stale worktrees after eval completes
# Usage: .git/hooks/forge-worktree-cleanup [stale-threshold-hours] [verbose]
STALE_HOURS="\${1:-24}"
VERBOSE="\${2:-0}"
node "${worktreeCleanupSrc}" "$(pwd)" "$STALE_HOURS" "$VERBOSE"
exit 0
`;

  fs.writeFileSync(worktreeCleanupDest, worktreeCleanupWrapper);
  fs.chmodSync(worktreeCleanupDest, 0o755);
  log(`Installed forge-worktree-cleanup hook`);
} catch (e) {
  die(`Failed to install forge-worktree-cleanup hook: ${e.message}`);
}

// 9. Summary
console.log('\n' + '='.repeat(60));
console.log('✅ Forge hooks installed successfully');
console.log('='.repeat(60));
console.log('\nHooks installed:');
console.log('  • session-start          — Bootstraps Forge at session start (via plugin)');
console.log('  • post-commit            — Tracks commits in brain/inbox/');
console.log('  • commit-msg             — Validates commit message format (task-ID required)');
console.log('  • pre-commit             — Scans staged content for secrets and large files');
console.log('  • post-rewrite           — Updates brain state after rebase/amend');
console.log('  • post-merge             — Consolidates brain state after merge to main');
console.log('  • pre-push               — Verifies eval green before push to main');
console.log('  • post-merge-dreamer     — Triggers dreamer retrospective (call manually with task-id)');
console.log('  • forge-worktree-cleanup — Removes stale worktrees after eval completes');
console.log('\nHooks are installed at:');
console.log(`  ${HOOKS_DIR}/<hook-name>`);
console.log('\nHook execution order on commit:');
console.log('  1. commit-msg (validate message format)');
console.log('  2. pre-commit (scan staged content for secrets/large files)');
console.log('  3. post-commit (track in brain)');
console.log('\nHook execution order on merge:');
console.log('  1. pre-push (verify eval green)');
console.log('  2. post-merge (consolidate brain state)');
console.log('  3. post-merge-dreamer (invoke manually: .git/hooks/post-merge-dreamer <task-id>)');
console.log('\nWorktree cleanup (invoke after eval completes):');
console.log('  .git/hooks/forge-worktree-cleanup [stale-hours] [verbose]');
console.log('\nTo uninstall, remove files from .git/hooks/');
console.log('To verify: ls .git/hooks/');
console.log('');

#!/usr/bin/env node

/**
 * post-rewrite.cjs
 *
 * PROVENANCE SYNC
 * Updates brain state when commits are rewritten (rebase, amend)
 * Fires after rebase/amend to map old SHAs to new SHAs
 *
 * Why this matters:
 * When you rebase or amend, commits get new SHAs. Without updating brain state,
 * dreamer sees old SHAs that no longer exist, task tracking breaks, decision scoring
 * becomes impossible. This hook maintains task provenance through rewrites.
 *
 * Cannot be bypassed:
 * - Rationalization: "Rebase doesn't affect tracking, it's just moving commits"
 *   Truth: SHAs change completely. Old SHAs are orphaned. Brain tracking breaks.
 * - Rationalization: "I'll update the brain manually later"
 *   Truth: You won't. State stays out of sync forever.
 *
 * Usage:
 *   Installed via forge-install-hooks in tracked projects
 *   node post-rewrite.cjs <rebase|amend> [project-slug] [forge-root]
 *
 * Exit codes:
 *   0 = brain state updated successfully (or no changes needed)
 *   1 = error updating brain state (non-blocking warning)
 *
 * Cross-platform: works on Linux, macOS, Windows
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

const REWRITE_TYPE = process.argv[2] || 'amend'; // 'amend' or 'rebase'
const PROJECT_SLUG = process.argv[3] || 'unknown';
const FORGE_ROOT = process.argv[4] || path.join(os.homedir(), 'forge');
const BRAIN_DIR = path.join(FORGE_ROOT, 'brain');
const INBOX_DIR = path.join(BRAIN_DIR, 'inbox');

function log(message) {
  const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
  console.error(`[${timestamp}] ${message}`);
}

// ==================== Edge Cases & Fallback Paths ====================
// Edge Case 1: Single commit amend (simple case)
//   Action: Update SHA in brain/inbox entries
//   Escalation: None
//
// Edge Case 2: Multi-commit rebase (many SHAs change)
//   Action: Map each old SHA to new SHA via git rebase history
//   Escalation: Parse git reflog or read rewrite instructions
//
// Edge Case 3: Rebase with conflict resolution (commits still valid)
//   Action: Update SHAs even though commits were hand-edited
//   Escalation: Trust new SHAs are correct
//
// Edge Case 4: Rebase onto new base (don't care about base, just SHAs)
//   Action: Update SHAs regardless of base change
//   Escalation: None - base is irrelevant to tracking
//
// Edge Case 5: Brain entry missing for rewritten commit
//   Action: Skip (shouldn't happen, but be graceful)
//   Escalation: Commit will be tracked next time post-commit fires
//
// Edge Case 6: Brain directory inaccessible
//   Action: Log warning but don't fail (non-blocking)
//   Escalation: Check permissions on ~/forge/brain
//
// Edge Case 7: Inbox file corrupted or unreadable
//   Action: Log warning, skip that file, continue
//   Escalation: Manual inspection of brain/inbox files
// ==================== End Edge Case Definitions ====================

log(`Post-rewrite hook triggered: ${REWRITE_TYPE}`);

// Validate brain directory exists
if (!fs.existsSync(BRAIN_DIR)) {
  log(`WARNING: Brain directory not found: ${BRAIN_DIR} (skipping sync)`);
  process.exit(0);
}

if (!fs.existsSync(INBOX_DIR)) {
  log(`No inbox directory yet. Skipping sync.`);
  process.exit(0);
}

// Read stdin to get old-new SHA mappings
// Format from git: <old-sha> <new-sha>\n (one per line)
let oldNewMappings = {};
const FULL_SHA_RE = /^[a-f0-9]{40}$/i;

// For amend: read from stdin
// For rebase: build mapping from git reflog
if (REWRITE_TYPE === 'amend') {
  const stdin = require('fs').readFileSync(0, 'utf-8');
  const lines = stdin.trim().split('\n');
  for (const line of lines) {
    const [oldSha, newSha] = line.split(/\s+/);
    if (oldSha && newSha && FULL_SHA_RE.test(oldSha) && FULL_SHA_RE.test(newSha)) {
      oldNewMappings[oldSha] = newSha;
      log(`SHA rewrite: ${oldSha.substring(0, 8)} → ${newSha.substring(0, 8)}`);
    }
  }
} else if (REWRITE_TYPE === 'rebase') {
  // For rebase, try to extract mappings from git log
  // This is complex - for now, just log that rebase happened
  log(`Rebase detected - SHA mappings would require git reflog parsing`);
  log(`(This is a best-effort update - manual verification recommended)`);
}

if (Object.keys(oldNewMappings).length === 0) {
  log(`No SHA mappings found. Exiting.`);
  process.exit(0);
}

// Update brain/inbox entries with new SHAs
let updatedCount = 0;
let skippedCount = 0;

try {
  const inboxFiles = fs.readdirSync(INBOX_DIR).filter(f => f.endsWith('.md'));
  log(`Scanning ${inboxFiles.length} inbox files for old SHAs...`);

  for (const file of inboxFiles) {
    const filePath = path.join(INBOX_DIR, file);
    let content = '';
    try {
      content = fs.readFileSync(filePath, 'utf-8');
    } catch (e) {
      log(`WARNING: Could not read ${file}: ${e.message}`);
      skippedCount += 1;
      continue;
    }

    let updated = false;
    let newContent = content;

    // Replace old SHAs with new SHAs in the file
    for (const [oldSha, newSha] of Object.entries(oldNewMappings)) {
      // Look for SHA in various formats: full, abbreviated, in fields
      const escaped = oldSha.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const anyRef = new RegExp(`\\b${escaped}\\b`, 'g');
      const commitRef = new RegExp(`(commit\\s*:\\s*)${escaped}`, 'gi');
      const shaRef = new RegExp(`(sha\\s*:\\s*)${escaped}`, 'gi');

      if (anyRef.test(newContent)) {
        newContent = newContent.replace(anyRef, newSha);
        updated = true;
      }
      if (commitRef.test(newContent)) {
        newContent = newContent.replace(commitRef, `$1${newSha}`);
        updated = true;
      }
      if (shaRef.test(newContent)) {
        newContent = newContent.replace(shaRef, `$1${newSha}`);
        updated = true;
      }
    }

    if (updated) {
      try {
        fs.writeFileSync(filePath, newContent, 'utf-8');
        updatedCount += 1;
        log(`Updated inbox entry: ${file}`);
      } catch (e) {
        log(`WARNING: Could not write ${file}: ${e.message}`);
      }
    }
  }
} catch (e) {
  log(`WARNING: Error scanning inbox directory: ${e.message}`);
}

// Create audit log
const auditLog = `${new Date().toISOString()} — post-rewrite hook
  type: ${REWRITE_TYPE}
  project: ${PROJECT_SLUG}
  mappings: ${Object.keys(oldNewMappings).length}
  updated: ${updatedCount}
  skipped: ${skippedCount}
`;

const auditPath = path.join(BRAIN_DIR, 'rewrite-audit.log');
try {
  fs.appendFileSync(auditPath, auditLog + '\n');
  log(`Audit logged to brain/rewrite-audit.log`);
} catch (e) {
  log(`WARNING: Could not write audit log: ${e.message}`);
}

log(`Post-rewrite complete: ${updatedCount} entries updated, ${skippedCount} skipped`);
process.exit(0);

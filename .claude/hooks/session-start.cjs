#!/usr/bin/env node

/**
 * session-start.cjs
 *
 * MANDATORY HOOK (D17)
 * Fires when Claude Code session starts, /clear, or context compacts
 * Reads using-forge/SKILL.md and inlines it as additionalContext
 *
 * Why this matters (Superpowers principle):
 * Every session must start with full Forge awareness. Without this inline,
 * you'll drift into unsafe patterns (skipping gates, rationalizing shortcuts).
 * This hook is the perimeter defense. It fires FIRST, before any other work.
 *
 * Cannot be skipped (this is a HARD-GATE):
 * - Rationalization: "I already know Forge, skip the boot"
 *   Truth: You drift. Pattern matching fails on new scenarios. Boot every time.
 *
 * Usage:
 *   This runs automatically via Claude Code session hook
 *   Requires: .claude/skills/using-forge/SKILL.md
 *
 * Cross-platform: works on Linux, macOS, Windows
 */

const fs = require('fs');
const path = require('path');

// Configuration
const SKILL_FILE = path.join(__dirname, '..', 'skills', 'using-forge', 'SKILL.md');

function log(message) {
  if (process.env.FORGE_HOOKS_DEBUG === '1') {
    console.error(`[session-start] ${message}`);
  }
}

function die(message) {
  console.error(`\n❌ FATAL: ${message}`);
  console.error(`\nSession cannot start without Forge bootstrap.`);
  console.error(`Fix: Check that .claude/skills/using-forge/SKILL.md exists.`);
  process.exit(1);
}

// ==================== Edge Cases & Fallback Paths ====================

// Edge Case 1: SKILL file doesn't exist
if (!fs.existsSync(SKILL_FILE)) {
  die(`using-forge/SKILL.md not found at ${SKILL_FILE}`);
}

// Edge Case 2: Cannot read SKILL file
let skillContent = '';
try {
  skillContent = fs.readFileSync(SKILL_FILE, 'utf-8');
} catch (e) {
  die(`Cannot read using-forge/SKILL.md: ${e.message}`);
}

// Edge Case 3: SKILL file is empty
if (!skillContent || skillContent.trim().length === 0) {
  die(`using-forge/SKILL.md is empty. Cannot bootstrap.`);
}

// ==================== Main Logic ====================

// Wrap skill content in EXTREMELY_IMPORTANT marker
const wrappedContent = `<EXTREMELY_IMPORTANT>
${skillContent}
</EXTREMELY_IMPORTANT>`;

const output = {
  hookSpecificOutput: {
    hookEventName: 'SessionStart',
    additionalContext: wrappedContent,
  },
};

process.stdout.write(JSON.stringify(output));

log(`✅ Forge bootstrap loaded and inlined`);
log(`Skill size: ${skillContent.length} chars`);

process.exit(0);

#!/usr/bin/env node
/**
 * pre-tool-use.cjs
 *
 * DESTRUCTIVE COMMAND INTERCEPTOR (HARD-GATE)
 * Fires before every Bash tool call. Intercepts patterns that are irreversible
 * or have high blast radius and requires explicit user confirmation before
 * proceeding. Prevents impulsive reflex actions (--no-verify bypasses, force
 * pushes, hard resets) that violate forge-letter-spirit.
 *
 * Blocks (asks for confirmation):
 *   - git push --force / -f
 *   - git reset --hard
 *   - git checkout -- .  / git restore .
 *   - git clean -f / -fd
 *   - git branch -D (force delete)
 *   - rm -rf <path>
 *   - DROP TABLE / DROP DATABASE
 *   - redis-cli FLUSHALL / FLUSHDB
 *
 * Does NOT block: normal reads, test runs, or standard dev operations.
 *
 * Input: JSON from stdin (Claude Code hook protocol)
 * Output: JSON to stdout (allow = exit 0 with no output; ask = permissionDecision)
 *
 * Cross-platform: works on Linux, macOS, Windows (via run-hook.cmd → bash → node)
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

// Read tool call from stdin
let input = '';
try {
  input = fs.readFileSync(0, 'utf-8').trim();
} catch (e) {
  // Cannot read stdin — allow by default
  process.exit(0);
}

let toolName = '';
let toolInput = {};

try {
  const parsed = JSON.parse(input);
  toolName = parsed.tool_name || parsed.toolName || '';
  toolInput = parsed.tool_input || parsed.input || {};
} catch (e) {
  // Cannot parse input JSON — allow by default
  process.exit(0);
}

// Only inspect Bash tool calls
if (toolName !== 'Bash') {
  process.exit(0);
}

const command = (toolInput.command || '').trim();
if (!command) {
  process.exit(0);
}

// ── Prompt injection canary check ──────────────────────────────────────────
// If the session canary token appears in the command, a tool result may have
// injected it to trigger execution. Block and warn.

const CANARY_FILE = path.join(os.homedir(), '.forge', '.canary');
let canaryToken = '';
try {
  if (fs.existsSync(CANARY_FILE)) {
    canaryToken = fs.readFileSync(CANARY_FILE, 'utf-8').trim();
  }
} catch (_) {
  // Canary file unreadable — skip check silently
}

if (canaryToken && command.includes(canaryToken)) {
  const output = {
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'ask',
      permissionDecisionReason:
        `[forge-pre-tool-use] CANARY TRIGGERED — POSSIBLE PROMPT INJECTION\n\n` +
        `Command: ${command}\n\n` +
        `The session canary token was found in this command. This may indicate a ` +
        `malicious tool result (web fetch, file read, API response) is attempting ` +
        `to execute arbitrary shell commands.\n\n` +
        `Do NOT proceed unless you manually inspected this command and verified ` +
        `it is safe and intentional.`,
    },
  };
  process.stdout.write(JSON.stringify(output));
  process.exit(0);
}

// ── Destructive patterns ────────────────────────────────────────────────────

const BLOCKED_PATTERNS = [
  {
    pattern: /git\s+push\s+(--force|-f)\b/i,
    reason:
      'git push --force rewrites remote history and cannot be undone by other contributors. ' +
      'Verify: (1) this is not main/master, or (2) you have explicit user approval, or (3) you are recovering a specific known incident.',
  },
  {
    pattern: /git\s+reset\s+--hard\b/i,
    reason:
      'git reset --hard permanently discards all uncommitted changes. ' +
      'Use git stash to save work first, or confirm there is truly nothing worth keeping.',
  },
  {
    pattern: /git\s+checkout\s+--\s*\./i,
    reason:
      'git checkout -- . discards all working directory changes. This cannot be undone without git stash or prior staging.',
  },
  {
    pattern: /git\s+restore\s+\.(\s|$)/i,
    reason:
      'git restore . discards all working directory changes. This cannot be undone.',
  },
  {
    pattern: /git\s+clean\s+(-[a-z]*f|-f[a-z]*)\b/i,
    reason:
      'git clean -f deletes untracked files permanently. Run git clean -n first to preview what will be deleted.',
  },
  {
    pattern: /git\s+branch\s+(-D\b|-d\s+-f\b|-fd\b|-df\b)/i,
    reason:
      'Force-deleting a git branch may destroy unmerged commits. Confirm the branch has been fully merged.',
  },
  {
    pattern: /\brm\s+-[a-z]*r[a-z]*f[a-z]*\s+[^\s-]/i,
    reason:
      'rm -rf is irreversible. Verify the exact path matches your intent and does not expand to an unexpected directory.',
  },
  {
    pattern: /\bDROP\s+(TABLE|DATABASE|SCHEMA)\b/i,
    reason:
      'DROP TABLE/DATABASE permanently destroys data. Confirm this is against an isolated eval/test database — not production or a shared environment.',
  },
  {
    pattern: /redis-cli\s+(.*\s+)?FLUSH(ALL|DB)\b/i,
    reason:
      'FLUSHALL/FLUSHDB wipes all Redis data instantly. Confirm this targets an isolated eval Redis instance — not a shared or production cache.',
  },
];

for (const { pattern, reason } of BLOCKED_PATTERNS) {
  if (pattern.test(command)) {
    const output = {
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'ask',
        permissionDecisionReason:
          `[forge-pre-tool-use] DESTRUCTIVE COMMAND — CONFIRM BEFORE PROCEEDING\n\n` +
          `Command: ${command}\n\n` +
          `Why this was flagged: ${reason}\n\n` +
          `To proceed: confirm this is intentional, you've verified the target, and there is no safer alternative.`,
      },
    };
    process.stdout.write(JSON.stringify(output));
    process.exit(0);
  }
}

// ── Skill-level allowed-tools check ───────────────────────────────────────
// If ~/.forge/.active-skill is set, verify the current tool is in that skill's
// allowed-tools frontmatter. Warns (asks) but does not hard-block (Approach A).

const ACTIVE_SKILL_FILE = path.join(os.homedir(), '.forge', '.active-skill');
let activeSkill = '';
try {
  if (fs.existsSync(ACTIVE_SKILL_FILE)) {
    activeSkill = fs.readFileSync(ACTIVE_SKILL_FILE, 'utf-8').trim();
  }
} catch (_) {
  // Unreadable — skip check
}

if (activeSkill) {
  // Find the skill's SKILL.md relative to the repo root (via __dirname)
  const repoRoot = path.resolve(__dirname, '..', '..');
  const skillFile = path.join(repoRoot, 'skills', activeSkill, 'SKILL.md');
  try {
    if (fs.existsSync(skillFile)) {
      const skillContent = fs.readFileSync(skillFile, 'utf-8');
      const fmMatch = skillContent.match(/^---\n([\s\S]*?)\n---/);
      if (fmMatch) {
        const fm = fmMatch[1];
        const toolsMatch = fm.match(/allowed-tools:\s*\n((?:\s+- \S+\n?)+)/);
        if (toolsMatch) {
          const allowedTools = toolsMatch[1]
            .split('\n')
            .map(l => l.replace(/^\s+- /, '').trim())
            .filter(Boolean);
          if (allowedTools.length > 0 && !allowedTools.includes(toolName)) {
            const output = {
              hookSpecificOutput: {
                hookEventName: 'PreToolUse',
                permissionDecision: 'ask',
                permissionDecisionReason:
                  `[forge-pre-tool-use] SKILL TOOL SCOPE WARNING\n\n` +
                  `Active skill: ${activeSkill}\n` +
                  `Attempted tool: ${toolName}\n` +
                  `Allowed tools: ${allowedTools.join(', ')}\n\n` +
                  `The skill '${activeSkill}' does not declare '${toolName}' in its allowed-tools list. ` +
                  `Proceed only if this tool use is intentional and within the skill's scope.`,
              },
            };
            process.stdout.write(JSON.stringify(output));
            process.exit(0);
          }
        }
      }
    }
  } catch (_) {
    // Skill file unreadable — skip check silently
  }
}

// Allow all other commands
process.exit(0);

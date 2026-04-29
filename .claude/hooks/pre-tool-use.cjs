#!/usr/bin/env node
/**
 * pre-tool-use.cjs
 *
 * PreToolUse hook: /freeze scope (Edit/Write/NotebookEdit/StrReplace), skill allowed-tools
 * (when PreToolUse is wired for that tool in hooks.json), then Bash-only checks:
 * canary-in-command and destructive command patterns (HARD-GATE / confirm).
 * Intercepts patterns that are irreversible
 * or have high blast radius and requires explicit user confirmation before
 * proceeding. Prevents impulsive reflex actions (--no-verify bypasses, force
 * pushes, hard resets) that violate forge-letter-spirit.
 *
 * Blocks (asks for confirmation):
 *   - Edit/Write/NotebookEdit/StrReplace outside the /freeze scope (if active)
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
 *
 * FORGE_DISABLE_CANARY=1 — skip canary-in-command check (and match session-start:
 * no canary file expected). Use only on trusted local machines; default is secure.
 *
 * FORGE_ROOT — optional absolute path to Forge repo root; defaults to two levels
 * above this hook (…/forge). Used to load tools/skill-tool-policy.json when present.
 *
 * Skill gate: when ~/.forge/.active-skill contains a skill name, allowed-tools are
 * taken from tools/skill-tool-policy.json if that file exists; else parsed from
 * skills/<name>/SKILL.md. Wire PreToolUse in hooks/hooks.json for each tool name
 * you want enforced (see matcher alternation there).
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const CASE_INSENSITIVE_FS = process.platform === 'win32' || process.platform === 'darwin';
let CACHED_CANARY_TOKEN = null;

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

if (!toolName) {
  process.exit(0);
}

const isBash = toolName === 'Bash';

// ── Freeze scope check ────────────────────────────────────────────────────
// If ~/.forge/.freeze exists, block Edit/Write/NotebookEdit/StrReplace to paths outside
// the frozen directory. Set by /freeze <dir>; cleared by /freeze off.

const FREEZE_FILE = path.join(os.homedir(), '.forge', '.freeze');
let frozenDir = '';
try {
  if (fs.existsSync(FREEZE_FILE)) {
    frozenDir = fs.readFileSync(FREEZE_FILE, 'utf-8').trim();
  }
} catch (_) {}

if (
  frozenDir &&
  (toolName === 'Edit' ||
    toolName === 'Write' ||
    toolName === 'NotebookEdit' ||
    toolName === 'StrReplace')
) {
  const resolvedFrozen = frozenDir.startsWith('~')
    ? path.join(os.homedir(), frozenDir.slice(1))
    : path.resolve(frozenDir);
  // Edit/Write use file_path; NotebookEdit uses notebook_path; StrReplace uses path
  const targetPath =
    toolInput.file_path ||
    toolInput.notebook_path ||
    toolInput.new_path ||
    toolInput.path ||
    '';
  if (!targetPath || String(targetPath).trim() === '') {
    const output = {
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'ask',
        permissionDecisionReason:
          `[forge-pre-tool-use] FREEZE SCOPE PATH UNKNOWN\n\n` +
          `Frozen directory: ${resolvedFrozen}\n` +
          `Tool '${toolName}' did not provide a valid target path. ` +
          `Refusing to proceed while /freeze is active.`,
      },
    };
    process.stdout.write(JSON.stringify(output));
    process.exit(0);
  }
  if (targetPath) {
    const resolvedTarget = path.normalize(path.resolve(targetPath));
    const normalizedFrozen = path.normalize(resolvedFrozen);
    const lhs = CASE_INSENSITIVE_FS ? resolvedTarget.toLowerCase() : resolvedTarget;
    const rhs = CASE_INSENSITIVE_FS ? normalizedFrozen.toLowerCase() : normalizedFrozen;
    const sep = path.sep;
    const outsideScope =
      lhs !== rhs &&
      !lhs.startsWith(rhs + sep);
    if (outsideScope) {
      const output = {
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'ask',
          permissionDecisionReason:
            `[forge-pre-tool-use] FREEZE SCOPE VIOLATION\n\n` +
            `Frozen directory: ${resolvedFrozen}\n` +
            `Attempted path:   ${resolvedTarget}\n\n` +
            `The /freeze lock is active. You may only edit files inside '${resolvedFrozen}'.\n\n` +
            `To proceed: confirm this is intentional and within scope, or run /freeze off to lift the lock.`,
        },
      };
      process.stdout.write(JSON.stringify(output));
      process.exit(0);
    }
  }
}

// ── Skill-level allowed-tools (when hooks.json wires PreToolUse for this tool) ─

const ACTIVE_SKILL_FILE = path.join(os.homedir(), '.forge', '.active-skill');
let activeSkill = '';
try {
  if (fs.existsSync(ACTIVE_SKILL_FILE)) {
    activeSkill = fs.readFileSync(ACTIVE_SKILL_FILE, 'utf-8').trim();
  }
} catch (_) {
  // Unreadable — skip
}

const forgeRoot = process.env.FORGE_ROOT
  ? path.resolve(String(process.env.FORGE_ROOT).trim())
  : path.resolve(__dirname, '..', '..');
if (process.env.FORGE_ROOT) {
  const home = os.homedir();
  if (!forgeRoot.startsWith(home + path.sep) && forgeRoot !== home) {
    process.exit(0);
  }
}

function resolveSkillAllowedTools(skillKey, skillFilePath, skillContent) {
  const policyPath = path.join(forgeRoot, 'tools', 'skill-tool-policy.json');
  try {
    if (fs.existsSync(policyPath)) {
      const policy = JSON.parse(fs.readFileSync(policyPath, 'utf-8'));
      const entry = policy.skills && policy.skills[skillKey];
      if (entry && Array.isArray(entry.allowed_tools) && entry.allowed_tools.length > 0) {
        return {
          allowedTools: entry.allowed_tools,
          isHardGate: !!entry.hard_gate,
          source: 'skill-tool-policy.json',
        };
      }
    }
  } catch (_) {
    // fall through to SKILL.md
  }
  if (!fs.existsSync(skillFilePath)) {
    return { allowedTools: [], isHardGate: false, source: null };
  }
  const fmMatch = skillContent.match(/^---\n([\s\S]*?)\n---/);
  if (!fmMatch) {
    return { allowedTools: [], isHardGate: false, source: null };
  }
  const fm = fmMatch[1];
  const toolsMatch = fm.match(/allowed-tools:\s*\n((?:\s+- \S+\n?)+)/);
  if (!toolsMatch) {
    const isHardGateSkill =
      /(^|\n)##\s*HARD-GATE\b/m.test(skillContent) ||
      /(^|\n)# [^\n]*\bHARD-GATE\b/m.test(skillContent) ||
      /^description:\s*"[^"]*\bHARD-GATE:/m.test(fm);
    return { allowedTools: [], isHardGate: isHardGateSkill, source: 'SKILL.md (no list)' };
  }
  const allowedTools = toolsMatch[1]
    .split('\n')
    .map(l => l.replace(/^\s+- /, '').trim())
    .filter(Boolean);
  const isHardGateSkill =
    /(^|\n)##\s*HARD-GATE\b/m.test(skillContent) ||
    /(^|\n)# [^\n]*\bHARD-GATE\b/m.test(skillContent) ||
    /^description:\s*"[^"]*\bHARD-GATE:/m.test(fm);
  return { allowedTools, isHardGate: isHardGateSkill, source: 'SKILL.md' };
}

if (activeSkill) {
  if (!/^[a-zA-Z0-9_-]+$/.test(activeSkill)) {
    process.exit(0);
  }
  const skillFile = path.join(forgeRoot, 'skills', activeSkill, 'SKILL.md');
  let skillContent = '';
  try {
    if (fs.existsSync(skillFile)) {
      skillContent = fs.readFileSync(skillFile, 'utf-8');
    }
  } catch (_) {
    skillContent = '';
  }
  const { allowedTools, isHardGate, source } = resolveSkillAllowedTools(
    activeSkill,
    skillFile,
    skillContent,
  );
  const toolAllowed = allowedTools.some(entry =>
    entry.endsWith('*') ? toolName.startsWith(entry.slice(0, -1)) : entry === toolName,
  );
  if (allowedTools.length > 0 && !toolAllowed) {
    const decision = isHardGate ? 'deny' : 'ask';
    const tail =
      decision === 'deny'
        ? `HARD-GATE skill '${activeSkill}' does not allow '${toolName}'. ` +
          `Unset ~/.forge/.active-skill or switch to a skill that lists this tool.`
        : `The skill '${activeSkill}' does not declare '${toolName}' in its allowed-tools list. ` +
          `Proceed only if this tool use is intentional and within the skill's scope.`;
    const output = {
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: decision,
        permissionDecisionReason:
          `[forge-pre-tool-use] SKILL TOOL SCOPE ${decision === 'deny' ? 'VIOLATION' : 'WARNING'}\n\n` +
          `Active skill: ${activeSkill}\n` +
          `Policy source: ${source || 'none'}\n` +
          `Attempted tool: ${toolName}\n` +
          `Allowed tools: ${allowedTools.join(', ')}\n\n` +
          tail,
      },
    };
    process.stdout.write(JSON.stringify(output));
    process.exit(0);
  }
}

// Canary + destructive-pattern checks are Bash-only
if (!isBash) {
  process.exit(0);
}

const command = (toolInput.command || '').trim();
if (!command) {
  process.exit(0);
}

// ── Prompt injection canary check ──────────────────────────────────────────
// If the session canary token appears in the command, a tool result may have
// injected it to trigger execution. Block and warn.

const canaryDisabled =
  process.env.FORGE_DISABLE_CANARY &&
  String(process.env.FORGE_DISABLE_CANARY).trim() === '1';

const CANARY_FILE = path.join(os.homedir(), '.forge', '.canary');
let canaryToken = '';
if (!canaryDisabled) {
  if (CACHED_CANARY_TOKEN !== null) {
    canaryToken = CACHED_CANARY_TOKEN;
  } else {
    try {
      if (fs.existsSync(CANARY_FILE)) {
        canaryToken = fs.readFileSync(CANARY_FILE, 'utf-8').trim();
      }
    } catch (_) {
      // Canary file unreadable — skip check silently
    }
    CACHED_CANARY_TOKEN = canaryToken;
  }
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
    pattern: /\brm\s+(?:-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*|--recursive(?:\s+--force)?|--force(?:\s+--recursive)?)\b/i,
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

// Allow all other Bash commands
process.exit(0);

#!/usr/bin/env node

/**
 * prompt-submit.cjs
 *
 * DISCIPLINE REINFORCER
 * Fires on every user message (UserPromptSubmit).
 * Injects a compact reminder of all active Forge HARD-GATEs into context
 * so the agent can't drift or rationalize shortcuts mid-conversation.
 *
 * Why this matters:
 * SessionStart fires once. After 20 messages agents forget gates exist.
 * This hook keeps the 8 non-negotiable rules in working context on every
 * turn — the cost is negligible, the drift prevention is real.
 *
 * Cannot be skipped:
 * - Rationalization: "I already know the gates, this is noise"
 *   Truth: You drift. Pattern matching degrades over long conversations.
 *   Consistent injection is the only defense against silent rationalization.
 *
 * Output: additionalContext injected into every prompt turn
 * Cross-platform: works on Linux, macOS, Windows
 */

const reminder = [
  '<forge-active-gates>',
  'HARD-GATES (non-negotiable, no exceptions):',
  '• forge-intake-gate    — PRD locked in brain before council',
  '• forge-council-gate   — All 4 surfaces + 5 contracts negotiated before spec freeze',
  '• forge-eval-gate      — Eval GREEN before any PR is raised',
  '• forge-worktree-gate  — Every task in a fresh worktree (D30)',
  '• forge-tdd            — Test written and watched FAIL before any implementation code',
  '• forge-verification   — Run commands and log real output before claiming done',
  '• forge-brain-persist  — Every decision committed to brain (never just in chat)',
  '• forge-trust-code     — Reviewer reads actual diff — never trusts implementer report',
  'If you are tempted to skip any gate: STOP. Invoke the skill. No exceptions.',
  '</forge-active-gates>',
].join('\n');

const output = {
  hookSpecificOutput: {
    hookEventName: 'UserPromptSubmit',
    additionalContext: reminder,
  },
};

process.stdout.write(JSON.stringify(output));
process.exit(0);

#!/usr/bin/env bash
# forge-doctor — quick host install health (Cursor + Claude Code plugin layouts).
# Reuses verify-forge-plugin-install.sh; adds symlink + settings.json + forge.mdc freshness.
#
# Usage: bash scripts/forge-doctor.sh   (from Forge repo root)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
EC=0

echo "=== Forge doctor (${FORGE_DIR}) ==="

if [[ -x "${FORGE_DIR}/scripts/verify-forge-plugin-install.sh" ]]; then
  bash "${FORGE_DIR}/scripts/verify-forge-plugin-install.sh" --all || EC=1
else
  echo "WARN: verify-forge-plugin-install.sh missing" >&2
fi

CL_CMD="${HOME}/.claude/commands/forge"
if [[ -L "${CL_CMD}" ]]; then
  target="$(readlink -f "${CL_CMD}" 2>/dev/null || readlink "${CL_CMD}")"
  if [[ "${target}" == "${FORGE_DIR}/commands" ]]; then
    echo "OK: ~/.claude/commands/forge -> ${FORGE_DIR}/commands"
  else
    echo "WARN: ~/.claude/commands/forge -> ${target} (expected ${FORGE_DIR}/commands)" >&2
  fi
else
  echo "WARN: ~/.claude/commands/forge not a symlink — run: bash scripts/install.sh --platform claude-code" >&2
fi

SETTINGS="${HOME}/.claude/settings.json"
if [[ -f "${SETTINGS}" ]] && command -v node >/dev/null 2>&1; then
  node <<'NODE' "${SETTINGS}" || true
const fs = require('fs');
const p = process.argv[1];
let d = {};
try { d = JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) {
  console.error('WARN: could not parse', p);
  process.exit(0);
}
const want = ['SessionStart', 'UserPromptSubmit', 'PreToolUse'];
for (const ev of want) {
  const arr = (d.hooks && d.hooks[ev]) || [];
  const forge = arr.filter((x) =>
    (x.hooks || []).some((h) => typeof h.command === 'string' && h.command.includes('forge-plugin'))
  );
  if (forge.length === 1) console.log('OK: settings.json ' + ev + ' — 1 forge-plugin hook');
  else console.error('WARN: settings.json ' + ev + ' — ' + forge.length + ' forge-plugin hook blocks (want 1); re-run install.sh --platform claude-code');
}
NODE
fi

CUR_RULE="${HOME}/.cursor/rules/forge.mdc"
CUR_PLUG="${HOME}/.cursor/plugins/local/forge/skills/using-forge/SKILL.md"
if [[ -f "${CUR_RULE}" ]] && [[ -f "${CUR_PLUG}" ]]; then
  if [[ "${CUR_RULE}" -ot "${CUR_PLUG}" ]]; then
    echo "WARN: ~/.cursor/rules/forge.mdc older than plugin skill — run: bash scripts/install.sh --platform cursor" >&2
  else
    echo "OK: ~/.cursor/rules/forge.mdc not older than plugin copy"
  fi
elif [[ ! -f "${CUR_RULE}" ]]; then
  echo "WARN: ~/.cursor/rules/forge.mdc missing — run install.sh --platform cursor" >&2
fi

exit "${EC}"

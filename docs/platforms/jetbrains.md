# Forge on JetBrains AI

## Prerequisites
- JetBrains IDE (IntelliJ, WebStorm, PyCharm, etc.) with AI assistant
- Git

## Installation

**Manual:** Copy the Forge guidelines template to each project you want Forge-enabled:

```bash
mkdir -p <your-project>/.junie
cp ~/forge/templates/junie-guidelines.md <your-project>/.junie/guidelines.md
```

**Via install script:**
```bash
cd ~/forge && bash scripts/install.sh --platform jetbrains
# Prints the manual instructions above
```

## Verification

Open the project in your JetBrains IDE. The AI assistant should follow Forge guidelines when working in the project. Ask it about Forge rules to verify.

## Keeping Forge updated

JetBrains does **not** load a live Forge plugin tree from `~/forge`; it uses **`.junie/guidelines.md`** copied into each project. When Forge’s template or your org’s fork moves forward:

```bash
cd ~/forge && git pull && bash scripts/install.sh --platform jetbrains
```

Then **re-copy** `templates/junie-guidelines.md` into each repo’s `.junie/guidelines.md` (or your internal equivalent). **How to hear about Forge releases** is the same as other hosts — **[README §4](../../README.md#4-keeping-forge-updated-how-you-hear-about-changes)**.

## Available Features

| Feature | Status |
|---|---|
| Guidelines context | Loaded from `.junie/guidelines.md` |
| Core rules | Non-negotiable rules enforced via guidelines |
| Anti-pattern table | Rationalization blocking |
| Skill references | Skills referenced by name in guidelines |

## How It Works

1. **Guidelines Loading:** JetBrains AI reads `.junie/guidelines.md` from the project root
2. **Rule Enforcement:** The guidelines file contains Forge's core rules and anti-pattern table
3. **Skill References:** Guidelines direct the AI to invoke specific skills by name

## Template Content

The template (`templates/junie-guidelines.md`) covers:
- What Forge is and how it works
- Core rules (intake first, council before code, worktree per task, eval gates, brain persistence)
- Anti-pattern blocking table
- Skill invocation guidance
- Directory structure reference

## Forge phase session styles

Junie / JetBrains AI follows **guidelines**, not Forge hooks. Use **planning-style** vs **execution-style** prompts per Forge phase — see **[`session-modes-forge.md`](session-modes-forge.md)**.

## Limitations

- **Manual setup:** Must copy template to each project individually
- **No skills system:** JetBrains AI does not have a skill loading mechanism
- **No hooks:** No SessionStart hook injection
- **No slash commands:** Commands are not available
- **No subagent dispatch:** No Agent tool
- **Context only:** JetBrains AI gets Forge's rules but not its full orchestration

## Troubleshooting

**Guidelines not loaded:**
- Verify file exists: `ls <project>/.junie/guidelines.md`
- Ensure JetBrains AI assistant is enabled in IDE settings
- Restart the IDE after adding the file

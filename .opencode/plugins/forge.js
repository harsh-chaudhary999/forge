// Forge plugin entry point for OpenCode
// Registers Forge skills, agents, and session-start hook

import { readFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const pluginRoot = resolve(__dirname, "../..");

export default {
  name: "forge",
  version: "1.0.0",
  description:
    "Multi-repo product orchestration. Takes a PRD and ships it end-to-end across any product stack.",

  hooks: {
    config: () => ({
      skills_dir: resolve(pluginRoot, "skills"),
      agents_dir: resolve(pluginRoot, "agents"),
      commands_dir: resolve(pluginRoot, "commands"),
      context_files: [resolve(pluginRoot, "CLAUDE.md")],
    }),

    "experimental.chat.system.transform": (system) => {
      try {
        const skillPath = resolve(
          pluginRoot,
          "skills/using-forge/SKILL.md"
        );
        const content = readFileSync(skillPath, "utf-8");
        const injection = [
          "<EXTREMELY_IMPORTANT>",
          "You have Forge superpowers. Below is the full content of the 'using-forge' skill:",
          "",
          content,
          "</EXTREMELY_IMPORTANT>",
        ].join("\n");
        return system + "\n" + injection;
      } catch {
        return system;
      }
    },
  },
};

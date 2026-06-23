# Glossary — Decision References (D1–D30)

The locked, externally visible Forge decisions surfaced in the glossary.

---

Key locked decisions (only externally visible decisions are listed here; D1–D4, D6–D12, D16–D23, D26–D29 are internal implementation decisions recorded in `brain/decisions/` and not surfaced in the glossary because they affect tooling internals, not skill-level behavior):

| Decision | Summary |
|---|---|
| D5 | No **LangChain-style agent frameworks** in **Forge plugin code**. **Product eval** may use **CDP, Playwright, Puppeteer, Appium, XCTest, MCP** on the host — **ask the operator** (browser MCP vs local CDP; **Appium MCP** vs ADB / XCTest for mobile) before locking the driver stack. |
| D13 | No runtime dependency on any external plugin at runtime |
| D14 | Trust code: spec-reviewer reads actual code, not reports or summaries |
| D15 | Skills are TDD'd against seed product pressure scenarios |
| D24 | HARD-GATE tags on every non-skippable step; red flags enforce them |
| D25 | Anti-Pattern preambles on every discipline-enforcing skill |
| D30 | Fresh worktree per project per task. No shared state. |

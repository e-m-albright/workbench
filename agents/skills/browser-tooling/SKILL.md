---
name: browser-tooling
description: Choose between Playwright and agent-browser. Use for UI bugs, deployed-page verification, browser automation, E2E coverage, or requests to inspect and interact with a webpage.
---

# Browser Tooling Router

These tools sit at **different layers of the stack**, not in competition:

```
AI Agent  →  agent-browser control layer  →  CDP  →  Chrome
             Playwright automation code   ──────────┘
```

- **Playwright** — deterministic automation framework. Use code for known workflows, production jobs, and regression tests.
- **agent-browser** (Vercel Labs) — agent-native browser CLI. Use compact snapshots and semantic actions for exploration, unfamiliar pages, and supervised interaction.

**The default stack is Playwright + agent-browser.** There are no standing browser MCP servers: the native Pi wrapper provides Agent Browser on demand without an MCP context tax.

## Decision tree

**"Look at this page" / "Did the deploy work?" / smoke check / drive a flow** → **agent-browser CLI** (default)
- `agent-browser open <url>`, then `click @e2` / `fill @e3 "…"` / snapshot. ~200–400 tokens/page.
- First choice for almost everything an agent does in a browser.

**Known multi-step portal or recurring read workflow** → **Playwright helper**
- Encode fixed routes, selectors, validation, and stop-before-submit boundaries in code.
- Keep the browser headed when a user must watch, authenticate, or intervene.

**"Catch this regression forever" / deterministic scrape / production workflow** → **Playwright tests**
- Free per run. Write tests in the project's E2E test directory (e.g. `web/tests/e2e/`). For WebRTC apps, use Chromium's fake-media flags (see below).
- After root-causing a bug with the CLI, write a Playwright test so it can never silently regress.

**"Long agentic flow across 20 screens where selectors rot"** → **Stagehand** (per-project)
- `@browserbasehq/stagehand` — natural-language `act`/`extract`/`observe`. Costs LLM tokens per run. Install per-project, not global.

**"Why is this slow / what error fired / network looks wrong"** → no standing tool
- We dropped the Chrome DevTools MCP (overlap + context tax). If you genuinely need perf/network/console traces, launch `npx chrome-devtools-mcp@latest` ad-hoc for that one session, then drop it — don't make it standing.

## Token budget reference

| Tool | Layer | Cost shape |
|------|-------|------------|
| Playwright tests in CI | framework | 0 / run (one-time write cost) |
| agent-browser CLI | agent control | ~200–400 tokens / page · no MCP tax |
| Playwright helper | deterministic workflow | implementation cost, then no model navigation cost |
| Stagehand | agent framework | LLM tokens / test run |
| ~~Playwright MCP~~ | dropped | was ~13.7k always-on context |
| ~~Chrome DevTools MCP~~ | dropped | was ~18k always-on context · launch ad-hoc if ever needed |

## Why CLI, not MCP, for browser control

An MCP server taxes every session's context with its tool schemas whether or not you browse. Agent Browser plus Pi's native wrapper already provides the agent-facing control surface on demand. Playwright-the-framework is a different layer from Playwright MCP: keep the framework for deterministic code and tests, while leaving the MCP disabled.

## Workflow patterns

**Bug report → permanent test:**
1. Reproduce or inspect with `agent-browser`.
2. Once root-caused, write a Playwright test so it is protected forever.

**WebRTC (example config, e.g. Daily.co projects):** Playwright tests with Chromium fake-media flags — `--use-fake-device-for-media-stream`, `--use-fake-ui-for-media-stream`, `--use-file-for-fake-audio-capture=path.wav`, `--use-file-for-fake-video-capture=path.y4m`.

## See also

- Full guide with examples: [browser-tooling.md](../../../playbook/knowledge/browser-tooling.md)
- [testing](../testing/SKILL.md) — writing the actual deterministic tests

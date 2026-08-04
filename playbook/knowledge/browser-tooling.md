# Browser Tooling for AI Agents

> **Last reviewed**: 2026-07-30 - removed PinchTab after the standby experiment produced no unique use case; Agent Browser gained the visible, persistent, and diagnostic capabilities that had motivated the overlap.

A tiered system for inspecting, testing, and debugging UIs from an AI agent. Pick the cheapest tier that does the job. **The endorsed stack is Playwright for deterministic code plus Agent Browser for agent-driven exploration and supervised interaction.** No browser MCP servers are loaded.

The tools sit at different layers: Playwright is the automation framework for known workflows, production jobs, and regression tests; Agent Browser is the agent-native control CLI for unfamiliar pages and interactive diagnosis. Both ultimately control Chrome over CDP.

---

## The tiers

| Tier | Tool | Job | Cost shape |
|------|------|-----|-----------|
| **1** | Playwright tests and helpers | Regression net, stable portal workflow, deterministic scrape | implementation cost, then no model navigation cost |
| **2** | `agent-browser` CLI | Default agent browsing / "look at this page" | ~200–400 tokens / page · no MCP tax |
| **5** | Stagehand (per-project) | Long agentic flows, selector-resilient | LLM tokens / run |
| ~~3a~~ | ~~Playwright MCP~~ | dropped — agent-browser covers it | was ~13.7k always-on |
| ~~4~~ | ~~Chrome DevTools MCP~~ | dropped — launch ad-hoc if ever needed | was ~18k always-on |

---

## Tier 1 — Playwright tests in CI

**Goal**: Catch regressions automatically, forever, free per run.

```bash
# Inside the project
deno x -A npm:playwright install chromium
deno x -A npm:playwright test
```

**WebRTC / Daily.co setup** — Daily's "headless robot" pattern uses Chromium launch flags:

```typescript
// playwright.config.ts
use: {
  launchOptions: {
    args: [
      '--use-fake-ui-for-media-stream',       // skip permission prompt
      '--use-fake-device-for-media-stream',   // test-pattern video
      '--use-file-for-fake-audio-capture=fixtures/audio.wav',
      '--use-file-for-fake-video-capture=fixtures/video.y4m',
    ],
  },
}
```

**When to write Tier 1 automation**: after root-causing a bug, or when a repeated portal workflow has known routes, selectors, validation rules, and approval boundaries. Use a test for regression coverage and a small headed helper for supervised authenticated workflows.

---

## Tier 2 — Token-cheap CLIs

### agent-browser

```bash
# Already installed globally via dotfiles (macos/brew.sh)
agent-browser open https://example.com
agent-browser inspect "button:has-text('Submit')"
agent-browser screenshot --output /tmp/page.png
```

**Best for**: "Did the deploy land? What does this study look like? Smoke-check this page."

### Removed: PinchTab

The local control-server experiment was removed on 2026-07-30. Its proposed job - persistent, visible, authenticated agent browsing - is now covered by Agent Browser profiles, headed sessions, streaming, and the native Pi wrapper. The always-on HTTP control plane added attack surface and operational state without a demonstrated workflow advantage. Reconsider only if multiple independent clients need to share and orchestrate one durable local browser service.

---

## Dropped: browser MCP servers (2026-06-09)

Playwright MCP and Chrome DevTools MCP were removed from `agents/shared/mcp-servers.json`. An MCP server taxes every session's context with its tool schemas whether or not browsing occurs; Agent Browser plus Pi's native wrapper provides the interactive agent-facing control surface on demand.

If you ever need DevTools-style perf/network/console forensics, launch it **ad-hoc** for that one session and drop it after — don't make it standing:

```bash
npx chrome-devtools-mcp@latest         # one-off, not in the managed config
```

Note: Playwright-the-*framework* (Tier 1 tests) is a different layer than Playwright-*MCP* (agent control). We keep the framework, drop the MCP.

---

## Tier 5 — Stagehand (per-project)

```bash
# Inside the project
npm install @browserbasehq/stagehand
```

```typescript
import { Stagehand } from '@browserbasehq/stagehand';

const stagehand = new Stagehand({ env: 'LOCAL' });
await stagehand.init();
await stagehand.page.goto('https://example.com');
await stagehand.page.act('click the submit button');
const data = await stagehand.page.extract({ instruction: 'get the order total' });
```

**Reach for it when**: A test flow spans many screens where the UI redesigns frequently and selector-based tests rot faster than they catch bugs.

**Skip it when**: Selector-based Playwright tests are still working — Stagehand costs LLM tokens per run.

---

## Common workflow

1. User reports a UI bug.
2. **Tier 2** (`agent-browser`): inspect and reproduce from a quick page snapshot or supervised headed session.
3. **Ad-hoc** (`chrome-devtools-mcp` for one session): only if a performance problem needs diagnostics Agent Browser cannot provide.
4. **Tier 1** (Playwright): write a regression test, deterministic reader, or headed portal helper once the flow is known.

For greenfield long flows, consider **Tier 5** (Stagehand) instead of Tier 1 if the UI is volatile.

---

## What we skip and why

- **Claude in Chrome / browser extensions**: can't run headless, can't run in CI.
- **Browserbase cloud (Stagehand managed)**: optional. Only if we hit captcha/anti-bot or need cross-machine session replay. Local Stagehand covers most needs free.
- **Browser-use** (the SDK): overlaps with Stagehand. Pick one.

---

## Sources

- *Playwright vs. Chrome DevTools MCP: Driving vs. Debugging* — covers the cost/specialty split
- *I Tested Every Browser Automation Tool for Claude Code* — token benchmarks
- *Daily.co: How to make a headless robot to test WebRTC* — fake-device flags
- *Stagehand* — Browserbase, https://github.com/browserbase/stagehand
- *agent-browser* — Vercel Labs, https://agent-browser.dev

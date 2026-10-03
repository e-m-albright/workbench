# Agent skills

Package repeatable workflows, executable verification, and operational knowledge with progressive disclosure. The [authoring skill](../../agents/skills/skill-authoring/SKILL.md) owns the procedure for changing Workbench skills.

## Skills are operational packages, not prompt fragments

Anthropic's internal Claude Code practice reinforces the existing Workbench model: a useful skill is a folder that can contain instructions, scripts, references, data, and assets, with progressive disclosure controlling what enters context. The most valuable content is accumulated operational knowledge, especially edge cases and gotchas, rather than generic best practices. A skill description is a routing interface for the model, so it should state when the capability applies more precisely than it summarizes the content for a human.

Anthropic reports its clearest internal quality gains from verification skills. That supports a priority order for Workbench: package executable checks and proven runbooks before adding advisory prose; let deterministic policy live in hooks or code; use temporary on-demand hooks when a task needs stricter controls than the project default. Lightweight skill-local logs can help repeated workflows learn, but durable project facts still belong in the repository's canonical documentation.

Interactive HTML artifacts are useful when supervision benefits from direct manipulation: editing a plan, comparing layouts, annotating a proposal, or inspecting a generated visualization. Markdown remains the better durable format when diffability, search, and long-term maintenance matter. The artifact earns its complexity only when it lowers review cost or reveals state that prose cannot.

Sources: [Anthropic on internal skills](https://claude.com/blog/lessons-from-building-claude-code-how-we-use-skills) and [Thariq Shihipar on interactive artifacts](https://www.lennysnewsletter.com/p/html-is-the-new-markdown-how-anthropic).

- **[everything-claude-code (affaan-m)](https://github.com/affaan-m/everything-claude-code)** -- "Harness performance system" bundling 60+ agents, 228+ skills, rules, hooks, and MCP configurations for Claude Code, Cursor, OpenCode, etc. Installable as Claude Code plugin or manually. **Mine for patterns** before adopting wholesale -- the agents/skills are uneven quality and the bundle is large.

- **[awesome-agent-skills (VoltAgent)](https://github.com/VoltAgent/awesome-agent-skills)** -- Curated index of 1,100+ agent skills from official teams (Anthropic, Google, Vercel, Stripe) and community contributors. Targets Claude Code, Codex, Gemini CLI, Cursor. Browse before writing a new skill from scratch.

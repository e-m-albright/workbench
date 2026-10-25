# Antigravity CLI

Re-enabled at the owner's request on 2026-10-25. Dotfiles owns the
`antigravity-cli` Homebrew cask and its `agy` binary; Workbench owns global
instructions and skills. The IDE and Gemini CLI remain retired.

`workbench sync antigravity` deploys `agents/shared/rules.md` to
`~/.gemini/AGENTS.md` and the canonical skill trees to
`~/.gemini/antigravity-cli/skills`. The usual preview, rules-only, no-skills,
backup, and drift behavior applies. `all` includes this target for the personal
profile; the work profile excludes it. Unmanaged skills are reported as external.

Settings, authentication, plugins, MCP configuration, and session state remain
untouched. There is no model default or permission preset imposed by Workbench.
Launch `agy --sandbox` to request the vendor terminal sandbox. This is not the
whole-process Workbench boundary: there is no managed shortcut, isolated home,
credential enrollment, or `workbench native` integration for Antigravity.
Adding one requires dedicated lifecycle and containment tests, not just another
launcher alias. No model request or authenticated runtime behavior was tested
when introducing this integration.

Current native contracts:

- [Global rules](https://antigravity.google/docs/rules/) include
  `~/.gemini/AGENTS.md`; repository `AGENTS.md` is discovered natively. The
  documented single-rule limit is 24,000 bytes.
- [CLI skills](https://antigravity.google/docs/skills/?tab=cli) use
  `~/.gemini/antigravity-cli/skills` and become interactive slash commands.
- [CLI settings](https://antigravity.google/docs/cli/using/) live in
  `~/.gemini/antigravity-cli/settings.json`.
- [Permissions](https://antigravity.google/docs/permissions/) and the vendor
  sandbox remain distinct from Workbench's isolation contract.

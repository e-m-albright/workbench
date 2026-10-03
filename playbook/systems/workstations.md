# Workstation tools and remote access

Public research on editors, terminals, capture tools, and remote access. The host repository owns installation and configuration; private workflows stay with their owner.

## Personal capture and notes

- **[Memos](https://usememos.com/)** ([GitHub](https://github.com/usememos/memos)) -- **WATCH FOR PRODUCT DISCIPLINE (reviewed 2026-09-14).** An MIT-licensed, self-hosted chronological Markdown feed for untitled notes, links, snippets, tasks, and attachments, with search, tags, pins, selective publishing, a web clipper, and REST/gRPC interfaces. Its strongest idea is deliberately narrower than a personal operating system: capture without choosing a title, folder, template, or workspace, then retrieve from one quiet timeline. Do not adopt it as a second canonical store or rebuild the existing capture path around it; Apple Notes already owns quick capture, while the private operating application owns structured actions, relationships, reference, and projections. Study its default-open composer, feed-shaped recency, and plain positioning when capture or resurfacing feels too formal. Trial only if Apple Notes capture repeatedly fails because captured items do not remain visible, and require an explicit ingestion-and-deletion path before any trial. As of review, the project reports version 0.30.0, 63k GitHub stars, 417 contributors, SQLite/MySQL/PostgreSQL support, and zero telemetry by default; popularity supports maturity, not fit.

## Terminal Stack

> Host installation state is owned by the dotfiles package manifest. This section records evaluation posture, including installed tools that may now be retirement candidates.

- **[Coldtea](https://www.coldtea.ai/)** -- **WATCH (reviewed 2026-09-14).** A macOS agentic development environment that wraps existing coding agents with task-board sync, per-task worktrees, shared plans and logs, pull-request and production browser testing across web and mobile, and monitoring ingestion that reproduces failures and files new work. The full software-delivery loop is more distinctive than its bundled terminal, editor, browser, or parallel-agent surfaces, which overlap the current local stack. Do not adopt it as another general agent workspace. Revisit for a bounded comparison when maintaining preview and production regression coverage becomes a recurring burden; test one real authenticated flow against the existing Playwright and Agent Browser path, and scrutinize source access, cloud execution, monitoring-data handling, generated issue quality, failure reproducibility, and pricing before enabling integrations. Source: [official product overview](https://www.coldtea.ai/).
- **[Warp](https://www.warp.dev/)** -- Terminal explicitly designed for **multi-agent dev**. Supports Codex, OpenCode, Gemini CLI as first-class threads with vertical tabs, configurable per-agent metadata (branch, worktree, PR), unified notification center. Send inline comments/snippets/files directly to a running agent session. Evaluate when juggling multiple Claude Code instances across worktrees becomes painful in plain Ghostty.
- **[Omarchy](https://omarchy.org/)** -- Attractive, opinionated Linux distribution, but there is no reason to move this macOS workflow onto an operating system bundle to acquire tools already chosen individually. Appreciate the integration; do not trial it without a Linux-machine need.
- **[Herdr](https://herdr.dev/)** -- Polished persistent terminal and coding-agent runtime, but it answers the same process-survival and workspace-management question already rejected for tmux, cmux, Zellij, and fleet control planes. The preferred local interaction remains ordinary Ghostty tabs, usually numbered 1-6, with Paseo owning agent continuity. Revisit only if a real process must survive terminal closure and neither a project service nor Paseo can own it.
- **[Yazelix](https://github.com/luccahuguet/yazelix)** -- Reproducible terminal IDE bundling **Yazi + Zellij + Helix** with an AI-aware layout. No longer an aspiration: the Zellij layer has not earned regular use, so adding a larger terminal-IDE bundle would compound the wrong surface.
- **[Zellij](https://zellij.dev/)** -- **Retired 2026-08-26.** Its web client, layouts, multiplayer attachment, and serialized resurrection were not used. Paseo owns agent continuity and the phone experience; there is no remaining phone-shell requirement.
- **tmux** -- **Retired 2026-08-26.** Do not introduce a terminal multiplexer without a demonstrated local process-continuity need. It is not part of the Paseo mobile path.
- **[Atuin](https://atuin.sh/)** -- Command history in SQLite with full-screen fuzzy search on the up-arrow + cross-machine sync. Evaluate as a `Ctrl-R` upgrade.
- **[Lazygit](https://github.com/jesseduffield/lazygit)** -- TUI for git, faster than CLI for hunk staging, rebasing, diffs. **Especially valuable alongside AI agents** -- file-level diff view gives precise control over every AI-touched line before committing.
- **[Lazydocker](https://github.com/jesseduffield/lazydocker)** -- Same TUI pattern for containers.
- **[Btop](https://github.com/aristocratos/btop)** -- Prettier, faster htop replacement.
- **[eza](https://eza.rocks/)** -- `ls` with git status, icons, tree mode. Successor to `exa`.
- **[bat](https://github.com/sharkdp/bat)** -- `cat` with syntax highlighting + git markers; doubles as a pager for other tools (`--pager`).
- **[delta](https://github.com/dandavison/delta)** -- Git's diff viewer rewritten: side-by-side, syntax highlighting, proper word-level highlights.
- **[difftastic](https://difftastic.wilfred.me.uk/)** -- **Structural (AST-based) diffs** that ignore reformatting noise. Devastating once you try it on a refactor PR.
- **[Starship](https://starship.rs/)** -- Fast cross-shell prompt surfacing git, k8s context, exec time, language versions. Cross-platform.

> **Starship — EVALUATED 2026-06-04, WATCH (not adopting).** Hands-on trial: installed, built a config mirroring the hand-rolled `amuse` zsh theme *exactly*, then a "personality" config (language/tool versions, `❯`, ops modules). Verdict: marginal value for this workflow. The features that justify the dependency are contextual-safety modules that stay **dark** here — no `aws`/`gcloud`/`terraform` installed, **0** kube contexts, **1** SSH host. Language versions are low-signal when you don't juggle toolchains, and the daily prompt is near-identical to what's already hand-rolled in `shell/amuse.zsh-theme`. Async git is the only real engine win and a decently big polyglot work repo didn't hitch. **Revisit if** the workflow shifts to multi-cluster / multi-account ops (`⎈ context`, `☁ aws-profile` are genuine prod-safety wins) or many remote shells (hostname-on-SSH). **Spin-off win banked regardless:** the A/B drove real `amuse` upgrades — richer git (ahead/behind, staged/unstaged/untracked counts), command duration, exit codes, and worktree / `cc:` profile context. Uninstalled; trial configs removed.
- **[sesh](https://github.com/joshmedeski/sesh)** -- **Rejected with the tmux retirement.** A picker around a multiplexer has no job when the underlying multiplexer has no job. Revisit only if tmux first earns a concrete local continuity workflow.
- **[fish](https://fishshell.com/)** -- Shell with sane defaults + autosuggestions without a plugin manager. Alternative to zsh+plugins.

## File transfer

- **[croc](https://github.com/schollz/croc)** -- Useful encrypted relay-based transfer when two machines cannot address each other directly and a short code is the desired exchange mechanism. It does not replace `rsync` for this workflow's normal local, SSH, incremental, or repeatable transfers. Revisit only for a recurring ad hoc transfer across network boundaries where `rsync` is genuinely awkward.

## Editors / Terminals

- **[Zed editor](https://zed.dev)** -- Modern editor written in Rust, GPU-accelerated rendering. Open-sourced Jan 2024. Positions as a native-performance alternative to Cursor/VS Code -- the tradeoff is a smaller extension ecosystem (no VS Code Marketplace). Built-in real-time collaborative editing ("channels") and an agentic AI edit mode. Worth a side-by-side with Cursor specifically for Python work given recent LSP investment; less compelling if our Cursor extension setup is load-bearing. Python, Markdown, LSP-first. Reading: [Making Python in Zed Fun](https://zed.dev/blog/making-python-in-zed-fun), [Settings UI rebuild](https://zed.dev/blog/settings-ui).
- **[Ghostty 1.3.0](https://www.xda-developers.com/ghostty-13-terminal-makes-finding-your-previous-commands-a-ton-easier/)** -- Modern terminal. Improved previous-command search.

## Home / Personal

- **[Scrypted](https://github.com/koush/scrypted)** -- Home automation platform. Evaluate as a HomeKit / NVR alternative.

## Remote Access

### Cross-harness mobile agent control

Paseo over Tailscale is the adopted phone surface for Pi, Claude Code, and Codex.
Use the [Paseo skill](../../agents/skills/paseo-management/SKILL.md) for operations.
The rejected terminal, continuity, and fleet alternatives and their revisit
conditions live in [tombstones](../../docs/decisions/tombstones.md#terminal-continuity-mobile-access-and-process-runners).

### BitBang (watch)

[BitBang CLI](https://github.com/richlegrand/bitbang-cli) is an interesting
**ad-hoc access** option, not part of the installed stack. As of 2026-08-04, its
single Go binary can expose a shell, a bounded file tree, or an HTTP proxy through
a capability URL. A browser is enough on the connecting side; WebRTC usually
provides a direct path through NAT, with encrypted TURN relay fallback. It needs
no account, inbound port, VPN, or preinstalled client. A six-digit, verbally
verified pairing flow can save credentials for later CLI connections.

The security design is thoughtful: the URL fragment holds the access secret and
is not sent to the signaling server; endpoint identity and DTLS fingerprints are
verified independently; and the server or TURN relay should see metadata and
ciphertext, not payloads. The important limits are:

- The URL is a bearer capability. The default `bitbang serve` grants shell,
  files, and proxy access, so a leaked URL has a large blast radius; use a
  capability-specific subcommand, optional PIN, and ephemeral identity instead.
- Browser clients still trust JavaScript delivered by the signaling server. The
  installed CLI avoids that code-delivery boundary, or the server can be
  self-hosted.
- This is a young, pre-1.0 project. The latest release was `0.4.7`, published
  2026-07-31; only the latest release is supported, the macOS binaries are not
  notarized, and the security policy says the project has a very small team.
- It does not serve the current workflow. The owner does not need phone terminal access; Paseo over Tailscale already owns agent continuity and mobile control.

**Disposition:** out for daily phone access. Re-evaluate only for a concrete temporary shell-sharing need. If trialed, use a non-sensitive test account, pin a release, inspect the installer, and serve only the narrow capability required.

Primary sources: [CLI documentation](https://github.com/richlegrand/bitbang-cli),
[trustless-signaling design](https://github.com/richlegrand/bitbang/blob/main/trustless-signaling.md),
[security policy](https://github.com/richlegrand/bitbang-cli/blob/main/SECURITY.md),
and [v0.4.7 release](https://github.com/richlegrand/bitbang-cli/releases/tag/0.4.7).

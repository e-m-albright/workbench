# Version control

Compare repository hosting and version-control workflows, including coordination under concurrent agent work.

## Git Hosting

- **[Codeberg](https://codeberg.org)** -- Non-profit git hosting (Codeberg e.V., Berlin) on the OSS Forgejo platform. Community-governed, EU-hosted, no tracking/ads/data sale. Built-in CI and Pages. Free (donations / membership). Evaluate for hosting OSS outside big tech or for EU data residency with a non-commercial ethos.
- **[GitLab](https://about.gitlab.com)** -- Single-platform DevSecOps: git + CI/CD + planning + integrated SAST/SCA/secrets/DAST + AI agents (GitLab Duo). OSS Community Edition (self-hosted) plus SaaS at gitlab.com. Premium/Ultimate paid tiers; Ultimate adds the security suite. Evaluate when you want a one-vendor full stack with strong self-hosted story or built-in security/compliance reporting.
- **[Sourcehut](https://sr.ht)** -- Minimalist OSS forge by Drew DeVault: git/Mercurial, mailing lists, issue tracking, CI, wikis, chat -- email-driven workflows. No JavaScript required, no tracking, no AI features; patches via `git send-email`. Paid subscription supports the project; still public alpha. Evaluate for maximum data portability and terminal/email-native workflow.

## Concurrent agent traffic

[Cursor's Git at any scale](https://cursor.com/blog/git-at-any-scale) describes version-control infrastructure for very high concurrent agent traffic. It is an infrastructure reference for a fleet with measured contention, not a reason to replace ordinary Git worktrees in Workbench. The [agent capability patterns](../agents/orchestration.md#bounded-local-delegation) own the current concurrency ceiling.

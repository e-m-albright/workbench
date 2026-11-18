# Version control

Compare repository hosting and version-control workflows, including coordination under concurrent agent work.

## Git Hosting

- **[Codeberg](https://codeberg.org)** -- Non-profit git hosting (Codeberg e.V., Berlin) on the OSS Forgejo platform. Community-governed, EU-hosted, no tracking/ads/data sale. Built-in CI and Pages. Free (donations / membership). Evaluate for hosting OSS outside big tech or for EU data residency with a non-commercial ethos.
- **[GitLab](https://about.gitlab.com)** -- Single-platform DevSecOps: git + CI/CD + planning + integrated SAST/SCA/secrets/DAST + AI agents (GitLab Duo). OSS Community Edition (self-hosted) plus SaaS at gitlab.com. Premium/Ultimate paid tiers; Ultimate adds the security suite. Evaluate when you want a one-vendor full stack with strong self-hosted story or built-in security/compliance reporting.
- **[Sourcehut](https://sr.ht)** -- Minimalist OSS forge by Drew DeVault: git/Mercurial, mailing lists, issue tracking, CI, wikis, chat -- email-driven workflows. No JavaScript required, no tracking, no AI features; patches via `git send-email`. Paid subscription supports the project; still public alpha. Evaluate for maximum data portability and terminal/email-native workflow.

## Concurrent agent traffic

**Read in full:** Vicent Martí, [Git at any scale](https://cursor.com/blog/git-at-any-scale), Cursor, 2026-08-18; reviewed 2026-11-17. Preserve the original article for its worked progression from network filesystems to packfile replication to Cursor's Continuity architecture. It is an infrastructure reference for measured fleet contention, not a reason to replace ordinary Git worktrees. The [agent capability patterns](../agents/orchestration.md#bounded-local-delegation) own the current concurrency ceiling.

The central mechanism is to separate durable truth from disposable serving copies. Continuity persists pushed packfiles in an object-store write-ahead log before acknowledging them, publishes reference transactions through a compare-and-swap update to the log index, and materializes ordinary Git repositories on local NVMe storage. Local Git keeps packfile traversal fast; a remote object lookup for every graph edge would introduce serial network round trips. Reads check the authoritative index and catch up before serving. UDP notifications accelerate replication but are not the correctness mechanism. Compaction is performed once and its results distributed, rather than independently repeated on every replica.

This does not eliminate coordination: it relies on the object store's conditional-write and consistency contract. Compatible API syntax alone does not establish identical behavior on another S3-compatible service. Cursor reports synthetic linear read scaling to 100 replicas and different push throughput on S3 Standard versus Express One Zone; these are vendor workload results, not a universal performance or failure-domain guarantee.

Useful elsewhere: commit durable state before acknowledging success, make caches reconstructible, separate correctness from routing and notification optimizations, and share expensive derived work. Foolhardy here: build a Git forge, adopt a log architecture for a small local store, or switch hosting merely for agent-scale throughput. Compare providers only when measured availability, clone/push latency, concurrency, residency, migration compatibility, or total cost justify it.

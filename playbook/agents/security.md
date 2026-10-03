# Agent security

Keep untrusted content, execution, credentials, and consequential authority behind explicit boundaries. The [Workbench isolation contract](../../docs/security/isolation.md) owns the implemented local controls.

## Trust machinery is the autonomy limit

The practical ceiling on autonomy is set by sandboxing, permission scope, verification, attribution, spend limits, and kill switches. Use operating-system containment for untrusted execution, with explicit network and credential boundaries. A model's approval or a tool-call guardrail does not provide that containment. Workbench's current enforcement is specified in its [isolation contract](../../docs/security/isolation.md).

OpenAI's Windows sandbox illustrates why containment is a composition problem rather than a single switch. Its unelevated path combines a synthetic security identifier, access-control lists, write-restricted tokens, and explicit protection for repository metadata. Its elevated path uses separate local accounts for networked and offline work, restricted tokens, and firewall policy. The reusable design is to separate online and offline identities, grant only the workspace access each needs, and layer operating-system identity, filesystem, process, and network controls. No one Windows primitive supplies the whole boundary.

## Passive retrieval can become code execution

Johann Rehberger demonstrated a targeted indirect prompt-injection chain against Claude Code Opus 5 Auto Mode. A website caused the preferred fetch tool to fail, the agent fell back to `curl`, followed a redirect to an archive, rejected the supplied binary, wrote its own Python decoder, and ran it inside the attacker-controlled extracted directory. Python module shadowing loaded a malicious `struct.py` during an apparently benign `base64` import. In small samples, the reported variants achieved their intended effects in three of five to four of five runs.

The important mechanism is not one poisoned filename. Goal pursuit converted a passive summary request into retrieval, extraction, code generation, and execution through individually plausible steps. A model-written replacement utility is not trusted when its imports resolve from attacker-controlled state. A permission classifier that judges one command at a time cannot enforce provenance across that chain.

### Disposition

- Keep external retrieval on dedicated read-only browser or connector tools. If they fail, stop rather than switching to a shell network client merely to complete a summary.
- Pi blocks `curl` and `wget` as a concrete tripwire, but this is not containment; other runtimes can still provide network access.
- Never execute an interpreter, build tool, decoder, or model-written helper from an untrusted download or extracted directory outside an operating-system sandbox.
- Use an explicit operating-system sandbox plus network egress restrictions for execution involving untrusted inputs. Auto approval and safety classifiers are not security boundaries.
- Treat archives, repositories, package contents, filenames, and working-directory import paths as executable attack surface, even when the visible task is read-only.

### Defense design if the gap becomes active

The right architecture is soft guidance plus hard containment, not a larger prompt-injection classifier. Rules can prevent common mistakes and identify suspicious transitions, but they cannot reliably decide whether sophisticated content is malicious. Deterministic policy should follow provenance and capability instead:

1. Mark browser, connector, archive, unfamiliar-repository, package, and automation output as untrusted ingress.
2. Keep source-reading sessions unable to act. Promote only a human-reviewed distillation into a fresh acting session.
3. When untrusted code must run, use a disposable worktree or copied workspace with no home directory, Keychain, SSH keys, agent credentials, authenticated browser profile, host process control, or durable Git authority.
4. Deny network egress by default while allowing loopback for application tests. If package installation or download is required, grant a narrow temporary route through a broker that records destination, redirects, content type, size, and hash.
5. Keep parent review and adoption outside the sandbox. The sandbox may produce a patch; it does not merge, commit, deploy, or publish.

High-signal tripwires are capability transitions rather than prose classification: read-only retrieval followed by shell networking; cross-origin or HTML-to-archive redirects; interpreter execution from an untrusted working directory; model-written helpers run immediately against untrusted files; module-shadowing filenames or package lifecycle hooks; nested-agent or detached-process creation; and new outbound destinations during local analysis.

### Adoption boundary

Operating-system isolation and command-policy checks are already implemented in Workbench. Provenance tracking and brokered authority are additional mechanisms to evaluate only for a concrete workflow that exceeds that boundary. The [experiment record](../../docs/experiments.md) owns trial status. Start any such trial with one execution profile and measurable bypass cases; keep the reusable threat model here.

This is a motivated proof of concept with 15 reported trials across three variants, not a population-level attack-success estimate. The transferable conclusion is architectural: model behavior and per-command approval can reduce risk, but only isolation and egress control bound the consequence of a successful injection.

Sources: Johann Rehberger, [Breaking Claude Code Opus 5 Auto Mode](https://embracethered.com/blog/posts/2026/breaking-claude-code-opus-5-and-automode/), 2026-08-26; Jessica Lyons, [Researcher shows how Claude Code can be tricked simply by asking it to summarize a website](https://www.theregister.com/research/2026/08/28/researcher-shows-how-claude-code-can-be-tricked-simply-by-asking-it-to-summarize-a-website/5293372), 2026-08-28.

## Authority belongs outside generated code

[OpenAPPA](https://github.com/archestra-ai/OpenAPPA) is an information-flow policy reference: labels on untrusted material can constrain later tool actions at an enforcement point outside the model. Its [paper](https://arxiv.org/abs/2607.24625) reports project evaluations, not complete coverage of shell, browser, network, or side-channel effects. Compare it only for a bounded untrusted-content workflow, with independent bypass and fail-closed tests. [Meta Muse's design](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse) uses a different external authority point, including credential surrogation and action review; the [control-plane landscape](assistants.md#persistent-personal-agents-to-monitor) tracks its product boundary.

Recent Cloudflare and Vercel work independently separates untrusted execution from credentials and consequential tools:

- Cloudflare routes sandbox egress through a trusted outbound worker that can inject credentials, restrict destinations, log requests, and reduce permissions during a run.
- Vercel Connect exchanges stored provider credentials for task-scoped runtime tokens.
- Vercel Run executes generated JavaScript or TypeScript without direct Node.js or network access and exposes only named host functions.
- Cloudflare WriteGuard classifies and blocks high-risk Model Context Protocol calls before tool handlers run while recording both the human identity and agent session.

The resulting requirements are stronger than “put secrets in a vault”:

- Untrusted code never receives a reusable provider credential.
- Egress is default-deny and accounts for DNS, redirects, proxies, loopback, metadata services, and alternate address forms.
- A trusted broker injects short-lived authority only for the exact destination and operation.
- Critical mutations require deterministic server-side policy or human confirmation before the handler executes.
- Audit events distinguish a person's direct action from an agent acting under that person.
- Permissions can narrow after setup or discovery completes.

Compare any deployment against those requirements explicitly. Workbench's [implemented boundary and accepted limits](../../docs/security/isolation.md) are separate from these stronger design criteria; local isolation alone does not establish brokered credentials or default-deny network access.

- **[OpenAPPA](https://github.com/archestra-ai/OpenAPPA)** -- **WATCH FOR UNTRUSTED-CONTENT POLICY.** Trial only when a bounded workflow needs information-flow restrictions at the tool boundary; independently test bypasses and fail-closed behavior. The [authority boundary](#authority-belongs-outside-generated-code) owns the mechanism and its limits.

# Boundary review guide

Use these prompts to inspect actual controls, not to manufacture a finding in
every category. Mark categories as examined, not applicable with a reason, or
unexamined. This guide owns the security/privacy rubric; other health skills
route here rather than copying it.

## Model before searching

For each consequential flow, identify the actor, input, validator, authorization
decision, effect, and failure behavior. Identify what the actor already controls
and which new authority or information a defect would grant. A privileged owner
editing their own trusted installation is not automatically a privilege escalation.
A privacy failure can occur during intended use without an attacker.

State testable invariants in plain language. Examples: a caller can read only
objects in their tenant; a failed refresh cannot advertise unverified data as
ready; a public export contains only explicitly approved fields. Check where the
invariant is enforced, not merely where a comment claims it holds.

## Security sweep

| Boundary | Trace and challenge |
|---|---|
| Authentication and authorization | Cover alternate routes, background jobs, object ownership, tenant scoping, revocation, and privileged defaults. Verify framework middleware and caller checks before reporting their apparent absence in a leaf function. Authentication alone does not authorize an object. |
| Injection and output | Follow input through SQL, shell arguments, templates, HTML, headers, and logs. Check parameterization and context-appropriate encoding. Argument arrays prevent shell parsing, not malicious flags interpreted by the called program. |
| Files and archives | Check canonical containment, path-component boundaries, symlink/hardlink behavior, archive entries, ownership, and the interval between validation and use. A string prefix check alone is not path confinement. |
| Network and parsing | Trace URL parsing, DNS resolution, redirects, internal-address access, protocols, deserialization, and schema validation into privileged state. Check response and decompression limits, timeouts, and cancellation. |
| State and resources | Challenge repeated, reordered, concurrent, interrupted, and resumed operations. Inspect transaction/lock boundaries, idempotency, stale authorization, cache invalidation, partial writes, and readiness publication. Check bounded work, queue growth, retries, and exhaustion. |
| Cryptography and credentials | Prefer vetted primitives; inspect nonce/randomness use, verification defaults, key access, token expiry, and secret exposure through process arguments, errors, or artifacts. Require stronger evidence for custom repairs than for a maintained upstream replacement. |
| Dependencies and delivery | Separate an advisory from installed version, reachable vulnerable behavior, and actual impact. Distinguish production, build, CI, and developer exposure; development-only is not harmless when it holds credentials or publishes artifacts. Inspect installer hooks, workflow token permissions, untrusted PR inputs, artifact/cache provenance, and release paths. |
| Agent-mediated effects | Follow untrusted documents, tool results, repository content, and CI metadata into model context and tool calls. Check enforced capability limits, output destinations, credential access, and approval boundaries; a prompt asking the model to behave is not an authorization control. |

Use existing ecosystem audits and secret scanners as complementary evidence.
Inspect ignored findings and scan scope. Do not infer absence of secrets from a
regex scan, or non-reachability from the absence of an obvious direct import.
Route upgrades to `dependency-upgrades`; keep residual-risk acceptance explicit.

## Privacy sweep

Trace one sensitive field or record through its full lifecycle, using synthetic
markers instead of real private data. Compare the actual flow with the project's
approved purpose and data boundary:

- **Collection and purpose:** does the feature require each field, and does a
  later use or recipient exceed what was authorized?
- **Propagation:** inspect logs, exceptions, traces, analytics, model prompts,
  search indexes, caches, temporary files, screenshots, exports, and CI artifacts.
  An authenticated recipient can still be an inappropriate recipient.
- **Inference:** consider stable identifiers, linked datasets, and existence
  checks that reveal a sensitive fact without exposing the underlying record.
- **Retention and control:** follow deletion/correction through derived copies,
  backups, and restoration. Check documented retention/access rules rather than
  assuming immediate backup deletion is required or technically possible.
- **Public boundary:** review build inputs and outputs, tracked files and relevant
  history, examples, and metadata. Keep reports from becoming a second copy of
  the exposure. History cleanup and credential rotation require owner authority.

Separate demonstrated policy violations from product questions and legal advice.
If purpose, retention, or permitted recipients are unspecified, ask for that
policy decision instead of silently inventing one.

## Confirm, disprove, or leave unresolved

For each candidate, retain a compact evidence chain:

1. Exact location and claimed invariant violation.
2. Reachable entry point, actor prerequisites, and input or event sequence.
3. Enforcement along the path, including evidence against the claim.
4. Observable impact and minimal synthetic reproduction, or a clearly labeled
   static argument and the missing verification.
5. Disposition: confirmed, disproved by a named control, or unresolved.

Severity describes impact and realistic prerequisites; confidence describes the
strength of evidence. Missing tests lower assurance but do not by themselves make
a defect critical. Hardening suggestions are separate from exploitable defects.
Include both unauthorized and authorized test cases: a patch that denies all
requests or disables the feature is not a successful security fix.

For temporal defects, write the interleaving or failure point explicitly and use
barriers or injected failures rather than timing sleeps. When a root cause is
confirmed, search siblings and other manifestations, not just the exact spelling.
Use a scoped syntax/data-flow analyzer only when text search cannot answer the
question and its setup and data handling are approved.

## Research basis and limits

Reviewed 2026-10-02. These are practitioner methods, not independent evidence
that this particular skill improves vulnerability recall. The workflow is an
original synthesis, not an installed or wholesale port of an upstream skill.

- [Trail of Bits: false-positive checking](https://trailofbits.com/skills/fp-check/)
  motivates explicit attacker prerequisites, caller tracing, and a skeptical
  verification pass. Keep an unresolved state rather than forcing its binary
  true/false summary when evidence is inaccessible.
- [Trail of Bits: differential review](https://trailofbits.com/skills/differential-review/)
  motivates baseline/history inspection and following affected callers. Do not
  import fixed file-count budgets, classify logging as inherently low risk, or
  inflate severity simply because tests are missing.
- [Trail of Bits: variant analysis](https://trailofbits.com/skills/variant-analysis/)
  motivates starting from a known root cause and broadening searches gradually.
  Use authorized scope and signal quality, not a universal false-positive quota.
- [OWASP: threat modeling](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html)
  supplies the system, threat, response, and validation questions, including
  business-workflow abuse. A small boundary table is often sufficient.
- [LINDDUN: privacy threat categories](https://linddun.org/linddun-go-categories/)
  adds linking, identification, existence disclosure, awareness/control, and
  purpose/retention concerns beyond conventional confidentiality checks.

The security review skill owns execution and reporting. Repository health owns
whether these checks are operated and maintained. Code health owns structural
changes; fewer lines or better names do not prove the boundaries are preserved.

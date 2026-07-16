---
name: security-review
description: Run a read-only security review of a diff, branch, or codebase — OWASP-shaped sweep with evidence-backed, severity-classified findings. Use for "security review", "audit this for vulnerabilities", or "is this safe to ship".
---

# Security Review

A portable, evidence-first security review. Read-only: produce a findings report; never apply fixes unless explicitly asked afterward. Under Claude Code, the `security-auditor` subagent can run this in isolated context; this skill is the vendor-neutral path and the only security lens under Codex.

## Scope first

Decide what you are reviewing before reading code:

- **A change**: `git diff main...HEAD` (or the named base/PR). Review the diff plus the immediate blast radius — callers of changed functions, config the change reads.
- **A codebase**: prioritize the trust boundaries — request handlers, auth middleware, DB access, file/URL handling, CI and deploy config. Don't read everything; follow untrusted input inward.

State the scope in the report so "clean" has a defined meaning.

## The sweep

Work every category. Every external input is untrusted until validated at the boundary; trust inside is earned by that validation.

1. **Injection** — string-built SQL/shell/template from user input instead of parameterized queries or argument arrays; `eval`/`exec`/`os.system`/`child_process.exec` driven by request data; unescaped data flowing into HTML, logs, LDAP/XML/NoSQL.
2. **Authentication** — routes or admin/debug endpoints with no authn check; per-route middleware that's easy to forget on new endpoints; timing-unsafe token comparison (`==` instead of constant-time).
3. **Authorization / IDOR** — object fetched by ID without an ownership check; role/tenant trusted from the request body; queries missing tenant/scope filters (`WHERE id = ?` with no `AND owner = ?`).
4. **Secrets** — keys, tokens, passwords, connection strings in code, config, fixtures, or workflow files; logging that prints credentials or full request bodies; check `git log -p` for the diff, not just the tree.
5. **Unsafe deserialization** — `pickle`, non-safe `yaml.load`, `Marshal`, native-object deserializers on untrusted bytes; JSON parsed straight into privileged structures without validation.
6. **SSRF** — server-side fetches to user-supplied URLs without an allowlist; webhook/image-proxy/URL-preview features that can reach internal addresses or metadata endpoints.
7. **Path traversal** — user input joined into filesystem paths without normalization + prefix checks; archive extraction without entry-path validation.
8. **Dependency CVEs** — use the ecosystem's native tool: `npm audit`, `pip-audit`, `cargo audit`, `govulncheck`, `bundle audit`. Report actual reachable severity, not raw advisory counts.

## Evidence discipline

Every finding must carry:

- **`file:line`** — exact location.
- **Why it's exploitable** — the concrete path from attacker-controlled input to impact. If you can't articulate the path, it's a hardening suggestion, not a finding; label it as such or drop it.
- **Severity** — critical (exploitable now, high impact) / high (exploitable with modest preconditions) / medium (needs unusual conditions or is defense-in-depth) / low (hygiene).
- **The fix** — named, not applied: parameterize, add the authz check, move to env/secret store, safe loader, allowlist, constant-time compare.

Don't reward complexity or invent findings to seem thorough. A short report with two real vulnerabilities beats twenty speculative ones. Distinguish what is *enforced* (framework, type system, middleware) from what is merely *conventional* — conventions drift.

## Report format

- One-paragraph verdict with confidence level ("safe to ship" / "ship after fixing X" / "do not ship").
- Findings ordered by severity, each with the evidence fields above.
- **Checked, clean** — explicitly list every category from the sweep that was examined and came up clean, with one line on what was checked. Silence is not clearance.
- Anything out of scope or unverifiable (e.g. a service you can't see), named as such.

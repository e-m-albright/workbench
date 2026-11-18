# Application identity and authorization

Reviewed 2026-10-14 against official documentation. These are watch candidates,
not adopted dependencies. Authentication establishes identity; authorization
decides whether that identity may perform an action on a resource. Neither a
successful sign-in nor a model's tool selection supplies that decision.

## Cerbos and WorkOS solve different starting problems

| Candidate | Documented role | Disposition and trigger |
| --- | --- | --- |
| [Cerbos](https://docs.cerbos.dev/cerbos/latest/index.html) | A separately deployed policy decision point, with application-side enforcement integrations. The open-source PDP evaluates contextual access policies; Hub manages policy testing, distribution, and audit aggregation; Synapse enriches decision context. Components can be adopted independently. | **WATCH; first policy-engine candidate.** Evaluate when authorization rules recur across services or become too complex to test clearly in application code. Do not add a service for a handful of simple checks. |
| [WorkOS](https://workos.com/) | Managed AuthKit, enterprise single sign-on, directory synchronization, audit logs, and fine-grained authorization. | **WATCH; enterprise identity candidate.** Compare with the [existing authentication choices](services.md#authentication) when customer requirements make enterprise identity plumbing repeated work. Do not migrate ordinary sign-in merely to consolidate vendors. |

Cerbos keeps the decision engine separable from the identity vendor and the
application's business rules. The application still authenticates callers,
supplies trustworthy principal/resource attributes, invokes the decision, and
enforces it on every relevant path. A policy decision does not itself filter a
database query or make a write safe. The reviewed documentation identifies PDP
0.56.0 and separately lists 0.57.0 as a prerelease; this is a documentation
version observation, not a release-cadence or security assessment.

[WorkOS FGA](https://workos.com/docs/fga) currently describes hierarchical,
resource-scoped roles and permission inheritance integrated with its identity
products. Its conceptual subjects include devices and agents, but the same page
explicitly says the supported subject types today are organization memberships
and groups. Do not treat agent subjects as shipped. The page also marks direct
permission exclusions and sub-resource identity-provider role mapping as future
work. Model the actual exceptions before choosing this hierarchy.

The [WorkOS pricing page](https://workos.com/pricing.md), read on the review date,
lists the first million monthly active AuthKit users as free, but single sign-on
and directory synchronization start at $125 per connection each in their first
band. Free user authentication does not make enterprise connections free. FGA
pricing was not established by that page; confirm the complete quote, service
commitments, and export terms before a trial.

## WorkOS: from sign-in APIs toward governed agent access

Reviewed 2026-11-17. WorkOS is extending its enterprise identity foundation into agent registration, delegated API access, managed connections, authenticated browsers, and hosting for internal apps. These are distinct maturity levels, not one generally available agent platform:

| Surface | Evidence and availability | Useful boundary |
| --- | --- | --- |
| [Agent Registration](https://workos.com/docs/authkit/agent-auth) | Documentation says generally available; agents register, bind to a user through a claim ceremony, and exchange assertions for credentials | Separate agent registration from user consent and application permissions. Anonymous registration must remain restricted; it is not authority to access shared business data. |
| [Connect token exchange](https://workos.com/blog/mcp-server-call-api-on-behalf-of-user) | Documented RFC 8693 flow, 2026-11-17; environment enablement is required | Issue a downstream-audience token, narrow scopes, preserve user/organization, and record the acting application. Verify signature, issuer, audience, actor, and operation scope at the API. Offline JWT verification alone does not establish immediate revocation. |
| [Agent Vault](https://workos.com/blog/agent-vault) | Announcement, 2026-11-17; access enabled by WorkOS, explicitly not generally available | Saved passwords stay out of agent prompts while a hosted or self-hosted browser receives an authenticated session. User takeover handles sign-in steps. WorkOS still stores logins when the browser is self-hosted. |
| [Atlas](https://workos.com/blog/atlas-apps) | Announcement, 2026-11-16; early access, teams onboarded individually | Hosting, company sign-in, centrally approved connections, app ownership, access management, and activity logs for agent-built internal apps. Not proof that generated business logic is safe. |

“Governed internal app hosting” means Atlas combines a place to run employee-built software with company sign-in and administrator controls. In the announcement's example, a coding agent builds a status board from approved Linear, Slack, and Snowflake connections and deploys it to an address coworkers can open. Administrators choose available connections, see app ownership, restrict app access to people/groups/roles, and inspect activity logs. Atlas brokers connection requests so reusable service credentials stay out of app code; personal access requires the user to connect their own account and approve that app. Apps can also expose MCP tools. These are announced early-access capabilities, not a tested deployment here.

The distinction is from generic hosting, which can run the app but leaves the organization to assemble those identity and governance pieces. It is also distinct from a CRM or a business-process engine: Atlas does not supply correct account definitions, source-level row permissions, safe payment logic, or proof that an agent-built app is correct. For example, limiting who can open a renewals tracker does not establish which customer records it may read or which renewals it may change. Confirm those separately before connecting company systems.

**Useful:** evaluate a delegated identity/connection primitive when a customer needs it rather than implementing an authorization server or passing broad user tokens between services. Atlas may remove repeated internal-app deployment work in a multi-user organization. Agent Vault is a candidate only for a real browser-only integration that cannot use a supported API.

**Foolhardy:** move ordinary local tools onto Atlas just to centralize them, upload browser credentials to a new vendor for convenience, or confuse a hidden password with limited authority. A signed-in browser can still perform consequential actions. Verify tenant isolation, source-side permissions, exact-action approval, revocation of existing sessions, retention, export, availability, and pricing. Keep the [application-owned business boundary](../agents/integrations.md#direct-agent-integrations-and-application-owned-boundaries) independent of whichever identity or hosting vendor is selected.

## Smallest useful evaluation

Use synthetic users in two tenants and one resource hierarchy. Test a permitted
read, a cross-tenant denial, inherited access, an explicit exception, list-query
filtering, a role removal, a stale session/cache, and decision-service failure.
Verify that denied operations cannot bypass the enforcement point through a
second API, background job, or agent tool. Measure the revocation delay and
choose fail-closed behavior explicitly.

For Cerbos, include policy tests, context freshness, policy distribution failure,
and the cost of operating a decision service. For WorkOS, prove the supported
subject model, customer identity-provider mapping, connection billing, and the
ability to export identities and authorization state. Published latency and
consistency promises remain vendor claims until measured or contracted.

These products do not replace source-system grants, exact-action approval,
idempotency, or reconciliation. The [integration boundary](../agents/integrations.md)
owns those concerns. Licenses, security advisories, contractual data handling,
and independent performance evidence were not comprehensively audited in this
initial documentation review.

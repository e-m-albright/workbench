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

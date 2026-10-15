# JavaScript runtimes and toolchain consolidation

Updated 2026-10-14. The agreed maintained stack is **Node LTS with pnpm**,
framework-owned Vite, Biome, and focused type-aware Oxlint promise checks.
Astro remains the content-site framework; Svelte/SvelteKit remains the
interactive-application framework. **Bun, Deno, and Vite+ are watch-only**. The
owner ended the Bun adoption trial and restored Node/pnpm after reviewing
compatibility and maintenance costs. Deno is retired from maintained tooling;
older experimental prototypes are excluded. The measurements below
record the evidence behind the decision, not a claim that every evaluated tool
was adopted.

## What should remain simple

Prefer fewer capable tools when they remove configuration, dependencies, and
failure modes. Count the responsibilities actually eliminated, not executable
names. A command that wraps five tools may simplify upgrades; a single binary
can still introduce a second runtime's compatibility problems.

| Layer | Current default | Leading alternative |
| --- | --- | --- |
| Interactive UI and application framework | Svelte and SvelteKit | [Solid and SolidStart](frameworks/solid.md) |
| Runtime | Supported Node LTS | Bun, verified against the application's actual dependencies |
| Dependencies | One pinned pnpm version and committed lockfile | Bun's installer and lockfile after an explicit migration |
| Development and application build | Framework-owned Vite configuration | Vite+ on watch; require demonstrated workflow consolidation |
| Tests | Vitest for Vite applications, Playwright for browser behavior | Bun test for a standalone Bun project where it removes another runner |
| Semantic checks | TypeScript and the framework checker, including svelte-check | No blanket replacement based on a runtime's type-checking feature |
| Formatting and linting | Biome plus selected type-aware Oxlint promise checks | Oxfmt when framework coverage and configuration consolidation are demonstrated |

SvelteKit's [Node adapter](https://svelte.dev/docs/kit/adapter-node) supplies a
standalone server target. Node publishes a [support lifecycle](https://nodejs.org/en/about/previous-releases)
and [project governance](https://nodejs.org/en/about/governance). These support
the baseline choice; they do not imply that corporate influence disappears.

## Candidates and disposition

| Candidate | What it consolidates | Decision and adoption cost |
| --- | --- | --- |
| **Node + pnpm** | Established runtime and dependency workflow; framework scripts coordinate checks | Default. Least disruption to existing pnpm applications. It deliberately retains separate runtime and package tools. |
| **Bun** | Runtime, installation, TypeScript execution, scripts, tests, bundling, executable packaging, and built-in service APIs | Local builds passed, but current jsdom compatibility prevents a uniform adoption. A package-manager change requires lockfile and CI review; a runtime change additionally requires integration and operational checks. |
| **Node + Vite+** | Runtime/package-manager coordination, Vite, Vitest, linting, formatting, packaging, and cached tasks | Watch-only. Local checks and selected tests passed after one configuration repair; the comparison did not establish a speed advantage or sufficient configuration removal. |
| **Deno** | Runtime, package management, checking, formatting, linting, tests, permissions, and executable packaging | Technically cohesive but unsuitable as a new long-term default given the announced end of team development. Existing users have a migration window. |
| **Nub** | A unified toolkit around stock Node, including scripts, installation, and version management | Secondary watch. It could simplify commands while preserving Node execution, but must remove existing owners rather than add shims above them. |
| **npm or Yarn** | Package management, not a replacement runtime or complete framework toolchain | Respect inherited projects. Neither currently supplies a reason to replace working pnpm projects for this consolidation objective. |
| **workerd / Workers** | Deployment and server execution | Choose for an application's hosting requirements. It does not replace local package management or the framework build. |

[Vite+ 1.0](https://voidzero.dev/posts/announcing-vite-plus-1-0) shipped on
2026-09-28 under MIT. Its installer delegates to the project's package manager;
Vite+ is not another package manager or JavaScript runtime. The earlier beta
status no longer justifies postponing evaluation. [Nub](https://nubjs.com/)
offers a different consolidation around stock Node and remains untested here.
Vite+ 1.1.0 has now been tested in disposable application copies.

## Why Deno's outlook changes the choice

The [2026-10-09 announcement](https://deno.com/blog/cloudflare), rechecked
2026-10-14, gives the runtime another year of monthly releases with fixes and
security updates before the team ends development,
and Deno Deploy another six months before shutdown. Those imply roughly
October 2027 and April 2027 respectively, not independently promised exact
cutoff dates. JSR continues under Cloudflare infrastructure; rusty_v8 also
continues. The team is redirecting work toward Cloudflare's platform.

The retirement of the default is about the announced maintenance horizon,
not the acquisition alone. Revisit only if a credible successor establishes
maintainers, releases, security response, and ecosystem compatibility. Open
source licensing permits continuation but does not establish that capacity.

### Deno already replaces pnpm's everyday role

| Job | pnpm | Deno |
| --- | --- | --- |
| Install project dependencies | `pnpm install` | `deno install` |
| Add an npm dependency | `pnpm add zod` | `deno add npm:zod` |
| Run a declared task | `pnpm run dev` | `deno task dev` |
| Reject lockfile changes in CI | `pnpm install --frozen-lockfile` | `deno install --frozen-lockfile` |
| Resolution record | `pnpm-lock.yaml` | `deno.lock` |

Deno supports package.json as well as deno.json and imports packages from npm
and JSR. See [installation](https://docs.deno.com/runtime/reference/cli/install/),
[dependency declarations](https://docs.deno.com/runtime/reference/cli/add/),
and [tasks](https://docs.deno.com/runtime/reference/cli/task/).
Replacing pnpm still requires reviewing workspaces, resolution, lifecycle
scripts, and CI. Avoid two installers owning the same dependency tree.

## What going all in on Bun would mean

The [Anthropic acquisition commitment](https://bun.com/blog/bun-joins-anthropic)
includes continued public development, MIT licensing, and Node compatibility.
Its use in Claude Code gives the sponsor a concrete maintenance incentive.
Continued general-purpose investment is promised; uniform prioritization of
all server workloads is not guaranteed.

The [Rust rewrite account](https://bun.com/blog/bun-in-rust) reports extensive
testing and fixed regressions. Treat its performance and reliability claims as
first-party evidence. Neither implementation language nor AI authorship alone
establishes application compatibility. Check the documented
[Node differences](https://bun.com/docs/runtime/nodejs-compat) and actual behavior.

Separate three commitments: Bun installs dependencies, Bun executes tools,
and Bun runs the production server. They can be evaluated separately. In
particular, [bun run respects Node shebangs](https://bun.com/docs/runtime);
using that command does not prove Vite ran on Bun. Record the actual execution
path when comparing results.

For SvelteKit, retain Vite, framework transforms, svelte-check, Vitest, and
Playwright unless a replacement demonstrates equivalent behavior. That reduces
the number of tools Bun can eliminate here. A standalone TypeScript service or
CLI may benefit more from its integrated runtime, tests, and packaging.

Use built-in Bun APIs when they remove meaningful code or dependencies. If
portability is required, keep those calls in a small service boundary and test
the alternative execution path. Avoid both a blanket ban and speculative
abstractions around every API.

## Bun watch criteria

The owner chose to restore Node/pnpm on 2026-10-14. Keep Bun out of maintained
runtime, package-manager, and type-checking paths. Track capabilities through
this watchlist rather than keeping an installed second development stack.

[Bun 1.4.3](https://bun.sh/blog/bun-v1.4.3) introduced a semantic TypeScript
checker based on TypeScript 7.0.2. Workbench's trial checked 18 files successfully;
it did not establish a speed advantage over Microsoft's matching compiler.
The checker does not replace
Astro/Svelte checks, declaration emission, or the editor language server.
Revisit only after diagnostic parity and repeated workflow savings are measured
against the same TypeScript version.

Other useful watch targets are parent-process cleanup with `--no-orphans`,
agent-readable diagnostic/profile output, and browser automation. Evaluate a
specific capability only when an actual task needs it. Retain Playwright and
existing tests until a replacement demonstrates the same coverage. Bun's
experimental module isolation is not a security sandbox; Node permission and
OS-confinement requirements remain separate gates.

Sources: [checker](https://bun.sh/docs/runtime/check),
[process cleanup](https://bun.sh/blog/bun-v1.3.14),
[profiles](https://bun.sh/blog/bun-v1.3.7), and
[WebView](https://bun.sh/docs/runtime/webview).

Follow [Bun releases](https://bun.com/blog) during dependency reviews. Require a
representative trial to show which tools, configuration, or recurring work the
new capabilities remove. Faster isolated commands alone do not justify keeping
another runtime installed. The Workbench trial verified frozen installation,
dependency auditing, and Pi 0.86.1 startup and credential-free RPC under Bun;
interactive sessions, authentication, and the full managed launcher were not
validated. Compatibility is possible, but these probes did not establish a
reason to replace Node for Pi.

## Deno watch criteria

Follow [Deno releases](https://github.com/denoland/deno/releases) and maintenance
announcements during dependency reviews, including any maintained successor.
Watch integrated checking, linting, formatting, testing, dependency management,
packaging, and framework support. Reconsider when those capabilities remove
enough existing tools or recurring work to justify migration, and the project
has a credible ongoing release and security-response commitment beyond the
[announced maintenance horizon](#why-denos-outlook-changes-the-choice).

For either ecosystem, compare the same dependency and compiler versions against
Node/pnpm. Require equivalent framework diagnostics, editor support, component
and browser tests, CLI behavior, install controls, debugging, and deployment
behavior for the proposed scope. Keep evaluation disposable until those checks
pass and the workflow benefit is measured. These watches do not require a
second installed stack or change the operating-system confinement boundary.

## Local comparison and next adoption gate

The 2026-10-12 comparison used an Astro application and a SvelteKit static
frontend on an M4 Pro, with Node 24.20.0, Bun 1.4.3, and Vite+ 1.1.0. Each
passing workload had five sequential samples after warmup, with randomized
candidate order. Node and Bun used the same dependencies; the Vite+ migration
also updated bundled tools, so that comparison includes dependency changes.

| Workload median | Existing Node tools | Node with Vite+ | Bun |
| --- | --- | --- | --- |
| Astro check | 7.28 s | 7.39 s | 6.35 s |
| Astro build and search index | 4.99 s | 5.24 s | 4.71 s |
| Svelte check | 3.15 s | 3.63 s | 3.23 s |
| SvelteKit build | 3.44 s | 3.82 s | 3.17 s |
| Short TypeScript automation with mocked inputs | 0.35 s | 0.35 s | 0.13 s |

Node passed the selected test suites. Bun failed jsdom setup and one assertion
about the return value of `fs.promises.access`. The jsdom failure was reduced
to a dependency-free `node:vm` difference: a context created with
`DONT_CONTEXTIFY` and its evaluated global are identical under Node but
different under Bun. jsdom 30.1.0 registers private fields on the first object;
event-listener calls on the second fail its receiver check. The filesystem
difference is `null` versus `undefined`, not demonstrated data loss.

One private-data inventory test was excluded equally. These were development
workloads, not production latency or full security/browser gates. Warm-cache
installation with scripts disabled took 0.78 s for pnpm and 0.40 s for Bun;
the graphs differed by one YAML package version. Treat this as an approximate
installer comparison. Small absolute savings on infrequent work do not justify
compatibility work; repeated edit feedback and avoided work matter more.

Vite+ migration retained Biome rather than completing its replacement. Its
generic check passed with warnings and did not replace framework checkers.
The [Oxc compatibility matrix](https://oxc.rs/compatibility.html) lists Svelte
formatting support, but Astro formatting still requires unavailable Prettier
plugin support. Oxlint does not lint framework templates. A direct Oxfmt check
of an Astro component found no eligible files. Preserve existing coverage until
a replacement is demonstrated; do not count a skipped file as a passing check.
Biome's [framework support](https://biomejs.dev/introduction/language-support/)
is also experimental: full HTML/template support requires explicit opt-in.
Keeping the existing configuration does not establish complete template coverage.

The [task cache](https://viteplus.dev/guide/cache) can avoid repeated work, but
enabling it is not sufficient. Two runs of the existing Svelte framework check
with `vp run --cache check` both reported zero cache hits: synchronization and
checking read and rewrote generated `.svelte-kit` declarations. Any cache trial
must validate both reuse and invalidation when real inputs change. No caching
improvement has been demonstrated in this workflow yet.

For the next adoption trial, keep the framework fixed and evaluate the complete
developer workflow. Preserve the Python toolchain in repositories that use it;
Vite+ applies to their JavaScript portions, not their whole architecture.

1. Record the baseline: dependency graph, commands, configs, cold and warm
   installation, development startup, edit feedback, test/build duration, and
   debugging steps. Separate install caches from runtime effects.
2. Run the same framework checks, component tests, and browser flows. Exercise
   authentication, server rendering, streaming, database access, native modules,
   tracing, and shutdown where the application uses them.
3. Build and run the actual production artifact on its declared runtime.
   A successful build alone is not evidence of runtime compatibility.
4. Count configuration and dependencies removed, unexpected workarounds,
   maintenance owners, and useful feedback latency. Benchmark production only
   if server execution is material to the workload; an installer cannot speed
   up the browser UI or a remote model response.
5. Choose one package manager and one normal runtime per project. Keep any
   claimed Node escape route tested rather than maintaining two daily workflows.
6. Promote Bun if it simplifies the complete workflow without correctness or
   operational regressions. Prefer Vite+ if integration improves while Node
   remains the better runtime. Retain Node/pnpm if neither improves the result.

The package-manager trial is reversible through reviewed configuration and
lockfile changes. Runtime-specific service APIs create a larger migration
surface. A runtime decision does not authorize machine-wide installation,
deployment, or migration of unrelated repositories.

## Oxc and Biome capability tradeoffs

Oxc supplies language-processing components as well as Oxlint and Oxfmt.
Vite+ combines these with sibling projects such as Vite and Vitest. Biome is
a separate formatter, linter, and code-assistance tool; it does not replace
the build or test pipeline.

[Oxlint](https://oxc.rs/docs/guide/usage/linter.html) offers TypeScript-backed
type-aware rules and ESLint-compatible JavaScript plugins, currently alpha.
Biome has its own type inference, including an experimental
[floating-promise rule](https://biomejs.dev/linter/rules/no-floating-promises/javascript/),
and [GritQL plugins](https://biomejs.dev/linter/plugins/) for custom diagnostics
and rewrites. Neither lacks custom checks or all type-aware analysis.

[Oxfmt](https://oxc.rs/docs/guide/usage/formatter.html) covers Markdown, YAML,
TOML, and SCSS formatting beyond Biome's current language coverage. Biome
provides CSS, JSON, GraphQL, and experimental HTML/framework linting beyond
Oxlint's JavaScript focus. Rule counts alone do not establish application fit.

Oxc's [agent integration](https://oxc.rs/docs/guide/usage/coding-agents.html)
provides agent-oriented diagnostics and editing workflows. It does not judge
architecture or replace dependency boundaries, dead-code checks, duplication
analysis, behavioral tests, or review. Enable checks for demonstrated failures
rather than adopting every rule under an "anti-slop" label.

Both projects continue releasing. VoidZero's
[September recap](https://voidzero.dev/posts/whats-new-sep-2026) records work
after joining Cloudflare. [Biome's release history](https://github.com/biomejs/biome/releases)
includes 2.5.15 with new Svelte rules and Astro fixes. Current development is
evidence of continuity, not a guarantee of future stewardship.

### Disposable Oxc versus Biome evaluation

On 2026-10-12, Oxlint 1.87.0 and Oxfmt 0.72.0 were evaluated against
the installed Biome versions and then Biome 2.5.15. The trial offered the
same 430 source files across an Astro application, a SvelteKit application,
and Workbench's TypeScript code. Separate deliberately broken and valid
fixtures tested diagnostic accuracy. Both linters received explicitly enabled
promise checks; this was not a comparison of default rule counts.

**Disposition: Oxlint demonstrated useful additional TypeScript checks;
replacing Biome completely did not pass the coverage and simplicity gate.**

| Check | Oxlint result | Biome 2.5.15 result |
| --- | --- | --- |
| Discarded typed `Cache.put` promise, found in application code and reduced to a fixture | Reported | Missed with floating-promise checking enabled |
| Unawaited imported Vitest async assertion | Reported by the TypeScript floating-promise rule | Missed in the fixture |
| Assigning `JSON.parse` output directly to a string | Reported with unsafe-assignment checking enabled | Missed in the fixture |
| Basic unused variables, explicit `any`, non-null assertions, and a discarded local async call | Reported with corresponding rules enabled | Reported with corresponding rules enabled |
| Valid guard on a nullable promise | Accepted | Misused-promise false positive |
| CSS mistakes and duplicate JSON keys | Outside lint coverage | Reported |
| Missing image alternative text in Astro and Svelte templates | Outside template coverage | Reported with experimental full framework support enabled |

The discarded cache write is a concrete error-handling and completion-lifetime
gap, not a measured production incident. The runtime behavior was not exercised
in this evaluation. Its correct repair depends on whether caching should delay
the response or continue as explicitly managed background work.

Oxlint also needed policy adjustments. Its unused-expression rule rejected
intentional Svelte effect dependency reads. An optional Vitest rule rejected
an assertion stored and awaited later; removing that optional rule retained
the TypeScript check for actually discarded assertions. A type-aware rule
also flagged legal `Promise.all` input mixing promises and ordinary values.
These results argue for reviewed rules rather than enabling every plugin.
Workbench's incumbent Biome linter was disabled, so its new lint findings
cannot all be credited to stronger analysis. Enabling Biome there also found
issues. Upgrading the Svelte application to Biome 2.5.15 additionally produced
33 CSS specificity warnings; their correctness was not adjudicated here.

Oxfmt formatted all 57 Svelte components after explicit Svelte opt-in. It
changed 62 application files overall; framework checking still reported no
errors or warnings, and 198 tests passed with the same one private-data
inventory test excluded. One component changed again on the second formatting
pass and stabilized on the third. This was a reproducible first-pass
consistency issue, not an endless formatting loop.

Oxfmt skipped all 41 Astro components in the selected site scope. Configuration
migration also warned that Biome overrides require manual translation. Existing
barrel-export policy, import organization, filename rules, and formatting
overrides therefore cannot be assumed preserved by automatic migration.
The trial did not establish a formatter speed advantage or browser performance
gain. All 571 original application files covered by the source manifest retained
their hashes; formatting and diagnostic changes stayed in disposable copies.

Keep Biome as the current formatter and broad lint baseline. The approved maintained supplement is limited to
`typescript/no-floating-promises` and `typescript/no-misused-promises`, with
the default correctness category disabled. This adds a tool rather than
consolidating the stack; the demonstrated error detection justifies it.
Vite+ can still be evaluated for builds and tests without making its lint and
format pipeline the sole quality gate. Revisit full replacement when Astro
formatting, required non-JavaScript linting, and explicit rule-policy parity
have demonstrated owners without increasing maintenance burden.

## Deno-related AI tools have separate lifecycles

The [agent security exploration](../../agents/security.md#hosted-sandboxes-and-credential-gateways)
owns Deno Sandbox, Claw Patrol, alternative providers, and the local-versus-hosted
decision. None requires making Deno the default application runtime.

| Capability | Role and disposition |
| --- | --- |
| Deno permissions | Restrict runtime access. They are not VM isolation; subprocess and native-library permissions can bypass the boundary. |
| Deno Sandbox | Hosted Linux microVM execution for generated code, with SDKs usable outside Deno. Deployment-service continuity needs clarification. |
| Claw Patrol | Gateway for protocol-aware rules and credential injection; separate from process isolation and package management. |
| Agent skills and documentation | Help coding assistants maintain Deno projects; not a new agent execution system. |
| JSR | Package distribution, explicitly continuing. Registry choice and runtime choice remain separate. |
| celld and workerd | Self-hosted Workers/Durable Objects direction. Hosting portability still leaves dependence on that programming model. |
| Cloudflare Agents SDK | Persistent agent state, connections, scheduling, and recovery on Cloudflare's platform. Evaluate for a product requiring those capabilities. |
| Supabase Edge Functions | A separately operated Deno-based service. Assess its provider's support commitments separately from Deno Deploy. |
| Fresh, Jupyter, desktop support, and executable compilation | General application and development capabilities, not independent reasons to select Deno for AI work. The [desktop comparison](https://docs.deno.com/runtime/desktop/comparison/), reviewed 2026-10-14, describes `deno desktop` from 2.9 with system WebView or bundled CEF; the [interface assessment](../../product/interfaces.md#cross-platform-desktop-applications) owns its limitations and revisit gate. |

Sources: [runtime security](https://docs.deno.com/runtime/fundamentals/security/),
[Sandbox](https://docs.deno.com/sandbox/), [Claw Patrol](https://deno.com/blog/clawpatrol),
[agent resources](https://docs.deno.com/ai/), [celld](https://celld.dev/),
[Cloudflare Agents](https://developers.cloudflare.com/agents/),
[Supabase functions](https://supabase.com/docs/guides/functions), and
[Deno release history](https://deno.com/blog).

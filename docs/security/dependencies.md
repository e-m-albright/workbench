# Native runtime dependencies

The locked sandbox runtime uses upstream `node-forge` 1.4.3 through a scoped npm
override. Packages are installed unchanged with lifecycle scripts disabled. There
is no local Forge source patch or audit exception.

[Native preparation](../../src/workbench/native.py) holds an exclusive lock from
readiness invalidation through publication. A concurrent preparer fails rather
than publishing readiness beside an interrupted installation. Preparation
invalidates the readiness manifest before reinstalling dependencies and verifies
the security probes before marking the runtime ready. Run
`workbench native prepare` to refresh an existing installation.

`just audit` installs the locked dependencies in a temporary directory, verifies
both regression probes, and runs the complete npm audit without filtering or
suppressing findings. Any install, probe, or audit failure fails the gate.

[The Forge regression probe](../../agents/shared/sandbox/verify-forge.cjs) checks
rejection of extra nested DigestAlgorithm elements with and without NULL
parameters, covering
[GHSA-86w9-cpqp-85rv](https://github.com/advisories/GHSA-86w9-cpqp-85rv).
It also verifies valid PKCS#1 v1.5 signatures, modified digests, and RSA-PSS.
The override can be removed when the sandbox runtime's dependency range selects
a fixed Forge release without it.

## Zod compatibility pin

[GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5) affects the
Zod v4 implementation bundled in the old dependency. Sandbox-runtime 0.0.81
explicitly imports `zod/v3`, a compatibility entry point supported by both Zod
3.25 and Zod 4. Workbench's scoped npm override selects Zod 4.6.7 while preserving
that v3 API; it does not force the runtime onto the incompatible v4 schema API.

[The Zod regression probe](../../agents/shared/sandbox/verify-zod.cjs) verifies
that oversized v4 arrays stop before producing per-item errors, and that the
sandbox's v3 configuration schema still accepts valid policies and rejects
malformed ones. Preparation must pass this probe before publishing readiness.
`just audit` runs it against a fresh locked install. No audit exception or Zod
source patch is used. Remove the override when the upstream dependency range
includes a fixed release.

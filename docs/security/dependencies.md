# Native runtime dependency repair

As of 2026-10-02, the pinned sandbox runtime depends on `node-forge` 1.4.0.
[GHSA-86w9-cpqp-85rv](https://github.com/advisories/GHSA-86w9-cpqp-85rv)
reports incomplete validation of nested ASN.1 elements during RSA PKCS#1 v1.5
signature verification. No fixed version is published. Downgrading the sandbox
to remove this dependency would also remove later sandbox security fixes.

Workbench backports the additional element-count check proposed in
[upstream pull request 1152](https://github.com/digitalbazaar/forge/pull/1152),
commit `ceba344`. This is a local repair based on an unmerged upstream proposal,
not an upstream release. The actual package version remains 1.4.0.

[The preparation code](../../src/workbench/native_dependencies.py) accepts only
the exact original RSA source checksum or the exact repaired checksum. A version
or source change requires fresh review. Preparation holds an exclusive lock from
readiness invalidation through publication; a concurrent preparer fails rather
than leaving another process's manifest beside an interrupted installation.
Preparation invalidates the readiness manifest before reinstalling dependencies,
applies the repair with lifecycle scripts disabled, and verifies malformed and
valid signatures before marking the runtime ready. Run `workbench native prepare` to repair an existing installation.

`just audit` installs the locked dependencies in a temporary directory, reproduces
the original parser defect, applies the same repair, and verifies rejection of
extra elements with and without NULL parameters. It also checks valid signatures,
modified digests, and RSA-PSS. The npm audit report is accepted only when the exact
repaired source is present and its only findings are this advisory at the expected
package location and the corresponding parent finding. Additional advisories,
package locations, malformed reports, and audit failures still fail the gate.
The output explicitly identifies the locally patched advisory. A different npm
fix proposal also fails the gate and requires review; the only accepted proposal
today is the rejected sandbox-runtime 0.0.50 downgrade.

Remove the backport, its regression probe, and the audit exception when an
upstream fixed release can replace the pin. Restore the direct npm audit command
then. This is the sole temporary dependency repair, not a general exception list.

# Managed launch review

The October 13, 2026 review supported one managed authority: `co`, `cc`, and `p`.
Full `codex`, `claude`, and `pi` retain native behavior and shared configuration.
The owner subsequently authorized the reviewed corrections, closure of the two
submitted branches without merging, and publication of the selected main-line
implementation. This record tracks their disposition rather than asking for the
same approval again.

The most consequential original defects were owner read exclusions losing to
explicit grants and managed Pi silently overriding an explicit private-inference
request. Both are corrected. The reviews did not demonstrate an escape by
launching a native child or clearing its environment. The remaining concerns
are meaningful boundaries of the design, especially admitted credentials and
content, pre-existing file aliases, host callbacks, and later host execution.

## Protection matrix

“Native” means a full command started by the owner from the host terminal.
A native binary started inside a managed process retains the parent's policy.

| Measure | Native full commands | Managed shortcuts |
| --- | --- | --- |
| Shared instructions and skills | Retained | Retained through filtered configuration |
| Hooks and tool guards | Applicable installed guards | Applicable guards; narrowly validated Codex trust survives refresh |
| Vendor sandbox | Installed settings and command flags apply; Pi has soft guards | Nested vendor OS sandbox disabled; Workbench supplies containment |
| Vendor approvals | Installed policy | Retained independently of outer enforcement |
| Process inheritance | No Workbench outer policy | Children retain restrictions, including with cleared environments |
| Host file access | Vendor-specific | Default deny plus checkout, public code, scratch, tools, state, and login grants |
| Private path exclusions | Vendor and soft-guard dependent | Final mandatory denials after grants; equality, ancestor, nested, and glob coverage |
| Desktop and Downloads | Host paths subject to vendor permissions | Read/write host directories mapped into isolated HOME, with exclusions |
| Network | Vendor-specific | Public TCP destinations on ports 80/443 through a proxy; private destinations denied |
| Browser and PDF | Installed tool behavior | Fresh contained browser; no personal profile; endpoint identity checked before vendor startup |
| Host callbacks | Native authority and host settings | Ghostty denies clipboard reads; owner-approved prompt-free writes permit clipboard replacement |
| Session exit | Vendor/process dependent | Contained guardian cleanup; malicious termination of that guardian remains a limit |

A native sandbox is not an unconditional promise: configuration, flags, and
vendor exceptions matter. Shared instructions and soft guards do not replace
operating-system containment. The managed boundary does not inspect TLS payloads
or make readable files safe to send to permitted public destinations.

## Reconciled findings and dispositions

The reviews were source assessments, not penetration tests. “Corrected” below
means the coordinator implemented the owner-approved remedy; cited synthetic
checks provide separate evidence. Final installed acceptance is recorded below.

| Original finding | Disposition | Evidence or remaining limit |
| --- | --- | --- |
| Owner exclusions could lose to read grants | **Corrected.** Mandatory owner/project denials are appended after all allows. | Synthetic macOS equality, ancestor, nested, and glob denial cases pass. Required tools beneath an exclusion fail closed. |
| Explicit private inference became hosted | **Corrected.** Managed Pi rejects explicit private/local startup intent before model input. | Regression tests; no private input was submitted during review. Native local Pi remains explicit. |
| Tilde scratch paths pointed into isolated HOME | **Corrected.** Defensive Desktop/Downloads mappings target host scratch directories. | Mappings do not add authority beyond the approved scratch grants; private exclusions still apply. |
| Native Pi claimed managed authority | **Corrected.** Welcome wording describes configuration; footers name actual authority. | Regression tests distinguish native and managed labels. |
| Chrome helper always failed | **Retired with guidance.** `ccc` and managed `--chrome` name the explicit native command. | No automatic switch to host authority. |
| Trust and preferences reset | **Corrected narrowly.** Selected-root and unchanged-hook Codex trust survive; valid Pi worker timeout is projected. | Unsupported TOML prompts again; arbitrary settings, permissions, other roots, malformed records, and linked state are not imported. |
| Login presence implied readiness | **Corrected.** Vendor-scoped authorize/replace backs up prior state; status reports file metadata and says authentication is unverified. | Provider acceptance, expiry, and long-lived refresh remain separate concerns. |
| Helpers promised unavailable authenticated work | **Corrected guidance.** `cca --feedback` uses supplied review text and makes no publication request. | Authenticated GitHub, secrets, Docker, and local previews require deliberate native workflows; no broad grants added. |
| Worktrees and sessions depended on checkout location | **Corrected diagnostics.** Pi preflights sibling placement before Git mutation; docs explain isolated histories and manual continuation. | Linked worktrees remain unsupported managed entrypoints; moving a checkout changes its state identity. |
| Global Git identity overrode repository settings | **Corrected.** Repository `user.name` and `user.email` override global scalar defaults. | Local includes, credential helpers, and arbitrary host Git configuration are not imported. |
| Bootstrap placement could be managed-writable | **Corrected.** Preparation and launch reject unsafe bootstrap paths and overlapping write roots. | Host-installed code is still trusted; no deployed compromise was established by review. |
| Background descendants could survive | **Corrected and verified for ordinary exit.** A same-sandbox guardian uses exit reporting and process termination. | Detached synthetic children ignoring SIGTERM were terminated; unrelated host processes survived. A malicious child may kill the guardian first; forced supervisor death is not guaranteed cleanup. |
| Terminal callbacks lacked installed evidence | **Host configuration verified; write risk accepted.** Ghostty denies reads and permits prompt-free writes at the owner's explicit request. | Terminal programs can replace clipboard contents. Installed parse/status and host gate pass; existing windows need Command+Shift+Comma. Other terminals are not covered by this evidence. |
| Network wording promised HTTP protocol checks | **Clarified.** The proxy permits public TCP ports 80/443, not verified application protocols. | Resolved private addresses remain denied. Public exfiltration of admitted content is possible. |
| Recursive plugin grants might admit data | **Accepted trust boundary, claims narrowed.** Installed plugin/extension trees are trusted code assets, not sanitized data trees. | Synthetic fixtures cover admission behavior; no real plugin secrets were read. Keep credentials outside those trees. |
| Hardlink behavior lacked coverage | **Verified accepted alias limit.** A pre-existing admitted hardlink remains readable even if another name is excluded. | Synthetic probes separately deny new protected hardlink creation and protected ancestor renaming. This is path containment, not content labeling. |
| Browser port could be claimed before lazy startup | **Corrected and verified.** Start a fresh contained browser before the vendor and pin its validated DevTools identity. | A competing synthetic listener prevents vendor startup. Installed Pi browser/PDF acceptance passes with private socket-directory permissions. |

The security review rejected a suspected cleanup symlink widening because the
installed runtime refuses out-of-tree realpath normalization for that path.
Direct child inheritance does not cover terminal/editor callbacks, kernel
vulnerabilities, or the owner later running agent-modified source on the host.

## Verification evidence

The final correction pass passed the project gate: 289 Python tests, 52 subtests,
126 Pi tests, and the repository's type, lint, shell, and document checks. The 15
opt-in macOS boundary tests passed separately, including private exclusions,
child inheritance, Pi RPC, and interactive startup at two terminal widths.
Dependency audits passed. Thirteen deployed files were compared with source,
and all three derived harness projections were refreshed with backups.

After deployment, installed `co` reached its ready prompt and all six managed
and native commands passed version startup. Installed Pi completed public
navigation, synthetic interaction, screenshots, PDF export, text extraction,
visual inspection of the rendered PDF, and protected-file checks. Browser port
closure and scratch removal were observed after exit. Ordinary `~/Desktop` and
`~/Downloads` paths passed synthetic read/write checks. No personal browser
profile or private document was used.

Integration checks caught and corrected two regressions before publication:
a recursive-root ancestor rule prevented removal of Pi lock directories, and
eager browser startup created socket storage with permissions rejected by Pi's
wrapper. Focused regression tests cover both cases. Redirecting managed output
to a file outside admitted paths remains subject to file restrictions; use the
checkout or admitted scratch directories for output files.

The Codex bootstrap failure was traced to public certificate roots while
Keychain was denied. `SSL_CERT_FILE=/etc/ssl/cert.pem` resolved account routing
through the existing proxy. Codex's changed-hook review remained owner-controlled;
acceptance skipped that prompt without granting new hook trust. Claude version startup and onboarding were checked;
authenticated Claude operation, OAuth refresh, and resume remain unverified.
No paid model request was sent during launch acceptance. The requested model
reviews were a separate activity.

Host Ghostty verification passed its complete host gate and configuration
validation. No clipboard contents were read or changed and no GUI reload was
automated. Existing windows need **Command+Shift+Comma** or **Reload Config**.

Selected ideas from [PR #7](https://github.com/e-m-albright/workbench/pull/7), its
[reviewed tip](https://github.com/e-m-albright/workbench/commit/84c439a), and the
[resume submission](https://github.com/e-m-albright/workbench/commit/0fb2846)
were implemented selectively: Claude policy access, tool paths, Git attribution,
project denial projection, resume guidance, and compaction preferences. PR #7
was closed unmerged and both remote branches were deleted at the owner's
request; local archive refs preserve the reviewed tips. Neither branch was
merged wholesale.

Provider login readability, public disclosure of admitted content, live source
later executed by the owner, shared-kernel exposure, and pre-existing admitted
file aliases remain accepted limits. Desktop and Downloads admission makes
careful placement of private files particularly important. Reconsider stronger
isolation if these limits no longer fit the workflow.

## Review provenance

Six fresh-context assessments were requested: two GPT-6.1 Sol and one GPT-6 Astra
for security, and the same mix for developer experience. Rubric:
`launch-review-v1`; review date: October 13, 2026. Model identities are the
configured review-agent identifiers, not independent provider attestations.
Raw reports and the frozen-source manifest remain in ignored local artifacts
under `.artifacts/launch-review/`. Ratings are advisory judgments, not safety
proofs or measurements. The coordinator resolves findings by evidence rather
than majority vote.

| Review | Configured model | Strongest contribution |
| --- | --- | --- |
| Security A | `gpt-6.1-sol` | Exclusion precedence, descendant lifetime, alias coverage |
| Security B | `gpt-6.1-sol` | Exclusion precedence, port versus protocol policy, recursive plugin admission |
| Security Astra | `gpt-6-astra` | Exclusion precedence, bootstrap placement, terminal prerequisites |
| Developer experience A | `gpt-6.1-sol` | Scratch path semantics, authority labels, workflow continuation |
| Developer experience B | `gpt-6.1-sol` | Explicit private intent, trust persistence, login recovery |
| Developer experience Astra | `gpt-6-astra` | Local verification limits, worktree placement, Git attribution |

Security reviewers rated correctness and privacy 3/5 each. Developer-experience
reviewers rated reliability 3–4/5 and ease of use 2–3/5, where 5 is best. These
ratings describe the original source snapshot. The reviewers did not rerun their
assessments after the owner-approved correction pass. Subsequent test results
are separate evidence, not revised model scores.

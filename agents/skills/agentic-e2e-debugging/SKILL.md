---
name: agentic-e2e-debugging
description: Exercise and debug a full user flow across the browser, services, and logs. Use for "test this start to finish", lifecycle failures, or end-to-end fixes that require repeated UI and backend verification.
---

# Agentic E2E Debugging

Use this workflow when a failure crosses the browser, one or more services,
and persisted state. For a single-page inspection, use
[`browser-tooling`](../browser-tooling/SKILL.md). For a failure that does not
need a browser, use
[`systematic-debugging`](../systematic-debugging/SKILL.md).

## Establish the contract

Before driving the UI, name:

- the user journey and expected terminal state
- the services and data stores it crosses
- the observable evidence for each transition
- the safe test account or fixture
- the repository's native start, health, log, and test commands

Do not invent generic service commands or credentials. Discover them from the
project's task runner, README, process configuration, and test fixtures. Ask
before creating accounts, changing shared data, or restarting a service you do
not own.

## The loop

1. Reproduce the journey from a known state and record the first incorrect
   transition.
2. Correlate that transition with bounded browser console, network, service-log,
   and data evidence. Prefer request, trace, session, or record IDs over time
   proximity.
3. Form one root-cause hypothesis and identify the observation that could
   disprove it.
4. Make the smallest fix at the layer that violated its contract.
5. Reload only the affected process using the project's supported mechanism.
6. Repeat the same journey from the same starting state.
7. Add the lowest-cost deterministic regression test that would have caught the
   defect, then run the relevant project gate.

Keep downstream errors separate from the earliest contract violation. One bad
request can create several secondary UI and worker failures; patching all of
them at once destroys the evidence chain.

## Evidence discipline

- Take a fresh browser snapshot after navigation before using element
  references.
- Use bounded log reads. Do not leave an unbounded follow process running.
- Capture relevant status codes, request payload shape, correlation IDs, state
  changes, and the exact failing assertion.
- Distinguish an absent event from an unobserved event. Add temporary targeted
  instrumentation when the current telemetry cannot tell.
- Remove temporary instrumentation unless it closes a durable observability
  gap; durable breadcrumbs must avoid secrets and personal data.
- Never copy a real user's cookie, token, or credentials into a test session.

## Browser and service control

Follow [`browser-tooling`](../browser-tooling/SKILL.md) to select the available
browser driver. Preserve a single session only when the journey requires it;
otherwise reset state between attempts so an earlier run cannot mask the bug.

Use project-owned lifecycle commands. Confirm which checkout the running
process watches before concluding that an edit did not work. In a worktree, a
watcher may be attached to a different checkout. Do not commit, merge, restart
shared infrastructure, kill arbitrary processes, or edit environment files
merely to trigger reload unless the user has authorized that operation.

## Regression lock-in

Choose the cheapest test that reproduces the violated contract:

- unit test for isolated logic
- contract test for a service or serialization boundary
- integration test for persistence or multi-service behavior
- browser journey only when browser behavior is essential

The test must fail for the original reason before the fix and pass afterward.
Use the repository's established framework and placement conventions; see
[`testing`](../testing/SKILL.md).

## Report

Report the journey, earliest failing transition, root cause, fix, regression
test, and verification commands. If the journey remains incomplete, name the
exact boundary and missing evidence instead of calling the flow verified.

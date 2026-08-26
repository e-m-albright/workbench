---
name: reflect
description: Review what worked, failed, and should improve. Use for "/reflect", "what could we have done better", retrospectives, or lessons learned.
argument-hint: "[quick|full] [focus]"
---

# Reflect

Produce an evidence-backed retrospective that improves the next workflow. Be candid without manufacturing criticism: a good result can still have an inefficient process, and a difficult process can still contain practices worth repeating.

## Gather evidence

1. Restate the intended outcome and whether it was achieved.
2. Check `git status --short` and the relevant diff when code changed.
3. Review commands, test results, corrections, reversals, and user feedback visible in the session.
4. Separate observed facts from inference. Do not claim confidence or coverage without evidence.

Use `quick` for a short workflow or a narrow question. Use `full` for long, costly, failed, or strategically important work.

## Analyze the workflow

Evaluate these questions:

- **Outcome:** Did the work solve the requested problem with the intended scope?
- **What worked:** Which decisions, tools, sequencing choices, or verification steps reduced risk or rework?
- **What did not:** Where did the process stall, drift, duplicate effort, rely on weak assumptions, or discover constraints late?
- **Better approach:** What specific sequence would be faster, clearer, or safer next time?
- **Durable improvement:** Should a test, document, rule, skill, command, or automation change prevent recurrence?

Prefer high-leverage observations. Avoid generic advice such as “plan better,” “communicate more,” or “add tests” unless you name the missed decision, communication boundary, or test seam.

For each proposed improvement, include:

- the evidence that supports it;
- the concrete change;
- its scope: this task, this repository, or global workflow;
- whether it is worth implementing now.

Ask before promoting an in-session preference into a broad rule. Do not modify files unless the user requested implementation as well as reflection.

## Output

```markdown
## Reflection

### Outcome
- <result and evidence>

### What worked
- <practice worth repeating and why>

### What did not
- <specific friction or mistake and its consequence>

### Better next time
1. <changed step or sequence>
2. <verification improvement>

### Worth formalizing
- <artifact and target path, or "Nothing yet">

### Confidence
- <high, medium, or low, with the main evidence gap>
```

In `quick` mode, keep each section to one or two bullets. In `full` mode, also cover relevant test posture, scope control, tool choice, handoff quality, and unresolved risks.

A reflection explains how to improve the process. If another session must continue the work, invoke the `handoff` skill separately so temporary state and durable learning remain distinct.

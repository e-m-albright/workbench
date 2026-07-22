---
name: pi-guide
description: Print a versioned tutorial for using Pi's native features and Evan's custom harness before proposing new machinery. Use for "/skill:pi-guide", "teach me Pi", "Pi shortcuts", or "am I using Pi well".
allowed-tools: Read
disable-model-invocation: true
argument-hint: "[quickstart|keys|sessions|tools|custom|philosophy|all]"
---

# Pi Guide

Teach the owner how to use Pi well before suggesting another extension. This is a
read-only tutorial, not a configuration workflow.

## Workflow

1. Read `references/tutorial.md` completely.
2. Interpret the optional argument:
   - no argument or `quickstart`: print the concise daily workflow and essential
     keys
   - `keys`: print the full practical keybinding guide
   - `sessions`: explain names, resume, tree, fork, clone, compact, export, and
     safe transcript navigation
   - `tools`: explain native tools, Bash, skills, prompt templates, packages,
     models, thinking, and project trust
   - `custom`: explain Workbench's Pi extensions and package additions
   - `philosophy`: explain what is intentionally absent and why
   - `all`: print every section, using compact tables
3. State the installed-doc snapshot version and distinguish native Pi behavior
   from Workbench customization.
4. If the user's observed behavior conflicts with the tutorial, treat the live
   behavior as evidence. Suggest the smallest diagnostic rather than claiming the
   documentation must be right.
5. End with at most three underused capabilities relevant to the user's current
   workflow. Do not recommend installing anything unless the user asks.

## Output rules

- Use exact command and key names.
- Warn when a command changes session state, branch position, credentials, or
  external state.
- Explain `/tree` preview versus Enter selection clearly: preview is harmless;
  Enter changes the active leaf.
- Prefer native Pi, terminal, Git, and existing trusted CLI features over custom
  replacements.
- Do not edit settings, install packages, authenticate services, or mutate files.

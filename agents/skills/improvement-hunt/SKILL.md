---
name: improvement-hunt
description: Deprecated alias for project-health-review. Use only for the old /improvement-hunt command.
disable-model-invocation: true
---

# Improvement Hunt

This workflow is now named `project-health-review` and is organized into three
explicit layers:

- `capability-health` decides what the project should provide.
- `repository-health` assesses the repository's operating layer.
- `code-health` assesses implementation health.

Use `project-health-review` to orchestrate all three. This compatibility entry
exists only so the old explicit command resolves to the new name; do not
maintain a second audit rubric here.

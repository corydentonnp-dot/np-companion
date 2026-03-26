---
description: Safe pull/push workflow for this repository.
agent: agent
---

# Git Operations

Use this prompt for routine pull or push operations without destructive commands.

## Pull Workflow

1. Check local state:
```powershell
git status --short
```
2. If local changes exist, commit first with timestamped message.
3. Pull from `origin/main`.
4. Report result:
- updated files count
- already up to date status
- merge conflicts (if any), then stop

## Push Workflow

1. Stage all intended changes and inspect status.
2. If there are staged changes, commit with timestamped message.
3. Push to `origin/main`.
4. If nothing to commit, report and stop.

## Safety Rules

- No force push.
- No reset hard.
- No pull force.
- No background terminal commands.
- Do not run unrelated side effects (tests/migrations/restarts) in this prompt.

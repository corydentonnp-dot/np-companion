---
description: Stage all changes, commit with a timestamped message, and push to GitHub.
agent: agent
---

# Push to Git

Stage everything, commit with a timestamp, and push to origin/main.

## Steps

1. Run this command in the terminal (NOT background, timeout 60000ms):
```powershell
cd C:\Users\coryd\Documents\NP_Companion; git add -A; git status --short
```

2. If there are staged changes, commit and push:
```powershell
git commit -m "Manual save -- $(Get-Date -Format 'MM-dd-yy HH:mm:ss')"; git push
```

3. If `git status` shows "nothing to commit" — say so and stop. Don't treat it as an error.

4. Report back: how many files changed, and confirm the push succeeded (or failed with reason).

## Rules
- Never use `isBackground: true` for these commands.
- Never force-push (`--force`). If push is rejected, report the error and stop.
- Do not run migrations, tests, or any other side effects — just commit and push.

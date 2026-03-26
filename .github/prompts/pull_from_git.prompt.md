---
description: Pull the latest changes from GitHub into this computer's local copy.
agent: agent
---

# Pull from Git

Pull the latest code from GitHub (origin/main) into the local workspace.

## Steps

1. First check for any uncommitted local changes (timeout 15000ms, NOT background):
```powershell
cd C:\Users\coryd\Documents\NP_Companion; git status --short
```

2. If there are uncommitted local changes, commit them first before pulling:
```powershell
git add -A; git commit -m "Auto-save before pull -- $(Get-Date -Format 'MM-dd-yy HH:mm:ss')"
```

3. Pull from origin:
```powershell
git pull origin main
```

4. Report back:
   - How many files were updated
   - If already up to date, say so
   - If there was a merge conflict, describe which files conflicted and stop — do NOT attempt to resolve conflicts automatically

## Rules
- Never use `isBackground: true` for these commands.
- Never use `git pull --force` or `git reset --hard`. Those destroy local work.
- Do not restart the Flask server, run tests, or do anything else — just pull.
- If the pull fails (auth error, conflict, etc.), report the exact error message and stop.

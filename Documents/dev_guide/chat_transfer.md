
Let me check the current MCP config and VS Code setup to write accurate instructions: 

Read [](file:///c%3A/Users/coryd/Documents/NP_Companion/.vscode)

Ran terminal command: node --version; python --version 2>&1; git --version 2>&1

Read [](file:///c%3A/Users/coryd/Documents/NP_Companion/.vscode/mcp.json)

Good. Now make sure mcp.json is tracked in git (it's in .vscode which has a wildcard exclusion — need to add an exception): 

Read [](file:///c%3A/Users/coryd/Documents/NP_Companion/.gitignore#10-10), lines 10 to 25

Searched for text `.vscode` (`**/.gitignore`), 3 results

mcp.json isn't whitelisted. Fix that and push it to GitHub so Computer 2 gets it automatically: 

Replacing 3 lines with 4 lines in [](file:///c%3A/Users/coryd/Documents/NP_Companion/.gitignore)


```

```


Ran terminal command: git add .gitignore .vscode/mcp.json; git commit -m "Track mcp.json for Playwright MCP sync to Computer 2"; git push

Good — mcp.json is now on GitHub. Here's the complete copy-paste guide for Computer 2:

---

## CareCompanion — Computer 2 Setup Guide

*Copy this whole thing into Gmail, then paste into VS Code chat on the other computer.*

---

### PART 1 — Install these 4 programs (in order)

**1. Python 3.11** — https://www.python.org/downloads/release/python-3110/
- Scroll down to "Files", download **Windows installer (64-bit)**
- ⚠️ On the FIRST screen of the installer, check **"Add Python to PATH"** before clicking Install

**2. Git** — https://git-scm.com/download/win
- Click the first download link, run it, click Next through everything

**3. Node.js** — https://nodejs.org/en/download
- Download **LTS version**, run installer, click Next through everything
- (This is needed for the Playwright browser tools)

**4. VS Code** — https://code.visualstudio.com/
- Download, install, defaults are fine

---

### PART 2 — Get the project (PowerShell commands)

Open **PowerShell** (search it in the Start menu). Paste these one at a time:

```powershell
cd C:\Users\coryd\Documents
git clone https://github.com/corydentonnp-dot/np-companion.git NP_Companion
cd NP_Companion
```

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

```powershell
Get-ChildItem migrations\*.py | Sort-Object Name | ForEach-Object { Write-Host "Running $($_.Name)..."; venv\Scripts\python.exe $_.FullName }
```

```powershell
code .
```

---

### PART 3 — VS Code setup (one-time)

**Install extensions** — when VS Code opens it will show a popup: *"Do you want to install recommended extensions?"* → click **Install All**. This installs:
- GitDoc (auto-sync on save)
- GitHub Copilot + Copilot Chat
- Python + Pylance

If the popup doesn't appear: press `Ctrl+Shift+X`, search each one manually and install.

**Sign into GitHub Copilot** — VS Code will prompt you to sign in. Use the same GitHub account (`corydentonnp-dot`).

---

### PART 4 — Enable Playwright MCP (browser tools for Copilot)

Press `Ctrl+Shift+P`, type `Developer: Reload Window`, press Enter.

After reload, open Copilot Chat (`Ctrl+Alt+I`), switch the dropdown from **Ask** to **Agent** mode. Click the tools icon — you should see Playwright browser tools listed (navigate, screenshot, click, etc.).

The first time you use a browser tool, it will download Playwright automatically (~30 seconds). After that it's instant.

---

### PART 5 — Run the app

In the VS Code terminal (`Ctrl+`` ` ``):

```powershell
.\run.ps1
```

Chrome should open to `localhost:5000`. Log in: `CORY` / `ASDqwe123`

---

### PART 6 — Verify sync is working

1. On **this computer**, save any file
2. Wait 30 seconds
3. On **Computer 2**, wait up to 60 seconds — the file should update automatically without doing anything

GitDoc handles this automatically. You'll see it in the VS Code status bar at the bottom.

---

### What's the same on both computers
- All code, templates, routes ✅
- config.py (credentials/settings) ✅
- tesseract (OCR engine) ✅
- Playwright MCP config ✅
- VS Code settings ✅

### What each computer keeps separately
- carecompanion.db — each machine has its own database (patients, sessions, etc.)
- venv — Python packages are reinstalled locally from requirements.txt

---

*Paste this into Copilot Chat on Computer 2 after VS Code is open and say: "I just cloned CareCompanion. Verify everything is set up correctly and start where we left off."* 



Made changes.
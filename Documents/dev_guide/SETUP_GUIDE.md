# CareCompanion — New Machine Setup Guide

> Everything you need to get CareCompanion running on a fresh Windows PC.
> Estimated time: 20–30 minutes.

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Install Prerequisites](#2-install-prerequisites)
3. [Install CareCompanion](#3-install-carecompanion)
4. [Configure Settings](#4-configure-settings)
5. [First Launch](#5-first-launch)
6. [Verify Installation](#6-verify-installation)
7. [Optional Configuration](#7-optional-configuration)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| OS | Windows 10 (64-bit) | Windows 11 Pro |
| RAM | 8 GB | 16 GB |
| Disk Space | 2 GB free | 5 GB free |
| Display | 1920×1080 | 1920×1080 |
| Scaling | **Must be 100%** | 100% (125%+ breaks OCR) |
| Network | LAN access to AC server | LAN + internet for API features |

### Required Software

| Software | Purpose | Download |
|---|---|---|
| Python 3.11+ | Runtime for the app | https://www.python.org/downloads/ |
| Tesseract OCR 5.x | Screen reading for AC automation | https://github.com/UB-Mannheim/tesseract/wiki |
| Google Chrome | NetPractice scraper (CDP) | https://www.google.com/chrome/ |
| Amazing Charts EHR | Target EHR system | Already installed at practice |

---

## 2. Install Prerequisites

### Step 1 — Install Python

1. Download Python 3.11+ from https://www.python.org/downloads/
2. Run the installer
3. **Check "Add Python to PATH"** at the bottom of the first screen
4. Click "Install Now"
5. Verify: open PowerShell and run:
   ```
   python --version
   ```
   You should see `Python 3.11.x` or higher.

### Step 2 — Install Tesseract OCR

1. Download the installer from https://github.com/UB-Mannheim/tesseract/wiki
2. Install to the default location: `C:\Program Files\Tesseract-OCR\`
3. Verify: open PowerShell and run:
   ```
   & "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
   ```
   You should see `tesseract v5.x.x`.

### Step 3 — Install Google Chrome

1. Download from https://www.google.com/chrome/
2. Install to the default location
3. Create a Chrome shortcut that enables remote debugging:
   - Right-click Desktop → New → Shortcut
   - Target: `"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222`
   - Name: "Chrome Debug"
4. This shortcut is used for the NetPractice schedule scraper.

---

## 3. Install CareCompanion

### Option A — From Source (Development Machine)

```powershell
# Clone or copy the project folder
cd C:\Users\YourName\Documents
# Copy CareCompanion folder here (via USB, Git, or network share)

# Create virtual environment
cd CareCompanion
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for NetPractice scraper)
python -m playwright install chromium
```

### Option B — From Pre-Built Package (Work Machine)

1. Obtain the `CareCompanion_vX.X.X.zip` file (via USB, Google Drive, or email)
2. Extract to: `C:\Users\YourName\Documents\CareCompanion`
3. The folder should contain:
   ```
   CareCompanion\
   ├── CareCompanion.exe      ← Double-click to run
   ├── config.py             ← Your settings (edit once)
   ├── _internal\            ← App code (auto-managed)
   ├── data\                 ← Created on first run
   ├── tesseract\            ← OCR engine (if bundled)
   └── browsers\             ← Chromium (if bundled)
   ```

---

## 4. Configure Settings

### Copy the config template

If installing from source and no `config.py` exists yet:

```powershell
copy config.example.py config.py
```

### Edit config.py

Open `config.py` in any text editor (Notepad, VS Code) and configure:

#### Required Settings

```python
# Flask secret key — REPLACE with a random string (32+ characters)
SECRET_KEY = "your-random-secret-key-here-at-least-32-chars"

# Amazing Charts paths — verify these match your installation
AC_EXE_PATH = r"C:\Program Files (x86)\Amazing Charts\AmazingCharts.exe"
AC_DB_PATH = r"\\192.168.2.51\Amazing Charts\AmazingCharts.mdf"
AC_IMPORTED_ITEMS_PATH = r"\\192.168.2.51\amazing charts\ImportItems"

# Tesseract path
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

#### Optional Settings (enable as needed)

```python
# Pushover notifications (mobile alerts)
PUSHOVER_USER_KEY = ""
PUSHOVER_API_TOKEN = ""

# SMTP email (weekly and monthly reports)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = ""
SMTP_PASS = ""
SMTP_FROM = ""

# API keys (improve rate limits and enable extra features)
OPENFDA_API_KEY = ""        # OpenFDA — drug safety
UMLS_API_KEY = ""           # NLM UMLS — SNOMED, RxNorm
LOINC_USERNAME = ""         # LOINC — lab reference ranges
LOINC_PASSWORD = ""
PUBMED_API_KEY = ""         # PubMed — literature search
```

#### Production Settings (before real patient data)

```python
DEBUG = False               # NEVER True in production
AC_MOCK_MODE = False        # False = live AC automation
SCREEN_RESOLUTION = (1920, 1080)
```

> **Security note:** `config.py` contains secrets. Never share it, commit it to Git, or place it in a shared folder. The `.gitignore` already excludes it.

---

## 5. First Launch

### From Source

```powershell
cd C:\Users\YourName\Documents\CareCompanion
venv\Scripts\activate
python launcher.py
```

Or use the batch file:
```
Double-click Start_CareCompanion.bat
```

### From Pre-Built Package

```
Double-click CareCompanion.exe
```

### What Happens on First Launch

1. SQLite database (`data/carecompanion.db`) is created automatically
2. All pending migrations run automatically
3. You are redirected to the **Registration** page
4. Create your admin account (first user = admin)
5. The dashboard loads at `http://localhost:5000`

### System Tray

A blue "NP" icon appears in your system tray. Right-click for:
- **Open CareCompanion** — show the browser window
- **Pause / Resume Agent** — toggle background monitoring
- **Check Inbox Now** — trigger immediate inbox scan
- **Quit** — fully close the application

---

## 6. Verify Installation

### Quick Smoke Test

After the app is running, check these URLs in Chrome:

| URL | Expected |
|---|---|
| `http://localhost:5000` | Login page (or dashboard if logged in) |
| `http://localhost:5000/api/health` | `{"status": "ok", "db": "connected"}` |

### Run Automated Tests (from source installs)

```powershell
cd C:\Users\YourName\Documents\CareCompanion
venv\Scripts\activate

# Main test suite
python test.py

# Full deployment check
python tools/deploy_check.py
```

Expected: all checks PASS, 0 failures, 0 errors.

### Run USB Smoke Test (from pre-built package)

```powershell
python tools/usb_smoke_test.py
```

Expected: 8/8 checks pass.

---

## 7. Optional Configuration

### NetPractice Schedule Scraper

1. Set `NETPRACTICE_URL` and `NETPRACTICE_CLIENT_NUMBER` in `config.py`
2. Launch Chrome with the debug shortcut (Section 2, Step 3)
3. Log in to NetPractice manually in that Chrome window
4. CareCompanion will use the active session to pull schedules

### Notification Setup

#### Pushover (mobile push notifications)

1. Create account at https://pushover.net/
2. Create an application to get your API token
3. Set `PUSHOVER_USER_KEY` and `PUSHOVER_API_TOKEN` in `config.py`
4. Test: Admin → Agent → Send Test Push

#### SMTP Email (weekly/monthly reports)

1. Set `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` in `config.py`
2. For Gmail: use an App Password (not your regular password)
3. Test: Admin → Agent → Send Test Email

### Agent Background Service

The agent runs background jobs for inbox monitoring, schedule polling, EOD checks, and more. To install as a Windows service:

```powershell
python agent_service.py install
python agent_service.py start
```

Or run it manually alongside the web app using `Start_CareCompanion.bat`.

### Display Scaling Warning

CareCompanion uses OCR to read the Amazing Charts screen. This requires:
- Screen resolution: **1920×1080**
- Display scaling: **100%**
- DPI: 96

If your display uses 125% or 150% scaling, OCR coordinates will be off. To check:
1. Right-click Desktop → Display Settings
2. Under "Scale and layout", ensure it says **100%**

---

## 8. Troubleshooting

### "Python is not recognized"

Python is not on your PATH. Reinstall Python and check "Add Python to PATH", or add it manually:
```
Settings → System → About → Advanced system settings → Environment Variables → Path → Edit → Add C:\Users\YourName\AppData\Local\Programs\Python\Python311\
```

### Restarting the Server

If you need to kill all Python processes and restart fresh:
```powershell
# Kill any existing Python/server processes
taskkill /F /IM python.exe 2>$null
taskkill /F /IM pythonw.exe 2>$null

# Verify port 5000 is free
netstat -ano | findstr ":5000"
# If anything shows LISTENING, kill that PID:
# taskkill /F /PID <the_PID_number>

# Navigate to project and activate venv
cd C:\Users\coryd\Documents\NP_Companion
.\venv\Scripts\Activate.ps1

# Start the Flask server
python launcher.py --mode=server
```

**One-click option:** Double-click `beta_launch.bat` or `restart.bat` — they handle all of the above automatically.

### "Port 5000 is already in use"

Another instance is running. Kill it:
```powershell
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force
```
Or use `restart.bat` which handles this automatically.

### "Tesseract not found"

Verify the path in `config.py` matches your install:
```powershell
Test-Path "C:\Program Files\Tesseract-OCR\tesseract.exe"
```
If False, Tesseract is installed elsewhere or not installed.

### OCR reads wrong text / coordinates are off

1. Check display scaling is 100% (not 125%)
2. Check resolution matches `SCREEN_RESOLUTION` in `config.py`
3. Recalibrate: run `python tools/deploy_check.py` Section 2 (Machine & Display)

### Database errors on startup

Run integrity check:
```powershell
python -c "import sqlite3; c=sqlite3.connect('data/carecompanion.db'); print(c.execute('PRAGMA integrity_check').fetchone())"
```
Should print `('ok',)`. If not, restore from the most recent backup in `data/backups/`.

### Agent won't start / no scheduled jobs

1. Check agent status: `http://localhost:5000/api/agent-status`
2. Check logs: `data/logs/carecompanion.log`
3. Restart: close and relaunch via `Start_CareCompanion.bat`

### Amazing Charts paths unreachable

From the work PC, verify network paths:
```powershell
Test-Path "\\192.168.2.51\Amazing Charts\AmazingCharts.mdf"
Test-Path "\\192.168.2.51\amazing charts\ImportItems"
```
If False, check network connectivity and share permissions.

---

## Quick Reference Card

| Task | Command |
|---|---|
| Start app (source) | `venv\Scripts\activate` → `python launcher.py` |
| Start app (packaged) | Double-click `CareCompanion.exe` |
| Start app (batch) | Double-click `Start_CareCompanion.bat` |
| Run tests | `python test.py` |
| Deployment check | `python tools/deploy_check.py` |
| Full verification | `python tools/verify_all.py` |
| Check health | `http://localhost:5000/api/health` |
| Kill stuck process | `Get-Process python \| Stop-Process -Force` |
| Restart | Double-click `restart.bat` |
| Backup database | Automatic nightly; manual: copy `data/carecompanion.db` |

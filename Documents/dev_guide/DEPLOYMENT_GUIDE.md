# CareCompanion — Deployment & Transfer Guide

> How to build on your personal PC, transfer to the work PC, and run it.

---

## Table of Contents

1. [One-Time Setup (Personal PC)](#1-one-time-setup-personal-pc)
2. [Building the .exe Package](#2-building-the-exe-package)
3. [Transferring to the Work PC](#3-transferring-to-the-work-pc)
4. [First-Time Install on Work PC](#4-first-time-install-on-work-pc)
5. [Opening & Running CareCompanion](#5-opening--running-carecompanion)
6. [Updating CareCompanion](#6-updating-carecompanion)
7. [Daily Workflow](#7-daily-workflow)
8. [Troubleshooting](#8-troubleshooting)
9. [What's Inside the Package](#9-whats-inside-the-package)

---

## 1. One-Time Setup (Personal PC)

You only need to do this once on your development machine.

### Install PyInstaller

```
cd C:\Users\coryd\Documents\CareCompanion
venv\Scripts\pip install pyinstaller
```

### Bundle Tesseract OCR (optional, for AC automation)

Create a `tesseract` folder next to the project and copy your Tesseract installation into it:

```
CareCompanion\
├── tesseract\
│   ├── tesseract.exe
│   └── tessdata\
│       └── eng.traineddata
```

The exe will automatically find Tesseract in this location.

### Bundle Playwright Chromium (optional, for NetPractice scraping)

Create a `browsers` folder and copy your Playwright Chromium install:

```
CareCompanion\
├── browsers\
│   └── chromium-XXXX\
│       └── chrome-win\
│           └── chrome.exe
```

Find your current Playwright browsers at:
`%LOCALAPPDATA%\ms-playwright`

---

## 2. Building the .exe Package

Open a terminal on your personal PC and run:

```
cd C:\Users\coryd\Documents\CareCompanion
venv\Scripts\python build.py
```

### Build options

| Command | What it does |
|---------|-------------|
| `python build.py` | Build with current version |
| `python build.py --bump patch` | Bump 1.0.0 → 1.0.1, then build |
| `python build.py --bump minor` | Bump 1.0.0 → 1.1.0, then build |
| `python build.py --notes "Fixed inbox bug"` | Include release notes |
| `python build.py --usb E:` | Build + auto-copy zip to USB drive E: |
| `python build.py --open-drive` | Build + open Google Drive in browser |
| `python build.py --no-build` | Skip PyInstaller, just zip + deliver |

### What happens

1. Version is bumped in `config.py` (if `--bump` is used)
2. An app icon (`CareCompanion.ico`) is generated if missing
3. PyInstaller packages everything into `dist\CareCompanion\`
4. A zip file is created: `dist\CareCompanion_v1.0.1.zip`
5. The zip is copied to USB or Google Drive is opened (if flags used)

---

## 3. Transferring to the Work PC

Pick whichever method is easiest for you:

### Option A: Google Drive (recommended for daily updates)

1. On personal PC: Upload `CareCompanion_v1.0.1.zip` to Google Drive
2. On work PC: Open Chrome → Google Drive → Download the zip
3. It lands in `C:\Users\FPA\Downloads\`

### Option B: USB Drive

1. On personal PC: Run `python build.py --usb E:` (or copy the zip manually)
2. Plug USB into work PC
3. The zip is on the root of the USB drive (e.g. `E:\CareCompanion_v1.0.1.zip`)

### Option C: Email

1. On personal PC: Email the zip to yourself
2. On work PC: Open email → download the attachment
3. Works for smaller updates; large files (400+ MB) may hit email limits

---

## 4. First-Time Install on Work PC

This is only done once. After this, all future versions are applied as updates.

### Step 1: Extract the zip

1. Navigate to where you downloaded the zip (e.g. `C:\Users\FPA\Downloads\`)
2. Right-click `CareCompanion_v1.0.0.zip` → **Extract All**
3. Extract to: `C:\Users\FPA\Documents\CareCompanion`
   (or wherever you want the app to live — Desktop works too)

After extraction, the folder should look like:

```
CareCompanion\
├── CareCompanion.exe      ← Double-click this to run
├── config.py             ← Your settings (edit once, never overwritten)
├── _internal\            ← App code and dependencies (auto-managed)
├── data\                 ← Created on first run (database, backups)
├── tesseract\            ← (if bundled) OCR engine
└── browsers\             ← (if bundled) Playwright Chromium
```

### Step 2: Edit config.py (one time)

Open `config.py` in Notepad (right-click → Open with → Notepad) and update these settings for the work PC:

```python
# Update these for the work machine:
TESSERACT_PATH = r"C:\Users\FPA\Documents\CareCompanion\tesseract\tesseract.exe"

# If the AC paths are different on this machine, update them too:
AC_EXE_PATH = r"C:\Program Files (x86)\Amazing Charts\AmazingCharts.exe"
```

**Important:** `config.py` is never overwritten by updates. Your settings are safe.

### Step 3: (Optional) Create a Desktop shortcut

1. Right-click `CareCompanion.exe` → **Send to** → **Desktop (create shortcut)**
2. Rename the shortcut to "CareCompanion"
3. Now you can double-click the shortcut to launch

---

## 5. Opening & Running CareCompanion

### Starting the app

**Double-click `CareCompanion.exe`** (or your Desktop shortcut).

What happens:
1. Flask web server starts on port 5000
2. Background agent starts (inbox monitor, scheduler, etc.)
3. A native window opens showing the CareCompanion dashboard
4. A system tray icon (blue "NP" circle) appears near the clock

### First-time launch

On the very first launch (no database yet):
1. The app creates the database automatically
2. You're redirected to the **Register** page
3. Create your account — the first user automatically becomes **admin**
4. Log in and you're ready to go

### Closing the app

- **Click the X** on the window → the window hides to the system tray (app keeps running)
- **To fully quit:** Right-click the blue "NP" tray icon → **Quit**

### System tray options

Right-click the tray icon for:
- **Open CareCompanion** — show the window again
- **Pause Agent** — temporarily stop background monitoring
- **Resume Agent** — restart background monitoring
- **Check Inbox Now** — trigger an immediate inbox check
- **Quit** — fully close the application

---

## 6. Updating CareCompanion

### On your personal PC

```
python build.py --bump patch --notes "What changed in this version"
```

Transfer the new zip to the work PC (Google Drive, USB, or email).

### On the work PC

1. **Make sure the zip is somewhere accessible** (Downloads, USB drive, etc.)
2. **Open CareCompanion** (it should already be running)
3. Go to **Admin** → **Software Updates**
4. Enter the folder path where the zip is:
   - Downloads: `C:\Users\FPA\Downloads`
   - USB drive: `E:\`
   - Google Drive sync: wherever your Drive folder is
5. Click **Scan Folder**
6. The newest version found will appear with release notes
7. Click **Apply Update**
   - The app extracts the zip, replaces code files
   - Your database, config.py, browsers, and tesseract are **never touched**
8. Click **Restart**
   - The app restarts with the new version
   - You'll be redirected to the dashboard automatically

### What's preserved during updates

These are **never** overwritten:
- `data/` — your database, backups, exports
- `config.py` — your machine-specific settings
- `browsers/` — Playwright Chromium
- `tesseract/` — Tesseract OCR

---

## 7. Daily Workflow

### Morning (Personal PC — if you made changes)

```
cd C:\Users\coryd\Documents\CareCompanion
python build.py --bump patch --notes "Morning fixes" --open-drive
```

Upload the zip from `dist\` to Google Drive.

### At Work

1. Download zip from Google Drive
2. Open CareCompanion → Admin → Software Updates
3. Enter `C:\Users\FPA\Downloads` → Scan → Apply → Restart
4. Done — takes under a minute

### If no changes were made

Don't build a new version. The existing version keeps running fine.

---

## 7a. Clinical Summary XML Import

CareCompanion parses CDA Clinical Summary XML files exported from Amazing Charts. There are three ways XML files can arrive:

### Automatic Folder Watching (watchdog)

If the `watchdog` library is installed, the agent automatically watches the configured export folder. Any new `.xml` file dropped into the folder is parsed and stored within seconds.

### Polling Fallback

A scheduler job polls the export folder every 30 seconds, detecting any new XML files that weren't caught by watchdog. This runs automatically — no configuration needed.

### Manual Upload

- **Dashboard:** Drag and drop one or more XML files onto the drop zone on the dashboard, or click to browse. MRN and patient data are auto-detected from the XML.
- **Patient Chart:** Open a patient chart and use the **Upload XML** button to import a file for a specific patient.

### Configuring the Export Folder

1. Go to **Settings** (gear icon)
2. Scroll to **Clinical Summary Import**
3. Enter the full path to the folder where AC exports XML files
4. Click **Save Export Folder**

Default: `data/clinical_summaries/` (relative to the app directory).

The `config.py` value `CLINICAL_SUMMARY_EXPORT_FOLDER` is used as a system-wide default. User-level settings override it.

### What Gets Imported

Each XML file populates:
- **Patient Record** (name, DOB, MRN)
- **Medications** (drug name, generic name, dosage, instructions, status)
- **Diagnoses** (problem name, ICD-10/SNOMED codes, status, onset date)
- **Allergies** (substance, reaction, severity)
- **Immunizations** (vaccine name, date given)
- **Vitals** (height, weight, BMI, BP, HR, O2, temp, RR per encounter date)

Re-importing for the same patient replaces their existing data.

---

## 8. Troubleshooting

### App won't start

- **Windows SmartScreen warning:** Click "More info" → "Run anyway". This is normal for new .exe files not from a known publisher.
- **Antivirus blocks it:** Add `CareCompanion.exe` and the `CareCompanion` folder to your antivirus exclusions (Windows Defender: Settings → Virus & threat protection → Manage settings → Exclusions → Add a folder).
- **Missing DLLs:** Make sure you extracted the entire zip, not just the .exe. The `_internal` folder must be present.

### Port 5000 already in use

Another instance may be running. Check the system tray for the blue "NP" icon and quit it first. Or open Task Manager and end `CareCompanion.exe`.

### Can't find the update zip

Double-check the folder path you entered. Common locations:
- Downloads: `C:\Users\FPA\Downloads`
- USB: `E:\` or `F:\` (check "This PC" in File Explorer)
- Desktop: `C:\Users\FPA\Desktop`

### Update says "no newer version found"

The zip filename must follow the pattern `CareCompanion_v1.2.3.zip` and the version number must be higher than the current version shown on the Updates page.

### App is slow / frozen

- Check Task Manager for CPU/memory usage
- Try Admin → Restart Server
- Quit and relaunch the .exe

### Need to reset everything

Delete the `data\carecompanion.db` file. On the next launch, a fresh database will be created and you'll go through the first-time setup again. Your config.py settings are kept.

---

## 9. What's Inside the Package

```
CareCompanion_v1.0.0.zip
└── CareCompanion\
    ├── CareCompanion.exe        ← Main executable (~15 MB)
    ├── config.py               ← User settings (edit once)
    ├── CareCompanion.ico        ← App icon
    ├── release_notes.txt       ← What changed (if provided)
    ├── _internal\              ← Python runtime + all dependencies
    │   ├── templates\          ← HTML templates
    │   ├── static\             ← CSS, JavaScript
    │   └── ... (Python libs)
    ├── data\                   ← Created on first run
    │   ├── carecompanion.db      ← SQLite database
    │   └── backups\            ← Automatic backups
    ├── tesseract\              ← Tesseract OCR (if bundled)
    │   ├── tesseract.exe
    │   └── tessdata\
    └── browsers\               ← Playwright Chromium (if bundled)
        └── chromium-XXXX\

Total size: ~400-500 MB (mostly Chromium + Python runtime)
Without browsers/tesseract: ~80-120 MB
```

---

## Quick Reference Card

| Task | Where | Command / Action |
|------|-------|-----------------|
| Build new version | Personal PC | `python build.py --bump patch` |
| Build + copy to USB | Personal PC | `python build.py --bump patch --usb E:` |
| Build + Google Drive | Personal PC | `python build.py --bump patch --open-drive` |
| Transfer | Any | Google Drive / USB / Email the zip |
| First install | Work PC | Extract zip → edit config.py → double-click exe |
| Daily update | Work PC | Admin → Updates → Scan → Apply → Restart |
| Launch app | Work PC | Double-click CareCompanion.exe |
| Hide to tray | Work PC | Click window X button |
| Show from tray | Work PC | Double-click tray icon |
| Fully quit | Work PC | Right-click tray icon → Quit |

---

## Pre-Beta USB Deployment Smoke Test

Before the first real-patient session, run the automated smoke test to verify the deployment is healthy.

### Steps

1. **Build:** `python build.py` — produces `build/carecompanion/`
2. **Copy** `build/carecompanion/` to USB drive
3. **On work PC:** Run `Start_CareCompanion.bat` from the USB directory
4. **Wait** ~30 seconds for the server to start
5. **Run the smoke test:**
   ```
   python tools/usb_smoke_test.py
   ```
6. **Verify** all checks pass in the generated `usb_smoke_report_*.txt`
7. **Open browser** to `http://localhost:5000` and confirm the login page loads
8. **Log in** and verify the dashboard is visible

### What the Smoke Test Checks

| # | Check | Pass Criteria |
|---|-------|---------------|
| 1 | Health endpoint | `GET /api/health` returns `{"status": "ok"}` |
| 2 | Login page | `GET /login` returns HTTP 200 |
| 3 | Database file | `data/carecompanion.db` exists on disk |
| 4 | Logs directory | `data/logs/` exists |
| 5 | Backups directory | `data/backups/` exists |
| 6 | DB integrity | `PRAGMA integrity_check` returns `ok` |
| 7 | Migrations | ≥35 migrations applied |
| 8 | Default user | At least 1 user exists in the database |

### Reference

- Script: [`tools/usb_smoke_test.py`](../tools/usb_smoke_test.py)
- Report output: `tools/usb_smoke_report_YYYYMMDD_HHMMSS.txt`

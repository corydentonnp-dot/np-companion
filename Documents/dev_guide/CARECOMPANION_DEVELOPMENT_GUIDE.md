**CARECOMPANION**

Complete Development Guide

*For Non-Programmers*

*Your Step-by-Step Blueprint to Building a Complete Clinical Workflow Platform*

**31 Features  â€¢  74+ Sub-Features  â€¢  104 Total Components**

Built for Windows 11 Pro  â€¢  VS Code  â€¢  Claude AI

---

# Feature Implementation Status

> **Last updated:** 2026-03-16  |  **Test suite:** ~887 tests (127 main + 42 pytest + 525 phase suites + 95 calculator phases + 98 final_plan phases)  |  **Database:** 60+ tables  |  **API clients:** 26 services  |  **Billing detectors:** 27  |  **Clinical calculators:** 19 (+ 4 blocked/partial)  |  **Pricing waterfall:** Cost Plus â†’ NADAC â†’ GoodRx â†’ NeedyMeds/RxAssist

| Feature | Description | Status | Notes |
|---------|-------------|--------|-------|
| **F1** | Core Platform (auth, dashboard, base UI) | âœ… Complete | 20+ blueprints, dark mode, auto-lock, agent health |
| **F2** | Background Agent & Scheduler | âœ… Complete | System tray, APScheduler, heartbeat, crash recovery |
| **F3** | NetPractice Schedule Scraper | âœ… Complete | Playwright-based, schedule parser, Chrome 136 debug profile |
| **F4** | Today View & Timer | âœ… Complete | Dashboard, timer, manual entry, paste-from-OCR, data collection, double-booking detection (RP4) |
| **F5** | Inbox Monitor | âœ… Complete | OCR-based, snapshot diffs, priority detection |
| **F6** | Clinical Summary Parser (CDA XML) | âœ… Complete | Patient chart, vitals, meds, diagnoses, allergies, new-med education trigger (RP4) |
| **F7** | On-Call Note Keeper | âœ… Complete | CRUD, export, callback tracking |
| **F8** | Order Set Manager | âœ… Complete | Sets, items, versions, execution tracking |
| **F9** | Chart Prefill (AC Automation) | â¸ï¸ AC-Blocked | Requires Amazing Charts calibration |
| **F10** | Medication Reference | âœ… Complete | Drug lookup, interactions, RxNorm enrichment, guideline review admin (RP4) |
| **F11** | Lab Tracker | âœ… Complete | Per-patient tracking, trends, panels |
| **F12** | Care Gap Tracker | âœ… Complete | Age/sex rules, admin rule editor, gap alerts |
| **F13** | Metrics Dashboard | âœ… Complete | Productivity, on-call, billing metrics |
| **F14** | Patient Roster | âœ… Complete | Search, chart links, specialist tracking |
| **F15** | Billing Tools | âœ… Complete | CPT/ICD-10 lookup, billing rules, opportunities |
| **F16** | Coding Suggester | âœ… Complete | ICD-10 search, favorites, code pairing, AWV interactive checklist (RP4) |
| **F17** | Care Gap Alerts (CDS) | âœ… Complete | HealthFinder API, CDC immunizations |
| **F18** | Delayed Message Sender | âœ… Complete | Queue, compose, cancel, scheduler job |
| **F19** | Result Response Templates | âœ… Complete | 13 templates across 5 tiers, template picker, shared template library (RP4) |
| **F20** | End-of-Day Checker | âœ… Complete | 5-category checklist, scheduler, Pushover alerts |
| **F21** | Push Notification System | âœ… Complete | Pushover, quiet hours, notification history |
| **F22** | Morning Briefing | âœ… Complete | Schedule + weather + care gaps + inbox summary |
| **F22a** | Commute Mode (TTS) | âœ… Complete | Web Speech API, hands-free briefing |
| **F23** | AutoHotkey Macro Library | âœ… Complete | CRUD, dot phrases, AHK generator, import/export, auto-sync to disk (RP4) |
| **F24** | Follow-Up Tickler System | âœ… Complete | Due dates, snooze, assign, recurring |
| **F25** | Prior Authorization Tracker | âœ… Complete | PA forms, status tracking, PDMP morning briefing flag (RP4) |
| **F26** | Referral Letter Generator | âœ… Complete | Templates, specialist directory, 21 specialty-specific field sets (RP4) |
| **F27** | Note Reformatter | âœ… Complete | Reformat logs, flagged items |
| **F28** | Provider Onboarding Wizard | âœ… Complete | 5-step wizard, skip support, auto-redirect, starter pack import (RP4) |
| **F29** | Admin Tools | âœ… Complete | User mgmt, config, sitemap, updates |
| **F30** | Offline Mode | ðŸ”² Not Started | Requires Service Worker + IndexedDB |
| **F31** | AI Assistant Integration | âœ… Complete | OpenAI/Anthropic/xAI, HIPAA ack |
| **F32** | Clinical Calculators | âœ… Complete | 48-calculator library: auto-score widget, risk tool picker, top-menu entry, trend monitoring, questionnaire forms, semi-auto pre-population, billing integration (Phases 31â€“38) |

### Structured API Cache Models (Phase 6)

All 13 cache tables implemented and wired to API clients:

| Cache Model | API | TTL | Status |
|------------|-----|-----|--------|
| `RxNormCache` | RxNorm (NIH/NLM) | Permanent | âœ… |
| `RxClassCache` | RxClass (NIH/NLM) | 90 days | âœ… |
| `Icd10Cache` | ClinicalTables (NLM) | 365 days | âœ… |
| `FdaLabelCache` | OpenFDA Labels | 30 days | âœ… |
| `FaersCache` | OpenFDA FAERS | 30 days | âœ… |
| `RecallCache` | OpenFDA Recalls | 24 hours | âœ… |
| `LoincCache` | LOINC (NLM) | 365 days | âœ… |
| `UmlsCache` | UMLS (NLM) | 90 days | âœ… |
| `HealthFinderCache` | AHRQ HealthFinder | 90 days | âœ… |
| `PubmedCache` | PubMed E-utilities | 30 days | âœ… |
| `MedlinePlusCache` | MedlinePlus Connect | 30 days | âœ… |
| `CdcImmunizationCache` | CDC CVX | 90 days | âœ… |
| `BillingRuleCache` | CMS PFS | Annual | âœ… |

### Pricing API Cache (Running Plan 3, Phases 19â€“29)

| Cache Key Pattern | API | TTL | Status |
|-------------------|-----|-----|--------|
| `cost_plus:name:{drug}` | Cost Plus Drugs | 72 hours | âœ… |
| `cost_plus:ndc:{ndc}` | Cost Plus Drugs | 72 hours | âœ… |
| `goodrx:search:{drug}` | GoodRx Price Compare | 24 hours | âœ… (awaiting API key) |
| `drug_assistance:programs:{drug}` | NeedyMeds + RxAssist | 7 days | âœ… |

### Pricing Integration Summary

- **PricingService** (`app/services/pricing_service.py`): Four-tier waterfall orchestrator â€” Cost Plus (Tier 1, free, no auth) â†’ NADAC (Tier 1b, free CMS data) â†’ GoodRx (Tier 2, HMAC-SHA256, called only when Cost Plus misses) â†’ NeedyMeds/RxAssist (Tier 3, patient assistance programs)
- **ToS Compliance**: GoodRx and Cost Plus prices never appear in the same UI component (waterfall mutual exclusivity)
- **Badge Colors**: <$30 green, <$100 yellow, â‰¥$100 red
- **Endpoints**: `/api/medref/pricing` (single drug), `/api/patient/<mrn>/pricing` (bulk, max 20)
- **Patient Education**: Pricing paragraph auto-appended to patient education materials
- **Cache Refresh**: Daily at 5:30 AM, scoped to today's scheduled patients only
- **Demo Mode**: 10 drugs seeded with realistic pricing data for all demo patients

---

### Clinical Calculator System (Phases 31â€“38)

Fully implemented as of 2026-03-22. 48 calculators organized across 11 clinical categories.

| Surface | Description | Route |
|---------|-------------|-------|
| **Auto-Score Widget** | BMI, LDL, Pack Years, PREVENT compute silently on chart load | Patient chart â†’ Risk Scores widget |
| **Risk Tool Picker** | EHR-prefilled interactive forms for 11 semi-auto calculators | `/patient/<mrn>/risk-tools` |
| **Calculator Library** | Full 48-calculator catalog with category tabs and search | `/calculators` |
| **Score Trend Monitoring** | Historical scoring with sparklines, threshold alerts, care-gap linkage | Patient chart â†’ score history |
| **Questionnaire Forms** | GAD-7, EPDS, GDS-15, AUDIT-C, C-SSRS, AIRQ, CAT, Wells DVT, etc. | Calculator detail page |
| **Billing Integration** | `CalculatorBillingDetector` â€” 9 scoring triggers â†’ billing opportunities | Auto-discovered by billing engine |

**Automation tiers:**
- `auto_ehr` (4): BMI, LDL, Pack Years, PREVENT â€” silent computation
- `semi_auto_ehr` (11): ADA Risk, STOP-BANG, PCP-HF, Dutch FH, AAP HTN, etc. â€” EHR pre-fill + minimal user input
- `patient_reported` (18): GAD-7, EPDS, AUDIT-C, CRAFFT, C-SSRS, CAT, mMRC, etc.
- `clinician_assessed` (13): Wells DVT, PERC, Ottawa rules, PECARN, etc.
- `blocked/partial` (4): ASCVD PCE, Gail Model, Peak Flow (main), AAP HTN <13 (awaiting external coefficients)

**Key files:**
- `app/services/calculator_engine.py` â€” core computation engine
- `app/services/calculator_registry.py` â€” 19-calculator metadata registry
- `routes/calculator.py` â€” `calculator_bp` (5 routes)
- `models/calculator.py` â€” `CalculatorResult` model
- `billing_engine/detectors/calculator_detector.py` â€” `CalculatorBillingDetector`
- `tests/test_calculator_*.py` â€” 95 tests across 6 test files
- `final_plan.md` â€” Pre-beta deployment plan (7 phases, all complete); added 98 tests across 8 new test files, 5 deployment tools, and 2 pre-existing bug fixes

---

# **How to Use This Guide**

This guide is designed so that you can work through it from beginning to end without prior programming knowledge. Every section builds on the one before it. Think of it like assembling furniture â€” you follow the numbered steps in order, check that each piece is working before moving to the next, and the AI (Claude inside VS Code) writes most of the actual code for you. Your job is to understand what you are building, follow the steps, run the checkpoints, and provide the human context that only you have about how Amazing Charts and NetPractice actually behave.

| How the guide is structured: Each PHASE is a group of related features that belong together and should be built together. Each FEATURE has its own step-by-step build section, an AI prompt you copy and paste, a checkpoint to test, and a list of dependencies (things that must exist before you start). GREEN BOXES are checkpoints. Do not move to the next feature until every item in the checkpoint is confirmed working. BLUE BOXES are informational context to help you understand what you are building. YELLOW BOXES are warnings and things that commonly go wrong. DARK BOXES are AI prompts or code â€” copy these exactly. |
| :---- |

# **Section 1: Software to Install**

Install every item in this section before writing a single line of code. This is the foundation. Each piece of software listed here is free. The instructions assume you are on your personal computer (not the work PC) for development, and you will deploy to the work PC later.

### **1.1  Python 3.11**

The main programming language for the entire backend of CareCompanion. Choose version 3.11 specifically for maximum library compatibility.

| Download URL: https://www.python.org/downloads/ |
| :---- |

**Installation steps:**

1. Go to python.org/downloads and download Python 3.11.x (not 3.12 or higher â€” some automation libraries lag behind).

2. Run the installer. On the FIRST screen, check the box that says "Add Python to PATH" before clicking Install. This is the most commonly missed step.

3. After installation, open a new Command Prompt window (search "cmd" in Start menu) and type: python \--version

4. You should see: Python 3.11.x â€” if you see an error, the PATH was not set correctly. Uninstall and reinstall with the checkbox checked.

### **1.2  Node.js (LTS version)**

Required for a small number of helper tools. Download the LTS (Long Term Support) version.

| Download URL: https://nodejs.org/ |
| :---- |

**Installation steps:**

5. Download the Windows LTS installer from nodejs.org.

6. Run the installer with all default settings.

7. Open Command Prompt and type: node \--version â€” you should see a version number.

### **1.3  Git for Windows**

Version control â€” tracks every change you make to your code so you can undo mistakes. Think of it as unlimited Ctrl+Z for your entire project.

| Download URL: https://git-scm.com/download/win |
| :---- |

**Installation steps:**

8. Download and run the installer. Accept all defaults â€” the default settings are correct for beginners.

9. When asked about the default text editor, you can choose VS Code from the dropdown if it appears.

10. After installation, open Command Prompt and type: git \--version

### **1.4  Visual Studio Code (VS Code)**

Your primary coding environment. Free, lightweight, and has excellent Claude AI integration.

| Download URL: https://code.visualstudio.com/ |
| :---- |

**Installation steps:**

11. Download from code.visualstudio.com and run the installer.

12. During installation, check both boxes that say "Add to PATH" and "Register Code as an editor for supported file types".

13. Open VS Code after installation.

### **1.5  Claude Extension for VS Code**

This puts Claude directly inside your coding environment so you can ask it to write code, explain errors, and suggest improvements without leaving VS Code.

| Download URL: Via VS Code Marketplace inside VS Code |
| :---- |

**Installation steps:**

14. Inside VS Code, click the square icon on the left sidebar (Extensions).

15. Search for "Claude" in the search box.

16. Install the extension by Anthropic.

17. Sign in with your Claude.ai account when prompted.

18. You will now see a Claude icon in your sidebar â€” clicking it opens a chat panel inside VS Code.

### **1.6  Tesseract OCR**

The screen-reading engine that lets your scripts read text off the Amazing Charts window.

| Download URL: https://github.com/UB-Mannheim/tesseract/wiki |
| :---- |

**Installation steps:**

19. Download the Windows installer from the UB Mannheim GitHub page linked above (look for the .exe file under the latest release).

20. Run the installer. When asked about installation path, note what folder it installs to â€” you will need this path later. Default is C:\\Program Files\\Tesseract-OCR\\

21. After installation, add Tesseract to your system PATH: search "environment variables" in the Start menu, click "Edit the system environment variables", click "Environment Variables", find "Path" under System Variables, click Edit, click New, and paste the Tesseract installation folder path.

22. Open a new Command Prompt and type: tesseract \--version

### **1.7  Tailscale**

Creates a secure private network between your phone and your work PC so you can access CareCompanion from anywhere. Free for personal use.

| Download URL: https://tailscale.com/download |
| :---- |

**Installation steps:**

23. Download and install Tailscale on your personal computer.

24. Create a free Tailscale account at tailscale.com.

25. Sign in to the Tailscale app.

26. You will also install Tailscale on your work PC and your phone later â€” all three devices need to be signed into the same Tailscale account for the tunnel to work.

### **1.8  AutoHotkey v2**

The tool that lets scripts control the mouse and keyboard â€” required for the Order Set Automator and text expansion macros.

| Download URL: https://www.autohotkey.com/ |
| :---- |

**Installation steps:**

27. Download AutoHotkey v2 from autohotkey.com (make sure to get v2, not v1 â€” the syntax is different).

28. Run the installer with default settings.

29. AutoHotkey scripts are plain text files with a .ahk extension. Double-clicking them runs the script.

### **1.9  Pushover App**

The push notification service that delivers de-identified inbox alerts to your phone. One-time $5 purchase for the app.

| Download URL: https://pushover.net/ |
| :---- |

**Installation steps:**

30. Create a free account at pushover.net.

31. Note your User Key from the dashboard â€” you will need this later.

32. Create a new Application in Pushover and note the API Token â€” this is what identifies CareCompanion as the sender.

33. Install the Pushover app on your phone ($5 one-time purchase) and sign in.

### **1.10  DB Browser for SQLite**

A visual tool to look inside your local database â€” useful for verifying data is being saved correctly and for troubleshooting.

| Download URL: https://sqlitebrowser.org/ |
| :---- |

**Installation steps:**

34. Download the Windows installer from sqlitebrowser.org.

35. Run with default settings. No configuration needed.

| âœ…  CHECKPOINT â€” Test Before Moving On: python \--version shows Python 3.11.x in Command Prompt node \--version shows a version number in Command Prompt git \--version shows a version number in Command Prompt VS Code opens and the Claude extension icon is visible in the sidebar tesseract \--version shows a version number in Command Prompt Tailscale is installed and you are signed into an account AutoHotkey v2 is installed You have a Pushover User Key and API Token saved somewhere safe DB Browser for SQLite opens without errors |
| :---- |

# **Section 2: Machine Information to Gather**

Before writing any code, you need to collect specific information about your work PC and your network. Some of this information gets baked into your configuration files. Gather all of it before development begins and keep it in a secure note.

| âš ï¸  Security Note: Never share any of the information collected in this section publicly or paste it into an AI chat. Store it in a password-protected notes app or a physical notebook kept securely. |
| :---- |

### **2.1  Work PC Local IP Address**

Why you need it: Your work PC's address on the clinic's local network â€” needed so room computers can reach CareCompanion.

**How to find it:**

| Open Command Prompt on your work PC and type: ipconfig Look for "IPv4 Address" under your active network adapter. It will look like 192.168.1.x or 10.0.0.x |
| :---- |

### **2.2  Work PC Computer Name**

Why you need it: Used for network identification and Tailscale routing.

**How to find it:**

| Right-click the Start button, click "System", and look for "Device name" at the top of the page. |
| :---- |

### **2.3  Work PC Windows Version & Build**

Why you need it: Some automation commands differ between Windows 10 versions.

**How to find it:**

| Press Windows+R, type "winver", press Enter. Note the version and OS Build numbers shown. |
| :---- |

### **2.4  Screen Resolution of Work PC**

Why you need it: Critical for the MRN screen reader â€” the capture region coordinates depend on your resolution.

**How to find it:**

| Right-click the desktop on your work PC and click "Display Settings". Note the resolution shown (e.g., 1920x1080). |
| :---- |

### **2.5  Amazing Charts Window Position**

Why you need it: The exact pixel coordinates of where the MRN appears in Amazing Charts.

**How to find it:**

| Open Amazing Charts on your work PC. Open any patient chart. The MRN will appear in the upper corner of the window. You will use the Calibration Tool (Feature 28a) to capture this precisely â€” for now, just note which corner of the screen it appears in and approximately how large the text is. |
| :---- |

### **2.6  NetPractice URL**

Why you need it: The exact web address you navigate to for NetPractice/WebPractice.

**How to find it:**

| Open the NetPractice browser tab and copy the full URL from the address bar. Note whether it uses https:// and the exact domain. |
| :---- |

### **2.7  Amazing Charts Version Number**

Why you need it: Some features may behave differently across AC versions.

**How to find it:**

| Inside Amazing Charts, click Help in the menu bar, then "About Amazing Charts". Note the version number. |
| :---- |

### **2.8  Tailscale IP of Work PC**

Why you need it: After installing Tailscale on the work PC, it gets assigned a private Tailscale IP (usually 100.x.x.x). This is what your phone uses to connect.

**How to find it:**

| Install Tailscale on the work PC (from tailscale.com), sign in with the same account as your personal computer, and note the 100.x.x.x address shown in the Tailscale app. |
| :---- |

### **2.9  Pushover User Key**

Why you need it: Your unique identifier in Pushover â€” goes in the CareCompanion config file.

**How to find it:**

| Log into pushover.net and copy the User Key from your dashboard. |
| :---- |

### **2.10  Pushover App API Token**

Why you need it: The token specific to the CareCompanion app you create in Pushover.

**How to find it:**

| In Pushover, go to "Your Applications" and copy the API Token for the CareCompanion application you created. |
| :---- |

| Information Item | Your Value (fill in by hand) |
| :---- | :---- |
| **Work PC Local IP** |  |
| **Work PC Computer Name** |  |
| **Windows Version & Build** |  |
| **Screen Resolution** |  |
| **Amazing Charts MRN Corner** |  |
| **NetPractice URL** |  |
| **Amazing Charts Version** |  |
| **Tailscale IP of Work PC** |  |
| **Pushover User Key** |  |
| **Pushover App API Token** |  |

# **Section 3: Setting Up VS Code and Claude**

This section gets your development environment ready. Think of VS Code as your workbench and Claude as your expert assistant sitting next to you. The goal of this setup is so that every time you need code written, you can describe what you want to Claude in plain English and it will write the code directly into your project files.

## **3.1  Creating Your Project Folder**

All of CareCompanion's code will live in one folder. Every file you create during this project goes inside this folder.

36. On your personal computer (not the work PC), open File Explorer.

37. Navigate to your Documents folder.

38. Create a new folder called: carecompanion

39. Open VS Code.

40. Click File \> Open Folder and select the carecompanion folder you just created.

41. VS Code will show the empty folder in the left sidebar. This is your project.

## **3.2  How to Use Claude Inside VS Code**

The Claude extension in VS Code works like a chat window that has direct access to your code files. This is different from using Claude in a web browser because Claude can read your existing code files and write directly into them.

| The three ways you will use Claude in this project: Ask Claude to write a new file from scratch. Describe what you want in plain English and Claude creates the file. Ask Claude to explain an error. When something breaks, paste the error message into Claude and ask what it means and how to fix it. Ask Claude to modify existing code. Open a file, then ask Claude to add a specific feature or change how something works. |
| :---- |

**How to open Claude in VS Code:**

42. Click the Claude icon in the left sidebar.

43. A chat panel opens on the right side of your screen.

44. To include a file in your question, type @ followed by the filename. Example: @app.py what does this file do?

45. To ask Claude to create or edit a file, describe what you want. Claude will show the code and offer to apply it directly.

## **3.3  Your Project Configuration File**

The first file you will create is a configuration file. This is where all your machine-specific information (IP addresses, API tokens, screen coordinates) lives, separate from the code itself. This way, when a colleague sets up CareCompanion, they just fill in their own config file without touching the code.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create a file called config.py in the root of my carecompanion project folder. This is a configuration file for a medical office workflow tool called CareCompanion. It should contain the following variables grouped into sections with comments:   SECTION 1 \- SERVER SETTINGS \- HOST: the IP address the Flask web server will listen on (default '0.0.0.0') \- PORT: the port number (default 5000\) \- SECRET\_KEY: a random string used for session security (generate a random 32-character string) \- DEBUG: boolean, default False   SECTION 2 \- MACHINE SETTINGS   \- SCREEN\_RESOLUTION: tuple for screen width and height, e.g. (1920, 1080\) \- MRN\_CAPTURE\_REGION: tuple of (x, y, width, height) for screen capture, default (0, 0, 300, 50\) \- AMAZING\_CHARTS\_PROCESS\_NAME: string, default 'AmazingCharts.exe' \- TESSERACT\_PATH: string path to tesseract executable   SECTION 3 \- NETPRACTICE SETTINGS \- NETPRACTICE\_URL: the base URL for NetPractice login \- SESSION\_COOKIE\_FILE: path to store the browser session, default 'data/np\_session.pkl'   SECTION 4 \- NOTIFICATION SETTINGS \- PUSHOVER\_USER\_KEY: empty string placeholder \- PUSHOVER\_API\_TOKEN: empty string placeholder \- NOTIFY\_QUIET\_HOURS\_START: integer hour (24h format), default 22 \- NOTIFY\_QUIET\_HOURS\_END: integer hour (24h format), default 7   SECTION 5 \- DATABASE SETTINGS \- DATABASE\_PATH: path to SQLite database file, default 'data/carecompanion.db' \- BACKUP\_PATH: path for database backups, default 'data/backups/'   SECTION 6 \- INBOX MONITOR SETTINGS \- INBOX\_CHECK\_INTERVAL\_MINUTES: integer, default 120 \- CRITICAL\_VALUE\_KEYWORDS: list of strings like \['critical', 'panic', 'STAT', 'HIGH', 'LOW'\]   Include a note at the top of the file warning the user never to commit this file to Git. |
| :---- |

## **3.4  Creating a .gitignore File**

A .gitignore file tells Git which files to never include in version control â€” specifically your config file (which contains sensitive tokens), your database file (which may contain patient-adjacent data), and session files.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create a .gitignore file in the root of my carecompanion project. Include rules to ignore: \- config.py (contains sensitive credentials) \- The entire data/ directory (contains database and session files) \- Python cache files (\_\_pycache\_\_, \*.pyc, \*.pyo) \- Virtual environment folders (venv/, .venv/) \- VS Code settings (.vscode/) \- Any .pkl files (session cookies) \- Any .log files \- The .env file if one exists   Add a comment explaining why config.py is excluded. |
| :---- |

## **3.5  Creating Your Python Virtual Environment**

A virtual environment is an isolated Python installation just for this project. It prevents your project's libraries from conflicting with other Python programs on your computer. Think of it as a clean workspace with only the tools this project needs.

**Steps to create it:**

46. In VS Code, open the Terminal by clicking Terminal \> New Terminal in the menu bar.

47. A terminal panel opens at the bottom. Type the following and press Enter:

| python \-m venv venv |
| :---- |

48. A folder called "venv" will appear in your project. This is your virtual environment.

49. Activate it by typing:

| .\\venv\\Scripts\\activate |
| :---- |

50. You should see "(venv)" appear at the start of your terminal line. This means the virtual environment is active.

51. Every time you open a new VS Code terminal, you need to re-run the activate command before installing or running anything.

## **3.6  Installing Python Libraries**

These are the Python add-on libraries that give CareCompanion its capabilities. Install them all now in your virtual environment so you don't have to stop and install things mid-build.

| pip install flask flask-login flask-sqlalchemy flask-bcrypt pip install playwright pyautogui pytesseract pillow pip install apscheduler requests pywin32 psutil pip install sqlalchemy pystray plyer playwright install chromium |
| :---- |

**What each group installs:**

* flask and related: The web server and user authentication system

* playwright: Browser automation for scraping NetPractice

* pyautogui: Mouse and keyboard automation for Amazing Charts

* pytesseract \+ pillow: OCR (screen reading) engine

* apscheduler: Runs scheduled tasks (inbox check every 2 hours, etc.)

* requests: Sends push notifications to Pushover

* pywin32 \+ psutil: Windows-specific tools for detecting which programs are running

* pystray: Creates the system tray icon for the background agent

| âœ…  CHECKPOINT â€” Test Before Moving On: The carecompanion folder is open in VS Code config.py exists in the project root and has all sections .gitignore exists and includes config.py The venv folder exists in the project Running "pip list" in the terminal (with venv active) shows flask, playwright, pyautogui, pytesseract, and others No errors appeared during pip install |
| :---- |

# **Section 4: Project Architecture Overview**

Before building anything, understanding how all the pieces fit together will save you significant confusion later. CareCompanion has three components that all talk to each other.

## **4.1  The Three Components**

| Component | What It Does |
| :---- | :---- |
| **Flask Web Server (app.py)** | Serves the browser interface that you see on your phone, the room computers, and your desktop. All the pages, buttons, and data displays come from here. |
| **Background Agent (agent.py)** | A silent script that runs in your system tray. It watches Amazing Charts for MRN changes, runs scheduled jobs, and triggers automations like inbox checks. |
| **SQLite Database (carecompanion.db)** | Your local data store. All time logs, notes, order sets, medication reference data, and settings are saved here. Never leaves your work PC. |

## **4.2  Folder Structure**

Your project should be organized as follows. Claude will help you create each file in the right location as you build each feature.

| carecompanion/ â”œâ”€â”€ app.py                  â† Main web server file â”œâ”€â”€ agent.py                â† Background desktop agent â”œâ”€â”€ config.py               â† Your machine settings (never committed to Git) â”œâ”€â”€ requirements.txt        â† List of all Python libraries â”œâ”€â”€ .gitignore â”‚ â”œâ”€â”€ models/                 â† Database table definitions â”‚   â”œâ”€â”€ \_\_init\_\_.py â”‚   â”œâ”€â”€ user.py             â† Provider accounts â”‚   â”œâ”€â”€ timelog.py          â† Visit timer records â”‚   â”œâ”€â”€ inbox.py            â† Inbox snapshots â”‚   â”œâ”€â”€ oncall.py           â† On-call notes â”‚   â”œâ”€â”€ orderset.py         â† Order set definitions â”‚   â”œâ”€â”€ medication.py       â† Medication reference â”‚   â”œâ”€â”€ labtrack.py         â† Lab value tracking â”‚   â”œâ”€â”€ caregap.py          â† Care gap records â”‚   â”œâ”€â”€ tickler.py          â† Follow-up tickler â”‚   â””â”€â”€ message.py          â† Delayed messages â”‚ â”œâ”€â”€ routes/                 â† Web page and API endpoints â”‚   â”œâ”€â”€ \_\_init\_\_.py â”‚   â”œâ”€â”€ auth.py             â† Login / logout / account management â”‚   â”œâ”€â”€ dashboard.py        â† Today view and home â”‚   â”œâ”€â”€ timer.py            â† Visit timer â”‚   â”œâ”€â”€ inbox.py            â† Inbox monitor â”‚   â”œâ”€â”€ oncall.py           â† On-call notes â”‚   â”œâ”€â”€ orders.py           â† Order set manager â”‚   â”œâ”€â”€ medref.py           â† Medication reference â”‚   â”œâ”€â”€ labtrack.py         â† Lab tracker â”‚   â”œâ”€â”€ caregap.py          â† Care gaps \+ billing â”‚   â”œâ”€â”€ metrics.py          â† Productivity dashboard â”‚   â””â”€â”€ tools.py            â† Utilities (calculator, generators) â”‚ â”œâ”€â”€ templates/              â† HTML pages â”‚   â”œâ”€â”€ base.html           â† Shared layout (nav, header, footer) â”‚   â”œâ”€â”€ login.html â”‚   â”œâ”€â”€ dashboard.html â”‚   â””â”€â”€ \[one file per route\] â”‚ â”œâ”€â”€ static/                 â† CSS, JavaScript, images â”‚   â”œâ”€â”€ css/ â”‚   â”‚   â””â”€â”€ main.css â”‚   â””â”€â”€ js/ â”‚       â””â”€â”€ main.js â”‚ â”œâ”€â”€ agent/                  â† Background agent modules â”‚   â”œâ”€â”€ mrn\_reader.py       â† OCR screen watcher â”‚   â”œâ”€â”€ inbox\_monitor.py    â† Inbox OCR and diff tracking â”‚   â”œâ”€â”€ scheduler.py        â† Scheduled job runner â”‚   â”œâ”€â”€ notifier.py         â† Pushover integration â”‚   â””â”€â”€ pyautogui\_runner.py â† Amazing Charts automation â”‚ â”œâ”€â”€ scrapers/               â† NetPractice browser automation â”‚   â””â”€â”€ netpractice.py      â† Schedule and portal scraper â”‚ â””â”€â”€ data/                   â† Created at runtime, excluded from Git     â”œâ”€â”€ carecompanion.db      â† SQLite database     â”œâ”€â”€ np\_session.pkl      â† NetPractice browser session     â””â”€â”€ backups/            â† Automatic nightly backups |
| :---- |

## **4.3  External APIs**

CareCompanion uses free government APIs (NIH, FDA, CMS, CDC) for clinical data enrichment. No PHI is ever sent to any external API â€” only clinical vocabulary terms (drug names, ICD-10 codes, LOINC codes). The full API specification, endpoint reference, caching architecture, and offline behavior are documented in **`Documents/API_Integration_Plan.md`** â€” the authoritative reference for all API integration.

### API Inventory

| Tier | API | Base URL | Auth | Primary Use | Key Features |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **1** | **RxNorm** | `https://rxnav.nlm.nih.gov/REST/` | None | Drug normalization, brandâ†”generic, properties, NDC codes | F6d, F10, F10c, F10d, F10e, F25, F26, F31 |
| **1** | **RxClass** | `https://rxnav.nlm.nih.gov/REST/rxclass/` | None | Therapeutic class mapping (drug â†’ class, class â†’ members) | F10 (condition-first search), NEW-D |
| **1** | **OpenFDA Labels** | `https://api.fda.gov/drug/label.json` | Optional key | Prescribing info: indications, dosing, warnings, interactions | F10, F10c, F10e, NEW-B, NEW-F |
| **1** | **OpenFDA FAERS** | `https://api.fda.gov/drug/event.json` | Optional key | Real-world adverse event frequency | F10 (opt-in per provider) |
| **1** | **OpenFDA Recalls** | `https://api.fda.gov/drug/enforcement.json` | Optional key | Active drug recall monitoring | F10e, F22, NEW-A, NEW-F |
| **1** | **ICD-10** | `https://clinicaltables.nlm.nih.gov/` | None | Diagnosis code lookup and validation | F17, F17b, F17c, Patient chart (**already implemented**) |
| **1** | **LOINC** | `https://fhir.loinc.org/CodeSystem/$lookup` | Free account | Lab test identification and reference ranges | F11, F11d, NEW-B |
| **1** | **UMLS** | `https://uts-ws.nlm.nih.gov/rest/` | âœ… Licensed 2026-03-19 | Master terminology crosswalk (SNOMEDâ†”ICD-10â†”RxNormâ†”LOINC) | F17c, F31, NEW-G |
| **1** | **SNOMED CT** | via UMLS atoms (sabs=SNOMEDCT_US) | âœ… Same UMLS key | Clinical concept codes, richer than ICD-10 for CDS | F17c, F31, NEW-G |
| **2** | **AHRQ HealthFinder** | `https://health.gov/myhealthfinder/api/v3/` | None | USPSTF preventive screening recommendations | F15, F15a, F22 |
| **2** | **CDC CVX** | via RxNorm + CDC schedules | None | Vaccine schedule recommendations | F15, F22 |
| **2** | **CMS HCPCS/CPT** | CMS.gov flat files | None | Procedure code reference data | F16, F14a |
| **2** | **NLM Conditions** | `https://clinicaltables.nlm.nih.gov/api/conditions/v3/search` | None | Clinical condition search for differentials | NEW-G |
| **3** | **PubMed** | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` | Free key | Guideline and systematic review search | NEW-C |
| **3** | **MedlinePlus** | `https://connect.medlineplus.gov/service` | None | Patient education content (English/Spanish) | NEW-E |
| **4** | **Open-Meteo** | `https://api.open-meteo.com/v1/forecast` | None | Weather for morning briefing | F22 |
| **Billing** | **CMS PFS** | `https://pfs.data.cms.gov/api` | None | Medicare RVU and payment rates | Phase 10B |
| **Billing** | **CMS Open Data** | `https://data.cms.gov/api/1/` | None | Actual Medicare utilization/payment data | Phase 10B |
| **CDS** | **VSAC** | `https://cts.nlm.nih.gov/fhir` | âœ… Same UMLS key | eCQM value sets, standardized condition definitions | Care Gaps, Billing |

### Caching Strategy

All API responses are cached in local SQLite tables following the existing `Icd10Cache` pattern. Cache-first architecture: local cache is always checked before any API call. On API failure, stale cached data is returned with a staleness indicator. TTLs range from permanent (RxNorm â€” drugs don't change names) to 24 hours (recalls â€” time-sensitive). See `API_Integration_Plan.md` Section 8 for the full cache table inventory and `get_cached_or_fetch()` pattern.

### No PHI in Outbound Requests

All outbound API calls contain ONLY clinical vocabulary (drug names, RXCUI codes, ICD-10 codes, LOINC codes, age/sex for HealthFinder). **Never** patient names, MRNs, DOBs, addresses, or insurance IDs. This is enforced by the `utils/api_client.py` helper which accepts only vocabulary parameters.

## **4.4  Multi-User Architecture**

Because you intend to share CareCompanion with colleagues, every piece of data in the database is tied to a user ID. When Dr. Smith logs in, she sees only her time logs, notes, and settings. When you log in, you see only yours. Shared resources like order sets and medication reference entries have a flag that marks them as either personal or shared-with-team.

The background agent on the work PC also knows which user is currently active based on who is logged into CareCompanion. This means time logs and MRN reads are attributed to the right provider even when multiple people use the same physical computer at different times during the day.

# **Section 5: Phase-by-Phase Build Guide**

Build in the order presented. Each phase produces a working, testable version of the platform that you can use even while later features are still being built. Do not skip phases â€” later features depend on earlier ones.

| PHASE 1: Foundation â€” Shell, Database & Authentication | \~10-14 hours |
| :---- | :---: |

Phase 1 produces a running web application with login/logout, user accounts, and all database tables defined. Nothing clinical yet â€” just the skeleton that everything else plugs into. At the end of Phase 1, you should be able to open a browser, navigate to your work PC's IP address, see a login screen, create accounts, and log in.

## **FEATURE 1: Project Skeleton & GUI Shell**

This is the web application's outer container â€” the navigation layout, login system, and responsive design that makes CareCompanion usable on phone, desktop, and room computers from a single codebase.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: I am building a web application called CareCompanion for a nurse practitioner's office. Build the following files for a Flask application:   1\. app.py \- Main Flask application file with:    \- Flask app initialization    \- SQLAlchemy database initialization    \- Flask-Login initialization for user sessions    \- Flask-Bcrypt for password hashing    \- Blueprint registration for routes (auth, dashboard, timer, inbox, oncall, orders, medref, labtrack, caregap, metrics, tools)    \- Configuration loading from config.py    \- Error handlers for 404 and 500    \- An app factory function create\_app()   2\. templates/base.html \- Base HTML template with:    \- Mobile-responsive layout using CSS Grid (no external CSS frameworks, pure CSS only)    \- A collapsible sidebar navigation with icons and labels for all 10 modules    \- A top header bar showing the logged-in provider's name, current time, and a notification bell    \- A main content area where child templates inject their content    \- Dark mode / light mode toggle button that saves preference to localStorage    \- Auto-lock overlay that appears after 5 minutes of inactivity â€” shows a PIN entry field    \- The app should feel clean and professional, suitable for a medical office    \- Responsive breakpoints so it works on a phone screen (375px) and a desktop (1920px)    \- Sidebar collapses to icons-only on smaller screens   3\. static/css/main.css \- Stylesheet with:    \- CSS custom properties for the colour palette (navy \#1B3A6B, teal \#0D7377, gold \#E8A020)    \- Dark mode variant using prefers-color-scheme and a data-theme attribute    \- Card component styles    \- Button styles (primary, secondary, danger, success)    \- Table styles    \- Form input styles    \- Badge / status indicator styles    \- Notification bell with unread count badge   4\. static/js/main.js \- JavaScript with:    \- Dark mode toggle logic with localStorage persistence    \- Auto-lock timer logic (5 minute inactivity timeout)    \- PIN entry to unlock (4-digit PIN set per user in settings)    \- Real-time clock update in the header    \- Notification bell fetch (polls /api/notifications every 60 seconds)    \- Mobile sidebar toggle logic |
| :---- |

### **Feature 1a: Multi-User Account System**

Every provider using CareCompanion gets their own account with a username, password (hashed and salted â€” never stored as plain text), display name, role (provider or MA), and personal preferences. Shared resources like order sets can be published by one user and seen by all.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add multi-user account functionality to my CareCompanion Flask app.   Create models/user.py with a User model containing: \- id (primary key) \- username (unique, required) \- password\_hash (never store plain text passwords) \- display\_name \- role (enum: 'provider', 'ma', 'admin') \- pin\_hash (4-digit PIN for auto-lock screen) \- preferences (JSON column for dark mode, notification settings, etc.) \- created\_at timestamp \- last\_login timestamp   Create routes/auth.py with: \- GET/POST /login \- login page with username/password form \- GET /logout \- logout and clear session \- GET/POST /register \- registration page (admin only after first user) \- GET/POST /settings/account \- change password, display name, PIN \- GET/POST /settings/notifications \- push notification preferences   Create templates/login.html, templates/register.html, templates/settings\_account.html   The first user to register automatically becomes admin. Subsequent registrations require an existing admin to be logged in. Passwords must be at least 8 characters. All routes except /login require authentication (use @login\_required decorator).   Include a role-based access function: providers see all modules, MAs see dashboard, orders, and care gaps only. |
| :---- |

### **Feature 1b: Role-Based Access**

Medical assistants who use the system should not have access to billing logs, productivity metrics, or on-call notes. This feature creates a permission layer so each role sees only what is appropriate.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add role-based access control to CareCompanion.   Create a decorator called @require\_role(role) that can be applied to any route. Create a dictionary called ROLE\_PERMISSIONS that maps each module to which roles can access it: \- 'provider': all modules \- 'ma': \['dashboard', 'orders', 'caregap', 'medref'\] \- 'admin': all modules plus user management   In base.html, update the sidebar so navigation items for restricted modules are hidden based on the logged-in user's role (pass role to template context).   Create a /admin/users route that lists all users, allows an admin to change roles, reset passwords, and deactivate accounts. Only accessible to admin role. |
| :---- |

### **Feature 1c: Dark Mode / Light Mode**

A simple toggle that remembers your preference per device. Dark mode is easier on the eyes during after-hours use.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: The dark mode toggle in main.js should: 1\. Check localStorage for 'theme' key on page load 2\. Apply data-theme="dark" to the \<html\> element if dark mode is saved 3\. On toggle click, switch the theme, save to localStorage, and POST to /api/settings/theme to save server-side per user as well   In main.css, add a complete dark mode colour scheme using \[data-theme="dark"\] selectors. Dark background: \#1a1a2e, card background: \#16213e, text: \#e0e0e0, accent: the same teal \#0D7377 |
| :---- |

### **Feature 1d: Notification Preferences Per User**

Each provider chooses when they want to be alerted. A surgeon colleague might want inbox alerts every 30 minutes; you might prefer every 2 hours on weekends only.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add a notification preferences page at /settings/notifications with the following per-user settings: \- Pushover enabled (boolean) \- Inbox check interval (dropdown: 30min, 1hr, 2hr, 4hr) \- Quiet hours start (time picker, default 10 PM) \- Quiet hours end (time picker, default 7 AM)   \- Weekend alerts enabled (boolean) \- Critical value alerts (always on, cannot be disabled) \- Which notification types to receive (checkboxes: new labs, new radiology, new messages, end-of-day reminder, morning briefing)   Save all preferences to the user's preferences JSON column. The scheduler reads these preferences per user before sending any notification. |
| :---- |

### **Feature 1e: Session Timeout & Auto-Lock**

Room computers are shared. If you walk out of the room and leave CareCompanion open, the screen should lock automatically to prevent anyone from seeing your patient data.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: The auto-lock system in main.js should: 1\. Track last user activity (any mouse move, keypress, or click resets the timer) 2\. After INACTIVITY\_TIMEOUT minutes (default 5, configurable per user), display a full-screen overlay 3\. The overlay shows only a PIN entry field (4 digits) and the CareCompanion logo 4\. Correct PIN dismisses the overlay 5\. After 3 incorrect PIN attempts, the overlay requires a full login 6\. The PIN is set in Account Settings, hashed and stored in the user record 7\. Add a POST /api/verify-pin endpoint that checks the PIN without exposing the hash   The overlay should be a fixed-position div with z-index 9999 and a blurred background, not a separate page. |
| :---- |

### **Feature 1f: Audit Trail for App Access**

A basic log of who accessed what and when. This is important once colleagues are on the platform.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create an audit log system: 1\. Add an AuditLog model to models/ with: id, user\_id, timestamp, action (string), module (string), ip\_address 2\. Create a log\_access(user\_id, action, module) helper function 3\. Apply it to every route using a Flask after\_request hook 4\. Create a /admin/audit-log page (admin only) showing the last 500 entries in a sortable table 5\. Allow filtering by user, date range, and module |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: Navigating to http://localhost:5000 shows the CareCompanion login page You can create a new account and log in The sidebar navigation is visible and all module links are present Dark mode toggle works and persists after page refresh Logging out redirects to the login page Trying to access any page while logged out redirects to login An MA account cannot access the Metrics or Billing pages Auto-lock overlay appears after 5 minutes of inactivity Correct PIN dismisses the overlay The admin/users page shows registered accounts |
| :---- |

## **FEATURE 2: Local Database Schema**

All 11 database tables are created now, even though most will be empty until later features populate them. Creating the schema upfront prevents the painful process of restructuring the database mid-build.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the complete SQLAlchemy database schema for CareCompanion. Create individual model files in the models/ directory.   models/timelog.py \- Time tracking records: \- id, user\_id (FK to User), mrn (string, the patient identifier), session\_start, session\_end, duration\_seconds \- visit\_type (string), is\_complex (boolean), face\_to\_face\_start, face\_to\_face\_end, face\_to\_face\_seconds \- billed\_level (string, e.g. '99213'), billing\_notes (text), created\_at   models/inbox.py \- Inbox monitoring: \- InboxSnapshot: id, user\_id, captured\_at, labs\_count, radiology\_count, messages\_count, refills\_count, other\_count \- InboxItem: id, user\_id, item\_hash (unique identifier per item), item\_type (lab/rad/message/refill), first\_seen\_at, last\_seen\_at, is\_resolved (bool), is\_held (bool), held\_reason, priority (normal/critical)   models/oncall.py \- On-call notes: \- id, user\_id, patient\_identifier (not full name \- provider's own shorthand), call\_time, chief\_complaint \- recommendation (text), callback\_promised (bool), callback\_by, callback\_completed (bool) \- documentation\_status (enum: pending/entered/not\_needed), note\_content (text), created\_at   models/orderset.py \- Saved order sets: \- OrderSet: id, user\_id, name, visit\_type, is\_shared (bool), created\_at, updated\_at, version \- OrderItem: id, orderset\_id, order\_name, order\_tab (which tab in Amazing Charts), order\_label (exact text as shown in AC), is\_default (bool), sort\_order   models/medication.py \- Medication reference: \- id, user\_id (null for shared entries), condition, drug\_name, drug\_class, line (first/second/third) \- dosing\_notes (text), special\_populations (text), contraindications (text), monitoring (text) \- personal\_notes (text), is\_shared (bool), guideline\_review\_flag (bool), created\_at, updated\_at   models/labtrack.py \- Per-patient lab tracking: \- LabTrack: id, user\_id, mrn, lab\_name, interval\_days, alert\_low, alert\_high, last\_checked, notes \- LabResult: id, labtrack\_id, result\_value (string), result\_date, is\_critical (bool), trend\_direction (up/down/stable)   models/caregap.py \- Preventive care tracking: \- id, user\_id, mrn, gap\_type (mammogram/colonoscopy/etc), due\_date, completed\_date \- is\_addressed (bool), documentation\_snippet (text), billing\_code\_suggested, created\_at   models/tickler.py \- Follow-up reminders: \- id, user\_id, assigned\_to\_user\_id (for MA delegation), mrn, patient\_display (non-PHI label) \- due\_date, priority (routine/important/urgent), notes (text), is\_completed, is\_recurring \- recurrence\_interval\_days, completed\_at, created\_at   models/message.py \- Delayed message queue: \- id, user\_id, recipient\_identifier, message\_content (text), scheduled\_send\_at \- status (pending/sent/failed/cancelled), sent\_at, delivery\_confirmed (bool), created\_at   models/reformatter.py \- Note reformatter records: \- id, user\_id, source\_note\_date, source\_provider, visit\_type, reformat\_status (pending/complete/needs\_review) \- flagged\_items (JSON \- list of items that could not be templated), created\_at, completed\_at   Initialize all models in models/\_\_init\_\_.py and call db.create\_all() on app startup. |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: The app starts without errors after adding the models DB Browser for SQLite opens data/carecompanion.db and shows all 15+ tables Each table has the correct columns visible in DB Browser No SQLAlchemy errors in the terminal when the app starts |
| :---- |

## **FEATURE 3: Desktop Background Agent**

The agent is a separate Python script that runs silently in your Windows system tray. It is the bridge between the web interface and the Windows desktop â€” it watches Amazing Charts, runs scheduled jobs, and triggers automations. The web server (app.py) and the agent (agent.py) communicate by reading and writing to the shared SQLite database.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create agent.py in the root of the carecompanion project. This is a Windows system tray application that runs independently of the Flask web server.   Requirements: 1\. System tray icon using pystray with a simple icon (create a basic icon using Pillow \- a blue circle with "NP" text) 2\. Right-click tray menu with options: Open CareCompanion (opens browser to localhost:5000), Pause Monitoring, Resume Monitoring, Check Inbox Now, View Status, Quit 3\. On startup, read config.py for all settings 4\. Maintain a status dictionary with: is\_running, last\_mrn\_check, last\_inbox\_check, active\_mrn, active\_user\_id, errors list 5\. Expose status via a simple HTTP endpoint at port 5001 (separate from Flask app on 5000\) that returns JSON â€” the Flask app polls this to show agent health in the UI 6\. A heartbeat that writes current timestamp to the database every 30 seconds so the web UI can detect if the agent has crashed 7\. Clean shutdown handling that saves any in-progress time log entries before quitting   Create agent/scheduler.py: \- Uses APScheduler with a BackgroundScheduler \- Jobs: inbox\_check (interval from user preferences), mrn\_poll (every 3 seconds), morning\_briefing (daily at configurable time), end\_of\_day\_check (daily at configurable time), nightly\_backup (daily at 2 AM) \- Each job wrapped in try/except that logs failures to the database rather than crashing the agent   Create a Windows Task Scheduler XML file (agent\_startup.xml) that starts agent.py at Windows login, runs as the current user, and restarts automatically if it crashes. |
| :---- |

### **Feature 3a: Agent Health Monitor**

A status widget visible in the CareCompanion web UI showing whether the background agent is currently running, when it last checked in, and a Restart button.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add an agent health indicator to the CareCompanion base template.   In base.html, add a small status indicator in the header (next to the notification bell) that shows: \- Green dot: agent is running (last heartbeat within 60 seconds) \- Yellow dot: agent may be stale (last heartbeat 60-300 seconds ago)   \- Red dot with bell: agent is not responding (last heartbeat \> 5 minutes ago)   Create GET /api/agent-status that queries the database for the last heartbeat timestamp and returns JSON with {status, last\_heartbeat, active\_mrn, jobs\_running}.   Add a Restart Agent button (visible to admin users) that runs a subprocess to restart agent.py.   In the agent health detail view (/admin/agent), show: uptime, jobs scheduled and last run times, any recent errors from the error log. |
| :---- |

### **Feature 3b: Per-Provider Agent Profiles**

When multiple providers use the same computer at different times, the agent correctly attributes data to whoever is currently logged into CareCompanion.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add active user tracking to the agent.   In app.py, add a POST /api/agent/set-active-user endpoint (called on login) that writes the current user\_id to a shared file (data/active\_user.json). On logout, write null to the same file.   In agent.py, poll data/active\_user.json every 10 seconds to know who is currently active. All database writes from the agent (time logs, inbox snapshots) use this active user\_id. If active\_user.json is null or missing, the agent pauses MRN tracking but continues scheduled jobs like inbox monitoring (which uses each provider's own credentials). |
| :---- |

### **Feature 3c: Crash Recovery & Resume**

If the agent crashes, it recovers gracefully and preserves any in-progress data.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add crash recovery to agent.py:   1\. On startup, check the database for any time log entries with a session\_start but no session\_end from the last 24 hours 2\. For each incomplete entry, create a popup notification asking the provider to confirm the session end time 3\. If they don't respond within 10 minutes, mark the entry with a 'duration\_estimate' flag and close it using the last heartbeat time as the approximate end 4\. Write a startup log entry to the database including the PID, startup time, and whether a crash recovery was performed 5\. Add a try/except wrapper around the main agent loop that catches any exception, logs it with full traceback to the database, attempts to restart the failed component, and sends a push notification to the admin user |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: Running "python agent.py" shows a system tray icon Right-clicking the tray icon shows the menu options The CareCompanion web UI shows a green agent status dot Killing and restarting agent.py triggers crash recovery notification The /admin/agent page shows uptime and job schedule Logging in and out of CareCompanion updates the active\_user.json file |
| :---- |

| PHASE 2: Data Layer â€” NetPractice Scraper & Inbox Monitor | \~12-16 hours |
| :---- | :---: |

## **FEATURE 4: NetPractice Schedule Scraper**

This is the data source that feeds your Today View, Pre-Visit Note Prep, and Care Gap tracker. A Playwright-powered script logs into NetPractice and retrieves tomorrow's patient schedule, storing it locally for use by other modules.

| âš ï¸  Google Authentication: The first time you run the scraper, it will open a browser window and ask you to log in manually. After you complete the Google authentication, the session is saved locally. You will need to repeat this when Google asks for re-authentication (typically every 2-4 weeks). |
| :---- |

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create scrapers/netpractice.py \- A Playwright-based scraper for NetPractice/WebPractice scheduling software.   The scraper needs to handle: 1\. Session management:    \- Store browser session (cookies, local storage) to data/np\_session.pkl after login    \- On each run, load the saved session first    \- Detect if redirected to Google login page and handle gracefully    \- If auth is required, set a flag in the database (needs\_reauth=True) and send a Pushover notification, then wait    \- Do NOT try to automate the Google login itself   2\. Schedule scraping function get\_schedule(target\_date):    \- Navigate to the schedule page for target\_date    \- Find all appointment slots with: patient name, DOB (if visible), appointment time, visit type, appointment duration, provider name    \- Handle pagination if the schedule spans multiple views    \- Return a list of dicts with this data    \- Save results to a Schedule table in the database   3\. Session health check is\_session\_valid():    \- Load saved session    \- Navigate to a known NetPractice page    \- Return True if the page loads correctly, False if redirected to login   4\. A scrape\_tomorrow() function that is called by the scheduler   Include detailed logging so you can see exactly what the scraper is doing when troubleshooting.   NOTE: I will provide you with screenshots of the NetPractice interface once the basic framework is running so you can update the CSS selectors to match the actual page layout. |
| :---- |

### **Feature 4a: New Patient Flag**

Automatically identifies new patients in the schedule so you can mentally prepare for longer encounters.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: In the schedule scraper and Today View: 1\. Add a is\_new\_patient field to the Schedule model (boolean) 2\. In the scraper, detect new patient appointments (NetPractice likely uses a different visit type label or a visual indicator \- flag any visit typed as "New Patient" or "NP" or "First Visit") 3\. In the Today View template, show a gold "NEW" badge next to new patient entries 4\. Add a count of new patients to the morning briefing |
| :---- |

### **Feature 4b: Visit Duration Estimator**

After a few weeks of data, predicts how long today's schedule will actually take based on your historical chart times.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add a duration estimator to the Today View: 1\. Create a function estimate\_schedule\_duration(user\_id, schedule\_entries) that:    \- Queries time logs for average duration by visit\_type for this user    \- Returns total estimated time and a comparison to booked time 2\. Display this in the Today View as: "Booked: 6.5 hrs | Your typical pace: 8.2 hrs | Likely end time: 5:45 PM" 3\. Only show this estimate once 20+ time log entries exist (otherwise insufficient data) |
| :---- |

### **Feature 4c: Double-Booking & Gap Detector**

Flags scheduling anomalies in the morning briefing before you arrive.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add schedule analysis to the scraper: 1\. After pulling the schedule, analyze for:    \- Back-to-back complex visits (new patient followed immediately by new patient)    \- Appointment shorter than your average for that visit type    \- Gaps longer than 30 minutes mid-day    \- Last appointment of day is a new patient (often runs long) 2\. Attach warning flags to schedule entries where anomalies are found 3\. Include anomaly summary in the morning briefing notification |
| :---- |

### **Feature 4e: Re-Authentication Watchdog**

Sends a push notification immediately when NetPractice needs re-authentication instead of silently failing.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add re-auth monitoring: 1\. The scraper's is\_session\_valid() check runs before every scrape 2\. If session is invalid, immediately:    a. Set user preference needs\_reauth=True in database    b. Send Pushover notification: "NetPractice needs re-authentication. Please remote in via Splashtop and log in."    c. Show a banner in CareCompanion's Today View     d. Skip the scrape attempt (don't try to run without auth) 3\. After successful re-auth, clear the flag and send a confirmation notification |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: Running the scraper manually prompts for login on first run After login, the session file exists at data/np\_session.pkl Running the scraper a second time does NOT prompt for login Tomorrow's schedule appears in the database (visible in DB Browser) The Today View shows tomorrow's schedule with visit types New patient appointments show the gold NEW badge Deleting np\_session.pkl and running again triggers the re-auth notification |
| :---- |

### **Feature 4f: Direct Patient Search (Off-Schedule)**

The CareCompanion dashboard must support searching for any patient by name or MRN, not just patients on today's schedule. This is needed for:
- Reviewing labs for patients not seen today
- Pulling a chart during an on-call situation
- Accessing records for clinical summary export on demand

Implementation: A search field in the dashboard header (persistent across all views) that queries the local database for previously-seen patients, and as a secondary path, triggers AC patient search via PyAutoGUI if the patient has not been imported yet.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add a persistent patient search field to the dashboard header: 1\. A search input visible on all pages (in base.html header bar) 2\. As the user types, query the local database for patients matching name or MRN 3\. Display results in a dropdown below the search field 4\. Clicking a result opens /patient/\<mrn\> (Patient Chart View, Feature 10e) 5\. If no local results, show "Search in Amazing Charts" button that: a. Focuses the AC window via win32gui b. Clicks the Patient List ID column search field c. Types the search term via PyAutoGUI d. Returns focus to the browser after 3 seconds 6\. Scope all queries to current\_user.id |
| :---- |

## **FEATURE 6: MRN Screen Reader**

The MRN reader detects the current patient's MRN from the Amazing Charts window title bar using `win32gui.GetWindowText()` and the regex `ID:\s*(\d+)`. Every time the MRN changes, it closes the previous time entry and starts a new one. This is what makes the Visit Timer work automatically without you pressing any buttons.

**Three-tier detection approach:**
1. **Primary** â€” `win32gui.GetWindowText()` on the foreground window, regex `ID:\s*(\d+)` to extract MRN
2. **Fallback** â€” OCR on the pink patient context bar in the inbox preview panel
3. **Last resort** â€” Tesseract region OCR only if both above methods return None

The reader also extracts DOB from the title bar using regex `DOB:\s*([\d/]+)`.

## **FEATURE 5: Inbox Monitor with Diff Tracking**

The inbox monitor watches your Amazing Charts inbox on a schedule, compares each snapshot to the previous one, identifies what is new, and sends de-identified push notifications. The diff tracking means held items (like your intentional no-show notes) don't trigger false alerts.

The inbox is always visible on the AC home screen â€” no keyboard shortcut or navigation required. The monitor cycles through the filter dropdown (7 options) and OCR-reads the `From | Subject | Received` table for each filter.

Confirmed filter dropdown labels (exact strings):
```
Show Everything, Show Charts, Show Charts to Co-Sign,
Show Imports to Sign-Off, Show Labs to Sign-Off,
Show Orders, Show Patient Messages
```

Subject prefixes identify item type: `LAB:` for labs, `CHART:` for forwarded charts, `VIIS` for immunization imports.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create agent/inbox\_reader.py â€” The Amazing Charts inbox monitoring system using PyAutoGUI and OCR.   The inbox is always visible on the AC home screen. It requires the AC main window (not a patient chart) to be the foreground window.   The monitor works in these steps: 1\. Focus the AC main window via win32gui (verify it is the home screen, not a chart window) 2\. Click the filter dropdown (second control in the inbox header row) 3\. For each filter in INBOX\_FILTER\_OPTIONS:    a. Click the filter option by exact text match    b. Wait 0.5 seconds for the table to refresh    c. Take a screenshot of the inbox table region    d. OCR the screenshot with Tesseract (psm=6)    e. Parse rows: split on newlines, extract From / Subject / Received columns    f. Generate item hash: sha256(item\_type + subject + received)[:16] 4\. Compare all hashes against the last InboxSnapshot in the database for this user 5\. Categorize: new\_items, resolved\_items, held\_items 6\. Write new InboxSnapshot to the database 7\. Call the notifier if there are new items   INBOX\_FILTER\_OPTIONS (exact label strings): \['Show Charts', 'Show Charts to Co-Sign', 'Show Imports to Sign-Off', 'Show Labs to Sign-Off', 'Show Orders', 'Show Patient Messages'\]   Note: "Show Everything" is read last to get total count.   Critical value detection: \- Scan OCR text for keywords: 'CRITICAL', 'PANIC VALUE', 'STAT', strings like 'H\*' or 'L\*' indicating out-of-range \- Any critical detection triggers an immediate high-priority Pushover notification regardless of quiet hours   The notification payload (NEVER include any patient names, MRNs, or identifiers): {   "new\_labs": 2,   "new\_radiology": 1,    "new\_messages": 3,   "critical\_flags": 1,   "held\_items": 4,   "checked\_at": "Sunday 11:02 AM" }   All coordinates for the filter dropdown and inbox table region come from config.py. Include TODO comments for each coordinate that needs calibration. Include detailed logging so each step is visible when troubleshooting. |
| :---- |

### **Feature 5b: Critical Value Visual Flag**

Critical lab results get an immediate separate high-priority notification.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Enhance the inbox monitor with tiered notification logic: 1\. Critical detection: Any item whose OCR text contains critical value keywords triggers an IMMEDIATE Pushover notification with sound 'siren', priority 1 (bypasses quiet hours) 2\. Normal new items: Batched into the regular scheduled notification 3\. The critical notification message: "ðŸš¨ CRITICAL VALUE in inbox \- Log in immediately to review" 4\. Log each critical detection with timestamp in the database for the audit trail |
| :---- |

### **Feature 5c: Held Item Registry**

A UI for formally marking inbox items as intentionally held so they don't inflate your unreviewed count.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Held Item Registry in the Inbox Monitor module: 1\. Add a /inbox/held page that lists all items with is\_held=True for the current user 2\. Form to mark new items as held with: item description (non-PHI), reason (dropdown: awaiting callback, no-show follow-up, pending outside records, other), expected resolution date 3\. Held items excluded from the "unreviewed" count in notifications 4\. Held items shown in their own section in the push notification (count only) 5\. A "resolve" button that marks the item as resolved and removes from held registry |
| :---- |

### **Feature 5d: Inbox Age Tracker**

Flags items sitting in your inbox beyond your defined review threshold.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add inbox age tracking: 1\. Every InboxItem has a first\_seen\_at timestamp 2\. Add user preference: inbox\_warning\_hours (default 48\) and inbox\_critical\_hours (default 72\) 3\. In the Inbox module UI, show items older than warning threshold with a yellow clock icon 4\. Items older than critical threshold show a red clock icon 5\. Include overdue item count in the morning briefing 6\. Add an inbox\_overdue\_items count to the push notification when any items exceed the critical threshold |
| :---- |

### **Feature 5f: Inbox Review Timestamp Log**

Documents your review turnaround time for liability defense.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add review timestamping: 1\. Every time the inbox monitor detects the inbox\_count has decreased (items resolved), log:    \- user\_id, timestamp, items\_resolved\_count, time\_since\_first\_seen 2\. Create a /inbox/audit-log page showing this history in a table 3\. Export button generates a PDF report of inbox review activity for a date range 4\. This log, combined with the time log, documents your clinical review timeline |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: Amazing Charts is open and the inbox monitor runs without crashing A new InboxSnapshot record appears in the database after running the monitor Running the monitor twice with no inbox changes shows zero new items Adding a test item and re-running shows one new item A Pushover notification arrives on your phone with item counts only (no names) The Held Item Registry page loads and allows marking items Held items do not appear in the new-item count in subsequent notifications |
| :---- |



| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create agent/ac\_window.py â€” Window management and MRN detection for Amazing Charts using pywin32.   The MRN reader runs in a loop every 3 seconds: 1\. Get the foreground window title using win32gui.GetWindowText(win32gui.GetForegroundWindow()) 2\. Check if window title starts with "Amazing Charts" 3\. Extract MRN using regex: r'ID:\\s\*(\\d+)' on the title text 4\. Extract DOB using regex: r'DOB:\\s\*(\[\\d/\]+)' on the title text 5\. If MRN extraction from title fails, fallback: OCR the pink patient context bar in the inbox preview panel (coordinates from config.py) 6\. If both title and OCR fail, fallback to Tesseract region OCR on MRN\_CAPTURE\_REGION 7\. Compare to the last known MRN:    \- If different (new patient): close out the previous time log entry, start a new one    \- If same: update the last\_seen timestamp on the current time log entry    \- If blank/unreadable: pause the timer (chart may be closed) 8\. Write all time log updates to the SQLite database   Idle detection: \- Use pywin32's GetLastInputInfo() to get milliseconds since last input \- If Amazing Charts is the foreground window but no activity for 5 minutes, pause the timer \- Resume timer when activity resumes   Include a calibration mode that can be triggered from the agent's tray menu: \- Confirms that win32gui is correctly identifying the AC chart window \- Shows the current title bar text and extracted MRN \- Verifies the fallback OCR region if title extraction fails |
| :---- |

### **Feature 6a: Chart Open Duration Warning**

Alerts you if a chart has been open suspiciously long without activity.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add a duration warning to the MRN reader: 1\. Add config value MAX\_CHART\_OPEN\_MINUTES (default 20\) 2\. If the same MRN has been active for longer than this threshold without keyboard/mouse activity:    a. Show a Windows desktop notification: "Chart \[MRN\] has been open 20 minutes. Still working?"    b. Two buttons: "Yes, still working" (resets timer) and "No, close session" (ends time log entry) 3\. Do not fire this warning more than once per hour for the same MRN |
| :---- |

### **Feature 6b: Idle Detection**

Pauses the chart timer during inactivity so your logged time accurately reflects active work.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add idle detection to mrn\_reader.py: 1\. Use pywin32's GetLastInputInfo() to get milliseconds since last input 2\. If idle for more than IDLE\_THRESHOLD\_SECONDS (default 300, configurable), set a flag idle\_since 3\. Pause the active time log entry (set a paused\_at timestamp) 4\. When activity resumes, resume the time log entry 5\. Store total\_idle\_seconds per time log entry separately from total duration 6\. In the Billing Audit Log, show both gross time (wall clock) and net active time (gross minus idle) |
| :---- |

### **Feature 6c: Manual MRN Entry Override**

For times when OCR fails, lets you manually log a session to preserve billing record integrity.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add manual MRN entry to the Timer module: 1\. In the Timer page, add a "Manual Entry" button 2\. A form appears with: MRN field, session start (datetime picker), session end (datetime picker), visit type dropdown, notes 3\. Submitting creates a TimLog entry with a manual\_entry=True flag 4\. Manual entries show a pencil icon in the audit log to distinguish them from automatically captured sessions 5\. Manual entries can be edited or deleted (auto-captured entries cannot be deleted, only annotated) |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: Opening a patient chart in Amazing Charts creates a new TimLog entry in the database Switching to a different patient chart creates a new entry and closes the previous one Closing Amazing Charts closes the active time log entry The calibration mode confirms win32gui is correctly identifying the AC chart window and extracting MRN from the title bar The fallback OCR region reads correctly when title bar extraction fails Leaving the computer idle for 5 minutes pauses the timer The Timer page in CareCompanion shows the current active MRN and session duration |
| :---- |

### **Feature 6d: Clinical Summary Exporter & Parser**

A new agent module (`agent/clinical_summary_parser.py`) that automates exporting and parsing the Amazing Charts Clinical Summary XML. This provides structured patient data (medications, diagnoses, allergies, vitals, labs, immunizations, demographics) without OCR â€” directly from the XML export.

**Critical constraint â€” two-phase workflow:** The Clinical Summary export is a two-phase batch process. **Phase 1 (Chart Opening):** For every patient on the schedule, search by patient ID in the blue Patient List field (under "Schedule", "Messages", "Reports", "Secure" buttons), verify the name, double-click to open the chart, select the **Visit Template** radio button, click **Select Template â†’ Procedure Visit â†’ Companion**, clear any popups, then press **Ctrl+S** to save/close (sends the note to the inbox). Repeat for ALL patients. **Phase 2 (XML Export):** Only after all charts are in the inbox â€” ensure the AC home screen is active (no chart windows open), find each patient's most recent chart in the inbox (verify by time column, name, and MRN), single-click to select, then navigate `Patient menu (Alt+P) > Export Clinical Summary`, select **"Full Patient Record"** from the encounter dropdown (never use a single encounter), verify all checkboxes and destination folder, click Export, dismiss the success dialog. Repeat for ALL patients.

**Export file naming:** `ClinicalSummary_PatientId_[MRN]_[YYYYMMDD]_[HHMMSS].xml`
**Format:** HL7 CDA (C-CDA R2.1), namespace `{'cda': 'urn:hl7-org:v3'}`
**Retention:** Auto-delete after 183 days (configurable), audit log every parse

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create agent/clinical\_summary\_parser.py for CareCompanion.   This module exports and parses the Amazing Charts Clinical Summary XML.   Function 1 â€” open\_patient\_chart(mrn: str, patient\_name: str) -> bool: \- Search for the patient by ID in the Patient List panel (blue field under Schedule/Messages/Reports/Secure buttons) \- Verify the first and last name match patient\_name \- Double-click the verified name to open a new chart \- In the chart window, select the "Visit Template" radio button \- Click the "Select Template" dropdown â†’ Procedure Visit â†’ Companion \- Clear any popup boxes (click OK or X) \- Press Ctrl+S to save and close the chart (sends note to inbox) \- Return True on success, False on failure   Function 2 â€” export\_clinical\_summary(mrn: str) -> str | None: \- Verify AC is on the home screen (no chart windows open) \- Verify no window title contains "ID:" (which indicates a chart is open) \- Find the patient's most recent chart in the inbox (verify by time column, name, and MRN) \- Single-click the chart row to select it \- Open Patient menu (Alt+P) \- Click "Export Clinical Summary" (near bottom of menu) \- In the dialog, select **\"Full Patient Record\"** from the encounter dropdown (never use a single encounter), verify all checkboxes are checked, verify the destination folder \- Click the Export button \- Dismiss the "Export Succeeded" dialog (press Enter) \- Watch data/clinical\_summaries/ for a new file matching ClinicalSummary\_PatientId\_\[MRN\]\_\*.xml \- Return the full file path or None on timeout (15 second timeout)   IMPORTANT: open\_patient\_chart() must be called for ALL patients on the schedule BEFORE calling export\_clinical\_summary() for any patient. This is a two-phase batch workflow.   Function 3 â€” parse\_clinical\_summary(xml\_path: str) -> dict: \- Parse HL7 CDA XML using xml.etree.ElementTree \- Namespace: {'cda': 'urn:hl7-org:v3'} \- Extract all sections listed below and return as a structured dict \- Sections: patient\_demographics, medications (active and inactive), allergies, diagnoses (active problems), vitals (most recent), lab\_results (all with dates), immunizations, social\_history, encounter\_reason, instructions, goals, health\_concerns \- Any section with nullFlavor="NI" returns an empty list, not an error \- Log the parse to AuditLog table (user\_id, mrn\_hash, timestamp, sections\_found) \- Never log patient names â€” use sha256(mrn)\[:12\] as the identifier   Function 4 â€” store\_parsed\_summary(user\_id: int, mrn: str, parsed: dict): \- Write medications to the Medication model (upsert by drug\_name + mrn) \- Write diagnoses to CareGap-adjacent storage \- Write lab results to LabResult model \- Write vitals to a new PatientVitals table \- Set a last\_xml\_parsed timestamp on the patient record   Function 5 â€” schedule\_deletion(xml\_path: str, days: int = 183): \- Register the file for deletion after \[days\] days via APScheduler \- Log scheduled deletion to AuditLog   Include a file watcher using Python's watchdog library as an alternative to polling, so the parser triggers automatically when AC writes the file. |
| :---- |

| âš ï¸  RxNorm Integration: The CDA XML embeds RxNorm CUI codes in medication strings (e.g., "Lipitor 20 mg tablet [RxNorm: 617310]"). The parser's `_parse_code_from_text()` function already extracts these codes. The `rxnorm_cui` value must be saved to the `PatientMedication.rxnorm_cui` column (not discarded). After parsing, the enrichment function `_enrich_rxnorm(rxcui)` in patient.py resolves each RXCUI into clean brand name, generic name, dose, and form via the NIH RxNorm API â€” cached locally in the `RxNormCache` table so each drug is only looked up once. If no RXCUI is present in the XML, the fallback uses `findRxcuiByString` (approximate string match) against the raw drug name. |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: Exporting a Clinical Summary from AC creates a file in data/clinical\_summaries/ The parser extracts medications, diagnoses, allergies, and vitals from the XML Parsed data appears in the CareCompanion database The file watcher detects new XML files automatically The AuditLog shows a record for each parse operation The auto-deletion job removes files older than 183 days Medications in the database have `rxnorm_cui` populated from the XML RxNorm-enriched medications show clean brand/generic names in the patient chart |
| :---- |

| PHASE 3: High-Value Daily Tools | \~20-26 hours |
| :---- | :---: |

## **FEATURE 7: On-Call Note Keeper**

A mobile-first note-taking interface accessible from your phone via Tailscale. You type or dictate notes during after-hours calls; they sync automatically to the desktop where they are ready to paste into Amazing Charts Monday morning.

| Tailscale Setup: Before testing this feature on your phone, install Tailscale on your work PC, sign in with the same account as your personal computer, and note the 100.x.x.x IP address. On your phone, install the Tailscale app and sign in. Then access CareCompanion at http://\[tailscale-ip\]:5000 |
| :---- |

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the On-Call Note Keeper module.   routes/oncall.py with routes: \- GET /oncall \- List all on-call notes, most recent first, grouped by date \- GET /oncall/new \- New note form (mobile-optimized) \- POST /oncall/new \- Save new note \- GET /oncall/\<id\> \- View single note \- POST /oncall/\<id\>/edit \- Edit existing note \- POST /oncall/\<id\>/status \- Update documentation status (pending/entered/not\_needed) \- POST /oncall/\<id\>/complete-callback \- Mark callback as completed \- GET /oncall/export/\<id\> \- Generate formatted note text for Amazing Charts paste-in   templates/oncall\_list.html \- Note list optimized for both mobile and desktop: \- Each note card shows: call time, chief complaint (truncated), documentation status badge, callback status \- Color coding: red=pending documentation, yellow=callback overdue, green=complete \- "New Call" button prominently placed   templates/oncall\_new.html \- New note form, MUST work perfectly on a phone: \- Large touch targets (minimum 44px height) \- Chief complaint: text input with voice input button (uses browser's Web Speech API for dictation) \- Call time: datetime picker (defaults to current time) \- Patient identifier: text input (your own shorthand \- not required to be the full name) \- Recommendation: large text area with voice input \- Callback promised: yes/no toggle \- If callback promised: callback by field (time picker) \- Documentation status: radio buttons \- Save button at bottom, easy to reach on phone   templates/oncall\_export.html \- Formatted text view for Amazing Charts: \- Shows the note formatted as: "After-hours call \[DATE\] \[TIME\]: Patient \[identifier\] called regarding \[complaint\]. Recommendation: \[rec\]. \[Callback instructions if applicable\]." \- One-click copy button (uses clipboard API) \- "Mark as Entered" button that updates status |
| :---- |

### **Feature 7a: Voice-to-Text Input**

Dictate call notes without typing â€” critical for calls taken while multitasking.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add voice input to the on-call note form: 1\. Add a microphone button next to each text area in oncall\_new.html 2\. Use the browser's Web Speech API (window.SpeechRecognition) for voice input 3\. Show visual feedback while recording (pulsing red dot) 4\. Transcribed text appends to (does not replace) existing field content 5\. Show a "listening..." indicator while active 6\. Graceful degradation: if the browser doesn't support SpeechRecognition (some mobile browsers), show a tooltip explaining the limitation |
| :---- |

### **Feature 7b: Call Callback Tracker**

Never forget a promised callback.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add callback tracking to the on-call system: 1\. In oncall\_list.html, add a dedicated "Callbacks Due" section at the top showing any promised callbacks past their due time 2\. The morning briefing notification includes: "On-call callbacks overdue: X" 3\. A push notification fires 30 minutes before a promised callback time: "Callback due in 30 minutes for \[patient identifier\]" 4\. The /oncall dashboard shows a count badge for overdue callbacks |
| :---- |

### **Feature 7d: Colleague On-Call Handoff**

Share a de-identified summary of active on-call items when handing off coverage.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add a handoff summary feature: 1\. GET /oncall/handoff \- Generates a summary of all notes from the current call period with status 2\. The summary contains ONLY: call times, chief complaints (no patient identifiers), and statuses 3\. A "Share Handoff" button generates a temporary 1-hour link that a colleague can open in their CareCompanion 4\. The link shows the handoff summary but does not require login (time-limited, read-only) |
| :---- |

### **Feature 7e: Note Status Tracking**

Clear visual status for every call note so nothing gets forgotten.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Enhance note status tracking: 1\. The on-call list uses a kanban-style status flow: New Call â†’ Pending Documentation â†’ Entered in Chart / No Documentation Needed 2\. Monday morning view: a filter showing only notes from the weekend with Pending Documentation status 3\. An unread badge on the On-Call nav item shows count of pending documentation notes 4\. Weekly on-call volume stats in the Metrics module: calls per week, most common complaints, average calls per night |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: Navigating to the On-Call page on your phone shows the mobile-optimized form Creating a note on your phone and refreshing the desktop shows the same note Voice input button activates the microphone and transcribes speech The export view formats the note correctly for Amazing Charts Clicking "Mark as Entered" changes the note status The morning briefing includes overdue callback count Tailscale is working: accessing http://\[tailscale-ip\]:5000/oncall from your phone outside the office works |
| :---- |

## **FEATURE 8: Order Set Manager & Executor**

The order set manager replaces the frustrating process of scrolling through Amazing Charts' long order list. You define your standard order sets once in CareCompanion, then with one click, PyAutoGUI executes the orders in Amazing Charts for you. You can add or remove individual orders before executing for each specific patient.

| âš ï¸  Important Safety Note: The order executor takes control of your mouse and keyboard. Amazing Charts MUST be open on the orders tab of the correct patient's chart before clicking Execute. The script will verify Amazing Charts is the foreground window and ask for confirmation before starting. Never trigger execution when Amazing Charts is not actively showing the right patient. |
| :---- |

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Order Set Manager module.   routes/orders.py: \- GET /orders \- Main order set manager page \- POST /orders/create \- Create new order set \- GET /orders/\<id\>/edit \- Edit order set \- POST /orders/\<id\>/update \- Save edits \- POST /orders/\<id\>/delete \- Delete order set (with confirmation) \- POST /orders/\<id\>/execute \- Trigger PyAutoGUI execution \- GET /orders/master-list \- View/edit the master list of all known orders \- POST /orders/share/\<id\> \- Publish order set to shared library   templates/orders.html \- The order set UI: LEFT PANEL: List of saved order sets with edit/share/delete buttons MIDDLE PANEL: Current order set items as checkboxes (pre-checked by default)   \- Each item: checkbox \+ order name \+ order tab label   \- "Remove" button per item   \- "Add Order" button opens a searchable dropdown of the master order list RIGHT PANEL (or bottom on mobile):    \- PRE-EXECUTION CHECKLIST: text box saying "Confirm Amazing Charts is open on Orders tab for the correct patient"   \- Confirmation checkbox the user must check   \- Large green EXECUTE button (only active when confirmation is checked)   \- Live status feed showing execution progress   agent/pyautogui\_runner.py: Create an execute\_order\_set(order\_items) function that: 1\. Verifies Amazing Charts is the foreground window (abort if not) 2\. Takes a pre-execution screenshot and saves it 3\. For each checked order item:    a. Click the correct tab (using stored coordinates or keyboard shortcut)    b. Find the order by scrolling and matching the label using OCR    c. Check the checkbox    d. Report progress back to the caller 4\. If any step fails: STOP immediately, save error screenshot, report failure 5\. Return a result object: {success, completed\_items, failed\_items, screenshots}   NOTE: The exact clicks and coordinates will need calibration to your Amazing Charts version. Include a calibration wizard that records where you click. |
| :---- |

### **Feature 8a: Shared Order Sets**

One provider builds a good order set; all colleagues benefit.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add order set sharing: 1\. Add is\_shared boolean and shared\_by\_user\_id to the OrderSet model 2\. In the order set list, add a "Community" tab showing all shared order sets from colleagues 3\. "Import" button copies a shared set to the user's personal library as an editable copy 4\. "Fork" label on imported sets indicating the original author 5\. The original author can retract a shared set (it becomes unavailable for new imports but doesn't affect already-imported copies) |
| :---- |

### **Feature 8b: Order Set Version History**

Every edit is saved so you can always go back.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add version history to order sets: 1\. Before saving any edit to an order set, copy the current version to an OrderSetVersion table (id, orderset\_id, version\_number, snapshot\_json, saved\_at, saved\_by\_user\_id) 2\. A "History" button on each order set shows the last 10 versions 3\. A "Restore" button restores any previous version (creating a new version entry rather than overwriting) |
| :---- |

### **Feature 8d: Pre-Execution Confirmation Screen**

No automation runs without your explicit confirmation of the correct patient.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Enhance the pre-execution flow: 1\. When Execute is clicked, show a modal dialog (not a separate page) with:    \- "You are about to execute \[Order Set Name\] in Amazing Charts"    \- "Please confirm: Amazing Charts is open on the Orders tab for \[type patient name here\]"    \- A text field where the user must type something to confirm (reduces accidental triggers)    \- A 3-second countdown before the Execute button becomes active (prevents double-clicking) 2\. After execution, show a result summary: X orders completed, Y failed (if any) 3\. Failed orders listed individually with screenshots attached |
| :---- |

### **Feature 8e: Partial Execution Recovery**

If the script is interrupted mid-execution, it recovers cleanly.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add execution state tracking: 1\. Before starting execution, write an OrderExecution record with status=in\_progress and the full list of orders 2\. Update status to completed/failed per order as they execute 3\. If the script is interrupted (exception, Amazing Charts closes, etc.), mark the execution record as interrupted 4\. On next visit to the orders page, show a banner: "Previous execution was interrupted. X of Y orders completed. Resume or restart?" 5\. Resume continues from where execution stopped |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: The Order Sets page loads and shows the left/middle/right panel layout Creating a new order set saves it to the database Adding and removing items from an order set works correctly The Execute button is disabled until the confirmation checkbox is checked Clicking Execute with Amazing Charts NOT open aborts safely with an error message With Amazing Charts open on the orders tab, execution starts and shows progress A failed order shows a screenshot in the results Shared order sets are visible in the Community tab |
| :---- |

## **FEATURE 9: Pre-Visit Note Prep**

Every night, this script opens Amazing Charts and runs the two-phase Clinical Summary export workflow for all patients on tomorrow's schedule. **Phase 1** opens each patient's chart with the Companion visit template to create a new, fresh note wihtout the prior vists' information(Visit Template â†’ Procedure Visit â†’ Companion) and closes it to the inbox (Ctrl+S). **Phase 2** exports the Clinical Summary XML for each patient from the inbox, always selecting **"Full Patient Record"** from the encounter dropdown to get the complete patient history. You arrive in the morning to parsed clinical data ready in CareCompanion's Patient Chart View.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Pre-Visit Note Prep system.   agent/note\_prep.py: A function run\_nightly\_note\_prep(user\_id) that runs the two-phase Clinical Summary export workflow: 1\. Retrieve tomorrow's schedule from the database (populated by the NetPractice scraper) 2\. **Phase 1 â€” Chart Opening (all patients):** For each patient entry:    a. Log the attempt (patient identifier hash \+ timestamp)    b. Bring Amazing Charts to focus    c. Search by patient ID in the Patient List panel (blue field under Schedule/Messages/Reports/Secure buttons)    d. Verify first and last name match    e. Double-click to open a new chart    f. Select the Visit Template radio button, then Select Template â†’ Procedure Visit â†’ Companion    g. Clear any popup boxes (OK or X)    h. Press Ctrl+S to save and close the chart (sends note to inbox)    i. Update chart-opened status in the database    j. Handle failures gracefully: log failure reason, continue to next patient 3\. **Phase 2 â€” XML Export (all patients):** After ALL charts are in the inbox:    a. Verify AC is on the home screen (no chart windows open)    b. For each patient: find the most recent chart in the inbox (verify by time column, name, and MRN)    c. Single-click the chart row to select    d. Alt+P â†’ Export Clinical Summary    e. Select **\"Full Patient Record\"** from encounter dropdown, verify all checkboxes, verify destination folder    f. Click Export, dismiss success dialog (Enter)    g. Watch data/clinical\_summaries/ for the new XML file    h. Update export status in the database    i. Handle failures gracefully: log failure reason, continue to next patient 4\. Send completion notification when done: "Note prep complete: 12/14 charts opened, 12/14 exports complete. 2 failed â€” see prep report."   routes/orders.py \- Add prep status endpoints: \- GET /prep/status \- Shows tonight's prep progress (auto-refreshing page) \- GET /prep/report \- Shows prep history with success/failure details \- POST /prep/retry/\<patient\_hash\> \- Retry a failed prep |
| :---- |

### **Feature 9a: Template Source Sync**

Uses your existing Amazing Charts templates so you maintain only one set.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add Amazing Charts template discovery: 1\. Create a function discover\_ac\_templates() that opens Amazing Charts, navigates to the template selection screen, and uses OCR to read all available template names 2\. Store discovered templates in the database (TemplateLibrary table: id, name, ac\_internal\_name, last\_synced) 3\. A /orders/templates page lets you map AC template names to visit types 4\. Run discovery automatically once a week and flag any new templates for your review |
| :---- |

### **Feature 9c: Prep Status Dashboard**

See exactly how far along tonight's prep is before you go to bed.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add a real-time prep status view: 1\. The prep status page at /prep/status auto-refreshes every 10 seconds using JavaScript 2\. Shows: progress bar (X of Y complete), estimated completion time, current patient being processed (as a hash/number, not name), any failures 3\. A push notification fires when prep is complete with the final count 4\. The Today View shows a "Prep Status" badge: green (complete), yellow (in progress), red (failed or not run) |
| :---- |

### **Feature 9d: Failed Prep Alert**

Know immediately which charts need manual prep attention.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Enhance failure handling: 1\. Failed preps are logged with: patient identifier hash, failure reason (not found, AC error, template error), timestamp, screenshot at time of failure 2\. Failures appear in the Today View as yellow flags next to the patient slot 3\. The morning briefing includes: "Note prep: 12 ready, 2 need attention" 4\. One-click retry button in the Today View for each failed chart |
| :---- |

### **Feature 9e: MA Prep Handoff**

Your MA can trigger prep for specific patients during rooming.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add MA-accessible prep features: 1\. MAs can see the prep status page 2\. A "Prep This Chart" button in the schedule view lets an MA trigger immediate prep for one specific patient 3\. After rooming (vital signs entered), the MA can add chief complaint to the note by typing it in CareCompanion and a PyAutoGUI script pastes it into the open note in Amazing Charts 4\. These MA-initiated updates show a different badge in the Today View so you know the note has been augmented |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: Triggering note prep manually for a test patient creates a note in Amazing Charts The prep status page shows real-time progress A failed prep shows the failure reason and screenshot The completion push notification arrives on your phone The Today View shows prep status badges for each patient Template discovery finds and lists your AC templates |
| :---- |

## **FEATURE 10: Medication Initiation Reference**

A searchable, locally-hosted drug reference organized by condition, showing first-line, second-line, and special population recommendations. Editable by you and shareable with colleagues. Accessible as a floating window via hotkey so it doesn't interrupt your charting.

| ðŸ”—  NIH RxNorm API Integration: This module is the primary consumer of the RxNorm API (see Section 4.3). The API powers: (1) **Autocomplete** â€” `getDisplayTerms` provides a curated list of drug display strings for the search bar, (2) **Spelling correction** â€” `getSpellingSuggestions` handles typos, (3) **Drug lookup** â€” `getDrugs` returns all formulations/strengths/routes for a given drug name, (4) **Brandâ†”Generic mapping** â€” `getGenericProduct` and `getRelatedByType` resolve brand names to generics and vice versa, (5) **Drug relationships** â€” `getAllRelatedInfo` navigates from a drug to its ingredients, dose forms, and drug class. All responses are cached in the local `RxNormCache` table. The API is free and requires no license or API key. |
| :---- |

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Medication Reference module.   routes/medref.py: \- GET /medref \- Main searchable reference page \- GET /medref/condition/\<name\> \- All drugs for a condition \- POST /medref/add \- Add new entry \- POST /medref/\<id\>/edit \- Edit entry \- POST /medref/\<id\>/annotate \- Add personal note to an entry \- GET /medref/popup \- Stripped-down popup view for floating window use \- POST /medref/share/\<id\> \- Share entry with colleagues   templates/medref.html: \- Search bar at top (searches condition names and drug names) \- Filter buttons: First Line, Second Line, All Lines; Special Populations: Renal, Pregnancy, Elderly, Pediatric \- Results as cards grouped by condition \- Each card: drug name, class, dosing summary, special population icons, edit/annotate buttons   templates/medref\_popup.html \- Minimal view for the AutoHotkey popup: \- No navigation, just search \+ results \- Opens as a small browser window (800x600) \- Auto-focuses the search field   Seed the database with common primary care conditions and first-line medications: HTN, DM2, Hypothyroidism, Hyperlipidemia, GERD, Depression, Anxiety, Asthma, COPD, UTI, URI/Sinusitis, Strep, Skin infections, Gout, Osteoporosis, Atrial Fibrillation, Heart Failure   For each condition include at minimum: first-line drug, class, typical starting dose, key monitoring, and one pregnancy/renal note.   AutoHotkey integration: Create a .ahk script (medref\_popup.ahk) that: \- Is triggered by a configurable hotkey (default: Win+M) \- Opens a small Chrome window to http://localhost:5000/medref/popup \- The window stays on top of other windows |
| :---- |

### **Feature 10a: Shared Formulary Notes**

Practice-specific annotations visible to all providers.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add shared annotations: 1\. Each medication entry can have both personal notes (visible only to the author) and shared notes (visible to all practice users) 2\. Shared notes show the author's initials and date 3\. An admin can delete inappropriate shared annotations 4\. Examples: "Blue Cross Step 1 requires this before approving drug X" or "Our pharmacy doesn't carry brand-name Z" |
| :---- |

### **Feature 10c: Pregnancy & Renal Quick Filter**

One-tap filter removes unsafe options based on patient context.

| ï¿½  RxNorm Enhancement: `getRelatedByRelationship` (rela=has_ingredient) identifies active ingredients for each medication. Safety checks can be applied at the ingredient level (not just brand name), which catches combination products that contain a contraindicated ingredient even when the brand name doesn't make the ingredient obvious. |
| :---- |

| ï¿½ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add contextual safety filters: 1\. Add a patient context bar at the top of the medref popup: toggle buttons for Pregnant, CKD (with eGFR dropdown), Elderly (\>75), Pediatric, Hepatic impairment 2\. When a filter is active, entries with contraindications for that population are either hidden or shown with a red warning banner 3\. The filter state persists for the duration of the browser session (cleared when you close the tab) |
| :---- |

### **Feature 10d: Recent Guideline Update Flag**

Keeps your reference honest about potentially stale entries.

| ï¿½  RxNorm Enhancement: `getRxcuiHistoryStatus` detects when a drug's RXCUI has been obsoleted or remapped by the NLM (e.g., drug withdrawn from market, name changed, reformulated). `findActiveProducts` finds current active replacements. This enables automatic flagging of outdated medication entries in the reference â€” entries whose RXCUI status has changed are auto-flagged for review without manual intervention. |
| :---- |

| ï¿½ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add guideline review tracking: 1\. Each entry has a last\_reviewed\_date and a guideline\_review\_flag boolean 2\. Admin can flag any entry as "recommend review" 3\. Flagged entries show a yellow banner: "This entry has not been reviewed since \[date\]. Verify against current guidelines." 4\. A /medref/review-needed page lists all flagged entries for bulk review and updating |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: The Medication Reference page loads and shows seeded conditions Searching "hypertension" returns relevant drug entries First-line filter shows only first-line options Pregnancy filter hides contraindicated entries The popup window opens at /medref/popup The AutoHotkey script opens the popup window on hotkey press Adding a personal annotation saves and displays correctly |
| :---- |

### **Feature 10e: Patient Chart View**

CareCompanion's most important display feature. A dedicated patient chart view accessible from:
1. The Today View â€” click any patient name to open their chart
2. The dashboard search bar â€” search by name or MRN (Feature 4f)

**Why this feature exists:** Amazing Charts requires 8+ clicks to navigate between medications, labs, and diagnoses for a single patient. The patient chart view in CareCompanion presents all of this information simultaneously in one browser window, loaded from the parsed Clinical Summary XML, with zero AC navigation required. The Prepped Note tab allows pre-charting before the visit and direct injection into AC when ready.

| ðŸ”—  RxNorm-Enriched Medications Widget: The Medications tab and the Active Medications overview widget display data enriched by the RxNorm API. Instead of showing the raw XML string (e.g., "Lipitor 20 mg tablet [RxNorm: 617310]"), the widget shows clean columns: **Brand Name** (Lipitor), **Generic Name** (atorvastatin), **Dose + Form** (20 mg tablet), **Frequency**, **Status**. The UpToDate hyperlink uses the generic name for more reliable lookups. All enrichment data comes from the `RxNormCache` table â€” populated at XML parse time, so the chart loads instantly with no API delay. |
| :---- |

**Chart view layout â€” Left sidebar tabs (mirrors AC section structure):**
```
ðŸ“‹ Overview         â† landing page with customizable widgets
ðŸ’Š Medications      â† active med list, last updated timestamp
ðŸ”¬ Labs             â† lab results with trend indicators (links to F11)
ðŸ©º Diagnoses        â† active problem list with ICD-10 codes
ðŸ’‰ Immunizations    â† immunization history from XML
ðŸ“Š Vitals           â† most recent vitals + historical trend
âš ï¸ Allergies        â† allergy list with reactions
ðŸ“ Prepped Note     â† note writing workspace (see below)
ðŸ“ Care Gaps        â† links to F15 care gap tracker for this patient
```

**Overview tab â€” customizable widgets:**
Users configure which widgets appear on the overview landing page. Available widgets:
- Active Medications (count + list)
- Recent Labs (last 3 results per tracked lab)
- Active Diagnoses (problem list)
- Recent Vitals (last BP, weight, BMI)
- Prior Screenings / Care Gaps due
- On-Call Notes for this patient
- Upcoming Appointments

Widget layout is saved per user in the preferences JSON column.

**Prepped Note tab:**
A plain-text note workspace with one labeled text area per AC section. Sections match the Enlarge Textbox window exactly:
```
Chief Complaint | History of Present Illness | Review of Systems |
Past Medical History | Social History | Family History | Allergies |
Medications | Physical Exam | Functional Status/Mental Status |
Confidential Information | Assessment | Plan | Instructions |
Goals | Health Concerns
```
Each section is a resizable textarea. Pre-populated from the Clinical Summary XML where available (structured sections) and left blank for narrative sections (HPI, Assessment, Plan) which the provider fills.

Three action buttons at the top of the Prepped Note tab:
- `Copy All to Clipboard` â€” formats all sections and copies for AC paste
- `Send to Amazing Charts` â€” triggers PyAutoGUI to paste each section into the Enlarge Textbox window using `Update & Go to Next Field`
- `Save Draft` â€” saves current content to the database (not sent to AC)

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Patient Chart View for CareCompanion.   routes/patient.py with: \- GET /patient/\<mrn\> â€” patient chart landing page (Overview tab) \- GET /patient/\<mrn\>/medications â€” medications tab \- GET /patient/\<mrn\>/labs â€” lab results tab (integrates with F11 lab tracker) \- GET /patient/\<mrn\>/diagnoses â€” active problem list tab \- GET /patient/\<mrn\>/immunizations â€” immunizations tab \- GET /patient/\<mrn\>/vitals â€” vitals history tab \- GET /patient/\<mrn\>/allergies â€” allergies tab \- GET /patient/\<mrn\>/note â€” prepped note tab \- POST /patient/\<mrn\>/note/save â€” save note draft to database \- POST /patient/\<mrn\>/note/send-to-ac â€” trigger PyAutoGUI paste to AC \- GET /patient/search?q= â€” search patients by name or MRN (returns JSON) \- POST /patient/\<mrn\>/refresh â€” trigger Clinical Summary export + re-parse   templates/patient\_chart.html: \- Left sidebar with tab icons and labels matching the section list above \- Active tab highlighted \- Main content area changes based on active tab \- Header bar showing: patient name, DOB, age/sex, MRN (last 4), last updated timestamp (from last XML parse), "Refresh from AC" button \- "Last synced: \[timestamp\]" indicator â€” shows how fresh the data is   templates/patient\_note.html (Prepped Note tab): \- One labeled textarea per AC note section (16 sections total, see list) \- Sections in the exact order from AC\_NOTE\_SECTIONS constant \- Each textarea: label at top, resizable, monospace font \- Auto-save to localStorage every 30 seconds (no data loss on close) \- Three action buttons as described above   All data on this page comes from the parsed Clinical Summary XML stored in the database. If no XML has been parsed for this patient, show a "No clinical summary loaded" banner with a "Load from Amazing Charts" button that triggers the export automation.   Scope all database queries to current\_user.id. MRN is displayed as last-4 digits only in any UI element visible on a shared screen. Full MRN is used only in database queries and API calls. |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: The patient chart view loads for a patient with parsed Clinical Summary data All sidebar tabs display correct data from the database The Prepped Note tab shows 16 section textareas in the correct order Copy All to Clipboard formats and copies all sections correctly Save Draft persists note content to the database The "Load from Amazing Charts" button triggers the export automation The search bar in the dashboard header returns matching patients MRN displays as last-4 only on all visible UI elements |
| :---- |

| PHASE 4: Monitoring & Tracking | \~16-20 hours |
| :---- | :---: |

## **FEATURE 11: Lab Value Tracker**

Per-patient lab monitoring with custom thresholds and trend visualization. Set up tracking criteria for specific patients â€” for example, track your CKD patient's creatinine every 6 months and alert you if it rises above 2.0. Fed automatically by the inbox monitor as new labs arrive.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Lab Value Tracker module.   routes/labtrack.py: \- GET /labtrack \- Dashboard showing all tracked patients with status \- GET /labtrack/\<mrn\> \- All tracked labs for one patient \- POST /labtrack/add \- Add new lab tracking criteria \- POST /labtrack/\<id\>/edit \- Edit tracking criteria \- POST /labtrack/\<id\>/result \- Manually add a result (when OCR-captured result is unclear) \- GET /labtrack/\<mrn\>/trend/\<lab\_name\> \- Trend chart data (JSON for Chart.js)   templates/labtrack.html: \- Overview table: patient identifier, lab name, last value, last date, next due date, trend arrow, status badge \- Status badges: Due Soon (yellow), Overdue (red), On Track (green), Critical Value (red \+ bell) \- Click patient row to expand all their tracked labs \- "Add Tracking" button opens a form   templates/labtrack\_patient.html \- Per-patient detail view: \- List of all tracked labs with trend sparklines (small inline Chart.js graphs) \- Each lab shows: last 5 values, dates, trend direction \- Alert threshold indicators (you set high/low lines on the chart) \- "Overdue" banner if next-due date has passed   Trend chart using Chart.js: \- Line chart with date on X axis, value on Y axis \- Horizontal reference lines for your custom alert thresholds \- Color coding: values in normal range (blue line), above threshold (orange), critical (red)   Integration with inbox monitor: \- When the inbox monitor detects a new lab in the inbox, it checks if that patient has any LabTrack entries \- If matching entries exist, the new result is added to LabResult table automatically \- If the new result triggers an alert threshold, send immediate push notification |
| :---- |

### **Feature 11a: Trend Visualization**

A line graph showing lab values over time with your custom threshold lines.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Implement Chart.js trend graphs in the lab tracker: 1\. For each LabTrack with 2+ results, render a Chart.js line chart 2\. The chart should show: date on X axis, numeric value on Y axis, the actual results as data points connected by a line 3\. Horizontal dashed lines for: alert\_low (orange), alert\_high (orange), and any standard reference range if entered 4\. Data points colored red if outside threshold, green if within 5\. Charts are rendered as inline SVG-equivalent canvas elements within the page (no separate page load) 6\. A trend label below each chart: "Trending UP â†‘", "Stable â†’", or "Trending DOWN â†“" based on the last 3 values |
| :---- |

### **Feature 11b: Custom Alert Thresholds Per Patient**

Different patients need different alert levels based on their baseline and conditions.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Enhance the LabTrack model and UI: 1\. Each LabTrack entry has: alert\_low (float), alert\_high (float), critical\_low (float), critical\_high (float) 2\. In the tracking setup form, show a visual range indicator: a horizontal bar divided into critical/alert/normal zones 3\. Sliders let you drag the threshold boundaries 4\. When a result falls in the critical zone, push notification fires immediately (bypasses quiet hours) 5\. Alert zone: next-scheduled-check notification includes the value and that it is outside range |
| :---- |

### **Feature 11d: Lab Panel Grouping**

View related labs together as panels, not individual values.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add lab panels to the tracker: 1\. Define standard panels: Basic Metabolic Panel (Na, K, Cl, CO2, BUN, Cr, Glucose), CMP (BMP \+ liver enzymes), CBC, Lipids, Thyroid, Diabetes (A1c \+ fasting glucose \+ microalbumin) 2\. When adding a tracked lab, option to add as part of a panel 3\. Panel view shows all components together in one card 4\. If one panel component is critical, the whole panel card highlights |
| :---- |

### **Feature 11c: Overdue Lab Notification**

Proactively flags patients whose labs are past due before you notice.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Implement overdue lab detection: 1\. A daily scheduled job (runs at 6 AM) checks all LabTrack entries 2\. For any patient where: last\_checked \+ interval\_days \< today, flag the entry as overdue 3\. Overdue entries appear in the Today View with a red clock icon next to the patient if they are on today's schedule 4\. Morning briefing includes: "Labs overdue: 3 patients on today's schedule have overdue tracking labs" 5\. The care gap checker also pulls from overdue LabTrack entries |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: The Lab Tracker page shows a table of tracked labs Adding a new tracking entry saves correctly Manually adding a result shows in the trend chart A lab above the high threshold shows the alert badge The trend chart renders correctly with Chart.js An overdue lab appears in the morning briefing |
| :---- |

### **Feature 11e: Clinical Summary Auto-Archive**

XML Clinical Summary files are stored in `data/clinical_summaries/` on the local machine. A daily scheduled job (`agent/scheduler.py`) deletes any file older than 183 days. Every parse operation is logged to the AuditLog table. Files are never transmitted outside the local machine.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add XML Clinical Summary auto-archive to CareCompanion: 1\. XML files are stored in data/clinical\_summaries/ after each Clinical Summary export 2\. Add a daily scheduled job in agent/scheduler.py that runs at 2:00 AM: a. Scans data/clinical\_summaries/ for all .xml files b. Deletes any file with mtime older than CLINICAL\_SUMMARY\_RETENTION\_DAYS (default 183, configurable in config.py) c. Logs each deletion to AuditLog: user\_id=system, action="xml\_archive\_delete", details=sha256(filename)[:12] 3\. Every parse operation already logs to AuditLog (mrn\_hash, timestamp, sections\_found) 4\. data/clinical\_summaries/ must be in .gitignore â€” these files contain full PHI 5\. Never transmit XML files outside the local machine |
| :---- |

## **FEATURE 12: Visit Timer & Face-to-Face Timer**

The chart time tracker runs automatically via the MRN reader (Feature 6). The face-to-face timer is intentional â€” you trigger it when you leave your desk and again when you return. Both feed the billing audit log.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Visit Timer module UI.   routes/timer.py: \- GET /timer \- Main timer dashboard (today's sessions) \- POST /timer/face/start \- Start face-to-face timer \- POST /timer/face/stop \- Stop face-to-face timer \- POST /timer/\<id\>/annotate \- Add billing annotation to a time log entry \- POST /timer/\<id\>/flag-complex \- Flag as unexpectedly complex visit \- GET /timer/export \- Export time logs as CSV \- GET /timer/report/\<date\> \- Day summary report   templates/timer.html: TODAY'S SESSIONS section: \- Table showing each chart session: time range, MRN (last 4 digits only for display), duration, visit type, face-to-face time (if captured) \- Billing level selector per row (99211-99215, 99201-99205, AWV codes) \- "Complex" flag toggle \- Notes field per row   ACTIVE SESSION banner at top (if a session is currently in progress): \- Shows: current MRN (last 4), session start time, elapsed time (live, updates every 30 seconds) \- Face-to-Face button: large, easy to tap: "ðŸ‘‹ Leaving Desk" / "ðŸ–¥ Back at Desk"   DAILY SUMMARY at bottom: \- Total chart time, total face-to-face time, number of patients, average per patient \- E\&M level distribution bar chart |
| :---- |

### **Feature 12a: Visit Type Auto-Tag**

Automatically categorizes sessions using the schedule data.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add visit type auto-tagging: 1\. When the MRN reader opens a new session, immediately check the Schedule table for an appointment today matching this patient 2\. If found, copy the visit\_type from the schedule to the time log entry 3\. The visit type is editable in the timer UI in case the auto-tag is wrong 4\. A confidence indicator shows whether the tag was auto-assigned or manually set |
| :---- |

### **Feature 12b: Time Complexity Flag**

Tag visits that ran longer than expected for future scheduling discussions.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add complexity flagging: 1\. A one-tap "Complex Visit" toggle button on each session row 2\. When flagged, a short notes field appears for you to note why (optional) 3\. Complex flags are incorporated into the Visit Duration Estimator (Feature 4b) as outliers that shouldn't skew the average 4\. The Metrics dashboard shows % of visits flagged as complex by visit type over time |
| :---- |

### **Feature 12c: Face-to-Face Widget on Room Computers**

A minimal one-button interface on exam room computers that doesn't require login.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create a minimal room computer widget: 1\. A route GET /timer/room-widget \- No authentication required 2\. Shows a single large button: "Provider Entered Room" / "Provider Left Room" 3\. The button calls POST /timer/face/room-toggle which:    a. Checks who the active provider is (from agent's active\_user.json)    b. Starts or stops the face-to-face timer for that provider's current active session 4\. The page auto-refreshes every 5 seconds to show current status 5\. Add a QR code to the widget page that room computers can display for easy phone access too |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: Today's sessions appear in the Timer page as you see patients Face-to-face timer starts and stops via the Leaving Desk / Back at Desk button Face-to-face time appears in the session row Billing level selector saves when changed The room computer widget at /timer/room-widget loads without login Pressing the room widget button starts/stops the face-to-face timer for the active session CSV export contains all sessions with correct times |
| :---- |

## **FEATURE 13: Productivity & Task Time Dashboard**

Visual reporting on top of the data already being collected. The longer the system runs, the more valuable this becomes. By the time your orientation ends you will have months of your own data.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Productivity Dashboard module.   routes/metrics.py: \- GET /metrics \- Main dashboard \- GET /metrics/weekly \- Weekly summary \- GET /metrics/api/chart-data \- JSON endpoint for Chart.js data   templates/metrics.html \- Dashboard with these charts and stats: 1\. TODAY CARD: Patients seen, Total chart time, Total face-to-face time, Avg per patient 2\. WEEKLY TREND: Line chart showing daily patient count and total chart time for last 30 days 3\. VISIT TYPE BREAKDOWN: Donut chart showing proportion of each visit type this month 4\. AVG CHART TIME BY VISIT TYPE: Horizontal bar chart (this is most useful for scheduling negotiations) 5\. FACE-TO-FACE RATIO: What percentage of your working time is actual face-to-face vs. documentation 6\. INBOX ACTIVITY: Line chart of inbox item counts over time (from inbox snapshots) 7\. ON-CALL VOLUME: Bar chart of after-hours calls by week   All charts use Chart.js. All data comes from the existing TimLog, InboxSnapshot, and OnCallNote tables. Data filtered to the current logged-in user only.   Add a date range picker to filter all charts to a specific period. Add an export button that generates a PDF summary of the current dashboard view using browser print styling. |
| :---- |

### **Feature 13a: Benchmark Comparison**

Anonymized comparison to practice peers â€” not for evaluation, for your own awareness.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add anonymized benchmarking (opt-in only): 1\. A user setting: participate\_in\_benchmarks (default false) 2\. Providers who opt in contribute their aggregate stats (no individual session data) to a shared benchmark table 3\. Aggregated metrics only: avg chart time by visit type, avg inbox turnaround, avg face-to-face ratio 4\. In the Metrics dashboard, a "Practice Average" line appears on relevant charts 5\. No individual identification â€” each provider sees only their own position relative to the group |
| :---- |

### **Feature 13b: Burnout Early Warning Indicators**

Data-driven flags for concerning trends before they become a problem.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add wellbeing trend monitoring: 1\. Weekly calculation of three indicators:    \- After-hours chart time: minutes of chart sessions outside 7 AM \- 6 PM    \- Inbox backlog trend: is the inbox item count growing week over week    \- Face-to-face ratio trend: is your documentation time growing relative to patient time 2\. If any indicator worsens for 3 consecutive weeks, a discrete note appears in your weekly summary: "Documentation time has increased 15% over the past 3 weeks." 3\. NOT an alert â€” just information presented matter-of-factly in the weekly report |
| :---- |

### **Feature 13c: Weekly Summary Email**

A formatted summary of your week delivered to your email Friday afternoon.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Implement weekly summary email: 1\. Every Friday at 5 PM, generate an HTML email for each opted-in provider 2\. Content: patients seen this week, total hours documented, top 3 visit types, inbox activity summary, on-call calls this week, one notable metric (e.g., "Your average chart time for follow-up visits decreased by 4 minutes this week") 3\. Uses Python's smtplib with Gmail SMTP (user provides their Gmail credentials in settings, stored encrypted) 4\. A /metrics/preview-weekly route lets you preview this week's summary before Friday |
| :---- |

## **FEATURE 14: Billing Audit Log**

A permanent, exportable record of every patient encounter with timing data and billing rationale. This is your documentation defense if any billing decision is ever questioned.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Billing Audit Log as a sub-view of the Timer module.   routes/timer.py \- Add: \- GET /billing/log \- Full billing audit log with filters \- GET /billing/log/export \- PDF export \- POST /billing/\<id\>/add-rationale \- Add documentation rationale to an entry   templates/billing\_log.html: \- Filter controls: date range, visit type, billing level, flagged only \- Table columns: Date, Patient (MRN last 4), Visit Type, Chart Time, Face-to-Face Time, Billed Level, Rationale, Flags \- Each row expandable to show full billing notes \- Export button   PDF export should generate a formal-looking document that could be submitted in an audit. Each entry should contain: date, time range, duration, face-to-face duration, visit type, selected E\&M level, your documentation rationale, and whether any complexity flags were set.   Include a totals summary: total visits by E\&M code, total estimated RVUs (use a simple lookup table of standard RVU values per code). |
| :---- |

### **Feature 14a: E\&M Level Calculator**

Suggests the appropriate billing level based on your documented time.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add an E\&M suggestion tool: 1\. A small calculator widget in the Timer page 2\. User inputs: MDM level (straightforward/low/moderate/high) and total documented time 3\. Returns: suggested E\&M level per 2023 AMA guidelines (time-based OR MDM-based, whichever supports higher) 4\. A "Use This Level" button pre-fills the billing level selector for the current session 5\. Inline reference showing the time thresholds for each level |
| :---- |

### **Feature 14b: Billing Anomaly Detector**

Flags inconsistencies between time and billing level for review.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add billing consistency checks: 1\. When a billing level is saved for a session, run these checks:    \- Is the documented time below the minimum for this level? (Flag: "Time may not support this level")    \- Is the documented time above the minimum for a higher level? (Flag: "Consider higher level based on time") 2\. Flagged entries show a yellow caution icon in the billing log 3\. A "Review Anomalies" filter shows only flagged entries 4\. Clicking the flag opens a side panel explaining the concern and what documentation would resolve it |
| :---- |

### **Feature 14c: Monthly Billing Summary Report**

Exportable monthly productivity report for practice management discussions.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create a monthly billing summary: 1\. GET /billing/monthly-report?month=YYYY-MM 2\. Generates a formatted HTML report (printable) with:    \- Total encounters by E\&M code level    \- Estimated RVU total (standard values per code)    \- Split between new patient and established patient codes    \- Time-based vs MDM-based billing distribution    \- Comparison to prior month 3\. Export as PDF option 4\. Schedule this to auto-generate and email to you on the 1st of each month |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: The Billing Audit Log shows time log entries with billing level selectors The E\&M calculator suggests the correct level for a given time and MDM input A session with too-short time for the selected level shows a caution flag PDF export generates a formatted document Adding a rationale note saves and appears in the PDF |
| :---- |

| PHASE 5: Clinical Decision Support | \~18-22 hours |
| :---- | :---: |

## **FEATURE 15: Care Gap Tracker**

A per-patient preventive care checklist generated from your schedule data. Age and sex-appropriate screenings are auto-populated. Flags appear in your Today View before each visit so you can address care gaps proactively.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Care Gap Tracker module.   The care gap system has two parts: a rules engine and a per-patient UI.   agent/caregap\_engine.py \- Rules engine: Create a function evaluate\_care\_gaps(patient\_data) where patient\_data includes: age, sex, known\_diagnoses (list), last\_visit\_date. The function returns a list of applicable care gap checks based on published USPSTF recommendations, and should access publically available API data when applicable. List the API access and make it editable within the admin menu on the user interface:   Define these hardcoded rules for at minimum, but API accessed data should over write or supersceed these suggestions: \- Colorectal cancer screening: age 45-75, interval 10yr (colonoscopy) or 1yr (FOBT) \- Breast cancer screening: women 40+, interval 2yr \- Cervical cancer screening: women 21-65, interval 3yr (Pap) or 5yr (Pap \+ HPV) \- Lung cancer screening: age 50-80, heavy smoker history, annual LDCT \- Osteoporosis screening: women 65+, or younger with risk factors \- Hypertension screening: all adults \- Diabetes screening: adults 35-70 who are overweight \- Lipid screening: men 35+, women 45+ or younger with risk factors \- Depression screening: all adults annually \- AAA screening: men 65-75 who ever smoked, one time \- Fall risk assessment: adults 65+ \- HIV screening: adults 15-65 one time \- Immunizations: Flu (annual), COVID (per current guidelines), Shingrix (50+), TDAP, Pneumococcal   Each rule object: {gap\_name, description, criteria\_function, interval\_days, billing\_code\_pair, documentation\_template}   routes/caregap.py: \- GET /caregap \- Overview of upcoming patients' care gaps \- GET /caregap/\<mrn\> \- All gaps for one patient \- POST /caregap/\<mrn\>/address/\<gap\_id\> \- Mark gap as addressed in today's visit \- GET /caregap/panel \- Panel-wide gap summary |
| :---- |

### **Feature 15a: Age and Sex Based Auto-Population**

Care gaps appropriate for each patient populate automatically.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: The care gap engine automatically generates gap entries for each patient on the schedule: 1\. When the schedule scraper pulls tomorrow's patients, trigger evaluate\_care\_gaps() for each 2\. Compare results against existing CareGap records for the patient 3\. Create new gap records only for gaps not already addressed or in progress 4\. The Today View shows a count badge per patient: "3 care gaps"  5\. Clicking opens the gap checklist without leaving the Today View (inline expansion or modal) |
| :---- |

### **Feature 15b: Care Gap Closure Documentation Prompt**

Auto-generates the documentation language when you address a gap.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: When a care gap is marked as addressed: 1\. Show a documentation snippet pre-generated from the gap's template 2\. Example: "Colorectal cancer screening discussed. Patient agrees to colonoscopy referral. Order placed today." 3\. A copy button puts this text in the clipboard for pasting into Amazing Charts 4\. The gap record is updated with: completed\_date, documentation\_snippet, the provider who addressed it |
| :---- |

### **Feature 15c: Panel-Wide Gap Report**

See which gaps are most prevalent across your entire panel.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the panel gap report at /caregap/panel: 1\. A summary table showing: gap name, number of patients due/overdue, % of panel covered 2\. Sort by worst coverage first (most overdue percentage) 3\. Filter by patient age range, sex 4\. An "Outreach List" button generates a list of patients due for a specific screening â€” formatted for your MA to use for outreach calls 5\. This list contains patient identifiers only (not full PHI in the UI) but can export a version formatted for your MA to use with full names from Amazing Charts |
| :---- |

## **FEATURE 16: Billing Capture Suggestions**

Preventive care and chronic disease management generate significant revenue beyond the standard visit code â€” but only if properly documented and billed. This module flags opportunities you might miss.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Billing Capture module integrated with the Care Gap Tracker.   This module provides billing code suggestions based on the visit type and what was addressed.   Create a billing rules reference (billing\_rules.py): Define opportunities for each scenario:   AWV (Annual Wellness Visit) add-ons: \- G0444: Annual depression screening \- G0442: Annual alcohol misuse screening \- G0439: Subsequent AWV (if prior year had G0438) \- 99497: Advance care planning (if discussed, 16+ minutes) \- Personalized Prevention Plan Services   Chronic Care Management (CCM): \- 99490: 20+ minutes non-face-to-face care coordination per month for 2+ chronic conditions \- 99487: Complex CCM, 60+ minutes \- Eligibility criteria: patient has 2+ chronic conditions expected to last 12+ months   Prolonged Services: \- 99417: Prolonged office visit, each 15-min increment beyond the maximum time for the E\&M level \- Required documentation: total time, time spent on each component   Behavioral Health Integration: \- 99484: General BHI, 20+ min per month   Transitional Care Management: \- 99495: Moderate complexity, 14-day discharge follow-up \- 99496: High complexity, 7-day discharge follow-up   routes: Add billing suggestion output to the care gap and timer modules. On the Timer page, after saving a billing level, show a panel: "Additional billing opportunities for this visit:" with applicable codes and what documentation is required. |
| :---- |

### **Feature 16b: CCM Eligibility Flag**

Identifies patients who qualify for monthly chronic care management billing.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add CCM tracking: 1\. A flag on patient records: ccm\_eligible (set manually by provider or based on problem list data when available) 2\. For CCM-eligible patients, the lab tracker and visit timer together accumulate monthly non-face-to-face minutes 3\. When monthly minutes cross 20, the Today View shows a CCM billing alert: "Patient X has accrued 22 min CCM this month â€” eligible for 99490" 4\. Required documentation template pre-generated and available to copy |
| :---- |

### **Feature 16a: AWV Add-On Code Checklist**

Ensures you complete and document all AWV components.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create an AWV visit companion: 1\. When an AWV visit is detected in today's schedule, show an AWV Companion panel in the Today View 2\. The panel is a checklist of all AWV components: Health risk assessment, vitals, cognitive assessment, depression screening, advance directives discussion, fall risk, etc. 3\. Checking each item documents it was completed 4\. At the end, show: "All components complete. Eligible codes: G0439, G0444" with documentation requirements 5\. Any unchecked components at visit end show a reminder before you close the chart |
| :---- |

### **Feature 16c: Prolonged Service Time Calculator**

Automatically detects when your time supports a prolonged service add-on.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Integrate prolonged service detection with the timer: 1\. When a session ends, if the documented time exceeds the maximum time for the selected E\&M level by 15+ minutes, show an alert: "Time qualifies for prolonged service add-on code 99417\. Each additional 15 minutes \= one unit." 2\. Show: "Your total time: 65 min. 99214 maximum: 39 min. Excess: 26 min \= 1 unit of 99417 (\~$XX additional)" 3\. Required documentation language pre-generated: "Total time spent on this encounter: \[X\] minutes, including \[time components\]." |
| :---- |

## **FEATURE 17: Coding Suggester**

Your personal ICD-10 and CPT lookup table, built around your own charting patterns. Grows more accurate as you use and annotate it.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Coding Suggester utility.   routes/tools.py \- Add: \- GET /tools/coding \- Coding suggester page \- GET /tools/coding/api/suggest?q=\<query\> \- AJAX search endpoint returning JSON \- POST /tools/coding/add-favorite \- Add a code to favorites \- POST /tools/coding/pair \- Record a code pairing (two codes used together)   templates/coding.html: \- Search field (searches both diagnosis text and code number) \- Results show: ICD-10 code, full description, specificity indicator, favorite button \- Pairing suggestions section below results \- Favorites list in sidebar   Seed the database with the ICD-10 codes most commonly used in primary care (top 200 diagnosis codes in outpatient settings)   AutoHotkey integration (coding\_popup.ahk): \- Hotkey Win+C opens /tools/coding as a small popup window \- Search field is auto-focused |
| :---- |

### **Feature 17b: ICD-10 Specificity Reminder**

Nudges you toward more specific codes when an unspecified one is selected.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add specificity guidance: 1\. When a user selects an unspecified code (codes ending in .9 or containing "unspecified"), check if more specific child codes exist 2\. If yes, show an inline suggestion: "More specific codes are available: \[list top 3\]" 3\. A "Why does this matter?" tooltip explains: more specific coding supports medical necessity and affects quality metrics 4\. Track the user's choice â€” if they consistently pick the specific code, stop suggesting (they've already learned it) |
| :---- |

### **Feature 17c: Code Pairing Suggestions**

Suggests secondary diagnoses that commonly appear together.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add diagnosis pairing intelligence: 1\. When the user selects a code, check the CodePairing table for codes that have been paired with it historically 2\. Show: "Commonly paired with: \[code\] \[description\]" with a one-click add button 3\. Pairing data comes from both your own history and from a seeded table of common clinical pairings (e.g., HTN \+ CKD, DM2 \+ neuropathy, hypothyroidism \+ depression) 4\. Each time a user saves two codes on the same day's coding session, record the pairing to refine future suggestions |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: The Care Gap Tracker shows age/sex appropriate gaps for test patients Marking a gap as addressed generates the documentation snippet The panel gap report shows coverage percentages AWV billing add-ons show when an AWV is on the schedule The coding suggester search returns relevant ICD-10 codes The specificity reminder appears for unspecified codes The coding popup opens via hotkey |
| :---- |

| PHASE 6: Communication Tools | \~10-14 hours |
| :---- | :---: |

## **FEATURE 18: Delayed Message Sender**

Compose patient portal messages or internal messages now and schedule them to send at a future time. This supports work-life boundary â€” you can write messages Sunday night without having them arrive at 11 PM.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Delayed Message Sender module.   routes/message.py: \- GET /messages \- Queue view showing all pending and sent messages \- GET /messages/new \- Compose form \- POST /messages/new \- Save to queue \- POST /messages/\<id\>/edit \- Edit pending message \- POST /messages/\<id\>/cancel \- Cancel pending message \- POST /messages/\<id\>/send-now \- Override schedule and send immediately   templates/messages.html: \- Two tabs: Pending Queue and Sent History \- Pending queue sorted by scheduled\_send\_at \- Each pending item: recipient identifier, message preview (truncated), scheduled time, edit/cancel/send-now buttons \- Status badge: Pending (yellow), Sent (green), Failed (red)   templates/messages\_compose.html: \- Recipient identifier field \- Message body (text area) \- Schedule datetime picker (defaults to next business day 9 AM) \- Recurring toggle: if enabled, interval selector (weekly/monthly) \- Preview button shows formatted message   Sending mechanism (agent/message\_sender.py): \- APScheduler job checks the message queue every 5 minutes \- For each message past its scheduled\_send\_at with status=pending:   a. Open NetPractice via Playwright   b. Navigate to the patient messaging section   c. Find the recipient   d. Compose and send the message   e. Update status to sent/failed   f. Send push notification confirmation or failure alert NOTE: The exact Playwright selectors for NetPractice messaging will need to be filled in once you provide screenshots of the interface. |
| :---- |

## **FEATURE 19: Abnormal Result Response Templates**

Pre-written, medically defensible communication templates for notifying patients of abnormal results, organized by urgency tier.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add result communication templates to the message composer.   Create a ResultTemplate model and seeded data for these tiers: TIER 1 \- Reassuring Normal Variant: "Your recent \[lab\] result was reviewed. The result is within a normal variation and requires no change to your current plan..." TIER 2 \- Mildly Abnormal, Lifestyle: "Your recent \[lab\] result shows a mildly elevated level. I recommend the following lifestyle changes..." TIER 3 \- Abnormal, Medication Adjustment: "Your recent \[lab\] result requires a change to your medications. I am \[adjusting/starting\] \[medication\]. Please \[fill/pick up\]..." TIER 4 \- Abnormal, In-Person Follow-Up: "Your recent \[lab\] result requires follow-up. Please call the office to schedule an appointment within \[timeframe\]..." TIER 5 \- Urgent: "Your recent \[lab\] result requires prompt attention. Please call the office today at \[number\]..."   In the message composer, add a "Use Template" button that opens a template picker. After selecting a tier and result type, the template fills the message body with \[bracketed\] fields highlighted for editing. Clear visual warning on Tier 4-5 templates: "This template is for results requiring action â€” verify recipient before sending." |
| :---- |

## **FEATURE 20: End-of-Day Pending Checker**

A scheduled check before end of business that surfaces anything requiring your attention before leaving.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the End-of-Day Checker as a scheduled agent job.   agent/eod\_checker.py: A function run\_eod\_check(user\_id) that: 1\. Checks for unsigned notes in Amazing Charts (via OCR scan of the notes section) 2\. Checks for unreviewed inbox items (from the last InboxSnapshot) 3\. Checks for overdue tickler items 4\. Checks for on-call notes still marked as pending documentation 5\. Checks for any messages in the delayed queue that will send tonight 6\. Compiles a summary and sends a push notification and/or desktop notification   The notification format: "End of Day Check \- \[TIME\] â€¢ Unsigned notes: X â€¢ Unreviewed inbox items: X â€¢ Overdue follow-ups: X â€¢ Pending on-call documentation: X All clear: YES / ACTION NEEDED"   A GET /tools/eod route shows the same information as a web page. Schedule this job at a user-configurable time (default 4:45 PM on workdays). |
| :---- |

### **Feature 20a: Unsigned Note Counter**

Specifically flags compliance risk from unsigned notes.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: In the EOD checker, prioritize unsigned note detection: 1\. The unsigned note check navigates to Amazing Charts' note management section 2\. Uses OCR to count notes marked as unsigned or pending 3\. If any unsigned notes exist, the push notification uses priority=1 (high priority, bypasses quiet hours) 4\. The EOD web page highlights unsigned notes in red at the top of the list 5\. A reminder fires again 30 minutes before clinic closing if notes remain unsigned |
| :---- |

### **Feature 20c: Configurable Checklist**

Each provider customizes their own end-of-day checklist.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add EOD checklist configuration: 1\. In user settings, a /settings/eod-checklist page with toggles for each check type 2\. Add custom check items (free text) that appear as manual reminders 3\. The EOD notification only includes items the user has enabled 4\. A "Send EOD Now" button for testing the configuration |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: The message queue shows pending messages with scheduled times Editing and cancelling pending messages works Result response templates appear in the message composer The EOD check runs at the scheduled time and sends a push notification Unsigned notes show correctly in the EOD result The EOD web page matches the push notification content |
| :---- |

| PHASE 7: Notifications & Utilities | \~14-18 hours |
| :---- | :---: |

## **FEATURE 21: Push Notification System**

The notification infrastructure used by every other module. Build this early so all future features can use it immediately.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the centralized notification system.   agent/notifier.py: class Notifier:     def send(self, user\_id, title, message, priority=0, sound='pushover', url=None)     def send\_critical(self, user\_id, title, message)  \# priority=2, bypasses quiet hours     def send\_to\_all(self, title, message)  \# sends to all active users   Pushover priority levels: \- \-2: No notification (lowest priority)   \- \-1: Quiet notification (no sound) \-  0: Normal \-  1: High priority (bypasses quiet hours) \-  2: Emergency (requires acknowledgment, retries every 30s for 1 hour)   The notifier checks user preferences before sending: \- Is Pushover enabled for this user? \- Is it within their quiet hours? \- Is this notification type enabled for this user? \- If quiet hours and priority \< 1: skip the notification (but log it as suppressed)   routes/tools.py \- Add: \- GET /notifications \- Notification history page \- POST /notifications/\<id\>/acknowledge \- Mark as acknowledged \- GET /settings/notifications \- Notification preferences page (already partially built in Feature 1d)   Log every notification attempt to a Notifications table with: user\_id, timestamp, type, message\_preview (first 50 chars, no PHI), priority, delivered (bool), suppressed\_reason |
| :---- |

## **FEATURE 22: Morning Briefing**

A scheduled daily summary of everything you need to know before arriving at work. Delivered to your phone and available as a web page.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Morning Briefing system.   agent/morning\_briefing.py: A function generate\_morning\_briefing(user\_id) that compiles: 1\. Today's schedule summary (from Schedule table): total patients, visit type breakdown, new patients, estimated end time 2\. Care gaps flagged for today's patients (count and types) 3\. Inbox status: items since yesterday, any critical flags 4\. On-call notes from last night pending documentation 5\. Overdue lab tracking items for today's patients 6\. Overdue tickler items 7\. Today's weather summary (use a free weather API with the clinic's ZIP code from config) 8\. One-line motivational note (rotate through a small list of clinical career quotes)   The briefing is sent as a Pushover notification with URL linking to the full web version. Full web version at GET /briefing/today shows all sections with more detail.   Scheduling: \- Default 6:30 AM on weekdays \- User-configurable time in notification preferences \- An on-demand "Send Briefing Now" button in the settings page for testing |
| :---- |

### **Feature 22a: Commute Mode**

Text-to-speech version of the briefing for hands-free review while driving.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add commute mode: 1\. GET /briefing/commute \- A page optimized for text-to-speech 2\. Uses the browser's Web Speech API (SpeechSynthesis) to read the briefing aloud 3\. Auto-plays when the page loads (with a play/pause button) 4\. Reads in a logical conversational order: "Good morning. You have 14 patients today. Three are new patients. Your first appointment is at 8 AM..." 5\. An "Add to Home Screen" prompt guides mobile users to add this as a shortcut for easy pre-commute access |
| :---- |

## **FEATURE 23: AutoHotkey Macro Library**

Text expansion hotkeys for Amazing Charts. Type a short code and it expands to a full template. Works inside Amazing Charts independently of the CareCompanion web server.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the AutoHotkey macro system with CareCompanion integration.   Part 1 \- macros/np\_companion.ahk (the AutoHotkey script): Create a comprehensive AutoHotkey v2 script that: 1\. Defines hotkey expansions for common clinical text (examples below) 2\. Reads macro definitions from a JSON file (macros/macros.json) so they can be edited in CareCompanion without touching the .ahk file 3\. Hotkeys:    ;;ros â†’ Full 10-system Review of Systems template    ;;penorm â†’ Physical exam within normal limits template    ;;f/u â†’ Standard follow-up instructions    ;;noshow â†’ No-show note template    ;;ref â†’ Referral order template    ;;htn â†’ HTN counseling boilerplate    ;;dm â†’ DM2 education documentation    ;;ama â†’ Against Medical Advice template    Win+M â†’ Open medication reference popup    Win+C â†’ Open coding suggester popup    Win+O â†’ Open order set manager 4\. A system tray icon showing macro status (active/paused) 5\. A hotkey (Win+P) to pause/resume all macros   Part 2 \- CareCompanion macro management: routes/tools.py \- Add: \- GET /macros \- Macro library management page \- POST /macros/add \- Add new macro \- POST /macros/\<id\>/edit \- Edit macro \- POST /macros/\<id\>/delete \- Delete macro   The AutoHotkey script reloads macros.json automatically whenever it changes (file watcher). |
| :---- |

## **FEATURE 24: Follow-Up Tickler System**

A local database of pending follow-up items tied to patient identifiers. Surfaces due items in the morning briefing and Today View so nothing falls through the cracks.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Follow-Up Tickler module.   routes/tools.py \- Add: \- GET /tickler \- Tickler dashboard \- POST /tickler/add \- Add new tickler item \- POST /tickler/\<id\>/complete \- Mark as completed \- POST /tickler/\<id\>/snooze \- Snooze to a new date \- POST /tickler/\<id\>/assign \- Assign to MA   templates/tickler.html: \- Three columns: Overdue (red), Due Today (yellow), Upcoming (white) \- Each item: patient identifier, description, due date, priority badge, assigned to, complete/snooze/assign buttons \- Quick-add form at top: patient identifier \+ description \+ due date \+ priority dropdown \- AutoHotkey hotkey (Win+T) to open tickler as popup while in Amazing Charts |
| :---- |

## **FEATURE 25: Controlled Substance Tracker**

A private local registry of patients on controlled substances with fill dates, intervals, and PDMP reminders.

| ï¿½  RxNorm Enhancement: `getAllProperties` retrieves the DEA schedule classification for any medication by RXCUI. This allows automatic identification of controlled substances from a patient's medication list â€” when a Clinical Summary is parsed, any medication whose RxNorm properties include a DEA schedule (II-V) is automatically flagged and can be pre-populated into the CS tracker. No manual entry needed for existing patients. |
| :---- |

| ï¿½ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Controlled Substance Tracker utility.   routes/tools.py \- Add: \- GET /cs-tracker \- Controlled substance registry \- POST /cs-tracker/add \- Add a patient entry \- POST /cs-tracker/\<id\>/fill \- Record a new fill \- GET /cs-tracker/calculator \- Standalone refill date calculator   The tracker UI includes: \- Patient identifier, medication, dose, days supply, last fill date \- Auto-calculated: earliest refill date, days until earliest refill, days supply remaining \- PDMP check due date (configurable interval per patient, typically every 3-6 months) \- UDS due date (configurable interval per patient) \- Status badges: Available to fill (green), Too Early (red with days remaining), PDMP Due (yellow), UDS Due (yellow)   The refill date calculator at /cs-tracker/calculator: \- Standalone tool: input last fill date \+ days supply â†’ outputs earliest fill date \- Useful even without creating a tracked entry |
| :---- |

## **FEATURE 26: Prior Authorization Generator**

Pre-fills PA narratives from diagnosis and medication inputs. Shared PA template library captures what language actually gets approved.

| ï¿½  RxNorm Enhancement: `getNDCs` provides National Drug Code numbers needed on PA forms. `getGenericProduct` documents whether a generic alternative exists (many PAs require generic-first documentation). `getAllRelatedInfo` finds therapeutic alternatives in the same drug class â€” useful for documenting "failed first-line" requirements. The drug name autocomplete in the PA form uses `getDisplayTerms` for standardized medication selection. |
| :---- |

| ï¿½ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Prior Authorization Generator.   routes/tools.py \- Add: \- GET /pa \- PA generator \- POST /pa/generate \- Generate PA narrative \- GET /pa/history \- PA submission history \- POST /pa/history/add \- Log submitted PA \- POST /pa/history/\<id\>/update-status \- Update PA status \- GET /pa/appeal/\<id\> \- Generate appeal letter   templates/pa.html: \- Drug name input with autocomplete from common medications \- Diagnosis (ICD-10 code \+ description) \- Insurance payer (stored list, add new) \- Failed first-line treatments (add/remove dynamically) \- Clinical justification free text \- "Generate Narrative" button \- Result: formatted PA narrative in a text area (editable before copying) \- Copy to clipboard button \- "Save to History" button logs this PA attempt   PA History tab: \- Table: drug, payer, submission date, status (pending/approved/denied/appealed), notes \- Denied entries: "Generate Appeal" button \- Filter by drug, payer, status |
| :---- |

## **FEATURE 27: Referral Letter Generator**

Generates formatted referral letters for any specialty, pre-filled with relevant clinical details.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Referral Letter Generator.   routes/tools.py \- Add: \- GET /referral \- Referral letter generator   \- POST /referral/generate \- Generate referral text \- GET /referral/log \- Referral tracking log \- POST /referral/log/add \- Log new referral   templates/referral.html: \- Specialty dropdown (Cardiology, Orthopedics, GI, Dermatology, Endocrinology, Neurology, Urology, Pulmonology, Nephrology, Rheumatology, Psychiatry, Surgery, other) \- Reason for referral (text) \- Relevant history (text area) \- Key clinical findings (text area) \- Current medications (text area) \- Urgency (routine/urgent/emergent) \- "Generate Letter" button produces a formatted referral letter in your name \- Referral letter format: your name/credentials, date, "Dear \[Specialty\] Colleague, I am referring \[patient descriptor \- NOT name\] for evaluation of \[reason\]..." \- Copy button and "Log This Referral" button   Referral Log: \- Patient identifier, specialty, date, reason, consultation received (yes/no), follow-up date \- Overdue flag: referrals sent \> 6 weeks without a return note |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: AutoHotkey script starts and shows system tray icon ;;ros hotkey expands to full ROS template inside Amazing Charts Win+M opens medication reference popup The Tickler dashboard shows overdue/today/upcoming columns Adding and completing tickler items works correctly The CS tracker calculator correctly calculates refill dates PA generator produces a formatted narrative Referral letter generator produces a formatted letter |
| :---- |

| PHASE 8: Platform & Multi-User Features | \~10-12 hours |
| :---- | :---: |

## **FEATURE 28: Provider Onboarding Wizard**

A guided setup flow for new colleagues joining the platform. A new provider should go from zero to productive in under an hour.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Provider Onboarding Wizard.   GET /onboarding \- Multi-step wizard (use JavaScript step transitions, no page reloads between steps)   Step 1 \- Account Setup: \- Display name, role selection, PIN creation \- Pushover credentials (with test button that sends a test notification)   Step 2 \- Machine Calibration: \- Screen resolution detection (JavaScript window.screen) \- MRN capture region calibration tool:   \- Button: "Take Calibration Screenshot"   \- Agent takes screenshot, displays it in the browser   \- User clicks on the MRN text in the screenshot   \- System sets MRN\_CAPTURE\_REGION based on the click position plus a margin   \- Button: "Test OCR" \- reads the region and shows what it found   Step 3 \- NetPractice Connection: \- NetPractice URL entry \- Button: "Open NetPractice for Login" \- opens the browser session \- Status indicator: session valid / needs login \- Re-authentication instructions   Step 4 \- Import Starter Pack: \- Grid of colleagues' shared order sets, macros, and medication reference entries \- Checkbox each item to import \- "Skip \- I'll build my own" option   Step 5 \- Complete: \- Summary of what was configured \- Link to the documentation \- "Go to Dashboard" button |
| :---- |

## **FEATURE 29: Practice Admin View**

Aggregate read-only view for a supervising physician or office manager. No individual provider data exposed.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Practice Admin View at /admin/practice.   This page is accessible only to users with the 'admin' role. All metrics displayed are aggregate across all providers â€” no individual breakdown.   Sections: 1\. PRACTICE INBOX OVERVIEW: Total inbox items across all providers (sum), critical items flag, average inbox size 2\. CARE GAP COVERAGE: Practice-wide percentage of patients current on key screenings 3\. ON-CALL ACTIVITY: Total calls this week, pending documentation count 4\. SYSTEM HEALTH: Agent uptime across all workstations, last scraper run, last backup time 5\. USER MANAGEMENT QUICK ACCESS: Link to /admin/users   All numbers are totals or averages. No individual provider names appear on this page. A timestamp shows "Data as of: \[last updated\]" |
| :---- |

## **FEATURE 30: Offline Mode**

CareCompanion degrades gracefully when the work PC is unreachable. Core functions remain available from cached data.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Add offline mode capability to CareCompanion.   Client-side (main.js): 1\. Use the browser's fetch API to poll /api/health every 30 seconds 2\. If the request fails or returns an error, set a global offline flag 3\. Display a persistent yellow banner: "âš ï¸ Connection to CareCompanion server unavailable. Showing cached data." 4\. Disable buttons that require server interaction (order execution, sending messages)   Service Worker (static/js/service-worker.js): 1\. Cache the following for offline use: medication reference data, macros list, on-call note form (so new notes can be composed offline) 2\. Offline on-call notes are saved to IndexedDB (browser storage) 3\. When connection is restored, sync queued notes to the server automatically 4\. Cache the last known schedule so the Today View shows even without connection   Status indicators: \- Green dot: connected \- Yellow dot: degraded (some features unavailable)   \- Red dot: offline (cached data only) \- Each module that is unavailable offline shows a greyed-out "Unavailable offline" label |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: The onboarding wizard walks through all 5 steps without errors Calibration screenshot appears in the browser Clicking on the MRN in the screenshot correctly sets the capture region A new colleague account imported order sets successfully The /admin/practice page shows aggregate stats Disconnecting from the internet shows the offline banner Composing an on-call note while offline and reconnecting syncs the note |
| :---- |

| PHASE 9: Note Reformatter â€” The Final Feature | \~16-20 hours |
| :---- | :---: |

The Note Reformatter is the most complex single feature in CareCompanion. It reads prior providers' notes from Amazing Charts, extracts the clinical content, reorganizes it into your preferred documentation structure, and flags anything that couldn't be reliably templated for your manual review. The core safety principle is that information can never be silently lost â€” anything the system cannot confidently place into your template must be visible to you in a review queue.

## **FEATURE 31: Prior Note Reformatter**

### **How It Works â€” Step by Step**

Step 1 â€” Source Note Discovery: The reformatter searches the patient's chart in Amazing Charts for comprehensive notes (Annual Physical, Established Care, Annual Wellness Visit, Comprehensive H\&P) where a full health history was documented. These are the richest source notes because they contain the complete picture.

Step 2 â€” Note Extraction: Using OCR and/or Amazing Charts' own export/print functionality, the system captures the full text of the selected source note.

Step 3 â€” Section Parsing: A text parsing engine identifies and extracts content by section type â€” Chief Complaint, HPI, Past Medical History, Surgical History, Family History, Social History, Medications, Allergies, Review of Systems, Physical Exam, Assessment, Plan. This works on recognizable section headers and their content.

Step 4 â€” Content Classification: Each extracted piece of content is classified by type and routed to the correct location in your preferred template. Some content maps cleanly (a medication list is always a medication list). Other content â€” unusual diagnoses, unfamiliar medications, complex HPI narratives â€” is flagged for manual placement.

Step 5 â€” Template Filling: The classified content is inserted into your preferred note structure. Your template defines where each type of content belongs. The filled template is presented to you for review â€” nothing goes into Amazing Charts without your eyes on it.

Step 6 â€” Flagged Item Review: Any content that could not be reliably mapped to your template appears in a dedicated review section. These are grouped by category: unusual diagnoses, unknown medications, complex narrative content, and items the parser could not categorize. You review each one and decide: add to template section, keep as free text, or discard.

| âš ï¸  Critical Safety Requirement: This feature works on clinical documentation. The system MUST flag and present for review any item it cannot confidently classify. There is no acceptable scenario where clinical information is discarded without your explicit confirmation. The flagged review queue is non-optional â€” the reformatted note cannot be saved until all flagged items have been reviewed and dispositioned. |
| :---- |

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the Note Reformatter module for CareCompanion.   This is a multi-step system. Build in this order:   STEP 1 \- Note capture (agent/note\_reader.py): Function capture\_note\_text(note\_type\_keywords): 1\. In Amazing Charts, navigate to the Notes section of the current patient chart 2\. Search for the most recent note matching keywords: 'Annual Physical', 'Annual Wellness', 'Comprehensive', 'New Patient', 'Established Care' 3\. Open the note 4\. Use Amazing Charts' print function to generate a printable/copyable version (this gives cleaner OCR than screenshotting the editor) 5\. OCR the printed/exported text 6\. Return the raw text   STEP 2 \- Section parser (agent/note\_parser.py): Function parse\_note\_sections(raw\_text): Uses pattern matching to identify section boundaries by looking for common header patterns: \- "Chief Complaint:", "CC:", "Reason for Visit:" \- "History of Present Illness:", "HPI:" \- "Past Medical History:", "PMH:", "Medical History:" \- "Past Surgical History:", "PSH:", "Surgical History:" \- "Family History:", "FH:" \- "Social History:", "SH:" \- "Medications:", "Current Medications:", "Med List:" \- "Allergies:", "Drug Allergies:" \- "Review of Systems:", "ROS:" \- "Physical Examination:", "Physical Exam:", "PE:", "Vitals:" \- "Assessment:", "Impression:", "Diagnosis:" \- "Plan:", "Assessment and Plan:", "A/P:" \- "Follow-up:", "Return:"   Returns a dict: {section\_name: section\_content} for each identified section. IMPORTANT: Any text between identified sections that doesn't fit a known header goes into a 'unclassified\_text' key. Any section that is unusually short (\< 5 words) goes into 'needs\_review'.   STEP 3 \- Content classifier (agent/note\_classifier.py): Function classify\_content(parsed\_sections): For each section, further classify the content: \- MEDICATIONS: Parse into a list of individual medication entries. Flag any medication not in a standard drug database (use a local list of \~2000 common medications as baseline). Flag any dosing language that is unusual or complex. \- DIAGNOSES (PMH/Assessment): Parse into individual diagnosis entries. Flag any diagnosis that contains unusual terminology, appears to be a rare condition, or cannot be matched to an ICD-10 code in your local reference. \- ALLERGIES: Parse into allergy \+ reaction pairs. Flag any that don't fit the standard allergen \+ reaction format. \- ROS: Identify each system reviewed and whether it was positive or negative. Flag any positive findings noted. \- PHYSICAL EXAM: Identify each body system and its findings. Flag any abnormal findings. \- NARRATIVE TEXT (HPI, Social History, Family History): These are harder to parse. Extract them as blocks. Flag entire sections if they contain unusual clinical language, specific numbers, or complexity indicators.   Returns: {section: {classified\_items: \[...\], flagged\_items: \[...\]}}   STEP 4 \- Template engine (agent/note\_reformatter.py): Function build\_reformatted\_note(classified\_content, user\_template): 1\. Load the user's preferred note template from the database 2\. Map classified content to template sections 3\. Build the filled template text 4\. Collect all flagged items into a review list 5\. Return: {filled\_template\_text, flagged\_items\_list, template\_coverage\_percentage}   STEP 5 \- UI (routes/reformatter.py \+ templates/reformatter.html): A multi-step wizard:   Page 1 \- Source Selection: \- Shows the patient's available comprehensive notes (from Amazing Charts search) \- Each note: date, type, author \- User selects which note to use as source   Page 2 \- Processing: \- Progress bar while extraction and parsing runs \- Shows: "Extracting text... Parsing sections... Classifying content... Building template..."   Page 3 \- Review Flagged Items (MANDATORY if any flags exist): \- Left panel: the flagged items list \- Right panel: your preferred template with filled sections highlighted in blue \- Each flagged item has:   \- The flagged text   \- Why it was flagged (e.g., "Medication not in standard reference", "Unusual diagnosis term", "Unclassified text")   \- Action buttons: \[Add to Section â–¼\] dropdown, \[Keep as Free Text\], \[Discard\]   \- "Discard" requires typing "DISCARD" to confirm and logs the discarded item permanently \- A progress tracker: "X of Y flagged items reviewed" \- The Next button is DISABLED until all flagged items are dispositioned   Page 4 \- Final Review: \- Full formatted note text in an editable text area \- Side-by-side view: original sections on left, reformatted result on right \- "Edit" button switches to editable mode \- "Copy to Clipboard" button \- "Mark as Complete" button logs the reformat in the ReformatLog table   SAFEGUARDS to implement: 1\. Every reformat session is logged: source note date, source author, processing timestamp, user who ran it, template coverage %, flagged item count, discarded item count, discarded item log 2\. Discarded items are permanently logged â€” they can never be truly deleted from the audit trail 3\. The filled template cannot be marked final if any flagged items remain in 'unreviewed' status 4\. If the parser cannot extract any structured sections (e.g., the note is completely free-text with no headers), the system shows a warning: "This note has no identifiable section structure. Full manual review required." and presents the entire note as one flagged item. 5\. A "Safe Mode" option processes only sections with \> 90% confidence; everything else goes to flags |
| :---- |

### **Sub-Feature: User Template Builder**

Before the reformatter can work, you define your preferred note structure.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Create the user template builder at /reformatter/template:   Users define their preferred note structure by: 1\. Selecting which sections to include (from a standard list) 2\. Setting the order of sections (drag-and-drop) 3\. For each section, setting: a default header label, any boilerplate text to always include, whether the section is required or optional 4\. A preview shows what a note built with this template looks like 5\. Templates can be shared with colleagues   The template is stored as JSON in the UserTemplate model. The reformatter loads this template for the active user. |
| :---- |

### **Sub-Feature: Medication Flagging Reference**

A locally-stored reference of common medications for the classifier.

| ï¿½  RxNorm Enhancement: Instead of maintaining a static list of 500 medications, the `CommonMedication` table can be seeded from the RxNorm API using `getAllConceptsByTTY` (term types SCD for clinical drugs, SBD for branded drugs). Fuzzy matching uses `getApproximateMatch` for medications that don't exactly match â€” this is far more accurate than local string matching because it accounts for abbreviations, salt forms, and dosage variations that RxNorm already knows about. Medications flagged repeatedly can be resolved via `findRxcuiByString` and added to the local cache permanently. |
| :---- |

| ï¿½ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Build the medication reference for the classifier: 1\. Create a local SQLite table: CommonMedication (generic\_name, brand\_names, drug\_class, typical\_doses) 2\. Seed with the top 500 most prescribed medications in primary care 3\. The classifier matches extracted medications against this list using fuzzy string matching (allow for spelling variations and abbreviations) 4\. Medications with \< 80% fuzzy match confidence are flagged 5\. An admin page lets you add medications to the reference that get flagged repeatedly |
| :---- |

### **Sub-Feature: Diagnosis Flagging Reference**

Maps common diagnoses to ICD-10 codes for classification confidence.

| ðŸ’¬  AI PROMPT â€” Copy this into Claude in VS Code: Build the diagnosis classifier reference: 1\. Create a local SQLite table: CommonDiagnosis (common\_name, synonyms, icd10\_code, is\_common\_primary\_care) 2\. Seed with the top 200 diagnoses in primary care 3\. Diagnoses that don't match (fuzzy \< 75%) are flagged 4\. Diagnoses that match but have is\_common\_primary\_care=False are flagged with a lower severity (yellow vs red) 5\. Rare disease terms trigger red flags with note: "Unusual diagnosis \- verify content before finalizing" |
| :---- |

| âœ…  CHECKPOINT â€” Test Before Moving On: The reformatter can extract text from a note in Amazing Charts The parser correctly identifies sections with standard headers Medications in the standard reference are classified without flags An unusual medication name is flagged for review The flagged items review page shows flagged content with action buttons The Next button is disabled until all flags are resolved Discarding an item requires confirmation and logs permanently The final review shows the complete reformatted note The ReformatLog table records each session A note with no section headers triggers the full-manual-review warning |
| :---- |

| PHASE 10A: Intelligence Layer â€” API-Powered Clinical Enrichment | \~20-24 hours |
| :---- | :---: |

Phase 10A adds a new layer of intelligence by combining data from free government APIs (NIH, FDA, CMS) with patient clinical data. These features enrich the existing patient chart, lab tracker, care gap engine, and medication reference with context that no EHR provides natively. All API integration follows the architecture documented in **`Documents/API_Integration_Plan.md`**.

| â„¹ï¸  API Foundation: Before building Phase 10A features, all Tier 1 cache tables must exist and the `utils/api_client.py` helper with the `get_cached_or_fetch()` pattern must be working. This is done in Phase 0.3 (CL23 pre-beta). The `RxNormCache`, `RxClassCache`, `FdaLabelCache`, `FaersCache`, `RecallCache`, `LoincCache`, `UmlsCache`, `HealthFinderCache`, `NlmConditionsCache`, `PubmedCache`, and `MedlinePlusCache` tables follow the existing `Icd10Cache` model pattern. See API_Integration_Plan.md Section 8 for the full schema. |
| :---- |

## **FEATURE NEW-A: Drug Recall Alert System**

Checks all patient medications against the FDA's active recall database daily. Surfaces recall alerts in the morning briefing, patient chart, and via push notification for Class I recalls.

**Dependencies:** OpenFDA Recalls API, RxNorm API, Pushover (F21), Morning Briefing (F22)

**Logic flow:**
1. Daily at 5:45 AM â€” query all unique RXCUI values across the patient medication database
2. For each drug: query OpenFDA Recalls for `status=Ongoing` matched against RXCUI
3. New matches create a `RecallAlert` record in database
4. Morning briefing: "FDA Recalls affecting patients: [N] â€” review list"
5. Patient Chart: red badge on Medications tab for affected patients
6. Provider action: one-click draft notification using recall template

## **FEATURE NEW-B: Abnormal Lab Interpretation Assistant**

When a lab result is outside range, cross-references the patient's medications against FDA label monitoring requirements to provide clinical context.

**Dependencies:** LOINC API, OpenFDA Labels API, RxNorm API, Lab Tracker (F11)

**Logic flow:**
1. On new lab result import from XML â€” check against LOINC reference range AND provider's custom threshold
2. If outside range: query patient's medication list, check each drug's FDA label for monitoring parameters
3. Generate contextual text: "[Lab] is [direction] â€” patient is on [drug] which [context]. Consider: [action]."
4. Display as collapsible "Clinical Context" section below the lab trend chart

## **FEATURE NEW-C: PubMed Guideline Lookup Panel**

A sidebar widget in the Patient Chart View that pre-loads recent clinical guidelines for the patient's top diagnoses.

**Dependencies:** NCBI E-utilities (PubMed API), Patient Chart View (F10e)

**Logic flow:**
1. When chart opens â€” identify top 3 active diagnoses (by encounter recency)
2. PubMed search: type=guideline|systematic review, last 3 years, high-impact journals
3. Cache per diagnosis for 30 days
4. Display as stacked cards: title + journal + year + abstract excerpt + DOI link
5. Per-provider: journal filter, article types, date range (2/3/5 years)

## **FEATURE NEW-D: Formulary Gap Detection**

Flags when a patient has a chronic diagnosis but no medication from the expected drug class for that condition.

**Dependencies:** RxClass API, ICD-10 API, Clinical Summary XML

**Logic flow:**
1. For each active diagnosis â†’ RxClass returns expected drug classes
2. Check patient med list for any medication in each expected class
3. If none found for chronic condition with >1 encounter â†’ flag as gap
4. Display: "No [drug class] found for [diagnosis] â€” verify treatment plan"
5. Dismissible with note (e.g., "managed with lifestyle modification") â€” does not re-appear

## **FEATURE NEW-E: Patient Education Auto-Draft**

Auto-populates patient message drafts with MedlinePlus educational content when care gaps are addressed or new medications are detected.

**Dependencies:** MedlinePlus Connect API, ICD-10 API, Delayed Message Sender (F18)

**Triggers:**
- Care gap addressed â†’ MedlinePlus content for that topic â†’ draft message in queue
- New medication detected in pre-visit prep â†’ MedlinePlus drug info â†’ draft message

Language preference (English/Spanish) per provider. All drafts require provider approval before sending.

## **FEATURE NEW-F: Drug Safety Panel**

A dedicated panel in the Patient Chart View aggregating all active drug safety signals for a patient.

**Dependencies:** RxNorm API, OpenFDA Labels API, OpenFDA Recalls API

**Display sections:**
- **Interactions** â€” from FDA label `drug_interactions` field, cross-referencing full med list
- **Recalls** â€” from OpenFDA Recalls matching patient's current medications
- **Monitoring Due** â€” from FDA label monitoring requirements + Lab Tracker dates

Each item has a "Document Reviewed" button â†’ audit trail entry for liability documentation.

## **FEATURE NEW-G: Differential Diagnosis Widget**

Collapsed by default in the Prepped Note tab, below Chief Complaint. Shows related conditions to consider.

**Dependencies:** ICD-10 API, UMLS API (âœ… licensed 2026-03-19), NLM Conditions API, SNOMED CT (via UMLS)

**Display sections:**
- **High Consideration** â€” conditions already in assessment
- **New Differentials** â€” from NLM Conditions API queried against chief complaint
- **Red Flags** â€” hardcoded per chief complaint category (chest pain, dyspnea, headache, etc.). These are prompts to consider, not diagnoses, and are always appropriate.

| âš ï¸  Clinical framing: The differential widget is labeled "Clinical Reference Only" â€” it does not diagnose. Red flags are hardcoded safety prompts, not API-derived, and are never wrong because they prompt consideration. All API-derived suggestions are labeled "NLM Clinical Conditions" with source attribution. |
| :---- |

| âœ…  CHECKPOINT â€” Phase 10A: All cache tables exist and migration has been run. The `api_client.py` helper works with `get_cached_or_fetch()`. Drug Recall Alert runs daily and flags affected patients in patient chart. Abnormal Lab context appears below lab trend charts when relevant. PubMed guidelines load in sidebar when opening patient chart. Formulary gap flags appear for untreated chronic conditions. Patient education drafts appear in message queue after care gap closure. Drug Safety Panel shows interactions, recalls, and monitoring due. Differential widget shows conditions relevant to chief complaint. Offline mode: all features degrade gracefully to cached/hardcoded data. |
| :---- |

| PHASE 10B: Billing Intelligence Layer â€” Revenue Opportunity Engine | \~16-20 hours |
| :---- | :---: |

Phase 10B adds a Proactive Billing Opportunity Engine that cross-references patient data against Medicare/Medicaid billing rules to surface revenue opportunities that would otherwise be missed. Full specification in **`Documents/API_Integration_Plan.md`** Sections 12-15.

| âš ï¸  Compliance: Every billing opportunity display must include "estimate" or "approximate" before dollar figures. The system never suggests billing for unrendered services. All billing decisions remain with the licensed provider. CCM/APCM require documented patient consent before the system marks them as billable. |
| :---- |

## **FEATURE: Billing Opportunity Engine**

**New models:** `BillingOpportunity` (per-visit opportunity tracking) and `BillingRuleCache` (annual CMS fee schedule data).

**Billing rule categories:**

| # | Category | Key Codes | Detection |
|---|----------|-----------|-----------|
| 1 | Chronic Care Management (CCM) | 99490, 99439, 99491, 99437 | â‰¥2 chronic conditions in problem list |
| 2 | Annual Wellness Visit (AWV) | G0402, G0438, G0439 + add-ons | AWV history + 12-month interval |
| 3 | E&M Complexity Add-On | G2211 | Established patient + serious condition |
| 4 | Transitional Care Management (TCM) | 99495, 99496 | Hospital discharge in inbox |
| 5 | Prolonged Service | 99417 | Timer exceeds E&M level max time |
| 6 | Behavioral Health Integration | 99484 | Behavioral health dx + active management |
| 7 | Remote Patient Monitoring | 99453-99458 | Qualifying condition + device program |

**Pre-visit workflow:** For each scheduled patient, the engine calculates eligible billing opportunities overnight and displays them as a collapsible "Billing Opportunities" card in the Today View with confidence levels (HIGH/MEDIUM), estimated revenue, and documentation requirements.

**Post-visit workflow:** After the visit, the Billing Capture section shows which opportunities were acted on vs. missed, with cumulative "opportunity gap" data feeding the Metrics dashboard (F13).

**Insurer intelligence:** Payer classified from Clinical Summary XML demographics (Medicare FFS / MA / Medicaid / Commercial). Payment estimates adjusted by payer factor (`commercial_payer_rate_factor`, `medicaid_rate_factor`).

**New routes:** `/settings/billing` (provider preferences), `/admin/billing` (practice-wide billing config, PFS locality, rate factors)

**Annual maintenance:** Billing rules are CMS policy â€” hard-coded, not API-driven. System generates admin reminder on November 1 to review and update rules when CMS publishes the new PFS Final Rule.

| âœ…  CHECKPOINT â€” Phase 10B: `BillingOpportunity` and `BillingRuleCache` tables exist. CMS PFS data loaded for current year. Pre-visit billing cards appear in Today View with estimated revenue. CCM eligibility flags for patients with â‰¥2 chronic conditions. AWV sequence logic correctly identifies G0402/G0438/G0439. G2211 add-on reminder appears for established patient visits. TCM window opens on hospital discharge detection (with priority push notification). Post-visit billing review shows captured vs. missed opportunities. `/settings/billing` and `/admin/billing` pages functional. Revenue estimates labeled "approximate" with payer caveats. |
| :---- |

# **Section 6: Deploying to Your Work PC**

Once a phase is complete and working on your personal computer, follow these steps to deploy it to your work PC. You will do this incrementally â€” deploy after each phase, not at the very end.

## **6.1  Setting Up Git for Deployment**

Git is how you move code from your development machine to the work PC. Think of it as a controlled copy-paste that tracks exactly what changed.

52. On your personal computer, in VS Code terminal (with venv active), run:

| cd carecompanion git init git add . git commit \-m "Initial project setup" |
| :---- |

53. Create a free private repository on GitHub (github.com). Name it carecompanion. Do NOT make it public.

54. Follow GitHub's instructions to connect your local repository to GitHub.

55. On your work PC, install Git for Windows, Python 3.11, and VS Code (same as Section 1).

56. On the work PC, open Command Prompt and run:

| git clone https://github.com/\[your-username\]/carecompanion |
| :---- |

## **6.2  Work PC Configuration**

The work PC needs its own config.py with work-PC-specific values â€” its own screen resolution, IP addresses, and paths.

57. Copy your config.py to the work PC (do this manually via USB drive or email â€” do NOT push config.py to GitHub).

58. Update the values in config.py for the work PC's screen resolution, Tailscale IP, and any paths.

59. Install Python libraries on the work PC:

| cd carecompanion python \-m venv venv .\\venv\\Scripts\\activate pip install \-r requirements.txt playwright install chromium |
| :---- |

## **6.3  Setting Up Auto-Start**

Both the web server and the background agent need to start automatically when the work PC boots.

60. Import agent\_startup.xml into Windows Task Scheduler:

| schtasks /create /xml agent\_startup.xml /tn "CareCompanion Agent" |
| :---- |

61. For the Flask web server, create a second Task Scheduler entry that runs:

| python app.py |
| :---- |

62. Set both tasks to: Trigger \= At log on, Run whether user is logged in or not (uncheck this â€” it needs the screen for OCR), Run with highest privileges.

63. Test by restarting the work PC and verifying CareCompanion is accessible at localhost:5000.

## **6.4  Update Workflow (After Each Phase)**

When you complete new features on your personal computer and want them on the work PC:

64. On personal computer: git add . && git commit \-m "Description of what changed" && git push

65. On work PC: git pull (this downloads your changes)

66. Restart the Flask server and agent on the work PC.

67. Test the new features.

# **Section 7: Outstanding Questions & Missing Information**

The following information is needed before specific features can be fully built or calibrated. Some of these can only be answered by using the software and observing its behavior. Provide screenshots or answers as you encounter each item and update your AI prompts accordingly.

## **7.1  Amazing Charts â€” Required Information**

### **MRN location and format**

âœ… **ANSWERED** â€” MRN is in the patient chart window title bar after `ID:`. Format is numeric, length varies. Use `win32gui.GetWindowText()` + regex `ID:\s*(\d+)`. No OCR required for MRN detection. The MRN is only visible when a patient chart window is open.

### **Inbox navigation**

âœ… **ANSWERED** â€” Inbox is in the right panel of the AC home screen â€” it is always visible, no keyboard shortcut needed to open it. The filter dropdown (second control in the inbox header row) has 7 exact options:
- Show Everything
- Show Charts
- Show Charts to Co-Sign
- Show Imports to Sign-Off
- Show Labs to Sign-Off
- Show Orders
- Show Patient Messages

Table columns: `From | Subject | Received`. Subject prefixes identify item type: `LAB:` for labs, `CHART:` for forwarded charts, `VIIS` for immunization imports.

### **Note creation keyboard shortcut**

âœ… **ANSWERED** â€” `F7` opens the Most Recent Encounter tab. The `Enlarge Textbox` button (in the toolbar row above Chief Complaint, to the left of the patient photo) opens the full-section editing window. `Update & Go to Next Field` button sequences through all 16 sections without closing the window.

### **Template selection interface**

âœ… **ANSWERED** â€” `Patient > Print > Notes & Letters` opens the Print Encounters dialog. Header dropdown has 9 options. Most recent encounter is pre-selected. `Save Section Template` and `Save as Visit Template` buttons are available in the Enlarge Textbox window for creating and applying templates.

### **Order entry interface**

Why it matters: How do you access orders for an open patient? What are the tab names in the order entry screen? How do you select an individual order â€” is it a checkbox, a button, a double-click?

| How to find it: Navigate to orders for a test patient and document every tab name and interaction method. |
| :---- |

### **Patient search behavior**

âœ… **ANSWERED** â€” Patient List panel on left side of the AC home screen. Type MRN in the `ID` column search field for fastest lookup. Search by Lastname/Firstname also available. Click patient row to open chart.

### **AC version and database location**

â³ **OPEN** â€” Confirm via Help > About Amazing Charts.

### **Amazing Charts process name**

â³ **OPEN** â€” Confirm via Task Manager (Ctrl+Shift+Esc â†’ Processes tab). Note the exact name in the Name column.

### **Screen resolution of work PC vs room computers**

Why it matters: Do the exam room computers have different screen resolutions than your main workstation? The MRN reader needs calibration per machine.

| How to find it: Check display settings on each computer (right-click desktop \> Display Settings). |
| :---- |

### **Print/export note capability**

âœ… **ANSWERED** â€” Two confirmed methods:
1. `Patient > Print > Notes & Letters` â†’ PDF (OCR fallback for narratives)
2. `Patient > Export Clinical Summary` â†’ XML (preferred, structured data)

XML file auto-named `ClinicalSummary_PatientId_[MRN]_[YYYYMMDD]_[HHMMSS].xml`. Export requires the AC home screen â€” all patient chart windows must be closed first.

## **7.2  NetPractice / WebPractice â€” Required Information**

### **Schedule page HTML structure**

Why it matters: What does the schedule page's HTML look like? The Playwright scraper needs to find patient names, appointment times, and visit types in the page source.

| How to find it: Open NetPractice in Chrome, right-click the schedule page, click Inspect, and screenshot the Elements panel showing the schedule rows. |
| :---- |

### **Patient messaging interface**

Why it matters: Where is patient messaging in NetPractice? Is it a separate section? What does the compose form look like?

| How to find it: Navigate to patient messaging and screenshot the compose form. |
| :---- |

### **Authentication sequence**

Why it matters: After entering the NetPractice URL, what exactly happens? Does it go to a NetPractice login page first, then redirect to Google, or directly to Google?

| How to find it: Log out of NetPractice and document every screen in the login sequence. |
| :---- |

### **Visit type labels**

Why it matters: What labels does NetPractice use for visit types? Exact text of the visit type names as they appear in the schedule.

| How to find it: Look at several different appointment types on the schedule and note the exact text used. |
| :---- |

### **New patient indicator**

Why it matters: How does NetPractice indicate a new patient on the schedule? Is it a label, an icon, a color, or a visit type name?

| How to find it: Find a new patient appointment on the schedule and note how it's visually distinguished. |
| :---- |

## **7.3  Splashtop â€” Required Information**

### **Remote session behavior**

Why it matters: When you connect to the work PC via Splashtop, does the work PC's screen stay the same as what you see remotely, or does it show a locked screen to anyone physically at the PC? This affects whether scripts can run visually while you are remoted in.

| How to find it: Connect via Splashtop and have someone check the physical work PC screen simultaneously. |
| :---- |

### **Resolution during remote session**

Why it matters: Does the screen resolution change when you connect via Splashtop? If so, the OCR region coordinates will be different during remote sessions.

| How to find it: Check your screen resolution in display settings both during and outside a Splashtop session. |
| :---- |

# **Section 8: Troubleshooting Common Problems**

When something doesn't work, use this section before asking Claude for help. Paste the exact error message into Claude along with the phrase "I am building CareCompanion. Here is the error:" â€” this gives Claude the context needed to help efficiently.

### **The Flask app doesn't start**

*Symptom: ModuleNotFoundError or similar*

**What to try:**

68. Make sure your virtual environment is activated (you should see (venv) in the terminal)

69. Run: pip install \-r requirements.txt

70. Make sure you are in the carecompanion folder when running python app.py

### **OCR reads the wrong text or nothing**

*Symptom: Empty string returned from Tesseract*

**What to try:**

71. Open the calibration tool and take a screenshot to verify the capture region is correct

72. The image may need preprocessing â€” increase contrast or scale before OCR

73. Tesseract may not be in your PATH â€” verify with: tesseract \--version in Command Prompt

74. The MRN text may be too small â€” increase the capture region size

### **PyAutoGUI clicks in the wrong place**

*Symptom: Automation hits wrong buttons or misses targets*

**What to try:**

75. Screen resolution may have changed â€” re-run calibration

76. Amazing Charts window may not be at the expected position â€” make sure it is maximized before running automation

77. Add time.sleep(0.5) between clicks to give Amazing Charts time to respond

### **Playwright can't log into NetPractice**

*Symptom: Page redirects to login or throws an error*

**What to try:**

78. Delete np\_session.pkl and log in manually again

79. Check that the NETPRACTICE\_URL in config.py is correct and includes https://

80. The session cookie may have expired â€” this happens every 2-4 weeks

### **Push notifications not arriving**

*Symptom: No notification on phone*

**What to try:**

81. Verify PUSHOVER\_USER\_KEY and PUSHOVER\_API\_TOKEN in config.py are correct

82. Check the Notifications log in CareCompanion â€” was the notification sent?

83. Check if quiet hours are blocking the notification

84. Send a test notification from the Pushover website directly to rule out the app

85. Check that the Pushover app has notification permission on your phone

### **Database errors on startup**

*Symptom: SQLAlchemy errors or OperationalError*

**What to try:**

86. Delete data/carecompanion.db and restart the app â€” this recreates all tables (you will lose any test data)

87. Make sure the data/ folder exists (create it manually if not)

88. Check for typos in model definitions if you edited any model files

### **Tailscale connection not working**

*Symptom: Can't access CareCompanion from phone*

**What to try:**

89. Both devices must be signed into the same Tailscale account

90. Tailscale must be running on both devices (check the system tray on the work PC)

91. Make sure the Flask app is running and bound to 0.0.0.0 (not 127.0.0.1)

92. Try pinging the work PC's Tailscale IP from your phone's browser

# **Section 9: Feature Tracking**

> **The detailed feature checklist has moved.** The authoritative Feature Registry now lives in:
>
> **`Documents/dev_guide/PROJECT_STATUS.md` â†’ `## Feature Registry`**
>
> That table tracks every feature's build status, test coverage, and user verification in one place.
> Update it there â€” not here â€” when features change status. See `.github/copilot-instructions.md` for maintenance rules.

---
## ADDENDUM: Feature F32 â€” Clinical Terminology Spell Check & Fuzzy Matcher

**Added:** 2026-03-18 (CL23 API Intelligence Build)
**Phase:** 10A (Intelligence Layer)
**Status:** Implemented

### Overview

Medical-aware spell checking and fuzzy matching for free text in clinical notes. Handles misspelled drug names, diagnoses, medical abbreviations, and clinical slang. Provider-approved corrections prevent silent errors while saving documentation time.

### How It Works

1. **Text Analysis** â€” When provider clicks "Check Terminology" in the Note Generator widget, all note section text is sent to the spell check service (no PHI leaves the system â€” only the text content).

2. **Multi-Layer Matching:**
   - **Layer 1 â€” Abbreviation Dictionary** (~200 entries): Exact-match medical abbreviations (HTNâ†’hypertension, DM2â†’type 2 diabetes mellitus, CTABâ†’clear to auscultation bilaterally, etc.)
   - **Layer 2 â€” Known Misspelling Dictionary** (~100 entries): Common clinical misspellings (lisiniprilâ†’lisinopril, hypothyriodismâ†’hypothyroidism, etc.)
   - **Layer 3 â€” Local Fuzzy Match**: Python `difflib.SequenceMatcher` against combined dictionaries (cutoff 0.75)
   - **Layer 4 â€” RxNorm API Fuzzy Match**: For unresolved 6+ character words that look clinical, queries RxNorm `getSpellingSuggestions` endpoint

3. **Confidence Scoring:**
   - **High (â‰¥85%)** â€” abbreviation exact matches, known misspelling matches â†’ auto-accept recommended
   - **Medium (60-85%)** â€” fuzzy matches â†’ flagged for provider review
   - **Below 60%** â€” filtered out to prevent false positives

4. **Provider Approval Workflow:**
   - Each finding shows: original word, suggested correction, confidence score, context, category
   - Provider clicks "Accept" to apply correction to note text, or "Ignore" to skip
   - Corrections are applied in-place to the note textarea content

### Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/spell-check` | POST | Analyze text, return findings with confidence scores |
| `/api/spell-check/expand` | POST | Expand a single abbreviation |

### Files

| File | Purpose |
|------|---------|
| `app/services/clinical_spell_check.py` | Core matching engine with dictionaries |
| `routes/intelligence.py` | API endpoints |
| `templates/patient_chart.html` | "Check Terminology" button + results UI in Note Generator widget |

### Dictionary Categories

| Category | Count | Examples |
|----------|-------|---------|
| Diagnosis abbreviations | ~70 | HTN, DM2, CHF, CKD, COPD, GERD, BPH, OSA |
| Clinical shorthand | ~50 | yo, hx, sx, tx, rx, dx, prn, bid, tid, qid |
| Physical exam terms | ~20 | WNL, NAD, CTAB, RRR, NTND, PERRLA, EOMI |
| Drug abbreviations | ~30 | ASA, APAP, NSAID, ACEI, ARB, CCB, SSRI, PPI |
| Lab abbreviations | ~30 | CBC, BMP, CMP, LFTs, TFTs, A1c, TSH, INR |
| Drug misspellings | ~50 | lisinipril, metforman, atorvistatin, gabapenton |
| Diagnosis misspellings | ~40 | hypertention, diabeties, hypothyriodism, nueropathy |

### Safety Notes

- No patient identifiers are included in the text analysis
- The spell check service runs locally â€” no text is sent to external APIs
- RxNorm fuzzy matching (Layer 4) sends only individual words, never patient context
- All corrections require explicit provider approval â€” no auto-correction without consent
- Abbreviation expansion is informational; original abbreviation is preserved if provider prefers


# CareCompanion — Feature Outline & Access Justification

**Prepared by:** Cory Denton, NP-C  
**Practice:** Family Practice Associates of Chesterfield, VA  
**Date:** March 19, 2026  
**Version:** 1.1.2 (Public Beta)  
**Audience:** Supervising Physician · Office Manager · IT Department

---

## Purpose of This Document

CareCompanion is a clinical workflow tool I have been developing to improve daily efficiency, patient safety, and revenue capture at the practice. It runs entirely on my workstation and integrates with Amazing Charts to automate repetitive charting and administrative tasks that the EHR does not support natively.

Recently, several of the tools and access required to run this project—Amazing Charts administrative features, terminal/command-line access, OCR software (Tesseract), and keyboard automation (PyAutoGUI/AHK)—were flagged by the IT monitoring systems. This document explains **what each tool does, why it is needed, and how the project is built to be safe and HIPAA-compliant.**

Dr. [Supervising Physician Name] has reviewed the concept and approved continued development. This document provides the detail needed for the office manager and IT department to understand the scope and grant the necessary access with confidence.

---

## Table of Contents

1. [What CareCompanion Does (Plain-Language Summary)](#1-what-carecompanion-does)
2. [Feature Overview](#2-feature-overview)
3. [Why These Tools Were Flagged — And Why They're Needed](#3-why-these-tools-were-flagged)
4. [Security & HIPAA Compliance](#4-security--hipaa-compliance)
5. [What IT Needs to Provision](#5-what-it-needs-to-provision)
6. [Estimated Practice Impact](#6-estimated-practice-impact)
7. [Frequently Asked Questions](#7-frequently-asked-questions)

---

## 1. What CareCompanion Does

Amazing Charts is our EHR, but it lacks built-in tools for:

- Alerting providers to **preventive care gaps** before a visit starts
- Detecting **missed billing opportunities** (CCM, AWV, TCM, G2211)
- Summarizing the **inbox** so I don't have to check it all day
- **Pre-loading chart data** (medications, diagnoses, labs) into a quick-view dashboard
- Tracking **lab follow-ups, ticklers, and on-call notes**
- Entering **order sets** without manually clicking through 20+ fields

CareCompanion fills those gaps. It is a locally-hosted web application (accessed at `localhost:5000` on my workstation only) with a background service that reads data from Amazing Charts, enriches it with clinical reference APIs, and displays it in a purpose-built dashboard.

**No patient data ever leaves the practice network.**

---

## 2. Feature Overview

### For the Supervising Physician

| Feature | What It Does | Clinical Value |
|---------|-------------|----------------|
| **Care Gap Engine** | Evaluates each patient against 30+ USPSTF 2024 guidelines (colonoscopy, mammography, A1C, lipids, immunizations, etc.) | Catches overdue screenings *before* the visit so they can be addressed in real time |
| **Medication Safety Monitoring** | Checks active medications against FDA recall databases and adverse event reports | Automated safety net — no manual recall checking needed |
| **Billing Opportunity Detection** | Flags CCM, AWV, TCM, G2211, 99417, BHI, and RPM eligibility per patient | Ensures the practice captures revenue for care that is already being provided |
| **Clinical Summary Pre-Load** | Parses Amazing Charts XML exports and displays meds, diagnoses, labs, vitals, allergies, and immunizations in a single view | Eliminates toggling between AC tabs; 5–10 min saved per visit on chart review |
| **Note Reformatter** | Parses free-text notes into Amazing Charts' 16 section format with medication/diagnosis flagging | Reduces documentation gaps and speeds up note entry |
| **Inbox Digest** | Monitors the AC inbox every 2 hours, categorizes items (labs, radiology, messages, refills), and sends a daily 5 PM summary via push notification | Reduces inbox anxiety; critical values bypass quiet hours immediately |

### For the Office Manager

| Feature | What It Does | Operational Value |
|---------|-------------|-------------------|
| **Schedule Briefing** | Reads today's appointments from NetPractice and displays with new-patient badges, duration estimates, and double-booking warnings | Better awareness of the day's flow; flags scheduling conflicts |
| **Billing Reports** | Monthly summary of detected billing opportunities vs. captured | Visibility into revenue that may be left on the table |
| **Time Tracking** | Per-encounter timer with visit-type tagging and pace analytics | Objective data on appointment throughput |
| **Lab Follow-Up Tracking** | Flags overdue lab results daily; categorizes by pending/received/overdue | Prevents patients from falling through the cracks |
| **Tickler Reminders** | Follow-up reminders (call patient, schedule test, refill Rx) with snooze/dismiss | No more sticky notes or forgotten callbacks |
| **On-Call Handoff** | Secure, time-limited shareable links for after-hours note handoff | Clean handoff documentation between covering providers |
| **Audit Trail** | Every action in the system is logged with timestamp, user, action, and IP | Built-in compliance and accountability |

### For IT

| Feature | Technical Footprint | Notes |
|---------|-------------------|-------|
| **Flask web server** | Runs on `localhost:5000` — no external-facing ports | Single-user, single-workstation |
| **Background agent** | System tray service on `localhost:5001` | Scheduled jobs (inbox polling, lab checks, digest, etc.) |
| **SQLite database** | Single file at `data/carecompanion.db` | No database server required |
| **Tesseract OCR** | Local installation, processes screenshots in-memory only | No disk writes of screenshots; no PHI in OCR logs |
| **Playwright (Chrome CDP)** | Connects to Chrome on `localhost:9222` for NetPractice schedule scraping | Local-only; no remote browsing |
| **Tailscale VPN** | Optional — used for provider's phone notifications when off-site | WireGuard-based; no firewall changes needed |

---

## 3. Why These Tools Were Flagged

### Amazing Charts Administrative Access

**What was flagged:** Accessing Amazing Charts with elevated user permissions.

**Why it's needed:** CareCompanion reads Clinical Summary XML exports from Amazing Charts. This is a built-in feature of the EHR (Patient → Export Clinical Summary). The export produces a standard FHIR CDA XML file that the application parses locally. No modifications are made to Amazing Charts data — this is strictly **read-only** interaction via the EHR's own export functionality.

**What it does NOT do:**
- Does not write to the Amazing Charts database
- Does not modify patient records
- Does not bypass any AC authentication
- Does not access other providers' data

---

### Terminal / Command-Line Access

**What was flagged:** Use of Windows command prompt or PowerShell.

**Why it's needed:** The CareCompanion application is a Python program. To start, stop, update, or troubleshoot it, basic terminal access is required:

| Command | Purpose |
|---------|---------|
| `python app.py` | Start the web application |
| `python agent_service.py` | Start the background service |
| `python build.py` | Package an update for deployment |
| `pip install -r requirements.txt` | Install Python dependencies |

These are standard development commands. No system administration, registry modification, or network reconfiguration is performed.

---

### Tesseract OCR (Optical Character Recognition)

**What was flagged:** Installation of Tesseract OCR software.

**Why it's needed:** Amazing Charts does not provide an API or any programmatic way to interact with its user interface. The only way to automate repetitive tasks (like reading inbox counts or navigating to a patient chart) is to **look at the screen the same way a human does** — by reading text.

Tesseract reads text from the Amazing Charts window in real-time to locate buttons, fields, and labels. This is the **industry-standard approach** for automating legacy desktop applications that lack APIs.

**How it works safely:**
- Screenshots are processed **entirely in memory** — never saved to disk
- Only UI label text is extracted (e.g., "Patient List", "Visit Template") — not clinical content
- No patient data is captured, stored, or transmitted via OCR
- The OCR engine runs locally — no cloud processing

**Why not just use screen coordinates?** Hardcoded coordinates break whenever the window moves, the resolution changes, or Amazing Charts updates. OCR-based element detection is more reliable and requires less maintenance.

---

### PyAutoGUI / AHK (Keyboard & Mouse Automation)

**What was flagged:** Installation/use of automation software (AutoHotKey or similar).

**Why it's needed:** CareCompanion uses PyAutoGUI (a Python library — not AHK) to automate repetitive data entry in Amazing Charts, specifically:

- **Order set entry:** Instead of manually clicking through 20+ fields to enter a standard order set, the automation fills in each field sequentially, saving 2–3 minutes per order set.
- **Chart navigation:** Typing a patient MRN into the search field and pressing Enter — the same keystrokes a human would perform, just faster and error-free.

**Built-in safety controls:**

| Safety Measure | Description |
|----------------|-------------|
| **Foreground check** | Automation will not proceed unless Amazing Charts is the active window — prevents typing into the wrong application |
| **PyAutoGUI failsafe** | Moving the mouse to any screen corner instantly aborts all automation |
| **Per-item state tracking** | Each automated action is logged in the database; if interrupted, it can resume safely |
| **Pre-execution screenshot** | A screenshot is captured before automation begins for debugging if something goes wrong |
| **No blind clicking** | If OCR cannot find the expected UI element, the automation stops — it does not guess |

---

## 4. Security & HIPAA Compliance

### Data Stays Local

```
┌─────────────────────────────────────────────────────┐
│             MY WORKSTATION (FPA-D-NP-DENTON)        │
│                                                     │
│  Amazing Charts  ──XML Export──▶  CareCompanion      │
│                                  (local processing) │
│                                       │             │
│                                  SQLite Database    │
│                                  (local file)       │
└─────────────────────────────────────────────────────┘
               │
               ▼ (outbound, non-PHI only)
  ┌──────────────────────────────┐
  │  NIH APIs (drug names,       │
  │  ICD-10 codes, lab codes)    │
  │  FDA APIs (recall checks)    │
  │  CMS Fee Schedule            │
  └──────────────────────────────┘
  
  ❌ No patient names, MRNs, DOBs, or any PHI sent externally
```

### Security Features Already Implemented

| Category | Measure |
|----------|---------|
| **Authentication** | Bcrypt-hashed passwords, Flask-Login sessions, role-based access (Admin / Provider / MA) |
| **PHI Protection** | MRNs stored as SHA-256 hashes in logs; only last 4 digits displayed in UI; full MRN used only for clinical accuracy |
| **Data Retention** | Clinical Summary XML files auto-deleted after 183 days (HIPAA minimum necessary standard) |
| **Encryption at Rest** | Compatible with Windows BitLocker full-disk encryption (recommended) |
| **Encryption in Transit** | All external API calls use HTTPS/TLS 1.2+; Tailscale uses WireGuard (ChaCha20-Poly1305) |
| **Audit Trail** | Every authenticated action logged: timestamp, user, action, module, IP address |
| **No Cloud Storage** | Zero cloud sync. Database is a single local file. |
| **No Telemetry** | No analytics, tracking, or data harvesting of any kind |
| **Dependency Pinning** | All 41 Python packages pinned to exact versions to prevent supply chain issues |

### What External APIs Receive

| API | Data Sent | PHI? |
|-----|-----------|------|
| NIH RxNorm | Drug names (e.g., "metformin 500mg") | No |
| NIH ICD-10 | Diagnosis codes (e.g., "E11.9") | No |
| FDA OpenFDA | Drug names for recall lookup | No |
| CMS Fee Schedule | CPT codes (e.g., "99490") | No |
| CDC Immunization | Age-based schedule queries | No |
| Pushover | Notification text (inbox summary counts — no patient names) | No |

---

## 5. What IT Needs to Provision

### One-Time Setup

| Item | Justification | Risk Level |
|------|---------------|------------|
| **Python 3.11 installed** on my workstation | Runtime for the application | Low — standard development tool |
| **Tesseract OCR installed** at a user-level path | Screen reading for Amazing Charts automation | Low — offline, local-only, no network activity |
| **Terminal access** (PowerShell or CMD) | Start/stop/update the application | Low — no admin commands; user-level only |
| **Chrome launched with** `--remote-debugging-port=9222` flag at startup | Allows the schedule scraper to read NetPractice appointments | Low — local-only; does not expose Chrome externally |
| **Windows Task Scheduler entry** for `Start_CareCompanion.bat` | Auto-start the background service on login | Low — runs under my user account |
| **Firewall exception** for `localhost:5000` and `localhost:5001` | Allow the local web interface and agent to communicate | Low — localhost only; no external ports opened |

### Ongoing

| Item | Frequency |
|------|-----------|
| No ongoing IT support needed | The application and all its dependencies are self-contained |
| Updates deployed via USB | I package updates on my development machine and deploy via USB — no network installation |
| No server infrastructure | No new servers, VMs, or cloud services |
| No network changes | No firewall rules, DNS changes, or Active Directory modifications beyond the items above |

---

## 6. Estimated Practice Impact

### Time Savings (Per Provider Per Day)

| Task | Without CareCompanion | With CareCompanion | Savings |
|------|---------------------|-------------------|---------|
| Pre-visit chart review | 5–10 min/patient × 20 patients | Automated or manual pre-load | **60–90 min/day** |
| Order set entry | 2–3 min/set × ~8 sets | Automated entry | **15–25 min/day** |
| Inbox monitoring | Check 4–6× daily when not in office, 3–5 min each | Automated digest + critical alerts | **15–20 min/day** |
| Lab follow-up tracking | Manual list maintenance, 10–15 min | Automated overdue detection | **10–15 min/day** |
| Care gap identification | Chart-by-chart review or none | Automated USPSTF screening | **10–20 min/day** |
| **Total Estimated Recovery** | | | **~1.5–2.5 hours/day** |

### Revenue Capture Opportunities

| Billing Code | Description | Estimated Revenue Per Event | Annual Potential |
|-------------|-------------|----------------------------|-----------------|
| **G0438/G0439** | Annual Wellness Visit (initial/subsequent) | $140–$180 | Depends on patient volume |
| **99490/99491** | Chronic Care Management | $40–$60/patient/month | Significant for Medicare panel |
| **99496–99498** | Transitional Care Management | $150–$300/discharge | Per hospital/SNF discharge |
| **G2211** | Behavioral Health Integration add-on | $90–$120/visit | With qualifying E/M visits |
| **99417** | Prolonged in-person E/M services | Varies | Complex visit add-on |

These are codes the practice may already qualify for but is not consistently capturing. CareCompanion flags eligible patients **before** the visit and provides documentation checklists **after** the visit to support accurate billing.

### Clinical Quality

- **30+ USPSTF preventive care guidelines** evaluated per patient automatically via demographic information queried aginst cached API calls
- **FDA drug recall monitoring** against active medication lists via cached API pulls
- **Immunization gap detection** per CDC adult schedule via cached API pulls
- **Lab result follow-up alerts** to prevent patients from falling through the cracks
- **Structured note templates** to reduce documentation variability

---

## 7. Frequently Asked Questions

**Q: Does this modify data in Amazing Charts?**  
A: No. CareCompanion reads XML exports that Amazing Charts produces through its own built-in Clinical Summary export feature. It does not write to the Amazing Charts database or modify any records.

**Q: Could the automation accidentally click the wrong thing?**  
A: No. The automation uses OCR to visually confirm it has found the correct UI element before clicking. If it cannot find the expected element, it stops and logs an error. It also verifies that Amazing Charts is the foreground window before every action, and the PyAutoGUI failsafe (move mouse to screen corner) instantly aborts all automation.

**Q: Is patient data sent to the cloud?**  
A: No. All patient data is processed locally on my workstation. The only outbound requests go to federal reference APIs (NIH, FDA, CMS, CDC) and contain only non-identifiable clinical codes like drug names, ICD-10 codes, and CPT codes — never patient names, MRNs, dates of birth, or any other PHI.

**Q: Does this require new servers or infrastructure?**  
A: No. It runs entirely on my existing workstation. The database is a single local file. Updates are currently planned to deployed via USB unless IT i sable an dwilling to allow remote update pushes. No servers, VMs, or cloud services are needed.

**Q: Who has access to the application?**  
A: Only authenticated users at my workstation. The application runs on `localhost` and is not accessible from other machines on the network. It has role-based access control (Admin, Provider, Medical Assistant) with bcrypt-hashed passwords and a full audit trail.

**Q: What happens if the automation breaks or Amazing Charts updates?**  
A: Because the automation uses OCR (reading screen text) rather than hardcoded pixel coordinates, it is resilient to minor UI changes. If a major update changes the AC interface significantly, the automation gracefully fails — it stops and logs an error rather than proceeding blindly. The core application (dashboard, care gaps, billing, labs, etc.) continues to function normally since it depends on XML data, not screen automation.

**Q: Is this HIPAA-compliant?**  
A: The application was designed with HIPAA requirements in mind. PHI never leaves the practice network, MRNs are hashed in logs, data is auto-deleted after retention periods, and all actions are audit-logged. A detailed security and compliance overview is available in the project documentation (SECURITY.md).

**Q: What if I'm not at work — does it keep running?**  
A: The background service runs while my workstation is on. Notifications respect quiet hours (10 PM – 7 AM), with an override only for critical lab values. When the workstation is off, nothing runs.

---

## Summary

CareCompanion is a **locally-hosted, single-workstation clinical tool** that enhances Amazing Charts with capabilities the EHR does not provide: preventive care gap detection, billing opportunity identification, inbox management, automated order entry, and clinical decision support.

The tools that were flagged — **terminal access, OCR software, and GUI automation** — are standard components of this type of desktop integration. They are necessary because Amazing Charts does not offer an API for programmatic access. Every component has been designed with safety controls and HIPAA-compliant data handling.

**What I'm requesting:**

1. Continued permission to run CareCompanion on my workstation
2. IT provisioning of the items listed in [Section 5](#5-what-it-needs-to-provision)
3. Recognition that Dr. [Supervising Physician Name] has approved this project

I am happy to demonstrate the application, walk through the code, or answer any additional questions.

---

*This document and the full source code are available for review at any time.*

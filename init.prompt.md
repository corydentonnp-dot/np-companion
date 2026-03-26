# CareCompanion - Master Project Context

This file is a compact project context reference.

Full operational rules live in .github/copilot-instructions.md.

---

## Project Overview

CareCompanion is a locally hosted clinical workflow automation platform for a
family nurse practitioner at a primary care office.

It automates repetitive tasks inside two systems:

- Amazing Charts - desktop EHR and charting
- NetPractice/WebPractice - web scheduling and communication

The platform runs as a Flask web server on a Windows 11 Pro work PC.
A background agent handles desktop automation, OCR reading, and scheduled jobs.

The developer is a non-programmer, so code should stay clear, explicit, and
readable.

---

## Key Documents

| Document | Location | Purpose |
|---|---|---|
| This file | init.prompt.md | Compact project context |
| Copilot Instructions | .github/copilot-instructions.md | Full coding and operational rules |
| Active Plan | Documents/dev_guide/ACTIVE_PLAN.md | Current sprint or in-progress plan |
| Development Guide | Documents/dev_guide/CARECOMPANION_DEVELOPMENT_GUIDE.md | Feature specs by phase |
| Project Status | Documents/dev_guide/PROJECT_STATUS.md | Build state, Feature Registry, Risk Register |
| API Integration Plan | Documents/dev_guide/API_INTEGRATION_PLAN.md | External API behavior and cache expectations |
| AC Interface Reference | Documents/dev_guide/AC_INTERFACE_REFERENCE_V4.md | Amazing Charts ground truth |
| Deployment Guide | Documents/dev_guide/DEPLOYMENT_GUIDE.md | Build, transfer, install, update |
| Changelog | Documents/CHANGE_LOG.md | Authoritative change history |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Web framework | Flask (app factory pattern) |
| ORM and DB | SQLAlchemy + SQLite |
| Auth | Flask-Login + Flask-Bcrypt |
| Browser automation | Playwright (Chromium) |
| Desktop automation | PyAutoGUI + pywin32 |
| OCR | pytesseract + Pillow |
| Scheduling | APScheduler |
| Notifications | Pushover API |
| Frontend | HTML + CSS + vanilla JS |
| Packaging | PyInstaller |
| OS target | Windows 11 Pro |

---

## Project Folder Structure

```text
CareCompanion/
|-- app.py
|-- agent_service.py
|-- launcher.py
|-- build.py
|-- config.py
|-- requirements.txt
|-- init.prompt.md
|-- .github/
|   |-- copilot-instructions.md
|   |-- agents/
|   |-- prompts/
|   `-- instructions/
|-- adapters/
|-- agent/
|-- app/
|   `-- services/
|-- billing_engine/
|-- models/
|-- routes/
|-- templates/
|-- static/
|-- scrapers/
|-- scripts/
|-- migrations/
|-- tests/
|-- utils/
|-- Documents/
|   |-- CHANGE_LOG.md
|   |-- dev_guide/
|   |-- overview/
|   `-- _archive/
`-- data/
```

---

## Feature Catalog (Phases 1-9)

| Phase | Focus | Highlights |
|---|---|---|
| 1 | Foundation | App shell, auth, DB setup, baseline agent |
| 2 | Data Layer | NetPractice ingestion, inbox monitor, MRN reader |
| 3 | Daily Tools | On-call notes, order sets, note prep, med reference |
| 4 | Monitoring | Lab tracking, timers, dashboard metrics |
| 5 | Clinical Support | Care gaps, billing capture, coding support |
| 6 | Communication | Delayed messaging, templates, EOD checks |
| 7 | Utilities | Notifications, briefing, macros, trackers |
| 8 | Governance | Reliability, testing, anti-sprawl enforcement |
| 9 | SaaS Readiness | Adapter boundaries, portability groundwork |

---

## Amazing Charts Keyboard Shortcuts

```python
AC_SHORTCUTS = {
    "demographics": "F5",
    "summary_sheet": "F6",
    "most_recent_encounter": "F7",
    "past_encounters": "F8",
    "imported_items": "F9",
    "account_information": "F11",
    "patient_menu": "Alt+P",
    "medications": "Ctrl+M",
    "health_risk_factors": "Ctrl+H",
    "immunizations": "Ctrl+I",
    "print_summary_sheet": "Ctrl+P",
    "print_messages": "Ctrl+G",
    "tracked_data": "Ctrl+T",
    "set_flags": "Alt+P -> Set Flags",
    "set_reminder": "Alt+P -> Set Reminder",
    "confidential": "Alt+P -> Confidential",
    "allergies": "Alt+P -> Allergies",
    "diagnoses": "Alt+P -> Diagnoses",
    "physical_exam": "Alt+P -> Physical Exam",
    "clinical_decision_support": "Alt+P -> Clinical Decision Support",
    "export_clinical_summary": "Alt+P -> Export Clinical Summary",
    "save_and_close": "Ctrl+S",
}
```

---

## Clinical Summary XML Sections

| Section | LOINC Code | Data Type |
|---|---|---|
| Medications | 10160-0 | Structured |
| Allergies | 48765-2 | Structured |
| Problems / Diagnoses | 11450-4 | Structured |
| Vital Signs | 8716-3 | Structured |
| Results / Labs | 30954-2 | Structured |
| Immunizations | 11369-6 | Structured |
| Social History | 29762-2 | Structured |
| Encounters | 46240-8 | Structured |
| Plan of Care | 18776-5 | Narrative |
| Assessments | 51848-0 | Narrative |
| Goals | 61146-7 | Narrative |
| Health Concerns | 75310-3 | Narrative |
| Instructions | 69730-0 | Narrative |
| Mental Status | 10190-7 | Narrative |
| Reason for Visit | 29299-5 | Narrative |
| Progress Notes | 11506-3 | Narrative |

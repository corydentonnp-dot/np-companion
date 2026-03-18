# Changelog — CL5
**Date:** 2026-03-16
**Phase:** Documentation — AC Integration Update
**Summary:** Major documentation update integrating Amazing Charts Clinical Summary XML pipeline, Enlarge Textbox window reference, answered outstanding questions, and 4 new features (4f, 6d, 10e, 11e). No application code changes — document edits only.

---

## Changes Made

### 1. AC Interface Reference — Enlarge Textbox Window Section (NEW)
- **File:** `Documents/ac_interface_reference.md`
- Copied from Downloads to `Documents/` folder
- Added new section: "Enlarge Textbox Window (Note Entry)"
- Documented: window title format, menu bar, two-column layout (Section list + Text area), 6 bottom action buttons
- Defined canonical `AC_NOTE_SECTIONS` (16 sections) and `AC_SPECIAL_SECTIONS` (Allergies, Medications)
- Documented `Update & Go to Next Field` for sequential automation

### 2. Copilot Instructions — AC Integration Updates (Task 1)
- **File:** `Documents/copilot-instructions.md`
- **1a:** Updated Feature 6 (MRN Reader) — replaced OCR-on-screen-region with `win32gui.GetWindowText()` title bar parsing (3-tier fallback)
- **1b:** Updated Feature 5 (Inbox Monitor) — replaced generic screenshot approach with confirmed 7-step filter-cycling approach using exact dropdown labels
- **1c:** Updated Feature 31 (Note Reformatter) — changed to XML-first approach with OCR fallback for narratives only
- **1d:** Added `AC_SHORTCUTS` dictionary (13 keyboard shortcuts)
- **1e:** Added Clinical Summary XML Export section (format, constraint, namespace, LOINC codes, templateIds)
- **1f:** Added `AC_NOTE_SECTIONS` canonical list (16 sections)
- **1g:** Updated folder structure (added `ac_window.py`, `clinical_summary_parser.py`, `inbox_reader.py`, `Documents/` folder, `data/clinical_summaries/`)
- **1h:** Added `data/clinical_summaries/` to sensitive files list
- Added Feature 6d (Clinical Summary Exporter & Parser) description
- Added Feature 10e (Patient Chart View) description
- Added Web-Based Config Editor feature spec

### 3. Development Guide — Outstanding Questions Answered (Task 2a)
- **File:** `Documents/NP_Companion_Development_Guide.md`
- Marked as **ANSWERED** with confirmed details:
  - MRN location → title bar, `win32gui.GetWindowText()` + regex `ID:\s*(\d+)`
  - Inbox navigation → right panel of home screen, 7 filter dropdown options
  - Note creation → F7 + Enlarge Textbox + Update & Go to Next Field
  - Template selection → Patient > Print > Notes & Letters, Save Section/Visit Template buttons
  - Print/export → PDF (Patient > Print) and XML (Patient > Export Clinical Summary)
  - Patient search → Patient List panel, ID column search field
- Left **OPEN**: AC version, Amazing Charts process name

### 4. Development Guide — New Feature 4f: Direct Patient Search (Task 2b)
- **File:** `Documents/NP_Companion_Development_Guide.md`
- Added after Feature 4e
- Dashboard-wide search by name or MRN for off-schedule patient access
- Includes AI prompt for implementation

### 5. Development Guide — New Feature 11e: Clinical Summary Auto-Archive (Task 2c)
- **File:** `Documents/NP_Companion_Development_Guide.md`
- Added after Feature 11d
- 183-day retention with daily cleanup job in `agent/scheduler.py`
- AuditLog for every parse and deletion

### 6. Development Guide — Updated Feature 5 Inbox Monitor (Task 2d)
- **File:** `Documents/NP_Companion_Development_Guide.md`
- Replaced generic OCR approach with confirmed 7-step filter-cycling workflow
- Updated AI prompt to reference `agent/inbox_reader.py` with exact filter labels
- Added `INBOX_FILTER_OPTIONS` list and subject prefix documentation

### 7. Development Guide — Updated Feature 6 MRN Reader (Task 2e)
- **File:** `Documents/NP_Companion_Development_Guide.md`
- Replaced OCR-on-region description with title bar parsing (3-tier: title → pink bar OCR → region OCR)
- Updated AI prompt to reference `agent/ac_window.py` with `win32gui` approach
- Updated calibration mode to verify `win32gui` identification instead of clicking screen region

### 8. Development Guide — New Feature 6d: Clinical Summary Exporter & Parser (Task 2f)
- **File:** `Documents/NP_Companion_Development_Guide.md`
- Added after Feature 6c (before Phase 3)
- Full AI prompt for `agent/clinical_summary_parser.py` with 4 functions
- Includes critical constraint about no chart windows during export
- Added checkpoint for testing

### 9. Development Guide — New Feature 10e: Patient Chart View (Task 2g)
- **File:** `Documents/NP_Companion_Development_Guide.md`
- Added after Feature 10d (before Phase 4)
- Sidebar tabs, Overview widgets, Prepped Note tab documentation
- Full AI prompt for `routes/patient.py` and templates
- Added checkpoint for testing

### 10. Development Guide — Master Build Checklist Updated
- **File:** `Documents/NP_Companion_Development_Guide.md`
- Added 4 new entries: Feature 4f, Feature 6d, Feature 10e, Feature 11e

### 11. AC Patient Info Guide (NEW — Task 3)
- **File:** `Documents/AC_Patient_Info_Guide.md`
- Standalone chapter documenting the complete patient data pipeline
- 8 sections: Purpose, Data Collection, XML Structure & Field Extraction Map, Database Storage Schema, Browser Display, AC Automation Details, HIPAA & Security, AI Prompts
- All XPath patterns verified against sample XML (PatientId 62815)
- Complete section index with templateIds, LOINC codes, and nullFlavor behavior
- 4 full AI prompts: clinical_summary_parser.py, patient.py, ac_window.py, inbox_reader.py

---

## Files Created
| File | Purpose |
|------|---------|
| `Documents/AC_Patient_Info_Guide.md` | Complete patient data pipeline documentation |

## Files Modified
| File | Changes |
|------|---------|
| `Documents/copilot-instructions.md` | AC integration updates (F5, F6, F31, shortcuts, XML, note sections, folder structure) |
| `Documents/NP_Companion_Development_Guide.md` | Answered questions, 4 new features, 2 updated features, build checklist |
| `Documents/ac_interface_reference.md` | Enlarge Textbox Window section added |

---

## Verification Steps

### Step 1: Confirm all files exist
```powershell
Test-Path "C:\Users\coryd\Documents\NP_Companion\Documents\AC_Patient_Info_Guide.md"
Test-Path "C:\Users\coryd\Documents\NP_Companion\Documents\ac_interface_reference.md"
Test-Path "C:\Users\coryd\Documents\NP_Companion\Documents\copilot-instructions.md"
Test-Path "C:\Users\coryd\Documents\NP_Companion\Documents\NP_Companion_Development_Guide.md"
```

### Step 2: Verify Section 7 answered questions
- Open `NP_Companion_Development_Guide.md`, search for "Section 7"
- Confirm MRN, Inbox, Note creation, Template, Print/export, Patient search show ✅ ANSWERED
- Confirm AC version and process name show ⏳ OPEN

### Step 3: Verify new features in Dev Guide
- Search for "Feature 4f" — Direct Patient Search exists after 4e
- Search for "Feature 6d" — Clinical Summary Exporter exists after 6c
- Search for "Feature 10e" — Patient Chart View exists after 10d
- Search for "Feature 11e" — Clinical Summary Auto-Archive exists after 11d

### Step 4: Verify AC_Patient_Info_Guide.md
- Open file, confirm 8 sections present
- Section 3 contains XPath tables with verified patterns
- Section 8 contains 4 AI prompts

### Step 5: Verify copilot-instructions.md
- Search for "AC_SHORTCUTS" — keyboard shortcuts dictionary present
- Search for "AC_NOTE_SECTIONS" — 16-item canonical list present
- Search for "Clinical Summary XML" — export section present
- Search for "clinical_summaries" — in folder structure and sensitive files

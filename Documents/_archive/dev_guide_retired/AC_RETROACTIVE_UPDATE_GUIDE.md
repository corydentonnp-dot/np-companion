# Archived from Documents/dev_guide on 03-26-26 05:18:36 UTC
# Reason: Overnight remediation archive cleanup

# AC Interface Reference v4 — Retroactive Update Guide

**Created:** March 17, 2026 (CL17)
**Purpose:** This document describes how the newly completed AC Interface
Reference v4 (2788 lines) and AC Orders spreadsheet (~870 items) impact
code and features that have **already been built**. It identifies every
discrepancy, gap, and improvement opportunity in existing code.

**Scope:** Only already-built code is covered here. Future features and
features not yet started belong in the Development Guide, not this document.

**Source materials:**
- `Documents/ac_interface_reference/Amazing charts interface/..md files/ac_interface_reference_v4.md`
- `Documents/ac_interface_reference/Amazing charts interface/Order Sets/AC orders.xlsx`
- `Documents/ac_interface_reference/Amazing charts interface/screenshots/` (50+ images)

---

## Summary of Key Discoveries

The AC Interface Reference v4 represents the most comprehensive documentation
of the Amazing Charts desktop application ever created for this project. It
was built from hands-on exploration of the live AC application and supersedes
all prior reference versions (v1–v3).

### What changed vs prior understanding:

| Category | Old Understanding | v4 Reality |
|----------|-------------------|------------|
| Work PC OS | Windows 10 | **Windows 11 Pro** |
| AC Process Name | `"AmazingCharts.exe"` (assumed) | **Window title: `Amazing Charts EHR (32 bit)`**, exe is `AmazingCharts.exe` at `C:\Program Files (x86)\Amazing Charts\` |
| AC Version | Unknown | **12.3.1 (build 297)** |
| Practice ID | Unknown | **2799** (Family Practice Associates of Chesterfield) |
| Screenshot library | 10 images | **50+ screenshots** covering every major dialog |
| Order catalog | Empty / unknown | **~870 orders** across 4 populated tabs with CPT codes |
| Database access | Assumed impossible | **SQL Server at `\\192.168.2.51`** — direct read may be possible |
| Imported items | Unknown method | **Network share: `\\192.168.2.51\amazing charts\ImportItems\[MRN]\`** |
| Inbox filters | 6 known filters | **7 filters** — "Show Everything" is the 7th |
| AC state detection | Not documented | **4 states documented** with detection logic |
| Login automation | Not documented | **Login flow fully documented** |
| Provider roster | Unknown source | **Available from Set Reminder dialog** |
| AC Log path | Unknown | **`C:\Program Files (x86)\Amazing Charts\Logs`** |

---

## File-by-File Impact Assessment

### 1. `config.py` — Machine Configuration

**Current state:** Working config with AC_MOCK_MODE=True and placeholder values.

**Issues found:**

| # | Issue | Current Value | Required Change | Priority |
|---|-------|---------------|-----------------|----------|
| 1 | Process name | `"AmazingCharts.exe"` | Update to reflect that the **window title** is `"Amazing Charts EHR (32 bit)"` while the **exe process** is `AmazingCharts.exe`. The code in `ac_window.py` uses `title.startswith('Amazing Charts')` which works with the real title, but `config.AMAZING_CHARTS_PROCESS_NAME` should be accurate for `psutil`-based process detection. Consider adding both: `AC_PROCESS_NAME = "AmazingCharts.exe"` and `AC_WINDOW_TITLE_PREFIX = "Amazing Charts"` | **HIGH** |
| 2 | Missing AC system values | Not present | Add new config entries: `AC_VERSION = "12.3.1"`, `AC_PRACTICE_ID = 2799`, `AC_EXE_PATH = r"C:\Program Files (x86)\Amazing Charts\AmazingCharts.exe"`, `AC_LOG_PATH = r"C:\Program Files (x86)\Amazing Charts\Logs"` | MEDIUM |
| 3 | Missing DB path | Not present | Add: `AC_DB_PATH = r"\\192.168.2.51\Amazing Charts\AmazingCharts.mdf"` — for future direct DB access | MEDIUM |
| 4 | Missing ImportItems path | Not present | Add: `AC_IMPORTED_ITEMS_PATH = r"\\192.168.2.51\amazing charts\ImportItems"` — patient documents accessible without navigating AC UI | MEDIUM |
| 5 | Missing login credentials | Not present | Add: `AC_LOGIN_USERNAME = ""` and `AC_LOGIN_PASSWORD = ""` (fill at deployment for auto-login) | LOW |
| 6 | Missing state constants | Not present | Add `AC_STATES` dict or enum for the 4 AC states | MEDIUM |

**Impact:** Config changes are non-breaking. All current code works in mock mode. These additions enable new capabilities but don't break existing functionality.

---

### 2. `agent/ac_window.py` — AC Window Management

**Current state:** Fully working win32gui-based window detection with mock mode. Functions: `find_ac_window()`, `get_ac_chart_title()`, `get_active_patient_mrn()`, `get_active_patient_dob()`, `is_ac_foreground()`, `focus_ac_window()`, `is_chart_window_open()`.

**What works correctly per v4:**
- ✅ `title.startswith('Amazing Charts')` matches the real window title `"Amazing Charts EHR (32 bit)"`
- ✅ MRN regex `r'ID:\s*(\d+)'` matches the confirmed chart title format `LASTNAME, FIRSTNAME  (DOB: M/D/YYYY; ID: XXXXX)`
- ✅ DOB regex `r'DOB:\s*([\d/]+)'` matches the same format
- ✅ `is_chart_window_open()` checks for `'ID:'` in titles — correct

**What's missing per v4:**

| # | Gap | Description | Priority |
|---|-----|-------------|----------|
| 1 | **No AC state machine** | v4 defines 4 states (`not_running`, `login_screen`, `home_screen`, `chart_open`). The current code only has two pseudo-states: "AC is foreground" and "a chart is open." There's no `get_ac_state()` function. This is the **most important gap** — every automation step should check state before proceeding. | **HIGH** |
| 2 | **No login screen detection** | v4 documents the login screen. If AC is open but at the login prompt, current code would incorrectly treat it as `home_screen`. Need OCR or title-based detection for the login dialog. | **HIGH** |
| 3 | **No Resurrect Note dialog detection** | v4 documents a "Resurrect [date] note?" dialog that appears when reopening a previously saved-but-unfinished note. If automation encounters this dialog, it will get stuck waiting for an expected screen that's blocked by the dialog. | MEDIUM |
| 4 | **No process-level detection** | Current code uses only `win32gui.EnumWindows()`. Adding `psutil` process check could distinguish `not_running` from `login_screen` more reliably (if AC exe is running but no login window is detected yet). | LOW |

**Recommended changes:**
```python
# Add to ac_window.py:
def get_ac_state():
    """Returns one of: 'not_running', 'login_screen', 'home_screen', 'chart_open'"""
    # 1. Check if AC process exists (psutil)
    # 2. If found, check window titles
    # 3. If chart regex matches → 'chart_open'
    # 4. If "Amazing Charts Login" in title → 'login_screen'
    # 5. If AC window found but no chart/login → 'home_screen'
    # 6. No AC process → 'not_running'

def detect_resurrect_dialog():
    """Check if the Resurrect Note dialog is blocking. Returns True if detected."""
    # OCR the foreground for "Resurrect" text

def handle_resurrect_dialog(accept=True):
    """Click Yes or No on the Resurrect Note dialog."""
```

---

### 3. `agent/inbox_reader.py` — Inbox Filter Cycling

**Current state:** Fully working OCR-based inbox reader that cycles through 6 filter tabs.

**Issue: Missing 7th filter**

The current `INBOX_FILTERS` list has 6 entries:
```python
INBOX_FILTERS = [
    'Show Charts',
    'Show Charts to Co-Sign',
    'Show Imports to Sign-Off',
    'Show Labs to Sign-Off',
    'Show Orders',
    'Show Patient Messages',
]
```

v4 confirms **7 filter options** — **"Show Everything"** is missing. This is a combined view that shows all items regardless of category.

**Impact:**
- The inbox reader skips `"Show Everything"` entirely, so it will never capture items that might only appear in that unified view
- If any metrics or dashboard counts use `len(INBOX_FILTERS)` to calculate coverage percentages, they would be slightly off
- The "Show Everything" filter is useful for getting a total item count to validate that individual filter cycles captured everything

**Required change:** Add `'Show Everything'` to the `INBOX_FILTERS` list. Consider whether it should be cycled first (to get a total) or last (to validate counts from individual filters).

**Priority:** MEDIUM — existing functionality works for the 6 known categories. Adding "Show Everything" improves completeness.

---

### 4. `agent/pyautogui_runner.py` — Order Set Executor

**Current state:** Fully working OCR-based order executor with safety checks, pre-execution screenshots, and per-item status tracking. Uses `find_and_click(item.order_tab)` to navigate to the correct tab, then `find_and_click(label)` to check the order.

**What works correctly per v4:**
- ✅ OCR-first approach for finding tab names and order labels
- ✅ Safety check: verifies AC is foreground before every click
- ✅ Pre-execution screenshot for audit trail
- ✅ Stops immediately on failure — never continues partially

**What could be improved:**

| # | Improvement | Description | Priority |
|---|-------------|-------------|----------|
| 1 | Tab name validation | Currently accepts any string for `order_tab`. v4 confirms exactly 8 valid tabs: `Nursing`, `Labs`, `Imaging`, `Diagnostics`, `Referrals`, `Follow Up`, `Patient Education`, `Other`. Add validation before execution. | MEDIUM |
| 2 | CPT code logging | Orders have CPT codes (from spreadsheet) but the execution audit doesn't capture them. Enhancing the `OrderExecutionItem` model to include a CPT code would improve billing integration. | LOW |
| 3 | Tab count awareness | 4 tabs are populated (Nursing, Labs, Imaging, Diagnostics), 4 are empty (Referrals through Other). Executor could skip known-empty tabs to save time. | LOW |

**No breaking issues.** The executor is well-designed and its OCR-first approach is confirmed correct by v4. The main gap is in the **data** (empty `MasterOrder` table), not the executor code.

---

### 5. `models/orderset.py` — Order Data Models

**Current state:** Complete set of models for order management: `OrderSet`, `OrderItem`, `MasterOrder`, `OrderSetVersion`, `OrderExecution`, `OrderExecutionItem`.

**Issues found:**

| # | Issue | Description | Priority |
|---|-------|-------------|----------|
| 1 | **`MasterOrder` missing `cpt_code` field** | The AC orders spreadsheet includes CPT codes for Nursing orders and LabCorp test numbers for Lab orders. The `MasterOrder` model has `order_name`, `order_tab`, `order_label`, `category` — but no `cpt_code` column. This needs a migration to add `cpt_code = db.Column(db.String(20))`. | **HIGH** |
| 2 | **`MasterOrder` table is empty** | The spreadsheet contains ~870 orders that should be seeded into this table. A migration/seed script needs to be created to parse `AC orders.xlsx` and populate the records. | **HIGH** |
| 3 | **No `ORDER_TABS` constant** | Tab names are stored as freeform strings in the database. There's no centralized list of valid tab names. v4 confirms exactly 8: `Nursing`, `Labs`, `Imaging`, `Diagnostics`, `Referrals`, `Follow Up`, `Patient Education`, `Other`. A constant should be added for validation. | MEDIUM |

**Required changes:**
1. Add migration script: `migrate_add_master_order_cpt.py` — adds `cpt_code` column to `master_orders`
2. Create seed script: `scripts/seed_master_orders.py` — reads xlsx, populates `master_orders`
3. Add constant (in `models/orderset.py` or `config.py`):
```python
ORDER_TABS = [
    'Nursing', 'Labs', 'Imaging', 'Diagnostics',
    'Referrals', 'Follow Up', 'Patient Education', 'Other'
]
```

---

### 6. `routes/patient.py` — Patient Chart Routes

**Current state:** Full patient chart page with 6 tabs, prepped note system, note section display. Two important routes are **stubs**.

**What works correctly per v4:**
- ✅ `AC_NOTE_SECTIONS` has exactly 16 sections — matches v4's confirmed Enlarge Textbox 16-section layout
- ✅ `AC_SPECIAL_SECTIONS = ["Allergies", "Medications"]` — v4 confirms these open separate windows
- ✅ Patient chart page renders all expected sections

**Stub routes that can now be implemented:**

| # | Route | Current State | What v4 Enables | Priority |
|---|-------|---------------|-----------------|----------|
| 1 | `send_to_ac(mrn)` | Returns `"Use Copy All and paste manually"` | v4 confirms the Enlarge Textbox has 16 sections with "Update & Go to Next Field" workflow. Note injection via PyAutoGUI is now viable: open chart → click Enlarge → paste section → advance → repeat. | **HIGH** |
| 2 | `refresh_patient(mrn)` | Returns fake `success: True`, does nothing | v4 confirms Clinical Summary XML export workflow. This stub should trigger the agent to export a fresh Clinical Summary for the given MRN. Also: ImportItems path (`\\192.168.2.51\amazing charts\ImportItems\[MRN]\`) provides direct file access without needing to navigate the AC UI. | **HIGH** |

**Additional opportunity:** v4 reveals the Imported Items are accessible via a network file share. A new function could check `\\192.168.2.51\amazing charts\ImportItems\{mrn}\` for patient documents (lab results, referral responses, etc.) without any AC automation — just file I/O.

---

### 7. `agent/clinical_summary_parser.py` — XML Export & Parsing

**Current state:** Two-phase automation (Phase 1: open charts, Phase 2: export XML) + CDA XML parser with 12 LOINC-coded section handlers.

**What works correctly per v4:**
- ✅ Two-phase export workflow is correct per v4 documentation
- ✅ CDA XML parsing handles all standard sections
- ✅ `nullFlavor="NI"` handling for empty sections
- ✅ Export path configuration in config.py

**Minor improvement:** v4 confirms AC version 12.3.1 exports XML in the exact format already handled by the parser. The parser was built from real XML output from this exact AC version — so it's fully aligned.

**No code changes needed.** This module is the best-aligned with v4 findings.

---

### 8. `agent/ocr_helpers.py` — OCR Engine

**Current state:** Full OCR detection engine with preprocessing, word-level bounding boxes, text finding, and element clicking.

**What works correctly per v4:**
- ✅ OCR-first approach is confirmed as the right strategy
- ✅ Window rect detection for screenshot targeting
- ✅ Preprocessing pipeline (grayscale, upscale 2x, contrast enhancement)
- ✅ Word bounding box extraction for precise clicking

**Future consideration:** If AC database direct access (at `\\192.168.2.51`) is confirmed working, some OCR-based data extraction could be supplemented or replaced by SQL queries. However, OCR remains essential for:
- UI navigation (clicking buttons, tabs, menus)
- Dialog detection (Resurrect Note, alerts, confirmations)
- Screen state validation (verifying the right screen is active)

**No code changes needed now.** OCR code stays as-is. DB access, if viable, would supplement — not replace — the OCR engine.

---

### 9. `agent/mrn_reader.py` — MRN Detection Pipeline

**Current state:** 3-tier MRN detection: win32gui title bar → CDP (browser) → OCR fallback.

**What works correctly per v4:**
- ✅ Title bar regex matches the confirmed format
- ✅ Win32gui approach is the right primary method
- ✅ OCR fallback targets the correct region (title bar top 60px)

**No code changes needed.** This module is fully aligned with v4.

---

### 10. `agent/caregap_engine.py` — Care Gap Rules Engine

**Current state:** 19 USPSTF screening rules, age/sex/risk factor matching, auto-persist to database, admin-editable.

**Relevant v4 finding:** v4 documents the CDS (Clinical Decision Support) window accessible via `Alt+P → Clinical Decision Support`. This AC-native window contains USPSTF recommendations that AC already tracks. This could be used to:
- Cross-reference CareCompanion's care gap calculations with AC's built-in CDS
- Import AC's CDS findings instead of calculating independently
- Validate that the 19 rules match what AC itself recommends

**No code changes needed now.** This is a future enhancement opportunity, not a bug.

---

## Priority Action Summary

### Immediate (before next feature development)

| # | Action | File(s) | Effort |
|---|--------|---------|--------|
| 1 | Update `AMAZING_CHARTS_PROCESS_NAME` and add `AC_WINDOW_TITLE_PREFIX` | config.py | 5 min |
| 2 | Add new AC config values (version, paths, practice ID) | config.py | 10 min |
| 3 | Add `get_ac_state()` function | agent/ac_window.py | 30 min |
| 4 | Add "Show Everything" to `INBOX_FILTERS` | agent/inbox_reader.py | 5 min |
| 5 | Add `cpt_code` column to MasterOrder | models/orderset.py + migration | 15 min |

### Short-term (next 1-2 development sessions)

| # | Action | File(s) | Effort |
|---|--------|---------|--------|
| 6 | Create master order seed script from AC orders.xlsx | scripts/seed_master_orders.py | 45 min |
| 7 | Add `ORDER_TABS` constant | models/orderset.py or config.py | 5 min |
| 8 | Add login screen detection | agent/ac_window.py | 20 min |
| 9 | Add Resurrect Note dialog detection/handling | agent/ac_window.py | 20 min |
| 10 | Test direct DB access from work PC | Manual investigation | 30 min |

### Medium-term (when building next AC automation features)

| # | Action | File(s) | Effort |
|---|--------|---------|--------|
| 11 | Implement `send_to_ac()` using Enlarge Textbox workflow | routes/patient.py + agent/ | 2-3 hrs |
| 12 | Implement `refresh_patient()` with XML export trigger | routes/patient.py + agent/ | 1-2 hrs |
| 13 | Add ImportItems file path integration | routes/patient.py | 30 min |
| 14 | Map AC database schema (if DB access works) | New documentation file | 1-2 hrs |

---

## What Does NOT Need Changing

These modules and files are **correctly aligned** with v4 and require no modifications:

| Module | Status | Notes |
|--------|--------|-------|
| `agent/mrn_reader.py` | ✅ Fully aligned | 3-tier detection works correctly per v4 |
| `agent/clinical_summary_parser.py` | ✅ Fully aligned | Two-phase workflow + XML parsing confirmed correct |
| `agent/ocr_helpers.py` | ✅ Fully aligned | OCR engine confirmed as correct primary strategy |
| `agent/notifier.py` | ✅ No impact | Notification system has no AC interface dependency |
| `agent/scheduler.py` | ✅ No impact | Job scheduling has no AC interface dependency |
| `agent/caregap_engine.py` | ✅ Fully aligned | Rules engine is independent of AC UI |
| `routes/` (most routes) | ✅ No impact | Web routes are AC-independent except patient.py |
| `models/` (most models) | ✅ No impact | Data models are AC-independent except orderset.py |
| `templates/` | ✅ No impact | Frontend templates are AC-independent |
| `static/` | ✅ No impact | CSS/JS are AC-independent |
| `scrapers/netpractice.py` | ✅ No impact | NetPractice scraper is a separate system |
| `AC_NOTE_SECTIONS` constant | ✅ Confirmed correct | 16 sections match v4's Enlarge Textbox exactly |
| `AC_SPECIAL_SECTIONS` constant | ✅ Confirmed correct | Allergies + Medications confirmed as separate windows |

---

## New Capabilities Unlocked by v4

These are capabilities that **did not exist before v4** and can now enhance
already-built features:

### 1. Direct Database Access
**What:** SQL Server at `\\192.168.2.51\Amazing Charts\AmazingCharts.mdf`
**Impact on existing code:** Could supplement OCR-based patient data extraction
with direct SQL queries. Patient demographics, medications, allergies, labs,
and diagnoses might all be queryable without navigating the AC UI.
**Status:** Requires testing at the work PC (ACTION ITEM #41).

### 2. Imported Items File Share
**What:** `\\192.168.2.51\amazing charts\ImportItems\[MRN]\`
**Impact on existing code:** The `refresh_patient()` stub in `routes/patient.py`
could use this to pull patient documents (lab results, referral responses)
via simple file I/O instead of complex AC automation.
**Status:** Requires testing at the work PC.

### 3. Provider Roster
**What:** Set Reminder dialog reveals a full list of providers in the practice.
**Impact on existing code:** Useful for multi-provider order routing, referral
generation, and care gap assignment. Not currently used anywhere.
**Status:** Available for future features.

### 4. Login Automation
**What:** v4 documents the login screen fields and workflow.
**Impact on existing code:** The agent currently cannot recover if AC is at
the login screen. With login automation, the agent could detect the login
state and auto-authenticate before proceeding with any automation task.
**Status:** Requires adding to `ac_window.py` (ACTION ITEM #44).

### 5. CDS Window Cross-Reference
**What:** AC has a built-in Clinical Decision Support window (Alt+P → CDS).
**Impact on existing code:** The care gap engine calculates USPSTF rules
independently. The CDS window could be used to cross-validate these calculations
or import AC's own recommendations.
**Status:** Enhancement opportunity for `caregap_engine.py`.

---

*This document should be reviewed and updated after each item in the
Priority Action Summary is completed. As items are resolved, move them
to the "What Does NOT Need Changing" section.*

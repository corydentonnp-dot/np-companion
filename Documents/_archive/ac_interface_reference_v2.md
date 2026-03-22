# Amazing Charts Interface Reference
# File: ac_interface_reference.md
# Location: carecompanion/ (project root, alongside init.prompt.md)
#
# This document describes the Amazing Charts (AC) desktop application interface
# as observed from live screenshots. GitHub Copilot should use this as the
# ground-truth reference for all PyAutoGUI automation, OCR region targeting,
# and pywin32 window management code written for CareCompanion.
#
# All pixel coordinates are RELATIVE and must be calibrated per machine using
# the MRN calibration tool (Feature 28a). Never hardcode coordinates.

---

## Window Identification

### Main Window Title Bar Format
```
Amazing Charts  Family Practice Associates of Chesterfield
```
The application title is always "Amazing Charts" followed by the practice name.
Use this to identify and focus the window via pywin32:

```python
import win32gui

def find_amazing_charts_window():
    """
    Returns the hwnd of the Amazing Charts main window.
    Title always starts with 'Amazing Charts'.
    """
    result = []
    def enum_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title.startswith('Amazing Charts'):
                result.append(hwnd)
    win32gui.EnumWindows(enum_callback, None)
    return result[0] if result else None
```

### Patient Chart Window Title Bar Format
When a patient chart is open, the title bar of the chart window reads:
```
[LASTNAME], [FIRSTNAME]  (DOB: MM/DD/YYYY; ID: [MRN])  [AGE] year old [man/woman],
```
Example observed:
```
TEST, TEST  (DOB: 10/1/1980; ID: 62815)  45 year old woman,
```

**MRN Location:** The patient ID number appears in the title bar after "ID: " —
this is the most reliable source of the MRN. It is NOT in a fixed screen region;
it is in the window title string itself.

```python
def get_active_patient_mrn():
    """
    Reads the MRN from the active Amazing Charts patient chart window title.
    More reliable than OCR on a screen region.
    Returns MRN string or None if no chart is open.
    """
    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd)
    import re
    match = re.search(r'ID:\s*(\d+)', title)
    return match.group(1) if match else None

def get_active_patient_dob():
    """Reads DOB from chart window title. Returns 'MM/DD/YYYY' string or None."""
    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd)
    import re
    match = re.search(r'DOB:\s*([\d/]+)', title)
    return match.group(1) if match else None
```

**Note for MRN Reader (Feature 6):** The original design used OCR on a screen
region to read the MRN. The title bar approach above is significantly more
reliable and should be used instead. Update mrn_reader.py to use
`win32gui.GetWindowText()` on the foreground window rather than Tesseract OCR.
Only fall back to OCR if the title bar parse returns None.

---

## Main Application Layout (Home Screen)

### Observed from: home_screen_pateitn_chart_highlighted.png

The AC home screen has three primary zones:

**Zone 1 — Top Menu Bar (left side)**
```
File  Edit  View  Patient  Billing  E-Prescribing  Help  Amazing Charts Services
```
These are standard Windows menu items accessible via `pyautogui.hotkey('alt', 'p')`
for the Patient menu, etc.

**Zone 2 — Top Toolbar (icon buttons, left side)**
Four large icon buttons:
- `Schedule` — opens scheduling calendar
- `Messages` — opens messaging
- `Reports` — opens the Search/Reports tool
- `Secure` — secure messaging

Counter badges visible above toolbar:
- `Scheduled: --`
- `Messages: [count]`
- `Pharmacy Requests: [count]`

**Zone 3 — Patient List Panel (left side, below toolbar)**
Columns: `ID | Lastname | Firstname | DOB`
Search fields at top of each column.
`Active` checkbox filter in upper right of panel.

**Zone 4 — Scheduling Calendar (lower left)**
Monthly calendar view. Shows "Today's Schedule" button with quick-view
links (1w, 2w, 3w, 4w, 6w and 2M, 3M, 4M, 6M, 1Y).
`Select a Provider` dropdown at bottom.
`Book Appointment` button.
`Check In/Out` button.

**Zone 5 — Inbox Panel (right side, upper half)**
Primary work area. Contains the inbox table and message preview.
See Inbox section below for full detail.

**Zone 6 — Patient Summary Panel (lower left, below calendar)**
When a patient is selected in the inbox, their summary appears here showing:
- Patient name and DOB
- Brief summary paragraph (age, last seen, last provider)
- Insurance information
- Any active alerts (shown in colored alert boxes — yellow, red, orange)

---

## Inbox Panel

### Observed from: home_screen_pateitn_chart_highlighted.png, Inbox_lab_home_page.png, AC_inbox_drop_down_filter_options_.png

### Inbox Structure
The inbox occupies the upper-right quadrant of the main AC window.

**Inbox Header Controls (top row):**
- Dropdown 1: `Inbox` (left) — switches between Inbox and other views
- Dropdown 2: Filter dropdown (middle) — content filter, see below
- Dropdown 3: `All` (right) — provider filter
- Icon buttons (far right): flag/priority icon, calendar icon, another icon

**Inbox Table Columns:**
```
From  |  Subject  |  Received
```
- `From` — sender name (e.g., LIBERTY, LABEDI, CORY)
- `Subject` — message subject, may be truncated
- `Received` — date and time (format: MM/DD/YYYY HH:MM AM/PM)

Selected/active row is highlighted in blue.

**Search Bar:** Below the header controls, above the table.
Text field labeled `Search`.

### Inbox Filter Dropdown Options
The middle dropdown (second control) filters inbox content.
**Exact option labels observed:**
```
Show Everything (4)        ← number in parentheses = item count
Show Charts (3)
Show Charts to Co-Sign (0)
Show Imports to Sign-Off (0)
Show Labs to Sign-Off (0)
Show Orders (0)
Show Patient Messages (0)
```
The number in parentheses updates live with the current count.

```python
# To filter inbox by type using PyAutoGUI:
# 1. Click the middle dropdown (second control in inbox header row)
# 2. Select the desired option by text match
# Strategy: use pyautogui to click the dropdown, then find and click the option

INBOX_FILTER_OPTIONS = {
    'everything':      'Show Everything',
    'charts':          'Show Charts',
    'cosign':          'Show Charts to Co-Sign',
    'imports':         'Show Imports to Sign-Off',
    'labs':            'Show Labs to Sign-Off',
    'orders':          'Show Orders',
    'messages':        'Show Patient Messages',
}
```

### Message Preview Panel (below inbox table)
When an inbox item is selected, a preview appears below the table with:
- `Patient` button (left side) — opens patient summary in left panel
- `To:` field
- `From:` field
- `Date:` field
- `Re:` field — subject line
- Message body text area
- Action buttons on the right side:
  - `Pull Chart` — opens the patient's chart
  - `Save To Chart` — saves message to chart
  - `Pull Lab` — (active for lab results only)
  - `Send Message` — (active when applicable)
- Below message body: `Orders` icon button, `Refill` icon button
- Toolbar above preview: `New | Reply | Forward | Print | Save | X (delete) | Delete`
- `Task Complete` checkbox (upper right of preview)

### Inbox Item Types and Subject Prefixes
Observed subject line prefixes:
- `LAB: [PATIENT LASTNAME]` — lab result
- `CHART: [PATIENT LASTNAME]` — chart message / forwarded chart
- `VIIS` — Virginia Immunization Information System import

### Patient Context Bar (pink/salmon banner)
When an inbox item is selected, a pink banner appears at the top of the preview:
```
[LASTNAME, FIRSTNAME]  (DOB: MM/DD/YYYY)  #[MRN]  [AGE] year old [man/woman],
last seen [X] months ago ([date]) by [Provider Name], [Credentials].
[Next Appt: None scheduled]
```
This banner contains the MRN and can be OCR-read as a fallback if window title
parsing is unavailable.

---

## Patient Chart Layout

### Observed from: fresh_open_patient_chart.png

The patient chart opens as a separate window (not a tab in the main window).
Window title format: `[LASTNAME], [FIRSTNAME]  (DOB: MM/DD/YYYY; ID: [MRN])  [age/sex]`

### Chart Tab Bar
Five tabs across the top of the chart window:
```
Demographics | Summary Sheet | Most Recent Encounter | Past Encounters | Imported Items | Account Information
```
Keyboard shortcuts (from Patient menu):
- `F5` — General Info Demographics
- `F6` — Summary Sheet
- `F7` — Most Recent Encounter
- `F8` — Past Encounters
- `F9` — Imported Items
- `F11` — Account Information

### Most Recent Encounter Tab Layout (F7)
This is the primary charting view. Layout observed:

**Left Column (approximately 40% width):**
- Date/time display and green status dot
- `Encounter` / `Visit Template` radio buttons
- `Select Encounter` dropdown
- `Overwrite all fields` / `Keep existing cc, hpi & ros` radio buttons
- Patient photo area (upper left of encounter section)
- Action buttons: `Enlarge Textbox | Set Flags | Set Remind | Risk Factors | Decision Support`
- `Chief Complaint` — text field
- `History of Present Illness` — multi-line scrollable text area
- `Review of Systems` — text area
- `Past Medical History` — text area
- `Social History` — dropdown + text area
- `Family History` — text/structured radio + text area
- `Allergies` — text area (with allergy icon)
- `Current Medications` — numbered list text area

**Right Column (approximately 60% width):**
- Tabs: `Physical Exam | Pictures | Illustrations | Confidential`
- Vitals grid (Weight, Height, Temp, BP, Pulse, RR, BMI, Sat%, on O2)
- Vitals history table below grid
- Physical exam free text area
- `Diagnoses` section with search field and `Problem List` dropdown
- `Assessment` text area
- Bottom tabs: `Plan | CDS | Instructions | Goals | Health Concerns`
- Health Maintenance table (shows recommended screenings with Last/Next dates)
- Right sidebar buttons: `Clinical Assessment | Write Orders | Write Scripts | Patient Ed Given`
- Bottom right: `Forward Chart` button (blue), `Sign-Off` button (white/outlined)

**Status Bar (bottom of chart window):**
```
[age] year old [sex] last seen [X] months ago ([date]) by [Provider], [Credentials]:
[Next appointment info]
```
Right side of status bar: `[Provider username]  [date]`

---

## Patient Menu

### Observed from: navigate_to_clinical_summary.png, patient__print_last_note_menu_tab.png

Accessed via the menu bar: `Patient` (or keyboard shortcut Alt+P when chart is open).

**Full Patient Menu Items with Keyboard Shortcuts:**
```
Add New Patient
Check In/Out
Patient Flow Tracking              ►  (submenu)
─────────────────────────────────────
Alerts & Directives
Account Information                F11
─────────────────────────────────────
General Info Demographics          F5
Billing Info Demographics
Summary Sheet                      F6
Most Recent Encounter              F7
Past Encounters                    F8
Imported Items                     F9
─────────────────────────────────────
Medications & ePrescribing         Ctrl+M
Orders & Requisitions
─────────────────────────────────────
Health (Risk) Factors              Ctrl+H
Immunizations & Injections         Ctrl+I
─────────────────────────────────────
Add Chart Addendum
Secure Message
Set A Reminder
Open Practice Rolodex
Make Patient Inactive
─────────────────────────────────────
Search Appointments
Did Not Keep Appointment
─────────────────────────────────────
Print                              ►  (submenu — see below)
─────────────────────────────────────
Preview and Import PHI
Export Transition of Care Document
Export Clinical Summary            ← KEY FEATURE
Export to HIE and PHRs
```

### Print Submenu
Accessed via `Patient > Print`:
```
Demographics                       Ctrl+D
Encounter Sheet
Formal Health Record
Immunizations
Lab/Xray Order
Messages                           Ctrl+G
Medications
Notes & Letters                    ← KEY FEATURE for note export
Encounters/Notes by Date Range
Summary Sheet                      Ctrl+P
Tracked Data                       Ctrl+T
```

---

## Printing / Exporting Notes

### Feature Usage: Note Reformatter (F31), Pre-Visit Note Prep (F9)

### Method 1: Patient > Print > Notes & Letters

**Navigation:**
```python
# Keyboard sequence to open Notes & Letters:
# Requires a patient chart to be open first
import pyautogui
import time

pyautogui.hotkey('alt', 'p')          # Open Patient menu
time.sleep(0.3)
pyautogui.press('up')                 # Navigate to Print (near bottom of menu)
# OR: click Print menu item directly
# Then hover right for submenu
# Then click "Notes & Letters"
```

**Print Encounters / Send Letter Dialog:**
Observed from: print_notes_letters_last_note_opening_page_.png and
print_notes_letters_last_note_opening_page_variable_2_.png

This dialog has two sections:

**Section 1 — Select Note (left panel, titled "1. Select Note"):**
- List of past encounters, one per row
- Each row format: `[Date]  [Age] [sex] [chief complaint] [CPT codes, truncated]`
- Example: `11/17/25: CPX (High Complexity > 3008F, 3351F, 1036F...`
- Most recent encounter is at the top and pre-selected (highlighted in blue)
- Scroll down to see older encounters
- Buttons below list: `View Saved Messages | View Saved Addenda | Close Window`

**Section 2 — Select Header for Printed Note (right panel, titled "2. Select Header"):**
Dropdown with these exact options:
```
Patient education:
Detailed Note (without header)
Detailed Note (with Practice header)    ← default selection highlighted
Detailed Note (with Customized header)
Detailed LARGE Note (without header)
Detailed LARGE Note (with Practice header)
Detailed LARGE Note (with Customized header)
History & Physical
SOAP Note (without header)
```

**Action Buttons:**
- `Print All` — prints all encounters
- `Print Preview` — opens print preview window
- `Print To Default Printer` — prints immediately

**Letter Writer section (bottom right):**
- `TO PATIENT` / `List All Contacts` radio buttons
- `Consultants Only` / `Referring Providers Only` / `Other Only` radio buttons
- Provider dropdown
- `Compose Letter` button

**Checkbox at bottom:**
`☑ Do not automatically open this window after signing a note`

**For CareCompanion Note Reformatter automation:**
```python
def print_last_note_to_pdf(output_path: str):
    """
    Opens the Print Encounters dialog, selects the most recent note,
    and prints to the default PDF printer.
    
    Prerequisites:
    - Amazing Charts must be the foreground window
    - A patient chart must be open
    - A PDF printer (e.g., Microsoft Print to PDF) must be set as default
      OR use the Export Clinical Summary method instead (preferred)
    """
    # Step 1: Open Patient menu
    pyautogui.hotkey('alt', 'p')
    time.sleep(0.4)
    
    # Step 2: Navigate to Print > Notes & Letters
    # TODO: Calibrate exact click coordinates for Print submenu item
    # The Print item is near the bottom of the Patient menu
    
    # Step 3: In the dialog, most recent note is pre-selected
    # Select "Detailed Note (with Practice header)" from dropdown
    
    # Step 4: Click Print Preview or Print To Default Printer
    pass
```

---

## Export Clinical Summary (Preferred Export Method)

### Feature Usage: Note Reformatter (F31), Clinical Summary data ingestion

### Observed from: navigate_to_clinical_summary.png, clin_sum_export_scceed.png, ClinicalSummary_PatientId_62815_20260316_130657.xml

**This is the PREFERRED method for extracting structured patient data.**
The Clinical Summary exports a machine-readable XML file (HL7 CDA / CCD format)
containing demographics, medications, allergies, diagnoses, vitals, lab results,
and encounter data — far richer than OCR of a printed note.

### Navigation Path
```
Patient menu > Export Clinical Summary
```
Keyboard: `Alt+P` to open Patient menu, then click `Export Clinical Summary`
(near bottom of menu, above "Export to HIE and PHRs")

### Clinical Summary Dialog
Observed from: clin_sum_export_scceed.png

**Title:** `Clinical Summary`

**Section 1 — Select Encounter Date:**
Dropdown at top: `Select Encounter Date:`
Dropdown shows encounters in format: `[date]: [age/sex description], [chief complaint]...`
Example observed: `3/16/2026: 59 yr old male, body aches, wheezing, cough, f...`

**Section 2 — Choose information to include (checkboxes):**

Header Information:
- ☑ Patient Demographics
- ☑ Provider and Office Information
- ☑ Date and Visit Location

Clinical Information (two-column layout):
Left column:
- ☑ Allergies
  - ☑ Include Inactive
- ☑ Assessments
- ☑ Chief Complaints
- ☑ Encounter Details
- ☑ Goals
- ☑ Health Concerns
- ☑ Immunizations
- ☑ Instructions
- ☑ Insurance (partially visible)

Right column:
- ☑ Laboratory Test Results (All)
- ☑ Medical Equipment
- ☑ Medications
- (additional items partially visible)

Additional item:
- ☐ Reason For Referral (unchecked by default)

**Section 3 — Print/Export/Send buttons:**
Row of action buttons:
- `Print Preview`
- `Print`
- `Export` ← **USE THIS for file-based export**
- `Send to Portal`

**Export Location field:**
Text field showing current export path.
Example observed: `C:\Users\FPA\Desktop\Patient Notes\Companion_Clin...`
`...` browse button to change location.
`Save Settings` button — saves the export path for future use.

**Close button** at bottom left.

### Export Success Dialog
After clicking Export, a modal dialog confirms success:

**Title:** `Export Succeeded`

**Message:**
```
The Clinical Summary was exported to
C:\Users\FPA\Desktop\Patient Notes\Companion_Clin_Sum_Export\ClinicalSummary_PatientId_[ID]_[YYYYMMDD]_[HHMMSS].xml.
```
Button: `OK`

### Exported File Naming Convention
```
ClinicalSummary_PatientId_[MRN]_[YYYYMMDD]_[HHMMSS].xml
```
Example: `ClinicalSummary_PatientId_62815_20260316_130657.xml`

The MRN is embedded in the filename — use this to match the file to the
patient without parsing the XML.

```python
import re
import os

def find_latest_clinical_summary(export_folder: str, mrn: str) -> str | None:
    """
    Finds the most recently exported Clinical Summary XML for a given MRN.
    Files are named: ClinicalSummary_PatientId_[MRN]_[YYYYMMDD]_[HHMMSS].xml
    """
    pattern = re.compile(
        rf'ClinicalSummary_PatientId_{re.escape(mrn)}_(\d{{8}})_(\d{{6}})\.xml'
    )
    matches = []
    for filename in os.listdir(export_folder):
        m = pattern.match(filename)
        if m:
            # Sort key: YYYYMMDD + HHMMSS as a single integer
            sort_key = int(m.group(1) + m.group(2))
            matches.append((sort_key, os.path.join(export_folder, filename)))
    
    if not matches:
        return None
    return sorted(matches, reverse=True)[0][1]
```

### Automating the Export
```python
def export_clinical_summary(mrn: str, export_folder: str) -> str | None:
    """
    Automates Patient > Export Clinical Summary for the currently open chart.
    Returns the path to the exported XML file, or None on failure.
    
    Prerequisites:
    - Amazing Charts is the foreground window
    - The correct patient chart is open
    - export_folder exists and is writable
    - Export Location has been pre-configured in AC (use Save Settings once manually)
    """
    import pyautogui
    import time
    
    # Verify AC is foreground
    if not is_amazing_charts_active():
        raise RuntimeError("Amazing Charts is not the foreground window")
    
    # Open Patient menu
    pyautogui.hotkey('alt', 'p')
    time.sleep(0.4)
    
    # Click "Export Clinical Summary"
    # TODO: Calibrate coordinates — it is near the bottom of the Patient menu,
    # above "Export to HIE and PHRs", below "Export Transition of Care Document"
    # pyautogui.click(PATIENT_MENU_EXPORT_CLINICAL_SUMMARY_X,
    #                 PATIENT_MENU_EXPORT_CLINICAL_SUMMARY_Y)
    time.sleep(0.5)
    
    # Clinical Summary dialog opens
    # The most recent encounter is pre-selected in the dropdown
    # All checkboxes default to checked — accept defaults
    
    # Click Export button
    # TODO: Calibrate Export button coordinates in the dialog
    # pyautogui.click(CLINICAL_SUMMARY_EXPORT_BTN_X,
    #                 CLINICAL_SUMMARY_EXPORT_BTN_Y)
    time.sleep(1.0)  # Wait for file write
    
    # Dismiss success dialog by pressing Enter (OK button)
    pyautogui.press('enter')
    time.sleep(0.3)
    
    # Find the exported file
    return find_latest_clinical_summary(export_folder, mrn)
```

---

## Clinical Summary XML Structure

### Observed from: ClinicalSummary_PatientId_62815_20260316_130657.xml

The exported XML is a standard HL7 CDA (Clinical Document Architecture) /
Consolidated CDA (C-CDA) document. This is machine-readable and structured —
far superior to OCR for data extraction.

### Key XML Sections and XPath Patterns

```python
import xml.etree.ElementTree as ET

# Namespace — required for all XPath queries
NS = {
    'cda': 'urn:hl7-org:v3',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

def parse_clinical_summary(xml_path: str) -> dict:
    """
    Parses an Amazing Charts Clinical Summary XML export.
    Returns a structured dict with all clinical sections.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    result = {
        'patient': extract_patient_demographics(root),
        'medications': extract_medications(root),
        'allergies': extract_allergies(root),
        'diagnoses': extract_diagnoses(root),
        'vitals': extract_vitals(root),
        'lab_results': extract_lab_results(root),
        'immunizations': extract_immunizations(root),
        'encounters': extract_encounters(root),
    }
    return result


def extract_patient_demographics(root) -> dict:
    """Extracts patient name, DOB, MRN, sex from CDA header."""
    patient = root.find('.//cda:recordTarget/cda:patientRole', NS)
    if patient is None:
        return {}
    
    # MRN from extension attribute
    mrn_elem = patient.find('cda:id', NS)
    mrn = mrn_elem.get('extension') if mrn_elem is not None else None
    
    # Name
    name = patient.find('.//cda:patient/cda:name', NS)
    given = name.find('cda:given', NS)
    family = name.find('cda:family', NS)
    
    # DOB
    dob_elem = patient.find('.//cda:patient/cda:birthTime', NS)
    dob_raw = dob_elem.get('value') if dob_elem is not None else None
    # Format: YYYYMMDD → MM/DD/YYYY
    
    # Sex
    sex_elem = patient.find('.//cda:patient/cda:administrativeGenderCode', NS)
    sex_code = sex_elem.get('code') if sex_elem is not None else None
    # 'F' = female, 'M' = male
    
    return {
        'mrn': mrn,
        'last_name': family.text if family is not None else '',
        'first_name': given.text if given is not None else '',
        'dob_raw': dob_raw,
        'sex_code': sex_code,
    }


def extract_medications(root) -> list:
    """
    Extracts current medications from the Medications section.
    Section templateId: 2.16.840.1.113883.10.20.22.2.1 (Medications)
    Returns list of dicts with drug_name, dose, frequency, status.
    """
    # TODO: implement XPath extraction for medication entries
    # Each medication is in a <substanceAdministration> element
    pass


def extract_diagnoses(root) -> list:
    """
    Extracts problem list / diagnoses.
    Section templateId: 2.16.840.1.113883.10.20.22.2.5 (Problem List)
    Returns list of dicts with icd10_code, display_name, onset_date, status.
    """
    pass


def extract_lab_results(root) -> list:
    """
    Extracts laboratory test results.
    Section templateId: 2.16.840.1.113883.10.20.22.2.3 (Results)
    Returns list of dicts with test_name, value, units, date, flag.
    """
    pass
```

### Why XML Export is Preferred Over OCR for Note Reformatter

| Method | Reliability | Structure | PHI Risk |
|--------|-------------|-----------|----------|
| OCR of printed note | ~80% (font/layout dependent) | None — raw text | Low |
| XML Clinical Summary | ~99% (structured data) | Full HL7 CDA | None (local file) |

**For Feature F31 (Note Reformatter):** Parse the Clinical Summary XML first
to extract medications, diagnoses, allergies, and demographics reliably.
Fall back to OCR of the printed note only for narrative sections (HPI, Assessment,
Plan) that are not structured in the XML.

---

## Reports / Search Tool

### Observed from: reports_tab.png

Accessed via: Toolbar `Reports` button, or the menu.

**Window Title:** `Search Amazing Charts`

**Tab bar at top:**
```
Common Searches  |  Population Health  |  MIPS
```

**Common Searches Tab Layout:**
- Left panel: `Category` list (scrollable):
  ```
  Demographics
  Medications
  Diagnoses
  Allergies
  Notes & Encounters
  Vital Signs (most recent)
  Health Maintenance
  Health Risk Factors
  Schedule
  Laboratory & Orders
  Billing & Coding
  ```
- Center: `Field` list (populates after category selected)
- `Alphabetize` checkbox
- `Operator` dropdown
- `Value` text field
- Instruction text: "Like and Not Like requires use of a wildcard (%)."
- `Add Criteria to Query` button (right side)

**Query Criteria section (middle):**
Table with columns: `Operator | Category | Fields | Value`
Buttons: `Start Over | Remove Selected Criteria`
Logic selector: `If more than 1 line, make lines: ● AND ○ OR Statements`

**Run Report** button (large, prominent)

**Save/Delete buttons:** `Save This | Delete Saved | Save This Query As...`

**Query Results section (bottom):**
Right-click any result row for options.
`Saved Queries:` dropdown.

**Bottom action buttons:**
```
Hide/Show Columns  |  [checkboxes]  |  De-Identify Results  |  Select All  |  Mail Email  |  Print  |  Export
```

**Note for Care Gap Tracker (F15) and Panel Reports (F15c):**
This Reports tool has a built-in query builder with access to Demographics,
Diagnoses, Health Maintenance, and Schedule categories. For panel-wide care
gap reports, consider automating queries here via PyAutoGUI rather than
reading individual charts, as it is faster and more reliable.

---

## Export to HIE and PHRs

### Observed from: export_to_HIE___PHR.png

Accessed via: `Patient > Export to HIE and PHRs`

**Export to HIEs and PHRs dialog:**
- Dropdown showing the most recent encounter for reference
- Buttons: `Close | Configure | CCD Settings | Export`

**HIE and PHR Configuration dialog:**
- Shows patient name, DOB, and ID in title: `HIE and PHR Configuration for [NAME]  (DOB: MM/DD/YYYY; ID: [MRN])`
- Left panel: `Available HIEs and PHRs` list (Microsoft HealthVault, Updox Portal observed)
- Right panel: `HIEs and PHRs for [NAME]` — table of configured connections
- Buttons: `Admin | Add >> | << Remove | Subscription | Close`

**Note:** This feature is NOT used by CareCompanion. The `Export Clinical Summary`
method (XML) is used instead. This dialog is documented only for completeness.

---

## Printed Note PDF Format

### Observed from: testprint_last_note.pdf (test_summary.pdf)

When printing via `Patient > Print > Notes & Letters` using the
"Detailed Note (with Practice header)" option, the output PDF has this structure:

### Page Header (every page)
```
[Header type selected]  ← e.g., "Patient education:"
[LASTNAME], [FIRSTNAME]  (DOB: MM/DD/YYYY  ID: [MRN])  [Date]  [Day of week]  [Time]
```

### Note Sections and Labels (observed exact text)
The printed note uses these exact section label formats:
```
CC      ← Chief Complaint
HPI     ← History of Present Illness
PMH     ← Past Medical History
SH      ← Social History (with tobacco dropdown value prepended)
FH      ← Family History
Meds    ← Current Medications (numbered list)
PE      ← Physical Exam
A/P     ← Assessment and Plan
```

**Important for note_parser.py (F31):**
These are the short-form section labels used in the printed note PDF.
The parser must recognize BOTH short forms (CC, HPI, PMH, SH, FH, Meds, PE, A/P)
AND long forms (Chief Complaint, History of Present Illness, etc.) to handle
notes from different providers or formatting styles.

### Medications Format in Printed Note
```
1) [drug name] [dose] [form], [directions]
2) [drug name] [dose] [form], [directions]
```
Each medication on a numbered line. Parser should split on `^\d+\)` regex.

### Assessment/Plan Format
```
# [Diagnosis] ([ICD-10 code]):[Plan text]
# [Diagnosis] ([ICD-10 code]):[Plan text]
PRESCRIBE: [drug] [dose] [form], [directions], #[qty], RF: [refills].
ORDERED/ADVISED: Order Date [date]
- ..[order name]([CPT code]) ...
```
Each diagnosis prefixed with `#`. Prescriptions prefixed with `PRESCRIBE:`.
Orders prefixed with `ORDERED/ADVISED:`.

### Page Footer
```
Amazing Charts
The information on this page is confidential.
Any release of this information requires the written authorization of the patient listed above.
Page [N] of [N]
Printed By: [Provider Name], [Credentials]  [MM/DD/YYYY HH:MM:SS AM/PM]
```

---

## Key Keyboard Shortcuts Summary

For use in PyAutoGUI automation scripts. All shortcuts require a patient
chart window to be open and focused.

```python
AC_SHORTCUTS = {
    # Chart navigation
    'demographics':          'f5',
    'summary_sheet':         'f6',
    'most_recent_encounter': 'f7',
    'past_encounters':       'f8',
    'imported_items':        'f9',
    'account_information':   'f11',
    
    # Patient menu actions
    'medications':           ('ctrl', 'm'),
    'health_risk_factors':   ('ctrl', 'h'),
    'immunizations':         ('ctrl', 'i'),
    'print_summary_sheet':   ('ctrl', 'p'),
    'print_messages':        ('ctrl', 'g'),
    'tracked_data':          ('ctrl', 't'),
    
    # Open Patient menu
    'patient_menu':          ('alt', 'p'),
}
```

---

## Export Folder Configuration

**Recommended folder structure for CareCompanion:**
```
C:\Users\[username]\Desktop\Patient Notes\
├── Companion_Clin_Sum_Export\    ← Clinical Summary XMLs (configure in AC once)
│   └── ClinicalSummary_PatientId_[MRN]_[YYYYMMDD]_[HHMMSS].xml
└── Companion_Note_Prints\        ← PDF note prints (if using print method)
    └── [MRN]_[YYYYMMDD]_[HHMMSS].pdf
```

The export folder path is saved in `config.py`:
```python
# In config.py:
CLINICAL_SUMMARY_EXPORT_FOLDER = r'C:\Users\FPA\Desktop\Patient Notes\Companion_Clin_Sum_Export'
NOTE_PRINT_EXPORT_FOLDER = r'C:\Users\FPA\Desktop\Patient Notes\Companion_Note_Prints'
```

The Clinical Summary export location must be configured once manually in
Amazing Charts (Patient > Export Clinical Summary > set Export Location >
click Save Settings). After that, the automation can click Export without
changing the path.

---

## Automation Strategy Summary for CareCompanion

Based on all observed screenshots and exports, the recommended automation
approach per feature is:

| Feature | Method | Reliability | Notes |
|---------|--------|-------------|-------|
| MRN detection (F6) | win32gui title bar parse | High | No OCR needed |
| Inbox monitoring (F5) | OCR on inbox table region | Medium | Use filter dropdowns |
| Clinical data extraction (F31) | XML Clinical Summary export | High | Preferred |
| Note text extraction (F31) | PDF print + OCR fallback | Medium | For narrative only |
| Order execution (F8) | PyAutoGUI click sequence | Medium | Needs calibration |
| Note creation (F9) | PyAutoGUI keyboard + click | Medium | Needs calibration |
| Patient search | PyAutoGUI + Patient List panel | Medium | Type in ID field |
| Care gap data | XML Clinical Summary (Health Maintenance section) | High | Parse XML |
| Medication list | XML Clinical Summary (Medications section) | High | Parse XML |
| Lab results | XML Clinical Summary (Results section) | High | Parse XML |

---

*This document was generated from live Amazing Charts screenshots captured
on 3/16/2026. Updated 3/17/2026 with system information, login flow, process
names, database path, Summary Sheet, Past Encounters, Imported Items, and
additional interface details. See image filenames referenced in each section.*

---

## CRITICAL DISCOVERY — Direct Database Access May Be Possible

### Observed from: about_amazing_charts__practice_id__version_number_accessed_from_top_menu_help__about.png, about_s_system_information_button_opens_this_window.png

The Amazing Charts database is a **SQL Server .mdf file on a network share**:

```
\\192.168.2.51\Amazing Charts\AmazingCharts.mdf
```

This is the single most important piece of information in this entire reference.
If a SQL Server connection can be established to 192.168.2.51, all inbox data,
patient records, medications, labs, and diagnoses can be queried directly —
eliminating the need for OCR and PyAutoGUI for data retrieval entirely.

```python
# Potential direct database connection (test before building OCR fallbacks)
# Server is on the local network at 192.168.2.51
# Database file: AmazingCharts.mdf
# Driver: SQL Server (likely SQL Server Express)

import pyodbc

# Attempt 1 — Windows Authentication (most likely for a local network share)
conn_str = (
    r'DRIVER={SQL Server};'
    r'SERVER=192.168.2.51;'
    r'DATABASE=AmazingCharts;'
    r'Trusted_Connection=yes;'
)

# Attempt 2 — Named instance (SQL Server Express default)
conn_str_named = (
    r'DRIVER={SQL Server};'
    r'SERVER=192.168.2.51\SQLEXPRESS;'
    r'DATABASE=AmazingCharts;'
    r'Trusted_Connection=yes;'
)

def test_db_connection() -> bool:
    """
    Test whether direct SQL Server access is available.
    Run this FIRST before building any OCR/PyAutoGUI automation.
    If this returns True, the entire OCR strategy can be replaced with
    direct SQL queries.
    """
    for conn_str in [conn_str, conn_str_named]:
        try:
            conn = pyodbc.connect(conn_str, timeout=5)
            conn.close()
            return True
        except:
            continue
    return False
```

**If database access is confirmed:** Update agent/inbox_monitor.py,
agent/clinical_summary_parser.py, and agent/mrn_reader.py to use SQL
queries instead of OCR. Reliability goes from Medium to High for all
data retrieval operations.

**The AC log path** (from ACLOGPATH environment variable):
```
C:\Program Files (x86)\Amazing Charts\Logs
```
Log files here may contain patient interaction history useful for audit
correlation. Check this folder for structured log formats.

---

## Amazing Charts Version and Installation Details

### Observed from: about_amazing_charts__practice_id__version_number_accessed_from_top_menu_help__about.png, amazing_charts_properties.png

**Version:** Amazing Charts 12.3.1, build 297
**Practice ID:** 2799
**Practice Name:** Family Practice Associates of Chesterfield
**Registration Number:** 06041130609159

**Executable location:**
```
C:\Program Files (x86)\Amazing Charts\AmazingCharts.exe
```

**File properties:**
- Type: Application (.exe), 32-bit
- Size: 38.7 MB (40,623,744 bytes)
- Description: Amazing Charts EHR
- Created/Modified: Monday, September 15, 2025, 3:57:58 PM

**Configuration file:**
```
C:\Program Files (x86)\Amazing Charts\SystemSettings.xml
```
This XML file contains practice-wide settings. May be readable for
configuration data without launching AC.

**How to access About dialog:**
```
Menu bar: Help > About
```
The About dialog also has a `System Information` button that opens
the Windows System Information (msinfo32) tool.

```python
# Update config.py with confirmed values:
AMAZING_CHARTS_EXE = r'C:\Program Files (x86)\Amazing Charts\AmazingCharts.exe'
AMAZING_CHARTS_CONFIG = r'C:\Program Files (x86)\Amazing Charts\SystemSettings.xml'
AMAZING_CHARTS_LOGS = r'C:\Program Files (x86)\Amazing Charts\Logs'
AMAZING_CHARTS_DB_SERVER = '192.168.2.51'
AMAZING_CHARTS_DB_PATH = r'\\192.168.2.51\Amazing Charts\AmazingCharts.mdf'
AMAZING_CHARTS_VERSION = '12.3.1'
AMAZING_CHARTS_BUILD = '297'
AMAZING_CHARTS_PRACTICE_ID = '2799'
```

---

## Work PC System Specifications

### Observed from: work_computers__system_info_.png, about_s_system_information_button_opens_this_window.png

**IMPORTANT:** The work PC runs **Windows 11 Pro**, not Windows 10.
Previous documentation referenced Windows 10 — update all references.

```python
# Confirmed work PC system details for config.py
WORK_PC_SYSTEM_NAME = 'FPA-D-NP-DENTON'
WORK_PC_USERNAME = 'FPA-D-NP-DENTON\\FPA'
WORK_PC_OS = 'Microsoft Windows 11 Pro'
WORK_PC_OS_BUILD = '10.0.26100 Build 26100'
WORK_PC_MODEL = 'HP EliteDesk 705 G5 Desktop Mini'
WORK_PC_PROCESSOR = 'AMD Ryzen 5 PRO 3400G with Radeon Vega Graphics, 3700 MHz, 4 Cores'
WORK_PC_RAM_GB = 16
WORK_PC_TIMEZONE = 'Eastern Daylight Time'
WORK_PC_GPU = 'AMD Radeon(TM) Vega 11 Graphics'
```

**Relevant for PyAutoGUI:** The AMD Radeon Vega 11 integrated graphics may
affect screenshot color rendering. If OCR results are inconsistent, try
adjusting image preprocessing contrast values for this GPU.

**Available physical memory: 4.31 GB** at time of screenshot — AC was
consuming roughly 166 MB (from Task Manager). Keep CareCompanion's memory
footprint minimal; this machine is not heavily resourced.

---

## Amazing Charts Process Names (Confirmed)

### Observed from: task_manager__number_1_is_the_AC_login_page___2_is_once_the_login_is_done_and_the_hope_page_has_loaded.png

Task Manager shows Amazing Charts as a process group:

```
Amazing Charts EHR (32 bit) (2)          ← parent group, always 32-bit
    ├── Amazing Charts                    ← #1: Login dialog only
    └── Amazing Charts  Family Practice Associates of Chesterfield  ← #2: Home screen loaded
```

**State detection logic:**

```python
import psutil

def get_ac_state() -> str:
    """
    Returns: 'not_running', 'login_screen', 'home_screen', 'chart_open'
    Based on process names observed in Task Manager.
    """
    ac_processes = []
    for proc in psutil.process_iter(['name', 'exe']):
        try:
            if 'amazing charts' in proc.info['name'].lower():
                ac_processes.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not ac_processes:
        return 'not_running'

    # Use win32gui to check window titles for more precision
    import win32gui
    titles = []
    def enum_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            titles.append(win32gui.GetWindowText(hwnd))
    win32gui.EnumWindows(enum_callback, None)

    # Login screen: window titled just "Amazing Charts" (no practice name)
    # Home screen: "Amazing Charts  Family Practice Associates of Chesterfield"
    # Chart open: "[LASTNAME], [FIRSTNAME]  (DOB: MM/DD/YYYY; ID: [MRN])"

    for title in titles:
        import re
        if re.search(r'DOB:.*ID:', title):
            return 'chart_open'
    for title in titles:
        if 'Family Practice' in title and title.startswith('Amazing Charts'):
            return 'home_screen'
    for title in titles:
        if title.strip() == 'Amazing Charts':
            return 'login_screen'

    return 'not_running'


# Process name for pywin32 window search:
AC_PROCESS_NAME = 'Amazing Charts EHR (32 bit)'
AC_LOGIN_WINDOW_TITLE = 'Amazing Charts'
AC_HOME_WINDOW_TITLE = 'Amazing Charts  Family Practice Associates of Chesterfield'
```

**Critical for automation:** Before any automated interaction, call
`get_ac_state()` to confirm AC is in the expected state. Never proceed
with home-screen automation if `chart_open` is returned (charts must be
closed for Clinical Summary export).

---

## Amazing Charts Login Flow

### Observed from: amazing_charts_login__typically_starts_with_the_proper_username_and_the_cursor_in_the_password_field.png, aamzing_charts_login__you_can_type_in_both_of_these_feilds.png, amazing_charts_open_location_no_monitor_1_of_2_at_fresh_load.png

**Login dialog window title:** `Amazing Charts`

**Login dialog layout:**
- Header: `Family Practice Associates of Chesterfield`
- Subheader: `Electronic Health Record System`
- `Username:` field — dropdown (pre-populated with last used username)
- `Password:` field — plain text input (cursor starts here when username is pre-filled)
- `Log In` button
- Advertising banner below (Amazing Charts Billing Service)
- Legal footer text

**Key behaviors observed:**
1. On a fresh AC launch, the Username dropdown is typically pre-filled with
   the last logged-in username (e.g., `CORY`). The cursor is already in
   the Password field — only the password needs to be typed.
2. The Username field IS editable — you can type directly or use the dropdown.
   Both fields accept keyboard input.
3. The login dialog appears at a non-standard screen position (observed
   overlapping other windows at approximately center-screen).

**Login automation:**

```python
def login_to_amazing_charts(username: str, password: str) -> bool:
    """
    Logs into Amazing Charts. Assumes AC is already launched and showing
    the login dialog (state = 'login_screen').

    Strategy:
    1. Find and focus the login window
    2. If username is already correct, Tab to password and type it
    3. If username needs to change, clear it and type the new username
    4. Type password and press Enter (or click Log In)
    """
    import win32gui
    import pyautogui
    import time

    # Find the login window
    login_hwnd = None
    def enum_callback(hwnd, _):
        nonlocal login_hwnd
        if win32gui.GetWindowText(hwnd) == 'Amazing Charts':
            if win32gui.IsWindowVisible(hwnd):
                login_hwnd = hwnd
    win32gui.EnumWindows(enum_callback, None)

    if not login_hwnd:
        return False

    win32gui.SetForegroundWindow(login_hwnd)
    time.sleep(0.3)

    # Username field — use Tab to move between fields
    # Field order: Username dropdown → Password field → Log In button
    pyautogui.hotkey('alt', 'u')  # May not work; use Tab navigation instead

    # Clear username and type new one if needed
    # TODO: Calibrate click coordinates for Username dropdown
    # Then: Tab to password field
    pyautogui.press('tab')
    time.sleep(0.2)

    # Type password (cursor should be in password field)
    pyautogui.typewrite(password, interval=0.05)
    pyautogui.press('enter')
    time.sleep(2.0)  # Wait for home screen to load

    return get_ac_state() == 'home_screen'
```

**Window position note:** From the multi-monitor screenshot
(amazing_charts_open_location_no_monitor_1_of_2_at_fresh_load.png),
AC opens on monitor 1 of 2. The login dialog position varies. Use
win32gui to find the window by title rather than fixed coordinates.

**Observed usernames in dropdown:** CORY, ADMIN (both confirmed visible
across screenshots).

---

## Resurrect Last Note Dialog

### Observed from: Fresh_load__note_resurrection_window__sometimes_opens__sometimes_not__.png

**This dialog appears intermittently on AC startup** — only when AC was
previously closed without saving or forwarding a note. It cannot be
predicted and must be handled by automation.

**Dialog title:** `Resurrect Last Note?`

**Dialog text:**
```
It appears Amazing Charts may have closed before your last note was
saved or forwarded.

Do you want to resurrect your last note?
```

**Buttons:** `Yes` | `No`

**Automation handling — always dismiss this dialog before proceeding:**

```python
import win32gui
import pyautogui
import time

def dismiss_resurrect_dialog() -> bool:
    """
    Checks for and dismisses the 'Resurrect Last Note?' dialog.
    Call this immediately after AC reaches home_screen state.
    Returns True if dialog was found and dismissed, False if not present.

    For CareCompanion: always click 'No' — pre-visit note prep creates
    fresh notes; resurrecting an old unsaved note would corrupt the workflow.
    """
    resurrect_hwnd = None
    def enum_callback(hwnd, _):
        nonlocal resurrect_hwnd
        if win32gui.GetWindowText(hwnd) == 'Resurrect Last Note?':
            resurrect_hwnd = hwnd
    win32gui.EnumWindows(enum_callback, None)

    if not resurrect_hwnd:
        return False

    win32gui.SetForegroundWindow(resurrect_hwnd)
    time.sleep(0.3)
    # Click 'No' — Tab to No button (Yes is default/first, No is second)
    pyautogui.press('tab')
    time.sleep(0.1)
    pyautogui.press('enter')
    time.sleep(0.5)
    return True


def wait_for_ac_ready(timeout_seconds: int = 30) -> bool:
    """
    Waits for AC to reach a usable home screen state, handling the
    resurrect dialog if it appears.
    Returns True when AC is ready, False on timeout.
    """
    import datetime
    deadline = datetime.datetime.now() + datetime.timedelta(seconds=timeout_seconds)

    while datetime.datetime.now() < deadline:
        state = get_ac_state()
        if state == 'home_screen':
            time.sleep(0.5)
            dismiss_resurrect_dialog()  # Handle if it appears after load
            return True
        elif state == 'login_screen':
            return False  # Need to login first
        time.sleep(1)

    return False
```

**Note:** The resurrect dialog appears on the AC home screen background,
not as a child of the login window. It will appear after `home_screen`
state is detected.

---

## AC Home Screen — Status Panel

### Observed from: amazing_charts_main_database_computer_IP.png

The bottom-left section of the AC home screen contains a fixed status
panel that is always visible:

```
AMAZING CHARTS STATUS
Main Computer: Your databases are on 192.168.2.51.
Licensing: This practice is licensed for 10 providers.
Maintenance & Support: Your practice is subscribed.
```

Below the status panel is a yellow marketing/news banner (MIPS webinar ad
observed). This banner changes and should be ignored by automation.

**This status panel confirms:** The database server IP (192.168.2.51) is
displayed in plain text on every AC home screen. This value can be read
via OCR on the status panel region as a fallback if config values are
not set.

```python
# The status panel is in the lower-left of the AC home screen
# Below the scheduling calendar, above the taskbar
# OCR this region to extract the database server IP:

def read_ac_status_panel() -> dict:
    """
    Reads the AMAZING CHARTS STATUS panel from the AC home screen.
    Returns dict with db_server_ip, provider_count, support_status.
    """
    import re
    # TODO: Calibrate AC_STATUS_PANEL_REGION in config.py
    # Approximate region: lower-left quadrant, below calendar
    region = config.AC_STATUS_PANEL_REGION  # (x, y, width, height)
    screenshot = pyautogui.screenshot(region=region)
    text = pytesseract.image_to_string(preprocess_for_ocr(screenshot))

    result = {}
    ip_match = re.search(r'databases are on ([\d.]+)', text)
    if ip_match:
        result['db_server_ip'] = ip_match.group(1)

    return result
```

---

## Summary Sheet Tab (F6)

### Observed from: patient_chat_summary_sheet_window_.png, chronicity_can_only_be_edited_from_this_location__clicking_the_chronicity_cell_associated_with_the_diagnosis.png, easier_way_to_access_problem_list_and_resolve_problems__putting_a_date_in_the_resolved_or_inactive_cell_completes_that_action.png

Accessed via: `F6` keyboard shortcut, or clicking the `Summary Sheet` tab
in an open patient chart.

**This is the richest single view in Amazing Charts for a patient.** It
shows problems, allergies, medications, immunizations/screenings, alerts,
and tracked data all on one screen.

### Summary Sheet Layout

**Left column (approximately 60% width):**

**Problems section:**
- Filter dropdown: `Show Active Problems Only` (default) / `Show All Problems`
- Action buttons: `Edit | Add | Resolve | Inactivate | Remove`
- Problem list table columns: `Problem | ICD | Active | Chronicity | Adding Provider`
- Each row: problem name (may be truncated), ICD-10 code, active date,
  chronicity value, provider last name
- Selected row highlighted in blue

**Allergies section:**
- Shows allergen icon + allergen name(s) as text
- Scrollable list

**Medications section:**
- Filter dropdown: `Show Active Medications Only`
- Action buttons: `Add | Inactivate | Write Scripts | Print`
- Medication list table columns: `Medication & Dosage | Sig.`
- Selected row highlighted in blue
- Shows full medication name, dose, form, and directions

**Decision Support & Injections section:**
- Three tabs: `Due | Complete | Injections`
- Action buttons: `Enlarge | Edit Rule | Refresh`
- Due table columns: `Name | Last | Next`
- Rows highlighted yellow = overdue or due soon
- Items include: screening recommendations, PHQ forms, vaccine due dates
- `Immunizations Only` checkbox, `Hide childhood` checkbox (checked by default),
  `Show Not Yet Due` checkbox
- `Migrate Old Vacs` button, `Print` button

**Right column (approximately 40% width):**

**Alerts & Directives section:**
- Flag icon + `Add/Edit` button
- `Name | Description` columns (empty in screenshot)

**Tracked Data/Flow Sheets section:**
- `Show All Data` checkbox, `Add/Edit | Remove | Graph | Print` buttons
- `Date | Item | Value` columns
- Example row: 3/16/2026 | PHQ-9 Patient Dx: | 0

**Reports & Resources section (bottom right):**
Three teal/cyan buttons:
- `Clinical Summary` ← **triggers the Clinical Summary export dialog**
- `Transition of Care`
- `Send Message to Patient`

**IMPORTANT:** The `Clinical Summary` button in the Summary Sheet's
Reports & Resources section is an **alternative path** to export the
clinical summary, in addition to `Patient menu > Export Clinical Summary`.
This button is accessible while in the patient chart (Summary Sheet tab),
but the export constraint (no open charts) still applies to the actual
export dialog that opens.

```python
# Summary Sheet keyboard shortcut
AC_SHORTCUTS['summary_sheet'] = 'F6'  # confirmed

# Clinical Summary button is in the bottom-right of the Summary Sheet
# Alternative path to: Patient menu > Export Clinical Summary
# TODO: Calibrate SUMMARY_SHEET_CLINICAL_SUMMARY_BTN coordinates
```

**Bottom status bar (Summary Sheet specific):**
```
Notes: 7    Messages: 2    Addenda: 0    DNKA: 0
```
(Did Not Keep Appointment count)

### Chronicity Editing

**Observed from: chronicity_can_only_be_edited_from_this_location__clicking_the_chronicity_cell_associated_with_the_diagnosis.png**

Chronicity can ONLY be set by clicking the `Chronicity` cell directly in
the Problems table on the Summary Sheet. It is not editable from any other
location in AC.

**Chronicity dropdown options (exact values):**
```
Acute
Chronic
Self-Limiting
Self-Limited (2 weeks)
Self-Limited (3 weeks)
Self-Limited (3 months)
Self-Limited (6 months)
Self-Limited (1 year)
```

This data is captured in the Clinical Summary XML under each diagnosis entry.

### Editing and Resolving Problems

**Observed from: easier_way_to_access_problem_list_and_resolve_problems__putting_a_date_in_the_resolved_or_inactive_cell_completes_that_action.png**

Clicking the `Edit` button on the Summary Sheet Problems section opens
a separate `Editing Problems` dialog with a spreadsheet-style layout:

**Dialog title:** `Editing Problems`

**Table columns:** `Problem | ICD | Active | Resolved | Inactive | Chronicity | Adding Provider`

**How to resolve a problem:** Type a date in the `Resolved` column cell
for that problem row and click `Save`. The date entry alone completes
the action — no other button press is required.

**How to inactivate a problem:** Type a date in the `Inactive` column cell.

**Dialog buttons:** `Cancel | Save`

```python
# The Editing Problems dialog is a separate window
# Title: 'Editing Problems'
# To resolve a problem via automation:
# 1. Click Edit button in Summary Sheet Problems section
# 2. Find the row matching the problem name
# 3. Click the Resolved cell for that row
# 4. Type the resolution date (MM/DD/YYYY format)
# 5. Click Save
# NOTE: This is relevant for the Note Reformatter (F31) if it needs to
# update problem statuses, and for the Care Gap tracker (F15)
```

---

## Past Encounters Tab (F8)

### Observed from: patietn_chart_past_encounters_tab__also_has_filter_encounters_by_certian_criteria_next_to_the_note_display_window__.png

Accessed via: `F8` keyboard shortcut, or clicking the `Past Encounters` tab.

**This tab is the most useful source for reading prior note text** without
using the print/export pathway. The note content is displayed as plain text
in the preview panel and can be read via OCR.

### Past Encounters Layout

**Left panel — Filters:**

Radio buttons for content type:
- `Orders`
- `Progress Notes Only`
- `All Encounters, Messages, Addenda` ← selected by default
- `Messages`
- `Addenda`
- `Show Refill Requests` checkbox

**Filter Encounters By section:**
Radio buttons:
- `Show all` ← default
- `Medications Only`
- `Physical Exam Only`
- `Vital Signs Only` (with unit dropdown: lb)
- `Assessment and Plan Only`

Dropdown filters:
- `ICD-9` dropdown
- `ICD-10` dropdown
- `Provider` dropdown
- `Date` checkbox + date range pickers (from / to)

**Right panel — Encounter List (upper):**
Table columns: `Date | Type | Subject`
Sort options: `Sort Newest to Oldest` ● (default) / `Sort Oldest to Newest`

Each row: date, type (Encounter/Message), subject (chief complaint truncated)
Selected row highlighted in blue.

**Note preview panel (lower right):**
Plain text display of the selected encounter's full note content.
Sections are labeled in plain text:
```
NOTE  (Monday January 5, 2026  02:03 PM)

Chief Complaint:
[text]

History of Present Illness:
[text]

Past Medical History:
[text]

Family History:
[text]

Social History:
[text]

Medications:
1) [drug...]
2) [drug...]
```

`Print Item` button (bottom right of preview).

**Note instruction at top:** "previously saved orders, notes, messages,
and addenda"

```python
# Past Encounters is a valuable OCR source for note text
# The plain text preview panel renders notes with section headers
# This is an ALTERNATIVE to the PDF print method for note extraction
# OCR the preview panel region after selecting the desired encounter

# Navigation:
# F8 → Past Encounters tab
# Most recent encounter is pre-selected (top row, blue highlight)
# The note preview shows immediately below the encounter list
# No additional click needed to show the most recent note preview

# For Note Reformatter (F31): consider reading from this panel
# instead of triggering the full print/export workflow
# Advantage: no dialog boxes, no PDF generation
# Disadvantage: text may be truncated or wrapped differently than PDF

AC_SHORTCUTS['past_encounters'] = 'F8'  # confirmed
```

---

## Select Encounter Dropdown (Most Recent Encounter Tab)

### Observed from: select_encounter_op_wnn_pulls_the_selected_historical_chart_and_fills_in_all_text_boxes_with_that_informaiton__.png

In the Most Recent Encounter tab (F7), the `Select Encounter` dropdown
at the top of the chart allows loading any historical encounter into
all text boxes. This populates the entire note form with past data.

**Dropdown format:** `MM/DD/YY CC: [chief complaint text truncated]`

**Confirmed encounter list for test patient:**
```
Select Encounter        ← default (blank)
01/05/26 CC: "cough" [Upc...  ← most recent
11/20/25 CC:
02/22/25 CC:
12/06/23 CC: telemed f/u A   ← highlighted/selected in screenshot
11/02/23 CC: AWV
06/21/23 CC: olkpjniuginb7t
06/21/23 CC: moin
```

**Behavior:** Selecting an encounter from this dropdown fills ALL text
fields in the Most Recent Encounter tab with that historical encounter's
data. The radio button `Overwrite all fields` vs `Keep existing cc, hpi & ros`
controls whether existing content is replaced.

**Relevance to Note Reformatter (F31):** This dropdown provides access
to any historical note. For the pre-charting workflow, selecting a past
comprehensive note (AWV, CPX) and reading all text boxes is an alternative
to the PDF export method.

```python
# To load a historical note into the encounter form:
# 1. Press F7 to open Most Recent Encounter tab
# 2. Click the Select Encounter dropdown
# 3. Select the desired encounter by text match
# 4. Radio button: select "Overwrite all fields" before selecting
# 5. After selection, all text boxes are populated with historical data
# 6. OCR each text box region to read the content

# The dropdown items follow format: MM/DD/YY CC: [text]
# Parse encounter date from the dropdown item text using:
import re
# re.match(r'(\d{2}/\d{2}/\d{2})\s+CC:\s*(.*)', dropdown_item)
```

---

## Imported Items Tab (F9)

### Observed from: imported_items__selecting_date_range_allows_filters_of_3_month__6month__9_month__1_year__2_year_or_all__some_patient_have_thousands_of_imported_items_and_it_takes_a_long_time_to_laod_the_lsit__.png

Accessed via: `F9` keyboard shortcut, or clicking `Imported Items` tab.

**WARNING:** Some patients have thousands of imported items. Loading this
tab with `All` selected can take a very long time. Automation should
always apply a date filter before loading this tab.

### Imported Items Layout

**Tab-specific menu bar:** `Import | File | View | Help` (different from
the main AC menu bar)

**Left toolbar buttons:** `Import New | Reminder`

**Sort options:** `Title` / `Date` ● (radio buttons)

**Date Range filter:** Dropdown with options:
```
3 month
6 month
9 month
1 year
2 year
All        ← avoid for patients with large records
```
With `All` / [date range] radio buttons.

**Left panel — File tree:**
Items organized in folders by category:
```
CLINICAL ASSESSMENT
    PHQ-2 (FORMS) (10/10/23)
    PHQ-2 (IMPORT) (10/10/23)
CLINICAL ASSESSMENTS
    PHQ-9 Patient Depression Questionnaire (03/16/26)
OUTBOUND LETTERS
    Letter to TEST TEST (03/26/24)    ← selected, highlighted
    Letter to TEST TEST (03/26/24)
    Letter to TEST TEST (03/26/24)
```

**Right panel — Document viewer:**
- Document metadata header: Date, Type, Subject, Comment, file path
- Full PDF/document viewer with zoom, page navigation, print controls
- `Print Comments | Print Item` buttons at bottom

**Document path format observed:**
```
\\192.168.2.51\amazing charts\ImportItems\[MRN]\[filename].pdf
```
This reveals that imported items are stored as files on the same server
as the database (192.168.2.51), under the patient's MRN as a folder name.

```python
# Imported items file path structure:
# \\192.168.2.51\amazing charts\ImportItems\[MRN]\[UUID].pdf
# This means imported documents may be directly accessible as files
# without needing to navigate through the AC UI

IMPORTED_ITEMS_PATH_TEMPLATE = r'\\192.168.2.51\amazing charts\ImportItems\{mrn}\'

# For reading lab PDFs, letters, or clinical assessments:
# Option 1: Navigate through AC UI (slow, OCR required)
# Option 2: Access files directly via the network share (fast, no AC needed)
# The direct file path is shown in the document header when viewing in AC

AC_SHORTCUTS['imported_items'] = 'F9'  # confirmed
```

---

## System Environment Variables (AC-Relevant)

### Observed from: system_software_environment_variables_.png

From System Information > Software Environment > Environment Variables:

**AC-specific variable:**
```
ACLOGPATH = C:\Program Files (x86)\Amazing Charts\Logs
```
The AC application log directory. Check here for error logs and
interaction history that may supplement automation debugging.

**Other relevant system variables:**
```
USERNAME = SYSTEM (or FPA-D-NP-DENTON\FPA for user context)
PROCESSOR_ARCHITECTURE = AMD64
NUMBER_OF_PROCESSORS = 8
OneDrive = C:\Users\FPA\OneDrive
```

**Windows Directory:** `C:\WINDOWS`
**System Directory:** `C:\WINDOWS\system32`

```python
# Add to config.py:
AC_LOG_PATH = r'C:\Program Files (x86)\Amazing Charts\Logs'
WORK_PC_USERNAME_SHORT = 'FPA'
WORK_PC_HOME_DRIVE = r'C:\Users\FPA'
```

---

## Updated Automation Strategy Table

Replace the previous strategy table with this updated version reflecting
confirmed system details:

| Feature | Primary Method | Fallback | Reliability | Key Detail |
|---------|---------------|----------|-------------|------------|
| MRN detection (F6) | `win32gui` title bar parse | OCR pink context bar | High | Regex `ID:\s*(\d+)` |
| Direct data access | SQL Server 192.168.2.51 | XML export | **Potentially Very High** | Test DB connection first |
| Inbox monitoring (F5) | OCR filter dropdown cycle | SQL query | Medium → High | 7 confirmed filter labels |
| Clinical Summary export | Home screen only, single-click patient in inbox | N/A | High | Charts must be closed |
| Note text (F31) | Past Encounters preview OCR | PDF print OCR | Medium | F8, no dialog needed |
| Historical note load | Select Encounter dropdown | Past Encounters tab | Medium | Fills all text boxes |
| Order execution (F8) | PyAutoGUI click sequence | N/A | Medium | Needs calibration |
| Note creation (F9) | Enlarge Textbox + Update & Go to Next Field | N/A | Medium | 16 sections sequential |
| Patient search | Patient List ID field | Lastname/Firstname | Medium | Type MRN in ID column |
| Care gap data | XML Clinical Summary | Summary Sheet OCR | High | Health Maintenance section |
| Medication list | XML Clinical Summary | Summary Sheet OCR | High | Shows active + inactive |
| Problem list | XML Clinical Summary | Summary Sheet OCR | High | ICD codes included |
| AC state detection | `win32gui` + `psutil` process check | N/A | High | 4 states: not_running, login, home, chart_open |
| Login automation | `win32gui` focus + password type | N/A | High | Username pre-filled, Tab to password |
| Resurrect dialog | `win32gui` title match + click No | N/A | High | Always dismiss on startup |
| Imported items | Direct file access via `\\192.168.2.51\` | AC UI navigation | High | Files at `\ImportItems\[MRN]\` |

---

*Document updated 3/17/2026 with 19 additional screenshots covering system
info, login flow, process names, database path, Summary Sheet, Past
Encounters, Imported Items, and environment variables. Reference image
files by their exact filenames as noted in each section header.*

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

---

## NOTE: Images 1-2 in This Batch (Duplicate Coverage)

`about_s_system_information_button_opens_this_window.png` and
`about_amazing_charts__practice_id__version_number_accessed_from_top_menu_help__about.png`
are covered in full detail in the previous section
**"Amazing Charts Version and Installation Details"** and
**"CRITICAL DISCOVERY — Direct Database Access May Be Possible"**.
No new information from these images in this batch.

---

## Set Flags Dialog

### Observed from: set_flags_button_and_window.png

**How to access:** Click the `Set Flags` button in the Most Recent Encounter
toolbar (second button from left, between `Enlarge Textbox` and `Set Remind`).
The button has a checkered flag icon.

**Dialog title:** `Flags for [LASTNAME] [FIRSTNAME] (DOB: MM/DD/YYYY  ID: [MRN])`

**Description text:**
```
Set your own flags to categorize patients as you find helpful.
Flags are a means to categorize patients in a way that is not
considered part of the medical record. Flags are neither
printed nor included in any reports or exports.
```

**Important:** Flags are NOT part of the medical record, NOT printed,
and NOT included in any exports including the Clinical Summary XML.
They are internal workflow tags only. CareCompanion should treat flags
as metadata only — never use them as clinical data sources.

**Flag checkboxes (confirmed visible options, checkboxes individually selectable):**
```
☑ Diabetic                            ← checked for this patient
☐ Non-Compliant Patient
☐ DNR-on file
☐ Controlled Substance Contract on file
☐ TERMINATED
☑ DECLINED PORTAL OR NO EMAIL         ← checked
☐ VERIFY CORRECT PATIENT CK DOB
☑ NO INFO RELEASED W/O PT KNOWLEDGE  ← checked
☐ ACO Member
☐ CEN Member
[additional items below scroll]
```

**Buttons:**
- `Setup Flag Categories` — admin function to define custom flag types
- `Save Flag(s)` — saves current selections (with flag icon)
- `Close Window` — closes without saving

**CareCompanion use cases:**
- The `Diabetic` flag provides a quick check for diabetes without parsing
  the problem list — but always confirm with ICD-10 codes from XML
- `NO INFO RELEASED W/O PT KNOWLEDGE` is a HIPAA-relevant flag that should
  surface as a warning in the patient chart view
- `DECLINED PORTAL OR NO EMAIL` should suppress any patient portal
  messaging features for that patient in CareCompanion

```python
# Flags window title pattern:
# 'Flags for [NAME] (DOB: ...'
# Not directly parseable from XML — flags only readable via OCR of this dialog

# For care gap purposes, Diabetic flag correlates to:
# - ICD-10 E11.xx in problem list (more reliable source)
# Do NOT rely on flags as the primary data source for any clinical logic
```

---

## Confidential Tab (Most Recent Encounter)

### Observed from: confidential_tab__shows_in_the_enlarge_textboxTOconfidential_sidebar_selection.png

**Location:** Fourth tab in the right-column tab row:
`Physical Exam | Pictures | Illustrations | Confidential`

**Access restriction text displayed:**
```
This confidential tab is only viewable by providers set to high level or
above. It is not viewable by administrators, nursing, or other staff.
```

**Contents:** A large free-text area (empty for this patient in screenshot).
A `Print Confidential` button appears at the top left of the tab.

**Relationship to Enlarge Textbox:** The `Confidential Information` section
in the Enlarge Textbox window corresponds to this tab. When the Enlarge
Textbox section list shows `Confidential Information`, it writes to this tab.

**CareCompanion implications:**
- The Prepped Note tab in CareCompanion includes a `Confidential Information`
  section matching the AC section list
- CareCompanion must enforce that only `provider` and `admin` roles can
  view this section — `ma` role must never see confidential content
- When sending note content to AC via `Update & Go to Next Field`, the
  automation must handle that clicking Confidential Information in AC may
  be restricted on some accounts

```python
# Role restriction for Confidential section in CareCompanion:
SECTION_ROLE_RESTRICTIONS = {
    'Confidential Information': ['provider', 'admin'],
    # All other sections: all roles can view
}

# In patient_note.html template:
# {% if current_user.role in ['provider', 'admin'] %}
#   <div class="note-section" id="confidential">...</div>
# {% endif %}
```

---

## Illustrations Tab (Most Recent Encounter)

### Observed from: illustrations_tab__rarely_used_.png

**Location:** Third tab in the right-column tab row:
`Physical Exam | Pictures | Illustrations | Confidential`

**Instruction text:**
```
To mark an illustration, click the right mouse button over the picture,
and hold it down to draw.
```

**Layout:** Two side-by-side illustration panels, each with:
- `Select Illustration` button
- Color palette (red, blue, yellow, green, black swatches)
- Line thickness selector
- `Clear | Remove | Description` buttons below

**Usage:** Rarely used per the filename note. Used for body diagram
annotations (e.g., marking wound locations on a body outline).

**CareCompanion:** Do not build any automation or display for this tab.
It is not part of the Clinical Summary XML export and has no data value
for the features in the development plan.

---

## Pictures Tab (Most Recent Encounter)

### Observed from: pictures_tab__rarely_used__.png

**Location:** Second tab in the right-column tab row:
`Physical Exam | Pictures | Illustrations | Confidential`

**Layout:** Two side-by-side picture panels, each with:
- `Browse` button (to select an image file)
- `Remove` button
- `Description` text field below the image area

**Usage:** Rarely used per filename. Used to attach clinical photos
(wound photos, skin lesion images, etc.) to an encounter.

**CareCompanion:** Do not build any automation or display for this tab.
Pictures are not included in the Clinical Summary XML export.

---

## Physical Exam Tab — Detailed View

### Observed from: physcial_exam_window.png

**Location:** First (leftmost) tab in the right-column tab row:
`Physical Exam | Pictures | Illustrations | Confidential`
This is the default active tab.

**Vitals input row (top of Physical Exam tab):**
Fields in order: `Weight (lb) | Height | Temp | BP | Pulse | RR | BMI | Sat% | on O2`
- Weight field has `lb` unit label, Height field has `in` label
- Temp field has `°F` label
- BP field has `/` separator (systolic/diastolic)
- Sat% field has `%` label
- `More` button on the left expands additional vital fields
- Small graph/trend icon (green line chart) at far right opens a vitals trend viewer

**Vitals history table:**
Columns: `Date | Weight (lb) | Height in | Temp F | BP | Pulse | RR | HC in | BMI | BMI% | Sat(%) | on O2`
Most recent row highlighted in blue (01/05/2026).
Rows for prior visits are shown below (11/20/2025, 02/22/2025 visible).

**Physical exam free text area (below vitals table):**
Plain text narrative. Each system on a separate line with dash prefix:
```
-Neck: Shotty adenopathy
- CV: regular rhythm, regular rate, no murmurs
- Resp: thorax symmetric with good excursion, Ocasional expatory wheeze bilaterally
- Neuro: alert, awake, normal speech
-Covid Positive, Flu Negative
[Updated by Gretchen Lockard, MD on 1/5/2026 2:19:46 PM]
```

**CareCompanion vitals display:** The vitals history table is the primary
source for the Vitals tab in the Patient Chart View. The Clinical Summary
XML also contains vitals — use XML as the primary source, use OCR of this
table only as fallback.

```python
# Vitals from XML (preferred):
# Section templateId for Vital Signs: 2.16.840.1.113883.10.20.22.2.4.1

# If reading vitals via OCR fallback, the vitals table region is in the
# upper portion of the right column of the Most Recent Encounter tab
# Column order: Date, Weight, Height, Temp, BP, Pulse, RR, HC, BMI, BMI%, Sat, O2
# Parse BP as 'systolic/diastolic' split on '/'

# The vitals text area (free text PE) corresponds to 'Physical Exam'
# section in AC_NOTE_SECTIONS and in the Enlarge Textbox window
```

---

## Allergies Window

### Observed from: allergies_button_opens_allergy_page__typing_allergy_word_starts_to_search_without_search_button__putting_end_date_on_allergy_in_the_list_feild_inactivates_it__tick_box_shows_inactive_allergies_.png

**How to access:**
- Click the allergy icon (red A in a circle) or the allergy text area in
  the Most Recent Encounter tab left column
- OR: In the Enlarge Textbox window, clicking `Allergies (Open Allergy Window)`
  opens this same dialog

**Dialog title:** `Allergies For [LASTNAME], [FIRSTNAME] (DOB: MM/DD/YYYY; ID: [MRN]) [age/sex]`

**Important behavior from filename:** Typing in the Search field starts
searching immediately without pressing the Search button.

### Allergies Window Layout

**Left panel — Add Common Allergy:**
Two columns of common allergen checkboxes:
```
Common Medication:          Common Environmental:
☐ Ace Inhibitors           ☐ Bee Sting
☐ Codeine                  ☐ House Dust
☐ Penicillins              ☐ Latex
☐ Sulfas                   ☐ Nuts/Peanuts
```

**Search/Add Allergies section:**
- `Search:` text field — type to search, results appear immediately
  (observed: typing `|wer` shows: safflower oil, sunflower oil, cauliflower,
  flowers, sunflower seed, Dermawerx Surgical Plus Pak)
- `Search` button (manual trigger)
- Search results list — click to select
- `Free Text:` field — for allergens not in database (italic in list,
  not eligible for automatic drug-allergy interaction checking)
- `Reaction:` dropdown
- `Severity:` dropdown
- `Add To List -->` button

**Right panel — Current Allergy/Sensitivity List:**
- `☐ This patient reports NO Known Allergies (NKA)` checkbox
- `☑ Show Inactive Allergies` checkbox
- Table columns: `Allergy | Reaction | Severity | Start Date | End Date`
- Confirmed entries: ACE Inhibitors (Start: 3/10/2026, End: 3/11/2026),
  Penicillins (no end date = active)

**How to inactivate an allergy (from filename):**
Enter an end date in the `End Date` column for that allergy row. The date
entry alone completes the inactivation — no separate button required.

**Buttons:**
- `Inactivate | Remove` (for selected allergy in right panel)
- `Save and Reconcile` — saves all changes
- `Cancel` — closes without saving

**CareCompanion implications:**
```python
# Allergies from XML (preferred source):
# Section templateId: 2.16.840.1.113883.10.20.22.2.6.1 (Allergies)
# Each entry: allergen name, reaction, severity, start date, end date
# Inactive allergies have an end date populated

# For the Allergies tab in Patient Chart View:
# Active allergies: end_date is null or future
# Inactive allergies: end_date is past (show separately if user requests)

# The allergy icon in the left column of Most Recent Encounter:
# Red circle with 'A' = allergies present
# Clicking opens this Allergies dialog (not editable inline in text box)
# This is consistent with AC_NOTE_SECTIONS: 'Allergies (Open Allergy Window)'

# Drug-allergy interaction checking only works for CODIFIED allergies
# (found in AC's database), not Free Text entries
# This distinction matters for the medication reference module (F10)
```

---

## Medication Window (Current Medication List)

### Observed from: clicking_the_medication_text_box_opens_the_medication_window__unable_to_directly_edit_medications_in_the_text_box__must_be_done_through_the_medication_window.png

**How to access:** Click anywhere on the `Current Medications` text box
in the left column of the Most Recent Encounter tab. The text box is NOT
directly editable — clicking it opens this separate dialog.

**Also accessible from:** `Patient > Medications & ePrescribing` (Ctrl+M),
or `Medications (Open Med Window)` in the Enlarge Textbox section list.

**Dialog title:** `Rx Current Medication List`

**Instruction text at top:**
```
To add a medication to the patient's Current Med List, search for the
medication and select the correct item from the list. If the patient is
unsure which is the correct choice, don't select a medication, just save
the information with as much information as possible before clicking the
Save Changes button.

To edit or remove a medication from the Current Med List, first select the
medication and then adjust the information and click Save Changes. The
updated info will also be displayed in the Plan section of the chart.
```

**Checkboxes at top:**
- `☐ Takes No Meds`
- `☐ Transition/Referral to practice`

### Current Med List Table
Columns: `MedName | Sig`
- `fentanyl 100 mcg buccal t...` | `DISSOLVE ONE IN...`
- `Januvia 100 mg tablet` | `One tablet twice daily`
- `Lipitor 10 mg tablet` | `take 1 tab po qhs`
- `lisinopril 10 mg tablet` | `take 1 tab po qd`
- `Tylenol 325 mg capsule` | `Take 1 tablet by mou...`
- `Ventolin HFA 90 mcg/act...` | `2 PUFFs Qid`
- `Wegovy 0.25 mg/0.5 mL...` | `inject 0.25 mg SQ on...`

### Add/Remove Medication Panel (right side)
- `Med Name:` text field with `● Contains` / `○ Starts with` radio buttons
- `Online Info` button
- Medication search results list area
- `Sig:` dropdown
- `Who Prescribed This Medication?` field
- `Reason Prescribed?` field
- `Date Started:` date picker (Tuesday, March 17, 2026 shown)
- `☐ Patient is no longer taking this medication` checkbox
- `Additional Comments/Reason:` field
- `☐ Administered During Visit` checkbox
- `☐ Medication Reconciliation Complete` checkbox
- `Clear | Save Changes` buttons

**CRITICAL for automation:**
The medications text box in the main chart view is READ-ONLY for display.
All medication editing MUST go through this dialog window. This window
opens as a separate floating window, not a tab.

```python
# The Medication Window is a separate window:
# Title: 'Rx Current Medication List' (or similar — confirm via win32gui)
# It is NOT a child of the patient chart window — it floats independently

# For CareCompanion medication display:
# Use Clinical Summary XML as primary source (preferred, no dialog needed)
# XML section: Medications (templateId 2.16.840.1.113883.10.20.22.2.1.1)
# Both active and inactive medications are in the XML

# For medication editing automation (F31, pre-charting):
# Do NOT attempt to automate medication editing through this window
# It requires search, selection, and form filling — too fragile
# Instead: display medication list from XML, allow provider to edit in AC directly

# Keyboard shortcut to open medications:
AC_SHORTCUTS['medications'] = ('ctrl', 'm')  # confirmed
```

---

## Set Reminder Dialog

### Observed from: set_reminder_button_opens_a_message_creation_page__has_optiont_to_save_next_to_yellow_box_next_to_button.png, reminder_creation_user_selection_scroll_list_.png

**How to access:** Click the `Set Remind` button in the Most Recent
Encounter toolbar (third button, red exclamation mark icon, between
`Set Flags` and the yellow notes area). A yellow reminder sticky note
icon/area sits immediately to the right of the button.

**Dialog title:** `Reminders for [LASTNAME] [FIRSTNAME] (DOB: MM/DD/YYYY  ID: [MRN])`

**Important disclaimer text (top of dialog):**
```
Reminders can be saved to a patient's chart and can also be set to
appear in a providers message box on a certain date.

Messages and reminders are NOT considered part of the medical record
and are neither printed nor exported with the patient's record.
```

**Like Flags, Reminders are NOT in the medical record and NOT in XML exports.**

### Reminder Creation Form — Three Numbered Sections:

**Section 1 — Send Msg/Reminder to Who?**
- Dropdown: `Provider in whose Inbox this msg/reminder will appear`
- Default selection: `Denton, C [CORY]` (current logged-in user)
- `☐ Also notify me, in addition to the provider above` checkbox

**Provider dropdown confirmed entries (from reminder_creation_user_selection_scroll_list_.png):**
```
Bottoms, J [JENNIFER]
Burton, A [ASHLEYB]
CAREPARTNERS, V [VIRGINIA]
Dailey, A [AMENAH]
Decker, R [RAYMOND]
Denton, C [CORY]         ← highlighted/selected
DOCTOR, D [DOCTOR]
Dodge, J [JULIA]
[additional entries below scroll]
```
This list reveals the full provider roster at the practice. The format
is `Lastname, Initial [USERNAME]`.

**Section 2 — Msg/Reminder Date?**
- Date picker (defaults to today: 3/17/2026)
- Quick-set buttons: `1 Week | 2 Weeks | 3 Weeks | 4 Weeks | 6 Weeks`
- Second row: `2 Months | 3 Months | 4 Months | 6 Months | 1 Year`

**Section 3 — Msg/Reminder Information?**
- `Patient:` dropdown (pre-filled: `TEST, TEST (DOB: 10/1/1980 ID: 62815)`)
- `☑ Also document in patient's chart (as yellow reminder that is NOT part of the medical record.)` checkbox
- `☐ Also document in patient's chart as Addendum` checkbox
- `Email Patient` button
- `Show Other Reminders` button
- `Subject of Msg/Reminder:` dropdown with `☑ Add Time Stamp` checkbox
  Default subject: `REMINDER: TEST TEST (10/1/1980)TEST TEST (10/1/...`
- `Text of Msg/Reminder (right-click to use template):` text area
- `Send` button (yellow, with flag icon — bottom right)
- `Close` button

**CareCompanion — Follow-Up Tickler (F24) integration:**
The Set Reminder dialog is AC's native reminder system. CareCompanion's
tickler (F24) is a parallel system that doesn't interact with AC reminders.
However, when a tickler item is completed via the AC injection pathway,
a reminder could optionally be sent to confirm. The provider list revealed
here (`Denton, C [CORY]` etc.) is useful for the MA assignment feature (F24b).

```python
# Confirmed provider username format: 'Denton, C [CORY]'
# Parse as: f'{lastname}, {first_initial} [{username}]'
# This list is useful for:
# - F24b: MA Assignment dropdown in tickler
# - F7d: On-call colleague handoff recipient selection
# - User creation/matching when colleagues onboard to CareCompanion

# The yellow sticky note area next to Set Remind button is a visual
# indicator that reminders exist for this patient
# It is NOT a separate button — it is a display area only
```

---

## Diagnoses Section — Assessment vs Problem List

### Observed from: diagnoses_saved_as_assessment_go_in_the_chart_only__add_problem_adds_to_chart_and_permanetly_in_the_patients_problem_list__.png, problem_list_no_access.png

### Diagnoses Search and Entry

The Diagnoses section is in the lower portion of the right column of the
Most Recent Encounter tab, below the Physical Exam area.

**Layout:**
- `Search Diagnosis` text field + `☐ Search Favorites` checkbox + `Lookup Dx` button
- ICD-10 search results appear as a dropdown list below the search field
  Example: typing `personal history of cov` shows `Z86.16  Personal History of COVID-19`
- Two action buttons appear next to the result:
  - `+ Assessment` — adds to THIS NOTE'S assessment section only (not permanent)
  - `+ Problem List` — adds to THIS NOTE and PERMANENTLY to the patient's problem list

**Critical distinction from filename:**
- `+ Assessment` → diagnosis appears ONLY in this chart note's Assessment section
- `+ Problem List` → diagnosis appears in this note AND is permanently added
  to the patient's problem list (Summary Sheet > Problems)

This is the primary mechanism for adding diagnoses during a visit. The
Assessment text area below receives the diagnosis in the format:
```
# [Diagnosis Name] ([ICD-10 Code]):[Plan text]
```

### Problem List Dropdown — Read-Only State

**Observed from: problem_list_no_access.png**

In the Most Recent Encounter tab, below the diagnosis search, there is a
dropdown that shows `Problem List` with:
- `☐ Active Only` checkbox
- `Problems` button (grayed out / pencil icon = edit mode)

This dropdown is for VIEWING the existing problem list within the encounter
context. The `Problems` button appears grayed out in standard encounter
view — it cannot be clicked to add problems from this dropdown location.

**The correct way to modify problems is via Summary Sheet > Problems section
(Edit button opens the Editing Problems dialog).**

```python
# Diagnosis entry in CareCompanion (Prepped Note tab):
# The Assessment section textarea should accept free-text in AC's format:
# '# [Diagnosis] ([ICD-10]):[Plan text]'
# When sending to AC via automation:
# 1. Use the Enlarge Textbox > Assessment section
# 2. Type/paste the formatted assessment text
# 3. Do NOT attempt to use the + Assessment or + Problem List buttons
#    via automation — too many dialog interactions required
# 4. The Assessment text box accepts direct text entry via the Enlarge Textbox

# For reading current diagnoses:
# Primary: Clinical Summary XML (problem list section)
# Secondary: OCR of Assessment text area in Most Recent Encounter tab
# The Assessment format: lines starting with '#' are diagnosis entries
import re
# re.findall(r'#\s+(.+?)\s+\(([A-Z]\d+\.?\d*)\):(.*)', assessment_text)
# Returns: [(diagnosis_name, icd10_code, plan_text), ...]
```

---

## Clinical Decision Support (CDS) Window

### Observed from: clinial_decision_support_cell_opens_this_window.png, Risk_factor_analyze_button_opens_clinical_decision_support__is_displayed_on_patietn_chart_landing_page.png

**How to access:**
- Double-click any row in the Decision Support table at the bottom of the
  Most Recent Encounter tab (the yellow/highlighted recommendation rows)
- OR: Click the `Decision Support` button (apple icon, rightmost button
  in the encounter toolbar)
- OR: Click `Analyze` button at the bottom of the Risk Factors window

**Window title:** `[LASTNAME], [FIRSTNAME] (DOB: MM/DD/YYYY; ID: [MRN])`

**Tab bar at top of CDS window:**
```
Clinical Quality Measures | Decision Support Due | Immunizations & Shots | Screenings & Tests | Injections (non-Decision Support)
```

### Decision Support Due Tab

**DS Type radio buttons:**
```
● All
○ History Only
○ Screenings Only
○ Recommendations
○ Other
○ Clinical Assessment
```

**Search field** + `Add New` button (top right)

**Left panel — Disclaimer text:**
```
Patient-specific rules are modifiable by right-clicking on the recommendation.
Practice-wide rules are modifiable in the Admin section of Amazing Charts.
[Vaccination disclaimer...]
Decision Support recommendations are based mostly on USPSTF. Click here
to review their current guidelines.
```

**Recommendation list (center):**
Table: `Name | Last | Next`
All rows shown (yellow = due/overdue):
```
Diabetic Foot Care Recomendation         -    10/01/1998 - 10/01/2055
Diabetic Neuropathy Screening for        -    10/01/1990
Hepatitis B (Adult)                      -    After 10/01/1999
Influenza Adult                          -    10/01/1999
PHQ-2 Patient Depression Questionnaire   -    10/01/1992
PHQ-9 Patient Depression Questionnaire-New  - 10/01/1992
Recommendations for Testing HgbA1C...   -    After 10/01/1981
Screening for and Management of Obesity -    Today          ← red = due today
Screening for Breast Cancer w/Mammography - 10/01/2020-10/01/2029
Screening for Cervical Cancer w/Pap     -    After 10/01/2001
Screening for Depression in Adults      -    10/01/1999 - 10/01/2007
Screening for High Blood Pressure...    -    Today          ← red = due today
Td (Tetanus, diphtheria)                -    After 10/01/1999
Tobacco use counseling...               -    10/01/1998
```
`Refresh` button at bottom.

### Selected Recommendation Detail Panel (right side)

When a recommendation row is clicked:
- `Name:` bold heading (e.g., `Diabetic Foot Care Recomendation`)
- `URL:` clickable link to evidence source
- `Grade:`
- `Type:` (Other / Screening / Immunization / etc.)
- `Specific Recommendations:` free text paragraph
- `Frequency of Service:` text
- `Footnote:`

**Document Completion or Refusal section:**
- `Date Performed:` date picker
- `☐ Patient Refuses This Recommendation` checkbox
- `Result/Comment (right-click to use templates):` text area
- Action buttons: `Meds | Orders | Save | Save/Close`

**Prior Results:** Table showing history of this recommendation.

**CareCompanion Care Gap Tracker (F15) integration:**
This CDS window is the source data for all care gap recommendations.
The data is also present in the Clinical Summary XML under Health
Maintenance section and in the Summary Sheet Decision Support table.

```python
# CDS recommendations match the Health Maintenance section in XML
# Primary data source: XML Clinical Summary (preferred)
# The 'Today' rows (red) = items due now → highest priority in care gap display

# For F15 (Care Gap Tracker), the CDS window shows the same data as:
# XML: //cda:section[cda:templateId/@root='2.16.840.1.113883.10.20.22.2.2.1']
# (Immunizations) and
# //cda:section[cda:templateId/@root='2.16.840.1.113883.10.20.22.2.15']
# (Plan of Care — includes health maintenance recommendations)

# Document completion via automation:
# 1. Double-click the recommendation row
# 2. Enter date in 'Date Performed' field
# 3. Optionally add Result/Comment
# 4. Click 'Save/Close'
# This marks the screening as complete in AC
```

---

## Risk Factors Window

### Observed from: rick_factors_button_opens_this_window.png, Risk_factor_analyze_button_opens_clinical_decision_support__is_displayed_on_patietn_chart_landing_page.png, risk_factors_button.png

**How to access:** Click the `Risk Factors` button in the Most Recent
Encounter toolbar. The button is between the yellow notes area and the
`Decision Support` (apple) button.

**Window title:** `[LASTNAME], [FIRSTNAME] (DOB: MM/DD/YYYY; ID: [MRN])`

**Purpose text:** `Amazing Charts uses this information to generate
continuing quality improvement (CQI/P4P) reports and determine health
maintenance recommendations.`

### Risk Factors Window Layout

**Left column — Past Medical History checkboxes (partial list):**
```
☐ CV: Coronary Artery Disease
☐ CV: Elevated Cholesterol
☐ CV: Heart Disease (e.g., CHF, CAD, valvular disease)
☐ CV: Hypertension
☐ CV: Stroke or Cerebral Ischemia
☐ CV: Transient Ischemic Attack
☑ Endocrine: Diabetes Mellitus        ← checked for this patient
☐ Endocrine: Diet-Related illness (e.g., obesity)
☐ Endocrine: Menopausal or Post-Menopausal
☐ ID: HIV Infection
☐ ID: Illicit Drug Use
☐ ID: Influenza 'At Risk' Factors (child caretaker, chronic aspirin use...)
☐ ID: Neisseria Meningitis Exposure
☐ ID: Pneumococcal Risk Factors (chronic alcoholism, cochlear implants...)
☐ ID: Sexually Transmitted Disease
☐ ID: Terminal Complement Component Deficiency
☐ OB/GYN: Immediately Postpartum
☐ OB/GYN: Pregnant Currently
☐ Osteoporosis Risk Factors (lower body weight < 70kg, smoker, weight...)
☐ Other: Asplenia
☐ Other: Chronic Liver Disease
☐ Other: COPD, Asthma, and Other Chronic Lung Diseases
☐ Other: Developmental Disability
☐ Other: Iron Deficiency
☐ Other: Sickle Cell Disease
☐ Renal: End-Stage Renal Disease
☐ Renal: Renal Dysfunction
```

**Right column — Social History checkboxes (partial list):**
```
☐ Chronic Care Facility resident
☐ Fluoride Absent from Water Source
☐ Healthcare worker
☐ ID: At Higher Risk for H1N1 infection (Pregnant, 6mo-4yrs, Caretaker of...)
☐ ID: At Risk for Varicella Infection with no evidence of immunity (high risk...)
☐ ID: Blood or body fluids exposure
☐ ID: Close Contact with Infant <12m
☐ ID: Hep A Risk Factors (sex partner or household member with HAV, tra...)
☑ ID: Hep B Risk Factors (household member with HBV, travel to 'At Risk'...)  ← checked
☐ ID: HIV Risk Factors Not Listed Elsewhere (transfusion between 1978-8...)
☐ ID: Homosexual Men
☐ ID: Injection Drug Use (IVDU): Current or former
☐ ID: MMR Risk Factors (attends college or other post-secondary institutio...)
☐ ID: Neisseria Meningitidis Risk Factors (first year college student in dorm...)
☐ PATIENT DEFERS ANSWERING ONE OR MORE OF THESE RISK F...
☐ Sex: Patient has had > 1 sexual partner in last 6 months
☐ Sex: Sexually Active
☐ Sex: Sexually Active with High Risk Behaviors (e.g., MSM, unprotected...)
☐ Tobacco: Current user
☐ Tobacco: Former user
```

**Family History section (bottom right):**
```
☐ Breast CA (1st Degree Relative - mother, daughter, sister)
☐ CAD (Male relative < 50y; Female relative < 60y)
☐ Tob: No FH of Tobacco use
```

**Bottom buttons:**
- `Close` button
- `● Patient HAS Risk Factors` / `○ Patient DENIES Risk Factors` radio buttons
- `☐ Don't automatically display this window for patients that have yet to have this data completed`
- `Set Flags` button
- `Analyze` button ← **opens the Clinical Decision Support window**
- `Save` button

**Risk Factors button location (from risk_factors_button.png):**
The `Risk Factors` button is in the encounter toolbar, to the LEFT of
the `Decision Support` (apple) button. It shows a circular person/figure
icon. The button label shows `Risk Factors (3)` when risk factors are set
(the number in parentheses is the count of checked items).

**CareCompanion implications:**
```python
# Risk Factors data is in the Clinical Summary XML under Social History
# and Plan of Care sections — but the full checkbox list above is not
# directly exportable; it is stored internally in AC's database

# For direct DB access: risk factors are likely in a separate table
# linked to patient ID. If SQL access is confirmed, query this directly.

# For the Care Gap Tracker (F15): Risk Factors checked here directly affect
# which screenings appear in the Decision Support recommendations list
# e.g., Diabetes Mellitus checked → Diabetic Foot Care appears as recommendation

# The 'Risk Factors (3)' count in the button label can be read via:
# win32gui.GetWindowText() or OCR of the button label area
# This is a useful quick indicator of whether risk factors have been assessed

AC_SHORTCUTS['health_risk_factors'] = ('ctrl', 'h')  # confirmed
```

---

## Toolbar Button Layout — Final Confirmed Reference

### Observed from: risk_factors_button.png, set_flags_button_and_window.png, confidential_tab__shows_in_the_enlarge_textboxTOconfidential_sidebar_selection.png

The Most Recent Encounter toolbar row (above the encounter form, below
the date/time header) contains these elements in confirmed left-to-right order:

```
[Enlarge Textbox] [Set Flags] [Set Remind] [YELLOW AREA (notes)] [▼scroll] [Risk Factors (N)] [Decision Support]
```

And the right-column tab row:
```
[Physical Exam] [Pictures] [Illustrations] [Confidential]
```

**Button details:**
- `Enlarge Textbox` — folder/document icon, opens 16-section note editor
- `Set Flags` — checkered flag icon, opens patient flag dialog
- `Set Remind` — red exclamation/pushpin icon, opens reminder creation dialog
- `[YELLOW AREA]` — large yellow sticky note area, shows saved reminders
- `[▼]` — scroll arrow to collapse/expand the yellow area
- `Risk Factors (N)` — circular person/figure icon, N = count of set risk factors
- `Decision Support` — red apple icon, opens CDS/Clinical Quality Measures window

```python
# Complete toolbar button reference for PyAutoGUI automation:
# All coordinates are relative and must be calibrated per screen resolution
# The toolbar is in the upper-right quadrant of the patient chart window
# Buttons appear in consistent left-to-right order as listed above

AC_ENCOUNTER_TOOLBAR = {
    'enlarge_textbox':    'left-most button in toolbar row',
    'set_flags':          'second button',
    'set_remind':         'third button',
    'yellow_notes_area':  'large yellow region — do not click for automation',
    'risk_factors':       'second from right, shows count in label',
    'decision_support':   'rightmost, red apple icon',
}

# Right-column tabs (Physical Exam is default/first):
AC_RIGHT_COLUMN_TABS = ['Physical Exam', 'Pictures', 'Illustrations', 'Confidential']
```

---

*Document updated 3/17/2026 (batch 3) with 15 new screenshots covering:
Set Flags dialog, Confidential tab, Illustrations tab, Pictures tab,
Physical Exam tab detail, Allergies window, Medication window, Set Reminder
dialog with provider roster, Diagnoses / Assessment section behavior,
Problem List access limitations, Clinical Decision Support window,
Risk Factors window, and confirmed toolbar button layout.*

---

## Edit Active Problem List Dialog

### Observed from: problem_list_button_opens_this_window.png

**How to access:** Click the pencil/edit `Problems` button in the Diagnoses
section of the Most Recent Encounter tab. This button is to the right of
the `☑ Active Only` checkbox, in the row below the Problem List dropdown.
It is only active (clickable) when the `Problems` button shows the pencil
icon — not grayed out.

**Dialog title:** `Edit Active Problem List`

**Layout:**
Table with two columns of checkboxes:
```
Problem Description                    Resolve    Inactivate
Acute sinusitis                        ☐          ☐
Attention deficit disorder             ☐          ☐
Central obesity                        ☐          ☐
Chronic nonmalignant pain              ☐          ☐
COVID-19                               ☐          ☐
Dyslipidemia                           ☐          ☐
Encounter for general adult medical examination with...  ☐  ☐
Endogenous hyperlipidemia              ☐          ☐
Falls                                  ☐          ☐
Gastro-esophageal reflux disease...    ☐          ☐
[additional items below scroll]
```

**`Update` button** — bottom right, applies checked changes.

**Important behavioral note:** This dialog shows ALL active problems as
plain text descriptions WITHOUT ICD-10 codes. Checking `Resolve` and
clicking `Update` resolves that problem. Checking `Inactivate` inactivates it.

**Difference from Summary Sheet Editing Problems dialog:**
- Summary Sheet > Edit button → `Editing Problems` dialog (shows ICD codes,
  Active/Resolved/Inactive columns, date-entry style)
- Most Recent Encounter > Problems button → `Edit Active Problem List`
  (simpler checkbox interface, no ICD codes shown, no date entry)

Both dialogs modify the same underlying problem list.

```python
# Edit Active Problem List window:
# Title: 'Edit Active Problem List'
# Opens as a separate floating window from the patient chart
# Useful for: quickly resolving problems after a visit (e.g., acute sinusitis)
# The Problems button in the Diagnoses section only becomes active when
# the Problem List dropdown is selected (not Assessment dropdown)

# For CareCompanion automation:
# Do NOT attempt to automate problem resolution through this dialog
# Use Summary Sheet > Edit (Editing Problems dialog) instead —
# it is more reliable and shows ICD codes for verification
# Primary data source for problem list: Clinical Summary XML

# The Problems button appearance:
# Active (pencil icon, clickable): problem list mode enabled
# Grayed out: assessment mode or read-only context
```

---

## Physical Exam Templates — Landing Page

### Observed from: user_template_landing_.png

**How to access:** From Most Recent Encounter tab, right-click any text
field while holding `Alt` key (fast template insert), OR navigate via the
template system. The Physical Exam Templates window appears when working
in the Physical Exam (PE) section.

**Window title:** `Physical Exam Templates`

**Section header:** `1. Select A Template`
`Select one or more templates from the lists below to review and/or edit
its content. To rapidly move a template to the note, just double-click it.`

### Two-Column Template List

**Left column — Personal Templates (provider-specific):**
```
ICXR_Neg          ← selected/highlighted
IPE Hands-Off
IPE_ABDcc
IPe_auto
* 99203
* Breast Exam
* Cerumen Disimpaction
* Comprehensive PE
* Coumadin
* Female Physical NO PAP
* GI
* GU
* I&D
* Joint Injection
* Knee exam
* Knee Injection
* Low Back Pain
* Male GU exam
* Male Physical Exam
* MSK
* Neuro
* Newborn exam
* Nexplanon Procedure
* Normal CV and Lungs
* Pediatric Exam
* Psych
* Rectal Exam
* SKIN
* Skin Biopsy
* Thyroid
* Trochanteric Bursitis
```

**Right column — Practice-Wide Templates (shared across all providers):**
```
dx: Allergic Rhinitis     ← highlighted in blue
dx: Asthmatic Bronchitis
dx: Cold/URI
dx: Pharyngitis
dx: UTI
Hospital Follow Up
Hospital Follow Up
Hospital Follow Up
Med MGMT PE Lev4
nL: Brief
nL: CPE
nL: GI/Abd
nL: GU (male)
nL: GYN
nL: Neuro (full)
nL: Neuro (low back)
nL: Psych
nL: Visual Only
RGD:EXTRALABS
```

### Right Panel Actions

**Import A Template section:**
- `● from Amazing Charts` radio button
- `○ from Local Folder` radio button
- `Import` button

**Export Selected Template section:**
- `Additional Comments:` text field
- `Export` button

**PE preview area** — shows the text content of the selected template

**Buttons at bottom:**
- `Add/Edit Templates` ← opens the full template editor (see below)
- `Cancel`
- `3. Move to Chart` ← inserts selected template text into the note

**CareCompanion — Feature 9a (Template Source Sync) implications:**
```python
# The template system in AC has two levels:
# 1. Personal Templates — belong to the logged-in provider
# 2. Practice-Wide Templates — shared across all providers

# Template naming conventions observed:
# 'ICXR_Neg' = chest X-ray negative (personal)
# 'dx: [condition]' = diagnosis-specific templates (practice-wide)
# 'nL: [type]' = normal/limited exam templates (practice-wide)
# '* [name]' = asterisk prefix = user-modified or starred template

# For Feature 9a (Template Source Sync):
# Templates are stored in AC's database, not as files
# They can be exported to XML via the Export button (see template_export.png)
# Export path: C:\Users\[user]\PE_[TemplateName]_[Practice]_[date].xml
# Import path: from Amazing Charts website or from local folder

# The 'Physical Exam Templates' window appears for the PE section
# Other note sections also have template windows accessible the same way
# The section-specific template window title varies by section context

# For automation (Feature 9, pre-visit note prep):
# Do NOT use the template UI for automation — it requires too many clicks
# Instead: read template text from AC's database (if SQL access confirmed)
# OR: manually populate templates from CareCompanion's own template storage
```

---

## Template Access via Edit Menu

### Observed from: access_user_templates.png

**Navigation path:** With a patient chart open on Most Recent Encounter tab:
```
Edit menu > My Preferences > Templates    (keyboard: Ctrl+T)
```

**Edit menu full contents:**
```
Cut          Ctrl+X
Copy         Ctrl+C
Paste        Ctrl+V
Select All   Ctrl+A
─────────────────────────
Allergies
Health (Risk) Factors    Ctrl+H
Vital Signs
Spelling     F7
─────────────────────────
My Preferences ►
    User Preferences     Ctrl+U
    Templates            Ctrl+T    ← circled in screenshot
    Turn OFF Text Box Updated Notification
```

**Keyboard shortcut confirmed:** `Ctrl+T` opens the Templates window directly.

```python
# Template access keyboard shortcut:
AC_SHORTCUTS['templates'] = ('ctrl', 't')  # confirmed

# Edit menu also reveals:
AC_SHORTCUTS['user_preferences'] = ('ctrl', 'u')  # confirmed
AC_SHORTCUTS['vital_signs'] = None  # no keyboard shortcut shown
AC_SHORTCUTS['spelling'] = 'f7'  # confirmed (F7 in chart context = spelling)
# NOTE: F7 in chart context = Spelling (not F7 = Most Recent Encounter
# which only applies from the main AC home screen)
# Context matters for F7 — home screen vs open chart

# The Templates window (Ctrl+T) opens to the Physical Exam Templates
# landing page shown in user_template_landing_.png
# It is section-context-sensitive: if cursor is in PE section, PE templates show
```

---

## Add/Edit Templates Window

### Observed from: add___edit_templates_window.png

**How to access:** Click `Add/Edit Templates` button in the Physical Exam
Templates window, OR open via Ctrl+T then click Add/Edit Templates.

**Window title:** `Add/Edit Templates`

**Instruction text at top:**
```
To add a template quickly from within a patient note, hold down the "ALT"
key while you Right-mouse click. The text will be added to this list
automatically as a new template. To add a template now, click the Add New
button below, then enter the new template into the text boxes.

To edit or delete a template, select it from the list below, make changes
in the text boxes at the bottom of the window, then click save.
```

**`Change Row Size` control** — top right, adjusts row height in the list.

### Template List Table

Columns: `TextBox Location | Template Name | Text | Shared`

**TextBox Location column** (left sidebar, scrollable list of all AC sections):
```
CC
ROS
HPI
PMH
ALL
SH
FH
MEDS
PE           ← highlighted/selected
ASSESSMENT
PLAN
COMMENTS
LETTER
ORDERS
ADDENDUM
REMINDER
SIGNOFF
RESULTS
INSTRUCT
GOALS
HEALTH CONCER
```

**This is the complete list of AC text box locations for templates.**
Each corresponds to an AC note section where templates can be stored.

**Template rows visible (for PE section):**
```
ICXR_Neg     CXR reviewed in office in the absence of a trained radiologist.  ☐ Shared
IPE Hands-Off   GEN: A&D NAD                                                  ☐
IPE_ABDcc    GEN: A&D NAD                                                      ☐
IPe_auto     [empty text shown]                                                ☐
* 99203      [empty]                                                            ☐
* Breast Exam   [text preview truncated]                                       ☐
* Cerumen    Cerumen was disimpacted from both ears using syringe irrigation.  ☐
* Comprehensive  [text]                                                        ☐
* Coumadin   [text]                                                            ☐
* Female Physical  - General: well groomed, in NAD sitting up on exam table   ☐
* GI         - General: well groomed, in NAD sitting up on exam table         ☐
* GU         [text]                                                            ☐
* I&D        I&D of  :                                                        ☐
* Joint Injection   [empty]                                                    ☐
* Knee exam  Knee: normal appearing, no effusion bilateral knees. No ttp bi... ☐
* Knee Injection   [empty]                                                     ☐
* Low Back Pain   Lumbar spine is normal appearing on inspection. No ttp spi... ☐
* Male GU exam   [text]                                                        ☐
* Male Physical   - General: well groomed, in NAD sitting up on exam table    ☐
```

**Bottom editing area:**
- `Template Name:` field (shows: `ICXR_Neg`)
- `Template Text:` multi-line text area showing:
  ```
  CXR reviewed in office in the absence of a trained radiologist.
  Impression: No acute cardiopulmonary process identified.
  -Lung fields: clear
  -Cardiac silhouette: similar to previous cxr
  -Costophrenic angles: sharp
  ```
- `Add New` button
- `Delete Selected` button
- `Save Changes` button
- Date stamp at bottom right: `3/17/2026`

**Import/Export sections (bottom left):**
```
Import A Template:
● from Amazing Charts Website
○ from Local Folder
[Import button]

Export A Template:
Select the template from the above list, then click the Export button.
[Export button]
```

```python
# Template TextBox Location codes map to AC note sections:
TEMPLATE_TEXTBOX_LOCATIONS = {
    'CC':           'Chief Complaint',
    'ROS':          'Review of Systems',
    'HPI':          'History of Present Illness',
    'PMH':          'Past Medical History',
    'ALL':          'Allergies',
    'SH':           'Social History',
    'FH':           'Family History',
    'MEDS':         'Medications',
    'PE':           'Physical Exam',
    'ASSESSMENT':   'Assessment',
    'PLAN':         'Plan',
    'COMMENTS':     'Comments',
    'LETTER':       'Letter',
    'ORDERS':       'Orders',
    'ADDENDUM':     'Addendum',
    'REMINDER':     'Reminder',
    'SIGNOFF':      'Sign-Off',
    'RESULTS':      'Results',
    'INSTRUCT':     'Instructions',
    'GOALS':        'Goals',
    'HEALTH CONCER': 'Health Concerns',
}

# NOTE: 'COMMENTS', 'LETTER', 'ADDENDUM', 'REMINDER', 'SIGNOFF', 'RESULTS'
# are TextBox locations for templates but are NOT in the AC_NOTE_SECTIONS list
# from the Enlarge Textbox window. They are supplementary template categories.

# ALT + Right-click shortcut: adds currently selected text in a note as a new
# template instantly — the fastest way to create templates in AC
# This is NOT automatable (requires human text selection + keyboard combo)

# The 'Shared' checkbox marks templates as practice-wide vs personal
# Unchecked = personal to this provider (default)
# Checked = visible to all providers (Practice-Wide Templates column)

# For CareCompanion Feature 9a (Template Source Sync):
# If SQL database access is confirmed:
# Templates are stored in a table queryable by provider + section + name
# Read templates directly from DB for CareCompanion's own template reference
# If no DB access: export templates via AC's Export function to XML files
# Template export path format: C:\Users\[user]\[section]_[name]_[practice]_[date].xml
```

---

## Template Export

### Observed from: template_export.png, template_stacking_text_window.png

### Template Export Confirmation Dialog

**Observed from: template_export.png**

After clicking `Export` in the Add/Edit Templates window, a confirmation
dialog appears:

**Title:** `Export Complete`

**Message:**
```
The template was successfully exported to
C:\Users\User\PE_CXRNeg_FamilyPracticeAssociatesofChesterfield_tp_031726.xml.

Do you wish to upload it to Amazing Charts and share it with others?
```

**Buttons:** `Yes | No`

**Export file path format:**
```
C:\Users\[username]\[Section]_[TemplateName]_[PracticeName]_tp_[MMDDYY].xml
```
Example: `C:\Users\User\PE_CXRNeg_FamilyPracticeAssociatesofChesterfield_tp_031726.xml`

```python
# Template export path components:
# Section abbreviation (PE, CC, ROS, etc.) + underscore
# Template name (spaces removed) + underscore
# Practice name (spaces removed) + underscore
# 'tp_' + date (MMDDYY format) + '.xml'

# For Feature 9a (Template Source Sync):
# Option 1 (preferred): Direct SQL database read
# Option 2: Trigger export via PyAutoGUI, then parse the XML file
# Option 3: Read the XML from known export path if already exported

TEMPLATE_EXPORT_FOLDER = r'C:\Users\FPA'  # based on system username 'FPA'
# Template XML files will appear here after export
```

### Template Stacking / Preview Window

**Observed from: template_stacking_text_window.png**

This shows the Physical Exam Templates window with a template selected
and its content visible in the preview area. The `* Breast Exam` template
is checked and the text is visible:

```
- General: well groomed, in NAD sitting on exam table
- CV: regular rate, regular rhythm, no murmurs or rubs
- Resp: thorax symmetric with good excursion, CTAB
- MSK: normal gait and station. Hands and fingers without deformities or cyanosis
- Skin: warm, dry and intact, no rashes
- Psych: conversant, appropriate affect, normal insight and judgement
- Breast Exam: Nurse, Alison Rapovy, was present during examination.
  On inspection, bilateral breasts are normal appearing, without skin changes
  or deformities.
  On palpation, no masses or nodules of bilateral breasts. No nipple discharge.
```

**Key behavior:** Multiple templates can be checked simultaneously (template
stacking). The preview area shows the combined text of all checked templates.
`3. Move to Chart` inserts the full stacked template text into the note section.

```python
# Template stacking: checking multiple templates combines their text
# The preview area shows the combined result before inserting
# '3. Move to Chart' is the final step to insert into the active note section

# Template text format uses:
# '-' prefix for each exam finding line
# Plain text, no special markup
# Line breaks between systems

# For CareCompanion Prepped Note tab:
# Store template text as plain text matching AC's format
# When sending to AC via Enlarge Textbox automation, paste the template
# text directly — AC accepts plain text in all note section fields
```

---

## Change Date/Time of Encounter

### Observed from: change_date_and_time_of_this_encounter.png

**How to access:** Hover over (or click) the green circle/dot button in
the Most Recent Encounter tab header, to the right of the date/time display
(`Monday March 16, 2026  12:47 PM`). A tooltip appears:
`Change the date/time of this encounter.`

**The green dot is a clickable button** — it opens a date/time picker to
change when the encounter is recorded.

```python
# The green dot button location:
# In the encounter header row, to the right of the date/time text
# Just to the left of the patient photo
# Tooltip: 'Change the date/time of this encounter.'

# For CareCompanion Pre-Visit Note Prep (Feature 9):
# When creating pre-visit notes the night before, the encounter date will be
# set to the preparation date, not the visit date
# After the actual visit, the provider may need to update the date
# CareCompanion should note this limitation in the prep status dashboard

# For automation: do NOT change encounter dates automatically
# Date/time of encounter is a clinically significant field
# Any automation that creates notes overnight must warn providers
# that the encounter date may need manual adjustment
```

---

## Search Clinical Diagnoses Window

### Observed from: search_clinical_dx.png, lookup_dx_button.png, lookup_dx_taskmanager.png

### The Lookup Dx Button

**Observed from: lookup_dx_button.png**

In the Diagnoses section of Most Recent Encounter tab:
```
[Search Diagnosis field]  [☐ Search Favorites]  [Lookup Dx button]
[Problem List dropdown]   [☐ Active Only]        [pencil Problems button]
[Edit Superbill button]
```

The `Lookup Dx` button is to the RIGHT of the `Search Favorites` checkbox.
Clicking it opens the `Search Clinical Diagnoses` window as a separate dialog.

The `Edit Superbill` button appears below the Problem List row — this opens
the superbill editor for billing codes.

### Search Clinical Diagnoses Window

**Observed from: search_clinical_dx.png**

**Window title:** `Search Clinical Diagnoses`

**Layout:**
- `Search:` label with radio buttons `○ ICD-9  ● ICD-10` (ICD-10 selected by default)
- Large search text field (empty on open)
- Results table with columns: `Code | Description | Chronicity | Favorite`
- (Table empty on open, populates when you type)

**Bottom buttons:**
- `☐ Search Favorites` checkbox
- `Cancel`
- `Refine Selection`
- `+ Assessment`
- `+ Problem List`

**Same `+ Assessment` / `+ Problem List` distinction applies here** as in
the inline diagnosis search.

### Task Manager Process Name for Diagnosis Search

**Observed from: lookup_dx_taskmanager.png**

When the Search Clinical Diagnoses window is open, Task Manager shows
the AC process group as `Amazing Charts EHR (32 bit) (3)` with three
child processes:
```
Amazing Charts EHR (32 bit) (3)
    ├── Amazing Charts  Family Practice Associates of Chesterfield
    ├── Search Clinical Diagnoses                                    ← new process
    └── TEST, TEST (DOB: 10/1/1980; ID: 62815) 45 year old woman,
```

**Critical for automation:** The `Search Clinical Diagnoses` window
appears as a SEPARATE PROCESS in Task Manager, not just a window within
AC. This means `win32gui.EnumWindows` will find it as its own window,
and `win32gui.GetWindowText()` will return `Search Clinical Diagnoses`
exactly.

```python
# Search Clinical Diagnoses window detection:
SEARCH_DX_WINDOW_TITLE = 'Search Clinical Diagnoses'

def is_search_dx_open() -> bool:
    """Returns True if the Search Clinical Diagnoses dialog is open."""
    found = []
    def enum_callback(hwnd, _):
        if win32gui.GetWindowText(hwnd) == SEARCH_DX_WINDOW_TITLE:
            found.append(hwnd)
    win32gui.EnumWindows(enum_callback, None)
    return len(found) > 0

# When this window is open, AC process count = 3 (vs 2 for home screen)
# The 'Amazing Charts EHR (32 bit) (3)' in Task Manager indicates
# that either the Search Dx window OR the Orders window is open
# (both open as separate processes)

# For automation: close this dialog before any other AC interaction
# Use pyautogui.press('escape') or click Cancel button
```

---

## Orders Window

### Observed from: orders_window.png, task_manager_orders.png, write_orders.png

### Write Orders Button Location

**Observed from: write_orders.png**

The `Write Orders` button is in the lower-right sidebar of the Most
Recent Encounter tab, in a vertical button column:

```
[Clinical Assessment (1)]    ← teal button, count in parentheses
[Write Orders]               ← button
[Write Scripts]              ← button
[☐ Patient Ed Given]        ← checkbox
[Forward Chart]              ← large blue button
[Sign-Off]                   ← button
```

**Also visible:** The Assessment text area shows the full assessment with
4 diagnoses, each in the `# [Name] ([ICD-10]):[Plan text]` format.

The `Clinical Assessment (1)` button indicates 1 item in the clinical
assessment queue. Clicking it opens an assessment-related workflow.

### Orders Window (Full View)

**Observed from: orders_window.png**

**Window title:** `Orders for [LASTNAME], [FIRSTNAME] (DOB: MM/DD/YYYY; ID: [MRN]) [age/sex]`

**Window menu bar:** `Define Order Sets | Help`

**IMPORTANT:** The `Define Order Sets` menu item is in the Orders window.
This is the native AC mechanism for order sets — however, per the
development plan, this feature was REMOVED from AC (the original problem
that motivated Feature F8 in CareCompanion).

### Orders Window Layout

**Top section — Reason For Order:**
- `(check/uncheck all)` checkbox at top
- Table of active diagnoses with checkboxes:
  ```
  ☑  J01.90   Acute sinusitis
  ☑  U07.1    COVID-19
  ☑  E11.69   Hyperlipidemia due to type 2 diabetes mellitu...
  ☑  R06.2    Wheeze
  ```
- `Search Diagnosis` field + `Lookup Dx` button (top right of this section)

**Order category tabs (horizontal tab bar):**
```
🏥 Nursing  |  🧪 Labs  |  📷 Imaging  |  👥 Referrals  |  📋 Follow-Up  |  📚 Patient Ed  |  📦 Other  |  🔬 Diagnostics
```

**Quick Add button** — top right of the order area
**Print Orders button** — top right

**Send selected orders to:** dropdown + field

**Nursing Orders section (currently visible tab):**
Two sub-tabs: `General | Immunizations`

**Confirmed Nursing/General orders list (scrollable, with CPT codes):**
```
☐  ....Cerumen removal Left (Lavage only) (CPT [code])     Comments field
☐  ....Cerumen removal Left (Lavage only)
☐  ....Cerumen removal Right (Lavage only) (CPT [code])
☐  ....Cerumen removal: Left (Instrument) (CPT [code])
☐  ....Cerumen removal: Right (Instrument) (CPT [code])
☐  ....EKG (Electrocardiogram) (CPT 93000)
☐  ....Inhaler Demo (CPT 94664)
☐  ....Jet Aerosol (CPT 94640)
☐  ....Levalbuterol .63mg/3ml (CPT J7614)
☐  ....Levalbuterol 1.25mg/3ml (CPT J7614)
☐  ....Mini Mental Status Exam                              Charged as part of visit
☐  ....Spirometry (bron eval) (CPT 94060)
☐  ....Spirometry (well) (CPT 94010)
☐  ....Visual Acuity (CPT 99173)
☐  ....Ace wrap (specify size)                              Included in procedure
☐  ....Adaptic dressing for Skin tear/abrasion              Included in procedure
☐  ....Administration Fee: Therapeutic, Prophylactic...     Specify and chart the med...
[additional items below scroll]
```

**Right panel — Order Queue:**
- `State | Order Text | Date Sent` columns (empty = no orders queued yet)
- `Order Date:` date picker (3/17/2026)
- `Ordering Provider:` dropdown (`Cory Denton, FNP`)
- `Order` table (empty)

**Bottom buttons:**
- `Save Orders` — saves without sending
- `Send Order Message` — sends orders

### Task Manager — Orders Window Process

**Observed from: task_manager_orders.png**

When the Orders window is open, AC shows 3 child processes and consumes
significantly more memory:
```
Amazing Charts EHR (32 bit) (3)         0.2%    204.7 MB
    ├── Amazing Charts  Family Practice Associates of Chesterfield
    ├── Orders for TEST, TEST (DOB: 10/1/1980; ID: 62815) 45 year ...  ← Orders window
    └── TEST, TEST (DOB: 10/1/1980; ID: 62815) 45 year old woman,
```
Note: Google Chrome is consuming 3,445.6 MB simultaneously — confirms
the work PC has memory pressure when AC + Chrome are both running.

**CareCompanion Order Set Automator (Feature F8) — Critical Details:**

```python
# Orders window title format:
# 'Orders for [LASTNAME], [FIRSTNAME] (DOB: MM/DD/YYYY; ID: [MRN]) [age/sex]'

def is_orders_window_open() -> bool:
    """Returns True if the Orders window is open."""
    found = []
    def enum_callback(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if title.startswith('Orders for ') and 'DOB:' in title:
            found.append(hwnd)
    win32gui.EnumWindows(enum_callback, None)
    return len(found) > 0

# The Orders window opens as a separate process (like Search Clinical Dx)
# AC process count = 3 when Orders window is open

# ORDER TABS confirmed from screenshot:
AC_ORDER_TABS = ['Nursing', 'Labs', 'Imaging', 'Referrals',
                 'Follow-Up', 'Patient Ed', 'Other', 'Diagnostics']

# Nursing tab has two sub-tabs: 'General' | 'Immunizations'

# Order checkbox format in list:
# '....OrderName (CPT XXXXX)'  with optional Comments column
# Four dots '....' prefix on most order items

# For Feature F8 (Order Set Automator) PyAutoGUI sequence:
# 1. Verify patient chart is open (correct patient MRN in title)
# 2. Click 'Write Orders' button in right sidebar
# 3. Wait for Orders window to open (poll is_orders_window_open())
# 4. For each order in the set:
#    a. Click the correct tab (Nursing / Labs / Imaging / etc.)
#    b. If sub-tabs exist (Nursing > General/Immunizations), click sub-tab
#    c. Scroll to find the order by text match (OCR or coordinate)
#    d. Check the checkbox
# 5. Click 'Save Orders' or 'Send Order Message'
# 6. Verify Orders window closes

# The 'Define Order Sets' menu in the Orders window:
# This is AC's native (but removed) order set feature
# Do NOT use this — it was removed from the practice's AC installation
# CareCompanion's F8 replaces this functionality entirely

# Ordering Provider dropdown shows: 'Cory Denton, FNP'
# This confirms the provider display format for the orders system
# Format: '[FirstName] [LastName], [Credentials]'

# MEMORY NOTE: Orders window + Chrome = high memory usage on this PC
# Keep CareCompanion's browser footprint minimal during order automation
# Consider closing non-essential Chrome tabs before running order automation
```

---

## Complete AC Process Count Reference

Based on all Task Manager screenshots, AC child process count indicates state:

```python
AC_PROCESS_STATES = {
    1: 'login_screen_only',           # Just the login dialog
    2: 'home_screen_or_chart_open',   # Home screen OR patient chart open
    3: 'dialog_or_secondary_window',  # Orders, Search Dx, or other dialog open
}

# More precise detection using win32gui window title enumeration:
# Title = 'Amazing Charts' alone → login screen
# Title = 'Amazing Charts  Family Practice...' → home screen (no chart)
# Title matches patient chart pattern → chart open
# Title = 'Orders for ...' → Orders window open
# Title = 'Search Clinical Diagnoses' → Dx search open
# Title = 'Edit Active Problem List' → Problem list editor open
# Title starts with 'Allergies For' → Allergies dialog open
# Title = 'Rx Current Medication List' → Medication dialog open
# Title = 'Resurrect Last Note?' → Resurrect dialog (startup)
# Title starts with 'Flags for' → Flags dialog open
# Title starts with 'Reminders for' → Reminder dialog open
# Title = 'Physical Exam Templates' → Template selection open
# Title = 'Add/Edit Templates' → Template editor open
# Title = 'Editing Problems' → Problem edit dialog open
# Title = 'Edit Active Problem List' → Problem list from encounter
# Title = '[LASTNAME], [FIRSTNAME] (DOB...' (with CDS content) → CDS window
```

---

## Final Summary: Confirmed AC Window Titles

All window titles observed and confirmed across all screenshot batches:

```python
AC_WINDOW_TITLES = {
    # Main windows
    'login':                'Amazing Charts',
    'home':                 'Amazing Charts  Family Practice Associates of Chesterfield',
    'patient_chart':        r'[A-Z]+, [A-Z]+ \(DOB: \d+/\d+/\d+; ID: \d+\)',  # regex
    'about':                'About Amazing Charts',

    # Dialogs opened from patient chart
    'orders':               r'Orders for .+ \(DOB: .+; ID: \d+\)',  # regex
    'search_dx':            'Search Clinical Diagnoses',
    'allergies':            r'Allergies For .+',  # regex
    'medications':          'Rx Current Medication List',  # or 'Current Medication List'
    'resurrect':            'Resurrect Last Note?',
    'flags':                r'Flags for .+',  # regex
    'reminders':            r'Reminders for .+',  # regex
    'templates':            'Physical Exam Templates',
    'template_editor':      'Add/Edit Templates',
    'edit_problems':        'Editing Problems',
    'edit_problem_list':    'Edit Active Problem List',
    'cds':                  r'.+ \(DOB: .+; ID: \d+\)',  # same as chart but different content
    'clinical_summary':     'Clinical Summary',
    'export_complete':      'Export Complete',
    'hie_config':           r'HIE and PHR Configuration for .+',

    # System dialogs
    'task_scheduler':       'Task Scheduler',
    'system_info':          'System Information',
}
```

---

*Document complete. Final update 3/17/2026 (batch 4 — final batch) covering:
Edit Active Problem List dialog, Physical Exam Templates window (full template
list), template access via Edit > My Preferences > Templates (Ctrl+T),
Add/Edit Templates window (complete TextBox Location list and template format),
template export path format, template stacking behavior, Change Date/Time
green dot button, Search Clinical Diagnoses window and process name,
Lookup Dx button layout, Orders window (full tab list and order format),
Write Orders button location, Task Manager process counts for all AC states,
and complete AC window title reference. Total images processed: 55+.*

---

## Patient Data Extraction

This section consolidates the former AC_PATIENT_INFO_GUIDE into the AC
interface ground-truth document.

### Purpose

Clinical Summary XML export is the primary structured data source for patient
chart hydration in CareCompanion. It reduces navigation burden in AC by
collecting medications, diagnoses, allergies, vitals, labs, immunizations,
demographics, and social history in one parseable payload.

### Two-phase export workflow

Phase 1 - chart preparation for all scheduled patients:
1. Search patient in AC Patient List by ID.
2. Verify name before opening chart.
3. Open chart and apply Visit Template -> Procedure Visit -> Companion.
4. Save and close chart with Ctrl+S.

Phase 2 - XML export for all scheduled patients:
1. Confirm AC is on home screen (no chart windows open).
2. Select patient chart row from inbox (single-click).
3. Open Patient menu and choose Export Clinical Summary.
4. Select Full Patient Record and export.

Critical rule: never export while any patient chart window is open.

### File naming convention

`ClinicalSummary_PatientId_[MRN]_[YYYYMMDD]_[HHMMSS].xml`

### XML standard and namespaces

- Standard: HL7 CDA / C-CDA R2.1
- Primary namespace: `urn:hl7-org:v3`
- Additional namespaces in examples: `sdtc`, `xsi`

### Core extraction map

Demographics (header):
- MRN, name, DOB, sex, address, telecom

Structured sections:
- Medications (LOINC 10160-0)
- Allergies (LOINC 48765-2)
- Problems/diagnoses (LOINC 11450-4)
- Vitals (LOINC 8716-3)
- Results/labs (LOINC 30954-2)
- Immunizations (LOINC 11369-6)
- Social history (LOINC 29762-2)

Narrative sections:
- Progress notes (LOINC 11506-3)
- Plan of care (LOINC 18776-5)
- Reason for visit (LOINC 29299-5)

### Empty/null handling expectations

- Use section-level `nullFlavor` checks where present.
- Support negation patterns for sections like allergies or immunizations.
- Treat missing optional entries as empty values, not parser failures.

### Storage and refresh expectations

- Parsed data is upserted into patient-adjacent tables by MRN and section keys.
- Re-import should update existing rows when source values change.
- XML files are retained locally and cleaned by scheduled retention policy.

### Display linkage

Patient Chart View consumes parsed XML data for medication, lab, diagnosis,
allergy, immunization, and vitals tabs. Narrative note prep remains editable
and can be sent back to AC through automation workflows.

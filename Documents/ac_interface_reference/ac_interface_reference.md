# Amazing Charts Interface Reference
# File: ac_interface_reference.md
# Location: np-companion/ (project root, alongside init.prompt.md)
#
# This document describes the Amazing Charts (AC) desktop application interface
# as observed from live screenshots. GitHub Copilot should use this as the
# ground-truth reference for all PyAutoGUI automation, OCR region targeting,
# and pywin32 window management code written for NP Companion.
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

**For NP Companion Note Reformatter automation:**
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

**Note:** This feature is NOT used by NP Companion. The `Export Clinical Summary`
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

**Recommended folder structure for NP Companion:**
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

## Automation Strategy Summary for NP Companion

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
on 3/16/2026. Update this file when new interface areas are photographed.*

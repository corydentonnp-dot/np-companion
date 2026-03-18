# AC Patient Info Guide — Clinical Summary Pipeline

**NP Companion Documentation**
Last updated: 03/16/2026

---

# **Section 1: Purpose and Rationale**

Amazing Charts requires 8+ clicks to navigate between medications, labs, and diagnoses for a single patient. The sections are spread across different tabs (F5 Demographics, F6 Summary Sheet, F7 Most Recent Encounter, Ctrl+M Medications, etc.) with no single view showing all clinical data at once.

The **Clinical Summary XML export** provides all structured patient data in a single machine-readable file. NP Companion parses this file once and displays it in a unified, fast, browser-based **Patient Chart View** (Feature 10e) with zero AC navigation required.

**The pipeline works in three stages:**

1. **Collect** — Export a Clinical Summary XML from Amazing Charts (automated or on-demand)
2. **Parse** — Extract structured data (medications, diagnoses, allergies, vitals, labs, immunizations, demographics) from the HL7 CDA XML file
3. **Display** — Present all data in a single browser page with sidebar tabs, plus a Prepped Note tab for pre-charting and direct injection back into AC

**Key benefits:**
- All patient data visible in one browser window instead of 8+ clicks in AC
- Pre-visit note preparation with direct paste-back into AC via PyAutoGUI
- Structured XML data is more reliable than OCR for medications, diagnoses, and demographics
- Narrative sections (HPI, Assessment, Plan) remain OCR-or-manual fallback only
- Lab results, when present, feed directly into the Lab Value Tracker (Feature 11)

---

# **Section 2: Data Collection — How Patient Data Enters NP Companion**

## **Two triggers for Clinical Summary export:**

### **Trigger 1: Scheduled patients (overnight pre-visit prep)**

The pre-visit note prep job (Feature 9) runs overnight via `agent/scheduler.py` for every patient on tomorrow's schedule. This is a **two-phase batch process** — all charts are opened first, then all exports happen.

#### Phase 1 — Chart Opening (repeat for ALL patients before exporting)

For each patient on the schedule:

1. In the **Patient List** panel — the blue search field underneath the "Schedule", "Messages", "Reports", "Secure" buttons — search by patient ID (from the NetPractice schedule)
2. Verify the first and last name match the expected patient
3. **Double-click** the verified name to open a new chart
4. In the chart window (title bar format: `LASTNAME, FIRSTNAME  (DOB: M/D/YYYY; ID: XXXXX)`), select the **Visit Template** radio button (not "Encounter")
5. Click the **Select Template** dropdown → **Procedure Visit** → **Companion**
6. Clear any popup boxes (click OK or X)
7. Press **Ctrl+S** to save and close the chart (this sends the note to the inbox)
8. Repeat steps 1–7 for every patient on the schedule

#### Phase 2 — XML Export (only after ALL charts are in the inbox)

For each patient on the schedule:

1. Ensure AC is on the **home screen** (no chart windows open — **critical constraint**)
2. In the inbox, find the patient's **most recent chart** — verify by checking the time column, patient name, and MRN
3. Single-click the chart row to select it (do NOT double-click)
4. Open the Patient menu: `Alt+P`
5. Click `Export Clinical Summary` (near the bottom of the Patient menu)
6. In the Export dialog:
   - Select **"Full Patient Record"** from the "Select Encounter Date" dropdown
     (do NOT use the default single encounter — we always want the complete patient record)
   - Verify all section checkboxes are checked
   - Verify the destination folder is correct
7. Click the `Export` button
8. Dismiss the "Export Succeeded" dialog by pressing `Enter`
9. The file appears in the configured export folder
10. Repeat steps 2–9 for every patient on the schedule

### **Trigger 2: On-demand (provider-initiated refresh)**

The provider clicks "Load from Amazing Charts" or "Refresh from AC" on any patient chart view in NP Companion. For a single-patient on-demand export:
1. Open the patient's chart (double-click from Patient List, apply Visit Template → Procedure Visit → Companion), then Ctrl+S to close to inbox
2. With AC on the home screen, find the patient in the inbox, single-click to select
3. Alt+P → Export Clinical Summary → select **"Full Patient Record"** from encounter dropdown → verify destination folder → Export → Enter to dismiss

## **Critical constraint — no chart windows open during export**

The Clinical Summary export (Phase 2) requires the AC **home screen** to be the active view. If any patient chart windows are open, the export will fail or export the wrong patient's data. Before every export:
1. Verify the AC window title does NOT contain `ID:` (which indicates a chart is open)
2. If a chart is open, send `Ctrl+S` to save and close it, then verify the title bar again
3. Only proceed with the export after confirming the home screen is active

## **File naming convention**

AC writes the XML file to a pre-configured export folder with this naming pattern:
```
ClinicalSummary_PatientId_[MRN]_[YYYYMMDD]_[HHMMSS].xml
```
Example: `ClinicalSummary_PatientId_62815_20260316_130657.xml`

The MRN in the filename matches the MRN in the XML header (`//cda:recordTarget/cda:patientRole/cda:id/@extension`).

## **File watcher mechanism**

NP Companion uses Python's `watchdog` library to monitor the `data/clinical_summaries/` folder. When AC writes a new XML file:
1. The file watcher detects the new file event
2. The parser (`agent/clinical_summary_parser.py`) is triggered automatically
3. The parsed data is written to the database
4. The patient chart view refreshes with the new data

As an alternative to the file watcher, polling checks `data/clinical_summaries/` every 5 seconds after an export is triggered, with a 15-second timeout.

---

# **Section 3: XML Structure and Field Extraction Map**

## **Document format**

- **Standard:** HL7 CDA (Clinical Document Architecture), C-CDA R2.1
- **Source EHR:** Amazing Charts
- **Namespace:** `{'cda': 'urn:hl7-org:v3'}`
- **Additional namespaces:** `sdtc` = `urn:hl7-org:sdtc`, `xsi` = `http://www.w3.org/2001/XMLSchema-instance`
- **Document templateIds:**
  - `2.16.840.1.113883.10.20.22.1.1` (US Realm Header, extension `2015-08-01`)
  - `2.16.840.1.113883.10.20.22.1.2` (CCD, extension `2015-08-01`)

All XPaths below are verified against sample file `ClinicalSummary_PatientId_62815_20260316_130657.xml`.

---

## **3.1 Patient Demographics**

**Location:** CDA header (not a body section — no section templateId)
**XPath root:** `//cda:ClinicalDocument/cda:recordTarget/cda:patientRole`

| Field | XPath (relative to patientRole) | Sample Value |
|-------|-------------------------------|--------------|
| MRN | `cda:id/@extension` | `62815` |
| MRN OID | `cda:id/@root` | `2.16.840.1.113883.3.1167.2799` |
| Given Name | `cda:patient/cda:name/cda:given` | `TEST` |
| Family Name | `cda:patient/cda:name/cda:family` | `TEST` |
| DOB | `cda:patient/cda:birthTime/@value` | `19801001` (YYYYMMDD) |
| Sex | `cda:patient/cda:administrativeGenderCode/@code` | `F` |
| Sex Display | `cda:patient/cda:administrativeGenderCode/@displayName` | `Female` |
| Race | `cda:patient/cda:raceCode/@code` | Check `@nullFlavor` first — `UNK` if unknown |
| Ethnicity | `cda:patient/cda:ethnicGroupCode/@code` | Check `@nullFlavor` first — `UNK` if unknown |
| Street | `cda:addr[@use='HP']/cda:streetAddressLine` | `13911 St Francis Blvd` |
| City | `cda:addr[@use='HP']/cda:city` | `Midlothian` |
| State | `cda:addr[@use='HP']/cda:state` | `VA` |
| Zip | `cda:addr[@use='HP']/cda:postalCode` | `23114` |
| Phone | `cda:telecom[@use='HP']/@value` | `tel:+1(804)-320-3999` |

---

## **3.2 Medications**

**Section templateId:** `2.16.840.1.113883.10.20.22.2.1.1` (extension `2014-06-09`)
**LOINC:** `10160-0` — History of Medication Use
**Entry templateId:** `2.16.840.1.113883.10.20.22.4.16` (Medication Activity)
**nullFlavor when empty:** No — section has entries when present

**Section XPath:**
```xpath
//cda:component/cda:structuredBody/cda:component/cda:section[
  cda:templateId[@root='2.16.840.1.113883.10.20.22.2.1.1']
]
```

**Per-entry XPaths (relative to `cda:entry/cda:substanceAdministration`):**

| Field | XPath | Notes |
|-------|-------|-------|
| Drug name | `cda:consumable/cda:manufacturedProduct/cda:manufacturedMaterial/cda:code/@displayName` | RxNorm display name |
| RxNorm code | `cda:consumable/cda:manufacturedProduct/cda:manufacturedMaterial/cda:code/@code` | `UNK` when no match |
| Sig reference | `cda:text/cda:reference/@value` | References narrative section (e.g., `#MedicationSig_1`) |
| Dose quantity | `cda:doseQuantity/@value` | Numeric |
| Start date | `cda:effectiveTime/cda:low/@value` | YYYYMMDD format |
| End date | `cda:effectiveTime/cda:high/@value` | Check `@nullFlavor` |

**Active vs. Inactive determination:**
- `<high nullFlavor="UNK" />` → **Active** (no end date)
- `<high value="20260111" />` → **Inactive** (date = inactivation date)
- All `statusCode` values are `completed` regardless — do NOT use statusCode for active/inactive

**Sample data** (Patient 62815 — 11 entries: 7 active, 4 inactive):

| Drug | RxNorm | Start | End | Status |
|------|--------|-------|-----|--------|
| Ventolin HFA 90 mcg/actuation | 801092 | 20260105 | UNK | Active |
| Wegovy 0.25 mg/0.5 mL | 2553501 | 20240701 | UNK | Active |
| Paxlovid 300 mg dose pack | UNK | 20260105 | 20260111 | Inactive |
| Adderall 10 mg tablet | 541892 | 20251105 | 20251206 | Inactive |

---

## **3.3 Allergies**

**Section templateId:** `2.16.840.1.113883.10.20.22.2.6.1` (extension `2015-08-01`)
**LOINC:** `48765-2` — Allergies, adverse reactions, alerts
**Act templateId:** `2.16.840.1.113883.10.20.22.4.30` (Allergy Concern Act)
**Observation templateId:** `2.16.840.1.113883.10.20.22.4.7` (Allergy Observation)
**nullFlavor when empty:** No — uses `negationInd="true"` pattern for NKA

**Section XPath:**
```xpath
//cda:component/cda:structuredBody/cda:component/cda:section[
  cda:templateId[@root='2.16.840.1.113883.10.20.22.2.6.1']
]
```

**Per-entry XPaths (relative to `cda:entry/cda:act/cda:entryRelationship/cda:observation`):**

| Field | XPath | Notes |
|-------|-------|-------|
| Allergen name | `cda:participant[@typeCode='CSM']/cda:participantRole/cda:playingEntity/cda:code/@displayName` | |
| Reaction | `cda:entryRelationship[@typeCode='MFST']/cda:observation/cda:value/@displayName` | |
| Severity | `cda:entryRelationship[@typeCode='SUBJ']/cda:observation/cda:value/@displayName` | |

**NKA (No Known Allergies) detection:**
- Check `cda:observation/@negationInd` — if `"true"`, patient has no known allergies
- The allergen `playingEntity/code` will have `nullFlavor="NA"`
- Return empty list, not an error

**Sample data** (Patient 62815): No Known Allergies (`negationInd="true"`)

---

## **3.4 Active Diagnoses / Problem List**

**Section templateId:** `2.16.840.1.113883.10.20.22.2.5.1` (extension `2015-08-01`)
**LOINC:** `11450-4` — Problem List
**Act templateId:** `2.16.840.1.113883.10.20.22.4.3` (Problem Concern Act)
**Observation templateId:** `2.16.840.1.113883.10.20.22.4.4` (Problem Observation)
**Status observation templateId:** `2.16.840.1.113883.10.20.22.4.6`
**nullFlavor when empty:** No

**Section XPath:**
```xpath
//cda:component/cda:structuredBody/cda:component/cda:section[
  cda:templateId[@root='2.16.840.1.113883.10.20.22.2.5.1']
]
```

**Per-entry XPaths (relative to `cda:entry/cda:act/cda:entryRelationship[@typeCode='SUBJ']/cda:observation`):**

| Field | XPath | Notes |
|-------|-------|-------|
| SNOMED code | `cda:value/@code` | codeSystem `2.16.840.1.113883.6.96` |
| Display name | `cda:value/@displayName` | |
| ICD-10 code | `cda:value/cda:translation/@code` | codeSystem `2.16.840.1.113883.6.3` |
| ICD-10 display | `cda:value/cda:translation/@displayName` | |
| Onset date | `cda:effectiveTime/cda:low/@value` | YYYYMMDD format |
| Status | `cda:entryRelationship[@typeCode='REFR']/cda:observation/cda:value/@displayName` | |

**SNOMED vs. ICD-10 pattern:**
- Most problems use SNOMED directly on `cda:value/@code`
- Some use `cda:value/@nullFlavor="OTH"` with an ICD-10 `cda:translation` child element
- Always check both: try SNOMED first, then check for `cda:translation` if SNOMED is null/OTH

**Sample data** (Patient 62815 — 15 entries, all Active):

| Code | System | Display | Onset |
|------|--------|---------|-------|
| 56018004 | SNOMED | Wheeze | 20260105 |
| U07.1 | ICD-10 | COVID-19 | 20260105 |
| 38341003 | SNOMED | Hypertension | 20231102 |
| 35253001 | SNOMED | Attention deficit disorder | 20231206 |
| 235595009 | SNOMED | Gastro-esophageal reflux disease | 20250222 |

---

## **3.5 Most Recent Vitals**

**Section templateId:** `2.16.840.1.113883.10.20.22.2.4.1` (extension `2015-08-01`)
**LOINC:** `8716-3` — Vital Signs
**Organizer templateId:** `2.16.840.1.113883.10.20.22.4.26` (extension `2015-08-01`)
**Observation templateId:** `2.16.840.1.113883.10.20.22.4.27` (extension `2014-06-09`)
**nullFlavor when empty:** No section-level nullFlavor — individual observations use `nullFlavor="NI"` when empty

**Section XPath:**
```xpath
//cda:component/cda:structuredBody/cda:component/cda:section[
  cda:templateId[@root='2.16.840.1.113883.10.20.22.2.4.1']
]
```

**Per-observation XPaths (relative to `cda:entry/cda:organizer/cda:component/cda:observation`):**

| Field | XPath | Notes |
|-------|-------|-------|
| LOINC code | `cda:code/@code` | Identifies the vital type |
| Display name | `cda:code/@displayName` | |
| Value | `cda:value/@value` | Check `@nullFlavor` first |
| Unit | `cda:value/@unit` | |
| Encounter date | `../../cda:effectiveTime/@value` | On the organizer element |

**Empty value detection:** If `cda:value/@nullFlavor="NI"`, the value is not available — return None, not an error.

**Vital LOINC codes:**

| LOINC | Vital Sign | Typical Unit |
|-------|-----------|--------------|
| 8302-2 | Height | [in_i] or cm |
| 29463-7 | Weight | [lb_av] or kg |
| 39156-5 | BMI (Body Mass Index) | kg/m2 |
| 8480-6 | BP Systolic | mm[Hg] |
| 8462-4 | BP Diastolic | mm[Hg] |
| 8867-4 | Heart Rate | /min |
| 59408-5 | O2 Saturation (Pulse Oximetry) | % |
| 8310-5 | Body Temperature | [degF] or Cel |
| 9279-1 | Respiratory Rate | /min |
| 3150-0 | Inhaled O2 Concentration | — |
| 8287-5 | Head Circumference | cm |
| 77606-2 | Weight-for-length Percentile | % |
| 8289-1 | Head Circumference Percentile | % |
| 59576-9 | BMI Percentile | % |

**Sample data** (Patient 62815): All vital observations present with `nullFlavor="NI"` (open encounter, no vitals entered yet).

---

## **3.6 Lab Results**

**Section templateId:** `2.16.840.1.113883.10.20.22.2.3.1` (extension `2015-08-01`)
**LOINC:** `30954-2` — Results
**nullFlavor when empty:** **YES** — `<section nullFlavor="NI">`

**Section XPath:**
```xpath
//cda:component/cda:structuredBody/cda:component/cda:section[
  cda:templateId[@root='2.16.840.1.113883.10.20.22.2.3.1']
]
```

**Empty check:** If the section element has `@nullFlavor="NI"`, return an empty list.

**When populated, per-entry XPaths (relative to `cda:entry/cda:organizer/cda:component/cda:observation`):**

| Field | XPath | Notes |
|-------|-------|-------|
| LOINC test code | `cda:code/@code` | |
| Test name | `cda:code/@displayName` | |
| Result value | `cda:value/@value` | |
| Units | `cda:value/@unit` | |
| Date | `cda:effectiveTime/@value` | YYYYMMDD format |
| Reference range | `cda:referenceRange/cda:observationRange/cda:text` | Free text |
| Abnormal flag | `cda:interpretationCode/@code` | H=High, L=Low, N=Normal |

**Sample data** (Patient 62815): No lab results — section has `nullFlavor="NI"`. Narrative: "No Lab Test required. No Lab results."

---

## **3.7 Immunizations**

**Section templateId:** `2.16.840.1.113883.10.20.22.2.2.1` (extension `2014-06-09`)
**LOINC:** `11369-6` — History of Immunizations
**Entry templateId:** `2.16.840.1.113883.10.20.22.4.52` (Immunization Activity, extension `2015-08-01`)
**Product templateId:** `2.16.840.1.113883.10.20.22.4.54` (extension `2014-06-09`)
**nullFlavor when empty:** No — uses `negationInd="true"` pattern

**Section XPath:**
```xpath
//cda:component/cda:structuredBody/cda:component/cda:section[
  cda:templateId[@root='2.16.840.1.113883.10.20.22.2.2.1']
]
```

**Per-entry XPaths (relative to `cda:entry/cda:substanceAdministration`):**

| Field | XPath | Notes |
|-------|-------|-------|
| negationInd | `@negationInd` | `true` = NOT given / no history |
| CVX code | `cda:consumable/cda:manufacturedProduct/cda:manufacturedMaterial/cda:code/@code` | |
| Vaccine name | `cda:consumable/cda:manufacturedProduct/cda:manufacturedMaterial/cda:code/@displayName` | |
| Date | `cda:effectiveTime/@value` | Check `@nullFlavor` |
| Status | `cda:statusCode/@code` | Check `@nullFlavor` |

**No-history detection:** If `@negationInd="true"`, the patient has no known immunization history. Return empty list.

**Sample data** (Patient 62815): No known immunization history (`negationInd="true"`, all sub-elements `nullFlavor="NI"`).

---

## **3.8 Social History**

**Section templateId:** `2.16.840.1.113883.10.20.22.2.17` (extension `2015-08-01`)
**LOINC:** `29762-2` — Social History
**nullFlavor when empty:** No

**Section XPath:**
```xpath
//cda:component/cda:structuredBody/cda:component/cda:section[
  cda:templateId[@root='2.16.840.1.113883.10.20.22.2.17']
]
```

**Three entry types:**

| Entry Type | templateId | LOINC | XPath for value |
|-----------|-----------|-------|----------------|
| Tobacco Use (History) | `2.16.840.1.113883.10.20.22.4.85` | `11367-0` | `.//cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.85']]/cda:value` |
| Smoking Status (Current) | `2.16.840.1.113883.10.20.22.4.78` | `72166-2` | `.//cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.78']]/cda:value` |
| Birth Sex | `2.16.840.1.113883.10.20.22.4.200` | `76689-9` | `.//cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.200']]/cda:value` |

Values are SNOMED codes on `@code` with human-readable `@displayName`.

**Sample data** (Patient 62815):
- Tobacco Use: SNOMED `266919005` — "Never smoker or smoked < 100 cigarettes/lifetime"
- Smoking Status: SNOMED `266919005` — "Never smoker or smoked < 100 cigarettes/lifetime"
- Birth Sex: `F` — "Female"

---

## **3.9 Goals, Health Concerns, and Assessments**

| Section | templateId | LOINC | nullFlavor when empty |
|---------|-----------|-------|-----------------------|
| Goals | `2.16.840.1.113883.10.20.22.2.60` | `61146-7` | **YES** |
| Health Concerns | `2.16.840.1.113883.10.20.22.2.58` (ext `2015-08-01`) | `75310-3` | **YES** |
| Assessments | `2.16.840.1.113883.10.20.22.2.8` | `51848-0` | **YES** |
| Mental Status | `2.16.840.1.113883.10.20.22.2.56` (ext `2015-08-01`) | `10190-7` | **YES** |

All four sections use `nullFlavor="NI"` when empty. Check `section/@nullFlavor` — if `"NI"`, return empty list.

**Sample data** (Patient 62815): All four sections empty (`nullFlavor="NI"`).

---

## **3.10 Narrative Sections (Free Text)**

Narrative-only clinical content is found in the **Progress Notes** section:

**Section templateId:** `2.16.840.1.113883.10.20.22.2.65` (extension `2016-11-01`)
**LOINC:** `11506-3` — Progress Note
**Entry templateId:** `2.16.840.1.113883.10.20.22.4.202` (extension `2016-11-01`)

**XPath to narrative text:**
```xpath
//cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.22.2.65']]/cda:text/cda:list/cda:item/cda:paragraph
```

**Sub-sections within paragraphs (identified by text prefix):**

| Sub-section | Prefix | Content Example |
|-------------|--------|-----------------|
| Chief Complaint | `"Chief Complaint:"` | "cough" |
| HPI | `"History of Present Illness:"` | Sick Visit: Symptoms started 1/2/26... |
| Past Medical History | `"Past Medical History:"` | chronic back pain, DM type 2, Hyperlipidemia |
| Family History | `"Family History:"` | NA, adopted |
| Social History | `"Social History:"` | Never smoker, no EtOH, No drugs, Married |
| Medications | `"Medications:"` | Serialized GUIDs (NOT human-readable — use structured section instead) |
| Physical Examination | `"Physical Examination:"` | General: fatigued, nontoxic, NAD... |
| Assessment & Plan | `"Assessment & Plan:"` | COVID-19 (U07.1): Start paxlovid... |

To extract a specific sub-section, parse each `<paragraph>` text content and match on the prefix string.

**Other narrative-only sections:**

| Section | templateId | LOINC | XPath |
|---------|-----------|-------|-------|
| Reason for Visit | `2.16.840.1.113883.10.20.22.2.12` | `29299-5` | `//cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.22.2.12']]/cda:text` |
| Plan of Care | `2.16.840.1.113883.10.20.22.2.10` | `18776-5` | `//cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.22.2.10']]/cda:text` |

---

## **3.11 Complete Section Index**

| Section | templateId Root | LOINC | nullFlavor? | Has Entries in Sample? |
|---------|----------------|-------|-------------|----------------------|
| Encounters | `2.16.840.1.113883.10.20.22.2.22.1` | `46240-8` | No | Yes (empty data) |
| Allergies | `2.16.840.1.113883.10.20.22.2.6.1` | `48765-2` | No | Yes (negated=NKA) |
| Functional Status | `2.16.840.1.113883.10.20.22.2.14` | `47420-5` | Yes | No |
| Reason for Visit | `2.16.840.1.113883.10.20.22.2.12` | `29299-5` | Yes | Narrative only |
| Immunizations | `2.16.840.1.113883.10.20.22.2.2.1` | `11369-6` | No | Yes (negated) |
| Instructions | `2.16.840.1.113883.10.20.22.2.45` | `69730-0` | Yes | No |
| Medical Equipment | `2.16.840.1.113883.10.20.22.2.23` | `46264-8` | No | Yes (negated) |
| Medications | `2.16.840.1.113883.10.20.22.2.1.1` | `10160-0` | No | **Yes (11 entries)** |
| Insurance | `2.16.840.1.113883.10.20.22.2.18` | `48768-6` | Yes | No |
| Plan of Care | `2.16.840.1.113883.10.20.22.2.10` | `18776-5` | No | Yes (1 entry) |
| Problems | `2.16.840.1.113883.10.20.22.2.5.1` | `11450-4` | No | **Yes (15 entries)** |
| Procedures | `2.16.840.1.113883.10.20.22.2.7.1` | `47519-4` | No | Yes (empty) |
| Reason for Referral | `1.3.6.1.4.1.19376.1.5.3.1.3.1` | `42349-1` | Yes | No |
| Results (Labs) | `2.16.840.1.113883.10.20.22.2.3.1` | `30954-2` | Yes | No |
| Social History | `2.16.840.1.113883.10.20.22.2.17` | `29762-2` | No | **Yes (3 entries)** |
| Vital Signs | `2.16.840.1.113883.10.20.22.2.4.1` | `8716-3` | No | **Yes (14 obs, all NI)** |
| Goals | `2.16.840.1.113883.10.20.22.2.60` | `61146-7` | Yes | No |
| Health Concerns | `2.16.840.1.113883.10.20.22.2.58` | `75310-3` | Yes | No |
| Mental Status | `2.16.840.1.113883.10.20.22.2.56` | `10190-7` | Yes | No |
| Assessments | `2.16.840.1.113883.10.20.22.2.8` | `51848-0` | Yes | No |
| Progress Notes | `2.16.840.1.113883.10.20.22.2.65` | `11506-3` | No | **Yes (full note)** |
| Care Teams | `2.16.840.1.113883.10.20.22.2.500` | `85847-2` | No | Yes |

---

# **Section 4: Database Storage Schema**

## **Upsert strategy**

When a Clinical Summary is re-parsed for a patient (e.g., after a refresh), the parser uses upsert logic — update existing records on re-parse, don't create duplicates.

| Data Type | Table | Upsert Key | Behavior |
|-----------|-------|-----------|----------|
| Medications | Medication | `drug_name + mrn` | Update dose/status/dates if changed |
| Diagnoses | CareGap-adjacent (Problem model) | `code + mrn` | Update status/onset if changed |
| Lab Results | LabResult | `test_code + mrn + date` | Insert only (labs are point-in-time) |
| Vitals | PatientVitals (new table) | `mrn + encounter_date` | Update if encounter date matches |
| Allergies | PatientAllergy (new table) | `allergen + mrn` | Upsert by allergen name |
| Immunizations | PatientImmunization (new table) | `vaccine_code + mrn + date` | Insert only |
| Demographics | Patient (existing) | `mrn` | Update all fields |
| Social History | PatientSocialHistory (new table) | `mrn + entry_type` | Update value on re-parse |

## **Tracking timestamps**

Each patient record includes:
- `last_xml_parsed` — timestamp of the most recent successful Clinical Summary parse
- `last_xml_file` — hashed reference to the source file (not the full path — no PHI in logs)

## **Auto-deletion job**

XML Clinical Summary files are stored in `data/clinical_summaries/` on the local machine. A daily scheduled job (`agent/scheduler.py`) runs at 2:00 AM:
1. Scans `data/clinical_summaries/` for all `.xml` files
2. Deletes any file with mtime older than `CLINICAL_SUMMARY_RETENTION_DAYS` (default 183, configurable in `config.py`)
3. Logs each deletion to AuditLog: `user_id=system`, `action="xml_archive_delete"`, `details=sha256(filename)[:12]`

---

# **Section 5: Browser Display — Patient Chart View**

## **Patient Chart View (Feature 10e)**

The Patient Chart View is NP Companion's primary patient data display. It presents all parsed Clinical Summary data in a single browser page, accessible from:
1. **Today View** — click any patient name to open their chart
2. **Dashboard search bar** — search by name or MRN (Feature 4f)

### **Layout**

**Header bar:**
- Patient name, DOB, age/sex, MRN (last 4 digits only), last updated timestamp
- "Refresh from AC" button — triggers Clinical Summary export + re-parse
- "Last synced: [timestamp]" indicator

**Left sidebar tabs (mirrors AC section structure):**

| Icon | Tab | Data Source |
|------|-----|-------------|
| 📋 | Overview | Configurable widgets (see below) |
| 💊 | Medications | XML → Medication table |
| 🔬 | Labs | XML → LabResult table (links to F11) |
| 🩺 | Diagnoses | XML → Problem table |
| 💉 | Immunizations | XML → PatientImmunization table |
| 📊 | Vitals | XML → PatientVitals table |
| ⚠️ | Allergies | XML → PatientAllergy table |
| 📝 | Prepped Note | Draft notes (see below) |
| 📁 | Care Gaps | Links to F15 care gap tracker |

### **Overview tab — configurable widgets**

Users configure which widgets appear on the overview landing page. Available widgets:
- Active Medications (count + list)
- Recent Labs (last 3 results per tracked lab)
- Active Diagnoses (problem list)
- Recent Vitals (last BP, weight, BMI)
- Prior Screenings / Care Gaps due
- On-Call Notes for this patient
- Upcoming Appointments

Widget layout is saved per user in the preferences JSON column.

### **Prepped Note tab**

A plain-text note workspace with one labeled text area per AC note section. Sections match the Enlarge Textbox window exactly, in the canonical `AC_NOTE_SECTIONS` order:

```
Chief Complaint | History of Present Illness | Review of Systems |
Past Medical History | Social History | Family History | Allergies |
Medications | Physical Exam | Functional Status/Mental Status |
Confidential Information | Assessment | Plan | Instructions |
Goals | Health Concerns
```

Each section is a resizable textarea with:
- Label at top
- Monospace font
- Pre-populated from Clinical Summary XML where available (structured sections)
- Left blank for narrative sections (HPI, Assessment, Plan) which the provider fills
- Auto-save to localStorage every 30 seconds (no data loss on browser close)

**Three action buttons:**

| Button | Action |
|--------|--------|
| `Copy All to Clipboard` | Formats all sections with headers and copies to clipboard |
| `Send to Amazing Charts` | Triggers PyAutoGUI to paste each section into the Enlarge Textbox window using `Update & Go to Next Field` |
| `Save Draft` | Saves current content to the database (not sent to AC) |

### **MRN display rule**

MRN is displayed as **last-4 digits only** in any UI element visible on a shared screen. Full MRN is used only in database queries and API calls.

### **No data state**

If no XML has been parsed for a patient, show a "No clinical summary loaded" banner with a "Load from Amazing Charts" button that triggers the export automation.

---

# **Section 6: AC Automation Details**

## **Export automation sequence**

The exact PyAutoGUI sequence for the two-phase Clinical Summary export:

### Phase 1 — Chart Opening (per patient)

| Step | Action | Code Pattern |
|------|--------|-------------|
| 1 | Verify AC is foreground | `is_ac_foreground()` returns True |
| 2 | Search patient by ID | Click Patient List search field (blue, under Schedule/Messages/Reports/Secure), type patient ID |
| 3 | Verify name match | OCR or read patient name from list, compare to expected |
| 4 | Open chart | Double-click the verified patient row |
| 5 | Select Visit Template | Click "Visit Template" radio button (not "Encounter") |
| 6 | Apply template | Click "Select Template" dropdown → Procedure Visit → Companion |
| 7 | Clear popups | Click OK or X on any popup boxes |
| 8 | Close chart to inbox | `pyautogui.hotkey('ctrl', 's')` — sends note to inbox |

Repeat Phase 1 for ALL patients before starting Phase 2.

### Phase 2 — XML Export (per patient, only after ALL charts are in inbox)

| Step | Action | Code Pattern |
|------|--------|-------------|
| 1 | Verify AC is foreground | `is_ac_foreground()` returns True |
| 2 | Verify no chart window open | Title does NOT contain `ID:` |
| 3 | Find patient in inbox | Locate most recent chart by time column, verify name + MRN |
| 4 | Select chart row | Single-click the inbox row (do NOT double-click) |
| 5 | Open Patient menu | `pyautogui.hotkey('alt', 'p')` |
| 6 | Click "Export Clinical Summary" | `pyautogui.click(x, y)` — near bottom of Patient menu |
| 7 | Specify destination folder | Verify/set the export folder path in the dialog |
| 8 | Select \"Full Patient Record\" | From the encounter dropdown — never use a single encounter |
| 9 | Verify checkboxes | All section checkboxes should be checked |
| 10 | Click Export button | `pyautogui.click(x, y)` |
| 11 | Dismiss success dialog | `pyautogui.press('enter')` |
| 12 | Wait for file | Poll/watch `data/clinical_summaries/` for `ClinicalSummary_PatientId_[MRN]_*.xml` |

**Timeout:** 15 seconds for file to appear. Return None on timeout.

## **Window verification using win32gui**

```python
import win32gui
import re

def is_ac_foreground() -> bool:
    title = win32gui.GetWindowText(win32gui.GetForegroundWindow())
    return title.startswith('Amazing Charts')

def get_active_patient_mrn() -> str | None:
    title = win32gui.GetWindowText(win32gui.GetForegroundWindow())
    match = re.search(r'ID:\s*(\d+)', title)
    return match.group(1) if match else None

def is_chart_window_open() -> bool:
    title = win32gui.GetWindowText(win32gui.GetForegroundWindow())
    return 'ID:' in title
```

## **Error handling**

| Scenario | Phase | Detection | Recovery |
|----------|-------|-----------|----------|
| AC not running | Both | `find_ac_window()` returns None | Log error, send push notification |
| Patient not found in list | 1 | Search returns no matching ID | Log error, skip patient, continue |
| Name mismatch | 1 | Displayed name ≠ expected name | Log error, skip patient, continue |
| Template selection fails | 1 | Visit Template or Companion not found | Log error, close chart (Ctrl+S), continue |
| Popup won't clear | 1 | Unexpected dialog after 5 seconds | Screenshot, try Escape/Enter, then Ctrl+S |
| Chart window open during export | 2 | Title contains `ID:` | Close chart (Ctrl+S), verify home screen, retry |
| Wrong patient in inbox | 2 | MRN from inbox row ≠ expected MRN | Log error, skip patient, continue |
| Export dialog doesn't appear | 2 | Timeout after 5 seconds | Log error, screenshot for debugging |
| File not created | 2 | 15-second timeout | Log error, retry once |

## **Prepped Note paste-back automation**

To paste a prepped note back into AC via the Enlarge Textbox window:

1. Open patient chart in AC (verify MRN matches)
2. Press `F7` to open Most Recent Encounter
3. Click `Enlarge Textbox` button
4. For each section in `AC_NOTE_SECTIONS` order:
   a. Verify the correct section is selected in the left panel
   b. Clear the text area and paste the section content from NP Companion
   c. Click `Update & Go to Next Field` to advance to the next section
5. After the last section (Health Concerns), click `Update & Close`

**Special sections:**
- `Allergies (Open Allergy Window)` and `Medications (Open Med Window)` open separate windows — automation must handle these as separate window targets
- These two sections are in `AC_SPECIAL_SECTIONS` and require different automation logic

---

# **Section 7: HIPAA and Security**

## **PHI handling rules**

| Rule | Implementation |
|------|---------------|
| XML files are full PHI | Stored locally only, never transmitted |
| Auto-deletion | `data/clinical_summaries/` cleaned daily — files older than 183 days (configurable in `config.py`) |
| Audit logging | Every parse logged to AuditLog: `mrn_hash`, `user_id`, `timestamp`, `sections_found`, `file_path_hash` |
| No patient names in logs | Use `sha256(mrn)[:12]` as the identifier in all log entries |
| MRN display | Last-4 digits only in any shared-screen UI context |
| Git exclusion | `data/clinical_summaries/` is in `.gitignore` |
| Database scoping | All queries scoped to `current_user.id` — one provider cannot see another's patient data |

## **Sensitive files list**

```
data/clinical_summaries/   ← Full PHI XML files, local only, 183-day retention
data/active_user.json      ← Current session user info
data/np_session.pkl         ← NetPractice session cookies
```

---

# **Section 8: AI Prompts**

## **8.1 Clinical Summary Parser — `agent/clinical_summary_parser.py`**

| 💬  AI PROMPT — Copy this into Claude in VS Code: Create agent/clinical\_summary\_parser.py for NP Companion.   This module exports and parses the Amazing Charts Clinical Summary XML.   Function 1 — open\_patient\_chart(mrn: str, patient\_name: str) -> bool: \- Search for the patient by ID in the Patient List panel (blue field under Schedule/Messages/Reports/Secure buttons) \- Verify the first and last name match patient\_name \- Double-click the verified name to open a new chart \- In the chart window, select the "Visit Template" radio button \- Click the "Select Template" dropdown → Procedure Visit → Companion \- Clear any popup boxes (click OK or X) \- Press Ctrl+S to save and close the chart (sends note to inbox) \- Return True on success, False on failure   Function 2 — export\_clinical\_summary(mrn: str) -> str | None: \- Verify AC is on the home screen (no chart windows open) \- Verify no window title contains "ID:" (which indicates a chart is open) \- Find the patient's most recent chart in the inbox (verify by time column, name, and MRN) \- Single-click the chart row to select it \- Open Patient menu (Alt+P) \- Click "Export Clinical Summary" (near bottom of menu) \- In the dialog, select **\"Full Patient Record\"** from the encounter dropdown (never use a single encounter), verify all checkboxes are checked, verify the destination folder \- Click the Export button \- Dismiss the "Export Succeeded" dialog (press Enter) \- Watch data/clinical\_summaries/ for a new file matching ClinicalSummary\_PatientId\_\[MRN\]\_\*.xml \- Return the full file path or None on timeout (15 second timeout)   IMPORTANT: open\_patient\_chart() must be called for ALL patients on the schedule BEFORE calling export\_clinical\_summary() for any patient. This is a two-phase batch workflow.   Function 3 — parse\_clinical\_summary(xml\_path: str) -> dict: \- Parse HL7 CDA XML using xml.etree.ElementTree \- Namespace: {'cda': 'urn:hl7-org:v3'} \- Extract all sections listed below and return as a structured dict \- Sections: patient\_demographics, medications (active and inactive), allergies, diagnoses (active problems), vitals (most recent), lab\_results (all with dates), immunizations, social\_history, encounter\_reason, instructions, goals, health\_concerns \- Any section with nullFlavor="NI" returns an empty list, not an error \- Log the parse to AuditLog table (user\_id, mrn\_hash, timestamp, sections\_found) \- Never log patient names — use sha256(mrn)\[:12\] as the identifier   Function 4 — store\_parsed\_summary(user\_id: int, mrn: str, parsed: dict): \- Write medications to the Medication model (upsert by drug\_name + mrn) \- Write diagnoses to CareGap-adjacent storage \- Write lab results to LabResult model \- Write vitals to a new PatientVitals table \- Set a last\_xml\_parsed timestamp on the patient record   Function 5 — schedule\_deletion(xml\_path: str, days: int = 183): \- Register the file for deletion after \[days\] days via APScheduler \- Log scheduled deletion to AuditLog   Include a file watcher using Python's watchdog library as an alternative to polling, so the parser triggers automatically when AC writes the file. |
| :---- |

---

## **8.2 Patient Chart View — `routes/patient.py`**

| 💬  AI PROMPT — Copy this into Claude in VS Code: Create the Patient Chart View for NP Companion.   routes/patient.py with: \- GET /patient/\<mrn\> — patient chart landing page (Overview tab) \- GET /patient/\<mrn\>/medications — medications tab \- GET /patient/\<mrn\>/labs — lab results tab (integrates with F11 lab tracker) \- GET /patient/\<mrn\>/diagnoses — active problem list tab \- GET /patient/\<mrn\>/immunizations — immunizations tab \- GET /patient/\<mrn\>/vitals — vitals history tab \- GET /patient/\<mrn\>/allergies — allergies tab \- GET /patient/\<mrn\>/note — prepped note tab \- POST /patient/\<mrn\>/note/save — save note draft to database \- POST /patient/\<mrn\>/note/send-to-ac — trigger PyAutoGUI paste to AC \- GET /patient/search?q= — search patients by name or MRN (returns JSON) \- POST /patient/\<mrn\>/refresh — trigger Clinical Summary export + re-parse   templates/patient\_chart.html: \- Left sidebar with tab icons and labels matching the section list above \- Active tab highlighted \- Main content area changes based on active tab \- Header bar showing: patient name, DOB, age/sex, MRN (last 4), last updated timestamp (from last XML parse), "Refresh from AC" button \- "Last synced: \[timestamp\]" indicator — shows how fresh the data is   templates/patient\_note.html (Prepped Note tab): \- One labeled textarea per AC note section (16 sections total, see list) \- Sections in the exact order from AC\_NOTE\_SECTIONS constant \- Each textarea: label at top, resizable, monospace font \- Auto-save to localStorage every 30 seconds (no data loss on close) \- Three action buttons as described above   All data on this page comes from the parsed Clinical Summary XML stored in the database. If no XML has been parsed for this patient, show a "No clinical summary loaded" banner with a "Load from Amazing Charts" button that triggers the export automation.   Scope all database queries to current\_user.id. MRN is displayed as last-4 digits only in any UI element visible on a shared screen. Full MRN is used only in database queries and API calls. |
| :---- |

---

## **8.3 AC Window Manager — `agent/ac_window.py`**

| 💬  AI PROMPT — Copy this into Claude in VS Code: Create agent/ac\_window.py for NP Companion.   This module handles all Amazing Charts window management using pywin32.   Function: find\_ac\_window() -> int | None \- Enumerate all visible windows with win32gui.EnumWindows \- Return hwnd of window whose title starts with 'Amazing Charts' \- Return None if not found   Function: get\_active\_patient\_mrn() -> str | None \- Get title of foreground window with win32gui.GetWindowText \- Extract MRN using regex: r'ID:\\s\*(\\d+)' \- Return MRN string or None   Function: get\_active\_patient\_dob() -> str | None \- Same approach, extract DOB using regex: r'DOB:\\s\*(\[\\d/\]+)'   Function: is\_ac\_foreground() -> bool \- Return True if the foreground window title starts with 'Amazing Charts'   Function: focus\_ac\_window() -> bool \- Find AC window, bring to foreground with win32gui.SetForegroundWindow \- Return True on success, False if AC not found   Function: get\_ac\_chart\_title() -> str | None \- Return full title bar text of the current patient chart window \- Used to verify the correct patient is open before automation runs |
| :---- |

---

## **8.4 Inbox Reader — `agent/inbox_reader.py`**

| 💬  AI PROMPT — Copy this into Claude in VS Code: Create agent/inbox\_reader.py for NP Companion.   This module reads the Amazing Charts inbox using PyAutoGUI and Tesseract OCR.   The inbox is always visible on the AC home screen — it does not need to be navigated to. It requires the AC main window (not a patient chart) to be the foreground window.   Function: read\_inbox(user\_id: int) -> InboxSnapshot: 1\. Verify AC main window is foreground (not a patient chart window) 2\. For each filter in INBOX\_FILTER\_OPTIONS:    a. Click the filter dropdown (second control in inbox header row)    b. Click the filter option by text match    c. Wait 0.5 seconds for table to refresh    d. Take a screenshot of the inbox table region    e. OCR the screenshot with Tesseract, psm=6    f. Parse rows: split on newlines, extract From / Subject / Received    g. Generate item hash: sha256(item\_type + subject + received)\[:16\] 3\. Compare all hashes against last InboxSnapshot for this user\_id 4\. Categorize: new\_items, resolved\_items, held\_items 5\. Write new InboxSnapshot to database 6\. Return the snapshot   INBOX\_FILTER\_OPTIONS (exact label strings): \['Show Charts', 'Show Charts to Co-Sign', 'Show Imports to Sign-Off', 'Show Labs to Sign-Off', 'Show Orders', 'Show Patient Messages'\]   Note: "Show Everything" is read last to get total count.   All coordinates for the filter dropdown and inbox table region come from config.py. Include TODO comments for each coordinate that needs calibration. Include detailed logging so each step is visible when troubleshooting. |
| :---- |

---

"""
CareCompanion — Clinical Summary Exporter & Parser

File location: carecompanion/agent/clinical_summary_parser.py

Two-phase batch workflow for extracting patient data from
Amazing Charts Clinical Summary CDA XML exports.

Phase 1: open_patient_chart() — opens charts + saves with template
Phase 2: export_clinical_summary() — exports XML from inbox

Also provides:
  parse_clinical_summary()   — parses CDA XML into structured data
  store_parsed_summary()     — writes parsed data to the database
  schedule_deletion()        — schedules XML file cleanup
  ClinicalSummaryHandler     — watchdog file observer handler

Feature: F6d (Clinical Summary Exporter & Parser)

HIPAA note: XML files contain full PHI. They are stored in a local
folder and auto-deleted after CLINICAL_SUMMARY_RETENTION_DAYS.
Audit logs use sha256(mrn)[:12] only — never patient names.
"""

import logging
import os
import re
import time
import xml.etree.ElementTree as ET

from utils import safe_patient_id
from datetime import datetime, timedelta, timezone

import config
from agent.ac_window import is_ac_foreground, is_chart_window_open
from agent.ocr_helpers import find_and_click, find_element_near_text, find_text_on_screen

logger = logging.getLogger('agent.clinical_summary')

# HL7 CDA namespace
NS = {'cda': 'urn:hl7-org:v3'}

# LOINC section codes for CDA parsing
SECTION_LOINC = {
    'medications': '10160-0',
    'allergies': '48765-2',
    'diagnoses': '11450-4',
    'vitals': '8716-3',
    'lab_results': '30954-2',
    'immunizations': '11369-6',
    'social_history': '29762-2',
    'encounter_reason': '46239-0',
    'instructions': '69730-0',
    'goals': '61146-7',
    'health_concerns': '75310-3',
    'patient_demographics': '10154-3',
    'insurance': '48768-6',
    'encounter_notes': '11506-3',
}


def _hash_mrn(mrn):
    return safe_patient_id(mrn)[:12]


def open_patient_chart(mrn, patient_name):
    """
    Phase 1: Open a patient chart, apply Visit Template, and save.

    Uses OCR to find UI elements by their visible text labels.
    Coordinates from config.py are used only as a last-resort fallback.

    Parameters
    ----------
    mrn : str
        Patient MRN.
    patient_name : str
        Expected patient name for verification.

    Returns
    -------
    bool
        True on success, False on failure.
    """
    logger.info(f'Opening chart for MRN hash {_hash_mrn(mrn)}')

    if not is_ac_foreground():
        logger.error('AC not foreground — cannot open chart')
        return False

    try:
        import pyautogui

        # Find the Patient List ID search field via OCR
        # The search field is near the "Patient List" or "ID" label
        search_coords = find_element_near_text(
            'Patient List', direction='right', offset_px=80
        )
        if not search_coords:
            # Try alternate label
            search_coords = find_element_near_text(
                'ID', direction='right', offset_px=40
            )
        if not search_coords:
            # Last resort: config fallback
            fallback = getattr(config, 'PATIENT_LIST_ID_SEARCH_XY', (0, 0))
            if fallback != (0, 0):
                logger.warning('OCR failed for Patient List search — using fallback coordinates')
                search_coords = fallback
            else:
                logger.warning('Cannot find Patient List search field — no OCR match and no fallback')
                return False

        pyautogui.click(*search_coords)
        time.sleep(0.3)

        # Type the MRN
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.typewrite(str(mrn), interval=0.05)
        time.sleep(1.0)

        # Double-click first result to open chart
        # The first result appears below the search field
        result_coords = (search_coords[0], search_coords[1] + 30)
        pyautogui.click(*result_coords)
        time.sleep(0.3)
        pyautogui.click(*result_coords)
        time.sleep(2.0)

        # Wait for chart window to appear
        for _ in range(10):
            if is_chart_window_open():
                break
            time.sleep(1)
        else:
            logger.error(f'Chart window did not appear for MRN hash {_hash_mrn(mrn)}')
            return False

        logger.info('Chart window detected')

        # Click Visit Template radio button via OCR
        vt_fallback = getattr(config, 'VISIT_TEMPLATE_RADIO_XY', (0, 0))
        find_and_click('Visit Template', fallback_xy=vt_fallback)
        time.sleep(0.5)

        # Click Select Template dropdown via OCR
        st_fallback = getattr(config, 'SELECT_TEMPLATE_DROPDOWN_XY', (0, 0))
        if find_and_click('Select Template', fallback_xy=st_fallback):
            time.sleep(0.5)
            # Type "Procedure Visit" then select Companion
            pyautogui.typewrite('Procedure', interval=0.05)
            time.sleep(0.3)
            pyautogui.press('enter')
            time.sleep(0.5)

        # Clear any popup boxes
        pyautogui.press('enter')
        time.sleep(0.5)
        pyautogui.press('escape')
        time.sleep(0.3)

        # Ctrl+S to save and close chart
        pyautogui.hotkey('ctrl', 's')
        time.sleep(1.0)

        # Wait for chart window to disappear
        for _ in range(5):
            if not is_chart_window_open():
                break
            time.sleep(1)

        logger.info(f'Chart opened and saved for MRN hash {_hash_mrn(mrn)}')
        return True

    except Exception as e:
        logger.error(f'open_patient_chart failed: {e}')
        return False


def export_clinical_summary(mrn):
    """
    Phase 2: Export the Clinical Summary XML for a patient.

    Uses OCR to find menu items and buttons by their visible text.
    Coordinates from config.py are used only as a last-resort fallback.

    Parameters
    ----------
    mrn : str
        Patient MRN.

    Returns
    -------
    str | None
        File path of the exported XML, or None on failure.
    """
    logger.info(f'Exporting clinical summary for MRN hash {_hash_mrn(mrn)}')

    # Verify AC is on home screen — close any open charts first
    if is_chart_window_open():
        try:
            import pyautogui
            pyautogui.hotkey('ctrl', 's')
            time.sleep(2)
        except Exception:
            pass

        if is_chart_window_open():
            logger.error('Chart still open after Ctrl+S — cannot export')
            return None

    try:
        import pyautogui

        # Open Patient menu via Alt+P (keyboard shortcut — no coordinates needed)
        pyautogui.hotkey('alt', 'p')
        time.sleep(0.5)

        # Find "Export Clinical Summary" menu item via OCR
        export_menu_fallback = getattr(config, 'EXPORT_CLIN_SUM_MENU_XY', (0, 0))
        if not find_and_click('Export Clinical Summary', fallback_xy=export_menu_fallback):
            # Try shorter text match
            if not find_and_click('Clinical Summary', fallback_xy=export_menu_fallback):
                logger.warning('Cannot find Export Clinical Summary menu item')
                pyautogui.press('escape')
                return None
        time.sleep(1.0)

        # Select "Full Patient Record" from the encounter dropdown.
        # The dialog defaults to the most recent encounter date, but we
        # always want the complete patient record (all history, meds, etc.).
        if not find_and_click('Full Patient Record'):
            # Fallback: click the dropdown to expand it, then select
            if find_and_click('Select Encounter Date'):
                time.sleep(0.3)
                if not find_and_click('Full Patient Record'):
                    logger.warning('Could not select Full Patient Record — using default encounter')
            else:
                logger.warning('Could not find encounter dropdown — using default')
        time.sleep(0.5)

        # Find and click the Export button in the dialog via OCR
        export_btn_fallback = getattr(config, 'EXPORT_BUTTON_XY', (0, 0))
        find_and_click('Export', fallback_xy=export_btn_fallback)
        time.sleep(1.0)

        # Dismiss success dialog
        pyautogui.press('enter')
        time.sleep(0.5)

        # Watch for new XML file
        export_folder = getattr(config, 'CLINICAL_SUMMARY_EXPORT_FOLDER', 'data/clinical_summaries/')
        if not os.path.isabs(export_folder):
            export_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), export_folder)
        os.makedirs(export_folder, exist_ok=True)

        pattern = f'ClinicalSummary_PatientId_{mrn}_'
        for _ in range(15):
            for fname in os.listdir(export_folder):
                if fname.startswith(pattern) and fname.endswith('.xml'):
                    fpath = os.path.join(export_folder, fname)
                    # Check if file was just created (within last 30 seconds)
                    mtime = os.path.getmtime(fpath)
                    if time.time() - mtime < 30:
                        logger.info(f'Export found: {fname}')
                        # Rename file to use hashed MRN instead of raw MRN
                        hashed_name = fname.replace(
                            f'PatientId_{mrn}_',
                            f'PatientId_{safe_patient_id(mrn)[:12]}_',
                        )
                        new_fpath = os.path.join(export_folder, hashed_name)
                        try:
                            os.rename(fpath, new_fpath)
                            fpath = new_fpath
                        except OSError:
                            pass  # Keep original if rename fails
                        return fpath
            time.sleep(1)

        logger.error(f'Timeout waiting for XML export for MRN hash {_hash_mrn(mrn)}')
        return None

    except Exception as e:
        logger.error(f'export_clinical_summary failed: {e}')
        return None


def parse_clinical_summary(xml_path):
    """
    Parse an HL7 CDA Clinical Summary XML file.

    Parameters
    ----------
    xml_path : str
        Full path to the CDA XML file.

    Returns
    -------
    dict
        Parsed sections: medications, allergies, diagnoses, vitals,
        lab_results, immunizations, social_history, etc.
    """
    logger.info(f'Parsing clinical summary: {os.path.basename(xml_path)}')

    result = {key: [] for key in SECTION_LOINC}
    result['patient_name'] = ''
    result['patient_mrn'] = ''
    result['patient_dob'] = ''

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.error(f'XML parse error: {e}')
        return result

    # Extract patient demographics from the header
    try:
        patient = root.find('.//cda:recordTarget/cda:patientRole', NS)
        if patient is not None:
            # MRN from patient ID
            for id_elem in patient.findall('cda:id', NS):
                ext = id_elem.get('extension', '')
                if ext:
                    result['patient_mrn'] = ext
                    break

            pt = patient.find('cda:patient', NS)
            if pt is not None:
                given = pt.find('.//cda:given', NS)
                family = pt.find('.//cda:family', NS)
                if given is not None and family is not None:
                    result['patient_name'] = f'{given.text} {family.text}'

                birth = pt.find('cda:birthTime', NS)
                if birth is not None:
                    result['patient_dob'] = birth.get('value', '')

                gender = pt.find('cda:administrativeGenderCode', NS)
                if gender is not None:
                    code = gender.get('code', '').upper()
                    if code == 'M':
                        result['patient_sex'] = 'M'
                    elif code == 'F':
                        result['patient_sex'] = 'F'
                    else:
                        result['patient_sex'] = gender.get('displayName', code)
    except Exception as e:
        logger.debug(f'Demographics parse error: {e}')

    # Extract each clinical section by LOINC code
    for section_name, loinc_code in SECTION_LOINC.items():
        try:
            entries = _extract_section(root, loinc_code)
            result[section_name] = entries
        except Exception as e:
            logger.debug(f'Section {section_name} parse error: {e}')

    # ---- Classify insurer from extracted insurance section ----
    try:
        from app.services.insurer_classifier import classify_insurer
        insurance_entries = result.get('insurance', [])
        raw_payer_text = ' '.join(
            ' '.join(v for v in row.values() if isinstance(v, str))
            for row in insurance_entries
        )
        result['insurer_type'] = classify_insurer(raw_payer_text)
        if result['insurer_type'] != 'unknown':
            logger.info(f'Insurer auto-detected: {result["insurer_type"]}')
    except Exception as e:
        logger.debug(f'Insurer classification error: {e}')
        result['insurer_type'] = 'unknown'

    sections_found = [k for k, v in result.items() if v and k not in ('patient_name', 'patient_mrn', 'patient_dob', 'insurer_type')]
    logger.info(f'Parsed {len(sections_found)} sections: {", ".join(sections_found)}')

    return result


def _extract_section(root, loinc_code):
    """
    Extract entries from a CDA section identified by LOINC code.

    CDA Clinical Summaries from Amazing Charts store the actual clinical
    data in narrative HTML tables inside the <text> element of each
    section — NOT in the <entry> elements, which contain performer /
    organization metadata.

    Returns a list of dicts, one per table row, mapping column headers
    to cell values.  Falls back to plain text if no table is found.
    """
    entries = []

    for section in root.findall('.//cda:section', NS):
        code_elem = section.find('cda:code', NS)
        if code_elem is None:
            continue
        if code_elem.get('code') != loinc_code:
            continue

        # Check for nullFlavor (section present but empty)
        if section.get('nullFlavor') == 'NI':
            return []

        text_elem = section.find('cda:text', NS)
        if text_elem is None:
            return []

        # Collect headers from <th> elements
        headers = []
        for th in text_elem.iter(f'{{{NS["cda"]}}}th'):
            headers.append((th.text or '').strip())

        # Parse each <tr> that contains <td> cells
        for tr in text_elem.iter(f'{{{NS["cda"]}}}tr'):
            cells = []
            for td in tr.findall(f'{{{NS["cda"]}}}td'):
                # Gather all text within the <td> (handles nested elements)
                cell_text = ''.join(td.itertext()).strip()
                cells.append(cell_text)

            if not cells:
                continue

            if headers and len(cells) == len(headers):
                row = dict(zip(headers, cells))
            else:
                # No headers or column mismatch — store positionally
                row = {f'col_{i}': v for i, v in enumerate(cells)}

            entries.append(row)

        # Fallback: plain text content (e.g. "No known immunization history")
        if not entries:
            plain = ''.join(text_elem.itertext()).strip()
            if plain:
                entries.append({'text': plain})

        break  # only process the first matching section

    return entries


def _parse_code_from_text(text):
    """
    Extract a coding system code from bracketed text.
    E.g. 'Hypertension [ICD10: I10]' → ('Hypertension', 'ICD10', 'I10')
          'albuterol [RxNorm: 801092]' → ('albuterol', 'RxNorm', '801092')
    Returns (display_name, code_system, code_value).
    """
    m = re.search(r'\[([^:]+):\s*([^\]]+)\]', text)
    if m:
        display = text[:m.start()].strip()
        return display, m.group(1).strip(), m.group(2).strip()
    return text.strip(), '', ''


def _parse_date(date_str):
    """Attempt to parse a date string into a datetime, returning None on failure."""
    if not date_str or date_str == '--':
        return None
    for fmt in ('%m/%d/%Y %H:%M:%S', '%m/%d/%Y %I:%M:%S %p', '%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def detect_new_medications(user_id, mrn, parsed):
    """
    Compare medications in the new XML against the patient's existing
    medications in the database.  Returns list of new medication dicts.

    Must be called BEFORE store_parsed_summary() deletes old records.

    Returns
    -------
    list[dict]
        Each dict: {'drug_name': str, 'rxcui': str, 'start_date': str}
    """
    from models.patient import PatientMedication

    # Snapshot current DB medications for this patient
    existing = PatientMedication.query.filter_by(
        user_id=user_id, mrn=mrn, status='active'
    ).all()
    existing_names = {m.drug_name.strip().lower() for m in existing if m.drug_name}

    # If no prior medications exist, don't flag everything as "new"
    if not existing_names:
        return []

    new_meds = []
    for row in parsed.get('medications', []):
        if 'text' in row:
            continue
        status = (row.get('Status') or 'active').strip().lower()
        if status != 'active':
            continue
        drug_text = row.get('Medication', '')
        display_name, code_sys, code_val = _parse_code_from_text(drug_text)
        name = (display_name or drug_text).strip()
        if not name:
            continue
        # Check if this medication is genuinely new
        if name.lower() not in existing_names:
            rxnorm_cui = code_val if code_sys.lower() in ('rxnorm', 'rx') else ''
            new_meds.append({
                'drug_name': name,
                'rxcui': rxnorm_cui,
                'start_date': row.get('Start Date', ''),
            })

    return new_meds


def _trigger_new_med_education(user_id, mrn, new_meds):
    """
    Trigger 2: Auto-draft education messages for newly detected medications.
    Runs in a try/except — never blocks the main parse pipeline.
    """
    if not new_meds:
        return
    try:
        from app.services.education_service import auto_draft_education_message  # B1.18
        auto_draft_education_message(user_id, mrn, new_meds)
    except Exception as e:
        logger.warning(f'Trigger 2 (new-med education) failed for MRN hash {_hash_mrn(mrn)}: {e}')


def store_parsed_summary(user_id, mrn, parsed):
    """
    Write parsed clinical summary data to the database.

    Parameters
    ----------
    user_id : int
    mrn : str
    parsed : dict
        Output from parse_clinical_summary().  Each section value is a
        list of dicts whose keys are the CDA table column headers.
    """
    from models import db
    from models.patient import (
        PatientVitals, PatientRecord, PatientMedication,
        PatientDiagnosis, PatientAllergy, PatientImmunization,
        PatientLabResult, PatientSocialHistory, PatientEncounterNote,
    )
    from models.audit import AuditLog
    from billing_engine.shared import hash_mrn

    now = datetime.now(timezone.utc)

    # ---- Trigger 2: detect new medications BEFORE clearing old data ----
    new_meds = detect_new_medications(user_id, mrn, parsed)

    # ---- Upsert PatientRecord ----
    record = (
        PatientRecord.query
        .filter_by(user_id=user_id, mrn=mrn)
        .first()
    )
    if not record:
        record = PatientRecord(user_id=user_id, mrn=mrn)
        db.session.add(record)

    record.last_xml_parsed = now
    record.patient_name = parsed.get('patient_name', '')
    # Normalize DOB to YYYY-MM-DD if stored as YYYYMMDD
    raw_dob = parsed.get('patient_dob', '')
    if len(raw_dob) == 8 and raw_dob.isdigit():
        raw_dob = f'{raw_dob[:4]}-{raw_dob[4:6]}-{raw_dob[6:]}'
    record.patient_dob = raw_dob
    record.patient_sex = parsed.get('patient_sex', '')

    # Insurer auto-detection from CDA XML insurance section
    detected_insurer = parsed.get('insurer_type', 'unknown')
    if detected_insurer and detected_insurer != 'unknown':
        record.insurer_type = detected_insurer

    # ---- Clear old data for this patient before re-importing ----
    for model in (PatientMedication, PatientDiagnosis, PatientAllergy,
                  PatientImmunization, PatientVitals, PatientLabResult,
                  PatientEncounterNote):
        model.query.filter_by(user_id=user_id, mrn=mrn).delete()

    # ---- Medications ----
    # Columns: Medication, Generic Name, Instructions, Dosage,
    #          Start Date, Status, Date Inactivated
    for row in parsed.get('medications', []):
        if 'text' in row:
            continue  # plain-text fallback — skip
        drug_text = row.get('Medication', '')
        display_name, code_sys, code_val = _parse_code_from_text(drug_text)
        rxnorm_cui = code_val if code_sys.lower() in ('rxnorm', 'rx') else ''
        status = (row.get('Status') or 'active').strip().lower()
        med = PatientMedication(
            user_id=user_id,
            mrn=mrn,
            drug_name=display_name or drug_text,
            rxnorm_cui=rxnorm_cui,
            dosage=row.get('Dosage', '').strip(),
            frequency=row.get('Instructions', '').strip(),
            status='active' if status == 'active' else 'inactive',
            start_date=_parse_date(row.get('Start Date')),
        )
        db.session.add(med)

    # ---- Diagnoses ----
    # Columns: Problem, Problem Status, Date Started, Date Resolved, Date Inactivated
    for row in parsed.get('diagnoses', []):
        if 'text' in row:
            continue
        problem_text = row.get('Problem', '')
        display_name, code_sys, code_val = _parse_code_from_text(problem_text)
        icd10 = code_val if code_sys.upper() in ('ICD10', 'ICD-10') else ''
        prob_status = (row.get('Problem Status') or 'active').strip().lower()
        diag = PatientDiagnosis(
            user_id=user_id,
            mrn=mrn,
            diagnosis_name=display_name or problem_text,
            icd10_code=icd10,
            status='active' if prob_status == 'active' else 'resolved',
            onset_date=_parse_date(row.get('Date Started')),
        )
        db.session.add(diag)

    # ---- Allergies ----
    # Columns: Substance, Reaction, Severity, Status
    for row in parsed.get('allergies', []):
        if 'text' in row:
            continue
        substance = row.get('Substance', '')
        display_name, _sys, _code = _parse_code_from_text(substance)
        allergy = PatientAllergy(
            user_id=user_id,
            mrn=mrn,
            allergen=display_name or substance,
            reaction=row.get('Reaction', '').replace('--', '').strip(),
            severity=row.get('Severity', '').replace('--', '').strip(),
        )
        db.session.add(allergy)

    # ---- Immunizations ----
    # Columns: Vaccine, Date, Status
    for row in parsed.get('immunizations', []):
        if 'text' in row:
            continue
        imm = PatientImmunization(
            user_id=user_id,
            mrn=mrn,
            vaccine_name=row.get('Vaccine', '').strip(),
            date_given=_parse_date(row.get('Date')),
        )
        db.session.add(imm)

    # ---- Vitals ----
    # Columns: Encounter, Height (in), Weight (lb), BMI (kg/m2),
    #          BP Sys (mmHg), BP Dias (mmHg), Heart Rate (/min),
    #          O2 % BldC Oximetry, …
    VITAL_COLS = {
        'Height (in)': ('Height', 'in'),
        'Weight (lb)': ('Weight', 'lb'),
        'BMI (kg/m2)': ('BMI', 'kg/m2'),
        'BP Sys (mmHg)': ('BP Systolic', 'mmHg'),
        'BP Dias (mmHg)': ('BP Diastolic', 'mmHg'),
        'Heart Rate (/min)': ('Heart Rate', '/min'),
        'O2 % BldC Oximetry': ('O2 Sat', '%'),
        'Body Temperature': ('Temperature', ''),
        'Respiratory Rate (/min)': ('Respiratory Rate', '/min'),
    }
    for row in parsed.get('vitals', []):
        if 'text' in row:
            continue
        encounter_dt = _parse_date(row.get('Encounter'))
        for col_header, (vname, vunit) in VITAL_COLS.items():
            value = (row.get(col_header) or '').strip()
            if not value or value == '--':
                continue
            vital = PatientVitals(
                user_id=user_id,
                mrn=mrn,
                vital_name=vname,
                vital_value=value,
                vital_unit=vunit,
                measured_at=encounter_dt,
            )
            db.session.add(vital)

    # ---- Lab Results (Phase 15.4 — previously parsed but discarded) ----
    mrn_hash = hash_mrn(mrn)
    for row in parsed.get('lab_results', []):
        if 'text' in row:
            continue
        test_text = row.get('Test Name', row.get('Test', ''))
        display_name, code_sys, code_val = _parse_code_from_text(test_text)
        loinc = code_val if code_sys.upper() == 'LOINC' else ''
        result_val = (row.get('Result') or row.get('Value') or '').strip()
        result_units = (row.get('Units') or '').strip()
        result_flag_raw = (row.get('Flag') or row.get('Interpretation') or 'normal').strip().lower()
        if result_flag_raw in ('h', 'high', 'abnormal', 'a'):
            result_flag = 'abnormal'
        elif result_flag_raw in ('hh', 'critical', 'c', 'll'):
            result_flag = 'critical'
        else:
            result_flag = 'normal'
        lab = PatientLabResult(
            user_id=user_id,
            mrn=mrn,
            patient_mrn_hash=mrn_hash,
            test_name=display_name or test_text,
            loinc_code=loinc,
            result_value=result_val,
            result_units=result_units,
            result_date=_parse_date(row.get('Date') or row.get('Collection Date')),
            result_flag=result_flag,
            source='xml_import',
        )
        db.session.add(lab)

    # ---- Social History (Phase 15.4 — previously parsed but discarded) ----
    social_rows = parsed.get('social_history', [])
    if social_rows:
        # Upsert: one social history record per patient
        social = PatientSocialHistory.query.filter_by(
            user_id=user_id, mrn=mrn
        ).first()
        if not social:
            social = PatientSocialHistory(
                user_id=user_id, mrn=mrn, patient_mrn_hash=mrn_hash
            )
            db.session.add(social)
        for row in social_rows:
            if 'text' in row:
                text_lower = row['text'].lower()
                if 'tobacco' in text_lower or 'smoking' in text_lower or 'smoker' in text_lower:
                    if any(w in text_lower for w in ('current', 'every day', 'daily', 'yes')):
                        social.tobacco_status = 'current'
                    elif any(w in text_lower for w in ('former', 'quit', 'ex-')):
                        social.tobacco_status = 'former'
                    elif any(w in text_lower for w in ('never', 'no', 'non-')):
                        social.tobacco_status = 'never'
                if 'alcohol' in text_lower or 'drink' in text_lower:
                    if any(w in text_lower for w in ('current', 'yes', 'social', 'moderate', 'heavy')):
                        social.alcohol_status = 'current'
                    elif any(w in text_lower for w in ('former', 'quit', 'stopped')):
                        social.alcohol_status = 'former'
                    elif any(w in text_lower for w in ('never', 'no', 'none', 'denied')):
                        social.alcohol_status = 'never'
                    social.alcohol_frequency = row['text'].strip()[:100]
                continue
            # Structured social history rows
            category = (row.get('Social History Element') or row.get('Type') or '').lower()
            value = (row.get('Description') or row.get('Value') or '').strip()
            if 'tobacco' in category or 'smoking' in category:
                val_lower = value.lower()
                if any(w in val_lower for w in ('current', 'every day', 'daily', 'yes')):
                    social.tobacco_status = 'current'
                elif any(w in val_lower for w in ('former', 'quit', 'ex-')):
                    social.tobacco_status = 'former'
                elif any(w in val_lower for w in ('never', 'no', 'non-')):
                    social.tobacco_status = 'never'
            elif 'alcohol' in category or 'drink' in category:
                val_lower = value.lower()
                if any(w in val_lower for w in ('current', 'yes', 'social', 'moderate', 'heavy')):
                    social.alcohol_status = 'current'
                elif any(w in val_lower for w in ('former', 'quit', 'stopped')):
                    social.alcohol_status = 'former'
                elif any(w in val_lower for w in ('never', 'no', 'none', 'denied')):
                    social.alcohol_status = 'never'
                social.alcohol_frequency = value[:100]
            elif 'substance' in category or 'drug' in category:
                social.substance_use_status = value[:100]
            elif 'sexual' in category:
                social.sexual_activity = value[:100]

    # ---- Encounter Notes (Prior Notes) ----
    # Columns: Date, Provider, Note Type, Note Text, Location
    for row in parsed.get('encounter_notes', []):
        if 'text' in row:
            continue
        note = PatientEncounterNote(
            user_id=user_id,
            mrn=mrn,
            encounter_date=_parse_date(row.get('Date')),
            provider_name=(row.get('Provider') or '').strip(),
            note_type=(row.get('Note Type') or 'Progress Note').strip(),
            note_text=(row.get('Note Text') or '').strip(),
            location=(row.get('Location') or '').strip(),
        )
        db.session.add(note)

    # ---- Populate last_awv_date from BillingOpportunity history (Phase 15.5) ----
    try:
        from models.billing import BillingOpportunity
        awv_opp = (
            BillingOpportunity.query
            .filter(
                BillingOpportunity.patient_mrn_hash == hash_mrn(mrn),
                BillingOpportunity.opportunity_type.in_(['AWV', 'G0438', 'G0439', 'G0402']),
                BillingOpportunity.status == 'captured',
            )
            .order_by(BillingOpportunity.visit_date.desc())
            .first()
        )
        if awv_opp and awv_opp.visit_date:
            record.last_awv_date = awv_opp.visit_date
    except Exception:
        pass  # BillingOpportunity may not have AWV data yet
    sections_found = [k for k, v in parsed.items()
                      if v and k not in ('patient_name', 'patient_mrn', 'patient_dob')]
    meds_count = len(parsed.get('medications', []))
    audit = AuditLog(
        user_id=user_id,
        action=f'clinical_summary_parsed mrn_hash={_hash_mrn(mrn)} sections={",".join(sections_found)} meds={meds_count}',
        module='clinical_summary',
    )
    db.session.add(audit)

    db.session.commit()
    logger.info(f'Stored parsed summary for MRN hash {_hash_mrn(mrn)}')

    # ---- Phase 23 (C3): Auto-populate monitoring rules from new data ----
    try:
        from app.services.monitoring_rule_engine import MonitoringRuleEngine
        engine = MonitoringRuleEngine(db)

        # Refresh rules for medications with RxNorm CUIs
        for row in parsed.get('medications', []):
            if 'text' in row:
                continue
            drug_text = row.get('Medication', '')
            display_name, code_sys, code_val = _parse_code_from_text(drug_text)
            rxnorm_cui = code_val if code_sys.lower() in ('rxnorm', 'rx') else ''
            if rxnorm_cui:
                engine.refresh_rules_for_medication(display_name or drug_text, rxnorm_cui)

        # Refresh condition-driven rules for new diagnoses
        for row in parsed.get('diagnoses', []):
            if 'text' in row:
                continue
            problem_text = row.get('Problem', '')
            _, code_sys, code_val = _parse_code_from_text(problem_text)
            icd10 = code_val if code_sys.upper() in ('ICD10', 'ICD-10') else ''
            if icd10:
                engine.refresh_condition_rules(icd10)
    except Exception as exc:
        logger.debug("Phase 23 monitoring refresh skipped: %s", exc)

    # ---- Trigger 2: auto-draft education for new medications ----
    if new_meds:
        logger.info(f'Trigger 2: {len(new_meds)} new med(s) detected for MRN hash {_hash_mrn(mrn)}')
        _trigger_new_med_education(user_id, mrn, new_meds)

    # ---- Trigger 3: auto-catalog medications for monitoring coverage ----
    _trigger_auto_catalog(parsed)


def _trigger_auto_catalog(parsed):
    """Auto-catalog each parsed medication into MedicationCatalogEntry."""
    try:
        from app.services.med_catalog_service import MedCatalogService
        svc = MedCatalogService()
        for row in parsed.get('medications', []):
            if 'text' in row:
                continue
            status = (row.get('Status') or 'active').strip().lower()
            if status != 'active':
                continue
            drug_text = row.get('Medication', '')
            display_name, code_sys, code_val = _parse_code_from_text(drug_text)
            name = (display_name or drug_text).strip()
            if not name:
                continue
            rxcui = code_val if code_sys.lower() in ('rxnorm', 'rx') else ''
            svc.auto_catalog_new_medication(name, rxcui or None)
    except Exception as e:
        logger.debug(f'Auto-catalog trigger skipped: {e}')


def detect_pregnancy(user_id, mrn):
    """Phase 15.6: Scan PatientDiagnosis for O-codes (O00-O9A) indicating pregnancy."""
    from models.patient import PatientDiagnosis
    o_codes = PatientDiagnosis.query.filter_by(
        user_id=user_id, mrn=mrn, status='active'
    ).all()
    for dx in o_codes:
        code = (dx.icd10_code or '').upper().strip()
        if code and code[0] == 'O' and len(code) >= 3:
            return True
    return False


def populate_last_awv_date(record):
    """Phase 15.5: Populate last_awv_date from BillingOpportunity history."""
    try:
        from models.billing import BillingOpportunity
        from billing_engine.shared import hash_mrn
        awv_opp = (
            BillingOpportunity.query
            .filter(
                BillingOpportunity.patient_mrn_hash == hash_mrn(record.mrn),
                BillingOpportunity.opportunity_type.in_(['AWV', 'G0438', 'G0439', 'G0402']),
                BillingOpportunity.status == 'captured',
            )
            .order_by(BillingOpportunity.visit_date.desc())
            .first()
        )
        if awv_opp and awv_opp.visit_date:
            record.last_awv_date = awv_opp.visit_date
    except Exception:
        pass


def schedule_deletion(xml_path, days=None):
    """
    Register an XML file for deletion after N days.
    Uses APScheduler for deferred cleanup.
    """
    if days is None:
        days = getattr(config, 'CLINICAL_SUMMARY_RETENTION_DAYS', 183)

    from models import db
    from models.audit import AuditLog

    run_date = datetime.now(timezone.utc) + timedelta(days=days)

    # Log the scheduled deletion
    audit = AuditLog(
        user_id=0,
        action=f'schedule_xml_deletion file={os.path.basename(xml_path)} delete_after={run_date.isoformat()}',
        module='clinical_summary',
    )
    db.session.add(audit)
    db.session.commit()

    logger.info(f'Scheduled deletion of {os.path.basename(xml_path)} after {days} days')


def _delete_file(path):
    """Safely delete a file."""
    try:
        if os.path.exists(path):
            os.remove(path)
            logger.info(f'Deleted XML file: {os.path.basename(path)}')
    except Exception as e:
        logger.error(f'Failed to delete {path}: {e}')


def run_scheduled_deletions():
    """
    Delete XML files older than CLINICAL_SUMMARY_RETENTION_DAYS.
    Called daily by the scheduler at 2 AM.
    """
    retention_days = getattr(config, 'CLINICAL_SUMMARY_RETENTION_DAYS', 183)
    folder = getattr(config, 'CLINICAL_SUMMARY_EXPORT_FOLDER', 'data/clinical_summaries/')
    if not os.path.isabs(folder):
        folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), folder)
    if not os.path.isdir(folder):
        return

    cutoff = time.time() - (retention_days * 86400)
    deleted = 0
    for fname in os.listdir(folder):
        if not fname.endswith('.xml'):
            continue
        fpath = os.path.join(folder, fname)
        try:
            if os.path.getmtime(fpath) < cutoff:
                os.remove(fpath)
                deleted += 1
        except Exception as e:
            logger.error(f'Failed to delete expired XML {fname}: {e}')

    if deleted:
        logger.info(f'XML cleanup: deleted {deleted} expired file(s)')


# ---- Watchdog file observer handler ----

try:
    from watchdog.events import FileSystemEventHandler

    class ClinicalSummaryHandler(FileSystemEventHandler):
        """
        Watches the clinical summary export folder for new XML files.
        Triggers parse + store when a new file appears.
        """

        def __init__(self, user_id):
            super().__init__()
            self.user_id = user_id

        def on_created(self, event):
            if event.is_directory:
                return
            if not event.src_path.endswith('.xml'):
                return

            logger.info(f'New XML detected: {os.path.basename(event.src_path)}')
            time.sleep(1)  # Wait for file to finish writing

            try:
                parsed = parse_clinical_summary(event.src_path)
                mrn = parsed.get('patient_mrn', '')
                if mrn:
                    store_parsed_summary(self.user_id, mrn, parsed)
                    schedule_deletion(event.src_path)
                else:
                    logger.warning(f'No MRN found in {os.path.basename(event.src_path)}')
            except Exception as e:
                logger.error(f'Failed to process XML: {e}')

except ImportError:
    # watchdog not installed — provide a fallback polling function
    ClinicalSummaryHandler = None
    logger.info('watchdog not installed — will use polling fallback')


# ---- Watcher / Poller Management ----

_watcher_observer = None  # module-level reference for stopping


def get_export_folder(user=None):
    """
    Return the resolved XML export folder path.

    Priority:
      1. User preference ``xml_export_folder`` (if user provided)
      2. ``config.CLINICAL_SUMMARY_EXPORT_FOLDER``
      3. ``data/clinical_summaries/``
    """
    folder = None
    if user is not None:
        folder = user.get_pref('xml_export_folder', None) if hasattr(user, 'get_pref') else None
    if not folder:
        folder = getattr(config, 'CLINICAL_SUMMARY_EXPORT_FOLDER', 'data/clinical_summaries/')
    if not os.path.isabs(folder):
        folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), folder)
    return folder


def start_xml_watcher(user_id, user=None):
    """
    Start a watchdog Observer on the export folder.

    Falls back to logging a warning if watchdog is unavailable or the
    folder doesn't exist.  The caller should schedule ``poll_export_folder``
    as a periodic fallback regardless.
    """
    global _watcher_observer  # noqa: PLW0603

    # Stop any previously running observer to prevent thread leaks
    if _watcher_observer is not None:
        try:
            _watcher_observer.stop()
            _watcher_observer.join(timeout=5)
        except Exception:
            pass
        _watcher_observer = None

    folder = get_export_folder(user)
    os.makedirs(folder, exist_ok=True)

    if ClinicalSummaryHandler is None:
        logger.info('watchdog not available — using polling only')
        return False

    try:
        from watchdog.observers import Observer
        handler = ClinicalSummaryHandler(user_id)
        observer = Observer()
        observer.schedule(handler, folder, recursive=False)
        observer.daemon = True
        observer.start()
        _watcher_observer = observer
        logger.info(f'Watchdog started on {folder}')
        return True
    except Exception as e:
        logger.error(f'Failed to start watchdog: {e}')
        return False


def stop_xml_watcher():
    """Stop the running watchdog Observer, if any."""
    global _watcher_observer  # noqa: PLW0603
    if _watcher_observer is not None:
        _watcher_observer.stop()
        _watcher_observer.join(timeout=5)
        _watcher_observer = None
        logger.info('Watchdog stopped')


def poll_export_folder(user_id, processed_files=None, user=None):
    """
    Fallback polling function when watchdog is not available.
    Call this periodically from the agent scheduler.
    """
    if processed_files is None:
        processed_files = set()

    export_folder = get_export_folder(user)

    if not os.path.isdir(export_folder):
        return processed_files

    for fname in os.listdir(export_folder):
        if not fname.endswith('.xml'):
            continue
        if fname in processed_files:
            continue

        fpath = os.path.join(export_folder, fname)
        try:
            parsed = parse_clinical_summary(fpath)
            mrn = parsed.get('patient_mrn', '')
            if mrn:
                store_parsed_summary(user_id, mrn, parsed)
                schedule_deletion(fpath)
            processed_files.add(fname)
        except Exception as e:
            logger.error(f'Polling: failed to process {fname}: {e}')

    return processed_files

"""
CareCompanion — Clinical Note Content Classifier
File: agent/note_classifier.py

Step 3 of the Note Reformatter (F31). Takes parsed note sections from
note_parser.py and classifies individual items within each section:
- Medications → individual med entries, flagged if not in standard reference
- Diagnoses → individual dx entries, flagged if not ICD-10 matchable
- Allergies → allergen + reaction pairs
- ROS → system-by-system positive/negative findings
- Physical Exam → body system findings, abnormals flagged
- Narrative text → HPI, Social Hx, Family Hx kept as blocks

Each item gets a confidence score. Items below the confidence threshold
are flagged for provider review.

Dependencies:
- agent/note_parser.py (section parsing)
- app/services/clinical_spell_check.py (terminology matching)
- app/services/api/icd10.py (diagnosis validation, optional)
- app/services/api/rxnorm.py (medication validation, optional)
"""

import re
import logging

logger = logging.getLogger(__name__)

# Confidence thresholds
HIGH_CONFIDENCE = 0.85
MEDIUM_CONFIDENCE = 0.60


def classify_content(parsed_sections, use_api=False):
    """
    Classify content within each parsed note section.

    Parameters
    ----------
    parsed_sections : dict
        Output from note_parser.parse_note_sections().
    use_api : bool
        If True, validate meds/diagnoses against RxNorm/ICD-10 APIs.

    Returns
    -------
    dict mapping section_name → {
        'classified_items': [{'text': str, 'type': str, 'confidence': float, ...}],
        'flagged_items': [{'text': str, 'reason': str, 'confidence': float}],
    }
    """
    result = {}

    for section_name, content in parsed_sections.items():
        if section_name in ('unclassified_text', 'needs_review', '_metadata'):
            continue
        if not content or not isinstance(content, str):
            continue

        if section_name == 'Medications':
            result[section_name] = _classify_medications(content, use_api)
        elif section_name in ('Assessment', 'Assessment and Plan', 'Past Medical History'):
            result[section_name] = _classify_diagnoses(content, use_api)
        elif section_name == 'Allergies':
            result[section_name] = _classify_allergies(content)
        elif section_name == 'Review of Systems':
            result[section_name] = _classify_ros(content)
        elif section_name == 'Physical Examination':
            result[section_name] = _classify_exam(content)
        else:
            # Narrative sections: HPI, SH, FH, Plan, Follow-up, etc.
            result[section_name] = _classify_narrative(section_name, content)

    return result


def _classify_medications(text, use_api=False):
    """Classify medication list items."""
    from agent.note_parser import parse_medication_list
    meds = parse_medication_list(text)

    classified = []
    flagged = []

    for med in meds:
        name = med.get('name', '').strip()
        if not name:
            continue

        confidence = 0.7  # Default for parsed meds

        # Check against spell check dictionary for known drugs
        try:
            from app.services.clinical_spell_check import MEDICAL_ABBREVIATIONS, COMMON_MISSPELLINGS
            name_lower = name.lower().split()[0] if name else ''
            # Known drug abbreviation
            if name_lower in MEDICAL_ABBREVIATIONS:
                confidence = 0.95
            # Known drug in misspelling dict values
            all_drug_names = set(COMMON_MISSPELLINGS.values())
            if name_lower in [d.lower() for d in all_drug_names]:
                confidence = 0.90
        except ImportError:
            pass

        # API validation if enabled
        if use_api and confidence < HIGH_CONFIDENCE:
            try:
                from app.services.api.rxnorm import RxNormService
                from models import db
                svc = RxNormService(db)
                result = svc.get_rxcui(name)
                if result and result.get('rxcui'):
                    confidence = 0.95
                else:
                    confidence = max(confidence, 0.50)
            except Exception:
                pass

        item = {
            'text': med.get('raw', name),
            'type': 'medication',
            'name': name,
            'dose': med.get('dose', ''),
            'frequency': med.get('frequency', ''),
            'confidence': confidence,
        }

        if confidence >= MEDIUM_CONFIDENCE:
            classified.append(item)
        else:
            flagged.append({
                'text': med.get('raw', name),
                'reason': 'Medication not recognized in standard reference',
                'confidence': confidence,
                'section': 'Medications',
            })

    return {'classified_items': classified, 'flagged_items': flagged}


def _classify_diagnoses(text, use_api=False):
    """Classify diagnosis list items."""
    from agent.note_parser import parse_diagnosis_list
    diagnoses = parse_diagnosis_list(text)

    classified = []
    flagged = []

    for dx in diagnoses:
        name = dx.get('name', '').strip()
        icd10 = dx.get('icd10', '')
        if not name:
            continue

        confidence = 0.6  # Default

        # If ICD-10 code present, higher confidence
        if icd10 and re.match(r'^[A-Z]\d{2}', icd10):
            confidence = 0.90

        # Check against common diagnoses
        COMMON_DX_KEYWORDS = [
            'hypertension', 'diabetes', 'hyperlipidemia', 'hypothyroidism',
            'depression', 'anxiety', 'copd', 'asthma', 'heart failure',
            'atrial fibrillation', 'coronary', 'arthritis', 'osteoporosis',
            'obesity', 'gerd', 'anemia', 'ckd', 'chronic kidney',
            'neuropathy', 'pain', 'insomnia', 'migraine', 'uti',
        ]
        name_lower = name.lower()
        if any(kw in name_lower for kw in COMMON_DX_KEYWORDS):
            confidence = max(confidence, 0.85)

        # API validation if enabled and no ICD-10 code
        if use_api and not icd10 and confidence < HIGH_CONFIDENCE:
            try:
                from app.services.api.icd10 import ICD10Service
                from models import db
                svc = ICD10Service(db)
                results = svc.search(name, max_results=1)
                if results:
                    icd10 = results[0].get('code', '')
                    confidence = 0.85
            except Exception:
                pass

        item = {
            'text': dx.get('raw', name),
            'type': 'diagnosis',
            'name': name,
            'icd10': icd10,
            'confidence': confidence,
        }

        if confidence >= MEDIUM_CONFIDENCE:
            classified.append(item)
        else:
            flagged.append({
                'text': dx.get('raw', name),
                'reason': 'Unusual diagnosis — could not match to standard terminology',
                'confidence': confidence,
                'section': 'Diagnoses',
            })

    return {'classified_items': classified, 'flagged_items': flagged}


def _classify_allergies(text):
    """Classify allergy list items."""
    from agent.note_parser import parse_allergy_list
    allergies = parse_allergy_list(text)

    classified = []
    flagged = []

    COMMON_ALLERGENS = [
        'penicillin', 'amoxicillin', 'sulfa', 'sulfamethoxazole',
        'codeine', 'morphine', 'aspirin', 'ibuprofen', 'nsaid',
        'latex', 'contrast', 'iodine', 'egg', 'shellfish', 'peanut',
        'ace inhibitor', 'lisinopril', 'cephalosporin', 'erythromycin',
        'azithromycin', 'fluoroquinolone', 'ciprofloxacin', 'tetracycline',
        'nkda', 'no known',
    ]

    for allergy in allergies:
        allergen = allergy.get('allergen', '').strip()
        if not allergen:
            continue

        confidence = 0.7
        allergen_lower = allergen.lower()
        if any(a in allergen_lower for a in COMMON_ALLERGENS):
            confidence = 0.95

        reaction = allergy.get('reaction', '')
        COMMON_REACTIONS = ['rash', 'hives', 'anaphylaxis', 'swelling', 'nausea',
                            'vomiting', 'itching', 'breathing', 'angioedema', 'gi upset']
        if reaction and any(r in reaction.lower() for r in COMMON_REACTIONS):
            confidence = max(confidence, 0.90)

        item = {
            'text': allergy.get('raw', allergen),
            'type': 'allergy',
            'allergen': allergen,
            'reaction': reaction,
            'confidence': confidence,
        }

        if confidence >= MEDIUM_CONFIDENCE:
            classified.append(item)
        else:
            flagged.append({
                'text': allergy.get('raw', allergen),
                'reason': 'Allergen not in standard reference — verify format',
                'confidence': confidence,
                'section': 'Allergies',
            })

    return {'classified_items': classified, 'flagged_items': flagged}


def _classify_ros(text):
    """Classify review of systems — identify positive and negative findings."""
    classified = []
    flagged = []

    SYSTEMS = [
        'constitutional', 'general', 'heent', 'head', 'eyes', 'ears', 'nose', 'throat',
        'cardiovascular', 'cardiac', 'cv', 'respiratory', 'pulmonary',
        'gastrointestinal', 'gi', 'genitourinary', 'gu',
        'musculoskeletal', 'msk', 'neurological', 'neuro',
        'psychiatric', 'psych', 'endocrine', 'hematologic',
        'integumentary', 'skin', 'allergic', 'immunologic',
    ]

    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue

        # Detect system name
        system_found = ''
        line_lower = line.lower()
        for sys in SYSTEMS:
            if sys in line_lower:
                system_found = sys
                break

        # Detect positive/negative
        is_negative = any(kw in line_lower for kw in [
            'negative', 'denies', 'no ', 'none', 'unremarkable', 'normal',
            'wnl', 'within normal', 'non-contributory',
        ])
        is_positive = any(kw in line_lower for kw in [
            'positive', 'reports', 'complains', 'endorses', 'yes',
            'present', 'abnormal', '+',
        ]) and not is_negative

        confidence = 0.80 if system_found else 0.50

        item = {
            'text': line,
            'type': 'ros_finding',
            'system': system_found,
            'is_positive': is_positive,
            'is_negative': is_negative,
            'confidence': confidence,
        }

        if confidence >= MEDIUM_CONFIDENCE:
            classified.append(item)
        else:
            flagged.append({
                'text': line,
                'reason': 'Could not identify body system for this ROS entry',
                'confidence': confidence,
                'section': 'Review of Systems',
            })

    return {'classified_items': classified, 'flagged_items': flagged}


def _classify_exam(text):
    """Classify physical exam findings — flag abnormals."""
    classified = []
    flagged = []

    EXAM_SYSTEMS = {
        'general': ['general', 'appearance', 'nad', 'well-developed', 'well-nourished', 'a&o', 'alert'],
        'heent': ['heent', 'head', 'eyes', 'ears', 'nose', 'throat', 'perrla', 'eomi', 'oropharynx', 'tms', 'nares'],
        'neck': ['neck', 'thyroid', 'lymph', 'supple', 'jvd'],
        'cardiovascular': ['heart', 'rrr', 'murmur', 's1', 's2', 'cardiac', 'pulses', 'edema'],
        'respiratory': ['lungs', 'ctab', 'cta', 'breath', 'wheeze', 'crackle', 'respiratory'],
        'abdomen': ['abdomen', 'abd', 'ntnd', 'bowel', 'hepatomegaly', 'splenomegaly', 'soft'],
        'musculoskeletal': ['extremities', 'rom', 'strength', 'joints', 'musculoskeletal', 'gait'],
        'neurological': ['neuro', 'cranial', 'reflexes', 'sensation', 'coordination', 'gait'],
        'skin': ['skin', 'rash', 'lesion', 'wound', 'integument'],
        'psychiatric': ['mood', 'affect', 'oriented', 'psych', 'judgment', 'insight'],
    }

    ABNORMAL_KEYWORDS = [
        'abnormal', 'decreased', 'increased', 'tender', 'swollen', 'erythema',
        'edema', 'murmur', 'wheeze', 'crackle', 'guarding', 'rebound',
        'positive', 'limited', 'deficit', 'asymmetric', 'irregular',
        'distended', 'mass', 'lesion', 'rash', 'effusion',
    ]

    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue

        line_lower = line.lower()

        # Find system
        system = ''
        for sys_name, keywords in EXAM_SYSTEMS.items():
            if any(kw in line_lower for kw in keywords):
                system = sys_name
                break

        is_abnormal = any(kw in line_lower for kw in ABNORMAL_KEYWORDS)
        confidence = 0.85 if system else 0.55

        item = {
            'text': line,
            'type': 'exam_finding',
            'system': system,
            'is_abnormal': is_abnormal,
            'confidence': confidence,
        }

        if is_abnormal:
            flagged.append({
                'text': line,
                'reason': 'Abnormal finding detected — verify documentation',
                'confidence': confidence,
                'section': 'Physical Examination',
                'severity': 'info',
            })

        if confidence >= MEDIUM_CONFIDENCE:
            classified.append(item)
        elif not is_abnormal:
            flagged.append({
                'text': line,
                'reason': 'Could not identify body system for this exam finding',
                'confidence': confidence,
                'section': 'Physical Examination',
            })

    return {'classified_items': classified, 'flagged_items': flagged}


def _classify_narrative(section_name, text):
    """Classify narrative sections (HPI, SH, FH) — kept as blocks."""
    word_count = len(text.split())
    confidence = 0.80 if word_count >= 10 else 0.50

    classified = [{
        'text': text,
        'type': 'narrative',
        'section': section_name,
        'word_count': word_count,
        'confidence': confidence,
    }]

    flagged = []
    if word_count < 5:
        flagged.append({
            'text': text,
            'reason': f'Section "{section_name}" is unusually short ({word_count} words)',
            'confidence': confidence,
            'section': section_name,
        })

    # Check for numbers or specific clinical values that might need verification
    if re.search(r'\b\d{2,3}/\d{2,3}\b', text):  # Blood pressure pattern
        flagged.append({
            'text': re.search(r'\b\d{2,3}/\d{2,3}\b', text).group(),
            'reason': 'Blood pressure value found in narrative — verify currency',
            'confidence': 0.90,
            'section': section_name,
            'severity': 'info',
        })

    return {'classified_items': classified, 'flagged_items': flagged}


def get_all_flagged_items(classified_result):
    """Aggregate all flagged items across all sections."""
    all_flagged = []
    for section_name, data in classified_result.items():
        if isinstance(data, dict):
            for item in data.get('flagged_items', []):
                item['section'] = item.get('section', section_name)
                all_flagged.append(item)
    return sorted(all_flagged, key=lambda x: x.get('confidence', 0))


def get_classification_summary(classified_result):
    """Return a summary of classification results."""
    total_classified = 0
    total_flagged = 0
    sections = []

    for section_name, data in classified_result.items():
        if isinstance(data, dict):
            c = len(data.get('classified_items', []))
            f = len(data.get('flagged_items', []))
            total_classified += c
            total_flagged += f
            if c + f > 0:
                sections.append(f"{section_name}: {c} classified, {f} flagged")

    return {
        'total_classified': total_classified,
        'total_flagged': total_flagged,
        'sections': sections,
        'needs_review': total_flagged > 0,
    }

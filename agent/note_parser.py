"""
CareCompanion — Clinical Note Section Parser
File: agent/note_parser.py

Standalone text parsing engine that identifies and extracts clinical
note sections from free text. This is Step 2 of the Note Reformatter
(F31) — it works on raw text without requiring Amazing Charts automation.

The parser recognizes standard clinical note section headers and extracts
their content. Unclassifiable text is captured in an 'unclassified_text'
key. Very short sections (< 5 words) are flagged for review.

This module has NO external dependencies — it uses only regex and
standard Python. It can run offline and processes text instantly.

Usage:
    from agent.note_parser import parse_note_sections
    sections = parse_note_sections(raw_note_text)
    # Returns: {'Chief Complaint': '...', 'HPI': '...', ...}
"""

import re
import logging

logger = logging.getLogger(__name__)


# =====================================================================
# Section header patterns — ordered by specificity (most specific first)
# =====================================================================
# Each tuple: (canonical_name, list_of_regex_patterns)
SECTION_PATTERNS = [
    ('Chief Complaint', [
        r'(?i)chief\s+complaint\s*[:.]',
        r'(?i)\bcc\s*[:.]',
        r'(?i)reason\s+for\s+visit\s*[:.]',
        r'(?i)presenting\s+complaint\s*[:.]',
    ]),
    ('History of Present Illness', [
        r'(?i)history\s+of\s+present\s+illness\s*[:.]',
        r'(?i)\bhpi\s*[:.]',
        r'(?i)present\s+illness\s*[:.]',
        r'(?i)interval\s+history\s*[:.]',
    ]),
    ('Past Medical History', [
        r'(?i)past\s+medical\s+history\s*[:.]',
        r'(?i)\bpmh\s*[:.]',
        r'(?i)medical\s+history\s*[:.]',
        r'(?i)active\s+problems?\s*[:.]',
        r'(?i)problem\s+list\s*[:.]',
    ]),
    ('Past Surgical History', [
        r'(?i)past\s+surgical\s+history\s*[:.]',
        r'(?i)\bpsh\s*[:.]',
        r'(?i)surgical\s+history\s*[:.]',
        r'(?i)prior\s+surgeries\s*[:.]',
    ]),
    ('Family History', [
        r'(?i)family\s+history\s*[:.]',
        r'(?i)\bfh\s*[:.]',
        r'(?i)fam\s+hx\s*[:.]',
    ]),
    ('Social History', [
        r'(?i)social\s+history\s*[:.]',
        r'(?i)\bsh\s*[:.]',
        r'(?i)soc\s+hx\s*[:.]',
    ]),
    ('Medications', [
        r'(?i)medications?\s*[:.]',
        r'(?i)current\s+medications?\s*[:.]',
        r'(?i)med(?:ication)?\s+list\s*[:.]',
        r'(?i)active\s+medications?\s*[:.]',
        r'(?i)\brx\s+list\s*[:.]',
    ]),
    ('Allergies', [
        r'(?i)allergies\s*[:.]',
        r'(?i)drug\s+allergies\s*[:.]',
        r'(?i)allergy\s+list\s*[:.]',
        r'(?i)adverse\s+reactions?\s*[:.]',
        r'(?i)\bnkda\b',
    ]),
    ('Review of Systems', [
        r'(?i)review\s+of\s+systems?\s*[:.]',
        r'(?i)\bros\s*[:.]',
    ]),
    ('Physical Examination', [
        r'(?i)physical\s+exam(?:ination)?\s*[:.]',
        r'(?i)\bpe\s*[:.]',
        r'(?i)vitals?\s*[:./]',
        r'(?i)exam(?:ination)?\s*[:.]',
        r'(?i)objective\s*[:.]',
    ]),
    ('Assessment', [
        r'(?i)assessment\s*[:.]',
        r'(?i)impression\s*[:.]',
        r'(?i)diagnos(?:is|es)\s*[:.]',
        r'(?i)clinical\s+impression\s*[:.]',
    ]),
    ('Assessment and Plan', [
        r'(?i)assessment\s+(?:and|&)\s+plan\s*[:.]',
        r'(?i)\ba/?p\s*[:.]',
        r'(?i)\ba\s*&\s*p\s*[:.]',
    ]),
    ('Plan', [
        r'(?i)plan\s*[:.]',
        r'(?i)treatment\s+plan\s*[:.]',
        r'(?i)management\s+plan\s*[:.]',
    ]),
    ('Follow-up', [
        r'(?i)follow[\s-]*up\s*[:.]',
        r'(?i)\bf/?u\s*[:.]',
        r'(?i)return\s+visit\s*[:.]',
        r'(?i)disposition\s*[:.]',
    ]),
    ('Immunizations', [
        r'(?i)immunizations?\s*[:.]',
        r'(?i)vaccines?\s*[:.]',
        r'(?i)vaccination\s+history\s*[:.]',
    ]),
    ('Health Maintenance', [
        r'(?i)health\s+maintenance\s*[:.]',
        r'(?i)preventive\s+care\s*[:.]',
        r'(?i)screening\s*[:.]',
    ]),
    ('Labs', [
        r'(?i)lab(?:oratory)?\s+results?\s*[:.]',
        r'(?i)labs?\s*[:.]',
        r'(?i)recent\s+labs?\s*[:.]',
        r'(?i)diagnostics?\s*[:.]',
    ]),
]


def parse_note_sections(raw_text):
    """
    Parse free text into clinical note sections.

    Parameters
    ----------
    raw_text : str
        Raw clinical note text (from OCR, clipboard, or manual entry).

    Returns
    -------
    dict with keys:
        - Each recognized section name maps to its text content
        - 'unclassified_text': text between sections that didn't match any header
        - 'needs_review': list of sections that are unusually short (<5 words)
        - '_metadata': dict with parsing stats
    """
    if not raw_text or not raw_text.strip():
        return {
            'unclassified_text': '',
            'needs_review': [],
            '_metadata': {'sections_found': 0, 'total_chars': 0, 'parse_confidence': 0},
        }

    text = raw_text.strip()

    # Build a combined regex of all section headers
    # Find all header positions in the text
    header_positions = []  # [(start, end, section_name), ...]

    for section_name, patterns in SECTION_PATTERNS:
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                header_positions.append((match.start(), match.end(), section_name))

    # Sort by position
    header_positions.sort(key=lambda x: x[0])

    # Deduplicate: if two headers overlap or are very close, keep the first
    deduped = []
    for pos in header_positions:
        if deduped and pos[0] < deduped[-1][1] + 5:
            continue  # Skip overlapping or too-close headers
        deduped.append(pos)

    # Extract section contents
    result = {}
    unclassified_parts = []
    needs_review = []

    if not deduped:
        # No section headers found — entire text is unclassified
        return {
            'unclassified_text': text,
            'needs_review': ['_entire_note'],
            '_metadata': {
                'sections_found': 0,
                'total_chars': len(text),
                'parse_confidence': 0.0,
                'warning': 'No identifiable section structure found. Full manual review required.',
            },
        }

    # Text before first header
    if deduped[0][0] > 0:
        pre_text = text[:deduped[0][0]].strip()
        if pre_text:
            unclassified_parts.append(pre_text)

    # Extract each section
    for i, (start, end, name) in enumerate(deduped):
        # Content runs from end of this header to start of next header
        next_start = deduped[i + 1][0] if i + 1 < len(deduped) else len(text)
        content = text[end:next_start].strip()

        # Merge "Assessment and Plan" — if both Assessment and Plan found separately
        # and Assessment+Plan is also found, prefer the combined version
        if name in result:
            result[name] += '\n' + content
        else:
            result[name] = content

        # Check for unusually short sections
        word_count = len(content.split())
        if word_count < 5 and content:
            needs_review.append(name)

    # Calculate confidence
    classified_chars = sum(len(v) for k, v in result.items() if k != 'unclassified_text')
    total_chars = len(text)
    confidence = classified_chars / total_chars if total_chars > 0 else 0

    result['unclassified_text'] = '\n'.join(unclassified_parts) if unclassified_parts else ''
    result['needs_review'] = needs_review
    result['_metadata'] = {
        'sections_found': len(deduped),
        'total_chars': total_chars,
        'classified_chars': classified_chars,
        'parse_confidence': round(confidence, 3),
        'section_names': [d[2] for d in deduped],
    }

    return result


def get_section_summary(parsed):
    """
    Return a human-readable summary of what was parsed.
    Useful for displaying in the UI before the provider reviews.
    """
    if not parsed:
        return 'No sections parsed.'

    meta = parsed.get('_metadata', {})
    sections = meta.get('section_names', [])
    confidence = meta.get('parse_confidence', 0)
    needs_review = parsed.get('needs_review', [])

    lines = [
        f"Sections found: {len(sections)}",
        f"Parse confidence: {confidence:.0%}",
    ]
    if sections:
        lines.append(f"Sections: {', '.join(sections)}")
    if needs_review:
        lines.append(f"Needs review: {', '.join(needs_review)}")
    if parsed.get('unclassified_text'):
        uc_words = len(parsed['unclassified_text'].split())
        lines.append(f"Unclassified text: {uc_words} words")

    return '\n'.join(lines)


# =====================================================================
# Subsection parsers — for deeper analysis within sections
# =====================================================================

def parse_medication_list(med_text):
    """
    Parse a medication section into individual medication entries.
    Returns list of dicts with 'name', 'dose', 'frequency', 'route'.
    """
    if not med_text:
        return []

    meds = []
    # Split by newlines or numbered list patterns
    lines = re.split(r'\n|(?:\d+[\.\)]\s)', med_text)

    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue

        # Try to extract dose from the line
        dose_match = re.search(
            r'(\d+(?:\.\d+)?\s*(?:mg|mcg|ml|units?|%|meq|g|iu)(?:/[\d.]+\s*(?:mg|mcg|ml))?)',
            line, re.IGNORECASE
        )
        freq_match = re.search(
            r'\b((?:once|twice|three\s+times?)\s+(?:daily|a\s+day|weekly)|'
            r'(?:bid|tid|qid|qd|qhs|qam|qpm|prn|daily|weekly|monthly|'
            r'q\d+h|every\s+\d+\s+hours?|at\s+bedtime))\b',
            line, re.IGNORECASE
        )

        name = line
        dose = ''
        frequency = ''

        if dose_match:
            dose = dose_match.group(1).strip()
            # Name is everything before the dose
            name = line[:dose_match.start()].strip().rstrip('-,;')
        if freq_match:
            frequency = freq_match.group(1).strip()
            if not dose_match:
                name = line[:freq_match.start()].strip().rstrip('-,;')

        if not name:
            name = line

        meds.append({
            'name': name.strip(' ,-;:'),
            'dose': dose,
            'frequency': frequency,
            'raw': line,
        })

    return meds


def parse_diagnosis_list(dx_text):
    """
    Parse an assessment/PMH section into individual diagnosis entries.
    Returns list of dicts with 'name', 'icd10' (if found), 'is_numbered'.
    """
    if not dx_text:
        return []

    diagnoses = []
    lines = re.split(r'\n', dx_text)

    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue

        # Check for numbered diagnosis (e.g., "1. Hypertension")
        numbered = bool(re.match(r'^\d+[\.\)]\s', line))
        clean = re.sub(r'^\d+[\.\)]\s*', '', line).strip()

        # Try to extract ICD-10 code
        icd_match = re.search(r'\b([A-Z]\d{2}(?:\.\d{1,4})?)\b', clean)
        icd10 = icd_match.group(1) if icd_match else ''

        # Remove ICD-10 code from name
        name = clean
        if icd10:
            name = re.sub(r'\s*[\(\[]\s*' + re.escape(icd10) + r'\s*[\)\]]?\s*', ' ', name).strip()
            name = re.sub(r'\b' + re.escape(icd10) + r'\b', '', name).strip().strip(' ,-;:')

        if name:
            diagnoses.append({
                'name': name,
                'icd10': icd10,
                'is_numbered': numbered,
                'raw': line,
            })

    return diagnoses


def parse_allergy_list(allergy_text):
    """
    Parse an allergy section into individual allergy + reaction pairs.
    Returns list of dicts with 'allergen', 'reaction'.
    """
    if not allergy_text:
        return []

    # Check for NKDA
    if re.search(r'(?i)\bnkda\b|no\s+known\s+(?:drug\s+)?allergies', allergy_text):
        return [{'allergen': 'NKDA', 'reaction': 'No known drug allergies'}]

    allergies = []
    lines = re.split(r'\n|[;,](?!\s*\d)', allergy_text)

    for line in lines:
        line = line.strip()
        if not line or len(line) < 2:
            continue

        # Try allergen - reaction pattern
        # "Penicillin - rash", "Sulfa (hives)", "ACE inhibitors: cough"
        parts = re.split(r'\s*[-:–]\s*|\s*[\(\[]\s*', line, maxsplit=1)
        allergen = parts[0].strip().rstrip('([-:')
        reaction = ''
        if len(parts) > 1:
            reaction = parts[1].strip().rstrip(')]')

        if allergen:
            allergies.append({
                'allergen': allergen,
                'reaction': reaction,
                'raw': line,
            })

    return allergies

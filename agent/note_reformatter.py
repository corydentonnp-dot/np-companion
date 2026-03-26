"""
CareCompanion — Note Reformatter Template Engine
File: agent/note_reformatter.py

Step 4 of the Note Reformatter (F31). Takes classified content from
note_classifier.py and maps it into the user's preferred note template.

The template defines which sections to include, their order, and any
boilerplate text. The engine fills each template section with the
corresponding classified content and collects all flagged items into
a review list.

Returns a filled template, flagged items, and coverage stats.
"""

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# Default note template — used when user hasn't customized their own
DEFAULT_TEMPLATE = {
    'name': 'Standard Primary Care Note',
    'sections': [
        {'key': 'Chief Complaint', 'label': 'Chief Complaint', 'required': True, 'boilerplate': ''},
        {'key': 'History of Present Illness', 'label': 'HPI', 'required': True, 'boilerplate': ''},
        {'key': 'Past Medical History', 'label': 'Past Medical History', 'required': False, 'boilerplate': ''},
        {'key': 'Past Surgical History', 'label': 'Past Surgical History', 'required': False, 'boilerplate': ''},
        {'key': 'Family History', 'label': 'Family History', 'required': False, 'boilerplate': ''},
        {'key': 'Social History', 'label': 'Social History', 'required': False, 'boilerplate': ''},
        {'key': 'Medications', 'label': 'Current Medications', 'required': True, 'boilerplate': ''},
        {'key': 'Allergies', 'label': 'Allergies', 'required': True, 'boilerplate': ''},
        {'key': 'Immunizations', 'label': 'Immunizations', 'required': False, 'boilerplate': ''},
        {'key': 'Review of Systems', 'label': 'Review of Systems', 'required': False, 'boilerplate': ''},
        {'key': 'Physical Examination', 'label': 'Physical Examination', 'required': True, 'boilerplate': ''},
        {'key': 'Labs', 'label': 'Labs / Diagnostics', 'required': False, 'boilerplate': ''},
        {'key': 'Assessment', 'label': 'Assessment', 'required': True, 'boilerplate': ''},
        {'key': 'Plan', 'label': 'Plan', 'required': True, 'boilerplate': ''},
        {'key': 'Follow-up', 'label': 'Follow-Up', 'required': False, 'boilerplate': ''},
    ],
}


def build_reformatted_note(classified_content, parsed_sections, user_template=None):
    """
    Map classified content into a note template.

    Parameters
    ----------
    classified_content : dict
        Output from note_classifier.classify_content().
    parsed_sections : dict
        Output from note_parser.parse_note_sections() (raw text per section).
    user_template : dict or None
        User's custom template. If None, uses DEFAULT_TEMPLATE.

    Returns
    -------
    dict with:
        'filled_text': str — the complete reformatted note text
        'filled_sections': dict — section_key → filled text
        'flagged_items': list — all items needing provider review
        'coverage': float — percentage of template sections filled (0.0-1.0)
        'missing_sections': list — required template sections with no content
        'template_name': str
    """
    template = user_template or DEFAULT_TEMPLATE

    filled_sections = {}
    filled_lines = []
    all_flagged = []
    filled_count = 0
    total_sections = len(template['sections'])

    for section_def in template['sections']:
        key = section_def['key']
        label = section_def['label']
        boilerplate = section_def.get('boilerplate', '')
        required = section_def.get('required', False)

        # Get classified content for this section
        classified_data = classified_content.get(key, {})
        # Also check "Assessment and Plan" combined key
        if not classified_data and key == 'Assessment':
            classified_data = classified_content.get('Assessment and Plan', {})
        if not classified_data and key == 'Plan':
            classified_data = classified_content.get('Assessment and Plan', {})

        # Build section text from classified items
        section_text = ''

        if isinstance(classified_data, dict):
            items = classified_data.get('classified_items', [])
            flags = classified_data.get('flagged_items', [])

            if items:
                section_text = _format_classified_items(key, items)
            all_flagged.extend(flags)
        elif key in parsed_sections and isinstance(parsed_sections[key], str):
            # Fallback to raw parsed text if classifier didn't process this section
            section_text = parsed_sections[key]

        # Apply boilerplate if section is empty
        if not section_text and boilerplate:
            section_text = boilerplate

        # Build the section
        if section_text:
            filled_count += 1
            filled_sections[key] = section_text
            filled_lines.append(f"{label}:")
            filled_lines.append(section_text)
            filled_lines.append('')  # Blank line between sections

    # Handle unclassified text
    unclassified = parsed_sections.get('unclassified_text', '')
    if unclassified:
        all_flagged.append({
            'text': unclassified[:500],
            'reason': 'Unclassified text that could not be mapped to any template section',
            'confidence': 0.0,
            'section': '_unclassified',
        })

    # Calculate coverage
    coverage = filled_count / total_sections if total_sections > 0 else 0

    # Missing required sections
    missing = [
        s['label'] for s in template['sections']
        if s.get('required') and s['key'] not in filled_sections
    ]

    return {
        'filled_text': '\n'.join(filled_lines),
        'filled_sections': filled_sections,
        'flagged_items': all_flagged,
        'coverage': round(coverage, 3),
        'missing_sections': missing,
        'template_name': template.get('name', 'Custom Template'),
        'total_sections': total_sections,
        'filled_sections_count': filled_count,
    }


def _format_classified_items(section_key, items):
    """Format a list of classified items into section text."""
    lines = []

    for item in items:
        item_type = item.get('type', '')

        if item_type == 'medication':
            name = item.get('name', '')
            dose = item.get('dose', '')
            freq = item.get('frequency', '')
            parts = [name]
            if dose:
                parts.append(dose)
            if freq:
                parts.append(freq)
            lines.append(' '.join(parts))

        elif item_type == 'diagnosis':
            name = item.get('name', '')
            icd10 = item.get('icd10', '')
            snomed = item.get('snomed_code', '')
            codes = []
            if icd10:
                codes.append(icd10)
            if snomed:
                codes.append(f"SNOMED {snomed}")
            if codes:
                lines.append(f"{name} ({', '.join(codes)})")
            else:
                lines.append(name)

        elif item_type == 'allergy':
            allergen = item.get('allergen', '')
            reaction = item.get('reaction', '')
            if reaction:
                lines.append(f"{allergen} — {reaction}")
            else:
                lines.append(allergen)

        elif item_type == 'ros_finding':
            system = item.get('system', '').title()
            text = item.get('text', '')
            if system:
                lines.append(f"{system}: {text}")
            else:
                lines.append(text)

        elif item_type == 'exam_finding':
            system = item.get('system', '').title()
            text = item.get('text', '')
            if system:
                lines.append(f"{system}: {text}")
            else:
                lines.append(text)

        elif item_type == 'narrative':
            lines.append(item.get('text', ''))

        else:
            lines.append(item.get('text', ''))

    return '\n'.join(lines)


def get_available_templates():
    """Return list of available templates (default + any user-created)."""
    return [DEFAULT_TEMPLATE]


def reformat_note(raw_text, user_template=None, use_api=False):
    """
    Complete pipeline: parse → classify → reformat.
    Convenience function that chains all three steps.

    Parameters
    ----------
    raw_text : str
        Raw clinical note text.
    user_template : dict or None
        User's custom template.
    use_api : bool
        Whether to validate against RxNorm/ICD-10 APIs.

    Returns
    -------
    dict with filled_text, flagged_items, coverage, etc.
    """
    from agent.note_parser import parse_note_sections
    from agent.note_classifier import classify_content

    # Step 2: Parse
    parsed = parse_note_sections(raw_text)

    # Step 3: Classify
    classified = classify_content(parsed, use_api=use_api)

    # Step 3b: SNOMED enrichment (only when API mode active)
    if use_api:
        classified = _enrich_with_snomed(classified)

    # Step 4: Build template
    result = build_reformatted_note(classified, parsed, user_template)

    # Add parser metadata
    result['parse_metadata'] = parsed.get('_metadata', {})

    return result


def _enrich_with_snomed(classified_content):
    """
    Enrich diagnosis items with SNOMED CT codes via the UMLS crosswalk.
    Adds 'snomed_code' and 'snomed_term' keys to classified diagnosis items.
    Fails silently if UMLS is unavailable.
    """
    try:
        from models import db
        from app.services.api.umls import UMLSService
        import config
        api_key = getattr(config, 'UMLS_API_KEY', '')
        if not api_key:
            return classified_content

        svc = UMLSService(db, api_key)

        for section_key, section_data in classified_content.items():
            if not isinstance(section_data, dict):
                continue
            items = section_data.get('classified_items', [])
            for item in items:
                if item.get('type') != 'diagnosis':
                    continue
                name = item.get('name', '')
                if not name:
                    continue
                # Search UMLS for the diagnosis term
                concepts = svc.search(name)
                if not concepts:
                    continue
                cui = concepts[0].get('cui')
                if not cui:
                    continue
                # Get SNOMED code
                snomed_codes = svc.get_snomed_for_concept(cui)
                if snomed_codes:
                    item['snomed_code'] = snomed_codes[0].get('code', '')
                    item['snomed_term'] = snomed_codes[0].get('description', '')
    except Exception:
        logger.debug('SNOMED enrichment skipped (UMLS unavailable)')

    return classified_content

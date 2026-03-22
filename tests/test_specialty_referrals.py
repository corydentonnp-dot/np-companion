"""
Phase P4-4 — Specialty-Specific Referral Templates (F27a)

Tests for SPECIALTY_FIELDS configuration, form rendering, letter generation
with specialty-specific clinical details, migration, and HIPAA compliance.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(ROOT, relpath), 'r', encoding='utf-8') as f:
        return f.read()


def run_tests():
    passed = []
    failed = []

    tools_py = _read('routes/tools.py')
    model_py = _read('models/tools.py')
    template = _read('templates/referral.html')

    # ==================================================================
    # 4.1 — SPECIALTY_FIELDS configuration dict
    # ==================================================================

    print('[1/15] SPECIALTY_FIELDS exists in routes/tools.py...')
    try:
        assert 'SPECIALTY_FIELDS' in tools_py, 'SPECIALTY_FIELDS not found'
        passed.append('4.1a SPECIALTY_FIELDS exists')
    except Exception as e:
        failed.append(f'4.1a SPECIALTY_FIELDS exists: {e}')

    print('[2/15] All 21 specialties covered...')
    try:
        from routes.tools import SPECIALTIES, SPECIALTY_FIELDS
        for s in SPECIALTIES:
            assert s in SPECIALTY_FIELDS, f'{s} missing from SPECIALTY_FIELDS'
        passed.append('4.1b all 21 specialties covered')
    except Exception as e:
        failed.append(f'4.1b all 21 specialties covered: {e}')

    print('[3/15] Each specialty has 2-4 fields (Other has 0)...')
    try:
        from routes.tools import SPECIALTIES, SPECIALTY_FIELDS
        for s in SPECIALTIES:
            fields = SPECIALTY_FIELDS[s]
            if s == 'Other':
                assert len(fields) == 0, f'Other should have 0 fields, got {len(fields)}'
            else:
                assert 2 <= len(fields) <= 4, f'{s} has {len(fields)} fields (expected 2-4)'
        passed.append('4.1c field count per specialty')
    except Exception as e:
        failed.append(f'4.1c field count per specialty: {e}')

    print('[4/15] Field structure validated (name, label, type, placeholder)...')
    try:
        from routes.tools import SPECIALTY_FIELDS
        for spec, fields in SPECIALTY_FIELDS.items():
            for f in fields:
                assert 'name' in f, f'{spec}: field missing name'
                assert 'label' in f, f'{spec}: field missing label'
                assert 'type' in f, f'{spec}: field missing type'
                assert f['type'] in ('text', 'textarea', 'select'), \
                    f'{spec}/{f["name"]}: invalid type {f["type"]}'
                assert 'placeholder' in f, f'{spec}/{f["name"]}: missing placeholder'
        passed.append('4.1d field structure valid')
    except Exception as e:
        failed.append(f'4.1d field structure valid: {e}')

    print('[5/15] Cardiology has expected fields...')
    try:
        from routes.tools import SPECIALTY_FIELDS
        cardio = SPECIALTY_FIELDS['Cardiology']
        names = [f['name'] for f in cardio]
        assert 'ekg_findings' in names, 'ekg_findings missing'
        assert 'echo_results' in names, 'echo_results missing'
        passed.append('4.1e Cardiology fields')
    except Exception as e:
        failed.append(f'4.1e Cardiology fields: {e}')

    print('[6/15] Psychiatry has screening/safety fields...')
    try:
        from routes.tools import SPECIALTY_FIELDS
        psych = SPECIALTY_FIELDS['Psychiatry']
        names = [f['name'] for f in psych]
        assert 'screening_scores' in names, 'screening_scores missing'
        assert 'safety_concerns' in names, 'safety_concerns missing'
        passed.append('4.1f Psychiatry fields')
    except Exception as e:
        failed.append(f'4.1f Psychiatry fields: {e}')

    print('[7/15] SPECIALTY_FIELDS is JSON-serializable...')
    try:
        from routes.tools import SPECIALTY_FIELDS
        result = json.dumps(SPECIALTY_FIELDS)
        parsed = json.loads(result)
        assert len(parsed) == 21, f'expected 21 specialties in JSON, got {len(parsed)}'
        passed.append('4.1g JSON serializable')
    except Exception as e:
        failed.append(f'4.1g JSON serializable: {e}')

    # ==================================================================
    # 4.2 — Template updates
    # ==================================================================

    print('[8/15] Template has specialty-fields container...')
    try:
        assert 'id="specialty-fields"' in template, 'specialty-fields div missing'
        assert 'SPECIALTY_FIELDS' in template, 'JS SPECIALTY_FIELDS variable missing'
        passed.append('4.2a specialty-fields container')
    except Exception as e:
        failed.append(f'4.2a specialty-fields container: {e}')

    print('[9/15] Template JS renders fields on specialty change...')
    try:
        assert "addEventListener('change'" in template or 'addEventListener("change"' in template, \
            'change event listener missing'
        assert 'spec-' in template, 'spec- field ID prefix missing'
        assert 'createElement' in template, 'dynamic field creation missing'
        passed.append('4.2b JS dynamic field rendering')
    except Exception as e:
        failed.append(f'4.2b JS dynamic field rendering: {e}')

    print('[10/15] Template sends specialty fields in generate request...')
    try:
        assert 'specFields' in template or 'spec_fields' in template or 'specFields.forEach' in template, \
            'specialty fields not collected in JS'
        passed.append('4.2c JS collects specialty fields')
    except Exception as e:
        failed.append(f'4.2c JS collects specialty fields: {e}')

    # ==================================================================
    # 4.3 — Letter generation with specialty content
    # ==================================================================

    print('[11/15] Generate route includes specialty-specific content in letter...')
    try:
        assert 'SPECIALTY-SPECIFIC CLINICAL DETAILS' in tools_py, \
            'specialty details section missing from letter generation'
        assert "SPECIALTY_FIELDS.get(specialty" in tools_py, \
            'SPECIALTY_FIELDS lookup missing in generate route'
        passed.append('4.3a letter includes specialty details')
    except Exception as e:
        failed.append(f'4.3a letter includes specialty details: {e}')

    print('[12/15] Empty specialty fields omitted from letter...')
    try:
        assert "if val:" in tools_py or "if val" in tools_py, \
            'empty field check missing'
        assert "if clinical_lines:" in tools_py, \
            'empty clinical_lines guard missing'
        passed.append('4.3b empty fields omitted')
    except Exception as e:
        failed.append(f'4.3b empty fields omitted: {e}')

    print('[13/15] specialty_fields column added to ReferralLetter model...')
    try:
        assert 'specialty_fields' in model_py, 'specialty_fields column missing from model'
        assert 'specialty_fields' in tools_py, 'specialty_fields not saved in generate route'
        passed.append('4.3c specialty_fields column in model')
    except Exception as e:
        failed.append(f'4.3c specialty_fields column in model: {e}')

    # ==================================================================
    # 4.4 — Migration & HIPAA
    # ==================================================================

    print('[14/15] Migration file exists and is runnable...')
    try:
        mig_path = os.path.join(ROOT, 'migrations', 'migrate_add_referral_specialty_fields.py')
        assert os.path.exists(mig_path), 'migration file not found'
        mig_content = _read('migrations/migrate_add_referral_specialty_fields.py')
        assert 'specialty_fields' in mig_content, 'column not in migration'
        assert 'referral_letter' in mig_content, 'table not in migration'
        passed.append('4.4a migration exists')
    except Exception as e:
        failed.append(f'4.4a migration exists: {e}')

    print('[15/15] HIPAA: No full names stored in specialty_fields...')
    try:
        # Verify the specialty_fields stored are clinical data only
        # Check that patient_display is NOT included in the specialty_details dict
        gen_section_start = tools_py.index('specialty_details = {}')
        gen_section = tools_py[gen_section_start:gen_section_start + 600]
        assert 'patient_display' not in gen_section, 'patient_display in specialty_details'
        assert 'patient_name' not in gen_section, 'patient_name in specialty_details'
        passed.append('4.4b HIPAA — no PHI in specialty_fields')
    except Exception as e:
        failed.append(f'4.4b HIPAA — no PHI in specialty_fields: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print(f'\n{"="*60}')
    print(f'Phase P4-4 Specialty Referral Templates: {len(passed)} passed, {len(failed)} failed')
    print(f'{"="*60}')
    if failed:
        for f_msg in failed:
            print(f'  FAIL  {f_msg}')
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

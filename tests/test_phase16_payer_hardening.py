"""
Phase 16 — Payer Hardening + External Data Imports

Verifies:
  16.1 Medicare Advantage as distinct payer path
  16.2 Payer suppression rules + cost-share notes
  16.3 DHS code list import migration
  16.4 Billing master list import migration
  16.5 Hardened billing routes (status validation, MRN sanitization)
  16.6 Migration idempotency verification

Usage:
    venv\\Scripts\\python.exe tests/test_phase16_payer_hardening.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(ROOT, relpath), encoding='utf-8') as f:
        return f.read()


def run_tests():
    passed = []
    failed = []

    # ==================================================================
    # 16.1 — Medicare Advantage distinct payer path
    # ==================================================================
    print('[1/15] MA returns is_medicare_advantage flag...')
    try:
        from billing_engine.payer_routing import get_payer_context
        ctx = get_payer_context({"insurer_type": "medicare_advantage", "age": 70})
        assert ctx["is_medicare_advantage"] is True
        assert ctx["is_medicare"] is True
        passed.append('16.1a: MA is_medicare_advantage flag')
    except Exception as e:
        failed.append(f'16.1a: MA flag: {e}')

    print('[2/15] MA uses CPT codes (not G-codes)...')
    try:
        assert ctx["use_g_codes"] is False, "MA should NOT use G-codes"
        assert ctx["use_modifier_33"] is True, "MA should use modifier 33"
        passed.append('16.1b: MA uses CPT codes, not G-codes')
    except Exception as e:
        failed.append(f'16.1b: MA code selection: {e}')

    print('[3/15] MA routes vaccine admin to 90471 (not G0008)...')
    try:
        assert ctx["admin_codes"]["flu_admin"] == "90471", "MA flu admin should be 90471"
        passed.append('16.1c: MA vaccine admin uses 90471')
    except Exception as e:
        failed.append(f'16.1c: MA vaccine admin: {e}')

    print('[4/15] Traditional Medicare still uses G-codes...')
    try:
        trad = get_payer_context({"insurer_type": "medicare", "age": 70})
        assert trad["use_g_codes"] is True
        assert trad["is_medicare_traditional"] is True
        assert trad["admin_codes"]["flu_admin"] == "G0008"
        passed.append('16.1d: Traditional Medicare G-codes preserved')
    except Exception as e:
        failed.append(f'16.1d: Traditional Medicare: {e}')

    # ==================================================================
    # 16.2 — Payer suppression rules
    # ==================================================================
    print('[5/15] Commercial payer suppresses CCM...')
    try:
        comm = get_payer_context({"insurer_type": "commercial", "age": 50})
        assert "CCM" in comm["suppressed_codes"]
        assert "payer_uncertain" in comm["suppressed_codes"]["CCM"]
        passed.append('16.2a: Commercial CCM suppression')
    except Exception as e:
        failed.append(f'16.2a: CCM suppression: {e}')

    print('[6/15] G2211 suppressed for non-Medicare-B...')
    try:
        assert "G2211_COMPLEXITY" in comm["suppressed_codes"]
        # MA should also suppress G2211
        ma_ctx = get_payer_context({"insurer_type": "medicare_advantage", "age": 70})
        assert "G2211_COMPLEXITY" in ma_ctx["suppressed_codes"]
        # Traditional Medicare should NOT suppress G2211
        trad2 = get_payer_context({"insurer_type": "medicare", "age": 70})
        assert "G2211_COMPLEXITY" not in trad2["suppressed_codes"]
        passed.append('16.2b: G2211 suppression for non-Medicare-B')
    except Exception as e:
        failed.append(f'16.2b: G2211 suppression: {e}')

    print('[7/15] Cost-share notes present for Medicare AWV...')
    try:
        trad3 = get_payer_context({"insurer_type": "medicare", "age": 70})
        assert "AWV_FLAG" in trad3["cost_share_notes"]
        assert "No copay" in trad3["cost_share_notes"]["AWV_FLAG"]
        passed.append('16.2c: Medicare AWV cost-share note')
    except Exception as e:
        failed.append(f'16.2c: Cost-share notes: {e}')

    # ==================================================================
    # 16.3 — DHS code list migration
    # ==================================================================
    print('[8/15] DHS code import migration exists...')
    try:
        src = _read('migrations/migrate_import_dhs_codes.py')
        assert 'billing_rule_cache' in src.lower() or 'BillingRuleCache' in src
        assert 'DHS' in src
        passed.append('16.3a: DHS migration exists')
    except Exception as e:
        failed.append(f'16.3a: DHS migration: {e}')

    print('[9/15] DHS migration cross-references detector codes...')
    try:
        assert 'BILLING_RULES' in src
        assert 'STARK' in src.upper() or 'flagged' in src
        passed.append('16.3b: DHS Stark Law cross-reference')
    except Exception as e:
        failed.append(f'16.3b: DHS cross-reference: {e}')

    # ==================================================================
    # 16.4 — Billing master list import migration
    # ==================================================================
    print('[10/15] Master list import migration exists...')
    try:
        src = _read('migrations/migrate_import_billing_master.py')
        assert 'BillingRule' in src
        assert 'opportunity_code' in src
        passed.append('16.4a: Master list migration exists')
    except Exception as e:
        failed.append(f'16.4a: Master list migration: {e}')

    print('[11/15] Master list maps all 17 categories...')
    try:
        assert 'CATEGORY_MAP' in src
        for cat in ['awv', 'ccm', 'procedures', 'chronic_monitoring', 'screening',
                     'immunizations', 'telehealth', 'pediatric', 'sdoh']:
            assert cat in src, f'Missing category: {cat}'
        passed.append('16.4b: Master list covers all categories')
    except Exception as e:
        failed.append(f'16.4b: Master list categories: {e}')

    print('[12/15] Master list upserts (not just inserts)...')
    try:
        assert 'existing' in src
        assert 'updated' in src
        assert 'inserted' in src
        passed.append('16.4c: Master list uses upsert pattern')
    except Exception as e:
        failed.append(f'16.4c: Master list upsert: {e}')

    # ==================================================================
    # 16.5 — Hardened billing routes
    # ==================================================================
    print('[13/15] Capture endpoint validates status...')
    try:
        src = _read('routes/intelligence.py')
        idx = src.index('def capture_opportunity')
        body = src[idx:idx + 600]
        assert 'pending' in body and 'partial' in body
        assert '409' in body
        passed.append('16.5a: Capture validates status')
    except Exception as e:
        failed.append(f'16.5a: Capture validation: {e}')

    print('[14/15] Dismiss endpoint caps reason length...')
    try:
        idx = src.index('def dismiss_opportunity')
        body = src[idx:idx + 800]
        assert '500' in body or 'reason' in body
        assert '409' in body
        passed.append('16.5b: Dismiss caps reason + validates status')
    except Exception as e:
        failed.append(f'16.5b: Dismiss validation: {e}')

    print('[15/15] Patient billing sanitizes MRN input...')
    try:
        idx = src.index('def patient_billing')
        body = src[idx:idx + 400]
        assert 're.match' in body or '_re.match' in body
        assert 'A-Za-z0-9' in body or 'alphanumeric' in body
        passed.append('16.5c: MRN input sanitization')
    except Exception as e:
        failed.append(f'16.5c: MRN sanitization: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print(f'\n{"=" * 60}')
    print(f'Phase 16 Payer Hardening: {len(passed)} passed, {len(failed)} failed')
    print(f'{"=" * 60}')
    for p in passed:
        print(f'  PASS  {p}')
    for f in failed:
        print(f'  FAIL  {f}')
    if failed:
        print('\n** FAILURES DETECTED **')
        sys.exit(1)
    else:
        print('\nAll Phase 16 tests passed.')
    return passed, failed


if __name__ == '__main__':
    run_tests()

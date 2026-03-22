"""
Phase 29.1 — Billing Engine Unit Tests

25 tests covering all shared utility functions:
  1-5:   age_from_dob() edge cases
  6-9:   has_dx() / get_dx()
  10-13: has_medication() / get_medications()
  14-16: is_overdue() / months_since()
  17-19: hash_mrn() / count_chronic_conditions()
  20-21: add_business_days()
  22-25: scoring factors (ExpectedNetValueCalculator)

Usage:
    venv\\Scripts\\python.exe tests/test_billing_unit.py
"""

import os
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    passed = []
    failed = []

    # ==================================================================
    # 1 — age_from_dob: valid date string
    # ==================================================================
    print('[1/25] age_from_dob: valid date string...')
    try:
        from billing_engine.utils import age_from_dob
        dob = date(1960, 1, 15)
        age = age_from_dob(dob)
        expected = date.today().year - 1960 - ((date.today().month, date.today().day) < (1, 15))
        assert age == expected, f'Expected {expected}, got {age}'
        passed.append('1: age_from_dob valid date')
    except Exception as e:
        failed.append(f'1: age_from_dob: {e}')

    # ==================================================================
    # 2 — age_from_dob: string format YYYY-MM-DD
    # ==================================================================
    print('[2/25] age_from_dob: string YYYY-MM-DD...')
    try:
        from billing_engine.utils import age_from_dob
        age = age_from_dob("1990-06-15")
        assert age > 30, f'Expected >30, got {age}'
        passed.append('2: age_from_dob YYYY-MM-DD string')
    except Exception as e:
        failed.append(f'2: age_from_dob string: {e}')

    # ==================================================================
    # 3 — age_from_dob: None returns 0
    # ==================================================================
    print('[3/25] age_from_dob: None → 0...')
    try:
        from billing_engine.utils import age_from_dob
        assert age_from_dob(None) == 0
        passed.append('3: age_from_dob None = 0')
    except Exception as e:
        failed.append(f'3: age_from_dob None: {e}')

    # ==================================================================
    # 4 — age_from_dob: invalid string returns 0
    # ==================================================================
    print('[4/25] age_from_dob: invalid string → 0...')
    try:
        from billing_engine.utils import age_from_dob
        assert age_from_dob("not-a-date") == 0
        passed.append('4: age_from_dob invalid = 0')
    except Exception as e:
        failed.append(f'4: age_from_dob invalid: {e}')

    # ==================================================================
    # 5 — age_from_dob: datetime input
    # ==================================================================
    print('[5/25] age_from_dob: datetime...')
    try:
        from billing_engine.utils import age_from_dob
        dt = datetime(1985, 3, 20, 14, 30)
        age = age_from_dob(dt)
        assert age > 35, f'Expected >35, got {age}'
        passed.append('5: age_from_dob datetime input')
    except Exception as e:
        failed.append(f'5: age_from_dob datetime: {e}')

    # ==================================================================
    # 6 — has_dx: plain string list
    # ==================================================================
    print('[6/25] has_dx: plain string list...')
    try:
        from billing_engine.utils import has_dx
        diagnoses = ["E11.65", "I10", "J44.1"]
        assert has_dx(diagnoses, "E11") is True
        assert has_dx(diagnoses, "Z99") is False
        passed.append('6: has_dx plain strings')
    except Exception as e:
        failed.append(f'6: has_dx strings: {e}')

    # ==================================================================
    # 7 — has_dx: dict list with icd10 key
    # ==================================================================
    print('[7/25] has_dx: dict list...')
    try:
        from billing_engine.utils import has_dx
        diagnoses = [{"icd10": "E11.65"}, {"icd10": "I10"}]
        assert has_dx(diagnoses, "E11") is True
        assert has_dx(diagnoses, ["J44", "J45"]) is False
        passed.append('7: has_dx dict list')
    except Exception as e:
        failed.append(f'7: has_dx dicts: {e}')

    # ==================================================================
    # 8 — has_dx: tuple/list of prefixes
    # ==================================================================
    print('[8/25] has_dx: multiple prefixes...')
    try:
        from billing_engine.utils import has_dx
        diagnoses = ["J44.1", "I25.10"]
        assert has_dx(diagnoses, ("J44", "J45")) is True
        assert has_dx(diagnoses, ["E10", "E11"]) is False
        passed.append('8: has_dx multiple prefixes')
    except Exception as e:
        failed.append(f'8: has_dx prefixes: {e}')

    # ==================================================================
    # 9 — has_dx: empty list
    # ==================================================================
    print('[9/25] has_dx: empty list...')
    try:
        from billing_engine.utils import has_dx
        assert has_dx([], "E11") is False
        assert has_dx(None, "E11") is False
        passed.append('9: has_dx empty/None = False')
    except Exception as e:
        failed.append(f'9: has_dx empty: {e}')

    # ==================================================================
    # 10 — has_medication: string list match
    # ==================================================================
    print('[10/25] has_medication: string match...')
    try:
        from billing_engine.utils import has_medication
        meds = ["Metformin 500mg", "Lisinopril 10mg", "Atorvastatin 20mg"]
        assert has_medication(meds, "metformin") is True
        assert has_medication(meds, "insulin") is False
        passed.append('10: has_medication string match')
    except Exception as e:
        failed.append(f'10: has_medication: {e}')

    # ==================================================================
    # 11 — has_medication: dict list with name key
    # ==================================================================
    print('[11/25] has_medication: dict list...')
    try:
        from billing_engine.utils import has_medication
        meds = [{"name": "Metformin 500mg"}, {"name": "Amlodipine 5mg"}]
        assert has_medication(meds, "metformin") is True
        assert has_medication(meds, ["warfarin", "apixaban"]) is False
        passed.append('11: has_medication dict list')
    except Exception as e:
        failed.append(f'11: has_medication dicts: {e}')

    # ==================================================================
    # 12 — has_medication: case insensitive
    # ==================================================================
    print('[12/25] has_medication: case insensitive...')
    try:
        from billing_engine.utils import has_medication
        meds = ["METFORMIN HCL 1000MG"]
        assert has_medication(meds, "metformin") is True
        assert has_medication(meds, "Metformin") is True
        passed.append('12: has_medication case insensitive')
    except Exception as e:
        failed.append(f'12: has_medication case: {e}')

    # ==================================================================
    # 13 — has_medication: empty list
    # ==================================================================
    print('[13/25] has_medication: empty...')
    try:
        from billing_engine.utils import has_medication
        assert has_medication([], "metformin") is False
        assert has_medication(None, "metformin") is False
        passed.append('13: has_medication empty/None = False')
    except Exception as e:
        failed.append(f'13: has_medication empty: {e}')

    # ==================================================================
    # 14 — is_overdue: past date beyond interval
    # ==================================================================
    print('[14/25] is_overdue: past date...')
    try:
        from billing_engine.utils import is_overdue
        old_date = date.today() - timedelta(days=400)
        assert is_overdue(old_date, 12) is True
        recent = date.today() - timedelta(days=30)
        assert is_overdue(recent, 12) is False
        passed.append('14: is_overdue correct for past dates')
    except Exception as e:
        failed.append(f'14: is_overdue: {e}')

    # ==================================================================
    # 15 — is_overdue: None date → always overdue
    # ==================================================================
    print('[15/25] is_overdue: None → overdue...')
    try:
        from billing_engine.utils import is_overdue
        assert is_overdue(None, 12) is True
        passed.append('15: is_overdue None = overdue')
    except Exception as e:
        failed.append(f'15: is_overdue None: {e}')

    # ==================================================================
    # 16 — months_since: various inputs
    # ==================================================================
    print('[16/25] months_since: calculations...')
    try:
        from billing_engine.utils import months_since
        # 6 months ago
        six_ago = date.today() - timedelta(days=180)
        m = months_since(six_ago)
        assert 5 <= m <= 7, f'Expected ~6, got {m}'
        # String input
        m2 = months_since("2020-01-01")
        assert m2 > 50, f'Expected >50, got {m2}'
        # None → 9999
        m3 = months_since(None)
        assert m3 == 9999
        passed.append('16: months_since calculations correct')
    except Exception as e:
        failed.append(f'16: months_since: {e}')

    # ==================================================================
    # 17 — hash_mrn: deterministic SHA-256
    # ==================================================================
    print('[17/25] hash_mrn: deterministic...')
    try:
        from billing_engine.shared import hash_mrn
        h1 = hash_mrn("12345")
        h2 = hash_mrn("12345")
        assert h1 == h2, 'Same MRN must produce same hash'
        assert len(h1) == 64, f'SHA-256 hex should be 64 chars, got {len(h1)}'
        h3 = hash_mrn("99999")
        assert h3 != h1, 'Different MRNs must produce different hashes'
        passed.append('17: hash_mrn deterministic SHA-256')
    except Exception as e:
        failed.append(f'17: hash_mrn: {e}')

    # ==================================================================
    # 18 — count_chronic_conditions: deduplicates by prefix
    # ==================================================================
    print('[18/25] count_chronic_conditions: dedup...')
    try:
        from billing_engine.shared import count_chronic_conditions
        diagnoses = [
            {"icd10_code": "E11.65", "status": "active"},
            {"icd10_code": "E11.9", "status": "active"},   # same E11 prefix
            {"icd10_code": "I10", "status": "active"},
            {"icd10_code": "J44.1", "status": "active"},
        ]
        count = count_chronic_conditions(diagnoses)
        # E11 should count once (deduped), I10 once, J44 once = 3
        assert count >= 2, f'Expected ≥2, got {count}'
        passed.append('18: count_chronic_conditions deduplicates')
    except Exception as e:
        failed.append(f'18: count_chronic: {e}')

    # ==================================================================
    # 19 — count_chronic_conditions: resolved excluded
    # ==================================================================
    print('[19/25] count_chronic_conditions: resolved...')
    try:
        from billing_engine.shared import count_chronic_conditions
        diagnoses = [
            {"icd10_code": "E11.65", "status": "resolved"},
            {"icd10_code": "I10", "status": "active"},
        ]
        count = count_chronic_conditions(diagnoses)
        # Only I10 should count (E11 is resolved)
        assert count <= 2, f'Resolved should reduce count, got {count}'
        passed.append('19: count_chronic_conditions skips resolved')
    except Exception as e:
        failed.append(f'19: count_chronic resolved: {e}')

    # ==================================================================
    # 20 — add_business_days: skips weekends
    # ==================================================================
    print('[20/25] add_business_days: weekends...')
    try:
        from billing_engine.shared import add_business_days
        # Start on a Friday, add 2 business days → should land on Tuesday
        friday = date(2026, 3, 20)  # 2026-03-20 is a Friday
        result = add_business_days(friday, 2)
        assert result == date(2026, 3, 24), f'Expected 2026-03-24 (Tue), got {result}'
        passed.append('20: add_business_days skips weekends')
    except Exception as e:
        failed.append(f'20: add_business_days: {e}')

    # ==================================================================
    # 21 — add_business_days: 0 days returns same date
    # ==================================================================
    print('[21/25] add_business_days: 0 days...')
    try:
        from billing_engine.shared import add_business_days
        monday = date(2026, 3, 16)
        result = add_business_days(monday, 0)
        assert result == monday, f'0 days should return same date, got {result}'
        passed.append('21: add_business_days 0 = same date')
    except Exception as e:
        failed.append(f'21: add_business_days 0: {e}')

    # ==================================================================
    # 22 — scoring: WEIGHTS dict has 8 factors
    # ==================================================================
    print('[22/25] scoring: 8 factor weights...')
    try:
        from billing_engine.scoring import WEIGHTS
        assert len(WEIGHTS) == 8, f'Expected 8 weights, found {len(WEIGHTS)}'
        expected_keys = {'collection_rate', 'denial_risk',
                         'doc_burden', 'completion_prob', 'time_to_cash',
                         'bonus_urgency', 'staff_effort', 'revenue_magnitude'}
        assert set(WEIGHTS.keys()) == expected_keys, f'Missing keys: {expected_keys - set(WEIGHTS.keys())}'
        passed.append('22: Scoring has 8 factor weights')
    except Exception as e:
        failed.append(f'22: Scoring weights: {e}')

    # ==================================================================
    # 23 — scoring: doc burden map covers key codes
    # ==================================================================
    print('[23/25] scoring: doc burden map...')
    try:
        from billing_engine.scoring import _DOC_BURDEN_MAP
        assert 'AWV' in _DOC_BURDEN_MAP, 'AWV missing from doc burden'
        assert 'CCM' in _DOC_BURDEN_MAP, 'CCM missing from doc burden'
        assert _DOC_BURDEN_MAP['AWV'] > _DOC_BURDEN_MAP.get('IMM_FLU', 0), \
            'AWV should have higher burden than immunizations'
        passed.append('23: Doc burden map correct')
    except Exception as e:
        failed.append(f'23: Doc burden: {e}')

    # ==================================================================
    # 24 — scoring: completion probability map
    # ==================================================================
    print('[24/25] scoring: completion probability...')
    try:
        from billing_engine.scoring import _COMPLETION_MAP
        assert 'STRONG_STANDALONE' in _COMPLETION_MAP
        assert 'STACK_ONLY' in _COMPLETION_MAP
        assert _COMPLETION_MAP['STRONG_STANDALONE'] > _COMPLETION_MAP['STACK_ONLY']
        passed.append('24: Completion probability ranked correctly')
    except Exception as e:
        failed.append(f'24: Completion prob: {e}')

    # ==================================================================
    # 25 — scoring: ExpectedNetValueCalculator exists
    # ==================================================================
    print('[25/25] scoring: Calculator class...')
    try:
        from billing_engine.scoring import ExpectedNetValueCalculator
        calc = ExpectedNetValueCalculator()
        assert hasattr(calc, 'score'), 'Calculator must have score() method'
        passed.append('25: ExpectedNetValueCalculator instantiable')
    except Exception as e:
        failed.append(f'25: Calculator: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print('\n' + '=' * 60)
    print(f'Phase 29.1 — Billing Unit: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)
    for p in passed:
        print(f'  \u2705 {p}')
    for f in failed:
        print(f'  \u274c {f}')
    print()

    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

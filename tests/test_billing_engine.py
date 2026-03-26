"""
CareCompanion -- Billing Engine Tests
tests/test_billing_engine.py

Pytest-based tests for the BillingCaptureEngine and all 27 detectors.

Usage:
    venv\\Scripts\\python.exe -m pytest tests/test_billing_engine.py -v
"""

import pytest
from datetime import date, timedelta


# ======================================================================
# Engine Initialization
# ======================================================================

class TestEngineInit:
    """Tests for BillingCaptureEngine initialization."""

    def test_engine_initializes(self, billing_engine):
        """Engine creates successfully with all detectors."""
        assert billing_engine is not None

    def test_engine_has_27_detectors(self, billing_engine):
        """Engine discovers all 27 detector classes."""
        assert len(billing_engine._detectors) == 27, (
            f'Expected 27 detectors, got {len(billing_engine._detectors)}: '
            f'{[d.CATEGORY for d in billing_engine._detectors]}'
        )

    def test_all_detectors_have_category(self, billing_engine):
        """Every detector has a non-empty CATEGORY."""
        for detector in billing_engine._detectors:
            assert detector.CATEGORY, (
                f'{detector.__class__.__name__} has empty CATEGORY'
            )

    def test_no_duplicate_categories(self, billing_engine):
        """No two detectors share the same CATEGORY."""
        categories = [d.CATEGORY for d in billing_engine._detectors]
        assert len(categories) == len(set(categories)), (
            f'Duplicate categories: {[c for c in categories if categories.count(c) > 1]}'
        )


# ======================================================================
# Engine Evaluation
# ======================================================================

class TestEngineEvaluation:
    """Tests for the evaluate() pipeline."""

    def test_evaluate_returns_list(self, billing_engine, sample_patient_data):
        """evaluate() returns a list."""
        result = billing_engine.evaluate(sample_patient_data)
        assert isinstance(result, list)

    def test_evaluate_returns_billing_opportunities(self, billing_engine, sample_patient_data):
        """evaluate() returns BillingOpportunity objects."""
        from models.billing import BillingOpportunity
        result = billing_engine.evaluate(sample_patient_data)
        for opp in result:
            assert isinstance(opp, BillingOpportunity)

    def test_evaluate_no_duplicate_codes(self, billing_engine, sample_patient_data):
        """evaluate() deduplicates by opportunity_code."""
        result = billing_engine.evaluate(sample_patient_data)
        codes = [opp.opportunity_code for opp in result if opp.opportunity_code]
        assert len(codes) == len(set(codes)), (
            f'Duplicate codes: {[c for c in codes if codes.count(c) > 1]}'
        )

    def test_evaluate_results_sorted_by_priority(self, billing_engine, sample_patient_data):
        """Results are sorted by priority (critical > high > medium > low)."""
        result = billing_engine.evaluate(sample_patient_data)
        if len(result) < 2:
            pytest.skip('Not enough results to verify sort order')

        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        priorities = [priority_order.get(opp.priority, 3) for opp in result]
        assert priorities == sorted(priorities)

    def test_evaluate_handles_empty_patient(self, billing_engine):
        """evaluate() handles patient with minimal data."""
        minimal = {
            'mrn': '00000',
            'age': 30,
            'sex': 'M',
            'insurer': 'Unknown',
            'insurer_type': 'commercial',
            'diagnoses': [],
            'medications': [],
            'user_id': 1,
        }
        result = billing_engine.evaluate(minimal)
        assert isinstance(result, list)

    def test_disabled_category_skipped(self, billing_engine, sample_patient_data):
        """Disabled detector categories are not evaluated."""
        # Disable a known category via patient preferences
        sample_patient_data['billing_categories_enabled'] = {'awv': False}
        result = billing_engine.evaluate(sample_patient_data)
        awv_codes = [opp for opp in result if opp.category == 'awv']
        assert len(awv_codes) == 0, 'AWV should be suppressed when disabled'


# ======================================================================
# False Positive Control
# ======================================================================

class TestFalsePositiveControl:
    """MRN 90029 -- healthy patient with acute URI should NOT trigger chronic codes."""

    def test_healthy_patient_no_ccm(self, billing_engine):
        """Healthy patient should not trigger CCM."""
        patient = {
            'mrn': '90029',
            'patient_name': 'Jessica Campbell',
            'age': 27, 'sex': 'F',
            'insurer': 'Aetna',
            'insurer_type': 'commercial',
            'diagnoses': [{'code': 'J06.9', 'description': 'Acute URI'}],
            'medications': [],
            'vitals': {'bp_systolic': 118, 'bp_diastolic': 72, 'bmi': 22.0},
            'ccm_enrolled': False,
            'ccm_minutes_this_month': 0,
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        ccm = [o for o in result if o.category == 'ccm']
        assert len(ccm) == 0, 'Healthy patient should not get CCM opportunity'

    def test_healthy_patient_no_bhi(self, billing_engine):
        """Healthy patient should not trigger BHI."""
        patient = {
            'mrn': '90029',
            'patient_name': 'Jessica Campbell',
            'age': 27, 'sex': 'F',
            'insurer': 'Aetna',
            'insurer_type': 'commercial',
            'diagnoses': [{'code': 'J06.9', 'description': 'Acute URI'}],
            'medications': [],
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        bhi = [o for o in result if o.category == 'bhi']
        assert len(bhi) == 0, 'Healthy patient should not get BHI opportunity'


# ======================================================================
# Individual Detector Tests
# ======================================================================

class TestG2211Detector:
    """G2211 add-on code detector."""

    def test_g2211_fires_for_longitudinal_visit(self, billing_engine):
        """G2211 fires for established patient with ongoing relationship."""
        patient = {
            'mrn': '90031',
            'patient_name': 'Betty Stewart',
            'age': 73, 'sex': 'F',
            'insurer': 'Humana', 'insurer_type': 'medicare_advantage',
            'diagnoses': [
                {'icd10_code': 'I10', 'diagnosis_name': 'HTN', 'status': 'active'},
                {'icd10_code': 'F41.1', 'diagnosis_name': 'Anxiety', 'status': 'active'},
            ],
            'medications': [{'name': 'lisinopril'}, {'name': 'buspirone'}],
            'visit_type': 'office',
            'last_visit_date': (date.today() - timedelta(days=60)).isoformat(),
            'prior_encounters_count': 1,
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        g2211 = [o for o in result if o.category == 'g2211']
        assert len(g2211) > 0, 'G2211 should fire for longitudinal visit'


class TestAWVDetector:
    """Annual Wellness Visit detector."""

    def test_awv_fires_for_medicare_no_recent_awv(self, billing_engine):
        """AWV fires for Medicare patient without recent AWV."""
        patient = {
            'mrn': '90001',
            'patient_name': 'Margaret Wilson',
            'age': 67, 'sex': 'F',
            'insurer': 'Medicare', 'insurer_type': 'medicare',
            'diagnoses': [{'icd10_code': 'I10', 'diagnosis_name': 'HTN', 'status': 'active'}],
            'medications': [],
            'awv_history': {'last_awv_date': None},
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        awv = [o for o in result if o.category == 'awv']
        assert len(awv) > 0, 'AWV should fire for Medicare without recent AWV'

    def test_awv_does_not_fire_for_recent_awv(self, billing_engine):
        """AWV does not fire if done within the year."""
        patient = {
            'mrn': '90001',
            'patient_name': 'Margaret Wilson',
            'age': 67, 'sex': 'F',
            'insurer': 'Medicare', 'insurer_type': 'medicare',
            'diagnoses': [{'icd10_code': 'I10', 'diagnosis_name': 'HTN', 'status': 'active'}],
            'medications': [],
            'awv_history': {
                'last_awv_date': (date.today() - timedelta(days=30)).isoformat(),
            },
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        awv = [o for o in result if o.category == 'awv']
        assert len(awv) == 0, 'AWV should not fire with recent AWV'


class TestTCMDetector:
    """Transitional Care Management detector."""

    def test_tcm_fires_post_discharge(self, billing_engine):
        """TCM fires for patient within 30-day post-discharge window."""
        patient = {
            'mrn': '90018',
            'patient_name': 'Matthew Hall',
            'age': 70, 'sex': 'M',
            'insurer': 'Medicare', 'insurer_type': 'medicare',
            'diagnoses': [
                {'icd10_code': 'I50.9', 'diagnosis_name': 'CHF', 'status': 'active'},
                {'icd10_code': 'E11.9', 'diagnosis_name': 'T2DM', 'status': 'active'},
            ],
            'medications': [],
            'discharge_date': (date.today() - timedelta(days=5)).isoformat(),
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        tcm = [o for o in result if o.category == 'tcm']
        assert len(tcm) > 0, 'TCM should fire within 30 days of discharge'

    def test_tcm_does_not_fire_beyond_window(self, billing_engine):
        """TCM does not fire if discharge was > 30 days ago."""
        patient = {
            'mrn': '90018',
            'patient_name': 'Matthew Hall',
            'age': 70, 'sex': 'M',
            'insurer': 'Medicare', 'insurer_type': 'medicare',
            'diagnoses': [{'icd10_code': 'I50.9', 'diagnosis_name': 'CHF', 'status': 'active'}],
            'medications': [],
            'discharge_date': (date.today() - timedelta(days=60)).isoformat(),
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        tcm = [o for o in result if o.category == 'tcm']
        assert len(tcm) == 0, 'TCM should not fire beyond 30-day window'


class TestCCMDetector:
    """Chronic Care Management detector."""

    def test_ccm_fires_for_2plus_chronic(self, billing_engine):
        """CCM fires for patient with 2+ chronic conditions."""
        patient = {
            'mrn': '90001',
            'patient_name': 'Margaret Wilson',
            'age': 67, 'sex': 'F',
            'insurer': 'Medicare', 'insurer_type': 'medicare',
            'diagnoses': [
                {'icd10_code': 'I10', 'diagnosis_name': 'HTN', 'status': 'active'},
                {'icd10_code': 'E11.9', 'diagnosis_name': 'T2DM', 'status': 'active'},
                {'icd10_code': 'E78.5', 'diagnosis_name': 'HLD', 'status': 'active'},
            ],
            'medications': [],
            'ccm_minutes_this_month': 25,
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        ccm = [o for o in result if o.category == 'ccm']
        assert len(ccm) > 0, 'CCM should fire for patient with 2+ chronic conditions'


class TestTobaccoDetector:
    """Tobacco cessation detector."""

    def test_tobacco_fires_for_smoker(self, billing_engine):
        """Tobacco cessation fires for active smoker."""
        patient = {
            'mrn': '90002',
            'patient_name': 'Robert Thompson',
            'age': 65, 'sex': 'M',
            'insurer': 'Medicare', 'insurer_type': 'medicare',
            'diagnoses': [
                {'icd10_code': 'F17.210', 'diagnosis_name': 'Nicotine dependence, cigarettes', 'status': 'active'},
            ],
            'medications': [],
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        tobacco = [o for o in result if o.category == 'tobacco_cessation']
        assert len(tobacco) > 0, 'Tobacco should fire for active smoker'


class TestSDOHDetector:
    """Social Determinants of Health detector."""

    def test_sdoh_fires_for_ipv_screening(self, billing_engine):
        """SDOH fires IPV screening for woman of reproductive age at preventive visit."""
        patient = {
            'mrn': '90026',
            'patient_name': 'Anna Mitchell',
            'age': 30, 'sex': 'F',
            'insurer': 'Blue Cross', 'insurer_type': 'commercial',
            'diagnoses': [],
            'medications': [],
            'visit_type': 'preventive',
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        sdoh = [o for o in result if o.category == 'sdoh']
        assert len(sdoh) > 0, 'SDOH should fire IPV screening for woman at preventive visit'


class TestPediatricDetector:
    """Pediatric-specific detector."""

    def test_pediatric_fires_for_child(self, billing_engine):
        """Pediatric detector fires for patient under 18."""
        patient = {
            'mrn': '90014',
            'patient_name': 'Christopher Lee',
            'age': 10, 'sex': 'M',
            'insurer': 'Virginia Medicaid', 'insurer_type': 'medicaid',
            'diagnoses': [
                {'icd10_code': 'F90.0', 'diagnosis_name': 'ADHD', 'status': 'active'},
                {'icd10_code': 'J45.20', 'diagnosis_name': 'Mild persistent asthma', 'status': 'active'},
            ],
            'medications': [],
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        peds = [o for o in result if o.category == 'pediatric']
        assert len(peds) > 0, 'Pediatric should fire for child patient'


class TestObesityDetector:
    """Obesity counseling detector."""

    def test_obesity_fires_for_bmi_over_30(self, billing_engine):
        """Obesity fires for patient with obesity diagnosis."""
        patient = {
            'mrn': '90003',
            'patient_name': 'Maria Garcia',
            'age': 35, 'sex': 'F',
            'insurer': 'Aetna', 'insurer_type': 'commercial',
            'diagnoses': [
                {'icd10_code': 'E66.01', 'diagnosis_name': 'Morbid obesity', 'status': 'active'},
            ],
            'medications': [],
            'vitals': {'bmi': 42.0},
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        obesity = [o for o in result if o.category == 'obesity_nutrition']
        assert len(obesity) > 0, 'Obesity should fire for BMI > 30'


class TestAlcoholDetector:
    """Alcohol screening detector."""

    def test_alcohol_fires_for_aud(self, billing_engine):
        """Alcohol screening fires for patient with AUD diagnosis."""
        patient = {
            'mrn': '90008',
            'patient_name': 'Michael Johnson',
            'patient_age': 50, 'sex': 'M',
            'insurer': 'United', 'insurer_type': 'commercial',
            'diagnoses': [
                {'icd10_code': 'F10.20', 'diagnosis_name': 'Alcohol use disorder', 'status': 'active'},
            ],
            'medications': [],
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        alcohol = [o for o in result if o.category == 'alcohol_screening']
        assert len(alcohol) > 0, 'Alcohol should fire for AUD patient'


class TestCognitiveDetector:
    """Cognitive assessment detector."""

    def test_cognitive_fires_for_dementia(self, billing_engine):
        """Cognitive assessment fires for patient with dementia."""
        patient = {
            'mrn': '90028',
            'patient_name': 'Kenneth Phillips',
            'patient_age': 82, 'sex': 'M',
            'insurer': 'Medicare', 'insurer_type': 'medicare',
            'diagnoses': [
                {'icd10_code': 'G30.9', 'diagnosis_name': "Alzheimer's disease", 'status': 'active'},
            ],
            'medications': [],
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        cognitive = [o for o in result if o.category == 'cognitive_assessment']
        assert len(cognitive) > 0, 'Cognitive should fire for Alzheimer patient'


class TestSTIDetector:
    """STI screening detector."""

    def test_sti_fires_for_at_risk_patient(self, billing_engine):
        """STI screening fires for eligible adult (Hep C screening)."""
        patient = {
            'mrn': '90027',
            'patient_name': 'Angela Turner',
            'patient_age': 30, 'patient_sex': 'F',
            'insurer': 'Virginia Medicaid', 'insurer_type': 'medicaid',
            'diagnoses': [],
            'medications': [],
            'last_hep_c_date': None,
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        sti = [o for o in result if o.category == 'sti_screening']
        assert len(sti) > 0, 'STI should fire Hep C screening for eligible adult'


class TestBHIDetector:
    """Behavioral Health Integration detector."""

    def test_bhi_fires_for_depression(self, billing_engine):
        """BHI fires for patient with depression diagnosis."""
        patient = {
            'mrn': '90005',
            'patient_name': 'Patricia Davis',
            'age': 70, 'sex': 'F',
            'insurer': 'Humana', 'insurer_type': 'medicare_advantage',
            'diagnoses': [
                {'icd10_code': 'F32.1', 'diagnosis_name': 'MDD, single episode, moderate', 'status': 'active'},
                {'icd10_code': 'I50.9', 'diagnosis_name': 'CHF', 'status': 'active'},
            ],
            'medications': [],
            'user_id': 1,
        }
        result = billing_engine.evaluate(patient)
        bhi = [o for o in result if o.category == 'bhi']
        assert len(bhi) > 0, 'BHI should fire for patient with depression'

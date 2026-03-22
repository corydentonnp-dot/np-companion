"""
tests/test_demo_mode.py — Phase 30.9
15 tests verifying demo-mode seed data integrity and billing walkthrough.
"""

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['FLASK_ENV'] = 'testing'

from app import create_app

app = create_app()
passed = []
failed = []


def _hash(mrn):
    return hashlib.sha256(str(mrn).encode()).hexdigest()


def run_tests():
    with app.app_context():
        from models import db
        from models.patient import PatientRecord, PatientDiagnosis, PatientMedication
        from models.bonus import BonusTracker
        from models.tcm import TCMWatchEntry
        from models.ccm import CCMEnrollment
        from models.monitoring import MonitoringSchedule
        from models.immunization import ImmunizationSeries
        from models.billing import DocumentationPhrase
        from models.user import User
        from billing_engine.engine import BillingCaptureEngine

        user = User.query.filter_by(is_active_account=True).first()
        uid = user.id

        # ------------------------------------------------------------------
        # 1. All 5 demo patients exist
        # ------------------------------------------------------------------
        try:
            demo_mrns = ['DEMO001', 'DEMO002', 'DEMO003', 'DEMO004', 'DEMO005']
            pts = PatientRecord.query.filter(
                PatientRecord.user_id == uid,
                PatientRecord.mrn.in_(demo_mrns)
            ).all()
            assert len(pts) == 5, f'Expected 5 demo patients, got {len(pts)}'
            passed.append('[1/15] 5 demo patients present')
        except Exception as e:
            failed.append(f'[1/15] 5 demo patients present — {e}')

        # ------------------------------------------------------------------
        # 2. DEMO001 has 4 diagnoses
        # ------------------------------------------------------------------
        try:
            dx = PatientDiagnosis.query.filter_by(user_id=uid, mrn='DEMO001').all()
            assert len(dx) >= 4, f'DEMO001 has {len(dx)} diagnoses, expected >=4'
            codes = {d.icd10_code for d in dx}
            assert 'E11.65' in codes, 'Missing E11.65'
            assert 'N18.3' in codes, 'Missing N18.3'
            passed.append('[2/15] DEMO001 diagnoses')
        except Exception as e:
            failed.append(f'[2/15] DEMO001 diagnoses — {e}')

        # ------------------------------------------------------------------
        # 3. DEMO001 has medications
        # ------------------------------------------------------------------
        try:
            meds = PatientMedication.query.filter_by(user_id=uid, mrn='DEMO001').all()
            assert len(meds) >= 3, f'DEMO001 has {len(meds)} meds, expected >=3'
            names = {m.drug_name for m in meds}
            assert any('Metformin' in n for n in names), 'Missing Metformin'
            passed.append('[3/15] DEMO001 medications')
        except Exception as e:
            failed.append(f'[3/15] DEMO001 medications — {e}')

        # ------------------------------------------------------------------
        # 4. Payer types are diverse
        # ------------------------------------------------------------------
        try:
            payers = {p.insurer_type for p in pts}
            assert 'medicare' in payers, 'No medicare'
            assert 'commercial' in payers, 'No commercial'
            assert 'medicaid' in payers, 'No medicaid'
            passed.append('[4/15] Diverse payer types')
        except Exception as e:
            failed.append(f'[4/15] Diverse payer types — {e}')

        # ------------------------------------------------------------------
        # 5. BonusTracker has Q1 2026 receipts
        # ------------------------------------------------------------------
        try:
            bt = BonusTracker.query.filter_by(user_id=uid).first()
            assert bt is not None, 'No BonusTracker'
            receipts = bt.get_receipts()
            assert '2026-01' in receipts, 'Missing Jan 2026'
            assert '2026-02' in receipts, 'Missing Feb 2026'
            assert '2026-03' in receipts, 'Missing Mar 2026'
            total = receipts['2026-01'] + receipts['2026-02'] + receipts['2026-03']
            assert total >= 5000, f'Q1 total only ${total}'
            passed.append('[5/15] BonusTracker Q1 2026')
        except Exception as e:
            failed.append(f'[5/15] BonusTracker Q1 2026 — {e}')

        # ------------------------------------------------------------------
        # 6. TCM watch entry exists for DEMO002
        # ------------------------------------------------------------------
        try:
            tcm = TCMWatchEntry.query.filter_by(
                patient_mrn_hash=_hash('DEMO002'), user_id=uid
            ).first()
            assert tcm is not None, 'No TCM entry for DEMO002'
            assert tcm.status == 'active', f'TCM status={tcm.status}'
            assert tcm.discharge_facility, 'Missing discharge facility'
            passed.append('[6/15] TCM watch entry DEMO002')
        except Exception as e:
            failed.append(f'[6/15] TCM watch entry DEMO002 — {e}')

        # ------------------------------------------------------------------
        # 7. CCM registry has 5 entries (2 active, 3 pending)
        # ------------------------------------------------------------------
        try:
            ccm_all = CCMEnrollment.query.filter(
                CCMEnrollment.user_id == uid,
                CCMEnrollment.patient_mrn_hash.in_(
                    [_hash(m) for m in demo_mrns]
                )
            ).all()
            assert len(ccm_all) >= 5, f'CCM entries: {len(ccm_all)}'
            statuses = [c.status for c in ccm_all]
            assert statuses.count('active') >= 2, f'Active={statuses.count("active")}'
            assert statuses.count('pending') >= 3, f'Pending={statuses.count("pending")}'
            passed.append('[7/15] CCM registry (2 active, 3 pending)')
        except Exception as e:
            failed.append(f'[7/15] CCM registry — {e}')

        # ------------------------------------------------------------------
        # 8. Phrase library ≥20 entries
        # ------------------------------------------------------------------
        try:
            count = DocumentationPhrase.query.count()
            assert count >= 20, f'Phrase library has only {count}'
            passed.append(f'[8/15] Phrase library ({count} entries)')
        except Exception as e:
            failed.append(f'[8/15] Phrase library — {e}')

        # ------------------------------------------------------------------
        # 9. MonitoringSchedule has overdue + active entries
        # ------------------------------------------------------------------
        try:
            schedules = MonitoringSchedule.query.filter(
                MonitoringSchedule.user_id == uid,
                MonitoringSchedule.patient_mrn_hash.in_(
                    [_hash(m) for m in demo_mrns]
                )
            ).all()
            assert len(schedules) >= 3, f'Only {len(schedules)} monitoring entries'
            statuses = {s.status for s in schedules}
            assert 'overdue' in statuses, 'No overdue entries'
            assert 'active' in statuses, 'No active entries'
            passed.append('[9/15] MonitoringSchedule (overdue + active)')
        except Exception as e:
            failed.append(f'[9/15] MonitoringSchedule — {e}')

        # ------------------------------------------------------------------
        # 10. ImmunizationSeries has incomplete Shingrix
        # ------------------------------------------------------------------
        try:
            shingrix = ImmunizationSeries.query.filter_by(
                patient_mrn_hash=_hash('DEMO001'),
                vaccine_group='Shingrix', user_id=uid
            ).first()
            assert shingrix is not None, 'No Shingrix entry'
            assert shingrix.dose_number < shingrix.total_doses, 'Shingrix complete?!'
            assert shingrix.series_status == 'in_progress', f'Status={shingrix.series_status}'
            passed.append('[10/15] ImmunizationSeries Shingrix incomplete')
        except Exception as e:
            failed.append(f'[10/15] ImmunizationSeries Shingrix — {e}')

        # ------------------------------------------------------------------
        # 11. ImmunizationSeries has overdue flu
        # ------------------------------------------------------------------
        try:
            flu = ImmunizationSeries.query.filter_by(
                patient_mrn_hash=_hash('DEMO002'),
                vaccine_group='Influenza', user_id=uid
            ).first()
            assert flu is not None, 'No flu entry'
            assert flu.series_status == 'overdue', f'Status={flu.series_status}'
            passed.append('[11/15] ImmunizationSeries Influenza overdue')
        except Exception as e:
            failed.append(f'[11/15] ImmunizationSeries Influenza — {e}')

        # ------------------------------------------------------------------
        # 12. End-to-end: DEMO001 (Medicare) generates billing opps
        # ------------------------------------------------------------------
        try:
            pr = PatientRecord.query.filter_by(user_id=uid, mrn='DEMO001').first()
            dx = PatientDiagnosis.query.filter_by(user_id=uid, mrn='DEMO001').all()
            meds = PatientMedication.query.filter_by(user_id=uid, mrn='DEMO001').all()
            pd = {
                'mrn': 'DEMO001',
                'patient_name': pr.patient_name,
                'patient_dob': pr.patient_dob,
                'patient_sex': pr.patient_sex,
                'insurer_type': pr.insurer_type,
                'diagnoses': [{'icd10_code': d.icd10_code, 'diagnosis_name': d.diagnosis_name, 'status': d.status} for d in dx],
                'medications': [{'drug_name': m.drug_name, 'status': m.status} for m in meds],
                'awv_history': {'last_awv_date': None},
            }
            engine = BillingCaptureEngine(db=db)
            results = engine.evaluate(pd)
            assert len(results) >= 3, f'Only {len(results)} opportunities for DEMO001'
            cats = {getattr(r, 'category', '') for r in results}
            assert 'ccm' in cats or 'awv' in cats, f'Missing expected categories, got {cats}'
            passed.append(f'[12/15] DEMO001 engine => {len(results)} opps')
        except Exception as e:
            failed.append(f'[12/15] DEMO001 engine — {e}')

        # ------------------------------------------------------------------
        # 13. End-to-end: DEMO003 (Commercial) gets tobacco cessation
        # ------------------------------------------------------------------
        try:
            pr = PatientRecord.query.filter_by(user_id=uid, mrn='DEMO003').first()
            dx = PatientDiagnosis.query.filter_by(user_id=uid, mrn='DEMO003').all()
            meds = PatientMedication.query.filter_by(user_id=uid, mrn='DEMO003').all()
            pd = {
                'mrn': 'DEMO003',
                'patient_name': pr.patient_name,
                'patient_dob': pr.patient_dob,
                'patient_sex': pr.patient_sex,
                'insurer_type': pr.insurer_type,
                'diagnoses': [{'icd10_code': d.icd10_code, 'diagnosis_name': d.diagnosis_name, 'status': d.status} for d in dx],
                'medications': [{'drug_name': m.drug_name, 'status': m.status} for m in meds],
                'awv_history': {'last_awv_date': None},
            }
            engine = BillingCaptureEngine(db=db)
            results = engine.evaluate(pd)
            cats = {getattr(r, 'category', '') for r in results}
            assert 'tobacco_cessation' in cats, f'No tobacco cessation, got {cats}'
            passed.append(f'[13/15] DEMO003 tobacco cessation detected')
        except Exception as e:
            failed.append(f'[13/15] DEMO003 tobacco — {e}')

        # ------------------------------------------------------------------
        # 14. Route test: /billing/log loads with demo data
        # ------------------------------------------------------------------
        try:
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(uid)
                resp = client.get('/billing/log')
                assert resp.status_code == 200, f'Status {resp.status_code}'
                passed.append('[14/15] /billing/log loads')
        except Exception as e:
            failed.append(f'[14/15] /billing/log — {e}')

        # ------------------------------------------------------------------
        # 15. Seed migration is idempotent (dry run)
        # ------------------------------------------------------------------
        try:
            pre_patients = PatientRecord.query.filter(
                PatientRecord.mrn.in_(demo_mrns)
            ).count()
            pre_ccm = CCMEnrollment.query.filter(
                CCMEnrollment.patient_mrn_hash.in_(
                    [_hash(m) for m in demo_mrns]
                )
            ).count()

            # Re-run migration
            from migrations.migrate_seed_demo_data import run_migration
            run_migration(app, db)

            post_patients = PatientRecord.query.filter(
                PatientRecord.mrn.in_(demo_mrns)
            ).count()
            post_ccm = CCMEnrollment.query.filter(
                CCMEnrollment.patient_mrn_hash.in_(
                    [_hash(m) for m in demo_mrns]
                )
            ).count()

            assert pre_patients == post_patients, f'Patients changed: {pre_patients} -> {post_patients}'
            assert pre_ccm == post_ccm, f'CCM changed: {pre_ccm} -> {post_ccm}'
            passed.append('[15/15] Seed idempotency verified')
        except Exception as e:
            failed.append(f'[15/15] Seed idempotency — {e}')

    # Report
    print(f'\n=== Demo Mode Tests: {len(passed)} passed, {len(failed)} failed ===')
    for p in passed:
        print(f'  PASS {p}')
    for f in failed:
        print(f'  FAIL {f}')
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

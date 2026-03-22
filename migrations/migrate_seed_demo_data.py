"""
Migration: Seed Demo Mode Data

Phase 30.1-30.7 — Seeds 5 demo patients with clinical data,
BonusTracker Q1 2026 receipts, TCM watch entry with deadline alert,
CCM registry entries, MonitoringSchedule records, and ImmunizationSeries.

Idempotent: all seeds use upsert logic (check before insert).

Usage:
    venv\\Scripts\\python.exe migrations/migrate_seed_demo_data.py
"""

import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _add_business_days(start, days):
    """Add business days (skip weekends)."""
    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


# ------------------------------------------------------------------
# Demo patient definitions
# ------------------------------------------------------------------

DEMO_PATIENTS = [
    {
        'mrn': 'DEMO001', 'name': 'Martha Johnson', 'dob': '1958-03-15',
        'sex': 'F', 'insurer': 'medicare',
        'diagnoses': [
            ('I10', 'Essential hypertension', 'chronic'),
            ('E11.65', 'Type 2 diabetes with hyperglycemia', 'chronic'),
            ('N18.3', 'Chronic kidney disease, stage 3', 'chronic'),
            ('E78.5', 'Hyperlipidemia, unspecified', 'chronic'),
        ],
        'medications': [
            ('Lisinopril 20mg', 'daily', 'active'),
            ('Metformin 1000mg', 'twice daily', 'active'),
            ('Atorvastatin 40mg', 'daily', 'active'),
        ],
    },
    {
        'mrn': 'DEMO002', 'name': 'Robert Williams', 'dob': '1954-07-22',
        'sex': 'M', 'insurer': 'medicare',
        'diagnoses': [
            ('I25.10', 'Coronary artery disease', 'chronic'),
            ('I50.22', 'Chronic systolic heart failure', 'chronic'),
            ('J44.1', 'COPD with acute exacerbation', 'chronic'),
            ('F33.1', 'Major depressive disorder, recurrent', 'chronic'),
        ],
        'medications': [
            ('Metoprolol Succinate 50mg', 'daily', 'active'),
            ('Entresto 97/103mg', 'twice daily', 'active'),
            ('Sertraline 100mg', 'daily', 'active'),
            ('Tiotropium 18mcg', 'daily', 'active'),
        ],
    },
    {
        'mrn': 'DEMO003', 'name': 'Jessica Garcia', 'dob': '1982-11-08',
        'sex': 'F', 'insurer': 'commercial',
        'diagnoses': [
            ('E66.01', 'Morbid obesity due to excess calories', 'chronic'),
            ('F41.1', 'Generalized anxiety disorder', 'chronic'),
            ('F17.210', 'Nicotine dependence, cigarettes', 'chronic'),
        ],
        'medications': [
            ('Buspirone 10mg', 'twice daily', 'active'),
        ],
    },
    {
        'mrn': 'DEMO004', 'name': 'Maria Lopez', 'dob': '1998-04-30',
        'sex': 'F', 'insurer': 'medicaid',
        'diagnoses': [
            ('F90.0', 'ADHD, predominantly inattentive', 'chronic'),
            ('O24.410', 'Gestational diabetes, first trimester', 'acute'),
        ],
        'medications': [
            ('Adderall 20mg', 'daily', 'active'),
        ],
    },
    {
        'mrn': 'DEMO005', 'name': 'James Brown', 'dob': '1971-01-19',
        'sex': 'M', 'insurer': 'unknown',
        'diagnoses': [
            ('I10', 'Essential hypertension', 'chronic'),
            ('R73.09', 'Other abnormal glucose (pre-diabetes)', 'chronic'),
            ('F17.210', 'Nicotine dependence, cigarettes', 'chronic'),
        ],
        'medications': [
            ('Amlodipine 5mg', 'daily', 'active'),
        ],
    },
]


def run_migration(app, db):
    """Seed demo data — idempotent."""
    import hashlib
    from models.patient import (
        PatientRecord, PatientDiagnosis, PatientMedication,
    )
    from models.bonus import BonusTracker
    from models.tcm import TCMWatchEntry
    from models.ccm import CCMEnrollment
    from models.monitoring import MonitoringSchedule
    from models.immunization import ImmunizationSeries
    from models.user import User

    user = User.query.filter_by(is_active_account=True).order_by(User.id.asc()).first()
    if not user:
        print('  No active user — cannot seed demo data')
        return
    uid = user.id

    def _hash(mrn):
        return hashlib.sha256(str(mrn).encode()).hexdigest()

    today = date.today()
    seeded = 0

    # ------------------------------------------------------------------
    # 30.1: 5 demo patients with clinical data
    # ------------------------------------------------------------------
    for p in DEMO_PATIENTS:
        mrn = p['mrn']
        existing = PatientRecord.query.filter_by(user_id=uid, mrn=mrn).first()
        if not existing:
            rec = PatientRecord(
                user_id=uid, mrn=mrn, patient_name=p['name'],
                patient_dob=p['dob'], patient_sex=p['sex'],
                insurer_type=p['insurer'],
            )
            db.session.add(rec)
            seeded += 1

        # Seed diagnoses
        for code, name, cat in p['diagnoses']:
            exists = PatientDiagnosis.query.filter_by(
                user_id=uid, mrn=mrn, icd10_code=code
            ).first()
            if not exists:
                db.session.add(PatientDiagnosis(
                    user_id=uid, mrn=mrn, diagnosis_name=name,
                    icd10_code=code, status='active', diagnosis_category=cat,
                ))

        # Seed medications
        for drug, freq, status in p['medications']:
            exists = PatientMedication.query.filter_by(
                user_id=uid, mrn=mrn, drug_name=drug
            ).first()
            if not exists:
                db.session.add(PatientMedication(
                    user_id=uid, mrn=mrn, drug_name=drug,
                    frequency=freq, status=status,
                ))

    db.session.commit()
    print(f'  30.1: Seeded {seeded} new demo patients (5 total target)')

    # ------------------------------------------------------------------
    # 30.2: BonusTracker — Q1 2026 receipts, ~$99K deficit
    # ------------------------------------------------------------------
    bt = BonusTracker.query.filter_by(user_id=uid).first()
    if bt:
        receipts = bt.get_receipts()
        if '2026-01' not in receipts:
            receipts['2026-01'] = 1800.0
            receipts['2026-02'] = 2100.0
            receipts['2026-03'] = 2100.0
            bt.monthly_receipts = json.dumps(receipts)
            db.session.commit()
            print(f'  30.2: Updated BonusTracker with Q1 2026 receipts ($6K)')
        else:
            print(f'  30.2: BonusTracker Q1 receipts already present')
    else:
        bt = BonusTracker(
            user_id=uid,
            provider_name=user.username or 'Demo Provider',
            base_salary=115000.0,
            quarterly_threshold=105000.0,
            bonus_multiplier=0.25,
            monthly_receipts=json.dumps({
                '2026-01': 1800.0,
                '2026-02': 2100.0,
                '2026-03': 2100.0,
            }),
        )
        db.session.add(bt)
        db.session.commit()
        print(f'  30.2: Created BonusTracker with Q1 2026 receipts ($6K)')

    # ------------------------------------------------------------------
    # 30.3: TCM watch entry — "2-day contact deadline TODAY"
    # ------------------------------------------------------------------
    mrn_hash_demo2 = _hash('DEMO002')
    existing_tcm = TCMWatchEntry.query.filter_by(
        patient_mrn_hash=mrn_hash_demo2, user_id=uid, status='active'
    ).first()
    if not existing_tcm:
        discharge = today - timedelta(days=1)
        tcm = TCMWatchEntry(
            patient_mrn_hash=mrn_hash_demo2,
            user_id=uid,
            discharge_date=discharge,
            discharge_facility='General Hospital',
            two_day_deadline=_add_business_days(discharge, 2),
            tcm_code_eligible='99495',
            status='active',
        )
        db.session.add(tcm)
        db.session.commit()
        print(f'  30.3: Created TCM watch entry (deadline: {tcm.two_day_deadline})')
    else:
        print(f'  30.3: TCM watch entry already exists')

    # ------------------------------------------------------------------
    # 30.4: CCM registry — 5 eligible (2 enrolled, 3 not)
    # ------------------------------------------------------------------
    ccm_patients = [
        ('DEMO001', 'active', today - timedelta(days=60)),   # enrolled
        ('DEMO002', 'active', today - timedelta(days=30)),   # enrolled
        ('DEMO003', 'pending', None),                         # not enrolled
        ('DEMO004', 'pending', None),                         # not enrolled
        ('DEMO005', 'pending', None),                         # not enrolled
    ]
    ccm_seeded = 0
    for mrn, status, enroll_date in ccm_patients:
        h = _hash(mrn)
        existing = CCMEnrollment.query.filter_by(
            patient_mrn_hash=h, user_id=uid
        ).first()
        if not existing:
            conds = []
            for p in DEMO_PATIENTS:
                if p['mrn'] == mrn:
                    conds = [{'code': c, 'description': n} for c, n, _ in p['diagnoses']
                             if _ == 'chronic']
            ce = CCMEnrollment(
                patient_mrn_hash=h, user_id=uid,
                enrollment_date=enroll_date,
                consent_date=enroll_date,
                consent_method='verbal' if enroll_date else None,
                qualifying_conditions=json.dumps(conds),
                status=status,
            )
            db.session.add(ce)
            ccm_seeded += 1
    db.session.commit()
    print(f'  30.4: Seeded {ccm_seeded} CCM enrollment entries')

    # ------------------------------------------------------------------
    # 30.5: Phrase library — check count (already seeded by seed_documentation_phrases)
    # ------------------------------------------------------------------
    from models.billing import DocumentationPhrase
    phrase_count = DocumentationPhrase.query.count()
    if phrase_count >= 20:
        print(f'  30.5: Phrase library already has {phrase_count} entries')
    else:
        print(f'  30.5: Phrase library has {phrase_count} entries (run seed_documentation_phrases.py for full set)')

    # ------------------------------------------------------------------
    # 30.6: MonitoringSchedule — overdue + due-soon + current
    # ------------------------------------------------------------------
    schedules = [
        # Overdue: A1c for diabetes patient
        (_hash('DEMO001'), 'A1C', '83036', 'Hemoglobin A1c',
         'Metformin 1000mg', 'E11.65', today - timedelta(days=30), 'overdue'),
        # Due soon: UACR for CKD patient
        (_hash('DEMO001'), 'UACR', '82043', 'Urine albumin-creatinine ratio',
         'Lisinopril 20mg', 'N18.3', today + timedelta(days=7), 'active'),
        # Current: Lipid panel
        (_hash('DEMO001'), 'LIPID', '80061', 'Lipid panel',
         'Atorvastatin 40mg', 'E78.5', today + timedelta(days=90), 'active'),
        # Overdue: BNP for HF
        (_hash('DEMO002'), 'BNP', '83880', 'BNP (heart failure)',
         'Entresto 97/103mg', 'I50.22', today - timedelta(days=14), 'overdue'),
    ]
    mon_seeded = 0
    for h, rule_code, lab_code, lab_name, med, cond, due, status in schedules:
        existing = MonitoringSchedule.query.filter_by(
            patient_mrn_hash=h, lab_code=lab_code, user_id=uid
        ).first()
        if not existing:
            ms = MonitoringSchedule(
                patient_mrn_hash=h, user_id=uid,
                lab_code=lab_code, lab_name=lab_name,
                monitoring_rule_code=f'MON_{rule_code}',
                triggering_medication=med,
                triggering_condition=cond,
                next_due_date=due,
                interval_days=180,
                status=status,
                priority='high' if status == 'overdue' else 'standard',
                source='DEMO',
            )
            db.session.add(ms)
            mon_seeded += 1
    db.session.commit()
    print(f'  30.6: Seeded {mon_seeded} monitoring schedule entries')

    # ------------------------------------------------------------------
    # 30.7: ImmunizationSeries — incomplete Shingrix, overdue flu
    # ------------------------------------------------------------------
    imm_rows = [
        # Incomplete Shingrix for DEMO001 (68F, dose 1 given, dose 2 due)
        (_hash('DEMO001'), 'Shingrix', '90750', 1, 2,
         today - timedelta(days=60), today + timedelta(days=30),
         'in_progress', 50, 999, False),
        # Overdue flu for DEMO002 (72M)
        (_hash('DEMO002'), 'Influenza', '90686', 0, 1,
         None, date(today.year, 9, 1) if today.month < 9 else date(today.year, 9, 1),
         'overdue', 6, 999, True),
    ]
    imm_seeded = 0
    for h, group, cpt, dose, total, ddate, ndue, status, amin, amax, seasonal in imm_rows:
        existing = ImmunizationSeries.query.filter_by(
            patient_mrn_hash=h, vaccine_group=group, user_id=uid
        ).first()
        if not existing:
            ims = ImmunizationSeries(
                patient_mrn_hash=h, user_id=uid,
                vaccine_group=group, vaccine_cpt=cpt,
                dose_number=dose, total_doses=total,
                dose_date=ddate, next_dose_due_date=ndue,
                series_status=status,
                age_min=amin, age_max=amax, seasonal=seasonal,
            )
            db.session.add(ims)
            imm_seeded += 1
    db.session.commit()
    print(f'  30.7: Seeded {imm_seeded} immunization series entries')

    print('  Demo data seeding complete.')


if __name__ == '__main__':
    os.environ['FLASK_ENV'] = 'testing'
    from app import create_app
    app = create_app()
    with app.app_context():
        from models import db
        run_migration(app, db)

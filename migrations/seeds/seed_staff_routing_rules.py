"""
Seed staff routing rules into staff_routing_rule table.
Phase 20.5

Usage:
    venv\\Scripts\\python.exe migrations/seed_staff_routing_rules.py
"""

import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RULES = [
    # MA — rooming prep
    ('CARE_GAP_SCREENING', 'ma', 'Screening instruments performed at rooming', 'Administer PHQ-9, GAD-7, or AUDIT-C at rooming per visit type', 'during_visit'),
    ('PROC_PULSE_OX', 'ma', 'Vital signs at rooming', 'Include pulse oximetry with standard vitals', 'during_visit'),
    ('OBESITY_NUTRITION', 'ma', 'BMI documentation at rooming', 'Document BMI and flag if ≥30 for G0447 counseling', 'during_visit'),
    ('VACCINE_ADMIN', 'ma', 'Immunization administration', 'Prepare vaccine, administer, document lot/site/route', 'during_visit'),
    ('VACCINE_FLU', 'ma', 'Flu vaccine prep', 'Check eligibility window (Sep-Mar), prepare dose', 'pre_visit'),
    ('VACCINE_SHINGRIX', 'ma', 'Shingrix series prep', 'Verify age ≥50, check series status, prepare dose', 'pre_visit'),
    ('VACCINE_PNEUMOCOCCAL', 'ma', 'Pneumococcal vaccine prep', 'Verify age ≥65 or risk factor, check series', 'pre_visit'),
    ('PROC_VENIPUNCTURE', 'ma', 'Lab draw at visit', 'Prepare tubes per order set, perform venipuncture', 'during_visit'),
    ('PROC_EKG', 'ma', 'EKG procedure', 'Perform 12-lead EKG, attach to chart', 'during_visit'),
    ('PROC_SPIROMETRY', 'ma', 'Spirometry procedure', 'Perform spirometry per ATS guidelines', 'during_visit'),
    ('PROC_NEBULIZER', 'ma', 'Nebulizer treatment', 'Prepare and administer nebulizer treatment', 'during_visit'),
    ('PROC_INJECTION_ADMIN', 'ma', 'Injection administration', 'Prepare and administer IM/SC injection', 'during_visit'),

    # Nurse — care coordination
    ('CCM', 'nurse', 'CCM time logging', 'Log non-face-to-face clinical staff time toward 20-min threshold', 'daily'),
    ('TCM', 'nurse', 'TCM 2-day contact', 'Complete phone/portal contact within 2 business days of discharge', 'daily'),
    ('PCM', 'nurse', 'PCM time logging', 'Log principal care management time for single complex condition', 'daily'),
    ('RPM', 'nurse', 'RPM data review', 'Review and document remote monitoring data', 'daily'),
    ('TELE_PHONE_EM', 'nurse', 'Phone encounter prep', 'Prepare chart summary for telephone E/M encounter', 'pre_visit'),

    # Front desk — scheduling
    ('AWV', 'front_desk', 'AWV scheduling for Medicare patients', 'Identify Medicare patients without AWV in 12 months, schedule visit', 'pre_visit'),
    ('AWV_INITIAL', 'front_desk', 'Initial AWV scheduling', 'Schedule G0438 for new Medicare patients', 'pre_visit'),

    # Referral coordinator — external referrals
    ('SCREEN_MAMMOGRAPHY', 'referral_coordinator', 'Mammography referral', 'Order and track mammography referral through completion', 'post_visit'),
    ('SCREEN_COLONOSCOPY', 'referral_coordinator', 'Colonoscopy referral', 'Order and track colonoscopy referral, ensure results returned', 'post_visit'),
    ('SCREEN_DEXA', 'referral_coordinator', 'DEXA scan referral', 'Order DEXA for osteoporosis screening, track results', 'post_visit'),
    ('SCREEN_LDCT', 'referral_coordinator', 'LDCT lung cancer screening', 'Order low-dose CT for eligible patients (age 50-80, 20+ pack-year)', 'post_visit'),

    # Biller — coding verification
    ('MODIFIER_25_PROMPT', 'biller', 'Modifier-25 verification', 'Verify separately identifiable E/M documented before applying -25', 'post_visit'),
    ('G2211', 'biller', 'G2211 complexity add-on', 'Verify chronic condition continuity documented, no preventive-only conflict', 'post_visit'),
    ('PROLONGED_SERVICE', 'biller', 'Prolonged service time', 'Verify time documentation for 99417 — must exceed threshold by 15-min increments', 'post_visit'),

    # Provider — clinical decisions
    ('ACP_STANDALONE', 'provider', 'Advance care planning', 'Discuss goals of care and document ACP conversation (99497)', 'during_visit'),
    ('TOBACCO_CESSATION', 'provider', 'Tobacco cessation counseling', 'Counsel ≥3 min (99406) or ≥10 min (99407), document time', 'during_visit'),
    ('ALCOHOL_SCREENING', 'provider', 'Alcohol screening + brief intervention', 'Perform AUDIT-C, brief intervention if positive', 'during_visit'),
    ('COGNITIVE_ASSESSMENT', 'provider', 'Cognitive assessment', 'Perform cognitive screening (MMSE/MoCA), document G0444', 'during_visit'),
    ('PREVENTIVE_EM', 'provider', 'E/M level selection', 'Document MDM complexity to support appropriate E/M level', 'during_visit'),
    ('BHI', 'provider', 'Behavioral health integration', 'Document BHI services — requires ≥20 min/month', 'during_visit'),
    ('COCM_INITIAL', 'provider', 'CoCM initial', 'Initiate collaborative care model with psychiatric consultant', 'during_visit'),
    ('STI_SCREENING', 'provider', 'STI screening order', 'Order STI screening per USPSTF guidelines for eligible patients', 'during_visit'),

    # Office manager — oversight
    ('BONUS_TRACKING', 'office_manager', 'Bonus tracking review', 'Review quarterly bonus projections and capture rates', 'monthly'),
]


def seed():
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data', 'carecompanion.db'
    )
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Clear existing rules for re-seed
    cur.execute("DELETE FROM staff_routing_rule")

    for opp_code, role, reason, task_desc, timing in RULES:
        cur.execute(
            "INSERT INTO staff_routing_rule (opportunity_code, responsible_role, routing_reason, prep_task_description, timing) VALUES (?, ?, ?, ?, ?)",
            (opp_code, role, reason, task_desc, timing),
        )

    conn.commit()
    conn.close()
    print(f'[OK] Seeded {len(RULES)} staff routing rules')


if __name__ == '__main__':
    seed()

"""
Seed: Documentation Phrase Library
Phase 21.3 — Populate documentation_phrase table with clinical documentation snippets.

Maps opportunity_codes to pre-written documentation language that supports
compliant billing. Phrases cover G2211, AWV, CCM, TCM, ACP, modifier-25,
tobacco, screening instruments, obesity, prolonged service, and more.

Idempotent: clears non-customized phrases before re-seeding.
Customized phrases (is_customized=True) are preserved across re-seeds.
"""

import json
import os
import sqlite3
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "carecompanion.db")


PHRASE_SEED = [
    # ── G2211: Visit Complexity Add-on ──
    {
        "opportunity_code": "G2211",
        "cpt_code": "G2211",
        "phrase_category": "mdm",
        "phrase_title": "G2211 Longitudinal Relationship",
        "phrase_text": "This visit addresses the patient's ongoing medical needs in the context of a continuous longitudinal relationship. The medical decision-making inherent to this encounter reflects the complexity of managing this patient's chronic condition(s) over time.",
        "payer_specific": "medicare",
        "clinical_context": "Established Medicare patient with chronic condition",
        "required_elements": json.dumps(["Established patient", "Medicare beneficiary", "Chronic condition documented", "E/M billed same encounter"]),
    },
    {
        "opportunity_code": "G2211",
        "cpt_code": "G2211",
        "phrase_category": "mdm",
        "phrase_title": "G2211 Chronic Complexity Statement",
        "phrase_text": "Ongoing management of [CONDITION] requiring continuity of care. This visit reflects the inherent complexity of evaluating and coordinating care for a patient with multiple interacting chronic conditions within an established longitudinal relationship.",
        "payer_specific": "medicare",
        "clinical_context": "Multiple chronic conditions",
        "required_elements": json.dumps(["Multiple chronic conditions", "Longitudinal relationship", "E/M same encounter"]),
    },

    # ── AWV: Annual Wellness Visit ──
    {
        "opportunity_code": "AWV",
        "cpt_code": "G0438",
        "phrase_category": "care_plan",
        "phrase_title": "AWV Initial — Health Risk Assessment",
        "phrase_text": "Performed initial Annual Wellness Visit including health risk assessment, review of medical/surgical history, screening schedule update, advance directive discussion, depression screening (PHQ-2), cognitive screening, fall risk assessment, BMI/vitals, and creation of personalized prevention plan.",
        "payer_specific": "medicare",
        "clinical_context": "First AWV for Medicare patient",
        "required_elements": json.dumps(["Health risk assessment completed", "Medical history updated", "Prevention plan created", "Screening schedule reviewed"]),
    },
    {
        "opportunity_code": "AWV",
        "cpt_code": "G0439",
        "phrase_category": "care_plan",
        "phrase_title": "AWV Subsequent — Prevention Plan Update",
        "phrase_text": "Performed subsequent Annual Wellness Visit. Updated health risk assessment, reviewed and updated personalized prevention plan, performed depression/cognitive screening, assessed fall risk, updated screening schedule, and reviewed advance directive status.",
        "payer_specific": "medicare",
        "clinical_context": "Subsequent AWV for Medicare patient",
        "required_elements": json.dumps(["Health risk assessment updated", "Prevention plan updated", "Screening schedule reviewed"]),
    },

    # ── 99214/99215: E/M MDM Documentation ──
    {
        "opportunity_code": "PREVENTIVE_EM",
        "cpt_code": "99214",
        "phrase_category": "mdm",
        "phrase_title": "99214 MDM — Moderate Complexity",
        "phrase_text": "Medical decision-making of moderate complexity: multiple chronic conditions requiring ongoing medication management. Data reviewed includes prior lab results and imaging. Risk of complications from drug therapy requires monitoring.",
        "clinical_context": "Office visit with moderate MDM",
        "required_elements": json.dumps(["2+ chronic conditions addressed", "Data reviewed documented", "Risk assessment documented"]),
    },
    {
        "opportunity_code": "PREVENTIVE_EM",
        "cpt_code": "99215",
        "phrase_category": "mdm",
        "phrase_title": "99215 MDM — High Complexity",
        "phrase_text": "Medical decision-making of high complexity: multiple chronic conditions with severe exacerbation or threat to life/limb. Independent review of external records and imaging. Treatment carries significant risk requiring discussion of risks/benefits.",
        "clinical_context": "Office visit with high MDM",
        "required_elements": json.dumps(["Severe exacerbation or threat to life", "External data independently reviewed", "Drug requiring intensive monitoring"]),
    },

    # ── Time-Based E/M Documentation ──
    {
        "opportunity_code": "PREVENTIVE_EM",
        "cpt_code": "99214",
        "phrase_category": "time",
        "phrase_title": "99214 Time-Based (30-39 min)",
        "phrase_text": "Total time spent on the date of encounter: [XX] minutes. Activities included face-to-face examination, reviewing results, coordinating care, counseling patient on treatment options, and documenting findings.",
        "clinical_context": "Time-based E/M billing (30-39 min total)",
        "required_elements": json.dumps(["Total time documented", "Activities enumerated"]),
    },
    {
        "opportunity_code": "PREVENTIVE_EM",
        "cpt_code": "99215",
        "phrase_category": "time",
        "phrase_title": "99215 Time-Based (40-54 min)",
        "phrase_text": "Total time spent on the date of encounter: [XX] minutes. Activities included comprehensive examination, independent review of external records, extensive counseling regarding treatment options and risks, care coordination with specialists, and documentation.",
        "clinical_context": "Time-based E/M billing (40-54 min total)",
        "required_elements": json.dumps(["Total time documented", "Activities enumerated"]),
    },

    # ── ACP: Advance Care Planning ──
    {
        "opportunity_code": "ACP_STANDALONE",
        "cpt_code": "99497",
        "phrase_category": "counseling",
        "phrase_title": "ACP Discussion — 99497",
        "phrase_text": "Advance care planning discussion conducted with patient [and/or surrogate]. Discussed healthcare preferences, values, and goals of care. Reviewed options for life-sustaining treatment, resuscitation preferences, and healthcare proxy designation. Patient expressed understanding. Time spent in ACP discussion: [XX] minutes (minimum 16 minutes required).",
        "payer_specific": "medicare",
        "clinical_context": "Voluntary ACP discussion with Medicare patient",
        "required_elements": json.dumps(["Discussion documented", "Time >= 16 minutes", "Patient/surrogate participation noted", "Preferences documented"]),
    },

    # ── CCM: Chronic Care Management ──
    {
        "opportunity_code": "CCM",
        "cpt_code": "99490",
        "phrase_category": "care_plan",
        "phrase_title": "CCM Monthly — 99490",
        "phrase_text": "Chronic care management services provided this month. Care plan reviewed and updated for: [CONDITIONS]. Non-face-to-face clinical staff time: [XX] minutes. Activities included medication reconciliation, care coordination with [SPECIALIST/FACILITY], patient/caregiver communication, and care plan documentation.",
        "payer_specific": "medicare",
        "clinical_context": "Monthly CCM billing (20+ min non-face-to-face)",
        "required_elements": json.dumps(["Patient consent on file", "2+ chronic conditions", "Care plan documented", "Time >= 20 minutes"]),
    },
    {
        "opportunity_code": "CCM",
        "cpt_code": "99490",
        "phrase_category": "care_plan",
        "phrase_title": "CCM Care Plan Template",
        "phrase_text": "CHRONIC CARE MANAGEMENT PLAN\nConditions managed: [LIST]\nMedications reviewed: [DATE]\nGoals: [PATIENT GOALS]\nBarriers: [BARRIERS]\nAction items: [ITEMS]\nNext scheduled contact: [DATE]\nCare coordinator: [NAME]",
        "payer_specific": "medicare",
        "clinical_context": "CCM care plan documentation template",
        "required_elements": json.dumps(["Conditions listed", "Goals documented", "Action items listed"]),
    },

    # ── TCM: Transitional Care Management ──
    {
        "opportunity_code": "TCM",
        "cpt_code": "99496",
        "phrase_category": "care_plan",
        "phrase_title": "TCM High Complexity — 99496",
        "phrase_text": "Transitional care management provided following discharge from [FACILITY] on [DATE]. Interactive contact made within 2 business days of discharge. Face-to-face visit within 7 calendar days. Services included: medication reconciliation, review of discharge summary, coordination with discharging facility, follow-up test review, and care plan update. Medical decision-making of high complexity.",
        "payer_specific": "medicare",
        "clinical_context": "TCM with high-complexity MDM, face-to-face within 7 days",
        "required_elements": json.dumps(["Interactive contact within 2 business days", "Face-to-face within 7 days", "High-complexity MDM", "Medication reconciliation documented"]),
    },
    {
        "opportunity_code": "TCM",
        "cpt_code": "99495",
        "phrase_category": "care_plan",
        "phrase_title": "TCM Moderate Complexity — 99495",
        "phrase_text": "Transitional care management provided following discharge from [FACILITY] on [DATE]. Interactive contact made within 2 business days of discharge. Face-to-face visit within 14 calendar days. Services included: medication reconciliation, review of discharge summary, coordination with discharging facility, and care plan update. Medical decision-making of moderate complexity.",
        "payer_specific": "medicare",
        "clinical_context": "TCM with moderate-complexity MDM, face-to-face within 14 days",
        "required_elements": json.dumps(["Interactive contact within 2 business days", "Face-to-face within 14 days", "Moderate-complexity MDM", "Medication reconciliation documented"]),
    },

    # ── Modifier -25: Significant, Separately Identifiable E/M ──
    {
        "opportunity_code": "MODIFIER_25_PROMPT",
        "cpt_code": None,
        "phrase_category": "mdm",
        "phrase_title": "Modifier -25 Justification",
        "phrase_text": "In addition to the [PROCEDURE/SERVICE] performed today, a significant, separately identifiable E/M service was provided. The patient presented with [PROBLEM] requiring evaluation beyond the scope of the planned procedure. Separate history, examination, and medical decision-making were performed and documented for this distinct problem.",
        "clinical_context": "E/M with procedure same day",
        "required_elements": json.dumps(["Separate problem identified", "Distinct history/exam documented", "MDM documented separately"]),
    },

    # ── Tobacco Cessation: 99406/99407 ──
    {
        "opportunity_code": "TOBACCO_CESSATION",
        "cpt_code": "99406",
        "phrase_category": "counseling",
        "phrase_title": "Tobacco Cessation 3-10 min — 99406",
        "phrase_text": "Tobacco cessation counseling provided. Assessed willingness to quit. Discussed health risks of continued tobacco use, benefits of cessation, and available treatment options including pharmacotherapy (NRT, varenicline, bupropion). Patient [is/is not] ready to set quit date. Counseling time: [XX] minutes (3-10 min).",
        "clinical_context": "Active tobacco user, intermediate counseling session",
        "required_elements": json.dumps(["Tobacco use status documented", "Counseling content documented", "Time documented (3-10 min)"]),
    },
    {
        "opportunity_code": "TOBACCO_CESSATION",
        "cpt_code": "99407",
        "phrase_category": "counseling",
        "phrase_title": "Tobacco Cessation >10 min — 99407",
        "phrase_text": "Intensive tobacco cessation counseling provided. Comprehensive discussion of health risks, cessation strategies, pharmacotherapy options (NRT, varenicline, bupropion), behavioral triggers, and quit plan development. Patient [is/is not] ready to set quit date of [DATE]. Referral to [RESOURCE] discussed. Counseling time: [XX] minutes (>10 min).",
        "clinical_context": "Active tobacco user, intensive counseling session",
        "required_elements": json.dumps(["Tobacco use status documented", "Comprehensive counseling documented", "Time documented (>10 min)"]),
    },

    # ── Screening Instruments: 96127 ──
    {
        "opportunity_code": "CARE_GAP_SCREENING",
        "cpt_code": "96127",
        "phrase_category": "screening",
        "phrase_title": "PHQ-9 Depression Screening — 96127",
        "phrase_text": "PHQ-9 depression screening administered. Score: [XX]/27. Interpretation: [MINIMAL/MILD/MODERATE/MODERATELY SEVERE/SEVERE]. [Clinical action taken/Monitoring plan documented].",
        "clinical_context": "Depression screening with standardized instrument",
        "required_elements": json.dumps(["Standardized instrument identified (PHQ-9)", "Score documented", "Interpretation documented"]),
    },
    {
        "opportunity_code": "CARE_GAP_SCREENING",
        "cpt_code": "96127",
        "phrase_category": "screening",
        "phrase_title": "GAD-7 Anxiety Screening — 96127",
        "phrase_text": "GAD-7 anxiety screening administered. Score: [XX]/21. Interpretation: [MINIMAL/MILD/MODERATE/SEVERE]. [Clinical action taken/Monitoring plan documented].",
        "clinical_context": "Anxiety screening with standardized instrument",
        "required_elements": json.dumps(["Standardized instrument identified (GAD-7)", "Score documented", "Interpretation documented"]),
    },
    {
        "opportunity_code": "CARE_GAP_SCREENING",
        "cpt_code": "96127",
        "phrase_category": "screening",
        "phrase_title": "AUDIT-C Alcohol Screening — 96127",
        "phrase_text": "AUDIT-C alcohol misuse screening administered. Score: [XX]/12. Interpretation: [NEGATIVE/POSITIVE for at-risk drinking]. [Brief intervention provided/Referral discussed].",
        "clinical_context": "Alcohol screening with standardized instrument",
        "required_elements": json.dumps(["Standardized instrument identified (AUDIT-C)", "Score documented", "Interpretation documented"]),
    },

    # ── Obesity/Nutrition: G0447/G0446 ──
    {
        "opportunity_code": "OBESITY_NUTRITION",
        "cpt_code": "G0447",
        "phrase_category": "counseling",
        "phrase_title": "Obesity IBT Counseling — G0447",
        "phrase_text": "Intensive behavioral therapy for obesity provided. BMI: [XX] (>=30). Discussed dietary assessment, physical activity goals, behavioral strategies for weight management, and available resources. Assessed barriers to weight loss. Follow-up plan established. Counseling time: [XX] minutes (minimum 15 min).",
        "payer_specific": "medicare",
        "clinical_context": "Medicare patient with BMI >= 30",
        "required_elements": json.dumps(["BMI >= 30 documented", "Dietary assessment discussed", "Physical activity addressed", "Time >= 15 minutes"]),
    },
    {
        "opportunity_code": "OBESITY_NUTRITION",
        "cpt_code": "G0446",
        "phrase_category": "counseling",
        "phrase_title": "CVD IBT Counseling — G0446",
        "phrase_text": "Intensive behavioral therapy for cardiovascular disease provided. Discussed cardiovascular risk factors, dietary modifications (DASH/Mediterranean), physical activity goals, lipid management, blood pressure monitoring, and smoking cessation (if applicable). Time: [XX] minutes (minimum 15 min).",
        "payer_specific": "medicare",
        "clinical_context": "Medicare patient with CVD risk factors",
        "required_elements": json.dumps(["CVD risk factors documented", "Dietary counseling provided", "Physical activity addressed", "Time >= 15 minutes"]),
    },

    # ── Prolonged Service: 99417 ──
    {
        "opportunity_code": "PROLONGED_SERVICE",
        "cpt_code": "99417",
        "phrase_category": "time",
        "phrase_title": "Prolonged Service — 99417",
        "phrase_text": "Prolonged service on the date of the encounter requiring additional [15] minutes beyond the time required for the primary E/M service. Total time: [XX] minutes (exceeding the typical time for 99215 by >= 15 minutes). Additional time spent on: [ACTIVITIES — complex MDM, care coordination, counseling, data review].",
        "clinical_context": "Visit exceeding 54/74 min (office/outpatient E/M)",
        "required_elements": json.dumps(["Total time documented", "Exceeds 99215 threshold by 15+ min", "Activities during additional time documented"]),
    },

    # ── BHI: Behavioral Health Integration ──
    {
        "opportunity_code": "BHI",
        "cpt_code": "99484",
        "phrase_category": "care_plan",
        "phrase_title": "BHI Monthly — 99484",
        "phrase_text": "Behavioral health integration services provided this month. Clinical staff time: [XX] minutes (minimum 20 min). Activities included care plan development/revision for [DIAGNOSIS], systematic assessment using [PHQ-9/GAD-7], care coordination, and patient engagement regarding treatment goals. Patient [is/is not] meeting behavioral health targets.",
        "clinical_context": "Monthly BHI services for patient with behavioral health diagnosis",
        "required_elements": json.dumps(["BH diagnosis documented", "Care plan in place", "Time >= 20 minutes", "Systematic assessment used"]),
    },

    # ── Cognitive Assessment: 99483 ──
    {
        "opportunity_code": "COGNITIVE_ASSESSMENT",
        "cpt_code": "99483",
        "phrase_category": "screening",
        "phrase_title": "Cognitive Assessment — 99483",
        "phrase_text": "Comprehensive cognitive assessment and care plan performed. Included: cognition-focused history, medication review for cognitive effects, functional assessment (ADLs/IADLs), standardized cognitive testing (MMSE/MoCA score: [XX]), safety assessment, caregiver needs assessment, and creation of cognitive care plan with referrals as indicated.",
        "payer_specific": "medicare",
        "clinical_context": "Medicare patient with cognitive concerns",
        "required_elements": json.dumps(["Cognitive testing performed", "Functional assessment documented", "Safety evaluation", "Care plan created"]),
    },

    # ── Alcohol Screening: G0442 ──
    {
        "opportunity_code": "ALCOHOL_SCREENING",
        "cpt_code": "G0442",
        "phrase_category": "screening",
        "phrase_title": "Alcohol Misuse Screening — G0442",
        "phrase_text": "Annual alcohol misuse screening performed using AUDIT-C questionnaire. Score: [XX]/12. Screening result: [NEGATIVE/POSITIVE]. [Brief counseling provided per G0443 / No intervention indicated at this time].",
        "payer_specific": "medicare",
        "clinical_context": "Annual Medicare alcohol misuse screening",
        "required_elements": json.dumps(["Standardized screening tool used", "Score documented", "Result interpretation documented"]),
    },

    # ── PCM: Principal Care Management ──
    {
        "opportunity_code": "PCM_PRINCIPAL_CARE",
        "cpt_code": "99424",
        "phrase_category": "care_plan",
        "phrase_title": "PCM Monthly — 99424",
        "phrase_text": "Principal Care Management services provided for [SINGLE HIGH-RISK CONDITION]. Non-face-to-face clinical staff time: [XX] minutes (minimum 30 min). Activities: disease-specific care plan review, medication management, monitoring/assessment, patient education, and care coordination focused on [CONDITION].",
        "payer_specific": "medicare",
        "clinical_context": "Single high-risk chronic condition (e.g., CHF, COPD)",
        "required_elements": json.dumps(["Single complex chronic condition identified", "Disease-specific care plan", "Time >= 30 minutes", "Patient consent on file"]),
    },

    # ── RPM: Remote Patient Monitoring ──
    {
        "opportunity_code": "RPM",
        "cpt_code": "99457",
        "phrase_category": "care_plan",
        "phrase_title": "RPM Interactive Communication — 99457",
        "phrase_text": "Remote physiologic monitoring treatment management services. Interactive communication with patient/caregiver regarding [CONDITION] monitoring data. Reviewed [BP/glucose/weight/SpO2] readings. Clinical decisions: [ACTIONS TAKEN]. Time: [XX] minutes (minimum 20 min cumulative in calendar month).",
        "clinical_context": "Monthly RPM with interactive patient communication",
        "required_elements": json.dumps(["RPM device in use", "Data reviewed", "Interactive communication documented", "Time >= 20 minutes/month"]),
    },

    # ── STI Screening ──
    {
        "opportunity_code": "STI_SCREENING",
        "cpt_code": "87491",
        "phrase_category": "screening",
        "phrase_title": "STI Screening Documentation",
        "phrase_text": "STI screening performed per USPSTF guidelines. Risk assessment indicates screening for [CHLAMYDIA/GONORRHEA/SYPHILIS/HIV/HEPB/HEPC]. Specimens collected: [URINE NAAT / BLOOD DRAW]. Patient counseled on risk reduction. Results to follow.",
        "clinical_context": "Sexually active patient meeting screening criteria",
        "required_elements": json.dumps(["Risk assessment documented", "Specific tests ordered", "Patient counseled"]),
    },

    # ── Vaccine Administration ──
    {
        "opportunity_code": "VACCINE_ADMIN",
        "cpt_code": "90471",
        "phrase_category": "procedure",
        "phrase_title": "Vaccine Administration Documentation",
        "phrase_text": "Vaccine administered: [VACCINE NAME], [DOSE] mL, [ROUTE] injection, [SITE]. Lot #: [LOT]. Expiration: [EXP]. VIS provided on [DATE]. Patient observed [XX] minutes post-administration with no adverse reaction. Administered by: [NAME/CREDENTIALS].",
        "clinical_context": "Any vaccine administration",
        "required_elements": json.dumps(["Vaccine name documented", "Lot number recorded", "VIS date", "Site/route documented"]),
    },

    # ── CoCM: Collaborative Care ──
    {
        "opportunity_code": "COCM_INITIAL",
        "cpt_code": "99492",
        "phrase_category": "care_plan",
        "phrase_title": "CoCM Initial Month — 99492",
        "phrase_text": "Collaborative care model initial month services. Psychiatric consultant: [NAME]. Behavioral care manager time: [XX] minutes (minimum 36 min). Activities: initial assessment, care plan development, PHQ-9/GAD-7 baseline, registry entry, behavioral intervention initiation, and psychiatric consultation for treatment recommendations.",
        "clinical_context": "First month of CoCM for behavioral health",
        "required_elements": json.dumps(["Psychiatric consultant identified", "Behavioral care manager time >= 36 min", "Care plan developed", "Registry documented"]),
    },
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Verify table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documentation_phrase'")
    if not cur.fetchone():
        print("[ERROR] documentation_phrase table does not exist. Run migration first.")
        conn.close()
        sys.exit(1)

    # Clear non-customized phrases (preserve user edits)
    cur.execute("DELETE FROM documentation_phrase WHERE is_customized = 0")
    deleted = cur.rowcount

    # Insert seed phrases
    for p in PHRASE_SEED:
        cur.execute(
            """INSERT INTO documentation_phrase
               (opportunity_code, cpt_code, phrase_category, phrase_title,
                phrase_text, payer_specific, clinical_context, required_elements,
                is_active, is_customized)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0)""",
            (
                p["opportunity_code"],
                p.get("cpt_code"),
                p["phrase_category"],
                p["phrase_title"],
                p["phrase_text"],
                p.get("payer_specific"),
                p.get("clinical_context"),
                p.get("required_elements"),
            ),
        )

    conn.commit()
    count = len(PHRASE_SEED)
    conn.close()
    print(f"[OK] Seeded {count} documentation phrases (cleared {deleted} previous non-customized).")


if __name__ == "__main__":
    seed()

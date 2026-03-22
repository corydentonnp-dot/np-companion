"""
CareCompanion — Billing Rule Seed Data
File: billing_engine/rules.py

Seed data dicts for the BillingRule DB table. Each entry maps an
opportunity_code to its CPT codes, payer eligibility, estimated revenue,
frequency limits, and documentation checklist.

Used by migrate_seed_billing_rules.py to populate/update the billing_rule
table. Actual detection logic lives in the detector modules — this file
is purely declarative reference data.

Phase 19D.3 — ~100 rules spanning all 26 detector modules.
"""

ALL_PAYERS = ["medicare_b", "medicare_advantage", "medicaid", "commercial"]
MEDICARE_ONLY = ["medicare_b", "medicare_advantage"]
MEDICARE_MEDICAID = ["medicare_b", "medicare_advantage", "medicaid"]

BILLING_RULES = {
    # =====================================================================
    # CCM — Chronic Care Management (ccm.py)
    # =====================================================================
    "CCM": {
        "category": "ccm",
        "description": "Chronic Care Management — 20+ min/month for 2+ chronic conditions",
        "cpt_codes": ["99490", "99439", "99491"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 62.0,
        "modifier": None,
        "documentation_checklist": [
            "Verify 2+ chronic conditions expected to last 12+ months",
            "Obtain written CCM consent from patient",
            "Document 20+ min of non-face-to-face care coordination",
            "Maintain comprehensive care plan in EHR",
            "Provide 24/7 access to care team",
        ],
        "frequency_limit": "monthly",
    },

    # =====================================================================
    # PCM — Principal Care Management (ccm.py)
    # =====================================================================
    "PCM_PRINCIPAL_CARE": {
        "category": "ccm",
        "description": "Principal Care Management — single high-complexity condition, 30+ min/month",
        "cpt_codes": ["99424", "99425"],
        "payer_types": MEDICARE_ONLY,
        "estimated_revenue": 70.0,
        "modifier": None,
        "documentation_checklist": [
            "Identify single complex chronic condition",
            "Document 30+ min of management time",
            "Create/update condition-specific care plan",
            "Coordinate specialist referrals as needed",
        ],
        "frequency_limit": "monthly",
    },

    # =====================================================================
    # AWV — Annual Wellness Visit (awv.py)
    # =====================================================================
    "AWV": {
        "category": "awv",
        "description": "Annual Wellness Visit — Medicare preventive with HRA",
        "cpt_codes": ["G0438", "G0439"],
        "payer_types": MEDICARE_ONLY,
        "estimated_revenue": 130.0,
        "modifier": None,
        "documentation_checklist": [
            "Complete Health Risk Assessment (HRA)",
            "Update personal/family history",
            "Depression screening (PHQ-2/PHQ-9)",
            "Cognitive assessment",
            "Functional ability/safety assessment",
            "Create/update personalized prevention plan",
            "Review screening schedule",
        ],
        "frequency_limit": "annual",
    },
    "PROLONGED_PREVENTIVE": {
        "category": "awv",
        "description": "Prolonged preventive service — AWV exceeding typical time",
        "cpt_codes": ["99354", "99355"],
        "payer_types": MEDICARE_ONLY,
        "estimated_revenue": 100.0,
        "modifier": None,
        "documentation_checklist": [
            "Document total face-to-face time exceeding typical AWV",
            "Detail additional counseling/coordination performed",
            "Start/stop times for prolonged service",
        ],
        "frequency_limit": "annual",
    },

    # =====================================================================
    # G2211 — Visit Complexity Add-on (g2211.py)
    # =====================================================================
    "G2211": {
        "category": "g2211",
        "description": "Visit complexity inherent to E/M — ongoing relationship with Medicare patient + chronic condition",
        "cpt_codes": ["G2211"],
        "payer_types": MEDICARE_ONLY,
        "estimated_revenue": 16.04,
        "modifier": None,
        "documentation_checklist": [
            "Patient is established Medicare beneficiary",
            "Has at least one chronic condition",
            "Visit addresses ongoing longitudinal relationship",
            "Append G2211 to office/outpatient E/M",
        ],
        "frequency_limit": "per_visit",
    },

    # =====================================================================
    # Tobacco Cessation (tobacco.py)
    # =====================================================================
    "TOBACCO_CESSATION": {
        "category": "tobacco_cessation",
        "description": "Tobacco cessation counseling — active smoker at E/M visit",
        "cpt_codes": ["99406", "99407"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 15.16,
        "modifier": None,
        "documentation_checklist": [
            "Assess tobacco use status",
            "Provide cessation counseling (3-10 min for 99406, >10 min for 99407)",
            "Document willingness to quit",
            "Offer pharmacotherapy (NRT, varenicline, bupropion)",
            "Schedule follow-up",
        ],
        "frequency_limit": "per_visit",
    },

    # =====================================================================
    # Alcohol Screening (alcohol.py)
    # =====================================================================
    "ALCOHOL_SCREENING": {
        "category": "alcohol_screening",
        "description": "Annual alcohol misuse screening and brief counseling",
        "cpt_codes": ["G0442", "G0443", "99408"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 17.80,
        "modifier": None,
        "documentation_checklist": [
            "Administer validated screening tool (AUDIT-C)",
            "Document screening score",
            "Provide brief counseling if positive",
            "Refer to treatment if indicated",
        ],
        "frequency_limit": "annual",
    },

    # =====================================================================
    # Cognitive Assessment (cognitive.py)
    # =====================================================================
    "COGNITIVE_ASSESSMENT": {
        "category": "cognitive_assessment",
        "description": "Cognitive assessment and care planning — Medicare 65+",
        "cpt_codes": ["99483"],
        "payer_types": MEDICARE_ONLY,
        "estimated_revenue": 257.72,
        "modifier": None,
        "documentation_checklist": [
            "Administer validated cognitive screening (MoCA, MMSE, Mini-Cog)",
            "Functional assessment",
            "Medication reconciliation",
            "Safety evaluation",
            "Caregiver assessment",
            "Create/update care plan",
            "Advance directive discussion",
        ],
        "frequency_limit": "annual",
    },

    # =====================================================================
    # Obesity / Nutrition (obesity.py)
    # =====================================================================
    "OBESITY_NUTRITION": {
        "category": "obesity_nutrition",
        "description": "Obesity screening and intensive behavioral therapy",
        "cpt_codes": ["G0447", "G0473", "97802", "97803"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 25.99,
        "modifier": None,
        "documentation_checklist": [
            "Calculate and document BMI",
            "Provide dietary/exercise counseling",
            "Document behavioral goals agreed upon",
            "Schedule follow-up for weight management",
        ],
        "frequency_limit": "per_visit",
    },

    # =====================================================================
    # ACP — Advance Care Planning (acp.py)
    # =====================================================================
    "ACP_STANDALONE": {
        "category": "acp_standalone",
        "description": "Advance Care Planning discussion — standalone or with AWV",
        "cpt_codes": ["99497", "99498"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 80.87,
        "modifier": None,
        "documentation_checklist": [
            "Discuss patient's values and goals of care",
            "Review/create advance directive",
            "Discuss healthcare proxy designation",
            "Document discussion content and patient decisions",
            "Provide copies of documents to patient",
        ],
        "frequency_limit": "annual",
    },

    # =====================================================================
    # STI Screening (sti.py)
    # =====================================================================
    "STI_SCREENING": {
        "category": "sti_screening",
        "description": "STI screening — sexually active patients per USPSTF",
        "cpt_codes": ["87491", "87591", "87389", "86803"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 35.0,
        "modifier": None,
        "documentation_checklist": [
            "Assess sexual history and risk factors",
            "Order appropriate STI panel (chlamydia, gonorrhea, HIV, syphilis)",
            "Document screening indication",
            "Provide counseling on risk reduction",
        ],
        "frequency_limit": "annual",
    },

    # =====================================================================
    # Preventive E/M (preventive.py)
    # =====================================================================
    "PREVENTIVE_EM": {
        "category": "preventive_visit",
        "description": "Preventive medicine E/M — annual physical for non-Medicare patients",
        "cpt_codes": ["99385", "99386", "99387", "99395", "99396", "99397"],
        "payer_types": ["medicaid", "commercial"],
        "estimated_revenue": 110.0,
        "modifier": None,
        "documentation_checklist": [
            "Comprehensive history",
            "Complete physical examination",
            "Age-appropriate screening review",
            "Immunization status update",
            "Anticipatory guidance",
        ],
        "frequency_limit": "annual",
    },

    # =====================================================================
    # BHI — Behavioral Health Integration (bhi.py)
    # =====================================================================
    "BHI": {
        "category": "bhi",
        "description": "Behavioral Health Integration — 20+ min/month for behavioral health conditions",
        "cpt_codes": ["99484"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 48.50,
        "modifier": None,
        "documentation_checklist": [
            "Identify qualifying behavioral health condition",
            "Document 20+ min of BHI services per month",
            "Systematic assessment using validated tool",
            "Care plan development/revision",
            "Coordinate with behavioral health specialist",
        ],
        "frequency_limit": "monthly",
    },

    # =====================================================================
    # RPM — Remote Patient Monitoring (rpm.py)
    # =====================================================================
    "RPM": {
        "category": "rpm",
        "description": "Remote Patient Monitoring — device setup + monthly monitoring",
        "cpt_codes": ["99453", "99454", "99457", "99458"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 55.0,
        "modifier": None,
        "documentation_checklist": [
            "Enroll patient in RPM program with qualifying condition",
            "Set up FDA-cleared monitoring device (99453)",
            "Ensure 16+ days of data transmission per month (99454)",
            "Document 20+ min interactive communication (99457)",
            "Document additional 20+ min if applicable (99458)",
        ],
        "frequency_limit": "monthly",
    },

    # =====================================================================
    # TCM — Transitional Care Management (tcm.py)
    # =====================================================================
    "TCM": {
        "category": "tcm",
        "description": "Transitional Care Management — post-discharge follow-up within 7-14 days",
        "cpt_codes": ["99495", "99496"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 280.0,
        "modifier": None,
        "documentation_checklist": [
            "Contact patient within 2 business days of discharge",
            "Medication reconciliation within 30 days",
            "Face-to-face visit within 7 days (99496) or 14 days (99495)",
            "Address discharge plan and follow-up needs",
            "Coordinate with inpatient team",
        ],
        "frequency_limit": "per_visit",
    },

    # =====================================================================
    # E/M Add-ons — Modifier 25 (em_addons.py)
    # =====================================================================
    "MODIFIER_25_PROMPT": {
        "category": "em_addons",
        "description": "Modifier -25 prompt — significant/separate E/M on same day as procedure",
        "cpt_codes": [],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 0.0,
        "modifier": "-25",
        "documentation_checklist": [
            "Document separate chief complaint or clinical decision-making",
            "Ensure E/M documentation stands alone from procedure",
            "Append modifier -25 to E/M code",
        ],
        "frequency_limit": "per_visit",
    },

    # =====================================================================
    # Care Gap Screenings (care_gaps.py)
    # =====================================================================
    "CARE_GAP_SCREENING": {
        "category": "care_gap_screenings",
        "description": "Care gap screenings — overdue preventive services from care gap engine",
        "cpt_codes": [],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 20.0,
        "modifier": None,
        "documentation_checklist": [
            "Identify overdue screening from care gap list",
            "Order appropriate test/procedure",
            "Document screening indication",
            "Schedule follow-up for results",
        ],
        "frequency_limit": "per_visit",
    },

    # =====================================================================
    # Vaccine Administration (vaccine_admin.py)
    # =====================================================================
    "VACCINE_ADMIN": {
        "category": "vaccine_admin",
        "description": "Vaccine administration — product code + admin code pair",
        "cpt_codes": ["90460", "90471", "90472", "90473", "90474"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 25.0,
        "modifier": None,
        "documentation_checklist": [
            "Verify immunization due per schedule",
            "Administer vaccine per protocol",
            "Bill product code AND administration code",
            "Document lot number, expiration, site, route",
            "Update immunization registry",
        ],
        "frequency_limit": "per_visit",
    },
    "IMM_HPV": {
        "category": "vaccine_admin",
        "description": "HPV vaccine series gap — incomplete series ages 9-26",
        "cpt_codes": ["90649", "90650", "90651"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 250.0,
        "modifier": None,
        "documentation_checklist": ["Verify series status", "Administer dose", "Update registry", "Schedule next dose if needed"],
        "frequency_limit": "per_visit",
    },
    "IMM_HEPB": {
        "category": "vaccine_admin",
        "description": "Hepatitis B vaccine series gap",
        "cpt_codes": ["90746", "90747"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 60.0,
        "modifier": None,
        "documentation_checklist": ["Verify series status", "Administer dose", "Update registry"],
        "frequency_limit": "per_visit",
    },
    "IMM_HEPA": {
        "category": "vaccine_admin",
        "description": "Hepatitis A vaccine series gap",
        "cpt_codes": ["90632", "90633"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 55.0,
        "modifier": None,
        "documentation_checklist": ["Verify series status", "Administer dose", "Update registry"],
        "frequency_limit": "per_visit",
    },
    "IMM_RSV": {
        "category": "vaccine_admin",
        "description": "RSV vaccine — adults 60+ or pregnant 32-36 weeks",
        "cpt_codes": ["90380", "90381"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 200.0,
        "modifier": None,
        "documentation_checklist": ["Verify age/pregnancy eligibility", "Administer RSV vaccine", "Update registry"],
        "frequency_limit": "once",
    },
    "IMM_MENACWY": {
        "category": "vaccine_admin",
        "description": "Meningococcal ACWY vaccine series gap — ages 11-18",
        "cpt_codes": ["90734"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 130.0,
        "modifier": None,
        "documentation_checklist": ["Verify series status", "Administer dose", "Update registry"],
        "frequency_limit": "per_visit",
    },
    "IMM_MENB": {
        "category": "vaccine_admin",
        "description": "Meningococcal B vaccine series gap — ages 16-23",
        "cpt_codes": ["90620", "90621"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 200.0,
        "modifier": None,
        "documentation_checklist": ["Verify series status", "Administer dose", "Update registry"],
        "frequency_limit": "per_visit",
    },

    # =====================================================================
    # Prolonged Services (prolonged.py)
    # =====================================================================
    "PROLONGED_SERVICE": {
        "category": "prolonged_service",
        "description": "Prolonged office/outpatient E/M — each additional 15 min beyond threshold",
        "cpt_codes": ["99417"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 67.50,
        "modifier": None,
        "documentation_checklist": [
            "Document total face-to-face time",
            "Detail medical decision-making or counseling beyond typical",
            "Bill 99417 per additional 15-minute increment",
        ],
        "frequency_limit": "per_visit",
    },

    # =====================================================================
    # PROCEDURES (procedures.py)
    # =====================================================================
    "PROC_EKG": {
        "category": "procedures",
        "description": "In-office EKG with qualifying cardiac/respiratory symptoms",
        "cpt_codes": ["93000", "93005", "93010"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 17.0,
        "modifier": None,
        "documentation_checklist": [
            "Document cardiac/respiratory symptom indication",
            "Perform and interpret 12-lead EKG",
            "Document interpretation in note",
        ],
        "frequency_limit": "per_visit",
    },
    "PROC_SPIROMETRY": {
        "category": "procedures",
        "description": "In-office spirometry for respiratory diagnosis",
        "cpt_codes": ["94010", "94060"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 30.0,
        "modifier": None,
        "documentation_checklist": [
            "Document respiratory indication (COPD, asthma, dyspnea)",
            "Perform spirometry with pre/post bronchodilator if indicated",
            "Document interpretation",
        ],
        "frequency_limit": "per_visit",
    },
    "PROC_PULSE_OX": {
        "category": "procedures",
        "description": "Pulse oximetry for respiratory complaint",
        "cpt_codes": ["94760", "94761"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 5.0,
        "modifier": None,
        "documentation_checklist": [
            "Document respiratory/cardiac indication",
            "Record SpO2 reading",
            "Document interpretation and clinical action",
        ],
        "frequency_limit": "per_visit",
    },
    "PROC_NEBULIZER": {
        "category": "procedures",
        "description": "In-office nebulizer treatment",
        "cpt_codes": ["94640"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 18.0,
        "modifier": None,
        "documentation_checklist": [
            "Document respiratory indication",
            "Administer nebulizer treatment",
            "Document pre/post assessment",
            "Record medication used",
        ],
        "frequency_limit": "per_visit",
    },
    "PROC_INJECTION_ADMIN": {
        "category": "procedures",
        "description": "Therapeutic injection administration (IM/SQ)",
        "cpt_codes": ["96372"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 22.0,
        "modifier": None,
        "documentation_checklist": [
            "Document injection indication",
            "Record medication, dose, route, site",
            "Bill admin code 96372 + drug J-code",
        ],
        "frequency_limit": "per_visit",
    },
    "PROC_VENIPUNCTURE": {
        "category": "procedures",
        "description": "Venipuncture for specimen collection",
        "cpt_codes": ["36415"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 3.0,
        "modifier": None,
        "documentation_checklist": [
            "Document blood draw performed in office",
            "Bill 36415 with lab orders",
        ],
        "frequency_limit": "per_visit",
    },

    # =====================================================================
    # CHRONIC MONITORING (chronic_monitoring.py)
    # =====================================================================
    "MON_A1C": {
        "category": "chronic_monitoring",
        "description": "Hemoglobin A1C for diabetes monitoring",
        "cpt_codes": ["83036"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 11.27,
        "modifier": None,
        "documentation_checklist": ["Order A1C", "Review result with patient", "Adjust treatment plan"],
        "frequency_limit": "quarterly",
    },
    "MON_LIPID": {
        "category": "chronic_monitoring",
        "description": "Lipid panel for statin/cardiovascular monitoring",
        "cpt_codes": ["80061"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 18.39,
        "modifier": None,
        "documentation_checklist": ["Order fasting lipid panel", "Review with patient", "Adjust medications"],
        "frequency_limit": "annual",
    },
    "MON_TSH": {
        "category": "chronic_monitoring",
        "description": "TSH for thyroid medication monitoring",
        "cpt_codes": ["84443"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 22.30,
        "modifier": None,
        "documentation_checklist": ["Order TSH", "Review result", "Adjust thyroid medication dose"],
        "frequency_limit": "annual",
    },
    "MON_RENAL": {
        "category": "chronic_monitoring",
        "description": "Basic metabolic panel for renal function monitoring",
        "cpt_codes": ["80048"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 10.56,
        "modifier": None,
        "documentation_checklist": ["Order BMP", "Review creatinine/eGFR", "Assess medication adjustments"],
        "frequency_limit": "annual",
    },
    "MON_CBC": {
        "category": "chronic_monitoring",
        "description": "CBC for anticonvulsant/chemotherapy/hematologic monitoring",
        "cpt_codes": ["85025"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 7.77,
        "modifier": None,
        "documentation_checklist": ["Order CBC with diff", "Review for cytopenias", "Adjust medications"],
        "frequency_limit": "annual",
    },
    "MON_INR": {
        "category": "chronic_monitoring",
        "description": "PT/INR for warfarin monitoring",
        "cpt_codes": ["85610"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 5.08,
        "modifier": None,
        "documentation_checklist": ["Order PT/INR", "Review therapeutic range", "Adjust warfarin dose"],
        "frequency_limit": "monthly",
    },
    "MON_LFT": {
        "category": "chronic_monitoring",
        "description": "Hepatic function panel for hepatotoxic medication monitoring",
        "cpt_codes": ["80076"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 11.22,
        "modifier": None,
        "documentation_checklist": ["Order hepatic panel", "Review AST/ALT", "Assess for hepatotoxicity"],
        "frequency_limit": "annual",
    },
    "MON_UACR": {
        "category": "chronic_monitoring",
        "description": "Urine microalbumin for diabetic nephropathy monitoring",
        "cpt_codes": ["82043"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 8.95,
        "modifier": None,
        "documentation_checklist": ["Order urine microalbumin/creatinine ratio", "Review result", "Initiate/adjust ACE/ARB if indicated"],
        "frequency_limit": "annual",
    },
    "MON_VITD": {
        "category": "chronic_monitoring",
        "description": "Vitamin D level for osteoporosis/CKD monitoring",
        "cpt_codes": ["82306"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 40.00,
        "modifier": None,
        "documentation_checklist": ["Order 25-hydroxy vitamin D", "Review result", "Adjust supplementation"],
        "frequency_limit": "annual",
    },

    # =====================================================================
    # TELEHEALTH (telehealth.py)
    # =====================================================================
    "TELE_PHONE_EM": {
        "category": "telehealth",
        "description": "Telephone E/M — phone encounter with medical decision-making",
        "cpt_codes": ["99441", "99442", "99443"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 51.24,
        "modifier": None,
        "documentation_checklist": [
            "Document call duration",
            "Medical decision-making performed",
            "Verify no resulting in-person visit within 24 hours",
            "Select code by time: 5-10 min (99441), 11-20 min (99442), 21-30 min (99443)",
        ],
        "frequency_limit": "per_visit",
    },
    "TELE_DIGITAL_EM": {
        "category": "telehealth",
        "description": "Online digital E/M — patient-initiated portal messages",
        "cpt_codes": ["99421", "99422", "99423"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 62.0,
        "modifier": None,
        "documentation_checklist": [
            "Patient initiated the message exchange",
            "Document cumulative provider time over 7 days",
            "Clinical decision-making required",
            "Select code by cumulative time: 5-10 min (99421), 11-20 min (99422), 21+ min (99423)",
        ],
        "frequency_limit": "per_visit",
    },
    "TELE_INTERPROF": {
        "category": "telehealth",
        "description": "Interprofessional telephone/electronic consult with specialist",
        "cpt_codes": ["99452"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 35.15,
        "modifier": None,
        "documentation_checklist": [
            "Document 16+ min reviewing/discussing with specialist",
            "Record specialist name and specialty",
            "Document clinical question and specialist recommendation",
        ],
        "frequency_limit": "per_visit",
    },

    # =====================================================================
    # CoCM — Collaborative Care Model (cocm.py)
    # =====================================================================
    "COCM_INITIAL": {
        "category": "cocm",
        "description": "CoCM initial month — psychiatric collaborative care with BH care manager",
        "cpt_codes": ["99492"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 165.04,
        "modifier": None,
        "documentation_checklist": [
            "Verify CoCM infrastructure (BH care manager + psychiatric consultant)",
            "Initial psychiatric assessment",
            "Document 36+ min of CoCM services",
            "Create behavioral health care plan",
            "Psychiatric consultant case review",
        ],
        "frequency_limit": "once",
    },
    "COCM_SUBSEQUENT": {
        "category": "cocm",
        "description": "CoCM subsequent month — ongoing psychiatric collaborative care",
        "cpt_codes": ["99493"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 130.28,
        "modifier": None,
        "documentation_checklist": [
            "Document 36+ min of CoCM services this month",
            "Update behavioral health care plan",
            "Psychiatric consultant case review",
            "Assess treatment progress with validated measure",
        ],
        "frequency_limit": "monthly",
    },
    "COCM_ADDITIONAL_30": {
        "category": "cocm",
        "description": "CoCM additional 30-min add-on — complex cases requiring extended time",
        "cpt_codes": ["99494"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 64.72,
        "modifier": None,
        "documentation_checklist": [
            "Document total CoCM time exceeds 66 min this month",
            "Detail additional services provided beyond base time",
        ],
        "frequency_limit": "monthly",
    },

    # =====================================================================
    # COUNSELING (counseling.py)
    # =====================================================================
    "COUNS_FALLS": {
        "category": "counseling",
        "description": "Falls prevention counseling/exercise for community-dwelling adults 65+",
        "cpt_codes": ["97110"],
        "payer_types": MEDICARE_ONLY,
        "estimated_revenue": 30.88,
        "modifier": None,
        "documentation_checklist": [
            "Document patient age 65+ with fall risk factors",
            "Assess fall history and gait/balance",
            "Provide fall prevention counseling",
            "Refer to exercise program if appropriate",
        ],
        "frequency_limit": "annual",
    },
    "COUNS_CVD_IBT": {
        "category": "counseling",
        "description": "Intensive behavioral therapy for CVD — Medicare beneficiaries with CVD risk",
        "cpt_codes": ["G0446"],
        "payer_types": MEDICARE_ONLY,
        "estimated_revenue": 28.31,
        "modifier": None,
        "documentation_checklist": [
            "Document CVD risk factors (HTN, dyslipidemia, DM, tobacco)",
            "Provide intensive behavioral counseling",
            "Set measurable lifestyle goals",
            "Schedule follow-up",
        ],
        "frequency_limit": "annual",
    },
    "COUNS_BREASTFEED": {
        "category": "counseling",
        "description": "Breastfeeding counseling for pregnant/nursing women",
        "cpt_codes": ["99401"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 32.0,
        "modifier": None,
        "documentation_checklist": [
            "Assess breastfeeding intent/status",
            "Provide anticipatory guidance on breastfeeding",
            "Document counseling content",
            "Refer to lactation consultant if needed",
        ],
        "frequency_limit": "per_visit",
    },
    "COUNS_DSMT": {
        "category": "counseling",
        "description": "Diabetes Self-Management Training referral",
        "cpt_codes": ["G0108", "G0109"],
        "payer_types": MEDICARE_MEDICAID,
        "estimated_revenue": 34.50,
        "modifier": None,
        "documentation_checklist": [
            "Confirm diabetes diagnosis",
            "Refer to DSMT-certified program",
            "Document referral order and diagnosis",
            "Follow up on completion",
        ],
        "frequency_limit": "annual",
    },
    "COUNS_CONTRACEPTION": {
        "category": "counseling",
        "description": "Contraception counseling for well-woman visit — coding support",
        "cpt_codes": ["99401"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 0.0,
        "modifier": None,
        "documentation_checklist": [
            "Assess reproductive goals",
            "Discuss contraceptive options",
            "Document shared decision-making",
        ],
        "frequency_limit": "annual",
    },
    "COUNS_SKIN_CANCER": {
        "category": "counseling",
        "description": "Skin cancer prevention counseling for fair-skinned persons 6mo-24y",
        "cpt_codes": ["99401"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 0.0,
        "modifier": None,
        "documentation_checklist": [
            "Assess skin type and UV exposure",
            "Counsel on sun-protective behaviors",
            "Document counseling for USPSTF measure",
        ],
        "frequency_limit": "annual",
    },

    # =====================================================================
    # SCREENING (screening.py)
    # =====================================================================
    "SCREEN_DEVELOPMENTAL": {
        "category": "screening",
        "description": "Developmental screening at 9/18/24/30 months per Bright Futures",
        "cpt_codes": ["96110"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 10.21,
        "modifier": None,
        "documentation_checklist": [
            "Administer ASQ-3 or M-CHAT",
            "Score and interpret",
            "Document results and discuss with caregiver",
            "Refer to early intervention if abnormal",
        ],
        "frequency_limit": "per_visit",
    },
    "SCREEN_SUBSTANCE": {
        "category": "screening",
        "description": "SBIRT — substance use screening and brief intervention for adults 18+",
        "cpt_codes": ["99408", "99409"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 37.24,
        "modifier": None,
        "documentation_checklist": [
            "Administer DAST-10 or NIDA Quick Screen",
            "Score and interpret",
            "Brief intervention if positive",
            "Refer to treatment if indicated",
            "Select 99408 (15-30 min) or 99409 (>30 min)",
        ],
        "frequency_limit": "annual",
    },
    "SCREEN_MATERNAL_DEPRESSION": {
        "category": "screening",
        "description": "Maternal depression screening at well-baby visits — Edinburgh/PHQ-9",
        "cpt_codes": ["96127"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 5.44,
        "modifier": None,
        "documentation_checklist": [
            "Administer Edinburgh or PHQ-9 to mother",
            "Score and interpret",
            "Document in infant chart",
            "Refer mother if positive",
        ],
        "frequency_limit": "per_visit",
    },

    # =====================================================================
    # SDOH (sdoh.py)
    # =====================================================================
    "SDOH_IPV": {
        "category": "sdoh",
        "description": "IPV screening for women of reproductive age at preventive visits",
        "cpt_codes": ["99420"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 0.0,
        "modifier": None,
        "documentation_checklist": [
            "Administer IPV screening tool",
            "Document screening result",
            "Provide resources/referral if positive",
        ],
        "frequency_limit": "annual",
    },
    "SDOH_HRA": {
        "category": "sdoh",
        "description": "HRA compliance checker — verify Health Risk Assessment for AWV",
        "cpt_codes": ["G0136"],
        "payer_types": MEDICARE_ONLY,
        "estimated_revenue": 0.0,
        "modifier": None,
        "documentation_checklist": [
            "Verify HRA instrument completed by patient",
            "Review HRA results",
            "Document SDOH findings in chart",
            "Address identified social needs",
        ],
        "frequency_limit": "annual",
    },

    # =====================================================================
    # PEDIATRIC (pediatric.py)
    # =====================================================================
    "PEDS_WELLCHILD": {
        "category": "pediatric",
        "description": "Well-child visit per Bright Futures periodicity schedule",
        "cpt_codes": ["99381", "99382", "99383", "99384", "99391", "99392", "99393", "99394"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 95.0,
        "modifier": None,
        "documentation_checklist": [
            "Age-appropriate history",
            "Complete physical exam",
            "Growth chart/BMI",
            "Developmental surveillance",
            "Anticipatory guidance",
            "Immunization review",
        ],
        "frequency_limit": "per_visit",
    },
    "PEDS_LEAD": {
        "category": "pediatric",
        "description": "Venous lead screening at 12 and 24 months — Medicaid mandatory",
        "cpt_codes": ["83655", "36415"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 10.72,
        "modifier": None,
        "documentation_checklist": [
            "Order venous lead level (83655)",
            "Venipuncture (36415)",
            "Document risk factors if applicable",
        ],
        "frequency_limit": "annual",
    },
    "PEDS_ANEMIA": {
        "category": "pediatric",
        "description": "Hemoglobin screening at 12 months per AAP/Bright Futures",
        "cpt_codes": ["85018", "36415"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 6.28,
        "modifier": None,
        "documentation_checklist": [
            "Order hemoglobin (85018)",
            "Venipuncture (36415)",
            "Assess iron intake/risk factors",
        ],
        "frequency_limit": "once",
    },
    "PEDS_DYSLIPIDEMIA": {
        "category": "pediatric",
        "description": "Universal dyslipidemia screening — ages 9-11 and 17-21 per NHLBI",
        "cpt_codes": ["80061", "36415"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 21.39,
        "modifier": None,
        "documentation_checklist": [
            "Order fasting lipid panel (80061)",
            "Venipuncture (36415)",
            "Assess family history of CVD",
            "Document BMI",
        ],
        "frequency_limit": "once",
    },
    "PEDS_FLUORIDE": {
        "category": "pediatric",
        "description": "Fluoride varnish application for children through age 5",
        "cpt_codes": ["99188"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 25.16,
        "modifier": None,
        "documentation_checklist": [
            "Verify erupted teeth present",
            "Apply fluoride varnish",
            "Document number of teeth treated",
            "Provide caregiver instructions",
        ],
        "frequency_limit": "quarterly",
    },
    "PEDS_VISION": {
        "category": "pediatric",
        "description": "Instrument-based vision screening ages 3-5 per USPSTF",
        "cpt_codes": ["99173", "99174", "99177"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 11.60,
        "modifier": None,
        "documentation_checklist": [
            "Perform instrument-based screening or Snellen chart",
            "Document results bilateral",
            "Refer if abnormal",
        ],
        "frequency_limit": "annual",
    },
    "PEDS_HEARING": {
        "category": "pediatric",
        "description": "Hearing screening per Bright Futures periodicity",
        "cpt_codes": ["92551", "92552", "92567"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 11.10,
        "modifier": None,
        "documentation_checklist": [
            "Perform pure tone screening",
            "Document pass/fail bilateral",
            "Refer if abnormal findings",
        ],
        "frequency_limit": "annual",
    },
    "PEDS_MATERNAL_DEPRESSION": {
        "category": "pediatric",
        "description": "Maternal depression screening at well-baby visits — patient <12mo",
        "cpt_codes": ["96127"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 5.44,
        "modifier": None,
        "documentation_checklist": [
            "Administer Edinburgh/PHQ-9 to mother",
            "Score and interpret",
            "Document result in infant chart",
            "Refer mother if positive",
        ],
        "frequency_limit": "per_visit",
    },

    # =====================================================================
    # MISC (misc.py)
    # =====================================================================
    "MISC_AFTER_HOURS": {
        "category": "misc",
        "description": "After-hours encounter add-on — outside M-F 8a-5p",
        "cpt_codes": ["99050", "99051", "99053"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 28.0,
        "modifier": None,
        "documentation_checklist": [
            "Document encounter time",
            "Add after-hours code to claim",
            "Bill with primary E/M code",
        ],
        "frequency_limit": "per_visit",
    },
    "MISC_CARE_PLAN_OVERSIGHT": {
        "category": "misc",
        "description": "Care plan oversight for home health/hospice patient",
        "cpt_codes": ["99339", "99340"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 80.0,
        "modifier": None,
        "documentation_checklist": [
            "Document time spent on oversight",
            "Review and update care plan",
            "Communicate with home health/hospice agency",
            "Bill monthly (15-29 min → 99339, 30+ min → 99340)",
        ],
        "frequency_limit": "monthly",
    },
    "MISC_PREP": {
        "category": "misc",
        "description": "PrEP quarterly follow-up — HIV-negative high-risk patients",
        "cpt_codes": ["99213", "87389"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 75.0,
        "modifier": None,
        "documentation_checklist": [
            "HIV Ag/Ab test (87389)",
            "Renal function panel",
            "STI screening if indicated",
            "Medication adherence counseling",
            "Refill PrEP prescription",
        ],
        "frequency_limit": "quarterly",
    },
    "MISC_GDM_SCREENING": {
        "category": "misc",
        "description": "Gestational diabetes screening at 24-28 weeks gestation",
        "cpt_codes": ["82947", "82951"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 15.37,
        "modifier": None,
        "documentation_checklist": [
            "Order 1-hour GTT or 3-hour GTT",
            "Patient instructions for fasting/glucose load",
            "Document gestational age",
            "Follow up on results",
        ],
        "frequency_limit": "per_pregnancy",
    },
    "MISC_PERINATAL_DEPRESSION": {
        "category": "misc",
        "description": "Perinatal depression screening — pregnant/postpartum women",
        "cpt_codes": ["96161"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 5.44,
        "modifier": None,
        "documentation_checklist": [
            "Administer Edinburgh or PHQ-9",
            "Score and interpret",
            "Document result",
            "Refer if positive",
            "Plan follow-up",
        ],
        "frequency_limit": "quarterly",
    },
    "MISC_STATIN_COUNSELING": {
        "category": "misc",
        "description": "Statin therapy counseling — ASCVD risk 10%+, not on statin",
        "cpt_codes": ["99401"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 0.0,
        "modifier": None,
        "documentation_checklist": [
            "Calculate and document ASCVD risk score",
            "Discuss statin benefits/risks",
            "Document shared decision-making",
            "Prescribe statin if accepted",
            "Address lifestyle modifications",
        ],
        "frequency_limit": "annual",
    },
    "MISC_FOLIC_ACID": {
        "category": "misc",
        "description": "Folic acid supplementation counseling — female reproductive age",
        "cpt_codes": ["99401"],
        "payer_types": ALL_PAYERS,
        "estimated_revenue": 0.0,
        "modifier": None,
        "documentation_checklist": [
            "Assess pregnancy planning status",
            "Counsel on folic acid 400-800 mcg daily",
            "Document counseling",
            "Prescribe if appropriate",
        ],
        "frequency_limit": "annual",
    },
}

BILLING_RULE_SEEDS = {}

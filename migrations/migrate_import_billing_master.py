"""
Phase 16.4 — Import Billing Master List

Loads CareCompanion_Billing_Master_List CSV into the BillingRule table.
Upserts on opportunity_code — updates existing rules with master list
revenue/documentation/payer data, inserts new rules not yet in seed.

Idempotent: safe to run multiple times.
"""

import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Documents", "_archive",
    "billing_master_list_export.csv",
)

# -----------------------------------------------------------------------
# Map CSV "Billing Opportunity" names → existing opportunity_code values
# Unmapped entries get auto-generated codes from _derive_code()
# -----------------------------------------------------------------------
NAME_TO_CODE = {
    "Initial AWV": "AWV_INITIAL",
    "Subsequent AWV": "AWV_SUBSEQUENT",
    "Initial Preventive Physical Exam (IPPE / Welcome to Medicare)": "AWV_IPPE",
    "Advance Care Planning (as part of AWV)": "ACP_STANDALONE",
    "Personalized Prevention Plan of Service (PPPS) Update": "AWV_PPPS",
    "Well-Woman Visit": "PREVENTIVE_WELL_WOMAN",
    "Wellness Exam (Periodic Preventive Medicine)": "PREVENTIVE_EM",
    "Prolonged Services (Office)": "PROLONGED_SERVICE",
    "Prolonged Preventive Services": "PROLONGED_PREVENTIVE",
    "CCM \u2014 Standard (20+ min)": "CCM",
    "CCM \u2014 Complex (60+ min)": "CCM_COMPLEX",
    "CCM \u2014 Additional 30 min": "CCM_ADDITIONAL",
    "Principal Care Management (PCM)": "PCM_PRINCIPAL_CARE",
    "TCM \u2014 High Complexity": "TCM_HIGH",
    "TCM \u2014 Moderate Complexity": "TCM",
    "General BHI": "BHI",
    "Collaborative Care Model (CoCM) \u2014 Initial": "COCM_INITIAL",
    "Collaborative Care Model (CoCM) \u2014 Subsequent": "COCM_SUBSEQUENT",
    "CoCM \u2014 Additional 30 min": "COCM_ADDITIONAL_30",
    "Depression Screening (PHQ-9, PHQ-2)": "SCREEN_DEPRESSION",
    "Anxiety Screening (GAD-7)": "SCREEN_ANXIETY",
    "Developmental/Autism Screening (ASQ, M-CHAT)": "SCREEN_DEVELOPMENTAL",
    "Emotional/Behavioral Assessment (PSC, CRAFFT)": "SCREEN_EMOTIONAL",
    "Alcohol Misuse Screening (AUDIT-C)": "ALCOHOL_SCREENING",
    "Substance Use Screening (DAST-10)": "SCREEN_SUBSTANCE",
    "Tobacco Use Screening & Counseling": "TOBACCO_CESSATION",
    "Cognitive Assessment / Screening": "COGNITIVE_ASSESSMENT",
    "Maternal Depression Screening (Edinburgh, PHQ-9)": "SCREEN_MATERNAL_DEPRESSION",
    "Cardiovascular Disease Screening (Lipid Panel)": "SCREEN_CVD_LIPID",
    "Diabetes Screening (Glucose / A1C)": "SCREEN_DIABETES",
    "Hepatitis C Screening": "SCREEN_HEPC",
    "Hepatitis B Screening": "SCREEN_HEPB",
    "HIV Screening": "SCREEN_HIV",
    "STI Screening (Chlamydia, Gonorrhea, Syphilis)": "STI_SCREENING",
    "Colorectal Cancer Screening (FIT, Cologuard, Colonoscopy)": "SCREEN_COLORECTAL",
    "Lung Cancer Screening (LDCT)": "SCREEN_LUNG",
    "Cervical Cancer Screening (Pap/HPV)": "SCREEN_CERVICAL",
    "Screening Mammography": "SCREEN_MAMMOGRAPHY",
    "Bone Density Screening (DEXA)": "SCREEN_DEXA",
    "Abdominal Aortic Aneurysm Screening (Ultrasound)": "SCREEN_AAA",
    "Tuberculosis Screening": "SCREEN_TB",
    "Influenza Vaccine": "VACCINE_FLU",
    "Pneumococcal Vaccine (PCV20, PPSV23)": "VACCINE_PNEUMO",
    "Shingles Vaccine (Shingrix)": "VACCINE_SHINGLES",
    "Tdap / Td Vaccine": "VACCINE_TDAP",
    "HPV Vaccine (Gardasil 9)": "IMM_HPV",
    "Hepatitis B Vaccine": "IMM_HEPB",
    "Hepatitis A Vaccine": "IMM_HEPA",
    "COVID-19 Vaccine": "VACCINE_COVID",
    "RSV Vaccine (Abrysvo/Arexvy)": "IMM_RSV",
    "Meningococcal Vaccine (MenACWY, MenB)": "IMM_MENACWY",
    "Obesity Screening & Counseling (Adults)": "OBESITY_NUTRITION",
    "Obesity Screening & Counseling (Pediatric)": "OBESITY_PEDS",
    "Medical Nutrition Therapy (MNT)": "COUNS_MNT",
    "Diabetes Self-Management Training (DSMT)": "COUNS_DSMT",
    "Intensive Behavioral Therapy for CVD": "COUNS_CVD_IBT",
    "Tobacco Cessation Counseling (Medicare-specific)": "TOBACCO_CESSATION_MEDICARE",
    "Contraception Counseling": "COUNS_CONTRACEPTION",
    "Breastfeeding Support & Counseling": "COUNS_BREASTFEED",
    "Skin Cancer Behavioral Counseling": "COUNS_SKIN_CANCER",
    "Falls Prevention Counseling (Older Adults)": "COUNS_FALLS",
    "Remote Patient Monitoring (RPM)": "RPM",
    "Remote Therapeutic Monitoring (RTM)": "RTM",
    "Annual Depression Screening (Medicare standalone)": "SCREEN_DEPRESSION_MEDICARE",
    "Glaucoma Screening (Medicare)": "SCREEN_GLAUCOMA",
    "Screening Pelvic Examination": "SCREEN_PELVIC",
    "Medicare Diabetes Prevention Program (MDPP)": "COUNS_MDPP",
    "EKG/ECG (12-lead)": "PROC_EKG",
    "Spirometry": "PROC_SPIROMETRY",
    "Point-of-Care Testing (CLIA-waived)": "PROC_POCT",
    "Venipuncture / Blood Draw": "PROC_VENIPUNCTURE",
    "Injection Administration": "PROC_INJECTION_ADMIN",
    "Nebulizer Treatment": "PROC_NEBULIZER",
    "Pulse Oximetry": "PROC_PULSE_OX",
    "HbA1c (Diabetes Management)": "MON_A1C",
    "Lipid Panel (Statin Monitoring)": "MON_LIPID",
    "Thyroid Function (TSH)": "MON_TSH",
    "Renal Function Panel / BMP / CMP": "MON_RENAL",
    "CBC (Complete Blood Count)": "MON_CBC",
    "INR (Warfarin Monitoring)": "MON_INR",
    "Hepatic Function Panel": "MON_LFT",
    "Urine Albumin/Creatinine Ratio (UACR)": "MON_UACR",
    "Vitamin D Level": "MON_VITD",
    "Telephone E/M (Established Patient)": "TELE_PHONE_EM",
    "Online Digital E/M (Patient Portal)": "TELE_DIGITAL_EM",
    "Interprofessional Consultation": "TELE_INTERPROF",
    "SDOH Screening / Assessment": "SDOH_SCREEN",
    "Intimate Partner Violence Screening": "SDOH_IPV",
    "Health Risk Assessment (HRA)": "SDOH_HRA",
    "Well-Child Visit (Bright Futures)": "PEDS_WELLCHILD",
    "Lead Screening": "PEDS_LEAD",
    "Anemia Screening (Hgb/Hct)": "PEDS_ANEMIA",
    "Dyslipidemia Screening": "PEDS_DYSLIPIDEMIA",
    "Fluoride Varnish Application": "PEDS_FLUORIDE",
    "Oral Fluoride Supplementation": "PEDS_FLUORIDE_RX",
    "Vision Screening": "PEDS_VISION",
    "Hearing Screening": "PEDS_HEARING",
    "Modifier 25 (Separate E/M + Procedure)": "MODIFIER_25_PROMPT",
    "After-Hours / Weekend / Holiday Premium": "MISC_AFTER_HOURS",
    "Care Plan Oversight": "MISC_CARE_PLAN_OVERSIGHT",
    "Chronic Pain Management (non-procedure)": "MISC_CHRONIC_PAIN",
    "PrEP (Pre-Exposure Prophylaxis) Management": "MISC_PREP",
    "Preeclampsia Prevention (Low-dose Aspirin)": "MISC_PREECLAMPSIA",
    "Folic Acid Supplementation Counseling": "MISC_FOLIC_ACID",
    "Statin Preventive Medication Counseling": "MISC_STATIN_COUNSELING",
    "Gestational Diabetes Screening": "MISC_GDM_SCREENING",
    "Perinatal Depression Screening & Counseling": "MISC_PERINATAL_DEPRESSION",
    "Bacteriuria Screening (Pregnant Women)": "MISC_BACTERIURIA",
}

# Category mapping from CSV category names to short DB category keys
CATEGORY_MAP = {
    "Annual Wellness Visit (AWV)": "awv",
    "Preventive Visit": "preventive",
    "E/M Add-On Codes": "em_addons",
    "Chronic Care Management (CCM)": "ccm",
    "Transitional Care Management (TCM)": "tcm",
    "Behavioral Health Integration (BHI)": "bhi",
    "Screening Instruments": "screening",
    "Preventive Lab Screenings": "preventive_labs",
    "Immunizations": "immunizations",
    "Counseling & Education": "counseling",
    "Care Management Services": "care_management",
    "In-Office Procedures": "procedures",
    "Chronic Disease Monitoring": "chronic_monitoring",
    "Telehealth & Communication": "telehealth",
    "SDOH & Risk Assessment": "sdoh",
    "Pediatric Add-Ons": "pediatric",
    "Often Overlooked": "misc",
}

# Payer type mapping
PAYER_MAP = {
    "Medicare": ["medicare_b", "medicare_advantage"],
    "All Payers": ["medicare_b", "medicare_advantage", "medicaid", "commercial"],
    "Commercial / Medicaid (with ACA)": ["medicaid", "commercial"],
    "Commercial (with ACA preventive benefit)": ["commercial"],
    "Medicaid": ["medicaid"],
    "Medicaid (mandatory in many states)": ["medicaid"],
}

FREQ_MAP = {
    "Annual": "annual",
    "Monthly": "monthly",
    "Once": "once",
    "One-time": "once",
    "Per qualifying visit": "per_visit",
    "Per visit": "per_visit",
    "Per pregnancy": "per_pregnancy",
}


def _parse_revenue(text):
    """Parse '$175' or '$1,200' → float. Returns 0.0 on failure."""
    text = (text or "").strip().replace("$", "").replace(",", "")
    try:
        return float(text)
    except (ValueError, TypeError):
        return 0.0


def _parse_codes(text):
    """Extract CPT/HCPCS code-like tokens from a string."""
    tokens = re.findall(r'\b[0-9A-Z]{4,7}\b', (text or "").upper())
    # Filter to valid-looking codes
    return [t for t in tokens if re.match(r'^[0-9]{4,5}$|^[A-Z]\d{3,5}$', t)]


def _parse_frequency(text):
    """Map frequency text to a canonical value."""
    text = (text or "").strip()
    for key, val in FREQ_MAP.items():
        if text.lower().startswith(key.lower()):
            return val
    return "per_visit"


def _parse_payer(text):
    """Map payer text to a list of payer types."""
    text = (text or "").strip()
    for key, val in PAYER_MAP.items():
        if key.lower() in text.lower():
            return val
    if "medicare" in text.lower():
        return ["medicare_b", "medicare_advantage"]
    if "medicaid" in text.lower():
        return ["medicaid"]
    return ["medicare_b", "medicare_advantage", "medicaid", "commercial"]


def _derive_code(name):
    """Generate an opportunity_code from a billing opportunity name."""
    # Strip parenthetical content, normalize
    clean = re.sub(r'\(.*?\)', '', name).strip()
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', clean)
    parts = clean.upper().split()[:4]
    return "_".join(parts)


def run():
    from app import create_app
    from models import db
    from models.billing import BillingRule

    app = create_app()
    with app.app_context():
        if not os.path.exists(CSV_PATH):
            print(f"[SKIP] Master list CSV not found: {CSV_PATH}")
            return

        # Read CSV
        with open(CSV_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Filter to rows with CPT codes
        data_rows = [r for r in rows if (r.get("CPT / HCPCS Code(s)") or "").strip()]
        print(f"[MASTER] {len(data_rows)} billing opportunities in CSV")

        inserted = 0
        updated = 0
        skipped = 0

        for row in data_rows:
            name = (row.get("Billing Opportunity") or "").strip()
            # Handle encoding artifacts (em-dash replacements)
            for artifact in ["\u2014", "\u00e2\u0080\u0094", "ΓÇö"]:
                name = name.replace(artifact, "\u2014")

            opp_code = NAME_TO_CODE.get(name)
            if not opp_code:
                # Try without the em-dash normalization
                for k, v in NAME_TO_CODE.items():
                    if k.replace("\u2014", "").strip() == name.replace("\u2014", "").strip():
                        opp_code = v
                        break
            if not opp_code:
                opp_code = _derive_code(name)

            category = CATEGORY_MAP.get(
                (row.get("Category") or "").strip(), "misc"
            )
            cpt_codes = _parse_codes(row.get("CPT / HCPCS Code(s)") or "")
            payer_types = _parse_payer(row.get("Payer Type") or "")
            revenue = _parse_revenue(row.get("Est. Revenue per Event") or "")
            modifier = (row.get("Modifier") or "").strip() or None
            freq = _parse_frequency(row.get("Frequency") or "")
            docs = (row.get("Documentation Requirements") or "").strip()
            description = name
            notes = (row.get("Notes / Gotchas") or "").strip()
            if notes:
                description = f"{name}. {notes}"

            # Build documentation checklist from requirements text
            checklist = []
            if docs:
                # Split on commas or semicolons for structured checklist
                items = re.split(r'[;,]', docs)
                checklist = [item.strip() for item in items if item.strip()]

            existing = BillingRule.query.filter_by(
                opportunity_code=opp_code
            ).first()

            if existing:
                # Update fields from master list if they provide more info
                changed = False
                if revenue > 0 and existing.estimated_revenue != revenue:
                    existing.estimated_revenue = revenue
                    changed = True
                if cpt_codes and existing.cpt_codes != json.dumps(cpt_codes):
                    existing.cpt_codes = json.dumps(cpt_codes)
                    changed = True
                if payer_types and existing.payer_types != json.dumps(payer_types):
                    existing.payer_types = json.dumps(payer_types)
                    changed = True
                if checklist and existing.documentation_checklist != json.dumps(checklist):
                    existing.documentation_checklist = json.dumps(checklist)
                    changed = True
                if modifier and existing.modifier != modifier:
                    existing.modifier = modifier
                    changed = True
                if changed:
                    updated += 1
                else:
                    skipped += 1
            else:
                new_rule = BillingRule(
                    opportunity_code=opp_code,
                    category=category,
                    description=description[:500] if description else name,
                    cpt_codes=json.dumps(cpt_codes) if cpt_codes else None,
                    payer_types=json.dumps(payer_types) if payer_types else None,
                    estimated_revenue=revenue,
                    modifier=modifier,
                    documentation_checklist=json.dumps(checklist) if checklist else None,
                    frequency_limit=freq,
                    is_active=True,
                )
                db.session.add(new_rule)
                inserted += 1

        db.session.commit()
        print(f"[MASTER] Inserted {inserted}, updated {updated}, skipped {skipped}")

        # Final count
        total = BillingRule.query.count()
        print(f"[MASTER] Total billing rules now: {total}")


if __name__ == "__main__":
    run()

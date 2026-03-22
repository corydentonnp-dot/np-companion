"""
Migration: Create payer_coverage_matrix table + seed data
File: migrations/migrate_add_payer_coverage.py
Phase 28.2 + 28.3

Creates the payer_coverage_matrix table and seeds it with coverage rules
extracted from:
  - Medicare payer coding guide (G-codes, preventive zero cost-share)
  - Private payer coding guide (modifier 33, ACA preventive benefit)
  - HealthCare.gov preventive care coverage references
  - CareCompanion Master Billing List CSV

Usage:
    venv\\Scripts\\python.exe migrations/migrate_add_payer_coverage.py
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Seed data — extracted from coding guides + HealthCare.gov references
# ------------------------------------------------------------------
# Each tuple: (cpt_code, payer_type, is_covered, cost_share_waived,
#              modifier_required, frequency_limit, age_range,
#              sex_requirement, coverage_notes, source_document)
SEED_ROWS = [
    # ===== AWV / IPPE — Medicare (from Medicare coding guide) =====
    ("G0438", "medicare_b", True, True, None, "1x/year", "18+", None,
     "Initial AWV — no copay or deductible", "medicare-payer-coding-guide"),
    ("G0439", "medicare_b", True, True, None, "1x/year", "18+", None,
     "Subsequent AWV — no copay or deductible", "medicare-payer-coding-guide"),
    ("G0402", "medicare_b", True, True, None, "1x/lifetime", "18+", None,
     "IPPE (Welcome to Medicare) — first 12 months Part B", "medicare-payer-coding-guide"),
    ("G0438", "medicare_advantage", True, True, None, "1x/year", "18+", None,
     "Initial AWV — coverage varies by MA plan", "medicare-payer-coding-guide"),
    ("G0439", "medicare_advantage", True, True, None, "1x/year", "18+", None,
     "Subsequent AWV — coverage varies by MA plan", "medicare-payer-coding-guide"),

    # ===== ACP — billed with AWV =====
    ("99497", "medicare_b", True, True, None, "1x/year", "18+", None,
     "ACP first 30 min — $0 copay when billed with AWV", "medicare-payer-coding-guide"),
    ("99498", "medicare_b", True, True, None, "1x/year", "18+", None,
     "ACP additional 30 min — $0 copay when billed with AWV", "medicare-payer-coding-guide"),
    ("99497", "commercial", True, False, None, "1x/year", "18+", None,
     "ACP — standard cost-sharing unless billed with preventive visit", "private-payer-coding-guide"),

    # ===== G2211 Complexity Add-On — Medicare Part B only =====
    ("G2211", "medicare_b", True, False, None, "per E/M visit", "18+", None,
     "Complexity add-on — Medicare Part B only, ~$16/visit", "medicare-payer-coding-guide"),
    ("G2211", "medicare_advantage", False, False, None, None, None, None,
     "G2211 NOT covered by Medicare Advantage", "medicare-payer-coding-guide"),
    ("G2211", "commercial", False, False, None, None, None, None,
     "G2211 NOT covered by commercial payers", "private-payer-coding-guide"),

    # ===== Screenings — Medicare G-codes =====
    ("G0442", "medicare_b", True, True, None, "1x/year", "18+", None,
     "Alcohol screening — no copay (Medicare preventive)", "medicare-payer-coding-guide"),
    ("G0443", "medicare_b", True, True, None, "4x/year", "18+", None,
     "Alcohol counseling — no copay (Medicare preventive)", "medicare-payer-coding-guide"),
    ("G0444", "medicare_b", True, True, None, "1x/year", "12+", None,
     "Depression screening — no copay (Medicare preventive)", "medicare-payer-coding-guide"),
    ("G0447", "medicare_b", True, True, None, "1x/year", "18+", None,
     "Obesity counseling — no copay (Medicare preventive, BMI ≥30)", "medicare-payer-coding-guide"),
    ("G0296", "medicare_b", True, True, None, "per visit", "55-80", None,
     "Lung cancer screening counseling — LDCT eligible", "medicare-payer-coding-guide"),

    # ===== Screenings — Commercial/Medicaid (modifier 33, ACA) =====
    ("99408", "commercial", True, True, "33", "1x/year", "18+", None,
     "Alcohol SBIRT — $0 copay with modifier 33 (ACA preventive)", "private-payer-coding-guide"),
    ("99408", "medicaid", True, True, "33", "1x/year", "18+", None,
     "Alcohol SBIRT — $0 copay with modifier 33 (ACA preventive)", "private-payer-coding-guide"),
    ("96127", "commercial", True, True, "33", "1x/year", "12+", None,
     "Depression/anxiety screening — $0 with modifier 33", "private-payer-coding-guide"),
    ("96127", "medicaid", True, True, "33", "1x/year", "12+", None,
     "Depression/anxiety screening — $0 with modifier 33", "private-payer-coding-guide"),
    ("99406", "commercial", True, True, "33", "2x/year", "18+", None,
     "Tobacco counseling 3-10 min — ACA preventive benefit", "private-payer-coding-guide"),
    ("99407", "commercial", True, True, "33", "2x/year", "18+", None,
     "Tobacco counseling >10 min — ACA preventive benefit", "private-payer-coding-guide"),
    ("99406", "medicaid", True, True, "33", "2x/year", "18+", None,
     "Tobacco counseling 3-10 min — ACA preventive benefit", "private-payer-coding-guide"),
    ("99407", "medicaid", True, True, "33", "2x/year", "18+", None,
     "Tobacco counseling >10 min — ACA preventive benefit", "private-payer-coding-guide"),
    ("97802", "commercial", True, True, "33", "per visit", "18+", None,
     "Nutrition therapy initial — ACA preventive for obesity/DM", "private-payer-coding-guide"),
    ("97803", "commercial", True, True, "33", "per visit", "18+", None,
     "Nutrition therapy subsequent — ACA preventive", "private-payer-coding-guide"),

    # ===== Preventive Well-Woman — Commercial =====
    ("99395", "commercial", True, True, "33", "1x/year", "18-39", "F",
     "Well-woman visit (est, 18-39) — ACA preventive", "private-payer-coding-guide"),
    ("99396", "commercial", True, True, "33", "1x/year", "40-64", "F",
     "Well-woman visit (est, 40-64) — ACA preventive", "private-payer-coding-guide"),
    ("99397", "commercial", True, True, "33", "1x/year", "65+", "F",
     "Well-woman visit (est, 65+) — ACA preventive", "private-payer-coding-guide"),
    ("99395", "medicaid", True, True, "33", "1x/year", "18-39", "F",
     "Well-woman visit — Medicaid preventive", "private-payer-coding-guide"),

    # ===== Periodic Wellness — Commercial =====
    ("99395", "commercial", True, True, "33", "1x/year", "18-39", None,
     "Periodic wellness (est, 18-39) — ACA preventive", "private-payer-coding-guide"),
    ("99396", "commercial", True, True, "33", "1x/year", "40-64", None,
     "Periodic wellness (est, 40-64) — ACA preventive", "private-payer-coding-guide"),
    ("99397", "commercial", True, True, "33", "1x/year", "65+", None,
     "Periodic wellness (est, 65+) — ACA preventive", "private-payer-coding-guide"),

    # ===== CCM/BHI/CoCM — Medicare =====
    ("99490", "medicare_b", True, False, None, "1x/month", "18+", None,
     "CCM initial 20 min — standard cost-sharing applies", "medicare-payer-coding-guide"),
    ("99491", "medicare_b", True, False, None, "1x/month", "18+", None,
     "CCM complex 30 min — standard cost-sharing", "medicare-payer-coding-guide"),
    ("99484", "medicare_b", True, False, None, "1x/month", "18+", None,
     "BHI care management — standard cost-sharing", "medicare-payer-coding-guide"),
    ("99492", "medicare_b", True, False, None, "1x/month", "18+", None,
     "CoCM initial month — psychiatric collaborative care", "medicare-payer-coding-guide"),
    ("99493", "medicare_b", True, False, None, "1x/month", "18+", None,
     "CoCM subsequent month", "medicare-payer-coding-guide"),

    # ===== TCM — Medicare =====
    ("99495", "medicare_b", True, False, None, "per discharge", "18+", None,
     "TCM moderate complexity — contact within 2 business days", "medicare-payer-coding-guide"),
    ("99496", "medicare_b", True, False, None, "per discharge", "18+", None,
     "TCM high complexity — contact within 2 business days", "medicare-payer-coding-guide"),
    ("99495", "commercial", True, False, None, "per discharge", "18+", None,
     "TCM — check plan coverage; many commercial plans cover", "private-payer-coding-guide"),

    # ===== Vaccine Admin — Medicare G-codes =====
    ("G0008", "medicare_b", True, True, None, "1x/season", "18+", None,
     "Flu vaccine admin — no copay (Medicare Part B)", "medicare-payer-coding-guide"),
    ("G0009", "medicare_b", True, True, None, "per schedule", "18+", None,
     "Pneumococcal vaccine admin — no copay", "medicare-payer-coding-guide"),
    ("G0010", "medicare_b", True, True, None, "per schedule", "18+", None,
     "Hepatitis B vaccine admin — no copay", "medicare-payer-coding-guide"),
    ("90471", "commercial", True, True, "33", "per schedule", "0+", None,
     "Vaccine admin first dose — ACA preventive benefit", "private-payer-coding-guide"),
    ("90472", "commercial", True, True, "33", "per schedule", "0+", None,
     "Vaccine admin each additional — ACA preventive benefit", "private-payer-coding-guide"),

    # ===== RPM — Medicare =====
    ("99453", "medicare_b", True, False, None, "1x setup", "18+", None,
     "RPM device setup — standard cost-sharing", "medicare-payer-coding-guide"),
    ("99454", "medicare_b", True, False, None, "1x/month", "18+", None,
     "RPM device supply — 16+ readings/month required", "medicare-payer-coding-guide"),
    ("99457", "medicare_b", True, False, None, "1x/month", "18+", None,
     "RPM treatment management first 20 min", "medicare-payer-coding-guide"),

    # ===== Prolonged Services =====
    ("99417", "medicare_b", True, False, None, "per visit", "18+", None,
     "Prolonged services each +15 min beyond highest E/M", "medicare-payer-coding-guide"),
    ("G0513", "medicare_b", True, True, None, "per visit", "18+", None,
     "Prolonged preventive first 30 min — no copay with AWV", "medicare-payer-coding-guide"),

    # ===== HealthCare.gov Preventive Services (Phase 28.3) =====
    # Source: healthcare.gov/coverage/preventive-care-benefits/
    ("77067", "commercial", True, True, "33", "1x/year", "40+", "F",
     "Mammography screening — ACA preventive, no cost-sharing", "healthcare-gov-preventive"),
    ("77067", "medicare_b", True, True, None, "1x/year", "40+", "F",
     "Mammography screening — Medicare Part B, no copay", "medicare-payer-coding-guide"),
    ("45378", "commercial", True, True, "33", "1x/10yr", "45-75", None,
     "Colonoscopy screening — ACA preventive", "healthcare-gov-preventive"),
    ("45378", "medicare_b", True, True, None, "1x/10yr", "45+", None,
     "Colonoscopy screening — Medicare preventive, no copay", "medicare-payer-coding-guide"),

    # Diabetes screening
    ("82947", "commercial", True, True, "33", "1x/year", "40+", None,
     "Glucose screening — ACA preventive for overweight/obese adults", "healthcare-gov-preventive"),
    ("83036", "commercial", True, True, "33", "1x/year", "40+", None,
     "A1C screening — ACA preventive for diabetes risk", "healthcare-gov-preventive"),

    # Lipid panel
    ("80061", "commercial", True, True, "33", "1x/5yr", "20+", None,
     "Lipid panel — ACA preventive for CVD risk assessment", "healthcare-gov-preventive"),
    ("80061", "medicare_b", True, True, None, "1x/5yr", "20+", None,
     "Lipid panel — Medicare cardiovascular screening", "medicare-payer-coding-guide"),

    # STI screening
    ("86780", "commercial", True, True, "33", "1x/year", "15-65", None,
     "HIV screening — ACA preventive, USPSTF A recommendation", "healthcare-gov-preventive"),
    ("87491", "commercial", True, True, "33", "1x/year", "15-24", "F",
     "Chlamydia screening — ACA preventive for sexually active women", "healthcare-gov-preventive"),
    ("87591", "commercial", True, True, "33", "1x/year", "15-24", "F",
     "Gonorrhea screening — ACA preventive", "healthcare-gov-preventive"),

    # Hepatitis C
    ("86803", "commercial", True, True, "33", "1x/lifetime", "18-79", None,
     "Hep C screening — ACA preventive, USPSTF B recommendation", "healthcare-gov-preventive"),
    ("86803", "medicare_b", True, True, None, "1x/lifetime", "18+", None,
     "Hep C screening — Medicare preventive benefit", "medicare-payer-coding-guide"),

    # Immunizations — HealthCare.gov
    ("90686", "commercial", True, True, "33", "1x/season", "6m+", None,
     "Influenza vaccine — ACA preventive, no cost-sharing", "healthcare-gov-preventive"),
    ("90750", "commercial", True, True, "33", "2 doses", "50+", None,
     "Shingrix vaccine — ACA preventive for 50+", "healthcare-gov-preventive"),
    ("90750", "medicare_b", True, True, None, "2 doses", "50+", None,
     "Shingrix vaccine — Medicare Part D (Part B if in-office admin)", "medicare-payer-coding-guide"),
    ("90732", "commercial", True, True, "33", "per ACIP", "65+", None,
     "Pneumococcal vaccine (PCV20) — ACA preventive", "healthcare-gov-preventive"),
    ("90732", "medicare_b", True, True, None, "per ACIP", "65+", None,
     "Pneumococcal vaccine — Medicare Part B, no copay", "medicare-payer-coding-guide"),

    # Cervical cancer screening
    ("87624", "commercial", True, True, "33", "1x/3yr", "21-65", "F",
     "HPV test — ACA preventive screening", "healthcare-gov-preventive"),
    ("88175", "commercial", True, True, "33", "1x/3yr", "21-65", "F",
     "Pap smear — ACA preventive screening", "healthcare-gov-preventive"),
    ("88175", "medicare_b", True, True, None, "1x/2yr", "21+", "F",
     "Pap smear — Medicare preventive screening", "medicare-payer-coding-guide"),

    # AAA screening
    ("76706", "medicare_b", True, True, None, "1x/lifetime", "65-75", "M",
     "AAA ultrasound screening — Medicare, men who have smoked", "medicare-payer-coding-guide"),

    # Bone density
    ("77080", "commercial", True, True, "33", "1x/2yr", "65+", "F",
     "DEXA scan — ACA preventive for osteoporosis screening", "healthcare-gov-preventive"),
    ("77080", "medicare_b", True, True, None, "1x/2yr", "65+", "F",
     "DEXA scan — Medicare bone density, no copay", "medicare-payer-coding-guide"),

    # SDOH / social determinants — ACA
    ("96160", "commercial", True, True, "33", "per visit", "0+", None,
     "SDOH risk assessment — ACA preventive", "healthcare-gov-preventive"),

    # Lead screening — Medicaid EPSDT
    ("83655", "medicaid", True, True, None, "per EPSDT", "0-6", None,
     "Lead screening — Medicaid mandatory for children ≤6", "healthcare-gov-preventive"),
]


def run_migration(app, db):
    with app.app_context():
        from models.billing import PayerCoverageMatrix  # noqa: F401

        logger.info("Running payer coverage migration (Phase 28.2 + 28.3)...")
        db.create_all()

        from sqlalchemy import inspect as sa_inspect
        tables = sa_inspect(db.engine).get_table_names()
        if "payer_coverage_matrix" not in tables:
            logger.error("  [FAIL] payer_coverage_matrix table not created")
            return False
        logger.info("  [OK] payer_coverage_matrix table exists")

        # Seed data — idempotent upsert by (cpt_code, payer_type, source_document)
        inserted = 0
        skipped = 0
        for row in SEED_ROWS:
            cpt, payer, covered, waived, modifier, freq, age, sex, notes, source = row
            existing = PayerCoverageMatrix.query.filter_by(
                cpt_code=cpt,
                payer_type=payer,
                source_document=source,
            ).first()
            if existing:
                # Update fields if changed
                changed = False
                for attr, val in [
                    ("is_covered", covered), ("cost_share_waived", waived),
                    ("modifier_required", modifier), ("frequency_limit", freq),
                    ("age_range", age), ("sex_requirement", sex),
                    ("coverage_notes", notes),
                ]:
                    if getattr(existing, attr) != val:
                        setattr(existing, attr, val)
                        changed = True
                if changed:
                    skipped += 1  # count as update
                else:
                    skipped += 1
                continue

            entry = PayerCoverageMatrix(
                cpt_code=cpt, payer_type=payer, is_covered=covered,
                cost_share_waived=waived, modifier_required=modifier,
                frequency_limit=freq, age_range=age, sex_requirement=sex,
                coverage_notes=notes, source_document=source,
            )
            db.session.add(entry)
            inserted += 1

        db.session.commit()
        logger.info("  Seed: %d inserted, %d skipped/updated", inserted, skipped)
        total = PayerCoverageMatrix.query.count()
        logger.info("  Total payer_coverage_matrix rows: %d", total)
        return True


if __name__ == "__main__":
    try:
        from app import create_app
        from models import db
    except ImportError as exc:
        logger.error("Import failed: %s", exc)
        sys.exit(1)

    flask_app = create_app()
    success = run_migration(flask_app, db)
    sys.exit(0 if success else 1)

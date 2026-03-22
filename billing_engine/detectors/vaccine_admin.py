"""
CareCompanion — Vaccine Administration Detector
billing_engine/detectors/vaccine_admin.py

Vaccine administration billing: 90471 (first injection) + 90472 (each
additional) plus vaccine product CPTs.

Phase 19B.6 enhancements:
- 6 additional vaccines: HPV, HepB, HepA, RSV, MenACWY, MenB
- Series completion tracking (flag patients overdue for dose 2/3)
- Enforce: always bill BOTH product code AND admin code
"""

from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn
from app.api_config import VACCINE_PRODUCT_CODES


class VaccineAdminDetector(BaseDetector):
    """Vaccine administration billing detector with expanded immunisation support."""

    CATEGORY = "vaccine_admin"
    DESCRIPTION = "Vaccine admin codes plus product CPTs for vaccines given today + series tracking"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        opps = []

        # ── Today's administered vaccines ──
        vaccines_given = pd.get("vaccines_given_today") or []
        if vaccines_given:
            opps.extend(self._detect_admin_today(pd, vaccines_given))

        # ── Series completion tracking ──
        vaccine_series = pd.get("vaccine_series") or []
        age = pd.get("age") or 0
        if vaccine_series or age > 0:
            opps.extend(self._detect_series_gaps(pd, vaccine_series, age))

        return opps

    def _detect_admin_today(self, pd, vaccines_given):
        """Generate admin + product billing for vaccines given today."""
        count = len(vaccines_given)
        codes = ["90471"]
        est_revenue = self._get_rate("90471")

        if count > 1:
            codes.append("90472")
            est_revenue += self._get_rate("90472") * (count - 1)

        vaccine_names = []
        for v in vaccines_given:
            product_cpt = v.get("product_cpt") or ""
            if product_cpt and product_cpt not in codes:
                codes.append(product_cpt)
                est_revenue += self._get_rate(product_cpt)
            vaccine_names.append(v.get("name") or product_cpt)

        eligibility = (
            f"{count} vaccine(s) administered today: {', '.join(vaccine_names)}. "
            "Bill BOTH administration codes AND vaccine product CPTs."
        )

        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="vaccine_admin",
            codes=codes,
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                "For each vaccine: document product name, lot #, expiration date, "
                "injection site (deltoid L/R, thigh L/R), route (IM/SC). "
                "VIS provided and discussed. Patient monitored 15 min. "
                "90471 = first injection admin. 90472 = each additional. "
                "ALWAYS bill product code + admin code together."
            ),
            confidence_level="HIGH",
            insurer_caveat=None,
            insurer_type=insurer,
            documentation_checklist='["Document product name and lot number","Document expiration date","Document injection site and route","Provide VIS to patient","Monitor patient 15 minutes","Bill admin code AND product code"]',
        )
        return [opp]

    def _detect_series_gaps(self, pd, vaccine_series, age):
        """Detect patients overdue for next dose in a multi-dose series."""
        opps = []
        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")

        # Build set of series already tracked in patient data
        series_map = {}
        for entry in vaccine_series:
            series_map[entry.get("vaccine_type", "")] = entry

        # Check each expanded vaccine against age eligibility
        vaccine_rules = [
            ("HPV", "90651", 9, 45, "HPV (Gardasil 9)"),
            ("HepB", "90739", 18, 999, "Hepatitis B (adult)"),
            ("HepA", "90632", 1, 18, "Hepatitis A (pediatric)"),
            ("RSV", "90680", 60, 999, "RSV (Arexvy/Abrysvo)"),
            ("MenACWY", "90734", 11, 55, "Meningococcal ACWY"),
            ("MenB", "90620", 16, 23, "Meningococcal B"),
        ]

        for vtype, cpt, age_min, age_max, name in vaccine_rules:
            if age < age_min or age > age_max:
                continue

            product_info = VACCINE_PRODUCT_CODES.get(cpt, {})
            total_doses = product_info.get("series_doses", 1)

            series_entry = series_map.get(vtype, {})
            doses_received = series_entry.get("doses_received", 0)
            series_complete = series_entry.get("complete", False)

            if series_complete or doses_received >= total_doses:
                continue

            if doses_received == 0:
                eligibility = f"{name}: age-eligible ({age}y), no doses on record. {total_doses}-dose series."
                confidence = "LOW"
            else:
                eligibility = (
                    f"{name}: {doses_received}/{total_doses} doses received. "
                    f"Overdue for dose {doses_received + 1}."
                )
                confidence = "MEDIUM"

            admin_rev = self._get_rate("90471")
            product_rev = self._get_rate(cpt)
            est_revenue = admin_rev + product_rev

            opps.append(self._make_opportunity(
                mrn_hash=mrn_hash,
                user_id=pd.get("user_id"),
                visit_date=pd.get("visit_date"),
                opportunity_type="vaccine_series",
                codes=["90471", cpt],
                est_revenue=est_revenue,
                eligibility_basis=eligibility,
                documentation_required=(
                    f"Administer {name}. Document product, lot, site, route. "
                    f"VIS provided. Bill 90471 + {cpt}. Update series tracker."
                ),
                confidence_level=confidence,
                insurer_caveat=None,
                insurer_type=insurer,
                opportunity_code=f"IMM_{vtype.upper()}",
                priority="low",
                documentation_checklist=f'["Verify series status","Administer {name}","Document product and lot","Bill admin + product code","Update series tracker"]',
            ))

        return opps

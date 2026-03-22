"""
CareCompanion — Alcohol/Substance Screening Detector
billing_engine/detectors/alcohol.py

Annual alcohol misuse screening (SBIRT) — G0442, G0443, 99408, 99409.
G0442+G0443 must be billed as a pair.  Elevated priority for F10-F19 Dx.
"""

from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn


class AlcoholDetector(BaseDetector):
    """Alcohol/substance screening (SBIRT) detector."""

    CATEGORY = "alcohol_screening"
    DESCRIPTION = "Annual alcohol misuse screening and SBIRT intervention"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        patient_age = pd.get("patient_age") or 0
        if patient_age < 18:
            return []

        visit_type = pd.get("visit_type") or ""
        if "awv" in visit_type.lower() or "wellness" in visit_type.lower():
            return []

        diagnoses = pd.get("diagnoses") or []
        substance_dx = [
            d for d in diagnoses
            if any(
                (d.get("icd10_code") or "").upper().startswith(f"F1{n}")
                for n in range(10)
            )
            and (d.get("status") or "").lower() != "resolved"
        ]

        codes = ["G0442", "G0443"]
        est_revenue = self._get_rate("G0442") + self._get_rate("G0443")

        if substance_dx:
            dx_names = [d.get("diagnosis_name") or d.get("icd10_code") for d in substance_dx[:2]]
            eligibility = (
                f"Active substance use diagnosis: {', '.join(dx_names)}. "
                "Annual SBIRT screening and brief intervention recommended."
            )
            codes.extend(["99408"])
            est_revenue += self._get_rate("99408")
            confidence = "HIGH"
        else:
            eligibility = (
                "Annual alcohol misuse screening recommended for all adults per USPSTF. "
                "G0442+G0443 must be billed as a pair."
            )
            confidence = "MEDIUM"

        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="alcohol_screening",
            codes=codes,
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                "Administer AUDIT-C or CAGE screening tool. Document score. "
                "If positive: brief counseling intervention (G0443). "
                "If SBIRT: document 15-30 min intervention (99408) or >30 min (99409). "
                "G0442 and G0443 must be billed together."
            ),
            confidence_level=confidence,
            insurer_caveat=None,
            insurer_type=insurer,
        )
        return [opp]

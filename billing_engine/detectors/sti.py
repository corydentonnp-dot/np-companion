"""
CareCompanion — STI/Hepatitis Screening Detector
billing_engine/detectors/sti.py

USPSTF-recommended STI/hepatitis screenings:
- Hep C: one-time, all adults 18-79
- Chlamydia/gonorrhea: women <=24 and at-risk
"""

from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn
from billing_engine.utils import months_since


class STIDetector(BaseDetector):
    """STI / hepatitis screening detector."""

    CATEGORY = "sti_screening"
    DESCRIPTION = "USPSTF STI/hepatitis screening for eligible adults"

    # Hep C is one-time per USPSTF; suppress if screened within 12 months
    HEP_C_LOOKBACK_MONTHS = 12

    def detect(self, patient_data, payer_context):
        pd = patient_data
        patient_age = pd.get("patient_age") or 0
        if patient_age < 18 or patient_age > 79:
            return []

        codes = []
        est_revenue = 0

        # Hep C screening — suppress if recently done
        last_hep_c = pd.get("last_hep_c_date")
        if months_since(last_hep_c) >= self.HEP_C_LOOKBACK_MONTHS:
            codes.append("86803")
            est_revenue += self._get_rate("86803")

        patient_sex = (pd.get("patient_sex") or "").lower()

        if patient_sex == "female" and patient_age <= 24:
            codes.extend(["87491", "87591"])
            est_revenue += self._get_rate("87491") + self._get_rate("87591")

        if not codes:
            return []

        parts = []
        if "86803" in codes:
            parts.append(f"Patient age {patient_age} — eligible for Hep C screening (USPSTF Grade B, one-time).")
        if "87491" in codes:
            parts.append("Chlamydia/gonorrhea screening also recommended (women <=24).")
        eligibility = " ".join(parts)

        insurer = pd.get("insurer_type") or "unknown"
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        opp = self._make_opportunity(
            mrn_hash=mrn_hash,
            user_id=pd.get("user_id"),
            visit_date=pd.get("visit_date"),
            opportunity_type="sti_screening",
            codes=codes,
            est_revenue=est_revenue,
            eligibility_basis=eligibility,
            documentation_required=(
                "STI screening ordered per USPSTF guidelines. "
                "Patient counseled on risk factors and prevention. "
                "Document screening rationale: age-based (Hep C) or risk-based. "
                "86803 = Hep C Ab. 87491 = chlamydia NAA. 87591 = gonorrhea NAA."
            ),
            confidence_level="HIGH",
            insurer_caveat=None,
            insurer_type=insurer,
        )
        return [opp]

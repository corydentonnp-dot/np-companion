"""
CareCompanion — Procedures Detector
billing_engine/detectors/procedures.py

In-office procedures: EKG, spirometry, POCT, venipuncture, injection admin,
nebulizer, pulse oximetry.  Phase 19B.1.
"""

from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn
from app.api_config import (
    EKG_SYMPTOM_PREFIXES,
    SPIROMETRY_DX_PREFIXES,
    RESPIRATORY_DX_PREFIXES,
)


def _has_dx_prefix(diagnoses, prefixes):
    """Return True if any active diagnosis matches a prefix list."""
    for dx in diagnoses:
        code = (dx.get("icd10_code") or "").upper()
        status = (dx.get("status") or "").lower()
        if status == "resolved":
            continue
        if any(code.startswith(p) for p in prefixes):
            return True
    return False


def _matching_dx_names(diagnoses, prefixes):
    """Return names of matching diagnoses for eligibility text."""
    names = []
    for dx in diagnoses:
        code = (dx.get("icd10_code") or "").upper()
        status = (dx.get("status") or "").lower()
        if status == "resolved":
            continue
        if any(code.startswith(p) for p in prefixes):
            names.append(dx.get("diagnosis_name") or code)
    return names


class ProceduresDetector(BaseDetector):
    """In-office procedural billing detector."""

    CATEGORY = "procedures"
    DESCRIPTION = "EKG, spirometry, POCT, venipuncture, injection, nebulizer, pulse ox"

    def detect(self, patient_data, payer_context):
        pd = patient_data
        diagnoses = pd.get("diagnoses") or []
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        user_id = pd.get("user_id")
        visit_date = pd.get("visit_date")
        insurer = pd.get("insurer_type") or "unknown"
        visit_type = (pd.get("visit_type") or "").lower()
        age = pd.get("age") or 0

        opps = []

        # ── PROC_EKG ──
        if _has_dx_prefix(diagnoses, EKG_SYMPTOM_PREFIXES):
            last_ekg = pd.get("last_ekg_date")
            from billing_engine.shared import months_since
            if not last_ekg or months_since(last_ekg) >= 12:
                dx_names = _matching_dx_names(diagnoses, EKG_SYMPTOM_PREFIXES)
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash, user_id=user_id, visit_date=visit_date,
                    opportunity_type="procedure",
                    codes=["93000"],
                    est_revenue=self._get_rate("93000"),
                    eligibility_basis=f"Cardiac indication: {', '.join(dx_names[:3])}. No EKG in 12+ months.",
                    documentation_required="12-lead EKG performed. Interpretation: [findings]. Clinical indication: [reason].",
                    confidence_level="MEDIUM",
                    insurer_caveat=None, insurer_type=insurer,
                    opportunity_code="PROC_EKG", priority="medium",
                    documentation_checklist='["Order 12-lead EKG","Document clinical indication","Interpret and document findings"]',
                ))

        # ── PROC_SPIROMETRY ──
        if _has_dx_prefix(diagnoses, SPIROMETRY_DX_PREFIXES):
            last_spiro = pd.get("last_spirometry_date")
            from billing_engine.shared import months_since
            if not last_spiro or months_since(last_spiro) >= 12:
                dx_names = _matching_dx_names(diagnoses, SPIROMETRY_DX_PREFIXES)
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash, user_id=user_id, visit_date=visit_date,
                    opportunity_type="procedure",
                    codes=["94060"],
                    est_revenue=self._get_rate("94060"),
                    eligibility_basis=f"Respiratory diagnosis: {', '.join(dx_names[:3])}. No spirometry in 12+ months.",
                    documentation_required="Pre/post bronchodilator spirometry. FEV1: [X]%, FVC: [X]%, FEV1/FVC ratio: [X].",
                    confidence_level="MEDIUM",
                    insurer_caveat=None, insurer_type=insurer,
                    opportunity_code="PROC_SPIROMETRY", priority="medium",
                    documentation_checklist='["Perform pre-bronchodilator spirometry","Administer bronchodilator","Perform post-bronchodilator spirometry","Document FEV1, FVC, FEV1/FVC ratio"]',
                ))

        # ── PROC_VENIPUNCTURE ──
        labs_ordered = pd.get("labs_ordered_today") or []
        if labs_ordered:
            opps.append(self._make_opportunity(
                mrn_hash=mrn_hash, user_id=user_id, visit_date=visit_date,
                opportunity_type="procedure",
                codes=["36415"],
                est_revenue=self._get_rate("36415"),
                eligibility_basis=f"In-office blood draw for {len(labs_ordered)} lab(s): {', '.join(str(l) for l in labs_ordered[:3])}.",
                documentation_required="Venipuncture performed by [staff]. Site: [antecubital/hand]. Specimens: [list].",
                confidence_level="HIGH",
                insurer_caveat=None, insurer_type=insurer,
                opportunity_code="PROC_VENIPUNCTURE", priority="low",
                documentation_checklist='["Document phlebotomist","Document draw site","List specimens collected"]',
            ))

        # ── PROC_INJECTION_ADMIN ──
        injections = pd.get("injections_given_today") or []
        if injections:
            opps.append(self._make_opportunity(
                mrn_hash=mrn_hash, user_id=user_id, visit_date=visit_date,
                opportunity_type="procedure",
                codes=["96372"],
                est_revenue=self._get_rate("96372") * len(injections),
                eligibility_basis=f"{len(injections)} therapeutic injection(s) administered today.",
                documentation_required="Injection admin [IM/SubQ/IV]. Medication: [name], dose, site, lot.",
                confidence_level="HIGH",
                insurer_caveat=None, insurer_type=insurer,
                opportunity_code="PROC_INJECTION_ADMIN", priority="low",
                documentation_checklist='["Document medication name and dose","Document route (IM/SubQ/IV)","Document injection site","Document lot number and expiration"]',
            ))

        # ── PROC_NEBULIZER ──
        neb_given = pd.get("nebulizer_given_today")
        if neb_given or (visit_type in ("acute", "urgent") and _has_dx_prefix(diagnoses, RESPIRATORY_DX_PREFIXES)):
            if neb_given:
                opps.append(self._make_opportunity(
                    mrn_hash=mrn_hash, user_id=user_id, visit_date=visit_date,
                    opportunity_type="procedure",
                    codes=["94640"],
                    est_revenue=self._get_rate("94640"),
                    eligibility_basis="Nebulizer treatment administered today.",
                    documentation_required="Nebulizer treatment with [albuterol/ipratropium]. Duration: [X] min. Pre/post assessment.",
                    confidence_level="HIGH",
                    insurer_caveat=None, insurer_type=insurer,
                    opportunity_code="PROC_NEBULIZER", priority="low",
                    documentation_checklist='["Document medication used","Document treatment duration","Document pre/post respiratory assessment"]',
                ))

        # ── PROC_PULSE_OX ──
        if _has_dx_prefix(diagnoses, RESPIRATORY_DX_PREFIXES):
            opps.append(self._make_opportunity(
                mrn_hash=mrn_hash, user_id=user_id, visit_date=visit_date,
                opportunity_type="procedure",
                codes=["94760"],
                est_revenue=self._get_rate("94760"),
                eligibility_basis="Respiratory complaint — pulse oximetry indicated.",
                documentation_required="Pulse oximetry: SpO2 [X]% on [room air/supplemental O2]. Continuous monitoring [Y/N].",
                confidence_level="LOW",
                insurer_caveat=None, insurer_type=insurer,
                opportunity_code="PROC_PULSE_OX", priority="low",
                documentation_checklist='["Perform pulse oximetry","Document SpO2 percentage","Document supplemental oxygen status"]',
            ))

        return opps

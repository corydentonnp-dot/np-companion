"""
CareCompanion — Base Detector Class
File: billing_engine/base.py

Abstract base class for all billing opportunity detectors.
Every detector in billing_engine/detectors/ must inherit from BaseDetector
and implement the detect() method.

The BillingCaptureEngine orchestrator auto-discovers all BaseDetector
subclasses and runs them against patient data.
"""

import logging

from app.api_config import (
    CCM_CODES, AWV_CODES, AWV_ADDON_CODES, TCM_CODES,
    EM_ADDON_CODES, BHI_CODES, RPM_CODES,
    SCREENING_CODES, VACCINE_ADMIN_CODES,
    TOBACCO_CESSATION_CODES, ALCOHOL_SCREENING_CODES,
    COGNITIVE_ASSESSMENT_CODES, OBESITY_NUTRITION_CODES,
    ACP_STANDALONE_CODES, STI_SCREENING_CODES, PREVENTIVE_EM_CODES,
    PROCEDURE_CODES, CHRONIC_MONITORING_CODES, PCM_CODES,
    VACCINE_PRODUCT_CODES,
    TELEHEALTH_CODES, COCM_CODES, COUNSELING_CODES,
    EXPANDED_SCREENING_CODES,
    PEDIATRIC_CODES, MISC_CODES,
)

logger = logging.getLogger(__name__)

# All api_config code dicts in one tuple for rate lookups
_ALL_CODE_DICTS = (
    CCM_CODES, AWV_CODES, AWV_ADDON_CODES, TCM_CODES,
    EM_ADDON_CODES, BHI_CODES, RPM_CODES,
    SCREENING_CODES, VACCINE_ADMIN_CODES,
    TOBACCO_CESSATION_CODES, ALCOHOL_SCREENING_CODES,
    COGNITIVE_ASSESSMENT_CODES, OBESITY_NUTRITION_CODES,
    ACP_STANDALONE_CODES, STI_SCREENING_CODES, PREVENTIVE_EM_CODES,
    PROCEDURE_CODES, CHRONIC_MONITORING_CODES, PCM_CODES,
    VACCINE_PRODUCT_CODES,
    TELEHEALTH_CODES, COCM_CODES, COUNSELING_CODES,
    EXPANDED_SCREENING_CODES,
    PEDIATRIC_CODES, MISC_CODES,
)


class BaseDetector:
    """
    Abstract base class for billing opportunity detectors.

    Subclasses must set CATEGORY and implement detect().
    The CATEGORY string must match the key used in the provider's
    billing_categories_enabled preferences dict for toggle support.
    """

    # Subclass must override these
    CATEGORY = ""           # e.g. "ccm", "procedures", "chronic_monitoring"
    DESCRIPTION = ""        # Human-readable one-liner

    def __init__(self, db=None, cms_pfs_service=None):
        self.db = db
        self._cms = cms_pfs_service

    def detect(self, patient_data, payer_context):
        """
        Detect billing opportunities for a single patient/visit.

        Parameters
        ----------
        patient_data : dict
            Same schema as BillingRulesEngine.evaluate_patient().
        payer_context : dict
            Output of billing_engine.payer_routing.get_payer_context().

        Returns
        -------
        list of BillingOpportunity objects (unsaved, ready for db.session.add())
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement detect()"
        )

    # ------------------------------------------------------------------
    # Shared helpers available to all detectors
    # ------------------------------------------------------------------

    def _get_rate(self, code):
        """
        Get estimated payment rate for a billing code.
        Tries CMS PFS service first, falls back to api_config estimates.
        """
        if self._cms:
            info = self._cms.get_code_info(code)
            if info and info.get("non_facility_pricing_amount"):
                return info["non_facility_pricing_amount"]

        for code_dict in _ALL_CODE_DICTS:
            if code in code_dict:
                return code_dict[code].get("rate_est", 0.0)
        return 0.0

    def _make_opportunity(self, *, mrn_hash, user_id, visit_date,
                          opportunity_type, codes, est_revenue,
                          eligibility_basis, documentation_required,
                          confidence_level, insurer_caveat, insurer_type,
                          category=None, opportunity_code=None,
                          modifier=None, priority=None,
                          documentation_checklist=None):
        """
        Build a BillingOpportunity ORM object.

        Populates both legacy columns (opportunity_type, applicable_codes, etc.)
        and new Phase-19A columns (category, opportunity_code, modifier, etc.)
        for full backwards compatibility.
        """
        from models.billing import BillingOpportunity
        return BillingOpportunity(
            patient_mrn_hash=mrn_hash,
            user_id=user_id,
            visit_date=visit_date,
            opportunity_type=opportunity_type,
            applicable_codes=",".join(codes) if isinstance(codes, list) else codes,
            estimated_revenue=round(est_revenue, 2),
            eligibility_basis=eligibility_basis,
            documentation_required=documentation_required,
            confidence_level=confidence_level,
            insurer_caveat=insurer_caveat,
            insurer_type=insurer_type,
            status="pending",
            # Phase 19A columns
            category=category or self.CATEGORY,
            opportunity_code=opportunity_code,
            modifier=modifier,
            priority=priority,
            documentation_checklist=documentation_checklist,
        )

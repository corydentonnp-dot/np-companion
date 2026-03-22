"""
CareCompanion — Pricing Waterfall Orchestrator
File: app/services/pricing_service.py

Central pricing service that orchestrates the Three-Tier Waterfall:
  Tier 1: Cost Plus Drugs — free, no auth (primary)
  Tier 2: GoodRx Price Compare — only when Tier 1 returns no result
  Tier 3: NeedyMeds/RxAssist — assistance programs for expensive meds

ToS NO-AGGREGATION CONSTRAINT: GoodRx prices must NEVER appear alongside
Cost Plus prices in the same UI component. The waterfall guarantees mutual
exclusivity — Tier 2 is only queried when Tier 1 misses.

Dependencies:
- app/services/api/cost_plus_service.py (CostPlusService)
- app/services/api/goodrx_service.py (GoodRxService)
- app/services/api/drug_assistance_service.py (DrugAssistanceService)
- app/api_config.py (thresholds, default ZIP)
- app/services/insurer_classifier.py (classify_insurer)
"""

import logging

from app.api_config import (
    DRUG_PRICE_ASSISTANCE_THRESHOLD,
    DRUG_PRICE_HIGH_INDICATOR,
    DRUG_PRICE_MEDIUM_INDICATOR,
    GOODRX_DEFAULT_ZIP,
)
from app.services.api.cost_plus_service import CostPlusService
from app.services.api.goodrx_service import GoodRxService
from app.services.api.drug_assistance_service import DrugAssistanceService
from app.services.api.nadac_service import NADACService

logger = logging.getLogger(__name__)

# Source constants
SOURCE_COST_PLUS = "cost_plus"
SOURCE_GOODRX = "goodrx"
SOURCE_NADAC = "nadac"
SOURCE_NONE = "none"

# Badge color constants
BADGE_GREEN = "green"
BADGE_YELLOW = "yellow"
BADGE_RED = "red"


def _compute_badge_color(price_monthly):
    """
    Determine badge color from monthly price.

    < DRUG_PRICE_MEDIUM_INDICATOR ($30) → GREEN
    < DRUG_PRICE_HIGH_INDICATOR ($100)  → YELLOW
    >= DRUG_PRICE_HIGH_INDICATOR        → RED
    None → None (no badge)
    """
    if price_monthly is None:
        return None
    if price_monthly < DRUG_PRICE_MEDIUM_INDICATOR:
        return BADGE_GREEN
    if price_monthly < DRUG_PRICE_HIGH_INDICATOR:
        return BADGE_YELLOW
    return BADGE_RED


def _build_pricing_result(source, price_monthly=None, price_display=None,
                          direct_url=None, attribution_text=None,
                          assistance_programs=None, raw_data=None,
                          is_stale=False, cache_timestamp=None):
    """
    Build a standardized PricingResult dict.
    """
    return {
        "source": source,
        "price_monthly_estimate": round(price_monthly, 2) if price_monthly is not None else None,
        "price_display_string": price_display or (
            f"${price_monthly:.2f}/month" if price_monthly is not None else None
        ),
        "direct_url": direct_url,
        "attribution_text": attribution_text,
        "assistance_programs": assistance_programs or [],
        "badge_color": _compute_badge_color(price_monthly),
        "cache_timestamp": cache_timestamp,
        "is_stale": is_stale,
    }


class PricingService:
    """
    Pricing Waterfall Orchestrator — coordinates Tier 1/2/3 pricing.

    NOT a BaseAPIClient subclass — this service orchestrates other
    services rather than making direct API calls itself.
    """

    def __init__(self, db):
        self.cost_plus = CostPlusService(db)
        self.goodrx = GoodRxService(db)
        self.assistance = DrugAssistanceService(db)
        self.nadac = NADACService(db)

    def get_pricing(self, rxcui=None, ndc=None, drug_name=None,
                    strength=None, quantity=30, patient_zip=None,
                    patient_insurer_type=None):
        """
        Unified pricing lookup via the Three-Tier Waterfall.

        Parameters
        ----------
        rxcui : str or None
            RxNorm CUI for the drug.
        ndc : str or None
            National Drug Code.
        drug_name : str or None
            Drug name (e.g. "lisinopril").
        strength : str or None
            Dose strength (e.g. "20 mg").
        quantity : int
            Number of units (default 30-day supply).
        patient_zip : str or None
            Patient ZIP code for GoodRx (default: GOODRX_DEFAULT_ZIP).
        patient_insurer_type : str or None
            From insurer_classifier: "medicare", "medicaid", "commercial",
            "uninsured", etc.

        Returns
        -------
        dict
            PricingResult with source, price, badge_color, assistance, etc.
            Never raises — all failures handled gracefully.
        """
        effective_zip = patient_zip or GOODRX_DEFAULT_ZIP
        tier1_result = None
        tier2_result = None
        price_monthly = None
        source = SOURCE_NONE

        # ---- Tier 1: Cost Plus Drugs ----
        try:
            tier1_result = self.cost_plus.get_price(
                rxcui=rxcui, ndc=ndc, drug_name=drug_name,
                strength=strength, quantity=quantity,
            )
        except Exception:
            logger.debug("Tier 1 (Cost Plus) error", exc_info=True)

        if tier1_result and tier1_result.get("found"):
            price_monthly = tier1_result.get("monthly_price")
            source = SOURCE_COST_PLUS
            result = _build_pricing_result(
                source=SOURCE_COST_PLUS,
                price_monthly=price_monthly,
                price_display=tier1_result.get("price_display"),
                direct_url=tier1_result.get("url"),
            )
        else:
            # ---- Tier 2: GoodRx Price Compare ----
            try:
                tier2_result = self.goodrx.get_price(
                    rxcui=rxcui, drug_name=drug_name,
                    quantity=quantity, zip_code=effective_zip,
                )
            except Exception:
                logger.debug("Tier 2 (GoodRx) error", exc_info=True)

            if tier2_result and tier2_result.get("found"):
                price_monthly = tier2_result.get("lowest_price")
                source = SOURCE_GOODRX
                result = _build_pricing_result(
                    source=SOURCE_GOODRX,
                    price_monthly=price_monthly,
                    direct_url=tier2_result.get("deep_link_url"),
                    attribution_text=tier2_result.get("attribution_text"),
                )
            else:
                # ---- No pricing data ----
                result = _build_pricing_result(source=SOURCE_NONE)

        # ---- Tier 1b: NADAC Reference Price (informational only) ----
        # Always attempt NADAC — it provides pharmacy acquisition cost context
        # regardless of which tier supplied the primary price.
        try:
            nadac_result = self.nadac.get_price(
                ndc=ndc, drug_name=drug_name, quantity=quantity,
            )
            if nadac_result and nadac_result.get("found"):
                result["nadac_price"] = {
                    "nadac_per_unit": nadac_result.get("nadac_per_unit"),
                    "nadac_monthly": nadac_result.get("nadac_monthly"),
                    "nadac_effective_date": nadac_result.get("effective_date", ""),
                    "pricing_unit": nadac_result.get("pricing_unit", ""),
                }
        except Exception:
            logger.debug("Tier 1b (NADAC) error", exc_info=True)

        # ---- Tier 3: Assistance Programs ----
        # Triggered when price exceeds threshold OR patient is medicaid/uninsured
        should_query_assistance = False
        if price_monthly is not None and price_monthly > DRUG_PRICE_ASSISTANCE_THRESHOLD:
            should_query_assistance = True
        if patient_insurer_type in ("medicaid", "uninsured"):
            should_query_assistance = True

        if should_query_assistance and drug_name:
            try:
                programs = self.assistance.get_assistance_programs(
                    drug_name, patient_insurer_type=patient_insurer_type,
                )
                result["assistance_programs"] = programs
            except Exception:
                logger.debug("Tier 3 (Assistance) error", exc_info=True)

        return result

    def get_pricing_for_medication(self, medication_obj, patient_record=None):
        """
        Convenience method — extracts fields from ORM objects and calls get_pricing.

        Parameters
        ----------
        medication_obj : PatientMedication
            ORM object with drug_name, rxnorm_cui, dosage, etc.
        patient_record : PatientRecord or None
            Optional ORM object with insurer_type field.

        Returns
        -------
        dict
            PricingResult dict.
        """
        drug_name = getattr(medication_obj, 'drug_name', None)
        rxcui = getattr(medication_obj, 'rxnorm_cui', None) or None
        dosage = getattr(medication_obj, 'dosage', None) or None

        # Extract insurer type from patient record if available
        insurer_type = None
        if patient_record:
            insurer_type = getattr(patient_record, 'insurer_type', None)

        return self.get_pricing(
            rxcui=rxcui,
            drug_name=drug_name,
            strength=dosage,
            patient_insurer_type=insurer_type,
        )

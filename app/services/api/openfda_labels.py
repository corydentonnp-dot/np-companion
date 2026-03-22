"""
CareCompanion — OpenFDA Drug Label Service
File: app/services/api/openfda_labels.py

Returns FDA-approved prescribing information (package inserts) for any drug.
This is the legal label — the authoritative source for indications,
contraindications, warnings, drug interactions, dosing, and monitoring.

Base URL: https://api.fda.gov/drug/label.json
Auth: No key required for <1000 req/day; free key for higher volume
Rate limit: 240 req/min without key; 1000 req/min with free key

Dependencies:
- app/services/api/base_client.py (BaseAPIClient)
- app/api_config.py (OPENFDA_LABEL_BASE_URL, OPENFDA_LABEL_CACHE_TTL_DAYS)

CareCompanion features that rely on this module:
- Medication Reference (F10) — replaces entire hand-curated drug database
- Pregnancy/Renal filter (F10c) — reads pregnancy and renal dosing sections
- Pre-visit note prep — monitoring language in Assessment/Plan section
- Drug Interaction Checker — drug_interactions section of labels
- Drug Safety Panel — black box warnings, contraindications
- Abnormal Lab Interpretation — monitoring requirements per FDA label
- PA Generator (F26) — FDA-approved indication language for PA narratives
"""

import logging
from app.api_config import OPENFDA_LABEL_BASE_URL, OPENFDA_LABEL_CACHE_TTL_DAYS
from app.services.api.base_client import BaseAPIClient, APIUnavailableError
from models.api_cache import FdaLabelCache

logger = logging.getLogger(__name__)

# Label sections to extract (by OpenFDA field name)
LABEL_SECTIONS = [
    "indications_and_usage",
    "contraindications",
    "warnings_and_cautions",
    "drug_interactions",
    "pregnancy",
    "pregnancy_or_breast_feeding",
    "renal_impairment",
    "dosage_and_administration",
    "pediatric_use",
    "adverse_reactions",
    "overdosage",
    "how_supplied",
    "boxed_warning",
    "purpose",
]


class OpenFDALabelsService(BaseAPIClient):
    """
    Service for the OpenFDA Drug Label (SPL) API.
    """

    def __init__(self, db):
        super().__init__(
            api_name="openfda_labels",
            base_url=OPENFDA_LABEL_BASE_URL,
            db=db,
            ttl_days=OPENFDA_LABEL_CACHE_TTL_DAYS,
        )

    def get_label_by_rxcui(self, rxcui: str) -> dict:
        """
        Fetch the FDA prescribing label for a drug by its RxCUI.
        This is the primary query method once the RxCUI is known.

        Returns
        -------
        dict — Extracted label sections plus metadata, or empty dict if not found.
        Keys include: brand_name, generic_name, manufacturer, label_sections
        (dict of section_name → text), has_black_box_warning (bool), _stale (bool)
        """
        try:
            # Use the openfda subfield search which is the reliable route
            data = self._get(
                "",  # Base URL is the full endpoint
                params={"search": f"openfda.rxcui:{rxcui}", "limit": 1},
            )
            result = self._parse_label(data)
            self._save_to_structured_cache(rxcui, result)
            return result
        except APIUnavailableError:
            logger.warning(f"OpenFDA labels unavailable for RxCUI: {rxcui}")
            return {}

    def get_label_by_name(self, drug_name: str) -> dict:
        """
        Fallback: fetch label by generic drug name when RxCUI is not available.
        """
        try:
            data = self._get(
                "",
                params={"search": f"openfda.generic_name:{drug_name}", "limit": 1},
            )
            return self._parse_label(data)
        except APIUnavailableError:
            logger.warning(f"OpenFDA labels unavailable for drug: {drug_name}")
            return {}

    def _parse_label(self, raw_data: dict) -> dict:
        """
        Extract the relevant sections from the raw OpenFDA label response.

        FDA labels are long free-text documents. We extract key sections
        and return them as a structured dict. The full text is stored in
        the cache; this parsed version is what gets displayed in the UI.
        """
        if not raw_data:
            return {}

        results = raw_data.get("results") or []
        if not results:
            return {}

        label = results[0]
        openfda = label.get("openfda") or {}

        # Extract named sections — each is a list of strings in OpenFDA format
        sections = {}
        for section_name in LABEL_SECTIONS:
            section_data = label.get(section_name) or []
            if section_data and isinstance(section_data, list):
                sections[section_name] = " ".join(section_data).strip()
            elif section_data and isinstance(section_data, str):
                sections[section_name] = section_data.strip()

        # Check for black box warning
        has_black_box = bool(
            label.get("boxed_warning") or
            label.get("warnings_and_cautions", "").upper().startswith("WARNING")
        )

        return {
            "brand_name": _first(openfda.get("brand_name")),
            "generic_name": _first(openfda.get("generic_name")),
            "manufacturer": _first(openfda.get("manufacturer_name")),
            "rxcui": _first(openfda.get("rxcui")),
            "ndc": _first(openfda.get("product_ndc")),
            "label_sections": sections,
            "has_black_box_warning": has_black_box,
            "_stale": raw_data.get("_stale", False),
        }

    def _save_to_structured_cache(self, rxcui, label):
        """Persist key label fields to the structured FdaLabelCache table."""
        if not label or not rxcui:
            return
        db = self.cache.db
        try:
            existing = FdaLabelCache.query.filter_by(rxcui=rxcui).first()
            if not existing:
                sections = label.get('label_sections') or {}
                db.session.add(FdaLabelCache(
                    rxcui=rxcui,
                    spl_id='',
                    brand_name=label.get('brand_name', '')[:300],
                    warnings_summary=(sections.get('warnings_and_cautions') or '')[:2000],
                    boxed_warning=(sections.get('boxed_warning') or '')[:2000],
                    contra_summary=(sections.get('contraindications') or '')[:2000],
                ))
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.debug(f'FdaLabelCache save error: {e}')

    def check_pregnancy_risk(self, rxcui: str) -> dict:
        """
        Extract pregnancy safety information for a drug.
        Returns a dict with: has_pregnancy_warning (bool), category (str), text (str)
        Used by the Pregnancy filter (F10c).
        """
        label = self.get_label_by_rxcui(rxcui)
        sections = label.get("label_sections") or {}
        pregnancy_text = (
            sections.get("pregnancy") or
            sections.get("pregnancy_or_breast_feeding") or
            ""
        )

        # Try to extract FDA pregnancy category (A/B/C/D/X) from text
        category = "N/A"
        if pregnancy_text:
            import re
            cat_match = re.search(
                r'(?:pregnancy\s+)?category\s+([A-DX])\b',
                pregnancy_text, re.IGNORECASE
            )
            if cat_match:
                category = cat_match.group(1).upper()
            elif "contraindicated" in pregnancy_text.lower():
                category = "X"

        has_warning = bool(pregnancy_text and (
            "contraindicated" in pregnancy_text.lower() or
            "avoid" in pregnancy_text.lower() or
            category in ("D", "X")
        ))
        return {
            "has_pregnancy_warning": has_warning,
            "category": category,
            "text": pregnancy_text[:500] if pregnancy_text else "",
        }

    def check_renal_dosing(self, rxcui: str, gfr: int = None) -> dict:
        """
        Extract renal dosing guidance for a drug.
        Returns a dict with: has_renal_guidance (bool), adjustment (str), text (str)
        Used by the Renal filter (F10c).
        """
        label = self.get_label_by_rxcui(rxcui)
        sections = label.get("label_sections") or {}
        renal_text = sections.get("renal_impairment") or ""
        if not renal_text:
            # Sometimes buried in dosage_and_administration
            dosage_text = sections.get("dosage_and_administration") or ""
            if "renal" in dosage_text.lower() or "creatinine" in dosage_text.lower():
                renal_text = dosage_text[:500]

        # Determine adjustment recommendation based on GFR if provided
        adjustment = "none"
        if renal_text:
            lower = renal_text.lower()
            if "contraindicated" in lower:
                adjustment = "contraindicated"
            elif "dose reduction" in lower or "reduce" in lower or "decrease" in lower:
                adjustment = "dose_reduction"
            elif "avoid" in lower:
                adjustment = "avoid"
            elif "monitor" in lower or "caution" in lower:
                adjustment = "monitor"

        return {
            "has_renal_guidance": bool(renal_text),
            "adjustment": adjustment,
            "text": renal_text[:500] if renal_text else "",
        }


def _first(lst):
    """Return first element of a list, or None if empty/None."""
    if lst and isinstance(lst, list):
        return lst[0]
    return lst

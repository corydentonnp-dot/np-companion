"""
CareCompanion — Billing Capture Engine Orchestrator
File: billing_engine/engine.py

Central orchestrator that auto-discovers all detector modules,
runs each against a patient/visit, deduplicates by opportunity_code,
and returns a sorted list of BillingOpportunity objects.

This is the single entry point for all billing opportunity detection.
The legacy BillingRulesEngine in app/services/billing_rules.py delegates
to this engine via a thin wrapper (Phase 19A.5).
"""

import logging

from billing_engine.payer_routing import get_payer_context
from billing_engine.detectors import discover_detector_classes
from billing_engine.scoring import ExpectedNetValueCalculator

logger = logging.getLogger(__name__)

# Priority ordering for sort (lower index = higher priority)
_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class BillingCaptureEngine:
    """
    Orchestrator for the modular billing capture system.

    Auto-discovers all BaseDetector subclasses from billing_engine/detectors/,
    instantiates them, and runs each detect() for a given patient.
    Results are deduplicated by opportunity_code and sorted by priority
    then estimated_revenue descending.
    """

    def __init__(self, db, cms_pfs_service=None):
        self.db = db
        self._cms = cms_pfs_service
        self._detector_classes = discover_detector_classes()
        self._detectors = [
            cls(db=db, cms_pfs_service=cms_pfs_service)
            for cls in self._detector_classes
        ]
        logger.info(
            "BillingCaptureEngine initialised with %d detectors: %s",
            len(self._detectors),
            ", ".join(d.CATEGORY for d in self._detectors),
        )

    def evaluate(self, patient_data):
        """
        Run all active detectors for a single patient/visit.

        Parameters
        ----------
        patient_data : dict
            Same schema as the legacy BillingRulesEngine.evaluate_patient().

        Returns
        -------
        list of BillingOpportunity objects (unsaved, ready for db.session.add())
        """
        payer_context = get_payer_context(patient_data)
        opportunities = []
        suppressions = []

        # Load per-provider billing category toggles (all default to enabled)
        enabled = self._load_category_toggles(patient_data)

        for detector in self._detectors:
            # Skip disabled categories — log suppression
            if not enabled.get(detector.CATEGORY, True):
                suppressions.append({
                    "opportunity_code": detector.CATEGORY,
                    "reason": "provider_disabled_category",
                    "detail": f"Category '{detector.CATEGORY}' disabled by provider preferences",
                })
                continue

            try:
                result = detector.detect(patient_data, payer_context)
                if result:
                    if isinstance(result, list):
                        opportunities.extend(result)
                    else:
                        opportunities.append(result)
            except Exception:
                logger.exception(
                    "Detector %s (%s) failed for patient",
                    detector.__class__.__name__,
                    detector.CATEGORY,
                )

        final = self._deduplicate_and_sort(opportunities, patient_data)

        # Phase 28.4-28.5: Enrich with payer cost-share + modifier notes
        self._enrich_cost_share(final, payer_context)

        # Attach suppressions for downstream logging
        self._last_suppressions = suppressions
        return final

    def get_suppressions(self):
        """Return suppression records from the last evaluate() call."""
        return getattr(self, "_last_suppressions", [])

    def log_suppressions(self, patient_mrn_hash, user_id, visit_date=None):
        """
        Persist suppression records from the last evaluate() call as
        OpportunitySuppression rows. Safe to call even if no suppressions.
        """
        suppressions = self.get_suppressions()
        if not suppressions:
            return 0
        try:
            from models.billing import OpportunitySuppression
            from models import db as _db
            count = 0
            for s in suppressions:
                rec = OpportunitySuppression(
                    patient_mrn_hash=patient_mrn_hash,
                    user_id=user_id,
                    visit_date=visit_date,
                    opportunity_code=s["opportunity_code"],
                    suppression_reason=s["reason"],
                    detail=s.get("detail"),
                )
                _db.session.add(rec)
                count += 1
            _db.session.commit()
            return count
        except Exception:
            logger.exception("Failed to log suppressions")
            return 0

    @staticmethod
    def record_funnel_stage(opportunity_id, patient_mrn_hash, stage, actor=None, notes=None, previous_stage=None):
        """
        Record a closed-loop funnel stage transition for a billing opportunity.
        """
        try:
            from models.billing import ClosedLoopStatus
            from models import db as _db
            entry = ClosedLoopStatus(
                opportunity_id=opportunity_id,
                patient_mrn_hash=patient_mrn_hash,
                funnel_stage=stage,
                stage_actor=actor,
                stage_notes=notes,
                previous_stage=previous_stage,
            )
            _db.session.add(entry)
            _db.session.commit()
            return entry
        except Exception:
            logger.exception("Failed to record funnel stage")
            return None

    def _load_category_toggles(self, patient_data):
        """
        Load per-provider billing category enable/disable preferences.
        Returns dict of {category_key: bool}.  Missing keys default to True.
        """
        enabled = patient_data.get("billing_categories_enabled") or {}
        if not enabled:
            user_id = patient_data.get("user_id")
            if user_id:
                try:
                    from models.user import User
                    user = User.query.get(user_id)
                    if user:
                        enabled = user.get_pref("billing_categories_enabled", {})
                except Exception:
                    pass
        return enabled

    def _enrich_cost_share(self, opportunities, payer_context):
        """
        Phase 28.4-28.5: Look up PayerCoverageMatrix for each opportunity's
        CPT code + payer type. Append cost-share display and modifier guidance
        to the insurer_caveat field.
        """
        payer_type = payer_context.get("payer_type", "commercial")
        try:
            from models.billing import PayerCoverageMatrix
            # Collect all CPT codes from opportunities
            cpt_codes = set()
            for opp in opportunities:
                codes_str = getattr(opp, "applicable_codes", "") or ""
                for token in codes_str.replace(",", " ").split():
                    token = token.strip()
                    if token and token[0].isalnum():
                        cpt_codes.add(token)

            if not cpt_codes:
                return

            # Batch query
            rows = PayerCoverageMatrix.query.filter(
                PayerCoverageMatrix.cpt_code.in_(cpt_codes),
                PayerCoverageMatrix.payer_type == payer_type,
            ).all()
            matrix = {r.cpt_code: r for r in rows}

            for opp in opportunities:
                codes_str = getattr(opp, "applicable_codes", "") or ""
                notes = []
                for token in codes_str.replace(",", " ").split():
                    token = token.strip()
                    entry = matrix.get(token)
                    if not entry:
                        continue
                    cs = entry.cost_share_display()
                    if cs:
                        notes.append(cs)
                    md = entry.modifier_display()
                    if md:
                        notes.append(md)

                if notes:
                    existing = getattr(opp, "insurer_caveat", "") or ""
                    combined = " | ".join(dict.fromkeys(notes))  # dedupe preserving order
                    if existing:
                        opp.insurer_caveat = existing + " | " + combined
                    else:
                        opp.insurer_caveat = combined
        except Exception:
            logger.debug("PayerCoverageMatrix enrichment skipped", exc_info=True)

    def _deduplicate_and_sort(self, opportunities, patient_data=None):
        """
        Deduplicate by opportunity_code (keep highest revenue if duplicate),
        score with ExpectedNetValueCalculator, then sort by
        expected_net_dollars descending (with priority tiebreak).
        """
        # Deduplicate: if two opportunities share the same opportunity_code,
        # keep the one with higher estimated_revenue.
        seen = {}
        for opp in opportunities:
            key = getattr(opp, "opportunity_code", None) or getattr(opp, "opportunity_type", "")
            existing = seen.get(key)
            if existing is None:
                seen[key] = opp
            elif (opp.estimated_revenue or 0) > (existing.estimated_revenue or 0):
                seen[key] = opp
        deduped = list(seen.values())

        # CMS per-encounter code limits: certain CPT codes can only appear
        # once per encounter regardless of opportunity_code.
        _ONCE_PER_ENCOUNTER_CODES = {"96127"}
        cpt_seen = {}
        final_deduped = []
        for opp in deduped:
            codes_str = getattr(opp, "applicable_codes", "") or ""
            cpt_codes = {c.strip() for c in codes_str.replace(",", " ").split() if c.strip()}
            limited = cpt_codes & _ONCE_PER_ENCOUNTER_CODES
            if limited:
                code = next(iter(limited))
                existing = cpt_seen.get(code)
                if existing is None:
                    cpt_seen[code] = opp
                    final_deduped.append(opp)
                elif (opp.estimated_revenue or 0) > (existing.estimated_revenue or 0):
                    final_deduped.remove(existing)
                    cpt_seen[code] = opp
                    final_deduped.append(opp)
            else:
                final_deduped.append(opp)
        deduped = final_deduped

        # Score each opportunity
        try:
            scorer = self._build_scorer(patient_data)
            for opp in deduped:
                scorer.score(opp, patient_data)
        except Exception:
            logger.exception("Scoring failed, falling back to revenue sort")

        # Sort: expected_net_dollars desc (with priority tiebreak)
        def sort_key(opp):
            pri = _PRIORITY_ORDER.get(
                (getattr(opp, "priority", None) or "medium").lower(), 2
            )
            enr = -(getattr(opp, "expected_net_dollars", None) or opp.estimated_revenue or 0)
            return (pri, enr)

        deduped.sort(key=sort_key)
        return deduped

    def _build_scorer(self, patient_data=None):
        """Build an ExpectedNetValueCalculator with available context."""
        collection_rates = None
        dx_profiles = {}
        bonus_tracker = None

        user_id = (patient_data or {}).get("user_id")

        # Load collection rates from BonusTracker
        if user_id:
            try:
                from models.bonus import BonusTracker
                tracker = BonusTracker.query.filter_by(user_id=user_id).first()
                if tracker:
                    collection_rates = tracker.get_collection_rates() or None
                    bonus_tracker = tracker
            except Exception:
                pass

        # Load DiagnosisRevenueProfile for patient's diagnoses
        if patient_data:
            diags = patient_data.get("diagnoses") or []
            codes = []
            for dx in diags:
                code = dx.get("code", "") if isinstance(dx, dict) else str(dx)
                if code:
                    codes.append(code)
            if codes:
                try:
                    from models.billing import DiagnosisRevenueProfile
                    profiles = DiagnosisRevenueProfile.query.filter(
                        DiagnosisRevenueProfile.icd10_code.in_(codes)
                    ).all()
                    dx_profiles = {p.icd10_code: p for p in profiles}
                except Exception:
                    pass

        return ExpectedNetValueCalculator(
            collection_rates=collection_rates,
            dx_profiles=dx_profiles,
            bonus_tracker=bonus_tracker,
        )

    @property
    def detector_count(self):
        """Number of registered detectors."""
        return len(self._detectors)

    @property
    def detector_categories(self):
        """List of registered detector CATEGORY strings."""
        return [d.CATEGORY for d in self._detectors]

"""
CareCompanion — Chronic Monitoring Detector
billing_engine/detectors/chronic_monitoring.py

Primary path: MonitoringRuleEngine (Phase 23) — API-driven dynamic rules.
Fallback path: MEDICATION_MONITORING_MAP (Phase 19B.2) — static config.

The fallback fires only when MonitoringRuleEngine is unavailable (DB not
migrated, table empty, or service error).  This ensures zero-downtime
migration.
"""

import logging
from billing_engine.base import BaseDetector
from billing_engine.shared import hash_mrn, months_since
from app.api_config import MEDICATION_MONITORING_MAP

logger = logging.getLogger(__name__)


def _has_dx_match(diagnoses, prefixes):
    """Return True if any active diagnosis matches the prefix list."""
    if not prefixes:
        return False
    for dx in diagnoses:
        code = (dx.get("icd10_code") or "").upper()
        status = (dx.get("status") or "").lower()
        if status == "resolved":
            continue
        if any(code.startswith(p) for p in prefixes):
            return True
    return False


def _has_med_match(medications, drug_names):
    """Return True if any active medication matches the drug name list."""
    if not drug_names:
        return False
    for med in medications:
        name = (med.get("drug_name") or med.get("name") or "").lower()
        status = (med.get("status") or "active").lower()
        if status in ("discontinued", "inactive"):
            continue
        if any(dn in name for dn in drug_names):
            return True
    return False


class ChronicMonitoringDetector(BaseDetector):
    """Medication-driven chronic lab monitoring detector."""

    CATEGORY = "chronic_monitoring"
    DESCRIPTION = "A1C, lipid, TSH, renal, CBC, INR, LFT, UACR, Vit D monitoring"

    def detect(self, patient_data, payer_context):
        # Try MonitoringRuleEngine first (Phase 23)
        opps = self._detect_via_engine(patient_data, payer_context)
        if opps is not None:
            return opps

        # Fallback to static MEDICATION_MONITORING_MAP (Phase 19B.2)
        return self._detect_via_legacy_map(patient_data, payer_context)

    # ── Primary path — MonitoringRuleEngine ────────────────────────

    def _detect_via_engine(self, patient_data, payer_context):
        """
        Use MonitoringRuleEngine.get_overdue_monitoring() for detection.
        Returns list of BillingOpportunity or None if engine unavailable.
        """
        try:
            from models import db
            from app.services.monitoring_rule_engine import MonitoringRuleEngine
            engine = MonitoringRuleEngine(db)
        except Exception:
            return None  # fallback to legacy

        pd = patient_data
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        user_id = pd.get("user_id")
        visit_date = pd.get("visit_date")
        insurer = pd.get("insurer_type") or "unknown"

        try:
            overdue = engine.get_overdue_monitoring(mrn_hash)
        except Exception as exc:
            logger.debug("MonitoringRuleEngine failed, using legacy: %s", exc)
            return None  # fallback to legacy

        if not overdue:
            # Check if the table has ANY data — if empty, fall back
            from models.monitoring import MonitoringSchedule
            total = MonitoringSchedule.query.limit(1).first()
            if total is None:
                return None  # table empty → fallback to legacy
            return []  # table has data, this patient just has nothing overdue

        opps = []
        rems_entries = engine.get_rems_entries(mrn_hash)
        rems_labs = {e.requirement_type for e in rems_entries}

        for entry in overdue:
            # Determine source for audit trail
            source_label = entry.source or "MANUAL"
            is_rems = entry.priority == "critical" or any(
                rt in (entry.lab_name or "").upper() for rt in rems_labs
            )

            confidence = "HIGH" if is_rems else "MEDIUM"
            priority = "critical" if is_rems else entry.priority or "medium"

            overdue_text = "no recent result on file"
            if entry.last_performed_date:
                overdue_text = f"last result {entry.last_performed_date}"

            trigger_parts = []
            if entry.triggering_medication:
                trigger_parts.append(f"medication: {entry.triggering_medication}")
            if entry.triggering_condition:
                trigger_parts.append(f"condition: {entry.triggering_condition}")
            trigger_str = "; ".join(trigger_parts) if trigger_parts else "monitoring rule"

            eligibility = (
                f"{entry.lab_name}: {trigger_str}. "
                f"Source: {source_label}. "
                f"Lab overdue — {overdue_text}."
            )

            doc_required = (
                f"Order {entry.lab_code}. "
                f"{entry.clinical_indication or 'Document clinical indication and review results.'}"
            )

            opps.append(self._make_opportunity(
                mrn_hash=mrn_hash,
                user_id=user_id,
                visit_date=visit_date,
                opportunity_type="chronic_monitoring",
                codes=[entry.lab_code],
                est_revenue=self._get_rate(entry.lab_code),
                eligibility_basis=eligibility,
                documentation_required=doc_required,
                confidence_level=confidence,
                insurer_caveat=None,
                insurer_type=insurer,
                opportunity_code=entry.monitoring_rule_code or entry.lab_code,
                priority=priority,
                documentation_checklist=(
                    f'["Order {entry.lab_code}",'
                    f'"Document clinical indication",'
                    f'"Review results when available",'
                    f'"Update care plan based on results"]'
                ),
            ))

        return opps

    # ── Fallback path — legacy MEDICATION_MONITORING_MAP ───────────

    def _detect_via_legacy_map(self, patient_data, payer_context):
        """Original Phase 19B.2 detection logic using static MAP."""
        pd = patient_data
        diagnoses = pd.get("diagnoses") or []
        medications = pd.get("medications") or []
        last_labs = pd.get("last_lab_dates") or {}
        mrn_hash = hash_mrn(pd.get("mrn") or "")
        user_id = pd.get("user_id")
        visit_date = pd.get("visit_date")
        insurer = pd.get("insurer_type") or "unknown"

        opps = []

        for _key, rule in MEDICATION_MONITORING_MAP.items():
            dx_prefixes = rule.get("dx_prefixes") or []
            med_names = rule.get("medications") or []
            lab_code = rule["lab_code"]
            interval = rule["interval_months"]
            rule_code = rule["rule_code"]
            description = rule["description"]

            # Patient must have qualifying Dx OR qualifying medication
            has_dx = _has_dx_match(diagnoses, dx_prefixes)
            has_med = _has_med_match(medications, med_names)
            if not has_dx and not has_med:
                continue

            # Check if lab is overdue
            last_date = last_labs.get(lab_code) or last_labs.get(rule_code)
            if last_date and months_since(last_date) < interval:
                continue

            trigger_reason = []
            if has_dx:
                trigger_reason.append("qualifying diagnosis")
            if has_med:
                trigger_reason.append("qualifying medication")

            overdue_text = "no recent result on file"
            if last_date:
                overdue_text = f"last result {last_date} ({months_since(last_date)}+ months ago)"

            opps.append(self._make_opportunity(
                mrn_hash=mrn_hash,
                user_id=user_id,
                visit_date=visit_date,
                opportunity_type="chronic_monitoring",
                codes=[lab_code],
                est_revenue=self._get_rate(lab_code),
                eligibility_basis=f"{description}: {', '.join(trigger_reason)}. Lab overdue — {overdue_text}.",
                documentation_required=f"Order {lab_code}. Document clinical indication and review results at follow-up.",
                confidence_level="MEDIUM",
                insurer_caveat=None,
                insurer_type=insurer,
                opportunity_code=rule_code,
                priority="medium",
                documentation_checklist=f'["Order {lab_code}","Document clinical indication","Review results when available","Update care plan based on results"]',
            ))

        return opps

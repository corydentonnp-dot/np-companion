"""
CareCompanion — MonitoringRuleEngine
File: app/services/monitoring_rule_engine.py

Phase 23.B2: Central service that replaces MEDICATION_MONITORING_MAP
as the monitoring rule source.  Provides a 6-step waterfall for rule
resolution, per-patient schedule population, REMS delegation, KDIGO
eGFR alerting, MELD/Child-Pugh scoring, FHIR PlanDefinition export,
and CDS Hooks card generation.

Public API
----------
get_monitoring_rules(rxcui, drug_name, icd10_code)
populate_patient_schedule(patient_mrn_hash, user_id, medications, diagnoses, lab_results)
refresh_rules_for_medication(drug_name, rxcui)
refresh_condition_rules(icd10_code)
get_overdue_monitoring(patient_mrn_hash)
bulk_refresh_new_medications(lookback_days)
refresh_preventive_vsac_oids()
get_rems_entries(patient_mrn_hash)
compute_egfr_alerts(patient_mrn_hash, medications, lab_results)
compute_meld_score(patient_mrn_hash, lab_results)
compute_child_pugh_score(patient_mrn_hash, lab_results)
export_rules_as_fhir_plan_definition(rxcui, icd10_code)
get_cds_hooks_cards(patient_mrn_hash)
"""

import logging
import math
import traceback
import urllib.request
import urllib.error
import json
from datetime import date, datetime, timedelta, timezone

from models import db
from models.monitoring import MonitoringRule, MonitoringSchedule, REMSTrackerEntry
from models.patient import PatientLabResult, PatientMedication
from models.agent import AgentError

logger = logging.getLogger(__name__)

# ── eGFR dose-adjustment thresholds (KDIGO) ───────────────────────
_EGFR_THRESHOLDS = {
    'metformin': [
        {'max': 30, 'action': 'CONTRAINDICATED',
         'msg': 'eGFR {value} — metformin contraindicated below 30 mL/min; hold medication per KDIGO'},
        {'min': 30, 'max': 45, 'action': 'DOSE_REDUCE',
         'msg': 'eGFR {value} — metformin dose reduction required (max 1000 mg/day) per KDIGO'},
    ],
    'empagliflozin': [
        {'max': 20, 'action': 'CONTRAINDICATED',
         'msg': 'eGFR {value} — empagliflozin: do not initiate below eGFR 20'},
    ],
    'dapagliflozin': [
        {'max': 20, 'action': 'CONTRAINDICATED',
         'msg': 'eGFR {value} — dapagliflozin: do not initiate below eGFR 20'},
    ],
    'canagliflozin': [
        {'max': 30, 'action': 'CONTRAINDICATED',
         'msg': 'eGFR {value} — canagliflozin contraindicated below eGFR 30'},
    ],
    'apixaban': [
        {'max': 25, 'action': 'DOSE_REDUCE',
         'msg': 'eGFR {value} — verify apixaban dose (2.5 mg BID if SCr ≥1.5 + age ≥80 or wt ≤60 kg)'},
    ],
    'rivaroxaban': [
        {'max': 15, 'action': 'CONTRAINDICATED',
         'msg': 'eGFR {value} — rivaroxaban: avoid below eGFR 15'},
        {'min': 15, 'max': 50, 'action': 'DOSE_REDUCE',
         'msg': 'eGFR {value} — rivaroxaban 15 mg daily (reduced dose) for eGFR 15–50'},
    ],
    'dabigatran': [
        {'max': 15, 'action': 'CONTRAINDICATED',
         'msg': 'eGFR {value} — dabigatran: avoid below eGFR 15'},
        {'min': 15, 'max': 30, 'action': 'DOSE_REDUCE',
         'msg': 'eGFR {value} — dabigatran 75 mg BID for eGFR 15–30'},
    ],
    'edoxaban': [
        {'max': 15, 'action': 'CONTRAINDICATED',
         'msg': 'eGFR {value} — edoxaban: avoid below eGFR 15'},
        {'min': 15, 'max': 50, 'action': 'DOSE_REDUCE',
         'msg': 'eGFR {value} — edoxaban 30 mg daily for eGFR 15–50'},
    ],
    'allopurinol': [
        {'max': 30, 'action': 'DOSE_REDUCE',
         'msg': 'eGFR {value} — allopurinol: start 100 mg, titrate slowly per ACR guidelines'},
    ],
    'gabapentin': [
        {'max': 30, 'action': 'DOSE_REDUCE',
         'msg': 'eGFR {value} — gabapentin: significant dose reduction required (max 300 mg/day)'},
        {'min': 30, 'max': 60, 'action': 'DOSE_REDUCE',
         'msg': 'eGFR {value} — gabapentin dose reduction recommended for eGFR 30–60'},
    ],
    'pregabalin': [
        {'max': 30, 'action': 'DOSE_REDUCE',
         'msg': 'eGFR {value} — pregabalin: reduce dose by 50–75%'},
        {'min': 30, 'max': 60, 'action': 'DOSE_REDUCE',
         'msg': 'eGFR {value} — pregabalin dose reduction recommended for eGFR 30–60'},
    ],
    'lithium': [
        {'max': 30, 'action': 'CONTRAINDICATED',
         'msg': 'eGFR {value} — lithium contraindicated below eGFR 30 without nephrology co-management'},
        {'min': 30, 'max': 60, 'action': 'DOSE_REDUCE',
         'msg': 'eGFR {value} — lithium dose adjustment required; narrow therapeutic index'},
    ],
}

# ── Monitoring bundles (C4 — labs that can share one venipuncture) ─
_MONITORING_BUNDLES = {
    'DM_BUNDLE': {
        'name': 'Diabetes Monitoring Bundle',
        'labs': ['4548-4', '80061', '14959-1', '80048'],  # A1C, lipid, UACR, BMP
    },
    'THYROID_BUNDLE': {
        'name': 'Thyroid Bundle',
        'labs': ['84443', '84439'],  # TSH, freeT4
    },
    'ANTICOAG_BUNDLE': {
        'name': 'Anticoagulation Bundle',
        'labs': ['6301-6', '85025'],  # INR, CBC
    },
    'CKD_BUNDLE': {
        'name': 'CKD Comprehensive Bundle',
        'labs': ['80048', '85025', '84100', '82310', '83970'],  # BMP,CBC,phos,Ca,PTH
    },
    'PSYCH_METABOLIC_BUNDLE': {
        'name': 'Metabolic Psych Bundle',
        'labs': ['82947', '4548-4', '80061'],  # glucose, A1C, lipid
    },
    'HF_BUNDLE': {
        'name': 'Heart Failure Bundle',
        'labs': ['80048', '83880', '85025', '83540'],  # BMP, BNP, CBC, iron
    },
}

# LOINC codes used in clinical scoring
_LOINC_EGFR   = '33914-3'
_LOINC_INR    = '6301-6'
_LOINC_BILI   = '1975-2'
_LOINC_CREAT  = '2160-0'
_LOINC_SODIUM = '2951-2'
_LOINC_ALBUMIN = '1751-7'

# Rule freshness threshold (days)
_RULE_CACHE_DAYS = 30


class MonitoringRuleEngine:
    """Central service replacing MEDICATION_MONITORING_MAP."""

    def __init__(self, db_session=None):
        self._db = db_session or db

    # ================================================================
    # 1. get_monitoring_rules — 6-step waterfall
    # ================================================================

    def get_monitoring_rules(
        self,
        rxcui: str = None,
        drug_name: str = None,
        icd10_code: str = None,
    ) -> list:
        """
        Return MonitoringRule entries for a medication (rxcui/drug_name)
        or condition (icd10_code).  Uses a 6-step cascade:

        1. DB cache hit (< 30 days old)
        2. DailyMed SPL extraction
        3. Drug@FDA PMR/PMC enrichment
        4. RxClass class-level fallback
        5. UpToDate (optional, skip if no key)
        6. Empty + log to AgentError
        """
        # --- Condition path (simpler — no API cascade) ---------------
        if icd10_code:
            return self._get_condition_rules(icd10_code)

        if not rxcui and not drug_name:
            return []

        # Step 1: DB cache
        rules = self._query_cached_rules(rxcui)
        if rules:
            return rules

        # Step 2: DailyMed SPL extraction
        rules = self._fetch_dailymed_rules(drug_name, rxcui)

        # Step 3: Drug@FDA PMR enrichment
        pmr_rules = self._fetch_drugfda_pmr_rules(drug_name, rxcui)
        if pmr_rules:
            rules = self._merge_rules(rules, pmr_rules)

        # Step 4: RxClass class-level fallback
        if not rules:
            rules = self._rxclass_fallback(rxcui)

        # Step 5: UpToDate/DynaMed enrichment (optional)
        if not rules:
            try:
                from app.services.api.uptodate import UpToDateService
                utd = UpToDateService(self._db)
                if utd.enabled:
                    utd_rules = utd.get_monitoring_recommendations(drug_name or rxcui)
                    if utd_rules:
                        rules = self._store_rules(utd_rules, source='UPTODATE')
            except Exception:
                pass  # Optional enrichment — never blocks waterfall

        # Step 6: Empty + log
        if not rules:
            logger.warning(
                "No monitoring rules found for rxcui=%s drug=%s — "
                "logging to AgentError for manual review",
                rxcui, drug_name,
            )
            try:
                err = AgentError(
                    job_name='monitoring_rule_engine',
                    error_message=(
                        f'No monitoring rules found for drug={drug_name} '
                        f'rxcui={rxcui}. All waterfall sources returned empty.'
                    ),
                )
                self._db.session.add(err)
                self._db.session.commit()
            except Exception:
                self._db.session.rollback()

        return rules

    # ================================================================
    # 2. populate_patient_schedule
    # ================================================================

    def populate_patient_schedule(
        self,
        patient_mrn_hash: str,
        user_id: int,
        medications: list,
        diagnoses: list,
        lab_results: list = None,
    ) -> list:
        """
        Create/update MonitoringSchedule entries for a patient based on
        their active medications, diagnoses, and lab history.

        Parameters
        ----------
        medications : list of dicts or PatientMedication objects
            Each must have drug_name and rxnorm_cui (or rxcui).
        diagnoses : list of dicts or PatientDiagnosis objects
            Each must have icd10_code.
        lab_results : list of PatientLabResult objects or dicts, optional
            Used to determine last_performed_date.

        Returns
        -------
        list of MonitoringSchedule entries created/updated.
        """
        lab_index = self._build_lab_index(lab_results or [])
        created = []
        seen_loinc = {}  # loinc_code → shortest interval_days

        # ---- Medication-driven rules --------------------------------
        for med in medications:
            drug_name = _attr(med, 'drug_name', '')
            rxcui = _attr(med, 'rxnorm_cui', '') or _attr(med, 'rxcui', '')
            if not drug_name:
                continue

            rules = self.get_monitoring_rules(rxcui=rxcui, drug_name=drug_name)
            for rule in rules:
                entry = self._upsert_schedule_entry(
                    patient_mrn_hash, user_id, rule, lab_index,
                    seen_loinc,
                    triggering_medication=drug_name,
                )
                if entry:
                    created.append(entry)

            # ---- REMS delegation (B5) --------------------------------
            try:
                from app.services.api.dailymed import DailyMedService
                dm = DailyMedService(self._db)
                dm.create_rems_entries(patient_mrn_hash, user_id, drug_name, rxcui)
            except Exception as exc:
                logger.debug("REMS check skipped for %s: %s", drug_name, exc)

        # ---- Condition-driven rules ---------------------------------
        for dx in diagnoses:
            icd10 = _attr(dx, 'icd10_code', '')
            dx_name = _attr(dx, 'diagnosis_name', '') or icd10
            if not icd10:
                continue

            rules = self.get_monitoring_rules(icd10_code=icd10)
            for rule in rules:
                entry = self._upsert_schedule_entry(
                    patient_mrn_hash, user_id, rule, lab_index,
                    seen_loinc,
                    triggering_condition=dx_name,
                )
                if entry:
                    created.append(entry)

        try:
            self._db.session.commit()
        except Exception:
            self._db.session.rollback()
            raise

        # ---- Annotate bundles ----------------------------------------
        self._annotate_bundles(patient_mrn_hash)

        return created

    # ================================================================
    # 3. refresh_rules_for_medication
    # ================================================================

    def refresh_rules_for_medication(
        self, drug_name: str, rxcui: str = None
    ) -> list:
        """
        Force-refresh monitoring rules for a single medication from
        DailyMed/Drug@FDA, ignoring cache freshness.
        """
        # Invalidate existing rules so waterfall proceeds past step 1
        if rxcui:
            MonitoringRule.query.filter_by(
                rxcui=rxcui, trigger_type='MEDICATION'
            ).update({'last_refreshed': datetime(2000, 1, 1, tzinfo=timezone.utc)})
            self._db.session.commit()

        return self.get_monitoring_rules(rxcui=rxcui, drug_name=drug_name)

    # ================================================================
    # 4. refresh_condition_rules
    # ================================================================

    def refresh_condition_rules(self, icd10_code: str) -> list:
        """Return condition-driven rules, refreshing from seed if needed."""
        return self._get_condition_rules(icd10_code)

    # ================================================================
    # 5. get_overdue_monitoring
    # ================================================================

    def get_overdue_monitoring(self, patient_mrn_hash: str) -> list:
        """
        Return active MonitoringSchedule entries that are overdue or
        due within the next 7 days (visit-day window).
        """
        cutoff = date.today() + timedelta(days=7)
        return (
            MonitoringSchedule.query
            .filter_by(patient_mrn_hash=patient_mrn_hash, status='active')
            .filter(MonitoringSchedule.next_due_date <= cutoff)
            .order_by(MonitoringSchedule.next_due_date)
            .all()
        )

    # ================================================================
    # 6. bulk_refresh_new_medications
    # ================================================================

    def bulk_refresh_new_medications(self, lookback_days: int = 7) -> int:
        """
        Query medications added in the past N days that lack
        MonitoringRule entries, and populate rules via waterfall.
        Returns count of new rules created.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        recent_meds = (
            PatientMedication.query
            .filter(PatientMedication.created_at >= cutoff)
            .filter(PatientMedication.status == 'active')
            .all()
        )

        count = 0
        seen_rxcui = set()
        for med in recent_meds:
            rxcui = med.rxnorm_cui or ''
            if not rxcui or rxcui in seen_rxcui:
                continue
            seen_rxcui.add(rxcui)

            existing = MonitoringRule.query.filter_by(
                rxcui=rxcui, trigger_type='MEDICATION'
            ).first()
            if existing:
                continue

            rules = self.get_monitoring_rules(
                rxcui=rxcui, drug_name=med.drug_name
            )
            count += len(rules)

        return count

    # ================================================================
    # 6b. refresh_preventive_vsac_oids  (B4)
    # ================================================================

    def refresh_preventive_vsac_oids(self) -> int:
        """
        Expand all PREVENTIVE_VSAC_OIDS through the UMLS/VSAC service
        and update VsacValueSetCache entries.  Returns the number of
        OIDs successfully refreshed.
        """
        try:
            from app.services.billing_valueset_map import PREVENTIVE_VSAC_OIDS
            from app.services.api.umls import UMLSService
            from models.api_cache import VsacValueSetCache
        except ImportError as exc:
            logger.warning("Cannot refresh preventive VSAC OIDs: %s", exc)
            return 0

        umls = UMLSService(self._db)
        refreshed = 0

        for service_key, oid in PREVENTIVE_VSAC_OIDS.items():
            try:
                codes = umls.get_vsac_value_set(oid)
                if not codes:
                    continue

                existing = VsacValueSetCache.query.filter_by(oid=oid).first()
                codes_json = json.dumps(codes)

                if existing:
                    existing.codes_json = codes_json
                    existing.code_count = len(codes)
                    existing.cached_at = datetime.now(timezone.utc)
                    existing.name = service_key
                else:
                    entry = VsacValueSetCache(
                        oid=oid,
                        name=service_key,
                        codes_json=codes_json,
                        code_count=len(codes),
                        source='vsac_api',
                    )
                    self._db.session.add(entry)

                self._db.session.flush()
                refreshed += 1
            except Exception as exc:
                logger.debug(
                    "VSAC refresh failed for %s (%s): %s",
                    service_key, oid, exc,
                )

        try:
            self._db.session.commit()
        except Exception:
            self._db.session.rollback()

        logger.info(
            "[MonitoringRuleEngine] Refreshed %d/%d preventive VSAC OIDs",
            refreshed, len(PREVENTIVE_VSAC_OIDS),
        )
        return refreshed

    # ================================================================
    # 7. get_rems_entries
    # ================================================================

    def get_rems_entries(self, patient_mrn_hash: str) -> list:
        """Return all active REMS tracker entries for a patient."""
        return (
            REMSTrackerEntry.query
            .filter_by(patient_mrn_hash=patient_mrn_hash, status='active')
            .order_by(REMSTrackerEntry.next_due_date)
            .all()
        )

    # ================================================================
    # 8. compute_egfr_alerts
    # ================================================================

    def compute_egfr_alerts(
        self,
        patient_mrn_hash: str,
        medications: list = None,
        lab_results: list = None,
    ) -> list:
        """
        Check latest eGFR against medication-specific KDIGO thresholds.
        Returns list of alert dicts with action, message, drug, egfr.
        """
        # Get latest eGFR
        egfr_value = self._get_latest_numeric_lab(
            patient_mrn_hash, lab_results,
            loinc_codes=[_LOINC_EGFR, '2160-0'],
            test_names=['egfr', 'gfr', 'glomerular'],
        )
        if egfr_value is None:
            return []

        # Get active meds if not provided
        if medications is None:
            medications = (
                PatientMedication.query
                .filter_by(mrn=patient_mrn_hash, status='active')
                .all()
            )

        alerts = []
        for med in medications:
            drug_name = _attr(med, 'drug_name', '').lower()
            for stem, thresholds in _EGFR_THRESHOLDS.items():
                if stem not in drug_name:
                    continue
                for t in thresholds:
                    lo = t.get('min', 0)
                    hi = t.get('max', 999)
                    if lo <= egfr_value < hi:
                        alerts.append({
                            'action': t['action'],
                            'message': t['msg'].format(value=egfr_value),
                            'drug': _attr(med, 'drug_name', ''),
                            'egfr': egfr_value,
                            'priority': 'critical' if t['action'] == 'CONTRAINDICATED' else 'high',
                            'guideline': 'KDIGO',
                        })
        return alerts

    # ================================================================
    # 9. compute_meld_score
    # ================================================================

    def compute_meld_score(
        self, patient_mrn_hash: str, lab_results: list = None
    ) -> dict:
        """
        Compute MELD-Na score from latest labs.

        Returns dict with score, class_label, component_values,
        triggered_actions, last_computed.
        """
        inr = self._get_latest_numeric_lab(
            patient_mrn_hash, lab_results,
            loinc_codes=[_LOINC_INR], test_names=['inr'],
        )
        bili = self._get_latest_numeric_lab(
            patient_mrn_hash, lab_results,
            loinc_codes=[_LOINC_BILI], test_names=['bilirubin total', 'total bilirubin'],
        )
        creat = self._get_latest_numeric_lab(
            patient_mrn_hash, lab_results,
            loinc_codes=[_LOINC_CREAT], test_names=['creatinine'],
        )
        sodium = self._get_latest_numeric_lab(
            patient_mrn_hash, lab_results,
            loinc_codes=[_LOINC_SODIUM], test_names=['sodium'],
        )

        if None in (inr, bili, creat):
            return {'score': None, 'reason': 'Insufficient labs (need INR, bilirubin, creatinine)'}

        # Clamp per MELD formula rules
        inr = max(inr, 1.0)
        bili = max(bili, 1.0)
        creat = min(max(creat, 1.0), 4.0)

        meld = round(
            10 * (
                0.957 * math.log(creat)
                + 0.378 * math.log(bili)
                + 1.120 * math.log(inr)
                + 0.643
            )
        )
        meld = min(max(meld, 6), 40)

        # MELD-Na adjustment (sodium 125–137)
        if sodium is not None:
            na = min(max(sodium, 125), 137)
            meld_na = round(
                meld + 1.32 * (137 - na) - 0.033 * meld * (137 - na)
            )
            meld_na = min(max(meld_na, 6), 40)
        else:
            meld_na = meld

        actions = []
        if meld_na >= 20:
            actions.append('Transplant evaluation advisory')
        elif meld_na >= 15:
            actions.append('Hepatology referral recommendation')
        elif meld_na >= 10:
            actions.append('Flag for hepatology review')

        label = 'Low' if meld_na < 10 else 'Moderate' if meld_na < 20 else 'High'

        return {
            'score': meld_na,
            'meld_raw': meld,
            'class_label': label,
            'component_values': {
                'inr': inr, 'bilirubin': bili,
                'creatinine': creat, 'sodium': sodium,
            },
            'triggered_actions': actions,
            'last_computed': datetime.now(timezone.utc).isoformat(),
        }

    # ================================================================
    # 10. compute_child_pugh_score
    # ================================================================

    def compute_child_pugh_score(
        self, patient_mrn_hash: str, lab_results: list = None
    ) -> dict:
        """
        Compute Child-Pugh score from labs + clinical parameters.

        Bilirubin, albumin, INR are from labs. Ascites and
        encephalopathy default to 'none' (1 point each) since we
        lack structured clinical data — can be overridden via kwargs
        in future versions.
        """
        bili = self._get_latest_numeric_lab(
            patient_mrn_hash, lab_results,
            loinc_codes=[_LOINC_BILI], test_names=['bilirubin total', 'total bilirubin'],
        )
        albumin = self._get_latest_numeric_lab(
            patient_mrn_hash, lab_results,
            loinc_codes=[_LOINC_ALBUMIN], test_names=['albumin'],
        )
        inr = self._get_latest_numeric_lab(
            patient_mrn_hash, lab_results,
            loinc_codes=[_LOINC_INR], test_names=['inr'],
        )

        if None in (bili, albumin, inr):
            return {'score': None, 'reason': 'Insufficient labs (need bilirubin, albumin, INR)'}

        # Bilirubin points
        if bili < 2:
            bili_pts = 1
        elif bili <= 3:
            bili_pts = 2
        else:
            bili_pts = 3

        # Albumin points
        if albumin > 3.5:
            alb_pts = 1
        elif albumin >= 2.8:
            alb_pts = 2
        else:
            alb_pts = 3

        # INR points
        if inr < 1.7:
            inr_pts = 1
        elif inr <= 2.3:
            inr_pts = 2
        else:
            inr_pts = 3

        # Ascites + encephalopathy default to none (1 pt each)
        ascites_pts = 1
        enceph_pts = 1

        total = bili_pts + alb_pts + inr_pts + ascites_pts + enceph_pts

        if total <= 6:
            cls = 'A'
            label = 'Well-compensated'
        elif total <= 9:
            cls = 'B'
            label = 'Significant functional compromise'
        else:
            cls = 'C'
            label = 'Decompensated'

        actions = []
        if cls in ('B', 'C'):
            actions.append('Intensify monitoring (LFTs monthly)')
            actions.append('Hepatology co-management flag')
        if cls == 'C':
            actions.append('Transplant evaluation advisory')

        return {
            'score': total,
            'class_label': f'Class {cls} — {label}',
            'component_values': {
                'bilirubin': bili, 'bilirubin_pts': bili_pts,
                'albumin': albumin, 'albumin_pts': alb_pts,
                'inr': inr, 'inr_pts': inr_pts,
                'ascites_pts': ascites_pts,
                'encephalopathy_pts': enceph_pts,
            },
            'triggered_actions': actions,
            'last_computed': datetime.now(timezone.utc).isoformat(),
        }

    # ================================================================
    # 11. export_rules_as_fhir_plan_definition
    # ================================================================

    def export_rules_as_fhir_plan_definition(
        self, rxcui: str = None, icd10_code: str = None
    ) -> dict:
        """
        Export MonitoringRule entries as a FHIR R4 PlanDefinition
        resource (JSON).  Each rule maps to an action entry with
        timingTiming, definitionCanonical (LOINC), and trigger
        conditions.
        """
        q = MonitoringRule.query.filter_by(is_active=True)
        if rxcui:
            q = q.filter_by(rxcui=rxcui)
        if icd10_code:
            q = q.filter_by(icd10_trigger=icd10_code)

        rules = q.all()

        actions = []
        for rule in rules:
            action = {
                'title': rule.lab_name,
                'description': rule.clinical_context or '',
                'priority': rule.priority,
                'timingTiming': {
                    'repeat': {
                        'frequency': 1,
                        'period': rule.interval_days,
                        'periodUnit': 'd',
                    }
                },
                'definitionCanonical': f'https://loinc.org/{rule.lab_loinc_code}',
                'code': [
                    {
                        'coding': [{
                            'system': 'https://loinc.org',
                            'code': rule.lab_loinc_code,
                            'display': rule.lab_name,
                        }]
                    }
                ],
            }
            if rule.icd10_trigger:
                action['condition'] = [{
                    'kind': 'applicability',
                    'expression': {
                        'language': 'text/fhirpath',
                        'expression': (
                            f"Condition.code.coding.where("
                            f"system='http://hl7.org/fhir/sid/icd-10-cm' "
                            f"and code='{rule.icd10_trigger}')"
                        ),
                    }
                }]
            actions.append(action)

        trigger_desc = rxcui or icd10_code or 'all'
        return {
            'resourceType': 'PlanDefinition',
            'status': 'active',
            'title': f'Monitoring Plan — {trigger_desc}',
            'date': datetime.now(timezone.utc).isoformat(),
            'publisher': 'CareCompanion MonitoringRuleEngine',
            'action': actions,
        }

    # ================================================================
    # 12. get_cds_hooks_cards
    # ================================================================

    def get_cds_hooks_cards(self, patient_mrn_hash: str) -> list:
        """
        Return CDS Hooks-compliant card structures for a patient's
        active monitoring needs, REMS status, and clinical alerts.
        """
        cards = []

        # Overdue monitoring cards
        overdue = self.get_overdue_monitoring(patient_mrn_hash)
        for entry in overdue:
            indicator = 'critical' if entry.priority == 'critical' else (
                'warning' if entry.next_due_date < date.today() else 'info'
            )
            cards.append({
                'summary': f'{entry.lab_name} due {entry.next_due_date}',
                'detail': entry.clinical_indication or '',
                'indicator': indicator,
                'source': {
                    'label': 'CareCompanion Monitoring',
                    'url': '',
                },
                'suggestions': [{
                    'label': f'Order {entry.lab_name}',
                    'actions': [{
                        'type': 'create',
                        'description': f'Order {entry.lab_name} (CPT {entry.lab_code})',
                        'resource': {
                            'resourceType': 'ServiceRequest',
                            'code': {
                                'coding': [{
                                    'system': 'http://www.ama-assn.org/go/cpt',
                                    'code': entry.lab_code,
                                    'display': entry.lab_name,
                                }]
                            },
                        },
                    }],
                }],
            })

        # REMS cards
        rems_entries = self.get_rems_entries(patient_mrn_hash)
        for entry in rems_entries:
            indicator = 'critical' if entry.escalation_level >= 2 else 'warning'
            cards.append({
                'summary': (
                    f'REMS: {entry.rems_program_name} — '
                    f'{entry.requirement_type} due {entry.next_due_date}'
                ),
                'detail': entry.requirement_description or '',
                'indicator': indicator,
                'source': {'label': 'CareCompanion REMS Tracker', 'url': ''},
                'suggestions': [],
            })

        # eGFR alerts
        egfr_alerts = self.compute_egfr_alerts(patient_mrn_hash)
        for alert in egfr_alerts:
            cards.append({
                'summary': alert['message'],
                'detail': f'KDIGO guideline — {alert["drug"]}',
                'indicator': 'critical' if alert['action'] == 'CONTRAINDICATED' else 'warning',
                'source': {'label': 'CareCompanion KDIGO', 'url': ''},
                'suggestions': [],
            })

        return cards

    # ================================================================
    # Private helpers
    # ================================================================

    def _query_cached_rules(self, rxcui: str) -> list:
        """Step 1: Check DB cache for fresh rules."""
        if not rxcui:
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(days=_RULE_CACHE_DAYS)
        rules = (
            MonitoringRule.query
            .filter_by(rxcui=rxcui, is_active=True, trigger_type='MEDICATION')
            .filter(MonitoringRule.last_refreshed >= cutoff)
            .all()
        )
        return rules

    def _fetch_dailymed_rules(self, drug_name: str, rxcui: str) -> list:
        """Step 2: Call DailyMed SPL extraction and persist rules."""
        if not drug_name:
            return []
        try:
            from app.services.api.dailymed import DailyMedService
            dm = DailyMedService(self._db)
            results = dm.extract_monitoring_requirements(drug_name, rxcui)
        except Exception as exc:
            logger.warning("DailyMed extraction failed for %s: %s", drug_name, exc)
            return []

        rules = []
        for r in results:
            rule = self._upsert_rule(
                rxcui=rxcui or '',
                lab_loinc=r['lab_loinc_code'],
                lab_cpt=r.get('lab_cpt_code', r['lab_loinc_code']),
                lab_name=r['lab_name'],
                interval_days=r['interval_days'],
                priority=r.get('priority', 'standard'),
                source='DAILYMED' if r.get('extraction_confidence', 0) < 0.85 else 'LLM_EXTRACTED',
                confidence=r.get('extraction_confidence', 0.8),
                context=r.get('clinical_context', ''),
                evidence_url=r.get('evidence_source_url', ''),
            )
            if rule:
                rules.append(rule)
        return rules

    def _fetch_drugfda_pmr_rules(self, drug_name: str, rxcui: str) -> list:
        """
        Step 3: Query OpenFDA Drug@FDA for post-marketing requirements.
        Returns list of MonitoringRule entries from PMR/PMC descriptions.
        """
        if not drug_name:
            return []
        try:
            url = (
                'https://api.fda.gov/drug/drugsfda.json'
                f'?search=openfda.brand_name:"{drug_name}"'
                '&limit=1'
            )
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'CareCompanion/1.0',
                    'Accept': 'application/json',
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            results = data.get('results', [])
            if not results:
                return []

            # Scan submissions for PMR/PMC docs
            rules = []
            for submission in results[0].get('submissions', []):
                for doc in submission.get('application_docs', []):
                    doc_type = doc.get('type', '').upper()
                    if 'PMR' not in doc_type and 'PMC' not in doc_type:
                        continue

                    title = doc.get('title', '')
                    if not title:
                        continue

                    # Use the B1 regex extraction on PMR text
                    from app.services.api.dailymed import DailyMedService
                    dm = DailyMedService(self._db)
                    matches = dm._regex_extract_monitoring(title)
                    for m in matches:
                        loinc, cpt, name = dm._normalize_lab_to_loinc(
                            m['lab_text']
                        )
                        if not loinc:
                            continue
                        interval = dm._extract_interval(m['interval_text'])
                        rule = self._upsert_rule(
                            rxcui=rxcui or '',
                            lab_loinc=loinc,
                            lab_cpt=cpt or loinc,
                            lab_name=name or m['lab_text'],
                            interval_days=interval,
                            priority='high',
                            source='DRUG_AT_FDA',
                            confidence=0.7,
                            context=title[:200],
                            evidence_url=doc.get('url', ''),
                        )
                        if rule:
                            rules.append(rule)
            return rules
        except Exception as exc:
            logger.debug("Drug@FDA PMR query failed for %s: %s", drug_name, exc)
            return []

    def _rxclass_fallback(self, rxcui: str) -> list:
        """
        Step 4: If no direct rules, check if any RxClass class-level
        rules exist for the drug's therapeutic classes.
        """
        if not rxcui:
            return []
        try:
            from app.services.api.rxclass import RxClassService
            rxclass = RxClassService(self._db)
            classes = rxclass.get_classes_for_drug(rxcui)
        except Exception:
            return []

        rules = []
        for cls in classes:
            class_id = cls.get('classId', cls.get('rxclassMinConceptItem', {}).get('classId', ''))
            if not class_id:
                continue
            class_rules = (
                MonitoringRule.query
                .filter_by(rxclass_id=class_id, is_active=True)
                .all()
            )
            rules.extend(class_rules)

        return rules

    def _get_condition_rules(self, icd10_code: str) -> list:
        """Return seed/manual rules for a condition ICD-10 code."""
        if not icd10_code:
            return []

        # Exact match first
        rules = (
            MonitoringRule.query
            .filter_by(
                icd10_trigger=icd10_code,
                trigger_type='CONDITION',
                is_active=True,
            )
            .all()
        )
        if rules:
            return rules

        # Prefix match (e.g., E11 matches E11.9, E11.65)
        prefix = icd10_code.split('.')[0]
        if prefix != icd10_code:
            rules = (
                MonitoringRule.query
                .filter(
                    MonitoringRule.icd10_trigger.like(f'{prefix}%'),
                    MonitoringRule.trigger_type == 'CONDITION',
                    MonitoringRule.is_active == True,
                )
                .all()
            )
        return rules

    def _upsert_rule(self, *, rxcui, lab_loinc, lab_cpt, lab_name,
                     interval_days, priority, source, confidence,
                     context, evidence_url) -> MonitoringRule | None:
        """Insert or update a MonitoringRule, respecting unique constraint."""
        try:
            existing = MonitoringRule.query.filter_by(
                rxcui=rxcui,
                lab_loinc_code=lab_loinc,
                trigger_type='MEDICATION',
            ).first()

            if existing:
                existing.last_refreshed = datetime.now(timezone.utc)
                if confidence > existing.extraction_confidence:
                    existing.extraction_confidence = confidence
                    existing.source = source
                    existing.interval_days = interval_days
                    existing.clinical_context = context
                self._db.session.flush()
                return existing

            rule = MonitoringRule(
                rxcui=rxcui,
                trigger_type='MEDICATION',
                source=source,
                lab_loinc_code=lab_loinc,
                lab_cpt_code=lab_cpt,
                lab_name=lab_name,
                interval_days=interval_days,
                priority=priority,
                evidence_source_url=evidence_url,
                extraction_confidence=confidence,
                clinical_context=context,
                is_active=True,
            )
            self._db.session.add(rule)
            self._db.session.flush()
            return rule
        except Exception as exc:
            self._db.session.rollback()
            logger.debug("Rule upsert failed: %s", exc)
            return None

    def _upsert_schedule_entry(
        self, patient_mrn_hash, user_id, rule, lab_index,
        seen_loinc, triggering_medication=None, triggering_condition=None,
    ) -> MonitoringSchedule | None:
        """Create or update a MonitoringSchedule entry for one rule."""
        loinc = rule.lab_loinc_code if isinstance(rule, MonitoringRule) else rule.get('lab_loinc_code', '')
        interval = rule.interval_days if isinstance(rule, MonitoringRule) else rule.get('interval_days', 180)
        lab_name = rule.lab_name if isinstance(rule, MonitoringRule) else rule.get('lab_name', '')
        lab_cpt = rule.lab_cpt_code if isinstance(rule, MonitoringRule) else rule.get('lab_cpt_code', loinc)
        priority = rule.priority if isinstance(rule, MonitoringRule) else rule.get('priority', 'standard')
        source = rule.source if isinstance(rule, MonitoringRule) else rule.get('source', '')
        rule_id = rule.id if isinstance(rule, MonitoringRule) else None
        context = rule.clinical_context if isinstance(rule, MonitoringRule) else rule.get('clinical_context', '')

        if not loinc:
            return None

        # Deduplication: keep shortest interval
        if loinc in seen_loinc:
            if interval >= seen_loinc[loinc]:
                return None
        seen_loinc[loinc] = interval

        # Determine last performed date from lab history
        last_date = lab_index.get(loinc, {}).get('date')
        last_value = lab_index.get(loinc, {}).get('value', '')
        last_flag = lab_index.get(loinc, {}).get('flag', '')

        if last_date:
            next_due = last_date + timedelta(days=interval)
        else:
            next_due = date.today()  # No result on file → immediately due

        # Check for existing entry
        existing = MonitoringSchedule.query.filter_by(
            patient_mrn_hash=patient_mrn_hash,
            lab_code=lab_cpt,
            status='active',
        ).first()

        if existing:
            # Update if shorter interval
            if interval < existing.interval_days:
                existing.interval_days = interval
                existing.next_due_date = next_due
                existing.monitoring_rule_id = rule_id
            if last_value:
                existing.last_result_value = str(last_value)
                existing.last_result_flag = last_flag
            return existing

        entry = MonitoringSchedule(
            patient_mrn_hash=patient_mrn_hash,
            user_id=user_id,
            monitoring_rule_id=rule_id,
            lab_code=lab_cpt,
            lab_name=lab_name,
            clinical_indication=context[:300] if context else '',
            triggering_medication=triggering_medication,
            triggering_condition=triggering_condition,
            last_performed_date=last_date,
            next_due_date=next_due,
            interval_days=interval,
            priority=priority,
            source=source,
            last_result_value=str(last_value) if last_value else None,
            last_result_flag=last_flag,
            status='active',
        )
        self._db.session.add(entry)
        return entry

    def _build_lab_index(self, lab_results: list) -> dict:
        """
        Build a dict mapping LOINC code → {date, value, flag} from
        a list of PatientLabResult objects or dicts. Keeps the most
        recent result per LOINC code.
        """
        index = {}
        for lab in lab_results:
            loinc = _attr(lab, 'loinc_code', '')
            if not loinc:
                continue
            result_date = _attr(lab, 'result_date', None)
            if result_date and isinstance(result_date, datetime):
                result_date = result_date.date()

            existing = index.get(loinc)
            if existing and existing['date'] and result_date:
                if result_date <= existing['date']:
                    continue

            index[loinc] = {
                'date': result_date,
                'value': _attr(lab, 'result_value', ''),
                'flag': _attr(lab, 'result_flag', 'normal'),
            }
        return index

    def _get_latest_numeric_lab(
        self, patient_mrn_hash, lab_results, loinc_codes, test_names,
    ) -> float | None:
        """
        Extract the latest numeric lab value matching LOINC codes or
        test name keywords from provided lab_results or DB query.
        """
        candidates = lab_results or []

        # If no results provided, query DB
        if not candidates:
            candidates = (
                PatientLabResult.query
                .filter_by(patient_mrn_hash=patient_mrn_hash)
                .order_by(PatientLabResult.result_date.desc())
                .limit(200)
                .all()
            )

        best_date = None
        best_value = None

        for lab in candidates:
            loinc = _attr(lab, 'loinc_code', '')
            name = _attr(lab, 'test_name', '').lower()
            rdate = _attr(lab, 'result_date', None)
            rval = _attr(lab, 'result_value', '')

            matched = False
            if loinc and loinc in loinc_codes:
                matched = True
            elif any(t in name for t in test_names):
                matched = True

            if not matched:
                continue

            # Parse numeric value
            try:
                # Handle values like ">60", "<10", "12.5 mg/dL"
                clean = str(rval).strip().lstrip('<>').split()[0]
                numeric = float(clean)
            except (ValueError, IndexError):
                continue

            if rdate and isinstance(rdate, datetime):
                rdate = rdate.date()

            if best_date is None or (rdate and rdate > best_date):
                best_date = rdate
                best_value = numeric

        return best_value

    def _annotate_bundles(self, patient_mrn_hash: str):
        """
        Set can_bundle_with on MonitoringSchedule entries where
        multiple labs can share a single venipuncture.
        """
        entries = (
            MonitoringSchedule.query
            .filter_by(patient_mrn_hash=patient_mrn_hash, status='active')
            .all()
        )
        if not entries:
            return

        entry_by_loinc = {}
        for e in entries:
            # Use lab_code (CPT) as key since that's what we have
            entry_by_loinc[e.lab_code] = e

        for bundle_key, bundle in _MONITORING_BUNDLES.items():
            matched_ids = []
            for loinc in bundle['labs']:
                e = entry_by_loinc.get(loinc)
                if e:
                    matched_ids.append(str(e.id))

            if len(matched_ids) >= 2:
                bundle_str = ','.join(matched_ids)
                for loinc in bundle['labs']:
                    e = entry_by_loinc.get(loinc)
                    if e:
                        e.can_bundle_with = bundle_str

    @staticmethod
    def _merge_rules(existing: list, new_rules: list) -> list:
        """Merge new rules into existing list, avoiding duplicates by LOINC."""
        seen = {r.lab_loinc_code for r in existing if isinstance(r, MonitoringRule)}
        merged = list(existing)
        for r in new_rules:
            loinc = r.lab_loinc_code if isinstance(r, MonitoringRule) else ''
            if loinc and loinc not in seen:
                seen.add(loinc)
                merged.append(r)
        return merged


# ── Module-level helper ────────────────────────────────────────────

def _attr(obj, name, default=None):
    """Safely get attribute from object or dict."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)

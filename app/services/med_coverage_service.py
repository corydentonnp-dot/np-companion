"""
CareCompanion — MedCoverageService
File: app/services/med_coverage_service.py

Phase MM-2.3: Coverage analysis — identifies unmapped meds, dead rules,
low-confidence entries, and provides the coverage review queue.

Public API
----------
get_coverage_queue(filters, page, per_page)
get_coverage_stats()
accept_suggested_rule(catalog_entry_id)
suppress_medication(catalog_entry_id, reason)
apply_class_rule(catalog_entry_id)
get_dead_rules()
"""

import logging
from datetime import datetime, timedelta, timezone

from models import db
from models.monitoring import (
    MedicationCatalogEntry, MonitoringRule, MonitoringRuleOverride,
    MonitoringEvaluationLog,
)

logger = logging.getLogger(__name__)


class MedCoverageService:
    """Coverage analysis and review queue for medication monitoring."""

    def __init__(self, db_session=None):
        self._db = db_session or db

    # ================================================================
    # 1. Coverage queue — entries needing review
    # ================================================================

    def get_coverage_queue(
        self,
        filters: dict = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict:
        """
        Return catalog entries needing human review:
          - status = 'unmapped' or 'pending_review'
          - confidence < 0.5
          - last_refreshed > 30 days ago
          - rxcui present but no active monitoring rule

        Returns dict with items, total, page, per_page, pages.
        """
        filters = filters or {}
        q = MedicationCatalogEntry.query.filter_by(is_active=True)

        reason_filter = filters.get('reason')

        if reason_filter == 'unmapped':
            q = q.filter(MedicationCatalogEntry.status.in_(['unmapped', 'pending_review']))
        elif reason_filter == 'low_confidence':
            q = q.filter(MedicationCatalogEntry.source_confidence < 0.5)
        elif reason_filter == 'stale':
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            q = q.filter(
                db.or_(
                    MedicationCatalogEntry.last_refreshed_at < cutoff,
                    MedicationCatalogEntry.last_refreshed_at == None,
                )
            )
        else:
            # Default: show all entries that need attention
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            q = q.filter(
                db.or_(
                    MedicationCatalogEntry.status.in_(['unmapped', 'pending_review']),
                    MedicationCatalogEntry.source_confidence < 0.5,
                    db.and_(
                        MedicationCatalogEntry.last_refreshed_at < cutoff,
                        MedicationCatalogEntry.last_refreshed_at != None,
                    ),
                    MedicationCatalogEntry.last_refreshed_at == None,
                )
            )

        if filters.get('search'):
            term = f"%{filters['search']}%"
            q = q.filter(
                db.or_(
                    MedicationCatalogEntry.display_name.ilike(term),
                    MedicationCatalogEntry.ingredient_name.ilike(term),
                )
            )

        q = q.order_by(
            MedicationCatalogEntry.local_patient_count.desc(),
            MedicationCatalogEntry.display_name,
        )

        total = q.count()
        pages = max(1, (total + per_page - 1) // per_page)
        items = q.offset((page - 1) * per_page).limit(per_page).all()

        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages,
        }

    # ================================================================
    # 2. Coverage statistics
    # ================================================================

    def get_coverage_stats(self) -> dict:
        """
        Comprehensive coverage stats for the dashboard.
        """
        total_meds = MedicationCatalogEntry.query.filter_by(is_active=True).count()

        # Meds with at least one monitoring rule
        meds_with_rules = (
            self._db.session.query(MedicationCatalogEntry.id)
            .filter(MedicationCatalogEntry.is_active == True)
            .filter(MedicationCatalogEntry.rxcui != '')
            .filter(MedicationCatalogEntry.rxcui != None)
            .join(MonitoringRule, MonitoringRule.rxcui == MedicationCatalogEntry.rxcui)
            .filter(MonitoringRule.is_active == True)
            .distinct()
            .count()
        )

        # Rules by source
        source_counts = {}
        source_rows = (
            self._db.session.query(
                MonitoringRule.source,
                db.func.count(MonitoringRule.id),
            )
            .filter(MonitoringRule.is_active == True)
            .group_by(MonitoringRule.source)
            .all()
        )
        for source, count in source_rows:
            source_counts[source or 'unknown'] = count

        # Total active rules
        total_rules = MonitoringRule.query.filter_by(is_active=True).count()

        # Unique labs covered
        labs_covered = (
            self._db.session.query(MonitoringRule.lab_loinc_code)
            .filter(MonitoringRule.is_active == True)
            .filter(MonitoringRule.lab_loinc_code != '')
            .distinct()
            .count()
        )

        # Unmapped meds
        unmapped = MedicationCatalogEntry.query.filter_by(
            status='unmapped', is_active=True
        ).count()

        pending = MedicationCatalogEntry.query.filter_by(
            status='pending_review', is_active=True
        ).count()

        # Low confidence
        low_confidence = (
            MedicationCatalogEntry.query
            .filter(MedicationCatalogEntry.source_confidence < 0.5)
            .filter_by(is_active=True)
            .count()
        )

        # Rules never fired (from evaluation log)
        never_fired_count = 0
        try:
            fired_rule_ids = (
                self._db.session.query(
                    db.func.json_each(MonitoringEvaluationLog.matched_rule_ids).columns.value
                )
                .filter(MonitoringEvaluationLog.fired == True)
                .distinct()
                .all()
            )
            fired_set = {str(r[0]) for r in fired_rule_ids}
            all_rule_ids = {
                str(r.id) for r in
                MonitoringRule.query.filter_by(is_active=True).all()
            }
            never_fired_count = len(all_rule_ids - fired_set)
        except Exception:
            # json_each may not work in all SQLite versions
            never_fired_count = 0

        # Override count
        overrides = MonitoringRuleOverride.query.filter_by(
            override_active=True
        ).count()

        return {
            'total_meds': total_meds,
            'meds_with_rules': meds_with_rules,
            'meds_without_rules': total_meds - meds_with_rules,
            'total_rules': total_rules,
            'rules_by_source': source_counts,
            'labs_covered': labs_covered,
            'unmapped': unmapped,
            'pending_review': pending,
            'low_confidence': low_confidence,
            'never_fired': never_fired_count,
            'overrides': overrides,
        }

    # ================================================================
    # 3. Accept a suggested rule
    # ================================================================

    def accept_suggested_rule(self, catalog_entry_id: int) -> dict:
        """
        Mark a pending_review catalog entry as 'active' — confirming
        that its current rule mapping is acceptable.
        """
        entry = MedicationCatalogEntry.query.get(catalog_entry_id)
        if not entry:
            return {'success': False, 'error': 'Entry not found'}

        entry.status = 'active'
        entry.updated_at = datetime.now(timezone.utc)

        try:
            self._db.session.commit()
        except Exception:
            self._db.session.rollback()
            raise

        return {'success': True, 'entry_id': catalog_entry_id}

    # ================================================================
    # 4. Suppress a medication
    # ================================================================

    def suppress_medication(
        self, catalog_entry_id: int, reason: str = ''
    ) -> dict:
        """
        Mark a catalog entry as 'suppressed' — it will not generate
        monitoring reminders. This is a clinical decision, not a delete.
        """
        entry = MedicationCatalogEntry.query.get(catalog_entry_id)
        if not entry:
            return {'success': False, 'error': 'Entry not found'}

        entry.status = 'suppressed'
        entry.notes = f"Suppressed: {reason}" if reason else entry.notes
        entry.updated_at = datetime.now(timezone.utc)

        try:
            self._db.session.commit()
        except Exception:
            self._db.session.rollback()
            raise

        return {'success': True, 'entry_id': catalog_entry_id}

    # ================================================================
    # 5. Apply class rule to unmapped med
    # ================================================================

    def apply_class_rule(self, catalog_entry_id: int) -> dict:
        """
        For an unmapped medication, find and apply monitoring rules
        from its drug class (via rxcui → rxclass).
        """
        entry = MedicationCatalogEntry.query.get(catalog_entry_id)
        if not entry:
            return {'success': False, 'error': 'Entry not found'}

        if not entry.rxcui:
            return {'success': False, 'error': 'No RxCUI — cannot look up class rules'}

        try:
            from app.services.monitoring_rule_engine import MonitoringRuleEngine
            engine = MonitoringRuleEngine(self._db)
            rules = engine._rxclass_fallback(entry.rxcui)
            if rules:
                entry.status = 'active'
                entry.updated_at = datetime.now(timezone.utc)
                self._db.session.commit()
                return {
                    'success': True,
                    'entry_id': catalog_entry_id,
                    'rules_found': len(rules),
                }
        except Exception as exc:
            self._db.session.rollback()
            logger.error("Class rule application failed: %s", exc)
            return {'success': False, 'error': str(exc)}

        return {'success': False, 'error': 'No class-level rules found'}

    # ================================================================
    # 6. Dead rules — never fired, low confidence, stale
    # ================================================================

    def get_dead_rules(self) -> list:
        """
        Return monitoring rules that appear dead:
          - Never fired in evaluation log (if eval data exists)
          - Confidence < 0.5 with no override
          - last_refreshed > 90 days ago

        Returns list of dicts with rule info and reason.
        """
        dead = []
        stale_cutoff = datetime.now(timezone.utc) - timedelta(days=90)

        # Low-confidence rules without overrides
        low_conf_rules = (
            MonitoringRule.query
            .filter(MonitoringRule.extraction_confidence < 0.5)
            .filter_by(is_active=True)
            .all()
        )
        for rule in low_conf_rules:
            has_override = MonitoringRuleOverride.query.filter_by(
                monitoring_rule_id=rule.id, override_active=True
            ).first()
            if not has_override:
                dead.append({
                    'rule_id': rule.id,
                    'lab_name': rule.lab_name,
                    'rxcui': rule.rxcui,
                    'confidence': rule.extraction_confidence,
                    'reason': 'low_confidence',
                })

        # Stale rules
        stale_rules = (
            MonitoringRule.query
            .filter(MonitoringRule.last_refreshed < stale_cutoff)
            .filter_by(is_active=True)
            .all()
        )
        seen_ids = {d['rule_id'] for d in dead}
        for rule in stale_rules:
            if rule.id not in seen_ids:
                dead.append({
                    'rule_id': rule.id,
                    'lab_name': rule.lab_name,
                    'rxcui': rule.rxcui,
                    'last_refreshed': rule.last_refreshed.isoformat() if rule.last_refreshed else None,
                    'reason': 'stale',
                })

        return dead

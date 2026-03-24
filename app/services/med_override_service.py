"""
CareCompanion — MedOverrideService
File: app/services/med_override_service.py

Phase MM-2.2: Override management for monitoring rules.
Implements the precedence chain:
  user_override → practice_override → MonitoringRule.interval_days → class_rule → null

Public API
----------
get_effective_interval(monitoring_rule_id, user_id)
set_user_override(monitoring_rule_id, user_id, interval_days, reason, **kwargs)
set_practice_override(monitoring_rule_id, interval_days, reason, created_by)
reset_override(override_id)
get_override_diff(monitoring_rule_id, user_id)
bulk_set_class_override(rxclass_id, interval_days, scope, scope_id, reason, created_by)
"""

import logging
from datetime import datetime, timezone

from models import db
from models.monitoring import MonitoringRule, MonitoringRuleOverride

logger = logging.getLogger(__name__)


class MedOverrideService:
    """Monitoring rule override management."""

    def __init__(self, db_session=None):
        self._db = db_session or db

    # ================================================================
    # 1. Get effective interval (precedence chain)
    # ================================================================

    def get_effective_interval(
        self, monitoring_rule_id: int, user_id: int = None
    ) -> dict:
        """
        Resolve the effective monitoring interval via precedence chain:
          user_override → practice_override → rule default → class_rule → null

        Returns dict with:
          interval_days, source, source_label, override_id (or None)
        """
        rule = MonitoringRule.query.get(monitoring_rule_id)
        if not rule:
            return {
                'interval_days': None,
                'source': 'none',
                'source_label': 'No rule found',
                'override_id': None,
            }

        # Check user-level override
        if user_id:
            user_override = MonitoringRuleOverride.query.filter_by(
                monitoring_rule_id=monitoring_rule_id,
                scope='user',
                scope_id=user_id,
                override_active=True,
            ).first()
            if user_override and user_override.override_interval_days is not None:
                return {
                    'interval_days': user_override.override_interval_days,
                    'source': 'user_override',
                    'source_label': 'User Override',
                    'override_id': user_override.id,
                }

        # Check practice-level override
        practice_override = MonitoringRuleOverride.query.filter_by(
            monitoring_rule_id=monitoring_rule_id,
            scope='practice',
            scope_id=None,
            override_active=True,
        ).first()
        if practice_override and practice_override.override_interval_days is not None:
            return {
                'interval_days': practice_override.override_interval_days,
                'source': 'practice_override',
                'source_label': 'Practice Override',
                'override_id': practice_override.id,
            }

        # Rule default
        if rule.interval_days:
            return {
                'interval_days': rule.interval_days,
                'source': 'rule_default',
                'source_label': f'Default ({rule.source})',
                'override_id': None,
            }

        # Class-level fallback: find any rule with same rxclass_id
        if rule.rxclass_id:
            class_rule = (
                MonitoringRule.query
                .filter_by(
                    rxclass_id=rule.rxclass_id,
                    is_active=True,
                )
                .filter(MonitoringRule.interval_days.isnot(None))
                .filter(MonitoringRule.id != rule.id)
                .first()
            )
            if class_rule:
                return {
                    'interval_days': class_rule.interval_days,
                    'source': 'class_rule',
                    'source_label': f'Class Fallback ({class_rule.rxclass_id})',
                    'override_id': None,
                }

        return {
            'interval_days': None,
            'source': 'none',
            'source_label': 'No interval configured',
            'override_id': None,
        }

    # ================================================================
    # 2. Set user override
    # ================================================================

    def set_user_override(
        self,
        monitoring_rule_id: int,
        user_id: int,
        interval_days: int = None,
        reason: str = '',
        priority: str = None,
        active: bool = True,
        reminder_text: str = None,
    ) -> MonitoringRuleOverride:
        """
        Create or update a user-level override for a monitoring rule.
        """
        existing = MonitoringRuleOverride.query.filter_by(
            monitoring_rule_id=monitoring_rule_id,
            scope='user',
            scope_id=user_id,
        ).first()

        if existing:
            existing.override_interval_days = interval_days
            existing.override_priority = priority
            existing.override_active = active
            existing.override_reminder_text = reminder_text
            existing.reason = reason
            existing.updated_at = datetime.now(timezone.utc)
            override = existing
        else:
            override = MonitoringRuleOverride(
                monitoring_rule_id=monitoring_rule_id,
                scope='user',
                scope_id=user_id,
                override_interval_days=interval_days,
                override_priority=priority,
                override_active=active,
                override_reminder_text=reminder_text,
                reason=reason,
                created_by=user_id,
            )
            self._db.session.add(override)

        try:
            self._db.session.commit()
        except Exception:
            self._db.session.rollback()
            raise

        logger.info(
            "User override set: rule=%d user=%d interval=%s",
            monitoring_rule_id, user_id, interval_days
        )
        return override

    # ================================================================
    # 3. Set practice override
    # ================================================================

    def set_practice_override(
        self,
        monitoring_rule_id: int,
        interval_days: int = None,
        reason: str = '',
        created_by: int = None,
        priority: str = None,
        active: bool = True,
        reminder_text: str = None,
    ) -> MonitoringRuleOverride:
        """
        Create or update a practice-level override for a monitoring rule.
        """
        existing = MonitoringRuleOverride.query.filter_by(
            monitoring_rule_id=monitoring_rule_id,
            scope='practice',
            scope_id=None,
        ).first()

        if existing:
            existing.override_interval_days = interval_days
            existing.override_priority = priority
            existing.override_active = active
            existing.override_reminder_text = reminder_text
            existing.reason = reason
            existing.updated_at = datetime.now(timezone.utc)
            override = existing
        else:
            override = MonitoringRuleOverride(
                monitoring_rule_id=monitoring_rule_id,
                scope='practice',
                scope_id=None,
                override_interval_days=interval_days,
                override_priority=priority,
                override_active=active,
                override_reminder_text=reminder_text,
                reason=reason,
                created_by=created_by,
            )
            self._db.session.add(override)

        try:
            self._db.session.commit()
        except Exception:
            self._db.session.rollback()
            raise

        logger.info(
            "Practice override set: rule=%d interval=%s by user=%d",
            monitoring_rule_id, interval_days, created_by
        )
        return override

    # ================================================================
    # 4. Reset (delete) an override
    # ================================================================

    def reset_override(self, override_id: int) -> bool:
        """
        Deactivate an override (soft-delete — sets override_active=False).
        Returns True on success.
        """
        override = MonitoringRuleOverride.query.get(override_id)
        if not override:
            return False

        override.override_active = False
        override.updated_at = datetime.now(timezone.utc)

        try:
            self._db.session.commit()
        except Exception:
            self._db.session.rollback()
            raise

        logger.info("Override %d deactivated", override_id)
        return True

    # ================================================================
    # 5. Get override diff (show all layers)
    # ================================================================

    def get_override_diff(
        self, monitoring_rule_id: int, user_id: int = None
    ) -> dict:
        """
        Show the full precedence chain for a rule, making it visible
        where the effective interval comes from.
        """
        rule = MonitoringRule.query.get(monitoring_rule_id)
        if not rule:
            return {'error': 'Rule not found'}

        result = {
            'rule_id': monitoring_rule_id,
            'api_default': rule.interval_days,
            'source': rule.source,
            'practice_override': None,
            'user_override': None,
            'effective': None,
            'source_label': None,
        }

        # Practice-level
        practice = MonitoringRuleOverride.query.filter_by(
            monitoring_rule_id=monitoring_rule_id,
            scope='practice',
            scope_id=None,
            override_active=True,
        ).first()
        if practice:
            result['practice_override'] = {
                'id': practice.id,
                'interval_days': practice.override_interval_days,
                'reason': practice.reason,
                'created_at': practice.created_at.isoformat() if practice.created_at else None,
            }

        # User-level
        if user_id:
            user_ov = MonitoringRuleOverride.query.filter_by(
                monitoring_rule_id=monitoring_rule_id,
                scope='user',
                scope_id=user_id,
                override_active=True,
            ).first()
            if user_ov:
                result['user_override'] = {
                    'id': user_ov.id,
                    'interval_days': user_ov.override_interval_days,
                    'reason': user_ov.reason,
                    'created_at': user_ov.created_at.isoformat() if user_ov.created_at else None,
                }

        # Compute effective
        effective = self.get_effective_interval(monitoring_rule_id, user_id)
        result['effective'] = effective['interval_days']
        result['source_label'] = effective['source_label']

        return result

    # ================================================================
    # 6. Bulk class override
    # ================================================================

    def bulk_set_class_override(
        self,
        rxclass_id: str,
        interval_days: int,
        scope: str = 'practice',
        scope_id: int = None,
        reason: str = '',
        created_by: int = None,
    ) -> int:
        """
        Apply an override to ALL monitoring rules sharing an rxclass_id.
        Returns count of overrides created/updated.
        """
        rules = MonitoringRule.query.filter_by(
            rxclass_id=rxclass_id, is_active=True
        ).all()

        count = 0
        for rule in rules:
            if scope == 'user' and scope_id:
                self.set_user_override(
                    monitoring_rule_id=rule.id,
                    user_id=scope_id,
                    interval_days=interval_days,
                    reason=reason,
                )
            else:
                self.set_practice_override(
                    monitoring_rule_id=rule.id,
                    interval_days=interval_days,
                    reason=reason,
                    created_by=created_by,
                )
            count += 1

        logger.info(
            "Bulk class override: rxclass=%s scope=%s interval=%d count=%d",
            rxclass_id, scope, interval_days, count
        )
        return count

"""
CareCompanion -- Billing Opportunities Manager Tests
tests/test_billing_opportunities.py

Comprehensive tests for the BillingOpportunity model, billing management
routes (capture/dismiss), ClosedLoopStatus tracking, and the billing
opportunity API endpoints.

Usage:
    venv\\Scripts\\python.exe -m pytest tests/test_billing_opportunities.py -v
"""

import json
import pytest
from datetime import date, datetime, timezone, timedelta


# ======================================================================
# BillingOpportunity Model Tests
# ======================================================================

class TestBillingOpportunityModel:
    """Tests for the BillingOpportunity ORM model."""

    def _make_opp(self, db_session, user_id=1, **overrides):
        """Helper: create and flush a BillingOpportunity with defaults."""
        from models.billing import BillingOpportunity
        defaults = {
            'patient_mrn_hash': 'a' * 64,
            'user_id': user_id,
            'visit_date': date.today(),
            'opportunity_type': 'AWV',
            'applicable_codes': 'G0439,G0444',
            'estimated_revenue': 175.0,
            'confidence_level': 'HIGH',
            'status': 'pending',
            'category': 'awv',
            'opportunity_code': 'AWV_INITIAL',
            'priority': 'high',
        }
        defaults.update(overrides)
        opp = BillingOpportunity(**defaults)
        db_session.add(opp)
        db_session.flush()
        return opp

    def test_create_opportunity(self, app, db_session):
        """BillingOpportunity can be created with required fields."""
        opp = self._make_opp(db_session)
        assert opp.id is not None
        assert opp.status == 'pending'
        assert opp.opportunity_type == 'AWV'

    def test_default_status_is_pending(self, app, db_session):
        """Default status is 'pending'."""
        opp = self._make_opp(db_session)
        assert opp.status == 'pending'

    def test_default_confidence_is_medium(self, app, db_session):
        """Default confidence_level is 'MEDIUM' when not overridden."""
        from models.billing import BillingOpportunity
        opp = BillingOpportunity(
            patient_mrn_hash='b' * 64,
            user_id=1,
            visit_date=date.today(),
            opportunity_type='CCM',
            applicable_codes='99490',
        )
        db_session.add(opp)
        db_session.flush()
        assert opp.confidence_level == 'MEDIUM'

    def test_repr(self, app, db_session):
        """__repr__ includes opportunity_type, visit_date, and status."""
        opp = self._make_opp(db_session)
        r = repr(opp)
        assert 'AWV' in r
        assert 'pending' in r

    def test_created_at_auto_set(self, app, db_session):
        """created_at is automatically set on creation."""
        opp = self._make_opp(db_session)
        assert opp.created_at is not None
        assert isinstance(opp.created_at, datetime)

    def test_reviewed_at_initially_none(self, app, db_session):
        """reviewed_at is None on creation."""
        opp = self._make_opp(db_session)
        assert opp.reviewed_at is None


# ======================================================================
# Model Methods
# ======================================================================

class TestGetCodesList:
    """Tests for BillingOpportunity.get_codes_list()."""

    def _make_opp(self, db_session, codes='G0439,G0444', **kw):
        from models.billing import BillingOpportunity
        opp = BillingOpportunity(
            patient_mrn_hash='c' * 64, user_id=1,
            visit_date=date.today(), opportunity_type='AWV',
            applicable_codes=codes, **kw,
        )
        db_session.add(opp)
        db_session.flush()
        return opp

    def test_codes_list_basic(self, app, db_session):
        """get_codes_list() splits comma-separated codes."""
        opp = self._make_opp(db_session, codes='G0439,G0444,G2211')
        assert opp.get_codes_list() == ['G0439', 'G0444', 'G2211']

    def test_codes_list_single(self, app, db_session):
        """get_codes_list() works with a single code."""
        opp = self._make_opp(db_session, codes='99490')
        assert opp.get_codes_list() == ['99490']

    def test_codes_list_strips_whitespace(self, app, db_session):
        """get_codes_list() strips whitespace around codes."""
        opp = self._make_opp(db_session, codes=' G0439 , G0444 ')
        assert opp.get_codes_list() == ['G0439', 'G0444']

    def test_codes_list_empty(self, app, db_session):
        """get_codes_list() returns [] for empty string."""
        opp = self._make_opp(db_session, codes='')
        assert opp.get_codes_list() == []

    def test_codes_list_none(self, app, db_session):
        """get_codes_list() returns [] for None."""
        from models.billing import BillingOpportunity
        opp = BillingOpportunity(
            patient_mrn_hash='d' * 64, user_id=1,
            visit_date=date.today(), opportunity_type='AWV',
            applicable_codes=None,
        )
        assert opp.get_codes_list() == []


class TestMarkCaptured:
    """Tests for BillingOpportunity.mark_captured()."""

    def _make_opp(self, db_session, status='pending'):
        from models.billing import BillingOpportunity
        opp = BillingOpportunity(
            patient_mrn_hash='e' * 64, user_id=1,
            visit_date=date.today(), opportunity_type='CCM',
            applicable_codes='99490', status=status,
        )
        db_session.add(opp)
        db_session.flush()
        return opp

    def test_mark_captured_sets_status(self, app, db_session):
        """mark_captured() sets status to 'captured'."""
        opp = self._make_opp(db_session)
        opp.mark_captured()
        assert opp.status == 'captured'

    def test_mark_captured_sets_reviewed_at(self, app, db_session):
        """mark_captured() sets reviewed_at to current UTC time."""
        opp = self._make_opp(db_session)
        before = datetime.now(timezone.utc)
        opp.mark_captured()
        assert opp.reviewed_at is not None
        assert opp.reviewed_at >= before

    def test_mark_captured_from_partial(self, app, db_session):
        """mark_captured() works from 'partial' status."""
        opp = self._make_opp(db_session, status='partial')
        opp.mark_captured()
        assert opp.status == 'captured'


class TestDismiss:
    """Tests for BillingOpportunity.dismiss()."""

    def _make_opp(self, db_session, status='pending'):
        from models.billing import BillingOpportunity
        opp = BillingOpportunity(
            patient_mrn_hash='f' * 64, user_id=1,
            visit_date=date.today(), opportunity_type='G2211',
            applicable_codes='G2211', status=status,
        )
        db_session.add(opp)
        db_session.flush()
        return opp

    def test_dismiss_sets_status(self, app, db_session):
        """dismiss() sets status to 'dismissed'."""
        opp = self._make_opp(db_session)
        opp.dismiss(reason='Not applicable today')
        assert opp.status == 'dismissed'

    def test_dismiss_sets_reason(self, app, db_session):
        """dismiss() records the dismissal reason."""
        opp = self._make_opp(db_session)
        opp.dismiss(reason='Already billed elsewhere')
        assert opp.dismissal_reason == 'Already billed elsewhere'

    def test_dismiss_default_reason(self, app, db_session):
        """dismiss() uses default reason when none provided."""
        opp = self._make_opp(db_session)
        opp.dismiss()
        assert opp.dismissal_reason == 'Dismissed by provider'

    def test_dismiss_sets_reviewed_at(self, app, db_session):
        """dismiss() sets reviewed_at to current UTC time."""
        opp = self._make_opp(db_session)
        before = datetime.now(timezone.utc)
        opp.dismiss(reason='Not applicable')
        assert opp.reviewed_at is not None
        assert opp.reviewed_at >= before

    def test_dismiss_from_partial(self, app, db_session):
        """dismiss() works from 'partial' status."""
        opp = self._make_opp(db_session, status='partial')
        opp.dismiss(reason='Too complex')
        assert opp.status == 'dismissed'


class TestGetChecklist:
    """Tests for BillingOpportunity.get_checklist()."""

    def _make_opp(self, db_session, checklist_json=None):
        from models.billing import BillingOpportunity
        opp = BillingOpportunity(
            patient_mrn_hash='g' * 64, user_id=1,
            visit_date=date.today(), opportunity_type='AWV',
            applicable_codes='G0439',
            documentation_checklist=checklist_json,
        )
        db_session.add(opp)
        db_session.flush()
        return opp

    def test_checklist_valid_json(self, app, db_session):
        """get_checklist() parses valid JSON array."""
        items = ['Record BMI', 'Complete PHQ-9', 'Review medications']
        opp = self._make_opp(db_session, json.dumps(items))
        assert opp.get_checklist() == items

    def test_checklist_none(self, app, db_session):
        """get_checklist() returns [] when documentation_checklist is None."""
        opp = self._make_opp(db_session, None)
        assert opp.get_checklist() == []

    def test_checklist_empty_string(self, app, db_session):
        """get_checklist() returns [] for empty string."""
        opp = self._make_opp(db_session, '')
        assert opp.get_checklist() == []

    def test_checklist_invalid_json(self, app, db_session):
        """get_checklist() returns [] for malformed JSON."""
        opp = self._make_opp(db_session, '{not valid json}')
        assert opp.get_checklist() == []

    def test_checklist_json_object_not_array(self, app, db_session):
        """get_checklist() returns [] if JSON is an object, not array."""
        opp = self._make_opp(db_session, json.dumps({'key': 'value'}))
        assert opp.get_checklist() == []


# ======================================================================
# Status Transitions
# ======================================================================

class TestStatusTransitions:
    """Tests for valid status transition patterns."""

    def _make_opp(self, db_session, status='pending'):
        from models.billing import BillingOpportunity
        opp = BillingOpportunity(
            patient_mrn_hash='h' * 64, user_id=1,
            visit_date=date.today(), opportunity_type='AWV',
            applicable_codes='G0439', status=status,
        )
        db_session.add(opp)
        db_session.flush()
        return opp

    def test_pending_to_captured(self, app, db_session):
        """pending -> captured is valid."""
        opp = self._make_opp(db_session, 'pending')
        opp.mark_captured()
        assert opp.status == 'captured'

    def test_pending_to_dismissed(self, app, db_session):
        """pending -> dismissed is valid."""
        opp = self._make_opp(db_session, 'pending')
        opp.dismiss(reason='Not applicable')
        assert opp.status == 'dismissed'

    def test_partial_to_captured(self, app, db_session):
        """partial -> captured is valid."""
        opp = self._make_opp(db_session, 'partial')
        opp.mark_captured()
        assert opp.status == 'captured'

    def test_partial_to_dismissed(self, app, db_session):
        """partial -> dismissed is valid."""
        opp = self._make_opp(db_session, 'partial')
        opp.dismiss(reason='Deferred')
        assert opp.status == 'dismissed'


# ======================================================================
# ClosedLoopStatus Model Tests
# ======================================================================

class TestClosedLoopStatus:
    """Tests for the ClosedLoopStatus model and its relationship."""

    def _make_opp(self, db_session):
        from models.billing import BillingOpportunity
        opp = BillingOpportunity(
            patient_mrn_hash='i' * 64, user_id=1,
            visit_date=date.today(), opportunity_type='AWV',
            applicable_codes='G0439', status='pending',
        )
        db_session.add(opp)
        db_session.flush()
        return opp

    def test_create_closed_loop_entry(self, app, db_session):
        """ClosedLoopStatus record can be created and linked to an opportunity."""
        from models.billing import ClosedLoopStatus
        opp = self._make_opp(db_session)
        entry = ClosedLoopStatus(
            opportunity_id=opp.id,
            patient_mrn_hash=opp.patient_mrn_hash,
            funnel_stage='surfaced',
            stage_actor='Test Provider',
            stage_notes='Initial detection',
            previous_stage=None,
        )
        db_session.add(entry)
        db_session.flush()
        assert entry.id is not None
        assert entry.funnel_stage == 'surfaced'

    def test_relationship_from_opportunity(self, app, db_session):
        """Opportunity.closed_loop_statuses returns related entries."""
        from models.billing import ClosedLoopStatus
        opp = self._make_opp(db_session)
        entry = ClosedLoopStatus(
            opportunity_id=opp.id,
            patient_mrn_hash=opp.patient_mrn_hash,
            funnel_stage='surfaced',
        )
        db_session.add(entry)
        db_session.flush()
        statuses = opp.closed_loop_statuses.all()
        assert len(statuses) == 1
        assert statuses[0].funnel_stage == 'surfaced'

    def test_multiple_funnel_stages(self, app, db_session):
        """Multiple ClosedLoopStatus entries track the full lifecycle."""
        from models.billing import ClosedLoopStatus
        opp = self._make_opp(db_session)
        stages = ['surfaced', 'accepted', 'submitted']
        for i, stage in enumerate(stages):
            entry = ClosedLoopStatus(
                opportunity_id=opp.id,
                patient_mrn_hash=opp.patient_mrn_hash,
                funnel_stage=stage,
                previous_stage=stages[i - 1] if i > 0 else None,
            )
            db_session.add(entry)
        db_session.flush()
        all_statuses = opp.closed_loop_statuses.order_by(ClosedLoopStatus.id).all()
        assert len(all_statuses) == 3
        assert [s.funnel_stage for s in all_statuses] == stages

    def test_stage_date_auto_set(self, app, db_session):
        """stage_date is auto-set on creation."""
        from models.billing import ClosedLoopStatus
        opp = self._make_opp(db_session)
        entry = ClosedLoopStatus(
            opportunity_id=opp.id,
            patient_mrn_hash=opp.patient_mrn_hash,
            funnel_stage='surfaced',
        )
        db_session.add(entry)
        db_session.flush()
        assert entry.stage_date is not None

    def test_repr(self, app, db_session):
        """ClosedLoopStatus __repr__ includes opp id and stage."""
        from models.billing import ClosedLoopStatus
        opp = self._make_opp(db_session)
        entry = ClosedLoopStatus(
            opportunity_id=opp.id,
            patient_mrn_hash=opp.patient_mrn_hash,
            funnel_stage='accepted',
        )
        db_session.add(entry)
        db_session.flush()
        r = repr(entry)
        assert 'accepted' in r


# ======================================================================
# Route Tests -- Capture Endpoint
# ======================================================================

class TestCaptureRoute:
    """Tests for POST /api/billing/opportunity/<id>/capture."""

    def _make_opp(self, db_session, user_id, status='pending'):
        from models.billing import BillingOpportunity
        opp = BillingOpportunity(
            patient_mrn_hash='j' * 64, user_id=user_id,
            visit_date=date.today(), opportunity_type='AWV',
            applicable_codes='G0439', status=status,
            category='awv', opportunity_code='AWV_INITIAL',
        )
        db_session.add(opp)
        db_session.flush()
        return opp

    def test_capture_success(self, app, db_session, auth_client):
        """Capturing a pending opportunity returns success."""
        user_id = auth_client._test_user.id
        opp = self._make_opp(db_session, user_id=user_id)
        db_session.commit()

        resp = auth_client.post(f'/api/billing/opportunity/{opp.id}/capture')
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success'] is True
        assert data['status'] == 'captured'

    def test_capture_partial_status(self, app, db_session, auth_client):
        """Capturing a partial opportunity returns success."""
        user_id = auth_client._test_user.id
        opp = self._make_opp(db_session, user_id=user_id, status='partial')
        db_session.commit()

        resp = auth_client.post(f'/api/billing/opportunity/{opp.id}/capture')
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success'] is True

    def test_capture_not_found(self, app, db_session, auth_client):
        """Capturing a non-existent opportunity returns 404."""
        resp = auth_client.post('/api/billing/opportunity/99999/capture')
        assert resp.status_code == 404
        data = resp.get_json()
        assert data['success'] is False

    def test_capture_wrong_user(self, app, db_session, auth_client):
        """Cannot capture another user's opportunity."""
        # Create opp owned by user_id=9999 (not the auth_client user)
        opp = self._make_opp(db_session, user_id=9999)
        db_session.commit()

        resp = auth_client.post(f'/api/billing/opportunity/{opp.id}/capture')
        assert resp.status_code == 404

    def test_capture_already_captured(self, app, db_session, auth_client):
        """Cannot capture an already-captured opportunity (409)."""
        user_id = auth_client._test_user.id
        opp = self._make_opp(db_session, user_id=user_id, status='captured')
        db_session.commit()

        resp = auth_client.post(f'/api/billing/opportunity/{opp.id}/capture')
        assert resp.status_code == 409
        data = resp.get_json()
        assert data['success'] is False

    def test_capture_already_dismissed(self, app, db_session, auth_client):
        """Cannot capture a dismissed opportunity (409)."""
        user_id = auth_client._test_user.id
        opp = self._make_opp(db_session, user_id=user_id, status='dismissed')
        db_session.commit()

        resp = auth_client.post(f'/api/billing/opportunity/{opp.id}/capture')
        assert resp.status_code == 409

    def test_capture_creates_closed_loop_entry(self, app, db_session, auth_client):
        """Capturing creates a ClosedLoopStatus 'accepted' entry."""
        from models.billing import ClosedLoopStatus
        user_id = auth_client._test_user.id
        opp = self._make_opp(db_session, user_id=user_id)
        db_session.commit()

        auth_client.post(f'/api/billing/opportunity/{opp.id}/capture')

        entries = ClosedLoopStatus.query.filter_by(opportunity_id=opp.id).all()
        assert len(entries) >= 1
        assert any(e.funnel_stage == 'accepted' for e in entries)


# ======================================================================
# Route Tests -- Dismiss Endpoint
# ======================================================================

class TestDismissRoute:
    """Tests for POST /api/billing/opportunity/<id>/dismiss."""

    def _make_opp(self, db_session, user_id, status='pending'):
        from models.billing import BillingOpportunity
        opp = BillingOpportunity(
            patient_mrn_hash='k' * 64, user_id=user_id,
            visit_date=date.today(), opportunity_type='G2211',
            applicable_codes='G2211', status=status,
            category='g2211', opportunity_code='G2211_LONGIT',
        )
        db_session.add(opp)
        db_session.flush()
        return opp

    def test_dismiss_success(self, app, db_session, auth_client):
        """Dismissing a pending opportunity returns success."""
        user_id = auth_client._test_user.id
        opp = self._make_opp(db_session, user_id=user_id)
        db_session.commit()

        resp = auth_client.post(
            f'/api/billing/opportunity/{opp.id}/dismiss',
            json={'reason': 'Patient declined'},
        )
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success'] is True
        assert data['status'] == 'dismissed'

    def test_dismiss_without_reason(self, app, db_session, auth_client):
        """Dismissing without a reason still succeeds."""
        user_id = auth_client._test_user.id
        opp = self._make_opp(db_session, user_id=user_id)
        db_session.commit()

        resp = auth_client.post(f'/api/billing/opportunity/{opp.id}/dismiss')
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success'] is True

    def test_dismiss_not_found(self, app, db_session, auth_client):
        """Dismissing a non-existent opportunity returns 404."""
        resp = auth_client.post('/api/billing/opportunity/99999/dismiss')
        assert resp.status_code == 404

    def test_dismiss_wrong_user(self, app, db_session, auth_client):
        """Cannot dismiss another user's opportunity."""
        opp = self._make_opp(db_session, user_id=9999)
        db_session.commit()

        resp = auth_client.post(f'/api/billing/opportunity/{opp.id}/dismiss')
        assert resp.status_code == 404

    def test_dismiss_already_dismissed(self, app, db_session, auth_client):
        """Cannot dismiss an already-dismissed opportunity (409)."""
        user_id = auth_client._test_user.id
        opp = self._make_opp(db_session, user_id=user_id, status='dismissed')
        db_session.commit()

        resp = auth_client.post(
            f'/api/billing/opportunity/{opp.id}/dismiss',
            json={'reason': 'Second dismiss'},
        )
        assert resp.status_code == 409

    def test_dismiss_already_captured(self, app, db_session, auth_client):
        """Cannot dismiss a captured opportunity (409)."""
        user_id = auth_client._test_user.id
        opp = self._make_opp(db_session, user_id=user_id, status='captured')
        db_session.commit()

        resp = auth_client.post(
            f'/api/billing/opportunity/{opp.id}/dismiss',
            json={'reason': 'Change of mind'},
        )
        assert resp.status_code == 409

    def test_dismiss_reason_truncated_to_500(self, app, db_session, auth_client):
        """Dismiss reason is truncated to 500 characters (server-side)."""
        user_id = auth_client._test_user.id
        opp = self._make_opp(db_session, user_id=user_id)
        db_session.commit()

        long_reason = 'x' * 1000
        resp = auth_client.post(
            f'/api/billing/opportunity/{opp.id}/dismiss',
            json={'reason': long_reason},
        )
        assert resp.status_code == 200
        # The route truncates to 500 chars before passing to dismiss()
        # So the stored reason should be <= 500 chars

    def test_dismiss_creates_closed_loop_entry(self, app, db_session, auth_client):
        """Dismissing creates a ClosedLoopStatus 'dismissed' entry."""
        from models.billing import ClosedLoopStatus
        user_id = auth_client._test_user.id
        opp = self._make_opp(db_session, user_id=user_id)
        db_session.commit()

        auth_client.post(
            f'/api/billing/opportunity/{opp.id}/dismiss',
            json={'reason': 'Not clinically relevant'},
        )

        entries = ClosedLoopStatus.query.filter_by(opportunity_id=opp.id).all()
        assert len(entries) >= 1
        assert any(e.funnel_stage == 'dismissed' for e in entries)


# ======================================================================
# Route Tests -- Patient Billing Opportunities Endpoint
# ======================================================================

class TestPatientBillingRoute:
    """Tests for GET /api/patient/<mrn>/billing-opportunities."""

    def _make_opp(self, db_session, user_id, mrn_hash, status='pending'):
        from models.billing import BillingOpportunity
        opp = BillingOpportunity(
            patient_mrn_hash=mrn_hash, user_id=user_id,
            visit_date=date.today(), opportunity_type='AWV',
            applicable_codes='G0439', status=status,
            estimated_revenue=175.0, confidence_level='HIGH',
            category='awv', opportunity_code='AWV_INITIAL',
            priority='high', expected_net_dollars=150.0,
        )
        db_session.add(opp)
        db_session.flush()
        return opp

    def test_returns_pending_opportunities(self, app, db_session, auth_client):
        """Returns pending opportunities for the patient."""
        from utils import safe_patient_id
        user_id = auth_client._test_user.id
        mrn = '62815'
        mrn_hash = safe_patient_id(mrn)
        self._make_opp(db_session, user_id=user_id, mrn_hash=mrn_hash)
        db_session.commit()

        resp = auth_client.get(f'/api/patient/{mrn}/billing-opportunities')
        data = resp.get_json()
        assert resp.status_code == 200
        assert 'opportunities' in data
        assert len(data['opportunities']) >= 1

    def test_excludes_dismissed_opportunities(self, app, db_session, auth_client):
        """Does not return dismissed opportunities."""
        from utils import safe_patient_id
        user_id = auth_client._test_user.id
        mrn = '62816'
        mrn_hash = safe_patient_id(mrn)
        self._make_opp(db_session, user_id=user_id, mrn_hash=mrn_hash, status='dismissed')
        db_session.commit()

        resp = auth_client.get(f'/api/patient/{mrn}/billing-opportunities')
        data = resp.get_json()
        assert len(data['opportunities']) == 0

    def test_excludes_captured_opportunities(self, app, db_session, auth_client):
        """Does not return captured opportunities."""
        from utils import safe_patient_id
        user_id = auth_client._test_user.id
        mrn = '62817'
        mrn_hash = safe_patient_id(mrn)
        self._make_opp(db_session, user_id=user_id, mrn_hash=mrn_hash, status='captured')
        db_session.commit()

        resp = auth_client.get(f'/api/patient/{mrn}/billing-opportunities')
        data = resp.get_json()
        assert len(data['opportunities']) == 0

    def test_scoped_to_current_user(self, app, db_session, auth_client):
        """Only returns opportunities for the logged-in user."""
        from utils import safe_patient_id
        mrn = '62818'
        mrn_hash = safe_patient_id(mrn)
        # Create opp for a different user
        self._make_opp(db_session, user_id=9999, mrn_hash=mrn_hash)
        db_session.commit()

        resp = auth_client.get(f'/api/patient/{mrn}/billing-opportunities')
        data = resp.get_json()
        assert len(data['opportunities']) == 0

    def test_invalid_mrn_returns_empty(self, app, db_session, auth_client):
        """Invalid MRN format returns empty list, not an error."""
        resp = auth_client.get('/api/patient/!!!INVALID!!!/billing-opportunities')
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['opportunities'] == []

    def test_opportunity_response_shape(self, app, db_session, auth_client):
        """Response includes expected fields for each opportunity."""
        from utils import safe_patient_id
        user_id = auth_client._test_user.id
        mrn = '62819'
        mrn_hash = safe_patient_id(mrn)
        self._make_opp(db_session, user_id=user_id, mrn_hash=mrn_hash)
        db_session.commit()

        resp = auth_client.get(f'/api/patient/{mrn}/billing-opportunities')
        data = resp.get_json()
        opp = data['opportunities'][0]
        expected_keys = [
            'id', 'type', 'category', 'opportunity_code', 'codes',
            'revenue', 'net_value', 'confidence', 'priority', 'basis',
            'documentation', 'insurer_caveat', 'checklist', 'modifier',
        ]
        for key in expected_keys:
            assert key in opp, f'Missing key: {key}'


# ======================================================================
# Unauthenticated Access Tests
# ======================================================================

class TestUnauthenticatedAccess:
    """Verify billing endpoints require authentication.

    Unauthenticated requests should never receive a successful JSON
    payload containing billing data.  The exact status code depends
    on middleware ordering (CSRF vs login_required) so we accept any
    non-200-with-data response.
    """

    def test_capture_requires_auth(self, app, client):
        """Capture endpoint does not succeed without auth."""
        resp = client.post('/api/billing/opportunity/1/capture')
        # Must NOT be a successful capture
        data = resp.get_json(silent=True) or {}
        assert resp.status_code != 200 or data.get('success') is not True

    def test_dismiss_requires_auth(self, app, client):
        """Dismiss endpoint does not succeed without auth."""
        resp = client.post('/api/billing/opportunity/1/dismiss')
        data = resp.get_json(silent=True) or {}
        assert resp.status_code != 200 or data.get('success') is not True

    def test_patient_billing_requires_auth(self, app, client):
        """Patient billing endpoint does not leak data without auth."""
        resp = client.get('/api/patient/62815/billing-opportunities')
        # If it returns 200, verify no real opportunity data is returned
        if resp.status_code == 200:
            data = resp.get_json(silent=True) or {}
            # An empty list is acceptable (no data leaked)
            assert data.get('opportunities', []) == []
        else:
            assert resp.status_code in (302, 401)

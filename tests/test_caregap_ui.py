"""
Phase 1 — Care Gap UI Tests (final_plan.md Phase 1)

10 tests covering the print handout route, print template contents,
Personalized/All toggle elements, and data-trigger-type attributes.

Usage:
    venv\\Scripts\\python.exe tests/test_caregap_ui.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _get_app():
    os.environ['FLASK_ENV'] = 'testing'
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


def _get_test_user(app):
    with app.app_context():
        from models.user import User
        user = User.query.filter_by(is_active_account=True).order_by(User.id.asc()).first()
        return user.id if user else 1


def _authed_client(app, user_id):
    c = app.test_client()
    with c.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
    return c


def _ensure_demo_gap(app, user_id, mrn='DEMO001'):
    """Ensure at least one CareGap row exists for the test MRN."""
    with app.app_context():
        from models import db
        from models.caregap import CareGap
        existing = CareGap.query.filter_by(user_id=user_id, mrn=mrn).first()
        if not existing:
            gap = CareGap(
                user_id=user_id,
                mrn=mrn,
                patient_name='Demo Patient',
                gap_type='colorectal_colonoscopy',
                gap_name='Colorectal Cancer Screening (Colonoscopy)',
                description='USPSTF recommends screening for colorectal cancer in adults age 45-75.',
                status='open',
                is_addressed=False,
                billing_code_suggested='G0105',
            )
            db.session.add(gap)
            db.session.commit()


def run_tests():
    passed = []
    failed = []

    app = _get_app()
    uid = _get_test_user(app)

    with app.app_context():
        _ensure_demo_gap(app, uid)
        c = _authed_client(app, uid)

        # ==================================================================
        # 1 — GET /caregap/DEMO001/print returns 200
        # ==================================================================
        print('[1/10] Print handout route...')
        try:
            r = c.get('/caregap/DEMO001/print')
            assert r.status_code == 200, f'Status {r.status_code}'
            passed.append('1: /caregap/DEMO001/print → 200')
        except Exception as e:
            failed.append(f'1: {e}')

        # ==================================================================
        # 2 — Print template contains @media print CSS block
        # ==================================================================
        print('[2/10] Print CSS...')
        try:
            r = c.get('/caregap/DEMO001/print')
            html = r.data.decode()
            assert '@media print' in html, 'Missing @media print CSS'
            passed.append('2: @media print CSS present')
        except Exception as e:
            failed.append(f'2: {e}')

        # ==================================================================
        # 3 — Print template does NOT contain navigation
        # ==================================================================
        print('[3/10] No nav chrome in print...')
        try:
            r = c.get('/caregap/DEMO001/print')
            html = r.data.decode()
            assert '<nav' not in html.lower(), 'Found <nav> in print template'
            assert 'sidebar' not in html.lower() or 'display: none' in html.lower() or 'display:none' in html.lower(), 'Sidebar reference without hide'
            passed.append('3: No navigation in print template')
        except Exception as e:
            failed.append(f'3: {e}')

        # ==================================================================
        # 4 — Print template has plain-English names (not ICD-10 codes)
        # ==================================================================
        print('[4/10] Plain-English gap names...')
        try:
            r = c.get('/caregap/DEMO001/print')
            html = r.data.decode()
            assert 'Health Screening Summary' in html, 'Missing title'
            # Should contain readable names, not raw codes
            assert 'Screening' in html or 'Vaccine' in html or 'screening' in html.lower(), \
                'No plain-English screening names found'
            passed.append('4: Plain-English gap names')
        except Exception as e:
            failed.append(f'4: {e}')

        # ==================================================================
        # 5 — Print template contains footer text
        # ==================================================================
        print('[5/10] Footer text...')
        try:
            r = c.get('/caregap/DEMO001/print')
            html = r.data.decode()
            assert 'Questions about these recommendations' in html, 'Missing footer text'
            passed.append('5: Footer text present')
        except Exception as e:
            failed.append(f'5: {e}')

        # ==================================================================
        # 6 — Print button link on per-patient page
        # ==================================================================
        print('[6/10] Print button on patient page...')
        try:
            r = c.get('/caregap/DEMO001')
            html = r.data.decode()
            assert '/print' in html, 'No /print link on patient page'
            assert 'Print' in html, 'No Print text on button'
            passed.append('6: Print button present on patient page')
        except Exception as e:
            failed.append(f'6: {e}')

        # ==================================================================
        # 7 — Toggle elements present on per-patient page
        # ==================================================================
        print('[7/10] Toggle elements...')
        try:
            r = c.get('/caregap/DEMO001')
            html = r.data.decode()
            assert 'Personalized' in html, 'Missing Personalized toggle button'
            assert 'All Applicable' in html, 'Missing All Applicable toggle button'
            assert 'viewToggle' in html or 'setViewMode' in html, 'Missing toggle JS'
            passed.append('7: Personalized/All toggle present')
        except Exception as e:
            failed.append(f'7: {e}')

        # ==================================================================
        # 8 — data-trigger-type attribute set on gap rows
        # ==================================================================
        print('[8/10] data-trigger-type attribute...')
        try:
            r = c.get('/caregap/DEMO001')
            html = r.data.decode()
            assert 'data-trigger-type' in html, 'Missing data-trigger-type attribute'
            passed.append('8: data-trigger-type attribute present')
        except Exception as e:
            failed.append(f'8: {e}')

        # ==================================================================
        # 9 — Demographic type gap present for age-eligible patient
        # ==================================================================
        print('[9/10] Demographic trigger type...')
        try:
            r = c.get('/caregap/DEMO001')
            html = r.data.decode()
            # Colonoscopy is age/sex only → demographic
            assert 'data-trigger-type="demographic"' in html, \
                'No demographic trigger type found'
            passed.append('9: Demographic trigger type present')
        except Exception as e:
            failed.append(f'9: {e}')

        # ==================================================================
        # 10 — Risk factor gap for patient with trigger condition
        # ==================================================================
        print('[10/10] Risk factor trigger type...')
        try:
            # Create a risk-factor gap (lung LDCT — requires heavy_smoker)
            from models import db
            from models.caregap import CareGap
            rf_gap = CareGap.query.filter_by(
                user_id=uid, mrn='DEMO001', gap_type='lung_ldct'
            ).first()
            if not rf_gap:
                rf_gap = CareGap(
                    user_id=uid,
                    mrn='DEMO001',
                    patient_name='Demo Patient',
                    gap_type='lung_ldct',
                    gap_name='Lung Cancer Screening (LDCT)',
                    description='Annual LDCT for patients with smoking history.',
                    status='open',
                    is_addressed=False,
                )
                db.session.add(rf_gap)
                db.session.commit()

            r = c.get('/caregap/DEMO001')
            html = r.data.decode()
            assert 'data-trigger-type="risk_factor"' in html, \
                'No risk_factor trigger type found'
            passed.append('10: Risk factor trigger type present')
        except Exception as e:
            failed.append(f'10: {e}')

    # ---- Summary --------------------------------------------------------
    print()
    print(f'Phase 1 Care Gap UI Tests: {len(passed)} passed, {len(failed)} failed')
    for p in passed:
        print(f'  ✓ {p}')
    for f in failed:
        print(f'  ✗ {f}')
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

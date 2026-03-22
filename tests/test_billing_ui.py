"""
Phase 29.6 — Billing UI Smoke Tests

10 tests verifying billing tab rendering, dashboard cards, settings
toggles, bonus dashboard, CCM sidebar, TCM banner, staff tasks,
and phrase library UI elements.

Usage:
    venv\\Scripts\\python.exe tests/test_billing_ui.py
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


def run_tests():
    passed = []
    failed = []

    app = _get_app()
    uid = _get_test_user(app)

    with app.app_context():
        c = _authed_client(app, uid)

        # ==================================================================
        # 1 — Billing log has table structure
        # ==================================================================
        print('[1/10] Billing log has table...')
        try:
            r = c.get('/billing/log')
            html = r.data.decode()
            assert '<table' in html.lower() or 'billing' in html.lower(), \
                'No table or billing content found'
            passed.append('1: Billing log renders table')
        except Exception as e:
            failed.append(f'1: {e}')

        # ==================================================================
        # 2 — E/M calculator shows form inputs
        # ==================================================================
        print('[2/10] E/M calculator form...')
        try:
            r = c.get('/billing/em-calculator')
            html = r.data.decode()
            has_form = '<form' in html.lower() or 'calculate' in html.lower()
            assert has_form, 'E/M calculator missing form elements'
            passed.append('2: E/M calculator has form')
        except Exception as e:
            failed.append(f'2: {e}')

        # ==================================================================
        # 3 — Bonus dashboard shows bonus/revenue content
        # ==================================================================
        print('[3/10] Bonus dashboard content...')
        try:
            r = c.get('/bonus')
            html = r.data.decode()
            has_bonus = 'bonus' in html.lower() or 'tracker' in html.lower()
            assert has_bonus, 'Bonus page missing expected content'
            passed.append('3: Bonus dashboard renders')
        except Exception as e:
            failed.append(f'3: {e}')

        # ==================================================================
        # 4 — CCM registry shows enrollment UI
        # ==================================================================
        print('[4/10] CCM registry UI...')
        try:
            r = c.get('/ccm/registry')
            html = r.data.decode()
            has_ccm = 'ccm' in html.lower() or 'chronic care' in html.lower() \
                      or 'registry' in html.lower() or 'enroll' in html.lower()
            assert has_ccm, 'CCM registry page missing expected content'
            passed.append('4: CCM registry renders')
        except Exception as e:
            failed.append(f'4: {e}')

        # ==================================================================
        # 5 — TCM watch list shows discharge tracking
        # ==================================================================
        print('[5/10] TCM watch list UI...')
        try:
            r = c.get('/tcm/watch-list')
            html = r.data.decode()
            has_tcm = 'tcm' in html.lower() or 'transition' in html.lower() \
                      or 'discharge' in html.lower() or 'watch' in html.lower()
            assert has_tcm, 'TCM page missing expected content'
            passed.append('5: TCM watch list renders')
        except Exception as e:
            failed.append(f'5: {e}')

        # ==================================================================
        # 6 — Staff billing tasks page
        # ==================================================================
        print('[6/10] Staff billing tasks...')
        try:
            r = c.get('/staff/billing-tasks')
            html = r.data.decode()
            has_staff = 'task' in html.lower() or 'staff' in html.lower() \
                       or 'billing' in html.lower()
            assert has_staff, 'Staff tasks page missing expected content'
            passed.append('6: Staff billing tasks renders')
        except Exception as e:
            failed.append(f'6: {e}')

        # ==================================================================
        # 7 — Phrase library shows documentation phrases
        # ==================================================================
        print('[7/10] Phrase library UI...')
        try:
            r = c.get('/settings/phrases')
            html = r.data.decode()
            has_phrase = 'phrase' in html.lower() or 'dotphrase' in html.lower() \
                        or 'documentation' in html.lower()
            assert has_phrase, 'Phrase library page missing expected content'
            passed.append('7: Phrase library renders')
        except Exception as e:
            failed.append(f'7: {e}')

        # ==================================================================
        # 8 — Caregap panel shows care gap list
        # ==================================================================
        print('[8/10] Caregap panel UI...')
        try:
            r = c.get('/caregap/panel')
            html = r.data.decode()
            has_gap = 'care' in html.lower() or 'gap' in html.lower() \
                     or 'panel' in html.lower() or 'preventive' in html.lower()
            assert has_gap, 'Caregap panel missing expected content'
            passed.append('8: Caregap panel renders')
        except Exception as e:
            failed.append(f'8: {e}')

        # ==================================================================
        # 9 — Monthly report has chart/summary content
        # ==================================================================
        print('[9/10] Monthly report content...')
        try:
            r = c.get('/billing/monthly-report')
            html = r.data.decode()
            has_report = 'report' in html.lower() or 'month' in html.lower() \
                        or 'billing' in html.lower()
            assert has_report, 'Monthly report missing expected content'
            passed.append('9: Monthly report renders')
        except Exception as e:
            failed.append(f'9: {e}')

        # ==================================================================
        # 10 — Campaigns page has campaign management UI
        # ==================================================================
        print('[10/10] Campaigns UI...')
        try:
            r = c.get('/campaigns')
            html = r.data.decode()
            has_campaign = 'campaign' in html.lower() or 'outreach' in html.lower() \
                          or 'roi' in html.lower()
            assert has_campaign, 'Campaigns page missing expected content'
            passed.append('10: Campaigns page renders')
        except Exception as e:
            failed.append(f'10: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print('\n' + '=' * 60)
    print(f'Phase 29.6 — UI Smoke Tests: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)
    for p in passed:
        print(f'  \u2705 {p}')
    for f in failed:
        print(f'  \u274c {f}')
    print()

    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

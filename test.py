"""
NP Companion — Verification Test Suite

Run this to check that all pages, database tables, and APIs are working.
Used by restart.bat to validate the server after restart.

Usage:
    venv\Scripts\python.exe test.py
    venv\Scripts\python.exe test.py --quick    (skip login-required pages)
"""

import os
import sys
import traceback
from app import create_app, bcrypt

def run_tests():
    """Run all verification tests. Returns (passed, failed, errors) lists."""
    app = create_app()
    app.config['TESTING'] = True

    passed = []
    failed = []
    errors = []

    # ------------------------------------------------------------------
    # 1. Database tables
    # ------------------------------------------------------------------
    print("=== NP Companion Verification ===\n")
    print("[1/4] Database tables...")
    with app.app_context():
        from models import db
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        expected = [
            'users', 'audit_log', 'time_logs', 'inbox_snapshots', 'inbox_items',
            'oncall_notes', 'order_sets', 'order_items', 'medication_entries',
            'lab_tracks', 'lab_results', 'care_gaps', 'ticklers', 'delayed_messages',
            'reformat_logs', 'agent_logs', 'agent_errors', 'schedules',
            'patient_vitals', 'patient_records', 'patient_medications',
            'patient_diagnoses', 'patient_allergies', 'patient_immunizations',
            'patient_note_drafts', 'handoff_links', 'care_gap_rules',
        ]
        missing = [t for t in expected if t not in tables]
        if missing:
            msg = f"Missing tables: {missing}"
            failed.append(msg)
            print(f"  FAIL  {msg}")
        else:
            msg = f"All {len(expected)} tables present"
            passed.append(msg)
            print(f"  PASS  {msg}")

    # ------------------------------------------------------------------
    # 2. User account check
    # ------------------------------------------------------------------
    test_user_id = None
    test_username = None

    print("\n[2/4] User account selection...")
    with app.app_context():
        from models.user import User
        requested_username = os.environ.get('NP_TEST_USERNAME', '').strip()

        if requested_username:
            user = User.query.filter_by(username=requested_username).first()
        else:
            user = (
                User.query
                .filter_by(is_active_account=True)
                .order_by(User.id.asc())
                .first()
            )

        if not user:
            if requested_username:
                msg = (
                    f'No user named "{requested_username}" found. '
                    'Set NP_TEST_USERNAME to an existing account or unset it.'
                )
            else:
                msg = 'No active user found — create/activate at least one account first.'
            failed.append(msg)
            print(f"  FAIL  {msg}")
            # Can't do authenticated tests without a user
            print(f"\nResults: {len(passed)} passed, {len(failed)} failed")
            return passed, failed, errors
        else:
            test_user_id = user.id
            test_username = user.username
            passed.append(f'Using test user {test_username}')
            print(
                f"  PASS  Using test user '{test_username}' "
                f"(role={user.role}, active={user.is_active_account})"
            )

    # ------------------------------------------------------------------
    # 3. Page render tests (authenticated)
    # ------------------------------------------------------------------
    print("\n[3/4] Page render tests...")
    pages = {
        'Dashboard':            '/dashboard',
        'Dashboard (yesterday)':'/dashboard?date=2026-03-15',
        'Settings - Account':   '/settings/account',
        'Setup Wizard':         '/setup',
        'Admin Hub':            '/admin',
        'Admin - Users':        '/admin/users',
        'Admin - Audit Log':    '/admin/audit-log',
        'Admin - Agent':        '/admin/agent',
        'Admin - NetPractice':  '/admin/netpractice',
        'Admin - NP Wizard':    '/admin/netpractice/wizard',
        'Admin - Sitemap':      '/admin/sitemap',
        'Admin - Config':       '/admin/config',
        'Admin - Tools':        '/admin/tools',
        'Admin - Gap Rules':   '/admin/caregap-rules',
        'Admin - Updates':     '/admin/updates',
        'API - Setup Status':   '/api/setup-status',
        'API - Agent Status':   '/api/agent-status',
        'API - Auth Status':    '/api/auth-status',
        'API - Notifications':  '/api/notifications',
        'API - Schedule':       '/api/schedule?date=2026-03-16',
        'Timer':                '/timer',
        'Inbox':                '/inbox',
        'On-Call':              '/oncall',
        'Orders':               '/orders',
        'Med Ref':              '/medref',
        'Lab Track':            '/labtrack',
        'Care Gaps':            '/caregap',
        'Metrics':              '/metrics',
        'Tools':                '/tools',
        'Patient Chart':        '/patient/99999',
        'Patient Roster':       '/patients',
        'On-Call New':          '/oncall/new',
    }

    with app.test_client() as client:
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user_id)

        for name, url in pages.items():
            try:
                r = client.get(url)
                if r.status_code == 200:
                    passed.append(f"{name} ({url})")
                    print(f"  PASS  {name} ({url})")
                else:
                    msg = f"{name} ({url}) -> {r.status_code}"
                    failed.append(msg)
                    print(f"  FAIL  {msg}")
            except Exception as e:
                msg = f"{name} ({url}) -> {e}"
                errors.append(msg)
                print(f"  ERROR {msg}")

    # ------------------------------------------------------------------
    # 4. Security checks
    # ------------------------------------------------------------------
    print("\n[4/4] Security checks...")
    with app.test_client() as client:
        # Settings notifications redirect (merged into /settings/account)
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user_id)
        r = client.get('/settings/notifications')
        if r.status_code == 302:
            passed.append("Settings notifications redirects to unified page")
            print("  PASS  /settings/notifications redirects (302)")
        else:
            failed.append(f"/settings/notifications returned {r.status_code}")
            print(f"  FAIL  /settings/notifications returned {r.status_code}")

    with app.test_client() as client:
        # 404 page
        r = client.get('/this-does-not-exist')
        if r.status_code == 404:
            passed.append("404 page works")
            print("  PASS  404 page returns 404")
        else:
            failed.append(f"404 page returned {r.status_code}")
            print(f"  FAIL  404 page returned {r.status_code}")

        # Login redirect for unauthenticated
        r = client.get('/dashboard')
        if r.status_code == 302:
            passed.append("Login redirect works")
            print("  PASS  Unauthenticated /dashboard redirects to login")
        else:
            failed.append(f"Login redirect returned {r.status_code}")
            print(f"  FAIL  Unauthenticated /dashboard returned {r.status_code}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    total = len(passed) + len(failed) + len(errors)
    print(f"\n{'='*50}")
    print(f"Results: {len(passed)} passed, {len(failed)} failed, {len(errors)} errors out of {total} checks")

    if failed:
        print(f"\nFailed checks:")
        for f in failed:
            print(f"  - {f}")
    if errors:
        print(f"\nErrors:")
        for e in errors:
            print(f"  - {e}")

    if not failed and not errors:
        print("\n*** ALL CHECKS PASSED ***")

    return passed, failed, errors


if __name__ == '__main__':
    try:
        passed, failed, errors = run_tests()
        if failed or errors:
            sys.exit(1)
        sys.exit(0)
    except Exception as e:
        print(f"\nFATAL ERROR running tests:\n{traceback.format_exc()}")
        sys.exit(2)

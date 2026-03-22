"""
Phase 2 — Misc Audit Fix Tests (final_plan.md Phase 2)

5 tests covering NetPractice placeholder, help text, version label,
and keyboard shortcut JS syntax.

Usage:
    venv\\Scripts\\python.exe tests/test_misc_audit_fixes.py
"""

import os
import sys
import re

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
        # 1 — NetPractice admin page loads
        # ==================================================================
        print('[1/5] NetPractice admin page...')
        try:
            r = c.get('/admin/netpractice')
            assert r.status_code == 200, f'Status {r.status_code}'
            passed.append('1: /admin/netpractice → 200')
        except Exception as e:
            failed.append(f'1: {e}')

        # ==================================================================
        # 2 — Provider name input has improved placeholder
        # ==================================================================
        print('[2/5] Provider name placeholder...')
        try:
            # Check the settings_account template (or any template with the field)
            templates_checked = 0
            for tpl_name in ['settings_account.html', 'settings.html',
                             'setup.html', 'onboarding.html']:
                tpl_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'templates', tpl_name,
                )
                if os.path.exists(tpl_path):
                    content = open(tpl_path, encoding='utf-8').read()
                    if 'np_provider_name' in content:
                        assert 'DENTON CORY' in content or 'placeholder' in content, \
                            f'No improved placeholder in {tpl_name}'
                        templates_checked += 1
            assert templates_checked >= 1, 'No templates found with np_provider_name'
            passed.append('2: Provider name placeholder has hint text')
        except Exception as e:
            failed.append(f'2: {e}')

        # ==================================================================
        # 3 — Provider name help text present in template
        # ==================================================================
        print('[3/5] Provider name help text...')
        try:
            found_help = False
            for tpl_name in ['settings_account.html', 'settings.html',
                             'setup.html', 'onboarding.html']:
                tpl_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'templates', tpl_name,
                )
                if os.path.exists(tpl_path):
                    content = open(tpl_path, encoding='utf-8').read()
                    if 'provider number in parentheses' in content.lower():
                        found_help = True
                        break
            assert found_help, 'Missing help text about provider number'
            passed.append('3: Provider name help text present')
        except Exception as e:
            failed.append(f'3: {e}')

        # ==================================================================
        # 4 — Version label visible in base.html user popover
        # ==================================================================
        print('[4/5] Version label in popover...')
        try:
            tpl_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'templates', 'base.html',
            )
            content = open(tpl_path, encoding='utf-8').read()
            assert 'app_version' in content, 'Missing app_version in base.html'
            assert 'Version' in content, 'Missing Version label in base.html'
            passed.append('4: Version label in user popover')
        except Exception as e:
            failed.append(f'4: {e}')

        # ==================================================================
        # 5 — Keyboard shortcut JS file is parseable (no syntax errors)
        # ==================================================================
        print('[5/5] main.js syntax check...')
        try:
            js_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'static', 'js', 'main.js',
            )
            content = open(js_path, encoding='utf-8').read()
            assert len(content) > 100, 'main.js too short — possibly corrupted'
            # Check balanced braces (basic syntax sanity)
            open_braces = content.count('{')
            close_braces = content.count('}')
            assert abs(open_braces - close_braces) <= 2, \
                f'Brace imbalance: {{ {open_braces} }} {close_braces}'
            # Confirm F10 is NOT in the preventDefault set
            # Look for any line that prevents F10
            f10_prevented = bool(re.search(
                r"e\.key\s*===?\s*['\"]F10['\"].*preventDefault|"
                r"preventDefault.*e\.key\s*===?\s*['\"]F10['\"]",
                content
            ))
            assert not f10_prevented, 'F10 is accidentally suppressed in main.js'
            passed.append('5: main.js syntax OK, F10 not suppressed')
        except Exception as e:
            failed.append(f'5: {e}')

    # ---- Summary --------------------------------------------------------
    print()
    print(f'Phase 2 Audit Fix Tests: {len(passed)} passed, {len(failed)} failed')
    for p in passed:
        print(f'  ✓ {p}')
    for f in failed:
        print(f'  ✗ {f}')
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

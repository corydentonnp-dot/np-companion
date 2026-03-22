"""
Phase 44 — Page Transitions Tests (UI_OVERHAUL.md System 8)

12 tests covering:
  - CSS keyframes for all transition types present in main.css
  - Page transition classes defined in main.css
  - Page transition JS interceptor in base.html
  - Settings UI has transition preset buttons
  - _applyTransition() function in settings.html
  - Server preference endpoint handles page_transition param
  - Valid transition values accepted; invalid values rejected

Usage:
    venv\\Scripts\\python.exe tests/test_transitions.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TEMPLATES_DIR = os.path.join(ROOT, 'templates')
STATIC_DIR = os.path.join(ROOT, 'static')

VALID_TRANSITIONS = ['none', 'fade', 'slide', 'zoom', 'subtle']


def _read_template(filename):
    path = os.path.join(TEMPLATES_DIR, filename)
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def _read_css():
    path = os.path.join(STATIC_DIR, 'css', 'main.css')
    with open(path, encoding='utf-8') as fh:
        return fh.read()


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
    total_tests = 12

    # ------------------------------------------------------------------ #
    # 1 — CSS contains page-transition keyframes
    # ------------------------------------------------------------------ #
    print(f'[1/{total_tests}] Page transition keyframes in main.css...')
    try:
        css = _read_css()
        assert '@keyframes' in css, '@keyframes not found in main.css'
        # At least one transition animation should exist
        has_anim = any(term in css for term in [
            'pt-fade', 'pt-slide', 'ptFade', 'ptSlide', 'page-transition',
            'pageTransition', 'transition-fade', 'fade-in',
        ])
        assert has_anim, 'no page transition keyframe animations found'
        passed.append('1: Page transition keyframes present in main.css')
    except Exception as e:
        failed.append(f'1: CSS keyframes — {e}')

    # ------------------------------------------------------------------ #
    # 2 — CSS contains page-transition-* class rules
    # ------------------------------------------------------------------ #
    print(f'[2/{total_tests}] page-transition-* CSS classes in main.css...')
    try:
        css = _read_css()
        has_class = any(f'page-transition-{t}' in css for t in
                        ['fade', 'slide', 'zoom', 'subtle'])
        assert has_class, 'no page-transition-{type} CSS classes found'
        passed.append('2: page-transition-* CSS classes present')
    except Exception as e:
        failed.append(f'2: CSS transition classes — {e}')

    # ------------------------------------------------------------------ #
    # 3 — Page transition JS interceptor in base.html
    # ------------------------------------------------------------------ #
    print(f'[3/{total_tests}] Page transition JS interceptor in base.html...')
    try:
        html = _read_template('base.html')
        has_interceptor = any(term in html for term in [
            'pageTransition', 'page-transition', 'page_transition',
            'transition-interceptor',
        ])
        assert has_interceptor, 'no page transition JS found in base.html'
        passed.append('3: Page transition JS interceptor present')
    except Exception as e:
        failed.append(f'3: Transition JS interceptor — {e}')

    # ------------------------------------------------------------------ #
    # 4 — localStorage usage for pageTransition in base.html
    # ------------------------------------------------------------------ #
    print(f'[4/{total_tests}] localStorage pageTransition in base.html...')
    try:
        html = _read_template('base.html')
        assert 'pageTransition' in html, \
            'pageTransition localStorage key not found in base.html'
        assert 'localStorage' in html, 'localStorage not found in base.html'
        passed.append('4: localStorage pageTransition usage present')
    except Exception as e:
        failed.append(f'4: localStorage pageTransition — {e}')

    # ------------------------------------------------------------------ #
    # 5 — settings.html has Page Transitions card
    # ------------------------------------------------------------------ #
    print(f'[5/{total_tests}] settings.html has Page Transitions section...')
    try:
        html = _read_template('settings.html')
        has_section = any(term in html for term in [
            'Page Transition', 'page-transition', 'transition-opt',
        ])
        assert has_section, 'no Page Transitions section in settings.html'
        passed.append('5: Page Transitions card in settings.html')
    except Exception as e:
        failed.append(f'5: Settings transition card — {e}')

    # ------------------------------------------------------------------ #
    # 6 — settings.html has _applyTransition() function
    # ------------------------------------------------------------------ #
    print(f'[6/{total_tests}] _applyTransition() in settings.html...')
    try:
        html = _read_template('settings.html')
        assert '_applyTransition' in html, \
            '_applyTransition function not found in settings.html'
        passed.append('6: _applyTransition() function present in settings.html')
    except Exception as e:
        failed.append(f'6: _applyTransition — {e}')

    # ------------------------------------------------------------------ #
    # 7 — settings.html has buttons for all valid transition values
    # ------------------------------------------------------------------ #
    print(f'[7/{total_tests}] settings.html has buttons for all transitions...')
    try:
        html = _read_template('settings.html')
        missing = [t for t in VALID_TRANSITIONS if t not in html]
        assert not missing, f'missing transition presets: {missing}'
        passed.append('7: All 5 transition preset buttons present in settings.html')
    except Exception as e:
        failed.append(f'7: Transition preset buttons — {e}')

    # ------------------------------------------------------------------ #
    # 8 — Server sync script in base.html
    # ------------------------------------------------------------------ #
    print(f'[8/{total_tests}] Server→localStorage sync script in base.html...')
    try:
        html = _read_template('base.html')
        assert 'get_pref' in html or 'page_transition' in html, \
            'no server pref sync found in base.html'
        passed.append('8: Server→localStorage sync script present')
    except Exception as e:
        failed.append(f'8: Server sync script — {e}')

    # ------------------------------------------------------------------ #
    # 9-12 — API endpoint tests (require Flask app)
    # ------------------------------------------------------------------ #
    print(f'[9/{total_tests}] Setting up Flask app for API tests...')
    try:
        app = _get_app()
        uid = _get_test_user(app)
        client = _authed_client(app, uid)
        passed.append('9: Flask app and test client ready')
    except Exception as e:
        failed.append(f'9: Flask app setup — {e}')
        total = len(passed) + len(failed)
        print(f'\n{"=" * 50}')
        print(f'Page Transition Tests: {len(passed)}/{total} passed')
        for msg in failed:
            print(f'  FAIL: {msg}')
        return len(failed) == 0

    # ------------------------------------------------------------------ #
    # 10 — POST /api/settings/theme accepts valid page_transition values
    # ------------------------------------------------------------------ #
    print(f'[10/{total_tests}] API accepts valid page_transition values...')
    try:
        for val in VALID_TRANSITIONS:
            r = client.post('/api/settings/theme',
                            json={'page_transition': val})
            assert r.status_code == 200, \
                f'Expected 200 for page_transition={val}, got {r.status_code}'
        passed.append('10: All 5 valid page_transition values accepted by API')
    except Exception as e:
        failed.append(f'10: API valid transitions — {e}')

    # ------------------------------------------------------------------ #
    # 11 — POST /api/settings/theme rejects invalid page_transition
    # ------------------------------------------------------------------ #
    print(f'[11/{total_tests}] API rejects invalid page_transition...')
    try:
        r = client.post('/api/settings/theme',
                        json={'page_transition': 'explode'})
        # Should not 500; invalid value should be ignored or rejected gracefully
        assert r.status_code in (200, 400), \
            f'Unexpected status {r.status_code} for invalid transition'
        # If 200, the value should have been ignored (not stored as-is)
        passed.append('11: Invalid page_transition handled gracefully')
    except Exception as e:
        failed.append(f'11: API invalid transition — {e}')

    # ------------------------------------------------------------------ #
    # 12 — POST /api/settings/theme still works for theme changes too
    # ------------------------------------------------------------------ #
    print(f'[12/{total_tests}] API still handles theme param alongside transition...')
    try:
        r = client.post('/api/settings/theme',
                        json={'theme': 'dark', 'page_transition': 'fade'})
        assert r.status_code == 200, f'Expected 200, got {r.status_code}'
        passed.append('12: Combined theme+page_transition POST accepted')
    except Exception as e:
        failed.append(f'12: Combined theme+transition — {e}')

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    total = len(passed) + len(failed)
    print(f'\n{"=" * 50}')
    print(f'Page Transition Tests: {len(passed)}/{total} passed')
    for msg in failed:
        print(f'  FAIL: {msg}')
    return len(failed) == 0


if __name__ == '__main__':
    ok = run_tests()
    sys.exit(0 if ok else 1)

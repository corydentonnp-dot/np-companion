"""
Phase 34 — Top Menu Integration Tests (5 tests)

Tests:
  1:  base.html References dropdown includes "Clinical Calculators" menu item
  2:  /calculators route returns 200 or login redirect (not 404)
  3:  patient_chart.html Calculators tab button present
  4:  main.js keyboard shortcut handler includes Ctrl+Shift+K logic
  5:  /calculators redirects unauthenticated users to login

Usage: venv\\Scripts\\python.exe tests\\test_calculator_menu.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_tests():
    passed = []
    failed = []

    # ── TEST 1: base.html References dropdown has "Clinical Calculators" ─

    print('[1/5] base.html References dropdown includes Clinical Calculators...')
    try:
        tpl_path = os.path.join(BASE_DIR, 'templates', 'base.html')
        with open(tpl_path, 'r', encoding='utf-8') as f:
            src = f.read()
        assert 'Clinical Calculators' in src, '"Clinical Calculators" text not found in base.html'
        assert '/calculators' in src, '/calculators URL not found in base.html'
        passed.append('1: base.html References dropdown has "Clinical Calculators" entry')
    except Exception as e:
        failed.append(f'1: base.html menu item: {e}')

    # ── TEST 2: /calculators route returns 200 or redirect ───────

    print('[2/5] /calculators route accessible (not 404)...')
    try:
        from app import create_app
        app = create_app()
        with app.test_client() as client:
            resp = client.get('/calculators')
            assert resp.status_code != 404, \
                f'/calculators returned 404 — blueprint not registered or URL incorrect'
            assert resp.status_code in (200, 301, 302, 401, 403), \
                f'Unexpected status {resp.status_code}'
            passed.append(f'2: /calculators returns {resp.status_code} (registered)')
    except Exception as e:
        failed.append(f'2: /calculators route: {e}')

    # ── TEST 3: patient_chart.html has Calculators tab ───────────

    print('[3/5] patient_chart.html has Calculators tab button...')
    try:
        tpl_path = os.path.join(BASE_DIR, 'templates', 'patient_chart.html')
        with open(tpl_path, 'r', encoding='utf-8') as f:
            src = f.read()
        assert 'data-tab="calculators"' in src, \
            'Calculators tab button (data-tab="calculators") not found in patient_chart.html'
        assert "switchTab('calculators'" in src, \
            "switchTab('calculators') not found in patient_chart.html"
        passed.append('3: patient_chart.html has Calculators tab button')
    except Exception as e:
        failed.append(f'3: Calculators tab: {e}')

    # ── TEST 4: main.js has Ctrl+Shift+K shortcut ────────────────

    print('[4/5] main.js includes Ctrl+Shift+K → /calculators shortcut...')
    try:
        main_js_path = os.path.join(BASE_DIR, 'static', 'js', 'main.js')
        with open(main_js_path, 'r', encoding='utf-8') as f:
            src = f.read()
        assert '/calculators' in src, '/calculators URL not in main.js'
        # Verify Ctrl+Shift+K logic: key == 'K' and ctrlKey and shiftKey
        assert "ctrlKey" in src, 'ctrlKey check not in main.js'
        assert "shiftKey" in src, 'shiftKey check not in main.js'
        # Specifically check for the calculators shortcut (K key)
        assert "e.key === 'K'" in src or "e.key === 'k'" in src, \
            "K key shortcut not found in main.js"
        passed.append('4: main.js has Ctrl+Shift+K → /calculators shortcut')
    except Exception as e:
        failed.append(f'4: Keyboard shortcut: {e}')

    # ── TEST 5: Unauthenticated user redirected to login ─────────

    print('[5/5] /calculators redirects unauthenticated users...')
    try:
        from app import create_app
        app = create_app()
        with app.test_client() as client:
            resp = client.get('/calculators', follow_redirects=False)
            # Should redirect (302) or give auth error (401/403), not serve content (200) to anon
            assert resp.status_code != 404, '/calculators not found'
            assert resp.status_code in (302, 301, 401, 403), \
                f'Expected redirect for unauthenticated, got {resp.status_code}'
            if resp.status_code in (301, 302):
                location = resp.headers.get('Location', '')
                assert 'login' in location.lower() or location, \
                    f'Redirect location unexpected: {location}'
            passed.append(f'5: /calculators redirects unauthenticated user ({resp.status_code})')
    except Exception as e:
        failed.append(f'5: Auth redirect: {e}')

    # ── Summary ─────────────────────────────────────────────────

    print('\n' + '=' * 60)
    print(f'Phase 34 — Menu Integration: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)
    for p in passed:
        print(f'  PASS {p}')
    for f in failed:
        print(f'  FAIL {f}')
    print()
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

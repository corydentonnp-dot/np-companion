"""
tests/test_split_view.py
PH44-3: Split View — automated checks
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    passed = 0
    failed = 0
    errors = []

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    css_path = os.path.join(base_dir, 'static', 'css', 'main.css')
    base_path = os.path.join(base_dir, 'templates', 'base.html')
    settings_path = os.path.join(base_dir, 'templates', 'settings.html')
    auth_path = os.path.join(base_dir, 'routes', 'auth.py')

    css = open(css_path, encoding='utf-8').read()
    base = open(base_path, encoding='utf-8').read()
    settings = open(settings_path, encoding='utf-8').read()
    auth_src = open(auth_path, encoding='utf-8').read()

    def chk(desc, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            errors.append(f'FAIL [{desc}]')

    # ── CSS checks ──────────────────────────────────────────────
    chk('split-panes class', '.split-panes {' in css)
    chk('split-pane class', '.split-pane {' in css)
    chk('split-divider class', '.split-divider {' in css)
    chk('split-toggle-btn class', '.split-toggle-btn {' in css)
    chk('split-pane-header class', '.split-pane-header {' in css)
    chk('main-content split-active', '.main-content.split-active {' in css)
    chk('responsive disable split', '.split-pane.pane-secondary { display: none; }' in css)

    # ── base.html checks ─────────────────────────────────────────
    chk('split-toggle-btn in header', 'split-toggle-btn' in base)
    chk('SplitViewManager JS class', 'window.SplitViewManager' in base)
    chk('SplitViewManager.open method', 'function open(url)' in base)
    chk('SplitViewManager.close method', 'function close()' in base)
    chk('Ctrl+click interceptor', 'e.ctrlKey' in base)
    chk('split-active class applied', "'split-active'" in base)
    chk('split-panes wrapper created', 'split-panes' in base)
    chk('splitMaxPanes localStorage read', 'splitMaxPanes' in base)
    chk('splitMaxPanes server sync', "localStorage.setItem('splitMaxPanes'" in base)

    # ── settings.html checks ──────────────────────────────────────
    chk('split_max_panes Settings card', 'Split View' in settings and 'split-panes-opt' in settings)
    chk('_setSplitPanes JS', '_setSplitPanes' in settings)

    # ── API endpoint check ────────────────────────────────────────
    chk('/api/settings/split_panes route', '/api/settings/split_panes' in auth_src)

    return passed, failed, errors


if __name__ == '__main__':
    passed, failed, errors = run_tests()
    for e in errors:
        print(e)
    print(f'\nResults: {passed} passed, {failed} failed out of {passed + failed} checks')
    sys.exit(0 if failed == 0 else 1)

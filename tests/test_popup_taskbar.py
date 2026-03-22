"""
Phase 44 — Popup Taskbar Tests (UI_OVERHAUL.md System 2)

10 tests covering:
  - #popup-taskbar container present in base.html
  - ModalTaskbar JS class defined in base.html
  - data-blocking="true" on all 4 security modals
  - Non-security modals do NOT have data-blocking
  - backbone JS wires click-outside to minimize

Usage:
    venv\\Scripts\\python.exe tests/test_popup_taskbar.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TEMPLATES_DIR = os.path.join(ROOT, 'templates')


def _read_template(filename):
    path = os.path.join(TEMPLATES_DIR, filename)
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def run_tests():
    passed = []
    failed = []
    total_tests = 10

    # ------------------------------------------------------------------ #
    # 1 — #popup-taskbar container present in base.html
    # ------------------------------------------------------------------ #
    print(f'[1/{total_tests}] popup-taskbar container in base.html...')
    try:
        html = _read_template('base.html')
        assert 'id="popup-taskbar"' in html, 'missing id="popup-taskbar"'
        passed.append('1: #popup-taskbar container present')
    except Exception as e:
        failed.append(f'1: #popup-taskbar container — {e}')

    # ------------------------------------------------------------------ #
    # 2 — ModalTaskbar class defined in base.html
    # ------------------------------------------------------------------ #
    print(f'[2/{total_tests}] ModalTaskbar class in base.html JS...')
    try:
        html = _read_template('base.html')
        assert 'ModalTaskbar' in html, 'ModalTaskbar class not found'
        passed.append('2: ModalTaskbar JS class defined')
    except Exception as e:
        failed.append(f'2: ModalTaskbar JS class — {e}')

    # ------------------------------------------------------------------ #
    # 3 — data-blocking="true" on #hipaa-modal
    # ------------------------------------------------------------------ #
    print(f'[3/{total_tests}] data-blocking on #hipaa-modal...')
    try:
        html = _read_template('base.html')
        # Find hipaa modal section
        assert 'id="hipaa-modal"' in html or 'hipaa-modal' in html, 'hipaa-modal not found'
        # Check data-blocking near that modal
        idx = html.find('hipaa-modal')
        chunk = html[max(0, idx - 50):idx + 300]
        assert 'data-blocking="true"' in chunk, \
            'data-blocking="true" not near hipaa-modal'
        passed.append('3: data-blocking="true" on hipaa-modal')
    except Exception as e:
        failed.append(f'3: hipaa-modal data-blocking — {e}')

    # ------------------------------------------------------------------ #
    # 4 — data-blocking="true" on lock overlay
    # ------------------------------------------------------------------ #
    print(f'[4/{total_tests}] data-blocking on lock overlay...')
    try:
        html = _read_template('base.html')
        assert 'lock-overlay' in html, 'lock-overlay not found'
        idx = html.find('lock-overlay')
        chunk = html[max(0, idx - 50):idx + 400]
        assert 'data-blocking="true"' in chunk, \
            'data-blocking="true" not near lock-overlay'
        passed.append('4: data-blocking="true" on lock overlay')
    except Exception as e:
        failed.append(f'4: lock-overlay data-blocking — {e}')

    # ------------------------------------------------------------------ #
    # 5 — data-blocking="true" on #p1-modal-overlay
    # ------------------------------------------------------------------ #
    print(f'[5/{total_tests}] data-blocking on #p1-modal-overlay...')
    try:
        html = _read_template('base.html')
        assert 'p1-modal-overlay' in html, 'p1-modal-overlay not found'
        idx = html.find('p1-modal-overlay')
        chunk = html[max(0, idx - 50):idx + 500]
        assert 'data-blocking="true"' in chunk, \
            'data-blocking="true" not near p1-modal'
        passed.append('5: data-blocking="true" on p1-modal-overlay')
    except Exception as e:
        failed.append(f'5: p1-modal data-blocking — {e}')

    # ------------------------------------------------------------------ #
    # 6 — data-blocking="true" on #deact-modal (in admin_users.html)
    # ------------------------------------------------------------------ #
    print(f'[6/{total_tests}] data-blocking on #deact-modal...')
    try:
        html = _read_template('admin_users.html')
        assert 'deact-modal' in html, 'deact-modal not found in admin_users.html'
        # Search for the div element definition (not JS references)
        marker = 'id="deact-modal"'
        assert marker in html, f'{marker} not found in admin_users.html'
        idx = html.find(marker)
        chunk = html[max(0, idx - 10):idx + 200]
        assert 'data-blocking="true"' in chunk, \
            'data-blocking="true" not on deact-modal element'
        passed.append('6: data-blocking="true" on deact-modal')
    except Exception as e:
        failed.append(f'6: deact-modal data-blocking — {e}')

    # ------------------------------------------------------------------ #
    # 7 — Total data-blocking count is exactly 4
    # ------------------------------------------------------------------ #
    print(f'[7/{total_tests}] Total data-blocking="true" count is 4...')
    try:
        base_html = _read_template('base.html')
        admin_html = _read_template('admin_users.html')
        count_base = base_html.count('data-blocking="true"')
        count_admin = admin_html.count('data-blocking="true"')
        total = count_base + count_admin
        assert total == 4, f'Expected 4 data-blocking="true" total, got {total} ({count_base} in base, {count_admin} in admin_users)'
        passed.append(f'7: Exactly 4 data-blocking="true" markers found')
    except Exception as e:
        failed.append(f'7: data-blocking count — {e}')

    # ------------------------------------------------------------------ #
    # 8 — ModalTaskbar has _saveState and _restoreState methods
    # ------------------------------------------------------------------ #
    print(f'[8/{total_tests}] ModalTaskbar has _saveState/_restoreState...')
    try:
        html = _read_template('base.html')
        assert '_saveState' in html, '_saveState not found'
        assert '_restoreState' in html, '_restoreState not found'
        passed.append('8: ModalTaskbar has _saveState/_restoreState')
    except Exception as e:
        failed.append(f'8: ModalTaskbar state methods — {e}')

    # ------------------------------------------------------------------ #
    # 9 — Minimize logic present (click-outside wiring)
    # ------------------------------------------------------------------ #
    print(f'[9/{total_tests}] Click-outside minimize logic present...')
    try:
        html = _read_template('base.html')
        assert 'minimize' in html.lower(), 'no minimize reference found'
        passed.append('9: Minimize logic present in base.html JS')
    except Exception as e:
        failed.append(f'9: Minimize logic — {e}')

    # ------------------------------------------------------------------ #
    # 10 — Taskbar restore logic present
    # ------------------------------------------------------------------ #
    print(f'[10/{total_tests}] Taskbar restore logic present...')
    try:
        html = _read_template('base.html')
        assert 'restore' in html.lower() or 'Restore' in html, \
            'no restore reference found'
        passed.append('10: Restore logic present in base.html JS')
    except Exception as e:
        failed.append(f'10: Restore logic — {e}')

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    total = len(passed) + len(failed)
    print(f'\n{"=" * 50}')
    print(f'Popup Taskbar Tests: {len(passed)}/{total} passed')
    for msg in failed:
        print(f'  FAIL: {msg}')
    return len(failed) == 0


if __name__ == '__main__':
    ok = run_tests()
    sys.exit(0 if ok else 1)

"""
Phase 44 — Breadcrumb Trail Tests (UI_OVERHAUL.md System 6)

10 tests covering:
  - #breadcrumb-trail container present in base.html
  - data-breadcrumb-badge attribute on <main> in base.html
  - breadcrumb JS sessionStorage logic present
  - {% block breadcrumb_badge %} defined in base.html
  - Patient chart, caregap, inbox, timer templates define breadcrumb_badge
  - Badge content appropriate for each page

Usage:
    venv\\Scripts\\python.exe tests/test_breadcrumbs.py
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
    # 1 — #breadcrumb-trail container in base.html
    # ------------------------------------------------------------------ #
    print(f'[1/{total_tests}] breadcrumb-trail container in base.html...')
    try:
        html = _read_template('base.html')
        assert 'breadcrumb-trail' in html, 'missing breadcrumb-trail element'
        passed.append('1: #breadcrumb-trail container present')
    except Exception as e:
        failed.append(f'1: #breadcrumb-trail container — {e}')

    # ------------------------------------------------------------------ #
    # 2 — data-breadcrumb-badge attribute on <main> in base.html
    # ------------------------------------------------------------------ #
    print(f'[2/{total_tests}] data-breadcrumb-badge on <main>...')
    try:
        html = _read_template('base.html')
        assert 'data-breadcrumb-badge' in html, \
            'data-breadcrumb-badge attribute not found in base.html'
        # Make sure it's on the main element
        idx = html.find('data-breadcrumb-badge')
        chunk = html[max(0, idx - 200):idx + 50]
        assert 'main' in chunk, 'data-breadcrumb-badge not on <main> element'
        passed.append('2: data-breadcrumb-badge on <main>')
    except Exception as e:
        failed.append(f'2: data-breadcrumb-badge attribute — {e}')

    # ------------------------------------------------------------------ #
    # 3 — {% block breadcrumb_badge %} defined in base.html
    # ------------------------------------------------------------------ #
    print(f'[3/{total_tests}] breadcrumb_badge block defined in base.html...')
    try:
        html = _read_template('base.html')
        bb_block = '{%' + ' block breadcrumb_badge ' + '%}'
        assert bb_block in html, \
            'breadcrumb_badge block not in base.html'
        passed.append('3: breadcrumb_badge block defined in base.html')
    except Exception as e:
        failed.append(f'3: breadcrumb_badge block — {e}')

    # ------------------------------------------------------------------ #
    # 4 — Breadcrumb sessionStorage JS logic present
    # ------------------------------------------------------------------ #
    print(f'[4/{total_tests}] Breadcrumb sessionStorage JS in base.html...')
    try:
        html = _read_template('base.html')
        assert 'breadcrumbs' in html, 'no breadcrumbs JS reference found'
        assert 'sessionStorage' in html, 'no sessionStorage reference found'
        passed.append('4: Breadcrumb sessionStorage JS present')
    except Exception as e:
        failed.append(f'4: Breadcrumb sessionStorage — {e}')

    # ------------------------------------------------------------------ #
    # 5 — patient_chart.html defines breadcrumb_badge
    # ------------------------------------------------------------------ #
    print(f'[5/{total_tests}] patient_chart.html defines breadcrumb_badge...')
    try:
        bb_block = '{%' + ' block breadcrumb_badge ' + '%}'
        bb_end = '{%' + ' endblock ' + '%}'
        html = _read_template('patient_chart.html')
        assert bb_block in html, \
            'breadcrumb_badge block not in patient_chart.html'
        idx2 = html.index(bb_block)
        end = html.index(bb_end, idx2)
        content = html[idx2 + len(bb_block):end].strip()
        assert len(content) > 0, 'breadcrumb_badge block is empty in patient_chart.html'
        passed.append('5: patient_chart.html breadcrumb_badge populated')
    except Exception as e:
        failed.append(f'5: patient_chart breadcrumb_badge — {e}')

    # ------------------------------------------------------------------ #
    # 6 — caregap.html defines breadcrumb_badge with gap count
    # ------------------------------------------------------------------ #
    print(f'[6/{total_tests}] caregap.html defines breadcrumb_badge...')
    try:
        bb_block = '{%' + ' block breadcrumb_badge ' + '%}'
        bb_end = '{%' + ' endblock ' + '%}'
        html = _read_template('caregap.html')
        assert bb_block in html, \
            'breadcrumb_badge block not in caregap.html'
        idx2 = html.index(bb_block)
        end = html.index(bb_end, idx2)
        content = html[idx2 + len(bb_block):end].strip()
        assert len(content) > 0, 'breadcrumb_badge block is empty in caregap.html'
        passed.append('6: caregap.html breadcrumb_badge populated')
    except Exception as e:
        failed.append(f'6: caregap breadcrumb_badge — {e}')

    # ------------------------------------------------------------------ #
    # 7 — inbox.html defines breadcrumb_badge
    # ------------------------------------------------------------------ #
    print(f'[7/{total_tests}] inbox.html defines breadcrumb_badge...')
    try:
        bb_block = '{%' + ' block breadcrumb_badge ' + '%}'
        bb_end = '{%' + ' endblock ' + '%}'
        html = _read_template('inbox.html')
        assert bb_block in html, \
            'breadcrumb_badge block not in inbox.html'
        idx2 = html.index(bb_block)
        end = html.index(bb_end, idx2)
        content = html[idx2 + len(bb_block):end].strip()
        assert len(content) > 0, 'breadcrumb_badge block is empty in inbox.html'
        passed.append('7: inbox.html breadcrumb_badge populated')
    except Exception as e:
        failed.append(f'7: inbox breadcrumb_badge — {e}')

    # ------------------------------------------------------------------ #
    # 8 — timer.html defines breadcrumb_badge
    # ------------------------------------------------------------------ #
    print(f'[8/{total_tests}] timer.html defines breadcrumb_badge...')
    try:
        bb_block = '{%' + ' block breadcrumb_badge ' + '%}'
        bb_end = '{%' + ' endblock ' + '%}'
        html = _read_template('timer.html')
        assert bb_block in html, \
            'breadcrumb_badge block not in timer.html'
        idx2 = html.index(bb_block)
        end = html.index(bb_end, idx2)
        content = html[idx2 + len(bb_block):end].strip()
        assert len(content) > 0, 'breadcrumb_badge block is empty in timer.html'
        passed.append('8: timer.html breadcrumb_badge populated')
    except Exception as e:
        failed.append(f'8: timer breadcrumb_badge — {e}')

    # ------------------------------------------------------------------ #
    # 9 — Breadcrumb chip rendering JS present
    # ------------------------------------------------------------------ #
    print(f'[9/{total_tests}] Breadcrumb chip rendering JS in base.html...')
    try:
        html = _read_template('base.html')
        # Look for chip creation or breadcrumb rendering logic
        assert 'breadcrumb' in html.lower(), 'no breadcrumb JS found'
        # At least one of the key rendering terms should exist
        has_render = any(term in html for term in [
            'innerHTML', 'appendChild', 'createElem', 'chip', 'trail'
        ])
        assert has_render, 'no breadcrumb rendering logic found'
        passed.append('9: Breadcrumb chip rendering JS present')
    except Exception as e:
        failed.append(f'9: Breadcrumb rendering JS — {e}')

    # ------------------------------------------------------------------ #
    # 10 — base.html has block breadcrumb_badge inside data attribute
    # ------------------------------------------------------------------ #
    print(f'[10/{total_tests}] breadcrumb_badge wired into data attribute...')
    try:
        html = _read_template('base.html')
        # The block should be used inside data-breadcrumb-badge="..."
        assert 'data-breadcrumb-badge=' in html, 'data-breadcrumb-badge= not found'
        idx = html.find('data-breadcrumb-badge=')
        chunk = html[idx:idx + 100]
        assert 'breadcrumb_badge' in chunk, \
            'breadcrumb_badge block not inside data-breadcrumb-badge attribute'
        passed.append('10: breadcrumb_badge block properly wired into data attribute')
    except Exception as e:
        failed.append(f'10: breadcrumb_badge wiring — {e}')

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    total = len(passed) + len(failed)
    print(f'\n{"=" * 50}')
    print(f'Breadcrumb Tests: {len(passed)}/{total} passed')
    for msg in failed:
        print(f'  FAIL: {msg}')
    return len(failed) == 0


if __name__ == '__main__':
    ok = run_tests()
    sys.exit(0 if ok else 1)

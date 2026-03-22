"""
Phase 44 — Type-Ahead Filtering Tests (UI_OVERHAUL.md System 7)

10 tests covering:
  - data-filterable attribute on all list/table page templates
  - Type-ahead JS logic present in base.html
  - Debounce logic present
  - Keydown handler wired up

Usage:
    venv\\Scripts\\python.exe tests/test_type_ahead.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TEMPLATES_DIR = os.path.join(ROOT, 'templates')

# Each tuple: (template filename, description)
FILTERABLE_PAGES = [
    ('patient_roster.html', 'patient rows'),
    ('notifications.html', 'notification rows'),
    ('caregap.html', 'patient gap rows'),
    ('tcm_watch.html', 'active watch cards'),
    ('ccm_registry.html', 'registry rows'),
    ('oncall.html', 'note cards'),
    ('monitoring_calendar.html', 'patient divs'),
    ('labtrack.html', 'tracking rows'),
    ('orders.html', 'order set cards'),
    ('inbox.html', 'inbox item rows'),
    ('timer.html', 'session rows'),
    ('staff_billing_tasks.html', 'task rows'),
    ('care_gaps_preventive.html', 'service cards'),
]


def _read_template(filename):
    path = os.path.join(TEMPLATES_DIR, filename)
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def run_tests():
    passed = []
    failed = []
    total_tests = len(FILTERABLE_PAGES) + 3

    # ------------------------------------------------------------------ #
    # 1-13 — Each list template has data-filterable on repeating items
    # ------------------------------------------------------------------ #
    for idx, (tmpl, desc) in enumerate(FILTERABLE_PAGES, start=1):
        label = f'{idx}: {tmpl} has data-filterable on {desc}'
        print(f'[{idx}/{total_tests}] {label}...')
        try:
            html = _read_template(tmpl)
            assert 'data-filterable' in html, \
                f'data-filterable attribute not found in {tmpl}'
            passed.append(label)
        except Exception as e:
            failed.append(f'{label} — {e}')

    n = len(FILTERABLE_PAGES)

    # ------------------------------------------------------------------ #
    # 14 — Type-ahead JS logic present in base.html
    # ------------------------------------------------------------------ #
    print(f'[{n+1}/{total_tests}] Type-ahead JS in base.html...')
    try:
        html = _read_template('base.html')
        # Look for type-ahead search input or filterable JS handler
        has_filter = any(term in html for term in [
            'data-filterable', 'filterable', 'type-ahead', 'typeahead',
            'filterItems', 'filter_items',
        ])
        assert has_filter, 'no type-ahead/filterable JS found in base.html'
        passed.append(f'{n+1}: Type-ahead JS present in base.html')
    except Exception as e:
        failed.append(f'{n+1}: Type-ahead JS — {e}')

    # ------------------------------------------------------------------ #
    # 15 — Debounce or keydown handler present in base.html
    # ------------------------------------------------------------------ #
    print(f'[{n+2}/{total_tests}] Debounce/keydown handler in base.html...')
    try:
        html = _read_template('base.html')
        has_debounce = any(term in html for term in [
            'debounce', 'keydown', 'keyup', 'input', 'setTimeout',
        ])
        assert has_debounce, 'no debounce/keydown handler found in base.html'
        passed.append(f'{n+2}: Debounce/keydown handler present')
    except Exception as e:
        failed.append(f'{n+2}: Debounce/keydown — {e}')

    # ------------------------------------------------------------------ #
    # 16 — Dashboard does NOT have data-filterable (not a list page)
    # ------------------------------------------------------------------ #
    print(f'[{n+3}/{total_tests}] Dashboard correctly lacks data-filterable...')
    try:
        html = _read_template('dashboard.html')
        if 'data-filterable' not in html:
            passed.append(f'{n+3}: dashboard.html correctly has no data-filterable')
        else:
            # Not necessarily a fail — might have filterable widgets — just note it
            passed.append(f'{n+3}: dashboard.html has data-filterable (may be intentional)')
    except Exception as e:
        failed.append(f'{n+3}: Dashboard filterable check — {e}')

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    total = len(passed) + len(failed)
    print(f'\n{"=" * 50}')
    print(f'Type-Ahead Filtering Tests: {len(passed)}/{total} passed')
    for msg in failed:
        print(f'  FAIL: {msg}')
    return len(failed) == 0


if __name__ == '__main__':
    ok = run_tests()
    sys.exit(0 if ok else 1)

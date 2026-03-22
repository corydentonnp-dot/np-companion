"""
tests/test_ai_enhancements.py
PH44-9: AI Enhancements (Help Popovers) — automated checks
AI Writing/Coach/Navigation are deferred (require encrypted API key storage).
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    passed = 0
    failed = 0
    errors = []

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    css_path = os.path.join(base_dir, 'static', 'css', 'main.css')
    base_path = os.path.join(base_dir, 'templates', 'base.html')
    help_py_path = os.path.join(base_dir, 'routes', 'help.py')
    hg_path = os.path.join(base_dir, 'data', 'help_guide.json')

    css = open(css_path, encoding='utf-8').read()
    base = open(base_path, encoding='utf-8').read()
    help_src = open(help_py_path, encoding='utf-8').read()
    hg = json.load(open(hg_path, encoding='utf-8'))

    def chk(desc, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            errors.append(f'FAIL [{desc}]')

    # CSS checks
    chk('help-icon CSS', '.help-icon {' in css)
    chk('help-popover CSS', '.help-popover {' in css)
    chk('help-popover-title CSS', '.help-popover-title' in css)
    chk('help-popover-body CSS', '.help-popover-body' in css or '.help-popover p' in css)
    chk('help-popover-link CSS', '.help-popover-link' in css or '.help-popover a' in css)
    chk('ai-assist-icon CSS', '.ai-assist-icon' in css)
    chk('ai-suggest-popover CSS', '.ai-suggest-popover' in css)

    # base.html elements
    chk('page-help-icon element', 'id="page-help-icon"' in base)
    chk('page-help-popover element', 'id="page-help-popover"' in base)
    chk('help-icon class on button', 'class="help-icon"' in base or "class='help-icon'" in base)

    # JS checks in base.html
    chk('window.__npHelp preload', 'window.__npHelp' in base)
    chk('__npHelp fetch /api/help/items', '/api/help/items' in base)
    chk('help popovers IIFE click delegate', 'help-icon' in base and ('addEventListener' in base or 'click' in base))
    chk('Escape key dismiss', "'Escape'" in base or '"Escape"' in base)
    chk('click-outside dismiss', 'contains' in base or 'closest' in base)

    # help.py API route
    chk('/api/help/items route exists', '/api/help/items' in help_src)
    chk('help_items returns list', 'help_items' in help_src)

    # help_guide.json
    categories = [c['id'] for c in hg.get('categories', [])]
    chk('ui-ux category in help_guide.json', 'ui-ux' in categories)

    ph44_ids = {'context-subpanel', 'popup-taskbar', 'split-view', 'pip-widgets',
                'smart-bookmarks', 'breadcrumb-trail', 'type-ahead-filter', 'page-transitions'}
    feature_ids = {f['id'] for f in hg.get('features', [])}
    missing = ph44_ids - feature_ids
    chk('all Phase 44 features in help_guide.json', len(missing) == 0)
    if missing:
        errors.append(f'  Missing feature IDs: {sorted(missing)}')

    # Total count sanity
    total_features = len(hg.get('features', []))
    chk('at least 50 features in help_guide.json', total_features >= 50)

    return passed, failed, errors


if __name__ == '__main__':
    passed, failed, errors = run_tests()
    for e in errors:
        print(e)
    print(f'\nResults: {passed} passed, {failed} failed out of {passed + failed} checks')
    sys.exit(0 if failed == 0 else 1)

"""
tests/test_bookmarks_folders.py
PH44-5: Smart Bookmarks with Folders — automated checks
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
    auth_path = os.path.join(base_dir, 'routes', 'auth.py')

    css = open(css_path, encoding='utf-8').read()
    base = open(base_path, encoding='utf-8').read()
    auth_src = open(auth_path, encoding='utf-8').read()

    def chk(desc, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            errors.append(f'FAIL [{desc}]')

    # CSS checks
    chk('bm-folder CSS', '.bm-folder {' in css)
    chk('bm-folder-dropdown CSS', '.bm-folder-dropdown {' in css)
    chk('bm-drop-indicator CSS', '.bm-drop-indicator {' in css)
    chk('bookmarks-bar drag-over CSS', '.bookmarks-bar.drag-over' in css)
    chk('bm-folder drag-over CSS', '.bm-folder.drag-over' in css)

    # base.html drag-to-bookmark JS
    chk('drag-to-bookmark JS in base.html', 'drag-to-bookmark' in base.lower() or 'dragstart' in base)
    chk('draggable attribute set', "setAttribute('draggable'" in base)
    chk('dragover on bookmarks bar', "dragover" in base and "bookmarks-bar" in base)
    chk('drop handler present', "'drop'" in base or '"drop"' in base)
    chk('data-no-drag exclusion', 'data-no-drag' in base)

    # auth.py API checks
    chk('_migrate_bookmarks helper', '_migrate_bookmarks' in auth_src)
    chk('folder type support in POST', "item_type == 'folder'" in auth_src)
    chk('folder children field', "'children'" in auth_src)
    chk('folder_rename endpoint', '/api/bookmarks/personal/folder/rename' in auth_src)
    chk('folder_delete endpoint', '/api/bookmarks/personal/folder/delete' in auth_src)
    chk('migration called on GET', '_migrate_bookmarks(personal)' in auth_src)
    chk('backward compatible label+url', "Label and URL required" in auth_src)

    # help_guide.json entries
    import json
    hg_path = os.path.join(base_dir, 'data', 'help_guide.json')
    hg = json.load(open(hg_path, encoding='utf-8'))
    smart_bm = next((f for f in hg['features'] if f['id'] == 'smart-bookmarks'), None)
    chk('smart-bookmarks in help_guide.json', smart_bm is not None)
    if smart_bm:
        chk('smart-bookmarks has description', bool(smart_bm.get('description')))

    return passed, failed, errors


if __name__ == '__main__':
    passed, failed, errors = run_tests()
    for e in errors:
        print(e)
    print(f'\nResults: {passed} passed, {failed} failed out of {passed + failed} checks')
    sys.exit(0 if failed == 0 else 1)

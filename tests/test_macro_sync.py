"""
Phase P4-5 — Macro Auto-Sync (F23a)

Tests for AHK_AUTO_SYNC_PATH config, _sync_ahk_to_disk() helper,
sync wiring in CRUD routes, manual sync endpoint, sync status UI,
and edge cases.
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(ROOT, relpath), 'r', encoding='utf-8') as f:
        return f.read()


def run_tests():
    passed = []
    failed = []

    config_py = _read('config.py')
    tools_py = _read('routes/tools.py')
    macros_html = _read('templates/macros.html')

    # ==================================================================
    # 5.1 — AHK_AUTO_SYNC_PATH config
    # ==================================================================

    print('[1/15] AHK_AUTO_SYNC_PATH exists in config.py...')
    try:
        assert 'AHK_AUTO_SYNC_PATH' in config_py, 'AHK_AUTO_SYNC_PATH not found'
        passed.append('5.1a config constant exists')
    except Exception as e:
        failed.append(f'5.1a config constant exists: {e}')

    print('[2/15] AHK_AUTO_SYNC_PATH defaults to None...')
    try:
        import config
        val = getattr(config, 'AHK_AUTO_SYNC_PATH', 'MISSING')
        assert val is None, f'expected None default, got {val}'
        passed.append('5.1b default is None')
    except Exception as e:
        failed.append(f'5.1b default is None: {e}')

    # ==================================================================
    # 5.2 — _sync_ahk_to_disk() helper
    # ==================================================================

    print('[3/15] _sync_ahk_to_disk() function exists...')
    try:
        assert 'def _sync_ahk_to_disk' in tools_py, 'function not found'
        passed.append('5.2a helper exists')
    except Exception as e:
        failed.append(f'5.2a helper exists: {e}')

    print('[4/15] Sync disabled when path is None...')
    try:
        from routes.tools import _sync_ahk_to_disk
        import config as _cfg
        original = getattr(_cfg, 'AHK_AUTO_SYNC_PATH', None)
        _cfg.AHK_AUTO_SYNC_PATH = None
        result = _sync_ahk_to_disk(1)
        assert result['synced'] is False, f'expected synced=False, got {result}'
        assert result.get('reason') == 'not_configured', f'wrong reason: {result}'
        _cfg.AHK_AUTO_SYNC_PATH = original
        passed.append('5.2b sync disabled when None')
    except Exception as e:
        failed.append(f'5.2b sync disabled when None: {e}')

    print('[5/15] Sync writes file when path configured...')
    try:
        from routes.tools import _sync_ahk_to_disk
        import config as _cfg
        tmpfile = tempfile.NamedTemporaryFile(mode='w', suffix='.ahk', delete=False)
        tmpfile.close()
        original = getattr(_cfg, 'AHK_AUTO_SYNC_PATH', None)
        _cfg.AHK_AUTO_SYNC_PATH = tmpfile.name
        # Need app context for DB queries
        from app import create_app
        app = create_app()
        with app.app_context():
            result = _sync_ahk_to_disk(1)
        assert result['synced'] is True, f'expected synced=True, got {result}'
        assert os.path.exists(tmpfile.name), 'AHK file not written'
        with open(tmpfile.name, 'r', encoding='utf-8') as f:
            content = f.read()
        assert len(content) > 0, 'AHK file is empty'
        assert result.get('synced_at') is not None, 'synced_at missing'
        os.unlink(tmpfile.name)
        _cfg.AHK_AUTO_SYNC_PATH = original
        passed.append('5.2c sync writes file')
    except Exception as e:
        failed.append(f'5.2c sync writes file: {e}')

    print('[6/15] Sync failure does not raise exception...')
    try:
        from routes.tools import _sync_ahk_to_disk
        import config as _cfg
        original = getattr(_cfg, 'AHK_AUTO_SYNC_PATH', None)
        # Point to an impossible path (drive that doesn't exist)
        _cfg.AHK_AUTO_SYNC_PATH = 'Z:\\nonexistent\\impossible\\path.ahk'
        from app import create_app
        app = create_app()
        with app.app_context():
            result = _sync_ahk_to_disk(1)
        # Should NOT raise — returns error info instead
        assert result['synced'] is False, f'expected synced=False on bad path'
        assert result.get('error') is not None, 'error field missing'
        _cfg.AHK_AUTO_SYNC_PATH = original
        passed.append('5.2d sync failure safe')
    except Exception as e:
        failed.append(f'5.2d sync failure safe: {e}')

    print('[7/15] _last_sync_result tracks state...')
    try:
        from routes.tools import _last_sync_result
        assert isinstance(_last_sync_result, dict), 'not a dict'
        assert 'synced_at' in _last_sync_result, 'synced_at key missing'
        assert 'error' in _last_sync_result, 'error key missing'
        assert 'macro_count' in _last_sync_result, 'macro_count key missing'
        passed.append('5.2e last_sync_result tracking')
    except Exception as e:
        failed.append(f'5.2e last_sync_result tracking: {e}')

    # ==================================================================
    # 5.3 — Sync calls wired into CRUD routes
    # ==================================================================

    print('[8/15] Sync called after macro_create...')
    try:
        # Find the macro_create function body
        idx = tools_py.index('def macro_create')
        next_def = tools_py.index('\ndef ', idx + 20)
        body = tools_py[idx:next_def]
        assert '_sync_ahk_to_disk' in body, 'sync not called in macro_create'
        passed.append('5.3a sync in macro_create')
    except Exception as e:
        failed.append(f'5.3a sync in macro_create: {e}')

    print('[9/15] Sync called after macro_update...')
    try:
        idx = tools_py.index('def macro_update(')
        next_def = tools_py.index('\ndef ', idx + 20)
        body = tools_py[idx:next_def]
        assert '_sync_ahk_to_disk' in body, 'sync not called in macro_update'
        passed.append('5.3b sync in macro_update')
    except Exception as e:
        failed.append(f'5.3b sync in macro_update: {e}')

    print('[10/15] Sync called after macro_delete...')
    try:
        idx = tools_py.index('def macro_delete(')
        next_def = tools_py.index('\ndef ', idx + 20)
        body = tools_py[idx:next_def]
        assert '_sync_ahk_to_disk' in body, 'sync not called in macro_delete'
        passed.append('5.3c sync in macro_delete')
    except Exception as e:
        failed.append(f'5.3c sync in macro_delete: {e}')

    print('[11/15] Sync called after dot_phrase_create...')
    try:
        idx = tools_py.index('def dot_phrase_create')
        next_def = tools_py.index('\ndef ', idx + 20)
        body = tools_py[idx:next_def]
        assert '_sync_ahk_to_disk' in body, 'sync not called in dot_phrase_create'
        passed.append('5.3d sync in dot_phrase_create')
    except Exception as e:
        failed.append(f'5.3d sync in dot_phrase_create: {e}')

    print('[12/15] Sync called after dot_phrase_delete...')
    try:
        idx = tools_py.index('def dot_phrase_delete(')
        next_def = tools_py.index('\ndef ', idx + 20)
        body = tools_py[idx:next_def]
        assert '_sync_ahk_to_disk' in body, 'sync not called in dot_phrase_delete'
        passed.append('5.3e sync in dot_phrase_delete')
    except Exception as e:
        failed.append(f'5.3e sync in dot_phrase_delete: {e}')

    # ==================================================================
    # 5.4 — Manual sync endpoint + macros UI
    # ==================================================================

    print('[13/15] Manual sync endpoint exists...')
    try:
        assert "def macro_sync()" in tools_py, 'macro_sync route not found'
        assert "/tools/macros/sync" in tools_py, 'sync URL not found'
        passed.append('5.4a manual sync endpoint')
    except Exception as e:
        failed.append(f'5.4a manual sync endpoint: {e}')

    print('[14/15] Macros template shows sync status...')
    try:
        assert 'sync-status' in macros_html, 'sync-status element missing'
        assert 'sync_enabled' in macros_html, 'sync_enabled variable missing'
        assert 'Auto-sync' in macros_html, 'Auto-sync text missing'
        assert 'last_sync' in macros_html, 'last_sync variable missing'
        passed.append('5.4b sync status in template')
    except Exception as e:
        failed.append(f'5.4b sync status in template: {e}')

    print('[15/15] Manual Sync Now button and JS...')
    try:
        assert 'Sync Now' in macros_html, 'Sync Now button missing'
        assert 'manualSync' in macros_html, 'manualSync function missing'
        assert '/tools/macros/sync' in macros_html, 'sync fetch URL missing'
        passed.append('5.4c Sync Now button + JS')
    except Exception as e:
        failed.append(f'5.4c Sync Now button + JS: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print(f'\n{"="*60}')
    print(f'Phase P4-5 Macro Auto-Sync: {len(passed)} passed, {len(failed)} failed')
    print(f'{"="*60}')
    if failed:
        for f_msg in failed:
            print(f'  FAIL  {f_msg}')
    return len(failed) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

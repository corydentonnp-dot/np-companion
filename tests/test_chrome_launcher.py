"""
Tests for utils/chrome_launcher.py:
  - is_chrome_debug_running()
  - ensure_chrome_debug()
  - get_chrome_launch_command()

Uses unittest.mock to avoid actually launching Chrome.
"""

import os
import sys
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from utils.chrome_launcher import (
    is_chrome_debug_running,
    ensure_chrome_debug,
    get_chrome_launch_command,
)


def run_tests():
    passed = []
    failed = []

    # ----------------------------------------------------------------
    # is_chrome_debug_running — CDP responding → True
    # ----------------------------------------------------------------
    print('[1/6] is_chrome_debug_running — success → True...')
    try:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"Browser": "Chrome/136"}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch('utils.chrome_launcher.urllib.request.urlopen', return_value=mock_resp):
            result = is_chrome_debug_running(port=9222)
        assert result is True, f'Expected True, got {result}'
        passed.append('is_running success')
        print('  PASS')
    except Exception as e:
        failed.append(f'is_running success: {e}')
        print(f'  FAIL  {e}')

    # ----------------------------------------------------------------
    # is_chrome_debug_running — connection refused → False
    # ----------------------------------------------------------------
    print('[2/6] is_chrome_debug_running — connection error → False...')
    try:
        with patch('utils.chrome_launcher.urllib.request.urlopen',
                   side_effect=urllib.error.URLError('Connection refused')):
            result = is_chrome_debug_running(port=9222)
        assert result is False, f'Expected False, got {result}'
        passed.append('is_running refused')
        print('  PASS')
    except Exception as e:
        failed.append(f'is_running refused: {e}')
        print(f'  FAIL  {e}')

    # ----------------------------------------------------------------
    # ensure_chrome_debug — already running → skip launch
    # ----------------------------------------------------------------
    print('[3/6] ensure_chrome_debug — already running → True, no launch...')
    try:
        with patch('utils.chrome_launcher.is_chrome_debug_running', return_value=True) as mock_check:
            with patch('utils.chrome_launcher.subprocess.Popen') as mock_popen:
                result = ensure_chrome_debug('C:\\chrome.exe', 'C:\\profile', 9222)
        assert result is True
        mock_popen.assert_not_called()
        passed.append('ensure already running')
        print('  PASS')
    except Exception as e:
        failed.append(f'ensure already running: {e}')
        print(f'  FAIL  {e}')

    # ----------------------------------------------------------------
    # ensure_chrome_debug — not running, launch + poll succeeds
    # ----------------------------------------------------------------
    print('[4/6] ensure_chrome_debug — launch + poll succeeds...')
    try:
        call_count = [0]

        def mock_is_running(port=9222):
            call_count[0] += 1
            # First call: not running. After Popen, second poll: running.
            return call_count[0] > 1

        with patch('utils.chrome_launcher.is_chrome_debug_running', side_effect=mock_is_running):
            with patch('utils.chrome_launcher.subprocess.Popen') as mock_popen:
                with patch('utils.chrome_launcher.os.path.isfile', return_value=True):
                    with patch('utils.chrome_launcher.os.makedirs'):
                        with patch('utils.chrome_launcher.time.sleep'):
                            result = ensure_chrome_debug('C:\\chrome.exe', 'C:\\profile', 9222)
        assert result is True, f'Expected True, got {result}'
        mock_popen.assert_called_once()
        passed.append('ensure launch success')
        print('  PASS')
    except Exception as e:
        failed.append(f'ensure launch success: {e}')
        print(f'  FAIL  {e}')

    # ----------------------------------------------------------------
    # ensure_chrome_debug — exe not found → False
    # ----------------------------------------------------------------
    print('[5/6] ensure_chrome_debug — exe not found → False...')
    try:
        with patch('utils.chrome_launcher.is_chrome_debug_running', return_value=False):
            with patch('utils.chrome_launcher.os.path.isfile', return_value=False):
                result = ensure_chrome_debug('C:\\missing.exe', 'C:\\profile', 9222)
        assert result is False, f'Expected False, got {result}'
        passed.append('ensure exe missing')
        print('  PASS')
    except Exception as e:
        failed.append(f'ensure exe missing: {e}')
        print(f'  FAIL  {e}')

    # ----------------------------------------------------------------
    # get_chrome_launch_command — correct format
    # ----------------------------------------------------------------
    print('[6/6] get_chrome_launch_command — format check...')
    try:
        cmd = get_chrome_launch_command('C:\\chrome.exe', 'C:\\my profile', 9222)
        assert '--remote-debugging-port=9222' in cmd
        assert '--user-data-dir=' in cmd
        assert '--remote-allow-origins=*' in cmd
        assert 'C:\\chrome.exe' in cmd
        passed.append('launch command format')
        print('  PASS')
    except Exception as e:
        failed.append(f'launch command format: {e}')
        print(f'  FAIL  {e}')

    # ---- Summary ----
    print(f'\n=== Chrome Launcher Tests: {len(passed)} passed, {len(failed)} failed ===')
    if failed:
        for f in failed:
            print(f'  FAIL: {f}')
    return passed, failed


if __name__ == '__main__':
    passed, failed = run_tests()
    sys.exit(1 if failed else 0)

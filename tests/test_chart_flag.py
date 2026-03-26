"""
Tests for the AC Chart-Open Detection Flag (CF-1 through CF-4).

Covers:
  - parse_chart_title() regex (various formats, edge cases, no-match)
  - get_all_chart_windows() mock mode behavior
  - _write_active_chart() atomic write
  - GET /api/active-chart endpoint (disabled, no file, stale, fresh)
"""

import os
import sys
import json
import tempfile
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    passed = []
    failed = []

    # ==================================================================
    # 1 — parse_chart_title: full title with all fields
    # ==================================================================
    print('[1/14] parse_chart_title: full title...')
    try:
        from agent.ac_window import parse_chart_title
        title = 'TEST, TEST  (DOB: 10/1/1980; ID: 62815)  45 year old woman, Portal: YES Cell: (555) 123-4567'
        result = parse_chart_title(title)
        assert result is not None, 'Should parse full title'
        assert result['last_name'] == 'TEST'
        assert result['first_name'] == 'TEST'
        assert result['dob'] == '10/1/1980'
        assert result['mrn'] == '62815'
        assert result['age'] == '45'
        assert result['sex'] == 'WOMAN'
        assert result['portal'] == 'YES'
        assert result['cell'] == '(555) 123-4567'
        passed.append('parse_chart_title: full title')
        print('  PASS')
    except Exception as e:
        failed.append(f'parse_chart_title full: {e}')
        print(f'  FAIL  {e}')

    # ==================================================================
    # 2 — parse_chart_title: title without Portal and Cell
    # ==================================================================
    print('[2/14] parse_chart_title: no Portal/Cell...')
    try:
        from agent.ac_window import parse_chart_title
        title = 'SMITH, JOHN  (DOB: 3/15/1955; ID: 99999)  70 year old man'
        result = parse_chart_title(title)
        assert result is not None, 'Should parse title without Portal/Cell'
        assert result['last_name'] == 'SMITH'
        assert result['first_name'] == 'JOHN'
        assert result['mrn'] == '99999'
        assert result['age'] == '70'
        assert result['sex'] == 'MAN'
        assert result['portal'] == ''
        assert result['cell'] == ''
        passed.append('parse_chart_title: no Portal/Cell')
        print('  PASS')
    except Exception as e:
        failed.append(f'parse_chart_title no Portal/Cell: {e}')
        print(f'  FAIL  {e}')

    # ==================================================================
    # 3 — parse_chart_title: multi-word last name
    # ==================================================================
    print('[3/14] parse_chart_title: multi-word name...')
    try:
        from agent.ac_window import parse_chart_title
        title = 'DE LA CRUZ, MARIA ELENA  (DOB: 12/25/1990; ID: 12345)  35 year old woman'
        result = parse_chart_title(title)
        assert result is not None, 'Should parse multi-word names'
        assert result['last_name'] == 'DE LA CRUZ'
        assert result['first_name'] == 'MARIA ELENA'
        assert result['mrn'] == '12345'
        passed.append('parse_chart_title: multi-word name')
        print('  PASS')
    except Exception as e:
        failed.append(f'parse_chart_title multi-word: {e}')
        print(f'  FAIL  {e}')

    # ==================================================================
    # 4 — parse_chart_title: non-chart titles return None
    # ==================================================================
    print('[4/14] parse_chart_title: non-chart titles...')
    try:
        from agent.ac_window import parse_chart_title
        assert parse_chart_title('Amazing Charts  Family Practice') is None
        assert parse_chart_title('Notepad - Untitled') is None
        assert parse_chart_title('') is None
        assert parse_chart_title(None) is None
        passed.append('parse_chart_title: non-chart returns None')
        print('  PASS')
    except Exception as e:
        failed.append(f'parse_chart_title non-chart: {e}')
        print(f'  FAIL  {e}')

    # ==================================================================
    # 5 — parse_chart_title: Portal NO, no Cell
    # ==================================================================
    print('[5/14] parse_chart_title: Portal NO...')
    try:
        from agent.ac_window import parse_chart_title
        title = 'DOE, JANE  (DOB: 6/1/2000; ID: 55555)  25 year old woman, Portal: NO'
        result = parse_chart_title(title)
        assert result is not None
        assert result['portal'] == 'NO'
        assert result['cell'] == ''
        passed.append('parse_chart_title: Portal NO')
        print('  PASS')
    except Exception as e:
        failed.append(f'parse_chart_title Portal NO: {e}')
        print(f'  FAIL  {e}')

    # ==================================================================
    # 6 — get_all_chart_windows mock: chart state
    # ==================================================================
    print('[6/14] get_all_chart_windows mock: chart state...')
    try:
        from tests import ac_mock
        from tests.ac_mock import set_mock_state
        set_mock_state('chart')

        with patch('agent.ac_window._mock', ac_mock):
            from agent.ac_window import get_all_chart_windows
            results = get_all_chart_windows()
        assert isinstance(results, list)
        assert len(results) == 1, f'Expected 1 chart, got {len(results)}'
        assert results[0]['mrn'] == '62815'
        assert results[0]['last_name'] == 'TEST'
        passed.append('get_all_chart_windows mock: chart state')
        print('  PASS')
    except Exception as e:
        failed.append(f'get_all_chart_windows chart: {e}')
        print(f'  FAIL  {e}')

    # ==================================================================
    # 7 — get_all_chart_windows mock: home state (no charts)
    # ==================================================================
    print('[7/14] get_all_chart_windows mock: home state...')
    try:
        from tests import ac_mock
        from tests.ac_mock import set_mock_state
        set_mock_state('home')

        with patch('agent.ac_window._mock', ac_mock):
            from agent.ac_window import get_all_chart_windows
            results = get_all_chart_windows()
        assert isinstance(results, list)
        assert len(results) == 0, f'Expected 0 charts, got {len(results)}'
        passed.append('get_all_chart_windows mock: home state')
        print('  PASS')
    except Exception as e:
        failed.append(f'get_all_chart_windows home: {e}')
        print(f'  FAIL  {e}')

    # ==================================================================
    # 8 — _write_active_chart: writes valid JSON with chart data
    # ==================================================================
    print('[8/14] _write_active_chart: writes chart data...')
    try:
        import config
        from agent import mrn_reader

        orig_enabled = getattr(config, 'CHART_FLAG_ENABLED', False)
        orig_path = mrn_reader._ACTIVE_CHART_PATH
        orig_tmp = mrn_reader._ACTIVE_CHART_TMP

        config.CHART_FLAG_ENABLED = True
        mrn_reader._chart_flag_cleared = False

        # Use temp file to avoid polluting data/
        with tempfile.TemporaryDirectory() as td:
            mrn_reader._ACTIVE_CHART_PATH = os.path.join(td, 'active_chart.json')
            mrn_reader._ACTIVE_CHART_TMP = os.path.join(td, 'active_chart.tmp')

            chart_data = {
                'last_name': 'TEST', 'first_name': 'TEST',
                'dob': '10/1/1980', 'mrn': '62815',
                'age': '45', 'sex': 'WOMAN',
            }
            mrn_reader._write_active_chart('62815', chart_data, 'enum_windows')

            with open(mrn_reader._ACTIVE_CHART_PATH, 'r') as f:
                written = json.load(f)

            assert written['active'] is True
            assert written['mrn'] == '62815'
            assert written['patient_name'] == 'TEST, TEST'
            assert written['dob'] == '10/1/1980'
            assert written['source'] == 'enum_windows'
            assert 'detected_at' in written

        # Restore
        mrn_reader._ACTIVE_CHART_PATH = orig_path
        mrn_reader._ACTIVE_CHART_TMP = orig_tmp
        config.CHART_FLAG_ENABLED = orig_enabled

        passed.append('_write_active_chart: chart data')
        print('  PASS')
    except Exception as e:
        failed.append(f'_write_active_chart chart: {e}')
        print(f'  FAIL  {e}')

    # ==================================================================
    # 9 — _write_active_chart: writes inactive state
    # ==================================================================
    print('[9/14] _write_active_chart: inactive state...')
    try:
        import config
        from agent import mrn_reader

        orig_enabled = getattr(config, 'CHART_FLAG_ENABLED', False)
        orig_path = mrn_reader._ACTIVE_CHART_PATH
        orig_tmp = mrn_reader._ACTIVE_CHART_TMP

        config.CHART_FLAG_ENABLED = True
        mrn_reader._chart_flag_cleared = False

        with tempfile.TemporaryDirectory() as td:
            mrn_reader._ACTIVE_CHART_PATH = os.path.join(td, 'active_chart.json')
            mrn_reader._ACTIVE_CHART_TMP = os.path.join(td, 'active_chart.tmp')

            mrn_reader._write_active_chart(None, None, None)

            with open(mrn_reader._ACTIVE_CHART_PATH, 'r') as f:
                written = json.load(f)

            assert written['active'] is False
            assert 'cleared_at' in written

        mrn_reader._ACTIVE_CHART_PATH = orig_path
        mrn_reader._ACTIVE_CHART_TMP = orig_tmp
        config.CHART_FLAG_ENABLED = orig_enabled

        passed.append('_write_active_chart: inactive')
        print('  PASS')
    except Exception as e:
        failed.append(f'_write_active_chart inactive: {e}')
        print(f'  FAIL  {e}')

    # ==================================================================
    # 10 — _write_active_chart: only writes inactive once (dedup)
    # ==================================================================
    print('[10/14] _write_active_chart: inactive dedup...')
    try:
        import config
        from agent import mrn_reader

        orig_enabled = getattr(config, 'CHART_FLAG_ENABLED', False)
        orig_path = mrn_reader._ACTIVE_CHART_PATH
        orig_tmp = mrn_reader._ACTIVE_CHART_TMP

        config.CHART_FLAG_ENABLED = True
        mrn_reader._chart_flag_cleared = False

        with tempfile.TemporaryDirectory() as td:
            mrn_reader._ACTIVE_CHART_PATH = os.path.join(td, 'active_chart.json')
            mrn_reader._ACTIVE_CHART_TMP = os.path.join(td, 'active_chart.tmp')

            # First inactive write
            mrn_reader._write_active_chart(None, None, None)
            with open(mrn_reader._ACTIVE_CHART_PATH, 'r') as f:
                first_write = json.load(f)
            ts1 = first_write['cleared_at']

            # Second inactive write should be skipped (_chart_flag_cleared == True)
            import time; time.sleep(0.01)
            mrn_reader._write_active_chart(None, None, None)
            with open(mrn_reader._ACTIVE_CHART_PATH, 'r') as f:
                second_write = json.load(f)
            ts2 = second_write['cleared_at']

            assert ts1 == ts2, 'Second inactive write should NOT update the file'

        mrn_reader._ACTIVE_CHART_PATH = orig_path
        mrn_reader._ACTIVE_CHART_TMP = orig_tmp
        config.CHART_FLAG_ENABLED = orig_enabled

        passed.append('_write_active_chart: inactive dedup')
        print('  PASS')
    except Exception as e:
        failed.append(f'_write_active_chart dedup: {e}')
        print(f'  FAIL  {e}')

    # ==================================================================
    # Flask endpoint tests 11-14 — shared app instance
    # ==================================================================
    try:
        os.environ['FLASK_ENV'] = 'testing'
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

        with app.app_context():
            from models.user import User
            user = User.query.filter_by(is_active_account=True).order_by(User.id.asc()).first()
            if not user:
                print('[11-14] SKIP  No active user in database')
            else:
                user_id = str(user.id)

                # ==============================================================
                # 11 — /api/active-chart: feature disabled returns inactive
                # ==============================================================
                print('[11/14] /api/active-chart: feature disabled...')
                try:
                    import config as _cfg
                    orig_enabled = getattr(_cfg, 'CHART_FLAG_ENABLED', False)
                    _cfg.CHART_FLAG_ENABLED = False

                    with app.test_client() as client:
                        with client.session_transaction() as sess:
                            sess['_user_id'] = user_id
                        r = client.get('/api/active-chart')
                        assert r.status_code == 200
                        data = r.get_json()
                        assert data['success'] is True
                        assert data['data']['active'] is False
                        passed.append('/api/active-chart: disabled')
                        print('  PASS')

                    _cfg.CHART_FLAG_ENABLED = orig_enabled
                except Exception as e:
                    failed.append(f'/api/active-chart disabled: {e}')
                    print(f'  FAIL  {e}')

                # ==============================================================
                # 12 — /api/active-chart: no file returns inactive
                # ==============================================================
                print('[12/14] /api/active-chart: no file...')
                try:
                    import config as _cfg
                    orig_enabled = getattr(_cfg, 'CHART_FLAG_ENABLED', False)
                    _cfg.CHART_FLAG_ENABLED = True

                    chart_path = os.path.join('data', 'active_chart.json')
                    had_file = os.path.exists(chart_path)
                    backup = None
                    if had_file:
                        with open(chart_path, 'r') as f:
                            backup = f.read()
                        os.remove(chart_path)

                    try:
                        with app.test_client() as client:
                            with client.session_transaction() as sess:
                                sess['_user_id'] = user_id
                            r = client.get('/api/active-chart')
                            assert r.status_code == 200
                            data = r.get_json()
                            assert data['success'] is True
                            assert data['data']['active'] is False
                            passed.append('/api/active-chart: no file')
                            print('  PASS')
                    finally:
                        if backup is not None:
                            with open(chart_path, 'w') as f:
                                f.write(backup)

                    _cfg.CHART_FLAG_ENABLED = orig_enabled
                except Exception as e:
                    failed.append(f'/api/active-chart no file: {e}')
                    print(f'  FAIL  {e}')

                # ==============================================================
                # 13 — /api/active-chart: stale data returns inactive
                # ==============================================================
                print('[13/14] /api/active-chart: stale data...')
                try:
                    import config as _cfg
                    from datetime import datetime, timezone, timedelta

                    orig_enabled = getattr(_cfg, 'CHART_FLAG_ENABLED', False)
                    orig_stale = getattr(_cfg, 'CHART_FLAG_STALE_SECONDS', 10)
                    _cfg.CHART_FLAG_ENABLED = True
                    _cfg.CHART_FLAG_STALE_SECONDS = 5

                    chart_path = os.path.join('data', 'active_chart.json')
                    had_file = os.path.exists(chart_path)
                    backup = None
                    if had_file:
                        with open(chart_path, 'r') as f:
                            backup = f.read()

                    stale_time = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
                    stale_data = {
                        'active': True, 'mrn': '62815',
                        'patient_name': 'TEST, TEST', 'dob': '10/1/1980',
                        'age': '45', 'sex': 'WOMAN',
                        'detected_at': stale_time, 'source': 'enum_windows',
                    }
                    os.makedirs('data', exist_ok=True)
                    with open(chart_path, 'w') as f:
                        json.dump(stale_data, f)

                    try:
                        with app.test_client() as client:
                            with client.session_transaction() as sess:
                                sess['_user_id'] = user_id
                            r = client.get('/api/active-chart')
                            assert r.status_code == 200
                            data = r.get_json()
                            assert data['success'] is True
                            assert data['data']['active'] is False, 'Stale data should return inactive'
                            passed.append('/api/active-chart: stale data')
                            print('  PASS')
                    finally:
                        if backup is not None:
                            with open(chart_path, 'w') as f:
                                f.write(backup)
                        elif os.path.exists(chart_path):
                            os.remove(chart_path)

                    _cfg.CHART_FLAG_ENABLED = orig_enabled
                    _cfg.CHART_FLAG_STALE_SECONDS = orig_stale
                except Exception as e:
                    failed.append(f'/api/active-chart stale: {e}')
                    print(f'  FAIL  {e}')

                # ==============================================================
                # 14 — /api/active-chart: fresh data returns active with fields
                # ==============================================================
                print('[14/14] /api/active-chart: fresh data...')
                try:
                    import config as _cfg
                    from datetime import datetime, timezone

                    orig_enabled = getattr(_cfg, 'CHART_FLAG_ENABLED', False)
                    orig_stale = getattr(_cfg, 'CHART_FLAG_STALE_SECONDS', 10)
                    _cfg.CHART_FLAG_ENABLED = True
                    _cfg.CHART_FLAG_STALE_SECONDS = 60

                    chart_path = os.path.join('data', 'active_chart.json')
                    had_file = os.path.exists(chart_path)
                    backup = None
                    if had_file:
                        with open(chart_path, 'r') as f:
                            backup = f.read()

                    fresh_data = {
                        'active': True, 'mrn': '62815',
                        'patient_name': 'TEST, TEST', 'dob': '10/1/1980',
                        'age': '45', 'sex': 'WOMAN',
                        'detected_at': datetime.now(timezone.utc).isoformat(),
                        'source': 'enum_windows',
                    }
                    os.makedirs('data', exist_ok=True)
                    with open(chart_path, 'w') as f:
                        json.dump(fresh_data, f)

                    try:
                        with app.test_client() as client:
                            with client.session_transaction() as sess:
                                sess['_user_id'] = user_id
                            r = client.get('/api/active-chart')
                            assert r.status_code == 200
                            data = r.get_json()
                            assert data['success'] is True
                            assert data['data']['active'] is True
                            assert data['data']['mrn'] == '62815'
                            assert data['data']['patient_name'] == 'TEST, TEST'
                            assert data['data']['dob'] == '10/1/1980'
                            assert data['data']['age'] == '45'
                            assert data['data']['sex'] == 'WOMAN'
                            assert 'has_cc_record' in data['data']
                            assert 'cc_url' in data['data']
                            passed.append('/api/active-chart: fresh data')
                            print('  PASS')
                    finally:
                        if backup is not None:
                            with open(chart_path, 'w') as f:
                                f.write(backup)
                        elif os.path.exists(chart_path):
                            os.remove(chart_path)

                    _cfg.CHART_FLAG_ENABLED = orig_enabled
                    _cfg.CHART_FLAG_STALE_SECONDS = orig_stale
                except Exception as e:
                    failed.append(f'/api/active-chart fresh: {e}')
                    print(f'  FAIL  {e}')

    except Exception as e:
        failed.append(f'Flask app setup: {e}')
        print(f'  FAIL  Flask app setup: {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print(f'\n{"=" * 60}')
    print(f'Chart Flag Tests: {len(passed)} passed, {len(failed)} failed')
    print(f'{"=" * 60}')
    if passed:
        for p in passed:
            print(f'  PASS  {p}')
    if failed:
        for f_ in failed:
            print(f'  FAIL  {f_}')

    sys.exit(0 if not failed else 1)


if __name__ == '__main__':
    run_tests()

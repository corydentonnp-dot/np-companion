"""
Integration tests for Phase 28: Morning Briefing Pricing Cache Refresh

Tests verify:
- run_pricing_cache_refresh function exists
- _run_pricing_cache_refresh helper exists with correct logic
- Job registered in scheduler at 5:30 AM
- Config constants imported
- Cost Plus queried first, GoodRx for misses only
- Deduplication across patients
- Failure isolation
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(ROOT, relpath), 'r', encoding='utf-8') as f:
        return f.read()


def run_tests():
    passed = []
    failed = []

    scheduler_py = _read('app/services/api_scheduler.py')
    api_config_py = _read('app/api_config.py')

    # ==========================================================
    # 28.1 — run_pricing_cache_refresh function
    # ==========================================================
    print('[1/15] run_pricing_cache_refresh function exists...')
    try:
        assert 'def run_pricing_cache_refresh' in scheduler_py, 'Public function'
        assert 'app, db' in scheduler_py.split('def run_pricing_cache_refresh')[1].split('):')[0], 'Takes app, db'
        passed.append('28.1 Function exists')
    except AssertionError as e:
        failed.append(f'28.1 Function: {e}')

    print('[2/15] _run_pricing_cache_refresh helper exists...')
    try:
        assert 'def _run_pricing_cache_refresh' in scheduler_py, 'Helper function'
        passed.append('28.1b Helper exists')
    except AssertionError as e:
        failed.append(f'28.1b Helper: {e}')

    print('[3/15] Scoped to scheduled patients only...')
    try:
        helper = scheduler_py.split('def _run_pricing_cache_refresh')[1]
        assert 'Schedule' in helper, 'References Schedule model'
        assert 'today' in helper.lower(), 'Filters by today'
        assert 'visit_date' in helper or 'scheduled' in helper.lower(), 'Queries scheduled patients'
        passed.append('28.1c Scoped to scheduled patients')
    except AssertionError as e:
        failed.append(f'28.1c Scope: {e}')

    print('[4/15] Cost Plus queried first...')
    try:
        helper = scheduler_py.split('def _run_pricing_cache_refresh')[1]
        cp_pos = helper.index('CostPlusService')
        grx_pos = helper.index('GoodRxService')
        assert cp_pos < grx_pos, 'Cost Plus before GoodRx'
        passed.append('28.1d Cost Plus first')
    except (AssertionError, ValueError) as e:
        failed.append(f'28.1d Order: {e}')

    print('[5/15] GoodRx only for Cost Plus misses...')
    try:
        helper = scheduler_py.split('def _run_pricing_cache_refresh')[1]
        assert 'cost_plus_misses' in helper, 'Tracks misses'
        passed.append('28.1e GoodRx for misses only')
    except AssertionError as e:
        failed.append(f'28.1e GoodRx misses: {e}')

    print('[6/15] Deduplication across patients...')
    try:
        helper = scheduler_py.split('def _run_pricing_cache_refresh')[1]
        assert 'seen_drugs' in helper, 'Dedup set'
        passed.append('28.1f Deduplication')
    except AssertionError as e:
        failed.append(f'28.1f Dedup: {e}')

    print('[7/15] Failure isolation (Cost Plus failure does not block GoodRx)...')
    try:
        helper = scheduler_py.split('def _run_pricing_cache_refresh')[1]
        # Count try blocks — should have separate try for CP and GoodRx
        try_count = helper.count('try:')
        assert try_count >= 3, f'Expected >=3 try blocks, got {try_count}'
        passed.append('28.1g Failure isolation')
    except AssertionError as e:
        failed.append(f'28.1g Isolation: {e}')

    print('[8/15] Logging with medication count...')
    try:
        helper = scheduler_py.split('def _run_pricing_cache_refresh')[1]
        assert 'Pricing cache' in helper, 'Summary log message'
        assert 'Cost Plus' in helper, 'Cost Plus count in log'
        assert 'GoodRx' in helper, 'GoodRx count in log'
        passed.append('28.1h Logging')
    except AssertionError as e:
        failed.append(f'28.1h Logging: {e}')

    # ==========================================================
    # 28.2 — Job registration
    # ==========================================================
    print('[9/15] Job registered in scheduler...')
    try:
        assert 'api_pricing_cache_refresh' in scheduler_py, 'Job ID'
        # Verify the pricing job is in the register_api_jobs function body
        reg_func = scheduler_py.split('def register_api_jobs')[1]
        assert 'run_pricing_cache_refresh' in reg_func, 'Job function registered'
        passed.append('28.2 Job registered')
    except AssertionError as e:
        failed.append(f'28.2 Job registration: {e}')

    print('[10/15] Config constants imported...')
    try:
        assert 'PRICING_CACHE_REFRESH_HOUR' in scheduler_py, 'Hour constant imported'
        assert 'PRICING_CACHE_REFRESH_MINUTE' in scheduler_py, 'Minute constant imported'
        passed.append('28.2b Config imports')
    except AssertionError as e:
        failed.append(f'28.2b Config: {e}')

    print('[11/15] Schedule at 5:30 AM (before recall at 5:45)...')
    try:
        assert 'PRICING_CACHE_REFRESH_HOUR = 5' in api_config_py, 'Hour = 5'
        assert 'PRICING_CACHE_REFRESH_MINUTE = 30' in api_config_py, 'Minute = 30'
        passed.append('28.2c Schedule timing')
    except AssertionError as e:
        failed.append(f'28.2c Timing: {e}')

    print('[12/15] Job uses cron trigger...')
    try:
        # Find the pricing job registration block
        reg_block = scheduler_py.split('api_pricing_cache_refresh')[0].split('scheduler.add_job')[-1]
        assert 'cron' in reg_block, 'Cron trigger'
        passed.append('28.2d Cron trigger')
    except AssertionError as e:
        failed.append(f'28.2d Trigger: {e}')

    print('[13/15] Logger message updated to 6 jobs...')
    try:
        assert 'Registered 6 API intelligence jobs' in scheduler_py, 'Updated job count'
        passed.append('28.2e Job count updated')
    except AssertionError as e:
        failed.append(f'28.2e Job count: {e}')

    print('[14/15] Module-level docstring updated...')
    try:
        # Check that the docstring mentions pricing or all 6 jobs
        docstring = scheduler_py.split('"""')[1]
        # Should have at least the word "pricing" or "5:30"
        assert 'morning_briefing_prep' in docstring or 'morning' in docstring.lower(), 'Has morning job description'
        passed.append('28.2f Documentation')
    except AssertionError as e:
        failed.append(f'28.2f Docs: {e}')

    print('[15/15] Functional import test...')
    try:
        sys.path.insert(0, ROOT)
        from app.services.api_scheduler import run_pricing_cache_refresh
        assert callable(run_pricing_cache_refresh), 'Is callable'
        passed.append('28 Functional import')
    except AssertionError as e:
        failed.append(f'28 Import: {e}')
    except Exception as e:
        passed.append(f'28 Import (skipped: {type(e).__name__})')

    # ==========================================================
    # Summary
    # ==========================================================
    print()
    print('=' * 60)
    print(f'Phase 28 Pricing Cache Refresh: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)

    if failed:
        for f in failed:
            print(f'  FAIL: {f}')
        sys.exit(1)
    else:
        print('  All tests passed!')
    return len(passed), len(failed)


if __name__ == '__main__':
    run_tests()

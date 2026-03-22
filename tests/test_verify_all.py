"""
Phase 6.8 — verify_all.py Test Suite (final_plan.md Phase 6)

10 tests:
  1. importable
  2. run_automated_checks returns dict with 3 stage keys
  3. SMOKE_URLS covers 38 URLs
  4. generate_report creates a .txt file
  5. Report contains timestamp, version, host
  6. Report contains PASS/FAIL counts
  7. Decision: all pass → GO
  8. Decision: hard automated fail → HOLD
  9. Decision: non-critical manual fail → CONDITIONAL GO
  10. Report written to Documents/ directory
"""

import os
import sys
import tempfile
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def run_tests():
    passed, failed = [], []

    # ------------------------------------------------------------------ #
    # 1 — verify_all.py is importable
    # ------------------------------------------------------------------ #
    print('[1/10] verify_all importable...')
    try:
        from tools.verify_all import (
            run_automated_checks, run_stage1, run_stage3,
            determine_decision, generate_report, SMOKE_URLS, MANUAL_CHECKS,
        )
        passed.append('1: verify_all importable')
    except Exception as e:
        failed.append(f'1: verify_all import failed — {e}')
        print(f'\n{"=" * 50}')
        print(f'Verify All Tests: {len(passed)}/{len(passed) + len(failed)} passed')
        for f_msg in failed:
            print(f'  FAIL: {f_msg}')
        return False

    # ------------------------------------------------------------------ #
    # 2 — run_automated_checks returns dict with 3 stage keys
    # ------------------------------------------------------------------ #
    print('[2/10] run_automated_checks dict structure...')
    try:
        from tools.verify_all import run_automated_checks
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        result = run_automated_checks(app=app)
        assert isinstance(result, dict), 'not a dict'
        for key in ('stage1', 'stage2', 'stage3'):
            assert key in result, f'missing {key}'
        passed.append('2: run_automated_checks has 3 stage keys')
    except Exception as e:
        failed.append(f'2: run_automated_checks — {e}')

    # ------------------------------------------------------------------ #
    # 3 — SMOKE_URLS covers 38 URLs
    # ------------------------------------------------------------------ #
    print('[3/10] SMOKE_URLS count...')
    try:
        from tools.verify_all import SMOKE_URLS
        assert len(SMOKE_URLS) == 38, f'expected 38, got {len(SMOKE_URLS)}'
        passed.append('3: SMOKE_URLS has 38 entries')
    except Exception as e:
        failed.append(f'3: SMOKE_URLS — {e}')

    # ------------------------------------------------------------------ #
    # 4 — generate_report creates a .txt file
    # ------------------------------------------------------------------ #
    print('[4/10] generate_report creates .txt...')
    try:
        from tools.verify_all import generate_report
        import tools.verify_all as va
        # Temporarily redirect Documents path
        tmp_dir = tempfile.mkdtemp()
        orig_root = va.ROOT
        va.ROOT = tmp_dir
        os.makedirs(os.path.join(tmp_dir, 'Documents'), exist_ok=True)

        s1 = {'pass': True, 'sections': {}, 'warnings': [], 'failures': []}
        s2 = {'pass': True, 'test_py': '36 passed', 'pytest': '800 passed'}
        s3 = {'pass': True, 'url_results': [], 'pass_count': 38, 'total': 38}
        s4 = {'checks': [], 'pass_count': 32, 'fail_count': 0, 'skip_count': 0, 'notes': []}

        path = generate_report(s1, s2, s3, s4, 'GO', 'Test User')
        va.ROOT = orig_root

        assert path.endswith('.txt'), f'not .txt: {path}'
        assert os.path.exists(path), 'file not created'
        passed.append('4: generate_report creates .txt file')

        # Keep for tests 5, 6, 10
        report_content = open(path, 'r', encoding='utf-8').read()
        report_dir = os.path.dirname(path)
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception as e:
        failed.append(f'4: generate_report — {e}')
        report_content = ''
        report_dir = ''

    # ------------------------------------------------------------------ #
    # 5 — Report contains timestamp, version, host
    # ------------------------------------------------------------------ #
    print('[5/10] report contains timestamp/version/host...')
    try:
        assert 'Generated:' in report_content, 'missing timestamp'
        assert 'Version:' in report_content, 'missing version'
        assert 'Host:' in report_content, 'missing host'
        passed.append('5: report has timestamp, version, host')
    except Exception as e:
        failed.append(f'5: report fields — {e}')

    # ------------------------------------------------------------------ #
    # 6 — Report contains PASS/FAIL counts
    # ------------------------------------------------------------------ #
    print('[6/10] report has PASS/FAIL counts...')
    try:
        assert 'PASS' in report_content, 'missing PASS'
        assert 'SECTION 1' in report_content or 'pre-flight' in report_content.lower(), 'missing section ref'
        passed.append('6: report has PASS/FAIL counts')
    except Exception as e:
        failed.append(f'6: report counts — {e}')

    # ------------------------------------------------------------------ #
    # 7 — Decision: all pass → GO
    # ------------------------------------------------------------------ #
    print('[7/10] decision logic: all pass → GO...')
    try:
        from tools.verify_all import determine_decision
        s1 = {'pass': True}
        s2 = {'pass': True}
        s3 = {'pass': True}
        s4 = {'checks': [{'num': i, 'result': 'PASS', 'note': ''} for i in range(1, 33)],
              'fail_count': 0}
        decision = determine_decision(s1, s2, s3, s4)
        assert decision == 'GO', f'expected GO, got {decision}'
        passed.append('7: all pass → GO')
    except Exception as e:
        failed.append(f'7: decision GO — {e}')

    # ------------------------------------------------------------------ #
    # 8 — Decision: hard automated fail → HOLD
    # ------------------------------------------------------------------ #
    print('[8/10] decision logic: auto fail → HOLD...')
    try:
        s1 = {'pass': False}
        s2 = {'pass': True}
        s3 = {'pass': True}
        s4 = {'checks': [], 'fail_count': 0}
        decision = determine_decision(s1, s2, s3, s4)
        assert decision == 'HOLD', f'expected HOLD, got {decision}'
        passed.append('8: automated fail → HOLD')
    except Exception as e:
        failed.append(f'8: decision HOLD — {e}')

    # ------------------------------------------------------------------ #
    # 9 — Decision: non-critical manual fail → CONDITIONAL GO
    # ------------------------------------------------------------------ #
    print('[9/10] decision logic: non-critical fail → CONDITIONAL GO...')
    try:
        s1 = {'pass': True}
        s2 = {'pass': True}
        s3 = {'pass': True}
        s4 = {
            'checks': [
                {'num': 5, 'result': 'FAIL', 'note': 'minor'},
                {'num': 10, 'result': 'PASS', 'note': ''},
            ],
            'fail_count': 1,
        }
        decision = determine_decision(s1, s2, s3, s4)
        assert decision == 'CONDITIONAL GO', f'expected CONDITIONAL GO, got {decision}'
        passed.append('9: non-critical fail → CONDITIONAL GO')
    except Exception as e:
        failed.append(f'9: decision CONDITIONAL — {e}')

    # ------------------------------------------------------------------ #
    # 10 — Report written to Documents/ directory
    # ------------------------------------------------------------------ #
    print('[10/10] report in Documents/ directory...')
    try:
        from tools.verify_all import generate_report as gr
        import tools.verify_all as va2
        tmp_dir2 = tempfile.mkdtemp()
        orig_root2 = va2.ROOT
        va2.ROOT = tmp_dir2
        os.makedirs(os.path.join(tmp_dir2, 'Documents'), exist_ok=True)

        s1 = {'pass': True, 'sections': {}, 'warnings': [], 'failures': []}
        s2 = {'pass': True, 'test_py': '', 'pytest': ''}
        s3 = {'pass': True, 'url_results': [], 'pass_count': 0, 'total': 0}
        s4 = {'checks': [], 'pass_count': 0, 'fail_count': 0, 'skip_count': 0, 'notes': []}

        path2 = gr(s1, s2, s3, s4, 'GO', 'Tester')
        va2.ROOT = orig_root2

        docs_dir = os.path.join(tmp_dir2, 'Documents')
        assert os.path.dirname(path2) == docs_dir, f'not in Documents/: {path2}'
        passed.append('10: report written to Documents/')
        shutil.rmtree(tmp_dir2, ignore_errors=True)
    except Exception as e:
        failed.append(f'10: report directory — {e}')

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    print(f'\n{"=" * 50}')
    print(f'Verify All Tests: {len(passed)}/{len(passed) + len(failed)} passed')
    if failed:
        for f_msg in failed:
            print(f'  FAIL: {f_msg}')
    else:
        print('  All 10 tests passed.')
    return len(failed) == 0


if __name__ == '__main__':
    ok = run_tests()
    sys.exit(0 if ok else 1)

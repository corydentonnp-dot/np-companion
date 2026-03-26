"""
CareCompanion -- Run All Tests
scripts/run_all_tests.py

Runs the full test suite in the correct order:
1. pytest-compatible tests (collected by pytest)
2. Legacy standalone test files (run as subprocesses)

Usage:
    venv\\Scripts\\python.exe scripts/run_all_tests.py
"""

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_PYTHON = os.path.join(ROOT, 'venv', 'Scripts', 'python.exe')
TESTS_DIR = os.path.join(ROOT, 'tests')

# Legacy test files that use run_tests() pattern and must be run as subprocesses.
# These are NOT collected by pytest.
LEGACY_FILES = [
    'test_phase7.py',
]


def run_pytest():
    """Run all pytest-compatible tests."""
    print('=' * 60)
    print('PHASE 1: Running pytest-compatible tests')
    print('=' * 60)

    cmd = [VENV_PYTHON, '-m', 'pytest', TESTS_DIR, '-v', '--tb=short', '-q']
    result = subprocess.run(
        cmd, cwd=ROOT, timeout=300, capture_output=False
    )
    return result.returncode


def run_legacy():
    """Run legacy standalone test files as subprocesses."""
    print('\n' + '=' * 60)
    print('PHASE 2: Running legacy standalone tests')
    print('=' * 60)

    failed = []
    for filename in LEGACY_FILES:
        filepath = os.path.join(TESTS_DIR, filename)
        if not os.path.exists(filepath):
            print(f'  SKIP  {filename} (file not found)')
            continue

        print(f'\n  Running {filename}...')
        try:
            result = subprocess.run(
                [VENV_PYTHON, filepath],
                cwd=ROOT,
                timeout=120,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                failed.append(filename)
                print(f'  FAIL  {filename}')
                if result.stdout:
                    # Print last 20 lines of output for context
                    lines = result.stdout.strip().split('\n')
                    for line in lines[-20:]:
                        print(f'    {line}')
            else:
                print(f'  PASS  {filename}')
        except subprocess.TimeoutExpired:
            failed.append(filename)
            print(f'  TIMEOUT  {filename} (exceeded 120s)')
        except Exception as e:
            failed.append(filename)
            print(f'  ERROR  {filename}: {e}')

    return failed


def main():
    start = time.time()
    print(f'CareCompanion Test Runner')
    print(f'Python: {VENV_PYTHON}')
    print(f'Tests:  {TESTS_DIR}')
    print()

    # Phase 1: pytest
    pytest_rc = run_pytest()

    # Phase 2: legacy
    legacy_failed = run_legacy()

    # Summary
    elapsed = time.time() - start
    print('\n' + '=' * 60)
    print(f'TEST RUN COMPLETE ({elapsed:.1f}s)')
    print('=' * 60)

    if pytest_rc == 0 and not legacy_failed:
        print('ALL TESTS PASSED')
        return 0
    else:
        if pytest_rc != 0:
            print(f'pytest: FAILED (exit code {pytest_rc})')
        if legacy_failed:
            print(f'Legacy failures: {", ".join(legacy_failed)}')
        return 1


if __name__ == '__main__':
    sys.exit(main())

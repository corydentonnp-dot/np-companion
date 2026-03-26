"""
CareCompanion -- Full QA Suite Runner
scripts/run_full_qa.py

Runs every check from the Testing Cheat Sheet in one shot and writes
a timestamped log to Documents/dev_guide/qa/logs/.

Usage:
    venv\\Scripts\\python.exe scripts/run_full_qa.py

What it runs (in order):
  1. Process count (before)
  2. Smoke test
  3. DB integrity check
  4. Log scan (full)
  5. PHI scan only
  6. List DB snapshots
  7. Run all tests (pytest + legacy)
  8. Detect changes
  9. Deep health (skipped if server not running)
  10. Process count (after)

Skipped intentionally:
  - DB snapshot/restore  -- destructive, run manually
  - Individual pytest subsets -- already covered by "run all tests"
  - E2E tests  -- requires Playwright + running server, run separately
"""

import io
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_PYTHON = os.path.join(ROOT, 'venv', 'Scripts', 'python.exe')
LOG_DIR = os.path.join(ROOT, 'Documents', 'dev_guide', 'qa', 'logs')


# Each entry: (label, command_list, timeout_seconds, skip_on_fail)
STEPS = [
    (
        'Process Count (before)',
        ['powershell', '-Command', '(Get-Process python -ErrorAction SilentlyContinue).Count'],
        15,
        False,
    ),
    (
        'Smoke Test',
        [VENV_PYTHON, os.path.join(ROOT, 'scripts', 'smoke_test.py')],
        120,
        False,
    ),
    (
        'DB Integrity Check',
        [VENV_PYTHON, os.path.join(ROOT, 'scripts', 'db_integrity_check.py')],
        120,
        False,
    ),
    (
        'Log Scan (full)',
        [VENV_PYTHON, os.path.join(ROOT, 'scripts', 'check_logs.py')],
        60,
        False,
    ),
    (
        'PHI Scan Only',
        [VENV_PYTHON, os.path.join(ROOT, 'scripts', 'check_logs.py'), '--phi-only'],
        60,
        False,
    ),
    (
        'List DB Snapshots',
        [VENV_PYTHON, os.path.join(ROOT, 'scripts', 'db_snapshot.py'), 'list'],
        30,
        False,
    ),
    (
        'Run All Tests',
        [VENV_PYTHON, os.path.join(ROOT, 'scripts', 'run_all_tests.py')],
        300,
        False,
    ),
    (
        'Detect Changes',
        [VENV_PYTHON, os.path.join(ROOT, 'scripts', 'detect_changes.py')],
        60,
        False,
    ),
    (
        'Deep Health Check',
        ['curl', '-s', '-o', '-', '-w', '\\nHTTP %{http_code}', 'http://localhost:5000/api/health/deep'],
        15,
        False,
    ),
    (
        'Process Count (after)',
        ['powershell', '-Command', '(Get-Process python -ErrorAction SilentlyContinue).Count'],
        15,
        False,
    ),
]


def run_step(label, cmd, timeout_sec):
    """Run a single step. Returns (exit_code, combined_output, elapsed_sec)."""
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=ROOT,
            timeout=timeout_sec,
            capture_output=True,
            text=True,
            errors='replace',
        )
        elapsed = time.time() - start
        output = (result.stdout or '') + (result.stderr or '')
        return result.returncode, output.strip(), elapsed
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return -1, f'TIMED OUT after {timeout_sec}s', elapsed
    except FileNotFoundError:
        elapsed = time.time() - start
        return -2, f'Command not found: {cmd[0]}', elapsed
    except Exception as e:
        elapsed = time.time() - start
        return -3, f'Error: {e}', elapsed


def main():
    os.makedirs(LOG_DIR, exist_ok=True)

    now = datetime.now(timezone.utc)
    timestamp = now.strftime('%Y-%m-%d_%H%M%S_UTC')
    log_file = os.path.join(LOG_DIR, f'qa_run_{timestamp}.log')

    lines = []
    lines.append('=' * 70)
    lines.append(f'  CareCompanion Full QA Run  --  {now.strftime("%m-%d-%y %H:%M:%S UTC")}')
    lines.append('=' * 70)
    lines.append('')

    total_pass = 0
    total_fail = 0
    total_skip = 0
    summary_rows = []

    for label, cmd, timeout_sec, _ in STEPS:
        header = f'--- [{label}] ---'
        lines.append(header)
        print(header)

        code, output, elapsed = run_step(label, cmd, timeout_sec)

        if code == 0:
            status = 'PASS'
            total_pass += 1
        elif code == -2:
            status = 'SKIP'
            total_skip += 1
        else:
            status = 'FAIL'
            total_fail += 1

        result_line = f'  Status: {status}  |  Exit: {code}  |  {elapsed:.1f}s'
        lines.append(result_line)
        print(result_line)

        if output:
            for line in output.split('\n'):
                lines.append(f'  {line}')
            # Only print last 20 lines to console to keep it readable
            out_lines = output.split('\n')
            if len(out_lines) > 20:
                print(f'  ... ({len(out_lines) - 20} lines omitted, see log) ...')
                for line in out_lines[-20:]:
                    print(f'  {line}')
            else:
                for line in out_lines:
                    print(f'  {line}')

        lines.append('')
        print('')
        summary_rows.append((label, status, code, f'{elapsed:.1f}s'))

    # Summary table
    lines.append('=' * 70)
    lines.append('  SUMMARY')
    lines.append('=' * 70)
    lines.append(f'  {"Step":<30} {"Status":<8} {"Exit":<8} {"Time"}')
    lines.append(f'  {"-"*30} {"-"*8} {"-"*8} {"-"*8}')
    for label, status, code, elapsed in summary_rows:
        lines.append(f'  {label:<30} {status:<8} {code:<8} {elapsed}')
    lines.append('')
    lines.append(f'  PASS: {total_pass}  |  FAIL: {total_fail}  |  SKIP: {total_skip}')
    lines.append('=' * 70)

    # Print summary to console
    for line in lines[-len(summary_rows) - 6:]:
        print(line)

    # Write log file
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    print(f'\nLog saved to: {log_file}')
    sys.exit(1 if total_fail > 0 else 0)


if __name__ == '__main__':
    main()

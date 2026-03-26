"""
CareCompanion -- Log Checker
scripts/check_logs.py

Scans application logs for errors, warnings, and potential PHI leaks.

Checks:
1. Error/exception counts in carecompanion.log
2. Structured errors in error_log.jsonl
3. PHI leak scan (MRN patterns, phone numbers, DOB patterns)
4. Log file sizes and rotation status

Usage:
    venv\\Scripts\\python.exe scripts/check_logs.py
    venv\\Scripts\\python.exe scripts/check_logs.py --phi-only
    venv\\Scripts\\python.exe scripts/check_logs.py --errors-only

Exit codes:
    0 = clean (no PHI leaks, errors are informational)
    1 = PHI leak detected (HIPAA concern)
    2 = excessive errors found
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT, 'data', 'logs')
MAIN_LOG = os.path.join(LOG_DIR, 'carecompanion.log')
ERROR_LOG = os.path.join(LOG_DIR, 'error_log.jsonl')

# Patterns that suggest PHI in logs
# MRN: 5-10 digit numbers that look like medical record numbers
# (excludes port numbers, timestamps, and common numeric IDs)
PHI_PATTERNS = [
    # Unmasked MRN (6-10 digits preceded by MRN/mrn/id context)
    (r'(?i)\b(?:mrn|patient.?id|record.?id)[:\s=]+\d{5,10}\b', 'Possible unmasked MRN'),
    # Date of birth patterns
    (r'(?i)\b(?:dob|date.?of.?birth|born)[:\s=]+\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b', 'Possible DOB'),
    # Phone numbers
    (r'\(\d{3}\)\s*\d{3}[- ]\d{4}', 'Possible phone number'),
    # SSN pattern
    (r'\b\d{3}-\d{2}-\d{4}\b', 'Possible SSN'),
    # Patient name context (first, last name near "patient")
    (r'(?i)patient[:\s]+[A-Z][a-z]+\s+[A-Z][a-z]+', 'Possible patient name'),
]

# Known safe patterns to exclude from PHI detection
SAFE_PATTERNS = [
    r'90\d{3}',  # Demo patient MRNs (90001-90035)
    r'62815',    # Test patient MRN
    r'TEST\s+TEST',  # Test patient name
    r'DEMO\s+PATIENT',  # Demo patient label
]


def scan_phi(filepath):
    """Scan a log file for potential PHI leaks."""
    findings = []
    if not os.path.exists(filepath):
        return findings

    safe_re = re.compile('|'.join(SAFE_PATTERNS))

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for line_num, line in enumerate(f, 1):
                for pattern, description in PHI_PATTERNS:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        # Skip known safe patterns (demo/test data)
                        if safe_re.search(match):
                            continue
                        findings.append({
                            'file': os.path.basename(filepath),
                            'line': line_num,
                            'pattern': description,
                            'match': match[:50],  # Truncate to avoid printing actual PHI
                        })
    except Exception as e:
        findings.append({
            'file': os.path.basename(filepath),
            'line': 0,
            'pattern': 'File read error',
            'match': str(e),
        })

    return findings


def scan_errors(filepath):
    """Count errors/warnings in the main log file."""
    counts = {'ERROR': 0, 'WARNING': 0, 'CRITICAL': 0}
    recent_errors = []

    if not os.path.exists(filepath):
        return counts, recent_errors

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                for level in counts:
                    if level in line:
                        counts[level] += 1
                        if level in ('ERROR', 'CRITICAL'):
                            recent_errors.append(line.strip()[:200])
    except Exception:
        pass

    # Keep only last 10 errors for display
    return counts, recent_errors[-10:]


def scan_error_jsonl(filepath):
    """Parse structured error log."""
    errors = []
    if not os.path.exists(filepath):
        return errors

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    errors.append(entry)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return errors


def check_log_sizes():
    """Check log file sizes."""
    results = []
    if not os.path.exists(LOG_DIR):
        return results

    for filename in os.listdir(LOG_DIR):
        filepath = os.path.join(LOG_DIR, filename)
        if os.path.isfile(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            results.append({
                'file': filename,
                'size_mb': round(size_mb, 2),
                'warning': size_mb > 50,  # Warn if > 50 MB
            })

    return results


def main():
    parser = argparse.ArgumentParser(description='CareCompanion Log Checker')
    parser.add_argument('--phi-only', action='store_true', help='Only scan for PHI leaks')
    parser.add_argument('--errors-only', action='store_true', help='Only scan for errors')
    args = parser.parse_args()

    exit_code = 0
    print('CareCompanion Log Checker')
    print(f'Log directory: {LOG_DIR}')
    print()

    if not os.path.exists(LOG_DIR):
        print('WARNING: Log directory does not exist. No logs to check.')
        return 0

    # ------------------------------------------------------------------
    # PHI Leak Scan
    # ------------------------------------------------------------------
    if not args.errors_only:
        print('=' * 60)
        print('PHI LEAK SCAN')
        print('=' * 60)

        all_findings = []
        for filename in os.listdir(LOG_DIR):
            filepath = os.path.join(LOG_DIR, filename)
            if os.path.isfile(filepath):
                findings = scan_phi(filepath)
                all_findings.extend(findings)

        if all_findings:
            print(f'  ALERT: {len(all_findings)} potential PHI leak(s) detected!')
            for f in all_findings[:20]:  # Show first 20
                print(f'    Line {f["line"]} in {f["file"]}: {f["pattern"]}')
            exit_code = 1
        else:
            print('  CLEAN: No PHI patterns detected in logs.')
        print()

    # ------------------------------------------------------------------
    # Error Scan
    # ------------------------------------------------------------------
    if not args.phi_only:
        print('=' * 60)
        print('ERROR SCAN')
        print('=' * 60)

        # Main log
        if os.path.exists(MAIN_LOG):
            counts, recent = scan_errors(MAIN_LOG)
            print(f'  carecompanion.log:')
            print(f'    CRITICAL: {counts["CRITICAL"]}')
            print(f'    ERROR:    {counts["ERROR"]}')
            print(f'    WARNING:  {counts["WARNING"]}')
            if recent:
                print(f'    Recent errors:')
                for err in recent[-5:]:
                    print(f'      {err[:120]}')
            if counts['CRITICAL'] > 0:
                exit_code = max(exit_code, 2)
        else:
            print('  carecompanion.log: not found')

        # Structured error log
        if os.path.exists(ERROR_LOG):
            errors = scan_error_jsonl(ERROR_LOG)
            print(f'\n  error_log.jsonl: {len(errors)} entries')
            for err in errors[-5:]:
                ts = err.get('timestamp', '?')
                msg = err.get('message', err.get('error', '?'))[:100]
                print(f'    [{ts}] {msg}')
        else:
            print('  error_log.jsonl: not found')
        print()

    # ------------------------------------------------------------------
    # Log File Sizes
    # ------------------------------------------------------------------
    if not args.phi_only and not args.errors_only:
        print('=' * 60)
        print('LOG FILE SIZES')
        print('=' * 60)
        sizes = check_log_sizes()
        for s in sizes:
            flag = ' [LARGE]' if s['warning'] else ''
            print(f'  {s["file"]}: {s["size_mb"]} MB{flag}')
        print()

    # Summary
    print('=' * 60)
    if exit_code == 0:
        print('LOG CHECK: CLEAN')
    elif exit_code == 1:
        print('LOG CHECK: PHI LEAK DETECTED -- review findings above')
    else:
        print('LOG CHECK: ERRORS FOUND -- review error scan above')

    return exit_code


if __name__ == '__main__':
    sys.exit(main())

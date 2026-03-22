"""
Phase 6 — verify_all.py — Interactive Pre-Beta Verification Orchestrator

5-stage verification:
  Stage 1: Automated deploy_check.py
  Stage 2: Full test suite (python tests/test_verification.py + pytest tests/)
  Stage 3: Flask test client URL smoke test (38 URLs)
  Stage 4: Interactive manual UI walkthrough (32 checks)
  Stage 5: Report generation with go/no-go decision

Usage:
    python tools/verify_all.py
"""

import os
import sys
import json
import subprocess
import platform
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
RESET = '\033[0m'

# ──────────────────────────────────────────────────────────────────────
# URL smoke test table (38 URLs)
# ──────────────────────────────────────────────────────────────────────
SMOKE_URLS = [
    ('GET', '/login', 200, 'Auth'),
    ('GET', '/dashboard', 200, 'Core'),
    ('GET', '/timer', 200, 'Core'),
    ('GET', '/inbox', 200, 'Core'),
    ('GET', '/oncall', 200, 'Core'),
    ('GET', '/orders', 200, 'Core'),
    ('GET', '/medref', 200, 'Core'),
    ('GET', '/labtrack', 200, 'Core'),
    ('GET', '/caregap', 200, 'Core'),
    ('GET', '/metrics', 200, 'Core'),
    ('GET', '/tools', 200, 'Core'),
    ('GET', '/patient/DEMO001', 200, 'Patient'),
    ('GET', '/caregap/DEMO001', 200, 'Patient'),
    ('GET', '/caregap/DEMO001/print', 200, 'Patient'),
    ('GET', '/briefing', 200, 'Intelligence'),
    ('GET', '/billing/log', 200, 'Billing'),
    ('GET', '/billing/em-calculator', 200, 'Billing'),
    ('GET', '/billing/monthly-report', 200, 'Billing'),
    ('GET', '/billing/why-not/DEMO001', 200, 'Billing'),
    ('GET', '/bonus', 200, 'Billing'),
    ('GET', '/ccm/registry', 200, 'Billing'),
    ('GET', '/tcm/watch-list', 200, 'Billing'),
    ('GET', '/monitoring/calendar', 200, 'Monitoring'),
    ('GET', '/care-gaps/preventive', 200, 'Monitoring'),
    ('GET', '/settings/phrases', 200, 'Settings'),
    ('GET', '/campaigns', 200, 'Campaigns'),
    ('GET', '/reports/revenue/2026/3', 200, 'Reports'),
    ('GET', '/reports/dx-families', 200, 'Reports'),
    ('GET', '/calculators', 200, 'Calculators'),
    ('GET', '/staff/billing-tasks', 200, 'Staff'),
    ('GET', '/admin', 200, 'Admin'),
    ('GET', '/admin/users', 200, 'Admin'),
    ('GET', '/admin/audit-log', 200, 'Admin'),
    ('GET', '/admin/agent', 200, 'Admin'),
    ('GET', '/admin/caregap-rules', 200, 'Admin'),
    ('GET', '/admin/billing-roi', 200, 'Admin'),
    ('GET', '/settings/account', 200, 'Settings'),
    ('GET', '/api/health', 200, 'API'),
]

# ──────────────────────────────────────────────────────────────────────
# 32 Manual UI checks
# ──────────────────────────────────────────────────────────────────────
MANUAL_CHECKS = [
    (1,  'Login page', 'Open Chrome → localhost:5000', 'Login form visible · No errors'),
    (2,  'Dashboard load', 'Log in as CORY · ASDqwe123', "Dashboard shows · Today's date visible"),
    (3,  'Timer', 'Click Timer in sidebar', 'Timer loads · Start session works'),
    (4,  'Inbox', 'Click Inbox', 'Filter tabs visible · Digest tab present'),
    (5,  'On-Call', 'Click On-Call → New Note', 'Form opens · Text can be entered'),
    (6,  'Orders', 'Click Orders', 'Order sets list visible'),
    (7,  'Med Ref', 'Click Med Ref · search "metformin"', 'Search box works · Results appear'),
    (8,  'Lab Track', 'Click Lab Track', 'Stats cards + table visible'),
    (9,  'Care Gaps', 'Click Care Gaps', 'Panel visible · Date navigation works'),
    (10, 'Metrics', 'Click Metrics', '7 Chart.js charts loaded (may be all zero)'),
    (11, 'Patient chart', 'Go to /patient/DEMO001', 'Chart loads with widget layout'),
    (12, 'Vitals widget', 'On DEMO001 chart', 'Height, weight, BMI, BP visible'),
    (13, 'Billing alert bar', 'On DEMO001 chart', 'At least 1 billing code suggested'),
    (14, 'Risk Scores widget', 'On DEMO001 chart', 'BMI, LDL, Pack Years, PREVENT cards visible'),
    (15, 'Risk Tool Picker', 'Click Calculators tab on DEMO001', 'Calculator form loads · EHR-pre-filled fields shown'),
    (16, 'CCM sidebar widget', 'On DEMO001 chart', 'CCM enrollment status shown'),
    (17, 'Care Gap print', 'Go to /caregap/DEMO001/print', 'Clean handout · No navigation chrome · Gap list in plain English'),
    (18, 'Billing log', 'Go to /billing/log', 'Table with filter controls visible'),
    (19, 'Bonus dashboard', 'Go to /bonus', 'Quarterly bar · Q1 2026 receipts · Deficit visible'),
    (20, 'CCM registry', 'Go to /ccm/registry', '≥2 enrolled patients shown'),
    (21, 'TCM watch list', 'Go to /tcm/watch-list', '≥1 watch entry with deadline indicator'),
    (22, 'Monitoring calendar', 'Go to /monitoring/calendar', 'Labs grouped by overdue/due/upcoming'),
    (23, 'Preventive gaps', 'Go to /care-gaps/preventive', 'Per-service compliance bars visible'),
    (24, 'Campaigns', 'Go to /campaigns', 'Campaign templates with launch buttons'),
    (25, 'Morning briefing', 'Go to /briefing', 'All sections: schedule, TCM, labs, bonus, risk alerts'),
    (26, 'Admin hub', 'Go to /admin', 'All 7 admin links visible'),
    (27, 'Agent status', 'Go to /admin/agent', 'Agent status dashboard shows'),
    (28, 'Care gap rules', 'Go to /admin/caregap-rules', '19 USPSTF rules listed'),
    (29, 'Settings account', 'Go to /settings/account', 'Account form with username and role'),
    (30, 'Restart script', 'Run restart.bat from File Explorer', 'Server restarts · Chrome reopens to dashboard'),
    (31, 'AC Mock Mode', 'Open config.py in Notepad', 'AC_MOCK_MODE = False confirmed (critical)'),
    (32, 'Provider sign-off', "Review this report's summary", 'All sections reviewed · Provider acknowledges'),
]

CRITICAL_MANUAL_IDS = {1, 11, 31}


# ====================================================================
# Stage 1 — Deploy check
# ====================================================================
def run_stage1():
    """Run deploy_check.py and return results dict."""
    results = {'pass': True, 'sections': {}, 'warnings': [], 'failures': []}
    try:
        from tools.deploy_check import DeployChecker
        checker = DeployChecker()
        checker.run_all_checks()
        for name, info in checker.results.items():
            ok = info['pass']
            detail = info.get('detail', '')
            results['sections'][name] = {'pass': ok, 'detail': detail}
            if not ok:
                if 'smtp' in name.lower() or 'email' in name.lower():
                    results['warnings'].append(f'{name}: {detail}')
                else:
                    results['failures'].append(f'{name}: {detail}')
                    results['pass'] = False
    except Exception as e:
        results['pass'] = False
        results['failures'].append(f'deploy_check import/run error: {e}')
    return results


# ====================================================================
# Stage 2 — Test suite
# ====================================================================
def run_stage2():
    """Run tests/test_verification.py and pytest tests/ and return results dict."""
    results = {'pass': True, 'test_py': '', 'pytest': '', 'details': []}
    python = sys.executable

    # tests/test_verification.py
    try:
        proc = subprocess.run(
            [python, os.path.join('tests', 'test_verification.py')],
            capture_output=True, text=True, timeout=300, cwd=ROOT
        )
        results['test_py'] = proc.stdout[-500:] if len(proc.stdout) > 500 else proc.stdout
        if proc.returncode != 0:
            results['pass'] = False
            results['details'].append(f'test_verification.py exited with code {proc.returncode}')
    except Exception as e:
        results['pass'] = False
        results['details'].append(f'test_verification.py error: {e}')

    # pytest
    try:
        proc = subprocess.run(
            [python, '-m', 'pytest', 'tests/', '--tb=short', '-q'],
            capture_output=True, text=True, timeout=300, cwd=ROOT
        )
        results['pytest'] = proc.stdout[-500:] if len(proc.stdout) > 500 else proc.stdout
        if proc.returncode != 0:
            results['pass'] = False
            results['details'].append(f'pytest exited with code {proc.returncode}')
    except Exception as e:
        results['pass'] = False
        results['details'].append(f'pytest error: {e}')

    return results


# ====================================================================
# Stage 3 — URL smoke test
# ====================================================================
def run_stage3(app=None):
    """Hit 38 URLs via Flask test client. Returns results dict."""
    results = {'pass': True, 'url_results': [], 'pass_count': 0, 'total': len(SMOKE_URLS)}

    if app is None:
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

    # Get test user for auth
    with app.app_context():
        try:
            from models.user import User
            user = User.query.filter_by(is_active_account=True).order_by(User.id.asc()).first()
            uid = user.id if user else 1
        except Exception:
            uid = 1

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(uid)

    for method, url, expected, category in SMOKE_URLS:
        try:
            resp = client.get(url)
            actual = resp.status_code
            ok = actual == expected
            results['url_results'].append({
                'url': url, 'expected': expected, 'actual': actual,
                'pass': ok, 'category': category,
            })
            if ok:
                results['pass_count'] += 1
            else:
                results['pass'] = False
        except Exception as e:
            results['url_results'].append({
                'url': url, 'expected': expected, 'actual': 0,
                'pass': False, 'category': category, 'error': str(e),
            })
            results['pass'] = False

    return results


# ====================================================================
# Stage 4 — Interactive manual checks
# ====================================================================
def run_stage4():
    """Run interactive manual UI walkthrough. Returns results dict."""
    results = {'checks': [], 'pass_count': 0, 'fail_count': 0, 'skip_count': 0, 'notes': []}
    total = len(MANUAL_CHECKS)

    print(f'\n{BOLD}About to begin manual UI checks.{RESET}')
    print('Start Flask server fresh and open Chrome to http://localhost:5000.')
    input('Press Enter when ready...')

    for num, feature, instruction, confirm in MANUAL_CHECKS:
        pct = int((num - 1) / total * 100)
        bar_filled = int(pct / 5)
        bar = '█' * bar_filled + '░' * (20 - bar_filled)
        print(f'\n[{bar}] {pct}% — Check {num}/{total}')
        print(f'{BOLD}#{num}. {feature}{RESET}')
        print(f'  Do: {instruction}')
        print(f'  Confirm: {confirm}')

        while True:
            answer = input('  PASS (y) / FAIL (n) / SKIP (s)? ').strip().lower()
            if answer in ('y', 'n', 's'):
                break
            print('  Please enter y, n, or s.')

        entry = {'num': num, 'feature': feature, 'result': answer, 'note': ''}
        if answer == 'y':
            results['pass_count'] += 1
            entry['result'] = 'PASS'
        elif answer == 'n':
            results['fail_count'] += 1
            entry['result'] = 'FAIL'
            note = input('  Describe the issue briefly: ').strip()
            entry['note'] = note
            results['notes'].append(f'#{num} {feature}: {note}')
        else:
            results['skip_count'] += 1
            entry['result'] = 'SKIP'

        results['checks'].append(entry)

    return results


# ====================================================================
# Decision logic
# ====================================================================
def determine_decision(stage1, stage2, stage3, stage4):
    """
    Return decision string:
      'GO'             — all automated pass + 0 manual fails
      'CONDITIONAL GO' — automated pass + 1-3 non-critical manual fails
      'HOLD'           — hard automated failure or critical manual fail
    """
    # Hard automated failures
    if not stage1.get('pass', False) or not stage2.get('pass', False) or not stage3.get('pass', False):
        return 'HOLD'

    # Critical manual check failures
    if stage4:
        for c in stage4.get('checks', []):
            if c['result'] == 'FAIL' and c['num'] in CRITICAL_MANUAL_IDS:
                return 'HOLD'

        fail_count = stage4.get('fail_count', 0)
        if fail_count == 0:
            return 'GO'
        elif fail_count <= 3:
            return 'CONDITIONAL GO'
        else:
            return 'HOLD'

    return 'GO'


# ====================================================================
# Stage 5 — Report generation
# ====================================================================
def generate_report(stage1, stage2, stage3, stage4, decision, verifier_name=''):
    """Write VERIFICATION_REPORT to Documents/. Returns report path."""
    now = datetime.now()
    report_name = f'VERIFICATION_REPORT_{now.strftime("%Y%m%d_%H%M%S")}.txt'
    report_path = os.path.join(ROOT, 'Documents', report_name)

    try:
        import config as cfg
        version = getattr(cfg, 'APP_VERSION', 'unknown')
    except Exception:
        version = 'unknown'

    lines = [
        '═' * 60,
        'CARECOMPANION — PRE-BETA VERIFICATION REPORT',
        '═' * 60,
        f'Generated: {now.strftime("%Y-%m-%d %H:%M:%S")}',
        f'Version:   {version}',
        f'Host:      {platform.node()}',
        f'Python:    {platform.python_version()}',
        f'Verified by: {verifier_name}',
        '',
    ]

    # Section 1 — deploy_check
    lines.append('── SECTION 1: AUTOMATED PRE-FLIGHT (deploy_check.py) ────────')
    for name, info in stage1.get('sections', {}).items():
        icon = '✓' if info['pass'] else '✗'
        lines.append(f'{icon} {name}: {info["detail"]}')
    lines.append('')

    # Section 2 — test suite
    lines.append('── SECTION 2: TEST SUITE ─────────────────────────────────────')
    lines.append(stage2.get('test_py', '').strip()[-200:] if stage2.get('test_py') else 'not run')
    lines.append(stage2.get('pytest', '').strip()[-200:] if stage2.get('pytest') else 'not run')
    lines.append('')

    # Section 3 — URL smoke test
    lines.append('── SECTION 3: URL SMOKE TEST ──────────────────────────────────')
    s3 = stage3
    lines.append(f'✓ {s3.get("pass_count", 0)}/{s3.get("total", 0)} URLs returned expected status')
    for u in s3.get('url_results', []):
        if not u['pass']:
            lines.append(f'  ✗ {u["url"]} → {u["actual"]} (expected {u["expected"]})')
    lines.append('')

    # Section 4 — manual checks
    lines.append('── SECTION 4: MANUAL VERIFICATION ────────────────────────────')
    for c in stage4.get('checks', []):
        icon = '✓' if c['result'] == 'PASS' else ('✗' if c['result'] == 'FAIL' else '–')
        line = f'{icon} {c["num"]:2d}. {c["feature"]}'
        if c.get('note'):
            line += f' — {c["note"]}'
        lines.append(line)
    lines.append('')

    # Section 5 — summary
    lines.append('── SECTION 5: SUMMARY ─────────────────────────────────────────')
    s1_pass = sum(1 for v in stage1.get('sections', {}).values() if v['pass'])
    s1_total = len(stage1.get('sections', {}))
    s1_warn = len(stage1.get('warnings', []))
    lines.append(f'Automated pre-flight:  {s1_pass}/{s1_total} PASS · {s1_warn} warning(s)')
    lines.append(f'Test suite:            {stage2.get("test_py", "").strip()[-80:]}')
    lines.append(f'URL smoke test:        {s3.get("pass_count", 0)}/{s3.get("total", 0)} PASS')
    m_pass = stage4.get('pass_count', 0)
    m_fail = stage4.get('fail_count', 0)
    m_skip = stage4.get('skip_count', 0)
    lines.append(f'Manual checks:         {m_pass} PASS · {m_fail} FAIL · {m_skip} SKIP')
    lines.append('')

    if stage4.get('notes'):
        lines.append('FAILS:')
        for note in stage4['notes']:
            lines.append(f'  • {note}')
    else:
        lines.append('FAILS: none')

    for w in stage1.get('warnings', []):
        lines.append(f'WARNING: {w}')
    lines.append('')

    # Decision
    lines.append('═' * 60)
    if decision == 'GO':
        lines.append('DECISION: ✅ GO FOR BETA — all checks passed')
        lines.append('')
        lines.append(f'This report confirms that CareCompanion {version} has passed all')
        lines.append('automated and manual pre-deployment checks. The application')
        lines.append('is cleared for Tier-1 beta use with real patient data.')
    elif decision == 'CONDITIONAL GO':
        lines.append('DECISION: ⚠️ CONDITIONAL GO — resolve noted items within 24 hours')
        lines.append('before first patient session.')
    else:
        lines.append('DECISION: 🛑 HOLD — must resolve critical issues before')
        lines.append('handling real patient data. See FAILS list above.')

    lines.extend([
        '',
        'Provider signature: ________________________',
        'Date: ____________________',
        '═' * 60,
    ])

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return report_path


# ====================================================================
# run_automated_checks — for test use
# ====================================================================
def run_automated_checks(app=None):
    """Run stages 1-3 (no interactive prompts). Returns dict with all 3 stage results."""
    s1 = run_stage1()
    s2 = run_stage2()
    s3 = run_stage3(app=app)
    return {'stage1': s1, 'stage2': s2, 'stage3': s3}


# ====================================================================
# Main entry point
# ====================================================================
def main():
    print(f'{BOLD}{"═" * 60}{RESET}')
    print(f'{BOLD}CARECOMPANION — PRE-BETA VERIFICATION SESSION{RESET}')
    print(f'{BOLD}{"═" * 60}{RESET}')
    print()

    # Stage 1
    print(f'{BOLD}Stage 1 — Automated Pre-Flight (deploy_check.py){RESET}')
    print('─' * 50)
    s1 = run_stage1()
    for name, info in s1.get('sections', {}).items():
        color = GREEN if info['pass'] else RED
        icon = '✓' if info['pass'] else '✗'
        print(f'  {color}{icon}{RESET} {name}: {info["detail"]}')
    if s1['failures']:
        print(f'\n{RED}⚠  Critical failures detected:{RESET}')
        for f in s1['failures']:
            print(f'    {RED}✗{RESET} {f}')
        answer = input('Resolve and re-run? (Y/N): ').strip().lower()
        if answer != 'y':
            print(f'{RED}🛑 HOLD — pre-flight checks failed{RESET}')
            return False

    # Stage 2
    print(f'\n{BOLD}Stage 2 — Test Suite{RESET}')
    print('─' * 50)
    s2 = run_stage2()
    if s2['pass']:
        print(f'  {GREEN}✓{RESET} test_verification.py + pytest: all passed')
    else:
        print(f'  {RED}✗{RESET} Test failures detected:')
        for d in s2['details']:
            print(f'    {d}')

    # Stage 3
    print(f'\n{BOLD}Stage 3 — URL Smoke Test (38 URLs){RESET}')
    print('─' * 50)
    s3 = run_stage3()
    for u in s3['url_results']:
        color = GREEN if u['pass'] else RED
        icon = '✓' if u['pass'] else '✗'
        print(f'  {color}{icon}{RESET} GET {u["url"]} → {u["actual"]}')
    print(f'  Result: {s3["pass_count"]}/{s3["total"]} passed')

    # Stage 4
    print(f'\n{BOLD}Stage 4 — Manual UI Walkthrough (32 checks){RESET}')
    print('─' * 50)
    s4 = run_stage4()

    # Decision
    decision = determine_decision(s1, s2, s3, s4)

    # Stage 5 — Report
    print(f'\n{BOLD}Stage 5 — Report Generation{RESET}')
    print('─' * 50)
    verifier = input('Enter your name for the report (e.g., Cory Denton, FNP): ').strip()
    report_path = generate_report(s1, s2, s3, s4, decision, verifier)
    print(f'Report written: {report_path}')

    # Final banner
    print(f'\n{BOLD}{"═" * 60}{RESET}')
    if decision == 'GO':
        print(f'{GREEN}{BOLD}✅ GO FOR BETA — all checks passed{RESET}')
    elif decision == 'CONDITIONAL GO':
        print(f'{YELLOW}{BOLD}⚠️  CONDITIONAL GO — resolve noted items within 24 hours{RESET}')
    else:
        print(f'{RED}{BOLD}🛑 HOLD — resolve critical issues before real patient data{RESET}')
    print(f'{BOLD}{"═" * 60}{RESET}')

    return decision == 'GO'


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

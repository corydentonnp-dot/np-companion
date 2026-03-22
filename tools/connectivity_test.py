"""
Phase 5.3 — Network & Tailscale Connectivity Test (final_plan.md Phase 5)

Standalone script to verify LAN, Tailscale, and AC file share connectivity.

Usage:
    python tools/connectivity_test.py
"""

import os
import sys
import subprocess
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Try to load config values — fallback to defaults if unavailable
try:
    sys.path.insert(0, ROOT)
    import config
    AC_DB_PATH = getattr(config, 'AC_DB_PATH', r'\\192.168.2.51\Amazing Charts\AmazingCharts.mdf')
    AC_IMPORTED_ITEMS_PATH = getattr(config, 'AC_IMPORTED_ITEMS_PATH', r'\\192.168.2.51\amazing charts\ImportItems')
    NETPRACTICE_URL = getattr(config, 'NETPRACTICE_URL', '')
    TAILSCALE_WORK_PC_IP = getattr(config, 'TAILSCALE_WORK_PC_IP', None)
except Exception:
    AC_DB_PATH = r'\\192.168.2.51\Amazing Charts\AmazingCharts.mdf'
    AC_IMPORTED_ITEMS_PATH = r'\\192.168.2.51\amazing charts\ImportItems'
    NETPRACTICE_URL = ''
    TAILSCALE_WORK_PC_IP = None


def check_ping(ip, count=2):
    """Ping an IP and return structured result."""
    result = {'pass': False, 'detail': ''}
    try:
        proc = subprocess.run(
            ['ping', '-n', str(count), ip],
            capture_output=True, text=True, timeout=15
        )
        result['pass'] = proc.returncode == 0
        result['detail'] = f'ping {ip}: {"reachable" if result["pass"] else "unreachable"}'
    except FileNotFoundError:
        result['detail'] = f'ping command not found'
    except subprocess.TimeoutExpired:
        result['detail'] = f'ping {ip}: timed out'
    except Exception as e:
        result['detail'] = f'ping {ip}: {e}'
    return result


def check_unc_path(path, label):
    """Check if a UNC/local path is accessible."""
    result = {'pass': False, 'detail': ''}
    try:
        exists = os.path.exists(path)
        result['pass'] = exists
        result['detail'] = f'{label}: {"accessible" if exists else "not accessible"}'
    except Exception as e:
        result['detail'] = f'{label}: {e}'
    return result


def check_netpractice():
    """HTTP check on NetPractice URL."""
    result = {'pass': False, 'detail': ''}
    if not NETPRACTICE_URL:
        result['detail'] = 'NETPRACTICE_URL not configured'
        return result
    try:
        import urllib.request
        req = urllib.request.Request(NETPRACTICE_URL)
        with urllib.request.urlopen(req, timeout=5) as resp:
            result['pass'] = 200 <= resp.status < 500
            result['detail'] = f'NetPractice: status {resp.status}'
    except Exception as e:
        result['detail'] = f'NetPractice: {e}'
    return result


def check_tailscale_status():
    """Check if Tailscale CLI is available and running."""
    result = {'pass': False, 'detail': '', 'devices': []}
    try:
        proc = subprocess.run(
            ['tailscale', 'status'],
            capture_output=True, text=True, timeout=10
        )
        if proc.returncode == 0:
            result['pass'] = True
            lines = [l.strip() for l in proc.stdout.strip().splitlines() if l.strip()]
            result['devices'] = lines
            result['detail'] = f'Tailscale: {len(lines)} device(s) connected'
        else:
            result['detail'] = f'Tailscale: not running ({proc.stderr.strip()[:80]})'
    except FileNotFoundError:
        result['detail'] = 'Tailscale: CLI not in PATH'
    except subprocess.TimeoutExpired:
        result['detail'] = 'Tailscale: status timed out'
    except Exception as e:
        result['detail'] = f'Tailscale: {e}'
    return result


def run_connectivity_test():
    """Run all connectivity checks. Returns list of (name, result_dict)."""
    checks = []

    # LAN checks
    checks.append(('LAN ping 192.168.2.51', check_ping('192.168.2.51')))
    checks.append(('AC DB share', check_unc_path(AC_DB_PATH, 'AC_DB_PATH')))
    checks.append(('NetPractice HTTP', check_netpractice()))

    # Tailscale checks
    ts = check_tailscale_status()
    checks.append(('Tailscale status', ts))

    if ts['pass'] and TAILSCALE_WORK_PC_IP:
        checks.append(('Tailscale ping work PC', check_ping(TAILSCALE_WORK_PC_IP)))

    # AC file share
    checks.append(('AC ImportItems share', check_unc_path(AC_IMPORTED_ITEMS_PATH, 'AC_IMPORTED_ITEMS_PATH')))

    return checks


def write_report(checks):
    """Write results to tools/connectivity_report.txt."""
    report_path = os.path.join(ROOT, 'tools', 'connectivity_report.txt')
    lines = [
        'CareCompanion Connectivity Test',
        '=' * 40,
        f'Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        '',
    ]

    pass_count = 0
    total = len(checks)
    for name, r in checks:
        icon = '✓' if r['pass'] else '✗'
        if r['pass']:
            pass_count += 1
        lines.append(f'{icon} {name}: {r["detail"]}')

    lines.append(f'\nRESULT: {pass_count}/{total} checks passed')

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return report_path


def main():
    print('CareCompanion Connectivity Test')
    print('=' * 40)

    checks = run_connectivity_test()

    pass_count = 0
    for name, r in checks:
        icon = '✓' if r['pass'] else '✗'
        if r['pass']:
            pass_count += 1
        print(f'  {icon} {name}: {r["detail"]}')

    report_path = write_report(checks)
    print(f'\nReport: {report_path}')
    print(f'RESULT: {pass_count}/{len(checks)} checks passed')

    return pass_count == len(checks)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

"""
Process Guard — Detects, logs, and kills orphaned Python processes.

Usage:
    python tools/process_guard.py              # Report only
    python tools/process_guard.py --kill       # Kill orphans (high CPU/memory)
    python tools/process_guard.py --kill-all   # Kill ALL Python except self
    python tools/process_guard.py --watch      # Continuous monitoring (30s interval)
    python tools/process_guard.py --watch --auto-kill  # Auto-kill on sustained 95% CPU

Watch mode logs every Python process with full parent-chain attribution to
data/logs/python_process_log.csv.  Each process is tagged with its origin
(CareCompanion, VS Code, Chrome, System, Unknown).

Called by run.ps1 at startup and by Copilot agent at session start/end.
"""

import csv
import glob
import os
import signal
import sys
import time
import argparse
from datetime import datetime, timezone

# -- Project root (two levels up from tools/) -------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOG_DIR = os.path.join(PROJECT_ROOT, 'data', 'logs')
LOG_PATH = os.path.join(LOG_DIR, 'python_process_log.csv')
WATCH_INTERVAL = 30  # seconds between scans
CPU_ALERT_THRESHOLD = 95.0   # percent -- alert when total CPU >= this
CPU_KILL_SECONDS = 180       # 3 minutes sustained above threshold
CSV_HEADERS = [
    'timestamp', 'pid', 'parent_pid', 'parent_name', 'origin',
    'cpu_pct', 'mem_mb', 'cmdline', 'status',
]


def _ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def _classify_origin(cmdline, parent_name):
    """Tag a Python process with its likely origin."""
    cmd_lower = (cmdline or '').lower()
    parent_lower = (parent_name or '').lower()

    # CareCompanion processes (Flask, agent, tests, migrations)
    cc_markers = [
        'launcher.py', 'agent.py', 'agent_service',
        'app.py', 'flask', 'carecompanion',
        'test_verification', 'test_billing', 'test_agent',
        'build.py', 'process_guard', 'run_all_tests',
        'run_full_qa', 'deploy_check', 'verify_all',
        'np_companion',
    ]
    for marker in cc_markers:
        if marker in cmd_lower:
            return 'CareCompanion'

    # VS Code / Copilot spawned
    if 'code' in parent_lower or 'electron' in parent_lower:
        return 'VS Code'
    if '.vscode' in cmd_lower or 'copilot' in cmd_lower:
        return 'VS Code'

    # Chrome / Playwright
    if 'chrome' in parent_lower or 'playwright' in cmd_lower:
        return 'Chrome/Playwright'

    # Python REPL or pip
    if cmd_lower.endswith('python.exe') or 'pip' in cmd_lower:
        return 'Python CLI'

    return 'Unknown'


def _get_parent_info(pid):
    """Resolve parent PID and parent process name."""
    try:
        import psutil
        proc = psutil.Process(pid)
        parent = proc.parent()
        if parent:
            return parent.pid, parent.name()
    except Exception:
        pass
    return 0, 'unknown'


def _get_processes():
    """Return list of python process dicts using psutil."""
    try:
        import psutil
    except ImportError:
        print("[WARN] psutil not installed -- falling back to tasklist")
        return _get_processes_tasklist()

    results = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'cmdline', 'create_time']):
        try:
            name = proc.info['name'] or ''
            if 'python' not in name.lower():
                continue
            mem_mb = (proc.info['memory_info'].rss / 1024 / 1024) if proc.info['memory_info'] else 0
            cmdline = ' '.join(proc.info['cmdline'] or [])
            ppid, pname = _get_parent_info(proc.info['pid'])
            origin = _classify_origin(cmdline, pname)
            results.append({
                'pid': proc.info['pid'],
                'name': name,
                'cpu': proc.info['cpu_percent'] or 0,
                'mem_mb': round(mem_mb, 1),
                'cmdline': cmdline[:200],
                'is_self': proc.info['pid'] == os.getpid(),
                'parent_pid': ppid,
                'parent_name': pname,
                'origin': origin,
            })
        except Exception:
            continue
    return results


def _get_processes_tasklist():
    """Fallback: use tasklist command when psutil unavailable."""
    import subprocess
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV', '/NH'],
            capture_output=True, text=True, timeout=10
        )
        lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
        results = []
        for line in lines:
            parts = line.replace('"', '').split(',')
            if len(parts) >= 5:
                pid = int(parts[1])
                results.append({
                    'pid': pid,
                    'name': parts[0],
                    'cpu': 0,
                    'mem_mb': round(int(parts[4].replace(' K', '').replace(',', '').strip()) / 1024, 1),
                    'cmdline': '',
                    'is_self': pid == os.getpid(),
                    'parent_pid': 0,
                    'parent_name': 'unknown',
                    'origin': 'Unknown',
                })
        return results
    except Exception as e:
        print(f"[ERROR] tasklist failed: {e}")
        return []


def report(processes):
    """Print process summary with origin attribution."""
    count = len(processes)
    total_mem = sum(p['mem_mb'] for p in processes)
    print(f"\n=== Python Process Report ===")
    print(f"Total: {count} processes, {total_mem:.0f} MB memory")
    if count > 8:
        print(f"[CRITICAL] {count} Python processes -- exceeds safe limit of 8!")
    elif count > 4:
        print(f"[WARNING] {count} Python processes -- approaching safe limit of 4")
    else:
        print(f"[OK] Process count within safe limits")

    # Origin breakdown
    origins = {}
    for p in processes:
        o = p.get('origin', 'Unknown')
        origins[o] = origins.get(o, 0) + 1
    if origins:
        print(f"\nBy origin: {', '.join(f'{k}={v}' for k, v in sorted(origins.items()))}")

    print(f"\n{'PID':>8}  {'CPU%':>5}  {'MEM':>7}  {'PPID':>6}  {'PARENT':>12}  {'ORIGIN':<18}  CMD")
    print("-" * 110)
    for p in sorted(processes, key=lambda x: x['mem_mb'], reverse=True):
        marker = " <-- SELF" if p['is_self'] else ""
        print(
            f"{p['pid']:>8}  {p['cpu']:>5.1f}  {p['mem_mb']:>6.1f}M  "
            f"{p.get('parent_pid', 0):>6}  {p.get('parent_name', '?')[:12]:>12}  "
            f"{p.get('origin', '?'):<18}  {p['cmdline'][:45]}{marker}"
        )
    print()


def kill_orphans(processes, aggressive=False):
    """Kill orphaned Python processes. Skip self."""
    try:
        import psutil
    except ImportError:
        print("[ERROR] psutil required for kill mode")
        return 0

    killed = 0
    for p in processes:
        if p['is_self']:
            continue
        try:
            proc = psutil.Process(p['pid'])
            if aggressive or p['cpu'] > 30 or p['mem_mb'] > 500:
                proc.terminate()
                proc.wait(timeout=5)
                killed += 1
                print(f"  Killed PID {p['pid']} ({p.get('origin','?')}, CPU={p['cpu']:.0f}%, MEM={p['mem_mb']:.0f}MB)")
        except Exception:
            try:
                import psutil as _ps
                _ps.Process(p['pid']).kill()
                killed += 1
                print(f"  Force-killed PID {p['pid']}")
            except Exception:
                pass
    return killed


# -- CSV logging ---------------------------------------------------

def _rotate_logs():
    """Keep only the last 7 days of log files."""
    try:
        pattern = os.path.join(LOG_DIR, 'python_process_log*.csv')
        files = sorted(glob.glob(pattern))
        while len(files) > 7:
            os.remove(files.pop(0))
    except Exception:
        pass


def _get_log_path():
    """Return today's log file path (daily rotation)."""
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    return os.path.join(LOG_DIR, f'python_process_log_{today}.csv')


def _write_csv_row(log_path, processes):
    """Append one snapshot row per process to the CSV log."""
    _ensure_log_dir()
    write_header = not os.path.exists(log_path)

    with open(log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS, extrasaction='ignore')
        if write_header:
            writer.writeheader()

        ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        for p in processes:
            writer.writerow({
                'timestamp': ts,
                'pid': p['pid'],
                'parent_pid': p.get('parent_pid', 0),
                'parent_name': p.get('parent_name', 'unknown'),
                'origin': p.get('origin', 'Unknown'),
                'cpu_pct': round(p['cpu'], 1),
                'mem_mb': round(p['mem_mb'], 1),
                'cmdline': p['cmdline'][:200],
                'status': 'self' if p['is_self'] else 'running',
            })


# -- Watch mode ----------------------------------------------------

def _get_total_cpu():
    """Get overall system CPU percentage."""
    try:
        import psutil
        return psutil.cpu_percent(interval=1)
    except Exception:
        return 0.0


def watch(auto_kill=False):
    """
    Continuous monitoring loop.  Logs all Python processes every 30s
    to data/logs/python_process_log_YYYY-MM-DD.csv.

    If auto_kill is True:
      - Alert at 95% total CPU
      - If >95% for 3 continuous minutes, kill non-essential Python
        processes and relaunch the Flask server
    """
    print(f"\n=== Process Guard -- Watch Mode ===")
    print(f"Interval: {WATCH_INTERVAL}s | CPU alert: {CPU_ALERT_THRESHOLD}%")
    print(f"Auto-kill: {'ON (3 min sustained)' if auto_kill else 'OFF (alert only)'}")
    print(f"Log: data/logs/python_process_log_YYYY-MM-DD.csv")
    print(f"Press Ctrl+C to stop.\n")

    _ensure_log_dir()
    _rotate_logs()

    prev_pids = set()
    cpu_high_since = None  # timestamp when CPU first exceeded threshold

    # Handle Ctrl+C gracefully
    running = True
    def _handle_sigint(sig, frame):
        nonlocal running
        running = False
    signal.signal(signal.SIGINT, _handle_sigint)

    while running:
        try:
            processes = _get_processes()
            cur_pids = {p['pid'] for p in processes}
            log_path = _get_log_path()

            # Log to CSV
            _write_csv_row(log_path, processes)

            # Delta: flag new processes
            new_pids = cur_pids - prev_pids
            gone_pids = prev_pids - cur_pids
            ts = datetime.now(timezone.utc).strftime('%H:%M:%S')

            count = len(processes)
            total_mem = sum(p['mem_mb'] for p in processes)

            # Origin breakdown
            origins = {}
            for p in processes:
                o = p.get('origin', 'Unknown')
                origins[o] = origins.get(o, 0) + 1
            origin_str = ', '.join(f'{k}={v}' for k, v in sorted(origins.items()))

            status = 'OK'
            if count > 8:
                status = 'CRITICAL'
            elif count > 4:
                status = 'WARNING'

            print(f"[{ts}] [{status}] {count} python, {total_mem:.0f}MB | {origin_str}")

            if new_pids:
                for pid in new_pids:
                    info = next((p for p in processes if p['pid'] == pid), None)
                    if info:
                        print(f"  + NEW PID {pid} [{info.get('origin','?')}] parent={info.get('parent_name','?')} cmd={info['cmdline'][:60]}")

            if gone_pids:
                print(f"  - Exited: {', '.join(str(p) for p in gone_pids)}")

            prev_pids = cur_pids

            # CPU monitoring
            total_cpu = _get_total_cpu()
            if total_cpu >= CPU_ALERT_THRESHOLD:
                if cpu_high_since is None:
                    cpu_high_since = time.time()
                    print(f"  [ALERT] System CPU at {total_cpu:.0f}% -- monitoring...")

                elapsed = time.time() - cpu_high_since
                print(f"  [ALERT] CPU >= {CPU_ALERT_THRESHOLD}% for {elapsed:.0f}s / {CPU_KILL_SECONDS}s")

                if auto_kill and elapsed >= CPU_KILL_SECONDS:
                    print(f"  [AUTO-KILL] CPU >= {CPU_ALERT_THRESHOLD}% for {CPU_KILL_SECONDS}s -- killing orphans + relaunching...")
                    _emergency_kill_and_relaunch(processes)
                    cpu_high_since = None
            else:
                if cpu_high_since is not None:
                    print(f"  [OK] CPU dropped to {total_cpu:.0f}% -- alert cleared")
                cpu_high_since = None

            # Rotate logs daily
            _rotate_logs()

        except Exception as e:
            print(f"  [ERROR] Watch cycle failed: {e}")

        # Sleep in small increments so Ctrl+C is responsive
        for _ in range(WATCH_INTERVAL):
            if not running:
                break
            time.sleep(1)

    print("\nWatch mode stopped.")


def _emergency_kill_and_relaunch(processes):
    """
    Kill all non-essential Python processes, then relaunch Flask.
    Preserves only the watchdog (self) process.
    """
    try:
        import psutil
    except ImportError:
        print("  [ERROR] psutil required for auto-kill")
        return

    # Kill everything except self
    killed = 0
    for p in processes:
        if p['is_self']:
            continue
        try:
            proc = psutil.Process(p['pid'])
            proc.terminate()
            proc.wait(timeout=5)
            killed += 1
            print(f"    Killed PID {p['pid']} ({p.get('origin','?')})")
        except Exception:
            try:
                psutil.Process(p['pid']).kill()
                killed += 1
            except Exception:
                pass

    print(f"  Killed {killed} processes. Waiting 3s for ports to free...")
    time.sleep(3)

    # Relaunch Flask server
    import subprocess
    python_exe = os.path.join(PROJECT_ROOT, 'venv', 'Scripts', 'python.exe')
    if not os.path.exists(python_exe):
        print(f"  [ERROR] Cannot relaunch -- {python_exe} not found")
        return

    launcher = os.path.join(PROJECT_ROOT, 'launcher.py')
    if not os.path.exists(launcher):
        print(f"  [ERROR] Cannot relaunch -- launcher.py not found")
        return

    try:
        subprocess.Popen(
            [python_exe, launcher, '--mode=dev'],
            cwd=PROJECT_ROOT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"  [RELAUNCH] Flask server restarted via launcher.py")
    except Exception as e:
        print(f"  [ERROR] Failed to relaunch: {e}")


# -- Main ----------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Process Guard -- detect/kill/watch orphaned Python processes')
    parser.add_argument('--kill', action='store_true', help='Kill high-CPU/memory orphans')
    parser.add_argument('--kill-all', action='store_true', help='Kill ALL Python processes except self')
    parser.add_argument('--watch', action='store_true', help='Continuous monitoring with CSV logging')
    parser.add_argument('--auto-kill', action='store_true',
                        help='With --watch: auto-kill + relaunch if CPU > 95%% for 3 min')
    args = parser.parse_args()

    if args.watch:
        watch(auto_kill=args.auto_kill)
        return

    processes = _get_processes()
    report(processes)

    if args.kill or args.kill_all:
        killed = kill_orphans(processes, aggressive=args.kill_all)
        print(f"Killed {killed} process(es).")
        remaining = _get_processes()
        print(f"Remaining: {len(remaining)} Python process(es)")

    sys.exit(1 if len(processes) > 8 else 0)


if __name__ == '__main__':
    main()

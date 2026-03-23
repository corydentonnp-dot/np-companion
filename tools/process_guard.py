"""
Process Guard — Detects and kills orphaned Python processes.

Usage:
    python tools/process_guard.py              # Report only
    python tools/process_guard.py --kill       # Kill orphans (high CPU/memory)
    python tools/process_guard.py --kill-all   # Kill ALL Python except self

Called by Copilot agent at session start/end to prevent 160+ process pileups.
"""

import os
import sys
import argparse

def _get_processes():
    """Return list of python process dicts using psutil."""
    try:
        import psutil
    except ImportError:
        print("[WARN] psutil not installed — falling back to tasklist")
        return _get_processes_tasklist()

    results = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'cmdline', 'create_time']):
        try:
            name = proc.info['name'] or ''
            if 'python' not in name.lower():
                continue
            mem_mb = (proc.info['memory_info'].rss / 1024 / 1024) if proc.info['memory_info'] else 0
            cmdline = ' '.join(proc.info['cmdline'] or [])
            results.append({
                'pid': proc.info['pid'],
                'name': name,
                'cpu': proc.info['cpu_percent'] or 0,
                'mem_mb': round(mem_mb, 1),
                'cmdline': cmdline[:120],
                'is_self': proc.info['pid'] == os.getpid(),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
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
                results.append({
                    'pid': int(parts[1]),
                    'name': parts[0],
                    'cpu': 0,
                    'mem_mb': round(int(parts[4].replace(' K', '').replace(',', '').strip()) / 1024, 1),
                    'cmdline': '',
                    'is_self': int(parts[1]) == os.getpid(),
                })
        return results
    except Exception as e:
        print(f"[ERROR] tasklist failed: {e}")
        return []


def report(processes):
    """Print process summary."""
    count = len(processes)
    total_mem = sum(p['mem_mb'] for p in processes)
    print(f"\n=== Python Process Report ===")
    print(f"Total: {count} processes, {total_mem:.0f} MB memory")
    if count > 8:
        print(f"[CRITICAL] {count} Python processes — exceeds safe limit of 8!")
    elif count > 4:
        print(f"[WARNING] {count} Python processes — approaching safe limit of 4")
    else:
        print(f"[OK] Process count within safe limits")

    print(f"\n{'PID':>8}  {'CPU%':>5}  {'MEM MB':>7}  {'SELF':>4}  CMD")
    print("-" * 80)
    for p in sorted(processes, key=lambda x: x['mem_mb'], reverse=True):
        marker = " <--" if p['is_self'] else ""
        print(f"{p['pid']:>8}  {p['cpu']:>5.1f}  {p['mem_mb']:>7.1f}  {'YES' if p['is_self'] else '':>4}  {p['cmdline'][:50]}{marker}")
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
                print(f"  Killed PID {p['pid']} (CPU={p['cpu']:.0f}%, MEM={p['mem_mb']:.0f}MB)")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            try:
                psutil.Process(p['pid']).kill()
                killed += 1
                print(f"  Force-killed PID {p['pid']}")
            except Exception:
                pass
    return killed


def main():
    parser = argparse.ArgumentParser(description='Process Guard — detect/kill orphaned Python processes')
    parser.add_argument('--kill', action='store_true', help='Kill high-CPU/memory orphans')
    parser.add_argument('--kill-all', action='store_true', help='Kill ALL Python processes except self')
    args = parser.parse_args()

    processes = _get_processes()
    report(processes)

    if args.kill or args.kill_all:
        killed = kill_orphans(processes, aggressive=args.kill_all)
        print(f"Killed {killed} process(es).")
        # Re-check
        remaining = _get_processes()
        print(f"Remaining: {len(remaining)} Python process(es)")

    # Exit code: 1 if critical, 0 if OK
    sys.exit(1 if len(processes) > 8 else 0)


if __name__ == '__main__':
    main()

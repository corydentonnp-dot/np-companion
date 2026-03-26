"""
CareCompanion -- Database Snapshot/Restore
scripts/db_snapshot.py

Creates a timestamped copy of the SQLite database before destructive testing,
and restores it afterwards.

Usage:
    venv\\Scripts\\python.exe scripts/db_snapshot.py --action snapshot
    venv\\Scripts\\python.exe scripts/db_snapshot.py --action restore
    venv\\Scripts\\python.exe scripts/db_snapshot.py --action list

Exit codes:
    0 = success
    1 = failure
"""

import argparse
import os
import shutil
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, 'data', 'carecompanion.db')
SNAPSHOT_DIR = os.path.join(ROOT, 'data', 'backups', 'snapshots')


def snapshot():
    """Create a timestamped copy of the database."""
    if not os.path.exists(DB_PATH):
        print(f'ERROR: Database not found at {DB_PATH}')
        return 1

    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(SNAPSHOT_DIR, f'carecompanion_{timestamp}.db')

    try:
        shutil.copy2(DB_PATH, dest)
        size_mb = os.path.getsize(dest) / (1024 * 1024)
        print(f'Snapshot created: {dest} ({size_mb:.1f} MB)')
        return 0
    except Exception as e:
        print(f'ERROR: Failed to create snapshot: {e}')
        return 1


def restore():
    """Restore the most recent snapshot."""
    if not os.path.exists(SNAPSHOT_DIR):
        print('ERROR: No snapshots directory found. Run --action snapshot first.')
        return 1

    snapshots = sorted([
        f for f in os.listdir(SNAPSHOT_DIR)
        if f.startswith('carecompanion_') and f.endswith('.db')
    ])

    if not snapshots:
        print('ERROR: No snapshots found.')
        return 1

    latest = os.path.join(SNAPSHOT_DIR, snapshots[-1])
    print(f'Restoring from: {latest}')

    try:
        shutil.copy2(latest, DB_PATH)
        size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
        print(f'Database restored ({size_mb:.1f} MB)')
        return 0
    except Exception as e:
        print(f'ERROR: Failed to restore: {e}')
        return 1


def list_snapshots():
    """List all available snapshots."""
    if not os.path.exists(SNAPSHOT_DIR):
        print('No snapshots directory found.')
        return 0

    snapshots = sorted([
        f for f in os.listdir(SNAPSHOT_DIR)
        if f.startswith('carecompanion_') and f.endswith('.db')
    ])

    if not snapshots:
        print('No snapshots found.')
        return 0

    print(f'Available snapshots ({len(snapshots)}):')
    for s in snapshots:
        path = os.path.join(SNAPSHOT_DIR, s)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f'  {s} ({size_mb:.1f} MB)')

    return 0


def main():
    parser = argparse.ArgumentParser(description='CareCompanion DB Snapshot/Restore')
    parser.add_argument(
        '--action', required=True, choices=['snapshot', 'restore', 'list'],
        help='Action to perform: snapshot, restore, or list'
    )
    args = parser.parse_args()

    if args.action == 'snapshot':
        return snapshot()
    elif args.action == 'restore':
        return restore()
    elif args.action == 'list':
        return list_snapshots()


if __name__ == '__main__':
    sys.exit(main())

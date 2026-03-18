"""
NP Companion — Self-Update Mechanism

Scans a folder for update zips (NP_Companion_v*.zip), compares versions,
and applies updates by replacing _internal/ + exe while preserving data/.
"""

import glob
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

logger = logging.getLogger('updater')

# Files/folders that are NEVER overwritten during updates
_PRESERVE = {'data', 'config.py', 'browsers', 'tesseract'}


def _parse_version(v: str) -> tuple:
    """Parse '1.2.3' into (1, 2, 3) for comparison."""
    parts = re.findall(r'\d+', v)
    return tuple(int(p) for p in parts)


def check_for_update(folder_path: str, current_version: str) -> dict | None:
    """
    Scan *folder_path* for NP_Companion_v*.zip files.
    Returns info about the newest version if it is newer than *current_version*,
    otherwise returns None.
    """
    if not folder_path or not os.path.isdir(folder_path):
        return None

    pattern = os.path.join(folder_path, 'NP_Companion_v*.zip')
    zips = glob.glob(pattern)
    if not zips:
        return None

    current = _parse_version(current_version)
    best = None

    for zp in zips:
        fname = os.path.basename(zp)
        match = re.search(r'v([\d.]+)', fname)
        if not match:
            continue
        ver_str = match.group(1)
        ver = _parse_version(ver_str)
        if ver > current:
            if best is None or ver > best['ver_tuple']:
                release_notes = _read_release_notes(zp)
                best = {
                    'version': ver_str,
                    'ver_tuple': ver,
                    'zip_path': zp,
                    'zip_name': fname,
                    'release_notes': release_notes,
                }

    if best:
        best.pop('ver_tuple')
        return best
    return None


def _read_release_notes(zip_path: str) -> str:
    """Try to read release_notes.txt from inside the zip."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if name.lower().endswith('release_notes.txt'):
                    return zf.read(name).decode('utf-8', errors='replace')
    except Exception:
        pass
    return ''


def apply_update(zip_path: str) -> dict:
    """
    Extract the update zip and replace the application files while
    preserving data/, config.py, browsers/, and tesseract/.

    Returns {'success': bool, 'message': str}
    """
    from utils.paths import get_base_dir, is_frozen

    base = get_base_dir()
    logger.info(f'Applying update from {zip_path} to {base}')

    try:
        # 1. Extract to a temp directory next to the base
        tmp_dir = tempfile.mkdtemp(dir=base, prefix='_update_')
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(tmp_dir)

        # The zip may contain a top-level folder (NP_Companion/) — detect it
        contents = os.listdir(tmp_dir)
        source = tmp_dir
        if len(contents) == 1 and os.path.isdir(os.path.join(tmp_dir, contents[0])):
            source = os.path.join(tmp_dir, contents[0])

        # 2. Copy extracted files into base, skipping preserved items
        updated = 0
        for item in os.listdir(source):
            if item.lower() in {p.lower() for p in _PRESERVE}:
                continue
            if item.startswith('_update_'):
                continue

            src = os.path.join(source, item)
            dst = os.path.join(base, item)

            # For the running exe: rename before replacing
            if is_frozen() and item.lower() == os.path.basename(sys.executable).lower():
                old_exe = dst + '.old'
                try:
                    if os.path.exists(old_exe):
                        os.remove(old_exe)
                    os.rename(dst, old_exe)
                except OSError as e:
                    logger.warning(f'Could not rename running exe: {e}')

            # Replace directories entirely
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst, ignore_errors=True)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            updated += 1

        # 3. Clean up temp directory
        shutil.rmtree(tmp_dir, ignore_errors=True)

        logger.info(f'Update applied: {updated} items replaced')
        return {'success': True, 'message': f'Updated {updated} items. Restart to use the new version.'}

    except Exception as e:
        logger.error(f'Update failed: {e}', exc_info=True)
        # Clean up on failure
        if 'tmp_dir' in locals():
            shutil.rmtree(tmp_dir, ignore_errors=True)
        return {'success': False, 'message': str(e)}


def restart_after_update():
    """
    Launch the new exe and exit the current process.
    Works for both frozen and dev mode.
    """
    logger.info('Restarting after update...')
    subprocess.Popen(
        [sys.executable] + (['--mode=all'] if getattr(sys, 'frozen', False) else sys.argv),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    sys.exit(0)

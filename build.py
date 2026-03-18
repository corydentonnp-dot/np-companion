"""
NP Companion — Build Script

Creates a distributable .exe package using PyInstaller.

Usage:
    python build.py                     # Build zip in dist/
    python build.py --usb E:            # Build + copy zip to USB drive
    python build.py --open-drive        # Build + open Google Drive folder
    python build.py --bump patch        # Bump version (major/minor/patch) then build
    python build.py --notes "Fixed X"   # Include release notes in the zip

Requirements:
    pip install pyinstaller pillow
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import webbrowser
import zipfile


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_DIR, 'dist')
BUILD_DIR = os.path.join(PROJECT_DIR, 'build')
CONFIG_FILE = os.path.join(PROJECT_DIR, 'config.py')
SPEC_FILE = os.path.join(PROJECT_DIR, 'npcompanion.spec')
ICON_FILE = os.path.join(PROJECT_DIR, 'NP_Companion.ico')
APP_NAME = 'NP_Companion'


# ── Version helpers ──────────────────────────────────────────────

def _read_version() -> str:
    with open(CONFIG_FILE, 'r') as f:
        for line in f:
            m = re.match(r'^APP_VERSION\s*=\s*["\'](.+?)["\']', line)
            if m:
                return m.group(1)
    raise RuntimeError('APP_VERSION not found in config.py')


def _write_version(new_ver: str):
    text = open(CONFIG_FILE, 'r').read()
    text = re.sub(
        r'(APP_VERSION\s*=\s*["\'])(.+?)(["\'])',
        rf'\g<1>{new_ver}\g<3>',
        text, count=1,
    )
    with open(CONFIG_FILE, 'w') as f:
        f.write(text)
    print(f'  Version bumped to {new_ver}')


def _bump(version: str, part: str) -> str:
    major, minor, patch = (int(x) for x in version.split('.'))
    if part == 'major':
        return f'{major+1}.0.0'
    elif part == 'minor':
        return f'{major}.{minor+1}.0'
    else:
        return f'{major}.{minor}.{patch+1}'


# ── Icon generator ───────────────────────────────────────────────

def _ensure_icon():
    if os.path.isfile(ICON_FILE):
        return
    print('  Generating app icon...')
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print('  [WARN] Pillow not installed — skipping icon generation')
        return

    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    for sz in sizes:
        img = Image.new('RGBA', (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Navy blue circle
        draw.ellipse((1, 1, sz-2, sz-2), fill=(27, 58, 107, 255))
        # White "NP" text
        font_size = max(sz // 3, 8)
        try:
            font = ImageFont.truetype('arial.ttf', font_size)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), 'NP', font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (sz - tw) // 2
        y = (sz - th) // 2
        draw.text((x, y), 'NP', fill=(255, 255, 255, 255), font=font)
        images.append(img)

    images[0].save(ICON_FILE, format='ICO', sizes=[(s, s) for s in sizes], append_images=images[1:])
    print(f'  Icon saved: {ICON_FILE}')


# ── Build ────────────────────────────────────────────────────────

def _run_pyinstaller():
    print('\n  Running PyInstaller...')
    pyinstaller_exe = os.path.join(PROJECT_DIR, 'venv', 'Scripts', 'pyinstaller.exe')
    if not os.path.isfile(pyinstaller_exe):
        pyinstaller_exe = 'pyinstaller'  # fall back to PATH
    cmd = [pyinstaller_exe, '--noconfirm', SPEC_FILE]
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    if result.returncode != 0:
        print('  [ERROR] PyInstaller failed.')
        sys.exit(1)
    print('  PyInstaller complete.')


def _create_zip(version: str, release_notes: str | None) -> str:
    out_dir = os.path.join(DIST_DIR, APP_NAME)
    if not os.path.isdir(out_dir):
        print(f'  [ERROR] Expected output at {out_dir}')
        sys.exit(1)

    zip_name = f'{APP_NAME}_v{version}.zip'
    zip_path = os.path.join(DIST_DIR, zip_name)

    # Write release notes inside the folder before zipping
    if release_notes:
        notes_file = os.path.join(out_dir, 'release_notes.txt')
        with open(notes_file, 'w') as f:
            f.write(f'NP Companion v{version}\n')
            f.write('=' * 40 + '\n\n')
            f.write(release_notes + '\n')

    print(f'  Creating {zip_name}...')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(out_dir):
            # Skip data dir in the zip — users keep their own
            rel_root = os.path.relpath(root, out_dir)
            if rel_root == 'data' or rel_root.startswith('data' + os.sep):
                continue
            for fname in files:
                filepath = os.path.join(root, fname)
                arcname = os.path.join(APP_NAME, os.path.relpath(filepath, out_dir))
                zf.write(filepath, arcname)

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f'  Zip created: {zip_path} ({size_mb:.1f} MB)')
    return zip_path


# ── Delivery ─────────────────────────────────────────────────────

def _copy_to_usb(zip_path: str, usb_drive: str):
    dest = os.path.join(usb_drive, os.path.basename(zip_path))
    print(f'  Copying to USB: {dest}')
    shutil.copy2(zip_path, dest)
    print('  Done.')


def _open_google_drive():
    """Open Google Drive in the browser for manual upload."""
    print('  Opening Google Drive...')
    webbrowser.open('https://drive.google.com')


# ── Main ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Build NP Companion .exe')
    parser.add_argument('--bump', choices=['major', 'minor', 'patch'],
                        help='Bump version before building')
    parser.add_argument('--usb', metavar='DRIVE',
                        help='Copy zip to USB drive (e.g., E:)')
    parser.add_argument('--open-drive', action='store_true',
                        help='Open Google Drive after building')
    parser.add_argument('--notes', metavar='TEXT',
                        help='Release notes to include in the zip')
    parser.add_argument('--no-build', action='store_true',
                        help='Skip PyInstaller (just zip and deliver)')
    args = parser.parse_args()

    print(f'NP Companion Build Script')
    print(f'========================\n')

    # 1. Bump version
    version = _read_version()
    if args.bump:
        version = _bump(version, args.bump)
        _write_version(version)
    print(f'  Version: {version}')

    # 2. Generate icon if needed
    _ensure_icon()

    # 3. Run PyInstaller
    if not args.no_build:
        _run_pyinstaller()

    # 4. Create zip
    zip_path = _create_zip(version, args.notes)

    # 5. Deliver
    if args.usb:
        _copy_to_usb(zip_path, args.usb)
    if args.open_drive:
        _open_google_drive()

    print(f'\n  Build complete! Zip: {zip_path}')
    print(f'  Transfer this zip to the work PC and use Admin > Updates to install.')


if __name__ == '__main__':
    main()

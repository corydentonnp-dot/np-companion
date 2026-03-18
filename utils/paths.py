"""
NP Companion — Path Resolution for Frozen (PyInstaller) and Dev Modes

Usage:
    from utils.paths import get_base_dir, get_resource_dir, get_data_dir, ...
"""

import os
import sys


def is_frozen() -> bool:
    """True when running inside a PyInstaller bundle."""
    return getattr(sys, 'frozen', False)


def get_base_dir() -> str:
    """
    The folder that contains the .exe (frozen) or the project root (dev).
    Writable — config.py and data/ live here.
    """
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_dir() -> str:
    """
    Where PyInstaller unpacks bundled files (templates, static, etc.).
    In dev mode, same as get_base_dir().
    """
    if is_frozen():
        return sys._MEIPASS
    return get_base_dir()


def get_data_dir() -> str:
    """
    Writable data directory: <base_dir>/data/
    Never overwritten by updates.
    """
    d = os.path.join(get_base_dir(), 'data')
    os.makedirs(d, exist_ok=True)
    return d


def get_tesseract_path() -> str:
    """
    Path to tesseract.exe. Uses the bundled copy when frozen,
    otherwise falls back to config.py setting.
    """
    if is_frozen():
        bundled = os.path.join(get_base_dir(), 'tesseract', 'tesseract.exe')
        if os.path.isfile(bundled):
            return bundled
    import config as cfg
    return getattr(cfg, 'TESSERACT_PATH', r'C:\Program Files\Tesseract-OCR\tesseract.exe')


def get_playwright_browsers_path() -> str:
    """
    Playwright Chromium browser directory.
    Bundled in <base_dir>/browsers/ when frozen.
    """
    if is_frozen():
        return os.path.join(get_base_dir(), 'browsers')
    return ''


def get_config_path() -> str:
    """
    Path to the user-editable config.py next to the exe (frozen)
    or in the project root (dev).
    """
    return os.path.join(get_base_dir(), 'config.py')


def get_db_path() -> str:
    """Full path to the SQLite database file."""
    return os.path.join(get_data_dir(), 'npcompanion.db')


def get_icon_path() -> str:
    """Path to the app icon file."""
    # Check next to exe first, then in resources
    for base in [get_base_dir(), get_resource_dir()]:
        p = os.path.join(base, 'NP_Companion.ico')
        if os.path.isfile(p):
            return p
    return ''

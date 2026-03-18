# -*- mode: python ; coding: utf-8 -*-
"""
NP Companion — PyInstaller Spec File

Build with:   pyinstaller --noconfirm npcompanion.spec
Or via:       python build.py
"""

import os
import sys

block_cipher = None
PROJECT = os.path.dirname(os.path.abspath(SPECPATH))

a = Analysis(
    ['launcher.py'],
    pathex=[PROJECT],
    binaries=[],
    datas=[
        # Templates and static assets — bundled into _internal
        ('templates', 'templates'),
        ('static', 'static'),
    ],
    hiddenimports=[
        # ── Flask & extensions ──
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'flask_bcrypt',
        'jinja2',
        'werkzeug',
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'greenlet',
        'bcrypt',
        'cffi',
        'cryptography',
        'cryptography.fernet',
        'itsdangerous',
        'markupsafe',
        'blinker',
        'click',
        'colorama',

        # ── Web view & tray ──
        'webview',
        'pystray',
        'pystray._win32',

        # ── Scheduling ──
        'apscheduler',
        'apscheduler.schedulers.background',
        'apscheduler.triggers.interval',
        'apscheduler.triggers.cron',

        # ── Windows automation ──
        'pyautogui',
        'pyperclip',
        'pytesseract',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'PIL.ImageEnhance',
        'PIL.ImageGrab',
        'win32gui',
        'win32con',
        'win32api',
        'psutil',
        'ctypes',
        'ctypes.wintypes',
        'mouseinfo',
        'pygetwindow',
        'pymsgbox',
        'pyrect',
        'pyscreeze',
        'pytweening',

        # ── Playwright ──
        'playwright',
        'playwright.sync_api',
        'playwright.async_api',
        'pyee',

        # ── Notifications ──
        'plyer',
        'plyer.platforms.win.notification',

        # ── File monitoring ──
        'watchdog',
        'watchdog.observers',
        'watchdog.events',

        # ── Standard library extras ──
        'json',
        'csv',
        'io',
        'hashlib',
        'pickle',
        'secrets',
        'asyncio',
        'xml.etree.ElementTree',
        'http.server',
        'urllib.request',
        'urllib.error',

        # ── Project modules ──
        'config',
        'utils',
        'utils.paths',
        'utils.updater',
        'models',
        'models.user',
        'models.audit',
        'models.timelog',
        'models.inbox',
        'models.oncall',
        'models.orderset',
        'models.medication',
        'models.labtrack',
        'models.caregap',
        'models.tickler',
        'models.message',
        'models.reformatter',
        'models.agent',
        'models.schedule',
        'models.patient',
        'routes',
        'routes.admin',
        'routes.agent_api',
        'routes.auth',
        'routes.caregap',
        'routes.dashboard',
        'routes.inbox',
        'routes.labtrack',
        'routes.medref',
        'routes.metrics',
        'routes.netpractice_admin',
        'routes.oncall',
        'routes.orders',
        'routes.timer',
        'routes.tools',
        'routes.patient',
        'routes.ai_api',
        'agent_service',
        'agent',
        'agent.ac_window',
        'agent.caregap_engine',
        'agent.clinical_summary_parser',
        'agent.inbox_digest',
        'agent.inbox_monitor',
        'agent.inbox_reader',
        'agent.mrn_reader',
        'agent.notifier',
        'agent.ocr_helpers',
        'agent.pyautogui_runner',
        'agent.scheduler',
        'scrapers',
        'scrapers.netpractice',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Large packages we don't need
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'notebook',
        'pytest',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NP_Companion',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,        # No console window — we use pywebview
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(PROJECT, 'NP_Companion.ico') if os.path.isfile(os.path.join(PROJECT, 'NP_Companion.ico')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NP_Companion',
)

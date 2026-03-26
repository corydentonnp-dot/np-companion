"""
CareCompanion Configuration

WARNING:
- Never commit this file to Git. It contains machine-specific settings and secrets.
- Add `config.py` to `.gitignore`.
- For production, set sensitive values via environment variables.
  See .env.example for the full list of env vars.

Program location in project structure:
- This file lives at the project root: carecompanion/config.py
- It should be in the same folder level as app.py, agent.py, and requirements.txt.
"""

import os
import secrets
import shutil
from datetime import timedelta

# ============================================================
# APP VERSION & UPDATE
# ============================================================
APP_VERSION = "1.1.4"
UPDATE_FOLDER = ""   # Path to folder containing update zips (Downloads, USB, Google Drive, etc.)

# ============================================================
# SECTION 1 - SERVER SETTINGS
# ============================================================
HOST = "0.0.0.0"
PORT = 5000

# Stable SECRET_KEY — persisted to data/.secret_key so sessions survive restarts.
# If the file doesn't exist yet, one is generated and saved automatically.
def _load_or_create_secret_key():
    key_path = os.path.join(os.path.dirname(__file__), "data", ".secret_key")
    if os.path.exists(key_path):
        with open(key_path, "r") as f:
            key = f.read().strip()
        if key:
            return key
    key = secrets.token_hex(32)
    os.makedirs(os.path.dirname(key_path), exist_ok=True)
    with open(key_path, "w") as f:
        f.write(key)
    return key

SECRET_KEY = os.getenv("SECRET_KEY", "") or _load_or_create_secret_key()
DEBUG = False  # Set to True for development only
TEMPLATES_AUTO_RELOAD = True  # Always reload templates on edit

# Session security
SESSION_COOKIE_HTTPONLY = True       # JS cannot read session cookie
SESSION_COOKIE_SAMESITE = 'Lax'     # Prevent CSRF via cross-site requests
PERMANENT_SESSION_LIFETIME = timedelta(hours=12)  # Session expires after 12h
REMEMBER_COOKIE_DURATION = timedelta(days=7)       # "Remember me" lasts 7 days
REMEMBER_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_SAMESITE = 'Lax'

# ============================================================
# SECTION 2 - MACHINE SETTINGS
# ============================================================
# Set AC_MOCK_MODE = True to test without Amazing Charts installed.
# The agent will use screenshot images from Documents/ac_interface_reference/
# instead of live screen captures. Set to False for real deployment.
AC_MOCK_MODE = False

SCREEN_RESOLUTION = (1920, 1080)
MRN_CAPTURE_REGION = (0, 0, 300, 50)
# The executable process name (as seen in Task Manager / psutil)
AMAZING_CHARTS_PROCESS_NAME = "AmazingCharts.exe"
# The window title prefix (as seen in win32gui window title bar)
# Real title is "Amazing Charts EHR (32 bit)" — startswith() match works
AC_WINDOW_TITLE_PREFIX = "Amazing Charts"

# AC system information (confirmed from AC Interface Reference v4)
AC_VERSION = "12.3.1"
AC_BUILD = "297"
AC_PRACTICE_ID = 2799
AC_PRACTICE_NAME = "Family Practice Associates of Chesterfield"
AC_EXE_PATH = r"C:\Program Files (x86)\Amazing Charts\AmazingCharts.exe"
AC_LOG_PATH = r"C:\Program Files (x86)\Amazing Charts\Logs"
AC_DB_PATH = r"\\192.168.2.51\Amazing Charts\AmazingCharts.mdf"
AC_IMPORTED_ITEMS_PATH = r"\\192.168.2.51\amazing charts\ImportItems"

# Login credentials for AC auto-login (fill at deployment)
AC_LOGIN_USERNAME = os.getenv("AC_LOGIN_USERNAME", "CORY")
AC_LOGIN_PASSWORD = os.getenv("AC_LOGIN_PASSWORD", "")

# Work PC specs (confirmed from v4)
WORK_PC_OS = "Windows 11 Pro"
WORK_PC_NAME = "FPA-D-NP-DENTON"
WORK_PC_RESOLUTION = (1920, 1080)
WORK_PC_MONITORS = 2

# AC application states — used by ac_window.get_ac_state()
AC_STATES = {
    'not_running': 'No AC process found',
    'login_screen': 'AC is open at login prompt',
    'home_screen': 'AC logged in, home screen visible',
    'chart_open': 'Patient chart window is open',
}

# Valid AC order tab names (confirmed from AC orders spreadsheet)
ORDER_TABS = [
    'Nursing', 'Labs', 'Imaging', 'Diagnostics',
    'Referrals', 'Follow Up', 'Patient Education', 'Other',
]

# Auto-detect Tesseract: PATH → bundled → hardcoded fallback
TESSERACT_PATH = os.getenv("TESSERACT_PATH") or \
    shutil.which("tesseract") or \
    (os.path.join(os.path.dirname(__file__), "tesseract", "tesseract.exe")
     if os.path.isfile(os.path.join(os.path.dirname(__file__), "tesseract", "tesseract.exe"))
     else r"C:\Users\FPA\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")

# ============================================================
# SECTION 3 - NETPRACTICE SETTINGS
# ============================================================
NETPRACTICE_URL = "https://wppm2.cgmus.com/scripts/npm7.mar"
NETPRACTICE_BOOKMARKED_URL = "https://wppm2.cgmus.com/scripts/npm7.mar?wlapp=npm7&MGWCHD=p"
NETPRACTICE_CLIENT_NUMBER = "2034"
SESSION_COOKIE_FILE = "data/np_session.json"
CHROME_CDP_PORT = 9222  # Chrome must be started with --remote-debugging-port=9222

# Chrome 136+ debug profile (May 2025+)
# Chrome 136 ignores --remote-debugging-port with the default profile.
# A dedicated --user-data-dir is required for CDP to work.
CHROME_EXE_PATH = os.getenv(
    "CHROME_EXE_PATH",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
)
CHROME_DEBUG_PROFILE_DIR = os.getenv(
    "CHROME_DEBUG_PROFILE_DIR",
    os.path.join(os.environ.get("USERPROFILE", ""), "chrome-debug-profile")
)

# ============================================================
# SECTION 4 - NOTIFICATION SETTINGS
# ============================================================
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY", "")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN", "")
PUSHOVER_EMAIL = os.getenv("PUSHOVER_EMAIL", "")
NOTIFY_QUIET_HOURS_START = 22
NOTIFY_QUIET_HOURS_END = 7

# ============================================================
# SECTION 5 - DATABASE SETTINGS
# ============================================================
DATABASE_PATH = "data/carecompanion.db"
BACKUP_PATH = "data/backups/"

# ============================================================
# SECTION 6 - INBOX MONITOR SETTINGS
# ============================================================
INBOX_CHECK_INTERVAL_MINUTES = 120
CRITICAL_VALUE_KEYWORDS = ["critical", "panic", "STAT", "HIGH", "LOW"]

# ============================================================
# SECTION 7 - AMAZING CHARTS AUTOMATION
# ============================================================
# OCR-FIRST APPROACH: The agent uses Tesseract OCR to locate UI elements
# by their visible text labels (e.g. "Show Charts", "Patient List",
# "Export Clinical Summary"). This works across any screen resolution,
# window size, or window position — no per-machine calibration needed.
#
# The coordinate values below are FALLBACK ONLY. They are used if OCR
# fails to find the expected text. Set them to (0, 0) to disable
# fallbacks and run pure OCR. You should only need to set these if
# Tesseract consistently fails on a specific element.
#
# See agent/ocr_helpers.py for the OCR detection engine.
# See agent/ac_interact.py for the 3-tier interaction engine (UIA → OCR → coordinates).
# ============================================================
IDLE_THRESHOLD_SECONDS = 300
MAX_CHART_OPEN_MINUTES = 20

# --- UIA + Win32 interaction settings ---
# AC_USE_UIA: Enable Windows UI Automation for AC element detection.
# Set False to skip UIA and use OCR-only (original behavior).
AC_USE_UIA = True

# AC_INTERACTION_TIER: Controls the priority order for AC automation.
#   'uia_first'  — try UIA, then OCR, then coordinates (recommended)
#   'ocr_first'  — try OCR, then coordinates (original behavior)
#   'legacy'     — coordinates only (for debugging)
AC_INTERACTION_TIER = 'uia_first'

# AC_UIA_TIMEOUT: Seconds to wait for UIA control search before
# falling back to OCR. Lower = faster fallback, higher = more patient.
AC_UIA_TIMEOUT = 1.5

# Fallback coordinates — used ONLY when OCR cannot find the element.
# Set to (0, 0) to disable a fallback and rely purely on OCR.
INBOX_FILTER_DROPDOWN_XY = (0, 0)          # Fallback: inbox filter dropdown
INBOX_TABLE_REGION = (0, 0, 0, 0)          # Fallback: inbox table area (x, y, w, h)
PATIENT_LIST_ID_SEARCH_XY = (0, 0)         # Fallback: Patient List ID search field
VISIT_TEMPLATE_RADIO_XY = (0, 0)           # Fallback: Visit Template radio button
SELECT_TEMPLATE_DROPDOWN_XY = (0, 0)       # Fallback: template dropdown
EXPORT_CLIN_SUM_MENU_XY = (0, 0)           # Fallback: Patient > Export Clinical Summary
EXPORT_BUTTON_XY = (0, 0)                  # Fallback: Export button in dialog
CLINICAL_SUMMARY_EXPORT_FOLDER = "data/clinical_summaries/"  # CareCompanion clicks Browse in AC and saves here
CLINICAL_SUMMARY_RETENTION_DAYS = 183
INBOX_WARNING_HOURS = 48
INBOX_CRITICAL_HOURS = 72

# Inbox Digest (F5e)
INBOX_DIGEST_ENABLED = True
INBOX_DIGEST_HOURS = 24            # Lookback window for digest summary
INBOX_DIGEST_SEND_HOUR = 17       # Hour (24h) to send daily digest push (e.g. 17 = 5 PM)
INBOX_DIGEST_SEND_MINUTE = 0

# ============================================================
# SECTION 8 - TEST DATA
# ============================================================
# When True, a perpetual 07:00 test patient appointment (TEST, TEST / MRN 62815)
# appears on the dashboard every day. Toggle via Admin > Config Settings.
TEST_PATIENT_APPOINTMENT_ENABLED = True

# Canonical location for all demo/test patient CDA XML files.
# Used by seed_test_data, admin purge/reimport, generate_test_xmls, and tests.
DEMO_PATIENTS_DIR = os.path.join(os.path.dirname(__file__), 'Documents', 'demo_patients')

# ============================================================
# SECTION 9 - API INTELLIGENCE KEYS
# ============================================================
# These are optional keys that improve rate limits and unlock
# additional features. The system works without them using
# anonymous/free tiers.

# OpenFDA — increases rate limit from 40/min to 240/min
# Register: https://open.fda.gov/apis/authentication/
OPENFDA_API_KEY = os.getenv("OPENFDA_API_KEY", "")

# NCBI PubMed — increases rate limit from 3/sec to 10/sec
# Register: https://www.ncbi.nlm.nih.gov/account/ → Settings → API Key
PUBMED_API_KEY = os.getenv("PUBMED_API_KEY", "")

# LOINC — required for lab reference ranges (FHIR $lookup)
# Register: https://loinc.org/get-started/
LOINC_USERNAME = os.getenv("LOINC_USERNAME", "")
LOINC_PASSWORD = os.getenv("LOINC_PASSWORD", "")

# ── Benchmark Performance Thresholds (milliseconds) ──────────────
BENCHMARK_BILLING_MAX_MS = 3000      # Single patient billing evaluation (includes cold-start overhead)
BENCHMARK_CAREGAP_MAX_MS = 200       # Single patient care gap evaluation
BENCHMARK_MONITORING_MAX_MS = 300    # Single patient monitoring lookup
BENCHMARK_FULL_SUITE_MAX_MS = 15000  # Full 18-patient × 3-engine suite

# UMLS — required for terminology crosswalk and differential diagnosis
# Register: https://uts.nlm.nih.gov/uts/ (requires login.gov or similar)
# Status: ✅ APPROVED 2026-03-19 — provides UMLS API, SNOMED CT, VSAC, RxNorm downloads
UMLS_API_KEY = os.getenv("UMLS_API_KEY", "")

# Virginia Immunization Information System (VIIS)
# For future immunization registry integration
VIIS_USERNAME = os.getenv("VIIS_USERNAME", "")
VIIS_PASSWORD = os.getenv("VIIS_PASSWORD", "")
VIIS_URL = "https://viis.virginia.gov"

# VIIS batch automation settings
VIIS_BATCH_ENABLED = False            # Set True when ready to run nightly VIIS checks
VIIS_BATCH_HOUR = 18                  # Hour (0-23) to run VIIS pre-visit batch
VIIS_BATCH_MINUTE = 30                # Minute (0-59)
VIIS_CHECK_INTERVAL_DAYS = 365        # Skip patients checked within this many days
VIIS_DELAY_MIN = 5                    # Min seconds between VIIS lookups (rate limiting)
VIIS_DELAY_MAX = 15                   # Max seconds between VIIS lookups

# Virginia Prescription Monitoring Program (PDMP)
# For future controlled substance monitoring integration
PDMP_EMAIL = os.getenv("PDMP_EMAIL", "")
PDMP_PASSWORD = os.getenv("PDMP_PASSWORD", "")
PDMP_URL = "https://virginia.pmpaware.net"

# ============================================================
# SECTION 10 - SMTP / EMAIL SETTINGS
# ============================================================
# Used by agent_service.py for weekly summary and monthly billing emails.
# Leave SMTP_SERVER empty to disable email features.
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "")   # Defaults to SMTP_USER if empty
SMTP_TO = os.getenv("SMTP_TO", "")       # Recipient for summary/billing emails

# ============================================================
# SECTION 11 - MACRO & AHK SETTINGS
# ============================================================
# AHK Auto-Sync: When set to a file path, the system auto-writes the full
# AHK macro library to disk on every macro/dot-phrase save.
# Set to None (default) to disable auto-sync.
AHK_AUTO_SYNC_PATH = os.getenv("AHK_AUTO_SYNC_PATH", None)

# ============================================================
# SECTION 12 - CHART FLAG SETTINGS
# ============================================================
# When enabled, a bottom-left widget in the web UI shows which
# patient chart is currently open in Amazing Charts.
CHART_FLAG_ENABLED = True
CHART_FLAG_STALE_SECONDS = 10  # Max age of active_chart.json before considered stale

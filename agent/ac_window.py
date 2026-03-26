"""
CareCompanion — Amazing Charts Window Manager

File location: carecompanion/agent/ac_window.py

Provides pywin32-based utilities for detecting and interacting with
the Amazing Charts desktop application windows.

Feature: F6 (MRN Screen Reader + AC Window Manager)
"""

import logging
import re

import config

try:
    import win32gui
except ImportError:
    win32gui = None

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger('agent.ac_window')

# ---------------------------------------------------------------------------
# Mock-mode support: when AC_MOCK_MODE is True, every public function
# delegates to the mock provider instead of touching win32gui.
# This block is inert when AC_MOCK_MODE is False (the default).
# ---------------------------------------------------------------------------
_mock = None
if getattr(config, 'AC_MOCK_MODE', False):
    try:
        from tests import ac_mock as _mock
        logger.info('AC_MOCK_MODE active — using simulated AC window')
    except ImportError:
        logger.warning('AC_MOCK_MODE is True but tests.ac_mock not found')


# ---------------------------------------------------------------------------
# Chart title parsing regex for the AC subprocess window format:
# LASTNAME, FIRSTNAME (DOB:MM/DD/YYYY; ID: #####) XX year old SEX, Portal:YES/NO Cell: (###) ###-####
# ---------------------------------------------------------------------------
_CHART_TITLE_RE = re.compile(
    r'^(?P<last_name>[^,]+),\s*'
    r'(?P<first_name>[^(]+?)\s*'
    r'\(DOB:\s*(?P<dob>[\d/]+);\s*'
    r'ID:\s*(?P<mrn>\d+)\)\s*'
    r'(?P<age>\d+)\s+year\s+old\s+'
    r'(?P<sex>\w+)'
    r'(?:,\s*Portal:\s*(?P<portal>YES|NO))?'
    r'(?:\s+Cell:\s*(?P<cell>[\d() -]+))?',
    re.IGNORECASE
)


def parse_chart_title(title):
    """
    Parse an AC subprocess chart window title into structured patient data.

    Expected format:
        LASTNAME, FIRSTNAME (DOB:MM/DD/YYYY; ID: #####) XX year old SEX, Portal:YES/NO Cell: (###) ###-####

    Handles variations: missing Cell, missing Portal, multi-word names.

    Parameters
    ----------
    title : str
        Window title text.

    Returns
    -------
    dict | None
        Dict with keys {last_name, first_name, dob, mrn, age, sex, portal, cell}
        or None if the title doesn't match the chart format.
    """
    if not title:
        return None
    m = _CHART_TITLE_RE.search(title)
    if not m:
        return None
    return {
        'last_name': m.group('last_name').strip(),
        'first_name': m.group('first_name').strip(),
        'dob': m.group('dob'),
        'mrn': m.group('mrn'),
        'age': m.group('age'),
        'sex': m.group('sex').upper(),
        'portal': m.group('portal') or '',
        'cell': (m.group('cell') or '').strip(),
    }


def get_all_chart_windows():
    """
    Enumerate ALL visible windows and return parsed patient data for
    any that match the AC chart title format.

    Unlike get_ac_chart_title() which only checks the foreground window,
    this uses EnumWindows to find chart subprocess windows regardless
    of z-order — so the chart is detected even when the browser is in focus.

    Returns
    -------
    list[dict]
        List of parsed chart dicts from parse_chart_title().
        Empty list if no charts found.
    """
    if _mock:
        return _mock.mock_get_all_chart_windows()
    if not win32gui:
        return []

    results = []

    def _enum_cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            parsed = parse_chart_title(title)
            if parsed:
                results.append(parsed)

    try:
        win32gui.EnumWindows(_enum_cb, None)
    except Exception as e:
        logger.error(f'EnumWindows failed in get_all_chart_windows: {e}')

    return results


def find_ac_window():
    """
    Enumerate all visible windows and return the hwnd of the first
    window whose title starts with "Amazing Charts".

    Returns
    -------
    int | None
        Window handle, or None if AC is not running.
    """
    if _mock:
        return _mock.mock_find_ac_window()
    if not win32gui:
        logger.warning('win32gui not available')
        return None

    result = []

    def _enum_cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and title.startswith('Amazing Charts'):
                result.append(hwnd)

    try:
        win32gui.EnumWindows(_enum_cb, None)
    except Exception as e:
        logger.error(f'EnumWindows failed: {e}')
        return None

    return result[0] if result else None


def get_ac_chart_title():
    """
    Return the full title bar text of the foreground window if it
    belongs to Amazing Charts. Returns None otherwise.
    """
    if _mock:
        return _mock.mock_get_ac_chart_title()
    if not win32gui:
        return None
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        if title and 'Amazing Charts' in title:
            return title
    except Exception as e:
        logger.debug(f'get_ac_chart_title error: {e}')
    return None


def get_active_patient_mrn():
    """
    Extract the patient MRN from the foreground Amazing Charts
    window title using the pattern ``ID: <digits>``.

    Returns
    -------
    str | None
        MRN string, or None if not found.
    """
    if _mock:
        return _mock.mock_get_active_patient_mrn()
    title = get_ac_chart_title()
    if not title:
        return None
    match = re.search(r'ID:\s*(\d+)', title)
    return match.group(1) if match else None


def get_active_patient_dob():
    """
    Extract the patient DOB from the foreground Amazing Charts
    window title using the pattern ``DOB: <date>``.

    Returns
    -------
    str | None
        DOB string (e.g. "01/15/1980"), or None if not found.
    """
    if _mock:
        return _mock.mock_get_active_patient_dob()
    title = get_ac_chart_title()
    if not title:
        return None
    match = re.search(r'DOB:\s*([\d/]+)', title)
    return match.group(1) if match else None


def is_ac_foreground():
    """Return True if the foreground window title starts with 'Amazing Charts'."""
    if _mock:
        return _mock.mock_is_ac_foreground()
    if not win32gui:
        return False
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        return bool(title and title.startswith('Amazing Charts'))
    except Exception:
        return False


def focus_ac_window():
    """
    Find the Amazing Charts window and bring it to the foreground.

    Returns
    -------
    bool
        True on success, False if AC window not found.
    """
    if _mock:
        return _mock.mock_focus_ac_window()
    hwnd = find_ac_window()
    if not hwnd:
        return False
    try:
        win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception as e:
        logger.error(f'SetForegroundWindow failed: {e}')
        return False


def is_chart_window_open():
    """
    Return True if any visible window title contains "ID:" — this
    indicates a patient chart is currently open in AC.
    """
    if _mock:
        return _mock.mock_is_chart_window_open()
    if not win32gui:
        return False

    found = []

    def _enum_cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and 'ID:' in title:
                found.append(True)

    try:
        win32gui.EnumWindows(_enum_cb, None)
    except Exception:
        pass
    return bool(found)


def get_ac_state():
    """
    Detect the current state of Amazing Charts.

    Returns one of:
      'not_running'  — AC process not found
      'login_screen' — AC is open but showing the login dialog
      'home_screen'  — AC is logged in, home screen visible (no chart open)
      'chart_open'   — A patient chart window is in the foreground

    This function should be called before any automation step to
    verify AC is in the expected state.
    """
    if _mock:
        return _mock.mock_get_ac_state()

    # Step 1: Check if AC process is running via psutil
    ac_process_found = False
    if psutil:
        process_name = getattr(config, 'AMAZING_CHARTS_PROCESS_NAME', 'AmazingCharts.exe')
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                    ac_process_found = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    else:
        # Fallback: check via win32gui if psutil unavailable
        ac_process_found = find_ac_window() is not None

    if not ac_process_found:
        return 'not_running'

    # Step 2: Check window titles to determine state
    if not win32gui:
        return 'not_running'

    titles = []

    def _enum_cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                titles.append(title)

    try:
        win32gui.EnumWindows(_enum_cb, None)
    except Exception as e:
        logger.error(f'EnumWindows failed in get_ac_state: {e}')
        return 'not_running'

    # Check for chart window (has "ID:" in title with DOB pattern)
    chart_pattern = re.compile(r'DOB:.*ID:\s*\d+')
    for title in titles:
        if chart_pattern.search(title):
            return 'chart_open'

    # Check for login screen
    prefix = getattr(config, 'AC_WINDOW_TITLE_PREFIX', 'Amazing Charts')
    for title in titles:
        if 'login' in title.lower() and prefix.lower() in title.lower():
            return 'login_screen'

    # Check for home screen (AC window exists but no chart/login)
    for title in titles:
        if title.startswith(prefix):
            return 'home_screen'

    return 'not_running'


def detect_resurrect_dialog():
    """
    Check if the "Resurrect Note" dialog is currently visible.

    This dialog appears when AC re-opens a chart that had an
    unsaved note from a previous session. It asks the user
    whether to resurrect (continue) or discard the old note.

    Returns True if the dialog is detected, False otherwise.
    """
    if _mock:
        return _mock.mock_detect_resurrect_dialog()
    if not win32gui:
        return False

    found = []

    def _enum_cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and 'resurrect' in title.lower():
                found.append(True)

    try:
        win32gui.EnumWindows(_enum_cb, None)
    except Exception:
        pass
    return bool(found)


def handle_resurrect_dialog(accept=True):
    """
    Handle the Resurrect Note dialog by clicking Yes (accept=True)
    or No (accept=False).

    Returns True if dialog was found and handled, False if not found.
    """
    if _mock:
        return _mock.mock_handle_resurrect_dialog(accept)

    if not detect_resurrect_dialog():
        return False

    try:
        import pyautogui
        import time

        if accept:
            # Click "Yes" — resurrect the old note
            pyautogui.press('enter')  # Yes is typically the default button
        else:
            # Click "No" — discard
            pyautogui.press('tab')
            pyautogui.press('enter')
        time.sleep(0.5)
        return True
    except Exception as e:
        logger.error(f'Failed to handle resurrect dialog: {e}')
        return False


def auto_login_ac():
    """
    Attempt to log into Amazing Charts when it is on the login screen.

    Reads AC_LOGIN_USERNAME and AC_LOGIN_PASSWORD from config.
    Focuses the login window, types credentials, presses Enter,
    then waits up to 15 seconds for the state to change to 'home_screen'.

    Returns
    -------
    bool
        True if login succeeded (state became home_screen), False otherwise.
    """
    if _mock:
        return _mock.mock_auto_login_ac()

    username = getattr(config, 'AC_LOGIN_USERNAME', '')
    password = getattr(config, 'AC_LOGIN_PASSWORD', '')

    if not username or not password:
        logger.warning('AC_LOGIN_USERNAME or AC_LOGIN_PASSWORD not set in config')
        return False

    state = get_ac_state()
    if state != 'login_screen':
        logger.info(f'auto_login_ac: AC not on login screen (state={state})')
        return False

    if not focus_ac_window():
        logger.error('auto_login_ac: could not focus AC window')
        return False

    try:
        import pyautogui
        import time

        time.sleep(0.5)

        # Clear any existing text in username field and type credentials
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.typewrite(username, interval=0.03)
        pyautogui.press('tab')
        time.sleep(0.2)
        pyautogui.typewrite(password, interval=0.03)
        pyautogui.press('enter')

        # Wait for login to complete (up to 15 seconds)
        for _ in range(15):
            time.sleep(1)
            new_state = get_ac_state()
            if new_state in ('home_screen', 'chart_open'):
                logger.info('auto_login_ac: login successful')
                return True

        logger.warning('auto_login_ac: login timed out — state did not change')
        return False

    except Exception as e:
        logger.error(f'auto_login_ac failed: {e}')
        return False

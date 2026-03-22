"""
CareCompanion — Amazing Charts Mock Provider

File location: carecompanion/tests/ac_mock.py

Provides simulated Amazing Charts responses for testing on machines
that don't have AC installed.  Activated by setting AC_MOCK_MODE = True
in config.py.

How it works:
  - ac_window.py checks config.AC_MOCK_MODE first. If True, it returns
    fake window data (title bar text, MRN, DOB) instead of calling win32gui.
  - ocr_helpers.py checks config.AC_MOCK_MODE first. If True, it loads
    screenshot images from Documents/ac_interface_reference/ instead of
    doing live screen captures.

This lets every module above (mrn_reader, inbox_reader, clinical_summary_parser)
run their real logic against realistic data — without AC being installed.

At deployment:
  - Set AC_MOCK_MODE = False (the default). Mock code never runs.
  - No recoding required. The mock paths sit silent in the codebase.

Screenshot source:
  Documents/ac_interface_reference/
  Reference doc: Documents/ac_interface_reference/ac_interface_reference.md
"""

import os
import logging

logger = logging.getLogger('tests.ac_mock')

# ---------------------------------------------------------------------------
# Paths to reference screenshots (relative to project root)
# ---------------------------------------------------------------------------
_REF_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'Documents', 'ac_interface_reference', 'screenshots',
)

SCREENSHOTS = {
    'home':             os.path.join(_REF_DIR, 'home_screen_pateitn_chart_highlighted.png'),
    'inbox':            os.path.join(_REF_DIR, 'inbox_lab_home_page.png'),
    'inbox_filters':    os.path.join(_REF_DIR, 'ac_inbox_drop_down_filter_options_.png'),
    'patient_chart':    os.path.join(_REF_DIR, 'fresh_open_patient_chart.png'),
    'clinical_summary': os.path.join(_REF_DIR, 'navigate_to_clinical_summary.png'),
    'print_menu':       os.path.join(_REF_DIR, 'patient_print_last_note_menu_tab.png'),
    'print_notes':      os.path.join(_REF_DIR, 'print_notes_letters_last_note_opening_page_.png'),
    'print_notes_v2':   os.path.join(_REF_DIR, 'print_notes_letters_last_note_opening_page_variable_2_.png'),
    'export_hie':       os.path.join(_REF_DIR, 'export_to_hie_&_phr.png'),
    'reports':          os.path.join(_REF_DIR, 'reports_tab.png'),
}

SAMPLE_XML = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'Documents', 'xml_test_patients',
    'ClinicalSummary_PatientId_62815_20260317_142457.xml',
)

# ---------------------------------------------------------------------------
# Fake patient data (matches the test patient in the XML and screenshots)
# ---------------------------------------------------------------------------
MOCK_PATIENT = {
    'mrn': '62815',
    'name': 'TEST, TEST',
    'dob': '10/1/1980',
    'age': 45,
    'sex': 'woman',
}

MOCK_WINDOW_TITLE = (
    f'{MOCK_PATIENT["name"]}  '
    f'(DOB: {MOCK_PATIENT["dob"]}; ID: {MOCK_PATIENT["mrn"]})  '
    f'{MOCK_PATIENT["age"]} year old {MOCK_PATIENT["sex"]},'
)

MOCK_HOME_TITLE = 'Amazing Charts  Family Practice Associates of Chesterfield'

# Which "screen state" the mock is in — controls what functions return
# Values: 'home', 'chart', 'inbox'
_mock_state = 'home'


def set_mock_state(state):
    """Set the simulated AC screen state: 'home', 'chart', 'inbox', or 'login'."""
    global _mock_state
    _mock_state = state


def get_mock_state():
    """Return the current mock state."""
    return _mock_state


# ---------------------------------------------------------------------------
# Mock replacements for ac_window.py functions
# ---------------------------------------------------------------------------

def mock_find_ac_window():
    """Fake hwnd — always returns a nonzero value."""
    return 12345


def mock_get_ac_chart_title():
    """Return mock title bar based on current state."""
    if _mock_state == 'chart':
        return MOCK_WINDOW_TITLE
    return MOCK_HOME_TITLE


def mock_get_active_patient_mrn():
    """Return mock MRN when in chart state."""
    if _mock_state == 'chart':
        return MOCK_PATIENT['mrn']
    return None


def mock_get_active_patient_dob():
    """Return mock DOB when in chart state."""
    if _mock_state == 'chart':
        return MOCK_PATIENT['dob']
    return None


def mock_is_ac_foreground():
    """Always True in mock mode — AC is always 'running'."""
    return True


def mock_is_chart_window_open():
    """True only when mock state is 'chart'."""
    return _mock_state == 'chart'


def mock_focus_ac_window():
    """Always succeeds in mock mode."""
    return True


def mock_get_ac_state():
    """Return AC state based on current mock state."""
    state_map = {
        'home': 'home_screen',
        'chart': 'chart_open',
        'inbox': 'home_screen',
        'login': 'login_screen',
    }
    return state_map.get(_mock_state, 'home_screen')


def mock_detect_resurrect_dialog():
    """In mock mode, resurrect dialog is never shown."""
    return False


def mock_handle_resurrect_dialog(accept=True):
    """In mock mode, no dialog to handle."""
    return False


def mock_auto_login_ac():
    """In mock mode, simulate a successful login."""
    global _mock_state
    if _mock_state == 'login':
        _mock_state = 'home'
        logger.info('Mock: auto_login_ac succeeded (login → home)')
        return True
    logger.info(f'Mock: auto_login_ac skipped (state={_mock_state})')
    return False


# ---------------------------------------------------------------------------
# Mock replacements for ocr_helpers.py functions
# ---------------------------------------------------------------------------

def _load_screenshot(name):
    """Load a screenshot image from the reference folder."""
    try:
        from PIL import Image
        path = SCREENSHOTS.get(name)
        if path and os.path.exists(path):
            return Image.open(path)
        logger.warning(f'Mock screenshot not found: {name} ({path})')
    except ImportError:
        logger.warning('Pillow not installed — cannot load mock screenshots')
    return None


def _screenshot_for_state():
    """Pick the right screenshot based on current mock state."""
    state_map = {
        'home': 'home',
        'chart': 'patient_chart',
        'inbox': 'inbox',
    }
    return state_map.get(_mock_state, 'home')


def mock_get_ac_window_rect():
    """Return a fake window rectangle (positioned at top-left)."""
    img = _load_screenshot(_screenshot_for_state())
    if img:
        return (0, 0, img.width, img.height)
    return (0, 0, 1920, 1080)


def mock_screenshot_ac_window():
    """Return a screenshot image from the reference folder."""
    img = _load_screenshot(_screenshot_for_state())
    if img:
        return img, (0, 0)
    return None, None


def mock_find_and_click(target_text, case_sensitive=False, partial=True,
                        fallback_xy=None, click_delay=0.0):
    """
    Mock click — runs real OCR against the screenshot to verify
    the text IS findable, but doesn't actually click anything.

    Returns True if the text was found in the screenshot (or if
    fallback coordinates are provided), False otherwise.
    """
    from agent.ocr_helpers import ocr_find_all_text, _find_best_match, _preprocess_for_ocr

    img = _load_screenshot(_screenshot_for_state())
    if img is None:
        if fallback_xy and fallback_xy != (0, 0):
            logger.info(f'Mock click (fallback) for "{target_text}"')
            return True
        return False

    words = ocr_find_all_text(img)
    match = _find_best_match(words, target_text, case_sensitive, partial)

    if match:
        logger.info(f'Mock click: found "{target_text}" at ({match["left"]}, {match["top"]})')
        return True

    if fallback_xy and fallback_xy != (0, 0):
        logger.info(f'Mock click (fallback) for "{target_text}"')
        return True

    logger.warning(f'Mock click: "{target_text}" NOT found in screenshot')
    return False


def mock_find_text_on_screen(target_text, case_sensitive=False, partial=True):
    """
    Mock text search — runs real OCR on the screenshot.
    Returns fake screen coordinates if found, None otherwise.
    """
    from agent.ocr_helpers import ocr_find_all_text, _find_best_match

    img = _load_screenshot(_screenshot_for_state())
    if img is None:
        return None

    words = ocr_find_all_text(img)
    match = _find_best_match(words, target_text, case_sensitive, partial)

    if match:
        x = match['left'] + match['width'] // 2
        y = match['top'] + match['height'] // 2
        return (x, y)
    return None


def mock_find_element_near_text(anchor_text, direction='right', offset_px=50,
                                case_sensitive=False):
    """Mock element-near-text — returns fake coordinates if anchor found."""
    center = mock_find_text_on_screen(anchor_text, case_sensitive=case_sensitive)
    if not center:
        return None
    x, y = center
    if direction == 'right':
        return (x + offset_px, y)
    elif direction == 'left':
        return (x - offset_px, y)
    elif direction == 'below':
        return (x, y + offset_px)
    elif direction == 'above':
        return (x, y - offset_px)
    return center


def mock_screenshot_region_near_text(anchor_text, width=600, height=400,
                                     direction='below', offset_px=0):
    """Mock region screenshot — crops the reference screenshot around the anchor."""
    from agent.ocr_helpers import ocr_find_all_text, _find_best_match

    img = _load_screenshot(_screenshot_for_state())
    if img is None:
        return None

    words = ocr_find_all_text(img)
    match = _find_best_match(words, anchor_text)

    if not match:
        return None

    if direction == 'below':
        left = max(0, match['left'] - 20)
        top = match['top'] + match['height'] + offset_px
    elif direction == 'right':
        left = match['left'] + match['width'] + offset_px
        top = max(0, match['top'] - 20)
    else:
        left = match['left']
        top = match['top'] + match['height']

    right = min(img.width, left + width)
    bottom = min(img.height, top + height)

    return img.crop((left, top, right, bottom))

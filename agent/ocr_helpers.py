"""
NP Companion — OCR Element Finding Helpers

File location: np-companion/agent/ocr_helpers.py

Provides OCR-first element detection for Amazing Charts automation.
Instead of hardcoded screen coordinates (which break across different
machines, resolutions, and window positions), these helpers:

  1. Find the AC window and get its screen position/size
  2. Use Tesseract OCR with word-level bounding boxes to locate
     text labels, buttons, and fields by their visible text
  3. Compute click targets relative to found text positions

This makes automation portable across any machine running AC.
Coordinates are only used as a last-resort fallback.

HIPAA note: Screenshots are never saved to disk — processed in memory only.
"""

import logging
import re
import time

try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageGrab
except ImportError:
    pytesseract = None
    Image = None
    ImageEnhance = None
    ImageGrab = None

try:
    import win32gui
except ImportError:
    win32gui = None

import config

logger = logging.getLogger('agent.ocr_helpers')

# ---------------------------------------------------------------------------
# Mock-mode support: when AC_MOCK_MODE is True, public functions delegate
# to tests.ac_mock instead of doing live screen captures.
# This block is inert when AC_MOCK_MODE is False (the default).
# ---------------------------------------------------------------------------
_mock = None
if getattr(config, 'AC_MOCK_MODE', False):
    try:
        from tests import ac_mock as _mock
        logger.info('AC_MOCK_MODE active — using screenshot-based OCR')
    except ImportError:
        logger.warning('AC_MOCK_MODE is True but tests.ac_mock not found')


# ======================================================================
# Window geometry helpers
# ======================================================================

def get_ac_window_rect():
    """
    Get the bounding rectangle of the Amazing Charts window.

    Returns
    -------
    tuple (left, top, right, bottom) or None
        Screen coordinates of the AC window, or None if not found.
    """
    if _mock:
        return _mock.mock_get_ac_window_rect()
    if not win32gui:
        logger.warning('win32gui not available — cannot locate AC window')
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

    if not result:
        logger.info('AC window not found')
        return None

    try:
        rect = win32gui.GetWindowRect(result[0])
        return rect  # (left, top, right, bottom)
    except Exception as e:
        logger.error(f'GetWindowRect failed: {e}')
        return None


def screenshot_ac_window():
    """
    Take a screenshot of only the Amazing Charts window area.

    Returns
    -------
    tuple (PIL.Image, (left, top)) or (None, None)
        The screenshot image and the top-left offset, or (None, None)
        if AC window is not found.
    """
    if _mock:
        return _mock.mock_screenshot_ac_window()
    if not ImageGrab:
        logger.warning('Pillow not available — cannot take screenshot')
        return None, None

    rect = get_ac_window_rect()
    if not rect:
        return None, None

    left, top, right, bottom = rect
    img = ImageGrab.grab(bbox=(left, top, right, bottom))
    return img, (left, top)


# ======================================================================
# OCR text and bounding box extraction
# ======================================================================

def _preprocess_for_ocr(image):
    """Preprocess an image for better OCR accuracy."""
    image = image.convert('L')  # Grayscale
    image = image.resize(
        (image.width * 2, image.height * 2),
        Image.LANCZOS
    )
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    return image


def ocr_find_all_text(image):
    """
    Run Tesseract OCR on an image and return all detected words
    with their bounding boxes.

    Parameters
    ----------
    image : PIL.Image
        The image to OCR (should be the AC window screenshot).

    Returns
    -------
    list of dict
        Each dict has: {"text": str, "left": int, "top": int,
                        "width": int, "height": int, "conf": int}
        Coordinates are relative to the input image (not screen).
    """
    if not pytesseract:
        logger.warning('pytesseract not available')
        return []

    # Set Tesseract path from config
    tesseract_path = getattr(config, 'TESSERACT_PATH', '')
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    processed = _preprocess_for_ocr(image)

    try:
        data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
    except Exception as e:
        logger.error(f'OCR failed: {e}')
        return []

    words = []
    n = len(data['text'])
    for i in range(n):
        text = data['text'][i].strip()
        conf = int(data['conf'][i])
        if text and conf > 30:  # Filter low-confidence noise
            # Coordinates are from the 2x preprocessed image — divide by 2
            words.append({
                'text': text,
                'left': data['left'][i] // 2,
                'top': data['top'][i] // 2,
                'width': data['width'][i] // 2,
                'height': data['height'][i] // 2,
                'conf': conf,
            })

    return words


def ocr_get_full_text(image):
    """
    Run OCR on an image and return the full text string.

    Parameters
    ----------
    image : PIL.Image

    Returns
    -------
    str
    """
    if not pytesseract:
        return ''

    tesseract_path = getattr(config, 'TESSERACT_PATH', '')
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    processed = _preprocess_for_ocr(image)

    try:
        return pytesseract.image_to_string(processed, config='--psm 6')
    except Exception as e:
        logger.error(f'OCR full text failed: {e}')
        return ''


# ======================================================================
# Element finding — locate UI elements by visible text
# ======================================================================

def find_text_on_screen(target_text, case_sensitive=False, partial=True):
    """
    Find screen coordinates of a text label in the Amazing Charts window.

    Searches for target_text in the OCR results. Returns the center point
    of the matching bounding box in SCREEN coordinates (ready for clicking).

    Parameters
    ----------
    target_text : str
        The text to search for (e.g. "Show Charts", "Export", "Patient List").
    case_sensitive : bool
        Whether the match is case-sensitive (default False).
    partial : bool
        Whether to match partial text (default True).
        If False, requires exact word match.

    Returns
    -------
    tuple (x, y) or None
        Screen coordinates of the center of the found text, or None.
    """
    if _mock:
        return _mock.mock_find_text_on_screen(target_text, case_sensitive, partial)
    img, offset = screenshot_ac_window()
    if img is None:
        return None

    words = ocr_find_all_text(img)
    match = _find_best_match(words, target_text, case_sensitive, partial)

    if not match:
        logger.debug(f'Text "{target_text}" not found via OCR')
        return None

    # Convert image-relative coordinates to screen coordinates
    screen_x = offset[0] + match['left'] + match['width'] // 2
    screen_y = offset[1] + match['top'] + match['height'] // 2

    logger.debug(f'Found "{target_text}" at screen ({screen_x}, {screen_y})')
    return (screen_x, screen_y)


def find_text_region(target_text, case_sensitive=False, partial=True):
    """
    Find the full bounding box of a text label in screen coordinates.

    Returns
    -------
    tuple (left, top, right, bottom) or None
    """
    img, offset = screenshot_ac_window()
    if img is None:
        return None

    words = ocr_find_all_text(img)
    match = _find_best_match(words, target_text, case_sensitive, partial)

    if not match:
        return None

    left = offset[0] + match['left']
    top = offset[1] + match['top']
    right = left + match['width']
    bottom = top + match['height']

    return (left, top, right, bottom)


def find_element_near_text(anchor_text, direction='right', offset_px=50,
                           case_sensitive=False):
    """
    Find a UI element near a known text label.

    Useful for clicking input fields, buttons, or dropdowns that are
    adjacent to a label. For example, clicking the search field to the
    right of the "Patient List" label.

    Parameters
    ----------
    anchor_text : str
        Visible text label to use as the anchor point.
    direction : str
        "right", "left", "below", or "above" — where the target
        element is relative to the anchor text.
    offset_px : int
        How far from the anchor text center to click (in pixels).
    case_sensitive : bool

    Returns
    -------
    tuple (x, y) or None
        Screen coordinates to click, or None if anchor not found.
    """
    if _mock:
        return _mock.mock_find_element_near_text(
            anchor_text, direction, offset_px, case_sensitive
        )
    center = find_text_on_screen(anchor_text, case_sensitive=case_sensitive)
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
    else:
        return center


def find_and_click(target_text, case_sensitive=False, partial=True,
                   fallback_xy=None, click_delay=0.3):
    """
    Find text on screen via OCR and click it. Falls back to coordinates
    only if OCR fails AND a fallback is provided.

    Parameters
    ----------
    target_text : str
        Text to find and click.
    case_sensitive : bool
    partial : bool
    fallback_xy : tuple (x, y) or None
        Last-resort coordinates if OCR fails. Should come from config.py.
    click_delay : float
        Seconds to wait after clicking.

    Returns
    -------
    bool
        True if click was performed, False if element not found.
    """
    if _mock:
        return _mock.mock_find_and_click(
            target_text, case_sensitive, partial, fallback_xy, click_delay
        )
    try:
        import pyautogui
    except ImportError:
        logger.error('pyautogui not available')
        return False

    coords = find_text_on_screen(target_text, case_sensitive, partial)

    if coords:
        pyautogui.click(*coords)
        time.sleep(click_delay)
        logger.debug(f'OCR click on "{target_text}" at {coords}')
        return True

    # Last resort: use fallback coordinates if provided
    if fallback_xy and fallback_xy != (0, 0):
        logger.warning(f'OCR failed for "{target_text}" — using fallback {fallback_xy}')
        pyautogui.click(*fallback_xy)
        time.sleep(click_delay)
        return True

    logger.warning(f'Cannot find "{target_text}" — no OCR match and no fallback')
    return False


def screenshot_region_near_text(anchor_text, width=600, height=400,
                                direction='below', offset_px=0):
    """
    Take a screenshot of a region relative to a text anchor.

    Useful for OCR-reading a table or form that appears below a header.

    Parameters
    ----------
    anchor_text : str
        The text label that anchors the region (e.g. "Show Charts").
    width : int
        Width of the capture region in pixels.
    height : int
        Height of the capture region.
    direction : str
        Where the region starts relative to the anchor: "below", "right".
    offset_px : int
        Additional offset from the anchor.

    Returns
    -------
    PIL.Image or None
        Cropped screenshot image, or None if anchor not found.
    """
    if _mock:
        return _mock.mock_screenshot_region_near_text(
            anchor_text, width, height, direction, offset_px
        )
    if not ImageGrab:
        return None

    region = find_text_region(anchor_text)
    if not region:
        return None

    a_left, a_top, a_right, a_bottom = region

    if direction == 'below':
        grab_left = a_left - 20  # Small margin left
        grab_top = a_bottom + offset_px
    elif direction == 'right':
        grab_left = a_right + offset_px
        grab_top = a_top - 20
    else:
        grab_left = a_left
        grab_top = a_bottom

    grab_right = grab_left + width
    grab_bottom = grab_top + height

    try:
        return ImageGrab.grab(bbox=(grab_left, grab_top, grab_right, grab_bottom))
    except Exception as e:
        logger.error(f'Region screenshot failed: {e}')
        return None


# ======================================================================
# Multi-word phrase matching
# ======================================================================

def _find_best_match(words, target_text, case_sensitive=False, partial=True):
    """
    Find the best match for a multi-word phrase in OCR word list.

    For multi-word targets like "Show Charts", this finds consecutive
    words and returns a merged bounding box.

    Returns
    -------
    dict with keys: text, left, top, width, height — or None
    """
    if not words:
        return None

    target = target_text if case_sensitive else target_text.lower()
    target_words = target.split()

    if len(target_words) == 1:
        # Single-word search
        for w in words:
            text = w['text'] if case_sensitive else w['text'].lower()
            if partial:
                if target in text:
                    return w
            else:
                if text == target:
                    return w
        return None

    # Multi-word phrase search: find consecutive words on roughly the same line
    for i in range(len(words) - len(target_words) + 1):
        candidate = words[i:i + len(target_words)]

        # Check if words are on the same line (tops within 10px of each other)
        tops = [w['top'] for w in candidate]
        if max(tops) - min(tops) > 15:
            continue

        # Check if text matches
        candidate_texts = [
            w['text'] if case_sensitive else w['text'].lower()
            for w in candidate
        ]

        match = True
        for j, ct in enumerate(candidate_texts):
            if partial:
                if target_words[j] not in ct:
                    match = False
                    break
            else:
                if ct != target_words[j]:
                    match = False
                    break

        if match:
            # Merge bounding boxes
            left = min(w['left'] for w in candidate)
            top = min(w['top'] for w in candidate)
            right = max(w['left'] + w['width'] for w in candidate)
            bottom = max(w['top'] + w['height'] for w in candidate)
            return {
                'text': ' '.join(w['text'] for w in candidate),
                'left': left,
                'top': top,
                'width': right - left,
                'height': bottom - top,
                'conf': min(w['conf'] for w in candidate),
            }

    return None

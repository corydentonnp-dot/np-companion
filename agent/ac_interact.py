"""
CareCompanion — Smart AC Interaction Layer (3-tier)

File location: carecompanion/agent/ac_interact.py

Unified interface for interacting with Amazing Charts. Tries three
strategies in order:

    Tier 1: UIA  — Find control via Windows UI Automation tree
    Tier 2: OCR  — Find text on screen via Tesseract OCR
    Tier 3: Legacy — Click hardcoded fallback coordinates

Callers should use smart_find_and_click() instead of directly calling
ocr_helpers.find_and_click() or pyautogui.click(). This ensures UIA
is attempted first (instant, reliable when available) and gracefully
degrades through OCR and coordinate fallbacks.

Config flags in config.py:
    AC_USE_UIA = True         — enable/disable UIA tier
    AC_INTERACTION_TIER = 'uia_first'  — 'uia_first', 'ocr_first', 'legacy'

HIPAA note: No PHI is logged. Only control names and search text.
"""

import logging
import time

import config

logger = logging.getLogger('agent.ac_interact')

# Import sibling modules — lazy/safe so missing deps don't break import
try:
    from agent.uia_helpers import (
        uia_find_control, uia_get_text, uia_find_menu_item,
        uia_wait_for_control, uia_get_control_rect, invalidate_cache,
    )
    HAS_UIA = True
except ImportError:
    HAS_UIA = False

try:
    from agent.win32_actions import (
        send_click_to_control, send_text_to_control,
        send_key, send_click, VK_RETURN, VK_TAB, VK_ESCAPE,
    )
    HAS_WIN32_ACTIONS = True
except ImportError:
    HAS_WIN32_ACTIONS = False

try:
    from agent.ocr_helpers import (
        find_and_click as ocr_find_and_click,
        find_text_on_screen, find_element_near_text,
    )
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False


# ---------------------------------------------------------------------------
# Mock-mode support
# ---------------------------------------------------------------------------
_mock = None
if getattr(config, 'AC_MOCK_MODE', False):
    try:
        from tests import ac_mock as _mock
        logger.info('AC_MOCK_MODE active — ac_interact will use mock data')
    except ImportError:
        logger.warning('AC_MOCK_MODE is True but tests.ac_mock not found')


def _uia_enabled():
    """Check if UIA tier is enabled in config."""
    return HAS_UIA and getattr(config, 'AC_USE_UIA', True)


def _get_tier():
    """Get the configured interaction tier strategy."""
    return getattr(config, 'AC_INTERACTION_TIER', 'uia_first')


def smart_find_and_click(target_text, case_sensitive=False, partial=True,
                         fallback_xy=None, click_delay=0.3,
                         uia_control_type=None, uia_automation_id=None):
    """
    Find a UI element and click it using the best available method.

    Tier 1 (UIA): Search the UIA tree for a control matching target_text
        by name. If found, click via Win32 message or UIA invoke.
    Tier 2 (OCR): Screenshot AC window, OCR-find the text, pyautogui click.
    Tier 3 (Legacy): Click fallback_xy coordinates if provided.

    Parameters
    ----------
    target_text : str
        Visible text of the control to click (button label, menu item, etc.).
    case_sensitive : bool
        For OCR tier — whether text match is case-sensitive.
    partial : bool
        For OCR tier — whether to allow partial text match.
    fallback_xy : tuple (x, y) or None
        Last-resort screen coordinates (from config.py).
    click_delay : float
        Seconds to wait after clicking.
    uia_control_type : str, optional
        Narrow UIA search to a specific control type (e.g. 'Button').
    uia_automation_id : str, optional
        If known, search by AutomationId instead of name (more stable).

    Returns
    -------
    dict
        {"success": bool, "tier": str, "method": str}
        tier is 'uia', 'ocr', or 'legacy'.
        method describes what actually happened.
    """
    if _mock:
        logger.debug(f'Mock smart_find_and_click: "{target_text}"')
        return {'success': True, 'tier': 'mock', 'method': 'mock'}

    tier = _get_tier()

    # ---- Tier 1: UIA ----
    if tier in ('uia_first',) and _uia_enabled():
        result = _try_uia_click(
            target_text, uia_control_type, uia_automation_id, click_delay
        )
        if result['success']:
            return result

    # ---- Tier 2: OCR ----
    if tier in ('uia_first', 'ocr_first') and HAS_OCR:
        result = _try_ocr_click(
            target_text, case_sensitive, partial, click_delay
        )
        if result['success']:
            return result

    # ---- Tier 3: Legacy coordinates ----
    if fallback_xy and fallback_xy != (0, 0) and HAS_PYAUTOGUI:
        logger.warning(
            f'Tiers 1+2 failed for "{target_text}" — using fallback {fallback_xy}'
        )
        try:
            pyautogui.click(*fallback_xy)
            time.sleep(click_delay)
            return {'success': True, 'tier': 'legacy', 'method': f'click({fallback_xy})'}
        except Exception as e:
            logger.error(f'Legacy click failed: {e}')

    logger.warning(f'All tiers failed for "{target_text}"')
    return {'success': False, 'tier': 'none', 'method': 'exhausted'}


def _try_uia_click(target_text, control_type, automation_id, click_delay):
    """Attempt to find and click via UIA."""
    try:
        ctrl = uia_find_control(
            name=target_text if not automation_id else None,
            automation_id=automation_id,
            control_type=control_type,
            timeout=1.5,
        )
        if ctrl is None:
            return {'success': False, 'tier': 'uia', 'method': 'not_found'}

        if HAS_WIN32_ACTIONS:
            ok = send_click_to_control(ctrl, pause=0.05)
        else:
            # Fallback to UIA invoke/click_input
            try:
                ctrl.invoke()
                ok = True
            except Exception:
                try:
                    ctrl.click_input()
                    ok = True
                except Exception:
                    ok = False

        if ok:
            time.sleep(click_delay)
            logger.debug(f'UIA click on "{target_text}" succeeded')
            return {'success': True, 'tier': 'uia', 'method': 'uia_click'}
        return {'success': False, 'tier': 'uia', 'method': 'click_failed'}
    except Exception as e:
        logger.debug(f'UIA click attempt failed: {e}')
        return {'success': False, 'tier': 'uia', 'method': f'error: {e}'}


def _try_ocr_click(target_text, case_sensitive, partial, click_delay):
    """Attempt to find and click via OCR."""
    try:
        coords = find_text_on_screen(target_text, case_sensitive, partial)
        if coords and HAS_PYAUTOGUI:
            pyautogui.click(*coords)
            time.sleep(click_delay)
            logger.debug(f'OCR click on "{target_text}" at {coords}')
            return {'success': True, 'tier': 'ocr', 'method': f'ocr_click({coords})'}
        return {'success': False, 'tier': 'ocr', 'method': 'not_found'}
    except Exception as e:
        logger.debug(f'OCR click attempt failed: {e}')
        return {'success': False, 'tier': 'ocr', 'method': f'error: {e}'}


def smart_read_text(name=None, automation_id=None, control_type=None,
                    anchor_text=None, region_direction='right',
                    region_offset=100):
    """
    Read text from an AC control using the best method.

    Tier 1 (UIA): Find control and read via ValuePattern/Name.
    Tier 2 (OCR): Find anchor text, screenshot nearby region, OCR.

    Parameters
    ----------
    name : str, optional
        Control name for UIA.
    automation_id : str, optional
        Control AutomationId for UIA.
    control_type : str, optional
        Control type for UIA.
    anchor_text : str, optional
        For OCR tier: text label near the field to read.
    region_direction : str
        For OCR: direction from anchor to look ('right', 'below', etc.).
    region_offset : int
        For OCR: pixel offset from anchor.

    Returns
    -------
    dict
        {"success": bool, "text": str, "tier": str}
    """
    if _mock:
        return {'success': True, 'text': 'mock_value', 'tier': 'mock'}

    # Tier 1: UIA
    if _uia_enabled() and (name or automation_id):
        ctrl = uia_find_control(
            name=name, automation_id=automation_id,
            control_type=control_type, timeout=1.5
        )
        if ctrl:
            text = uia_get_text(ctrl)
            if text:
                return {'success': True, 'text': text, 'tier': 'uia'}

    # Tier 2: OCR (read a region near anchor text)
    if HAS_OCR and anchor_text:
        try:
            from agent.ocr_helpers import screenshot_region_near_text, ocr_get_full_text
            img = screenshot_region_near_text(
                anchor_text, width=300, height=30,
                direction=region_direction, offset_px=region_offset
            )
            if img:
                text = ocr_get_full_text(img).strip()
                if text:
                    return {'success': True, 'text': text, 'tier': 'ocr'}
        except Exception as e:
            logger.debug(f'OCR read failed: {e}')

    return {'success': False, 'text': '', 'tier': 'none'}


def smart_type_text(text, name=None, automation_id=None,
                    control_type='Edit', anchor_text=None,
                    anchor_direction='right', anchor_offset=50,
                    fallback_xy=None):
    """
    Type text into an AC field using the best method.

    Tier 1 (UIA): Find Edit control, set value via UIA/Win32.
    Tier 2 (OCR): Find anchor text, click nearby, type via pyautogui.
    Tier 3 (Legacy): Click fallback_xy and type.

    Parameters
    ----------
    text : str
        Text to enter. HIPAA: NOT logged.
    name : str, optional
        Control name for UIA.
    automation_id : str, optional
        AutomationId for UIA.
    control_type : str
        UIA control type (default 'Edit').
    anchor_text : str, optional
        For OCR tier: label near the input field.
    anchor_direction : str
        Direction from anchor to the input.
    anchor_offset : int
        Pixels from anchor to click.
    fallback_xy : tuple, optional
        Last-resort coordinates.

    Returns
    -------
    dict
        {"success": bool, "tier": str}
    """
    if _mock:
        return {'success': True, 'tier': 'mock'}

    # Tier 1: UIA
    if _uia_enabled() and (name or automation_id):
        ctrl = uia_find_control(
            name=name, automation_id=automation_id,
            control_type=control_type, timeout=1.5
        )
        if ctrl and HAS_WIN32_ACTIONS:
            ok = send_text_to_control(ctrl, text)
            if ok:
                return {'success': True, 'tier': 'uia'}

    # Tier 2: OCR — click near anchor and type
    if HAS_OCR and anchor_text and HAS_PYAUTOGUI:
        coords = find_element_near_text(
            anchor_text, direction=anchor_direction, offset_px=anchor_offset
        )
        if coords:
            pyautogui.click(*coords)
            time.sleep(0.2)
            pyautogui.typewrite(text, interval=0.02)
            return {'success': True, 'tier': 'ocr'}

    # Tier 3: Legacy
    if fallback_xy and fallback_xy != (0, 0) and HAS_PYAUTOGUI:
        pyautogui.click(*fallback_xy)
        time.sleep(0.2)
        pyautogui.typewrite(text, interval=0.02)
        return {'success': True, 'tier': 'legacy'}

    return {'success': False, 'tier': 'none'}


def smart_navigate_menu(menu_path, fallback_xy=None, click_delay=0.3):
    """
    Navigate an AC menu tree.

    Tier 1 (UIA): Walk menu items via UIA tree.
    Tier 2 (OCR): Click each menu item by text sequentially.
    Tier 3: Click fallback coordinates.

    Parameters
    ----------
    menu_path : list[str]
        E.g. ['Patient', 'Export Clinical Summary'].
    fallback_xy : tuple, optional
        Last-resort coordinates for the final menu item.
    click_delay : float
        Delay between menu clicks.

    Returns
    -------
    dict
        {"success": bool, "tier": str}
    """
    if _mock:
        return {'success': True, 'tier': 'mock'}

    # Tier 1: UIA menu navigation
    if _uia_enabled():
        item = uia_find_menu_item(menu_path)
        if item:
            if HAS_WIN32_ACTIONS:
                ok = send_click_to_control(item)
            else:
                try:
                    item.click_input()
                    ok = True
                except Exception:
                    ok = False
            if ok:
                time.sleep(click_delay)
                return {'success': True, 'tier': 'uia'}

    # Tier 2: OCR — click each menu item by text
    if HAS_OCR and HAS_PYAUTOGUI:
        for item_name in menu_path:
            coords = find_text_on_screen(item_name)
            if not coords:
                logger.warning(f'Menu OCR failed at "{item_name}"')
                break
            pyautogui.click(*coords)
            time.sleep(click_delay)
        else:
            # All items found and clicked
            return {'success': True, 'tier': 'ocr'}

    # Tier 3: Legacy
    if fallback_xy and fallback_xy != (0, 0) and HAS_PYAUTOGUI:
        pyautogui.click(*fallback_xy)
        time.sleep(click_delay)
        return {'success': True, 'tier': 'legacy'}

    return {'success': False, 'tier': 'none'}

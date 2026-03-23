"""
CareCompanion — UIA Element Finding Helpers

File location: carecompanion/agent/uia_helpers.py

Provides Windows UI Automation (UIA) element detection for Amazing Charts.
This is the UIA-first companion to ocr_helpers.py. When AC exposes controls
via UIA, this module finds them by name, automation_id, class_name, or
control_type — far more reliable than OCR text matching.

Functions in this module are purely READ + FIND. Click/type actions live
in win32_actions.py to keep concerns separated.

HIPAA note: No PHI is logged. Control names are logged but never patient data.
"""

import logging
import time

import config

logger = logging.getLogger('agent.uia_helpers')

# ---------------------------------------------------------------------------
# Safe imports — pywinauto may not be installed
# ---------------------------------------------------------------------------
try:
    from pywinauto import Application, timings
    HAS_PYWINAUTO = True
except ImportError:
    HAS_PYWINAUTO = False

try:
    import win32gui
except ImportError:
    win32gui = None

# ---------------------------------------------------------------------------
# Mock-mode support
# ---------------------------------------------------------------------------
_mock = None
if getattr(config, 'AC_MOCK_MODE', False):
    try:
        from tests import ac_mock as _mock
        logger.info('AC_MOCK_MODE active — UIA helpers will use mock data')
    except ImportError:
        logger.warning('AC_MOCK_MODE is True but tests.ac_mock not found')

# ---------------------------------------------------------------------------
# Module-level cached app reference (avoids reconnecting on every call)
# ---------------------------------------------------------------------------
_cached_app = None
_cached_hwnd = None


def _find_ac_hwnd():
    """Find the Amazing Charts window handle."""
    if not win32gui:
        return None
    result = []

    def _cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and title.startswith('Amazing Charts'):
                result.append(hwnd)
    try:
        win32gui.EnumWindows(_cb, None)
    except Exception:
        return None
    return result[0] if result else None


def get_uia_app():
    """
    Connect to the Amazing Charts window via pywinauto UIA backend.
    Caches the connection — subsequent calls reuse the same Application
    object unless the window handle changed.

    Returns
    -------
    pywinauto.Application | None
        Connected application, or None if AC not found or pywinauto missing.
    """
    global _cached_app, _cached_hwnd

    if _mock:
        return _mock.mock_get_uia_app() if hasattr(_mock, 'mock_get_uia_app') else None
    if not HAS_PYWINAUTO:
        logger.warning('pywinauto not installed — UIA helpers unavailable')
        return None

    hwnd = _find_ac_hwnd()
    if not hwnd:
        logger.debug('AC window not found for UIA connection')
        _cached_app = None
        _cached_hwnd = None
        return None

    # Reuse cached connection if hwnd hasn't changed
    if _cached_app and _cached_hwnd == hwnd:
        try:
            # Verify connection is still alive
            _cached_app.window(handle=hwnd).wrapper_object()
            return _cached_app
        except Exception:
            _cached_app = None
            _cached_hwnd = None

    try:
        app = Application(backend='uia').connect(handle=hwnd)
        _cached_app = app
        _cached_hwnd = hwnd
        return app
    except Exception as e:
        logger.error(f'UIA connect failed: {e}')
        _cached_app = None
        _cached_hwnd = None
        return None


def invalidate_cache():
    """Force reconnect on next get_uia_app() call."""
    global _cached_app, _cached_hwnd
    _cached_app = None
    _cached_hwnd = None


def uia_find_control(name=None, automation_id=None, control_type=None,
                     class_name=None, parent=None, timeout=3.0):
    """
    Find a single UIA control matching the given criteria.

    Parameters
    ----------
    name : str, optional
        The control's Name property (visible text).
    automation_id : str, optional
        The control's AutomationId (stable programmatic id).
    control_type : str, optional
        The control type (e.g. 'Button', 'Edit', 'MenuItem', 'TreeItem').
    class_name : str, optional
        The Win32 class name.
    parent : UIAWrapper, optional
        Search within this control instead of the main window.
    timeout : float
        Seconds to wait for the control to appear (default 3s).

    Returns
    -------
    UIAWrapper | None
        The found control wrapper, or None if not found.
    """
    if _mock and hasattr(_mock, 'mock_uia_find_control'):
        return _mock.mock_uia_find_control(
            name=name, automation_id=automation_id,
            control_type=control_type, class_name=class_name
        )

    app = get_uia_app()
    if not app:
        return None

    try:
        if parent is None:
            hwnd = _find_ac_hwnd()
            if not hwnd:
                return None
            parent = app.window(handle=hwnd).wrapper_object()

        # Build search criteria
        criteria = {}
        if name:
            criteria['title'] = name
        if automation_id:
            criteria['auto_id'] = automation_id
        if control_type:
            criteria['control_type'] = control_type
        if class_name:
            criteria['class_name'] = class_name

        if not criteria:
            logger.warning('uia_find_control called with no search criteria')
            return None

        # Try to find with retries up to timeout
        end_time = time.monotonic() + timeout
        while True:
            try:
                found = parent.child_window(**criteria)
                wrapper = found.wrapper_object()
                return wrapper
            except Exception:
                if time.monotonic() >= end_time:
                    return None
                time.sleep(0.3)

    except Exception as e:
        logger.debug(f'uia_find_control error: {e}')
        return None


def uia_find_all(name=None, automation_id=None, control_type=None,
                 class_name=None, parent=None):
    """
    Find ALL UIA controls matching the criteria (no timeout, one-shot).

    Returns
    -------
    list[UIAWrapper]
        List of matching controls (may be empty).
    """
    if _mock and hasattr(_mock, 'mock_uia_find_all'):
        return _mock.mock_uia_find_all(
            name=name, automation_id=automation_id,
            control_type=control_type, class_name=class_name
        )

    app = get_uia_app()
    if not app:
        return []

    try:
        if parent is None:
            hwnd = _find_ac_hwnd()
            if not hwnd:
                return []
            parent = app.window(handle=hwnd).wrapper_object()

        criteria = {}
        if name:
            criteria['title'] = name
        if automation_id:
            criteria['auto_id'] = automation_id
        if control_type:
            criteria['control_type'] = control_type
        if class_name:
            criteria['class_name'] = class_name

        if not criteria:
            return []

        return parent.children(**criteria)
    except Exception as e:
        logger.debug(f'uia_find_all error: {e}')
        return []


def uia_find_menu_item(menu_path):
    """
    Navigate an AC menu bar by path (e.g. ['Patient', 'Export Clinical Summary']).

    Parameters
    ----------
    menu_path : list[str]
        Ordered menu item names from top-level to leaf.

    Returns
    -------
    UIAWrapper | None
        The final menu item control, or None if navigation failed.
    """
    if _mock and hasattr(_mock, 'mock_uia_find_menu_item'):
        return _mock.mock_uia_find_menu_item(menu_path)

    app = get_uia_app()
    if not app:
        return None

    try:
        hwnd = _find_ac_hwnd()
        if not hwnd:
            return None
        window = app.window(handle=hwnd).wrapper_object()

        current = window
        for item_name in menu_path:
            found = None
            # Try MenuItem first, then Menu
            for ctype in ('MenuItem', 'Menu'):
                try:
                    child = current.child_window(title=item_name, control_type=ctype)
                    found = child.wrapper_object()
                    break
                except Exception:
                    continue
            if not found:
                logger.debug(f'Menu item not found: "{item_name}" in path {menu_path}')
                return None
            # Click to expand the menu level (except the last item)
            if item_name != menu_path[-1]:
                try:
                    found.click_input()
                    time.sleep(0.3)
                except Exception:
                    pass
            current = found

        return current
    except Exception as e:
        logger.debug(f'uia_find_menu_item error: {e}')
        return None


def uia_get_text(control):
    """
    Extract text content from a UIA control.
    Tries multiple patterns: ValuePattern, window_text, Name property.

    Parameters
    ----------
    control : UIAWrapper
        The control to read text from.

    Returns
    -------
    str
        The text content, or empty string if unreadable.
    """
    if control is None:
        return ''
    try:
        # Try ValuePattern (edit controls, combo boxes)
        iface = control.iface_value
        if iface:
            val = iface.CurrentValue
            if val:
                return str(val)
    except Exception:
        pass
    try:
        text = control.window_text()
        if text:
            return str(text)
    except Exception:
        pass
    try:
        name = control.element_info.name
        if name:
            return str(name)
    except Exception:
        pass
    return ''


def uia_wait_for_control(timeout=10.0, poll_interval=0.5, **criteria):
    """
    Wait for a control to appear, polling until timeout.

    Parameters
    ----------
    timeout : float
        Maximum seconds to wait.
    poll_interval : float
        Seconds between polls.
    **criteria
        Keyword args passed to uia_find_control (name, automation_id, etc.).

    Returns
    -------
    UIAWrapper | None
        The control if found within timeout, else None.
    """
    end_time = time.monotonic() + timeout
    while time.monotonic() < end_time:
        ctrl = uia_find_control(timeout=0.1, **criteria)
        if ctrl:
            return ctrl
        time.sleep(poll_interval)
    return None


def uia_get_children_text(parent=None, control_type=None):
    """
    Get text from all child controls of a given type.
    Useful for reading list items, table cells, tree items, etc.

    Parameters
    ----------
    parent : UIAWrapper, optional
        Parent control (defaults to AC main window).
    control_type : str, optional
        Filter children by control type (e.g. 'ListItem', 'DataItem').

    Returns
    -------
    list[str]
        List of text values from matching children.
    """
    children = uia_find_all(control_type=control_type, parent=parent)
    texts = []
    for child in children:
        text = uia_get_text(child)
        if text:
            texts.append(text)
    return texts


def uia_get_control_rect(control):
    """
    Get the screen rectangle of a UIA control.

    Returns
    -------
    tuple (left, top, right, bottom) | None
    """
    if control is None:
        return None
    try:
        rect = control.element_info.rectangle
        return (rect.left, rect.top, rect.right, rect.bottom)
    except Exception:
        return None

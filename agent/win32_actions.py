"""
CareCompanion — Win32 Message Actions

File location: carecompanion/agent/win32_actions.py

Sends Win32 messages (WM_LBUTTONDOWN, WM_CHAR, WM_KEYDOWN, etc.) to
Amazing Charts controls. Unlike pyautogui which moves the physical mouse
cursor and requires AC to be foreground, Win32 messages are sent directly
to a window handle — no cursor movement, no foreground requirement.

This module handles ACTIONS (click, type, keypress). Element FINDING
lives in uia_helpers.py. The two modules are designed to work together:
    control = uia_find_control(name='Save')
    send_click_to_control(control)

HIPAA note: Typed text is NOT logged. Only control names are logged.
"""

import ctypes
import ctypes.wintypes
import logging
import time

import config

logger = logging.getLogger('agent.win32_actions')

# ---------------------------------------------------------------------------
# Win32 constants
# ---------------------------------------------------------------------------
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102
WM_SETTEXT = 0x000C
WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E
WM_COMMAND = 0x0111
WM_CLOSE = 0x0010
BM_CLICK = 0x00F5
MK_LBUTTON = 0x0001

# Virtual key codes used in AC shortcuts
VK_RETURN = 0x0D
VK_TAB = 0x09
VK_ESCAPE = 0x1B
VK_F1 = 0x70
VK_F2 = 0x71
VK_F3 = 0x72
VK_F4 = 0x73
VK_F5 = 0x74
VK_F6 = 0x75
VK_F7 = 0x76
VK_F8 = 0x77
VK_F9 = 0x78
VK_F10 = 0x79
VK_F11 = 0x7A
VK_F12 = 0x7B

# ---------------------------------------------------------------------------
# Safe imports
# ---------------------------------------------------------------------------
try:
    import win32gui
    import win32api
    HAS_WIN32 = True
except ImportError:
    win32gui = None
    win32api = None
    HAS_WIN32 = False

# ---------------------------------------------------------------------------
# Mock-mode support
# ---------------------------------------------------------------------------
_mock = None
if getattr(config, 'AC_MOCK_MODE', False):
    try:
        from tests import ac_mock as _mock
        logger.info('AC_MOCK_MODE active — Win32 actions will be simulated')
    except ImportError:
        logger.warning('AC_MOCK_MODE is True but tests.ac_mock not found')


def _make_lparam(x, y):
    """Pack (x, y) into a 32-bit lParam for mouse messages."""
    return (y << 16) | (x & 0xFFFF)


def send_click(hwnd, x, y, pause=0.05):
    """
    Send a left-click to a window at (x, y) client coordinates
    via WM_LBUTTONDOWN + WM_LBUTTONUP.

    Does NOT move the physical cursor or require foreground focus.

    Parameters
    ----------
    hwnd : int
        Target window handle.
    x, y : int
        Client-area coordinates within the window.
    pause : float
        Delay between down/up messages (seconds).
    """
    if _mock:
        logger.debug(f'Mock send_click hwnd={hwnd} x={x} y={y}')
        return True

    if not HAS_WIN32:
        logger.error('win32gui not available — cannot send click')
        return False

    try:
        lparam = _make_lparam(x, y)
        win32gui.PostMessage(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
        time.sleep(pause)
        win32gui.PostMessage(hwnd, WM_LBUTTONUP, 0, lparam)
        return True
    except Exception as e:
        logger.error(f'send_click failed: {e}')
        return False


def send_click_to_control(control, pause=0.05):
    """
    Send a click to the center of a UIA control's bounding rect.

    Parameters
    ----------
    control : UIAWrapper
        The control to click (from uia_helpers).
    pause : float
        Delay between down/up (seconds).

    Returns
    -------
    bool
        True if sent successfully, False on error.
    """
    if _mock:
        try:
            name = control.element_info.name if control else 'None'
        except Exception:
            name = '?'
        logger.debug(f'Mock send_click_to_control: {name}')
        return True

    if control is None:
        logger.warning('send_click_to_control: control is None')
        return False

    try:
        rect = control.element_info.rectangle
        # Get center in screen coordinates
        cx = (rect.left + rect.right) // 2
        cy = (rect.top + rect.bottom) // 2

        # Convert screen coords to client coords relative to the control's parent
        hwnd = control.element_info.handle
        if not hwnd:
            # No direct handle — try using the control's invoke pattern instead
            try:
                control.invoke()
                return True
            except Exception:
                pass
            # Last resort: click_input (moves physical cursor)
            try:
                control.click_input()
                return True
            except Exception as e:
                logger.error(f'send_click_to_control fallback failed: {e}')
                return False

        # Convert screen to client coordinates
        point = ctypes.wintypes.POINT(cx, cy)
        ctypes.windll.user32.ScreenToClient(hwnd, ctypes.byref(point))
        return send_click(hwnd, point.x, point.y, pause)
    except Exception as e:
        logger.error(f'send_click_to_control error: {e}')
        return False


def send_right_click(hwnd, x, y, pause=0.05):
    """Send a right-click at client (x, y)."""
    if _mock:
        return True
    if not HAS_WIN32:
        return False
    try:
        lparam = _make_lparam(x, y)
        win32gui.PostMessage(hwnd, WM_RBUTTONDOWN, MK_LBUTTON, lparam)
        time.sleep(pause)
        win32gui.PostMessage(hwnd, WM_RBUTTONUP, 0, lparam)
        return True
    except Exception as e:
        logger.error(f'send_right_click failed: {e}')
        return False


def send_key(hwnd, vk_code, pause=0.05):
    """
    Send a single keypress (down + up) to a window.

    Parameters
    ----------
    hwnd : int
        Target window handle.
    vk_code : int
        Virtual key code (e.g. VK_RETURN, VK_TAB, VK_F5).
    pause : float
        Delay between down/up.
    """
    if _mock:
        logger.debug(f'Mock send_key hwnd={hwnd} vk={hex(vk_code)}')
        return True
    if not HAS_WIN32:
        return False
    try:
        win32gui.PostMessage(hwnd, WM_KEYDOWN, vk_code, 0)
        time.sleep(pause)
        win32gui.PostMessage(hwnd, WM_KEYUP, vk_code, 0)
        return True
    except Exception as e:
        logger.error(f'send_key failed: {e}')
        return False


def send_text(hwnd, text, char_delay=0.02):
    """
    Type text into a window by sending WM_CHAR for each character.

    Parameters
    ----------
    hwnd : int
        Target window handle (should be a focused edit control).
    text : str
        Text to type. HIPAA: this value is NOT logged.
    char_delay : float
        Delay between characters (seconds).
    """
    if _mock:
        logger.debug(f'Mock send_text hwnd={hwnd} len={len(text)}')
        return True
    if not HAS_WIN32:
        return False
    try:
        for ch in text:
            win32gui.PostMessage(hwnd, WM_CHAR, ord(ch), 0)
            if char_delay > 0:
                time.sleep(char_delay)
        return True
    except Exception as e:
        logger.error(f'send_text failed: {e}')
        return False


def send_text_to_control(control, text, clear_first=True, char_delay=0.02):
    """
    Type text into a UIA control. Tries ValuePattern first (instant),
    falls back to WM_CHAR character-by-character.

    Parameters
    ----------
    control : UIAWrapper
        Target edit control.
    text : str
        Text to enter. HIPAA: NOT logged.
    clear_first : bool
        If True, clear the field before typing.
    char_delay : float
        Delay between characters for WM_CHAR fallback.
    """
    if _mock:
        logger.debug(f'Mock send_text_to_control: len={len(text)}')
        return True

    if control is None:
        return False

    # Try UIA ValuePattern (instant, works on .NET controls)
    try:
        iface = control.iface_value
        if iface:
            iface.SetValue(text)
            return True
    except Exception:
        pass

    # Fallback: send WM_CHAR to the control's hwnd
    hwnd = None
    try:
        hwnd = control.element_info.handle
    except Exception:
        pass

    if hwnd:
        if clear_first:
            # Select all + delete
            send_key(hwnd, 0x41, pause=0)  # Ctrl+A would need modifier
            # Simpler: use WM_SETTEXT to clear
            try:
                win32gui.SendMessage(hwnd, WM_SETTEXT, 0, text)
                return True
            except Exception:
                pass
        return send_text(hwnd, text, char_delay)

    # No hwnd — try type_keys as last resort
    try:
        control.type_keys(text, with_spaces=True, pause=char_delay)
        return True
    except Exception as e:
        logger.error(f'send_text_to_control: all methods failed: {e}')
        return False


def get_window_text(hwnd):
    """
    Read text from a window via WM_GETTEXT.

    Returns
    -------
    str
        Window text, or empty string on failure.
    """
    if _mock:
        return ''
    if not HAS_WIN32:
        return ''
    try:
        length = win32gui.SendMessage(hwnd, WM_GETTEXTLENGTH, 0, 0)
        if length <= 0:
            return ''
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.SendMessageW(hwnd, WM_GETTEXT, length + 1, buf)
        return buf.value
    except Exception:
        return ''


def send_menu_command(hwnd, command_id):
    """
    Send a WM_COMMAND to a window — equivalent to selecting a menu item
    by its command ID.

    Parameters
    ----------
    hwnd : int
        Target window handle.
    command_id : int
        The menu item command ID (discoverable via Spy++ or UIA probe).
    """
    if _mock:
        logger.debug(f'Mock send_menu_command hwnd={hwnd} id={command_id}')
        return True
    if not HAS_WIN32:
        return False
    try:
        win32gui.PostMessage(hwnd, WM_COMMAND, command_id, 0)
        return True
    except Exception as e:
        logger.error(f'send_menu_command failed: {e}')
        return False

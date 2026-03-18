"""
NP Companion — MRN Screen Reader

File location: np-companion/agent/mrn_reader.py

Core MRN detection loop called every 3 seconds by the agent scheduler.
Implements three-tier detection, TimeLog management, idle detection (F6b),
chart duration warning (F6a), and calibration mode (F6c).

HIPAA note: MRN values are stored in the database for billing accuracy.
Logs use sha256(mrn)[:12] only. UI displays last-4 digits only.
"""

import ctypes
import ctypes.wintypes
import hashlib
import logging
import re
import time
from datetime import datetime, timedelta, timezone

import config
from agent.ac_window import (
    get_ac_chart_title,
    get_active_patient_dob,
    get_active_patient_mrn,
    is_ac_foreground,
)
from agent.ocr_helpers import get_ac_window_rect

logger = logging.getLogger('agent.mrn_reader')

# Module-level state — persists across calls within the agent process
_last_known_mrn = None
_last_mrn_seen_at = None
_blank_since = None          # When MRN first went blank
_last_warning_at = {}        # MRN → last chart-duration warning time
_chart_open_since = {}       # MRN → when chart was first detected

# Timeout before closing a TimeLog when MRN goes blank (seconds)
_BLANK_TIMEOUT = 60


def _hash_mrn(mrn):
    """Return a truncated SHA-256 hash of the MRN for safe logging."""
    return hashlib.sha256(mrn.encode()).hexdigest()[:12]


# Cached NP scraper instance for DOM MRN extraction
_np_scraper = None


def _try_np_dom_mrn():
    """
    Try to extract MRN from a running NetPractice browser tab via CDP.
    Only attempts if Chrome is running on the configured CDP port.
    Returns MRN string or None.
    """
    global _np_scraper
    try:
        import asyncio
        from scrapers.netpractice import NetPracticeScraper
        from flask import current_app

        if _np_scraper is None:
            _np_scraper = NetPracticeScraper(current_app._get_current_object())

        loop = asyncio.new_event_loop()
        try:
            mrn, _name = loop.run_until_complete(_np_scraper.get_current_patient_mrn())
            return mrn
        finally:
            loop.close()
    except Exception as e:
        logger.debug(f'NP DOM MRN extraction failed: {e}')
        return None


def _get_idle_seconds():
    """
    Use GetLastInputInfo (user32.dll) to determine seconds since
    last keyboard/mouse input. Returns 0 on failure.
    """
    try:
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [
                ('cbSize', ctypes.wintypes.UINT),
                ('dwTime', ctypes.wintypes.DWORD),
            ]

        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
            millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
            return max(0, millis // 1000)
    except Exception as e:
        logger.debug(f'GetLastInputInfo failed: {e}')
    return 0


def _try_ocr_mrn():
    """
    Fallback: OCR the AC window to find MRN.

    Strategy (OCR-first, two-pass):
      Pass 1: Title bar only (top 60px) — fast, high confidence
      Pass 2: Broader top region (top 200px) — catches ID shown in
              patient header area, not just the title bar

    Returns MRN string or None.
    """
    try:
        import pytesseract
        from PIL import ImageGrab

        rect = get_ac_window_rect()

        # --- Pass 1: Title bar (top 60px) ---
        if rect:
            left, top, right, _bottom = rect
            region = (left, top, right, top + 60)
        else:
            region = getattr(config, 'MRN_CAPTURE_REGION', (0, 0, 300, 50))

        img = ImageGrab.grab(bbox=region)
        text = pytesseract.image_to_string(img, config='--psm 7')
        match = re.search(r'ID:\s*(\d+)', text)
        if match:
            return match.group(1)

        # --- Pass 2: Broader patient header area (top 200px) ---
        if rect:
            left, top, right, bottom = rect
            header_height = min(200, bottom - top)
            region2 = (left, top, right, top + header_height)
            img2 = ImageGrab.grab(bbox=region2)
            text2 = pytesseract.image_to_string(img2, config='--psm 6')
            match2 = re.search(r'ID:\s*(\d+)', text2)
            if match2:
                return match2.group(1)
            # Look for standalone 4+ digit number near "Patient" or "Chart"
            match2 = re.search(r'\b(\d{4,})\b', text2)
            if match2:
                return match2.group(1)
        else:
            # Single-pass fallback: look for any 4+ digit number
            match = re.search(r'\b(\d{4,})\b', text)
            return match.group(1) if match else None

        return None
    except Exception as e:
        logger.debug(f'OCR fallback failed: {e}')
        return None


def _show_chart_duration_warning(mrn):
    """Show a Windows toast notification for long chart open time."""
    last4 = mrn[-4:] if len(mrn) >= 4 else mrn
    msg = f'Chart ****{last4} has been open {getattr(config, "MAX_CHART_OPEN_MINUTES", 20)} minutes. Still working?'

    try:
        from plyer import notification
        notification.notify(
            title='NP Companion',
            message=msg,
            timeout=10,
        )
        logger.info(f'Chart duration warning shown for ...{_hash_mrn(mrn)}')
    except ImportError:
        try:
            from win10toast import ToastNotifier
            toast = ToastNotifier()
            toast.show_toast('NP Companion', msg, duration=10, threaded=True)
            logger.info(f'Chart duration warning shown for ...{_hash_mrn(mrn)}')
        except Exception as e:
            logger.warning(f'Toast notification failed: {e}')
    except Exception as e:
        logger.warning(f'Chart duration warning failed: {e}')


def read_mrn(user_id):
    """
    Core MRN detection function called every 3 seconds by the agent.

    Three-tier detection:
      1. Primary — win32gui title bar parsing
      2. Fallback — OCR on MRN capture region
      3. Last resort — Tesseract region OCR

    Returns
    -------
    dict
        {"mrn": str|None, "dob": str|None, "source": "title"|"ocr"|"none"}
    """
    global _last_known_mrn, _last_mrn_seen_at, _blank_since

    now = datetime.now(timezone.utc)
    source = 'none'
    mrn = None
    dob = None

    # ---- Tier 1: Title bar parsing ------------------------------------
    if is_ac_foreground():
        mrn = get_active_patient_mrn()
        dob = get_active_patient_dob()
        if mrn:
            source = 'title'

    # ---- Tier 1.5: NP DOM extraction (if AC title bar had no MRN) ----
    if not mrn:
        mrn = _try_np_dom_mrn()
        if mrn:
            source = 'np_dom'

    # ---- Tier 2 & 3: OCR fallback ------------------------------------
    if not mrn:
        mrn = _try_ocr_mrn()
        if mrn:
            source = 'ocr'

    # ---- TimeLog management -------------------------------------------
    from models import db
    from models.timelog import TimeLog

    idle_seconds = _get_idle_seconds()
    idle_threshold = getattr(config, 'IDLE_THRESHOLD_SECONDS', 300)
    is_idle = idle_seconds >= idle_threshold

    if mrn:
        _blank_since = None  # Reset blank timer

        if mrn != _last_known_mrn:
            # New MRN detected — close previous session
            if _last_known_mrn:
                _close_active_session(user_id, now)
                _chart_open_since.pop(_last_known_mrn, None)

            # Start a new session
            new_entry = TimeLog(
                user_id=user_id,
                mrn=mrn,
                session_start=now,
            )
            db.session.add(new_entry)
            db.session.commit()
            _chart_open_since[mrn] = now
            logger.info(f'New session started for MRN hash {_hash_mrn(mrn)}')

        _last_known_mrn = mrn
        _last_mrn_seen_at = now

        # ---- Idle detection (F6b) ------------------------------------
        active = (
            TimeLog.query
            .filter_by(user_id=user_id, mrn=mrn, session_end=None)
            .order_by(TimeLog.session_start.desc())
            .first()
        )
        if active:
            if is_idle:
                if not active.face_to_face_end:
                    # Use face_to_face_end as a "paused_at" marker
                    # to avoid adding another column right now
                    pass
                total_idle = getattr(active, 'total_idle_seconds', None) or 0
                # Accumulate idle time (3-second polling interval)
                active.total_idle_seconds = total_idle + 3
                db.session.commit()

        # ---- Chart duration warning (F6a) ----------------------------
        max_minutes = getattr(config, 'MAX_CHART_OPEN_MINUTES', 20)
        chart_start = _chart_open_since.get(mrn, now)
        minutes_open = (now - chart_start).total_seconds() / 60

        if minutes_open >= max_minutes and is_idle:
            last_warn = _last_warning_at.get(mrn)
            if not last_warn or (now - last_warn).total_seconds() >= 3600:
                _show_chart_duration_warning(mrn)
                _last_warning_at[mrn] = now

    else:
        # MRN is blank/unreadable
        if _last_known_mrn:
            if _blank_since is None:
                _blank_since = now
            elif (now - _blank_since).total_seconds() >= _BLANK_TIMEOUT:
                # Timeout reached — close the session
                _close_active_session(user_id, now)
                _chart_open_since.pop(_last_known_mrn, None)
                _last_known_mrn = None
                _blank_since = None

    return {'mrn': mrn, 'dob': dob, 'source': source}


def _close_active_session(user_id, now):
    """Close the most recent open TimeLog for the given user/MRN."""
    from models import db
    from models.timelog import TimeLog

    active = (
        TimeLog.query
        .filter_by(user_id=user_id, mrn=_last_known_mrn, session_end=None)
        .order_by(TimeLog.session_start.desc())
        .first()
    )
    if active:
        active.session_end = now
        active.duration_seconds = int((now - active.session_start).total_seconds())
        db.session.commit()
        logger.info(f'Session closed for MRN hash {_hash_mrn(_last_known_mrn)}, '
                     f'duration={active.duration_seconds}s')


def calibrate_mrn_reader():
    """
    Diagnostic tool triggered from the agent tray menu.
    Prints current window info for MRN reader calibration.
    """
    print('=' * 60)
    print('MRN Reader Calibration')
    print('=' * 60)

    title = get_ac_chart_title()
    print(f'Foreground window title: {title}')
    print(f'AC is foreground: {is_ac_foreground()}')

    mrn = get_active_patient_mrn()
    dob = get_active_patient_dob()
    print(f'Extracted MRN: {mrn}')
    print(f'Extracted DOB: {dob}')

    ocr_mrn = _try_ocr_mrn()
    print(f'OCR fallback MRN: {ocr_mrn}')
    print(f'OCR would succeed: {ocr_mrn is not None}')
    print('=' * 60)

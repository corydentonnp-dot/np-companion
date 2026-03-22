"""
CareCompanion — Inbox OCR Reader

File location: carecompanion/agent/inbox_reader.py

Reads the Amazing Charts inbox by cycling through filter tabs,
performing OCR on each view, and tracking changes via diff hashing.

Feature: F5 (Inbox Monitor with Diff Tracking)
Feature: F5b (Critical Value Detection)

HIPAA note: Only item hashes are stored — never patient names.
"""

import hashlib
import logging
import time
from datetime import datetime, timezone

import config
from agent.ac_window import is_ac_foreground, is_chart_window_open, get_ac_state
from agent.ocr_helpers import find_and_click, find_text_on_screen, screenshot_region_near_text, ocr_get_full_text

logger = logging.getLogger('agent.inbox_reader')

# Ordered list of AC inbox filters to cycle through.
# v4 confirms 7 filter options. "Show Everything" is cycled last
# to capture any items that didn't appear in category-specific filters
# and to provide a total item count for validation.
INBOX_FILTERS = [
    'Show Charts',
    'Show Charts to Co-Sign',
    'Show Imports to Sign-Off',
    'Show Labs to Sign-Off',
    'Show Orders',
    'Show Patient Messages',
    'Show Everything',
]

# Keywords that trigger critical value alerts
CRITICAL_KEYWORDS = ['CRITICAL', 'PANIC VALUE', 'STAT', 'H*', 'L*']


def _hash_item(filter_name, subject, received):
    """Generate a non-reversible hash for a single inbox item."""
    raw = f'{filter_name}|{subject}|{received}'
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _categorize_subject(subject):
    """Classify an inbox item by its subject prefix."""
    upper = subject.upper().strip()
    if upper.startswith('LAB:') or upper.startswith('LAB '):
        return 'lab'
    if upper.startswith('CHART:') or upper.startswith('CHART '):
        return 'chart'
    if 'VIIS' in upper or 'IMMUNIZ' in upper:
        return 'immunization'
    if upper.startswith('MSG:') or upper.startswith('MESSAGE'):
        return 'message'
    if upper.startswith('RX:') or 'REFILL' in upper:
        return 'refill'
    if upper.startswith('RAD:') or 'RADIOLOGY' in upper:
        return 'radiology'
    if any(kw in upper for kw in ('DISCHARGE', 'DC SUMMARY', 'HOSPITAL SUMMARY',
                                   'SNF DISCHARGE', 'DISCH SUMM', 'TRANSITION OF CARE')):
        return 'discharge'
    return 'other'


def _check_critical(text):
    """Return True if OCR text contains critical value indicators."""
    upper = text.upper()
    for keyword in CRITICAL_KEYWORDS:
        if keyword in upper:
            return True
    return False


def _click_filter(filter_text):
    """
    Click the inbox filter dropdown and select the given filter.

    Strategy (OCR-first):
      1. Try to find the filter dropdown label via OCR
      2. Click it, then type the filter name
      3. Fall back to config coordinates only if OCR fails
    """
    try:
        import pyautogui

        # OCR-first: look for the dropdown label text on screen
        # AC's inbox filter dropdown is labeled "Show" or shows the
        # current filter name. Try to find it by looking for known text.
        fallback_xy = getattr(config, 'INBOX_FILTER_DROPDOWN_XY', (0, 0))
        clicked = find_and_click('Show', partial=True, fallback_xy=fallback_xy)

        if not clicked:
            logger.warning(f'Could not find inbox filter dropdown for "{filter_text}"')
            return False

        time.sleep(0.3)

        # Type the filter name to find it in the dropdown
        # (AC dropdown supports typing to filter)
        pyautogui.typewrite(filter_text[:10], interval=0.05)
        time.sleep(0.2)
        pyautogui.press('enter')
        time.sleep(0.5)
        return True
    except Exception as e:
        logger.error(f'Failed to click filter "{filter_text}": {e}')
        return False


def _ocr_inbox_table():
    """
    Screenshot and OCR the inbox table region.

    Strategy (OCR-first):
      1. Find the inbox table area by looking for a known header
         text (e.g. "Subject" or "Received" column headers)
      2. Screenshot the region below that header
      3. Fall back to config coordinates only if OCR can't find headers

    Returns raw text string.
    """
    try:
        from PIL import ImageGrab

        # OCR-first: find the table by locating column headers
        # AC inbox table has "Subject" and "Received" column headers
        table_img = screenshot_region_near_text(
            'Subject', width=800, height=500, direction='below', offset_px=5
        )

        if table_img:
            text = ocr_get_full_text(table_img)
            if text.strip():
                return text

        # Fallback: try the config region if set
        region = getattr(config, 'INBOX_TABLE_REGION', (0, 0, 0, 0))
        if region != (0, 0, 0, 0):
            logger.info('OCR header search failed — using fallback INBOX_TABLE_REGION')
            img = ImageGrab.grab(bbox=region)
            return ocr_get_full_text(img)

        logger.warning('Cannot locate inbox table — no OCR headers found and no fallback region')
        return ''
    except Exception as e:
        logger.error(f'Inbox OCR failed: {e}')
        return ''


def _parse_rows(text, filter_name):
    """
    Parse OCR text into individual inbox items.

    Returns list of dicts:
        [{"filter": str, "subject": str, "received": str, "hash": str,
          "category": str, "is_critical": bool}]
    """
    items = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    for line in lines:
        # Each OCR line is treated as one inbox item
        # Attempt to split into subject and received date
        parts = line.rsplit('  ', 1)  # Double-space split
        subject = parts[0].strip() if parts else line
        received = parts[1].strip() if len(parts) > 1 else ''

        if not subject:
            continue

        item_hash = _hash_item(filter_name, subject, received)
        category = _categorize_subject(subject)
        is_critical = _check_critical(subject)

        items.append({
            'filter': filter_name,
            'subject': subject,
            'received': received,
            'hash': item_hash,
            'category': category,
            'is_critical': is_critical,
        })

    return items


def _auto_create_tcm_watch(user_id, item, now):
    """Create a TCMWatchEntry when a discharge inbox item is detected."""
    try:
        from models.tcm import TCMWatchEntry
        from models import db

        # Extract facility from subject if possible (e.g. "DC Summary - Memorial Hospital")
        subject = item.get('subject', '')
        facility = ''
        for sep in (' - ', ': ', ' from '):
            if sep in subject:
                facility = subject.split(sep, 1)[1].strip()
                break

        # Use item hash as patient_mrn_hash (no PHI available from OCR subject)
        entry = TCMWatchEntry(
            patient_mrn_hash=item['hash'],
            user_id=user_id,
            discharge_date=now.date(),
            discharge_facility=facility or 'Unknown',
            status='active',
            notes=f'Auto-created from inbox: {subject}',
        )
        entry.compute_deadlines()
        db.session.add(entry)
        logger.info(f'Auto-created TCM watch entry from discharge inbox item: {item["hash"]}')
    except Exception as e:
        logger.error(f'Failed to auto-create TCM watch entry: {e}')


def read_inbox(user_id):
    """
    Main inbox reading function called by the agent.

    Cycles through all inbox filters, OCRs each view, performs
    diff tracking against existing InboxItems in the database,
    and creates an InboxSnapshot with category counts.

    Returns
    -------
    dict
        {"new_count": int, "resolved_count": int, "critical_flags": int,
         "total_unresolved": int, "counts": {...}}
    """
    logger.info(f'Starting inbox read for user {user_id}')

    # Verify AC is on the home screen before reading inbox
    ac_state = get_ac_state()
    if ac_state != 'home_screen':
        logger.info(f'AC state is "{ac_state}" — need "home_screen" for inbox read, skipping')
        return {'new_count': 0, 'resolved_count': 0, 'critical_flags': 0,
                'total_unresolved': 0, 'counts': {}}

    from models import db
    from models.inbox import InboxSnapshot, InboxItem

    now = datetime.now(timezone.utc)
    all_items = []
    critical_flags = 0

    # Cycle through each filter
    for filter_name in INBOX_FILTERS:
        logger.info(f'Reading filter: {filter_name}')
        if not _click_filter(filter_name):
            continue

        text = _ocr_inbox_table()
        if not text.strip():
            logger.info(f'No items in {filter_name}')
            continue

        items = _parse_rows(text, filter_name)
        all_items.extend(items)

        for item in items:
            if item['is_critical']:
                critical_flags += 1

    # Get all current unresolved items for this user
    existing = (
        InboxItem.query
        .filter_by(user_id=user_id, is_resolved=False)
        .all()
    )
    existing_hashes = {item.item_hash: item for item in existing}
    scanned_hashes = {item['hash'] for item in all_items}

    new_count = 0
    resolved_count = 0

    # New items — hashes seen now but not in DB
    for item in all_items:
        if item['hash'] not in existing_hashes:
            new_entry = InboxItem(
                user_id=user_id,
                item_hash=item['hash'],
                item_type=item['category'],
                first_seen_at=now,
                last_seen_at=now,
                priority='critical' if item['is_critical'] else 'normal',
            )
            db.session.add(new_entry)
            new_count += 1

            # Auto-create TCM watch entry for discharge items
            if item['category'] == 'discharge':
                _auto_create_tcm_watch(user_id, item, now)
        else:
            # Update last_seen_at for existing items
            existing_hashes[item['hash']].last_seen_at = now

    # Resolved items — in DB but not in current scan
    for h, item in existing_hashes.items():
        if h not in scanned_hashes:
            item.is_resolved = True
            resolved_count += 1

    # Build category counts
    counts = {}
    for item in all_items:
        cat = item['category']
        counts[cat] = counts.get(cat, 0) + 1

    # Create snapshot
    snapshot = InboxSnapshot(
        user_id=user_id,
        captured_at=now,
        labs_count=counts.get('lab', 0),
        radiology_count=counts.get('radiology', 0),
        messages_count=counts.get('message', 0),
        refills_count=counts.get('refill', 0),
        other_count=counts.get('other', 0) + counts.get('chart', 0)
                    + counts.get('immunization', 0) + counts.get('discharge', 0),
    )
    db.session.add(snapshot)
    db.session.commit()

    total_unresolved = InboxItem.query.filter_by(user_id=user_id, is_resolved=False).count()

    logger.info(f'Inbox read complete: {new_count} new, {resolved_count} resolved, '
                f'{critical_flags} critical, {total_unresolved} total unresolved')

    return {
        'new_count': new_count,
        'resolved_count': resolved_count,
        'critical_flags': critical_flags,
        'total_unresolved': total_unresolved,
        'counts': counts,
    }

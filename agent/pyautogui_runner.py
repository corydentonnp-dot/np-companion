"""
CareCompanion — PyAutoGUI Order Executor (F8)

File location: carecompanion/agent/pyautogui_runner.py

Executes order sets in Amazing Charts by automating mouse clicks
and keyboard input. Safety-first design:
  - Verifies AC is foreground before EVERY click
  - Takes pre-execution screenshot
  - Stops immediately on any failure
  - Tracks per-item execution state for recovery (F8e)

When AC_MOCK_MODE is True, all automation calls are simulated
and return success without touching the real screen.
"""

import logging
import os
from datetime import datetime, timezone

import config
from models import db
from models.orderset import OrderExecution, OrderExecutionItem

logger = logging.getLogger('agent.pyautogui_runner')

# Screenshot storage
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Optional imports — not available in all environments
try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    pyautogui.PAUSE = 0.3
except ImportError:
    pyautogui = None

_mock_mode = getattr(config, 'AC_MOCK_MODE', False)


def _is_ac_foreground():
    """Check if Amazing Charts is the foreground window."""
    if _mock_mode:
        return True
    try:
        from agent.ac_window import find_ac_window
        return find_ac_window() is not None
    except Exception:
        return False


def _take_screenshot(label='screenshot'):
    """Take a screenshot and return the file path."""
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{label}_{ts}.png'
    filepath = os.path.join(SCREENSHOT_DIR, filename)

    if _mock_mode:
        # In mock mode, create a placeholder
        logger.info(f'Mock screenshot: {filepath}')
        return filepath

    if pyautogui:
        try:
            img = pyautogui.screenshot()
            img.save(filepath)
            return filepath
        except Exception as e:
            logger.error(f'Screenshot failed: {e}')

    return ''


def execute_order_set(execution_id):
    """
    Execute an order set tracked by an OrderExecution record.
    Processes only items with status='pending'.

    Returns a result dict for the API response.
    """
    execution = db.session.get(OrderExecution, execution_id)
    if not execution:
        return {'success': False, 'error': 'Execution record not found.'}

    pending_items = [i for i in execution.items if i.status == 'pending']
    if not pending_items:
        return {'success': True, 'message': 'No pending items to execute.', 'execution_id': execution.id}

    # Step 1: Verify Amazing Charts is foreground
    if not _is_ac_foreground():
        execution.status = 'failed'
        execution.error_message = 'Amazing Charts is not the foreground window. Aborting.'
        execution.finished_at = datetime.now(timezone.utc)
        db.session.commit()
        return {
            'success': False,
            'error': execution.error_message,
            'execution_id': execution.id,
        }

    # Step 2: Pre-execution screenshot
    pre_screenshot = _take_screenshot('pre_execution')
    execution.pre_screenshot = pre_screenshot

    # Step 3: Execute each pending item
    completed = 0
    failed = 0

    for item in pending_items:
        try:
            # Verify AC is still foreground before each click
            if not _is_ac_foreground():
                item.status = 'failed'
                item.error_message = 'Amazing Charts lost focus during execution.'
                execution.status = 'interrupted'
                execution.error_message = 'Amazing Charts lost focus. Execution interrupted.'
                execution.completed_items = completed
                execution.failed_items = failed + 1
                execution.finished_at = datetime.now(timezone.utc)
                db.session.commit()
                return {
                    'success': False,
                    'error': execution.error_message,
                    'execution_id': execution.id,
                    'completed': completed,
                    'failed': failed + 1,
                    'interrupted': True,
                }

            # Execute the order click
            success = _execute_single_order(item)

            if success:
                item.status = 'completed'
                completed += 1
            else:
                item.status = 'failed'
                item.error_screenshot = _take_screenshot(f'fail_{item.id}')
                item.error_message = 'Order not found or click failed.'
                failed += 1

                # Stop immediately on failure
                execution.status = 'interrupted'
                execution.error_message = f'Failed on order: {item.order_name}'
                execution.completed_items = completed
                execution.failed_items = failed
                execution.finished_at = datetime.now(timezone.utc)
                db.session.commit()
                return {
                    'success': False,
                    'error': execution.error_message,
                    'execution_id': execution.id,
                    'completed': completed,
                    'failed': failed,
                    'interrupted': True,
                }

            db.session.commit()

        except Exception as e:
            logger.error(f'Execution error on item {item.id}: {e}')
            item.status = 'failed'
            item.error_message = str(e)
            item.error_screenshot = _take_screenshot(f'error_{item.id}')
            failed += 1

            execution.status = 'interrupted'
            execution.error_message = f'Exception: {e}'
            execution.completed_items = completed
            execution.failed_items = failed
            execution.finished_at = datetime.now(timezone.utc)
            db.session.commit()
            return {
                'success': False,
                'error': str(e),
                'execution_id': execution.id,
                'completed': completed,
                'failed': failed,
                'interrupted': True,
            }

    # All items completed successfully
    execution.status = 'completed'
    execution.completed_items = completed
    execution.failed_items = failed
    execution.finished_at = datetime.now(timezone.utc)
    db.session.commit()

    return {
        'success': True,
        'execution_id': execution.id,
        'completed': completed,
        'failed': failed,
        'message': f'All {completed} orders executed successfully.',
    }


def _execute_single_order(item):
    """
    Execute a single order item in Amazing Charts.

    In mock mode, always returns True.
    In real mode, navigates to the correct tab and clicks the checkbox.
    Validates the tab name against known AC order tabs before executing.
    """
    if _mock_mode:
        logger.info(f'Mock execute: {item.order_name} (tab={item.order_tab})')
        return True

    # Validate tab name against known AC order tabs
    if item.order_tab:
        from models.orderset import ORDER_TABS
        if item.order_tab not in ORDER_TABS:
            logger.warning(f'Unknown order tab: "{item.order_tab}" — '
                           f'valid tabs are: {ORDER_TABS}')
            # Continue anyway — OCR will attempt to find it

    if not pyautogui:
        logger.error('pyautogui not installed — cannot execute orders')
        return False

    try:
        # Real execution flow:
        # 1. Click the correct tab using OCR to find the tab label
        # 2. Scroll to find the order by label text
        # 3. Click the checkbox

        # NOTE: The exact coordinates need calibration per AC installation.
        # This uses OCR-based element detection for portability.
        from agent.ocr_helpers import find_text_on_screen, find_and_click

        # Navigate to the correct tab if specified
        if item.order_tab:
            if not find_and_click(item.order_tab):
                logger.warning(f'Could not find tab: {item.order_tab}')
                return False
            pyautogui.sleep(0.5)

        # Find and click the order checkbox
        label = item.order_label or item.order_name
        if not find_and_click(label):
            logger.warning(f'Could not find order: {label}')
            return False

        return True

    except Exception as e:
        logger.error(f'Failed to execute order "{item.order_name}": {e}')
        return False

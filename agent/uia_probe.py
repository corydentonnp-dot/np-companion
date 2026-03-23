"""
CareCompanion — UIA Feasibility Probe

File location: carecompanion/agent/uia_probe.py

Diagnostic script that connects to Amazing Charts via Windows UI
Automation (UIA) and dumps the control tree. Run this with AC open
at different states (home screen, chart open, inbox visible) to
discover which controls are programmatically accessible.

Usage:
    venv\\Scripts\\python.exe agent/uia_probe.py [--depth N] [--output FILE]

Output is saved to data/uia_dumps/ by default.

This script is a one-time probe — it does NOT modify AC or send clicks.
Read-only inspection only.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger('agent.uia_probe')

# ---------------------------------------------------------------------------
# Safe imports — pywinauto may not be installed yet
# ---------------------------------------------------------------------------
try:
    from pywinauto import Desktop, Application, findwindows
    from pywinauto.controls.uiawrapper import UIAWrapper
    HAS_PYWINAUTO = True
except ImportError:
    HAS_PYWINAUTO = False

try:
    import win32gui
except ImportError:
    win32gui = None


def find_ac_hwnd():
    """Find the Amazing Charts main window handle via win32gui."""
    if not win32gui:
        return None
    result = []
    def _cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and title.startswith('Amazing Charts'):
                result.append((hwnd, title))
    try:
        win32gui.EnumWindows(_cb, None)
    except Exception as e:
        logger.error(f'EnumWindows failed: {e}')
    return result


def _control_to_dict(ctrl, depth=0, max_depth=8):
    """Recursively convert a UIA control wrapper to a JSON-serializable dict."""
    if depth > max_depth:
        return {'_truncated': True, '_reason': f'max_depth={max_depth}'}

    info = {}
    try:
        info['control_type'] = ctrl.element_info.control_type or 'Unknown'
    except Exception:
        info['control_type'] = 'Unknown'
    try:
        info['name'] = ctrl.element_info.name or ''
    except Exception:
        info['name'] = ''
    try:
        info['class_name'] = ctrl.element_info.class_name or ''
    except Exception:
        info['class_name'] = ''
    try:
        info['automation_id'] = ctrl.element_info.automation_id or ''
    except Exception:
        info['automation_id'] = ''
    try:
        rect = ctrl.element_info.rectangle
        info['rect'] = {
            'left': rect.left, 'top': rect.top,
            'right': rect.right, 'bottom': rect.bottom
        }
    except Exception:
        info['rect'] = None
    try:
        info['is_enabled'] = ctrl.is_enabled()
    except Exception:
        info['is_enabled'] = None
    try:
        info['is_visible'] = ctrl.is_visible()
    except Exception:
        info['is_visible'] = None

    # Try to read text value for edit/text controls
    try:
        if hasattr(ctrl, 'window_text'):
            text = ctrl.window_text()
            if text and text != info['name']:
                info['window_text'] = text[:200]
    except Exception:
        pass

    # Recursively enumerate children
    children = []
    try:
        for child in ctrl.children():
            children.append(_control_to_dict(child, depth + 1, max_depth))
    except Exception as e:
        children = [{'_error': str(e)}]

    if children:
        info['children'] = children
        info['child_count'] = len(children)

    return info


def probe_uia_tree(hwnd, title, max_depth=8):
    """
    Connect to AC window via UIA backend and dump the full control tree.

    Parameters
    ----------
    hwnd : int
        Window handle for the AC window.
    title : str
        Window title (for logging/metadata).
    max_depth : int
        Maximum depth to recurse into the control tree.

    Returns
    -------
    dict
        Full control tree as a nested dict.
    """
    try:
        app = Application(backend='uia').connect(handle=hwnd)
        main = app.window(handle=hwnd)

        tree = _control_to_dict(main.wrapper_object(), depth=0, max_depth=max_depth)
        tree['_meta'] = {
            'hwnd': hwnd,
            'title': title,
            'probe_time': datetime.now(timezone.utc).isoformat(),
            'max_depth': max_depth,
            'backend': 'uia',
        }
        return tree
    except Exception as e:
        logger.error(f'UIA probe failed: {e}')
        return {
            '_error': str(e),
            '_meta': {
                'hwnd': hwnd,
                'title': title,
                'probe_time': datetime.now(timezone.utc).isoformat(),
                'backend': 'uia',
            }
        }


def probe_win32_tree(hwnd, title, max_depth=8):
    """
    Fallback probe using win32 backend (for VB6/legacy apps where
    UIA tree may be sparse).
    """
    try:
        app = Application(backend='win32').connect(handle=hwnd)
        main = app.window(handle=hwnd)

        tree = _control_to_dict(main.wrapper_object(), depth=0, max_depth=max_depth)
        tree['_meta'] = {
            'hwnd': hwnd,
            'title': title,
            'probe_time': datetime.now(timezone.utc).isoformat(),
            'max_depth': max_depth,
            'backend': 'win32',
        }
        return tree
    except Exception as e:
        logger.error(f'Win32 probe failed: {e}')
        return {
            '_error': str(e),
            '_meta': {
                'hwnd': hwnd,
                'title': title,
                'probe_time': datetime.now(timezone.utc).isoformat(),
                'backend': 'win32',
            }
        }


def _count_controls(tree):
    """Count total controls in a tree dict (recursive)."""
    count = 1
    for child in tree.get('children', []):
        if isinstance(child, dict) and '_error' not in child and '_truncated' not in child:
            count += _count_controls(child)
    return count


def _summarize_tree(tree, indent=0):
    """Return a human-readable summary of the control tree."""
    lines = []
    prefix = '  ' * indent
    name = tree.get('name', '')
    ctype = tree.get('control_type', '?')
    cls = tree.get('class_name', '')
    aid = tree.get('automation_id', '')

    label = f'{prefix}[{ctype}]'
    if name:
        label += f' "{name}"'
    if cls:
        label += f'  class={cls}'
    if aid:
        label += f'  id={aid}'
    lines.append(label)

    for child in tree.get('children', []):
        if isinstance(child, dict) and '_error' not in child and '_truncated' not in child:
            lines.extend(_summarize_tree(child, indent + 1))
    return lines


def save_dump(tree, label, output_dir=None):
    """Save the tree dump to data/uia_dumps/ as JSON + human-readable text."""
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'uia_dumps'
        )
    os.makedirs(output_dir, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    backend = tree.get('_meta', {}).get('backend', 'unknown')
    base = f'{label}_{backend}_{ts}'

    json_path = os.path.join(output_dir, f'{base}.json')
    txt_path = os.path.join(output_dir, f'{base}.txt')

    # JSON dump
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(tree, f, indent=2, default=str)

    # Human-readable summary
    summary_lines = _summarize_tree(tree)
    total = _count_controls(tree)
    header = [
        f'UIA Probe — {label}',
        f'Backend: {backend}',
        f'Time: {tree.get("_meta", {}).get("probe_time", "?")}',
        f'Title: {tree.get("_meta", {}).get("title", "?")}',
        f'Total controls: {total}',
        '=' * 70,
        '',
    ]
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(header + summary_lines))

    return json_path, txt_path, total


def detect_ac_state(title):
    """Detect AC state from window title for labeling the dump."""
    import re
    if re.search(r'DOB:.*ID:\s*\d+', title):
        return 'chart_open'
    if 'login' in title.lower():
        return 'login_screen'
    if title.startswith('Amazing Charts'):
        return 'home_screen'
    return 'unknown'


def main():
    parser = argparse.ArgumentParser(description='UIA Feasibility Probe for Amazing Charts')
    parser.add_argument('--depth', type=int, default=8,
                        help='Maximum tree depth to recurse (default: 8)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output directory (default: data/uia_dumps/)')
    parser.add_argument('--backend', choices=['uia', 'win32', 'both'], default='both',
                        help='Which pywinauto backend to use (default: both)')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    if not HAS_PYWINAUTO:
        logger.error('pywinauto is not installed. Run: pip install pywinauto==0.6.8')
        sys.exit(1)

    # Find AC windows
    windows = find_ac_hwnd()
    if not windows:
        logger.error('Amazing Charts is not running or no visible window found.')
        logger.info('Start AC and navigate to the state you want to probe, then re-run.')
        sys.exit(1)

    logger.info(f'Found {len(windows)} AC window(s):')
    for hwnd, title in windows:
        logger.info(f'  hwnd={hwnd}  title="{title[:80]}"')

    for hwnd, title in windows:
        state = detect_ac_state(title)
        logger.info(f'\n{"="*70}')
        logger.info(f'Probing AC window: state={state}, hwnd={hwnd}')
        logger.info(f'Title: {title}')
        logger.info(f'{"="*70}')

        if args.backend in ('uia', 'both'):
            logger.info('\n--- UIA Backend ---')
            tree = probe_uia_tree(hwnd, title, max_depth=args.depth)
            json_path, txt_path, total = save_dump(tree, state, args.output)
            logger.info(f'UIA tree: {total} controls found')
            logger.info(f'  JSON: {json_path}')
            logger.info(f'  Text: {txt_path}')

            if total <= 3:
                logger.warning('UIA tree is very sparse — AC may use custom-drawn controls.')
                logger.warning('Win32 backend or OCR fallback recommended.')

        if args.backend in ('win32', 'both'):
            logger.info('\n--- Win32 Backend ---')
            tree = probe_win32_tree(hwnd, title, max_depth=args.depth)
            json_path, txt_path, total = save_dump(tree, state, args.output)
            logger.info(f'Win32 tree: {total} controls found')
            logger.info(f'  JSON: {json_path}')
            logger.info(f'  Text: {txt_path}')

    logger.info('\nProbe complete. Review dumps in data/uia_dumps/')
    logger.info('Run with AC at different states (home, chart, inbox) for full coverage.')


if __name__ == '__main__':
    main()

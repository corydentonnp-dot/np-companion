"""
NP Companion — Unified Launcher

Entry point for both dev and packaged (.exe) modes.

Usage:
  python launcher.py                 # default: --mode=all
  python launcher.py --mode=dev      # Flask dev server with hot-reload
  python launcher.py --mode=server   # Flask only (no agent, no tray)
  python launcher.py --mode=agent    # Agent only (tray + scheduler)
  python launcher.py --mode=all      # Full stack: Flask + Agent + tray + pywebview

When frozen (PyInstaller exe), double-clicking runs --mode=all.
"""

import argparse
import os
import sys
import threading
import time
import logging

# ── External config override ─────────────────────────────────────
# When frozen, the user's config.py lives next to the .exe (not inside
# _internal).  We prepend that directory to sys.path so that
# `import config` finds it before any bundled copy.
if getattr(sys, 'frozen', False):
    _exe_dir = os.path.dirname(sys.executable)
    if _exe_dir not in sys.path:
        sys.path.insert(0, _exe_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('launcher')


def _setup_env():
    """Set environment variables needed by bundled binaries."""
    from utils.paths import is_frozen, get_tesseract_path, get_playwright_browsers_path

    # Tesseract
    tess = get_tesseract_path()
    if os.path.isfile(tess):
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tess
        except ImportError:
            pass

    # Playwright browsers
    if is_frozen():
        browsers = get_playwright_browsers_path()
        if os.path.isdir(browsers):
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = browsers

    # Clean up leftover .old files from a previous update
    from utils.paths import get_base_dir
    base = get_base_dir()
    for f in os.listdir(base):
        if f.endswith('.old'):
            try:
                os.remove(os.path.join(base, f))
            except OSError:
                pass


def _run_flask_dev():
    """Flask development server with hot-reload."""
    from app import create_app
    app = create_app()
    app.run(
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5000),
        debug=True,
        use_reloader=True,
    )


def _run_flask_production():
    """Flask production server in a thread (no reloader)."""
    from app import create_app
    app = create_app()
    app.run(
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5000),
        debug=False,
        use_reloader=False,
    )


def _start_flask_thread():
    """Start Flask in a daemon thread and return it."""
    t = threading.Thread(target=_run_flask_production, daemon=True, name='flask')
    t.start()
    return t


def _start_agent_headless():
    """Start the agent (scheduler + HTTP 5001) without blocking."""
    from agent_service import AgentService
    service = AgentService()
    service.start_headless()
    return service


def _run_agent_standalone():
    """Run agent.py as a standalone process with tray icon."""
    from agent_service import main as agent_main
    agent_main()


def _run_all():
    """
    Full-stack mode: Flask + Agent + system tray + pywebview window.
    This is what runs when the .exe is double-clicked.
    """
    _setup_env()

    logger.info('Starting NP Companion (full stack)...')

    # 1. Start Flask in background thread
    flask_thread = _start_flask_thread()

    # Wait for Flask to boot
    _wait_for_flask(timeout=15)

    # 2. Start Agent (headless — no tray, we manage tray here)
    agent_service = _start_agent_headless()

    # 3. Try pywebview for native window, fall back to browser
    webview_available = False
    try:
        import webview
        webview_available = True
    except ImportError:
        pass

    if webview_available:
        _run_with_webview(agent_service)
    else:
        _run_with_tray_only(agent_service)


def _wait_for_flask(timeout=15):
    """Block until Flask responds on port 5000."""
    import urllib.request
    import urllib.error
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen('http://127.0.0.1:5000/login', timeout=2)
            logger.info('Flask server is ready')
            return
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)
    logger.warning('Flask did not respond within %ds — continuing anyway', timeout)


def _run_with_webview(agent_service):
    """Open pywebview native window; closing hides to tray."""
    import webview

    try:
        import pystray
        from pystray import MenuItem as TrayItem
        from PIL import Image, ImageDraw
        has_tray = True
    except ImportError:
        has_tray = False

    from utils.paths import get_icon_path

    window = webview.create_window(
        'NP Companion',
        'http://127.0.0.1:5000',
        width=1280,
        height=900,
        min_size=(800, 600),
    )

    if has_tray:
        # Build tray icon
        def _make_icon_image():
            icon_path = get_icon_path()
            if icon_path and os.path.isfile(icon_path):
                return Image.open(icon_path)
            img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse((4, 4, 60, 60), fill=(27, 58, 107, 255))
            draw.text((18, 22), 'NP', fill=(255, 255, 255, 255))
            return img

        tray_icon = None

        def _show_window(icon=None, item=None):
            window.show()

        def _quit_all(icon=None, item=None):
            agent_service.stop()
            if tray_icon:
                tray_icon.stop()
            window.destroy()

        def _on_window_closing():
            """Window X clicked — hide to tray instead of quitting."""
            window.hide()
            return False  # Prevent actual close

        window.events.closing += _on_window_closing

        menu = pystray.Menu(
            TrayItem('Open NP Companion', _show_window, default=True),
            TrayItem('Pause Agent', lambda: agent_service.pause()),
            TrayItem('Resume Agent', lambda: agent_service.resume()),
            TrayItem('Check Inbox Now', lambda: agent_service.trigger_inbox_check()),
            TrayItem('Quit', _quit_all),
        )

        tray_icon = pystray.Icon(
            'NP Companion',
            _make_icon_image(),
            'NP Companion',
            menu,
        )

        # Run tray in background thread — webview.start() must be on main
        tray_thread = threading.Thread(target=tray_icon.run, daemon=True, name='tray')
        tray_thread.start()

    # Block on main thread — this is required by pywebview
    webview.start()

    # If we get here, the window was truly closed (not hidden)
    agent_service.stop()


def _run_with_tray_only(agent_service):
    """No pywebview — open browser and run pystray on main thread."""
    import webbrowser
    webbrowser.open('http://127.0.0.1:5000')

    try:
        import pystray
        from pystray import MenuItem as TrayItem
        from PIL import Image, ImageDraw
    except ImportError:
        logger.info('No pystray — running headless. Press Ctrl+C to stop.')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            agent_service.stop()
        return

    def _make_icon_image():
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((4, 4, 60, 60), fill=(27, 58, 107, 255))
        draw.text((18, 22), 'NP', fill=(255, 255, 255, 255))
        return img

    def _open_app(icon=None, item=None):
        webbrowser.open('http://127.0.0.1:5000')

    def _quit_all(icon=None, item=None):
        agent_service.stop()
        icon.stop()

    menu = pystray.Menu(
        TrayItem('Open NP Companion', _open_app, default=True),
        TrayItem('Pause Agent', lambda: agent_service.pause()),
        TrayItem('Resume Agent', lambda: agent_service.resume()),
        TrayItem('Quit', _quit_all),
    )

    icon = pystray.Icon('NP Companion', _make_icon_image(), 'NP Companion', menu)
    icon.run()  # Blocks on main thread
    agent_service.stop()


def main():
    parser = argparse.ArgumentParser(description='NP Companion Launcher')
    parser.add_argument(
        '--mode',
        choices=['all', 'dev', 'server', 'agent'],
        default='all',
        help='Run mode (default: all)',
    )
    args = parser.parse_args()

    _setup_env()

    if args.mode == 'dev':
        _run_flask_dev()
    elif args.mode == 'server':
        _run_flask_production()
    elif args.mode == 'agent':
        _run_agent_standalone()
    elif args.mode == 'all':
        _run_all()


if __name__ == '__main__':
    main()

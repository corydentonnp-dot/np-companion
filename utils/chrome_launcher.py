"""
Chrome Debug Profile Launcher — Chrome 136+ Compatible

Chrome 136 (May 2025+) ignores --remote-debugging-port when using the
default user profile. A dedicated --user-data-dir is required for CDP.

This module manages launching Chrome with the correct flags and verifying
that the CDP endpoint is reachable.
"""

import json
import logging
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error

logger = logging.getLogger("carecompanion.chrome_launcher")


def is_chrome_debug_running(port=9222):
    """Check if Chrome DevTools Protocol is accepting connections.

    Returns True if GET http://127.0.0.1:{port}/json/version succeeds.
    """
    url = f"http://127.0.0.1:{port}/json/version"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                logger.debug("Chrome CDP active — %s", data.get("Browser", "unknown"))
                return True
    except (urllib.error.URLError, OSError, ValueError):
        pass
    return False


def ensure_chrome_debug(exe_path, profile_dir, port=9222):
    """Launch Chrome with a dedicated debug profile if not already running.

    Args:
        exe_path:    Full path to chrome.exe
        profile_dir: Path for the dedicated --user-data-dir
        port:        CDP port number (default 9222)

    Returns True if Chrome CDP is responding after this call, False otherwise.
    """
    if is_chrome_debug_running(port):
        logger.info("Chrome debug already running on port %d", port)
        return True

    if not os.path.isfile(exe_path):
        # Fallback: try shutil.which in case Chrome is on PATH
        import shutil
        found = shutil.which("chrome") or shutil.which("google-chrome")
        if found:
            logger.info("Chrome not at %s, using PATH fallback: %s", exe_path, found)
            exe_path = found
        else:
            logger.warning("Chrome executable not found at %s and not on PATH", exe_path)
            return False

    # Ensure profile directory exists
    os.makedirs(profile_dir, exist_ok=True)

    cmd = [
        exe_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--remote-allow-origins=*",
        "--restore-last-session",
    ]

    logger.info("Launching Chrome debug profile: %s", " ".join(cmd))

    try:
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW
        subprocess.Popen(cmd, creationflags=creation_flags)
    except OSError as exc:
        logger.error("Failed to launch Chrome: %s", exc)
        return False

    # Poll for CDP readiness (up to 8 seconds)
    for _ in range(8):
        time.sleep(1)
        if is_chrome_debug_running(port):
            logger.info("Chrome debug profile ready on port %d", port)
            return True

    logger.warning("Chrome launched but CDP not responding after 8 s on port %d", port)
    return False


def get_chrome_launch_command(exe_path, profile_dir, port=9222):
    """Return the full shell command string for documentation / admin UI."""
    return (
        f'"{exe_path}" '
        f"--remote-debugging-port={port} "
        f'--user-data-dir="{profile_dir}" '
        f"--remote-allow-origins=* "
        f"--restore-last-session"
    )

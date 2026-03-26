"""
main.py — Entry point for the No Companion Patient Generator.
Run directly:   python main.py
Packaged exe:   PyInstaller calls this automatically.
"""

import sys
import os

# Ensure the bundled data directory is on the path when frozen as .exe
if getattr(sys, "frozen", False):
    base = sys._MEIPASS
    sys.path.insert(0, base)

from gui import launch

if __name__ == "__main__":
    launch()

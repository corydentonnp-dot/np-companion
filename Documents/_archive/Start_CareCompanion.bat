@echo off
:: ============================================================
:: CareCompanion — Start Server
:: Double-click this file (or run it from File Explorer) to
:: start the CareCompanion web server.
::
:: The server will stay open in this window.
:: To STOP the server, close this window or press Ctrl+C.
:: ============================================================

:: Move to the project folder no matter where this file is launched from
cd /d "%~dp0"

:: Run using the venv's Python directly — no activate script needed
venv\Scripts\python.exe launcher.py --mode=dev

:: If the app exits (crash or Ctrl+C), pause so you can read any error messages
:: before the window closes.
echo.
echo ============================================================
echo  CareCompanion has stopped.
echo  Check the messages above for any errors.
echo  Press any key to close this window.
echo ============================================================
pause > nul
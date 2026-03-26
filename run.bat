@echo off
cd /d "%~dp0"
cls
echo.
echo  ============================================
echo   CareCompanion Launcher
echo  ============================================
echo.
echo   [1] Start localhost server  (dev mode)
echo   [2] Start CareCompanion.exe (packaged app)
echo   [3] Start with process watchdog
echo   [4] Fresh machine setup  (first-time install)
echo.
choice /c 1234 /n /m "  Choose (1, 2, 3, or 4): "
if errorlevel 4 goto startsetup
if errorlevel 3 goto startwatch
if errorlevel 2 goto startexe

:startsetup
echo.
echo  Running fresh machine setup...
echo  This will take 2-5 minutes on first run.
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
goto end

:startdev
echo.
echo  Cleaning up orphaned processes...
powershell -ExecutionPolicy Bypass -File "%~dp0run.ps1" --cleanup-only
echo.
echo  Starting CareCompanion dev server...
start "CareCompanion Server" cmd /k powershell -ExecutionPolicy Bypass -File "%~dp0run.ps1"
echo  Waiting for server to boot...
ping -n 5 127.0.0.1 >nul
echo.
echo  ============================================
echo   CareCompanion is running!
echo   http://127.0.0.1:5000/dashboard
echo  ============================================
echo.
echo  The server is in the other command window.
echo  Close THAT window to stop the server.
echo.
pause
exit /b

:startwatch
echo.
echo  Cleaning up orphaned processes...
powershell -ExecutionPolicy Bypass -File "%~dp0run.ps1" --cleanup-only
echo.
echo  Starting CareCompanion with process watchdog...
start "CareCompanion Server" cmd /k powershell -ExecutionPolicy Bypass -File "%~dp0run.ps1" --watch-processes
echo  Waiting for server to boot...
ping -n 5 127.0.0.1 >nul
echo.
echo  ============================================
echo   CareCompanion is running with watchdog!
echo   http://127.0.0.1:5000/dashboard
echo  ============================================
echo.
echo  The server + watchdog are in the other window.
echo  Close THAT window to stop everything.
echo.
pause

:end
exit /b

:startexe
if not exist "dist\CareCompanion\CareCompanion.exe" (
  echo.
  echo  ERROR: CareCompanion.exe not found.
  echo  Build it first:  venv\Scripts\python.exe build.py
  echo.
  pause
  exit /b
)
echo.
echo  Starting CareCompanion.exe...
start "" "dist\CareCompanion\CareCompanion.exe"
exit /b

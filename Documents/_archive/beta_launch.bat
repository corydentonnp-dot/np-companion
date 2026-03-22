@echo off
setlocal enabledelayedexpansion

:: ================================================================
:: CareCompanion — Beta Launch Script
:: ================================================================
:: What this does:
::   1. Kills all running Python / CareCompanion processes
::   2. Waits for port 5000 to be free
::   3. Verifies Python environment
::   4. Starts the Flask server (minimized)
::   5. Launches the desktop exe (falls back to Chrome)
:: ================================================================

set "PROJECT=C:\Users\coryd\Documents\CareCompanion"
set "PYTHON=%PROJECT%\venv\Scripts\python.exe"
set "EXE=%PROJECT%\dist\CareCompanion\CareCompanion.exe"
set "ERRORLOG=%PROJECT%\data\beta_launch_error.txt"

if not exist "%PROJECT%\data" mkdir "%PROJECT%\data"
if exist "%ERRORLOG%" del "%ERRORLOG%"

cd /d "%PROJECT%"

echo.
echo ============================================
echo  CareCompanion — Beta Launch
echo ============================================
echo.

:: ------------------------------------------------------------------
:: STEP 1: Kill all Python and CareCompanion processes
:: ------------------------------------------------------------------
echo [1/5] Stopping existing processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
taskkill /F /IM CareCompanion.exe >nul 2>&1
timeout /t 3 /nobreak >nul
echo       Done.

:: ------------------------------------------------------------------
:: STEP 2: Verify port 5000 is free
:: ------------------------------------------------------------------
echo [2/5] Checking port 5000...
set RETRIES=0
:CHECK_PORT
netstat -ano | findstr ":5000 " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    set /a RETRIES+=1
    if !RETRIES! geq 10 (
        echo ERROR: Port 5000 still in use after 10 retries. >> "%ERRORLOG%"
        netstat -ano | findstr ":5000 " >> "%ERRORLOG%"
        goto :ERROR
    )
    echo       Port 5000 still in use, waiting... (attempt !RETRIES!/10^)
    timeout /t 2 /nobreak >nul
    goto :CHECK_PORT
)
echo       Port 5000 is free.

:: ------------------------------------------------------------------
:: STEP 3: Verify Python environment
:: ------------------------------------------------------------------
echo [3/5] Checking Python environment...
if not exist "%PYTHON%" (
    echo ERROR: Python not found at %PYTHON% >> "%ERRORLOG%"
    echo Make sure the virtual environment exists. >> "%ERRORLOG%"
    goto :ERROR
)
echo       Python OK.

:: ------------------------------------------------------------------
:: STEP 4: Start the Flask server (minimized window)
:: ------------------------------------------------------------------
echo [4/5] Starting Flask server...
start /min "CareCompanion Server" "%PYTHON%" launcher.py --mode=server

:: Wait for server to be ready
set RETRIES=0
:WAIT_SERVER
timeout /t 1 /nobreak >nul
"%PYTHON%" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/login')" >nul 2>&1
if %errorlevel% neq 0 (
    set /a RETRIES+=1
    if !RETRIES! geq 20 (
        echo ERROR: Server did not start within 20 seconds. >> "%ERRORLOG%"
        goto :ERROR
    )
    goto :WAIT_SERVER
)
echo       Server is running on port 5000.

:: ------------------------------------------------------------------
:: STEP 5: Launch the desktop exe (or fall back to Chrome)
:: ------------------------------------------------------------------
echo [5/5] Launching CareCompanion...
if exist "%EXE%" (
    start "" "%EXE%"
    echo       Desktop app launched.
) else (
    echo       EXE not found — opening Chrome instead...
    start "" "chrome" "http://127.0.0.1:5000/dashboard"
)

echo.
echo ============================================
echo  CareCompanion is running!
echo  Close this window to keep it running in
echo  the background, or press any key to exit.
echo ============================================
pause >nul
goto :EOF

:: ------------------------------------------------------------------
:: ERROR HANDLER
:: ------------------------------------------------------------------
:ERROR
echo.
echo ============================================
echo  LAUNCH FAILED — see error details below
echo ============================================
type "%ERRORLOG%"
echo.
echo Press any key to close...
pause >nul

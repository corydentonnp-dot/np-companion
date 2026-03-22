@echo off
setlocal enabledelayedexpansion

:: ================================================================
:: CareCompanion — One-Click Launch
:: ================================================================
:: What this does:
::   1. Kills all running Python / CareCompanion processes
::   2. Waits for ports 5000 + 5001 to be free
::   3. Runs the verification test suite
::   4. Git commit + push (if .git exists and there are changes)
::   5. Starts Flask server + background agent
::   6. Launches the desktop exe (falls back to Chrome)
::
:: Usage:
::   Double-click this file, or run from terminal:
::     run.bat              — full sequence (default)
::     run.bat --skip-tests — skip verification tests
::     run.bat --skip-git   — skip git commit/push
::     run.bat --dev        — start in dev mode (hot-reload, no exe)
:: ================================================================

:: Use the folder this bat file lives in — works no matter where project is
set "PROJECT=%~dp0"
:: Remove trailing backslash
if "%PROJECT:~-1%"=="\" set "PROJECT=%PROJECT:~0,-1%"

set "PYTHON=%PROJECT%\venv\Scripts\python.exe"
set "EXE=%PROJECT%\dist\CareCompanion\CareCompanion.exe"
set "ERRORLOG=%PROJECT%\data\launch_error.txt"

:: Parse flags
set SKIP_TESTS=0
set SKIP_GIT=0
set DEV_MODE=0
for %%a in (%*) do (
    if "%%a"=="--skip-tests" set SKIP_TESTS=1
    if "%%a"=="--skip-git" set SKIP_GIT=1
    if "%%a"=="--dev" set DEV_MODE=1
)

:: Ensure data directory exists
if not exist "%PROJECT%\data" mkdir "%PROJECT%\data"
if exist "%ERRORLOG%" del "%ERRORLOG%"

cd /d "%PROJECT%"

echo.
echo ============================================
echo  CareCompanion — One-Click Launch
echo ============================================
echo.

:: ------------------------------------------------------------------
:: STEP 1: Kill all existing processes
:: ------------------------------------------------------------------
echo [1/6] Stopping existing processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
taskkill /F /IM CareCompanion.exe >nul 2>&1
timeout /t 3 /nobreak >nul
echo       Done.

:: ------------------------------------------------------------------
:: STEP 2: Verify ports are free
:: ------------------------------------------------------------------
echo [2/6] Checking ports 5000 + 5001...
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
    echo       Port 5000 still in use, waiting... ^(attempt !RETRIES!/10^)
    timeout /t 2 /nobreak >nul
    goto :CHECK_PORT
)
echo       Ports are free.

:: ------------------------------------------------------------------
:: STEP 3: Verify Python environment
:: ------------------------------------------------------------------
echo [3/6] Checking Python environment...
if not exist "%PYTHON%" (
    echo ERROR: Python not found at %PYTHON% >> "%ERRORLOG%"
    echo Make sure the virtual environment exists: >> "%ERRORLOG%"
    echo   python -m venv venv >> "%ERRORLOG%"
    goto :ERROR
)
echo       Python OK.

:: ------------------------------------------------------------------
:: STEP 4: Run verification tests (unless --skip-tests)
:: ------------------------------------------------------------------
if %SKIP_TESTS%==1 (
    echo [4/6] Skipping tests ^(--skip-tests flag^)
) else (
    echo [4/6] Running verification tests...
    echo.
    "%PYTHON%" tests\test_verification.py
    set TEST_EXIT=!errorlevel!

    if !TEST_EXIT! neq 0 (
        echo. >> "%ERRORLOG%"
        echo ============================================ >> "%ERRORLOG%"
        echo  TEST FAILURE — %date% %time% >> "%ERRORLOG%"
        echo ============================================ >> "%ERRORLOG%"
        echo test_verification.py exited with code !TEST_EXIT! >> "%ERRORLOG%"
        "%PYTHON%" tests\test_verification.py >> "%ERRORLOG%" 2>&1
        goto :ERROR
    )
    echo.
    echo       All tests passed!
)

:: ------------------------------------------------------------------
:: STEP 5: Git commit + push (unless --skip-git or no .git)
:: ------------------------------------------------------------------
if %SKIP_GIT%==1 (
    echo [5/6] Skipping git ^(--skip-git flag^)
) else if not exist "%PROJECT%\.git" (
    echo [5/6] Skipping git ^(no .git repository found^)
    echo       Run 'git init' to enable auto-commit on launch.
) else (
    echo [5/6] Git commit + push...

    :: Check if there are any changes to commit
    git status --porcelain 2>nul | findstr /r /c:"." >nul 2>&1
    if !errorlevel!==0 (
        git add -A
        git commit -m "Auto-commit before launch — %date% %time%"
        if !errorlevel! neq 0 (
            echo       Warning: git commit failed, continuing anyway...
        ) else (
            echo       Committed changes.
        )
    ) else (
        echo       No changes to commit.
    )

    :: Push if remote exists
    git remote 2>nul | findstr /r /c:"." >nul 2>&1
    if !errorlevel!==0 (
        git push 2>nul
        if !errorlevel!==0 (
            echo       Pushed to remote.
        ) else (
            echo       Warning: git push failed ^(offline or auth issue^), continuing...
        )
    ) else (
        echo       No remote configured, skipping push.
    )
)

:: ------------------------------------------------------------------
:: STEP 6: Start server + launch app
:: ------------------------------------------------------------------
if %DEV_MODE%==1 (
    echo [6/6] Starting dev server ^(hot-reload^)...
    start /d "%PROJECT%" "CareCompanion Server" "%PYTHON%" launcher.py --mode=dev
) else (
    echo [6/6] Starting server + agent...
    start /min /d "%PROJECT%" "CareCompanion Server" "%PYTHON%" launcher.py --mode=server
)

:: Wait for server to be ready
echo       Waiting for server...
set RETRIES=0
:WAIT_SERVER
timeout /t 1 /nobreak >nul
"%PYTHON%" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/login', timeout=3)" >nul 2>&1
if %errorlevel% neq 0 (
    set /a RETRIES+=1
    if !RETRIES! geq 20 (
        echo ERROR: Server did not start within 20 seconds. >> "%ERRORLOG%"
        goto :ERROR
    )
    goto :WAIT_SERVER
)
echo       Server is running on port 5000.

:: Launch app
if %DEV_MODE%==1 (
    echo       Opening Chrome...
    start "" "chrome" "http://127.0.0.1:5000/dashboard"
) else if exist "%EXE%" (
    echo       Launching desktop app...
    start "" "%EXE%"
) else (
    echo       EXE not found — opening Chrome instead...
    start "" "chrome" "http://127.0.0.1:5000/dashboard"
)

echo.
echo ============================================
echo  CareCompanion is running!
echo  Dashboard: http://127.0.0.1:5000/dashboard
echo ============================================
echo.
echo Flags:  --skip-tests  --skip-git  --dev
echo.
echo Press any key to close this window.
echo (The server keeps running in the background)
pause >nul
goto :EOF

:: ------------------------------------------------------------------
:: ERROR HANDLER
:: ------------------------------------------------------------------
:ERROR
echo.
echo ============================================
echo  LAUNCH FAILED
echo ============================================
echo.
if exist "%ERRORLOG%" (
    type "%ERRORLOG%"
    echo.
    echo Error log saved to: %ERRORLOG%
)
echo.
echo Press any key to close...
pause >nul

@echo off
setlocal enabledelayedexpansion

:: ================================================================
:: NP Companion — Full Restart Script
:: ================================================================
:: What this does:
::   1. Kills ALL running Python processes (servers, scripts, etc.)
::   2. Waits for port 5000 to be free
::   3. Runs the verification test suite (test.py)
::   4. If tests pass, starts the Flask server
::   5. Opens Chrome to the dashboard
::   6. If anything fails, writes errors to data\restart_error.txt
::       and opens it in Notepad
:: ================================================================

set "PROJECT=C:\Users\coryd\Documents\NP_Companion"
set "PYTHON=%PROJECT%\venv\Scripts\python.exe"
set "ERRORLOG=%PROJECT%\data\restart_error.txt"

:: Ensure data directory exists
if not exist "%PROJECT%\data" mkdir "%PROJECT%\data"

:: Clear old error log
if exist "%ERRORLOG%" del "%ERRORLOG%"

cd /d "%PROJECT%"

echo.
echo ============================================
echo  NP Companion — Full Restart
echo ============================================
echo.

:: ------------------------------------------------------------------
:: STEP 1: Kill all Python processes
:: ------------------------------------------------------------------
echo [1/5] Killing all Python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
:: Give processes time to fully terminate
timeout /t 3 /nobreak >nul
echo       Done.

:: ------------------------------------------------------------------
:: STEP 2: Verify port 5000 is free
:: ------------------------------------------------------------------
echo [2/5] Checking port 5000 is free...
set RETRIES=0
:CHECK_PORT
netstat -ano | findstr ":5000 " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    set /a RETRIES+=1
    if !RETRIES! geq 10 (
        echo ERROR: Port 5000 still in use after 10 retries. >> "%ERRORLOG%"
        echo.       >> "%ERRORLOG%"
        echo Processes still using port 5000: >> "%ERRORLOG%"
        netstat -ano | findstr ":5000 " >> "%ERRORLOG%"
        goto :ERROR
    )
    echo       Port 5000 still in use, waiting... (attempt !RETRIES!/10)
    timeout /t 2 /nobreak >nul
    goto :CHECK_PORT
)
echo       Port 5000 is free.

:: ------------------------------------------------------------------
:: STEP 3: Verify Python and venv exist
:: ------------------------------------------------------------------
echo [3/5] Checking Python environment...
if not exist "%PYTHON%" (
    echo ERROR: Python not found at %PYTHON% >> "%ERRORLOG%"
    echo.       >> "%ERRORLOG%"
    echo Make sure the virtual environment exists: >> "%ERRORLOG%"
    echo   python -m venv venv >> "%ERRORLOG%"
    goto :ERROR
)
echo       Python OK.

:: ------------------------------------------------------------------
:: STEP 4: Run verification tests
:: ------------------------------------------------------------------
echo [4/5] Running verification tests...
echo.
"%PYTHON%" test.py
set TEST_EXIT=%errorlevel%

if %TEST_EXIT% neq 0 (
    echo. >> "%ERRORLOG%"
    echo ============================================ >> "%ERRORLOG%"
    echo  TEST FAILURE — %date% %time% >> "%ERRORLOG%"
    echo ============================================ >> "%ERRORLOG%"
    echo. >> "%ERRORLOG%"
    echo test.py exited with code %TEST_EXIT% >> "%ERRORLOG%"
    echo. >> "%ERRORLOG%"
    echo Full test output: >> "%ERRORLOG%"
    echo. >> "%ERRORLOG%"
    "%PYTHON%" test.py >> "%ERRORLOG%" 2>&1
    goto :ERROR
)
echo.
echo       All tests passed!

:: ------------------------------------------------------------------
:: STEP 5: Start the Flask server and open Chrome
:: ------------------------------------------------------------------
echo [5/5] Starting Flask server...
start "NP Companion Server" "%PYTHON%" launcher.py --mode=dev

:: Wait for server to be ready
echo       Waiting for server to start...
set RETRIES=0
:WAIT_SERVER
timeout /t 1 /nobreak >nul
"%PYTHON%" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/login')" >nul 2>&1
if %errorlevel% neq 0 (
    set /a RETRIES+=1
    if !RETRIES! geq 15 (
        echo ERROR: Server did not start within 15 seconds. >> "%ERRORLOG%"
        goto :ERROR
    )
    goto :WAIT_SERVER
)

echo       Server is running!
echo.

:: Open Chrome to the dashboard
echo Opening Chrome to dashboard...
start "" "chrome" "http://127.0.0.1:5000/dashboard"

echo.
echo ============================================
echo  NP Companion is running!
echo  Dashboard: http://127.0.0.1:5000/dashboard
echo ============================================
echo.
echo Press any key to close this window...
echo (The server will keep running in its own window)
pause >nul
goto :END

:: ------------------------------------------------------------------
:: ERROR HANDLER
:: ------------------------------------------------------------------
:ERROR
echo.
echo ============================================
echo  STARTUP FAILED — see error log
echo ============================================
echo.
echo Error log: %ERRORLOG%
start "" notepad "%ERRORLOG%"
echo.
echo Press any key to close...
pause >nul

:END
endlocal

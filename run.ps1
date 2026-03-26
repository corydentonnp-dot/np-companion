# ================================================================
# CareCompanion -- One-Click Launch (PowerShell)
# ================================================================
# What this does:
#   1. Kills running Python / CareCompanion processes (only if found)
#   2. Waits for ports 5000 + 5001 to be free
#   3. Starts Flask dev server via launcher.py
#   4. Opens Chrome to the dashboard
#   5. Optionally starts the process watchdog (--watch-processes)
#
# Tests and git are SKIPPED by default for fast launch.
# Opt in with --with-tests / --with-git when needed.
#
# Usage:
#   .\run.ps1                        -- fast launch (no tests, no git)
#   .\run.ps1 --with-tests           -- run verification tests first
#   .\run.ps1 --with-git             -- git commit+push first
#   .\run.ps1 --watch-processes      -- start process watchdog alongside server
#   .\run.ps1 --cleanup-only         -- kill orphans and exit (no server)
#   .\run.ps1 --with-tests --with-git -- full sequence
# ================================================================

param(
    [switch]$WithTests,
    [switch]$WithGit,
    [switch]$WatchProcesses,
    [switch]$CleanupOnly,
    # Legacy flags still accepted (no-ops now, tests/git skip by default)
    [switch]$SkipTests,
    [switch]$SkipGit
)

# Accept raw args passed from run.bat or command line
foreach ($a in $args) {
    if ($a -eq '--with-tests')       { $WithTests       = $true }
    if ($a -eq '--with-git')         { $WithGit          = $true }
    if ($a -eq '--watch-processes')   { $WatchProcesses  = $true }
    if ($a -eq '--cleanup-only')     { $CleanupOnly      = $true }
}

# Keep default ErrorActionPreference (Continue) -- a launcher must be resilient

# -- Paths ---------------------------------------------------------
$Project  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python   = Join-Path $Project 'venv\Scripts\python.exe'
$ErrorLog = Join-Path $Project 'data\launch_error.txt'

Set-Location $Project

# Ensure data directory exists
if (-not (Test-Path (Join-Path $Project 'data'))) {
    New-Item -ItemType Directory -Path (Join-Path $Project 'data') | Out-Null
}
if (Test-Path $ErrorLog) { Remove-Item $ErrorLog -Force }

# -- Helper: write to error log and exit --------------------------
function Fail($msg) {
    $msg | Out-File -FilePath $ErrorLog -Encoding utf8 -Append
    Write-Host ''
    Write-Host '============================================'
    Write-Host '  LAUNCH FAILED'
    Write-Host '============================================'
    Write-Host ''
    Write-Host $msg
    Write-Host ''
    Write-Host "Error log: $ErrorLog"
    exit 1
}

Write-Host ''
Write-Host '============================================'
Write-Host '  CareCompanion -- One-Click Launch'
Write-Host '============================================'
Write-Host ''

# ==================================================================
# STEP 1: Stop existing processes (only if running)
# ==================================================================
Write-Host '[1/6] Stopping existing processes...'
$killed = $false

foreach ($name in @('python', 'pythonw', 'CareCompanion')) {
    $procs = Get-Process -Name $name -ErrorAction SilentlyContinue
    if ($procs) {
        $count = @($procs).Count
        Write-Host "       Killing $name ($count)..."
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
        $killed = $true
    }
}

if ($killed) {
    # Brief wait for OS to release handles / ports
    Start-Sleep -Seconds 1
    Write-Host '       Processes stopped.'
} else {
    Write-Host '       No existing processes found.'
}

# -- Run process report (shows origin of any remaining Python processes) --
$guardScript = Join-Path $Project 'tools\process_guard.py'
if (Test-Path $guardScript) {
    Write-Host '       Running process audit...'
    $guardProc = Start-Process -FilePath $Python `
                               -ArgumentList $guardScript `
                               -WorkingDirectory $Project `
                               -NoNewWindow -PassThru -Wait:$false
    $guardFinished = $guardProc.WaitForExit(15000)
    if (-not $guardFinished) {
        $guardProc | Stop-Process -Force -ErrorAction SilentlyContinue
    }
}

# -- Cleanup-only mode: kill orphans and exit --------------------------
if ($CleanupOnly) {
    Write-Host ''
    Write-Host '  Cleanup-only mode -- killing orphans and exiting.'
    if (Test-Path $guardScript) {
        $killProc = Start-Process -FilePath $Python `
                                  -ArgumentList "$guardScript", '--kill-all' `
                                  -WorkingDirectory $Project `
                                  -NoNewWindow -PassThru -Wait:$false
        $killFinished = $killProc.WaitForExit(30000)
        if (-not $killFinished) {
            $killProc | Stop-Process -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host '  Done.'
    exit 0
}

# ==================================================================
# STEP 2: Verify ports are free
# ==================================================================
Write-Host '[2/6] Checking ports 5000 + 5001...'

for ($i = 1; $i -le 10; $i++) {
    # Use netstat instead of Get-NetTCPConnection -- it never throws and works on all PS versions
    $busy = netstat -ano 2>$null | Select-String ':5000\s.*LISTENING'
    if (-not $busy) { break }

    if ($i -eq 10) {
        Fail 'Port 5000 still in use after 10 retries. Run: Get-Process python | Stop-Process -Force'
    }
    Write-Host "       Port 5000 still in use, waiting... (attempt $i/10)"
    Start-Sleep -Seconds 2
}
Write-Host '       Ports are free.'

# ==================================================================
# STEP 3: Verify Python environment
# ==================================================================
Write-Host '[3/6] Checking Python environment...'
if (-not (Test-Path $Python)) {
    Fail "Python not found at $Python. Run: python -m venv venv"
}
Write-Host '       Python OK.'

# ==================================================================
# STEP 4: Run verification tests (with 120s timeout)
# ==================================================================
if ($WithTests) {
    Write-Host '[4/6] Running verification tests...'
    Write-Host ''

    $testScript = Join-Path $Project 'tests\test_verification.py'
    $proc = Start-Process -FilePath $Python `
                          -ArgumentList $testScript `
                          -WorkingDirectory $Project `
                          -NoNewWindow -PassThru -Wait:$false

    # Wait up to 120 seconds for tests to finish
    $finished = $proc.WaitForExit(120000)

    if (-not $finished) {
        # Test hung -- kill it and fail
        $proc | Stop-Process -Force -ErrorAction SilentlyContinue
        Fail 'Verification tests timed out after 120 seconds.'
    }

    if ($proc.ExitCode -ne 0) {
        Fail "Verification tests failed with exit code $($proc.ExitCode)."
    }
    Write-Host ''
    Write-Host '       All tests passed!'
} else {
    Write-Host '[4/6] Skipping tests (use --with-tests to run)'
}

# ==================================================================
# STEP 5: Git commit + push
# ==================================================================
if (-not $WithGit) {
    Write-Host '[5/6] Skipping git (use --with-git to run)'
} elseif (-not (Test-Path (Join-Path $Project '.git'))) {
    Write-Host '[5/6] Skipping git (no .git repository found)'
} else {
    Write-Host '[5/6] Git commit + push...'

    $status = & git status --porcelain 2>$null
    if ($status) {
        & git add -A
        $commitResult = & git commit -m "Auto-commit before launch -- $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" 2>&1
        $null = $commitResult  # capture output
        if ($LASTEXITCODE -eq 0) {
            Write-Host '       Committed changes.'
        } else {
            Write-Host '       Warning: git commit failed, continuing...'
        }
    } else {
        Write-Host '       No changes to commit.'
    }

    $remotes = & git remote 2>$null
    if ($remotes) {
        & git push 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host '       Pushed to remote.'
        } else {
            Write-Host '       Warning: git push failed (offline or auth), continuing...'
        }
    } else {
        Write-Host '       No remote configured, skipping push.'
    }
}

# ==================================================================
# STEP 6: Start server + launch Chrome
# ==================================================================
Write-Host '[6/6] Starting dev server (hot-reload)...'

$null = Start-Process -FilePath $Python `
                            -ArgumentList 'launcher.py', '--mode=dev' `
                            -WorkingDirectory $Project `
                            -PassThru

Write-Host '       Waiting for server on port 5000...'

$ready = $false
for ($i = 1; $i -le 15; $i++) {
    Start-Sleep -Seconds 2
    $listening = netstat -ano 2>$null | Select-String ':5000\s.*LISTENING'
    if ($listening) {
        $ready = $true
        break
    }
    Write-Host "       Still waiting... ($i/15)"
}

if ($ready) {
    Write-Host '       Server is running on port 5000.'
} else {
    Write-Host '       Server did not bind within 30s -- launching Chrome anyway.'
}

# Open default browser
Write-Host '       Opening browser...'
Start-Process 'http://127.0.0.1:5000/dashboard'

Write-Host ''
Write-Host '============================================'
Write-Host '  CareCompanion is running!'
Write-Host '  Dashboard: http://127.0.0.1:5000/dashboard'
Write-Host '============================================'
Write-Host ''

# ==================================================================
# STEP 7 (optional): Start process watchdog
# ==================================================================
if ($WatchProcesses) {
    $guardScript = Join-Path $Project 'tools\process_guard.py'
    if (Test-Path $guardScript) {
        Write-Host '[7/7] Starting process watchdog (--watch --auto-kill)...'
        Write-Host '       Logs to data/logs/python_process_log_*.csv'
        Write-Host '       Alerts at 95% CPU, auto-kills after 3 min sustained.'
        Write-Host ''
        # Run watchdog in foreground -- it blocks until Ctrl+C
        $watchProc = Start-Process -FilePath $Python `
                                   -ArgumentList "$guardScript", '--watch', '--auto-kill' `
                                   -WorkingDirectory $Project `
                                   -NoNewWindow -PassThru
        # Store PID for potential cleanup
        Write-Host "       Watchdog PID: $($watchProc.Id)"
    } else {
        Write-Host '[7/7] Watchdog script not found -- skipping'
    }
} else {
    Write-Host 'Tip: use --watch-processes to start the process watchdog'
}

Write-Host ''
Write-Host 'Flags:  --with-tests  --with-git  --watch-processes  --cleanup-only'
Write-Host ''
Write-Host '(The server keeps running in the background)'
exit 0

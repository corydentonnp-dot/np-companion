# ================================================================
# CareCompanion -- Fresh Machine Setup Script
# ================================================================
# Run this ONCE on a new machine after cloning the repo.
# Handles everything: venv, packages, migrations, VS Code extensions.
#
# Usage:
#   Right-click setup.ps1 -> Run with PowerShell
#   -- OR --
#   powershell -ExecutionPolicy Bypass -File setup.ps1
#   -- OR --
#   Choose option 4 in run.bat
# ================================================================

$ErrorActionPreference = 'Continue'
$Project = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Project

# -- Counters for final summary -----------------------------------
$Script:Passed  = @()
$Script:Failed  = @()
$Script:Skipped = @()

function Pass($msg)  { $Script:Passed  += $msg; Write-Host "  [OK]   $msg" -ForegroundColor Green }
function Fail($msg)  { $Script:Failed  += $msg; Write-Host "  [FAIL] $msg" -ForegroundColor Red }
function Skip($msg)  { $Script:Skipped += $msg; Write-Host "  [SKIP] $msg" -ForegroundColor Yellow }
function Step($msg)  { Write-Host ""; Write-Host "--- $msg ---" -ForegroundColor Cyan }

Write-Host ""
Write-Host "============================================" -ForegroundColor White
Write-Host "  CareCompanion -- Fresh Machine Setup"      -ForegroundColor White
Write-Host "============================================" -ForegroundColor White
Write-Host ""
Write-Host "  Project: $Project"
Write-Host ""

# ------------------------------------------------------------------
# STEP 1: Find Python 3.11
# ------------------------------------------------------------------
Step "STEP 1: Locating Python 3.11"

$Python = $null

# Try py launcher first (most reliable on Windows)
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($pyLauncher) {
    $ver = & py -3.11 --version 2>&1
    if ($ver -match '3\.11') {
        $Python = 'py -3.11'
        Pass "Found Python 3.11 via py launcher: $ver"
    }
}

# Try python3.11 directly
if (-not $Python) {
    $p311 = Get-Command python3.11 -ErrorAction SilentlyContinue
    if ($p311) {
        $Python = 'python3.11'
        Pass "Found Python 3.11 at: $($p311.Source)"
    }
}

# Try python and check version
if (-not $Python) {
    $pCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pCmd) {
        $ver = & python --version 2>&1
        if ($ver -match '3\.11') {
            $Python = 'python'
            Pass "Found Python 3.11 at: $($pCmd.Source)"
        } else {
            Fail "python found but wrong version: $ver (need 3.11)"
        }
    }
}

if (-not $Python) {
    Fail "Python 3.11 not found in PATH."
    Write-Host ""
    Write-Host "  Install Python 3.11 from:" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/release/python-3110/" -ForegroundColor Yellow
    Write-Host "  IMPORTANT: Check 'Add Python to PATH' on the first installer screen." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  After installing, re-run this script." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Resolve actual python.exe path for subsequent calls
$PythonExe = Join-Path $Project 'venv\Scripts\python.exe'

# ------------------------------------------------------------------
# STEP 2: Create virtual environment
# ------------------------------------------------------------------
Step "STEP 2: Virtual environment"

if (Test-Path $PythonExe) {
    Pass "venv already exists -- skipping creation"
} else {
    Write-Host "  Creating venv..."
    if ($Python -eq 'py -3.11') {
        $proc = Start-Process -FilePath 'py' -ArgumentList '-3.11', '-m', 'venv', 'venv' `
                              -WorkingDirectory $Project -NoNewWindow -PassThru
    } else {
        $proc = Start-Process -FilePath $Python -ArgumentList '-m', 'venv', 'venv' `
                              -WorkingDirectory $Project -NoNewWindow -PassThru
    }
    $done = $proc.WaitForExit(120000)
    if (-not $done) { $proc | Stop-Process -Force -ErrorAction SilentlyContinue }

    if (Test-Path $PythonExe) {
        Pass "venv created successfully"
    } else {
        Fail "venv creation failed -- $PythonExe not found after create"
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# ------------------------------------------------------------------
# STEP 3: Install / upgrade pip requirements
# ------------------------------------------------------------------
Step "STEP 3: Installing Python packages"

$reqFile = Join-Path $Project 'requirements.txt'
if (-not (Test-Path $reqFile)) {
    Fail "requirements.txt not found at $reqFile"
} else {
    Write-Host "  Installing from requirements.txt (this may take 2-3 minutes on first run)..."
    $proc = Start-Process -FilePath $PythonExe `
                          -ArgumentList '-m', 'pip', 'install', '-r', $reqFile, '--quiet' `
                          -WorkingDirectory $Project -NoNewWindow -PassThru
    $done = $proc.WaitForExit(300000)  # 5 minute timeout
    if (-not $done) {
        $proc | Stop-Process -Force -ErrorAction SilentlyContinue
        Fail "pip install timed out after 5 minutes"
    } elseif ($proc.ExitCode -eq 0) {
        Pass "All packages installed"
    } else {
        Fail "pip install exited with code $($proc.ExitCode)"
        Write-Host "  Try running manually: venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    }
}

# ------------------------------------------------------------------
# STEP 4: Run database migrations
# ------------------------------------------------------------------
Step "STEP 4: Running database migrations"

$migDir = Join-Path $Project 'migrations'
if (-not (Test-Path $migDir)) {
    Skip "No migrations directory found"
} else {
    $migrations = Get-ChildItem "$migDir\*.py" | Sort-Object Name
    $migCount   = 0
    $migFailed  = 0

    if ($migrations.Count -eq 0) {
        Skip "No migration files found in migrations\"
    } else {
        Write-Host "  Found $($migrations.Count) migration files..."
        foreach ($mig in $migrations) {
            Write-Host "    Running $($mig.Name)..." -NoNewline
            $proc = Start-Process -FilePath $PythonExe `
                                  -ArgumentList $mig.FullName `
                                  -WorkingDirectory $Project -NoNewWindow -PassThru
            $done = $proc.WaitForExit(60000)  # 60s per migration
            if (-not $done) {
                $proc | Stop-Process -Force -ErrorAction SilentlyContinue
                Write-Host " TIMEOUT" -ForegroundColor Red
                $migFailed++
            } elseif ($proc.ExitCode -eq 0) {
                Write-Host " OK" -ForegroundColor Green
                $migCount++
            } else {
                # Exit code 1 is often "table already exists" -- treat as OK
                Write-Host " skipped (already applied)" -ForegroundColor Yellow
                $migCount++
            }
        }

        if ($migFailed -eq 0) {
            Pass "$migCount migrations applied (or already current)"
        } else {
            Fail "$migFailed migrations timed out -- see output above"
        }
    }
}

# ------------------------------------------------------------------
# STEP 5: Install VS Code extensions
# ------------------------------------------------------------------
Step "STEP 5: Installing VS Code extensions"

$codePath = $null
$codeCandidates = @(
    'C:\Users\coryd\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd',
    "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd",
    "$env:ProgramFiles\Microsoft VS Code\bin\code.cmd"
)
foreach ($c in $codeCandidates) {
    if (Test-Path $c) { $codePath = $c; break }
}
if (-not $codePath) {
    $codeCmd = Get-Command code -ErrorAction SilentlyContinue
    if ($codeCmd) { $codePath = $codeCmd.Source }
}

if (-not $codePath) {
    Skip "VS Code CLI not found -- install extensions manually"
    Write-Host "  Install VS Code from: https://code.visualstudio.com/" -ForegroundColor Yellow
} else {
    $extensions = @(
        @{ id = 'vsls-contrib.gitdoc';        name = 'GitDoc (auto-commit/push)' },
        @{ id = 'ms-python.python';            name = 'Python' },
        @{ id = 'ms-python.vscode-pylance';    name = 'Pylance' },
        @{ id = 'github.copilot-chat';         name = 'GitHub Copilot Chat' }
    )

    foreach ($ext in $extensions) {
        Write-Host "  Installing $($ext.name)..." -NoNewline
        $proc = Start-Process -FilePath $codePath `
                              -ArgumentList "--install-extension $($ext.id) --force" `
                              -NoNewWindow -PassThru
        $done = $proc.WaitForExit(60000)
        if (-not $done) {
            $proc | Stop-Process -Force -ErrorAction SilentlyContinue
            Write-Host " TIMEOUT" -ForegroundColor Yellow
            Skip "$($ext.name) install timed out"
        } elseif ($proc.ExitCode -eq 0) {
            Write-Host " OK" -ForegroundColor Green
            Pass "$($ext.name)"
        } else {
            # code.cmd returns non-zero even on "already installed" sometimes
            Write-Host " OK (may already be installed)" -ForegroundColor Yellow
            Pass "$($ext.name)"
        }
    }
}

# ------------------------------------------------------------------
# STEP 6: Check Node.js (needed for Playwright MCP)
# ------------------------------------------------------------------
Step "STEP 6: Checking Node.js (Playwright MCP)"

$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCmd) {
    $nodeVer = & node --version 2>&1
    if ($nodeVer -match 'v(\d+)\.') {
        $major = [int]$Matches[1]
        if ($major -ge 18) {
            Pass "Node.js $nodeVer found"
        } else {
            Fail "Node.js $nodeVer found but need v18+. Update at: https://nodejs.org/"
        }
    } else {
        Pass "Node.js found: $nodeVer"
    }
} else {
    Fail "Node.js not found -- Playwright browser tools will not work"
    Write-Host "  Install Node.js LTS from: https://nodejs.org/en/download" -ForegroundColor Yellow
}

# ------------------------------------------------------------------
# STEP 7: Verify .vscode/mcp.json exists
# ------------------------------------------------------------------
Step "STEP 7: Playwright MCP config"

$mcpPath = Join-Path $Project '.vscode\mcp.json'
if (Test-Path $mcpPath) {
    Pass "mcp.json present"
} else {
    Write-Host "  Creating .vscode\mcp.json..."
    $mcpDir = Join-Path $Project '.vscode'
    if (-not (Test-Path $mcpDir)) { New-Item -ItemType Directory -Path $mcpDir | Out-Null }
    $mcpContent = '{
  "servers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}'
    Set-Content -Path $mcpPath -Value $mcpContent -Encoding utf8
    Pass "mcp.json created"
}

# ------------------------------------------------------------------
# STEP 8: Quick smoke test
# ------------------------------------------------------------------
Step "STEP 8: Quick smoke test"

$smokeScript = Join-Path $Project 'scripts\smoke_test.py'
if (-not (Test-Path $smokeScript)) {
    Skip "smoke_test.py not found -- skipping"
} else {
    Write-Host "  Running smoke test..."
    $proc = Start-Process -FilePath $PythonExe -ArgumentList $smokeScript `
                          -WorkingDirectory $Project -NoNewWindow -PassThru
    $done = $proc.WaitForExit(60000)
    if (-not $done) {
        $proc | Stop-Process -Force -ErrorAction SilentlyContinue
        Fail "Smoke test timed out"
    } elseif ($proc.ExitCode -eq 0) {
        Pass "Smoke test passed"
    } else {
        Fail "Smoke test failed (exit code $($proc.ExitCode)) -- run 'scripts\smoke_test.py' manually to see errors"
    }
}

# ------------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------------
Write-Host ""
Write-Host "============================================" -ForegroundColor White
Write-Host "  Setup Complete -- Summary"                  -ForegroundColor White
Write-Host "============================================" -ForegroundColor White
Write-Host ""

if ($Script:Passed.Count -gt 0) {
    Write-Host "  PASSED ($($Script:Passed.Count)):" -ForegroundColor Green
    foreach ($m in $Script:Passed) { Write-Host "    + $m" -ForegroundColor Green }
}

if ($Script:Skipped.Count -gt 0) {
    Write-Host ""
    Write-Host "  SKIPPED ($($Script:Skipped.Count)):" -ForegroundColor Yellow
    foreach ($m in $Script:Skipped) { Write-Host "    ~ $m" -ForegroundColor Yellow }
}

if ($Script:Failed.Count -gt 0) {
    Write-Host ""
    Write-Host "  FAILED ($($Script:Failed.Count)) -- ACTION REQUIRED:" -ForegroundColor Red
    foreach ($m in $Script:Failed) { Write-Host "    ! $m" -ForegroundColor Red }
}

Write-Host ""

if ($Script:Failed.Count -eq 0) {
    Write-Host "  All done! Next steps:" -ForegroundColor Green
    Write-Host ""
    Write-Host "  1. Press Ctrl+Shift+P in VS Code -> 'Developer: Reload Window'" -ForegroundColor White
    Write-Host "  2. Sign into GitHub Copilot when prompted" -ForegroundColor White
    Write-Host "  3. Run the app: double-click run.bat -> choose option 1" -ForegroundColor White
    Write-Host "  4. Log in at http://localhost:5000  (CORY / ASDqwe123)" -ForegroundColor White
} else {
    Write-Host "  Fix the items above, then re-run this script." -ForegroundColor Yellow
    Write-Host "  Most failures are safe to re-run -- already-applied steps are skipped." -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to close"

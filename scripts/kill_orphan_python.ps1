# Find PIDs listening on port 5000 (the Flask server) - keep these
$keepPids = @()
try {
    $keepPids = (Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue |
                 Where-Object { $_.State -eq 'Listen' -or $_.State -eq 'Established' }).OwningProcess |
                Where-Object { $_ -gt 0 }
} catch {}
# Get all python processes NOT in the keep list
$all = Get-Process python -ErrorAction SilentlyContinue
$toKill = $all | Where-Object { $_.Id -notin $keepPids }
if (-not $toKill) {
    Write-Host "No orphaned Python processes found."
} else {
    Write-Host "Keeping PIDs on port 5000: $($keepPids -join ', ')"
    Write-Host "Killing $($toKill.Count) orphaned Python process(es)..."
    $toKill | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "Done. Remaining: $((Get-Process python -ErrorAction SilentlyContinue).Count)"
}
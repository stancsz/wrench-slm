# Stop Wrench Sidecar daemon natively on Windows
$Root = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $Root "data\sidecar.pid"

if (Test-Path $PidFile) {
    $PidVal = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($PidVal) {
        Write-Host "Stopping Wrench Sidecar (PID: $PidVal)..." -ForegroundColor Yellow
        Stop-Process -Id $PidVal -Force -ErrorAction SilentlyContinue
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Wrench Sidecar stopped." -ForegroundColor Green
        exit 0
    }
}

Write-Host "No active Wrench Sidecar PID file found." -ForegroundColor Gray

# Start Wrench Sidecar daemon natively on Windows
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "[ERROR] .venv not found at $VenvPython" -ForegroundColor Red
    exit 1
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting Wrench Gateway Sidecar (Pure-Blood Daemon)      " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Model Architecture : 100% Pure-Blood NanoWrench"
Write-Host "Gateway Target     : C:\Users\stanc\github\lean-router\logs"
Write-Host "Canary Port        : http://127.0.0.1:4010"
Write-Host ""

$env:PYTHONUNBUFFERED = "1"
$env:LEAN_ROUTER_LOGS_DIR = "C:\Users\stanc\github\lean-router\logs"

$StdOut = Join-Path $Root "logs\sidecar.stdout.log"
$StdErr = Join-Path $Root "logs\sidecar.stderr.log"

$Process = Start-Process -FilePath $VenvPython `
    -ArgumentList "-u", "-m", "wrench.sidecar" `
    -WorkingDirectory $Root `
    -RedirectStandardOutput $StdOut `
    -RedirectStandardError $StdErr `
    -WindowStyle Hidden `
    -PassThru

$PidFile = Join-Path $Root "data\sidecar.pid"
Set-Content -Path $PidFile -Value $Process.Id -Encoding utf8

Write-Host "[OK] Wrench Sidecar started with PID $($Process.Id)" -ForegroundColor Green
Write-Host "[OK] PID recorded at $PidFile" -ForegroundColor Green
Write-Host "[OK] Health check: curl http://127.0.0.1:4010/health" -ForegroundColor Green

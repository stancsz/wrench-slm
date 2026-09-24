$ErrorActionPreference = 'Stop'
$out = Join-Path (Get-Location).Path 'phases/phase-273-5060ti-current-package-e2e/client-smoke'
$ws = Join-Path $out 'dsh-workspace'
New-Item -ItemType Directory -Force -Path $ws | Out-Null
Copy-Item -LiteralPath (Join-Path (Get-Location).Path 'README.md') -Destination (Join-Path $ws 'README.md') -Force
$pkg = 'C:\Users\stanc\models\wrench-5060-preflight-20260921\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-Experimental-Preview'
$serverOut = Join-Path $out 'dsh-server.stdout.log'
$serverErr = Join-Path $out 'dsh-server.stderr.log'
$trace = Join-Path $out 'dsh.trace.jsonl'
$serverArgs = @((Join-Path $pkg 'wrench_server.py'), '--model-dir', $pkg, '--allowed-root', $ws, '--port', '28943', '--mechanical-only', '--max-request-bytes', '536870912', '--trace-log', $trace)
$server = Start-Process -FilePath (Get-Command python).Source -ArgumentList $serverArgs -WorkingDirectory $pkg -WindowStyle Hidden -RedirectStandardOutput $serverOut -RedirectStandardError $serverErr -PassThru
try {
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:28943/health' -TimeoutSec 2
            if ($health.status -eq 'ok') { $ready = $true; break }
        } catch { }
        Start-Sleep -Milliseconds 250
    }
    if (-not $ready) { throw 'server readiness timeout' }
    Push-Location $ws
    try {
        $env:WRENCH_LOCAL_API_KEY = 'wrench-local'
        & dsh --profile headless --patch (Join-Path (Get-Location).Path '..\..\..\..\phases\phase-273-5060ti-current-package-e2e\dsh-current.patch.yml') 'Read README.md and report its first heading.' 2>&1 | Tee-Object -FilePath (Join-Path $out 'dsh.stdout.txt')
        $exitCode = $LASTEXITCODE
    } finally {
        Pop-Location
        Remove-Item Env:WRENCH_LOCAL_API_KEY -ErrorAction SilentlyContinue
    }
    Write-Output ("DSH_EXIT={0}" -f $exitCode)
    exit $exitCode
} finally {
    if ($server -and -not $server.HasExited) { Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue }
}

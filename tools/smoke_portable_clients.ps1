param(
    [Parameter(Mandatory = $true)]
    [string]$PackageDir,
    [string]$AllowedRoot = (Get-Location).Path,
    [string]$OutputDir = "",
    [int]$Port = 28900
)

$ErrorActionPreference = "Stop"
$package = (Resolve-Path -LiteralPath $PackageDir -ErrorAction Stop).Path
$root = (Resolve-Path -LiteralPath $AllowedRoot -ErrorAction Stop).Path
$python = Get-Command python -ErrorAction Stop
$opencodeCommand = Get-Command opencode.cmd -ErrorAction SilentlyContinue
if (-not $opencodeCommand) { $opencodeCommand = Get-Command opencode -ErrorAction Stop }
$opencode = $opencodeCommand.Source
$dshCommand = Get-Command dsh.cmd -ErrorAction SilentlyContinue
if (-not $dshCommand) { $dshCommand = Get-Command dsh -ErrorAction Stop }
$dsh = $dshCommand.Source
$server = Join-Path $package "wrench_server.py"
$opencodeTemplate = Join-Path $package "opencode.wrench.json"
$dshPatch = Join-Path $package "dsh-wrench.patch.yml"
foreach ($required in @($server, $opencodeTemplate, $dshPatch)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Portable package is missing required client file: $required"
    }
}

if (-not $OutputDir) {
    $OutputDir = Join-Path ([IO.Path]::GetTempPath()) ("wrench-client-smoke-" + [Guid]::NewGuid().ToString("N"))
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$OutputDir = (Resolve-Path -LiteralPath $OutputDir -ErrorAction Stop).Path
$workspace = Join-Path $OutputDir "client-workspace"
New-Item -ItemType Directory -Force -Path $workspace | Out-Null
$opencodeConfigPath = Join-Path $workspace "opencode.json"
Copy-Item -LiteralPath $opencodeTemplate -Destination $opencodeConfigPath
# The portable package intentionally defaults to 28900, but this smoke test
# accepts an alternate port so concurrent runs do not collide. Rewrite only
# the temporary client copies, never the downloaded package.
$opencodeConfig = Get-Content -LiteralPath $opencodeConfigPath -Raw
$opencodeConfig = $opencodeConfig.Replace(
    "http://127.0.0.1:28900/v1",
    ("http://127.0.0.1:{0}/v1" -f $Port)
)
Set-Content -LiteralPath $opencodeConfigPath -Value $opencodeConfig -Encoding utf8
$dshPatchForSmoke = Join-Path $workspace "dsh-wrench.smoke.patch.yml"
$dshPatchText = Get-Content -LiteralPath $dshPatch -Raw
$dshPatchText = $dshPatchText.Replace(
    "http://127.0.0.1:28900/v1",
    ("http://127.0.0.1:{0}/v1" -f $Port)
)
Set-Content -LiteralPath $dshPatchForSmoke -Value $dshPatchText -Encoding utf8
Copy-Item -LiteralPath (Join-Path $root "README.md") -Destination (Join-Path $workspace "README.md")
$trace = Join-Path $OutputDir "wrench-client.trace.jsonl"
$serverOut = Join-Path $OutputDir "server.stdout.log"
$serverErr = Join-Path $OutputDir "server.stderr.log"
$serverArgs = @(
    $server,
    "--model-dir", $package,
    "--allowed-root", $workspace,
    "--port", $Port,
    "--mechanical-only",
    "--max-request-bytes", 536870912,
    "--trace-log", $trace
)
$serverProcess = $null
$opencodeOutput = ""
$dshOutput = ""
$opencodeExit = $null
$dshExit = $null
$opencodeMode = "normal"
$opencodeSupportsPure = $false
$originalKey = $env:WRENCH_LOCAL_API_KEY
$originalDeepSeekKey = $env:DEEPSEEK_API_KEY

try {
    $serverProcess = Start-Process -FilePath $python.Source -ArgumentList $serverArgs `
        -WorkingDirectory $package -WindowStyle Hidden `
        -RedirectStandardOutput $serverOut -RedirectStandardError $serverErr -PassThru
    $ready = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        try {
            $health = Invoke-RestMethod -Method Get -Uri ("http://127.0.0.1:{0}/health" -f $Port) -TimeoutSec 2
            if ($health.status -eq "ok") {
                $ready = $true
                break
            }
        } catch {
            if ($serverProcess.HasExited) {
                throw "Wrench server exited before readiness"
            }
        }
        Start-Sleep -Milliseconds 250
    }
    if (-not $ready) { throw "Wrench server readiness timeout" }

    Push-Location $workspace
    try {
        $clientErrorPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $opencodeHelp = (& $opencode run --help 2>&1 | Out-String)
        $opencodeSupportsPure = $opencodeHelp -match "(?m)--pure\b"
        $opencodeOutput = (& $opencode run -m wrench/wrench-local `
            "Read README.md and report its first heading." 2>&1 | Out-String)
        $opencodeExit = $LASTEXITCODE
        if ($opencodeExit -ne 0 -and $opencodeSupportsPure) {
            $opencodeMode = "pure-fallback"
            $pureOutput = (& $opencode run --pure -m wrench/wrench-local `
                "Read README.md and report its first heading." 2>&1 | Out-String)
            $opencodeOutput = "NORMAL ATTEMPT:`n$opencodeOutput`nPURE FALLBACK:`n$pureOutput"
            $opencodeExit = $LASTEXITCODE
        }

        $env:WRENCH_LOCAL_API_KEY = "wrench-local"
        # Current DSH resolves the deepseek-official route through its
        # credentials service, whose environment discovery uses this name.
        # Keep the package-local variable too for older DSH releases.
        $env:DEEPSEEK_API_KEY = "wrench-local"
        $dshOutput = (& $dsh --profile headless --patch $dshPatchForSmoke `
            "Read README.md and report its first heading." 2>&1 | Out-String)
        $dshExit = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $clientErrorPreference
        Pop-Location
        $env:WRENCH_LOCAL_API_KEY = $originalKey
        $env:DEEPSEEK_API_KEY = $originalDeepSeekKey
    }

    $traceRows = @()
    if (Test-Path -LiteralPath $trace) {
        $traceRows = @(Get-Content -LiteralPath $trace | ForEach-Object { $_ | ConvertFrom-Json })
    }
    $readToolObserved = @(
        $traceRows | Where-Object {
            @($_.tool_names) -contains "read" -or @($_.tool_names) -contains "Read"
        }
    ).Count -gt 0
    $receipt = [ordered]@{
        schema = "wrench.portable-client-smoke.v1"
        status = if ($opencodeExit -eq 0 -and $dshExit -eq 0) { "PASSED" } else { "FAILED" }
        package_dir = $package
        allowed_root = $workspace
        port = $Port
        clients = [ordered]@{
            opencode = [ordered]@{
                exit_code = $opencodeExit
                mode = $opencodeMode
                supports_pure = $opencodeSupportsPure
                structured_read_observed = $readToolObserved
                output_file = "opencode.stdout.txt"
            }
            deepseek_harness = [ordered]@{
                exit_code = $dshExit
                structured_read_observed = $readToolObserved
                output_file = "dsh.stdout.txt"
            }
        }
        trace = [ordered]@{
            rows = $traceRows.Count
            model_calls = @($traceRows | ForEach-Object { $_.model_calls } | Measure-Object -Sum).Sum
            protocols = @($traceRows | ForEach-Object { $_.protocol } | Select-Object -Unique)
            backends = @($traceRows | ForEach-Object { $_.backend } | Select-Object -Unique)
            read_tool_observed = $readToolObserved
            mutation_claim = $false
            path = $trace
        }
        claims_not_authorized = @(
            "independent RTX 5060 Ti verification",
            "learned MiniMax parity",
            "dense-native 4M decoder quality",
            "production readiness"
        )
    }
    $opencodeOutput | Set-Content -LiteralPath (Join-Path $OutputDir "opencode.stdout.txt") -Encoding utf8
    $dshOutput | Set-Content -LiteralPath (Join-Path $OutputDir "dsh.stdout.txt") -Encoding utf8
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputDir "receipt.json") -Encoding utf8
    Write-Output ($receipt | ConvertTo-Json -Depth 8)
    if ($receipt.status -ne "PASSED") { exit 1 }
} finally {
    $env:WRENCH_LOCAL_API_KEY = $originalKey
    $env:DEEPSEEK_API_KEY = $originalDeepSeekKey
    if ($serverProcess -and -not $serverProcess.HasExited) {
        try { Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue } catch { }
    }
}

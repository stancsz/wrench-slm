param(
    [Parameter(Mandatory = $true)]
    [string]$PackageDir,
    [string]$AllowedRoot = (Get-Location).Path,
    [string]$OutputDir = "",
    [int]$Port = 28900,
    [int]$ClaudePort = 28944,
    [int]$ClaudeProxyPort = 28945,
    [string]$ClaudeExecutable = "claude"
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
$claudeCommand = Get-Command ("{0}.cmd" -f $ClaudeExecutable) -ErrorAction SilentlyContinue
if (-not $claudeCommand) { $claudeCommand = Get-Command $ClaudeExecutable -ErrorAction Stop }
$claude = $claudeCommand.Source
$powershell = Get-Command powershell.exe -ErrorAction Stop
$server = Join-Path $package "wrench_server.py"
$opencodeTemplate = Join-Path $package "opencode.wrench.json"
$dshPatch = Join-Path $package "dsh-wrench.patch.yml"
$claudeLauncher = Join-Path $package "run_claude_code.ps1"
foreach ($required in @($server, $opencodeTemplate, $dshPatch)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Portable package is missing required client file: $required"
    }
}
if (-not (Test-Path -LiteralPath $claudeLauncher -PathType Leaf)) {
    throw "Portable package is missing required Claude Code launcher: $claudeLauncher"
}
if ($Port -eq $ClaudePort -or $Port -eq $ClaudeProxyPort -or $ClaudePort -eq $ClaudeProxyPort) {
    throw "Client and Claude proxy ports must be distinct"
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
$claudeTrace = Join-Path $OutputDir "wrench-claude.trace.jsonl"
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
$claudeOutput = ""
$opencodeExit = $null
$dshExit = $null
$claudeExit = $null
$opencodeMode = "normal"
$opencodeSupportsPure = $false
$originalKey = $env:WRENCH_LOCAL_API_KEY
$originalDeepSeekKey = $env:DEEPSEEK_API_KEY
$originalHome = $env:HOME
$originalUserProfile = $env:USERPROFILE
$originalXdgConfigHome = $env:XDG_CONFIG_HOME
$originalXdgCacheHome = $env:XDG_CACHE_HOME
$originalXdgDataHome = $env:XDG_DATA_HOME
$originalXdgStateHome = $env:XDG_STATE_HOME
$originalXdgRuntimeDir = $env:XDG_RUNTIME_DIR

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
        # DSH can keep a background profile or credential snapshot alive.
        # Give this smoke a disposable home so a previous provider session
        # cannot decide the route or credential state for this run.
        $dshHome = Join-Path $OutputDir "dsh-isolated"
        $dshConfigHome = Join-Path $dshHome "config"
        $dshCacheHome = Join-Path $dshHome "cache"
        $dshDataHome = Join-Path $dshHome "data"
        $dshStateHome = Join-Path $dshHome "state"
        $dshRuntimeHome = Join-Path $dshHome "runtime"
        foreach ($dshDirectory in @(
            $dshHome,
            $dshConfigHome,
            $dshCacheHome,
            $dshDataHome,
            $dshStateHome,
            $dshRuntimeHome
        )) {
            New-Item -ItemType Directory -Force -Path $dshDirectory | Out-Null
        }
        $env:HOME = $dshHome
        $env:USERPROFILE = $dshHome
        $env:XDG_CONFIG_HOME = $dshConfigHome
        $env:XDG_CACHE_HOME = $dshCacheHome
        $env:XDG_DATA_HOME = $dshDataHome
        $env:XDG_STATE_HOME = $dshStateHome
        $env:XDG_RUNTIME_DIR = $dshRuntimeHome
        $dshOutput = (& $dsh --profile headless --patch $dshPatchForSmoke `
            "Read README.md and report its first heading." 2>&1 | Out-String)
        $dshExit = $LASTEXITCODE

        # The Claude launcher owns a second local server and a loopback-only
        # outbound blocker. Run it as a real client, with no provider
        # credentials, and keep its trace separate from the shared OpenCode
        # and DSH endpoint trace.
        $claudeOutput = (& $powershell.Source -NoProfile -ExecutionPolicy Bypass `
            -File $claudeLauncher `
            -Port $ClaudePort `
            -ProxyPort $ClaudeProxyPort `
            -AllowedRoot $workspace `
            -TraceLog $claudeTrace `
            -ClaudeExecutable $claude `
            -Print `
            -Prompt "Read README.md and report its first heading." 2>&1 | Out-String)
        $claudeExit = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $clientErrorPreference
        Pop-Location
        $env:WRENCH_LOCAL_API_KEY = $originalKey
        $env:DEEPSEEK_API_KEY = $originalDeepSeekKey
        $env:HOME = $originalHome
        $env:USERPROFILE = $originalUserProfile
        $env:XDG_CONFIG_HOME = $originalXdgConfigHome
        $env:XDG_CACHE_HOME = $originalXdgCacheHome
        $env:XDG_DATA_HOME = $originalXdgDataHome
        $env:XDG_STATE_HOME = $originalXdgStateHome
        $env:XDG_RUNTIME_DIR = $originalXdgRuntimeDir
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
    $claudeTraceRows = @()
    if (Test-Path -LiteralPath $claudeTrace) {
        $claudeTraceRows = @(Get-Content -LiteralPath $claudeTrace | ForEach-Object { $_ | ConvertFrom-Json })
    }
    $claudeReadToolObserved = @(
        $claudeTraceRows | Where-Object {
            @($_.tool_names) -contains "read" -or @($_.tool_names) -contains "Read"
        }
    ).Count -gt 0
    $receipt = [ordered]@{
        schema = "wrench.portable-client-smoke.v1"
        status = if (
            $opencodeExit -eq 0 -and
            $dshExit -eq 0 -and
            $claudeExit -eq 0 -and
            $readToolObserved -and
            $claudeReadToolObserved
        ) { "PASSED" } else { "FAILED" }
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
                isolated_home = "dsh-isolated"
                output_file = "dsh.stdout.txt"
            }
            claude_code = [ordered]@{
                exit_code = $claudeExit
                structured_read_observed = $claudeReadToolObserved
                trace_rows = $claudeTraceRows.Count
                output_file = "claude.stdout.txt"
                trace_file = "wrench-claude.trace.jsonl"
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
    $claudeOutput | Set-Content -LiteralPath (Join-Path $OutputDir "claude.stdout.txt") -Encoding utf8
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputDir "receipt.json") -Encoding utf8
    Write-Output ($receipt | ConvertTo-Json -Depth 8)
    if ($receipt.status -ne "PASSED") { exit 1 }
} finally {
    $env:WRENCH_LOCAL_API_KEY = $originalKey
    $env:DEEPSEEK_API_KEY = $originalDeepSeekKey
    $env:HOME = $originalHome
    $env:USERPROFILE = $originalUserProfile
    $env:XDG_CONFIG_HOME = $originalXdgConfigHome
    $env:XDG_CACHE_HOME = $originalXdgCacheHome
    $env:XDG_DATA_HOME = $originalXdgDataHome
    $env:XDG_STATE_HOME = $originalXdgStateHome
    $env:XDG_RUNTIME_DIR = $originalXdgRuntimeDir
    if ($serverProcess -and -not $serverProcess.HasExited) {
        try { Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue } catch { }
    }
}

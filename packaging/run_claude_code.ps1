param(
    [int]$Port = 28944,
    [int]$ProxyPort = 28945,
    [string]$AllowedRoot = (Get-Location).Path,
    [string]$Prompt = "",
    [string]$ClaudeExecutable = "claude",
    [switch]$Print,
    [switch]$LoadModel,
    [switch]$KeepConfig,
    [string]$UpstreamUrl = "",
    [switch]$DisableMechanicalRoute,
    [string]$ConfigDirectory = "",
    [string]$TraceLog = "",
    [string[]]$AllowedTools = @("Read", "Glob", "Grep"),
    [string[]]$ClaudeArgument = @()
)

$ErrorActionPreference = "Stop"
$python = Get-Command python -ErrorAction Stop
$server = Join-Path $PSScriptRoot "wrench_server.py"
$blocker = Join-Path $PSScriptRoot "wrench_loopback_blocker.py"
if (-not (Test-Path -LiteralPath $server -PathType Leaf)) {
    throw "The downloaded Wrench package is missing wrench_server.py"
}
if (-not (Test-Path -LiteralPath $blocker -PathType Leaf)) {
    throw "The downloaded Wrench package is missing wrench_loopback_blocker.py"
}

$resolvedRoot = (Resolve-Path -LiteralPath $AllowedRoot -ErrorAction Stop).Path
if ($Port -lt 1 -or $Port -gt 65535) { throw "Port must be between 1 and 65535" }
if ($ProxyPort -lt 1 -or $ProxyPort -gt 65535) { throw "ProxyPort must be between 1 and 65535" }
if ($Port -eq $ProxyPort) { throw "Port and ProxyPort must be different" }

if (-not $TraceLog) {
    $TraceLog = Join-Path $PSScriptRoot "wrench-claude.trace.jsonl"
}

$createdConfig = $false
if (-not $ConfigDirectory) {
    $ConfigDirectory = Join-Path ([IO.Path]::GetTempPath()) ("wrench-claude-" + [Guid]::NewGuid().ToString("N"))
    $createdConfig = $true
}
New-Item -ItemType Directory -Force -Path $ConfigDirectory | Out-Null

$serverStdout = Join-Path ([IO.Path]::GetTempPath()) ("wrench-server-" + [Guid]::NewGuid().ToString("N") + ".out.log")
$serverStderr = Join-Path ([IO.Path]::GetTempPath()) ("wrench-server-" + [Guid]::NewGuid().ToString("N") + ".err.log")
$serverArguments = @(
    $server,
    "--model-dir", $PSScriptRoot,
    "--allowed-root", $resolvedRoot,
    "--port", $Port,
    "--max-request-bytes", 536870912,
    "--trace-log", $TraceLog
)
if (-not $LoadModel) {
    $serverArguments += "--mechanical-only"
}
if ($UpstreamUrl) {
    $serverArguments += @("--upstream-url", $UpstreamUrl, "--upstream-timeout-seconds", "60")
}
if ($DisableMechanicalRoute) {
    $serverArguments += "--disable-mechanical-route"
}

$blockerProcess = $null
$serverProcess = $null
$savedEnvironment = @{}
$environmentNames = @(
    "CLAUDE_CONFIG_DIR",
    "CLAUDE_SECURE_STORAGE_CONFIG_DIR",
    "CLAUDE_CODE_SIMPLE",
    "CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT",
    "CLAUDE_CODE_USE_GATEWAY",
    "CLAUDE_GATEWAY_ALLOW_LOOPBACK",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "VERTEXAI_PROJECT",
    "VERTEXAI_LOCATION",
    "CLOUD_ML_REGION",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY"
)

try {
    foreach ($name in $environmentNames) {
        $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
    }

    $blockerProcess = Start-Process -FilePath $python.Source `
        -ArgumentList @($blocker, "--host", "127.0.0.1", "--port", $ProxyPort) `
        -WindowStyle Hidden -PassThru
    Start-Sleep -Milliseconds 150
    if ($blockerProcess.HasExited) {
        throw "The external traffic blocker exited before Claude Code started"
    }

    $serverProcess = Start-Process -FilePath $python.Source `
        -ArgumentList $serverArguments `
        -WindowStyle Hidden -RedirectStandardOutput $serverStdout `
        -RedirectStandardError $serverStderr -PassThru

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
                $errorTail = if (Test-Path -LiteralPath $serverStderr) {
                    (Get-Content -LiteralPath $serverStderr -Tail 20 -ErrorAction SilentlyContinue) -join " | "
                } else { "" }
                throw "Wrench server exited before readiness. $errorTail"
            }
        }
        Start-Sleep -Milliseconds 250
    }
    if (-not $ready) { throw "Wrench server readiness timeout on port $Port" }

    $env:CLAUDE_CONFIG_DIR = (Resolve-Path -LiteralPath $ConfigDirectory).Path
    $env:CLAUDE_SECURE_STORAGE_CONFIG_DIR = $env:CLAUDE_CONFIG_DIR
    $env:CLAUDE_CODE_SIMPLE = "1"
    $env:CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT = "1"
    $env:CLAUDE_CODE_USE_GATEWAY = "1"
    $env:CLAUDE_GATEWAY_ALLOW_LOOPBACK = "1"
    $env:ANTHROPIC_BASE_URL = "http://127.0.0.1:$Port"
    $env:ANTHROPIC_AUTH_TOKEN = "wrench-local-only"
    $env:ANTHROPIC_API_KEY = $null
    $env:AWS_ACCESS_KEY_ID = $null
    $env:AWS_SECRET_ACCESS_KEY = $null
    $env:AWS_SESSION_TOKEN = $null
    $env:GOOGLE_APPLICATION_CREDENTIALS = $null
    $env:VERTEXAI_PROJECT = $null
    $env:VERTEXAI_LOCATION = $null
    $env:CLOUD_ML_REGION = $null
    $proxyUrl = "http://127.0.0.1:$ProxyPort"
    $env:HTTP_PROXY = $proxyUrl
    $env:HTTPS_PROXY = $proxyUrl
    $env:ALL_PROXY = $proxyUrl
    $env:NO_PROXY = "127.0.0.1,localhost"

    $claudeArguments = @()
    if ($Print) { $claudeArguments += "--print" }
    if ($Prompt) { $claudeArguments += $Prompt }
    $claudeArguments += @("--bare", "--add-dir", $resolvedRoot)
    if ($AllowedTools -and $AllowedTools.Count -gt 0) {
        $claudeArguments += "--allowed-tools"
        # Claude Code accepts comma-separated tools as one argument. Passing
        # separate values lets the option parser consume the positional prompt.
        $claudeArguments += ($AllowedTools -join ",")
    }
    if ($ClaudeArgument -and $ClaudeArgument.Count -gt 0) {
        $claudeArguments += $ClaudeArgument
    }
    & $ClaudeExecutable @claudeArguments
    $exitCode = $LASTEXITCODE
} finally {
    foreach ($name in $environmentNames) {
        [Environment]::SetEnvironmentVariable($name, $savedEnvironment[$name], "Process")
    }
    if ($serverProcess -and -not $serverProcess.HasExited) {
        try { Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue } catch { }
    }
    if ($blockerProcess -and -not $blockerProcess.HasExited) {
        try { Stop-Process -Id $blockerProcess.Id -Force -ErrorAction SilentlyContinue } catch { }
    }
    Remove-Item -LiteralPath $serverStdout, $serverStderr -Force -ErrorAction SilentlyContinue
    if ($createdConfig -and -not $KeepConfig) {
        Remove-Item -LiteralPath $ConfigDirectory -Recurse -Force -ErrorAction SilentlyContinue
    }
}

exit $exitCode

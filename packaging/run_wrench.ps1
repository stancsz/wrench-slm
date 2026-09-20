param(
    [int]$Port = 28900,
    [string]$AllowedRoot = $PSScriptRoot,
    [int]$MaxRequestBytes = 268435456,
    [switch]$LoadModel
)

$ErrorActionPreference = "Stop"
$python = Get-Command python -ErrorAction Stop
$server = Join-Path $PSScriptRoot "wrench_server.py"
if (-not (Test-Path -LiteralPath $server -PathType Leaf)) {
    throw "The downloaded Wrench package is missing wrench_server.py"
}

$arguments = @(
    $server,
    "--model-dir", $PSScriptRoot,
    "--allowed-root", $AllowedRoot,
    "--port", $Port,
    "--max-request-bytes", $MaxRequestBytes
)
if (-not $LoadModel) {
    $arguments += "--mechanical-only"
}

& $python.Source @arguments
exit $LASTEXITCODE

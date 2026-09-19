[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $SourceRoot,

    [Parameter(Mandatory = $true)]
    [string] $ArtifactRoot,

    [Parameter(Mandatory = $true)]
    [string] $ExpectedSourceCommit,

    [Parameter(Mandatory = $true)]
    [string] $ExpectedArtifactCommit,

    [Parameter(Mandatory = $true)]
    [string] $ReceiptRoot,

    [string] $PythonExe = "py",
    [string[]] $PythonArguments = @("-3")
)

$ErrorActionPreference = "Stop"
$SourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path
$ArtifactRoot = (Resolve-Path -LiteralPath $ArtifactRoot).Path
$ReceiptRoot = [IO.Path]::GetFullPath($ReceiptRoot)
$ScriptRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$ModelPath = Join-Path $ArtifactRoot "models\Wrench-Qwen3.6-8expert-BF16"
$SmokePath = Join-Path $ReceiptRoot "runtime-smoke.json"
$PreflightPath = Join-Path $ReceiptRoot "runtime-preflight-receipt.json"
$VerifiedPath = Join-Path $ReceiptRoot "verified-cross-host-receipt.json"
$LogPath = Join-Path $ReceiptRoot "worker.log"

New-Item -ItemType Directory -Force -Path $ReceiptRoot | Out-Null
Start-Transcript -LiteralPath $LogPath -Force | Out-Null

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)] [string] $Root,
        [Parameter(Mandatory = $true)] [string[]] $GitArguments
    )
    & git -C $Root @GitArguments
    if ($LASTEXITCODE -ne 0) {
        throw "git command failed in ${Root}: git $($GitArguments -join ' ')"
    }
}

function Get-GitHead {
    param([Parameter(Mandatory = $true)] [string] $Root)
    $head = (& git -C $Root rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "cannot read git HEAD in $Root"
    }
    return $head
}

try {
    $dirty = @(& git -C $SourceRoot status --porcelain)
    if ($LASTEXITCODE -ne 0) {
        throw "source checkout is not a git worktree: $SourceRoot"
    }
    if ($dirty.Count -gt 0) {
        $dirtyPath = Join-Path $ReceiptRoot "source-dirty.txt"
        $dirty | Set-Content -LiteralPath $dirtyPath -Encoding utf8
        throw "BLOCKED_DIRTY_SOURCE_CHECKOUT; see $dirtyPath"
    }

    Invoke-Git -Root $SourceRoot -GitArguments @("fetch", "origin", "main")
    if ((Get-GitHead -Root $SourceRoot) -ne $ExpectedSourceCommit) {
        Invoke-Git -Root $SourceRoot -GitArguments @("checkout", "--detach", $ExpectedSourceCommit)
    }
    if ((Get-GitHead -Root $SourceRoot) -ne $ExpectedSourceCommit) {
        throw "source commit did not reach expected pin $ExpectedSourceCommit"
    }

    Invoke-Git -Root $ArtifactRoot -GitArguments @("fetch", "origin", "main")
    if ((Get-GitHead -Root $ArtifactRoot) -ne $ExpectedArtifactCommit) {
        Invoke-Git -Root $ArtifactRoot -GitArguments @("checkout", "--detach", $ExpectedArtifactCommit)
    }
    if ((Get-GitHead -Root $ArtifactRoot) -ne $ExpectedArtifactCommit) {
        throw "artifact commit did not reach expected pin $ExpectedArtifactCommit"
    }
    Invoke-Git -Root $ArtifactRoot -GitArguments @("lfs", "pull", "--include=models/Wrench-Qwen3.6-8expert-BF16/*")
    Invoke-Git -Root $ArtifactRoot -GitArguments @("lfs", "fsck")

    & $PythonExe @PythonArguments (Join-Path $ScriptRoot "tools\smoke_pruned_qwen.py") $ModelPath `
        --output $SmokePath --prompt "Return only the word OK." --max-new-tokens 8
    if ($LASTEXITCODE -ne 0) {
        throw "runtime smoke failed"
    }

    & $PythonExe @PythonArguments (Join-Path $ScriptRoot "tools\compose_cross_host_receipt.py") `
        --host rtx-5060-ti --source-root $SourceRoot --artifact-root $ArtifactRoot `
        --source-commit $ExpectedSourceCommit --artifact-commit $ExpectedArtifactCommit `
        --runtime-smoke $SmokePath --output $PreflightPath
    if ($LASTEXITCODE -ne 0) {
        throw "cross-host receipt composition failed"
    }

    & $PythonExe @PythonArguments (Join-Path $ScriptRoot "tools\verify_cross_host_receipt.py") `
        $PreflightPath --expected-source-commit $ExpectedSourceCommit `
        --expected-artifact-commit $ExpectedArtifactCommit --output $VerifiedPath
    if ($LASTEXITCODE -ne 0) {
        throw "cross-host receipt verification failed"
    }

    Write-Output "PASS_5060TI_PREFLIGHT"
    Write-Output "verified receipt: $VerifiedPath"
}
finally {
    Stop-Transcript | Out-Null
}

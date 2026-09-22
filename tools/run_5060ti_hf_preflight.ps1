[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $SourceRoot,

    [Parameter(Mandatory = $true)]
    [string] $ExpectedSourceCommit,

    [Parameter(Mandatory = $true)]
    [string] $HuggingFaceRepoId,

    [Parameter(Mandatory = $true)]
    [string] $HuggingFaceRevision,

    [Parameter(Mandatory = $true)]
    [string] $ModelRoot,

    [Parameter(Mandatory = $true)]
    [string] $ReceiptRoot,

    [string] $PythonExe = "py",
    [string[]] $PythonArguments = @("-3"),
    [string] $HfExecutable = "hf",
    [string] $JobId = "",
    [string] $ClaimNonce = "",
    [switch] $SkipDownload
)

$ErrorActionPreference = "Stop"
$SourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path
$ModelRoot = [IO.Path]::GetFullPath($ModelRoot)
$ReceiptRoot = [IO.Path]::GetFullPath($ReceiptRoot)
$ScriptRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$RepoLeaf = ($HuggingFaceRepoId -split "/")[-1]
$PackageRoot = Join-Path $ModelRoot $RepoLeaf
$ValidationPath = Join-Path $ReceiptRoot "package-validation.json"
$SmokePath = Join-Path $ReceiptRoot "package-smoke.json"
$ResourcePath = Join-Path $ReceiptRoot "resource-snapshot.json"
$PreflightPath = Join-Path $ReceiptRoot "hf-cross-host-receipt.json"
$VerifiedPath = Join-Path $ReceiptRoot "verified-hf-cross-host-receipt.json"
$LogPath = Join-Path $ReceiptRoot "worker.log"

New-Item -ItemType Directory -Force -Path $ModelRoot, $ReceiptRoot | Out-Null
Start-Transcript -LiteralPath $LogPath -Force | Out-Null

function Get-HostResourceSample {
    $os = Get-CimInstance Win32_OperatingSystem
    $ramTotal = [double]$os.TotalVisibleMemorySize * 1024
    $ramFree = [double]$os.FreePhysicalMemory * 1024
    if ($ramTotal -le 0) {
        throw "cannot read host RAM capacity"
    }
    $gpuLines = @(& nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader,nounits)
    if ($LASTEXITCODE -ne 0 -or $gpuLines.Count -eq 0) {
        throw "cannot read NVIDIA VRAM state"
    }
    $gpus = foreach ($line in $gpuLines) {
        $parts = $line -split ","
        if ($parts.Count -lt 3) {
            throw "unexpected nvidia-smi output: $line"
        }
        $totalMiB = [double]($parts[1].Trim())
        $usedMiB = [double]($parts[2].Trim())
        if ($totalMiB -le 0) {
            throw "invalid GPU capacity: $line"
        }
        [pscustomobject]@{
            name = $parts[0].Trim()
            total_mib = $totalMiB
            used_mib = $usedMiB
            free_mib = $totalMiB - $usedMiB
            free_fraction = ($totalMiB - $usedMiB) / $totalMiB
        }
    }
    [pscustomobject]@{
        ram_total_bytes = $ramTotal
        ram_free_bytes = $ramFree
        ram_free_fraction = $ramFree / $ramTotal
        gpus = @($gpus)
    }
}

function Assert-HostResourceReserve {
    param([Parameter(Mandatory = $true)] [object] $Sample)
    if ([double]$Sample.ram_free_fraction -lt 0.10) {
        throw "BLOCKED_HOST_RESOURCE_RESERVE: RAM free fraction is below 10 percent"
    }
    foreach ($gpu in $Sample.gpus) {
        if ([double]$gpu.free_fraction -lt 0.10) {
            throw "BLOCKED_HOST_RESOURCE_RESERVE: VRAM free fraction is below 10 percent on $($gpu.name)"
        }
    }
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)] [string] $Executable,
        [Parameter(Mandatory = $true)] [string[]] $Arguments
    )
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "command failed: $Executable $($Arguments -join ' ')"
    }
}

try {
    $before = Get-HostResourceSample
    Assert-HostResourceReserve -Sample $before

    $dirty = @(& git -C $SourceRoot status --porcelain)
    if ($LASTEXITCODE -ne 0) {
        throw "source checkout is not a git worktree: $SourceRoot"
    }
    if ($dirty.Count -gt 0) {
        throw "BLOCKED_DIRTY_SOURCE_CHECKOUT"
    }
    $head = (& git -C $SourceRoot rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $head -ne $ExpectedSourceCommit) {
        throw "source commit mismatch: $head != $ExpectedSourceCommit"
    }

    if (-not (Get-Command -Name $HfExecutable -ErrorAction SilentlyContinue)) {
        throw "Hugging Face CLI not found: $HfExecutable"
    }
    New-Item -ItemType Directory -Force -Path $PackageRoot | Out-Null
    if (-not $SkipDownload) {
        Invoke-Checked -Executable $HfExecutable -Arguments @(
            "download", $HuggingFaceRepoId, "--revision", $HuggingFaceRevision,
            "--local-dir", $PackageRoot
        )
    } elseif (-not (Test-Path -LiteralPath $PackageRoot -PathType Container)) {
        throw "skip download requested but package root is missing: $PackageRoot"
    }

    $after = Get-HostResourceSample
    Assert-HostResourceReserve -Sample $after
    [pscustomobject]@{
        schema = "wrench.host-resource-reserve.v1"
        status = "PASS_HOST_RESOURCE_RESERVE"
        before_download = $before
        after_download = $after
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ResourcePath -Encoding utf8

    Invoke-Checked -Executable $PythonExe -Arguments ($PythonArguments + @(
        (Join-Path $ScriptRoot "tools\validate_wrench_package.py"),
        "--model-dir", $PackageRoot,
        "--output", $ValidationPath
    ))
    Invoke-Checked -Executable $PythonExe -Arguments ($PythonArguments + @(
        (Join-Path $ScriptRoot "tools\smoke_hf_wrench_package.py"),
        "--model-dir", $PackageRoot,
        "--output", $SmokePath
    ))

    $gpuIdentity = ((& nvidia-smi --query-gpu=name --format=csv,noheader) -join "; ").Trim()
    if (-not $gpuIdentity) {
        throw "GPU identity is empty"
    }
    $composeArguments = $PythonArguments + @(
        (Join-Path $ScriptRoot "tools\compose_hf_cross_host_receipt.py"),
        "--host", "rtx-5060-ti",
        "--source-root", $SourceRoot,
        "--source-commit", $ExpectedSourceCommit,
        "--huggingface-repo-id", $HuggingFaceRepoId,
        "--huggingface-revision", $HuggingFaceRevision,
        "--package-root", $PackageRoot,
        "--validation", $ValidationPath,
        "--smoke", $SmokePath,
        "--resource-snapshot", $ResourcePath,
        "--gpu-identity", $gpuIdentity,
        "--host-name", $env:COMPUTERNAME,
        "--output", $PreflightPath
    )
    if ($JobId -or $ClaimNonce) {
        if (-not ($JobId -and $ClaimNonce)) {
            throw "JobId and ClaimNonce must be supplied together"
        }
        $composeArguments += @("--job-id", $JobId, "--claim-nonce", $ClaimNonce)
    }
    Invoke-Checked -Executable $PythonExe -Arguments $composeArguments
    $verifyArguments = $PythonArguments + @(
        (Join-Path $ScriptRoot "tools\verify_hf_cross_host_receipt.py"),
        $PreflightPath,
        "--expected-source-commit", $ExpectedSourceCommit,
        "--expected-repo-id", $HuggingFaceRepoId,
        "--expected-revision", $HuggingFaceRevision,
        "--expected-host-name", $env:COMPUTERNAME,
        "--output", $VerifiedPath
    )
    if ($JobId -or $ClaimNonce) {
        $verifyArguments += @("--expected-job-id", $JobId, "--expected-claim-nonce", $ClaimNonce)
    }
    Invoke-Checked -Executable $PythonExe -Arguments $verifyArguments

    Write-Output "PASS_5060TI_HF_PACKAGE_PREFLIGHT"
    Write-Output "verified receipt: $VerifiedPath"
}
finally {
    Stop-Transcript | Out-Null
}

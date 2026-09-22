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
    [switch] $SkipPackageDownload
)

$ErrorActionPreference = "Stop"
$SourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path
$ModelRoot = [IO.Path]::GetFullPath($ModelRoot)
$ReceiptRoot = [IO.Path]::GetFullPath($ReceiptRoot)
$ScriptRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$RepoLeaf = ($HuggingFaceRepoId -split "/")[-1]
$PackageRoot = Join-Path $ModelRoot $RepoLeaf
$CasesPath = Join-Path $SourceRoot "evals\wrench-expanded-v2\cases.jsonl"
$LogPath = Join-Path $ReceiptRoot "full-verification.log"
$FullReceiptPath = Join-Path $ReceiptRoot "full-verification-receipt.json"
$PreflightReceiptPath = Join-Path $ReceiptRoot "verified-hf-cross-host-receipt.json"
$FullPort = Get-Random -Minimum 29000 -Maximum 29900

New-Item -ItemType Directory -Force -Path $ReceiptRoot | Out-Null
$LogPath | ForEach-Object { New-Item -ItemType File -Force -Path $_ | Out-Null }

function Get-HostResourceSample {
    $os = Get-CimInstance Win32_OperatingSystem
    $ramTotal = [double]$os.TotalVisibleMemorySize * 1024
    $ramFree = [double]$os.FreePhysicalMemory * 1024
    if ($ramTotal -le 0) { throw "cannot read host RAM capacity" }
    $gpuLines = @(& nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader,nounits)
    if ($LASTEXITCODE -ne 0 -or $gpuLines.Count -eq 0) { throw "cannot read NVIDIA VRAM state" }
    $gpus = foreach ($line in $gpuLines) {
        $parts = $line -split ","
        if ($parts.Count -lt 3) { throw "unexpected nvidia-smi output: $line" }
        $totalMiB = [double]($parts[1].Trim())
        $usedMiB = [double]($parts[2].Trim())
        if ($totalMiB -le 0) { throw "invalid GPU capacity: $line" }
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
    & $Executable @Arguments 2>&1 | Tee-Object -FilePath $LogPath -Append
    if ($LASTEXITCODE -ne 0) {
        throw "command failed: $Executable $($Arguments -join ' ')"
    }
}

function Stop-ChildServer {
    param([object] $Process)
    if ($Process -and -not $Process.HasExited) {
        try { Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue } catch { }
        try { $Process.WaitForExit(5000) } catch { }
    }
}

$serverProcess = $null
$before = $null
$after = $null
$status = "FAIL_5060TI_CURRENT_PACKAGE_VERIFICATION"
$failure = $null

try {
    $before = Get-HostResourceSample
    Assert-HostResourceReserve -Sample $before
    if (-not (Test-Path -LiteralPath $CasesPath -PathType Leaf)) {
        throw "missing canonical 220-case fixture: $CasesPath"
    }

    $preflight = Join-Path $ScriptRoot "tools\run_5060ti_hf_preflight.ps1"
    $preflightArgs = @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $preflight,
        "-SourceRoot", $SourceRoot,
        "-ExpectedSourceCommit", $ExpectedSourceCommit,
        "-HuggingFaceRepoId", $HuggingFaceRepoId,
        "-HuggingFaceRevision", $HuggingFaceRevision,
        "-ModelRoot", $ModelRoot,
        "-ReceiptRoot", $ReceiptRoot,
        "-PythonExe", $PythonExe,
        "-HfExecutable", $HfExecutable,
        "-JobId", $JobId,
        "-ClaimNonce", $ClaimNonce
    )
    if ($SkipPackageDownload) { $preflightArgs += "-SkipDownload" }
    # The nested Windows PowerShell invocation already defaults to `py -3`.
    # Passing the bare `-3` as a value makes the child parser treat it as a
    # switch, so only forward Python arguments when the caller explicitly
    # selected a non-default launcher argument.
    $defaultPythonArguments = @("-3")
    if (-not (@($PythonArguments).Count -eq 1 -and @($PythonArguments)[0] -ceq $defaultPythonArguments[0])) {
        foreach ($argument in $PythonArguments) {
            $preflightArgs += @("-PythonArguments", $argument)
        }
    }
    Invoke-Checked -Executable "powershell" -Arguments $preflightArgs

    $serverOut = Join-Path $ReceiptRoot "package-server.stdout.log"
    $serverErr = Join-Path $ReceiptRoot "package-server.stderr.log"
    $serverArgs = @(
        (Join-Path $PackageRoot "wrench_server.py"),
        "--model-dir", $PackageRoot,
        "--allowed-root", $SourceRoot,
        "--host", "127.0.0.1",
        "--port", $FullPort,
        "--model-name", "wrench-5060ti-package",
        "--mechanical-only",
        "--max-request-bytes", 536870912
    )
    $serverProcess = Start-Process -FilePath $PythonExe -ArgumentList ($PythonArguments + $serverArgs) `
        -WorkingDirectory $PackageRoot -WindowStyle Hidden `
        -RedirectStandardOutput $serverOut -RedirectStandardError $serverErr -PassThru
    Start-Sleep -Milliseconds 750
    if ($serverProcess.HasExited) { throw "package server exited before 220 replay" }

    $replayDir = Join-Path $ReceiptRoot "replay-220"
    Invoke-Checked -Executable $PythonExe -Arguments ($PythonArguments + @(
        (Join-Path $ScriptRoot "tools\run_wrench_case_eval.py"),
        $CasesPath,
        "--endpoint", ("http://127.0.0.1:{0}/v1/chat/completions" -f $FullPort),
        "--model", "wrench-5060ti-package",
        "--root", $SourceRoot,
        "--output", (Join-Path $replayDir "evaluation.json"),
        "--health-fixture"
    ))
    Stop-ChildServer -Process $serverProcess
    $serverProcess = $null

    Invoke-Checked -Executable $PythonExe -Arguments ($PythonArguments + @(
        (Join-Path $ScriptRoot "tools\probe_model_local_server.py"),
        "--package-dir", $PackageRoot,
        "--target-tokens", 4000000,
        "--output", (Join-Path $ReceiptRoot "probe-4m.json")
    ))
    Invoke-Checked -Executable $PythonExe -Arguments ($PythonArguments + @(
        (Join-Path $ScriptRoot "tools\probe_package_retrieval_quality.py"),
        "--package-dir", $PackageRoot,
        "--output", (Join-Path $ReceiptRoot "retrieval-2m-4m.json")
    ))

    $clientSmoke = Join-Path $ScriptRoot "tools\smoke_portable_clients.ps1"
    $clientStatus = "SKIPPED_CLIENT_TOOLS_NOT_INSTALLED"
    if ((Get-Command opencode -ErrorAction SilentlyContinue) -and (Get-Command dsh -ErrorAction SilentlyContinue)) {
        Invoke-Checked -Executable "powershell" -Arguments @(
            "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $clientSmoke,
            "-PackageDir", $PackageRoot,
            "-AllowedRoot", $SourceRoot,
            "-OutputDir", (Join-Path $ReceiptRoot "clients"),
            "-Port", ($FullPort + 1)
        )
        $clientStatus = "PASS_CLIENT_SMOKE"
    }

    $after = Get-HostResourceSample
    Assert-HostResourceReserve -Sample $after
    $status = "PASS_5060TI_CURRENT_PACKAGE_VERIFICATION"
    $receipt = [ordered]@{
        schema = "wrench.5060ti.current-package-verification.v1"
        status = $status
        job_id = $JobId
        claim_nonce = $ClaimNonce
        host_name = $env:COMPUTERNAME
        gpu_identity = ((& nvidia-smi --query-gpu=name --format=csv,noheader) -join "; ").Trim()
        source_commit = $ExpectedSourceCommit
        huggingface_repo_id = $HuggingFaceRepoId
        huggingface_revision = $HuggingFaceRevision
        package_root = $PackageRoot
        resource_snapshot_before = $before
        resource_snapshot_after = $after
        preflight_receipt = $PreflightReceiptPath
        package_only_220_receipt = (Join-Path $replayDir "evaluation.json")
        model_local_4m_receipt = (Join-Path $ReceiptRoot "probe-4m.json")
        retrieval_2m_4m_receipt = (Join-Path $ReceiptRoot "retrieval-2m-4m.json")
        client_smoke_status = $clientStatus
        client_smoke_receipt = (Join-Path $ReceiptRoot "clients\receipt.json")
        limitations = @(
            "The 220 replay is package-only diagnostic evidence and has no teacher trace upload.",
            "The package-local route is hybrid mechanical staging, not dense-native 4M attention.",
            "This receipt does not establish learned MiniMax parity or production readiness."
        )
    }
    $receipt | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $FullReceiptPath -Encoding utf8
    Write-Output "PASS_5060TI_CURRENT_PACKAGE_VERIFICATION"
}
catch {
    $failure = $_.Exception.Message
    Add-Content -LiteralPath $LogPath -Value ("FAILURE: " + $failure)
    $after = try { Get-HostResourceSample } catch { $null }
    $receipt = [ordered]@{
        schema = "wrench.5060ti.current-package-verification.v1"
        status = $status
        job_id = $JobId
        claim_nonce = $ClaimNonce
        host_name = $env:COMPUTERNAME
        source_commit = $ExpectedSourceCommit
        huggingface_repo_id = $HuggingFaceRepoId
        huggingface_revision = $HuggingFaceRevision
        resource_snapshot_before = $before
        resource_snapshot_after = $after
        failure_details = $failure
        log_path = $LogPath
        limitations = @("No independent 5060Ti pass is claimed from a failed or partial run.")
    }
    $receipt | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $FullReceiptPath -Encoding utf8
    throw
}
finally {
    Stop-ChildServer -Process $serverProcess
}

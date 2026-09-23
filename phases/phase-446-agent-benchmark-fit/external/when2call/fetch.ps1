$ErrorActionPreference = 'Stop'

$commit = 'ecc8d42388e91ab37e7e737d48e16e8ecea3d1dc'
$expectedSha256 = '8C3694E583EEEB8DBC297E6CD90DA70EFC68EFA4B6ADB7227523E828C6B7B14C'
$dataDir = Join-Path $PSScriptRoot 'data'
$dataPath = Join-Path $dataDir 'when2call_test_mcq.jsonl'
$licensePath = Join-Path $PSScriptRoot 'LICENSE.txt'

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/NVIDIA/When2Call/$commit/data/test/when2call_test_mcq.jsonl" -OutFile $dataPath
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/NVIDIA/When2Call/$commit/LICENSE.txt" -OutFile $licensePath

$actualSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $dataPath).Hash
if ($actualSha256 -ne $expectedSha256) {
    throw "When2Call SHA-256 mismatch. Expected $expectedSha256, got $actualSha256"
}

[pscustomobject]@{
    revision = $commit
    file = 'data/when2call_test_mcq.jsonl'
    sha256 = $actualSha256
    bytes = (Get-Item -LiteralPath $dataPath).Length
} | ConvertTo-Json -Compress

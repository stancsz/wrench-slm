$ErrorActionPreference = 'Stop'

$datasetRevision = '524ef5422f63899e7c1a97c791197c37ace0e051'
$repositoryRevision = '22da2533bd8471576043279e3f8134d7e31c11c1'
$expectedSha256 = '51495DC14E5403CCC56D7430253CF41A1E5AA30CE7E35AE9B207FCE667EA7A2A'
$dataDir = Join-Path $PSScriptRoot 'data'
$dataPath = Join-Path $dataDir 'test_en.json'
$licensePath = Join-Path $PSScriptRoot 'LICENSE'

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
Invoke-WebRequest -Uri "https://huggingface.co/datasets/Joelzhang/ToolBeHonest/resolve/$datasetRevision/test_en.json" -OutFile $dataPath
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/ToolBeHonest/ToolBeHonest/$repositoryRevision/LICENSE" -OutFile $licensePath

$actualSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $dataPath).Hash
if ($actualSha256 -ne $expectedSha256) {
    throw "ToolBeHonest SHA-256 mismatch. Expected $expectedSha256, got $actualSha256"
}

[pscustomobject]@{
    dataset_revision = $datasetRevision
    repository_revision = $repositoryRevision
    file = 'data/test_en.json'
    sha256 = $actualSha256
    bytes = (Get-Item -LiteralPath $dataPath).Length
} | ConvertTo-Json -Compress

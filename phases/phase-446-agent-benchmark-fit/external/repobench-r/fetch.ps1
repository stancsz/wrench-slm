$ErrorActionPreference = 'Stop'
$fetcher = Join-Path $PSScriptRoot 'fetch.py'
& py -3 $fetcher
if ($LASTEXITCODE -ne 0) { throw "RepoBench-R fetch failed with exit code $LASTEXITCODE" }
